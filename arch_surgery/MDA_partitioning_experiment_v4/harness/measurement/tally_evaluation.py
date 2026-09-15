#!/usr/bin/env python
"""The evaluation phase's tally: what one `call_models` cost, and how accurate.

A **tally** summarises the records into the tables the experiment plan's §4
asks for.  It has nothing to pass — what passes is the gate over the same
records — so it is registered as a *measurement stage* and runs under
``--measure``, never under ``--gate``.  Where the tally *checks* something,
that check is a gate with teeth and lives in ``harness/gates/gate_tally.py``.

Six tables, five the shape of one of the plan's §4.2 placeholders and one
beside the second:

``cost_per_call``      §4.2.1 — model executions per evaluation, sweeps per
                       evaluation, sweeps per block, the arrangement-method
                       calls beside them, and the ratio triple against the
                       declared reference arm.
``matched_accuracy``   §4.2.2 — the exit-audit maximum, restricted and whole
                       state, **on both rulers**, with the argmax component
                       named rather than averaged, and the similarity verdict.
``fixed_point_distance`` beside §4.2.2 — how far apart two arms' exit states
                       are at the same entry: the predicate's residual between
                       the two states the runs wrote, restricted as the audit
                       is, reported and not accepted on (added after the
                       campaign by task A76 (fixed-point-distance)).
``ownership_rung``     §4.2.3 — the flat control against the flat control with
                       the burn time owned by a constant.
``per_sweep_overhead`` §3.5 check 5 — what each arm's convergence test cost, in
                       evaluations and components compared, with the empty
                       block visits' **sweep** share disclaimed and the two
                       predicates in columns of their own.
``failure_taxonomy``   §4.2.6 — every scheduled run a row, denominators stated.
``node_calls_per_block`` the report's headline shape 3 (``REPORT_HEADLINE_TABLES.md``):
                       mean node calls per evaluation **per block**, every
                       configuration stacked in one table per source, with the
                       ratio of the partitioned arm to its declared reference;
                       the grouping is derived from the committed node map and
                       the per-run artifact (added by task A79 (report-captions)).

**Captions, since task A79 (report-captions).** Every table still declares
units, row, column, population and construction (``tables.Caption``) — that
declaration is printed **once per table kind** in the report's results
appendix — and carries a ``summary`` of a few lines, which is what the report
prints under the table.  Text that varies per table (the reference arm and
whether it is a fallback, the audit position, a population's own share) lives
in the summary; the declaration is the same for every table of a kind.  A
table whose rows are individual runs is marked ``detail`` and is rendered into
the companion file, not the report.

**What the population is, stated once here and in every caption.** These
tables are over **one declared population** (``tally.published_sources``): the
**campaign** sources — the campaign plan's own job sets, one per run stage,
under ``runs/campaign/`` — once a campaign record exists, and the **gate**
sources — the records the verification gates made, under ``runs/gates/``, one
or two seeds per arm — while none does.  Never both: with the campaign present
a gate record is refused by kind at the population's construction, and every
caption and denominator sentence names the kind of run it is over, read from
the records.  A source whose family is not published is counted and named in
the stage record rather than tabled.

Within the evaluation phase the pairing across arms is by **seed** for the
displaced regime and by **design-vector column** for the stencil regime
(:func:`pairing_key`), because the stencil points all carry seed 0 and a
seed-keyed pairing over them would compare one point per arm under a caption
naming the whole set.

Written by task **A53 (harness-tally)**; the campaign sources and the
stencil pairing by task **A75 (campaign-tally-source)**.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from harness.child import predicate as predicate_mod
from harness.experiment import arms as arms_mod
from harness.measurement import stats as stats_mod
from harness.measurement import tally as tally_mod
from harness.measurement import tables as tables_mod
from harness.core.config import Campaign
from harness.measurement.tables import Caption, Column, Table, cell_list

__all__ = ["tally", "print_tally", "PHASE", "pairing_key", "node_grouping"]

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
    if present is None or "A1" in present:
        return "A1", (
            "pulsed: the declared reference, because it and the partitioned "
            "arm sit on the same reduced map"
        )
    return "A0", (
        "pulsed, but this population carries no A1 run, so the ratio falls "
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


def pairing_key(record: Mapping[str, Any]) -> int | None:
    """What two arms' runs are paired on: the seed, or the stencil column.

    A displaced or unperturbed entry is one job per (arm, seed) and pairs by
    seed.  A stencil point is one job per (arm, column, sign) and every one
    of them carries seed 0, so within a one-sign stencil source the pairing
    key is the **design-vector column**, read from the record's own job
    identity (``job_identity.stencil_column``, the pool's stamp); a record
    that carries neither is unpaired, never keyed 0.
    """
    if record.get("regime") == "stencil":
        column = (record.get("job_identity") or {}).get("stencil_column")
        if column is None:
            column = record.get("stencil_column")
        return None if column is None else int(column)
    seed = record.get("campaign_seed")
    return None if seed is None else int(seed)


def _by_arm_and_seed(
    population: stats_mod.Population, configuration: str
) -> dict[str, dict[int, Mapping[str, Any]]]:
    """Records indexed by arm and pairing key, for a **keyed** pairing.

    A ratio between two arms is paired point by point or it is not paired at
    all: pairing two lists by position compares whichever runs happened to
    sort first, which is a ratio over a population nobody can state.  The key
    is :func:`pairing_key` — the seed, or the stencil column.  Within one
    declared source an (arm, key) is one job; a second record for the same
    key would be a source that is not the comparable set it declares itself
    to be, and the first is kept.
    """
    out: dict[str, dict[int, Mapping[str, Any]]] = {}
    for record in population.records:
        if record.get("campaign_configuration") != configuration:
            continue
        key = pairing_key(record)
        if key is None:
            continue
        out.setdefault(str(record.get("campaign_arm")), {}).setdefault(key, record)
    return out


def _paired_with(population: stats_mod.Population) -> str:
    """The column header's word for the pairing key of this population."""
    regimes = {str(r.get("regime")) for r in population.records}
    return "columns" if regimes == {"stencil"} else "seeds"


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
                "The reference arm is the declared one "
                "(tally_evaluation.reference_arm): A1 on a pulsed "
                "configuration, A0 on a steady-state one, and A0 as a stated "
                "fallback where the population carries no A1 run — the "
                "caption says which"
            ),
            summary=(
                f"Node calls per evaluation by arm on {configuration}, "
                f"{tally_mod.source_phrase(source)}, with the ratio against "
                f"{base} pooled, as the per-run median and as runs on which the "
                f"arm cost more. {_reference_sentence(base, why_base)} Prime "
                f"calls stand beside the node calls, not in them."
            ),
            clauses=(
                "the arrangement-method calls are stamped beside the node "
                "calls and are never pooled into them",
                "the empty block visits are included in every sweep count and "
                "are disclaimed in the per-sweep-overhead table, which states "
                "their sweep share",
                f"these are {population.runs_word}: the population named "
                f"above and no other",
                "pairs are keyed by seed in a displaced or reference source and "
                "by design-vector column in a stencil source; the pairing "
                "column's heading says which",
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
            Column("paired_seeds", f"paired with {base} at {_paired_with(population)}"),
            Column("pooled", f"vs {base} pooled", fmt=_fmt_ratio),
            Column("median", f"vs {base} median", fmt=_fmt_ratio),
            Column("worse", "worse", fmt=_fmt_int),
        ),
        rows=tuple(rows),
        denominator=denominator,
        denominator_is=f"evaluation-phase {population.runs_word} of {configuration}",
        acceptance=True,
        kind="cost_per_call",
        report_omits=("paired_seeds",),
    )


