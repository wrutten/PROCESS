#!/usr/bin/env python
"""A second implementation of every published cell, and the comparison.

Two implementations of one declared definition drifted apart twice in this
project (queue issues **I-18** and **I-19**): a rule was written down once, and
the two places that computed it stopped agreeing without anything failing.  The
tally (``harness/tally_evaluation.py``, ``harness/tally_optimisation.py``) is
one implementation.  This module is the other, and ``--verify`` is the only
thing that can catch the drift.

**What makes it a second implementation and not a second copy.**  This module
imports **no** part of the tally: not ``harness/stats.py``, not either
``tally*`` module, not ``harness/tables.py``.  Every construction below is
re-derived from the declaration — the docstring in ``stats.py``, which the
experiment plan's §3.4–§3.6 wrote — and from the record fields
``harness/records.py`` declares.  An analysis that imported the constructions
would agree with the tally by construction and would prove nothing.  What it
*does* read is the tally's **output**: the two stage records
``runs/gates/tally_evaluation/measurements.json`` and
``…/tally_optimisation/measurements.json``, cell by cell.

Three entry points, and they are deliberately different kinds of thing:

``--verify``
    a **gate** (registered as ``recomputation``): every cell of every emitted
    table, recomputed here from the run records, against the cell the tally
    published.  0 mismatches over a stated denominator, or a verdict of FAIL.
    It refuses an empty comparison, refuses a population carrying a
    budget-capped demonstration record, and refuses a population whose records
    straddle two commits unless ``--resume`` asked for it — and it names the
    commits it read (``framework.survey_heads``).

``--teeth``
    the six deliberate breaks the criterion must catch, run and printed.  They
    are the gate's teeth: a criterion whose failure mode has never been
    exercised is an assertion, not a measurement (protocol §12).

``--tables``
    a **measurement** stage (registered as ``recomputed_tables``): this
    module's own markdown tables, with their own captions and denominators, to
    be read beside the tally's.  It has nothing to pass, so it is not a gate.

**What cannot be recomputed from records.**  One emitted table — *the predicate
trial* — is not built from run records at all: its decisive-pass counts come
from an observer that watches a run's predicate evaluations while it runs, and
no reader of records can reconstruct them afterwards.  This module recomputes
that table's **shaping** from the same gate verdict the tally read
(``gates/predicate_mode/gate.json``) and says so in the verdict, so a reader can
see that those cells are a check on the table and not on the measurement.

Heritage: the constructions are the V4 experiment plan's §3.4, §3.5 and §3.6 as
declared in ``harness/stats.py``'s docstrings; the populations are the
declarations in ``harness/tally.py`` (the two sources) and
``harness/tally_optimisation.py`` (seed-complete arm groups), re-derived here.
Written by task **A54 (harness-analysis)**, plan item H7.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from harness import framework
from harness.arms import MATRIX_ORDER
from harness.config import Campaign, default_campaign

__all__ = [
    "AnalysisError",
    "Population",
    "recompute",
    "compare",
    "verify",
    "tables",
    "gate",
    "measurement",
    "main",
]


class AnalysisError(framework.GateError):
    """A refused recomputation.  Never downgraded into a warning.

    A subclass of the framework's refusal so the button reports it the way it
    reports every other one — ``REFUSED — …`` with the sentence — rather than
    as a traceback a reader has to decode.
    """


# --------------------------------------------------------------------------
# where the tally's output lives
# --------------------------------------------------------------------------

#: The two stage records ``--verify`` compares against, by the measurement
#: stage that writes each.  The comparison is against the tally's **output**
#: and never against its code (the queue's A54 row, added at A53's merge).
TALLY_STAGES: tuple[str, ...] = ("tally_evaluation", "tally_optimisation")

#: Where the gate whose verdict carries the predicate trial's counts writes it.
PREDICATE_TRIAL_VERDICT = Path("predicate_mode") / "gate.json"

#: The stamp on a record made with the optimiser's evaluation budget
#: deliberately cut, to force the retry ladder to run more than one attempt.
#: Such a record demonstrates a decomposition and is not a measurement of
#: anything; a population carrying one is refused rather than quietly shrunk.
FORCED_BUDGET_STAMP = "force_maxcal"

#: The arm every optimisation-phase ratio and pair is stated against: the flat
#: control, which differs from the shipped reference by the stopping rule alone
#: (experiment plan §3.5).
BASE_ARM = "B0"

#: The pair whose spread calibrates check 1's threshold — two arms differing
#: only in the stopping rule, measured inside the same campaign.
YARDSTICK_PAIR = ("BR", "B0")

#: The arms check 2's acceptance rule is read on.  Every other pair is
#: published beside it, outside the rule.
ACCEPTANCE_PAIRS: tuple[str, ...] = ("B1", "B3")

#: The two convergence tests, by the name the record gives each.  Never pooled:
#: an arm stops on exactly one of them and their widths differ by nearly two
#: orders of magnitude, so their sum belongs to neither.
PREDICATES: tuple[str, ...] = ("coupling_state", "upstream")

#: Fields that identify **which exit-audit instrument** produced a record's
#: residuals.  Read through :func:`audit_instrument` and nowhere else, because
#: the instrument is changing under decision D25 (task A62
#: (exit-audit-restore)) and a caption must state the version **read from the
#: record**, never assumed from the date.
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


# --------------------------------------------------------------------------
# the constructions, re-derived from their declarations
# --------------------------------------------------------------------------


def middle(values: Sequence[float]) -> float | None:
    """The declared median: **nearest-rank, upper-middle**.

    The element at index ``n // 2`` of the sorted values — deliberately not the
    mean of the two central order statistics, because an interpolated median is
    not one of the measured values and every acceptance quantity here is a
    measured one.  ``None`` over an empty sequence, never 0.
    """
    ordered = sorted(values)
    return ordered[len(ordered) // 2] if ordered else None


def ninetieth(values: Sequence[float]) -> float | None:
    """The declared p90: **nearest-rank**, element ``ceil(0.9 n)`` counting
    from 1.  ``None`` over an empty sequence."""
    ordered = sorted(values)
    if not ordered:
        return None
    return ordered[max(0, math.ceil(0.9 * len(ordered)) - 1)]


def extremes(values: Sequence[float]) -> list[float] | None:
    """``[min, max]`` over the values: the observed range, not an interval."""
    ordered = sorted(values)
    return [ordered[0], ordered[-1]] if ordered else None


def arithmetic_mean(values: Sequence[Any]) -> float | None:
    """The per-run mean over the values that exist.  ``None`` over none."""
    present = [v for v in values if v is not None]
    return (sum(present) / len(present)) if present else None


def completed(record: Mapping[str, Any]) -> bool:
    """The run finished and wrote a record: ``status == "ok"``.

    Weaker than :func:`at_an_accepted_optimum`, and never the population of an
    optimisation-phase check — an optimiser can finish without converging.
    """
    return record.get("status") == "ok"


def at_an_accepted_optimum(record: Mapping[str, Any]) -> bool:
    """An accepted optimum: ``status == "ok"`` **and** the output file's
    ``ifail == 1``.

    Two sources deliberately — the harness's own word for how the run ended and
    PROCESS's own output file, which is independent of the harness.
    """
    return completed(record) and (record.get("mfile") or {}).get("ifail") == 1.0


def attempt_count(record: Mapping[str, Any]) -> int:
    """How many times the optimiser was called on this start: the length of
    ``attempts[]``.  An evaluation-phase record has none and reads 0."""
    attempts = record.get("attempts")
    return len(attempts) if isinstance(attempts, list) else 0


def was_retried(record: Mapping[str, Any]) -> bool:
    """A retried seed: the optimiser was called more than once on it.

    Computed from ``attempts[]`` and **from nothing else**.  The record carries
    a derived ``attempt_accounting.retried`` and it is deliberately not
    consulted: it is a copy of this same count, and a tally reading a stored
    flag cannot tell a driver that stopped stamping attempts from a run that
    did not retry.  One of this module's teeth is exactly that substitution.
    """
    return attempt_count(record) > 1


def retried_seeds(rows: Mapping[int, Mapping[str, Any]]) -> list[int]:
    """The seeds of *rows* whose run retried, in order."""
    return sorted(seed for seed, record in rows.items() if was_retried(record))


def node_calls_per_attempt(record: Mapping[str, Any]) -> list[Any]:
    """Solve-phase model executions of each attempt, in order."""
    return [a.get("node_calls_solve_phase") for a in (record.get("attempts") or [])]


def summed_node_calls(record: Mapping[str, Any]) -> float | None:
    """Solve-phase node calls **summed over the attempts**, or ``None``.

    The quantity every cost ratio is over, so that the ratio is visibly over
    what the attempts decompose.  ``None`` where any attempt carries no cost:
    a partial sum is not a sum.
    """
    values = node_calls_per_attempt(record)
    if not values or any(v is None for v in values):
        return None
    return float(sum(int(v) for v in values))


def summation_identity(record: Mapping[str, Any]) -> dict[str, Any]:
    """Σ over attempts against the run's solve-phase total, with the residual.

    Stated as a number rather than assumed, for node calls and for sweeps.
    ``applicable`` is False for a record with no attempts — the evaluation
    phase runs no optimiser, so there is nothing to decompose.
    """
    attempts = record.get("attempts")
    if not isinstance(attempts, list) or not attempts:
        return {"applicable": False, "n_attempts": 0, "parts": {}}
    parts: dict[str, Any] = {}
    for per_attempt_field, total_field in (
        ("node_calls_solve_phase", "node_calls_solve_phase"),
        ("sweeps", "dispatch_sweeps_solve_phase"),
    ):
        values = [a.get(per_attempt_field) for a in attempts]
        total = record.get(total_field)
        if any(v is None for v in values) or total is None:
            parts[per_attempt_field] = {"checked": False}
            continue
        summed = sum(int(v) for v in values)
        parts[per_attempt_field] = {
            "checked": True,
            "per_attempt": [int(v) for v in values],
            "summed": summed,
            "run_total": int(total),
            "residual": int(total) - summed,
            "decomposes": int(total) == summed,
        }
    checked = [p for p in parts.values() if p.get("checked")]
    return {
        "applicable": True,
        "n_attempts": len(attempts),
        "parts": parts,
        "decomposes": bool(checked) and all(p["decomposes"] for p in checked),
    }


def iterations_of_the_final_attempt(record: Mapping[str, Any]) -> int | None:
    """Check 2, construction one: the optimiser's iterations on its **final
    attempt**, taken from the last element of ``attempts[]``.

    From the list rather than from the run's own ``n_solver_iterations``, so
    that a disagreement with the summed construction is a disagreement about
    the list and not about which field was read.
    """
    attempts = record.get("attempts") or []
    return attempts[-1].get("n_iterations") if attempts else None


def iterations_summed(record: Mapping[str, Any]) -> int | None:
    """Check 2, construction two and the **declared acceptance statistic**:
    iterations summed over every attempt, failed attempts included.

    ``None`` where any attempt carries no iteration count: a partial sum is not
    a sum.
    """
    attempts = record.get("attempts") or []
    if not attempts:
        return None
    values = [a.get("n_iterations") for a in attempts]
    if any(v is None for v in values):
        return None
    return sum(int(v) for v in values)


def ratio_three_ways(
    reference: Sequence[float], arm: Sequence[float]
) -> dict[str, Any]:
    """The ratio against the reference, three ways, over a **paired** set.

    *pooled* is Σ arm / Σ reference — the campaign's cost; *median* is the
    nearest-rank upper-middle of the per-seed ratios — the typical run; *worse*
    counts the seeds on which the arm cost more.  The three are published
    together because they can disagree in direction.  Element *i* of each
    sequence is the same seed, so a length mismatch is a wrong pairing and is
    refused rather than silently truncated.
    """
    if len(reference) != len(arm):
        raise AnalysisError(
            f"a paired ratio over {len(reference)} reference values and "
            f"{len(arm)} arm values: the two sides are not the same seeds, so "
            f"the ratio would be over a population nobody can state"
        )
    per_run = [
        (b / a)
        for a, b in zip(reference, arm)
        if a not in (0, None) and b is not None
    ]
    total_reference = sum(reference) if reference else 0
    return {
        "n": len(reference),
        "pooled": (sum(arm) / total_reference) if total_reference else None,
        "median": middle(per_run),
        "bracket": extremes(per_run),
        "worse": sum(1 for a, b in zip(reference, arm) if b > a),
    }


def cost_with_and_without_retried(
    reference: Mapping[int, Mapping[str, Any]],
    arm: Mapping[int, Mapping[str, Any]],
    seeds: Sequence[int],
) -> dict[str, Any]:
    """The cost ratio **with** and **without** the retried seeds, side by side.

    Both readings are defensible and both are published: a retry the other arm
    did not need is real cost the architecture avoided at that start, *and* it
    is a robustness event rather than a per-evaluation cost.  A seed is retried
    when **either** side of the pair retried — the pair is what the ratio is
    over, and dropping a seed from one side only would compare two different
    populations.  The quantity is solve-phase node calls summed over
    ``attempts[]``, so the ratio is over what the attempts decompose.
    """
    both = [s for s in seeds if s in reference and s in arm]
    retried_here = sorted(
        s for s in both if was_retried(reference[s]) or was_retried(arm[s])
    )
    quiet = [s for s in both if s not in set(retried_here)]

    def triple(seed_set: Sequence[int]) -> dict[str, Any]:
        pairs = [
            (summed_node_calls(reference[s]), summed_node_calls(arm[s]))
            for s in seed_set
        ]
        pairs = [(a, b) for a, b in pairs if a is not None and b is not None]
        if not pairs:
            return {"n": 0, "pooled": None, "median": None, "bracket": None,
                    "worse": 0}
        return ratio_three_ways([a for a, _ in pairs], [b for _, b in pairs])

    return {
        "seeds": list(both),
        "retried_seeds": retried_here,
        "n_retried": len(retried_here),
        "with_retried": triple(both),
        "without_retried": triple(quiet),
    }


def relative_objective_gap(a: float, b: float) -> float:
    """Check 1's statistic: ``|Δ norm_objf| / max(|a|, |b|)``.

    Per pair, relative, with the larger magnitude of the two sides as the
    denominator — the same form the cluster gap uses.  The absolute difference
    is published beside, never accepted against.
    """
    denominator = max(abs(a), abs(b))
    return abs(b - a) / denominator if denominator else 0.0


def threshold_at(
    yardstick: float | None, *, factor: float, floor: float
) -> float | None:
    """Check 1's acceptance rule: ``max(F × yardstick, floor)``.

    The yardstick is the reference-to-flat-control spread measured **inside the
    same campaign**, so the threshold is calibrated on the problem rather than
    chosen.
    """
    return None if yardstick is None else max(factor * yardstick, floor)


def objective_clusters(values: Sequence[float], *, gap: float) -> list[list[int]]:
    """Check 1a's clustering: indices grouped by sorted objective, split
    wherever the **relative** gap between adjacent sorted values exceeds *gap*.

    The gap is relative to the larger magnitude of the adjacent pair.  Two
    optima in one cluster are the same attractor for the hop rate.
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


