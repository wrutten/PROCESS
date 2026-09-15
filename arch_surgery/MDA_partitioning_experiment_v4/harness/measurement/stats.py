#!/usr/bin/env python
"""Every declared construction of the experiment, once, with its declaration.

The experiment plan declares how each published number is built — which median,
which population, what counts as an accepted optimum, how a ratio against the
reference is stated.  Those declarations lived in the previous revision as
comments beside the code that happened to need them, which is how two
implementations of one definition drifted apart twice (issues I-18 and I-19 of
the queue).  Here each is **one function**, and **its docstring is the
declaration**: a report caption quotes the docstring rather than paraphrasing
it, and the independent analysis (task A54) recomputes against these same
functions' *outputs*, never by importing a second copy of the rule.

Nothing in this module reads a file, starts a process or knows what a table
looks like.  It takes numbers and records and returns numbers.

Three things here are refusals rather than computations, because the experiment
plan states them as refusals:

:class:`Population`
    what a table is over.  A population **refuses** a record stamped
    ``force_maxcal`` — those are budget-capped demonstration runs, never
    measurements — and refuses to be built from records of more than one phase.

:func:`retried`
    whether a run retried is computed from ``attempts[]`` and from nothing
    else.  There is no stored "retried" flag to trust, and the one place a
    stored flag could have come from (``attempt_accounting.retried``) is a
    *derived* field of the same list, so trusting it would be trusting a copy.

:func:`attempt_summation`
    the identity ``Σ attempts == the run total``, computed and **printed**
    rather than assumed.  The record contract already refuses a record whose
    parts do not add up (``records.assert_attempt_summation``); this is the
    tally's own statement of the same identity, so the published with- and
    without-retried-seeds ratios are visibly over quantities that decompose the
    published one.

Heritage: the constructions are the V4 experiment plan's §3.4, §3.5 and §3.6
and the previous revision's ``phase_a.py`` / ``phase_b.py`` tallies, read at
``362c0b47``.  Written by task **A53 (harness-tally)**.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

__all__ = [
    "CAMPAIGN_PUBLISHED_RUN_KINDS",
    "measurable_run_kinds",
    "traceback_last_line",
    "crash_detail",
    "StatsError",
    "Population",
    "median",
    "p90",
    "seed_bracket",
    "accepted_optimum",
    "finished",
    "every_arm_converged",
    "configuration_invalid_seeds",
    "ACCEPTED_CLASS",
    "COUPLING_LOOP_CAP_CLASS",
    "outcome_class",
    "per_arm_success",
    "retried",
    "retried_seeds",
    "n_attempts",
    "attempt_summation",
    "iterations_final_attempt",
    "iterations_summed_over_attempts",
    "node_calls_by_attempt",
    "ratio_triple",
    "with_and_without_retried",
    "relative_objective_difference",
    "acceptance_threshold",
    "clusters",
    "hops",
    "below_cluster_resolution",
    "similarity",
    "failure_taxonomy",
    "restricted_statistic",
    "whole_state_statistic",
    "accuracy_population",
    "audit_position_of",
    "empty_visit_shares",
    "predicate_widths",
    "fixed_point_distance",
    "NODE_GROUP_ORDER",
    "ONCE_PER_RUN_GROUP",
    "node_groups",
    "per_node_census",
    "census_by_group",
    "module_sweeps",
    "dsm_rows_by_group",
    "weighted_total",
    "n_evaluations",
    "per_seed_ratio_summary",
    "iteration_variables",
    "point_difference",
    "namespace_residuals",
    "figure_of_merit",
]


class StatsError(RuntimeError):
    """A refused construction.  Never downgraded into a warning."""


# --------------------------------------------------------------------------
# what a table is over
# --------------------------------------------------------------------------


#: The stamp that says a record was made with the optimiser's evaluation budget
#: deliberately cut, to force the retry ladder to run more than one attempt.
#: Such a record demonstrates a *decomposition*; it is not a measurement of
#: anything, and the queue's A53 row requires it filtered out of every
#: population rather than left to a reader to notice.
FORCED_BUDGET_STAMP = "force_maxcal"

#: The run kinds a published table may be computed over.  ``campaign`` is the
#: experiment's own population; ``gate`` is what a verification gate made, and
#: is what every table in this package is over while ``EXECUTION_APPROVED`` is
#: False.  Each of those is a set somebody declared and can state in a caption.
#:
#: A ``smoke`` record is neither: it is one run of the campaign's own chain,
#: made to prove the chain runs end to end on one seed and one configuration,
#: and deliberately not a population.  Summarising one beside measurements
#: would print a median over a single run under the same caption as a median
#: over twenty-five — trap T11 with the denominator supplied.  So a record of
#: any kind not named here is **refused** at construction rather than filtered
#: out: a filter shrinks a population quietly, which is the error this project
#: has already made three times.
MEASURABLE_RUN_KINDS: tuple[str, ...] = ("campaign", "gate")

#: The run kinds a published table may be computed over **once a campaign
#: record exists**.  A gate record is a measurable kind only for want of a
#: campaign: the moment the campaign has run, a table over gate runs beside a
#: table over campaign runs is two populations under one caption vocabulary,
#: so :meth:`Population.of` refuses a gate record — by kind, at construction,
#: never by filter — when told the campaign is present (task A75
#: (campaign-tally-source), gate ``run_kind_separation``'s second direction).
CAMPAIGN_PUBLISHED_RUN_KINDS: tuple[str, ...] = ("campaign",)


def measurable_run_kinds(*, campaign_present: bool) -> tuple[str, ...]:
    """Which run kinds a published population may contain, given whether the
    campaign has run.  One rule, read by the population and by the gate."""
    return CAMPAIGN_PUBLISHED_RUN_KINDS if campaign_present else MEASURABLE_RUN_KINDS


@dataclass(frozen=True)
class Population:
    """The records a table is over, with the refusals that make it statable.

    **The declaration.** A population is a list of finished-or-not run records
    that share one phase, together with the denominator the table's counts are
    against.  It carries its own membership rule in :attr:`what`, because a
    count whose population cannot be stated in one clause is not ready to be
    published (trap T11).

    **Four refusals, all at construction:**

    * a record whose run kind is not one of :data:`MEASURABLE_RUN_KINDS` — a
      ``smoke`` record, one run of the campaign's chain made to prove the chain
      runs — is refused outright.  It is not excluded and counted, because
      unlike a budget-capped demonstration it is not a run of the population at
      all;
    * a record stamped ``force_maxcal`` — a budget-capped demonstration — is
      refused by name.  It is not dropped silently, because a population that
      quietly shrinks is the error this project has made three times;
    * a mixture of phases is refused, because the evaluation phase and the
      optimisation phase do not record the same quantities and a table over
      both is a table over a population nobody can state;
    * a population of no records at all is **allowed** but carries
      ``is_empty``, and every consumer must say so rather than publish a zero
      over nothing.  A gate over an empty set is the defect protocol §12 names;
      a *tally* over an empty set is a row that reads "0 / 0", which is
      honest as long as the denominator is printed beside it.
    """

    records: tuple[Mapping[str, Any], ...]
    what: str
    denominator: int
    phase: str
    #: Records excluded at construction, by reason, so the exclusion is a
    #: published number and not an invisible filter.
    excluded: tuple[tuple[str, str], ...] = ()

    @staticmethod
    def of(
        records: Sequence[Mapping[str, Any]],
        *,
        what: str,
        denominator: int | None = None,
        campaign_present: bool = False,
    ) -> "Population":
        """Build a population, refusing what may not be in one.

        ``denominator`` defaults to the number of records **asked for** — that
        is, the number offered here, demonstration runs included — because the
        denominator of a taxonomy is what was scheduled and not what survived.
        Pass it explicitly wherever the scheduled count is known independently
        (25 seeds per arm, say) and differs from the records on disk.

        ``campaign_present`` says whether a campaign record exists anywhere
        the tally reads (``tally.campaign_present``).  With it True the only
        kind a published population may hold is ``campaign``
        (:func:`measurable_run_kinds`): a gate record offered then is refused
        the way a smoke record always is, because the gate population was the
        tables' population *for want of a campaign* and a cell over it beside
        the campaign's cells would be a number without the condition that
        limits it (trap T11).
        """
        offered = list(records)
        kept: list[Mapping[str, Any]] = []
        excluded: list[tuple[str, str]] = []
        allowed = measurable_run_kinds(campaign_present=campaign_present)
        unsummarisable = [
            (_label(record), str(record.get("campaign_run_kind")))
            for record in offered
            if record.get("campaign_run_kind") is not None
            and record.get("campaign_run_kind") not in allowed
        ]
        if unsummarisable:
            raise StatsError(
                f"{len(unsummarisable)} record(s) of a run kind this table may "
                f"not be computed over reached a population: "
                f"{unsummarisable[:5]}.  The kinds a published table may "
                f"summarise are {list(allowed)}"
                + (
                    " while a campaign record exists — a gate record was the "
                    "tables' population for want of a campaign and is excluded "
                    "by kind now that one has run"
                    if campaign_present
                    else ""
                )
                + "; a 'smoke' record is one run of the campaign's own chain, "
                f"made to show the chain runs, and a table over it would carry "
                f"a caption naming a population it is not over."
            )
        for record in offered:
            if record.get(FORCED_BUDGET_STAMP) is not None:
                excluded.append(
                    (
                        _label(record),
                        f"stamped {FORCED_BUDGET_STAMP}="
                        f"{record.get(FORCED_BUDGET_STAMP)!r}: a budget-capped "
                        f"demonstration of the retry ladder, never a "
                        f"measurement",
                    )
                )
                continue
            kept.append(record)
        phases = {r.get("campaign_phase") for r in kept}
        phases.discard(None)
        if len(phases) > 1:
            raise StatsError(
                f"a population of {sorted(phases)} records: the evaluation "
                f"phase and the optimisation phase do not record the same "
                f"quantities, so a table over both is a table over a "
                f"population nobody can state.  Split them."
            )
        return Population(
            records=tuple(kept),
            what=what,
            denominator=len(offered) if denominator is None else int(denominator),
            phase=next(iter(phases)) if phases else "",
            excluded=tuple(excluded),
        )

    def assert_no_forced_budget(self) -> None:
        """Refuse rather than report, where a caller wants the harder rule.

        :meth:`of` *excludes* a demonstration record and says so.  A caller
        that must not have been handed one in the first place — the tally's own
        contract gate — calls this and gets a refusal instead.
        """
        if self.excluded:
            raise StatsError(
                f"{len(self.excluded)} record(s) stamped {FORCED_BUDGET_STAMP} "
                f"reached a population that refuses them: "
                f"{', '.join(name for name, _ in self.excluded)}.  A "
                f"budget-capped demonstration is not a measurement and may not "
                f"be summarised with measurements."
            )

    @property
    def is_empty(self) -> bool:
        return not self.records

    @property
    def run_kinds(self) -> tuple[str, ...]:
        """The run kinds of the kept records, sorted; what the caption names."""
        return tuple(sorted({str(r.get("campaign_run_kind")) for r in self.records}))

    @property
    def runs_word(self) -> str:
        """``campaign runs`` or ``gate runs`` — the population's kind, for a
        caption or a denominator sentence, read from the records and never
        assumed.  An empty population reads ``runs``."""
        kinds = self.run_kinds
        if len(kinds) == 1:
            return f"{kinds[0]} runs"
        return "runs" if not kinds else f"{'/'.join(kinds)} runs"

    def where(self, predicate) -> "Population":
        """The sub-population satisfying *predicate*, denominator preserved."""
        return Population(
            records=tuple(r for r in self.records if predicate(r)),
            what=self.what,
            denominator=self.denominator,
            phase=self.phase,
            excluded=self.excluded,
        )

    def by(self, key: str) -> dict[Any, "Population"]:
        """Split by a record field, each part keeping this population's rule."""
        out: dict[Any, list[Mapping[str, Any]]] = {}
        for record in self.records:
            out.setdefault(record.get(key), []).append(record)
        return {
            value: Population(
                records=tuple(rows),
                what=f"{self.what}, {key} = {value!r}",
                denominator=len(rows),
                phase=self.phase,
                excluded=(),
            )
            for value, rows in out.items()
        }

    def __len__(self) -> int:
        return len(self.records)