def _reference_sentence(base: str, why_base: str) -> str:
    """The one thing a cost-ratio caption must say: which arm, and why."""
    if why_base.startswith("steady state"):
        return f"{base} is the reference (steady state: no burn-time coupling)."
    if why_base.startswith("pulsed:"):
        return f"{base} is the declared reference (the same reduced map as A2)."
    return (
        f"**Fallback**: no A1 run here, so the ratio is against {base}, not "
        f"the declared pair."
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
                "**the audit position is a column**: a residual taken at the "
                "entry to the output path and one taken after the run are "
                "different quantities and never share an unlabelled table",
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
                "the denominator of a median, which is trap T11; the caption "
                "says whether every run of the population carried it",
            ),
            summary=(
                f"Exit accuracy by arm on {configuration}, "
                f"{tally_mod.source_phrase(source)}: the restricted maximum "
                f"scaled residual (median, p90) on both rulers, the whole-state "
                f"maximum and the argmax component; audit position "
                + (", ".join(positions) if positions else "not recorded")
                + ". The whole-state column is large for A2 by design and is "
                "not judged."
                + (
                    ""
                    if not reasons
                    else " Some runs carried no restricted statistic: "
                    + "; ".join(sorted(reasons))
                    + "."
                )
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
        denominator_is=f"evaluation-phase {population.runs_word} of {configuration}",
        acceptance=True,
        audit_position_labelled=True,
        kind="matched_accuracy",
    )
    table.similarity_verdicts = verdicts  # type: ignore[attr-defined]
    return table


#: The evaluation phase's ladder, in rung order (plan §3.2): adjacent arms
#: differ by one named thing.  A configuration that skips an arm (st skips
#: A1) has the rung across the gap.
LADDER: tuple[str, ...] = ("AR", "A0", "A1", "A2")


def ladder_pairs(present: Sequence[str], headline_base: str) -> list[tuple[str, str, str]]:
    """``(base, arm, role)`` for every pair the fixed-point distance reports.

    One row per rung of the ladder among the arms present — ``AR → A0`` (the
    stopping rule), ``A0 → A1`` (ownership), ``A1 → A2`` (the partition) —
    with the partitioned arm against the declared reference marked
    ``headline``, and on a pulsed configuration ``A0 → A2`` beside, which is
    the previous revision's pair and the steady-state configuration's
    headline, so the three configurations share a readable row.
    """
    ladder = [arm for arm in LADDER if arm in present]
    out: list[tuple[str, str, str]] = []
    for base, arm in zip(ladder, ladder[1:]):
        role = "headline" if (arm == "A2" and base == headline_base) else "rung"
        out.append((base, arm, role))
    if "A0" in ladder and "A2" in ladder and headline_base != "A0":
        out.append(("A0", "A2", "beside"))
    return out