def hop_rate(
    cluster_of: Mapping[Any, int], pairs: Sequence[tuple[Any, Any]]
) -> dict[str, Any]:
    """The hop rate: pairs whose two sides land in different clusters."""
    both = [(a, b) for a, b in pairs if a in cluster_of and b in cluster_of]
    hopped = [(a, b) for a, b in both if cluster_of[a] != cluster_of[b]]
    return {
        "n_pairs": len(both),
        "n_hops": len(hopped),
        "rate": (len(hopped) / len(both)) if both else None,
    }


def below_resolution(
    relatives: Sequence[float], *, floor: float, gap: float
) -> int:
    """Check 1b's named category: pairs with ``floor < r < gap`` — distinct
    optima below cluster resolution, declared in advance so a pair the
    clustering cannot separate is not read as "the same optimum"."""
    return sum(1 for r in relatives if floor < r < gap)


def similarity_verdict(
    a: float | None, b: float | None, *, factor: float
) -> dict[str, Any]:
    """The similarity verdict at factor F, with the plan's zero clause.

    Similar when ``max/min ≤ F``.  Both exactly zero is *trivially similar*;
    one zero and the other not is an unbounded ratio and is not similar; a
    missing distribution is a refusal to judge, not a verdict.
    """
    if a is None or b is None:
        return {"similar": None, "why": "a distribution is empty", "ratio": None}
    if a == 0 and b == 0:
        return {"similar": True, "why": "both exactly zero: trivially similar",
                "ratio": None}
    if a == 0 or b == 0:
        return {
            "similar": False,
            "why": "one side exactly zero, the other not: the ratio is unbounded",
            "ratio": None,
        }
    ratio = max(a, b) / min(a, b)
    return {"similar": bool(ratio <= factor),
            "why": f"ratio {ratio:.4g} against F = {factor:g}", "ratio": ratio}


def taxonomy(
    records: Iterable[Mapping[str, Any]], *, denominator: int
) -> dict[str, Any]:
    """The failure taxonomy with its denominator: one row per disposition, the
    rows summing to the number of runs **scheduled**.

    A run that wrote no record is ``no_record`` and is counted, not skipped: a
    whole class of failures once left a tally silently because an absent file
    raised instead of counting.
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


def audit_instrument(record: Mapping[str, Any]) -> str:
    """**Which exit-audit instrument produced this record's residuals**, as one
    line built from the record's own snapshot block.

    Read from the record and never assumed: the snapshot the audit restores
    from is being widened from the coupling state to the whole data structure
    (decision D25, task **A62 (exit-audit-restore)**), and every residual in
    every table moves when it lands.  The same table shape will carry two
    different instruments' numbers across that merge, and this column is what
    tells them apart.
    """
    snapshot = record.get("audit_snapshot")
    present: dict[str, Any] = {}
    if isinstance(snapshot, Mapping):
        for name in AUDIT_INSTRUMENT_FIELDS:
            if name in snapshot:
                present[name] = snapshot[name]
    parts: list[str] = []
    taken = present.get("positions_snapshotted") or present.get("positions_taken")
    if taken:
        parts.append(f"snapshot at {','.join(sorted(map(str, taken)))}")
    if present.get("n_restored") is not None:
        parts.append(f"{present['n_restored']} restored")
    if present.get("n_not_restorable") is not None:
        parts.append(f"{present['n_not_restorable']} not restorable")
    if not parts:
        parts.append(
            "no snapshot recorded on this record"
            if snapshot is None
            else "snapshot recorded with no position taken"
        )
    return "; ".join(parts)


def restricted_audit(record: Mapping[str, Any], *, ruler: str) -> dict[str, Any]:
    """The restricted audit maximum on one named ruler, with its **argmax**.

    The declared accuracy statistic: the largest scaled coupling-state residual
    over the components **not owned** by the configuration's once-per-run
    deferred nodes.  The argmax is part of the statistic, not a diagnostic — the
    maximum is one component's residual, and a table that averaged it would
    report a number no run produced.  ``n_excluded`` is the count the
    restriction removed **on this ruler**; the two rulers' counts are never
    pooled, and a record whose restricted block is null carries no count at all.
    """
    block = (record.get("exit_audit") or {}).get(ruler)
    if not isinstance(block, Mapping):
        return {"present": False}
    restricted = block.get("restricted")
    if not isinstance(restricted, Mapping):
        return {"present": False, "n_excluded": None}
    return {
        "present": True,
        "max": restricted.get("max"),
        "argmax": restricted.get("argmax"),
        "n_above_tau": restricted.get("n_above"),
        "n_excluded": block.get("n_excluded_from_the_restricted_statistic"),
    }


def whole_state_audit(record: Mapping[str, Any], *, ruler: str) -> dict[str, Any]:
    """The exit-audit maximum over **all** components on one named ruler.

    Published beside the restricted statistic to show the exclusion's size and
    never judged on its own: the once-per-run deferred nodes' outputs are stale
    at the audit by design, so a partitioned arm's whole-state maximum is large
    for a reason the design chose.
    """
    block = (record.get("exit_audit") or {}).get(ruler)
    if not isinstance(block, Mapping):
        return {"present": False}
    return {"present": True, "max": block.get("residual_max")}


def empty_visit_sweep_share(record: Mapping[str, Any]) -> float | None:
    """The **sweep** share of the empty block visits — and only that share.

    A block whose members are all skipped at the call site is still visited and
    still costs a full walk of the model sequence.  Those visits are counted and
    disclaimed, never repaired.  Two shares exist and they are not
    interchangeable: the *visit* share overstates the cost, because a block
    visited with no members costs no sweep at all.  The quotable one is the
    fraction of the run's dispatch sweeps those visits actually cost, and it is
    the only one this function returns.
    """
    empty_sweeps = record.get("empty_block_sweeps") or {}
    dispatch = record.get("dispatch_sweeps")
    n_empty_sweeps = sum(empty_sweeps.values()) if empty_sweeps else 0
    return (n_empty_sweeps / dispatch) if dispatch else None


def predicate_columns(record: Mapping[str, Any]) -> dict[str, Any]:
    """The two predicates' counts, **split**, with the width of each, and the
    test the run actually stopped on.  There is deliberately no total: a pooled
    predicate-evaluation count is a number belonging to neither test."""
    counters = record.get("predicate_counters") or {}
    coupling = counters.get("coupling_state_predicate") or {}
    upstream = counters.get("upstream_predicate") or {}
    return {
        "coupling_state": {
            "evaluations": record.get("predicate_evaluations"),
            "components_compared": record.get("components_compared"),
            "mean_test_width": coupling.get("mean_test_width"),
            "by_block": coupling.get("mean_test_width_by_block") or {},
        },
        "upstream": {
            "evaluations": record.get("upstream_predicate_evaluations"),
            "components_compared": record.get("upstream_components_compared"),
            "mean_test_width": upstream.get("mean_test_width"),
        },
        "stops_on": (
            "coupling_state"
            if record.get("predicate_evaluations")
            else ("upstream" if record.get("upstream_predicate_evaluations") else None)
        ),
    }


# --------------------------------------------------------------------------
# the populations, re-derived from their declarations
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Source:
    """One named, statable set of records a table may summarise.

    ``runs/gates/`` is **not one population**: several gates run the same arm at
    the same seed from different entries and three of them run it deliberately
    doctored, so a mean over that tree is a mean over a set nobody can state.  A
    source is a named subtree whose records are a comparable set, with the
    sentence that says why.
    """

    name: str
    subpath: str
    phases: str
    what: str
    keep: Callable[[Path], bool] | None = None


#: The two declared sources, re-derived from the declaration in
#: ``harness/tally.py``.  Re-derived rather than imported: if this module's
#: population and the tally's differ, that difference is a finding the verify
#: reports, and importing the tally's list would hide it.
SOURCES: tuple[Source, ...] = (
    Source(
        name="reference_runs",
        subpath="gates/reproduction/runs",
        phases="AB",
        what=(
            "the reproduction gate's own runs: one record per arm, "
            "configuration and seed of the reference set, made by the "
            "committed run path.  Gate runs, never campaign runs"
        ),
    ),
    Source(
        name="paired_entries",
        subpath="gates/entry_and_warm",
        phases="A",
        what=(
            "the entry gate's paired evaluations: every evaluation-phase arm "
            "entered from the same displaced coupling state at one seed"
        ),
        keep=lambda relative: len(relative.parts) > 1
        and relative.parts[1] == "pairing",
    ),
)


@dataclass(frozen=True)
class Population:
    """The records a table is over, with the refusals that make it statable."""

    records: tuple[Mapping[str, Any], ...]
    what: str
    phase: str
    excluded: tuple[str, ...] = ()

    @staticmethod
    def of(
        records: Sequence[Mapping[str, Any]], *, what: str
    ) -> "Population":
        """Build a population, naming what may not be in one.

        A record stamped ``force_maxcal`` is a budget-capped demonstration of
        the retry ladder and never a measurement; it is excluded **by name**
        rather than dropped silently, and :meth:`assert_no_demonstration`
        turns that into a refusal for a caller that must not have been handed
        one.  A mixture of phases is refused outright: the two phases do not
        record the same quantities and a table over both is a table over a
        population nobody can state.
        """
        kept: list[Mapping[str, Any]] = []
        excluded: list[str] = []
        for record in records:
            if record.get(FORCED_BUDGET_STAMP) is not None:
                excluded.append(label_of(record))
                continue
            kept.append(record)
        phases = {r.get("campaign_phase") for r in kept}
        phases.discard(None)
        if len(phases) > 1:
            raise AnalysisError(
                f"a population of {sorted(phases)} records: the two phases do "
                f"not record the same quantities, so a table over both is a "
                f"table over a population nobody can state.  Split them."
            )
        return Population(
            records=tuple(kept),
            what=what,
            phase=next(iter(phases)) if phases else "",
            excluded=tuple(excluded),
        )

    def assert_no_demonstration(self) -> None:
        """Refuse a population that was handed a budget-capped demonstration."""
        if self.excluded:
            raise AnalysisError(
                f"{len(self.excluded)} record(s) stamped {FORCED_BUDGET_STAMP} "
                f"reached a population that refuses them: "
                f"{', '.join(self.excluded)}.  A budget-capped demonstration "
                f"is not a measurement and may not be summarised with "
                f"measurements."
            )

    def __len__(self) -> int:
        return len(self.records)


def label_of(record: Mapping[str, Any]) -> str:
    """A record's identity in one string, for a message a reader can act on."""
    return (
        f"{record.get('campaign_arm', '?')}/"
        f"{record.get('campaign_configuration', '?')}/"
        f"seed{record.get('campaign_seed', '?')}"
    )


def read_records(root: Path) -> list[tuple[Path, Mapping[str, Any]]]:
    """Every run record under *root*, in path order, read as JSON.

    A record that will not parse is a row whose status says so, never an
    exception: a crashed subprocess that wrote half a file is a taxonomy row,
    and raising on it is how a class of failures once left a tally silently.
    """
    out: list[tuple[Path, Mapping[str, Any]]] = []
    for path in sorted(Path(root).rglob("metrics.json")):
        try:
            record = json.loads(path.read_text())
        except Exception:  # noqa: BLE001 - an unreadable record is a row
            record = {
                "status": "no_record",
                "failure_class": "machinery",
                "record_path": str(path),
            }
        out.append((path, record))
    return out


def source_records(
    campaign: Campaign, source: Source
) -> list[Mapping[str, Any]]:
    """Every record of one declared source, in path order."""
    root = Path(campaign.runs_dir) / source.subpath
    if not root.exists():
        return []
    rows = read_records(root)
    if source.keep is None:
        return [record for _, record in rows]
    return [
        record
        for path, record in rows
        if source.keep(path.parent.relative_to(root))
    ]


def arm_order(names: Iterable[str]) -> list[str]:
    """The plan's arm-matrix order, with anything unknown after it."""
    return sorted(
        names,
        key=lambda n: MATRIX_ORDER.index(n) if n in MATRIX_ORDER else len(MATRIX_ORDER),
    )


def by_arm(
    population: Population, configuration: str
) -> dict[str, list[Mapping[str, Any]]]:
    """This configuration's records grouped by arm, in path order."""
    out: dict[str, list[Mapping[str, Any]]] = {}
    for record in population.records:
        if record.get("campaign_configuration") != configuration:
            continue
        out.setdefault(str(record.get("campaign_arm")), []).append(record)
    return out


