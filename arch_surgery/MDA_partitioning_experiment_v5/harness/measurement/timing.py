"""The wall-clock instrument's stages, and the three appendix tables (V5 plan §6).

Driver change DR12 (task A101 (v5-timers-and-once); V5 list item 9; decisions
D33 and D38): observation-only timers in the driver copy, switched by
``PROCESS_ARCH_TIMERS=on``, harvested into every record under ``timers``
(the driver's accumulators, the harness's excluded costs and the epochs) and
``launcher`` (the pool's independent wall and load average).  **Context,
never evidence** (D33; CLAUDE.md): no verdict reads a number from here.

What one record's timers become — **the rows** (seconds; per evaluation in
the evaluation phase, per whole optimisation in the optimisation phase):

* per module — ``M1``, ``M2``, ``M3``, ``Feedforward`` (the pulse node and
  the feed-forward tail), ``Post-processing`` (the once-per-run set): the
  models' own wall, summed over the group's nodes through the committed node
  map (the same grouping the count tables use, ``tally_evaluation.node_grouping``);
* ``MDA convergence test`` — the coupling-state read, bind and residual of
  the block loops, plus upstream's own objective-and-constraints comparison
  in the reference arms (the two are kept apart in the record);
* ``dispatch`` — the sweep bodies less their nodes: the design-vector
  injection, the switch dispatch and the counters;
* ``objective and constraints`` — the layer upstream's idempotence predicate
  compares;
* ``optimiser own time`` — the solve-phase wall less every evaluation
  (optimisation phase; by construction 0 in the evaluation phase);
* ``fixed per run`` — process start to the first evaluation less the
  harness's own set-up, the once-per-run resolution inside the first
  evaluation (DR9's schedule, the artifacts' first load), and the run's tail
  after the solve less the output path's own sweeps (which the module rows
  hold, as the count tables hold their sweeps);
* ``unattributed residual`` — what is left of the total after the rows;
* ``Total`` — the evaluation's measured wall (evaluation phase), or the
  launcher's wall less the harness-only costs (optimisation phase).

**Excluded and named**: the exit-audit sweep, the state snapshots, the
record assembly and the harness's set-up before the run — each a number in
the record (``timers.excluded``), so the exclusion is measured rather than
asserted.

**The stages** (``experiment_runner.py --timing <stage>``):

* ``repeatability`` — the gate job set (both phases, every arm, one seed per
  configuration: gate GC's set) three times at **W = 1** (D38), timers on;
  a job whose repetitions differ in any count is refused; per row the median
  and ``[min, max]`` over the repetitions (A91's form);
* ``timers-off`` — the same job set once with the timers unset at W = 1: the
  instrument's own cost, read as the difference of the launcher's wall;
* ``validity`` — D38's check: the campaign's timing of the same seeds must
  lie within the repetitions' range; where it does not, the appendix's
  timings come from a one-worker timing pass and the stage record says so;
* ``tables`` — the three appendix tables rendered over the repeatability
  records as **test data** (never the paper's document, which
  ``paper_tables.py`` renders over the campaign through the same functions).

Every record these stages make is ``run_kind == "timing"`` under
``runs/timing/`` and is never pooled with the campaign or the gates.
"""

from __future__ import annotations

import dataclasses
import json
import os
from pathlib import Path
from typing import Any, Mapping, Sequence

from ..core import framework
from ..core import pool as pool_mod
from ..core import records as records_mod
from ..core.config import Campaign, Config
from ..core.framework import GateError
from ..experiment import arms as arms_mod
from . import stats as stats_mod

RUNS_SUBPATH = Path("timing")
RUN_KIND = "timing"
STAGES: tuple[str, ...] = ("repeatability", "timers-off", "validity", "tables")

#: The repetition index travels in the job identity through a variable the
#: driver never reads (gate GC's label mechanism), so three repetitions are
#: three jobs with three directories.
REPETITION_VARIABLE = "HARNESS_TIMING_REPETITION"
REPETITIONS = 3

#: The seeds of the gate job set: gate GC's (one declaration, imported).
from ..gates.gate_count_neutrality import EVALUATION_SEED, OPTIMISATION_SEED  # noqa: E402

#: The counts every repetition of a job must agree on, or the job is refused.
COUNT_FIELDS: tuple[str, ...] = (
    "status",
    "node_calls_total",
    "node_calls_single_eval",
    "node_calls_solve_phase",
    "dispatch_sweeps",
    "n_model_calls_sweeps",
    "sweeps_per_eval.n_evaluations",
    "n_solver_iterations",
    "exact.norm_objf",
    "exact.objf",
    "exit_audit.frozen.residual_max_hex",
)

