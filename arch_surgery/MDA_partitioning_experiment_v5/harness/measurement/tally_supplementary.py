"""The supplementary stage's tables, beside the campaign and labelled so.

V5 plan §3 and §10 after A96 (st-trajectory-ladder): ``B0`` and ``B2`` on
``st_regression`` under the census set at τ = 1e-12 — the rung where the
census loops read exact and the optimiser's path returns — reported
**beside** the campaign's declared cell (census / 1e-8), never pooled with it.
The records are stamped ``run_kind == "supplementary"`` and live under
``runs/supplementary/<stage name>/`` (``chain.supplementary_jobs``); the
population here is declared over that kind alone (``stats.Population.of(...,
kinds=)``), so a campaign record offered to it is refused as a supplementary
record is refused by every campaign table.

**What is emitted** — the optimisation tally's own constructions, over the
supplementary population, each table named ``supplementary …`` and captioned
with the stage's test set and tolerance: the seed set (the starts on which
every arm reached an accepted optimum), the per-arm success table, the
failure table, the same-optimum check (B1's statistic), the iterations table
with ``R = ρ × ε`` (B3), the cost with and without retried seeds (B2), the
achieved accuracy at the accepted optimum, the per-sweep overhead and the
module sweeps per run.  And one table this module builds itself: **beside
the campaign** — per seed, the campaign's ``B0``/``B2`` at the declared τ
against the supplementary ``B0``/``B2`` at 1e-12: the acceptance, the
evaluations, the solve-phase node calls, ``norm_objf`` and its paired
relative difference across the two tolerances — so that a reader sees where
the census set's trajectory term (A93, A96) lies and where the paths return.

Written by task **A102 (v5-campaign)**; V5 list items 1, 3, 4 as reduced.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Any, Mapping, Sequence

from ..core import framework
from ..core import records as records_mod
from ..core.config import Campaign, SupplementaryStage
from ..core.framework import GateError
from . import stats as stats_mod
from . import tally as tally_mod
from . import tally_optimisation as tally_b
from .tables import Caption, Column, Table

STAGE_NAME = "tally_supplementary"
RUN_KINDS: tuple[str, ...] = ("supplementary",)
PHASE = "B"


def stage_root(campaign: Campaign, stage: SupplementaryStage) -> Path:
    return Path(campaign.runs_dir) / "supplementary" / stage.name


def supplementary_records(campaign: Campaign, stage: SupplementaryStage) -> tuple[list[Mapping[str, Any]], list[Path], list[str]]:
    """Every record under the stage's root, its directory, and the refusals."""
    root = stage_root(campaign, stage)
    records: list[Mapping[str, Any]] = []
    paths: list[Path] = []
    refusals: list[str] = []
    for path in sorted(root.rglob("metrics.json")):
        record = records_mod.read(path.parent)
        kind = record.get("campaign_run_kind")
        if kind != stage.run_kind:
            raise GateError(
                f"{path.parent} under the supplementary root is stamped run kind "
                f"{kind!r}, not {stage.run_kind!r}; a record of another kind under "
                f"this root would be pooled with the stage by location alone"
            )
        try:
            records_mod.assert_usable(record, where=str(path.parent))
        except records_mod.RecordError as exc:
            refusals.append(f"{path.parent}: {exc}")
        records.append(record)
        paths.append(path.parent)
    return records, paths, refusals


def _campaign_optimisation_records(campaign: Campaign, configuration: str, arms: Sequence[str]) -> dict[str, dict[int, Mapping[str, Any]]]:
    """The campaign's optimisation records of *configuration* for *arms*, by arm and seed, from disk."""
    from .. import chain as chain_mod  # noqa: PLC0415

    out: dict[str, dict[int, Mapping[str, Any]]] = {}
    try:
        jobs = chain_mod.campaign_jobs(campaign, "optimisation")
    except chain_mod.ChainError:
        return out
    for job in jobs:
        if job.config.name != configuration or job.arm not in arms:
            continue
        if not (Path(job.outdir) / "metrics.json").exists():
            continue
        record = records_mod.read(job.outdir)
        if record.get("campaign_run_kind") != "campaign":
            continue
        out.setdefault(job.arm, {})[int(job.seed)] = record
    return out


def _rel(a: float | None, b: float | None) -> float | None:
    if a is None or b is None:
        return None
    scale = max(abs(a), abs(b))
    return abs(a - b) / scale if scale else 0.0


def _objf(record: Mapping[str, Any]) -> float | None:
    hexed = (record.get("exact") or {}).get("norm_objf")
    if isinstance(hexed, str):
        try:
            return float.fromhex(hexed)
        except ValueError:
            return None
    value = (record.get("values") or {}).get("norm_objf")
    return None if value is None else float(value)


def _evaluations(record: Mapping[str, Any]) -> int | None:
    return (record.get("sweeps_per_eval") or {}).get("n_evaluations")