def by_arm_and_seed(
    population: Population, configuration: str
) -> dict[str, dict[int, Mapping[str, Any]]]:
    """This configuration's records indexed by arm and seed.

    A ratio between two arms is paired **seed by seed** or it is not paired at
    all: pairing two lists by position compares whichever runs happened to sort
    first.  Within one declared source an (arm, seed) is one job; a second
    record for the same key is the source failing to be the comparable set it
    declares itself to be, and the first is kept.
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


def seed_complete_arm_groups(
    index: Mapping[str, Mapping[int, Mapping[str, Any]]]
) -> list[tuple[tuple[str, ...], list[int]]]:
    """Split a source into **seed-complete arm groups**.

    The plan's one population per configuration is "the seeds on which *every*
    arm converged", and it assumes what a campaign guarantees: every arm runs at
    every seed.  A gate's runs do not guarantee it, so that construction over
    the whole source returns an empty set — and an empty set is an absence, not
    a population.  Each group is a set of arms and the seeds at which all of
    them ran, which *is* a population the construction applies to.  A group of
    one arm is dropped: there is no pair in it.  In a campaign there is exactly
    one group per configuration and this split is invisible.
    """
    at_seed: dict[int, set[str]] = {}
    for arm, seeds in index.items():
        for seed in seeds:
            at_seed.setdefault(seed, set()).add(arm)
    grouped: dict[tuple[str, ...], list[int]] = {}
    for seed, arms in sorted(at_seed.items()):
        if len(arms) < 2:
            continue
        grouped.setdefault(tuple(arm_order(arms)), []).append(seed)
    return sorted(grouped.items(), key=lambda kv: (-len(kv[0]), kv[0]))


def restricted_index(
    index: Mapping[str, Mapping[int, Mapping[str, Any]]],
    arms: Sequence[str],
    seeds: Sequence[int],
) -> dict[str, dict[int, Mapping[str, Any]]]:
    """The sub-index of one arm group: those arms, at those seeds, only."""
    return {
        arm: {seed: index[arm][seed] for seed in seeds if seed in index[arm]}
        for arm in arms
        if arm in index
    }


def every_arm_converged(
    index: Mapping[str, Mapping[int, Mapping[str, Any]]], seeds: Sequence[int]
) -> list[int]:
    """The one optimisation-phase seed set: the seeds on which **every** arm
    reached an accepted optimum.  The seeds outside it are not dropped — they
    are the failure table, published beside."""
    return [
        seed
        for seed in seeds
        if all(
            at_an_accepted_optimum(index.get(arm, {}).get(seed, {}))
            for arm in index
        )
    ]


def configuration_invalid(
    index: Mapping[str, Mapping[int, Mapping[str, Any]]], seeds: Sequence[int]
) -> list[int]:
    """Seeds on which **no** arm reached an accepted optimum: configuration
    hardness, not an arm effect."""
    return [
        seed
        for seed in seeds
        if not any(
            at_an_accepted_optimum(index.get(arm, {}).get(seed, {}))
            for arm in index
        )
    ]


def evaluation_reference_arm(pulsed: bool, present: Iterable[str]) -> str:
    """The evaluation phase's declared reference arm for the cost ratio.

    On a **pulsed** configuration it is the flat control with the burn time
    owned by a constant, because it and the partitioned arm sit on the same
    reduced map.  On a **steady-state** configuration there is no burn-time
    coupling, that arm degenerates onto the plain flat control and is skipped.
    A population that does not carry the declared arm falls back to the plain
    flat control, which is the previous revision's construction and a different
    comparison.
    """
    if not pulsed:
        return "A0"
    return "A0p" if "A0p" in set(present) else "A0"


# --------------------------------------------------------------------------
# a recomputed table
# --------------------------------------------------------------------------


@dataclass
class Recomputed:
    """One recomputed table: its name, its key columns, its rows.

    This module writes its own captions and its own denominators, and refuses a
    table without either, for the same reason the tally's table module does: a
    count published over a population quietly smaller than the one named is
    this project's trap T11, and a table whose meaning needs the surrounding
    prose to decode is incomplete (protocol §16).
    """

    name: str
    caption: str
    columns: tuple[str, ...]
    key_columns: tuple[str, ...]
    rows: tuple[Mapping[str, Any], ...]
    denominator: int
    denominator_is: str
    #: Cells that are composed strings rather than a construction's number.
    #: Reported separately, because agreement on a rendered string is weaker
    #: evidence than agreement on a computed quantity.
    composite: tuple[str, ...] = ()
    #: Where the numbers came from, when it is not the run records.
    from_records: bool = True

    def __post_init__(self) -> None:
        if not str(self.caption).strip():
            raise AnalysisError(
                f"recomputed table {self.name!r} carries no caption.  A table "
                f"whose meaning requires the surrounding prose to decode is "
                f"incomplete (protocol §16)."
            )
        if not isinstance(self.denominator, int) or isinstance(
            self.denominator, bool
        ):
            raise AnalysisError(
                f"recomputed table {self.name!r} has no denominator.  A count "
                f"published over a population quietly smaller than the one "
                f"named is this project's trap T11."
            )
        if not str(self.denominator_is).strip():
            raise AnalysisError(
                f"recomputed table {self.name!r} states a denominator of "
                f"{self.denominator} without saying what it counts."
            )

    def key(self, row: Mapping[str, Any]) -> tuple[Any, ...]:
        return tuple(row.get(column) for column in self.key_columns)

    def markdown(self) -> str:
        lines = [f"*Caption: {self.caption}*", ""]
        lines.append("| " + " | ".join(self.columns) + " |")
        lines.append("|" + "|".join("---" for _ in self.columns) + "|")
        for row in self.rows:
            lines.append(
                "| " + " | ".join(_render(row.get(c)) for c in self.columns) + " |"
            )
        lines.append("")
        lines.append(f"*n = {self.denominator} ({self.denominator_is}).*")
        return "\n".join(lines)

    def as_record(self) -> dict[str, Any]:
        return {
            "table": self.name,
            "caption": self.caption,
            "denominator": self.denominator,
            "denominator_is": self.denominator_is,
            "columns": list(self.columns),
            "key_columns": list(self.key_columns),
            "composite_cells": list(self.composite),
            "recomputed_from_run_records": self.from_records,
            "rows": [dict(row) for row in self.rows],
            "markdown": self.markdown(),
        }


def _render(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def _join_seeds(seeds: Sequence[int]) -> str:
    return ", ".join(str(s) for s in seeds) if seeds else "—"


def _bracket_text(values: Sequence[float]) -> str:
    bracket = extremes([v for v in values if v is not None])
    return "—" if bracket is None else f"[{bracket[0]:g}, {bracket[1]:g}]"


# --------------------------------------------------------------------------
# the evaluation phase's tables
# --------------------------------------------------------------------------


def _cost_per_call(
    campaign: Campaign, population: Population, configuration: str, source: str
) -> Recomputed:
    """What one evaluation cost, per arm, with the ratio triple (plan §4.2.1)."""
    grouped = by_arm(population, configuration)
    indexed = by_arm_and_seed(population, configuration)
    base = evaluation_reference_arm(
        campaign.configuration(configuration).pulsed, grouped
    )
    rows: list[dict[str, Any]] = []
    for arm in arm_order(grouped):
        finished = [r for r in grouped[arm] if completed(r)]
        calls = [r.get("node_calls_single_eval") for r in finished]
        sweeps = [r.get("n_model_calls_sweeps") for r in finished]
        blocks: dict[str, float] = {}
        for record in finished:
            totals = (record.get("block_loop_totals") or {}).get("sweeps_by_block") or {}
            for block, value in totals.items():
                blocks[block] = blocks.get(block, 0) + value
        ratio: dict[str, Any] = {}
        paired: list[int] = []
        if arm != base:
            reference, values, paired = _pair_on(
                indexed, base, arm, "node_calls_single_eval"
            )
            if reference:
                ratio = ratio_three_ways(reference, values)
        rows.append(
            {
                "arm": arm,
                "ok": f"{len(finished)}/{len(grouped.get(arm, []))}",
                "calls_per_eval": arithmetic_mean(calls),
                "calls_bracket": _bracket_text(calls),
                "sweeps_per_eval": arithmetic_mean(sweeps),
                "sweeps_by_block": (
                    ", ".join(f"{k} {v:g}" for k, v in sorted(blocks.items())) or "—"
                ),
                "arrangement_method_calls": arithmetic_mean(
                    [r.get("n_arrangement_method_calls") for r in finished]
                ),
                "paired_seeds": _join_seeds(paired),
                "pooled": ratio.get("pooled"),
                "median": ratio.get("median"),
                "worse": ratio.get("worse") if ratio else None,
            }
        )
    denominator = sum(len(v) for v in grouped.values())
    return Recomputed(
        name=f"cost per call — {configuration} — {source}",
        caption=(
            f"units: model-node executions per evaluation; sweeps are walks of "
            f"the model sequence; ratios dimensionless.  A row is one arm of "
            f"the evaluation phase on this configuration.  A column is a "
            f"per-run mean over that arm's finished runs with the observed "
            f"bracket, or one of the three readings of the ratio against the "
            f"reference arm {base}.  Population: {population.what}; "
            f"{denominator} run(s) of {configuration}.  Construction: pooled = "
            f"Σ arm / Σ reference over the seed-paired runs, median = "
            f"nearest-rank upper-middle of the per-run ratios, worse = runs on "
            f"which the arm cost more.  These are gate runs at one or two "
            f"seeds: no cell here is a campaign statistic."
        ),
        columns=(
            "arm", "ok", "calls_per_eval", "calls_bracket", "sweeps_per_eval",
            "sweeps_by_block", "arrangement_method_calls", "paired_seeds",
            "pooled", "median", "worse",
        ),
        key_columns=("arm",),
        rows=tuple(rows),
        denominator=denominator,
        denominator_is=f"evaluation-phase gate runs of {configuration}",
        composite=("ok", "calls_bracket", "sweeps_by_block", "paired_seeds"),
    )


def _pair_on(
    indexed: Mapping[str, Mapping[int, Mapping[str, Any]]],
    base: str,
    arm: str,
    field_name: str,
) -> tuple[list[float], list[float], list[int]]:
    """The two sides of a seed-keyed pairing, and the seeds they are over.

    Both sides must have finished and both must carry the field; a seed where
    either is missing is out of the pairing rather than silently zero.
    """
    if base not in indexed or arm not in indexed:
        return [], [], []
    reference: list[float] = []
    values: list[float] = []
    kept: list[int] = []
    for seed in sorted(set(indexed[base]) & set(indexed[arm])):
        left, right = indexed[base][seed], indexed[arm][seed]
        a, b = left.get(field_name), right.get(field_name)
        if a is None or b is None:
            continue
        if not (completed(left) and completed(right)):
            continue
        reference.append(a)
        values.append(b)
        kept.append(seed)
    return reference, values, kept


def _accuracy_rows(
    campaign: Campaign,
    grouped: Mapping[str, Sequence[Mapping[str, Any]]],
    *,
    optimisation: bool,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, list[float]]]]:
    """The rows of an accuracy table, on both rulers, and the distributions.

    Both rulers or neither: the mixed ruler reads lower wherever its
    denominator binds — by construction, not by being more accurate — so a
    table carrying one column alone would report a change of ruler as a change
    of accuracy.
    """
    rows: list[dict[str, Any]] = []
    distributions: dict[str, dict[str, list[float]]] = {}
    for arm in arm_order(grouped):
        finished = [r for r in grouped[arm] if completed(r)]
        for ruler in campaign.predicate_modes:
            restricted = [restricted_audit(r, ruler=ruler) for r in finished]
            whole = [whole_state_audit(r, ruler=ruler) for r in finished]
            restricted_values = [
                s["max"] for s in restricted
                if s.get("present") and s.get("max") is not None
            ]
            whole_values = [
                s["max"] for s in whole
                if s.get("present") and s.get("max") is not None
            ]
            argmaxes = sorted({s.get("argmax") for s in restricted if s.get("argmax")})
            excluded = sorted(
                {s.get("n_excluded") for s in restricted
                 if s.get("n_excluded") is not None}
            )
            positions = sorted(
                {str(r.get("audit_position")) for r in finished
                 if r.get("audit_position")}
            )
            instruments = sorted({audit_instrument(r) for r in finished})
            distributions.setdefault(arm, {})[ruler] = restricted_values
            row: dict[str, Any] = {
                "arm": arm,
                "ruler": ruler,
                "n": len(finished) if optimisation else len(restricted_values),
                "restricted_median": middle(restricted_values),
                "argmax": (
                    (", ".join(argmaxes)
                     if argmaxes and any(v for v in restricted_values)
                     else ("— (every component exactly 0)"
                           if restricted_values else "—"))
                    if optimisation
                    else (", ".join(argmaxes) if argmaxes else "—")
                ),
                "whole_median": middle(whole_values),
                "n_excluded": (
                    ", ".join(str(v) for v in excluded) if excluded else "—"
                ),
                "audit_position": (
                    positions[0]
                    if len(positions) == 1
                    else ("/".join(positions) if positions else None)
                ),
                "instrument": (
                    ("; " if optimisation else ";").join(instruments)
                    if instruments
                    else "—"
                ),
            }
            if optimisation:
                row["restricted_max"] = (
                    max(restricted_values) if restricted_values else None
                )
                row["n_above_tau"] = (
                    ", ".join(str(s.get("n_above_tau")) for s in restricted) or "—"
                )
            else:
                row["restricted_p90"] = ninetieth(restricted_values)
                row["whole_p90"] = ninetieth(whole_values)
            rows.append(row)
    return rows, distributions


def _matched_accuracy(
    campaign: Campaign, population: Population, configuration: str, source: str
) -> tuple[Recomputed, list[dict[str, Any]]]:
    """The achieved accuracy of the evaluation phase (plan §4.2.2)."""
    grouped = by_arm(population, configuration)
    base = evaluation_reference_arm(
        campaign.configuration(configuration).pulsed, grouped
    )
    rows, distributions = _accuracy_rows(campaign, grouped, optimisation=False)
    verdicts: list[dict[str, Any]] = []
    for arm in arm_order(grouped):
        if arm == base or base not in distributions or arm not in distributions:
            continue
        for ruler in campaign.predicate_modes:
            a = distributions[base].get(ruler) or []
            b = distributions[arm].get(ruler) or []
            verdicts.append(
                {
                    "configuration": configuration,
                    "pair": f"{arm}/{base}",
                    "ruler": ruler,
                    "median": similarity_verdict(
                        middle(a), middle(b), factor=campaign.similarity_factor
                    ),
                    "p90": similarity_verdict(
                        ninetieth(a), ninetieth(b), factor=campaign.similarity_factor
                    ),
                }
            )
    positions = sorted({r["audit_position"] for r in rows if r["audit_position"]})
    denominator = sum(len(v) for v in grouped.values())
    return (
        Recomputed(
            name=f"matched accuracy — {configuration} — {source}",
            caption=(
                f"units: dimensionless — the largest scaled coupling-state "
                f"residual found by one further full sweep past termination.  "
                f"A row is one arm on one ruler.  A column is the restricted or "
                f"whole-state maximum's median and p90 over that arm's finished "
                f"runs, the component the restricted maximum sat on, and how "
                f"many components the restriction removed.  Population: "
                f"{population.what}; {denominator} run(s) of {configuration}.  "
                f"Construction: median = nearest-rank upper-middle, p90 = "
                f"nearest-rank ceil(0.9 n); the restricted maximum excludes the "
                f"components the configuration's once-per-run deferred nodes "
                f"write.  Audit position: "
                f"{', '.join(positions) if positions else 'not recorded here'} "
                f"— a residual taken at the entry to the output path and one "
                f"taken after the run are different quantities.  The audit "
                f"instrument's version is read from the record, never assumed: "
                f"task A62 (exit-audit-restore) widens the snapshot under "
                f"decision D25 and moves every value in these columns.  Both "
                f"rulers or neither."
            ),
            columns=(
                "arm", "ruler", "n", "restricted_median", "restricted_p90",
                "argmax", "whole_median", "whole_p90", "n_excluded",
                "audit_position", "instrument",
            ),
            key_columns=("arm", "ruler"),
            rows=tuple(rows),
            denominator=denominator,
            denominator_is=f"evaluation-phase gate runs of {configuration}",
            composite=("argmax", "n_excluded", "instrument"),
        ),
        verdicts,
    )


def _ownership_rung(
    campaign: Campaign, population: Population, configuration: str, source: str
) -> Recomputed | None:
    """The cost and the price of taking the burn time out of the loop (§4.2.3)."""
    if not campaign.configuration(configuration).pulsed:
        return None
    grouped = by_arm(population, configuration)
    indexed = by_arm_and_seed(population, configuration)
    if not indexed.get("A0p"):
        return None
    flat = [r for r in grouped.get("A0", []) if completed(r)]
    reference, values, paired = _pair_on(
        indexed, "A0", "A0p", "node_calls_single_eval"
    )
    ratio = ratio_three_ways(reference, values) if reference else {}
    pinned = [
        indexed["A0p"][seed]
        for seed in sorted(indexed.get("A0p", {}))
        if completed(indexed["A0p"][seed])
    ]
    residuals = [
        abs((r.get("lift_residual") or {}).get("raw_s"))
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
    row = {
        "n": len(paired),
        "paired_seeds": _join_seeds(paired),
        "pooled": ratio.get("pooled"),
        "median": ratio.get("median"),
        "worse": ratio.get("worse") if ratio else None,
        "residual_s_median": middle(residuals),
        "residual_s_bracket": _bracket_text(residuals),
        "relative_median": middle(relatives),
    }
    return Recomputed(
        name=f"ownership rung A0 → A0p — {configuration} — {source}",
        caption=(
            f"units: the node-call ratio is dimensionless; the burn-time "
            f"residual is in seconds and relative to the burn time.  A row is "
            f"this configuration's rung.  A column is the cost of taking the "
            f"burn time out of the flat loop, or the inconsistency the constant "
            f"leaves behind.  Population: {population.what}; {len(flat)} "
            f"flat-control and {len(pinned)} pinned run(s) of {configuration}.  "
            f"Construction: the ratio triple on node calls of the single "
            f"evaluation; the residual is the lifted component's own "
            f"inconsistency at exit, |value|, median nearest-rank upper-middle.  "
            f"Neither column is a claim about the partition: this rung moves "
            f"one thing only."
        ),
        columns=(
            "n", "paired_seeds", "pooled", "median", "worse",
            "residual_s_median", "residual_s_bracket", "relative_median",
        ),
        key_columns=("n", "paired_seeds"),
        rows=(row,),
        denominator=len(flat) + len(pinned),
        denominator_is=f"A0 and A0p gate runs of {configuration}",
        composite=("paired_seeds", "residual_s_bracket"),
    )


def _per_sweep_overhead(
    population: Population,
    configuration: str,
    source: str,
    *,
    records_by_arm: Mapping[str, Sequence[Mapping[str, Any]]],
    optimisation: bool,
) -> Recomputed:
    """What the convergence tests cost, in counts (plan §3.5 check 5).

    The two predicates sit in columns of their own.  There is no summed column
    and none can be added: an arm stops on exactly one of the two tests, and
    their widths differ by nearly two orders of magnitude, so their sum is a
    number belonging to neither.
    """
    rows: list[dict[str, Any]] = []
    for arm in arm_order(records_by_arm):
        for record in records_by_arm[arm]:
            if not completed(record):
                continue
            widths = predicate_columns(record)
            coupling, upstream = widths["coupling_state"], widths["upstream"]
            row: dict[str, Any] = {
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
                "empty_sweep_share": empty_visit_sweep_share(record),
            }
            if optimisation:
                row["solve_sweeps"] = record.get("dispatch_sweeps_solve_phase")
                row["output_loop_sweeps"] = record.get("output_loop_sweeps")
            rows.append(row)
    shares = sorted(
        {round(100 * r["empty_sweep_share"], 2)
         for r in rows if r["empty_sweep_share"] is not None}
    )
    columns = ["arm", "seed", "stops_on", "dispatch_sweeps"]
    if optimisation:
        columns += ["solve_sweeps", "output_loop_sweeps"]
    columns += [
        "coupling_evaluations", "coupling_components", "coupling_width",
        "coupling_width_by_block", "upstream_evaluations",
        "upstream_components", "upstream_width", "empty_sweep_share",
    ]
    phase = "optimisation" if optimisation else "evaluation"
    return Recomputed(
        name=f"per-sweep overhead — {configuration} — {source}",
        caption=(
            f"units: counts — evaluations of a convergence test, and components "
            f"compared summed over them; sweeps are walks of the model "
            f"sequence.  A row is one finished {phase}-phase run.  A column is "
            f"a counter of one **named** convergence test, or a sweep total.  "
            f"Population: {population.what}; the finished {phase}-phase gate "
            f"runs of {configuration}.  Construction: the driver's own "
            f"counters, exact and concurrency-invariant.  The two predicates "
            f"are never pooled.  The empty block visits are counted and "
            f"disclaimed, never repaired, and the share quoted is the SWEEP "
            f"share — over this population "
            + (", ".join(f"{v:g} %" for v in shares)
               if shares else "not computable on any run here")
            + ".  The visit share is larger and is never quoted.  No conclusion "
            f"rests on a timing: the question is asked in counts alone."
        ),
        columns=tuple(columns),
        key_columns=("arm", "seed"),
        rows=tuple(rows),
        denominator=len(rows),
        denominator_is=f"finished {phase}-phase gate runs of {configuration}",
        composite=("stops_on", "coupling_width_by_block"),
    )


def _failure_taxonomy(
    population: Population, configuration: str, source: str
) -> Recomputed:
    """Every scheduled run a row, with its denominator (plan §4.2.6)."""
    grouped = by_arm(population, configuration)
    classes = sorted(
        {str(r.get("failure_class")) for records in grouped.values() for r in records}
    )
    rows: list[dict[str, Any]] = []
    for arm in arm_order(grouped):
        counted = taxonomy(grouped[arm], denominator=len(grouped[arm]))
        row: dict[str, Any] = {
            "arm": arm,
            "denominator": counted["denominator"],
            "sums": "yes" if counted["rows_sum_to_denominator"] else "NO",
        }
        for name in classes:
            row[name] = counted["by_failure_class"].get(name, 0)
        rows.append(row)
    return Recomputed(
        name=f"failure taxonomy — {configuration} — {source}",
        caption=(
            f"units: counts of runs.  A row is one arm on this configuration.  "
            f"A column is one disposition of the taxonomy.  Population: "
            f"{population.what}; every gate run of {configuration}.  "
            f"Construction: every scheduled run is a row and a run that wrote "
            f"no record is counted as no_record, never skipped.  An arm "
            f"inactive on a configuration is absent from this table rather "
            f"than reading 0: a skipped arm and a failing arm are different "
            f"results."
        ),
        columns=("arm", "denominator", *classes, "sums"),
        key_columns=("arm",),
        rows=tuple(rows),
        denominator=sum(len(v) for v in grouped.values()),
        denominator_is=f"evaluation-phase gate runs of {configuration}",
        composite=("sums",),
    )


def _predicate_trial(records_dir: Path) -> Recomputed | None:
    """The predicate trial, reshaped from the trial gate's own verdict.

    **Not recomputable from run records.**  The decisive-pass counts come from
    an observer that watches each predicate evaluation of the frozen run and
    reads it again on the mixed ruler while the run happens; nothing in a
    record afterwards reconstructs them.  What this recomputes is the table's
    *shaping* out of the same verdict the tally read, so the comparison over
    these rows checks the table and not the measurement, and the verdict says
    so.
    """
    path = Path(records_dir) / PREDICATE_TRIAL_VERDICT
    if not path.exists():
        return None
    verdict = json.loads(path.read_text())
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
    return Recomputed(
        name="the predicate trial — frozen against mixed",
        caption=(
            "units: counts of predicate evaluations; the audit columns are hex "
            "floats of the largest scaled residual.  A row is one pair of runs "
            "— the same arm, configuration and seed under each ruler.  A column "
            "is a count of the trial, or one run's exit audit read on one named "
            "ruler.  Population: "
            + str(verdict.get("population") or "the predicate-trial gate's runs")
            + ".  Construction: **read from the trial gate's verdict, not from "
            "run records** — the decisive-pass counts come from an observer "
            "that watches the run's own predicate evaluations and cannot be "
            "reconstructed from a record afterwards, so this recomputation "
            "checks the table's shaping and not the measurement.  Decisive "
            "passes are two counts, never one: crossings, and the verdict "
            "changes that alone can make two runs differ."
        ),
        columns=(
            "configuration", "arm", "seed", "evaluations", "crossings",
            "verdict_changes", "identical", "audit_frozen_run_frozen_ruler",
            "audit_frozen_run_mixed_ruler", "audit_mixed_run_frozen_ruler",
            "audit_mixed_run_mixed_ruler",
        ),
        key_columns=("configuration", "arm", "seed"),
        rows=tuple(rows),
        denominator=len(rows),
        denominator_is="pairs of runs, one per ruler",
        composite=("identical",),
        from_records=False,
    )


# --------------------------------------------------------------------------
# the optimisation phase's tables
# --------------------------------------------------------------------------


def _seed_set(
    population: Population,
    configuration: str,
    index: Mapping[str, Mapping[int, Mapping[str, Any]]],
    source: str,
) -> tuple[Recomputed, list[int]]:
    """The one population per configuration, and how many seeds retried."""
    seeds = sorted({seed for rows in index.values() for seed in rows})
    converged = every_arm_converged(index, seeds)
    invalid = configuration_invalid(index, seeds)
    row = {
        "arms": len(index),
        "arm_names": " · ".join(arm_order(index)),
        "seeds_offered": len(seeds),
        "n": len(converged),
        "seeds": _join_seeds(converged),
        "configuration_invalid": len(invalid),
        "retried": " · ".join(
            f"{arm} {len(retried_seeds(index[arm]))}" for arm in arm_order(index)
        ),
    }
    return (
        Recomputed(
            name=f"the seed set — {configuration} — {source}",
            caption=(
                f"units: counts of seeds.  A row is this configuration.  A "
                f"column is the size of the one population every "
                f"optimisation-phase table on this configuration is over, or a "
                f"per-arm count of the seeds on which the optimiser was called "
                f"more than once.  Population: {population.what}; the arms here "
                f"are {', '.join(arm_order(index))} at seeds "
                f"{_join_seeds(seeds)}.  Construction: a seed is in the set when "
                f"every arm present reached an accepted optimum (status ok AND "
                f"the output file's ifail == 1); the retried count is computed "
                f"from attempts[] and never from a stored flag.  This is one "
                f"seed-complete arm group of the source — the plan's "
                f"construction assumes every arm at every seed, which a gate's "
                f"runs do not guarantee.  The seeds outside the set are the "
                f"failure table, published beside."
            ),
            columns=(
                "arms", "arm_names", "seeds_offered", "n", "seeds",
                "configuration_invalid", "retried",
            ),
            key_columns=("arm_names",),
            rows=(row,),
            denominator=len(seeds),
            denominator_is=f"distinct seeds run on {configuration}",
            composite=("arm_names", "seeds", "retried"),
        ),
        converged,
    )


def _failure_table(
    population: Population,
    configuration: str,
    index: Mapping[str, Mapping[int, Mapping[str, Any]]],
    converged: Sequence[int],
    source: str,
) -> Recomputed:
    """Every seed outside the set, with its cost beside the other arms'."""
    seeds = sorted({seed for rows in index.values() for seed in rows})
    outside = [s for s in seeds if s not in set(converged)]
    order = arm_order(index)
    rows: list[dict[str, Any]] = []
    for seed in outside:
        failed = [
            arm for arm in order
            if seed in index[arm] and not at_an_accepted_optimum(index[arm][seed])
        ]
        absent = [arm for arm in order if seed not in index[arm]]
        rows.append(
            {
                "seed": seed,
                "failed": ", ".join(failed) or "—",
                "not_run": ", ".join(absent) or "—",
                "ifail": ", ".join(
                    str((index[arm][seed].get("mfile") or {}).get("ifail"))
                    for arm in failed
                ) or "—",
                "attempts": ", ".join(
                    str(attempt_count(index[arm][seed])) for arm in failed
                ) or "—",
                "failed_cost": ", ".join(
                    str(index[arm][seed].get("node_calls_solve_phase"))
                    for arm in failed
                ) or "—",
                "other_cost": " / ".join(
                    f"{arm} "
                    + (
                        str(index[arm][seed].get("node_calls_solve_phase"))
                        if seed in index[arm] and arm not in failed
                        else "—"
                    )
                    for arm in order
                ),
                "configuration_invalid": (
                    "yes" if len(failed) + len(absent) == len(order) else "no"
                ),
            }
        )
    return Recomputed(
        name=f"the failure table — {configuration} — {source}",
        caption=(
            f"units: counts — model executions for the cost columns, optimiser "
            f"exit codes for ifail.  A row is one seed outside the converged "
            f"set.  A column is which arm failed there, how it failed, what it "
            f"cost, and what the other arms cost at the same start.  "
            f"Population: {population.what}; {len(outside)} of {len(seeds)} "
            f"seed(s) on {configuration} lie outside the every-arm-converged "
            f"set.  Construction: membership by accepted optimum; the cost "
            f"column is node_calls_solve_phase, the same unit the cost table "
            f"uses.  An arm the gate did not run at a seed reads *not run* "
            f"rather than *failed*."
        ),
        columns=(
            "seed", "failed", "not_run", "ifail", "attempts", "failed_cost",
            "other_cost", "configuration_invalid",
        ),
        key_columns=("seed",),
        rows=tuple(rows),
        denominator=len(seeds),
        denominator_is=f"distinct seeds run on {configuration}",
        composite=(
            "failed", "not_run", "ifail", "attempts", "failed_cost",
            "other_cost", "configuration_invalid",
        ),
    )