def _label(record: Mapping[str, Any]) -> str:
    """A record's identity in one string, for a message a reader can act on."""
    return (
        f"{record.get('campaign_arm', '?')}/"
        f"{record.get('campaign_configuration', '?')}/"
        f"seed{record.get('campaign_seed', '?')}"
    )


# --------------------------------------------------------------------------
# the quantile constructions
# --------------------------------------------------------------------------


def median(values: Sequence[float]) -> float | None:
    """**Nearest-rank, upper-middle**: the element at index ``n // 2`` of the
    sorted values.

    Declared once in the experiment plan §3.5 for *every* check of the
    optimisation phase, and used here for the evaluation phase too so that one
    word means one thing across the report.  It is deliberately not the mean of
    the two central order statistics: an interpolated median is not one of the
    measured values, and every acceptance quantity in this experiment is a
    measured one.  ``None`` over an empty sequence — never 0, which is a value.
    """
    ordered = sorted(values)
    if not ordered:
        return None
    return ordered[len(ordered) // 2]


def p90(values: Sequence[float]) -> float | None:
    """**Nearest-rank p90**: element ``ceil(0.9 n)`` of the sorted values,
    counting from 1.

    The same rule the previous revision declared, kept so its numbers remain
    comparable.  ``None`` over an empty sequence.
    """
    ordered = sorted(values)
    if not ordered:
        return None
    return ordered[max(0, math.ceil(0.9 * len(ordered)) - 1)]


def seed_bracket(values: Sequence[float]) -> list[float] | None:
    """``[min, max]`` over the seeds in the table's population.

    The bracket published beside every absolute per-run mean.  It is the
    observed range and not a confidence interval; the population it is over is
    the table's, stated in the caption.
    """
    ordered = sorted(values)
    if not ordered:
        return None
    return [ordered[0], ordered[-1]]


# --------------------------------------------------------------------------
# what counts as a result
# --------------------------------------------------------------------------


def finished(record: Mapping[str, Any]) -> bool:
    """The run completed and wrote a record: ``status == "ok"``.

    Weaker than :func:`accepted_optimum`, and never the population of an
    optimisation-phase check — an optimiser can finish without converging.
    """
    return record.get("status") == "ok"


def accepted_optimum(record: Mapping[str, Any]) -> bool:
    """**An accepted optimum**: ``status == "ok"`` *and* MFILE ``ifail == 1``.

    Two sources, deliberately: the harness's own word for how the run ended,
    and PROCESS's own output file, which is independent of the harness.  The
    previous revision measured why both are needed — a run can record a nonzero
    iteration count and an ``ifail`` of 5, and keeping the pair merely because
    an iteration count exists put an unconverged side into a ratio.
    """
    return finished(record) and (record.get("mfile") or {}).get("ifail") == 1.0


def every_arm_converged(
    by_arm: Mapping[str, Mapping[int, Mapping[str, Any]]],
    seeds: Sequence[int],
) -> list[int]:
    """**The one optimisation-phase seed set**: the seeds on which *every* arm
    reached an accepted optimum.

    One population per configuration for every optimisation-phase table (plan
    §3.5, decision (c)).  The seeds outside it are not dropped: they are the
    failure table, published beside, so an arm that fails on expensive seeds
    cannot be flattered by the filter.
    """
    return [
        seed
        for seed in seeds
        if all(
            accepted_optimum(by_arm.get(arm, {}).get(seed, {}))
            for arm in by_arm
        )
    ]


def configuration_invalid_seeds(
    by_arm: Mapping[str, Mapping[int, Mapping[str, Any]]],
    seeds: Sequence[int],
) -> list[int]:
    """Seeds on which **no** arm reached an accepted optimum.

    Configuration hardness, not an arm effect; counted separately so that a
    per-arm failure rate is not inflated by a start the problem itself rejects.
    """
    return [
        seed
        for seed in seeds
        if not any(
            accepted_optimum(by_arm.get(arm, {}).get(seed, {}))
            for arm in by_arm
        )
    ]


#: The outcome class of a start that reached an accepted optimum.
ACCEPTED_CLASS = "accepted"

#: The outcome class of a start the coupling-state loop refused at its sweep
#: cap (``ModuleSolveFailure``; the harness's failure class ``unconverged``).
#: The harness stamps such a run ``crashed`` like a run PROCESS's own code
#: raised in, and the taxonomy tables split them; this construction splits
#: them the same way and names the split.
COUPLING_LOOP_CAP_CLASS = "coupling-loop cap (ModuleSolveFailure)"


def _exception_name(record: Mapping[str, Any]) -> str:
    """The exception a crashed run raised, by its class name, from the
    traceback's last line (``pkg.mod.Name: message`` → ``Name``)."""
    line = traceback_last_line(record)
    if not line:
        return "no traceback"
    head = line.split(":", 1)[0].strip()
    return head.rsplit(".", 1)[-1] or "no traceback"


def outcome_class(record: Mapping[str, Any]) -> str:
    """**The outcome class of one start** — one label per record, from the
    same two sources :func:`accepted_optimum` reads plus the harness's failure
    class:

    * ``accepted`` — :func:`accepted_optimum` (``status == "ok"`` and MFILE
      ``ifail == 1``);
    * ``finished, ifail = k`` — the run finished (``status == "ok"``) and the
      optimiser's exit code was ``k != 1`` (``ifail = 5``: VMCON's retry ladder
      exhausted); a finished start that is not an accepted optimum;
    * ``crashed (<Exception>)`` — the harness's failure class ``crashed``:
      PROCESS's own code raised, the exception named from the traceback's last
      line (``RuntimeError`` for the model-internal Newton solve's
      ``Failed to converge after 50 iterations, value is nan``);
    * :data:`COUPLING_LOOP_CAP_CLASS` — the harness's failure class
      ``unconverged``: the coupling-state loop refused at its sweep cap
      (``ModuleSolveFailure``), which the harness also stamps ``crashed``;
    * any other failure class by its own name (``timeout``, ``machinery``,
      ``refused``, ``unconverged-at-cap``), none of which occurred in the
      campaign.

    The classes partition the starts: every record has exactly one.
    """
    if accepted_optimum(record):
        return ACCEPTED_CLASS
    if finished(record):
        ifail = (record.get("mfile") or {}).get("ifail")
        shown = int(ifail) if isinstance(ifail, float) and ifail == int(ifail) else ifail
        return f"finished, ifail = {shown}"
    failure_class = str(record.get("failure_class") or "unknown")
    if failure_class == "crashed":
        return f"crashed ({_exception_name(record)})"
    if failure_class == "unconverged":
        return COUPLING_LOOP_CAP_CLASS
    return failure_class


def _class_rank(label: str) -> tuple[int, str]:
    """The order the outcome classes print in: accepted, finished by exit
    code, crashed by exception, the coupling-loop cap, anything else."""
    if label == ACCEPTED_CLASS:
        return (0, label)
    if label.startswith("finished, ifail = "):
        return (1, label)
    if label.startswith("crashed ("):
        return (2, label)
    if label == COUPLING_LOOP_CAP_CLASS:
        return (3, label)
    return (4, label)


def per_arm_success(
    by_arm: Mapping[str, Mapping[int, Mapping[str, Any]]],
    seeds: Sequence[int],
) -> dict[str, Any]:
    """**Per-arm success** — reliability stated per arm over the starts
    offered, beside the seed-set filter every cost table applies.

    Per arm: the starts **offered** (the seeds at which the arm has a record),
    the **accepted optima** (:func:`accepted_optimum`: ``status == "ok"`` and
    MFILE ``ifail == 1``), every other start by its :func:`outcome_class`
    with its count and its seeds named, and the starts **lost that another
    arm accepted** — the seeds on which this arm did not reach an accepted
    optimum while at least one other arm of the group did (the asymmetric
    failures; a seed no arm accepted is configuration hardness, counted in
    :func:`configuration_invalid_seeds`, and is not one).  Beside them the
    **seed set** (:func:`every_arm_converged`).  Per seed: each arm's class,
    how many arms accepted, whether the seed is in the set and which arms
    lost it.

    The rate is ``accepted / offered`` with the denominator printed, never a
    percentage alone (trap T11).  **Reported, not accepted on**: no
    pre-declared rule of the plan reads it; the experiment's cost cells stay
    over the seed set and this construction says what that filter leaves out
    (decision D29, 2026-09-15, on A81 (benchmarking-practices)'s finding F1).
    Written by task **A82 (per-arm-success)**.
    """
    order = list(by_arm)
    labels_by_seed: dict[int, dict[str, str]] = {
        seed: {
            arm: outcome_class(by_arm[arm][seed])
            for arm in order
            if seed in by_arm[arm]
        }
        for seed in seeds
    }
    accepted_arms: dict[int, list[str]] = {
        seed: [arm for arm, label in labels.items() if label == ACCEPTED_CLASS]
        for seed, labels in labels_by_seed.items()
    }
    seed_set = every_arm_converged(by_arm, seeds)
    classes = sorted(
        {
            label
            for labels in labels_by_seed.values()
            for label in labels.values()
            if label != ACCEPTED_CLASS
        },
        key=_class_rank,
    )
    arms: dict[str, dict[str, Any]] = {}
    for arm in order:
        offered = sorted(s for s in seeds if s in by_arm[arm])
        seeds_by_class: dict[str, list[int]] = {label: [] for label in classes}
        accepted: list[int] = []
        for seed in offered:
            label = labels_by_seed[seed][arm]
            if label == ACCEPTED_CLASS:
                accepted.append(seed)
            else:
                seeds_by_class[label].append(seed)
        lost = [
            seed
            for seed in offered
            if labels_by_seed[seed][arm] != ACCEPTED_CLASS
            and accepted_arms[seed]
        ]
        arms[arm] = {
            "offered": len(offered),
            "accepted": len(accepted),
            "accepted_seeds": accepted,
            "by_class": {label: len(seeds_by_class[label]) for label in classes},
            "seeds_by_class": seeds_by_class,
            "lost_another_arm_accepted": lost,
        }
    per_seed = [
        {
            "seed": seed,
            "classes": labels_by_seed[seed],
            "n_accepted": len(accepted_arms[seed]),
            "in_seed_set": seed in set(seed_set),
            "lost_by": [
                arm
                for arm in order
                if arm in labels_by_seed[seed]
                and labels_by_seed[seed][arm] != ACCEPTED_CLASS
                and accepted_arms[seed]
            ],
        }
        for seed in seeds
    ]
    return {
        "classes": classes,
        "arms": arms,
        "seed_set": seed_set,
        "per_seed": per_seed,
    }


# --------------------------------------------------------------------------
# the retry ladder
# --------------------------------------------------------------------------


def n_attempts(record: Mapping[str, Any]) -> int:
    """How many times the optimiser was called on this start.

    Read from ``attempts[]``, the per-attempt list the driver stamps at every
    boundary of its retry ladder.  An evaluation-phase record has none and
    reads 0.
    """
    attempts = record.get("attempts")
    return len(attempts) if isinstance(attempts, list) else 0


def retried(record: Mapping[str, Any]) -> bool:
    """**A retried seed**: the optimiser was called more than once on it.

    Computed from ``attempts[]`` and from nothing else.  There is a derived
    ``attempt_accounting.retried`` in the record and it is *not* consulted: it
    is a copy of this same count, and a tally that reads a stored flag cannot
    tell a driver that stopped stamping attempts from a run that did not retry.
    The experiment plan publishes every cost ratio with and without these
    seeds, so which seeds they are is load-bearing.
    """
    return n_attempts(record) > 1


def retried_seeds(rows: Mapping[int, Mapping[str, Any]]) -> list[int]:
    """The seeds of *rows* whose run retried, in order."""
    return sorted(seed for seed, record in rows.items() if retried(record))


def node_calls_by_attempt(record: Mapping[str, Any]) -> list[int | None]:
    """Solve-phase model executions of each attempt, in order.

    The cost half of the per-attempt accounting (driver change DR7).  The
    with- and without-retried-seeds ratios of the plan's §3.5 are built from
    these, never from the run total alone: a retry's evaluations are in the run
    total while its iterations are not in check 2, and pooling them into a cost
    ratio without saying so is what made the previous revision's headline on
    one configuration unreadable.
    """
    return [a.get("node_calls_solve_phase") for a in (record.get("attempts") or [])]


def attempt_summation(record: Mapping[str, Any]) -> dict[str, Any]:
    """**The summation identity**: Σ over attempts == the run's solve-phase
    total, for node calls and for sweeps, with its residual.

    Computed here and **printed** by every stage that publishes a
    with/without-retried ratio.  The record contract already refuses a record
    whose parts do not add up (``records.assert_attempt_summation``); this
    states the same identity as a number the reader can see, so that "the parts
    decompose the whole" is a measurement in the report rather than a property
    of code nobody ran.

    ``applicable`` is False for an evaluation-phase record, which has no
    optimiser and therefore nothing to decompose, and for a record whose
    attempts carry no cost at all.
    """
    attempts = record.get("attempts")
    if not isinstance(attempts, list) or not attempts:
        return {
            "applicable": False,
            "why": "no attempts: this phase runs no optimiser, or the run "
            "stopped before the driver stamped one",
        }
    out: dict[str, Any] = {"applicable": True, "n_attempts": len(attempts)}
    parts: dict[str, Any] = {}
    for per_attempt_field, total_field in (
        ("node_calls_solve_phase", "node_calls_solve_phase"),
        ("sweeps", "dispatch_sweeps_solve_phase"),
    ):
        values = [a.get(per_attempt_field) for a in attempts]
        total = record.get(total_field)
        if any(v is None for v in values) or total is None:
            parts[per_attempt_field] = {
                "checked": False,
                "why": "the driver stamped no cost at an attempt boundary of "
                "this run",
            }
            continue
        summed = sum(int(v) for v in values)
        parts[per_attempt_field] = {
            "checked": True,
            "per_attempt": [int(v) for v in values],
            "summed": summed,
            "run_total_field": total_field,
            "run_total": int(total),
            "residual": int(total) - summed,
            "decomposes": int(total) == summed,
        }
    out["parts"] = parts
    checked = [p for p in parts.values() if p.get("checked")]
    out["decomposes"] = bool(checked) and all(p["decomposes"] for p in checked)
    out["n_checked"] = len(checked)
    return out


def iterations_final_attempt(record: Mapping[str, Any]) -> int | None:
    """**Check 2, construction one**: the optimiser's iterations on its **final
    attempt**.

    The previous revision's construction, kept so its numbers stay comparable,
    and published beside the summed one — never instead of it.  Taken from the
    last element of ``attempts[]`` rather than from the run's own
    ``n_solver_iterations``, so that both constructions come from the same
    list and a disagreement between them is a disagreement about the list and
    not about which field was read.
    """
    attempts = record.get("attempts") or []
    if not attempts:
        return None
    return attempts[-1].get("n_iterations")


def iterations_summed_over_attempts(record: Mapping[str, Any]) -> int | None:
    """**Check 2, construction two**: iterations **summed over every attempt**,
    failed attempts included.

    The declared acceptance statistic of check 2 (plan §3.5, amended
    2026-09-10): the trajectory the check controls is the whole optimiser path,
    and a failed attempt is part of it.  ``None`` where any attempt carries no
    iteration count, because a partial sum is not a sum.
    """
    attempts = record.get("attempts") or []
    if not attempts:
        return None
    values = [a.get("n_iterations") for a in attempts]
    if any(v is None for v in values):
        return None
    return sum(int(v) for v in values)


# --------------------------------------------------------------------------
# ratios
# --------------------------------------------------------------------------


def ratio_triple(
    reference: Sequence[float], arm: Sequence[float]
) -> dict[str, Any]:
    """**The ratio against the reference, three ways** (plan §4, conventions).

    * **pooled** — sum over the set / sum over the set: the campaign's cost;
    * **per-run median** with ``[min, max]``: the typical run;
    * **worse** — the count of seeds on which the arm cost *more* than the
      reference.

    The three are published together because they can disagree in direction: a
    median far from the pooled value means a few seeds carry the campaign's
    cost, and a reader who sees only one of the three cannot tell.  The two
    sequences are **paired**: element *i* of each is the same seed, and a
    caller that pairs them wrongly gets a ratio over a population nobody can
    state, which is why the lengths must match.
    """
    if len(reference) != len(arm):
        raise StatsError(
            f"a paired ratio over {len(reference)} reference values and "
            f"{len(arm)} arm values: the two sides are not the same seeds, so "
            f"the pairing is wrong and the ratio would be over a population "
            f"nobody can state"
        )
    per_run = [
        (b / a) for a, b in zip(reference, arm) if a not in (0, None) and b is not None
    ]
    total_reference = sum(reference) if reference else 0
    return {
        "n": len(reference),
        "pooled": (sum(arm) / total_reference) if total_reference else None,
        "median": median(per_run),
        "bracket": seed_bracket(per_run),
        "worse": sum(1 for a, b in zip(reference, arm) if b > a),
        "construction": (
            "pooled = Σ arm / Σ reference over the seed set; median = "
            "nearest-rank upper-middle of the per-seed ratios; worse = seeds "
            "on which the arm cost more"
        ),
    }


def with_and_without_retried(
    reference: Mapping[int, Mapping[str, Any]],
    arm: Mapping[int, Mapping[str, Any]],
    seeds: Sequence[int],
) -> dict[str, Any]:
    """**The cost ratio with and without the retried seeds, side by side**
    (plan §3.5, "retries are a term, not a footnote").

    Both readings are defensible and both are published: a retry the other arm
    did not need is real cost the architecture avoided at that start, *and* it
    is a robustness event rather than a per-evaluation cost.  The ratio is
    built from ``attempts[].node_calls_solve_phase`` — summed over the attempts
    — rather than from the run total, so that the quantity the ratio is over is
    visibly the one the attempts decompose; :func:`attempt_summation` states
    that identity and every caller prints it.

    A seed is retried if **either** side retried: the pair is what the ratio is
    over, and dropping a seed from one side only would compare two different
    populations.
    """
    both = [s for s in seeds if s in reference and s in arm]
    retried_here = sorted(
        s for s in both if retried(reference[s]) or retried(arm[s])
    )
    quiet = [s for s in both if s not in set(retried_here)]

    def summed(record: Mapping[str, Any]) -> float | None:
        values = node_calls_by_attempt(record)
        if not values or any(v is None for v in values):
            return None
        return float(sum(int(v) for v in values))

    def triple(seed_set: Sequence[int]) -> dict[str, Any]:
        pairs = [
            (summed(reference[s]), summed(arm[s]))
            for s in seed_set
        ]
        pairs = [(a, b) for a, b in pairs if a is not None and b is not None]
        if not pairs:
            return {"n": 0, "pooled": None, "median": None, "bracket": None,
                    "worse": 0, "construction": "no seed carried per-attempt "
                    "node calls on both sides"}
        return ratio_triple([a for a, _ in pairs], [b for _, b in pairs])

    return {
        "seeds": list(both),
        "retried_seeds": retried_here,
        "n_retried": len(retried_here),
        "with_retried": triple(both),
        "without_retried": triple(quiet),
        "construction": (
            "solve-phase node calls summed over attempts[] per run; a seed is "
            "retried when either side of the pair ran more than one attempt"
        ),
    }


def relative_objective_difference(a: float, b: float) -> float:
    """**Check 1's statistic**: ``|Δ norm_objf| / max(|a|, |b|)``.

    Per pair, relative, with the larger magnitude of the two sides as the
    denominator — the same form the cluster gap uses.  An *absolute* delta
    compared against a relative floor is a different construction, and the
    plan is authoritative: the absolute difference is published beside, never
    accepted against.
    """
    denominator = max(abs(a), abs(b))
    return abs(b - a) / denominator if denominator else 0.0


def acceptance_threshold(
    yardstick: float | None, *, factor: float, floor: float
) -> float | None:
    """**Check 1's acceptance rule**: ``max(F × yardstick, floor)``.

    The yardstick is the reference-to-flat-control spread measured **inside the
    same campaign**, so the threshold is calibrated on the problem rather than
    chosen; the floor is the correctness tolerance below which two optima are
    the same optimum by decision.
    """
    if yardstick is None:
        return None
    return max(factor * yardstick, floor)


def clusters(values: Sequence[float], *, gap: float) -> list[list[int]]:
    """**Check 1a's clustering**: indices grouped by sorted objective, split
    wherever the **relative** gap between adjacent sorted values exceeds *gap*.

    The gap is relative to the larger magnitude of the adjacent pair.  Two
    optima in one cluster are the same attractor for the purpose of the hop
    rate; two in different clusters are different attractors.
    """
    if not values:
        return []
    order = sorted(range(len(values)), key=lambda i: values[i])
    groups: list[list[int]] = [[order[0]]]
    for index in order[1:]:
        previous = values[groups[-1][-1]]
        current = values[index]
        denominator = max(abs(previous), abs(current))
        relative = (abs(current - previous) / denominator) if denominator else 0.0
        if relative > gap:
            groups.append([index])
        else:
            groups[-1].append(index)
    return groups


def hops(
    cluster_of: Mapping[Any, int], pairs: Sequence[tuple[Any, Any]]
) -> dict[str, Any]:
    """**The hop rate**: pairs whose two sides land in different clusters.

    Reported per arm pair with the reference-to-flat-control pair's own rate as
    the comparator, because an optimiser that lands in a different attractor
    from a different start is a property of the problem before it is a property
    of the architecture.
    """
    both = [(a, b) for a, b in pairs if a in cluster_of and b in cluster_of]
    hopped = [(a, b) for a, b in both if cluster_of[a] != cluster_of[b]]
    return {
        "n_pairs": len(both),
        "n_hops": len(hopped),
        "rate": (len(hopped) / len(both)) if both else None,
    }


def below_cluster_resolution(
    relatives: Sequence[float], *, floor: float, gap: float
) -> dict[str, Any]:
    """**Check 1b's named category**: pairs closer than the cluster gap but
    further apart than the correctness floor.

    ``floor < r < gap``.  These are *distinct optima below cluster resolution*
    — a named category with its own count, declared in advance so that a pair
    the clustering cannot separate is not silently read as "the same optimum".
    The smallest observed inter-optimum gap is published beside it so a reader
    can see whether a configuration's optima are denser than the gap resolves.
    """
    inside = [r for r in relatives if floor < r < gap]
    return {
        "n": len(inside),
        "n_pairs": len(relatives),
        "floor": floor,
        "cluster_gap": gap,
        "smallest_nonzero_relative": min(
            (r for r in relatives if r > 0), default=None
        ),
        "what": (
            "pairs whose optima differ by more than the correctness floor and "
            "less than the cluster gap: distinct optima below cluster "
            "resolution"
        ),
    }


def similarity(
    a: float | None, b: float | None, *, factor: float
) -> dict[str, Any]:
    """**The similarity verdict at factor F**, with the plan's zero clause.

    Two distributions are similar when ``max/min ≤ F``.  Both exactly zero is
    *trivially similar* and the report says so; one zero and the other not is
    an unbounded ratio and is not similar.  A missing distribution is neither:
    it is a refusal to judge, and the caller publishes the absence.
    """
    if a is None or b is None:
        return {"similar": None, "why": "a distribution is empty", "ratio": None}
    if a == 0 and b == 0:
        return {
            "similar": True,
            "why": "both exactly zero: trivially similar",
            "ratio": None,
        }
    if a == 0 or b == 0:
        return {
            "similar": False,
            "why": "one side exactly zero, the other not: the ratio is unbounded",
            "ratio": None,
        }
    ratio = max(a, b) / min(a, b)
    return {
        "similar": bool(ratio <= factor),
        "why": f"ratio {ratio:.4g} against F = {factor:g}",
        "ratio": ratio,
    }


# --------------------------------------------------------------------------
# the taxonomy
# --------------------------------------------------------------------------


def failure_taxonomy(
    records: Iterable[Mapping[str, Any]], *, denominator: int
) -> dict[str, Any]:
    """**The failure taxonomy with its denominator**: one row per disposition,
    the rows summing to the number of runs **scheduled**.

    Every scheduled run is a row.  A run that wrote no record is ``no_record``
    and is counted, not skipped: a whole class of failures once left a tally
    silently because an absent file raised instead of counting.
    """
    counts: dict[str, int] = {}
    seen = 0
    for record in records:
        seen += 1
        row = record.get("failure_class") or "unknown"
        counts[row] = counts.get(row, 0) + 1
    if seen < denominator:
        counts["no_record"] = counts.get("no_record", 0) + (denominator - seen)
    return {
        "denominator": denominator,
        "by_failure_class": dict(sorted(counts.items())),
        "rows_sum_to_denominator": sum(counts.values()) == denominator,
    }


def traceback_last_line(record: Mapping[str, Any]) -> str | None:
    """The last non-empty line of an unfinished record's traceback, or None.

    The class detail the taxonomy carries beside its counts: ``crashed`` says
    the run raised, the last line says what — and two arms crashing on the
    same seed with the same line is a different finding from two different
    lines.  A finished record has no traceback and reads None.
    """
    if record.get("status") == "ok":
        return None
    text = record.get("traceback")
    if not isinstance(text, str):
        return None
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    return lines[-1] if lines else None


def crash_detail(records: Iterable[Mapping[str, Any]]) -> str:
    """The distinct traceback last lines among *records*, each with its count,
    most frequent first, joined with ``; `` — or ``—`` where no run crashed."""
    counts: dict[str, int] = {}
    for record in records:
        line = traceback_last_line(record)
        if line is None:
            continue
        counts[line] = counts.get(line, 0) + 1
    if not counts:
        return "—"
    return "; ".join(
        f"{line} ×{n}" for line, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    )


# --------------------------------------------------------------------------
# the exit audit
# --------------------------------------------------------------------------


def audit_position_of(record: Mapping[str, Any]) -> str | None:
    """Where this run's exit audit was taken.

    ``entry_to_write_output_files`` on a campaign-shaped optimisation record —
    the state the solve handed over — and ``after_run`` on the reproduction
    gate's, where the previous revision measured.  Two residuals taken at
    different positions are two different quantities, and every caption that
    carries one states which.
    """
    return record.get("audit_position")


#: Fields that identify **which exit-audit instrument** produced a record's
#: residuals.  They are read through :func:`audit_instrument` and nowhere else,
#: so that a change to the instrument lands in one place.  The live case: task
#: **A62 (exit-audit-restore)** changes the snapshot to restore the whole data
#: structure (decision D25), which moves ``exit_audit.*`` on every record and
#: adds fields naming what was restored.  A caption must state the instrument
#: version **read from the record**, never assumed from the date — the same
#: table shape will carry two different instruments' numbers across that merge.
AUDIT_INSTRUMENT_FIELDS: tuple[str, ...] = (
    "positions_offered",
    "positions_taken",
    "positions_snapshotted",
    "n_components",
    "n_restored",
    "n_not_restorable",
    "not_restorable",
    "installed",
)


def audit_instrument(record: Mapping[str, Any]) -> dict[str, Any]:
    """**Which exit-audit instrument produced this record's residuals.**

    One accessor, because the instrument is changing: the snapshot the audit
    restores from is being widened from the coupling state to the whole data
    structure (decision D25, task A62 (exit-audit-restore)), and every residual
    in every table moves when it lands.  A caption that says *which* instrument
    a number came from stays true across that merge; a caption that describes
    the instrument in prose does not.

    Returns whatever of :data:`AUDIT_INSTRUMENT_FIELDS` the record carries, a
    one-line ``version`` string built from them, and the audit position.
    Fields the record does not carry are simply absent: this reads a record, it
    does not assert what a record should contain.
    """
    snapshot = record.get("audit_snapshot")
    present: dict[str, Any] = {}
    if isinstance(snapshot, Mapping):
        for name in AUDIT_INSTRUMENT_FIELDS:
            if name in snapshot:
                present[name] = snapshot[name]
    version_parts: list[str] = []
    taken = present.get("positions_snapshotted") or present.get("positions_taken")
    if taken:
        version_parts.append(f"snapshot at {','.join(sorted(map(str, taken)))}")
    if present.get("n_restored") is not None:
        version_parts.append(f"{present['n_restored']} restored")
    if present.get("n_not_restorable") is not None:
        version_parts.append(f"{present['n_not_restorable']} not restorable")
    if not version_parts:
        version_parts.append(
            "no snapshot recorded on this record"
            if snapshot is None
            else "snapshot recorded with no position taken"
        )
    return {
        "position": audit_position_of(record),
        "fields": present,
        "version": "; ".join(version_parts),
    }


def restricted_statistic(
    record: Mapping[str, Any], *, ruler: str
) -> dict[str, Any]:
    """**The restricted audit maximum on one named ruler, with its argmax.**

    The declared accuracy statistic of the evaluation phase (plan §3.4 check
    1): the largest scaled coupling-state residual over the components **not
    owned** by the configuration's once-per-run deferred nodes.  The
    **argmax is part of the statistic**, not a diagnostic: the maximum is one
    component's residual, and a table that averages it over runs is reporting a
    number no run produced.

    ``n_excluded`` is the count of components the restriction removed **on this
    ruler**.  The two rulers' counts are never pooled, and a record whose
    restricted block is null carries no count at all — reported as ``None``,
    never as 0.
    """
    audit = record.get("exit_audit") or {}
    block = audit.get(ruler)
    if not isinstance(block, Mapping):
        return {
            "ruler": ruler,
            "present": False,
            "why": f"the record's exit audit carries no {ruler!r} block",
        }
    restricted = block.get("restricted")
    if not isinstance(restricted, Mapping):
        return {
            "ruler": ruler,
            "present": False,
            "why": (
                "the audit was taken without a once-per-run deferral artifact, "
                "so there is no restricted statistic on this record"
            ),
            "n_excluded": None,
            "whole_state_max": block.get("residual_max"),
        }
    return {
        "ruler": ruler,
        "present": True,
        "max": restricted.get("max"),
        "max_hex": restricted.get("max_hex"),
        "argmax": restricted.get("argmax"),
        "n_above_tau": restricted.get("n_above"),
        "n_excluded": block.get("n_excluded_from_the_restricted_statistic"),
        "n_kept": restricted.get("n_kept"),
        "tau": restricted.get("tau"),
    }


def accuracy_population(
    records: Sequence[Mapping[str, Any]], *, ruler: str
) -> dict[str, Any]:
    """**The n of an accuracy table's row, declared once: the runs it is over.**

    Both accuracy tables — the evaluation phase's *matched accuracy* and the
    optimisation phase's *achieved accuracy* — print a column headed ``n``, and
    until task **A54 (harness-analysis)** found it they built it two different
    ways: one counted the finished **runs**, the other counted the **values**
    that had a restricted statistic.  Over the gate records the two coincide,
    so nothing disagreed and nobody could see it; that is the exact shape of
    issues I-18 and I-19.

    **The declaration, one reading: ``n`` counts the runs.**  A row of these
    tables is one arm on one ruler over a set of runs, and the denominator of a
    median must be the set the row names.  A run whose exit audit carries no
    restricted block is therefore **counted in n** and named in the column
    beside it, which reads the smaller number with the reason — never dropped
    from n, because a denominator that quietly shrinks to the values that
    happened to exist is this project's trap T11.

    Returns the run count, the restricted statistic of each run in order, the
    values that exist, how many of them there are, and the distinct reasons the
    rest carry none.
    """
    statistics = [restricted_statistic(record, ruler=ruler) for record in records]
    values = [
        statistic["max"]
        for statistic in statistics
        if statistic.get("present") and statistic.get("max") is not None
    ]
    without = [
        {
            "run": _label(record),
            "why": statistic.get("why")
            or "the record's restricted statistic is null",
        }
        for record, statistic in zip(records, statistics)
        if not (statistic.get("present") and statistic.get("max") is not None)
    ]
    return {
        "n": len(records),
        "n_is": (
            "the runs this row is over; a run whose audit carries no "
            "restricted block is counted here and shows in the column beside "
            "as one that carried no statistic"
        ),
        "statistics": statistics,
        "values": values,
        "n_with_the_statistic": len(values),
        "without": without,
        "reasons": sorted({row["why"] for row in without}),
    }


def whole_state_statistic(
    record: Mapping[str, Any], *, ruler: str
) -> dict[str, Any]:
    """The exit-audit maximum over **all** components on one named ruler.

    Published beside the restricted statistic to show the exclusion's size, and
    never judged on its own: the once-per-run deferred nodes' outputs are stale
    at the audit by design, so a partitioned arm's whole-state maximum is large
    for a reason the design chose.
    """
    audit = record.get("exit_audit") or {}
    block = audit.get(ruler)
    if not isinstance(block, Mapping):
        return {"ruler": ruler, "present": False}
    brief = block.get("brief") or {}
    return {
        "ruler": ruler,
        "present": True,
        "max": block.get("residual_max"),
        "max_hex": block.get("residual_max_hex"),
        "argmax": brief.get("argmax"),
        "n_above_tau": brief.get("n_above"),
    }


# --------------------------------------------------------------------------
# the per-sweep overhead (plan §3.5 check 5)
# --------------------------------------------------------------------------


def empty_visit_shares(record: Mapping[str, Any]) -> dict[str, Any]:
    """**The empty-visit disclaimer's two shares, with the one that may be
    quoted named.**

    A block whose members are all skipped at the call site is still visited and
    still costs a full walk of the model sequence.  Those visits are counted
    and disclaimed, never repaired (the user's ruling), and every table that
    weights sweeps must say so.

    Two shares exist and they are **not interchangeable**.  The *visit* share
    is the fraction of block visits that executed nothing; the *sweep* share is
    the fraction of the run's dispatch sweeps those visits actually cost.  The
    disclaimer quotes the **sweep share**: the visit share overstates the cost,
    because a block visited with no members costs no sweep at all.  This
    function returns both and marks which one a caption may quote, so that the
    wrong one cannot be picked up by accident.
    """
    visits = record.get("block_visits") or {}
    empty = record.get("empty_block_visits") or {}
    empty_sweeps = record.get("empty_block_sweeps") or {}
    dispatch = record.get("dispatch_sweeps")
    n_visits = sum(visits.values()) if visits else 0
    n_empty = sum(empty.values()) if empty else 0
    n_empty_sweeps = sum(empty_sweeps.values()) if empty_sweeps else 0
    return {
        "n_block_visits": n_visits,
        "n_empty_block_visits": n_empty,
        "visit_share": (n_empty / n_visits) if n_visits else None,
        "visit_share_may_be_quoted": False,
        "n_empty_block_sweeps": n_empty_sweeps,
        "dispatch_sweeps": dispatch,
        "sweep_share": (n_empty_sweeps / dispatch) if dispatch else None,
        "sweep_share_may_be_quoted": True,
        "empty_blocks": sorted(k for k, v in (empty or {}).items() if v),
        "disclaimer": (
            "the empty block visits are counted and disclaimed, never "
            "repaired: dropping a block whose members are skipped at the call "
            "site would change the node weights the comparison rests on.  The "
            "share quoted is the SWEEP share — the fraction of the run's "
            "dispatch sweeps those visits cost — never the visit share, which "
            "overstates it"
        ),
    }


#: The two convergence tests this experiment counts, by the name the record
#: gives each.  They are **never pooled into one column**: an arm stops on
#: exactly one of them, they are not the same test, and their widths differ by
#: nearly two orders of magnitude — the objective/constraint test compares tens
#: of values, the coupling-state test compares hundreds.  Adding the two counts
#: would produce a column whose value belongs to no test.
PREDICATES: dict[str, str] = {
    "coupling_state": (
        "the coupling-state test: every component of the block's own write "
        "set, or of the whole coupling state where the block has none"
    ),
    "upstream": (
        "upstream's own stopping test: the objective, and the constraint "
        "vector when the objective agreed.  The pair short-circuits, so the "
        "width counted is the width compared"
    ),
}


def predicate_widths(record: Mapping[str, Any]) -> dict[str, Any]:
    """**The two predicates' counts, split, with the width of each.**

    Returns one block per predicate of :data:`PREDICATES` and **no total**.
    There is deliberately no summed field to reach for: a pooled
    predicate-evaluation count is a number that belongs to neither test, and
    the tally's table module refuses a column that carries one.
    """
    counters = record.get("predicate_counters") or {}
    coupling = counters.get("coupling_state_predicate") or {}
    upstream = counters.get("upstream_predicate") or {}
    return {
        "coupling_state": {
            "evaluations": record.get("predicate_evaluations"),
            "components_compared": record.get("components_compared"),
            "mean_test_width": coupling.get("mean_test_width"),
            "by_block": coupling.get("mean_test_width_by_block") or {},
            "what": PREDICATES["coupling_state"],
        },
        "upstream": {
            "evaluations": record.get("upstream_predicate_evaluations"),
            "components_compared": record.get("upstream_components_compared"),
            "mean_test_width": upstream.get("mean_test_width"),
            "what": PREDICATES["upstream"],
        },
        "stops_on": (
            "coupling_state"
            if record.get("predicate_evaluations")
            else (
                "upstream"
                if record.get("upstream_predicate_evaluations")
                else None
            )
        ),
        "never_pooled": (
            "the two counts are published in separate columns; their sum is "
            "not a quantity of any test"
        ),
    }


# --------------------------------------------------------------------------
# the distance between two arms' fixed points
# --------------------------------------------------------------------------


def fixed_point_distance(
    pairs: Sequence[Mapping[str, Any]], *, tau: float
) -> dict[str, Any]:
    """**The distance between two arms' exit states at the same entry**, over
    the pairs of one arm against the reference arm.

    The exit audit measures how far each arm's exit state is from *a* fixed
    point — one further sweep, taken per run.  It does not say whether two
    arms reached the *same* point, and the experiment assumes they do: the
    partitioned arrangement is meant to reach the flat arrangement's fixed
    point at lower cost, not a different one.  This statistic is that
    comparison, taken from the exit states the runs wrote (``y_exit.json``)
    and nothing else — no model runs.

    **Per pair** (one entry, two arms): the predicate's own scaled residual
    evaluated between the two exit states instead of between two successive
    sweeps — ``max_i |y_arm,i − y_base,i| / s_i`` over the continuous
    components, ``s_i`` the committed scale (the **frozen** ruler, the one τ is
    stated on) — **restricted** to the components not written by the
    configuration's once-per-run deferred nodes, exactly the restriction the
    matched-accuracy table applies and for the same reason: those components
    are stale at the partitioned arm's exit by design.  With it travel the
    component the maximum sat on, the count of restricted components at or
    above τ, the whole-state maximum beside, and whether the pair is
    *categorically clean* — no discrete component differs, no constant moved,
    no NaN appeared on one side only.  The mixed ruler is not offered: its
    denominator reads a *current* value, and a distance between two states
    has no current side.

    **Over the pairs:** ``n`` counts the pairs the two arms have in common at
    the pairing key; ``n_compared`` the pairs on which both exit states exist
    and were read, and the shortfall is named by reason, never dropped;
    the median (nearest-rank upper-middle) and p90 (nearest-rank ``ceil(0.9
    n)``) of the restricted maximum over the compared pairs, the worst pair and
    its key (none when every compared pair reads exactly 0: nothing is worst),
    the count of compared pairs with any restricted component at or
    above τ, the count that are categorically unclean, and the whole-state
    median and p90 beside.

    **Reported, not accepted on.**  No acceptance rule was pre-declared for
    this quantity in the experiment plan; it was added after the campaign
    (task A76 (fixed-point-distance)) from records already on disk.  The
    reader is given τ beside every cell and the acceptance stays with the
    checks that declared one.
    """
    compared = [p for p in pairs if p.get("compared")]
    reasons: dict[str, int] = {}
    for p in pairs:
        if not p.get("compared"):
            reason = str(p.get("why") or "unstated")
            reasons[reason] = reasons.get(reason, 0) + 1
    restricted = [float(p["restricted_max"]) for p in compared]
    whole = [float(p["whole_max"]) for p in compared]
    worst = (
        max(compared, key=lambda p: float(p["restricted_max"]))
        if compared and max(restricted) > 0
        else None
    )
    return {
        "n": len(pairs),
        "n_compared": len(compared),
        "not_compared_by_reason": reasons,
        "restricted_median": median(restricted),
        "restricted_p90": p90(restricted),
        "restricted_max": max(restricted) if restricted else None,
        "worst_pair_key": None if worst is None else worst.get("key"),
        "argmax_components": sorted(
            {str(p.get("restricted_argmax")) for p in compared if p.get("restricted_argmax")}
        ),
        "n_pairs_above_tau": sum(
            1 for p in compared if int(p.get("restricted_n_above_tau") or 0) > 0
        ),
        "n_pairs_unclean": sum(
            1 for p in compared if not p.get("categorically_clean", True)
        ),
        "whole_median": median(whole),
        "whole_p90": p90(whole),
        "n_excluded": sorted({int(p["n_excluded"]) for p in compared if p.get("n_excluded") is not None}),
        "tau": tau,
        "construction": (
            "per pair: the predicate's scaled residual between the two exit "
            "states on the frozen ruler, restricted to the components the "
            "once-per-run deferred nodes do not write; over pairs: nearest-rank "
            "upper-middle median and nearest-rank ceil(0.9 n) p90 of the "
            "restricted maximum"
        ),
    }


# --------------------------------------------------------------------------
# the headline tables' constructions (task A79 (report-captions), 2026-09-15)
# --------------------------------------------------------------------------

#: The node groups of the partition, in the order the headline tables print
#: them: the three modules, the articulation point, the feed-forward tail.
#: Read from the committed node map's ``module_order``, never typed here; this
#: tuple is the *printing* order and is checked against that map.
NODE_GROUP_ORDER: tuple[str, ...] = ("M1", "M2", "M3", "PULSE", "FF")

#: The label of the group that holds the configuration's once-per-run deferred
#: nodes, whatever module the map puts them in: the partitioned arm runs them
#: once at the end of the solve, so their calls belong to no module's loop.
ONCE_PER_RUN_GROUP = "once per run"


def node_groups(
    node_map: Mapping[str, Any],
    per_run_nodes: Sequence[str],
    nodes_seen: Sequence[str],
) -> list[dict[str, Any]]:
    """**The module grouping of the headline tables**, derived and never listed.

    Every node the census counted is placed by the committed node map
    (``harness/data/dsm_node_map.json``, ``nodes[<node>].module``) into
    ``M1``, ``M2``, ``M3``, ``PULSE`` or ``FF``, **except** the configuration's
    once-per-run deferred nodes — the ``post_solve_nodes`` of the per-run
    artifact the runs name — which form their own group whatever module the map
    assigns them, because the partitioned arm executes them once per run, after
    the solve, and their calls are not a module's loop cost.  A node the census
    saw and the map does not name is a refusal: the grouping would otherwise be
    guessed.  Groups with no node seen are omitted rather than printed as 0,
    so a group's absence means *no such node ran here* and not *it cost
    nothing*.  Returns ``[{"group", "nodes"}]`` in ``NODE_GROUP_ORDER`` with the
    once-per-run group last.
    """
    modules = node_map.get("nodes") or {}
    order = node_map.get("module_order") or {}
    unknown = sorted(n for n in nodes_seen if n not in modules)
    if unknown:
        raise StatsError(
            f"the census counted node(s) {unknown} that the committed node map "
            f"does not place in a module; the grouping would be guessed, so "
            f"the per-module table is refused"
        )
    declared = {m for m in order if m != "X"}
    if declared != set(NODE_GROUP_ORDER):
        raise StatsError(
            f"the node map's module_order names {sorted(declared)} and this "
            f"construction prints {NODE_GROUP_ORDER}; one of them has moved"
        )
    once = set(per_run_nodes)
    grouped: dict[str, list[str]] = {g: [] for g in NODE_GROUP_ORDER}
    grouped[ONCE_PER_RUN_GROUP] = []
    for node in sorted(set(nodes_seen)):
        if node in once:
            grouped[ONCE_PER_RUN_GROUP].append(node)
        else:
            grouped[str(modules[node]["module"])].append(node)
    return [
        {"group": group, "nodes": nodes}
        for group, nodes in grouped.items()
        if nodes
    ]


def per_node_census(record: Mapping[str, Any], *, phase: str) -> dict[str, int]:
    """**Model executions per node, read from the run's own census.**

    The evaluation phase (``phase == "A"``) stamps ``node_census.counted``: the
    measured evaluation alone, frozen before the exit audit's uncharged sweep,
    so it sums to ``node_calls_single_eval``.  The optimisation phase
    (``"B"``) stamps ``node_census.per_node_counted`` over the **whole run** —
    every attempt, the output path and the exit audit's one sweep — and says
    whether that sum matches the driver's counter
    (``counted_matches_node_calls_total``); a record where it does not is a
    refusal, because a per-module split of a total nobody can reconcile is a
    table of nothing.  The whole-run count exceeds the solve-phase total by
    the output path and the audit, and the per-module table prints that
    difference as its own row rather than apportioning it.
    """
    census = record.get("node_census") or {}
    if phase == "A":
        counted = census.get("counted")
    else:
        counted = census.get("per_node_counted")
        if census.get("counted_matches_node_calls_total") is False:
            raise StatsError(
                f"{_label(record)}: the per-node census sums to "
                f"{census.get('sum_counted')} and the driver's counter reads "
                f"{census.get('node_calls_total_reported')}; a per-module split "
                f"of a total that does not reconcile is refused"
            )
    if not isinstance(counted, Mapping) or not counted:
        raise StatsError(
            f"{_label(record)}: no per-node census on this record, so the "
            f"per-module table cannot be built from it"
        )
    return {str(k): int(v) for k, v in counted.items()}


def census_by_group(
    counted: Mapping[str, int], groups: Sequence[Mapping[str, Any]]
) -> dict[str, int]:
    """Node calls summed over each group's nodes, one run: ``{group: calls}``."""
    return {
        str(g["group"]): sum(int(counted.get(node, 0)) for node in g["nodes"])
        for g in groups
    }


def module_sweeps(
    counted: Mapping[str, int], groups: Sequence[Mapping[str, Any]]
) -> dict[str, float]:
    """**Module sweeps in one run** — the cell of the per-module headline tables.

    A module is *swept* when the schedule walks it, and every model node
    inside it runs once per sweep.  So the module's sweep count is the census
    count that **all of its nodes share**, and the table's cell is a sweep
    count rather than a node-call count: a ratio of sweeps does not depend on
    whether one counts model calls or DSM rows, which a ratio of node calls
    does (the previous revision's §4.5 demoted the node-weighted total for
    exactly this reason).

    The premise is checked, never assumed: **if two nodes of one group carry
    different census counts the construction refuses**, naming the group, the
    counts and the run.  The previous revision refused the same way, and the
    check is a tooth of gate ``tally_contracts``.  A group with no node seen
    is absent from the result rather than reading 0, as :func:`node_groups`
    leaves it absent.

    Returns ``{group: sweeps}``.
    """
    out: dict[str, float] = {}
    for group in groups:
        name = str(group["group"])
        nodes = [str(n) for n in group["nodes"]]
        if not nodes:
            continue
        counts = {node: int(counted.get(node, 0)) for node in nodes}
        distinct = sorted(set(counts.values()))
        if len(distinct) != 1:
            raise StatsError(
                f"group {name!r} executed its nodes unequally — {counts} — so "
                f"its cell is not a sweep count.  The per-module table states "
                f"module sweeps per run and is refused rather than printed "
                f"over a group whose members did not execute together."
            )
        out[name] = float(distinct[0])
    return out


def dsm_rows_by_group(
    node_map: Mapping[str, Any], groups: Sequence[Mapping[str, Any]]
) -> dict[str, dict[str, int]]:
    """**`models` per group**, under the two defensible attributions (trap T9).

    ``models`` is the number of collapsed-DSM rows a group resolves, so that
    ``total calls = Σ sweeps × models``.  The committed node map
    (``harness/data/dsm_node_map.json``) pins rows **per module**
    (``units.dsm_rows``) and pins a row for only four individual nodes,
    nulling the rest, because trap T9 forbids reading the dependency-analysis
    repository's exports live.  The once-per-run group is assembled from
    nodes that live in other modules' row ranges, so **how many rows it owns
    is unknown** and the total is published as an interval rather than a
    point estimate:

    ``v = 1``
        each once-per-run node owns a row of its own, taken out of the module
        the map assigns it — the case the measured liveness supports, since a
        row credited to its home module would be credited that module's sweep
        count, which the node does not have;
    ``v = 0``
        the once-per-run nodes own no row and their home modules keep every
        row — the point estimate the previous revision published before the
        inconsistency was named.

    Returns ``{group: {"v1": rows, "v0": rows}}``.  No per-module *ratio* is
    affected by the choice: a ratio of sweeps never reads ``models``.
    """
    rows = (node_map.get("units") or {}).get("dsm_rows") or {}
    nodes = node_map.get("nodes") or {}
    missing = sorted(g for g in NODE_GROUP_ORDER if g not in rows)
    if missing:
        raise StatsError(
            f"the committed node map states no DSM row count for {missing}; "
            f"`models` would be guessed, so the per-module total is refused"
        )
    out: dict[str, dict[str, int]] = {}
    once = next(
        (g for g in groups if str(g["group"]) == ONCE_PER_RUN_GROUP), None
    )
    home: dict[str, int] = {}
    if once is not None:
        for node in once["nodes"]:
            placed = str((nodes.get(str(node)) or {}).get("module") or "")
            if placed not in rows:
                raise StatsError(
                    f"once-per-run node {node!r} is placed in module "
                    f"{placed!r}, which the node map gives no row count; the "
                    f"v = 1 attribution cannot be formed and the total is "
                    f"refused"
                )
            home[placed] = home.get(placed, 0) + 1
    for group in groups:
        name = str(group["group"])
        if name == ONCE_PER_RUN_GROUP:
            out[name] = {"v1": len(group["nodes"]), "v0": 0}
        else:
            whole = int(rows[name])
            out[name] = {"v1": whole - home.get(name, 0), "v0": whole}
    return out


def weighted_total(
    sweeps: Mapping[str, float], models: Mapping[str, Mapping[str, int]], *, case: str
) -> float | None:
    """``Σ sweeps × models`` over the groups, under one row attribution.

    ``case`` is ``"v1"`` or ``"v0"``.  A group the run has no sweep count for
    contributes nothing and the total is ``None`` if no group does, so a total
    is never a sum over a population quietly smaller than the table's rows
    (trap T11).
    """
    if case not in ("v1", "v0"):
        raise StatsError(f"no row attribution {case!r}: it is 'v1' or 'v0'")
    terms = [
        float(value) * int(models[group][case])
        for group, value in sweeps.items()
        if group in models and value is not None
    ]
    return sum(terms) if terms else None

def n_evaluations(record: Mapping[str, Any]) -> int | None:
    """**The run's evaluations of the model set** — ``sweeps_per_eval.n_evaluations``.

    The count of ``call_models`` entries the driver's histogram saw during
    the solve, output path excluded, summed over every attempt (the driver
    accumulates the histogram across the retry ladder).  This is the ε of
    R = ρ × ε (the V5 improvement list, item 1) and the field issue **I-26**
    names as the correct one: ``n_model_calls`` counts sweeps of the dispatch
    body (``numerics.n_model_calls``), not evaluations.  Check 2's ε column
    reads this construction too since task A80 (report-accuracy-audit) closed
    I-26; the sweep ratio it used to print is kept there as its own column.
    """
    block = record.get("sweeps_per_eval") or {}
    value = block.get("n_evaluations")
    return None if value is None else int(value)


def per_seed_ratio_summary(
    reference: Sequence[float], arm: Sequence[float]
) -> dict[str, Any]:
    """**A per-seed ratio, summarised**: the headline tables' second reading.

    Over paired values (element *i* of each is the same seed): the
    **pooled** ratio Σ arm / Σ reference; the **mean** of the per-seed
    ratios; their nearest-rank upper-middle **median** and ``[min, max]``;
    and **``n_above_one``**, the count of seeds on which the arm's value
    exceeded the reference's (ratio > 1).  The pooled ratio is the campaign's
    figure; the mean and median are the typical seed's; the count says on how
    many seeds the direction reversed.  A pair whose reference is 0 or whose
    side is missing is dropped from the per-seed statistics and counted in
    ``n_dropped``, never silently.
    """
    if len(reference) != len(arm):
        raise StatsError(
            f"a per-seed ratio over {len(reference)} reference values and "
            f"{len(arm)} arm values: the two sides are not the same seeds"
        )
    per_seed = [
        (b / a)
        for a, b in zip(reference, arm)
        if a not in (0, None) and b is not None
    ]
    total_reference = sum(v for v in reference if v is not None)
    bracket = seed_bracket(per_seed)
    return {
        "n": len(per_seed),
        "n_dropped": len(reference) - len(per_seed),
        "pooled": (
            (sum(v for v in arm if v is not None) / total_reference)
            if total_reference
            else None
        ),
        "mean": (sum(per_seed) / len(per_seed)) if per_seed else None,
        "median": median(per_seed),
        "min": None if bracket is None else bracket[0],
        "max": None if bracket is None else bracket[1],
        "n_above_one": sum(1 for r in per_seed if r > 1),
    }


# --------------------------------------------------------------------------
# the previous revision's remaining table shapes (task A86
# (v3-tables-remainder), 2026-09-15)
# --------------------------------------------------------------------------


def iteration_variables(record: Mapping[str, Any]) -> dict[str, float]:
    """**The accepted design vector, keyed by iteration-variable name.**

    The output file carries the vector twice over, both keyed by the solver's
    slot: ``mfile.itvars`` as ``itvar001 … itvarNNN`` and
    ``mfile.itvar_names`` as the name in each slot.  This construction joins
    them **on the slot** and returns ``{name: value}``.

    **The premise is checked, never assumed.**  The lift adds one iteration
    variable on a pulsed configuration, so two arms' vectors are of different
    lengths and *matching by position would compare two different variables*
    (the previous revision's §5.2.2 caption: *"Variables are matched by name,
    never by index"*).  A record with a value in a slot the name map does not
    carry therefore has no keyed vector at all and is **refused**, rather than
    being zipped by position.
    """
    mfile = record.get("mfile") or {}
    values = mfile.get("itvars") or {}
    names = mfile.get("itvar_names") or {}
    if not values or not names:
        raise StatsError(
            f"{_label(record)}: the output file carries no keyed iteration "
            f"variables (values {len(values)}, names {len(names)}), so there "
            f"is no design vector to compare by name"
        )
    unnamed = sorted(set(values) - set(names))
    if unnamed:
        raise StatsError(
            f"{_label(record)}: the output file carries value(s) {unnamed} "
            f"with no name.  A design vector matched by index would compare "
            f"two different variables once the lift has added one, so the "
            f"keyed vector is refused rather than zipped by position."
        )
    return {
        str(names[slot]): float(value)
        for slot, value in sorted(values.items())
        if value is not None
    }


def point_difference(
    a: Mapping[str, float], b: Mapping[str, float]
) -> dict[str, Any]:
    """**How far apart two runs' design points are** — a diagnostic, never an
    acceptance (decision **D6**).

    Over the variables the two vectors **share by name**, the per-variable
    relative difference ``|Δx| / max(|x_a|, |x_b|)``; the maximum of those,
    the variable it sat on, how many variables are shared, and the names
    carried by one side only — which are reported and **never compared**,
    because a variable one arm does not have has no difference.

    Returns ``{"max", "argmax", "n_shared", "extra"}``; ``max`` is ``None``
    where the two share no variable, and a shared pair both of whose values
    are exactly zero contributes 0, not a division.
    """
    shared = sorted(set(a) & set(b))
    extra = sorted(set(a) ^ set(b))
    worst: float | None = None
    argmax: str | None = None
    for name in shared:
        scale = max(abs(a[name]), abs(b[name]))
        gap = 0.0 if scale == 0 else abs(a[name] - b[name]) / scale
        if worst is None or gap > worst:
            worst, argmax = gap, name
    return {
        "max": worst,
        "argmax": argmax if worst else argmax,
        "n_shared": len(shared),
        "extra": extra,
    }


def namespace_residuals(
    audit: Mapping[str, Any], *, ruler: str
) -> dict[str, float]:
    """**The maximum scaled residual of each excluded namespace, in one run.**

    The restricted statistic excludes the components the configuration's
    once-per-run deferred nodes write, and the report's headline rests
    entirely on that exclusion being right.  This construction says how much
    is behind it: for every component the run's own ``excluded_keys`` names,
    the scaled residual on the named ruler, grouped by the **namespace** part
    of the ``namespace.field`` key and reduced to that namespace's maximum.

    ``audit`` is the run's ``audit_residual.json``.  The keys are the run's
    own — a namespace list typed here would be a list of what somebody
    expected the exclusion to hold — so a file carrying **no** ``excluded_keys``
    is refused rather than read as an empty exclusion, and a ruler the file
    does not carry is refused rather than falling back to another one.
    """
    excluded = audit.get("excluded_keys")
    if excluded is None:
        raise StatsError(
            "the audit residual file names no excluded_keys, so which "
            "components the restriction removed would have to be guessed; "
            "the per-namespace table is refused rather than built over a "
            "list typed by hand"
        )
    block = (audit.get("rulers") or {}).get(ruler)
    if not isinstance(block, Mapping):
        raise StatsError(
            f"the audit residual file carries no {ruler!r} ruler (it has "
            f"{sorted((audit.get('rulers') or {}))}); a namespace maximum on "
            f"another ruler would be a different quantity under this heading"
        )
    scaled = block.get("scaled_hex") or {}
    out: dict[str, float] = {}
    for key in excluded:
        raw = scaled.get(str(key))
        if raw is None:
            continue
        value = float.fromhex(str(raw)) if isinstance(raw, str) else float(raw)
        namespace = str(key).split(".", 1)[0]
        out[namespace] = max(out.get(namespace, 0.0), value)
    return out


def figure_of_merit(numerics_source: str, i_figure_merit: Any) -> dict[str, Any]:
    """**The objective's name and sense**, from the frozen tree's own enum.

    ``i_figure_merit`` is an integer in every record and a **negative** value
    means *maximise* (the previous revision's §5.6 caption).  The name is the
    description string of the matching member of ``FiguresOfMerit`` in
    ``process/data_structure/numerics.py`` **of the experiment's frozen
    copy** — parsed from the file's text, never imported, so that reading the
    objective's name cannot run model code.

    A figure of merit the enum does not carry is **refused**: a table that
    printed the integer where the name belongs would be a table whose reader
    cannot tell which problem was solved.
    """
    if i_figure_merit is None:
        raise StatsError(
            "a record carries no i_figure_merit, so the problem it solved "
            "cannot be stated"
        )
    number = int(i_figure_merit)
    members: dict[int, str] = {}
    for value, description in re.findall(
        r"=\s*\(\s*(\d+)\s*,\s*\n?\s*\"([^\"]+)\"", numerics_source
    ):
        members[int(value)] = description
    if abs(number) not in members:
        raise StatsError(
            f"i_figure_merit {number} names no member of the frozen tree's "
            f"FiguresOfMerit (it carries {sorted(members)}); the objective "
            f"would be printed as an integer, which says nothing about which "
            f"problem was solved"
        )
    return {
        "i_figure_merit": number,
        "objective": members[abs(number)],
        "sense": "maximise" if number < 0 else "minimise",
    }
