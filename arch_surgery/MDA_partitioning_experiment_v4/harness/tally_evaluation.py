#!/usr/bin/env python
"""The evaluation phase's tally: what one `call_models` cost, and how accurate.

A **tally** summarises the records into the tables the experiment plan's §4
asks for.  It has nothing to pass — what passes is the gate over the same
records — so it is registered as a *measurement stage* and runs under
``--measure``, never under ``--gate``.  Where the tally *checks* something,
that check is a gate with teeth and lives in ``harness/gate_tally.py``.

Five tables, each the shape of one of the plan's §4.2 placeholders:

``cost_per_call``      §4.2.1 — model executions per evaluation, sweeps per
                       evaluation, sweeps per block, the arrangement-method
                       calls beside them, and the ratio triple against the
                       declared reference arm.
``matched_accuracy``   §4.2.2 — the exit-audit maximum, restricted and whole
                       state, **on both rulers**, with the argmax component
                       named rather than averaged, and the similarity verdict.
``ownership_rung``     §4.2.3 — the flat control against the flat control with
                       the burn time owned by a constant.
``per_sweep_overhead`` §3.5 check 5 — what each arm's convergence test cost, in
                       evaluations and components compared, with the empty
                       block visits' **sweep** share disclaimed and the two
                       predicates in columns of their own.
``failure_taxonomy``   §4.2.6 — every scheduled run a row, denominators stated.

**What the population is, stated once here and in every caption.** These
tables are over the **gate runs** — the records the verification gates made,
under ``runs/gates/`` — because ``EXECUTION_APPROVED`` is False and no campaign
record exists.  They are one or two seeds per arm per configuration, so no cell
here is a campaign statistic and none may be quoted as one.  What the tally
demonstrates at this commit is that the constructions are implemented, that
they refuse what they must refuse, and that they reproduce the previous
revision's published cells on the twenty runs where a previous number exists.

Written by task **A53 (harness-tally)**.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from harness import arms as arms_mod
from harness import stats as stats_mod
from harness import tally as tally_mod
from harness import tables as tables_mod
from harness.config import Campaign
from harness.tables import Caption, Column, Table, cell_list

__all__ = ["tally", "print_tally", "PHASE"]

PHASE = "A"

#: The arm each other arm's ratio is stated against, per the plan §3.4 check 3:
#: the pinned flat control on a pulsed configuration, where both arms sit on
#: the same reduced map, and the plain flat control on a steady-state one,
#: where the pinned arm degenerates onto it and is skipped.
def reference_arm(pulsed: bool, present: Any = None) -> tuple[str, str]:
    """The declared reference arm of the evaluation phase's cost ratio, and why.

    On a **pulsed** configuration the declared reference is the flat control
    with the burn time owned by a constant, because it and the partitioned arm
    sit on the same reduced map.  On a **steady-state** configuration there is
    no burn-time coupling, that arm degenerates onto the plain flat control and
    is skipped, so the plain flat control is the reference.

    A population that does not carry the declared arm falls back to the plain
    flat control and **says so in the caption** — that is the previous
    revision's construction, published beside the declared one with the
    burn-time residual reported separately.  It is a fallback and never a
    silent substitution: the two references are not the same comparison.
    """
    if not pulsed:
        return "A0", (
            "steady state: there is no burn-time coupling, the pinned flat "
            "control degenerates onto the plain one and is skipped"
        )
    if present is None or "A0p" in present:
        return "A0p", (
            "pulsed: the declared reference, because it and the partitioned "
            "arm sit on the same reduced map"
        )
    return "A0", (
        "pulsed, but this population carries no A0p run, so the ratio falls "
        "back to the plain flat control — the previous revision's "
        "construction, in which the burn-time residual is reported separately "
        "rather than being part of the arm.  This is a FALLBACK and not the "
        "declared pair"
    )


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


def _fmt_share(value: Any) -> str:
    return "—" if value is None else f"{100 * value:.2f} %"


def _mean(values: Sequence[float]) -> float | None:
    numbers = [v for v in values if v is not None]
    return (sum(numbers) / len(numbers)) if numbers else None


def _bracket(values: Sequence[float]) -> str:
    bracket = stats_mod.seed_bracket([v for v in values if v is not None])
    return "—" if bracket is None else f"[{bracket[0]:g}, {bracket[1]:g}]"


# --------------------------------------------------------------------------
# grouping
# --------------------------------------------------------------------------


def _by_arm(
    population: stats_mod.Population, configuration: str
) -> dict[str, list[Mapping[str, Any]]]:
    out: dict[str, list[Mapping[str, Any]]] = {}
    for record in population.records:
        if record.get("campaign_configuration") != configuration:
            continue
        out.setdefault(str(record.get("campaign_arm")), []).append(record)
    return out


def _by_arm_and_seed(
    population: stats_mod.Population, configuration: str
) -> dict[str, dict[int, Mapping[str, Any]]]:
    """Records indexed by arm and seed, for a **seed-keyed** pairing.

    A ratio between two arms is paired seed by seed or it is not paired at all:
    pairing two lists by position compares whichever runs happened to sort
    first, which is a ratio over a population nobody can state.  Within one
    declared source an (arm, seed) is one job; a second record for the same key
    would be a source that is not the comparable set it declares itself to be,
    and is reported rather than kept.
    """
    out: dict[str, dict[int, Mapping[str, Any]]] = {}
    for record in population.records:
        if record.get("campaign_configuration") != configuration:
            continue
        seed = record.get("campaign_seed")
        if seed is None:
            continue
        out.setdefault(str(record.get("campaign_arm")), {}).setdefault(
            int(seed), record
        )
    return out


def _paired(
    by_seed: Mapping[str, Mapping[int, Mapping[str, Any]]],
    base: str,
    arm: str,
    field: str,
) -> tuple[list[float], list[float], list[int]]:
    """The two sides of a seed-keyed pairing, and the seeds they are over."""
    if base not in by_seed or arm not in by_seed:
        return [], [], []
    seeds = sorted(set(by_seed[base]) & set(by_seed[arm]))
    reference: list[float] = []
    values: list[float] = []
    kept: list[int] = []
    for seed in seeds:
        a = by_seed[base][seed].get(field)
        b = by_seed[arm][seed].get(field)
        if a is None or b is None:
            continue
        if not (
            stats_mod.finished(by_seed[base][seed])
            and stats_mod.finished(by_seed[arm][seed])
        ):
            continue
        reference.append(a)
        values.append(b)
        kept.append(seed)
    return reference, values, kept


def _arm_order(names) -> list[str]:
    order = arms_mod.MATRIX_ORDER
    return sorted(names, key=lambda n: order.index(n) if n in order else len(order))


# --------------------------------------------------------------------------
# the tables
# --------------------------------------------------------------------------


def cost_per_call(
    campaign: Campaign,
    population: stats_mod.Population,
    configuration: str,
    source: str,
) -> Table:
    """§4.2.1 — what one evaluation cost, per arm, with the ratio triple."""
    by_arm = _by_arm(population, configuration)
    config = campaign.configuration(configuration)
    base, why_base = reference_arm(config.pulsed, set(by_arm))
    rows: list[dict[str, Any]] = []
    finished_by_arm = {
        arm: [r for r in records if stats_mod.finished(r)]
        for arm, records in by_arm.items()
    }
    by_seed = _by_arm_and_seed(population, configuration)
    for arm in _arm_order(by_arm):
        records = finished_by_arm.get(arm, [])
        calls = [r.get("node_calls_single_eval") for r in records]
        sweeps = [r.get("n_model_calls_sweeps") for r in records]
        by_block: dict[str, float] = {}
        for record in records:
            totals = record.get("block_loop_totals") or {}
            for block, value in (totals.get("sweeps_by_block") or {}).items():
                by_block[block] = by_block.get(block, 0) + value
        ratio: dict[str, Any] = {}
        paired_seeds: list[int] = []
        if arm != base:
            reference, values, paired_seeds = _paired(
                by_seed, base, arm, "node_calls_single_eval"
            )
            if reference:
                ratio = stats_mod.ratio_triple(reference, values)
        rows.append(
            {
                "arm": arm,
                "ok": f"{len(records)}/{len(by_arm.get(arm, []))}",
                "calls_per_eval": _mean(calls),
                "calls_bracket": _bracket(calls),
                "sweeps_per_eval": _mean(sweeps),
                "sweeps_by_block": (
                    ", ".join(f"{k} {v:g}" for k, v in sorted(by_block.items()))
                    or "—"
                ),
                "arrangement_method_calls": _mean(
                    [
                        r.get("n_arrangement_method_calls")
                        for r in records
                    ]
                ),
                "paired_seeds": (
                    ", ".join(str(s) for s in paired_seeds) if paired_seeds else "—"
                ),
                "pooled": ratio.get("pooled"),
                "median": ratio.get("median"),
                "worse": ratio.get("worse") if ratio else None,
            }
        )
    denominator = sum(len(v) for v in by_arm.values())
    return Table(
        name=f"cost per call — {configuration} — {source}",
        caption=Caption(
            units="model-node executions per `call_models` evaluation; sweeps "
            "are walks of the model sequence; ratios are dimensionless",
            row_is="one arm of the evaluation phase on this configuration",
            column_is="a per-run mean over that arm's finished runs, with the "
            "observed bracket, or one of the three readings of the ratio "
            "against the declared reference arm",
            population=(
                f"{population.what}; {denominator} run(s) of "
                f"{configuration}, of which "
                f"{sum(len(v) for v in finished_by_arm.values())} finished"
            ),
            construction=(
                "stats.ratio_triple — pooled = Σ arm / Σ reference over the "
                "paired runs; median = nearest-rank upper-middle of the "
                "per-run ratios; worse = runs on which the arm cost more.  "
                f"The reference arm is {base} — {why_base}"
            ),
            clauses=(
                "the arrangement-method calls are stamped beside the node "
                "calls and are never pooled into them",
                "the empty block visits are included in every sweep count and "
                "are disclaimed in the per-sweep-overhead table, which states "
                "their sweep share",
                "these are gate runs at one or two seeds, not campaign runs: "
                "no cell here is a campaign statistic",
            ),
            how_to_read=(
                "a pooled ratio below 1 with worse = 0 means the arm was "
                "cheaper on every run of this population; a median far from "
                "the pooled value means a few runs carry the cost"
            ),
        ),
        columns=(
            Column("arm", "arm"),
            Column("ok", "ok/run"),
            Column("calls_per_eval", "node calls / eval", fmt=lambda v: "—" if v is None else f"{v:.1f}"),
            Column("calls_bracket", "bracket"),
            Column("sweeps_per_eval", "sweeps / eval", fmt=lambda v: "—" if v is None else f"{v:.2f}"),
            Column("sweeps_by_block", "sweeps by block"),
            Column("arrangement_method_calls", "arrangement·method calls", fmt=lambda v: "—" if v is None else f"{v:.1f}"),
            Column("paired_seeds", f"paired with {base} at seeds"),
            Column("pooled", f"vs {base} pooled", fmt=_fmt_ratio),
            Column("median", f"vs {base} median", fmt=_fmt_ratio),
            Column("worse", "worse", fmt=_fmt_int),
        ),
        rows=tuple(rows),
        denominator=denominator,
        denominator_is=f"evaluation-phase gate runs of {configuration}",
        acceptance=True,
    )


def matched_accuracy(
    campaign: Campaign,
    population: stats_mod.Population,
    configuration: str,
    source: str,
) -> Table:
    """§4.2.2 — the achieved accuracy, on both rulers, with the argmax named."""
    by_arm = _by_arm(population, configuration)
    config = campaign.configuration(configuration)
    base, why_base = reference_arm(config.pulsed, set(by_arm))
    rows: list[dict[str, Any]] = []
    distributions: dict[str, dict[str, list[float]]] = {}
    reasons: set[str] = set()
    for arm in _arm_order(by_arm):
        records = [r for r in by_arm[arm] if stats_mod.finished(r)]
        for ruler in campaign.predicate_modes:
            # One construction for n, declared in stats.accuracy_population: it
            # counts the **runs** this row is over, and the column beside it
            # says how many of them carried a restricted statistic.
            block = stats_mod.accuracy_population(records, ruler=ruler)
            restricted = block["statistics"]
            restricted_values = block["values"]
            reasons.update(block["reasons"])
            whole = [
                stats_mod.whole_state_statistic(r, ruler=ruler) for r in records
            ]
            whole_values = [
                s["max"] for s in whole if s.get("present") and s.get("max") is not None
            ]
            argmaxes = sorted(
                {s.get("argmax") for s in restricted if s.get("argmax")}
            )
            excluded = sorted(
                {
                    s.get("n_excluded")
                    for s in restricted
                    if s.get("n_excluded") is not None
                }
            )
            distributions.setdefault(arm, {})[ruler] = restricted_values
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
                    "restricted_p90": stats_mod.p90(restricted_values),
                    "argmax": ", ".join(argmaxes) if argmaxes else "—",
                    "whole_median": stats_mod.median(whole_values),
                    "whole_p90": stats_mod.p90(whole_values),
                    "n_excluded": (
                        ", ".join(str(v) for v in excluded) if excluded else "—"
                    ),
                    "audit_position": positions[0] if len(positions) == 1 else (
                        "/".join(positions) if positions else None
                    ),
                    "instrument": cell_list(instruments),
                }
            )
    verdicts = []
    for arm in _arm_order(by_arm):
        if arm == base or base not in distributions or arm not in distributions:
            continue
        for ruler in campaign.predicate_modes:
            a = distributions[base].get(ruler) or []
            b = distributions[arm].get(ruler) or []
            verdicts.append(
                {
                    "pair": f"{arm}/{base}",
                    "ruler": ruler,
                    "median": stats_mod.similarity(
                        stats_mod.median(a),
                        stats_mod.median(b),
                        factor=campaign.similarity_factor,
                    ),
                    "p90": stats_mod.similarity(
                        stats_mod.p90(a),
                        stats_mod.p90(b),
                        factor=campaign.similarity_factor,
                    ),
                }
            )
    positions = sorted({row["audit_position"] for row in rows if row["audit_position"]})
    table = Table(
        name=f"matched accuracy — {configuration} — {source}",
        caption=Caption(
            units="dimensionless: the largest scaled coupling-state residual "
            "found by one further full sweep past termination",
            row_is="one arm on one ruler",
            column_is="the restricted or whole-state maximum's median and p90 "
            "over that arm's finished runs, the component the restricted "
            "maximum sat on, and how many components the restriction removed",
            population=(
                f"{population.what}; {sum(len(v) for v in by_arm.values())} "
                f"run(s) of {configuration}"
            ),
            construction=(
                "stats.restricted_statistic and stats.whole_state_statistic; "
                "median = nearest-rank upper-middle, p90 = nearest-rank "
                "ceil(0.9 n).  The restricted maximum excludes the components "
                "the configuration's once-per-run deferred nodes write, "
                "derived node → write sets → spec keys, never by a prefix rule"
            ),
            clauses=(
                "**audit position**: "
                + (
                    ", ".join(positions)
                    if positions
                    else "not recorded on any run of this population"
                )
                + ".  A residual taken at the entry to the output path and one "
                "taken after the run are different quantities and never share "
                "an unlabelled table",
                "**the audit instrument's version is read from the record** "
                "(stats.audit_instrument), never assumed: task A61 "
                "(insstrain-diagnosis) classified the largest residual seen at "
                "this commit as an artefact of the instrument — an output-path "
                "setting the snapshot does not restore — and task A62 "
                "(exit-audit-restore) widens the snapshot to the whole data "
                "structure under decision D25, which moves every value in "
                "these columns.  The instrument column is what tells two "
                "otherwise identical tables apart, and the argmax component is "
                "read from the record rather than written into this table",
                "**both rulers or neither**: the mixed ruler reads lower "
                "wherever its denominator binds, by construction, so a table "
                "showing one column alone reports a change of ruler as a "
                "change of accuracy",
                "the two rulers' exclusion counts are listed per row and are "
                "never pooled; a run whose restricted block is null carries no "
                "count at all and reads —",
                "**n counts runs, not values** (stats.accuracy_population): a "
                "run whose audit carries no restricted block is counted in n "
                "and shows in the column beside it, rather than vanishing from "
                "the denominator of a median, which is trap T11.  Over this "
                "population "
                + (
                    "every run carried the statistic"
                    if not reasons
                    else "some did not: " + "; ".join(sorted(reasons))
                ),
            ),
            how_to_read=(
                "the restricted column is the declared statistic; the "
                "whole-state column is large for the partitioned arms by "
                "design — their once-per-run nodes run at the end, so those "
                "outputs are stale at the audit — and is published to show the "
                "exclusion's size, not judged"
            ),
        ),
        columns=(
            Column("arm", "arm"),
            Column("ruler", "ruler"),
            Column("n", "n (runs)", fmt=_fmt_int),
            Column("n_with_the_statistic", "with a restricted statistic", fmt=_fmt_int),
            Column("restricted_median", "restricted median", fmt=_fmt_exp),
            Column("restricted_p90", "restricted p90", fmt=_fmt_exp),
            Column("argmax", "restricted argmax"),
            Column("whole_median", "whole-state median", fmt=_fmt_exp),
            Column("whole_p90", "whole-state p90", fmt=_fmt_exp),
            Column("n_excluded", "components excluded"),
            Column("audit_position", "audit position"),
            Column("instrument", "audit instrument (snapshot positions taken)"),
        ),
        rows=tuple(rows),
        denominator=sum(len(v) for v in by_arm.values()),
        denominator_is=f"evaluation-phase gate runs of {configuration}",
        acceptance=True,
        audit_position_labelled=True,
    )
    table.similarity_verdicts = verdicts  # type: ignore[attr-defined]
    return table


def ownership_rung(
    campaign: Campaign,
    population: stats_mod.Population,
    configuration: str,
    source: str,
) -> Table | None:
    """§4.2.3 — the cost and the price of taking the burn time out of the loop."""
    config = campaign.configuration(configuration)
    if not config.pulsed:
        return None
    by_arm = _by_arm(population, configuration)
    by_seed = _by_arm_and_seed(population, configuration)
    flat = [r for r in by_arm.get("A0", []) if stats_mod.finished(r)]
    rows: list[dict[str, Any]] = []
    reference, values, paired_seeds = _paired(
        by_seed, "A0", "A0p", "node_calls_single_eval"
    )
    ratio = stats_mod.ratio_triple(reference, values) if reference else {}
    pinned = [
        by_seed["A0p"][seed] for seed in sorted(by_seed.get("A0p", {}))
        if stats_mod.finished(by_seed["A0p"][seed])
    ]
    if not by_seed.get("A0p"):
        return None
    residuals = [
        (r.get("lift_residual") or {}).get("raw_s")
        for r in pinned
        if (r.get("lift_residual") or {}).get("raw_s") is not None
    ]
    relatives = [
        abs((r.get("lift_residual") or {}).get("raw_s"))
        / abs(r.get("t_plant_pulse_burn"))
        for r in pinned
        if (r.get("lift_residual") or {}).get("raw_s") is not None
        and r.get("t_plant_pulse_burn")
    ]
    rows.append(
        {
            "n": len(paired_seeds),
            "paired_seeds": ", ".join(str(s) for s in paired_seeds) or "—",
            "pooled": ratio.get("pooled"),
            "median": ratio.get("median"),
            "worse": ratio.get("worse") if ratio else None,
            "residual_s_median": stats_mod.median([abs(v) for v in residuals]),
            "residual_s_bracket": _bracket([abs(v) for v in residuals]),
            "relative_median": stats_mod.median([abs(v) for v in relatives]),
        }
    )
    return Table(
        name=f"ownership rung A0 → A0p — {configuration} — {source}",
        caption=Caption(
            units="node-call ratio dimensionless; the burn-time residual in "
            "seconds and relative to the burn time",
            row_is="this configuration's rung",
            column_is="the cost of taking the burn time out of the flat loop, "
            "and the inconsistency the constant leaves behind",
            population=(
                f"{population.what}; {len(flat)} flat-control and "
                f"{len(pinned)} pinned run(s) of {configuration}"
            ),
            construction=(
                "stats.ratio_triple on node calls of the single evaluation; "
                "the residual is constraint 93's own function at exit, "
                "|value|, median = nearest-rank upper-middle"
            ),
            clauses=(
                "the residual is 0 by construction in the flat control, which "
                "converges the burn time, and is the price of the constant in "
                "the pinned arm",
                "neither column is a claim about the partition: this rung "
                "moves one thing only",
            ),
            how_to_read=(
                "the ratio is the loop's cost of converging the burn time; "
                "the residual is what holding it constant costs in accuracy"
            ),
        ),
        columns=(
            Column("n", "n", fmt=_fmt_int),
            Column("paired_seeds", "paired at seeds"),
            Column("pooled", "A0p/A0 pooled", fmt=_fmt_ratio),
            Column("median", "median", fmt=_fmt_ratio),
            Column("worse", "worse", fmt=_fmt_int),
            Column("residual_s_median", "burn-time residual, s (median)", fmt=_fmt_exp),
            Column("residual_s_bracket", "bracket, s"),
            Column("relative_median", "relative (median)", fmt=_fmt_exp),
        ),
        rows=tuple(rows),
        denominator=len(flat) + len(pinned),
        denominator_is=f"A0 and A0p gate runs of {configuration}",
        acceptance=True,
    )


def per_sweep_overhead(
    campaign: Campaign,
    population: stats_mod.Population,
    configuration: str,
    source: str,
) -> Table:
    """§3.5 check 5 — what the convergence tests cost, in counts.

    The two predicates sit in **columns of their own**.  There is no summed
    column and none can be added: ``tables.Table`` refuses a column declaring
    itself pooled, and ``stats.predicate_widths`` offers no total to reach for.
    """
    by_arm = _by_arm(population, configuration)
    rows: list[dict[str, Any]] = []
    for arm in _arm_order(by_arm):
        for record in [r for r in by_arm[arm] if stats_mod.finished(r)]:
            widths = stats_mod.predicate_widths(record)
            shares = stats_mod.empty_visit_shares(record)
            coupling = widths["coupling_state"]
            upstream = widths["upstream"]
            rows.append(
                {
                    "arm": arm,
                    "seed": record.get("campaign_seed"),
                    "stops_on": widths["stops_on"] or "—",
                    "dispatch_sweeps": record.get("dispatch_sweeps"),
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
    disclaimer = (
        "**the empty block visits are counted and disclaimed, never "
        "repaired**: a block whose members are skipped at the call site is "
        "still visited and still costs a full walk of the model sequence.  The "
        "share quoted is the **sweep** share — the fraction of the run's "
        "dispatch sweeps those visits cost — and over this population it is "
        + (
            ", ".join(f"{v:g} %" for v in shares_seen)
            if shares_seen
            else "not computable on any run here"
        )
        + ".  The *visit* share is a different and larger number and is never "
        "quoted: a block visited with no members costs no sweep at all"
    )
    return Table(
        name=f"per-sweep overhead — {configuration} — {source}",
        caption=Caption(
            units="counts: evaluations of a convergence test, and components "
            "compared summed over them; sweeps are walks of the model sequence",
            row_is="one run of one arm",
            column_is="a counter of one **named** convergence test, or the "
            "sweep total the run's dispatch body walked",
            population=(
                f"{population.what}; the finished evaluation-phase gate runs "
                f"of {configuration}"
            ),
            construction=(
                "stats.predicate_widths and stats.empty_visit_shares, read "
                "from the driver's own counters — exact and "
                "concurrency-invariant, like the node counter"
            ),
            clauses=(
                "**the two predicates are never pooled**: the coupling-state "
                "test and upstream's objective/constraint test are not the "
                "same test, an arm stops on exactly one of them, and their "
                "widths differ by nearly two orders of magnitude.  Their sum "
                "is a number belonging to neither and the table module refuses "
                "a column carrying one",
                disclaimer,
                "no conclusion rests on a timing: this table answers the "
                "per-sweep-overhead question in counts alone",
            ),
            how_to_read=(
                "read the width column of the test the arm actually stops on; "
                "the other test's columns are 0 or blank for that arm, which "
                "is the point of keeping them apart"
            ),
        ),
        columns=(
            Column("arm", "arm"),
            Column("seed", "seed", fmt=_fmt_int),
            Column("stops_on", "stops on"),
            Column("dispatch_sweeps", "dispatch sweeps", fmt=_fmt_int),
            Column("coupling_evaluations", "coupling-state tests", predicate="coupling_state", fmt=_fmt_int),
            Column("coupling_components", "components compared", predicate="coupling_state", fmt=_fmt_int),
            Column("coupling_width", "mean width", predicate="coupling_state", fmt=lambda v: "—" if v is None else f"{v:.1f}"),
            Column("coupling_width_by_block", "width by block", predicate="coupling_state"),
            Column("upstream_evaluations", "objective/constraint tests", predicate="upstream", fmt=_fmt_int),
            Column("upstream_components", "values compared", predicate="upstream", fmt=_fmt_int),
            Column("upstream_width", "mean width", predicate="upstream", fmt=lambda v: "—" if v is None else f"{v:.1f}"),
            Column("empty_sweep_share", "empty-visit sweep share", fmt=_fmt_share),
        ),
        rows=tuple(rows),
        denominator=len(rows),
        denominator_is=(
            f"finished evaluation-phase gate runs of {configuration}"
        ),
        acceptance=True,
    )


def failure_taxonomy(
    campaign: Campaign,
    population: stats_mod.Population,
    configuration: str,
    source: str,
) -> Table:
    """§4.2.6 — every scheduled run a row, with its denominator."""
    by_arm = _by_arm(population, configuration)
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
        rows.append(row)
    return Table(
        name=f"failure taxonomy — {configuration} — {source}",
        caption=Caption(
            units="counts of runs",
            row_is="one arm on this configuration",
            column_is="one disposition of the taxonomy",
            population=f"{population.what}; every gate run of {configuration}",
            construction=(
                "stats.failure_taxonomy — every scheduled run is a row and a "
                "run that wrote no record is counted as no_record, never "
                "skipped"
            ),
            clauses=(
                "the rows sum to the denominator, and the table says so per "
                "arm rather than leaving it to be added up",
                "an arm inactive on a configuration is absent from this table "
                "rather than reading 0: a skipped arm and a failing arm are "
                "different results",
            ),
            how_to_read=(
                "a nonzero crashed column is a machinery result that must be "
                "explained before any ratio on this configuration is cited"
            ),
        ),
        columns=(
            Column("arm", "arm"),
            Column("denominator", "scheduled", fmt=_fmt_int),
            *[Column(name, name, fmt=_fmt_int) for name in classes],
            Column("sums", "rows sum"),
        ),
        rows=tuple(rows),
        denominator=sum(len(v) for v in by_arm.values()),
        denominator_is=f"evaluation-phase gate runs of {configuration}",
        acceptance=True,
    )


def predicate_trial(campaign: Campaign, records_dir: Path) -> Table | None:
    """§4.2.5 — the predicate trial, from the trial gate's own verdict.

    Read from ``gates/predicate_mode/gate.json`` rather than recomputed: the
    decisive-pass counts come from an observer that watches the run's own
    predicate evaluations, which is not a thing a reader of records can
    reconstruct afterwards.  The table's job is to publish the gate's numbers
    in the plan's shape, with the caption rule the plan's §4.2.5 states.
    """
    verdict_path = Path(records_dir) / "predicate_mode" / "gate.json"
    if not verdict_path.exists():
        return None
    verdict = json.loads(verdict_path.read_text())
    rows: list[dict[str, Any]] = []
    for run in verdict.get("runs") or []:
        audit = run.get("audit") or {}
        rows.append(
            {
                "configuration": run.get("configuration"),
                "arm": run.get("arm"),
                "seed": run.get("seed"),
                "evaluations": run.get("n_predicate_evaluations"),
                "crossings": run.get("n_evaluations_with_a_decisive_component"),
                "verdict_changes": run.get(
                    "n_evaluations_where_the_verdict_changed"
                ),
                "identical": "yes" if run.get("identical") else "no",
                "audit_frozen_run_frozen_ruler": (audit.get("frozen") or {}).get("frozen"),
                "audit_frozen_run_mixed_ruler": (audit.get("frozen") or {}).get("mixed"),
                "audit_mixed_run_frozen_ruler": (audit.get("mixed") or {}).get("frozen"),
                "audit_mixed_run_mixed_ruler": (audit.get("mixed") or {}).get("mixed"),
            }
        )
    binding = verdict.get("binding_set") or []
    ratios = sorted(
        {
            round(float(event["value_over_scale"]), 2)
            for event in binding
            if event.get("value_over_scale") is not None
        }
    )
    return Table(
        name="the predicate trial — frozen against mixed",
        caption=Caption(
            units="counts of predicate evaluations; the audit columns are hex "
            "floats of the largest scaled residual",
            row_is="one pair of runs — the same arm, configuration and seed "
            "under each ruler",
            column_is="a count of the trial, or one run's exit audit read on "
            "one named ruler",
            population=(
                verdict.get("population")
                or "the predicate-trial gate's own runs"
            ),
            construction=(
                "the trial gate's observer, which watches each predicate "
                "evaluation of the frozen run and reads it again on the mixed "
                "ruler; the record comparison is bit-for-bit with no tolerance"
            ),
            clauses=(
                "**decisive passes are published as two counts** (the plan's "
                "§4.2.5 caption rule): *crossings* — evaluations at which some "
                "component crossed the tolerance between the rulers — and "
                "*verdict changes* — evaluations whose verdict changed because "
                "the crossing component was the one holding the evaluation "
                "open.  Only the second can make two runs differ, and the "
                "gate binds on it",
                "**the exit audit is on both rulers, never one**: each run is "
                "audited on the frozen and the mixed ruler, so a difference "
                "between the audit columns of one row is a change of ruler and "
                "a difference down a column is a change of run",
                (
                    "the components that made a pass decisive carry |y|/s up "
                    f"to {max(ratios):g} over this population"
                    if ratios
                    else "no component made a pass decisive over this "
                    "population, which is a result about these arms and these "
                    "seeds, stated with its population"
                ),
            ),
            how_to_read=(
                "a pair with no verdict change must be bit-identical, which is "
                "the gate's identity; every difference in this table is "
                "attributable to the named components"
            ),
        ),
        columns=(
            Column("configuration", "configuration"),
            Column("arm", "arm"),
            Column("seed", "seed", fmt=_fmt_int),
            Column("evaluations", "predicate evaluations", predicate="coupling_state", fmt=_fmt_int),
            Column("crossings", "decisive passes: crossings", fmt=_fmt_int),
            Column("verdict_changes", "decisive passes: verdicts changed", fmt=_fmt_int),
            Column("identical", "pair bit-identical"),
            Column("audit_frozen_run_frozen_ruler", "frozen run · frozen ruler"),
            Column("audit_frozen_run_mixed_ruler", "frozen run · mixed ruler"),
            Column("audit_mixed_run_frozen_ruler", "mixed run · frozen ruler"),
            Column("audit_mixed_run_mixed_ruler", "mixed run · mixed ruler"),
        ),
        rows=tuple(rows),
        denominator=len(rows),
        denominator_is="pairs of runs, one per ruler",
        acceptance=True,
    )


# --------------------------------------------------------------------------
# the stage
# --------------------------------------------------------------------------


def tally(campaign: Campaign, *, resume: bool = False) -> dict[str, Any]:
    """The evaluation phase's tables, one set per declared source.

    A *source* is a named subtree of ``runs/gates/`` whose records are a
    comparable set, with the sentence that says why (``tally.SOURCES``).  The
    tally never averages across sources and never averages across the whole
    gate tree: several gates run the same arm at the same seed from different
    entries and three of them run it doctored, so a mean over that tree would
    be a mean over a set nobody can state.
    """
    paths = tally_mod.declared_paths(campaign)
    provenance = tally_mod.survey(paths)
    straddle = tally_mod.assert_one_commit(provenance, resume=resume)
    emitted: list[Table] = []
    verdicts: list[dict[str, Any]] = []
    refusals: list[str] = []
    sources: list[dict[str, Any]] = []
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
                "subpath": source.subpath,
                "what": source.what,
                "n_records": len(population),
                "n_excluded_as_demonstrations": len(population.excluded),
            }
        )
        if population.is_empty:
            continue
        for config in campaign.configurations:
            if not _by_arm(population, config.name):
                continue
            emitted.append(
                cost_per_call(campaign, population, config.name, source.name)
            )
            accuracy = matched_accuracy(
                campaign, population, config.name, source.name
            )
            emitted.append(accuracy)
            verdicts.extend(
                {"source": source.name, "configuration": config.name, **v}
                for v in getattr(accuracy, "similarity_verdicts", [])
            )
            rung = ownership_rung(campaign, population, config.name, source.name)
            if rung is not None:
                emitted.append(rung)
            emitted.append(
                per_sweep_overhead(campaign, population, config.name, source.name)
            )
            emitted.append(
                failure_taxonomy(campaign, population, config.name, source.name)
            )
    trial = predicate_trial(
        campaign, Path(campaign.runs_dir) / tally_mod.GATE_RUNS_SUBPATH
    )
    if trial is not None:
        emitted.append(trial)
    return {
        "phase": PHASE,
        "sources": sources,
        "population": "; ".join(f"{s['source']}: {s['n_records']} record(s)" for s in sources),
        "n_records": sum(s["n_records"] for s in sources),
        "records_outside_every_source": tally_mod.records_outside_every_source(
            campaign
        ),
        "runs_provenance": provenance,
        "runs_straddle_note": straddle,
        "record_contract_refusals": refusals,
        "similarity_verdicts": verdicts,
        "tables": [table.as_record() for table in emitted],
        "n_tables": len(emitted),
    }


#: How many record-contract refusals are printed in full before the rest are
#: summarised.  Every one of them is in the stage's own JSON record; the
#: terminal shows enough to act on and says how many more there are, rather
#: than burying the tables under a hundred identical sentences.
REFUSALS_PRINTED = 5


def print_tally(block: Mapping[str, Any]) -> None:
    """The stage's tables on the terminal, each with its caption."""
    for source in block.get("sources") or []:
        print(
            f"\n  source {source['source']:<16} {source['n_records']:>3} "
            f"record(s) under {source['subpath']}"
        )
        print(f"    {source['what']}")
        if source.get("n_excluded_as_demonstrations"):
            print(
                f"    {source['n_excluded_as_demonstrations']} excluded as "
                f"budget-capped demonstrations"
            )
    outside = block.get("records_outside_every_source") or {}
    if outside:
        print(
            f"\n  {outside.get('n_in_a_declared_source')} of "
            f"{outside.get('n_records_under_runs_gates')} record(s) under "
            f"runs/gates/ are in a declared source; "
            f"{outside.get('n_outside_every_declared_source')} are not, by gate: "
            f"{outside.get('outside_by_gate')}"
        )
    provenance = block.get("runs_provenance") or {}
    print(
        f"  runs surveyed: {provenance.get('n_records')} record(s) at "
        f"{provenance.get('heads')}"
    )
    if block.get("runs_straddle_note"):
        print(f"  NOTE: {block['runs_straddle_note']}")
    refused = list(block.get("record_contract_refusals") or [])
    for line in refused[:REFUSALS_PRINTED]:
        print(f"  RECORD REFUSED: {line}")
    if len(refused) > REFUSALS_PRINTED:
        print(
            f"  RECORD REFUSED: and {len(refused) - REFUSALS_PRINTED} more, "
            f"all in this stage's own record"
        )
    for table in block.get("tables") or []:
        print(f"\n  --- {table['table']}")
        print(f"      caption: {table['caption']}")
        for line in _rendered(table):
            print(f"      {line}")
        print(f"      n = {table['denominator']} ({table['denominator_is']})")
    for verdict in block.get("similarity_verdicts") or []:
        print(
            f"  similarity {verdict['configuration']} {verdict['pair']} on "
            f"{verdict['ruler']}: median {verdict['median']['similar']} "
            f"({verdict['median']['why']}), p90 {verdict['p90']['similar']} "
            f"({verdict['p90']['why']})"
        )


def _rendered(table: Mapping[str, Any]) -> list[str]:
    """A table record's markdown body as terminal lines."""
    return [
        line
        for line in table["markdown"].splitlines()
        if line.startswith("|")
    ]