def beside_the_campaign(
    campaign: Campaign,
    stage: SupplementaryStage,
    configuration: str,
    supplementary: Mapping[str, Mapping[int, Mapping[str, Any]]],
) -> Table:
    """Per seed: the campaign's and the supplementary stage's B0/B2 side by side."""
    arms = list(stage.arms)
    declared = _campaign_optimisation_records(campaign, configuration, arms)
    seeds = sorted({s for rows in supplementary.values() for s in rows} | {s for rows in declared.values() for s in rows})
    rows: list[dict[str, Any]] = []
    n_both = 0
    for seed in seeds:
        row: dict[str, Any] = {"seed": seed}
        for arm in arms:
            camp = (declared.get(arm) or {}).get(seed)
            supp = (supplementary.get(arm) or {}).get(seed)
            row[f"{arm}_declared_accepted"] = None if camp is None else stats_mod.accepted_optimum(camp)
            row[f"{arm}_supplementary_accepted"] = None if supp is None else stats_mod.accepted_optimum(supp)
            row[f"{arm}_declared_evaluations"] = None if camp is None else _evaluations(camp)
            row[f"{arm}_supplementary_evaluations"] = None if supp is None else _evaluations(supp)
            row[f"{arm}_declared_node_calls"] = None if camp is None else camp.get("node_calls_solve_phase")
            row[f"{arm}_supplementary_node_calls"] = None if supp is None else supp.get("node_calls_solve_phase")
            row[f"{arm}_objf_rel_diff_across_tau"] = (
                _rel(_objf(camp), _objf(supp))
                if camp is not None and supp is not None
                and stats_mod.accepted_optimum(camp) and stats_mod.accepted_optimum(supp)
                else None
            )
        if all(row.get(f"{a}_declared_accepted") and row.get(f"{a}_supplementary_accepted") for a in arms):
            n_both += 1
        rows.append(row)
    columns = [Column("seed", "seed", fmt=tally_b._fmt_int)]
    for arm in arms:
        columns += [
            Column(f"{arm}_declared_accepted", f"{arm} accepted @{campaign.declared_tau:g}"),
            Column(f"{arm}_supplementary_accepted", f"{arm} accepted @{stage.tau:g}"),
            Column(f"{arm}_declared_evaluations", f"{arm} evaluations @{campaign.declared_tau:g}", fmt=tally_b._fmt_int),
            Column(f"{arm}_supplementary_evaluations", f"{arm} evaluations @{stage.tau:g}", fmt=tally_b._fmt_int),
            Column(f"{arm}_declared_node_calls", f"{arm} solve-phase node calls @{campaign.declared_tau:g}", fmt=tally_b._fmt_int),
            Column(f"{arm}_supplementary_node_calls", f"{arm} solve-phase node calls @{stage.tau:g}", fmt=tally_b._fmt_int),
            Column(f"{arm}_objf_rel_diff_across_tau", f"{arm} |Δ norm_objf| / max across τ", fmt=tally_b._fmt_exp),
        ]
    return Table(
        name=f"supplementary beside the campaign — {configuration} — {stage.name}",
        caption=Caption(
            units="counts and dimensionless",
            row_is="one start (seed) on this configuration",
            column_is=(
                f"per arm: whether the campaign's run at the declared τ = {campaign.declared_tau:g} "
                f"and the supplementary run at τ = {stage.tau:g} reached an accepted optimum, "
                f"their evaluation counts and solve-phase node calls, and the paired relative "
                f"difference of norm_objf across the two tolerances (where both accepted)"
            ),
            population=(
                f"the supplementary stage {stage.name!r} ({stage.test_set}/{stage.tau:g}, run kind "
                f"{stage.run_kind!r}) beside the campaign's optimisation records of the same arms "
                f"and seeds ({campaign.test_set}/{campaign.declared_tau:g}); {len(seeds)} seed(s), "
                f"{n_both} on which every arm accepted at both tolerances"
            ),
            construction=(
                "read from the records by seed; accepted = stats.accepted_optimum; evaluations = "
                "sweeps_per_eval.n_evaluations; node calls = node_calls_solve_phase; the objective "
                "from exact.norm_objf; never pooled: two tolerances are two campaigns (D23)"
            ),
        ),
        columns=tuple(columns),
        rows=tuple(rows),
        denominator=len(seeds),
        denominator_is="starts offered to the supplementary stage",
        kind="supplementary_beside_campaign",
        detail=True,
    )