def _same_optimum(
    campaign: Campaign,
    population: Population,
    configuration: str,
    index: Mapping[str, Mapping[int, Mapping[str, Any]]],
    converged: Sequence[int],
    source: str,
) -> Recomputed | None:
    """Check 1 — is it the same optimum?

    ``None`` where this arm group carries no flat control: every pair of this
    check is anchored on it, and a table over no comparison would state a
    denominator for nothing.
    """
    if BASE_ARM not in index:
        return None
    pairs: list[tuple[str, str]] = []
    if all(a in index for a in YARDSTICK_PAIR):
        pairs.append(YARDSTICK_PAIR)
    for arm in arm_order(index):
        if arm != BASE_ARM and arm not in YARDSTICK_PAIR:
            pairs.append((BASE_ARM, arm))
    accepted: list[tuple[str, int, float]] = []
    for arm, rows in index.items():
        for seed, record in rows.items():
            if at_an_accepted_optimum(record):
                value = _hex_float((record.get("exact") or {}).get("norm_objf"))
                if value is not None:
                    accepted.append((arm, seed, value))
    gap = campaign.cluster_gap_factor * campaign.objf_floor_rel
    cluster_of: dict[tuple[str, int], int] = {}
    for number, group in enumerate(
        objective_clusters([v for _, _, v in accepted], gap=gap)
    ):
        for position in group:
            arm, seed, _ = accepted[position]
            cluster_of[(arm, seed)] = number

    def gaps(a: str, b: str) -> tuple[list[float], list[int]]:
        values: list[float] = []
        seeds: list[int] = []
        for seed in converged:
            left, right = index.get(a, {}).get(seed), index.get(b, {}).get(seed)
            if not (left and right):
                continue
            fa = _hex_float((left.get("exact") or {}).get("norm_objf"))
            fb = _hex_float((right.get("exact") or {}).get("norm_objf"))
            if fa is None or fb is None:
                continue
            values.append(relative_objective_gap(fa, fb))
            seeds.append(seed)
        return values, seeds

    yardstick_values = (
        gaps(*YARDSTICK_PAIR)[0] if all(a in index for a in YARDSTICK_PAIR) else []
    )
    yard_median, yard_p90 = middle(yardstick_values), ninetieth(yardstick_values)
    rows: list[dict[str, Any]] = []
    for a, b in pairs:
        values, seeds = gaps(a, b)
        is_yardstick = (a, b) == YARDSTICK_PAIR
        limit_median = None if is_yardstick else threshold_at(
            yard_median, factor=campaign.similarity_factor,
            floor=campaign.objf_floor_rel,
        )
        limit_p90 = None if is_yardstick else threshold_at(
            yard_p90, factor=campaign.similarity_factor,
            floor=campaign.objf_floor_rel,
        )
        observed_median, observed_p90 = middle(values), ninetieth(values)
        verdict = "—"
        if limit_median is not None and observed_median is not None:
            passed = observed_median <= limit_median and (
                observed_p90 is None or limit_p90 is None or observed_p90 <= limit_p90
            )
            verdict = "PASS" if passed else "FAIL"
        hop = hop_rate(cluster_of, [((a, s), (b, s)) for s in seeds])
        rows.append(
            {
                "pair": f"{a} → {b}" + (" (yardstick)" if is_yardstick else ""),
                "n": len(values),
                "r_median": observed_median,
                "r_p90": observed_p90,
                "threshold_median": limit_median,
                "threshold_p90": limit_p90,
                "verdict": verdict,
                "hops": f"{hop['n_hops']}/{hop['n_pairs']}"
                + (f" ({hop['rate']:.2f})" if hop["rate"] is not None else ""),
                "below_resolution": below_resolution(
                    values, floor=campaign.objf_floor_rel, gap=gap
                ),
                "retried_in_pair": sum(
                    1 for s in seeds
                    if was_retried(index[a][s]) or was_retried(index[b][s])
                ),
            }
        )
    return Recomputed(
        name=f"same optimum (check 1) — {configuration} — {source}",
        caption=(
            f"units: dimensionless — a relative difference of the normalised "
            f"objective.  A row is one arm pair over the seed set.  A column is "
            f"the paired relative objective difference's median and p90, the "
            f"threshold they are judged against, and the clustering statistics. "
            f" Population: {population.what}; {len(converged)} seed(s) on which "
            f"every arm of {configuration} reached an accepted optimum.  "
            f"Construction: |Δ norm_objf| / max(|a|, |b|) per pair from the hex "
            f"floats; median nearest-rank upper-middle, p90 nearest-rank "
            f"ceil(0.9 n); threshold = max(F × yardstick, floor) with F = "
            f"{campaign.similarity_factor:g} and floor = "
            f"{campaign.objf_floor_rel:g}, the yardstick being the "
            f"{YARDSTICK_PAIR[0]} → {YARDSTICK_PAIR[1]} spread in this same "
            f"population; clusters at a relative gap of {gap:g}.  The yardstick "
            f"row carries no threshold and no verdict: it *is* the "
            f"calibration.  *Below resolution* is a named category — distinct "
            f"optima closer than the cluster gap and further apart than the "
            f"correctness floor.  The retried column is computed from "
            f"attempts[], never from a stored flag."
        ),
        columns=(
            "pair", "n", "r_median", "r_p90", "threshold_median",
            "threshold_p90", "verdict", "hops", "below_resolution",
            "retried_in_pair",
        ),
        key_columns=("pair",),
        rows=tuple(rows),
        denominator=len(converged),
        denominator_is=f"seeds on which every arm of {configuration} converged",
        composite=("pair", "verdict", "hops"),
    )


