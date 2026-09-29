#!/usr/bin/env python
"""The paper's results tables, computed from the campaign's run records.

The paper *Structuring fusion MDAO with DSMs* (§3, Case 2: PROCESS) prints
three tables in shapes the report does not: the evaluation phase's module
sweeps against the **plain** flat control ``A0`` (the report's Table 9 states
its ratio against the declared rung reference ``A1`` and has no per-run
distribution), the optimiser's iterations per configuration, and the
optimisation phase's module sweeps.  This module writes them into
:data:`PAPER_NAME` beside the report, as Markdown grids and as LaTeX rows to
paste into the paper's ``tabular`` bodies.

**The shape is the user's (2026-09-28).** A cell is a module's **sweeps per
run**, averaged over the ``n`` perturbed runs of the arm; the ratio column is
the **ratio of the means** (Σ intervened / Σ control over the paired runs, the
report's pooled reading); beside it the per-run ratio's median with its
``[min, max]``.  The rows are the three modules, **Feedforward** (the pulse
node and any feed-forward tail node: executed on every evaluation, no
iteration) and **Post-processing** (the once-per-run deferred nodes: needed by
no objective or constraint, so the partitioned arm runs them only in the
output pass).  There is no total row: sweeps of different modules do not add.

**Nothing here is a new construction.** Every number is the tally's own
building block applied to the tally's own population: the published sources
(:mod:`tally`), the node grouping (:func:`tally_evaluation.node_grouping`),
:func:`stats.module_sweeps`, the optimisation phase's seed set
(:func:`stats.every_arm_converged` over :func:`tally_optimisation.arm_groups`)
and :func:`stats.per_seed_ratio_summary`.  And every cell the stage records
already hold is **compared** with them, exactly, before anything is written
(:func:`cross_check`); the comparison is shown able to fail on each run
(:func:`_cross_check_tooth`, protocol §12).  A mismatch is reported and the
file is not written.
"""

from __future__ import annotations

import ast
import copy
import math
import dataclasses
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from harness.core.config import Campaign
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

#: The one execution of the post-processing set that completes the partitioned
#: arm's evaluation (the user, 2026-09-28: *"If phase A is a single evaluation
#: run, it should converge the MDA and then run all these other models exactly
#: once right? Otherwise it doesn't produce the same information as the
#: reference case."*).  The flat arms' final sweep already computes those
#: outputs at the converged state; the partitioned arm's measured evaluation
#: leaves them uncomputed, and its driver runs them once, after convergence, in
#: the output pass.  Phase A's census stops before that pass, so the execution
#: is **charged here by construction, not read from the census**; the premise
#: (the measured count is exactly 0) is checked on every run, and phase B's
#: whole-run census — 2 per run in B2, the output pass and the exit audit, on
#: every seed — is the measurement that says it is one execution.
CHARGED_ONCE = {"A2": 1.0}

#: Phase A cells printed as the integer every run reads, not as a mean (the
#: user, 2026-09-29): the partitioned arm's feedforward and post-processing
#: rows run once per evaluation by construction.  A run reading anything else
#: is a refusal, not a rounded mean.
EXACT_CELLS = {("A2", "Feedforward"), ("A2", "Post-processing")}

PHASE_A_SOURCE = tally_mod.ACCEPTANCE_REGIME
PHASE_A_PAIR = ("A0", "A2")
PHASE_B_SOURCE = "campaign_optimisation"
PHASE_B_PAIR = tally_b.HEADLINE_PAIR

#: The iteration quantity of the report's Table 12 (check 2's statistic).
ITERATIONS_LABEL, ITERATIONS = tally_b.PATH_QUANTITIES[0]


class PaperTablesError(RuntimeError):
    """The tables cannot be stated over the records as they are."""


# --------------------------------------------------------------------------
# the population, as the tally forms it
# --------------------------------------------------------------------------


