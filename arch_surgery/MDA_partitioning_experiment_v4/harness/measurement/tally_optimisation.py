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

**What the population is.** These tables are over the **gate runs** under
``runs/gates/`` — ``EXECUTION_APPROVED`` is False and no campaign record
exists.  They are one or two seeds per arm per configuration, so no cell is a
campaign statistic and none may be quoted as one.

Written by task **A53 (harness-tally)**.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from harness.experiment import arms as arms_mod
from harness.measurement import stats as stats_mod
from harness.measurement import tally as tally_mod
from harness.core.config import Campaign
from harness.measurement.tables import Caption, Column, Table, cell_list

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
ACCEPTANCE_PAIRS: tuple[str, ...] = ("B1", "B3")


def _fmt_ratio(value: Any) -> str:
    return "—" if value is None else f"{value:.4f}"


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
        ),
        converged,
    )


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
    """
    if BASE_ARM not in by_arm:
        return None
    rows: list[dict[str, Any]] = []
    for arm in _arm_order(by_arm):
        if arm == BASE_ARM:
            continue
        seeds = [
            s
            for s in converged
            if s in by_arm[arm] and s in by_arm[BASE_ARM]
        ]
        final_ratios: list[float] = []
        summed_ratios: list[float] = []
        evaluation_ratios: list[float] = []
        final_sums = [0, 0]
        summed_sums = [0, 0]
        disagreements = 0
        for seed in seeds:
            base_record, arm_record = by_arm[BASE_ARM][seed], by_arm[arm][seed]
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
            ea = base_record.get("n_model_calls")
            eb = arm_record.get("n_model_calls")
            if ea and eb:
                evaluation_ratios.append(eb / ea)
        summed_median = stats_mod.median(summed_ratios)
        accepted_on = arm in ACCEPTANCE_PAIRS
        rows.append(
            {
                "pair": f"{BASE_ARM} → {arm}"
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
                "attempts": ", ".join(
                    f"{seed}:{stats_mod.n_attempts(by_arm[BASE_ARM][seed])}/"
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
            row_is="one arm against the flat control over the seed set",
            column_is="one of check 2's two iteration constructions, its sum "
            "ratio, or the evaluation-count ratio beside them",
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
                "the evaluation-count ratio is beside both: iterations, even "
                "summed, miss the lifted arm's extra stencil column and the "
                "line-search evaluations that vary at equal iteration count",
                "*constructions disagree* counts the seeds on which the final "
                "attempt's pair and the summed pair are not the same numbers — "
                "0 means no run in this population retried",
            ),
            how_to_read=(
                "read the acceptance column against the summed median; a "
                "final-attempt median that differs from it names the retried "
                "seeds, which the attempts column lists"
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
            Column("evaluations_median", "evaluations median", fmt=_fmt_ratio),
            Column("attempts", "attempts per seed (base/arm)"),
            Column("constructions_disagree", "constructions disagree", fmt=_fmt_int),
        ),
        rows=tuple(rows),
        denominator=len(converged),
        denominator_is=(
            f"seeds on which every arm of {configuration} converged"
        ),
        acceptance=True,
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
        denominator_is=f"optimisation-phase gate runs of {configuration}",
        acceptance=True,
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
                "the arrangement-method calls are a column of their own and "
                "are never pooled into the node calls",
                "the output-time and audit sweeps are excluded from this unit "
                "symmetrically in every arm",
            ),
            how_to_read=(
                "where *retried* is 0 the with- and without- columns are the "
                "same number, and the pair of columns is the statement that "
                "nothing in this population depended on a retry"
            ),
        ),
        columns=(
            Column("arm", "arm"),
            Column("n", "n", fmt=_fmt_int),
            Column("node_calls_mean", "node calls / run", fmt=lambda v: "—" if v is None else f"{v:.1f}"),
            Column("bracket", "bracket"),
            Column("arrangement_method_calls", "arrangement·method calls", fmt=_fmt_int),
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
        denominator_is=f"optimisation-phase gate runs of {configuration}",
        acceptance=True,
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
                "**audit position**: "
                + (", ".join(positions) if positions else "not recorded on any run here")
                + ".  `entry_to_write_output_files` is the declared position — "
                "the state the solve handed over — and `after_run` is the "
                "reproduction gate's, where the previous revision measured.  "
                "The two are different quantities and share this table only "
                "because the position is a column of its own",
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
                "denominator of a median, which is trap T11.  Over this "
                "population "
                + (
                    "every run carried the statistic"
                    if not reasons
                    else "some did not: " + "; ".join(sorted(reasons))
                ),
            ),
            how_to_read=(
                "read the argmax beside the maximum: a residual above the "
                "tolerance whose argmax is the component A61 named is a "
                "statement about the audit instrument, not about the arm"
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
                f"{population.what}; the finished optimisation-phase gate runs "
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
                "which over this population is "
                + (
                    ", ".join(f"{v:g} %" for v in shares_seen)
                    if shares_seen
                    else "not computable on any run here"
                )
                + ".  The visit share is larger and is never quoted",
                "no conclusion rests on a timing: the question is asked in "
                "counts alone",
            ),
            how_to_read=(
                "read the width column of the test the arm actually stops on; "
                "the other test's columns are 0 for that arm, which is why "
                "they are kept apart"
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
            f"finished optimisation-phase gate runs of {configuration}"
        ),
        acceptance=True,
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
    emitted: list[Table] = []
    refusals: list[str] = []
    sources: list[dict[str, Any]] = []
    seed_sets: dict[str, list[int]] = {}
    not_produced: list[dict[str, str]] = []
    for source in tally_mod.SOURCES:
        if PHASE not in source.phases:
            continue
        rows, source_refusals = tally_mod.source_rows(campaign, source)
        refusals.extend(f"[{source.name}] {line}" for line in source_refusals)
        population = tally_mod.population_for(
            rows, phase=PHASE, what=f"{source.name} — {source.what}"
        )
        population.assert_no_forced_budget()
        sources.append(
            {
                "source": source.name,
                "owner": source.owner,
                "what": source.what,
                "n_records": len(population),
                "n_excluded_as_demonstrations": len(population.excluded),
            }
        )
        if population.is_empty:
            continue
        for config in campaign.configurations:
            whole = _by_arm_and_seed(population, config.name)
            if not whole:
                continue
            groups = arm_groups(whole)
            for arms, seeds in groups:
                label = f"{source.name} · {'·'.join(arms)}"
                by_arm = restrict(whole, arms, seeds)
                table, converged = seed_set(
                    campaign, population, config.name, by_arm, label
                )
                seed_sets[f"{label}/{config.name}"] = converged
                emitted.append(table)
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
    return {
        "phase": PHASE,
        "sources": sources,
        "population": "; ".join(
            f"{s['source']}: {s['n_records']} record(s)" for s in sources
        ),
        "n_records": sum(s["n_records"] for s in sources),
        "records_outside_every_source": tally_mod.records_outside_every_source(
            campaign
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