def _hex_float(value: Any) -> float | None:
    """A hex float as a number.  What a bit-comparison compares."""
    return float.fromhex(value) if isinstance(value, str) else None


def _iteration_multiplier(
    campaign: Campaign,
    population: Population,
    configuration: str,
    index: Mapping[str, Mapping[int, Mapping[str, Any]]],
    converged: Sequence[int],
    source: str,
) -> Recomputed | None:
    """Check 2 — the iteration multiplier, in **both** declared constructions.

    The acceptance statistic is the **summed** median; the final attempt's is
    published beside it for comparability with the previous revision.  Both sit
    beside the evaluation count, which is the multiplier the transfer needs and
    which neither iteration construction captures.
    """
    if BASE_ARM not in index:
        return None
    rows: list[dict[str, Any]] = []
    for arm in arm_order(index):
        if arm == BASE_ARM:
            continue
        seeds = [s for s in converged if s in index[arm] and s in index[BASE_ARM]]
        final_ratios: list[float] = []
        summed_ratios: list[float] = []
        evaluation_ratios: list[float] = []
        final_totals = [0, 0]
        summed_totals = [0, 0]
        disagreements = 0
        for seed in seeds:
            base_record, arm_record = index[BASE_ARM][seed], index[arm][seed]
            fa = iterations_of_the_final_attempt(base_record)
            fb = iterations_of_the_final_attempt(arm_record)
            sa = iterations_summed(base_record)
            sb = iterations_summed(arm_record)
            if fa and fb:
                final_ratios.append(fb / fa)
                final_totals[0] += fa
                final_totals[1] += fb
            if sa and sb:
                summed_ratios.append(sb / sa)
                summed_totals[0] += sa
                summed_totals[1] += sb
            if (fa, fb) != (sa, sb):
                disagreements += 1
            ea, eb = base_record.get("n_model_calls"), arm_record.get("n_model_calls")
            if ea and eb:
                evaluation_ratios.append(eb / ea)
        summed_median = middle(summed_ratios)
        accepted_on = arm in ACCEPTANCE_PAIRS
        rows.append(
            {
                "pair": f"{BASE_ARM} → {arm}" + ("" if accepted_on else " (beside)"),
                "n": len(seeds),
                "summed_median": summed_median,
                "summed_sum_ratio": (
                    (summed_totals[1] / summed_totals[0]) if summed_totals[0] else None
                ),
                "acceptance": (
                    "beside" if not accepted_on
                    else ("—" if summed_median is None
                          else ("PASS" if summed_median <= campaign.iteration_ratio_max
                                else "FAIL"))
                ),
                "final_median": middle(final_ratios),
                "final_sum_ratio": (
                    (final_totals[1] / final_totals[0]) if final_totals[0] else None
                ),
                "evaluations_median": middle(evaluation_ratios),
                "attempts": ", ".join(
                    f"{seed}:{attempt_count(index[BASE_ARM][seed])}/"
                    f"{attempt_count(index[arm][seed])}"
                    for seed in seeds
                ) or "—",
                "constructions_disagree": disagreements,
            }
        )
    return Recomputed(
        name=f"iteration multiplier (check 2) — {configuration} — {source}",
        caption=(
            f"units: dimensionless ratios of counts.  A row is one arm against "
            f"the flat control over the seed set.  A column is one of check 2's "
            f"two iteration constructions, its sum ratio, or the "
            f"evaluation-count ratio beside them.  Population: "
            f"{population.what}; {len(converged)} seed(s) on which every arm of "
            f"{configuration} reached an accepted optimum.  Construction: "
            f"iterations summed over attempts[] is the declared acceptance "
            f"statistic, nearest-rank upper-middle median against "
            f"{campaign.iteration_ratio_max:g}; the final attempt's count is "
            f"the previous revision's construction, published beside.  Both are "
            f"read from attempts[], so a disagreement between them is a "
            f"disagreement about that list.  The sum ratio is beside every "
            f"median because the two can point in opposite directions."
        ),
        columns=(
            "pair", "n", "summed_median", "summed_sum_ratio", "acceptance",
            "final_median", "final_sum_ratio", "evaluations_median",
            "attempts", "constructions_disagree",
        ),
        key_columns=("pair",),
        rows=tuple(rows),
        denominator=len(converged),
        denominator_is=f"seeds on which every arm of {configuration} converged",
        composite=("pair", "acceptance", "attempts"),
    )


def _attempt_identity(
    population: Population,
    configuration: str,
    index: Mapping[str, Mapping[int, Mapping[str, Any]]],
    source: str,
) -> Recomputed:
    """The summation identity, **printed** rather than assumed."""
    rows: list[dict[str, Any]] = []
    for arm in arm_order(index):
        for seed in sorted(index[arm]):
            record = index[arm][seed]
            identity = summation_identity(record)
            parts = identity.get("parts") or {}
            node = parts.get("node_calls_solve_phase") or {}
            sweeps = parts.get("sweeps") or {}
            rows.append(
                {
                    "arm": arm,
                    "seed": seed,
                    "attempts": identity.get("n_attempts", 0),
                    "retried": "yes" if was_retried(record) else "no",
                    "node_per_attempt": (
                        " + ".join(str(v) for v in node.get("per_attempt") or []) or "—"
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
                        "—" if identity.get("decomposes") is None
                        else ("yes" if identity["decomposes"] else "NO")
                    ),
                }
            )
    checked = [r for r in rows if r["decomposes"] in ("yes", "NO")]
    return Recomputed(
        name=f"the attempt summation identity — {configuration} — {source}",
        caption=(
            f"units: counts — model executions and sweeps of the model "
            f"sequence.  A row is one optimisation run.  A column is the "
            f"per-attempt costs, the run's solve-phase total they decompose, "
            f"and the residual between them.  Population: {population.what}; "
            f"{len(rows)} optimisation run(s) of {configuration}, of which "
            f"{len(checked)} carry a per-attempt cost the identity can be "
            f"checked on.  Construction: Σ over attempts[] against "
            f"node_calls_solve_phase and dispatch_sweeps_solve_phase.  This "
            f"identity is why the with- and without-retried-seeds cost ratios "
            f"may be published: they are over quantities that visibly "
            f"decompose the published total."
        ),
        columns=(
            "arm", "seed", "attempts", "retried", "node_per_attempt",
            "node_total", "node_residual", "sweeps_per_attempt",
            "sweeps_total", "sweeps_residual", "decomposes",
        ),
        key_columns=("arm", "seed"),
        rows=tuple(rows),
        denominator=len(rows),
        denominator_is=f"optimisation-phase gate runs of {configuration}",
        composite=(
            "retried", "node_per_attempt", "sweeps_per_attempt", "decomposes",
        ),
    )