def tally(campaign: Campaign, *, resume: bool = False) -> dict[str, Any]:
    """The supplementary stages' tables, one set per declared stage."""
    emitted: list[Table] = []
    stages_out: list[dict[str, Any]] = []
    refusals: list[str] = []
    every_path: list[Path] = []
    seed_sets: dict[str, list[int]] = {}
    not_produced: list[dict[str, str]] = []
    for stage in campaign.supplementary:
        records, paths, stage_refusals = supplementary_records(campaign, stage)
        every_path.extend(paths)
        refusals.extend(f"[{stage.name}] {line}" for line in stage_refusals)
        # The stage's own settings, so every table's τ and test set are the
        # stage's (the achieved-accuracy table reads the campaign's τ).
        under = dataclasses.replace(campaign, test_set=stage.test_set, tau=float(stage.tau))
        offered = len(stage.configurations) * len(stage.arms) * campaign.n_seeds
        population = stats_mod.Population.of(
            [r for r in records if r.get("campaign_phase") == PHASE],
            what=(
                f"the supplementary stage {stage.name!r}: {', '.join(stage.arms)} on "
                f"{', '.join(stage.configurations)} under {stage.test_set}/{stage.tau:g}, "
                f"seeds 0–{campaign.n_seeds - 1}, run kind {stage.run_kind!r}; reported beside "
                f"the campaign ({campaign.test_set}/{campaign.declared_tau:g}), never pooled"
            ),
            denominator=offered,
            kinds=RUN_KINDS,
        )
        population.assert_no_forced_budget()
        stages_out.append(
            {
                "stage": stage.name,
                "test_set": stage.test_set,
                "tau": stage.tau,
                "why": stage.why,
                "n_records": len(population),
                "n_offered": offered,
                "run_kinds": list(population.run_kinds),
                "root": str(stage_root(campaign, stage)),
            }
        )
        if population.is_empty:
            continue
        for configuration in stage.configurations:
            whole = tally_b._by_arm_and_seed(population, configuration)
            if not whole:
                continue
            emitted.append(tally_b.failure_taxonomy(population, configuration, f"supplementary {stage.name}"))
            for arms, seeds in tally_b.arm_groups(whole):
                label = f"supplementary {stage.name} · {'·'.join(arms)} · {stage.test_set}/{stage.tau:g}"
                by_arm = tally_b.restrict(whole, arms, seeds)
                table, converged = tally_b.seed_set(under, population, configuration, by_arm, label)
                seed_sets[f"{label}/{configuration}"] = converged
                emitted.append(table)
                emitted.extend(tally_b.per_arm_success(population, configuration, by_arm, label))
                emitted.append(tally_b.failure_table(population, configuration, by_arm, converged, label))
                for name, built in (
                    ("same optimum (B1)", tally_b.same_optimum(under, population, configuration, by_arm, converged, label)),
                    ("iterations and R = ρ × ε (B3)", tally_b.iterations(under, population, configuration, by_arm, converged, label)),
                    ("cost (B2)", tally_b.cost(population, configuration, by_arm, converged, label)),
                    ("module sweeps per run (B2)", tally_b.module_sweeps(under, population, configuration, by_arm, converged, label)),
                    ("node calls per module", tally_b.node_calls_per_module(under, population, configuration, by_arm, converged, label)),
                ):
                    if built is None:
                        not_produced.append({"table": f"{name} — {configuration} — {label}", "why": "no flat control in the arm group"})
                    else:
                        emitted.append(built)
                emitted.append(tally_b.attempts(population, configuration, by_arm, label))
                emitted.append(tally_b.achieved_accuracy(under, population, configuration, by_arm, label))
                emitted.append(tally_b.per_sweep_overhead(population, configuration, by_arm, label))
            emitted.append(beside_the_campaign(campaign, stage, configuration, whole))
    provenance = tally_mod.survey(every_path)
    return {
        "stage": STAGE_NAME,
        "phase": PHASE,
        "population_family": "supplementary",
        "what": (
            "the declared supplementary stages' tables (config.SUPPLEMENTARY_STAGES; V5 plan §3, "
            "A96): the optimisation tally's constructions over the stage's own records under its "
            "own test set and tolerance, labelled supplementary, reported beside the campaign and "
            "never pooled with it; plus one table per configuration placing the campaign's and the "
            "supplementary runs side by side per seed"
        ),
        "stages": stages_out,
        "population": "; ".join(f"{s['stage']}: {s['n_records']} of {s['n_offered']} record(s)" for s in stages_out),
        "n_records": sum(s["n_records"] for s in stages_out),
        "runs_provenance": provenance,
        "record_contract_refusals": refusals,
        "seed_sets": seed_sets,
        "tables_not_produced": not_produced,
        "tables": [table.as_record() for table in emitted],
        "n_tables": len(emitted),
        "tree_git_head": framework.git_head(),
    }


def print_tally(block: Mapping[str, Any]) -> None:
    from .tally_evaluation import _rendered  # noqa: PLC0415

    print(f"\n  population family: {block.get('population_family')} — {block.get('population')}")
    for stage in block.get("stages") or []:
        print(f"  stage {stage['stage']}: {stage['test_set']}/{stage['tau']:g}, {stage['n_records']} of {stage['n_offered']} record(s) under {stage['root']}")
    for line in block.get("record_contract_refusals") or []:
        print(f"  refused: {line}")
    for table in block.get("tables") or []:
        for line in _rendered(table):
            print(line)
    for name, seeds in (block.get("seed_sets") or {}).items():
        print(f"  seed set {name}: n = {len(seeds)} ({seeds})")