#: The table rows, in printing order, per phase.
MODULE_ROWS: tuple[str, ...] = ("M1", "M2", "M3", "Feedforward", "Post-processing")
PHASE_A_ROWS: tuple[str, ...] = (
    *MODULE_ROWS,
    "MDA convergence test",
    "dispatch",
    "objective and constraints",
    "unattributed residual",
    "Total",
)
PHASE_B_ROWS: tuple[str, ...] = (
    *MODULE_ROWS,
    "MDA convergence test",
    "dispatch",
    "objective and constraints",
    "optimiser own time",
    "fixed per run",
    "unattributed residual",
    "Total",
)
BREAKDOWN_ROWS: tuple[str, ...] = (
    "model evaluation (the modules summed)",
    "MDA overhead per sweep: convergence test",
    "MDA overhead per sweep: dispatch",
    "optimiser overhead per iteration",
    "fixed per run",
    "Total",
)

#: How the node map's groups fold into the paper's module rows.
GROUP_TO_ROW: dict[str, str] = {
    "M1": "M1",
    "M2": "M2",
    "M3": "M3",
    "PULSE": "Feedforward",
    "FF": "Feedforward",
    stats_mod.ONCE_PER_RUN_GROUP: "Post-processing",
}

#: The pair of arms each phase's ratio columns are on (D34 for phase A).
PHASE_B_PAIR: tuple[str, str] = ("B0", "B2")


def _at(record: Mapping[str, Any], path: str) -> Any:
    return records_mod.resolve_path(record, path) if records_mod.has_path(record, path) else None


# --------------------------------------------------------------------------
# the job set
# --------------------------------------------------------------------------


def timing_root(campaign: Campaign, stage: str) -> Path:
    return Path(campaign.runs_dir) / RUNS_SUBPATH / stage


def one_worker(campaign: Campaign, *, timers: bool) -> Campaign:
    """The campaign at **W = 1** (D38) with the timers composed as asked."""
    return dataclasses.replace(campaign, workers=1, timers=timers)


def job_set(
    campaign: Campaign, references: Mapping[str, Any], *, stage: str, repetition: int
) -> list[tuple[str, str, str, pool_mod.Job]]:
    """``(phase, configuration, arm, job)`` per active arm of both phases:
    the evaluation phase from the displaced entry at gate GC's seed, the
    optimisation phase from GC's start; every record ``timing``, in a named
    directory under ``runs/timing/<stage>/``."""
    from ..gates import reproduction as reproduction_mod  # noqa: PLC0415

    root = timing_root(campaign, stage)
    plan: list[tuple[str, str, str, pool_mod.Job]] = []
    label = {REPETITION_VARIABLE: str(repetition)}
    for config in campaign.configurations:
        reference = references[config.name]
        for arm in arms_mod.active_arms(config, "A"):
            plan.append(
                (
                    "A",
                    config.name,
                    arm,
                    pool_mod.Job(
                        phase="A",
                        arm=arm,
                        config=config,
                        seed=EVALUATION_SEED,
                        outdir=root / config.name / f"A_{arm}" / f"rep{repetition}",
                        regime="perturbed",
                        delta=campaign.delta,
                        pin_hex=reproduction_mod.entry_pin(
                            config, arm, reference, seed=EVALUATION_SEED, delta=campaign.delta
                        ),
                        entry_state=Path(reference["snapshot"]),
                        run_kind=RUN_KIND,
                        timers=campaign.timers,
                        override_env=label,
                    ),
                )
            )
        for arm in arms_mod.active_arms(config, "B"):
            plan.append(
                (
                    "B",
                    config.name,
                    arm,
                    pool_mod.Job(
                        phase="B",
                        arm=arm,
                        config=config,
                        seed=OPTIMISATION_SEED,
                        outdir=root / config.name / f"B_{arm}" / f"rep{repetition}",
                        regime="unperturbed",
                        delta=None,
                        run_kind=RUN_KIND,
                        timers=campaign.timers,
                        override_env=label,
                    ),
                )
            )
    return plan


# --------------------------------------------------------------------------
# one record -> its rows
# --------------------------------------------------------------------------


def _sum(mapping: Mapping[str, Any] | None, keys: Sequence[str] | None = None) -> float:
    if not isinstance(mapping, Mapping):
        return 0.0
    if keys is None:
        return float(sum(float(v) for v in mapping.values()))
    return float(sum(float(mapping.get(k, 0.0) or 0.0) for k in keys))