def _cost(
    population: Population,
    configuration: str,
    index: Mapping[str, Mapping[int, Mapping[str, Any]]],
    converged: Sequence[int],
    source: str,
) -> Recomputed | None:
    """Check 4 — the cost, with and without the retried seeds."""
    if BASE_ARM not in index:
        return None
    rows: list[dict[str, Any]] = []
    for arm in arm_order(index):
        both = cost_with_and_without_retried(index[BASE_ARM], index[arm], converged)
        finished = [
            index[arm][s] for s in converged
            if s in index[arm] and completed(index[arm][s])
        ]
        calls = [r.get("node_calls_solve_phase") for r in finished]
        bracket = extremes([c for c in calls if c is not None])
        rows.append(
            {
                "arm": arm,
                "n": both["with_retried"]["n"],
                "node_calls_mean": (
                    sum(c for c in calls if c is not None) / len(calls)
                    if calls else None
                ),
                "bracket": (
                    "—" if bracket is None else f"[{bracket[0]:g}, {bracket[1]:g}]"
                ),
                "arrangement_method_calls": sum(
                    (r.get("n_arrangement_method_calls") or 0) for r in finished
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
    return Recomputed(
        name=f"cost (check 4) — {configuration} — {source}",
        caption=(
            f"units: model executions during the solve; ratios dimensionless.  "
            f"A row is one arm over the seed set.  A column is an absolute "
            f"per-run mean with its bracket, or one reading of the ratio "
            f"against the flat control.  Population: {population.what}; "
            f"{len(converged)} seed(s) on which every arm of {configuration} "
            f"reached an accepted optimum.  Construction: solve-phase node "
            f"calls **summed over attempts[]** per run, so the ratio is over "
            f"the quantity the attempts decompose; pooled = Σ arm / Σ base, "
            f"median nearest-rank upper-middle of the per-seed ratios, worse = "
            f"seeds on which the arm cost more.  Retries are a term, not a "
            f"footnote: the ratio is published with and without the retried "
            f"seeds, and a seed counts as retried when **either** side of the "
            f"pair retried.  The arrangement-method calls are a column of their "
            f"own and are never pooled into the node calls."
        ),
        columns=(
            "arm", "n", "node_calls_mean", "bracket",
            "arrangement_method_calls", "with_pooled", "with_median",
            "with_worse", "n_retried", "without_pooled", "without_median",
            "without_n",
        ),
        key_columns=("arm",),
        rows=tuple(rows),
        denominator=len(converged),
        denominator_is=f"seeds on which every arm of {configuration} converged",
        composite=("bracket",),
    )


def _achieved_accuracy(
    campaign: Campaign,
    population: Population,
    configuration: str,
    index: Mapping[str, Mapping[int, Mapping[str, Any]]],
    source: str,
) -> Recomputed:
    """The exit audit at the accepted optimum, on both rulers, with its position.

    A campaign-shaped optimisation record is audited at the **entry to the
    output path** — the state the solve handed over — and the reproduction
    gate's records are audited **after the run**, where the previous revision
    measured.  Those are two different quantities and share this table only
    because the position is a column of its own.
    """
    grouped = {
        arm: [index[arm][seed] for seed in sorted(index[arm])]
        for arm in arm_order(index)
    }
    rows, _ = _accuracy_rows(campaign, grouped, optimisation=True)
    positions = sorted({r["audit_position"] for r in rows if r["audit_position"]})
    return Recomputed(
        name=f"achieved accuracy at the accepted optimum — {configuration} — {source}",
        caption=(
            f"units: dimensionless — the largest scaled coupling-state residual "
            f"found by one further full sweep past termination.  A row is one "
            f"arm on one ruler.  A column is the restricted or whole-state "
            f"audit maximum over that arm's finished runs, the component the "
            f"restricted maximum sat on, and how many components the "
            f"restriction removed.  Population: {population.what}; the finished "
            f"optimisation-phase runs of {configuration} in this arm group.  "
            f"Construction: median nearest-rank upper-middle; the restricted "
            f"maximum excludes the components the configuration's once-per-run "
            f"deferred nodes write.  Audit position: "
            f"{', '.join(positions) if positions else 'not recorded on any run here'}"
            f".  The audit instrument's version is **read from the record**: "
            f"task A62 (exit-audit-restore) widens the snapshot to the whole "
            f"data structure under decision D25, which moves every value in "
            f"these columns, and this column is what tells two otherwise "
            f"identical tables apart.  Both rulers or neither."
        ),
        columns=(
            "arm", "ruler", "n", "restricted_median", "restricted_max",
            "argmax", "n_above_tau", "whole_median", "n_excluded",
            "audit_position", "instrument",
        ),
        key_columns=("arm", "ruler"),
        rows=tuple(rows),
        denominator=sum(len(v) for v in index.values()),
        denominator_is=(
            f"optimisation-phase runs of {configuration} in this arm group"
        ),
        composite=("argmax", "n_above_tau", "n_excluded", "instrument"),
    )


def _lift_closed(
    population: Population,
    configuration: str,
    index: Mapping[str, Mapping[int, Mapping[str, Any]]],
    source: str,
) -> Recomputed | None:
    """Check 3 — the burn-time consistency residual at every accepted optimum."""
    rows: list[dict[str, Any]] = []
    for arm in arm_order(index):
        accepted = [
            record
            for seed, record in sorted(index[arm].items())
            if at_an_accepted_optimum(record) and record.get("constraint_93")
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
        bracket = extremes(residuals)
        rows.append(
            {
                "arm": arm,
                "n": len(accepted),
                "residual_s_median": middle(residuals),
                "bracket": (
                    "—" if bracket is None
                    else f"[{bracket[0]:.3e}, {bracket[1]:.3e}]"
                ),
                "relative_median": middle(relatives),
                "in_equality_block": ", ".join(
                    sorted({str(r["constraint_93"].get("is_in_equality_block"))
                            for r in accepted})
                ),
            }
        )
    if not rows:
        return None
    return Recomputed(
        name=f"the lift closed (check 3) — {configuration} — {source}",
        caption=(
            f"units: seconds for the residual; the relative column is "
            f"dimensionless (residual / burn time).  A row is one arm whose "
            f"runs name the burn-time consistency constraint.  A column is the "
            f"residual of that constraint at the accepted optima.  Population: "
            f"{population.what}; the accepted optima of {configuration} whose "
            f"input file names the constraint.  Construction: the model's own "
            f"extracted consistency relation evaluated on the returned state, "
            f"|value|, median nearest-rank upper-middle.  An arm whose input "
            f"file does not name the constraint is absent from this table "
            f"rather than reading 0; residuals at unconverged exits are never "
            f"pooled with these."
        ),
        columns=(
            "arm", "n", "residual_s_median", "bracket", "relative_median",
            "in_equality_block",
        ),
        key_columns=("arm",),
        rows=tuple(rows),
        denominator=sum(len(v) for v in index.values()),
        denominator_is=f"optimisation-phase gate runs of {configuration}",
        composite=("bracket", "in_equality_block"),
    )


# --------------------------------------------------------------------------
# the whole recomputation
# --------------------------------------------------------------------------


def recompute(campaign: Campaign) -> dict[str, Any]:
    """Every table the experiment plan's §4 asks for, recomputed from records.

    One set per declared source, the optimisation phase split again into
    seed-complete arm groups.  Returns the tables by name, the populations they
    are over and the similarity verdicts, so the caller can compare any of them
    against the tally's own output.
    """
    records_dir = Path(campaign.runs_dir) / "gates"
    produced: dict[str, Recomputed] = {}
    populations: list[dict[str, Any]] = []
    verdicts: list[dict[str, Any]] = []
    seed_sets: dict[str, list[int]] = {}
    not_produced: list[str] = []
    for source in SOURCES:
        records = source_records(campaign, source)
        for phase in ("A", "B"):
            if phase not in source.phases:
                continue
            population = Population.of(
                [r for r in records if r.get("campaign_phase") == phase],
                what=f"{source.name} — {source.what}",
            )
            population.assert_no_demonstration()
            populations.append(
                {
                    "source": source.name,
                    "phase": phase,
                    "subpath": source.subpath,
                    "n_records": len(population),
                    "n_excluded_as_demonstrations": len(population.excluded),
                }
            )
            if not len(population):
                continue
            if phase == "A":
                for config in campaign.configurations:
                    if not by_arm(population, config.name):
                        continue
                    table = _cost_per_call(
                        campaign, population, config.name, source.name
                    )
                    produced[table.name] = table
                    accuracy, pairs = _matched_accuracy(
                        campaign, population, config.name, source.name
                    )
                    produced[accuracy.name] = accuracy
                    verdicts.extend(
                        {"source": source.name, **v} for v in pairs
                    )
                    rung = _ownership_rung(
                        campaign, population, config.name, source.name
                    )
                    if rung is not None:
                        produced[rung.name] = rung
                    overhead = _per_sweep_overhead(
                        population, config.name, source.name,
                        records_by_arm=by_arm(population, config.name),
                        optimisation=False,
                    )
                    produced[overhead.name] = overhead
                    taxonomy_table = _failure_taxonomy(
                        population, config.name, source.name
                    )
                    produced[taxonomy_table.name] = taxonomy_table
            else:
                for config in campaign.configurations:
                    whole = by_arm_and_seed(population, config.name)
                    if not whole:
                        continue
                    for arms, seeds in seed_complete_arm_groups(whole):
                        label = f"{source.name} · {'·'.join(arms)}"
                        index = restricted_index(whole, arms, seeds)
                        table, converged = _seed_set(
                            population, config.name, index, label
                        )
                        produced[table.name] = table
                        seed_sets[f"{label}/{config.name}"] = converged
                        failures = _failure_table(
                            population, config.name, index, converged, label
                        )
                        produced[failures.name] = failures
                        for built in (
                            _same_optimum(campaign, population, config.name,
                                          index, converged, label),
                            _iteration_multiplier(campaign, population,
                                                  config.name, index,
                                                  converged, label),
                            _cost(population, config.name, index, converged,
                                  label),
                        ):
                            if built is None:
                                not_produced.append(
                                    f"{config.name} — {label}: a check anchored "
                                    f"on {BASE_ARM}, which this arm group does "
                                    f"not carry"
                                )
                            else:
                                produced[built.name] = built
                        identity = _attempt_identity(
                            population, config.name, index, label
                        )
                        produced[identity.name] = identity
                        accuracy = _achieved_accuracy(
                            campaign, population, config.name, index, label
                        )
                        produced[accuracy.name] = accuracy
                        lift = _lift_closed(population, config.name, index, label)
                        if lift is not None:
                            produced[lift.name] = lift
                        overhead = _per_sweep_overhead(
                            population, config.name, label,
                            records_by_arm={
                                arm: [index[arm][s] for s in sorted(index[arm])]
                                for arm in arm_order(index)
                            },
                            optimisation=True,
                        )
                        produced[overhead.name] = overhead
    trial = _predicate_trial(records_dir)
    if trial is not None:
        produced[trial.name] = trial
    return {
        "tables": produced,
        "populations": populations,
        "similarity_verdicts": verdicts,
        "seed_sets": seed_sets,
        "tables_not_produced": not_produced,
    }


# --------------------------------------------------------------------------
# the comparison
# --------------------------------------------------------------------------


def _same(a: Any, b: Any) -> bool:
    """Cell equality: exact, with NaN equal to NaN.

    No tolerance anywhere.  Two implementations of one declared construction
    over one set of records land on the same number or they do not agree, and a
    tolerance here would be a place for a drift to hide.
    """
    if isinstance(a, float) and isinstance(b, float):
        if math.isnan(a) and math.isnan(b):
            return True
    if isinstance(a, bool) != isinstance(b, bool):
        return False
    return a == b


def read_tally_output(records_dir: Path) -> dict[str, Any]:
    """The tally's emitted tables, by name, from the two stage records.

    Read from disk, never recomputed by importing the tally: the point of the
    second implementation is that it cannot agree by construction.
    """
    tables: dict[str, Mapping[str, Any]] = {}
    stages: list[dict[str, Any]] = []
    for stage in TALLY_STAGES:
        path = Path(records_dir) / stage / "measurements.json"
        if not path.exists():
            raise AnalysisError(
                f"the tally stage record {path} does not exist, so there is "
                f"nothing to verify against.  Run `experiment_runner.py "
                f"--measure {stage}` first; --verify compares against the "
                f"tally's output and never against its code, so the output has "
                f"to be on disk."
            )
        block = json.loads(path.read_text())
        for table in block.get("tables") or []:
            tables[table["table"]] = table
        stages.append(
            {
                "stage": stage,
                "record": str(path),
                "phase": block.get("phase"),
                "n_tables": block.get("n_tables"),
                "population": block.get("population"),
                "sources": [
                    {"source": s.get("source"), "n_records": s.get("n_records")}
                    for s in block.get("sources") or []
                ],
                "runs_provenance": block.get("runs_provenance"),
            }
        )
    return {"tables": tables, "stages": stages}


def compare(
    mine: Mapping[str, Recomputed], theirs: Mapping[str, Mapping[str, Any]]
) -> dict[str, Any]:
    """Every published cell, this implementation's against the tally's.

    A table one side emits and the other does not is a mismatch of its own, not
    one fewer comparison; so is a row key present on one side only, and so is a
    column list that differs.  The cell counts are split into **numeric** cells
    — the constructions — and **composite** cells, which are strings a table
    composes out of several values: agreement on a rendered string is weaker
    evidence than agreement on a computed quantity, so the two denominators are
    reported apart rather than added into one number.
    """
    mismatches: list[str] = []
    n_cells = 0
    n_numeric = 0
    n_composite = 0
    n_rows = 0
    only_mine = sorted(set(mine) - set(theirs))
    only_theirs = sorted(set(theirs) - set(mine))
    for name in only_theirs:
        mismatches.append(
            f"TABLE ONLY IN THE TALLY: {name!r} — the analysis does not "
            f"produce it, so its cells are unverified"
        )
    for name in only_mine:
        mismatches.append(
            f"TABLE ONLY IN THE ANALYSIS: {name!r} — the tally did not publish "
            f"it, so the two implementations disagree about what is a table"
        )
    per_table: list[dict[str, Any]] = []
    for name in sorted(set(mine) & set(theirs)):
        recomputed, published = mine[name], theirs[name]
        table_mismatches = 0
        their_columns = [c["key"] for c in published.get("columns") or []]
        if list(recomputed.columns) != their_columns:
            table_mismatches += 1
            mismatches.append(
                f"{name}: columns differ — the analysis has "
                f"{list(recomputed.columns)}, the tally has {their_columns}"
            )
        n_cells += 1
        n_numeric += 1
        if not _same(recomputed.denominator, published.get("denominator")):
            table_mismatches += 1
            mismatches.append(
                f"{name}: denominator — the analysis computes "
                f"{recomputed.denominator!r}, the tally published "
                f"{published.get('denominator')!r}"
            )
        theirs_rows: dict[tuple[Any, ...], Mapping[str, Any]] = {}
        for row in published.get("rows") or []:
            theirs_rows[recomputed.key(row)] = row
        mine_rows = {recomputed.key(row): row for row in recomputed.rows}
        for key in sorted(set(theirs_rows) - set(mine_rows), key=repr):
            table_mismatches += 1
            mismatches.append(f"{name}: row {key!r} is in the tally and not here")
        for key in sorted(set(mine_rows) - set(theirs_rows), key=repr):
            table_mismatches += 1
            mismatches.append(f"{name}: row {key!r} is here and not in the tally")
        for key in sorted(set(mine_rows) & set(theirs_rows), key=repr):
            n_rows += 1
            for column in recomputed.columns:
                if column not in their_columns:
                    continue
                n_cells += 1
                if column in recomputed.composite:
                    n_composite += 1
                else:
                    n_numeric += 1
                found = mine_rows[key].get(column)
                expected = theirs_rows[key].get(column)
                if not _same(found, expected):
                    table_mismatches += 1
                    mismatches.append(
                        f"{name}: row {key!r} column {column!r} — the analysis "
                        f"computes {found!r}, the tally published {expected!r}"
                    )
        per_table.append(
            {
                "table": name,
                "n_rows": len(mine_rows),
                "n_columns": len(recomputed.columns),
                "n_mismatched": table_mismatches,
                "recomputed_from_run_records": recomputed.from_records,
            }
        )
    return {
        "n_tables_compared": len(set(mine) & set(theirs)),
        "n_tables_only_in_the_analysis": len(only_mine),
        "n_tables_only_in_the_tally": len(only_theirs),
        "n_rows_compared": n_rows,
        "n_cells_compared": n_cells,
        "n_cells_from_a_construction": n_numeric,
        "n_cells_composed_as_a_string": n_composite,
        "n_mismatched": len(mismatches),
        "mismatches": mismatches,
        "per_table": per_table,
    }


# --------------------------------------------------------------------------
# the criterion
# --------------------------------------------------------------------------


#: Modules this one may not import, because importing any of them would make
#: the recomputation agree with the tally **by construction** and prove
#: nothing.  ``stats`` holds the constructions, the two ``tally`` modules hold
#: the table builders, and ``tables`` holds the emission rules — all three are
#: the things a second implementation exists to disagree with.
FORBIDDEN_IMPORTS: tuple[str, ...] = (
    "harness.stats",
    "harness.tally",
    "harness.tally_evaluation",
    "harness.tally_optimisation",
    "harness.tables",
)


def imports_of(source: str) -> list[str]:
    """Every module *source* imports, by dotted name, read from its syntax.

    Read from the parsed source rather than from ``sys.modules`` so that an
    import inside a function body — the shape the rest of this package uses to
    break cycles — is seen too.
    """
    import ast  # noqa: PLC0415 - used only by this check

    found: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            found.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.append(node.module)
            found.extend(f"{node.module}.{alias.name}" for alias in node.names)
    return sorted(set(found))


def forbidden_imports(source: str) -> list[str]:
    """The tally modules *source* imports, which must be none.

    The independence this whole module rests on, stated as a measurement rather
    than as a comment: an analysis that imported a construction would agree with
    the tally by construction, and the two drifts this gate exists to catch
    (I-18, I-19) would both have passed it.
    """
    return [
        name
        for name in imports_of(source)
        if any(
            name == forbidden or name.startswith(forbidden + ".")
            for forbidden in FORBIDDEN_IMPORTS
        )
    ]


def assert_one_commit(provenance: Mapping[str, Any], *, resume: bool) -> str | None:
    """Refuse a population straddling two commits unless ``--resume`` asked.

    Returns the sentence to print where the straddle is allowed, and raises
    where it is not.  Without ``--resume`` every run is re-made, so a record
    from another commit means one was kept that should not have been — and a
    recomputation over it is a set of numbers over a population that is not the
    one the stage names.
    """
    here = framework.git_head()
    heads = list(provenance.get("heads") or [])
    if not provenance.get("n_records", 0) or heads == [here]:
        return None
    if not resume:
        raise AnalysisError(
            f"the analysis read {provenance['n_records']} run record(s) made "
            f"at {heads} while this tree is at {here}, and --resume was not "
            f"asked for.  Without it every run is re-made, so a record from "
            f"another commit means one was kept that should not have been, and "
            f"the recomputation would be over a population that is not the one "
            f"it names."
        )
    return (
        f"the analysis read {provenance['n_records']} run record(s) made at "
        f"{heads}, not all at this tree's {here} — which is what --resume asks "
        f"for, and is stated here rather than assumed"
    )


def assert_not_empty(result: Mapping[str, Any]) -> None:
    """Refuse a comparison with nothing in it.

    A gate that cannot find what it compares must refuse, never pass over
    nothing (trap T11).  Zero mismatches over zero cells is not a result.
    """
    if not result.get("n_tables_compared") or not result.get("n_cells_compared"):
        raise AnalysisError(
            f"the comparison is empty: {result.get('n_tables_compared')} "
            f"table(s) and {result.get('n_cells_compared')} cell(s) on both "
            f"sides.  A gate that cannot find what it compares must refuse, "
            f"never pass over nothing (trap T11)."
        )


def verify(campaign: Campaign, *, resume: bool = False) -> framework.Check:
    """Every published cell, recomputed here and compared with the tally's.

    Four refusals, each of which is a way the comparison could pass over
    nothing:

    * an **empty comparison** — no table on either side, or no cell in the
      tables there are.  A gate that cannot find what it compares must refuse,
      never pass over nothing (trap T11);
    * a **budget-capped demonstration** in a population — a record made with the
      optimiser's budget deliberately cut is not a measurement and may not be
      summarised with measurements;
    * a **population straddling two commits** without ``--resume`` — without it
      every run is re-made, so a record from another commit means one was kept
      that should not have been;
    * a **population this implementation and the tally do not agree about** —
      reported as a finding, never reconciled silently.
    """
    check = framework.Check(
        name="recomputation",
        binds=(
            "every cell the tally publishes is reproduced by a second "
            "implementation that shares no construction with it"
        ),
    )
    records_dir = Path(campaign.runs_dir) / framework.GATES_SUBPATH

    provenance = framework.survey_heads(
        [Path(campaign.runs_dir) / source.subpath for source in SOURCES]
    )
    here = framework.git_head()
    heads = list(provenance.get("heads") or [])
    straddle = assert_one_commit(provenance, resume=resume)
    if straddle:
        check.note(straddle)
    check.note(
        f"runs read: {provenance['n_records']} record(s) at "
        f"{provenance['records_by_head']}"
    )

    own_source = Path(__file__).read_text()
    borrowed = forbidden_imports(own_source)
    if borrowed:
        check.fail(
            f"INDEPENDENCE: this module imports {borrowed} — a recomputation "
            f"that imports the tally's constructions agrees with it by "
            f"construction and proves nothing, which is exactly how the drifts "
            f"I-18 and I-19 went unnoticed"
        )
    else:
        check.note(
            f"independence: this module imports none of "
            f"{list(FORBIDDEN_IMPORTS)}; it reads the tally's output and "
            f"re-derives every construction from the declaration"
        )

    published = read_tally_output(records_dir)
    recomputed = recompute(campaign)
    result = compare(recomputed["tables"], published["tables"])

    # the populations, mine against the tally's own statement of them
    population_differences: list[str] = []
    theirs_by_source: dict[tuple[str, str], int] = {}
    for stage in published["stages"]:
        for source in stage["sources"]:
            theirs_by_source[(str(stage["phase"]), str(source["source"]))] = int(
                source["n_records"] or 0
            )
    for row in recomputed["populations"]:
        key = (str(row["phase"]), str(row["source"]))
        theirs = theirs_by_source.get(key)
        if theirs is None:
            population_differences.append(
                f"the analysis derives a population for phase {row['phase']} "
                f"source {row['source']!r} ({row['n_records']} record(s)) that "
                f"the tally's own record does not name"
            )
        elif theirs != row["n_records"]:
            population_differences.append(
                f"phase {row['phase']} source {row['source']!r}: the analysis "
                f"derives {row['n_records']} record(s), the tally states "
                f"{theirs}"
            )
    for key, count in theirs_by_source.items():
        if not any(
            (str(r["phase"]), str(r["source"])) == key
            for r in recomputed["populations"]
        ):
            population_differences.append(
                f"the tally names a population for phase {key[0]} source "
                f"{key[1]!r} ({count} record(s)) that the analysis does not "
                f"derive"
            )

    check.population = (
        f"{result['n_tables_compared']} table(s) emitted by the two tally "
        f"stages, recomputed cell by cell from "
        f"{provenance['n_records']} run record(s) under "
        f"{len(SOURCES)} declared source(s), plus this module's own import "
        f"list against the tally modules it may not borrow from"
    )
    # The cells, plus one for the independence check: an analysis that
    # borrowed a construction would agree with the tally by construction, so
    # "it did not borrow one" is a compared thing and belongs in the
    # denominator rather than in a sentence beside it.
    check.n_compared = result["n_cells_compared"] + 1

    assert_not_empty(result)

    check.note(
        f"{result['n_cells_compared']} cell(s) compared over "
        f"{result['n_rows_compared']} row(s) of "
        f"{result['n_tables_compared']} table(s): "
        f"{result['n_cells_from_a_construction']} from a construction and "
        f"{result['n_cells_composed_as_a_string']} composed as a string"
    )
    unverified = [
        row["table"] for row in result["per_table"]
        if not row["recomputed_from_run_records"]
    ]
    if unverified:
        check.note(
            "not recomputable from run records, and compared only as a "
            "reshaping of the same gate verdict the tally read: "
            + ", ".join(unverified)
        )
    for line in result["mismatches"]:
        check.fail(line)
    for line in population_differences:
        check.fail(f"POPULATION: {line}")
    if not population_differences:
        check.note(
            "the populations this implementation derives and the ones the "
            "tally states are the same, source by source and phase by phase"
        )

    for name, caught, message in run_teeth(
        campaign, published["tables"], recomputed["tables"]
    ):
        check.tooth(name, caught, message)

    check.detail.insert(
        0,
        f"commits of the records read: {heads or ['none']}; this tree is at "
        f"{here}",
    )
    return check


# --------------------------------------------------------------------------
# the teeth
# --------------------------------------------------------------------------


TEETH: tuple[str, ...] = (
    "a tally cell moved by one",
    "a construction altered in the analysis",
    "an empty comparison",
    "a demonstration record in a population",
    "a retried flag trusted from a stored field",
    "a population straddling two commits",
    "a construction imported from the tally",
)


def _a_numeric_cell(
    tables: Mapping[str, Mapping[str, Any]]
) -> tuple[str, int, str] | None:
    """The first integer cell in the tally's output, for a tooth to move."""
    for name in sorted(tables):
        for position, row in enumerate(tables[name].get("rows") or []):
            for column, value in row.items():
                if isinstance(value, int) and not isinstance(value, bool):
                    return name, position, column
    return None


def _tooth_a_moved_cell(
    campaign: Campaign,
    published: Mapping[str, Mapping[str, Any]],
    recomputed: Mapping[str, Recomputed],
) -> tuple[str, bool, str]:
    """Move one published cell by one and require the comparison to catch it.

    This half proves the comparison really reads the tally's output: a
    comparison that agreed with anything would agree with a moved cell too.
    """
    target = _a_numeric_cell(published)
    if target is None:
        return (
            TEETH[0],
            False,
            "the tally published no integer cell to move, so the tooth could "
            "not be constructed",
        )
    name, position, column = target
    doctored = dict(published)
    doctored[name] = {
        **published[name],
        "rows": [
            ({**row, column: row[column] + 1} if index == position else row)
            for index, row in enumerate(published[name]["rows"])
        ],
    }
    result = compare(recomputed, doctored)
    caught = result["n_mismatched"] > 0
    return (
        TEETH[0],
        caught,
        f"{name!r} row {position} column {column!r} moved by one: "
        + (
            f"the comparison reported {result['n_mismatched']} mismatch(es) — "
            + result["mismatches"][0]
            if caught
            else "the comparison reported none.  It must."
        ),
    )


def _tooth_a_wrong_denominator(
    campaign: Campaign,
    published: Mapping[str, Mapping[str, Any]],
    recomputed: Mapping[str, Recomputed],
) -> tuple[str, bool, str]:
    """Alter a construction **in the analysis** and require the tally to catch it.

    The other half of the moved cell: a doctored published cell proves the
    comparison reads the tally, and a doctored **construction** proves it reads
    the records through this module's own rules.  The alteration is a wrong
    denominator — the pooled ratio taken against Σ arm instead of Σ reference,
    which is precisely the shape of the drift issues I-18 and I-19 recorded —
    and it is applied by replacing this module's ratio function for the length
    of the tooth and restoring it afterwards, so that a whole recomputation
    really runs with the wrong rule rather than one cell being edited.
    """
    honest = ratio_three_ways

    def wrong(reference: Sequence[float], arm: Sequence[float]) -> dict[str, Any]:
        out = dict(honest(reference, arm))
        total_arm = sum(arm) if arm else 0
        out["pooled"] = (sum(reference) / total_arm) if total_arm else None
        return out

    globals()["ratio_three_ways"] = wrong
    try:
        result = compare(recompute(campaign)["tables"], published)
    finally:
        globals()["ratio_three_ways"] = honest
    caught = result["n_mismatched"] > 0
    return (
        TEETH[1],
        caught,
        "the pooled ratio recomputed against the wrong denominator (Σ "
        "reference / Σ arm instead of Σ arm / Σ reference): "
        + (
            f"the comparison reported {result['n_mismatched']} mismatch(es) — "
            + result["mismatches"][0]
            if caught
            else "the comparison reported none.  It must."
        ),
    )


def _tooth_an_empty_comparison(
    campaign: Campaign,
    published: Mapping[str, Mapping[str, Any]],
    recomputed: Mapping[str, Recomputed],
) -> tuple[str, bool, str]:
    """An empty table set must be refused, never reported as 0 mismatches."""
    try:
        assert_not_empty(compare({}, {}))
    except AnalysisError as exc:
        return TEETH[2], True, f"refused — {str(exc).splitlines()[0]}"
    return (
        TEETH[2],
        False,
        "a comparison over no table and no cell was accepted.  It must not be.",
    )


def _tooth_a_demonstration_record(
    campaign: Campaign,
    published: Mapping[str, Mapping[str, Any]],
    recomputed: Mapping[str, Recomputed],
) -> tuple[str, bool, str]:
    """A population handed a budget-capped demonstration must be refused."""
    population = Population.of(
        [
            {
                "campaign_phase": "B",
                "campaign_arm": "B3",
                "campaign_configuration": "st_regression",
                "campaign_seed": 0,
                FORCED_BUDGET_STAMP: 3,
            }
        ],
        what="the tooth's own record",
    )
    try:
        population.assert_no_demonstration()
    except AnalysisError as exc:
        return TEETH[3], True, f"refused — {str(exc).splitlines()[0]}"
    return (
        TEETH[3],
        False,
        "a record stamped force_maxcal was accepted into a population.  It "
        "must not be.",
    )


def _tooth_a_stored_retried_flag(
    campaign: Campaign,
    published: Mapping[str, Mapping[str, Any]],
    recomputed: Mapping[str, Recomputed],
) -> tuple[str, bool, str]:
    """A stored ``retried`` flag that disagrees with ``attempts[]``.

    The record carries a derived ``attempt_accounting.retried``.  Reading it
    instead of counting ``attempts[]`` would be trusting a copy, and a driver
    that stopped stamping attempts would then be indistinguishable from a run
    that did not retry.  The tooth makes the two disagree, in both directions,
    and requires this module to follow the list.
    """
    says_yes_but_ran_once = {
        "attempts": [{"attempt": 1, "n_iterations": 7}],
        "attempt_accounting": {"applicable": True, "n_attempts": 9, "retried": True},
    }
    says_no_but_ran_twice = {
        "attempts": [
            {"attempt": 1, "n_iterations": 7},
            {"attempt": 2, "n_iterations": 3},
        ],
        "attempt_accounting": {"applicable": True, "n_attempts": 1, "retried": False},
    }
    caught = (
        was_retried(says_yes_but_ran_once) is False
        and was_retried(says_no_but_ran_twice) is True
    )
    return (
        TEETH[4],
        caught,
        "one record with a single entry in attempts[] and a stored "
        "attempt_accounting.retried of True, and one with two entries and a "
        "stored flag of False: this module computes "
        f"{was_retried(says_yes_but_ran_once)!r} and "
        f"{was_retried(says_no_but_ran_twice)!r} — "
        + (
            "the list decides in both directions and the stored flag is never "
            "consulted"
            if caught
            else "it followed the stored flag.  It must not."
        ),
    )


def _tooth_a_mixed_commit_population(
    campaign: Campaign,
    published: Mapping[str, Mapping[str, Any]],
    recomputed: Mapping[str, Recomputed],
) -> tuple[str, bool, str]:
    """A population straddling two commits must be refused without ``--resume``.

    Exercised against a directory of the tooth's own making, so the tooth does
    not depend on what happens to be on disk, and through the same refusal the
    criterion calls rather than a restatement of it.
    """
    import tempfile  # noqa: PLC0415 - a tooth's own scratch directory

    with tempfile.TemporaryDirectory() as scratch:
        root = Path(scratch)
        for index, head in enumerate(("a" * 40, "b" * 40)):
            directory = root / f"run{index}"
            directory.mkdir()
            (directory / "metrics.json").write_text(
                json.dumps({"tree_git_head": head, "status": "ok"})
            )
        provenance = framework.survey_heads([root])
        try:
            assert_one_commit(provenance, resume=False)
        except AnalysisError as exc:
            allowed = assert_one_commit(provenance, resume=True)
            return (
                TEETH[5],
                bool(allowed),
                f"two records made at {provenance['heads']} in one population: "
                f"refused without --resume — {str(exc).splitlines()[0]}; with "
                f"--resume the straddle is stated rather than assumed",
            )
    return (
        TEETH[5],
        False,
        "a population straddling two commits was accepted without --resume.  "
        "It must not be.",
    )


def _tooth_an_imported_construction(
    campaign: Campaign,
    published: Mapping[str, Mapping[str, Any]],
    recomputed: Mapping[str, Recomputed],
) -> tuple[str, bool, str]:
    """A source that imports a tally construction must be caught.

    The independence check is the one this gate's whole claim rests on, so it
    gets a tooth like everything else: a source line importing the constructions
    is put in front of the same scanner the criterion runs, and it must name it.
    """
    doctored = (
        "from harness.stats import median\n"
        "from harness import tally_optimisation\n"
        "import harness.tables\n"
    )
    found = forbidden_imports(doctored)
    clean = forbidden_imports("from harness import framework\nimport json\n")
    caught = bool(found) and not clean
    return (
        TEETH[6],
        caught,
        f"a source importing the tally's constructions: the scanner names "
        f"{found} and names nothing in a source that imports only the "
        f"framework — "
        + (
            "so a construction borrowed from the tally cannot reach this "
            "module unreported"
            if caught
            else "the scanner did not separate the two.  It must."
        ),
    )


#: The teeth, in the order the criterion runs them.
TOOTH_BODIES: tuple[Callable[..., tuple[str, bool, str]], ...] = (
    _tooth_a_moved_cell,
    _tooth_a_wrong_denominator,
    _tooth_an_empty_comparison,
    _tooth_a_demonstration_record,
    _tooth_a_stored_retried_flag,
    _tooth_a_mixed_commit_population,
    _tooth_an_imported_construction,
)


def run_teeth(
    campaign: Campaign,
    published: Mapping[str, Mapping[str, Any]],
    recomputed: Mapping[str, Recomputed],
) -> list[tuple[str, bool, str]]:
    """Every deliberate break, run, with what the comparison did about it."""
    return [tooth(campaign, published, recomputed) for tooth in TOOTH_BODIES]


# --------------------------------------------------------------------------
# the measurement stage
# --------------------------------------------------------------------------


def tables(campaign: Campaign, *, resume: bool = False) -> dict[str, Any]:
    """This module's own tables, to be read beside the tally's.

    A measurement: it publishes numbers and has nothing to pass.  What guards
    it is the ``recomputation`` gate over the same records, which is where the
    verdict lives.
    """
    provenance = framework.survey_heads(
        [Path(campaign.runs_dir) / source.subpath for source in SOURCES]
    )
    recomputed = recompute(campaign)
    produced = recomputed["tables"]
    return {
        "what": (
            "every published cell of the experiment plan's §4 tables, "
            "recomputed by a second implementation that shares no construction "
            "with the tally.  Read beside `tally_evaluation` and "
            "`tally_optimisation`; the verdict on whether the two agree is the "
            "`recomputation` gate's, not this stage's"
        ),
        "populations": recomputed["populations"],
        "population": "; ".join(
            f"{p['source']}/{p['phase']}: {p['n_records']} record(s)"
            for p in recomputed["populations"]
        ),
        "runs_provenance": provenance,
        "seed_sets": recomputed["seed_sets"],
        "tables_not_produced": recomputed["tables_not_produced"],
        "similarity_verdicts": recomputed["similarity_verdicts"],
        "tables": [produced[name].as_record() for name in sorted(produced)],
        "n_tables": len(produced),
        "n_cells": sum(
            len(t.rows) * len(t.columns) for t in produced.values()
        ),
    }


def print_tables(block: Mapping[str, Any]) -> None:
    """The stage's tables on the terminal, each with its caption."""
    print(f"\n  {block['what']}")
    for row in block.get("populations") or []:
        print(
            f"  population {row['source']}/{row['phase']}: "
            f"{row['n_records']} record(s) under {row['subpath']}"
        )
    provenance = block.get("runs_provenance") or {}
    print(
        f"  runs read: {provenance.get('n_records')} record(s) at "
        f"{provenance.get('heads')}"
    )
    for table in block.get("tables") or []:
        print(f"\n  --- {table['table']}")
        print(f"      caption: {table['caption']}")
        for line in table["markdown"].splitlines():
            if line.startswith("|"):
                print(f"      {line}")
        print(f"      n = {table['denominator']} ({table['denominator_is']})")
    print(f"\n  {block['n_tables']} table(s), {block['n_cells']} cell(s)")


# --------------------------------------------------------------------------
# registration
# --------------------------------------------------------------------------


def gate(campaign: Campaign) -> framework.Gate:
    """The ``recomputation`` gate: ``--verify`` with its six teeth.

    Promoted from the criterion by :func:`harness.framework.gate_from_check`,
    which does not restate it: the numbers the gate reports are the numbers the
    criterion computed, and what the promotion adds is the verdict record, the
    registry entry and the **declared** tooth list — a declared tooth the
    criterion stops running is a tooth that did not trip, and the gate fails
    rather than quietly losing it.
    """
    return framework.gate_from_check(
        name="recomputation",
        binds=(
            "every cell the tally publishes, recomputed from the run records "
            "by a second implementation sharing no construction with it"
        ),
        what_it_proves=(
            "that no declared definition of the experiment plan reached one "
            "implementation and not the other — the drift issues I-18 and "
            "I-19 recorded — over a stated denominator of cells, tables and "
            "run records, with the commits of those records named"
        ),
        run=lambda *, resume=False: verify(campaign, resume=resume),
        teeth=TEETH,
        needs_runs=False,
        # Relative to ``runs/gates``, which is what ``Gate.run`` joins them to
        # — not to ``runs/``, which is what a ``Source.subpath`` is relative
        # to.  The two are one directory apart and a wrong one here surveys an
        # empty tree and reports "0 record(s)" instead of the straddle.
        runs_under=tuple(
            str(Path(source.subpath).relative_to("gates")) for source in SOURCES
        ),
    )


def measurement(campaign: Campaign) -> framework.Measurement:
    """The ``recomputed_tables`` stage: ``--tables``, which has nothing to pass."""
    return framework.Measurement(
        name="recomputed_tables",
        reports=(
            "the experiment plan's section 4 tables recomputed by a second "
            "implementation, each with its own caption and denominator, to be "
            "read beside the tally's own"
        ),
        guarded_by="recomputation",
        body=lambda *, resume=False: tables(campaign, resume=resume),
        printer=print_tables,
    )


# --------------------------------------------------------------------------
# the button
# --------------------------------------------------------------------------


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--verify",
        action="store_true",
        help="recompute every published cell and compare it with the tally's",
    )
    parser.add_argument(
        "--teeth",
        action="store_true",
        help="run the deliberate breaks the comparison must catch, and print them",
    )
    parser.add_argument(
        "--tables",
        action="store_true",
        help="emit this implementation's own tables, with captions and denominators",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="accept a population whose records were made at another commit",
    )
    parser.add_argument("--records", default=None, help="where the record goes")
    args = parser.parse_args(argv)
    if not (args.verify or args.teeth or args.tables):
        parser.error("nothing asked for: give --verify, --teeth or --tables")

    campaign = default_campaign()
    records_dir = (
        Path(args.records)
        if args.records
        else Path(campaign.runs_dir) / framework.GATES_SUBPATH
    )
    status = 0

    if args.verify:
        try:
            verdict = gate(campaign).run(
                records_dir=records_dir, teeth=True, resume=args.resume
            )
        except framework.GateError as exc:
            print(f"\n=== recomputation — REFUSED TO RUN\n    {exc}")
            return 1
        for line in framework.report_lines(
            {
                "check": "recomputation",
                "binds": verdict["binds"],
                "verdict": verdict["verdict"],
                "population": verdict.get("population", ""),
                "n_compared": verdict.get("n_compared", 0),
                "n_mismatched": verdict.get("n_mismatched", 0),
                "detail": verdict.get("detail", []),
                "teeth": [
                    {"tooth": t["tooth"], "caught": t["caught"],
                     "what": t["evidence"]}
                    for t in verdict.get("teeth", [])
                ],
            }
        ):
            print(line)
        print(f"  record: {verdict['record']}")
        if verdict["verdict"] != "PASS":
            status = 1
    elif args.teeth:
        published = read_tally_output(records_dir)["tables"]
        recomputed = recompute(campaign)["tables"]
        for name, caught, message in run_teeth(campaign, published, recomputed):
            print(f"  tooth {'TRIPPED' if caught else 'DID NOT TRIP'}: {name}")
            print(f"    {message}")
            if not caught:
                status = 1

    if args.tables:
        block = measurement(campaign).run(
            records_dir=records_dir, resume=args.resume
        )
        print(f"  record: {block['record']}")

    return status


if __name__ == "__main__":
    sys.exit(main())
