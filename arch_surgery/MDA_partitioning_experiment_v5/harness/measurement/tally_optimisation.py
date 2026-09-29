#!/usr/bin/env python
"""The optimisation phase's tally: the same optimum, the same path, the cost.

A **tally** summarises the records into the tables the experiment plan's §4
asks for.  It has nothing to pass, so it is a *measurement stage* and runs
under ``--measure``; the checks it depends on are gates with teeth and live in
``harness/gates/gate_tally.py``.

Eight tables, each the shape of one of the plan's §4.3 or §3.5 placeholders:

``seed_set``        §4.3.1 — the one population per configuration (the seeds on
                    which **every** arm reached an accepted optimum) with the
                    retried-seed count per arm.
``failure_table``   §4.3.1 — every seed **outside** that set, with each failed
                    arm's exit code, attempts and cost beside the other arms'
                    cost at the same start.
``per_arm_success`` §4.3 — reliability per arm over the 25 starts offered:
                    accepted optima, the other starts by outcome class (exit
                    code; PROCESS's own exception; the coupling-loop cap), the
                    starts lost that another arm accepted, the seed set beside;
                    reported, not accepted on (decision D29).  Its per-seed
                    companion ``per_arm_success_by_seed`` is one row per seed.
                    *(Task A82 (per-arm-success), 2026-09-15.)*
``same_optimum``    §4.3.2 / check 1 — the paired relative objective difference
                    against the threshold the campaign's own yardstick sets,
                    with clusters, hops and the below-resolution category.
``iterations``      check 2 — **both** constructions: the final attempt's count
                    and the count summed over every attempt, beside the
                    evaluation count, which is the multiplier the transfer
                    needs.
``attempts``        the summation identity, printed: Σ over attempts equals the
                    run's solve-phase total, for node calls and for sweeps.
``cost``            check 4 — solve-phase node calls in the one format, with
                    the ratio published **with and without** the retried seeds.
``achieved_accuracy`` the exit audit at the accepted optimum, on **both**
                    rulers, with the audit position and the instrument's own
                    version in columns of their own and the argmax component
                    named rather than averaged.
``lift_closed``     check 3 — constraint 93's residual at every accepted
                    optimum, in seconds and relative to the burn time.

``failure_taxonomy`` check 4 — every scheduled start a row, per arm, with the
                    denominator and the traceback's last line as the detail.
``node_calls_per_module`` the report's headline shape 1 (``REPORT_HEADLINE_TABLES.md``):
                    node calls per module per configuration with per-run
                    brackets, the pooled B2/B0, the per-run median and the
                    count of runs on which B2 cost more; grouping derived from
                    the committed node map and the per-run artifact.
``optimiser_path``  headline shape 2: one table over the configurations for the
                    optimiser's iterations, the evaluation count ε (from
                    ``sweeps_per_eval.n_evaluations``, issue I-26's field), the
                    cost per evaluation ρ and the cost per run R = ρ × ε, each
                    as per-arm means and the B2/B0 ratio summarised per seed.
                    *(Both added by task A79 (report-captions); the caption
                    rule of that task is stated in ``tally_evaluation``.)*

**What the population is.** These tables are over **one declared population**
(``tally.published_sources``): the **campaign** source
``campaign_optimisation`` — the campaign plan's own optimisation job set, 25
starts per arm per configuration under ``runs/campaign/optimisation/`` — once a
campaign record exists, and the gate source ``reference_runs`` — one or two
seeds per arm — while none does.  Never both: with the campaign present a gate
record is refused by kind at the population's construction, and every caption
and denominator sentence names the kind of run it is over, read from the
records.  A crashed start is a taxonomy row and a failure-table row; it is
never a cost (plan §3.5).

Written by task **A53 (harness-tally)**; the campaign source and the phase's
taxonomy table by task **A75 (campaign-tally-source)**.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from harness.experiment import arms as arms_mod
from harness.measurement import stats as stats_mod
from harness.measurement import tally as tally_mod
from harness.core.config import Campaign
from harness.measurement.tables import (
    Caption,
    Column,
    Table,
    cell_list,
    sweep_cell,
)

#: The optimisation phase's arms in rung order, for the headline tables'
#: columns (plan §3.2).
LADDER: tuple[str, ...] = ("BR", "B0", "B1", "B2")

#: The headline ratio's pair: the partitioned arm against the flat control.
HEADLINE_PAIR: tuple[str, str] = ("B0", "B2")

__all__ = ["tally", "print_tally", "PHASE"]

PHASE = "B"

#: The arm every ratio and every pair is stated against (plan §3.5): the flat
#: control, which differs from the shipped reference by the stopping rule alone.
BASE_ARM = "B0"

#: The arm pair whose spread is check 1's **yardstick** — the spread the same
#: campaign measures between two arms that differ only in the stopping rule.
YARDSTICK_PAIR = ("BR", "B0")

#: The arms check 2's acceptance rule is read on (plan §3.5 check 2).  Every
#: other pair is **published beside**, outside the rule: the shipped reference
#: differs from the flat control by the stopping rule, which is not what this
#: check controls, and a verdict printed against it would be a verdict on the
#: wrong comparison.
ACCEPTANCE_PAIRS: tuple[str, ...] = ("B1", "B2")


def _fmt_ratio(value: Any) -> str:
    return "—" if value is None else f"{value:.4f}"


def _fmt_cell(value: Any) -> str:
    """A ratio, or a pre-composed cell (the total row's interval) unchanged."""
    if value is None:
        return "—"
    if isinstance(value, str):
        return value
    return f"{value:.4f}"


def _fmt_int(value: Any) -> str:
    return "—" if value is None else f"{int(value)}"


def _fmt_exp(value: Any) -> str:
    if value is None:
        return "—"
    if value == 0:
        return "0"
    return f"{value:.3e}"


def _hexf(value: Any) -> float | None:
    return float.fromhex(value) if isinstance(value, str) else None


def _by_arm_and_seed(
    population: stats_mod.Population, configuration: str
) -> dict[str, dict[int, Mapping[str, Any]]]:
    """Records of this configuration, indexed by arm and seed.

    Where two gates ran the same arm at the same seed under their own roots,
    the records are the same job and the first is kept; the count of collisions
    is reported by the caller, never absorbed silently.
    """
    out: dict[str, dict[int, Mapping[str, Any]]] = {}
    for record in population.records:
        if record.get("campaign_configuration") != configuration:
            continue
        arm = str(record.get("campaign_arm"))
        seed = record.get("campaign_seed")
        if seed is None:
            continue
        out.setdefault(arm, {}).setdefault(int(seed), record)
    return out


def _arm_order(names) -> list[str]:
    order = arms_mod.MATRIX_ORDER
    return sorted(names, key=lambda n: order.index(n) if n in order else len(order))


def arm_groups(
    by_arm: Mapping[str, Mapping[int, Mapping[str, Any]]]
) -> list[tuple[tuple[str, ...], list[int]]]:
    """Split a source's records into **seed-complete arm groups**.

    The plan's one population per configuration is "the seeds on which *every*
    arm converged", and it assumes what a campaign guarantees: every arm runs
    at every seed.  A gate's runs do not guarantee it — the reproduction gate
    runs one set of arms at its unperturbed seed and a different set at its
    perturbed one — so that construction over the whole source would return an
    empty set, and an empty set is not a population, it is an absence.

    So the source is first split by **which arms have a run at a seed**.  Each
    group is a set of arms and the seeds at which all of them ran, which *is* a
    population the plan's construction applies to; the group is named in every
    caption.  A group of one arm is dropped: there is no pair in it.

    This is a property of the gate runs, not of the method.  In a campaign
    there is exactly one group per configuration and this function returns it.
    """
    seeds_of_arm = {arm: set(rows) for arm, rows in by_arm.items()}
    by_seed: dict[int, set[str]] = {}
    for arm, seeds in seeds_of_arm.items():
        for seed in seeds:
            by_seed.setdefault(seed, set()).add(arm)
    grouped: dict[tuple[str, ...], list[int]] = {}
    for seed, arms in sorted(by_seed.items()):
        if len(arms) < 2:
            continue
        key = tuple(_arm_order(arms))
        grouped.setdefault(key, []).append(seed)
    return sorted(grouped.items(), key=lambda kv: (-len(kv[0]), kv[0]))


def restrict(
    by_arm: Mapping[str, Mapping[int, Mapping[str, Any]]],
    arms: Sequence[str],
    seeds: Sequence[int],
) -> dict[str, dict[int, Mapping[str, Any]]]:
    """The sub-index of one arm group: those arms, at those seeds, only."""
    return {
        arm: {seed: by_arm[arm][seed] for seed in seeds if seed in by_arm[arm]}
        for arm in arms
        if arm in by_arm
    }


# --------------------------------------------------------------------------
# the tables
# --------------------------------------------------------------------------


def seed_set(
    campaign: Campaign,
    population: stats_mod.Population,
    configuration: str,
    by_arm: Mapping[str, Mapping[int, Mapping[str, Any]]],
    source: str,
) -> tuple[Table, list[int]]:
    """§4.3.1 — the one population, and how many of its seeds retried."""
    seeds = sorted({seed for rows in by_arm.values() for seed in rows})
    converged = stats_mod.every_arm_converged(by_arm, seeds)
    invalid = stats_mod.configuration_invalid_seeds(by_arm, seeds)
    rows = [
        {
            "arms": len(by_arm),
            "arm_names": " · ".join(_arm_order(by_arm)),
            "seeds_offered": len(seeds),
            "n": len(converged),
            "seeds": ", ".join(str(s) for s in converged) or "—",
            "configuration_invalid": len(invalid),
            "retried": " · ".join(
                f"{arm} {len(stats_mod.retried_seeds(by_arm[arm]))}"
                for arm in _arm_order(by_arm)
            ),
        }
    ]
    return (
        Table(
            name=f"the seed set — {configuration} — {source}",
            caption=Caption(
                units="counts of seeds",
                row_is="this configuration",
                column_is="the size of the one population every "
                "optimisation-phase table on this configuration is over, or a "
                "per-arm count of the seeds on which the optimiser was called "
                "more than once",
                population=(
                    f"{population.what}; the arms present here are "
                    f"{', '.join(_arm_order(by_arm))} at seeds "
                    f"{', '.join(str(s) for s in seeds) or 'none'}"
                ),
                construction=(
                    "stats.every_arm_converged — a seed is in the set when "
                    "every arm present reached an accepted optimum "
                    "(status ok AND the output file's ifail == 1); "
                    "stats.retried, which counts attempts[] and never a stored "
                    "flag"
                ),
                clauses=(
                    "**this is one arm group of the source.**  The plan's "
                    "construction assumes what a campaign guarantees — every "
                    "arm at every seed — and a gate's runs do not: the source "
                    "is therefore split by which arms have a run at a seed, "
                    "and each group is a population the construction applies "
                    "to.  The group is named in this table's title and in "
                    "every other table of the same group",
                    "the seeds outside the set are not dropped: they are the "
                    "failure table, published beside this one, so an arm that "
                    "fails on expensive seeds cannot be flattered by the filter",
                    "a seed on which **no** arm converged is configuration "
                    "hardness, counted in its own column and not against any arm",
                ),
                how_to_read=(
                    "this n is the denominator of every other optimisation-phase "
                    "table on this configuration"
                ),
                summary=(
                    f"The seed set of {configuration}: seeds offered, seeds on "
                    f"which every arm ({' · '.join(_arm_order(by_arm))}) "
                    f"reached an accepted optimum (n, the denominator of every "
                    f"check on this configuration), configuration-invalid "
                    f"seeds and retried seeds per arm."
                ),
            ),
            columns=(
                Column("arms", "arms", fmt=_fmt_int),
                Column("arm_names", "which"),
                Column("seeds_offered", "seeds offered", fmt=_fmt_int),
                Column("n", "n (every arm converged)", fmt=_fmt_int),
                Column("seeds", "seeds in the set"),
                Column("configuration_invalid", "configuration-invalid seeds", fmt=_fmt_int),
                Column("retried", "retried seeds per arm"),
            ),
            rows=tuple(rows),
            denominator=len(seeds),
            denominator_is=f"distinct seeds run on {configuration}",
            acceptance=True,
            kind="seed_set",
            report_omits=("seeds",),
        ),
        converged,
    )


def _seeds_text(seeds: Sequence[int]) -> str:
    return ", ".join(str(s) for s in seeds) or "—"


def per_arm_success(
    population: stats_mod.Population,
    configuration: str,
    by_arm: Mapping[str, Mapping[int, Mapping[str, Any]]],
    source: str,
) -> tuple[Table, Table]:
    """§4.3 — reliability per arm over the starts offered, and its per-seed
    companion.  ``stats.per_arm_success`` is the declaration; this is its
    shape.  The first table is the report's (counts per arm, the seed-naming
    columns left to the companion file); the second is one row per seed and
    goes to the companion file whole."""
    order = _arm_order(by_arm)
    seeds = sorted({seed for rows in by_arm.values() for seed in rows})
    built = stats_mod.per_arm_success({arm: by_arm[arm] for arm in order}, seeds)
    classes: list[str] = built["classes"]
    n_set = len(built["seed_set"])
    rows: list[dict[str, Any]] = []
    for arm in order:
        part = built["arms"][arm]
        row: dict[str, Any] = {
            "arm": arm,
            "offered": part["offered"],
            "accepted": part["accepted"],
        }
        for label in classes:
            row[label] = part["by_class"][label]
        row["lost_another_arm_accepted"] = len(part["lost_another_arm_accepted"])
        row["seed_set"] = n_set
        row["seeds_not_accepted"] = cell_list(
            [
                f"{label}: {_seeds_text(part['seeds_by_class'][label])}"
                for label in classes
                if part["seeds_by_class"][label]
            ]
        )
        row["lost_seeds"] = _seeds_text(part["lost_another_arm_accepted"])
        rows.append(row)
    arms_text = " · ".join(order)
    summary_table = Table(
        name=f"per-arm success — {configuration} — {source}",
        caption=Caption(
            units="counts of starts",
            row_is="one optimisation arm on this configuration",
            column_is="the starts offered, the accepted optima, every other "
            "start by its outcome class, the starts lost that another arm "
            "accepted, and the seed set beside",
            population=(
                f"{population.what}; the arms present here are {arms_text} at "
                f"seeds {_seeds_text(seeds)}"
            ),
            construction=(
                "stats.per_arm_success — accepted is stats.accepted_optimum "
                "(status ok AND the output file's ifail == 1); every other "
                "start carries one stats.outcome_class (finished with the "
                "optimiser's exit code; crashed in PROCESS's own code, the "
                "exception named; refused by the coupling-state loop's sweep "
                "cap, ModuleSolveFailure); a start is lost when this arm did "
                "not accept and another arm did; the seed set is "
                "stats.every_arm_converged"
            ),
            clauses=(
                "**reported, not accepted on**: no pre-declared rule of the "
                "plan reads a per-arm rate; the cost tables stay over the seed "
                "set and this table states what that filter leaves out "
                "(decision D29, 2026-09-15, on A81 (benchmarking-practices)'s "
                "finding F1)",
                "the classes partition the offered starts: accepted plus the "
                "class columns sum to the starts offered in every row",
                "a seed no arm accepted is configuration hardness (the seed-set "
                "table's configuration-invalid column) and is not a lost start "
                "of any arm; the lost starts are the asymmetric failures",
                "the harness stamps a coupling-loop refusal and a PROCESS "
                "exception both as status crashed; the failure class and the "
                "traceback separate them here, as in the taxonomy table",
            ),
            how_to_read=(
                "read accepted over offered as the arm's success rate with its "
                "denominator; the lost column is what the seed-set filter hides "
                "from a cost ratio"
            ),
            summary=(
                f"Per-arm success on {configuration}: of the 25 starts offered "
                f"to each arm ({arms_text}), the accepted optima (status ok and "
                f"ifail == 1), the other starts by outcome class (finished with "
                f"the optimiser's exit code; crashed in PROCESS's own code; "
                f"refused at the coupling-state loop's sweep cap), the starts "
                f"lost that another arm accepted, and the seed set beside. "
                f"Reported, not accepted on: no pre-declared rule reads it "
                f"(D29, 2026-09-15)."
            ),
        ),
        columns=(
            Column("arm", "arm"),
            Column("offered", "starts offered", fmt=_fmt_int),
            Column("accepted", "accepted optima", fmt=_fmt_int),
            *[Column(label, label, fmt=_fmt_int) for label in classes],
            Column(
                "lost_another_arm_accepted", "lost, another arm accepted",
                fmt=_fmt_int,
            ),
            Column("seed_set", "seed set (every arm accepted)", fmt=_fmt_int),
            Column("seeds_not_accepted", "seeds not accepted, by class"),
            Column("lost_seeds", "seeds lost that another arm accepted"),
        ),
        rows=tuple(rows),
        denominator=len(seeds),
        denominator_is=f"starts offered per arm on {configuration}",
        acceptance=True,
        kind="per_arm_success",
        report_omits=("seeds_not_accepted", "lost_seeds"),
    )
    seed_rows: list[dict[str, Any]] = []
    for entry in built["per_seed"]:
        row = {"seed": entry["seed"]}
        for arm in order:
            row[arm] = entry["classes"].get(arm, "not run")
        row["n_accepted"] = entry["n_accepted"]
        row["in_seed_set"] = "yes" if entry["in_seed_set"] else "no"
        row["lost_by"] = ", ".join(entry["lost_by"]) or "—"
        seed_rows.append(row)
    by_seed_table = Table(
        name=f"per-arm success by seed — {configuration} — {source}",
        caption=Caption(
            units="outcome classes (text) and counts of arms",
            row_is="one seed offered to every arm of the group",
            column_is="each arm's outcome class at that seed, how many arms "
            "accepted, whether the seed is in the seed set, and which arms "
            "lost it while another accepted",
            population=(
                f"{population.what}; the arms present here are {arms_text} at "
                f"seeds {_seeds_text(seeds)}"
            ),
            construction=(
                "stats.per_arm_success (per-seed part) — stats.outcome_class "
                "per record; in the seed set when every arm accepted "
                "(stats.every_arm_converged); lost by an arm when it did not "
                "accept and another did"
            ),
            clauses=(
                "the per-seed detail behind the per-arm success table: the "
                "report carries the counts, this table the seeds",
                "a seed no arm accepted is configuration-invalid and reads 0 "
                "arms accepted with no arm losing it",
            ),
            how_to_read=(
                "read down an arm's column for its failures; read the lost-by "
                "column for the asymmetric ones"
            ),
            summary=(
                f"Per-arm success on {configuration} by seed: each arm's "
                f"outcome class at every start offered, the count of arms that "
                f"accepted, membership of the seed set, and the arms that lost "
                f"the start while another accepted."
            ),
        ),
        columns=(
            Column("seed", "seed", fmt=_fmt_int),
            *[Column(arm, arm) for arm in order],
            Column("n_accepted", "arms accepted", fmt=_fmt_int),
            Column("in_seed_set", "in the seed set"),
            Column("lost_by", "lost by (another arm accepted)"),
        ),
        rows=tuple(seed_rows),
        denominator=len(seeds),
        denominator_is=f"distinct seeds run on {configuration}",
        acceptance=True,
        kind="per_arm_success_by_seed",
        detail=True,
    )
    return summary_table, by_seed_table


def failure_table(
    population: stats_mod.Population,
    configuration: str,
    by_arm: Mapping[str, Mapping[int, Mapping[str, Any]]],
    converged: Sequence[int],
    source: str,
) -> Table:
    """§4.3.1 — every seed outside the set, with its cost beside the others'."""
    seeds = sorted({seed for rows in by_arm.values() for seed in rows})
    outside = [s for s in seeds if s not in set(converged)]
    order = _arm_order(by_arm)
    rows: list[dict[str, Any]] = []
    for seed in outside:
        failed = [
            arm
            for arm in order
            if seed in by_arm[arm]
            and not stats_mod.accepted_optimum(by_arm[arm][seed])
        ]
        absent = [arm for arm in order if seed not in by_arm[arm]]
        rows.append(
            {
                "seed": seed,
                "failed": ", ".join(failed) or "—",
                "not_run": ", ".join(absent) or "—",
                "ifail": ", ".join(
                    str((by_arm[arm][seed].get("mfile") or {}).get("ifail"))
                    for arm in failed
                )
                or "—",
                "attempts": ", ".join(
                    str(stats_mod.n_attempts(by_arm[arm][seed])) for arm in failed
                )
                or "—",
                "failed_cost": ", ".join(
                    str(by_arm[arm][seed].get("node_calls_solve_phase"))
                    for arm in failed
                )
                or "—",
                "other_cost": " / ".join(
                    f"{arm} "
                    + (
                        str(by_arm[arm][seed].get("node_calls_solve_phase"))
                        if seed in by_arm[arm] and arm not in failed
                        else "—"
                    )
                    for arm in order
                ),
                "configuration_invalid": (
                    "yes" if len(failed) + len(absent) == len(order) else "no"
                ),
            }
        )
    return Table(
        name=f"the failure table — {configuration} — {source}",
        caption=Caption(
            units="counts: model executions for the cost columns, optimiser "
            "exit codes for ifail",
            row_is="one seed outside the converged set",
            column_is="which arm failed there, how it failed, what it cost, "
            "and what the other arms cost at the same start",
            population=(
                f"{population.what}; {len(outside)} of {len(seeds)} seed(s) on "
                f"{configuration} lie outside the every-arm-converged set"
            ),
            construction=(
                "stats.accepted_optimum for membership; the cost column is "
                "node_calls_solve_phase, the same unit the cost table uses"
            ),
            clauses=(
                "an arm the gate did not run at a seed reads *not run* rather "
                "than *failed*: an absent record and a failed run are "
                "different results",
                "a seed on which every arm failed or was absent is marked "
                "configuration-invalid",
            ),
            how_to_read=(
                "the converged set is the fairer cost population but can "
                "flatter an arm that fails on expensive seeds; this table is "
                "what keeps it honest"
            ),
            summary=(
                f"Seeds of {configuration} outside the seed set: which arm "
                f"failed there and how (ifail, attempts), its cost and the "
                f"other arms' at the same start; a seed every arm failed on is "
                f"configuration-invalid."
            ),
        ),
        columns=(
            Column("seed", "seed", fmt=_fmt_int),
            Column("failed", "failed arm(s)"),
            Column("not_run", "not run"),
            Column("ifail", "ifail"),
            Column("attempts", "attempts"),
            Column("failed_cost", "failed arm node calls"),
            Column("other_cost", "other arms' node calls"),
            Column("configuration_invalid", "configuration-invalid"),
        ),
        rows=tuple(rows),
        denominator=len(seeds),
        denominator_is=f"distinct seeds run on {configuration}",
        acceptance=True,
        kind="failure_table",
        detail=True,
    )


def failure_taxonomy(
    population: stats_mod.Population,
    configuration: str,
    source: str,
) -> Table:
    """Check 4's taxonomy — every scheduled start a row, per arm, with the
    denominator stated and the traceback's last line as the class detail.

    Over the **whole** source population of the configuration — every arm at
    every start, before the seed-complete arm grouping — because the taxonomy
    is what was scheduled and what became of it, and a grouping by which arms
    converged would be the taxonomy filtering itself.  The same construction
    as the evaluation phase's (``stats.failure_taxonomy``, ``stats.crash_detail``).
    """
    by_arm: dict[str, list[Mapping[str, Any]]] = {}
    for record in population.records:
        if record.get("campaign_configuration") != configuration:
            continue
        by_arm.setdefault(str(record.get("campaign_arm")), []).append(record)
    classes = sorted(
        {
            str(record.get("failure_class"))
            for records in by_arm.values()
            for record in records
        }
    )
    rows: list[dict[str, Any]] = []
    for arm in _arm_order(by_arm):
        taxonomy = stats_mod.failure_taxonomy(
            by_arm[arm], denominator=len(by_arm[arm])
        )
        row: dict[str, Any] = {
            "arm": arm,
            "denominator": taxonomy["denominator"],
            "sums": "yes" if taxonomy["rows_sum_to_denominator"] else "NO",
        }
        for name in classes:
            row[name] = taxonomy["by_failure_class"].get(name, 0)
        row["detail"] = stats_mod.crash_detail(by_arm[arm])
        rows.append(row)
    return Table(
        name=f"failure taxonomy — {configuration} — {source}",
        caption=Caption(
            units="counts of runs; the detail column is text",
            row_is="one arm on this configuration",
            column_is="one disposition of the taxonomy, and the detail: the "
            "last line of each unfinished run's traceback, distinct, with "
            "its count",
            population=(
                f"{population.what}; every {population.runs_word[:-1]} of "
                f"{configuration}, every start"
            ),
            construction=(
                "stats.failure_taxonomy — every scheduled run is a row and a "
                "run that wrote no record is counted as no_record, never "
                "skipped; stats.crash_detail for the detail"
            ),
            clauses=(
                "the rows sum to the denominator, and the table says so per "
                "arm rather than leaving it to be added up",
                "an arm inactive on a configuration is absent from this table "
                "rather than reading 0: a skipped arm and a failing arm are "
                "different results",
                "a crashed start is counted here and in the failure table, and "
                "reaches no cost cell: the cost tables are over the "
                "every-arm-converged seed set (plan §3.5)",
            ),
            how_to_read=(
                "a nonzero crashed column is a machinery result that must be "
                "explained before any ratio on this configuration is cited; "
                "the detail says whether one failure mode or several"
            ),
            summary=(
                f"Every scheduled optimisation of {configuration}, "
                f"{tally_mod.source_phrase(source)}, by arm and disposition; "
                f"the detail is each crashed run's last traceback line. A "
                f"crashed start is never a cost."
            ),
        ),
        columns=(
            Column("arm", "arm"),
            Column("denominator", "scheduled", fmt=_fmt_int),
            *[Column(name, name, fmt=_fmt_int) for name in classes],
            Column("sums", "rows sum"),
            Column("detail", "detail (traceback's last line × count)"),
        ),
        rows=tuple(rows),
        denominator=sum(len(v) for v in by_arm.values()),
        denominator_is=f"optimisation-phase {population.runs_word} of {configuration}",
        acceptance=True,
        kind="failure_taxonomy",
    )


def same_optimum(
    campaign: Campaign,
    population: stats_mod.Population,
    configuration: str,
    by_arm: Mapping[str, Mapping[int, Mapping[str, Any]]],
    converged: Sequence[int],
    source: str,
) -> Table | None:
    """§4.3.2 / check 1 — is it the same optimum?

    ``None`` where this arm group carries no flat control: every pair of this
    check is anchored on it, so without it there is nothing to compare and an
    empty table would state a denominator over no comparison.  The omission is
    named in the stage's record rather than left as a blank table.
    """
    if BASE_ARM not in by_arm:
        return None
    pairs: list[tuple[str, str]] = []
    if all(a in by_arm for a in YARDSTICK_PAIR):
        pairs.append(YARDSTICK_PAIR)
    for arm in _arm_order(by_arm):
        if arm != BASE_ARM and BASE_ARM in by_arm and arm not in YARDSTICK_PAIR:
            pairs.append((BASE_ARM, arm))
    accepted: list[tuple[str, int, float]] = []
    for arm, rows in by_arm.items():
        for seed, record in rows.items():
            if stats_mod.accepted_optimum(record):
                value = _hexf((record.get("exact") or {}).get("norm_objf"))
                if value is not None:
                    accepted.append((arm, seed, value))
    gap = campaign.cluster_gap_factor * campaign.objf_floor_rel
    groups = stats_mod.clusters([v for _, _, v in accepted], gap=gap)
    cluster_of: dict[tuple[str, int], int] = {}
    for index, group in enumerate(groups):
        for position in group:
            arm, seed, _ = accepted[position]
            cluster_of[(arm, seed)] = index

    def relatives(a: str, b: str) -> tuple[list[float], list[int]]:
        values: list[float] = []
        seeds: list[int] = []
        for seed in converged:
            ra, rb = by_arm.get(a, {}).get(seed), by_arm.get(b, {}).get(seed)
            if not (ra and rb):
                continue
            fa = _hexf((ra.get("exact") or {}).get("norm_objf"))
            fb = _hexf((rb.get("exact") or {}).get("norm_objf"))
            if fa is None or fb is None:
                continue
            values.append(stats_mod.relative_objective_difference(fa, fb))
            seeds.append(seed)
        return values, seeds

    yardstick_values, _ = (
        relatives(*YARDSTICK_PAIR) if all(a in by_arm for a in YARDSTICK_PAIR) else ([], [])
    )
    yard_median = stats_mod.median(yardstick_values)
    yard_p90 = stats_mod.p90(yardstick_values)
    rows: list[dict[str, Any]] = []
    for a, b in pairs:
        values, seeds = relatives(a, b)
        is_yardstick = (a, b) == YARDSTICK_PAIR
        threshold_median = (
            None
            if is_yardstick
            else stats_mod.acceptance_threshold(
                yard_median,
                factor=campaign.similarity_factor,
                floor=campaign.objf_floor_rel,
            )
        )
        threshold_p90 = (
            None
            if is_yardstick
            else stats_mod.acceptance_threshold(
                yard_p90,
                factor=campaign.similarity_factor,
                floor=campaign.objf_floor_rel,
            )
        )
        observed_median = stats_mod.median(values)
        observed_p90 = stats_mod.p90(values)
        verdict = "—"
        if threshold_median is not None and observed_median is not None:
            passed = observed_median <= threshold_median and (
                observed_p90 is None or threshold_p90 is None
                or observed_p90 <= threshold_p90
            )
            verdict = "PASS" if passed else "FAIL"
        hop = stats_mod.hops(
            cluster_of, [((a, s), (b, s)) for s in seeds]
        )
        resolution = stats_mod.below_cluster_resolution(
            values, floor=campaign.objf_floor_rel, gap=gap
        )
        rows.append(
            {
                "pair": f"{a} → {b}" + (" (yardstick)" if is_yardstick else ""),
                "n": len(values),
                "r_median": observed_median,
                "r_p90": observed_p90,
                "threshold_median": threshold_median,
                "threshold_p90": threshold_p90,
                "verdict": verdict,
                "hops": f"{hop['n_hops']}/{hop['n_pairs']}"
                + (f" ({hop['rate']:.2f})" if hop["rate"] is not None else ""),
                "below_resolution": resolution["n"],
                "retried_in_pair": sum(
                    1
                    for s in seeds
                    if stats_mod.retried(by_arm[a][s])
                    or stats_mod.retried(by_arm[b][s])
                ),
            }
        )
    return Table(
        name=f"same optimum (check 1) — {configuration} — {source}",
        caption=Caption(
            units="dimensionless: a relative difference of the normalised "
            "objective",
            row_is="one arm pair over the seed set",
            column_is="the paired relative objective difference's median and "
            "p90, the threshold they are judged against, and the clustering "
            "statistics",
            population=(
                f"{population.what}; {len(converged)} seed(s) on which every "
                f"arm of {configuration} reached an accepted optimum"
            ),
            construction=(
                "stats.relative_objective_difference — |Δ norm_objf| / "
                "max(|a|, |b|) per pair, from the hex floats; median = "
                "nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n); "
                "stats.acceptance_threshold = max(F × yardstick, floor) with "
                f"F = {campaign.similarity_factor:g} and floor = "
                f"{campaign.objf_floor_rel:g}, the yardstick being the "
                f"{YARDSTICK_PAIR[0]} → {YARDSTICK_PAIR[1]} spread measured in "
                "this same population; stats.clusters at a relative gap of "
                f"{gap:g}"
            ),
            clauses=(
                "the yardstick row carries no threshold and no verdict: it "
                "*is* the threshold's calibration",
                "*below resolution* counts pairs further apart than the "
                "correctness floor and closer than the cluster gap — distinct "
                "optima below cluster resolution, a named category and not a "
                "rounding remark",
                "the retried column is computed from attempts[], never from a "
                "stored flag, so a pair containing a retry is visible here as "
                "well as in the cost table",
            ),
            how_to_read=(
                "a verdict is read only where a threshold exists; a hop is a "
                "seed whose two sides landed in different objective clusters, "
                "and the yardstick pair's own hop rate is the comparator"
            ),
            summary=(
                f"Check 1 on {configuration}: the paired relative objective "
                f"difference of each arm against B0 over the seed set (median, "
                f"p90) against max(F × yardstick, floor), the yardstick being "
                f"{YARDSTICK_PAIR[0]} → {YARDSTICK_PAIR[1]} in this population, "
                f"with hops and pairs below cluster resolution. The yardstick "
                f"row carries no verdict."
            ),
        ),
        columns=(
            Column("pair", "pair"),
            Column("n", "n", fmt=_fmt_int),
            Column("r_median", "r median", fmt=_fmt_exp),
            Column("r_p90", "r p90", fmt=_fmt_exp),
            Column("threshold_median", "threshold median", fmt=_fmt_exp),
            Column("threshold_p90", "threshold p90", fmt=_fmt_exp),
            Column("verdict", "verdict"),
            Column("hops", "hops"),
            Column("below_resolution", "below resolution", fmt=_fmt_int),
            Column("retried_in_pair", "retried seeds in pair", fmt=_fmt_int),
        ),
        rows=tuple(rows),
        denominator=len(converged),
        denominator_is=(
            f"seeds on which every arm of {configuration} converged"
        ),
        acceptance=True,
        kind="same_optimum",
    )


def iterations(
    campaign: Campaign,
    population: stats_mod.Population,
    configuration: str,
    by_arm: Mapping[str, Mapping[int, Mapping[str, Any]]],
    converged: Sequence[int],
    source: str,
) -> Table | None:
    """Check 2 — the iteration multiplier, in **both** declared constructions.

    The acceptance statistic is the **summed** median; the final attempt's is
    published beside it for comparability with the previous revision.  Both sit
    beside the evaluation count, which is the multiplier the transfer needs and
    which neither iteration construction captures: iterations miss the lifted
    arm's extra stencil column and the line-search evaluations that vary at
    equal iteration count.

    **The evaluation column reads ε** — ``sweeps_per_eval.n_evaluations``
    through :func:`stats.n_evaluations`, the count of ``call_models``
    evaluations summed over the attempts — since task A80
    (report-accuracy-audit) closed issue **I-26**: until then the column read
    the record field ``n_model_calls``, which is the driver's count of
    *sweeps* of the dispatch body (``numerics.n_model_calls``; the copied
    driver declares it not comparable between a flat loop and a block
    schedule), under a heading that said evaluations.  That sweep ratio is
    kept as its own column, **sweeps median**, because the discussion reads
    it (the partitioned arm's dispatch runs ~2.7× as many sweeps, each over a
    third of the map) and a reader wants both numbers side by side.

    The rows are every arm against the flat control, and — as the plan's
    §3.5 declared ("``B1 → B2`` and ``B0 → BR`` reported beside, outside the
    acceptance rule") — the **``B1 → B2`` step itself**, beside, where both
    arms are present: it is the row the pre-declared ``ε = 1`` expectation is
    read from, per seed.
    """
    if BASE_ARM not in by_arm:
        return None
    pairs: list[tuple[str, str]] = [
        (BASE_ARM, arm) for arm in _arm_order(by_arm) if arm != BASE_ARM
    ]
    if all(arm in by_arm for arm in ACCEPTANCE_PAIRS):
        pairs.append(tuple(ACCEPTANCE_PAIRS[:2]))  # the plan's B1 → B2, beside
    rows: list[dict[str, Any]] = []
    for base_arm, arm in pairs:
        seeds = [
            s
            for s in converged
            if s in by_arm[arm] and s in by_arm[base_arm]
        ]
        final_ratios: list[float] = []
        summed_ratios: list[float] = []
        evaluation_ratios: list[float] = []
        sweep_ratios: list[float] = []
        final_sums = [0, 0]
        summed_sums = [0, 0]
        disagreements = 0
        for seed in seeds:
            base_record, arm_record = by_arm[base_arm][seed], by_arm[arm][seed]
            fa = stats_mod.iterations_final_attempt(base_record)
            fb = stats_mod.iterations_final_attempt(arm_record)
            sa = stats_mod.iterations_summed_over_attempts(base_record)
            sb = stats_mod.iterations_summed_over_attempts(arm_record)
            if fa and fb:
                final_ratios.append(fb / fa)
                final_sums[0] += fa
                final_sums[1] += fb
            if sa and sb:
                summed_ratios.append(sb / sa)
                summed_sums[0] += sa
                summed_sums[1] += sb
            if (fa, fb) != (sa, sb):
                disagreements += 1
            ea = stats_mod.n_evaluations(base_record)
            eb = stats_mod.n_evaluations(arm_record)
            if ea and eb:
                evaluation_ratios.append(eb / ea)
            wa = base_record.get("n_model_calls")
            wb = arm_record.get("n_model_calls")
            if wa and wb:
                sweep_ratios.append(wb / wa)
        summed_median = stats_mod.median(summed_ratios)
        accepted_on = base_arm == BASE_ARM and arm in ACCEPTANCE_PAIRS
        rows.append(
            {
                "pair": f"{base_arm} → {arm}"
                + ("" if accepted_on else " (beside)"),
                "n": len(seeds),
                "final_median": stats_mod.median(final_ratios),
                "final_sum_ratio": (
                    (final_sums[1] / final_sums[0]) if final_sums[0] else None
                ),
                "summed_median": summed_median,
                "summed_sum_ratio": (
                    (summed_sums[1] / summed_sums[0]) if summed_sums[0] else None
                ),
                "acceptance": (
                    "beside"
                    if not accepted_on
                    else (
                        "—"
                        if summed_median is None
                        else (
                            "PASS"
                            if summed_median <= campaign.iteration_ratio_max
                            else "FAIL"
                        )
                    )
                ),
                "evaluations_median": stats_mod.median(evaluation_ratios),
                "evaluations_equal": sum(1 for r in evaluation_ratios if r == 1.0),
                "sweeps_median": stats_mod.median(sweep_ratios),
                "attempts": ", ".join(
                    f"{seed}:{stats_mod.n_attempts(by_arm[base_arm][seed])}/"
                    f"{stats_mod.n_attempts(by_arm[arm][seed])}"
                    for seed in seeds
                )
                or "—",
                "constructions_disagree": disagreements,
            }
        )
    return Table(
        name=f"iteration multiplier (check 2) — {configuration} — {source}",
        caption=Caption(
            units="dimensionless ratios of counts",
            row_is="one arm against the flat control over the seed set, and "
            "the B1 → B2 step beside where both arms are present",
            column_is="one of check 2's two iteration constructions, its sum "
            "ratio, the evaluation-count ratio ε beside them, the seeds on "
            "which ε is exactly 1, and the sweep ratio",
            population=(
                f"{population.what}; {len(converged)} seed(s) on which every "
                f"arm of {configuration} reached an accepted optimum"
            ),
            construction=(
                "stats.iterations_summed_over_attempts (the **declared "
                "acceptance statistic**, nearest-rank upper-middle median "
                f"against {campaign.iteration_ratio_max:g}) and "
                "stats.iterations_final_attempt (the previous revision's "
                "construction, published beside for comparability).  Both are "
                "read from attempts[], so a disagreement between them is a "
                "disagreement about that list and not about which field was "
                "read"
            ),
            clauses=(
                "the sum ratio is published beside every median because a "
                "median of per-seed ratios and the ratio of the sums can point "
                "in opposite directions",
                "the evaluation-count ratio ε is beside both: iterations, even "
                "summed, miss the lifted arm's extra stencil column and the "
                "line-search evaluations that vary at equal iteration count.  "
                "It reads stats.n_evaluations (sweeps_per_eval.n_evaluations, "
                "call_models evaluations summed over the attempts) — issue "
                "I-26, closed by task A80 (report-accuracy-audit): until then "
                "this column read n_model_calls, the driver's count of sweeps "
                "of the dispatch body, under a heading that said evaluations",
                "the sweep ratio (n_model_calls, sweeps of the dispatch body "
                "over the whole run) is its own column: a block sweep runs one "
                "module, not all of them, so it is a mechanism, not a cost, and "
                "is never read as ε",
                "*ε = 1 on* counts the seeds on which the two arms took exactly "
                "the same number of evaluations; on the B1 → B2 row it is the "
                "plan's §3.5 pre-declared expectation, per seed",
                "*constructions disagree* counts the seeds on which the final "
                "attempt's pair and the summed pair are not the same numbers — "
                "0 means no run in this population retried",
            ),
            how_to_read=(
                "read the acceptance column against the summed median; a "
                "final-attempt median that differs from it names the retried "
                "seeds, which the attempts column lists"
            ),
            summary=(
                f"Check 2 on {configuration}: the optimiser's iterations "
                f"against B0 over the seed set, summed over attempts (the "
                f"acceptance statistic, median against "
                f"{campaign.iteration_ratio_max:g}) and on the final attempt, "
                f"with the ratio of sums beside; ε is the evaluation-count "
                f"ratio (sweeps_per_eval.n_evaluations, I-26 closed) with the "
                f"seeds on which it is exactly 1, and the sweep ratio is its "
                f"own column. The B1 → B2 row is the plan's pre-declared ε = 1."
            ),
        ),
        columns=(
            Column("pair", "pair"),
            Column("n", "n", fmt=_fmt_int),
            Column("summed_median", "summed median (acceptance)", fmt=_fmt_ratio),
            Column("summed_sum_ratio", "summed sum ratio", fmt=_fmt_ratio),
            Column("acceptance", "verdict"),
            Column("final_median", "final-attempt median", fmt=_fmt_ratio),
            Column("final_sum_ratio", "final-attempt sum ratio", fmt=_fmt_ratio),
            Column("evaluations_median", "ε median (evaluations)", fmt=_fmt_ratio),
            Column("evaluations_equal", "ε = 1 on", fmt=_fmt_int),
            Column("sweeps_median", "sweeps median", fmt=_fmt_ratio),
            Column("attempts", "attempts per seed (base/arm)"),
            Column("constructions_disagree", "constructions disagree", fmt=_fmt_int),
        ),
        rows=tuple(rows),
        denominator=len(converged),
        denominator_is=(
            f"seeds on which every arm of {configuration} converged"
        ),
        acceptance=True,
        kind="iteration_multiplier",
        report_omits=("attempts",),
    )


def attempts(
    population: stats_mod.Population,
    configuration: str,
    by_arm: Mapping[str, Mapping[int, Mapping[str, Any]]],
    source: str,
) -> Table:
    """The summation identity, **printed** rather than assumed."""
    rows: list[dict[str, Any]] = []
    for arm in _arm_order(by_arm):
        for seed in sorted(by_arm[arm]):
            record = by_arm[arm][seed]
            identity = stats_mod.attempt_summation(record)
            parts = identity.get("parts") or {}
            node = parts.get("node_calls_solve_phase") or {}
            sweeps = parts.get("sweeps") or {}
            rows.append(
                {
                    "arm": arm,
                    "seed": seed,
                    "attempts": identity.get("n_attempts", 0),
                    "retried": "yes" if stats_mod.retried(record) else "no",
                    "node_per_attempt": (
                        " + ".join(str(v) for v in node.get("per_attempt") or [])
                        or "—"
                    ),
                    "node_total": node.get("run_total"),
                    "node_residual": node.get("residual"),
                    "sweeps_per_attempt": (
                        " + ".join(str(v) for v in sweeps.get("per_attempt") or [])
                        or "—"
                    ),
                    "sweeps_total": sweeps.get("run_total"),
                    "sweeps_residual": sweeps.get("residual"),
                    "decomposes": (
                        "—"
                        if identity.get("decomposes") is None
                        else ("yes" if identity["decomposes"] else "NO")
                    ),
                }
            )
    checked = [r for r in rows if r["decomposes"] in ("yes", "NO")]
    return Table(
        name=f"the attempt summation identity — {configuration} — {source}",
        caption=Caption(
            units="counts: model executions and sweeps of the model sequence",
            row_is="one optimisation run",
            column_is="the per-attempt costs, the run's solve-phase total they "
            "decompose, and the residual between them",
            population=(
                f"{population.what}; {len(rows)} optimisation run(s) of "
                f"{configuration}, of which {len(checked)} carry a per-attempt "
                f"cost the identity can be checked on"
            ),
            construction=(
                "stats.attempt_summation — Σ over attempts[] against "
                "node_calls_solve_phase and dispatch_sweeps_solve_phase"
            ),
            clauses=(
                "this identity is why the with- and without-retried-seeds cost "
                "ratios may be published: they are computed over quantities "
                "that visibly decompose the published total, and a residual "
                "that is not 0 would make them ratios of something else",
                "the record contract already refuses a record whose parts do "
                "not add up; this table is the same identity stated as a "
                "number a reader can see",
            ),
            how_to_read=(
                "every residual column reads 0, or the run is refused before "
                "it reaches any other table here"
            ),
            summary=(
                f"The attempt-summation identity per run on {configuration}: "
                f"each attempt's node calls and sweeps against the solve-phase "
                f"totals and the residual, which the record contract requires "
                f"to be 0 before a run reaches any other table."
            ),
        ),
        columns=(
            Column("arm", "arm"),
            Column("seed", "seed", fmt=_fmt_int),
            Column("attempts", "attempts", fmt=_fmt_int),
            Column("retried", "retried"),
            Column("node_per_attempt", "node calls per attempt"),
            Column("node_total", "= solve-phase total", fmt=_fmt_int),
            Column("node_residual", "residual", fmt=_fmt_int),
            Column("sweeps_per_attempt", "sweeps per attempt"),
            Column("sweeps_total", "= solve-phase total", fmt=_fmt_int),
            Column("sweeps_residual", "residual", fmt=_fmt_int),
            Column("decomposes", "decomposes"),
        ),
        rows=tuple(rows),
        denominator=len(rows),
        denominator_is=f"optimisation-phase {population.runs_word} of {configuration}",
        acceptance=True,
        kind="attempt_summation",
        detail=True,
    )


def cost(
    population: stats_mod.Population,
    configuration: str,
    by_arm: Mapping[str, Mapping[int, Mapping[str, Any]]],
    converged: Sequence[int],
    source: str,
) -> Table | None:
    """Check 4 — the cost, with and without the retried seeds.

    ``None`` where the arm group carries no flat control: every ratio here is
    against it.
    """
    if BASE_ARM not in by_arm:
        return None
    rows: list[dict[str, Any]] = []
    for arm in _arm_order(by_arm):
        both = stats_mod.with_and_without_retried(
            by_arm[BASE_ARM], by_arm[arm], converged
        )
        finished = [
            by_arm[arm][s]
            for s in converged
            if s in by_arm[arm] and stats_mod.finished(by_arm[arm][s])
        ]
        calls = [r.get("node_calls_solve_phase") for r in finished]
        bracket = stats_mod.seed_bracket([c for c in calls if c is not None])
        rows.append(
            {
                "arm": arm,
                "n": both["with_retried"]["n"],
                "node_calls_mean": (
                    sum(c for c in calls if c is not None) / len(calls)
                    if calls
                    else None
                ),
                "bracket": "—" if bracket is None else f"[{bracket[0]:g}, {bracket[1]:g}]",
                "arrangement_method_calls": sum(
                    (r.get("n_arrangement_method_calls") or 0)
                    for r in finished
                ),
                # The same count per run, so that it sits beside 'node calls /
                # run' in the row's own unit (a per-run mean, D21 (c)); the sum
                # over the set stays beside it and its heading says it is a sum
                # (task A80 (report-accuracy-audit), on A79's finding §7.9).
                "arrangement_method_calls_per_run": (
                    sum((r.get("n_arrangement_method_calls") or 0) for r in finished)
                    / len(finished)
                    if finished
                    else None
                ),
                "with_pooled": both["with_retried"]["pooled"],
                "with_median": both["with_retried"]["median"],
                "with_worse": both["with_retried"]["worse"],
                "n_retried": both["n_retried"],
                "without_pooled": both["without_retried"]["pooled"],
                "without_median": both["without_retried"]["median"],
                "without_n": both["without_retried"]["n"],
            }
        )
    return Table(
        name=f"cost (check 4) — {configuration} — {source}",
        caption=Caption(
            units="model executions during the solve; ratios dimensionless",
            row_is="one arm over the seed set",
            column_is="an absolute per-run mean with its bracket, or one "
            "reading of the ratio against the flat control",
            population=(
                f"{population.what}; {len(converged)} seed(s) on which every "
                f"arm of {configuration} reached an accepted optimum"
            ),
            construction=(
                "stats.with_and_without_retried — solve-phase node calls "
                "**summed over attempts[]** per run, so the ratio is over the "
                "quantity the attempts decompose (the identity is in the "
                "attempt-summation table); pooled = Σ arm / Σ base, median = "
                "nearest-rank upper-middle of the per-seed ratios, worse = "
                "seeds on which the arm cost more"
            ),
            clauses=(
                "**retries are a term, not a footnote**: the ratio is "
                "published *with* and *without* the retried seeds because both "
                "readings are defensible — a retry the other arm did not need "
                "is real cost the architecture avoided at that start, *and* it "
                "is a robustness event rather than a per-evaluation cost",
                "a seed counts as retried when **either** side of the pair "
                "retried: the pair is what the ratio is over",
                "the arrangement-method (prime) calls are two columns of their "
                "own — the per-run mean, in the unit of the node-call column "
                "beside it, and the sum over the arm's runs in the seed set — "
                "and are never pooled into the node calls; on the partitioned "
                "arm there is one such call per sweep of the dispatch body",
                "the output-time and audit sweeps are excluded from this unit "
                "symmetrically in every arm",
            ),
            how_to_read=(
                "where *retried* is 0 the with- and without- columns are the "
                "same number, and the pair of columns is the statement that "
                "nothing in this population depended on a retry"
            ),
            summary=(
                f"Check 4 on {configuration}: solve-phase node calls per run "
                f"by arm over the seed set (mean, bracket) and the ratio "
                f"against B0 pooled and as the per-seed median, with and "
                f"without the seeds on which either side retried. Prime calls "
                f"are columns of their own (per-run mean, and the sum over the "
                f"set); the output path and audit are excluded in every arm."
            ),
        ),
        columns=(
            Column("arm", "arm"),
            Column("n", "n", fmt=_fmt_int),
            Column("node_calls_mean", "node calls / run", fmt=lambda v: "—" if v is None else f"{v:.1f}"),
            Column("bracket", "bracket"),
            Column("arrangement_method_calls_per_run", "arrangement·method calls / run", fmt=lambda v: "—" if v is None else f"{v:.1f}"),
            Column("arrangement_method_calls", "arrangement·method calls, Σ over the set", fmt=_fmt_int),
            Column("with_pooled", "with retried: pooled", fmt=_fmt_ratio),
            Column("with_median", "with retried: median", fmt=_fmt_ratio),
            Column("with_worse", "worse", fmt=_fmt_int),
            Column("n_retried", "retried seeds", fmt=_fmt_int),
            Column("without_pooled", "without retried: pooled", fmt=_fmt_ratio),
            Column("without_median", "without retried: median", fmt=_fmt_ratio),
            Column("without_n", "n without", fmt=_fmt_int),
        ),
        rows=tuple(rows),
        denominator=len(converged),
        denominator_is=(
            f"seeds on which every arm of {configuration} converged"
        ),
        acceptance=True,
        kind="cost",
    )


def lift_closed(
    population: stats_mod.Population,
    configuration: str,
    by_arm: Mapping[str, Mapping[int, Mapping[str, Any]]],
    source: str,
) -> Table | None:
    """Check 3 — constraint 93's residual at every accepted optimum."""
    rows: list[dict[str, Any]] = []
    for arm in _arm_order(by_arm):
        accepted = [
            record
            for seed, record in sorted(by_arm[arm].items())
            if stats_mod.accepted_optimum(record) and record.get("constraint_93")
        ]
        if not accepted:
            continue
        residuals = [
            abs(r["constraint_93"]["residual_s"])
            for r in accepted
            if (r.get("constraint_93") or {}).get("residual_s") is not None
        ]
        relatives = [
            abs(r["constraint_93"]["residual_relative_to_burn_time"])
            for r in accepted
            if (r.get("constraint_93") or {}).get("residual_relative_to_burn_time")
            is not None
        ]
        bracket = stats_mod.seed_bracket(residuals)
        rows.append(
            {
                "arm": arm,
                "n": len(accepted),
                "residual_s_median": stats_mod.median(residuals),
                "bracket": "—" if bracket is None else f"[{bracket[0]:.3e}, {bracket[1]:.3e}]",
                "relative_median": stats_mod.median(relatives),
                "in_equality_block": ", ".join(
                    sorted(
                        {
                            str(r["constraint_93"].get("is_in_equality_block"))
                            for r in accepted
                        }
                    )
                ),
            }
        )
    if not rows:
        return None
    return Table(
        name=f"the lift closed (check 3) — {configuration} — {source}",
        caption=Caption(
            units="seconds for the residual; the relative column is "
            "dimensionless (residual / burn time)",
            row_is="one arm whose runs name the burn-time consistency "
            "constraint",
            column_is="the residual of that constraint at the accepted optima",
            population=(
                f"{population.what}; the accepted optima of {configuration} "
                f"whose input file names constraint 93"
            ),
            construction=(
                "the model's own extracted burn-time consistency relation, "
                "evaluated on the returned state — never read back from an "
                "output table; |value|, median = nearest-rank upper-middle"
            ),
            clauses=(
                "an arm whose input file does not name the constraint is "
                "absent from this table rather than reading 0",
                "residuals at unconverged exits are not here: they belong "
                "beside the failure table and are never pooled with these",
            ),
            how_to_read=(
                "an optimiser that owns the burn time must still satisfy the "
                "relation the model used to assign it, or it has returned a "
                "point that is not on the same manifold"
            ),
            summary=(
                f"Check 3 on {configuration}: the burn-time consistency "
                f"residual (constraint 93) at the accepted optima of the arms "
                f"that own the burn time, in seconds and relative to the burn "
                f"time; an arm not naming the constraint is absent, not 0."
            ),
        ),
        columns=(
            Column("arm", "arm"),
            Column("n", "n accepted", fmt=_fmt_int),
            Column("residual_s_median", "residual, s (median)", fmt=_fmt_exp),
            Column("bracket", "bracket, s"),
            Column("relative_median", "relative (median)", fmt=_fmt_exp),
            Column("in_equality_block", "in the equality block"),
        ),
        rows=tuple(rows),
        denominator=sum(len(v) for v in by_arm.values()),
        denominator_is=f"optimisation-phase {population.runs_word} of {configuration}",
        acceptance=True,
        kind="lift_closed",
    )


def achieved_accuracy(
    campaign: Campaign,
    population: stats_mod.Population,
    configuration: str,
    by_arm: Mapping[str, Mapping[int, Mapping[str, Any]]],
    source: str,
) -> Table:
    """The exit audit at the accepted optimum, on both rulers, with its position.

    The table the audit-position rule exists for.  A campaign-shaped
    optimisation record is audited at the **entry to the output path** — the
    state the solve handed over — and the reproduction gate's records are
    audited **after the run**, where the previous revision measured.  Those are
    two different quantities, and this table carries the position in a column
    of its own so they can share it; a table that mixed them without the column
    would be refused by ``tables.Table``.

    The **argmax component is named, never averaged**: the statistic is one
    component's residual, and the component that holds it is the finding.
    """
    rows: list[dict[str, Any]] = []
    reasons: set[str] = set()
    for arm in _arm_order(by_arm):
        records = [
            by_arm[arm][seed]
            for seed in sorted(by_arm[arm])
            if stats_mod.finished(by_arm[arm][seed])
        ]
        for ruler in campaign.predicate_modes:
            # One construction for n, declared in stats.accuracy_population,
            # and the same one the evaluation phase's table uses: it counts the
            # **runs** this row is over, never the values that happened to
            # exist.
            block = stats_mod.accuracy_population(records, ruler=ruler)
            restricted = block["statistics"]
            restricted_values = block["values"]
            reasons.update(block["reasons"])
            whole = [
                stats_mod.whole_state_statistic(r, ruler=ruler) for r in records
            ]
            whole_values = [v["max"] for v in whole if v.get("max") is not None]
            argmaxes = sorted({v.get("argmax") for v in restricted if v.get("argmax")})
            excluded = sorted(
                {v.get("n_excluded") for v in restricted if v.get("n_excluded") is not None}
            )
            positions = sorted(
                {str(r.get("audit_position")) for r in records if r.get("audit_position")}
            )
            instruments = sorted(
                {stats_mod.audit_instrument(r)["version"] for r in records}
            )
            rows.append(
                {
                    "arm": arm,
                    "ruler": ruler,
                    "n": block["n"],
                    "n_with_the_statistic": block["n_with_the_statistic"],
                    "restricted_median": stats_mod.median(restricted_values),
                    "restricted_max": max(restricted_values) if restricted_values else None,
                    "argmax": (
                        ", ".join(argmaxes)
                        if argmaxes and any(v for v in restricted_values)
                        else (
                            "— (every component exactly 0)"
                            if restricted_values
                            else "—"
                        )
                    ),
                    "n_above_tau": ", ".join(
                        str(v.get("n_above_tau")) for v in restricted
                    ) or "—",
                    "whole_median": stats_mod.median(whole_values),
                    "n_excluded": ", ".join(str(v) for v in excluded) if excluded else "—",
                    "audit_position": positions[0] if len(positions) == 1 else (
                        "/".join(positions) if positions else None
                    ),
                    "instrument": cell_list(instruments),
                }
            )
    positions = sorted({r["audit_position"] for r in rows if r["audit_position"]})
    return Table(
        name=f"achieved accuracy at the accepted optimum — {configuration} — {source}",
        caption=Caption(
            units="dimensionless: the largest scaled coupling-state residual "
            "found by one further full sweep past termination",
            row_is="one arm on one ruler",
            column_is="the restricted or whole-state audit maximum over that "
            "arm's finished runs, the component the restricted maximum sat on, "
            "and how many components the restriction removed",
            population=(
                f"{population.what}; the finished optimisation-phase runs of "
                f"{configuration} in this arm group"
            ),
            construction=(
                "stats.restricted_statistic and stats.whole_state_statistic; "
                "median = nearest-rank upper-middle.  The restricted maximum "
                "excludes the components the configuration's once-per-run "
                "deferred nodes write, derived node → write sets → spec keys"
            ),
            clauses=(
                "**the audit position is a column**: `entry_to_write_output_files` "
                "is the declared position — the state the solve handed over — "
                "and `after_run` is the reproduction gate's, where the previous "
                "revision measured.  The two are different quantities and share "
                "this table only because the position is a column of its own",
                "**the audit instrument's version is read from the record** "
                "(stats.audit_instrument).  Task A61 (insstrain-diagnosis) "
                "showed that the largest residual at the accepted point on the "
                "pulsed configurations is an artefact of this instrument — the "
                "output path permanently changes a model setting the snapshot "
                "does not restore, so the audit's sweep is not the loop's map "
                "— and task A62 (exit-audit-restore) widens the snapshot under "
                "decision D25, which moves every value in these columns.  The "
                "argmax is read from the record and is not written into this "
                "table",
                "**both rulers or neither**: the mixed ruler reads lower "
                "wherever its denominator binds, by construction",
                "the two rulers' exclusion counts are listed per row and never "
                "pooled; a run whose restricted block is null carries no count "
                "and reads —",
                "**n counts runs, not values** (stats.accuracy_population, the "
                "same construction the evaluation phase's table uses): a run "
                "whose audit carries no restricted block is counted in n and "
                "shows in the column beside it, rather than vanishing from the "
                "denominator of a median, which is trap T11; the caption says "
                "whether every run of the population carried it",
            ),
            how_to_read=(
                "read the argmax beside the maximum: a residual above the "
                "tolerance whose argmax is the component A61 named is a "
                "statement about the audit instrument, not about the arm"
            ),
            summary=(
                f"Exit accuracy by arm on {configuration} over the arm "
                f"group's finished runs (accepted or not): the restricted maximum "
                f"scaled residual (median, max) on both rulers, the argmax and "
                f"the whole-state maximum; audit position "
                + (", ".join(positions) if positions else "not recorded")
                + ". The whole-state column is large for B2 by design and is "
                "not judged."
                + (
                    ""
                    if not reasons
                    else " Some runs carried no restricted statistic: "
                    + "; ".join(sorted(reasons))
                    + "."
                )
            ),
        ),
        columns=(
            Column("arm", "arm"),
            Column("ruler", "ruler"),
            Column("n", "n (runs)", fmt=_fmt_int),
            Column("n_with_the_statistic", "with a restricted statistic", fmt=_fmt_int),
            Column("restricted_median", "restricted median", fmt=_fmt_exp),
            Column("restricted_max", "restricted max", fmt=_fmt_exp),
            Column("argmax", "restricted argmax"),
            Column("n_above_tau", "components above τ"),
            Column("whole_median", "whole-state median", fmt=_fmt_exp),
            Column("n_excluded", "components excluded"),
            Column("audit_position", "audit position"),
            Column("instrument", "audit instrument"),
        ),
        rows=tuple(rows),
        denominator=sum(len(v) for v in by_arm.values()),
        denominator_is=(
            f"optimisation-phase runs of {configuration} in this arm group"
        ),
        acceptance=True,
        audit_position_labelled=True,
        kind="achieved_accuracy",
        report_omits=("n_above_tau",),
    )


def per_sweep_overhead(
    population: stats_mod.Population,
    configuration: str,
    by_arm: Mapping[str, Mapping[int, Mapping[str, Any]]],
    source: str,
) -> Table:
    """§3.5 check 5 in the phase that has an optimiser, the predicates apart."""
    rows: list[dict[str, Any]] = []
    for arm in _arm_order(by_arm):
        for seed in sorted(by_arm[arm]):
            record = by_arm[arm][seed]
            if not stats_mod.finished(record):
                continue
            widths = stats_mod.predicate_widths(record)
            shares = stats_mod.empty_visit_shares(record)
            coupling, upstream = widths["coupling_state"], widths["upstream"]
            rows.append(
                {
                    "arm": arm,
                    "seed": seed,
                    "stops_on": widths["stops_on"] or "—",
                    "dispatch_sweeps": record.get("dispatch_sweeps"),
                    "solve_sweeps": record.get("dispatch_sweeps_solve_phase"),
                    "output_loop_sweeps": record.get("output_loop_sweeps"),
                    "coupling_evaluations": coupling["evaluations"],
                    "coupling_components": coupling["components_compared"],
                    "coupling_width": coupling["mean_test_width"],
                    "coupling_width_by_block": (
                        ", ".join(
                            f"{k} {v:.0f}"
                            for k, v in sorted((coupling["by_block"] or {}).items())
                        )
                        or "—"
                    ),
                    "upstream_evaluations": upstream["evaluations"],
                    "upstream_components": upstream["components_compared"],
                    "upstream_width": upstream["mean_test_width"],
                    "empty_sweep_share": shares["sweep_share"],
                }
            )
    shares_seen = sorted(
        {
            round(100 * row["empty_sweep_share"], 2)
            for row in rows
            if row["empty_sweep_share"] is not None
        }
    )
    return Table(
        name=f"per-sweep overhead — {configuration} — {source}",
        caption=Caption(
            units="counts: evaluations of a convergence test, components "
            "compared summed over them, and sweeps of the model sequence",
            row_is="one optimisation run",
            column_is="a counter of one **named** convergence test, or a sweep "
            "total",
            population=(
                f"{population.what}; the finished optimisation-phase {population.runs_word} "
                f"of {configuration}"
            ),
            construction=(
                "stats.predicate_widths and stats.empty_visit_shares, from the "
                "driver's own counters — exact and concurrency-invariant"
            ),
            clauses=(
                "**the two predicates are never pooled**: an arm stops on "
                "exactly one of them and their widths differ by nearly two "
                "orders of magnitude, so their sum belongs to neither.  The "
                "table module refuses a column carrying one",
                "**the empty block visits are counted and disclaimed, never "
                "repaired**, and the share quoted is the **sweep** share — the "
                "fraction of the run's dispatch sweeps those visits cost — "
                "stated per population in the caption.  The visit share is "
                "larger and is never quoted",
                "no conclusion rests on a timing: the question is asked in "
                "counts alone",
            ),
            how_to_read=(
                "read the width column of the test the arm actually stops on; "
                "the other test's columns are 0 for that arm, which is why "
                "they are kept apart"
            ),
            summary=(
                f"Convergence-test cost per finished optimisation on "
                f"{configuration}: dispatch sweeps (solve phase and output-time "
                f"loop apart), and for the test the arm stops on its "
                f"evaluations, components compared and mean width; the two "
                f"predicates are never summed. Empty-visit sweep share: "
                + (
                    ", ".join(f"{v:g} %" for v in shares_seen)
                    if shares_seen
                    else "not computable on any run here"
                )
                + "."
            ),
        ),
        columns=(
            Column("arm", "arm"),
            Column("seed", "seed", fmt=_fmt_int),
            Column("stops_on", "stops on"),
            Column("dispatch_sweeps", "dispatch sweeps", fmt=_fmt_int),
            Column("solve_sweeps", "of which solve phase", fmt=_fmt_int),
            Column("output_loop_sweeps", "output-time loop", fmt=_fmt_int),
            Column("coupling_evaluations", "coupling-state tests", predicate="coupling_state", fmt=_fmt_int),
            Column("coupling_components", "components compared", predicate="coupling_state", fmt=_fmt_int),
            Column("coupling_width", "mean width", predicate="coupling_state", fmt=lambda v: "—" if v is None else f"{v:.1f}"),
            Column("coupling_width_by_block", "width by block", predicate="coupling_state"),
            Column("upstream_evaluations", "objective/constraint tests", predicate="upstream", fmt=_fmt_int),
            Column("upstream_components", "values compared", predicate="upstream", fmt=_fmt_int),
            Column("upstream_width", "mean width", predicate="upstream", fmt=lambda v: "—" if v is None else f"{v:.1f}"),
            Column("empty_sweep_share", "empty-visit sweep share", fmt=lambda v: "—" if v is None else f"{100 * v:.2f} %"),
        ),
        rows=tuple(rows),
        denominator=len(rows),
        denominator_is=(
            f"finished optimisation-phase {population.runs_word} of {configuration}"
        ),
        acceptance=True,
        kind="per_sweep_overhead",
        detail=True,
    )


# --------------------------------------------------------------------------
# the headline tables (task A79 (report-captions), 2026-09-15)
# --------------------------------------------------------------------------


def _fmt_calls(value: Any) -> str:
    return "—" if value is None else f"{value:.1f}"


def _fmt_path(value: Any) -> str:
    """A path quantity: whole numbers above a thousand, four significant below."""
    if value is None:
        return "—"
    return f"{value:.0f}" if abs(value) >= 1000 else f"{value:.4g}"


def _summed_solve_calls(record: Mapping[str, Any]) -> float | None:
    """Solve-phase node calls summed over attempts[] — check 4's unit."""
    values = stats_mod.node_calls_by_attempt(record)
    if not values or any(v is None for v in values):
        return None
    return float(sum(int(v) for v in values))



def module_sweeps(
    campaign: Campaign,
    population: stats_mod.Population,
    configuration: str,
    by_arm: Mapping[str, Mapping[int, Mapping[str, Any]]],
    converged: Sequence[int],
    source: str,
) -> Table | None:
    """**Module sweeps per run** — the optimisation phase's per-module headline.

    The previous revision's §5.5.1, reproduced: one block per configuration,
    one row per node group and a **total calls** row, ``models`` the group's
    collapsed-DSM row count, and per arm the **number of times that group was
    swept in the whole run** as the mean over the seed set with its
    ``[min, max]`` bracket.  Beside them the pooled ratio of the partitioned
    arm to the flat one, that ratio's **per-run** distribution (median with
    its bracket), and the count of runs on which the partitioned arm swept the
    group **more** — which the pooled ratio does not show.

    The cell is a sweep count for the same reason as the evaluation phase's:
    every node of a group runs once per sweep, and
    :func:`stats.module_sweeps` refuses the run where they did not.  The
    census counts the **whole run** — every attempt, the output path and the
    exit audit's one sweep.  Neither cancels from a ratio: the output path
    is architecture and differs by arm (two MDA_Output sweeps of every node in
    ``BR``/``B0``, none in ``B1``, one execution of each once-per-run node in
    ``B2``), and the audit adds one sweep of every node in every arm.  The
    caption says so.  (Until 2026-09-28 it said the output pass added one sweep
    to every row and cancelled — the previous revision's wording, which the
    records' own per-node census contradicts.)
    """
    base, arm = HEADLINE_PAIR
    if base not in by_arm or arm not in by_arm:
        return None
    from harness.measurement import tally_evaluation as tally_a  # noqa: PLC0415

    seeds = [
        s
        for s in converged
        if s in by_arm[base]
        and s in by_arm[arm]
        and stats_mod.finished(by_arm[base][s])
        and stats_mod.finished(by_arm[arm][s])
    ]
    records = [
        by_arm[a][s]
        for a in _arm_order(by_arm)
        for s in converged
        if s in by_arm[a] and stats_mod.finished(by_arm[a][s])
    ]
    if not records:
        return None
    groups = tally_a.node_grouping(campaign, configuration, records, phase=PHASE)
    node_map = json.loads(
        (Path(campaign.data_dir) / "dsm_node_map.json").read_text()
    )
    models = stats_mod.dsm_rows_by_group(node_map, groups)

    def sweeps_of(record: Mapping[str, Any]) -> dict[str, float]:
        return stats_mod.module_sweeps(
            stats_mod.per_node_census(record, phase=PHASE), groups
        )

    values: dict[str, dict[str, list[float]]] = {}
    totals: dict[str, dict[str, list[float]]] = {}
    for a in _arm_order(by_arm):
        for s in converged:
            record = by_arm[a].get(s)
            if record is None or not stats_mod.finished(record):
                continue
            sweeps = sweeps_of(record)
            for group, value in sweeps.items():
                values.setdefault(group, {}).setdefault(a, []).append(value)
            for case in ("v1", "v0"):
                total = stats_mod.weighted_total(sweeps, models, case=case)
                if total is not None:
                    totals.setdefault(case, {}).setdefault(a, []).append(total)

    rows: list[dict[str, Any]] = []
    for group in groups:
        name = str(group["group"])
        row: dict[str, Any] = {
            "module": name,
            "models": models[name]["v1"],
        }
        for a in LADDER:
            arm_values = values.get(name, {}).get(a, [])
            row[f"{a}_mean"] = (
                (sum(arm_values) / len(arm_values)) if arm_values else None
            )
            bracket = stats_mod.seed_bracket(arm_values)
            row[f"{a}_bracket"] = (
                "—" if bracket is None else f"[{bracket[0]:g}, {bracket[1]:g}]"
            )
        summary = stats_mod.per_seed_ratio_summary(
            [sweeps_of(by_arm[base][s]).get(name, 0.0) for s in seeds],
            [sweeps_of(by_arm[arm][s]).get(name, 0.0) for s in seeds],
        )
        row.update(
            {
                "pooled": summary["pooled"],
                "median": summary["median"],
                "bracket": (
                    "—"
                    if summary["min"] is None
                    else f"[{summary['min']:.3f}, {summary['max']:.3f}]"
                ),
                "n_above_one": summary["n_above_one"],
                "n_pairs": summary["n"],
            }
        )
        rows.append(row)

    total: dict[str, Any] = {
        "module": tally_a.TOTAL_ROW,
        "models": sum(models[str(g["group"])]["v1"] for g in groups),
    }
    for a in LADDER:
        arm_values = totals.get("v1", {}).get(a, [])
        total[f"{a}_mean"] = (
            (sum(arm_values) / len(arm_values)) if arm_values else None
        )
        total[f"{a}_bracket"] = "—"
    pooled_both: list[float] = []
    for case in ("v1", "v0"):
        left = [
            stats_mod.weighted_total(sweeps_of(by_arm[base][s]), models, case=case)
            or 0.0
            for s in seeds
        ]
        right = [
            stats_mod.weighted_total(sweeps_of(by_arm[arm][s]), models, case=case)
            or 0.0
            for s in seeds
        ]
        if sum(left):
            pooled_both.append(sum(right) / sum(left))
    summary = stats_mod.per_seed_ratio_summary(
        [
            stats_mod.weighted_total(sweeps_of(by_arm[base][s]), models, case="v1")
            or 0.0
            for s in seeds
        ],
        [
            stats_mod.weighted_total(sweeps_of(by_arm[arm][s]), models, case="v1")
            or 0.0
            for s in seeds
        ],
    )
    total.update(
        {
            "pooled": (
                f"[{min(pooled_both):.3f}, {max(pooled_both):.3f}]"
                if len(pooled_both) == 2
                else None
            ),
            "median": summary["median"],
            "bracket": (
                "—"
                if summary["min"] is None
                else f"[{summary['min']:.3f}, {summary['max']:.3f}]"
            ),
            "n_above_one": summary["n_above_one"],
            "n_pairs": summary["n"],
        }
    )
    rows.append(total)

    executed = int(
        ((node_map.get("units") or {}).get("dsm_rows") or {}).get(
            "executed_in_a_sweep"
        )
        or 0
    )
    return Table(
        name=f"module sweeps per run — {configuration} — {source}",
        caption=Caption(
            units=(
                "sweeps of a node group per optimisation run; `models` is a "
                "count of collapsed-DSM rows; the total row is "
                "Σ sweeps × models, a count of DSM-row executions; ratios are "
                "dimensionless"
            ),
            row_is=(
                "one node group of this configuration — the three modules, the "
                "pulse node, the feed-forward tail and the once-per-run "
                "deferred nodes as the committed node map and the "
                "configuration's per-run artifact place them — then the total "
                "over those rows"
            ),
            column_is=(
                "the group's collapsed-DSM row count, or one arm's mean sweeps "
                "of that group per run over the seed set with the observed "
                "[min, max] bracket, or one of the three readings of B2 "
                "against B0: pooled, the per-run median with its bracket, and "
                "the count of runs on which B2 swept the group more"
            ),
            population=(
                f"{population.what}; {len(converged)} seed(s) on which every "
                f"arm of {configuration} reached an accepted optimum"
            ),
            construction=(
                "stats.module_sweeps — the census count every node of the "
                "group shares (node_census.per_node_counted, the whole run), "
                "the construction refusing the run if the group's nodes did "
                "not execute together; stats.per_seed_ratio_summary for the "
                "three readings of the ratio; the total row is "
                "stats.weighted_total (Σ sweeps × models) with models from "
                "stats.dsm_rows_by_group"
            ),
            clauses=(
                "a cell is a **sweep** count, not a node-call count: within a "
                "group every model node runs once per sweep, so a per-module "
                "ratio does not depend on whether one counts model calls or "
                "DSM rows",
                "the total does depend on it, and its ratio cell is the "
                "interval over the two defensible attributions of the "
                "once-per-run nodes' DSM rows — `[v = 1, v = 0]` (trap T9: "
                "per-node DSM rows are not readable in this repository); the "
                "per-arm total cells and the per-run distribution are the "
                "v = 1 case",
                "these are whole-run census counts: they include the output path — two MDA_Output sweeps of every node in `BR` and `B0`, none in `B1`, one execution of each once-per-run node in `B2` — and the exit audit's one sweep of every node in every arm, which is the harness's accuracy instrument and no arm's architecture. Neither cancels from a ratio: the audit's sweep moves a ratio by under 0.2 % in every row but the once-per-run one, where it is half of `B2`'s count, and the output path differs by arm; check 4's cost table sums the solve phase alone",
                f"the committed node map states {executed} DSM rows execute in "
                f"a sweep and this configuration attributes "
                f"{int(total['models'])} of them; the remainder are rows of "
                f"nodes that execute on no configuration of this experiment "
                f"and are in no row",
                "reported, not accepted on: the acceptance quantity is check "
                "4's solve-phase cost table",
            ),
            how_to_read=(
                "read the ratio column down the modules — it is the result, "
                "and it is unit-free; then read the last two columns, which "
                "say whether the pooled ratio holds run by run"
            ),
            summary=(
                f"Module sweeps per run on {configuration} over its seed set: "
                f"how often each node group was swept in one optimisation, as "
                f"the mean with its [min, max] bracket (a bare integer where "
                f"every run agreed). `models` is the group's collapsed-DSM row "
                f"count, so total calls = Σ sweeps × models, bracketed over "
                f"the once-per-run nodes' unknown rows. Whole-run census "
                f"counts: they include the output path and the exit audit's one "
                f"sweep, and neither cancels from a ratio. Reported, not accepted on."
            ),
        ),
        columns=(
            Column("module", "module"),
            Column("models", "models", fmt=_fmt_int),
            *[
                item
                for a in LADDER
                for item in (
                    Column(f"{a}_mean", f"{a} mean", fmt=sweep_cell),
                    Column(f"{a}_bracket", f"{a} [min, max]"),
                )
            ],
            Column("pooled", "B2/B0 pooled", fmt=_fmt_cell),
            Column("median", "B2/B0 per-run median", fmt=_fmt_ratio),
            Column("bracket", "[min, max]"),
            Column("n_above_one", "runs B2 > B0", fmt=_fmt_int),
            Column("n_pairs", "of n", fmt=_fmt_int),
        ),
        rows=tuple(rows),
        denominator=len(converged),
        denominator_is=(
            f"seed(s) on which every arm of {configuration} converged"
        ),
        kind="module_sweeps",
    )


def node_calls_per_module(
    campaign: Campaign,
    population: stats_mod.Population,
    configuration: str,
    by_arm: Mapping[str, Mapping[int, Mapping[str, Any]]],
    converged: Sequence[int],
    source: str,
) -> Table | None:
    """The report's headline shape 1: node calls per module, one configuration.

    Over the seed set.  One row per node group (``tally_evaluation.node_grouping``
    — the committed node map's modules, the once-per-run deferred nodes as
    their own group), then **all counted nodes** (the whole-run census total)
    and **of which outside the solve phase** (that total less the solve-phase
    total of check 4: the output path and the exit audit's one sweep, which
    the census counts per node and check 4 excludes).  Per arm the per-run
    mean and ``[min, max]``; for B2 against B0 the pooled ratio, the per-run
    median with its bracket, and the count of runs on which B2 cost more.
    ``None`` where the group lacks either arm of the pair.
    """
    base, arm = HEADLINE_PAIR
    if base not in by_arm or arm not in by_arm:
        return None
    from harness.measurement import tally_evaluation as tally_a  # noqa: PLC0415

    seeds = [
        s for s in converged
        if s in by_arm[base] and s in by_arm[arm]
        and stats_mod.finished(by_arm[base][s]) and stats_mod.finished(by_arm[arm][s])
    ]
    records = [
        by_arm[a][s]
        for a in _arm_order(by_arm)
        for s in converged
        if s in by_arm[a] and stats_mod.finished(by_arm[a][s])
    ]
    if not records:
        return None
    groups = tally_a.node_grouping(campaign, configuration, records, phase=PHASE)
    all_nodes = [n for g in groups for n in g["nodes"]]

    def per_run(record: Mapping[str, Any]) -> dict[str, float]:
        counted = stats_mod.per_node_census(record, phase=PHASE)
        grouped: dict[str, float] = dict(stats_mod.census_by_group(counted, groups))
        total = float(sum(counted.values()))
        grouped["all counted nodes"] = total
        solve = _summed_solve_calls(record)
        grouped["of which outside the solve phase"] = (
            None if solve is None else total - solve
        )
        return grouped

    values: dict[str, dict[str, list[float]]] = {}
    for a in _arm_order(by_arm):
        for s in converged:
            record = by_arm[a].get(s)
            if record is None or not stats_mod.finished(record):
                continue
            for group, calls in per_run(record).items():
                values.setdefault(group, {}).setdefault(a, []).append(calls)
    labels = (
        [(g["group"], g["nodes"]) for g in groups]
        + [("all counted nodes", all_nodes), ("of which outside the solve phase", [])]
    )
    rows: list[dict[str, Any]] = []
    for group, nodes in labels:
        row: dict[str, Any] = {
            "module": group,
            "n_nodes": len(nodes) if group != "of which outside the solve phase" else None,
            "nodes": (
                tally_a.group_members(campaign, group, nodes)
                if group not in ("all counted nodes", "of which outside the solve phase")
                else ("every node above" if group == "all counted nodes" else "the output path and the exit audit's sweep")
            ),
        }
        for a in LADDER:
            arm_values = [v for v in values.get(group, {}).get(a, []) if v is not None]
            row[f"{a}_mean"] = (sum(arm_values) / len(arm_values)) if arm_values else None
            bracket = stats_mod.seed_bracket(arm_values)
            row[f"{a}_bracket"] = "—" if bracket is None else f"[{bracket[0]:g}, {bracket[1]:g}]"
        left = [per_run(by_arm[base][s])[group] for s in seeds]
        right = [per_run(by_arm[arm][s])[group] for s in seeds]
        pairs = [(a_, b_) for a_, b_ in zip(left, right) if a_ is not None and b_ is not None]
        summary = stats_mod.per_seed_ratio_summary(
            [a_ for a_, _ in pairs], [b_ for _, b_ in pairs]
        )
        row.update(
            {
                "pooled": summary["pooled"],
                "median": summary["median"],
                "bracket": (
                    "—"
                    if summary["min"] is None
                    else f"[{summary['min']:.3f}, {summary['max']:.3f}]"
                ),
                "n_above_one": summary["n_above_one"],
                "n_pairs": summary["n"],
            }
        )
        rows.append(row)
    return Table(
        name=f"node calls per module — {configuration} — {source}",
        caption=Caption(
            units="model-node executions per optimisation run, per node "
            "group; ratios dimensionless",
            row_is="one node group of the configuration (the three modules, "
            "the pulse node, the feed-forward tail and the once-per-run "
            "deferred nodes, as the committed node map and the per-run "
            "artifact place them), then every counted node, then the part of "
            "that total outside the solve phase",
            column_is="per arm, the per-run mean and [min, max] over the seed "
            "set; for B2 against B0, the pooled ratio, the per-run median "
            "with its [min, max], and the count of runs on which B2 cost more",
            population=(
                f"{population.what}; {len(converged)} seed(s) on which every "
                f"arm of {configuration} reached an accepted optimum"
            ),
            construction=(
                "stats.per_node_census (node_census.per_node_counted — the "
                "whole run: every attempt, the output path and the exit "
                "audit's one sweep) summed over each group of "
                "stats.node_groups; means and stats.seed_bracket over the "
                "arm's runs in the seed set; the B2/B0 columns are "
                "stats.per_seed_ratio_summary over the paired runs (pooled = "
                "Σ B2 / Σ B0; median = nearest-rank upper-middle of the per-run "
                "ratios; runs B2 > B0 = ratio above 1).  The *outside the "
                "solve phase* row is the census total less the solve-phase "
                "node calls summed over attempts[] — check 4's unit — so the "
                "two tables reconcile by subtraction"
            ),
            clauses=(
                "the census counts the whole run, so a module's calls include "
                "its share of the output path (two sweeps in BR and B0, one "
                "call per deferred node in B1 and B2) and of the audit's one "
                "sweep; the last row states that share and it is not "
                "apportioned to the modules",
                "the once-per-run group holds the configuration's deferred "
                "nodes whatever module the map assigns them: B2 runs them once "
                "per run, the flat arms every sweep",
                "the arrangement-method (prime) calls are not model nodes and "
                "are in no row; check 4's table carries them beside",
            ),
            how_to_read=(
                "read the B2/B0 column down the modules: a module near 1 is "
                "solved about as often as the flat arm sweeps it; the "
                "once-per-run row is the deferral's whole saving"
            ),
            summary=(
                f"Node calls per run by node group and arm on {configuration} "
                f"over the seed set (mean, [min, max]); B2 against B0 pooled, "
                f"as the per-run median with its bracket and as runs on which "
                f"B2 cost more. Whole-run census counts: the last row is the "
                f"part outside the solve phase, so *all counted nodes* less it "
                f"is check 4's total."
            ),
        ),
        columns=(
            Column("module", "module"),
            Column("n_nodes", "nodes", fmt=_fmt_int),
            Column("nodes", "which"),
            *[
                col
                for a in LADDER
                for col in (
                    Column(f"{a}_mean", f"{a} mean", fmt=_fmt_calls),
                    Column(f"{a}_bracket", f"{a} [min, max]"),
                )
            ],
            Column("pooled", "B2/B0 pooled", fmt=_fmt_ratio),
            Column("median", "B2/B0 per-run median", fmt=_fmt_ratio),
            Column("bracket", "[min, max]"),
            Column("n_above_one", "runs B2 > B0", fmt=_fmt_int),
            Column("n_pairs", "of n", fmt=_fmt_int),
        ),
        rows=tuple(rows),
        denominator=len(converged),
        denominator_is=f"seeds on which every arm of {configuration} converged",
        acceptance=True,
        kind="node_calls_per_module",
    )


#: The optimiser's path, quantity by quantity: the label the table prints,
#: and the construction that reads one run.  ``R = ρ × ε`` holds per run by
#: construction (ρ is R / ε), which is why the four rows are one table.
# --------------------------------------------------------------------------
# the previous revision's §5 cross-configuration shapes (task A86
# (v3-tables-remainder), 2026-09-15)
# --------------------------------------------------------------------------

#: The pairs the location diagnostic and the identity table read, in the
#: order they print: check 1's own pairs, then the partition at an unchanged
#: trajectory.  ``None`` in the second slot means "every other arm".
DIAGNOSTIC_PAIRS: tuple[tuple[str, str], ...] = (
    YARDSTICK_PAIR,
    (BASE_ARM, "B1"),
    (BASE_ARM, "B2"),
    ("B1", "B2"),
)

#: The arms that solve the configuration's own problem, and the arms that
#: solve the problem after the burn-time lift.  Derived from the ladder's
#: rungs (plan §3.3): the ownership rung ``B0 → B1`` is where the lift enters,
#: so everything from ``B1`` on carries it.
UNLIFTED_ARMS: tuple[str, ...] = LADDER[: LADDER.index("B1")]
LIFTED_ARMS: tuple[str, ...] = LADDER[LADDER.index("B1") :]

#: The pair the identity table is about: the partition at an unchanged
#: optimiser trajectory.  The previous revision proved the same thing one
#: rung over, for its trust step.
IDENTITY_PAIR: tuple[str, str] = ("B1", "B2")


def _objective_pairs(
    by_arm: Mapping[str, Mapping[int, Mapping[str, Any]]],
    a: str,
    b: str,
    converged: Sequence[int],
) -> tuple[list[float], list[int]]:
    """Check 1's relative objective difference per seed, and the seeds."""
    values: list[float] = []
    seeds: list[int] = []
    for seed in converged:
        ra, rb = by_arm.get(a, {}).get(seed), by_arm.get(b, {}).get(seed)
        if not (ra and rb):
            continue
        fa = _hexf((ra.get("exact") or {}).get("norm_objf"))
        fb = _hexf((rb.get("exact") or {}).get("norm_objf"))
        if fa is None or fb is None:
            continue
        values.append(stats_mod.relative_objective_difference(fa, fb))
        seeds.append(seed)
    return values, seeds


def location_diagnostic(
    campaign: Campaign,
    population: stats_mod.Population,
    source: str,
    groups: Sequence[Any],
) -> Table | None:
    """**Where the arms actually landed** — the previous revision's §5.2.2.

    One row per configuration and arm pair: check 1's objective agreement
    repeated for direct comparison, then the **maximum over iteration
    variables of the per-variable relative difference** on the unscaled
    accepted design vector, as the median, p90 and maximum over the pair's
    seeds, with the argmax variable named and the count of shared variables
    beside the name of any variable one side carries and the other does not.

    Variables are matched **by name** (:func:`stats.iteration_variables`),
    never by index: the lift adds ``t_plant_pulse_burn``, so the lifted arms
    carry one more iteration variable than the flat ones on a pulsed
    configuration, and the unshared variable is named and never compared.

    **This is a diagnostic. D6 forbids gating on it, and nothing in this
    report's verdicts rests on it.**
    """
    rows: list[dict[str, Any]] = []
    n_pairs_total = 0
    for configuration, arms, by_arm, converged in groups:
        for a, b in DIAGNOSTIC_PAIRS:
            if a not in by_arm or b not in by_arm:
                continue
            objective, seeds = _objective_pairs(by_arm, a, b, converged)
            distances: list[float] = []
            argmaxes: dict[str, int] = {}
            extra: list[str] = []
            shared: set[int] = set()
            for seed in seeds:
                left = stats_mod.iteration_variables(by_arm[a][seed])
                right = stats_mod.iteration_variables(by_arm[b][seed])
                difference = stats_mod.point_difference(left, right)
                if difference["max"] is None:
                    continue
                distances.append(difference["max"])
                shared.add(difference["n_shared"])
                if difference["argmax"]:
                    argmaxes[difference["argmax"]] = (
                        argmaxes.get(difference["argmax"], 0) + 1
                    )
                for name in difference["extra"]:
                    if name not in extra:
                        extra.append(name)
            bracket = stats_mod.seed_bracket(distances)
            census = sorted(argmaxes.items(), key=lambda kv: (-kv[1], kv[0]))
            n_pairs_total += len(seeds)
            rows.append(
                {
                    "configuration": configuration,
                    "pair": f"{a} → {b}"
                    + (" (yardstick)" if (a, b) == YARDSTICK_PAIR else ""),
                    "n": len(seeds),
                    "objf_median": stats_mod.median(objective),
                    "objf_p90": stats_mod.p90(objective),
                    "point_median": stats_mod.median(distances),
                    "point_p90": stats_mod.p90(distances),
                    "point_max": None if bracket is None else bracket[1],
                    "shared": (
                        "; ".join(str(v) for v in sorted(shared))
                        if shared
                        else "—"
                    ),
                    "extra": cell_list(extra),
                    "argmax": cell_list(
                        [f"{name} ({n}/{len(distances)})" for name, n in census[:3]]
                    ),
                }
            )
    if not rows:
        return None
    return Table(
        name=f"location diagnostic — {source}",
        caption=Caption(
            units="dimensionless: relative differences of the normalised "
            "objective and of an iteration variable",
            row_is="one arm pair of one configuration over its seed set",
            column_is="an order statistic of the pair's objective difference "
            "or of its design-point difference, the variable the point "
            "difference sat on most often, or the variables the two sides do "
            "not share",
            population=(
                f"{population.what}; {n_pairs_total} pair(s) over the "
                f"configurations' seed sets"
            ),
            construction=(
                "stats.iteration_variables joins the output file's itvars to "
                "its itvar_names **on the solver's slot** and refuses a "
                "record with a value in a slot the name map does not carry; "
                "stats.point_difference is the maximum over the shared names "
                "of |Δx| / max(|x_a|, |x_b|) on the unscaled vector, with the "
                "argmax named; median = nearest-rank upper-middle, p90 = "
                "nearest-rank ceil(0.9 n); the objective columns are "
                "stats.relative_objective_difference, check 1's own"
            ),
            clauses=(
                "**This is a diagnostic. D6 forbids gating on it, and "
                "nothing in this report's verdicts rests on it** — some "
                "iteration variables are not identified by the problem and "
                "differ at an unchanged optimum",
                "variables are matched **by name**, never by index: the lift "
                "adds `t_plant_pulse_burn`, so a lifted arm carries one more "
                "iteration variable than a flat one on a pulsed "
                "configuration; the unshared variable is named in its own "
                "column and never compared",
                "the yardstick pair is a change of **stopping rule** and "
                "nothing else; where it moves the point as far as an "
                "architectural rung does, non-identification is a property "
                "of the configuration and not of the partition",
                "the objective columns are check 1's, repeated here so the "
                "two questions — how good, and where — are read side by side",
            ),
            how_to_read=(
                "read the objective columns against the point columns on one "
                "row: agreement to thirteen digits on the first with a "
                "per-cent difference on the second is a weakly identified "
                "direction, not a disagreement about the optimum"
            ),
            summary=(
                "Where each pair of arms landed, by configuration: check 1's "
                "objective difference beside the maximum relative difference "
                "over the **iteration variables**, matched by name, as median, "
                "p90 and maximum, with the argmax variable named and any "
                "variable one side alone carries. **A diagnostic, never an "
                "acceptance** (D6): some iteration variables are not "
                "identified by the problem and differ at an unchanged optimum."
            ),
        ),
        columns=(
            Column("configuration", "configuration"),
            Column("pair", "pair"),
            Column("n", "n", fmt=_fmt_int),
            Column("objf_median", "objf med", fmt=_fmt_exp),
            Column("objf_p90", "objf p90", fmt=_fmt_exp),
            Column("point_median", "point med", fmt=_fmt_exp),
            Column("point_p90", "point p90", fmt=_fmt_exp),
            Column("point_max", "point max", fmt=_fmt_exp),
            Column("shared", "shared vars"),
            Column("extra", "extra vars"),
            Column("argmax", "argmax census"),
        ),
        rows=tuple(rows),
        denominator=n_pairs_total,
        denominator_is=(
            "arm-pair comparisons over the configurations' seed sets"
        ),
        kind="location_diagnostic",
    )


def identity(
    population: stats_mod.Population,
    source: str,
    groups: Sequence[Any],
) -> Table | None:
    """**The partition at an unchanged trajectory** — the §5.3 identity table.

    One row per configuration: over the pairs on which **both** arms reached
    an accepted optimum, how many ran the identical number of evaluations of
    the model set, the identical number of optimiser iterations, and reached
    a **bit-identical** ``norm_objf`` — compared as the hex float the record
    stamps, so "identical" is exact and not "within noise".

    The previous revision's table proved its trust step left the optimiser's
    path unchanged; this proves the **partition** does, one rung over.
    """
    a, b = IDENTITY_PAIR
    rows: list[dict[str, Any]] = []
    total = 0
    for configuration, arms, by_arm, converged in groups:
        if a not in by_arm or b not in by_arm:
            continue
        pairs = [
            seed
            for seed in converged
            if seed in by_arm[a]
            and seed in by_arm[b]
            and stats_mod.accepted_optimum(by_arm[a][seed])
            and stats_mod.accepted_optimum(by_arm[b][seed])
        ]
        total += len(pairs)

        def _same(seed: int, read) -> bool | None:
            left, right = read(by_arm[a][seed]), read(by_arm[b][seed])
            return None if left is None or right is None else left == right

        def _count(read) -> int:
            return sum(1 for seed in pairs if _same(seed, read) is True)

        rows.append(
            {
                "configuration": configuration,
                "pair": f"{a} → {b}",
                "pairs": len(pairs),
                "evaluations_identical": _count(stats_mod.n_evaluations),
                "iterations_identical": _count(
                    stats_mod.iterations_summed_over_attempts
                ),
                "objf_identical": _count(
                    lambda record: (record.get("exact") or {}).get("norm_objf")
                ),
            }
        )
    if not rows:
        return None
    return Table(
        name=f"the identity B1 → B2 — {source}",
        caption=Caption(
            units="counts of seeds",
            row_is="one configuration",
            column_is="how many of the configuration's both-accepted pairs "
            "agree exactly on one quantity",
            population=(
                f"{population.what}; {total} pair(s) on which both arms of "
                f"{a} → {b} reached an accepted optimum"
            ),
            construction=(
                "stats.n_evaluations (sweeps_per_eval.n_evaluations) and "
                "stats.iterations_summed_over_attempts compared as integers; "
                "the objective compared as the **hex float** the record "
                "stamps (`exact.norm_objf`), so identity is bit identity and "
                "not agreement to a printed precision"
            ),
            clauses=(
                "a pair counts only where both sides reached an accepted "
                "optimum; the seeds outside that set are the failure table's",
                "integers are compared exactly, so *identical* here is exact "
                "and never 'within noise'",
                "this is the **partition** at an unchanged trajectory: the "
                "two arms differ by the partition alone, both carrying the "
                "lift and the prime",
            ),
            how_to_read=(
                "a count equal to the pair count says the partition changed "
                "nothing about the path the optimiser took, only what each "
                "step cost"
            ),
            summary=(
                f"The partition at an unchanged trajectory, by configuration: "
                f"over the pairs on which both {a} and {b} reached an accepted "
                f"optimum, how many agree exactly on evaluations of the model "
                f"set, on optimiser iterations, and on a bit-identical "
                f"`norm_objf` (compared as the stamped hex float). `B1` is "
                f"inactive on `st_regression`, which therefore has no row."
            ),
        ),
        columns=(
            Column("configuration", "configuration"),
            Column("pair", "pair"),
            Column("pairs", "pairs", fmt=_fmt_int),
            Column("evaluations_identical", "evaluations identical", fmt=_fmt_int),
            Column("iterations_identical", "iterations identical", fmt=_fmt_int),
            Column("objf_identical", "objf bit-identical", fmt=_fmt_int),
        ),
        rows=tuple(rows),
        denominator=total,
        denominator_is=(
            f"pairs on which both arms of {a} → {b} reached an accepted optimum"
        ),
        kind="identity",
    )


def _set_members(
    by_arm: Mapping[str, Mapping[int, Mapping[str, Any]]],
    converged: Sequence[int],
    *, without_retried: bool,
) -> list[int]:
    """One of check 4's two published seed sets."""
    if not without_retried:
        return list(converged)
    return [
        seed
        for seed in converged
        if not any(
            stats_mod.retried(rows[seed])
            for rows in by_arm.values()
            if seed in rows
        )
    ]


COST_SETS: tuple[tuple[str, bool], ...] = (
    ("every arm accepted", False),
    ("without retried seeds", True),
)


def _summed_over(
    by_arm: Mapping[str, Mapping[int, Mapping[str, Any]]],
    arm: str,
    seeds: Sequence[int],
) -> float | None:
    values = [
        _summed_solve_calls(by_arm[arm][seed])
        for seed in seeds
        if seed in by_arm.get(arm, {})
    ]
    values = [v for v in values if v is not None]
    return sum(values) if values else None


def cost_sums(
    population: stats_mod.Population,
    source: str,
    groups: Sequence[Any],
) -> Table | None:
    """**Check 4's cost as sums over a seed set** — the previous revision's §5.5.

    One row per configuration and published set, one column per arm holding
    the **summed solve-phase node calls** over that set, and the ratio of the
    partitioned arm to the flat control.  The same quantity the per-arm cost
    table states as a per-run mean, summed: the claim is about total work
    over the campaign, which is what a deployment question asks.

    V4's two sets are not the previous revision's.  It published
    identical-**ok** and identical-**converged**; V4 has one acceptance set —
    the seeds on which every arm reached an accepted optimum — and publishes
    the retried-seed exclusion beside it, because a retry is a robustness
    event and a cost at once (the cost table's two ratio pairs).
    """
    rows: list[dict[str, Any]] = []
    n_rows = 0
    for configuration, arms, by_arm, converged in groups:
        if BASE_ARM not in by_arm:
            continue
        for label, without in COST_SETS:
            seeds = _set_members(by_arm, converged, without_retried=without)
            row: dict[str, Any] = {
                "configuration": configuration,
                "set": label,
                "n": len(seeds),
            }
            for arm in LADDER:
                row[arm] = _summed_over(by_arm, arm, seeds) if arm in by_arm else None
            base = row.get(BASE_ARM)
            row["ratio"] = (
                (row["B2"] / base)
                if base and row.get("B2") is not None
                else None
            )
            rows.append(row)
            n_rows += 1
    if not rows:
        return None
    return Table(
        name=f"cost sums (check 4) — {source}",
        caption=Caption(
            units="model-node executions during the solve, summed over the "
            "set; the ratio is dimensionless",
            row_is="one configuration under one published seed set",
            column_is="one arm's summed solve-phase node calls over that set, "
            "or the partitioned arm's ratio to the flat control",
            population=(
                f"{population.what}; {n_rows} row(s) over the "
                f"configurations' seed sets"
            ),
            construction=(
                "solve-phase node calls **summed over attempts[]** per run "
                "(the attempt-summation identity is printed per run in the "
                "companion file), then summed over the set's seeds; the ratio "
                "is Σ B2 / Σ B0 over the same seeds"
            ),
            clauses=(
                "**these are sums, so the claim is about total work over the "
                "set** and not about every run: the per-run distribution is "
                "the per-module table's last columns, which show where the "
                "sign reverses",
                "the two sets are V4's own — the seeds on which every arm "
                "reached an accepted optimum, and the same set less the seeds "
                "on which any arm retried — not the previous revision's ok / "
                "converged pair, because V4 has one acceptance set and "
                "publishes the retry exclusion beside it",
                "the output path and the exit audit are excluded from this "
                "unit symmetrically in every arm",
                "prime calls are not model nodes and are in no column here "
                "(D19); they are the sweeps-and-prime-calls table's",
            ),
            how_to_read=(
                "read the ratio column down the two sets of one "
                "configuration: where they agree, nothing in the result "
                "depended on a retry"
            ),
            summary=(
                "Check 4 as sums: solve-phase model-node executions summed "
                "over each configuration's seed set and over that set less "
                "the retried seeds, one column per arm, with the partitioned "
                "arm's ratio to the flat control. Sums, so the claim is about "
                "total work over the set; the per-run reading is the "
                "per-module table's."
            ),
        ),
        columns=(
            Column("configuration", "configuration"),
            Column("set", "set"),
            Column("n", "n", fmt=_fmt_int),
            *[Column(arm, arm, fmt=_fmt_int) for arm in LADDER],
            Column("ratio", "B2/B0", fmt=_fmt_ratio),
        ),
        rows=tuple(rows),
        denominator=n_rows,
        denominator_is=(
            "configuration × set rows, each over its own seeds — the n column"
        ),
        acceptance=True,
        kind="cost_sums",
    )


def cost_anchors(
    population: stats_mod.Population,
    source: str,
    groups: Sequence[Any],
) -> Table | None:
    """**Both anchors** — the previous revision's second §5.5 table.

    The same rows as the cost sums, and three ratios: the stopping-rule
    change `BR → B0`, the architecture at a matched stopping rule `B2/B0`,
    and the end-to-end change a user switching from PROCESS as shipped would
    see, `B2/BR`.  Neither ratio is more correct: they answer different
    questions, and the report's headline uses `B0` because that is the anchor
    the ladder decomposes against.
    """
    rows: list[dict[str, Any]] = []
    n_rows = 0
    for configuration, arms, by_arm, converged in groups:
        if BASE_ARM not in by_arm:
            continue
        for label, without in COST_SETS:
            seeds = _set_members(by_arm, converged, without_retried=without)
            sums = {
                arm: (_summed_over(by_arm, arm, seeds) if arm in by_arm else None)
                for arm in LADDER
            }

            def _ratio(top: str, bottom: str) -> float | None:
                a, b = sums.get(top), sums.get(bottom)
                return (a / b) if (a is not None and b) else None

            rows.append(
                {
                    "configuration": configuration,
                    "set": label,
                    "n": len(seeds),
                    "reference_to_base": _ratio(BASE_ARM, "BR"),
                    "partition_to_base": _ratio("B2", BASE_ARM),
                    "partition_to_reference": _ratio("B2", "BR"),
                }
            )
            n_rows += 1
    if not rows:
        return None
    return Table(
        name=f"cost against both anchors — {source}",
        caption=Caption(
            units="dimensionless ratios of summed solve-phase node calls",
            row_is="one configuration under one published seed set",
            column_is="one of the three anchored ratios",
            population=(
                f"{population.what}; {n_rows} row(s) over the "
                f"configurations' seed sets"
            ),
            construction=(
                "the same sums as the cost-sums table, ratioed: BR → B0 is "
                "Σ B0 / Σ BR, B2/B0 is Σ B2 / Σ B0 and B2/BR is Σ B2 / Σ BR, "
                "each over the set's own seeds"
            ),
            clauses=(
                "**B2/B0 isolates the architecture at a matched stopping "
                "rule** and is the ladder's number; **B2/BR is the "
                "end-to-end change** a user switching from PROCESS as shipped "
                "would see, and conflates the architecture with the "
                "stopping-rule change",
                "BR → B0 is that stopping-rule change alone, and it is not "
                "free: where it exceeds 1 the matched baseline is already "
                "cheaper than the code as shipped, so measuring against B0 "
                "understates what a user would gain",
                "neither ratio is more correct; the report's headline uses "
                "B0 because that is the anchor the ladder decomposes against",
            ),
            how_to_read=(
                "the gap between the last two columns is exactly what the "
                "stopping rule is worth on that configuration"
            ),
            summary=(
                "The partitioned arm's cost ratio against **both** anchors, "
                "by configuration and set: the stopping-rule change BR → B0, "
                "the architecture at a matched stopping rule B2/B0, and the "
                "end-to-end B2/BR. Same sums as the cost-sums table."
            ),
        ),
        columns=(
            Column("configuration", "configuration"),
            Column("set", "set"),
            Column("n", "n", fmt=_fmt_int),
            Column("reference_to_base", "BR→B0", fmt=_fmt_ratio),
            Column("partition_to_base", "B2/B0", fmt=_fmt_ratio),
            Column("partition_to_reference", "B2/BR", fmt=_fmt_ratio),
        ),
        rows=tuple(rows),
        denominator=n_rows,
        denominator_is=(
            "configuration × set rows, each over its own seeds — the n column"
        ),
        acceptance=True,
        kind="cost_anchors",
    )


def sweeps_and_prime_calls(
    population: stats_mod.Population,
    source: str,
    groups: Sequence[Any],
) -> Table | None:
    """**Sweeps and prime calls** — the previous revision's third §5.5 table.

    The accounting that explains how node calls fall while dispatch sweeps
    rise: per configuration and arm over the seed set, the summed solve-phase
    node calls, the summed **dispatch sweeps** (``n_model_calls``, the field
    issue **I-26** names as the sweep count), the summed prime
    (arrangement-method) calls, and the two rates ``prime/sweep`` — which
    verifies the prime's contract of one ``set_fw_geometry()`` per sweep —
    and ``prime/node``, the cost decision **D19** excludes from every ratio
    in this report, named here per trap T11.  Both are **counts**, never
    costs.
    """
    rows: list[dict[str, Any]] = []
    n_rows = 0
    for configuration, arms, by_arm, converged in groups:
        for arm in _arm_order(by_arm):
            records = [
                by_arm[arm][seed]
                for seed in converged
                if seed in by_arm[arm] and stats_mod.finished(by_arm[arm][seed])
            ]
            if not records:
                continue

            def _sum(field: str) -> float | None:
                values = [r.get(field) for r in records]
                values = [v for v in values if v is not None]
                return sum(values) if values else None

            calls = _summed_over(by_arm, arm, converged)
            sweeps = _sum("n_model_calls")
            primes = _sum("n_arrangement_method_calls")
            rows.append(
                {
                    "configuration": configuration,
                    "arm": arm,
                    "n": len(records),
                    "node_calls": calls,
                    "sweeps": sweeps,
                    "prime_calls": primes,
                    "prime_per_sweep": (
                        (primes / sweeps) if (primes and sweeps) else None
                    ),
                    "prime_per_node": (
                        (primes / calls) if (primes and calls) else None
                    ),
                }
            )
            n_rows += 1
    if not rows:
        return None
    return Table(
        name=f"sweeps and prime calls — {source}",
        caption=Caption(
            units="counts: model-node executions, dispatch sweeps and "
            "arrangement-method calls, summed over the seed set; the two "
            "rates are dimensionless",
            row_is="one arm of one configuration over its seed set",
            column_is="one summed count, or one of the two rates",
            population=(
                f"{population.what}; {n_rows} arm row(s) over the "
                f"configurations' seed sets"
            ),
            construction=(
                "solve-phase node calls summed over attempts[] and then over "
                "the set; `n_model_calls` is the **dispatch sweep** count "
                "(issue I-26: it counts walks of the dispatch body, not "
                "evaluations of the model set) and `n_arrangement_method_calls` "
                "the prime calls, each summed over the same runs; the rates "
                "are those sums divided"
            ),
            clauses=(
                "**both rates are counts, never costs**: whether a prime call "
                "is cheap against an average model node is a timing, and no "
                "conclusion in this report rests on one (I-10)",
                "`prime/sweep` is the prime's contract — one "
                "`set_fw_geometry()` per sweep of the dispatch body — and is "
                "read as a check, not as a result",
                "`prime/node` is the quantity decision D19 excludes from "
                "every cost ratio in this report, named here so the exclusion "
                "has a size (trap T11)",
                "a flat arm runs no prime and its rate columns read —",
            ),
            how_to_read=(
                "node calls fall while sweeps rise: the partitioned arm walks "
                "the dispatch body far more often and executes far fewer "
                "nodes each time"
            ),
            summary=(
                "The accounting behind the cost result, by configuration and "
                "arm over the seed set: summed solve-phase node calls, summed "
                "dispatch sweeps (`n_model_calls`, I-26), summed prime calls, "
                "and the rates prime/sweep — the prime's one-per-sweep "
                "contract — and prime/node, the quantity D19 excludes from "
                "every cost ratio. Counts, never costs."
            ),
        ),
        columns=(
            Column("configuration", "configuration"),
            Column("arm", "arm"),
            Column("n", "n", fmt=_fmt_int),
            Column("node_calls", "node calls", fmt=_fmt_int),
            Column("sweeps", "dispatch sweeps", fmt=_fmt_int),
            Column("prime_calls", "prime calls", fmt=_fmt_int),
            Column("prime_per_sweep", "prime/sweep", fmt=_fmt_ratio),
            Column("prime_per_node", "prime/node", fmt=_fmt_ratio),
        ),
        rows=tuple(rows),
        denominator=n_rows,
        denominator_is=(
            "arm rows over the configurations' seed sets — the n column"
        ),
        kind="sweeps_and_prime_calls",
    )


def problem_definition(
    campaign: Campaign,
    population: stats_mod.Population,
    source: str,
    groups: Sequence[Any],
) -> Table | None:
    """**They do not optimise the same thing** — the §5.6 table.

    One row per configuration, from the records' own stamps: the figure of
    merit, its name and sense read from the frozen tree's own
    ``FiguresOfMerit`` enum, the number of iteration variables, the equality
    and inequality constraint counts, and whether the configuration is
    pulsed.

    Every configuration's runs must agree on each stamp; a configuration
    whose records disagree is **refused** rather than reduced to whichever
    record sorted first, because that would be a table stating one problem
    where two were solved.
    """
    numerics = Path(campaign.tree) / "process" / "data_structure" / "numerics.py"
    if not numerics.exists():
        raise tally_mod.TallyError(
            f"the frozen tree carries no {numerics}, so the objective's name "
            f"cannot be read and the problem-definition table is refused "
            f"rather than printed with an integer where the name belongs"
        )
    source_text = numerics.read_text()
    fields = (
        "i_figure_merit",
        "nvar",
        "n_equality_constraints",
        "n_inequality_constraints",
        "n_constraints",
    )
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for configuration, arms, by_arm, converged in groups:
        if configuration in seen:
            continue
        def _records(arms_wanted: Sequence[str]) -> list[Mapping[str, Any]]:
            return [
                by_arm[arm][seed]
                for arm in arms_wanted
                if arm in by_arm
                for seed in converged
                if seed in by_arm[arm] and stats_mod.finished(by_arm[arm][seed])
            ]

        def _stamps(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
            """The stamps these runs agree on, refusing where they do not."""
            out: dict[str, Any] = {}
            for field in fields:
                values = sorted({r.get(field) for r in records})
                if len(values) != 1:
                    raise tally_mod.TallyError(
                        f"{configuration}: these runs stamp {field} as "
                        f"{values}; a problem-definition row cannot state one "
                        f"problem where the records say two were solved"
                    )
                out[field] = values[0]
            return out

        # The **configuration's own** problem is the one the unlifted arms
        # solve; the lift adds an iteration variable and a constraint, which
        # is a change of problem and is stated in its own columns rather than
        # averaged into the row (I-20 (b)).
        flat = _records(UNLIFTED_ARMS)
        lifted = _records(LIFTED_ARMS)
        if not flat:
            continue
        seen.add(configuration)
        stamped = _stamps(flat)
        after = _stamps(lifted) if lifted else None
        merit = stats_mod.figure_of_merit(
            source_text, stamped["i_figure_merit"]
        )

        def _constraints(block: Mapping[str, Any] | None) -> str:
            if block is None:
                return "—"
            return (
                f"{block['n_constraints']} "
                f"({block['n_equality_constraints']} / "
                f"{block['n_inequality_constraints']})"
            )

        rows.append(
            {
                "configuration": configuration,
                "n": len(flat),
                "i_figure_merit": stamped["i_figure_merit"],
                "objective": merit["objective"],
                "sense": merit["sense"],
                "nvar": stamped["nvar"],
                "constraints": _constraints(stamped),
                "nvar_lifted": None if after is None else after["nvar"],
                "constraints_lifted": _constraints(after),
                "pulsed": (
                    "yes"
                    if campaign.configuration(configuration).pulsed
                    else "no (k = 0)"
                ),
            }
        )
    if not rows:
        return None
    return Table(
        name=f"problem definition — {source}",
        caption=Caption(
            units="counts of iteration variables and constraints; the "
            "objective is a name",
            row_is="one configuration",
            column_is="one part of the optimisation problem that "
            "configuration poses",
            population=(
                f"{population.what}; the stamps of every finished run of the "
                f"unlifted arms of each of {len(rows)} configuration(s), and "
                f"of the lifted arms beside, each checked for agreement"
            ),
            construction=(
                "the stamps `i_figure_merit`, `nvar`, `n_constraints`, "
                "`n_equality_constraints` and `n_inequality_constraints` of "
                f"every finished run of {' and '.join(UNLIFTED_ARMS)} (the "
                f"configuration's own problem) and of "
                f"{' and '.join(LIFTED_ARMS)} beside (the problem after the "
                "lift), each refused where its runs disagree; the objective's name and sense are "
                "stats.figure_of_merit — the description of the matching "
                "member of `FiguresOfMerit` in the **frozen tree's** "
                "`process/data_structure/numerics.py`, parsed from the file "
                "and never imported, a negative figure of merit meaning "
                "*maximise*"
            ),
            clauses=(
                "**the three configurations do not optimise the same thing**, "
                "so every cross-configuration comparison in this report is "
                "three answers to three questions and never one sample of "
                "three",
                "on a configuration whose objective **is** the lifted "
                "quantity, the ownership rung promotes that objective into "
                "the design vector: the arms either side of it are not "
                "solving the same optimisation problem (I-20 (b))",
                "the counts are the run's own stamps, not the input file "
                "read again",
                "**the lift changes the problem**, so its `nvar` and "
                "constraint counts are columns of their own rather than "
                "folded into the configuration's: the unlifted arms state "
                "what the configuration poses and the lifted arms what the "
                "intervention poses",
            ),
            how_to_read=(
                "read the objective column against the report's ladder: a "
                "rung that touches the objective is a change of problem, not "
                "only a change of architecture"
            ),
            summary=(
                "What each configuration actually optimises, from the runs' "
                "own stamps: the figure of merit and its name and sense (read "
                "from the frozen tree's `FiguresOfMerit`; negative means "
                "maximise), the iteration variables and constraints as total "
                "(equality / inequality) before and after the lift, and "
                "whether it is pulsed. The three are three different "
                "optimisation problems, and the lift makes a fourth and fifth."
            ),
        ),
        columns=(
            Column("configuration", "configuration"),
            Column("n", "n (runs)", fmt=_fmt_int),
            Column("i_figure_merit", "`i_figure_merit`", fmt=_fmt_int),
            Column("objective", "objective"),
            Column("sense", "sense"),
            Column("nvar", "vars", fmt=_fmt_int),
            Column("constraints", "constraints (eq / ineq)"),
            Column("nvar_lifted", "vars after the lift", fmt=_fmt_int),
            Column("constraints_lifted", "constraints after the lift"),
            Column("pulsed", "pulsed"),
        ),
        rows=tuple(rows),
        denominator=len(rows),
        denominator_is="configurations whose problem this table states",
        kind="problem_definition",
    )


PATH_QUANTITIES: tuple[tuple[str, str], ...] = (
    ("iterations (summed over attempts)", "iterations"),
    ("evaluations of the model set, ε", "evaluations"),
    ("node calls per evaluation, ρ", "calls_per_evaluation"),
    ("node calls per run, R = ρ × ε", "calls_per_run"),
)


def _path_value(record: Mapping[str, Any], quantity: str) -> float | None:
    if quantity == "iterations":
        value = stats_mod.iterations_summed_over_attempts(record)
        return None if value is None else float(value)
    evaluations = stats_mod.n_evaluations(record)
    if quantity == "evaluations":
        return None if evaluations is None else float(evaluations)
    calls = _summed_solve_calls(record)
    if quantity == "calls_per_run":
        return calls
    if calls is None or not evaluations:
        return None
    return calls / evaluations


def optimiser_path(
    campaign: Campaign,
    population: stats_mod.Population,
    source: str,
    groups: Sequence[tuple[str, tuple[str, ...], Mapping[str, Mapping[int, Mapping[str, Any]]], Sequence[int]]],
) -> Table | None:
    """The report's headline shape 2: the optimiser's path over the configurations.

    One table per source, one row per quantity and configuration (and arm
    group, which in a campaign is one per configuration): the optimiser's
    **iterations** summed over attempts (check 2's declared construction),
    the **evaluations** of the model set ε (``sweeps_per_eval.n_evaluations``
    — the field issue I-26 names; it sums the attempts), the **node calls per
    evaluation** ρ = R / ε and the **node calls per run** R (check 4's unit,
    summed over attempts).  Per arm the mean over the seed set; for B2
    against B0 the mean of the per-seed ratios, their median with
    ``[min, max]`` and the count of seeds with ratio above 1.  Reading down a
    configuration's four rows gives R = ρ × ε seed by seed.
    """
    base, arm = HEADLINE_PAIR
    rows: list[dict[str, Any]] = []
    per_configuration_n: list[tuple[str, int]] = []
    for configuration, arms, by_arm, converged in groups:
        if base not in by_arm or arm not in by_arm:
            continue
        per_configuration_n.append((configuration, len(converged)))
        for label, quantity in PATH_QUANTITIES:
            row: dict[str, Any] = {
                "quantity": label,
                "configuration": configuration,
                "arms": " · ".join(arms),
                "n": len(converged),
            }
            for a in LADDER:
                if a not in by_arm:
                    row[a] = None
                    continue
                values = [
                    _path_value(by_arm[a][s], quantity)
                    for s in converged
                    if s in by_arm[a] and stats_mod.finished(by_arm[a][s])
                ]
                values = [v for v in values if v is not None]
                row[a] = (sum(values) / len(values)) if values else None
            pairs = [
                (_path_value(by_arm[base][s], quantity), _path_value(by_arm[arm][s], quantity))
                for s in converged
                if s in by_arm[base] and s in by_arm[arm]
                and stats_mod.finished(by_arm[base][s]) and stats_mod.finished(by_arm[arm][s])
            ]
            pairs = [(x, y) for x, y in pairs if x is not None and y is not None]
            summary = stats_mod.per_seed_ratio_summary(
                [x for x, _ in pairs], [y for _, y in pairs]
            )
            row.update(
                {
                    # The previous revision's column of this name was the
                    # **ratio of the means** — equal to the ratio of the sums
                    # over the same seeds, the campaign-cost statistic (its
                    # §5.3 caption).  The mean of the per-seed ratios is a
                    # different statistic and answers the typical seed's
                    # question; both are published, each under its own
                    # heading (task A86 (v3-tables-remainder)).
                    "ratio_pooled": summary["pooled"],
                    "ratio_mean": summary["mean"],
                    "ratio_median": summary["median"],
                    "ratio_bracket": (
                        "—"
                        if summary["min"] is None
                        else f"[{summary['min']:.3f}, {summary['max']:.3f}]"
                    ),
                    "n_above_one": summary["n_above_one"],
                }
            )
            rows.append(row)
    if not rows:
        return None
    return Table(
        name=f"the optimiser's path over the configurations — {source}",
        caption=Caption(
            units="counts per optimisation run (iterations, evaluations, "
            "model-node executions) and their ratios, dimensionless",
            row_is="one quantity of the optimiser's path on one configuration "
            "(and arm group): iterations summed over attempts, the "
            "evaluation count ε, the node calls per evaluation ρ, the node "
            "calls per run R",
            column_is="per arm, the mean over the seed set; for B2 against B0, "
            "the ratio of those means, the mean of the per-seed ratios, their "
            "median with [min, max], and the count of seeds on which the "
            "ratio exceeds 1",
            population=(
                f"{population.what}; the seed set of each configuration "
                f"(every arm converged), stated per row and never summed: "
                + ", ".join(f"{c} {n}" for c, n in per_configuration_n)
            ),
            construction=(
                "stats.iterations_summed_over_attempts (check 2's declared "
                "statistic); stats.n_evaluations (sweeps_per_eval.n_evaluations, "
                "the field issue I-26 names — the driver's histogram summed over "
                "the attempts, output path excluded); R = solve-phase node calls "
                "summed over attempts[] (check 4's unit); ρ = R / ε per run.  "
                "Means are arithmetic over the arm's runs in the seed set; the "
                "B2/B0 columns are stats.per_seed_ratio_summary (mean and "
                "nearest-rank upper-middle median of the per-seed ratios, their "
                "[min, max], the count above 1) — whose **pooled** reading is "
                "Σ B2 / Σ B0 over the same seeds, the ratio of the two mean "
                "columns beside it and the campaign-cost statistic, and whose "
                "**mean** reading is the mean of the per-seed ratios, the "
                "typical seed's"
            ),
            clauses=(
                "R = ρ × ε holds per seed by construction, so a configuration's "
                "four rows decompose check 4's cost ratio into how many "
                "evaluations the optimiser took and what each cost",
                "**two statistics, two headings**: `B2/B0 mean` is the "
                "ratio of the two arms' means — equal to the ratio of the "
                "sums over the same seeds, which is what the campaign cost; "
                "`B2/B0 mean of per-seed ratios` is the mean of the ratios a "
                "seed at a time, which is what a typical start saw.  They "
                "differ by a lot where a few long runs dominate the sums, and "
                "publishing one under the other's name would state the wrong "
                "quantity (task A86 (v3-tables-remainder))",
                "the iteration row is the same construction as check 2's "
                "acceptance column, and the ε row the same field as check 2's "
                "ε column (issue I-26, closed by task A80 (report-accuracy-"
                "audit): until then that column read n_model_calls, the "
                "driver's sweep count)",
                "B1 is absent on a steady-state configuration and reads —",
            ),
            how_to_read=(
                "an ε row near 1 with an R row well below 1 says the partition "
                "changed what an evaluation costs and not how many the "
                "optimiser needed; a median far from the mean names a few "
                "seeds carrying the difference"
            ),
            summary=(
                f"The optimiser's path per configuration over the seed set, "
                f"{tally_mod.source_phrase(source)}: per arm the mean "
                f"iterations (summed over attempts), evaluations ε "
                f"(sweeps_per_eval.n_evaluations), node calls per "
                f"evaluation ρ and per run R; B2/B0 as the ratio of those "
                f"means (the campaign-cost statistic), as the mean of the "
                f"per-seed ratios, as their median [min, max] and as the count "
                f"above 1. R = ρ × ε per seed; "
                f"n is per configuration, never summed."
            ),
        ),
        columns=(
            Column("quantity", "quantity"),
            Column("configuration", "configuration"),
            Column("arms", "arms"),
            Column("n", "n", fmt=_fmt_int),
            *[Column(a, a, fmt=_fmt_path) for a in LADDER],
            Column("ratio_pooled", "B2/B0 mean", fmt=_fmt_ratio),
            Column("ratio_mean", "B2/B0 mean of per-seed ratios", fmt=_fmt_ratio),
            Column("ratio_median", "B2/B0 median", fmt=_fmt_ratio),
            Column("ratio_bracket", "[min, max]"),
            Column("n_above_one", "seeds B2/B0 > 1", fmt=_fmt_int),
        ),
        rows=tuple(rows),
        # One denominator per configuration — the n column — and never their
        # sum: configurations are not pooled (D21 (b)).  The table's own count
        # is the number of configurations it stacks (task A80
        # (report-accuracy-audit), on A79's assessment).
        denominator=len(per_configuration_n),
        denominator_is=(
            "configurations stacked, each over its own seed set — the n column: "
            + " / ".join(f"{configuration} {n}" for configuration, n in per_configuration_n)
            + " seeds on which every arm converged; never pooled"
        ),
        acceptance=True,
        kind="optimiser_path",
    )


# --------------------------------------------------------------------------
# the stage
# --------------------------------------------------------------------------


def tally(campaign: Campaign, *, resume: bool = False) -> dict[str, Any]:
    """The optimisation phase's tables, one set per declared source.

    A *source* is a named subtree of ``runs/gates/`` whose records are a
    comparable set, with the sentence that says why (``tally.SOURCES``).  The
    tally never averages across sources and never averages across the whole
    gate tree.
    """
    paths = tally_mod.declared_paths(campaign)
    provenance = tally_mod.survey(paths)
    straddle = tally_mod.assert_one_commit(provenance, resume=resume)
    present = tally_mod.campaign_present(campaign)
    emitted: list[Table] = []
    refusals: list[str] = []
    sources: list[dict[str, Any]] = []
    seed_sets: dict[str, list[int]] = {}
    not_produced: list[dict[str, str]] = []
    for source in tally_mod.published_sources(campaign):
        if PHASE not in source.phases:
            continue
        rows, source_refusals = tally_mod.source_rows(campaign, source)
        refusals.extend(f"[{source.name}] {line}" for line in source_refusals)
        population = tally_mod.population_for(
            rows,
            phase=PHASE,
            what=f"{source.name} — {source.what}",
            campaign_present=present,
        )
        population.assert_no_forced_budget()
        sources.append(
            {
                "source": source.name,
                "owner": source.owner,
                "family": source.family,
                "what": source.what,
                "n_records": len(population),
                "n_excluded_as_demonstrations": len(population.excluded),
                "run_kinds": list(population.run_kinds),
            }
        )
        if population.is_empty:
            continue
        path_groups: list[tuple[str, tuple[str, ...], Mapping[str, Mapping[int, Mapping[str, Any]]], Sequence[int]]] = []
        for config in campaign.configurations:
            whole = _by_arm_and_seed(population, config.name)
            if not whole:
                continue
            emitted.append(failure_taxonomy(population, config.name, source.name))
            groups = arm_groups(whole)
            for arms, seeds in groups:
                label = f"{source.name} · {'·'.join(arms)}"
                by_arm = restrict(whole, arms, seeds)
                table, converged = seed_set(
                    campaign, population, config.name, by_arm, label
                )
                seed_sets[f"{label}/{config.name}"] = converged
                path_groups.append((config.name, arms, by_arm, converged))
                emitted.append(table)
                emitted.extend(
                    per_arm_success(population, config.name, by_arm, label)
                )
                emitted.append(
                    failure_table(population, config.name, by_arm, converged, label)
                )
                for name, table in (
                    (
                        "same optimum (check 1)",
                        same_optimum(
                            campaign, population, config.name, by_arm,
                            converged, label,
                        ),
                    ),
                    (
                        "iteration multiplier (check 2)",
                        iterations(
                            campaign, population, config.name, by_arm,
                            converged, label,
                        ),
                    ),
                    (
                        "cost (check 4)",
                        cost(population, config.name, by_arm, converged, label),
                    ),
                ):
                    if table is None:
                        not_produced.append(
                            {
                                "table": f"{name} — {config.name} — {label}",
                                "why": (
                                    f"this arm group carries no {BASE_ARM} run, "
                                    f"and every pair of this check is anchored "
                                    f"on it.  A table over no comparison would "
                                    f"state a denominator for nothing"
                                ),
                            }
                        )
                    else:
                        emitted.append(table)
                emitted.append(attempts(population, config.name, by_arm, label))
                emitted.append(
                    achieved_accuracy(
                        campaign, population, config.name, by_arm, label
                    )
                )
                lift = lift_closed(population, config.name, by_arm, label)
                if lift is not None:
                    emitted.append(lift)
                emitted.append(
                    per_sweep_overhead(population, config.name, by_arm, label)
                )
                modules = node_calls_per_module(
                    campaign, population, config.name, by_arm, converged, label
                )
                if modules is not None:
                    emitted.append(modules)
                sweeps = module_sweeps(
                    campaign, population, config.name, by_arm, converged, label
                )
                if sweeps is not None:
                    emitted.append(sweeps)
        path = optimiser_path(campaign, population, source.name, path_groups)
        if path is not None:
            emitted.append(path)
        # The previous revision's cross-configuration §5 shapes (task A86
        # (v3-tables-remainder)): one row per configuration, or per
        # configuration and pair, arm or published set.
        for built in (
            location_diagnostic(campaign, population, source.name, path_groups),
            identity(population, source.name, path_groups),
            cost_sums(population, source.name, path_groups),
            cost_anchors(population, source.name, path_groups),
            sweeps_and_prime_calls(population, source.name, path_groups),
            problem_definition(campaign, population, source.name, path_groups),
        ):
            if built is not None:
                emitted.append(built)
    from harness.measurement.tally_evaluation import _not_published  # noqa: PLC0415

    return {
        "phase": PHASE,
        "campaign_present": present,
        "population_family": "campaign" if present else "gate",
        "sources": sources,
        "sources_not_published": _not_published(campaign, PHASE),
        "population": "; ".join(
            f"{s['source']}: {s['n_records']} record(s)" for s in sources
        ),
        "n_records": sum(s["n_records"] for s in sources),
        "records_outside_every_source": tally_mod.records_outside_every_source(
            campaign
        ),
        "campaign_records_outside_every_source": (
            tally_mod.campaign_records_outside_every_source(campaign)
        ),
        "runs_provenance": provenance,
        "runs_straddle_note": straddle,
        "record_contract_refusals": refusals,
        "seed_sets": seed_sets,
        "tables_not_produced": not_produced,
        "tables": [table.as_record() for table in emitted],
        "n_tables": len(emitted),
    }


def print_tally(block: Mapping[str, Any]) -> None:
    """The stage's tables on the terminal, each with its caption."""
    from harness.measurement.tally_evaluation import print_tally as _print  # noqa: PLC0415

    _print(block)
    if block.get("seed_sets"):
        for name, seeds in block["seed_sets"].items():
            print(f"  seed set {name}: n = {len(seeds)} ({seeds})")