def _excluded_by_the_per_run_nodes(
    campaign: Campaign,
    configuration: str,
    record: Mapping[str, Any],
    spec_keys: Sequence[str],
    tested_keys: Sequence[str],
) -> tuple[set[str], set[str], str] | tuple[None, None, str]:
    """The components the once-per-run nodes write, re-derived for *record*.

    The same derivation as the exit audit's (node list from the per-run
    artifact → the committed write census → the spec's keys; never a prefix
    rule), from the artifacts in this tree's ``harness/data/``, and **checked
    against the record**: the audit stamped the sha256 of the set it excluded
    — the written components among the *tested* (continuous and non-finite)
    ones, which is the second set returned — and a derivation that lands
    elsewhere means the artifacts on disk are not the ones the run read, which
    is a refusal and not a smaller table.  The first set returned is every
    spec component those nodes write, of any category, which is what the
    restricted residual leaves out.
    """
    audit = (record.get("exit_audit") or {}).get("frozen") or {}
    restricted = audit.get("restricted")
    if not isinstance(restricted, Mapping):
        return None, None, "the record's exit audit carries no restricted block"
    artifact = Path(campaign.data_dir) / Path(str(restricted.get("artifact"))).name
    census_path = Path(campaign.data_dir) / "node_writesets.json"
    if not artifact.exists() or not census_path.exists():
        return None, None, (
            f"the per-run artifact {artifact.name} or the write census is not "
            f"in this tree's data directory"
        )
    nodes = list(json.loads(artifact.read_text())["post_solve_nodes"])
    census = json.loads(census_path.read_text())["per_scenario"]
    if configuration not in census:
        raise tally_mod.TallyError(
            f"{census_path} carries no write census for {configuration!r}; "
            f"the excluded set would be guessed, so the distance is refused"
        )
    writes_by_node = census[configuration]["writes_by_node"]
    excluded: set[str] = set()
    for node in nodes:
        excluded |= set(writes_by_node.get(node) or ())
    written = excluded & set(spec_keys)
    excluded = written & set(tested_keys)
    import hashlib  # noqa: PLC0415 - one digest, here only

    digest = hashlib.sha256("\n".join(sorted(excluded)).encode()).hexdigest()
    if digest != restricted.get("excluded_sha256"):
        raise tally_mod.TallyError(
            f"the excluded set derived from {artifact.name} and "
            f"{census_path.name} hashes to {digest[:12]}…, the record's audit "
            f"stamped {str(restricted.get('excluded_sha256'))[:12]}…: the "
            f"artifacts in this tree are not the ones the run read, so the "
            f"restricted distance is refused rather than published over a set "
            f"nobody chose"
        )
    return written, excluded, ""


def _exit_state(
    where: Mapping[str, Path], record: Mapping[str, Any], spec
) -> tuple[list | None, str]:
    """The exit coupling state a run wrote, restored exactly, or why not."""
    digest = record.get("job_digest")
    directory = where.get(str(digest)) if digest else None
    if directory is None:
        return None, "the record's directory is unknown to the source"
    name = record.get("exit_state_written_to")
    if not name:
        return None, "the run wrote no exit state (exit_state_written_to is empty)"
    path = Path(directory) / str(name)
    if not path.exists():
        return None, f"{name} is missing from the run directory"
    try:
        return predicate_mod.restore_snapshot(spec, json.loads(path.read_text())), ""
    except predicate_mod.PredicateError as exc:
        raise tally_mod.TallyError(
            f"{path}: the exit state does not restore against this tree's "
            f"coupling-state artifact ({exc}); a distance over a mapping nobody "
            f"chose is refused"
        ) from exc