def rows_of(
    record: Mapping[str, Any], groups: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    """One record's timing rows, in seconds, from its ``timers`` and ``launcher``
    blocks.  Refuses a record that carries no timers.  ``groups`` is the node
    grouping the count tables use for the record's configuration and phase."""
    timers = record.get("timers")
    launcher = record.get("launcher") or {}
    if not isinstance(timers, Mapping) or not timers.get("enabled"):
        raise GateError(
            f"{stats_mod._label(record)} carries no timers (PROCESS_ARCH_TIMERS "
            f"unset when it was made); a timing row over it would be a number "
            f"nobody measured"
        )
    driver = timers.get("driver") or {}
    excluded = timers.get("excluded") or {}
    epochs = timers.get("epochs") or {}
    phase = record.get("campaign_phase")
    node_s = driver.get("node_s") or {}
    tail_s = driver.get("tail_node_s") or {}
    modules: dict[str, float] = {row: 0.0 for row in MODULE_ROWS}
    grouped_nodes: set[str] = set()
    for group in groups:
        row = GROUP_TO_ROW.get(str(group["group"]))
        if row is None:
            raise GateError(f"node group {group['group']!r} folds into no table row")
        for node in group["nodes"]:
            grouped_nodes.add(str(node))
            modules[row] += float(node_s.get(node, 0.0) or 0.0) + float(tail_s.get(node, 0.0) or 0.0)
    ungrouped = sorted((set(node_s) | set(tail_s)) - grouped_nodes)
    ungrouped_s = _sum(node_s, ungrouped) + _sum(tail_s, ungrouped)
    model_in_sweeps = _sum(node_s)
    sweep_s = float(driver.get("sweep_s") or 0.0)
    dispatch = sweep_s - model_in_sweeps
    test = (
        float(driver.get("test_read_s") or 0.0)
        + float(driver.get("test_bind_s") or 0.0)
        + float(driver.get("test_residual_s") or 0.0)
        + float(driver.get("upstream_test_s") or 0.0)
    )
    objective = float(driver.get("objective_s") or 0.0)
    run_setup = float(driver.get("run_setup_s") or 0.0)
    call_models_s = float(driver.get("call_models_s") or 0.0)
    n_call_models = int(driver.get("n_call_models") or 0)
    at_end = driver.get("at_solve_end") or {}
    solve_s = driver.get("solve_s")
    optimiser_own = (
        float(solve_s) - float(at_end.get("call_models_s") or driver.get("call_models_s") or 0.0)
        if solve_s is not None
        else 0.0
    )
    # the run's tail after the solve, less the output path's own sweeps and
    # objective evaluations (already in the module, dispatch and objective rows)
    post_solve_attributed = (
        (sweep_s - float(at_end.get("sweep_s") or sweep_s))
        + (_sum(tail_s) - float(at_end.get("tail_s") or _sum(tail_s)))
        + (objective - float(at_end.get("objective_s") or objective))
        + (test - float(at_end.get("test_s") or test))
    )
    spawned = launcher.get("spawned_at")
    first_call = driver.get("first_call_models_at")
    solve_ended = driver.get("solve_ended_at") or driver.get("last_call_models_ended_at")
    run_returned = epochs.get("run_returned_at")
    harness_before = float(excluded.get("harness_before_run_s") or 0.0)
    fixed = None
    if spawned is not None and first_call is not None and solve_ended is not None and run_returned is not None:
        fixed = (
            (float(first_call) - float(spawned) - harness_before)
            + (float(run_returned) - float(solve_ended) - post_solve_attributed)
            + run_setup
        )
    # the process's exit after the record is written -- the interpreter's
    # teardown, in the launcher's wall and in no driver timer -- measured
    # from the two epochs and named as an excluded cost
    process_exit_s = (
        float(launcher["returned_at"]) - float(epochs["record_written_at"])
        if launcher.get("returned_at") is not None and epochs.get("record_written_at") is not None
        else 0.0
    )
    excluded = {**excluded, "process_exit_s": process_exit_s}
    excluded_total = sum(float(v or 0.0) for k, v in excluded.items() if k.endswith("_s") and not k.startswith("exit_audit_driver"))
    launcher_wall = launcher.get("wall_s")
    rows: dict[str, float | None] = {**modules}
    rows["MDA convergence test"] = test
    rows["dispatch"] = dispatch
    rows["objective and constraints"] = objective
    if phase == "A":
        # per evaluation: the one MEASURED call_models is the whole evaluation
        # (the warmed form, A102: the discarded warm-up's timers are kept
        # apart under timers.warmup_driver and are in no row)
        total = call_models_s
        attributed = sum(modules.values()) + ungrouped_s + test + dispatch + objective + run_setup
        rows["unattributed residual"] = total - attributed
        rows["Total"] = total
        # The fixed per-run term of an evaluation record: process start to
        # the WARM-UP's first evaluation (where the numba cache load lands)
        # less the harness's set-up, plus the once-per-run set-up inside it.
        # Not a row of the phase A table (plan §6); stamped beside for the
        # report.  None on a record made by the cold child.
        warmup_driver = timers.get("warmup_driver") or {}
        warmup_first = epochs.get("warmup_first_call_models_at")
        if spawned is not None and warmup_first is not None:
            fixed = (
                float(warmup_first) - float(spawned) - harness_before
                + float(warmup_driver.get("run_setup_s") or 0.0)
            )
    else:
        total = (float(launcher_wall) - excluded_total) if launcher_wall is not None else None
        rows["optimiser own time"] = optimiser_own
        rows["fixed per run"] = fixed
        attributed = (
            sum(modules.values()) + ungrouped_s + test + dispatch + objective + optimiser_own
            + (fixed or 0.0)
        )
        rows["unattributed residual"] = (total - attributed) if (total is not None and fixed is not None) else None
        rows["Total"] = total
    return {
        "phase": phase,
        "rows": rows,
        "ungrouped_nodes": ungrouped,
        "ungrouped_s": ungrouped_s,
        "n_call_models": n_call_models,
        "n_evaluations": (1 if phase == "A" else _at(record, "sweeps_per_eval.n_evaluations")),
        "n_sweeps": int(driver.get("n_sweeps") or 0),
        "n_iterations": _at(record, "exit_forensics.n_solver_iterations_summed_over_attempts") or record.get("n_solver_iterations"),
        "call_models_s": call_models_s,
        "fixed_per_run_s": fixed,
        "run_setup_s": run_setup,
        "post_solve_attributed_s": post_solve_attributed,
        "launcher_wall_s": launcher_wall,
        "excluded_s": excluded_total,
        "excluded": dict(excluded),
        "loadavg": {"at_spawn": launcher.get("loadavg_at_spawn"), "at_return": launcher.get("loadavg_at_return")},
        "timers_off_wall_s": None,
    }


def breakdown_of(row_block: Mapping[str, Any]) -> dict[str, Any]:
    """The cost-breakdown table's rows for one optimisation record, from its rows."""
    rows = row_block["rows"]
    n_sweeps = max(int(row_block.get("n_sweeps") or 0), 1)
    n_iterations = max(int(row_block.get("n_iterations") or 0), 1)
    n_evaluations = max(int(row_block.get("n_evaluations") or 0), 1)
    total = rows.get("Total")
    model = sum(float(rows.get(m) or 0.0) for m in MODULE_ROWS)
    out = {
        "model evaluation (the modules summed)": {"s": model, "per": model / n_evaluations, "per_is": "ms per evaluation"},
        "MDA overhead per sweep: convergence test": {"s": rows.get("MDA convergence test"), "per": float(rows.get("MDA convergence test") or 0.0) / n_sweeps, "per_is": "ms per sweep"},
        "MDA overhead per sweep: dispatch": {"s": rows.get("dispatch"), "per": float(rows.get("dispatch") or 0.0) / n_sweeps, "per_is": "ms per sweep"},
        "optimiser overhead per iteration": {"s": rows.get("optimiser own time"), "per": float(rows.get("optimiser own time") or 0.0) / n_iterations, "per_is": "ms per iteration"},
        "fixed per run": {"s": rows.get("fixed per run"), "per": rows.get("fixed per run"), "per_is": "s per run"},
        "Total": {"s": total, "per": (float(total) / n_evaluations) if total is not None else None, "per_is": "ms per evaluation"},
    }
    for entry in out.values():
        entry["share"] = (float(entry["s"]) / float(total)) if (total and entry["s"] is not None) else None
    return out


# --------------------------------------------------------------------------
# summaries over records
# --------------------------------------------------------------------------


def _median_bracket(values: Sequence[float]) -> dict[str, Any]:
    clean = [float(v) for v in values if v is not None]
    bracket = stats_mod.seed_bracket(clean)
    return {
        "n": len(clean),
        "mean": (sum(clean) / len(clean)) if clean else None,
        "median": stats_mod.median(clean),
        "min": None if bracket is None else bracket[0],
        "max": None if bracket is None else bracket[1],
    }


def summarise_rows(blocks: Sequence[Mapping[str, Any]], row_names: Sequence[str]) -> dict[str, dict[str, Any]]:
    """Per row: mean, median and [min, max] over the records' rows."""
    return {
        name: _median_bracket([b["rows"].get(name) for b in blocks if b["rows"].get(name) is not None])
        for name in row_names
    }


def ratio_of(
    base: Mapping[int, Mapping[str, Any]], arm: Mapping[int, Mapping[str, Any]], row_names: Sequence[str]
) -> dict[str, dict[str, Any]]:
    """Per row: the ratio of the means and the per-key ratio's median with
    [min, max] over the keys both arms carry (stats.per_seed_ratio_summary)."""
    keys = sorted(set(base) & set(arm))
    out: dict[str, dict[str, Any]] = {}
    for name in row_names:
        left = [base[k]["rows"].get(name) for k in keys]
        right = [arm[k]["rows"].get(name) for k in keys]
        if not keys or any(v is None for v in left + right):
            out[name] = {"n": 0, "pooled": None, "median": None, "min": None, "max": None}
            continue
        out[name] = stats_mod.per_seed_ratio_summary([float(v) for v in left], [float(v) for v in right])
    return out


def _grouping(campaign: Campaign, configuration: str, records: Sequence[Mapping[str, Any]], phase: str):
    from . import tally_evaluation as tally_a  # noqa: PLC0415

    return tally_a.node_grouping(campaign, configuration, records, phase=phase)


def tables_over(
    campaign: Campaign,
    records: Sequence[Mapping[str, Any]],
    *,
    key_of,
) -> dict[str, Any]:
    """The three appendix tables' data over a population of timed records.

    ``key_of(record)`` is the pairing key (the seed, or the repetition).  Per
    configuration: the phase A table (ms per evaluation) over the evaluation
    records, the phase B table (s per optimisation) and the cost breakdown
    over the optimisation records; arms as columns with the mean, the ratio
    of the means on the phase's pair and the per-key median with [min, max].
    Records without timers are counted and named, never silently dropped.
    """
    from .paper_tables import phase_a_pair  # noqa: PLC0415

    out: dict[str, Any] = {"configurations": [], "n_records": len(records), "n_untimed": 0, "untimed": []}
    by_config: dict[str, dict[str, dict[str, dict[int, Any]]]] = {}
    for record in records:
        if record.get("status") != "ok":
            continue
        if not (record.get("timers") or {}).get("enabled"):
            out["n_untimed"] += 1
            out["untimed"].append(stats_mod._label(record))
            continue
        by_config.setdefault(str(record["campaign_configuration"]), {}).setdefault(
            str(record["campaign_phase"]), {}
        ).setdefault(str(record["campaign_arm"]), {})[key_of(record)] = record
    for config in campaign.configurations:
        phases = by_config.get(config.name) or {}
        block: dict[str, Any] = {"configuration": config.name, "phase_a": None, "phase_b": None, "breakdown": None}
        for phase, rows_of_phase, ladder, pair in (
            ("A", PHASE_A_ROWS, ("AR", "A0", "A1", "A2"), phase_a_pair(config.pulsed)),
            ("B", PHASE_B_ROWS, ("BR", "B0", "B1", "B2"), PHASE_B_PAIR),
        ):
            by_arm = phases.get(phase) or {}
            if not by_arm:
                continue
            every = [r for arm in by_arm.values() for r in arm.values()]
            groups = _grouping(campaign, config.name, every, phase)
            rowed = {arm: {k: rows_of(r, groups) for k, r in rows.items()} for arm, rows in by_arm.items()}
            columns = {
                arm: summarise_rows(list(rowed[arm].values()), rows_of_phase) if arm in rowed else None
                for arm in ladder
            }
            base, arm = pair
            ratios = ratio_of(rowed.get(base) or {}, rowed.get(arm) or {}, rows_of_phase) if base in rowed and arm in rowed else None
            table = {
                "rows": list(rows_of_phase),
                "unit": "ms per evaluation" if phase == "A" else "s per optimisation",
                "scale": 1000.0 if phase == "A" else 1.0,
                "arms": list(ladder),
                "n_per_arm": {a: len(rowed.get(a) or {}) for a in ladder},
                "pair": [base, arm],
                "n_pairs": len(set(rowed.get(base) or {}) & set(rowed.get(arm) or {})),
                "columns": columns,
                "ratio": ratios,
                "ungrouped_nodes": sorted({n for arm_rows in rowed.values() for b in arm_rows.values() for n in b["ungrouped_nodes"]}),
                "excluded_s_mean": {
                    a: _median_bracket([b["excluded_s"] for b in rowed[a].values()])["mean"] if a in rowed else None
                    for a in ladder
                },
            }
            block["phase_a" if phase == "A" else "phase_b"] = table
            if phase == "B":
                breakdown: dict[str, Any] = {"rows": list(BREAKDOWN_ROWS), "arms": list(ladder), "columns": {}}
                for a in ladder:
                    if a not in rowed:
                        breakdown["columns"][a] = None
                        continue
                    per_record = [breakdown_of(b) for b in rowed[a].values()]
                    breakdown["columns"][a] = {
                        name: {
                            "s": _median_bracket([p[name]["s"] for p in per_record]),
                            "per": _median_bracket([p[name]["per"] for p in per_record]),
                            "per_is": per_record[0][name]["per_is"] if per_record else None,
                            "share": _median_bracket([p[name]["share"] for p in per_record]),
                        }
                        for name in BREAKDOWN_ROWS
                    }
                block["breakdown"] = breakdown
        out["configurations"].append(block)
    return out


# --------------------------------------------------------------------------
# rendering
# --------------------------------------------------------------------------


def _fmt(value: Any, scale: float, places: int = 2) -> str:
    if value is None:
        return "—"
    return f"{float(value) * scale:.{places}f}"


def _fmt_ratio(summary: Mapping[str, Any] | None) -> tuple[str, str]:
    if not summary or summary.get("pooled") is None:
        return "—", "—"
    med = summary.get("median")
    lo, hi = summary.get("min"), summary.get("max")
    bracket = f"{med:.2f} [{lo:.2f}, {hi:.2f}]" if med is not None and lo is not None and hi is not None else "—"
    return f"{summary['pooled']:.2f}", bracket


def render_markdown(tables: Mapping[str, Any], *, caption_w: str) -> list[str]:
    """The three tables as Markdown grids, per configuration."""
    lines: list[str] = []
    for block in tables["configurations"]:
        c = block["configuration"]
        for key, title in (("phase_a", "phase A in wall clock, ms per evaluation"), ("phase_b", "phase B in wall clock, s per optimisation")):
            table = block.get(key)
            if table is None:
                lines += [f"**`{c}` — {title}**: no timed record in the population.", ""]
                continue
            base, arm = table["pair"]
            head = " | ".join(f"{a} (n={table['n_per_arm'][a]})" for a in table["arms"])
            lines += [
                f"**`{c}` — {title}** (pair {arm}/{base}, {table['n_pairs']} pair(s); {caption_w})",
                "",
                f"| row | {head} | {arm}/{base} | {arm}/{base} med [min, max] |",
                "|---|" + "---:|" * (len(table["arms"]) + 2),
            ]
            for name in table["rows"]:
                cells = [
                    _fmt((table["columns"][a] or {}).get(name, {}).get("mean") if table["columns"].get(a) else None, table["scale"])
                    for a in table["arms"]
                ]
                pooled, bracket = _fmt_ratio((table["ratio"] or {}).get(name)) if table["ratio"] else ("—", "—")
                lines.append(f"| {name} | {' | '.join(cells)} | {pooled} | {bracket} |")
            lines.append("")
        breakdown = block.get("breakdown")
        if breakdown is not None:
            lines += [f"**`{c}` — cost breakdown, phase B** (s per optimisation, the per-unit figure, share of Total; {caption_w})", ""]
            head = " | ".join(f"{a}: s · per · share" for a in breakdown["arms"])
            lines += [f"| row | {head} |", "|---|" + "---|" * len(breakdown["arms"])]
            for name in breakdown["rows"]:
                cells = []
                for a in breakdown["arms"]:
                    col = breakdown["columns"].get(a)
                    if not col:
                        cells.append("—")
                        continue
                    s = col[name]["s"]["mean"]
                    per = col[name]["per"]["mean"]
                    share = col[name]["share"]["mean"]
                    per_is = col[name]["per_is"] or ""
                    per_scale = 1000.0 if per_is.startswith("ms") else 1.0
                    cells.append(
                        f"{_fmt(s, 1.0)} · {_fmt(per, per_scale)} {per_is} · "
                        + ("—" if share is None else f"{100 * share:.1f} %")
                    )
                lines.append(f"| {name} | {' | '.join(cells)} |")
            lines.append("")
    if tables["n_untimed"]:
        lines += [f"*{tables['n_untimed']} record(s) without timers were not in any cell: {', '.join(tables['untimed'][:6])}*", ""]
    return lines


# --------------------------------------------------------------------------
# the stages
# --------------------------------------------------------------------------


def _references(campaign: Campaign, *, resume: bool) -> Mapping[str, Any]:
    from ..gates import gates as gates_mod  # noqa: PLC0415

    return gates_mod.entry_references(campaign, resume=resume)


def _counts(record: Mapping[str, Any]) -> dict[str, Any]:
    return {path: _at(record, path) for path in COUNT_FIELDS}


def repeatability(campaign: Campaign, *, resume: bool = False) -> dict[str, Any]:
    """Three repetitions of the gate job set at W = 1 with the timers on."""
    timed = one_worker(campaign, timers=True)
    references = _references(timed, resume=resume)
    plans = [job_set(timed, references, stage="repeatability", repetition=k) for k in range(1, REPETITIONS + 1)]
    load_before = os.getloadavg()
    for plan in plans:
        pool_mod.run_serially([job for *_r, job in plan], timed, resume=resume)
    load_after = os.getloadavg()
    jobs: list[dict[str, Any]] = []
    refused = 0
    records: list[Mapping[str, Any]] = []
    for index, (phase, config_name, arm, _job) in enumerate(plans[0]):
        reps = [records_mod.read(plan[index][3].outdir) for plan in plans]
        counts = [_counts(r) for r in reps]
        identical = all(c == counts[0] for c in counts)
        config = campaign.configuration(config_name)
        rows = None
        if identical and all(r.get("status") == "ok" for r in reps):
            groups = _grouping(campaign, config_name, reps, phase)
            blocks = [rows_of(r, groups) for r in reps]
            names = PHASE_A_ROWS if phase == "A" else PHASE_B_ROWS
            rows = summarise_rows(blocks, names)
            records.extend(reps)
        else:
            refused += 1
        jobs.append(
            {
                "phase": phase,
                "configuration": config_name,
                "arm": arm,
                "key": f"{phase}/{arm}/{config_name}",
                "n_repetitions": len(reps),
                "counts_identical": identical,
                "counts": counts[0] if identical else counts,
                "refused": None if identical else "the repetitions differ in counts: refused (A91's rule)",
                "rows_median_bracket": rows,
                "launcher_wall_s": _median_bracket([(r.get("launcher") or {}).get("wall_s") for r in reps]),
                "loadavg": [(r.get("launcher") or {}).get("loadavg_at_return") for r in reps],
                "tree_git_head": sorted({str(r.get("tree_git_head"))[:8] for r in reps}),
                "paths": [str(plan[index][3].outdir) for plan in plans],
            }
        )
    tables = tables_over(campaign, records, key_of=lambda r: int(((r.get("job_identity") or {}).get("override_env") or {}).get(REPETITION_VARIABLE) or 0))
    return {
        "stage": "repeatability",
        "what": "the gate job set three times at W = 1 with the timers on: per row the median and [min, max] over the repetitions; a job whose repetitions differ in counts is refused (V5 plan §6; D38; A91's form)",
        "tree_git_head": framework.git_head(),
        "workers": 1,
        "repetitions": REPETITIONS,
        "n_jobs": len(jobs),
        "n_refused": refused,
        "loadavg_before": load_before,
        "loadavg_after": load_after,
        "jobs": jobs,
        "tables_over_the_repetitions": tables,
        "context": "context, never evidence (D33): no verdict reads these numbers",
    }


def timers_off(campaign: Campaign, *, resume: bool = False) -> dict[str, Any]:
    """The gate job set once at W = 1 with the timers unset, beside the
    repeatability records: the instrument's own cost."""
    off = one_worker(campaign, timers=False)
    references = _references(off, resume=resume)
    plan = job_set(off, references, stage="timers_off", repetition=0)
    pool_mod.run_serially([job for *_r, job in plan], off, resume=resume)
    timed_root = timing_root(campaign, "repeatability")
    rows: list[dict[str, Any]] = []
    for phase, config_name, arm, job in plan:
        record = records_mod.read(job.outdir)
        walls_on = []
        for k in range(1, REPETITIONS + 1):
            path = timed_root / config_name / f"{phase}_{arm}" / f"rep{k}"
            if (path / "metrics.json").exists():
                r = records_mod.read(path)
                if r.get("status") == "ok":
                    walls_on.append((r.get("launcher") or {}).get("wall_s"))
        on = _median_bracket(walls_on)
        off_wall = (record.get("launcher") or {}).get("wall_s")
        rows.append(
            {
                "phase": phase,
                "configuration": config_name,
                "arm": arm,
                "key": f"{phase}/{arm}/{config_name}",
                "status": record.get("status"),
                "timers_enabled": bool((record.get("timers") or {}).get("enabled")),
                "counts": _counts(record),
                "wall_s_timers_off": off_wall,
                "wall_s_timers_on_median_bracket": on,
                "instrument_cost_s": (on["median"] - off_wall) if (on["median"] is not None and off_wall is not None) else None,
                "instrument_cost_share": ((on["median"] - off_wall) / off_wall) if (on["median"] is not None and off_wall) else None,
                "path": str(job.outdir),
            }
        )
    return {
        "stage": "timers_off",
        "what": "one run per job of the gate job set with PROCESS_ARCH_TIMERS unset at W = 1; the launcher's wall against the repeatability repetitions' median: the instrument's own cost, reported beside (V5 plan §6)",
        "tree_git_head": framework.git_head(),
        "workers": 1,
        "n_jobs": len(rows),
        "rows": rows,
        "context": "context, never evidence (D33)",
    }


def _campaign_record_for(campaign: Campaign, phase: str, config_name: str, arm: str, seed: int) -> Path | None:
    from .. import chain as chain_mod  # noqa: PLC0415

    try:
        plan = chain_mod.campaign_plan(campaign)
    except Exception:  # noqa: BLE001 - no campaign plan means no campaign record
        return None
    root = chain_mod.chain_root(campaign, plan) / ("evaluation" if phase == "A" else "optimisation")
    path = root / config_name / arm / pool_mod.seed_directory(seed)
    return path if (path / "metrics.json").exists() else None


def validity(campaign: Campaign) -> dict[str, Any]:
    """D38's check: the campaign's timing of the repeatability seeds must lie
    within the repetitions' range, per job and row 'Total'; otherwise the
    appendix's timings come from a one-worker timing pass and this says so."""
    timed_root = timing_root(campaign, "repeatability")
    rows: list[dict[str, Any]] = []
    n_within = n_outside = n_no_campaign = 0
    for config in campaign.configurations:
        for phase, seed in (("A", EVALUATION_SEED), ("B", OPTIMISATION_SEED)):
            for arm in arms_mod.active_arms(config, phase):
                reps = []
                for k in range(1, REPETITIONS + 1):
                    path = timed_root / config.name / f"{phase}_{arm}" / f"rep{k}"
                    if (path / "metrics.json").exists():
                        reps.append(records_mod.read(path))
                reps = [r for r in reps if r.get("status") == "ok" and (r.get("timers") or {}).get("enabled")]
                row: dict[str, Any] = {"phase": phase, "configuration": config.name, "arm": arm, "seed": seed, "n_repetitions": len(reps)}
                campaign_path = _campaign_record_for(campaign, phase, config.name, arm, seed)
                if not reps:
                    row["verdict"] = "no repetition record"
                    rows.append(row)
                    continue
                groups = _grouping(campaign, config.name, reps, phase)
                totals = [rows_of(r, groups)["rows"]["Total"] for r in reps]
                bracket = _median_bracket(totals)
                row["repetitions_total_s"] = bracket
                if campaign_path is None:
                    row["verdict"] = "no campaign record: the check waits for the campaign"
                    n_no_campaign += 1
                    rows.append(row)
                    continue
                campaign_record = records_mod.read(campaign_path)
                if campaign_record.get("status") != "ok" or not (campaign_record.get("timers") or {}).get("enabled"):
                    row["verdict"] = "the campaign record carries no timers or did not finish"
                    n_no_campaign += 1
                    rows.append(row)
                    continue
                total = rows_of(campaign_record, groups)["rows"]["Total"]
                within = bracket["min"] is not None and bracket["min"] <= float(total) <= bracket["max"]
                row["campaign_total_s"] = total
                row["campaign_path"] = str(campaign_path)
                row["within_the_repetitions_range"] = within
                row["verdict"] = "within" if within else "OUTSIDE: the appendix timings for this job come from a one-worker timing pass (D38)"
                n_within += int(within)
                n_outside += int(not within)
                rows.append(row)
    return {
        "stage": "validity",
        "what": "D38: the campaign's timing of the repeatability seeds against the repetitions' [min, max] of Total, per job",
        "tree_git_head": framework.git_head(),
        "n_jobs": len(rows),
        "n_within": n_within,
        "n_outside": n_outside,
        "n_without_a_campaign_record": n_no_campaign,
        "appendix_timings_from": (
            "the campaign (every checked job within the range)" if (n_outside == 0 and n_within > 0)
            else ("a one-worker timing pass over the seed set (D38): the campaign's timing lies outside the repetitions' range on " + str(n_outside) + " job(s)" if n_outside else "not decidable yet: no campaign record checked")
        ),
        "rows": rows,
    }


def tables_stage(campaign: Campaign) -> dict[str, Any]:
    """The three appendix tables rendered over the repeatability records —
    **test data**, written under ``runs/timing/`` and never the paper's document."""
    timed_root = timing_root(campaign, "repeatability")
    records = [records_mod.read(p.parent) for p in sorted(timed_root.rglob("metrics.json"))]
    tables = tables_over(campaign, records, key_of=lambda r: int(((r.get("job_identity") or {}).get("override_env") or {}).get(REPETITION_VARIABLE) or 0))
    lines = [
        "# Wall-clock tables over the timing records — TEST DATA",
        "",
        "> **Never the paper's document.** Rendered by `harness/measurement/timing.py` over the "
        "repeatability stage's records (the gate job set, three repetitions at W = 1, run kind `timing`) "
        "to smoke the three appendix tables of V5 plan §6; the paper's cells come from the campaign "
        "through `paper_tables.py`. Context, never evidence (D33).",
        "",
        *render_markdown(tables, caption_w="W = 1; pairing key = the repetition; exclusions: the exit-audit sweep, the state snapshots, the record assembly, the harness's set-up before the run"),
    ]
    out = timing_root(campaign, "tables") / "wall_clock_tables_from_timing_records.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n")
    return {
        "stage": "tables",
        "what": "the three appendix tables over the repeatability records, as test data",
        "tree_git_head": framework.git_head(),
        "n_records": len(records),
        "written": str(out),
        "tables": tables,
    }