def with_runs(campaign: Campaign, runs_dir: Path | None) -> Campaign:
    """The campaign reading its run records from *runs_dir*.

    Run records are untracked and move with a retired worktree to
    ``idf_probe/runs/A<n>_runs/``; this points the read at such a copy.
    Nothing else of the campaign changes, and nothing is written there.
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
        rows,
        phase=phase,
        what=f"{source.name} — {source.what}",
        campaign_present=present,
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
# the three tables
# --------------------------------------------------------------------------


def phase_a(campaign: Campaign) -> list[dict[str, Any]]:
    """Module sweeps per evaluation, ``AR A0 A1 A2``, A2 against A0."""
    population = _population(campaign, PHASE_A_SOURCE, tally_a.PHASE)
    base, arm = PHASE_A_PAIR
    blocks: list[dict[str, Any]] = []
    for config in campaign.configurations:
        by_seed = tally_a._by_arm_and_seed(population, config.name)
        if not by_seed:
            continue
        finished = {
            a: {k: r for k, r in rows.items() if stats_mod.finished(r)}
            for a, rows in by_seed.items()
        }
        every = [r for rows in finished.values() for r in rows.values()]
        groups = tally_a.node_grouping(campaign, config.name, every, phase=tally_a.PHASE)
        sweeps = {
            a: {
                k: stats_mod.module_sweeps(
                    stats_mod.per_node_census(r, phase=tally_a.PHASE), groups
                )
                for k, r in rows.items()
            }
            for a, rows in finished.items()
        }
        measured = copy.deepcopy(sweeps)
        for a, charge in CHARGED_ONCE.items():
            for k, s in sweeps.get(a, {}).items():
                value = s.get(stats_mod.ONCE_PER_RUN_GROUP)
                if value is None:
                    continue
                if value != 0:
                    raise PaperTablesError(
                        f"{config.name} {a} seed {k}: the post-processing set was "
                        f"swept {value} times in the measured evaluation; the charge "
                        f"of one deferred execution presumes 0 and is refused"
                    )
                s[stats_mod.ONCE_PER_RUN_GROUP] = charge
        paired = sorted(set(finished.get(base, {})) & set(finished.get(arm, {})))
        rows_out: list[dict[str, Any]] = []
        for label, members in ROWS:
            row: dict[str, Any] = {"row": label, "groups": list(members)}
            for a in tally_a.LADDER:
                row[f"{a}_measured"] = _mean(
                    [
                        v
                        for s in measured.get(a, {}).values()
                        if (v := _row_sweeps(s, members, config.name)) is not None
                    ]
                )
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
            if any(v is None for v in left + right):
                row["summary"] = None
            else:
                row["summary"] = _summary(left, right)
            rows_out.append(row)
        blocks.append(
            {
                "configuration": config.name,
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
    architecture (the user, 2026-09-28: *"If it is the experiment harness, it
    should not add model evaluations"*), and phase A's census already stops
    before it.  Phase B's ``per_node_counted`` includes it: the audit is one
    sweep of the complete node set, so it adds exactly 1 to every node.  That
    premise is checked on the record, never assumed — ``audit_node_calls``
    must equal the number of nodes counted — and the run is refused otherwise.
    The output path (MDA_Output in ``BR``/``B0``, the deferred nodes' one
    execution in ``B2``) is architecture and stays in.
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
            a: {
                s: stats_mod.module_sweeps(_without_exit_audit(r), groups)
                for s, r in runs_of(a)
            }
            for a in by_arm
        }
        measured = {
            a: {
                s: stats_mod.module_sweeps(
                    stats_mod.per_node_census(r, phase=tally_b.PHASE), groups
                )
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
            out["summary"] = (
                None if any(v is None for v in left + right) else _summary(left, right)
            )
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


def optimiser_evaluations(campaign: Campaign) -> list[dict[str, Any]]:
    """How the optimiser's model evaluations decompose, per configuration and arm.

    From the code, not assumed: every point VMCON evaluates (pyvmcon's
    ``problem(x)``, PROCESS's ``VmconProblem.__call__``) runs one function
    evaluation and one central-difference gradient — ``2·nvar`` perturbed
    evaluations and one reconcile call (``evaluators.fcnvmc2``) — so
    ``k = 2·nvar + 2`` model evaluations per point.  An iteration evaluates its
    iterate and, unless it converges, its line-search point(s).  So a run of
    ``it`` iterations whose every line search accepts its first trial makes
    ``2·it − 1`` point evaluations and ``ε = (2·it − 1)·k`` model evaluations;
    each further line-search trial adds one point.  Checked here on every run
    of the seed set, not assumed.

    The accepted line-search point is the next iterate, and the next iteration
    evaluates it again (pyvmcon 2.4.2: ``result = problem(x)`` at the loop's
    head; the line search's result is used only for the Hessian update).  The
    **re-evaluated** share is ``Σ (it − 1)·k / Σ ε`` — one repeat per line
    search, and the final iteration has none.  Both are stated over the runs
    the optimiser solved in **one attempt**: an attempt that failed may have
    ended at an iteration's head or after its line search, so its point count
    is not determined by its iteration count, and the retried runs are counted
    and set aside rather than attributed.
    """
    rows: list[dict[str, Any]] = []
    for configuration, by_arm, converged in _phase_b_groups(campaign):
        for a in sorted(by_arm, key=lambda x: tally_b.LADDER.index(x) if x in tally_b.LADDER else 99):
            runs = [
                by_arm[a][s]
                for s in converged
                if s in by_arm[a] and stats_mod.finished(by_arm[a][s])
            ]
            nvars = sorted({len((r.get("mfile") or {}).get("itvars") or {}) for r in runs})
            if len(nvars) != 1 or not nvars[0]:
                raise PaperTablesError(
                    f"{configuration} {a}: iteration-variable counts {nvars} over "
                    f"the seed set; one k per arm is presumed"
                )
            k = 2 * nvars[0] + 2
            exact = extra = divisible = retried = 0
            repeated = total = 0.0
            for r in runs:
                eps = stats_mod.n_evaluations(r)
                it = stats_mod.iterations_summed_over_attempts(r)
                attempts = stats_mod.n_attempts(r)
                if eps is None or it is None or not attempts:
                    raise PaperTablesError(
                        f"{stats_mod._label(r)}: evaluations {eps}, iterations "
                        f"{it}, attempts {attempts}; the decomposition is refused"
                    )
                divisible += eps % k == 0
                if attempts != 1:
                    retried += 1
                    continue
                if eps % k == 0:
                    trials = eps // k - (2 * it - 1)
                    exact += trials == 0
                    extra += max(trials, 0)
                repeated += (it - 1) * k
                total += eps
            rows.append(
                {
                    "configuration": configuration,
                    "arm": a,
                    "n": len(runs),
                    "nvar": nvars[0],
                    "fd_per_gradient": 2 * nvars[0],
                    "per_point": k,
                    "divisible": divisible,
                    "retried": retried,
                    "exact": exact,
                    "extra_trials": extra,
                    "iterations": _mean([stats_mod.iterations_summed_over_attempts(r) for r in runs]),
                    "evaluations": _mean([stats_mod.n_evaluations(r) for r in runs]),
                    "fd_share": (2 * nvars[0]) / k,
                    "repeated_share": repeated / total if total else None,
                }
            )
    return rows


#: The collapsed DSM's rows per configuration (the dependency-analysis
#: study's exports, imported by ``fixedpoint/gen_function_counts.py``).
DSM_ROWS_FILE = "dsm_function_counts.json"

#: The constraint rows, not counted among the models (the user, 2026-09-29).
#: One row in the older exports, two after the dependency-analysis study split
#: it (its M125, 2026-09-17), which only the tok export postdates.
CONSTRAINT_ROWS = frozenset({"Constraints", "ConsistencyConstraints", "EngineeringConstraints"})


def cases(
    campaign: Campaign, optimisation: Mapping[str, Mapping[str, Any]]
) -> list[dict[str, Any]]:
    """How the three configurations differ: objective, design variables,
    constraints, the cross-module coupling (the burn time) and the number of
    models (the collapsed DSM's model rows, drivers and constraints excluded).

    The objective, the variable and constraint counts and ``pulsed`` are the
    report's problem-definition table, read from the ``tally_optimisation``
    stage record and not recomputed.  Derived here: the objective's variable,
    the field the configuration's committed per-run artifact names as the
    objective (``seeds.detail.objective``); and the cross-module coupling's
    variable, the one iteration-variable name every lifted run (``B2``)
    carries and no flat run (``B0``) does.  Refused where the runs disagree.
    """
    table = _stage_table(optimisation, f"problem definition — {PHASE_B_SOURCE}")
    by_config = {r["configuration"]: r for r in table["rows"]}
    dsm_rows = json.loads((Path(campaign.data_dir) / DSM_ROWS_FILE).read_text())
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
                raise PaperTablesError(
                    f"{configuration}: the lift adds {sorted(lifted)}, not one variable"
                )
        artifacts = sorted(
            {
                Path(str(r.get("per_run_artifact"))).name
                for arm in by_arm
                for r in by_arm[arm].values()
                if r.get("per_run_artifact")
                and not str(r.get("per_run_artifact")).count("lifted")
            }
        )
        if len(artifacts) != 1:
            raise PaperTablesError(f"{configuration}: per-run artifacts {artifacts}; one expected")
        seeds = json.loads((Path(campaign.data_dir) / artifacts[0]).read_text())["seeds"]
        seeds = ast.literal_eval(seeds) if isinstance(seeds, str) else seeds
        objective_fields = [str(f) for f in seeds["detail"]["objective"]]
        if len(objective_fields) != 1:
            raise PaperTablesError(
                f"{configuration}: the objective reads {objective_fields}; one field expected"
            )
        # the models: the configuration's rows of the collapsed DSM less the
        # top-level driver rows and the constraint rows, from the committed
        # per-configuration counts
        dsm = (dsm_rows.get("configurations") or {}).get(configuration)
        if dsm is None:
            raise PaperTablesError(
                f"{configuration}: {DSM_ROWS_FILE} has no DSM rows for it; the number "
                f"of models would be guessed"
            )
        row["models"] = sum(
            1 for r in dsm["rows"] if r["kind"] == "model" and r["model"] not in CONSTRAINT_ROWS
        )
        row["objective_variable"] = objective_fields[0].split(".")[-1]
        row["lifted_variable"] = next(iter(lifted)) if lifted else None
        row["pulsed_bool"] = pulsed
        out.append(row)
    return out


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
        raise PaperTablesError(
            f"{len(found)} stage table(s) named {prefix!r}…; expected exactly one"
        )
    return found[0]


def cross_check(
    built: Mapping[str, Any],
    evaluation: Mapping[str, Mapping[str, Any]],
    optimisation: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Every cell the stage records also hold, compared exactly.

    Phase A: each single-group row's per-arm mean against the report's
    Table 9 (``module sweeps per run — <configuration> — campaign_displaced``)
    — its ratio is against ``A1`` on a pulsed configuration and is compared
    only where the stage's reference is ``A0``.  Phase B: the iteration row's
    arm means, pooled ratio, median, bracket and n against Table 12; each
    single-group module row's arm means, pooled ratio, median, bracket and
    pair count against Table 17.  Floats are compared with ``==``.
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
                same(f"A {c} {row['row']} {a} mean", row[f"{a}_measured"], theirs.get(f"{a}_mean"))
            charged = stats_mod.ONCE_PER_RUN_GROUP in row["groups"]
            if theirs.get("reference") == PHASE_A_PAIR[0] and row["summary"] and not charged:
                same(f"A {c} {row['row']} pooled", row["summary"]["pooled"], theirs.get("ratio"))
                same(f"A {c} {row['row']} pairs", row["summary"]["n"] + row["summary"]["n_dropped"], theirs.get("n_pairs"))

    path = _stage_table(optimisation, f"the optimiser's path over the configurations — {PHASE_B_SOURCE}")
    by_config = {
        r["configuration"]: r for r in path["rows"] if r["quantity"] == ITERATIONS_LABEL
    }
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
        table = _stage_table(
            optimisation, f"module sweeps per run — {c} — {PHASE_B_SOURCE} ·"
        )
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
    for phase, key in (("phase_a", "A2_measured"), ("phase_b_iterations", "B2"), ("phase_b_modules", "B2_measured")):
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
#: themselves are exact.  Standard errors from the records: phase A sweep means
#: 0.07–0.10; phase B iterations 0.1 on tok, 4–10 elsewhere; phase B module
#: sweeps 20–40 on tok, 500–2700 elsewhere; pooled ratios 0.01–0.25.  So phase A
#: means and iterations to one decimal, every ratio, median and bracket to two
#: decimals.  Phase B module sweeps are printed as integers (the user,
#: 2026-09-28: *"It is too complicated. just round to integers"*) — more digits
#: than their uncertainty supports, but none of them a false zero.  The comparison with
#: the stage records reads the raw values.
RATIO_DECIMALS = 2
MEAN_DECIMALS = 1
SWEEP_FIGURES = 2


def decimals(value: Any, places: int) -> str:
    """*value* to *places* decimals: ``0.7246 → 0.72``, ``5.52 → 5.5``."""
    if value is None:
        return "—"
    return f"{float(value):.{places}f}"


def figures(value: Any, significant: int = SWEEP_FIGURES) -> str:
    """*value* to *significant* figures, never scientific notation, trailing
    zeros kept: ``1977.23 → 2000``, ``640 → 640``, ``1 → 1.0``, ``0 → 0``."""
    if value is None:
        return "—"
    number = float(value)
    if number == 0:
        return "0"
    exponent = math.floor(math.log10(abs(number)))
    rounded = round(number, significant - 1 - exponent)
    # rounding can carry into the next decade (0.996 → 1.0)
    exponent = math.floor(math.log10(abs(rounded)))
    return f"{rounded:.{max(0, significant - 1 - exponent)}f}"


def sig(value: Any) -> str:
    """A ratio, median or bracket end: :data:`RATIO_DECIMALS` decimals."""
    return decimals(value, RATIO_DECIMALS)


def mean_1dp(value: Any) -> str:
    return decimals(value, MEAN_DECIMALS)


def _ratio(value: Any) -> str:
    return sig(value)


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
    return text.replace("—", "--")


def _module_lines(
    blocks: Sequence[Mapping[str, Any]], ladder: Sequence[str], pair: tuple[str, str], n_of, mean,

) -> tuple[list[str], list[str]]:
    ratio_head = f"{pair[1]}/{pair[0]}"
    arm_heads = list(ladder)
    md: list[str] = []
    tex: list[str] = []
    for block in blocks:
        c = block["configuration"]
        md += [
            f"**`{SHORT.get(c, c)}`** ({c}, n = {n_of(block)})",
            "",
            f"| Module | {' | '.join(arm_heads)} | {ratio_head} | {ratio_head} med [min, max] |",
            "|---|" + "---:|" * len(ladder) + "---:|---:|",
        ]
        tex += [
            f"\\multicolumn{{{len(ladder) + 3}}}{{l}}{{\\texttt{{{SHORT.get(c, c)}}} ($n = {n_of(block)}$)}} \\\\",
            "\\hline",
        ]
        for row in block["rows"]:
            cells = [
                str(row[f"{a}_exact"]) if f"{a}_exact" in row else mean(row[a]) for a in ladder
            ]
            tex_cells = cells
            s = row["summary"]
            md_label = tex_label = row["row"]
            md.append(
                f"| {md_label} | {' | '.join(cells)} | {_ratio(s and s['pooled'])} | {_median_bracket(s)} |"
            )
            tex.append(
                _tex(
                    f"{tex_label:<15} & {' & '.join(tex_cells)} & {_ratio(s and s['pooled'])} & {_median_bracket(s)} \\\\"
                )
            )
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

        # the name without its symbol ("Plasma major radius (R₀)" → "plasma major
        # radius"): the variable name beside it is the precise statement
        name_of = str(r["objective"]).split(" (")[0]
        # "major radius" alone: the tokamak's only major radius is the plasma's (the user)
        name_of = OBJECTIVE_SHORTER.get(name_of, name_of)
        sense = {"minimise": "min.", "maximise": "max."}[str(r["sense"])]
        objective = f"{sense} {name_of[:1].lower()}{name_of[1:]} ({code(r['objective_variable'])})"
        variables = f"{r['nvar']} → {r['nvar_lifted']}" if r["nvar"] != r["nvar_lifted"] else str(r["nvar"])
        # the total alone: the stage cell reads "total (eq / ineq)"
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


def _tabular(kind: str, rows: Sequence[str]) -> list[str]:
    """The rows inside the paper's ``tabular``, with its column spec and header.

    The column specs are the paper's own (``3 results.tex``); the phase B
    module header carries the ×10² unit its cells are printed in.
    """
    spec, header = {
        "A": ("l|rrrr|rc", "Module & AR & A0 & A1 & A2 & A2/A0 & A2/A0 med [min, max]"),
        "I": (
            "l|rrrr|rc",
            "Configuration & BR & B0 & B1 & B2 & B2/B0 & B2/B0 med [min, max]",
        ),
        "B": (
            "l|cccc|cc",
            "Module & BR & B0 & B1 & B2 & B2/B0 & B2/B0 med [min, max]",
        ),
    }[kind]
    body = list(rows)
    if kind == "I":
        body = [*body, "\\hline"]
    return [
        f"\\begin{{tabular}}{{{spec}}}",
        "\\hline",
        f"{header} \\\\",
        "\\hline",
        *body,
        "\\end{tabular}",
    ]


def render(campaign: Campaign, records_dir: Path) -> dict[str, Any]:
    """The page, and the comparison it was written under."""
    a = phase_a(campaign)
    iterations, modules = phase_b(campaign)
    built = {"phase_a": a, "phase_b_iterations": iterations, "phase_b_modules": modules}
    evaluation = _stage_tables(records_dir, "tally_evaluation")
    case_rows = cases(campaign, _stage_tables(records_dir, "tally_optimisation"))
    optimisation = _stage_tables(records_dir, "tally_optimisation")
    check = cross_check(built, evaluation, optimisation)
    tooth = _cross_check_tooth(built, evaluation, optimisation)

    from harness.measurement import plan_tables as plan_tables_mod  # noqa: PLC0415

    marker = plan_tables_mod.population_marker(campaign, records_dir)
    commits = ", ".join(f"`{h[:8]}`" for h in marker["records_by_commit"]) or "—"

    lines = [
        "# Paper tables — Case 2: PROCESS",
        "",
        "> **Document status** — **GENERATED, never hand-edited.** Written whole by "
        "`harness/measurement/paper_tables.py` (`experiment_runner.py --paper-tables write`) "
        "from the campaign's run records, and compared whole by `--paper-tables check`. "
        "It fills the three tables of `Structuring-fusion-MDAO-with-DSMs/3 results.tex` "
        "(`tab:phaseA_results`, `tab:phaseB_iterations`, `tab:phaseB_results`); each table "
        "is given as a Markdown grid and as LaTeX rows for the paper's `tabular` body.",
        "",
        f"*Over the **campaign** population — {marker['n_run_records']} run records at "
        f"{commits}; sources `{PHASE_A_SOURCE}` (phase A) and `{PHASE_B_SOURCE}` (phase B).*",
        "",
        "**Conventions (the user, 2026-09-28).** A module cell is that module's **sweeps per "
        "run** — per `call_models` evaluation in phase A, per whole optimisation in phase B — "
        "averaged over the arm's n perturbed runs. Every model node of a module runs once per "
        "sweep, so a sweep ratio does not depend on whether one counts model calls or DSM rows. "
        "The ratio column is the **ratio of the means** (Σ intervened / Σ control over the "
        "paired runs); the next column is the per-run ratio's median with its [min, max]. "
        "**Feedforward** is the pulse node (run once per evaluation after M3, no iteration); "
        "**Post-processing** is the once-per-run set — nodes no objective or constraint "
        "depends on, which the partitioned arm runs once, after convergence, in the output "
        "pass. **Phase A charges `A2` that one execution** (1 in its Post-processing "
        "cell): the flat arms' final sweep already computes those outputs at the converged "
        "state, and without it `A2`'s evaluation would not produce the same information. "
        "The charge is by construction — phase A's census stops before the output pass, and "
        "`A2`'s measured count there is 0 on every run, which is checked; phase B's census "
        "measures the pass (`B2`'s Post-processing reads 1 per run once the exit audit is "
        "taken out). "
        "There is **no total row**: sweeps of different modules do not add. "
        "Rounding follows each quantity's sampling uncertainty over the starts (the counts "
        "themselves are exact): phase A sweep means and phase B iteration means to one "
        "decimal, phase B module sweeps to integers, every ratio, median and bracket to two "
        "decimals; `A2`'s phase A Feedforward and Post-processing cells are the integer 1 "
        "every run reads (checked), not a mean. `med` in a column head is the median. "
        "`—` is a group that does not exist on the configuration or an arm that is inactive "
        "there (`A1`/`B1` on `st`).",
        "",
        "Node groups per configuration (phase A; phase B's are restated in its section "
        "only where they differ):",
        "",
        *_groups_note(a),
        "",
        f"**Comparison with the stage records.** {check['compared']} cells these tables share "
        f"with the report's Tables 9, 12 and 17 (the stage records under the records "
        f"directory) compared exactly — `A2`'s phase A Post-processing mean before the charge "
        f"and phase B's module means before the exit audit is taken out; phase B's module "
        f"ratios have no stage counterpart once it is: **{check['mismatched']} mismatched of "
        f"{check['compared']}**; the comparison caught a doctored cell on each of the three "
        f"sides: **{'yes' if tooth else 'NO'}**. The phase A ratio against `A0` and its "
        f"per-run distribution have no stage counterpart on the pulsed configurations (the "
        f"report's reference there is `A1`).",
        "",
        "## Table — how the three configurations differ",
        "",
        "One row per configuration. Objective, design variables and constraints are the "
        "report's problem-definition table (the runs' own stamps); `a → b` is the flat arms "
        "(`BR`, `B0`) → the arms with the burn time taken out of the MDA (`B1`, `B2`), which add "
        "the burn time as an iteration variable and its consistency constraint. The objective's "
        "variable and the cross-module coupling's variable are derived from the committed "
        "per-run artifact and the runs. Models is the number of model rows of the "
        "configuration's collapsed DSM, its top-level driver rows and its constraint "
        "rows excluded (`harness/data/dsm_function_counts.json`).",
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
        "## Table `tab:phaseA_results` — phase A, module sweeps per evaluation",
        "",
        "Mean sweeps of each module in one `call_models` evaluation over the n displaced-entry "
        "runs per arm; `A2/A0` is the ratio of the means over the runs both arms finished.",
        "",
    ]
    md, tex = _module_lines(a, tally_a.LADDER, PHASE_A_PAIR, lambda b: _n_text(b["n_per_arm"]), mean_1dp)
    lines += md + ["```latex", *_tabular("A", tex), "```", ""]

    lines += [
        "## Table `tab:phaseB_iterations` — phase B, optimiser iterations",
        "",
        "Mean optimiser iterations per run, summed over the optimiser's retry attempts, over "
        "the n seeds on which every arm reached an accepted optimum; `B2/B0` is the ratio of "
        "the means. The same statistic as the report's Table 12.",
        "",
        "| Configuration | n | BR | B0 | B1 | B2 | B2/B0 | B2/B0 med [min, max] |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    tex = []
    for row in iterations:
        c = row["configuration"]
        cells = [mean_1dp(row[x]) for x in tally_b.LADDER]
        s = row["summary"]
        lines.append(
            f"| `{SHORT.get(c, c)}` | {row['n']} | {' | '.join(cells)} | {_ratio(s['pooled'])} | {_median_bracket(s)} |"
        )
        tex.append(
            _tex(
                f"\\texttt{{{SHORT.get(c, c)}}} ($n = {row['n']}$) & {' & '.join(cells)} & "
                f"{_ratio(s['pooled'])} & {_median_bracket(s)} \\\\"
            )
        )
    lines += ["", "```latex", *_tabular("I", tex), "```", ""]

    lines += [
        "## Table `tab:phaseB_results` — phase B, module sweeps per optimisation",
        "",
        "Mean sweeps of each module over one whole optimisation, rounded to integers (more "
        "digits than the seed-to-seed uncertainty supports). Every attempt and the output "
        "path, which is architecture (MDA_Output's sweeps in `BR`/`B0`, none in `B1`, the "
        "deferred nodes' one execution in `B2`). The exit audit's one sweep of every node is "
        "the harness's accuracy instrument and is **subtracted** (1 per node, checked on each "
        "run against the record's `audit_node_calls`); the report's Table 17 includes it. "
        "Over the n seeds on which every arm reached an accepted optimum; "
        "`B2/B0` is the ratio of the means. The paper prints `tok`; all three are given.",
        "",
    ]
    if any(b["groups"] != x["groups"] for b, x in zip(modules, a)):
        lines += ["Node groups (phase B):", "", *_groups_note(modules), ""]
    md, tex = _module_lines(
        modules, tally_b.LADDER, PHASE_B_PAIR, lambda b: b["n"], lambda v: decimals(v, 0)
    )
    lines += md + ["```latex", *_tabular("B", tex), "```", ""]

    evaluations = optimiser_evaluations(campaign)
    lines += [
        "## How the optimiser's evaluations decompose (phase B)",
        "",
        "Every point VMCON evaluates costs `k = 2·nvar + 2` model evaluations: one function "
        "evaluation, a central-difference gradient (`2·nvar`) and one reconcile call. An "
        "iteration evaluates its iterate and its line-search point, so a run of `it` "
        "iterations whose line searches accept their first trial makes `ε = (2·it − 1)·k`. "
        "*exact* counts the runs on which that holds with no further trial; *repeated* is the "
        "share of all evaluations spent re-evaluating an accepted line-search point at the "
        "next iteration's head, `Σ (it − 1)·k / Σ ε`. Over the phase B seed set; *exact*, "
        "the extra trials and *repeated* are over the runs solved in one attempt (a failed "
        "attempt may end before or after its line search), the retried runs counted apart.",
        "",
        "| Configuration | arm | n | nvar | FD calls per gradient | evaluations per point k | "
        "mean iterations | mean ε | ε divisible by k | retried runs | exact | extra line-search "
        "trials | FD share | repeated share |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in evaluations:
        c = row["configuration"]
        lines.append(
            f"| `{SHORT.get(c, c)}` | {row['arm']} | {row['n']} | {row['nvar']} | "
            f"{row['fd_per_gradient']} | {row['per_point']} | {mean_1dp(row['iterations'])} | "
            f"{figures(row['evaluations'])} | {row['divisible']}/{row['n']} | {row['retried']} | "
            f"{row['exact']}/{row['n'] - row['retried']} | {row['extra_trials']} | {sig(row['fd_share'])} | "
            f"{sig(row['repeated_share'])} |"
        )
    lines.append("")

    return {
        "markdown": "\n".join(lines),
        "cross_check": check,
        "tooth": tooth,
        "built": built,
    }


def paper_path(campaign: Campaign) -> Path:
    """Beside ``EXPERIMENT_REPORT.md`` — the experiment folder, whatever runs dir is read."""
    return Path(__file__).resolve().parents[2] / PAPER_NAME


def _refuse_on_mismatch(result: Mapping[str, Any]) -> None:
    check = result["cross_check"]
    if check["mismatched"] or not result["tooth"]:
        raise PaperTablesError(
            f"the comparison with the stage records failed: {check['mismatched']} "
            f"of {check['compared']} mismatched, tooth "
            f"{'bites' if result['tooth'] else 'DOES NOT BITE'}; first: "
            f"{check['mismatches'][:3]}"
        )


def write(campaign: Campaign, records_dir: Path) -> dict[str, Any]:
    result = render(campaign, records_dir)
    _refuse_on_mismatch(result)
    path = paper_path(campaign)
    path.write_text(result["markdown"] + "\n")
    return {**result, "path": str(path), "written": True}


def check(campaign: Campaign, records_dir: Path) -> dict[str, Any]:
    result = render(campaign, records_dir)
    path = paper_path(campaign)
    committed = path.read_text() if path.exists() else ""
    return {
        **result,
        "path": str(path),
        "identical": committed == result["markdown"] + "\n",
    }


def report(result: Mapping[str, Any]) -> None:
    check_ = result["cross_check"]
    print(
        f"  cross-check with the stage records: {check_['mismatched']} mismatched "
        f"of {check_['compared']} compared; tooth "
        f"{'bites' if result['tooth'] else 'DOES NOT BITE'}"
    )
    for line in check_["mismatches"][:10]:
        print(f"    {line}")
    if "identical" in result:
        print(f"  {result['path']}: {'IDENTICAL' if result['identical'] else 'DIFFERS'}")
    if result.get("written"):
        print(f"  written: {result['path']}")
