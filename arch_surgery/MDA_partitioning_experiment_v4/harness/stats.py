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
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

__all__ = [
    "StatsError",
    "Population",
    "median",
    "p90",
    "seed_bracket",
    "accepted_optimum",
    "finished",
    "every_arm_converged",
    "configuration_invalid_seeds",
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
    "audit_position_of",
    "empty_visit_shares",
    "predicate_widths",
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


@dataclass(frozen=True)
class Population:
    """The records a table is over, with the refusals that make it statable.

    **The declaration.** A population is a list of finished-or-not run records
    that share one phase, together with the denominator the table's counts are
    against.  It carries its own membership rule in :attr:`what`, because a
    count whose population cannot be stated in one clause is not ready to be
    published (trap T11).

    **Three refusals, all at construction:**

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
    ) -> "Population":
        """Build a population, refusing what may not be in one.

        ``denominator`` defaults to the number of records **asked for** — that
        is, the number offered here, demonstration runs included — because the
        denominator of a taxonomy is what was scheduled and not what survived.
        Pass it explicitly wherever the scheduled count is known independently
        (25 seeds per arm, say) and differs from the records on disk.
        """
        offered = list(records)
        kept: list[Mapping[str, Any]] = []
        excluded: list[tuple[str, str]] = []
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