def stage(campaign: Campaign, name: str, *, resume: bool = False) -> tuple[int, dict[str, Any]]:
    if name == "repeatability":
        record = repeatability(campaign, resume=resume)
        return (0 if record["n_refused"] == 0 else 1), record
    if name == "timers-off":
        record = timers_off(campaign, resume=resume)
        return (0 if all(r["status"] == "ok" for r in record["rows"]) else 1), record
    if name == "validity":
        record = validity(campaign)
        return (0 if record["n_outside"] == 0 else 1), record
    if name == "tables":
        return 0, tables_stage(campaign)
    raise GateError(f"{name!r} is not a timing stage; the stages are {STAGES}")


def report(record: Mapping[str, Any]) -> list[str]:
    lines = [f"  {record['stage']}: {record['what']}"]
    if record["stage"] == "repeatability":
        for job in record["jobs"]:
            if job["refused"]:
                lines.append(f"  {job['key']:34s} REFUSED — {job['refused']}")
                continue
            rows = job["rows_median_bracket"]
            total = rows["Total"]
            scale = 1000.0 if job["phase"] == "A" else 1.0
            unit = "ms/eval" if job["phase"] == "A" else "s/run"
            lines.append(
                f"  {job['key']:34s} counts identical over {job['n_repetitions']}; Total {unit} "
                f"{_fmt(total['median'], scale)} [{_fmt(total['min'], scale)}, {_fmt(total['max'], scale)}]; "
                f"residual {_fmt(rows['unattributed residual']['median'], scale)}; "
                f"launcher wall s {_fmt(job['launcher_wall_s']['median'], 1.0)} at {job['tree_git_head']}"
            )
        lines.append(f"  {record['n_refused']} of {record['n_jobs']} job(s) refused")
    elif record["stage"] == "timers_off":
        for row in record["rows"]:
            cost = row["instrument_cost_s"]
            lines.append(
                f"  {row['key']:34s} off {_fmt(row['wall_s_timers_off'], 1.0)} s, on median "
                f"{_fmt(row['wall_s_timers_on_median_bracket']['median'], 1.0)} s -> instrument "
                f"{'—' if cost is None else f'{cost:+.2f} s'}"
                + ("" if row["instrument_cost_share"] is None else f" ({100 * row['instrument_cost_share']:+.1f} %)")
            )
    elif record["stage"] == "validity":
        for row in record["rows"]:
            lines.append(f"  {row['phase']}/{row['arm']}/{row['configuration']}: {row['verdict']}")
        lines.append(f"  appendix timings from: {record['appendix_timings_from']}")
    elif record["stage"] == "tables":
        lines.append(f"  {record['n_records']} record(s) -> {record['written']}")
    return lines