def fixed_point_distance(
    campaign: Campaign,
    population: stats_mod.Population,
    configuration: str,
    source: str,
    where: Mapping[str, Path],
) -> Table | None:
    """Beside §4.2.2 — how far apart two arms' exit states are at the same entry.

    One row per arm against the declared reference arm of the evaluation
    phase.  The statistic is ``stats.fixed_point_distance``; the residual
    itself is the predicate's own (``harness/child/ystate.py``, decision
    D14(c): one implementation of the coupling-state test), evaluated between
    the two exit states the runs wrote.  ``where`` maps a record's job digest
    to its run directory, because the record's own ``outdir`` names the tree
    the campaign ran in and not the tree the records were seeded into.
    """
    config = campaign.configuration(configuration)
    by_arm = _by_arm(population, configuration)
    by_seed = _by_arm_and_seed(population, configuration)
    headline_base, why_base = reference_arm(config.pulsed, set(by_arm))
    pairs_to_report = ladder_pairs(list(by_seed), headline_base)
    if not pairs_to_report:
        return None
    spec = predicate_mod.load_spec(config.coupling_state_path)
    spec_keys = [spec.name(i) for i in range(len(spec.keys))]
    # The audit's exclusion count is over the components its scaled vector
    # holds: the continuous and non-finite ones, in index order (ystate's
    # ``idx_c``).  Discrete and constant components are tested for equality,
    # not scaled, so they are not in that count.
    tested_keys = [
        spec.name(i)
        for i in sorted(set(spec.idx_continuous) | set(spec.idx_nonfinite))
    ]
    tau = float(campaign.tau)
    rows: list[dict[str, Any]] = []
    n_pairs_total = 0
    states: dict[tuple[str, int], tuple[list | None, str]] = {}

    def state_of(arm: str, key: int) -> tuple[list | None, str]:
        if (arm, key) not in states:
            states[(arm, key)] = _exit_state(where, by_seed[arm][key], spec)
        return states[(arm, key)]

    for base, arm, role in pairs_to_report:
        pairs: list[dict[str, Any]] = []
        for key in sorted(set(by_seed[base]) & set(by_seed[arm])):
            left, right = by_seed[base][key], by_seed[arm][key]
            pair: dict[str, Any] = {"key": key, "compared": False}
            if not (stats_mod.finished(left) and stats_mod.finished(right)):
                pair["why"] = "a side did not finish"
                pairs.append(pair)
                continue
            y_base, why_a = state_of(base, key)
            y_arm, why_b = state_of(arm, key)
            if y_base is None or y_arm is None:
                pair["why"] = why_a or why_b
                pairs.append(pair)
                continue
            written_a, excluded_a, why_x = _excluded_by_the_per_run_nodes(
                campaign, configuration, left, spec_keys, tested_keys
            )
            written_b, excluded_b, why_y = _excluded_by_the_per_run_nodes(
                campaign, configuration, right, spec_keys, tested_keys
            )
            if excluded_a is None or excluded_b is None:
                pair["why"] = why_x or why_y
                pairs.append(pair)
                continue
            if excluded_a != excluded_b or written_a != written_b:
                raise tally_mod.TallyError(
                    f"{configuration} {base}/{arm} at key {key}: the two "
                    f"records' audits excluded different sets "
                    f"({len(excluded_a)} and {len(excluded_b)} components); "
                    f"a restricted distance over two restrictions is refused"
                )
            kept = [i for i, name in enumerate(spec_keys) if name not in written_a]
            restricted = spec.residual(y_base, y_arm, subset=kept, ruler="frozen")
            whole = spec.residual(y_base, y_arm, ruler="frozen")
            pair.update(
                {
                    "compared": True,
                    "restricted_max": float(restricted.max),
                    "restricted_max_hex": float(restricted.max).hex(),
                    "restricted_argmax": (
                        None if restricted.argmax is None else spec.name(restricted.argmax)
                    ),
                    "restricted_n_above_tau": restricted.n_above(tau),
                    "whole_max": float(whole.max),
                    "whole_argmax": (
                        None if whole.argmax is None else spec.name(whole.argmax)
                    ),
                    "categorically_clean": not (
                        restricted.mismatch_discrete
                        or restricted.moved_constant
                        or restricted.nan_new
                    ),
                    "n_excluded": len(excluded_a),
                }
            )
            pairs.append(pair)
        n_pairs_total += len(pairs)
        summary = stats_mod.fixed_point_distance(pairs, tau=tau)
        rows.append(
            {
                "pair": f"{arm}/{base}",
                "role": role,
                "n": summary["n"],
                "n_compared": summary["n_compared"],
                "not_compared": cell_list(
                    [f"{k}: {v}" for k, v in sorted(summary["not_compared_by_reason"].items())]
                ),
                "restricted_median": summary["restricted_median"],
                "restricted_p90": summary["restricted_p90"],
                "restricted_max": summary["restricted_max"],
                "worst_pair": summary["worst_pair_key"],
                "argmax": cell_list(summary["argmax_components"]),
                "n_pairs_above_tau": summary["n_pairs_above_tau"],
                "n_pairs_unclean": summary["n_pairs_unclean"],
                "whole_median": summary["whole_median"],
                "whole_p90": summary["whole_p90"],
                "n_excluded": cell_list([str(v) for v in summary["n_excluded"]]),
            }
        )
    positions = sorted(
        {
            str(r.get("audit_position"))
            for arm in by_seed
            for r in by_seed[arm].values()
            if r.get("audit_position")
        }
    )
    paired_on = _paired_with(population)
    return Table(
        name=f"fixed-point distance — {configuration} — {source}",
        caption=Caption(
            units=(
                "dimensionless: the largest scaled difference between two "
                "arms' exit coupling states at the same entry, in the units "
                "τ is stated in"
            ),
            row_is=(
                "one pair of arms: each rung of the evaluation phase's ladder "
                "(adjacent arms, differing by one named thing) and, marked "
                "headline, the partitioned arm against the declared reference "
                "(A1 on a pulsed configuration, A0 on a steady-state one); on "
                "a pulsed configuration A2/A0 is published beside, the "
                "previous revision's pair"
            ),
            column_is=(
                "the pairs the two arms share (by seed, or by design-vector "
                "column in a stencil source), how many of "
                "them were compared and why the rest were not, the restricted "
                "distance's median, p90 and worst pair, the components the "
                "maximum sat on, the pairs with any restricted component at "
                "or above τ, the pairs where a discrete component differs or "
                "a constant moved, and the whole-state distance beside"
            ),
            population=(
                f"{population.what}; {n_pairs_total} pair(s) of {configuration}"
            ),
            construction=(
                "stats.fixed_point_distance: the predicate's own scaled "
                "residual (harness/child/ystate.py, frozen ruler: "
                "max_i |y_arm,i − y_base,i| / s_i) evaluated between the two "
                "exit states the runs wrote (y_exit.json), restricted to the "
                "components the configuration's once-per-run deferred nodes do "
                "not write — the exit audit's own exclusion, re-derived from "
                "the artifacts and checked against the digest the audit "
                "stamped; median = nearest-rank upper-middle, p90 = "
                "nearest-rank ceil(0.9 n) over the compared pairs"
            ),
            clauses=(
                "**reported, not accepted on**: no acceptance rule was "
                "pre-declared for this quantity; it was added after the "
                "campaign by task A76 (fixed-point-distance) from the exit "
                "states already on disk, and no model ran to produce it",
                "**what it adds to the matched-accuracy table beside it**: "
                "that table says how far each arm is from *a* fixed point; "
                "this one says how far the two arms' points are from *each "
                "other*.  Both are on the frozen ruler; the mixed ruler is not "
                "offered here because its denominator reads a current value "
                "and a distance between two states has no current side",
                "**the exit states are the ones the audit read**: taken at "
                "the audit position the caption names, before the audit's own "
                "sweep, so a state moved by the instrument cannot enter this "
                "table",
                "**n counts the pairs the two arms share**, and n_compared the "
                "ones on which both exit states exist and both audits carry the "
                "restriction; the shortfall is named by reason in the column "
                "beside, never dropped (trap T11)",
                "the whole-state distance is large for the partitioned arm by "
                "design — its once-per-run nodes run at the end, so their "
                "outputs are stale at exit — and is published to show the "
                "exclusion's size, not judged",
            ),
            how_to_read=(
                "a restricted median far below τ with 0 pairs above τ means "
                "the two arms stopped at the same fixed point to within the "
                "tolerance they were asked for; a pair above τ names an entry "
                "on which they did not, and the worst-pair column says which"
            ),
            summary=(
                f"Distance between two arms' exit states at the same entry on "
                f"{configuration}, {tally_mod.source_phrase(source)}: restricted "
                f"median, p90, worst pair and the pairs with a component "
                f"≥ τ = {tau:g}, one row per rung of the ladder; headline pair "
                f"A2/{headline_base}; exit states taken at "
                + (", ".join(positions) if positions else "an unrecorded position")
                + ". Reported, not accepted on."
            ),
        ),
        columns=(
            Column("pair", "pair"),
            Column("role", "role"),
            Column("n", f"n ({paired_on} shared)", fmt=_fmt_int),
            Column("n_compared", "compared", fmt=_fmt_int),
            Column("not_compared", "not compared (reason: count)"),
            Column("restricted_median", "restricted median", fmt=_fmt_exp),
            Column("restricted_p90", "restricted p90", fmt=_fmt_exp),
            Column("restricted_max", "restricted worst", fmt=_fmt_exp),
            Column("worst_pair", f"worst {paired_on[:-1]}", fmt=_fmt_int),
            Column("argmax", "restricted argmax"),
            Column("n_pairs_above_tau", "pairs with a component ≥ τ", fmt=_fmt_int),
            Column("n_pairs_unclean", "pairs categorically unclean", fmt=_fmt_int),
            Column("whole_median", "whole-state median", fmt=_fmt_exp),
            Column("whole_p90", "whole-state p90", fmt=_fmt_exp),
            Column("n_excluded", "components excluded"),
        ),
        rows=tuple(rows),
        denominator=n_pairs_total,
        denominator_is=(
            f"evaluation-phase pairs of {configuration} over the ladder's rungs"
        ),
        acceptance=False,
        kind="fixed_point_distance",
    )


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
        by_seed, "A0", "A1", "node_calls_single_eval"
    )
    ratio = stats_mod.ratio_triple(reference, values) if reference else {}
    pinned = [
        by_seed["A1"][seed] for seed in sorted(by_seed.get("A1", {}))
        if stats_mod.finished(by_seed["A1"][seed])
    ]
    if not by_seed.get("A1"):
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
        name=f"ownership rung A0 → A1 — {configuration} — {source}",
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
            summary=(
                f"The rung A0 → A1 on {configuration}, "
                f"{tally_mod.source_phrase(source)}: the per-call cost of "
                f"pinning the burn time (A1/A0) and the residual the constant "
                f"leaves at exit, in seconds and relative to the burn time. "
                f"Not a claim about the partition."
            ),
        ),
        columns=(
            Column("n", "n", fmt=_fmt_int),
            Column("paired_seeds", f"paired at {_paired_with(population)}"),
            Column("pooled", "A1/A0 pooled", fmt=_fmt_ratio),
            Column("median", "median", fmt=_fmt_ratio),
            Column("worse", "worse", fmt=_fmt_int),
            Column("residual_s_median", "burn-time residual, s (median)", fmt=_fmt_exp),
            Column("residual_s_bracket", "bracket, s"),
            Column("relative_median", "relative (median)", fmt=_fmt_exp),
        ),
        rows=tuple(rows),
        denominator=len(flat) + len(pinned),
        denominator_is=f"A0 and A1 {population.runs_word} of {configuration}",
        acceptance=True,
        kind="ownership_rung",
        report_omits=("paired_seeds",),
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
        "dispatch sweeps those visits cost — stated per population in the "
        "caption.  The *visit* share is a different and larger number and is "
        "never quoted: a block visited with no members costs no sweep at all"
    )
    shares_sentence = (
        "The empty-visit sweep share over this population is "
        + (
            ", ".join(f"{v:g} %" for v in shares_seen)
            if shares_seen
            else "not computable on any run here"
        )
        + "."
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
                f"{population.what}; the finished evaluation-phase {population.runs_word} "
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
            summary=(
                f"Convergence-test cost per finished run on {configuration}, "
                f"{tally_mod.source_phrase(source)}: sweeps, and for the test "
                f"the arm stops on its evaluations, components compared and "
                f"mean width; the two predicates are never summed. "
                f"{shares_sentence}"
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
            f"finished evaluation-phase {population.runs_word} of {configuration}"
        ),
        acceptance=True,
        kind="per_sweep_overhead",
        detail=True,
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
            population=f"{population.what}; every {population.runs_word[:-1]} of {configuration}",
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
            summary=(
                f"Every scheduled evaluation of {configuration}, "
                f"{tally_mod.source_phrase(source)}, by arm and disposition, "
                f"the rows summing to the scheduled count; the detail is each "
                f"unfinished run's last traceback line."
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
        denominator_is=f"evaluation-phase {population.runs_word} of {configuration}",
        acceptance=True,
        kind="failure_taxonomy",
    )


def node_grouping(
    campaign: Campaign,
    configuration: str,
    records: Sequence[Mapping[str, Any]],
    *,
    phase: str,
) -> list[dict[str, Any]]:
    """The node groups the per-block and per-module tables print, derived.

    From the committed node map (``harness/data/dsm_node_map.json``) and the
    configuration's per-run artifact — the one **every record of the
    configuration names** in ``per_run_artifact``; two records naming two
    artifacts is a refusal — whose ``post_solve_nodes`` are the once-per-run
    group.  The artifact's node set is checked against what each record's
    exit audit stamped as excluded (``exit_audit.restricted.per_run_nodes``)
    where a record carries it, so the grouping is the one the runs were
    audited under and not one read off a file nobody ran.  The nodes grouped
    are the ones any record's census counted (:func:`stats.per_node_census`).
    """
    names = sorted(
        {Path(str(r.get("per_run_artifact"))).name for r in records if r.get("per_run_artifact")}
    )
    if not names:
        raise tally_mod.TallyError(
            f"{configuration}: no record names a per-run artifact; the "
            f"once-per-run group would be guessed, so the table is refused"
        )
    # The committed input file and the lifted one each have a per-run
    # artifact (the optimisation phase's flat arms name the first, the lifted
    # arms the second); the grouping needs their node sets to be the same set,
    # and refuses otherwise.
    node_sets: dict[str, list[str]] = {}
    for name in names:
        artifact = Path(campaign.data_dir) / name
        if not artifact.exists():
            raise tally_mod.TallyError(
                f"{configuration}: the per-run artifact {name} the records name "
                f"is not in this tree's data directory"
            )
        node_sets[name] = sorted(
            str(n) for n in json.loads(artifact.read_text())["post_solve_nodes"]
        )
    if len({tuple(v) for v in node_sets.values()}) != 1:
        raise tally_mod.TallyError(
            f"{configuration}: the records name {names}, whose once-per-run "
            f"node sets differ ({node_sets}); one grouping cannot serve them "
            f"and the table is refused rather than grouped by a guess"
        )
    per_run = node_sets[names[0]]
    for record in records:
        audited = ((record.get("exit_audit") or {}).get("restricted") or {}).get("per_run_nodes")
        if audited is not None and set(audited) != set(per_run):
            raise tally_mod.TallyError(
                f"{configuration}: the exit audit of {stats_mod._label(record)} "
                f"excluded {sorted(audited)} and the artifact(s) {names} name "
                f"{sorted(per_run)}; the grouping would not be the one the run "
                f"was audited under"
            )
    node_map = json.loads((Path(campaign.data_dir) / "dsm_node_map.json").read_text())
    seen: set[str] = set()
    for record in records:
        seen |= set(stats_mod.per_node_census(record, phase=phase))
    return stats_mod.node_groups(node_map, per_run, sorted(seen))


#: Up to this many nodes a group's members are listed by name in the table;
#: a larger group prints the node map's label for the module and its count,
#: the membership being the committed map's (``harness/data/dsm_node_map.json``).
MEMBERS_LISTED_UP_TO = 4


def group_members(campaign: Campaign, group: str, nodes: Sequence[str]) -> str:
    """The *which* cell of a node-group row: names, or the map's label."""
    if len(nodes) <= MEMBERS_LISTED_UP_TO:
        return ", ".join(nodes)
    node_map = json.loads((Path(campaign.data_dir) / "dsm_node_map.json").read_text())
    label = str(((node_map.get("modules") or {}).get(group) or {}).get("label") or group)
    return f"{label}: {len(nodes)} nodes (the committed node map's members)"


def node_calls_per_block(
    campaign: Campaign,
    population: stats_mod.Population,
    source: str,
) -> Table | None:
    """The report's headline shape 3: node calls per block, configurations stacked.

    One table per source.  For each configuration the population carries, one
    row per node group (:func:`node_grouping`) and a TOTAL row; a column per
    evaluation-phase arm with the **mean node calls per evaluation** over the
    arm's finished runs (``node_census.counted``, the measured evaluation
    alone), and the **pooled** ratio of the partitioned arm to the
    configuration's declared reference (Σ A2 / Σ reference over the pairs both
    sides finished, keyed as :func:`pairing_key` keys them).  The TOTAL row's
    ratio is the cost-per-call table's pooled ratio, reached by another road:
    the census sums to ``node_calls_single_eval`` on every record.
    """
    rows: list[dict[str, Any]] = []
    n_finished = 0
    any_arms = False
    for config in campaign.configurations:
        by_arm = _by_arm(population, config.name)
        if not by_arm:
            continue
        any_arms = True
        finished_by_arm = {
            arm: [r for r in records if stats_mod.finished(r)]
            for arm, records in by_arm.items()
        }
        every = [r for records in finished_by_arm.values() for r in records]
        n_finished += len(every)
        if not every:
            continue
        groups = node_grouping(campaign, config.name, every, phase=PHASE)
        base, _why = reference_arm(config.pulsed, set(by_arm))
        by_seed = _by_arm_and_seed(population, config.name)
        # Per run, calls per group, for the means and the paired ratio.
        per_group_calls: dict[str, dict[str, list[int]]] = {}
        for arm, records in finished_by_arm.items():
            for record in records:
                counted = stats_mod.per_node_census(record, phase=PHASE)
                grouped = stats_mod.census_by_group(counted, groups)
                grouped["TOTAL"] = sum(counted.values())
                for group, calls in grouped.items():
                    per_group_calls.setdefault(group, {}).setdefault(arm, []).append(calls)
        paired_keys = sorted(
            k
            for k in set(by_seed.get(base, {})) & set(by_seed.get("A2", {}))
            if stats_mod.finished(by_seed[base][k]) and stats_mod.finished(by_seed["A2"][k])
        ) if base in by_seed and "A2" in by_seed else []
        labels = [(g["group"], g["nodes"]) for g in groups] + [("TOTAL", [n for g in groups for n in g["nodes"]])]
        for group, nodes in labels:
            row: dict[str, Any] = {
                "configuration": config.name,
                "block": group,
                "n_nodes": len(nodes),
                "nodes": group_members(campaign, group, nodes) if group != "TOTAL" else "all counted nodes",
                "reference": base,
            }
            for arm in LADDER:
                values = per_group_calls.get(group, {}).get(arm)
                row[arm] = _mean(values) if values else None
            ratio = None
            if paired_keys:
                left = [
                    stats_mod.census_by_group(
                        stats_mod.per_node_census(by_seed[base][k], phase=PHASE), groups
                    ) | {"TOTAL": sum(stats_mod.per_node_census(by_seed[base][k], phase=PHASE).values())}
                    for k in paired_keys
                ]
                right = [
                    stats_mod.census_by_group(
                        stats_mod.per_node_census(by_seed["A2"][k], phase=PHASE), groups
                    ) | {"TOTAL": sum(stats_mod.per_node_census(by_seed["A2"][k], phase=PHASE).values())}
                    for k in paired_keys
                ]
                total_reference = sum(v[group] for v in left)
                ratio = (
                    sum(v[group] for v in right) / total_reference
                    if total_reference
                    else None
                )
            row["ratio"] = ratio
            row["n_pairs"] = len(paired_keys)
            rows.append(row)
    if not any_arms:
        return None
    return Table(
        name=f"node calls per block — {source}",
        caption=Caption(
            units="model-node executions per `call_models` evaluation, per "
            "block; the ratio is dimensionless",
            row_is="one node group of one configuration (the three modules, "
            "the pulse node, the feed-forward tail and the once-per-run "
            "deferred nodes, each as the committed node map and the "
            "configuration's per-run artifact place them), then that "
            "configuration's TOTAL over every counted node",
            column_is="one evaluation-phase arm's mean node calls per "
            "evaluation over its finished runs, or the pooled ratio of A2 to "
            "the configuration's declared reference over the pairs both sides "
            "finished",
            population=(
                f"{population.what}; {n_finished} finished run(s) over every "
                f"configuration the source carries"
            ),
            construction=(
                "stats.per_node_census (node_census.counted — the measured "
                "evaluation alone, frozen before the exit audit's sweep) "
                "summed over each group of stats.node_groups; the group's "
                "mean is the arithmetic mean over the arm's finished runs; the "
                "ratio is Σ A2 / Σ reference over the paired runs "
                "(stats.per_seed_ratio_summary's pooled reading), the "
                "reference being A1 on a pulsed configuration and A0 on a "
                "steady-state one (tally_evaluation.reference_arm)"
            ),
            clauses=(
                "the once-per-run group holds the configuration's deferred "
                "nodes whatever module the map assigns them: the partitioned "
                "arm runs them once, after the solve, so their calls are not a "
                "module's loop cost",
                "a group absent from a configuration's rows means no such node "
                "ran there, not that it cost nothing",
                "the TOTAL row is the cost-per-call table's per-run mean and "
                "pooled ratio reached through the census, which sums to "
                "node_calls_single_eval on every record",
                "the arrangement-method (prime) calls are not model nodes and "
                "are not in any row",
            ),
            how_to_read=(
                "read down a configuration's block rows to see where the "
                "partition's saving sits; a ratio near 1 on a block means the "
                "block is solved about as often as the flat arm sweeps it"
            ),
            summary=(
                f"Mean node calls per evaluation by block and arm, "
                f"configurations stacked, {tally_mod.source_phrase(source)}; "
                f"the ratio is A2 pooled against the configuration's reference "
                f"(the *reference* column: A1 pulsed, A0 on st). The "
                f"once-per-run row is the deferred nodes; prime calls are not "
                f"counted."
            ),
        ),
        columns=(
            Column("configuration", "configuration"),
            Column("block", "block"),
            Column("n_nodes", "nodes", fmt=_fmt_int),
            Column("nodes", "which"),
            *[
                Column(arm, arm, fmt=lambda v: "—" if v is None else f"{v:.1f}")
                for arm in LADDER
            ],
            Column("reference", "reference"),
            Column("ratio", "A2 / reference (pooled)", fmt=_fmt_ratio),
            Column("n_pairs", "pairs", fmt=_fmt_int),
        ),
        rows=tuple(rows),
        denominator=n_finished,
        denominator_is=(
            f"finished evaluation-phase {population.runs_word} of every "
            f"configuration in this source"
        ),
        acceptance=True,
        kind="node_calls_per_block",
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
                "the size of |y|/s on the components that made a pass "
                "decisive, or the absence of any such component, is stated per "
                "population in the caption",
            ),
            summary=(
                "The predicate trial, frozen against mixed: per pair of runs, "
                "the decisive passes as crossings and as verdict changes, "
                "bit-identity, and the exit audit on both rulers. "
                + (
                    "The decisive components carry |y|/s up to "
                    f"{max(ratios):g}."
                    if ratios
                    else "No component made a pass decisive."
                )
                + " From gate predicate_mode's verdict."
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
        kind="predicate_trial",
        detail=True,
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
    present = tally_mod.campaign_present(campaign)
    emitted: list[Table] = []
    verdicts: list[dict[str, Any]] = []
    refusals: list[str] = []
    sources: list[dict[str, Any]] = []
    for source in tally_mod.published_sources(campaign):
        if PHASE not in source.phases:
            continue
        rows, source_refusals = tally_mod.source_rows(campaign, source)
        refusals.extend(f"[{source.name}] {line}" for line in source_refusals)
        # Where each record lives in THIS tree, by job digest: the record's own
        # ``outdir`` names the tree the campaign ran in, and the exit states
        # the fixed-point distance reads sit beside the record, not in it.
        where = {
            str(row.record.get("job_digest")): Path(row.path).parent
            for row in rows
            if row.record.get("job_digest")
        }
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
            distance = fixed_point_distance(
                campaign, population, config.name, source.name, where
            )
            if distance is not None:
                emitted.append(distance)
            rung = ownership_rung(campaign, population, config.name, source.name)
            if rung is not None:
                emitted.append(rung)
            emitted.append(
                per_sweep_overhead(campaign, population, config.name, source.name)
            )
            emitted.append(
                failure_taxonomy(campaign, population, config.name, source.name)
            )
        stacked = node_calls_per_block(campaign, population, source.name)
        if stacked is not None:
            emitted.append(stacked)
    trial = predicate_trial(
        campaign, Path(campaign.runs_dir) / tally_mod.GATE_RUNS_SUBPATH
    )
    if trial is not None:
        emitted.append(trial)
    return {
        "phase": PHASE,
        "campaign_present": present,
        "population_family": "campaign" if present else "gate",
        "sources": sources,
        "sources_not_published": _not_published(campaign, PHASE),
        "population": "; ".join(f"{s['source']}: {s['n_records']} record(s)" for s in sources),
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
        "similarity_verdicts": verdicts,
        "tables": [table.as_record() for table in emitted],
        "n_tables": len(emitted),
    }


def _not_published(campaign: Campaign, phase: str) -> dict[str, Any]:
    """The sources of the other family, counted and named, with the reason."""
    return {
        "why": tally_mod.why_not_published(campaign),
        "sources": [
            {
                "source": source.name,
                "family": source.family,
                "n_records": len(tally_mod.source_rows(campaign, source)[0]),
            }
            for source in tally_mod.unpublished_sources(campaign)
            if phase in source.phases
        ],
    }


#: How many record-contract refusals are printed in full before the rest are
#: summarised.  Every one of them is in the stage's own JSON record; the
#: terminal shows enough to act on and says how many more there are, rather
#: than burying the tables under a hundred identical sentences.
REFUSALS_PRINTED = 5


def print_tally(block: Mapping[str, Any]) -> None:
    """The stage's tables on the terminal, each with its caption."""
    print(
        f"\n  population: the {block.get('population_family')} family "
        f"(campaign record present: {block.get('campaign_present')})"
    )
    for source in block.get("sources") or []:
        print(
            f"\n  source {source['source']:<28} {source['n_records']:>3} "
            f"record(s) of {source['owner']}'s job set, run kind(s) "
            f"{source.get('run_kinds')}"
        )
        print(f"    {source['what']}")
        if source.get("n_excluded_as_demonstrations"):
            print(
                f"    {source['n_excluded_as_demonstrations']} excluded as "
                f"budget-capped demonstrations"
            )
    unpublished = block.get("sources_not_published") or {}
    if unpublished.get("sources"):
        print(
            "\n  not published: "
            + ", ".join(
                f"{s['source']} ({s['n_records']} record(s))"
                for s in unpublished["sources"]
            )
            + f" — {unpublished.get('why')}"
        )
    campaign_outside = block.get("campaign_records_outside_every_source") or {}
    if campaign_outside.get("n_records_under_runs_campaign"):
        print(
            f"  {campaign_outside.get('n_in_a_campaign_source')} of "
            f"{campaign_outside.get('n_records_under_runs_campaign')} record(s) "
            f"under runs/campaign/ are in a campaign source; "
            f"{campaign_outside.get('n_outside_every_campaign_source')} are not"
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
