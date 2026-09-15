#!/usr/bin/env python
"""Reading the records a tally is over, and saying which runs they are.

The two phase tallies (``tally_evaluation.py``, ``tally_optimisation.py``) and
the reference-cell gate all start from the same place: **the records on disk**,
never from each other's output.  This module is that place.

Three things live here and nothing else does:

:func:`gather`
    every run record under a root, read through ``records.read`` so an absent
    record is a row rather than an exception, annotated with where it came from
    and put through ``records.assert_usable`` — the completeness contract, the
    both-rulers refusal and the attempt-summation refusal — so that a tally
    computed over a record that does not carry what it declares **refuses**
    rather than publishing a column with holes in it.

:func:`survey`
    which commit every record was made at, and the refusal that follows.  A
    tally whose records straddle two commits is a tally over a population
    nobody can state; it is allowed only when the caller asked for ``--resume``
    and said so, and the surveyed commits are **printed** with every stage so a
    verdict says which runs it read rather than leaving a reader to assume they
    are current.

:func:`reference_cells`
    the previous revision's published cells, reproduced from *this* revision's
    records through the committed reproduction reference and the field-name map
    — never by regenerating the reference.  This is a check, so it is a gate
    with teeth and lives in ``harness/gates/gate_tally.py``; what lives here is the
    comparison it runs.

Written by task **A53 (harness-tally)**.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from harness.core import framework
from harness.core import records as records_mod
from harness.gates import reference as reference_mod
from harness.measurement import stats as stats_mod
from harness.core.config import EXECUTION_APPROVED, Campaign

__all__ = [
    "TallyError",
    "RunRow",
    "gather",
    "survey",
    "assert_one_commit",
    "population_for",
    "reference_cells",
    "GATE_RUNS_SUBPATH",
    "CAMPAIGN_RUNS_SUBPATH",
    "Source",
    "GATE_SOURCES",
    "CAMPAIGN_SOURCES",
    "SOURCES",
    "campaign_present",
    "published_sources",
    "unpublished_sources",
    "why_not_published",
]


class TallyError(framework.GateError):
    """A refused tally.  Never downgraded into a warning.

    A subclass of the framework's refusal so that the button reports it the way
    it reports every other refusal — ``REFUSED — …`` with the sentence — rather
    than as an uncaught traceback.  A refusal a reader has to decode from a
    stack trace is a refusal that reads like a crash.
    """


#: Where the **gate** runs a tally may read live, relative to the campaign's
#: records directory.  Every record under this root is stamped ``gate`` or
#: ``smoke``; the campaign's own records live under :data:`CAMPAIGN_RUNS_SUBPATH`
#: and are the tables' population once they exist (:func:`published_sources`).
GATE_RUNS_SUBPATH = Path("gates")

#: Where the campaign's records live, relative to the campaign's records
#: directory: ``chain.campaign_plan``'s ``root_name``, re-derived at import
#: rather than typed, so that a renamed root is a refusal here and not a
#: tally that reads nothing (trap T12's shape, one directory up).
CAMPAIGN_RUNS_SUBPATH = Path("campaign")


# --------------------------------------------------------------------------
# reading
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class RunRow:
    """One record, with where it was found and what refused it, if anything."""

    record: Mapping[str, Any]
    path: Path
    #: The declared source the record belongs to, e.g. ``reference_runs``; the
    #: gate directory for a record read outside a source.
    source: str
    #: The refusal ``records.assert_usable`` raised, or None.
    refusal: str | None = None

    @property
    def key(self) -> str:
        return (
            f"{self.record.get('campaign_arm')}/"
            f"{self.record.get('campaign_configuration')}/"
            f"seed{self.record.get('campaign_seed')}"
        )


def gather(
    root: Path, *, contract: bool = True
) -> tuple[list[RunRow], list[str]]:
    """Every run record under *root*, read and put through the contract.

    Returns the rows and the refusals.  A refusal is **not** raised here: the
    caller decides whether a tally over a population containing one may be
    published, and the answer is no — but a refusal that raises from inside a
    walk names one record and hides the rest, and a reader needs the list.

    An absent or unreadable record is a row whose ``status`` is ``no_record``,
    because a crashed subprocess that wrote nothing is a taxonomy row and
    turning it into an exception is how a whole class of failures once left a
    tally silently.
    """
    rows: list[RunRow] = []
    refusals: list[str] = []
    root = Path(root)
    for path in sorted(root.rglob("metrics.json")):
        record = records_mod.read(path.parent)
        relative = path.parent.relative_to(root)
        source = relative.parts[0] if relative.parts else "."
        refusal: str | None = None
        if contract and record.get("status") != "no_record":
            try:
                records_mod.assert_usable(record, where=str(relative))
            except records_mod.RecordError as exc:
                refusal = str(exc)
                refusals.append(f"{relative}: {exc}")
        rows.append(RunRow(record=record, path=path, source=source, refusal=refusal))
    return rows, refusals


def survey(paths: Sequence[Path]) -> dict[str, Any]:
    """Which commit every record under *paths* was made at.

    A thin pass-through to :func:`harness.core.framework.survey_heads`, kept here so
    that a tally stage and a gate survey the same way and a reader comparing
    two records' provenance blocks is comparing like with like.
    """
    return framework.survey_heads(list(paths))


def assert_one_commit(provenance: Mapping[str, Any], *, resume: bool) -> str | None:
    """Refuse a population straddling two commits unless ``--resume`` asked.

    Returns a sentence to print where the straddle is allowed, and raises where
    it is not.  The rule is the gates' (harness plan amendment 13): without
    ``--resume`` every run is re-made, so a record from another commit means
    one was kept that should not have been — and a tally over it is a set of
    numbers over a population that is not the one the stage names.
    """
    heads = list(provenance.get("heads") or [])
    here = framework.git_head()
    if provenance.get("n_records", 0) == 0:
        return None
    if heads == [here]:
        return None
    if not resume:
        raise TallyError(
            f"the tally read {provenance['n_records']} run record(s) made at "
            f"{heads} while this tree is at {here}, and --resume was not asked "
            f"for.  Without it every run is re-made, so a record from another "
            f"commit means one was kept that should not have been.  Re-run the "
            f"gates, or ask for --resume and accept a population that "
            f"straddles {len(heads)} commit(s)."
        )
    return (
        f"the tally read {provenance['n_records']} run record(s) made at "
        f"{heads}, not all at this tree's {here} — which is what --resume asks "
        f"for, and is stated here rather than left to be assumed"
    )


def population_for(
    rows: Iterable[RunRow],
    *,
    phase: str,
    what: str,
    denominator: int | None = None,
    predicate: Any = None,
    campaign_present: bool = False,
) -> stats_mod.Population:
    """The records of one phase as a :class:`harness.measurement.stats.Population`.

    The population's own refusals apply: a record stamped ``force_maxcal`` is
    excluded **by name** and counted in ``excluded``, a mixture of phases is
    refused, and with ``campaign_present`` a record of any kind but
    ``campaign`` is refused by kind.  ``what`` is the membership rule in one
    clause and becomes the table caption's population field.
    """
    selected = [
        row.record
        for row in rows
        if row.record.get("campaign_phase") == phase
        and (predicate is None or predicate(row.record))
    ]
    return stats_mod.Population.of(
        selected, what=what, denominator=denominator, campaign_present=campaign_present
    )


# --------------------------------------------------------------------------
# the declared sources
# --------------------------------------------------------------------------
#
# ``runs/gates/`` holds every record the verification gates made, and they are
# **not one population**.  Several gates run the same arm at the same seed from
# different entries, and three of them run it deliberately doctored.  Averaging
# across that tree would produce a per-run mean over a set nobody can state,
# which is this project's trap T11 in its purest form.
#
# So the tally does not read "the gate runs".  It reads a **declared source**:
# a named subtree whose records are a comparable set, with the sentence that
# says why they are comparable.  Every table's caption carries that sentence,
# and a record under ``runs/gates/`` belonging to no declared source is counted
# and named in the stage record rather than quietly left out.


@dataclass(frozen=True)
class Source:
    """One named, statable set of records the tally may summarise.

    Named by **job set**, not by directory (task A72 (resume-identity-and-
    shared-pool), survey item B1): under the shared pool every gate's runs
    live in one directory keyed by job identity, so a subtree no longer picks
    out a gate's population.  ``jobs`` is the gate's own declaration of the
    jobs it reads — harness plan amendment 21, rule (xi): a gate's arm, seed
    or configuration set *is* a tally population — and the pool resolves each
    job to the one directory its record can be in.
    """

    name: str
    #: The gate — or the chain plan — whose job set this is, for the caption
    #: and the provenance.
    owner: str
    #: The job set, composed from the records on disk exactly as the owning
    #: gate composes it; a job whose prerequisites are not made yet is not
    #: composable and the source is then empty, which is stated, not hidden.
    jobs: Callable[[Campaign], Sequence[Any]]
    #: Which phases this source carries: "A", "B" or "AB".
    phases: str
    #: The membership rule, in one clause, for the caption.
    what: str
    #: Which **population** this source belongs to: ``"gate"`` — a
    #: verification gate's job set, the tables' population for want of a
    #: campaign — or ``"campaign"`` — one run stage of the campaign plan's job
    #: set.  A table is over one family and says which (:func:`published_sources`).
    family: str = "gate"
    #: The run kind every record of this source must be stamped with.  Checked
    #: on the composed jobs (:func:`source_jobs`) and on the records
    #: (``Population.of``); a source whose jobs say otherwise is a refusal.
    run_kind: str = "gate"
    #: The membership rule in **a few words**, for the report's short captions
    #: (task A79 (report-captions)); ``what`` stays the full sentence the
    #: appendix's populations paragraph prints once.
    short: str = ""

    def phrase(self) -> str:
        return self.short or self.name


def _reference_runs(campaign: Campaign) -> list[Any]:
    from harness.gates import reproduction as reproduction_mod  # noqa: PLC0415

    return reproduction_mod.planned_jobs(campaign)


def _paired_entries(campaign: Campaign) -> list[Any]:
    from harness.gates import gate_entry as gate_entry_mod  # noqa: PLC0415

    return gate_entry_mod.pairing_jobs(campaign)


def _campaign_stage(stage: str, *, stencil_sign: int | None = None):
    """The campaign plan's job set for one run stage, by the chain's own
    composition (``chain.campaign_jobs``); a stencil source takes one sign."""

    def jobs(campaign: Campaign) -> list[Any]:
        from harness import chain as chain_mod  # noqa: PLC0415

        composed = chain_mod.campaign_jobs(campaign, stage)
        if stencil_sign is not None:
            composed = [j for j in composed if j.stencil_sign == stencil_sign]
        return composed

    return jobs


#: The **gate** sources: two, because two gates' job sets are comparable
#: populations and the rest are not.  They are what the tables are over
#: while no campaign record exists.
GATE_SOURCES: tuple[Source, ...] = (
    Source(
        name="reference_runs",
        owner="reproduction",
        jobs=_reference_runs,
        phases="AB",
        what=(
            "the reproduction gate's own runs — one record per arm, "
            "configuration and seed of the reference set, each made by the "
            "committed run path, the optimisations from the configuration's "
            "own starting point and the evaluations from the same displaced "
            "entry state.  The gate population, never the campaign: one or "
            "two seeds per arm is the whole population and no cell is a "
            "campaign statistic"
        ),
        family="gate",
        run_kind="gate",
        short="the reproduction gate's own runs (one or two seeds per arm)",
    ),
    Source(
        name="paired_entries",
        owner="entry_and_warm",
        jobs=_paired_entries,
        phases="A",
        what=(
            "the entry gate's paired evaluations — every evaluation-phase arm "
            "entered from the **same** displaced coupling state at one seed, "
            "which is the experiment plan's own Phase A entry construction.  "
            "The gate population, one seed per arm per configuration"
        ),
        family="gate",
        run_kind="gate",
        short="the entry gate's paired evaluations (one seed per arm)",
    ),
)

#: The **campaign** sources: one per run stage of ``chain.campaign_plan`` —
#: the stencil stage split into its forward and backward point sets, which
#: the experiment plan publishes as the bracket (§3.4, §3.5's transfer) and
#: which pair by design-vector column within a set, never across.  Each is
#: the chain's own job set for that stage (rule (xi): a plan's job set is a
#: tally population), every job stamped ``campaign``, resolved to
#: ``runs/campaign/…`` by the pool.  Present only while ``EXECUTION_APPROVED``
#: is True — with it False no campaign record may exist and a source over
#: none would be a caption naming a population that is not there.
CAMPAIGN_SOURCES: tuple[Source, ...] = (
    Source(
        name="campaign_entry_references",
        owner="campaign plan, stage entry_references",
        jobs=_campaign_stage("entry_references"),
        phases="A",
        what=(
            "the campaign population: the entry references — one flat A0 "
            "evaluation per configuration from the input file's own design "
            "point, the once-per-run cold-start term (plan §3.4), reported "
            "beside and never pooled with the displaced or stencil entries"
        ),
        family="campaign",
        run_kind="campaign",
        short="the entry reference",
    ),
    Source(
        name="campaign_displaced",
        owner="campaign plan, stage evaluation_displaced",
        jobs=_campaign_stage("evaluation_displaced"),
        phases="A",
        what=(
            "the campaign population: the evaluation phase's displaced-entry "
            "regime at δ = 0.10 — every arm active on the configuration "
            "entered from the same seeded displacement of the reference fixed "
            "point, seeds 1–25, one call_models each (plan §3.4); the "
            "acceptance regime"
        ),
        family="campaign",
        run_kind="campaign",
        short="the displaced entries (δ = 0.10)",
    ),
    Source(
        name="campaign_stencil_forward",
        owner="campaign plan, stage evaluation_stencil",
        jobs=_campaign_stage("evaluation_stencil", stencil_sign=1),
        phases="A",
        what=(
            "the campaign population: the evaluation phase's stencil regime, "
            "the **forward** points x_i (1 + epsfcn) entered from the "
            "reference fixed point, one per design-vector column per arm "
            "(plan §3.4); paired across arms by column, not seed"
        ),
        family="campaign",
        run_kind="campaign",
        short="the forward stencil points",
    ),
    Source(
        name="campaign_stencil_backward",
        owner="campaign plan, stage evaluation_stencil",
        jobs=_campaign_stage("evaluation_stencil", stencil_sign=-1),
        phases="A",
        what=(
            "the campaign population: the evaluation phase's stencil regime, "
            "the **backward** points x_i (1 − epsfcn) each entered from its "
            "own forward point's exit — the sequence the optimiser's "
            "evaluator executes — one per design-vector column per arm (plan "
            "§3.4); paired across arms by column, not seed"
        ),
        family="campaign",
        run_kind="campaign",
        short="the backward stencil points",
    ),
    Source(
        name="campaign_optimisation",
        owner="campaign plan, stage optimisation",
        jobs=_campaign_stage("optimisation"),
        phases="B",
        what=(
            "the campaign population: the optimisation phase — every arm "
            "active on the configuration, one full optimisation per start, "
            "seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the "
            "iteration variables' initial values (plan §3.5); a crashed start "
            "is a taxonomy row, never a cost"
        ),
        family="campaign",
        run_kind="campaign",
        short="the optimisations (25 starts per arm)",
    ),
)

#: Every source this tally declares.  The campaign family is declared only
#: while execution is approved (see :data:`CAMPAIGN_SOURCES`).
SOURCES: tuple[Source, ...] = GATE_SOURCES + (
    CAMPAIGN_SOURCES if EXECUTION_APPROVED else ()
)

#: The composition refusals a source may swallow into "empty": the gates'
#: (``GateError``, ``ReproductionError``) and the chain's (``ChainError``, a
#: ``GateError`` subclass) — every one of them "a prerequisite record is not
#: on disk".  Anything else is a bug and is raised.
COMPOSITION_REFUSALS: tuple[str, ...] = ("GateError", "ReproductionError", "ChainError")


def source_phrase(name: str) -> str:
    """The short membership phrase of the source called *name*, for a caption."""
    for source in SOURCES:
        if source.name == name:
            return source.phrase()
    return name


def source_jobs(campaign: Campaign, source: Source) -> list[Any]:
    """The job set of *source*, or nothing where it is not composable yet.

    A dependent job's identity carries the reference record it is entered
    from; with no reference on disk the owner refuses to compose it
    (:data:`COMPOSITION_REFUSALS`), and a source nobody can state is empty —
    stated in the stage record's population, never a row.  A composed job
    whose run kind is not the source's is refused: the source would then
    name a population its records are not.
    """
    try:
        jobs = list(source.jobs(campaign))
    except Exception as exc:  # noqa: BLE001 - only the composition refusals
        if type(exc).__name__ not in COMPOSITION_REFUSALS:
            raise
        return []
    wrong = [job.key for job in jobs if job.run_kind != source.run_kind]
    if wrong:
        raise TallyError(
            f"source {source.name!r} declares run kind {source.run_kind!r} and "
            f"{len(wrong)} of its {len(jobs)} composed job(s) are stamped "
            f"otherwise: {wrong[:3]}.  A source names one population."
        )
    return jobs


def campaign_present(campaign: Campaign) -> bool:
    """Does any campaign source have a record on disk?

    The one question the population rule turns on: with a campaign record
    present the tables are over the campaign family and a gate record is
    refused by kind; without one the gate family is the population and says
    so.  Read from the records, never from ``EXECUTION_APPROVED`` alone — an
    approved campaign that has not run yet has no population.
    """
    return any(
        (directory / "metrics.json").exists()
        for source in SOURCES
        if source.family == "campaign"
        for directory in source_directories(campaign, source)
    )


def published_sources(campaign: Campaign) -> tuple[Source, ...]:
    """The sources whose tables are published at this press: the campaign
    family when a campaign record exists, the gate family otherwise.  Never
    both — a table is over one population and its caption says which."""
    family = "campaign" if campaign_present(campaign) else "gate"
    return tuple(source for source in SOURCES if source.family == family)


def unpublished_sources(campaign: Campaign) -> tuple[Source, ...]:
    """The other family, for the stage record: counted and named, not tabled."""
    published = {source.name for source in published_sources(campaign)}
    return tuple(source for source in SOURCES if source.name not in published)


def why_not_published(campaign: Campaign) -> str:
    """The sentence the stage record carries beside the unpublished family."""
    if campaign_present(campaign):
        return (
            "the campaign population exists, so the gate sources are not "
            "published: a gate record is excluded by kind from every published "
            "cell (stats.measurable_run_kinds with campaign_present=True); the "
            "gate sources' records are still read by the gates that own them"
        )
    return (
        "no campaign record exists, so the campaign sources are empty and the "
        "gate sources are the tables' population, stated in every caption"
    )


def source_directories(campaign: Campaign, source: Source) -> list[Path]:
    """The one directory per job of *source*, resolved by the pool."""
    from harness.core import pool as pool_mod  # noqa: PLC0415

    return pool_mod.directories_for(source_jobs(campaign, source), campaign)


def gather_directories(
    directories: Sequence[Path], *, source: str, contract: bool = True
) -> tuple[list[RunRow], list[str]]:
    """The record in each of *directories*, read and put through the contract.

    :func:`gather`'s shape over an explicit list of run directories: a
    directory with no record is a ``no_record`` row, never an exception.
    """
    rows: list[RunRow] = []
    refusals: list[str] = []
    for directory in directories:
        path = Path(directory) / "metrics.json"
        record = records_mod.read(path.parent)
        refusal: str | None = None
        if contract and record.get("status") != "no_record":
            try:
                records_mod.assert_usable(record, where=str(path.parent.name))
            except records_mod.RecordError as exc:
                refusal = str(exc)
                refusals.append(f"{path.parent.name}: {exc}")
        rows.append(RunRow(record=record, path=path, source=source, refusal=refusal))
    return rows, refusals


def source_rows(campaign: Campaign, source: Source) -> tuple[list[RunRow], list[str]]:
    """Every record of one declared source, with the contract's refusals.

    A job whose directory holds no record yet is **not** a row: the source is
    the records that exist of the job set, and a missing record is the owning
    gate's failure to report, not a ``no_record`` row in a table.
    """
    directories = [
        d for d in source_directories(campaign, source) if (d / "metrics.json").exists()
    ]
    return gather_directories(directories, source=source.name)


def declared_paths(campaign: Campaign) -> list[Path]:
    """The directories the **published** sources resolve to, for the provenance
    survey: a stage's ``runs read`` line names the records its tables are over."""
    paths: list[Path] = []
    seen: set[str] = set()
    for source in published_sources(campaign):
        for directory in source_directories(campaign, source):
            if str(directory) not in seen:
                seen.add(str(directory))
                paths.append(directory)
    return paths


def campaign_records_outside_every_source(campaign: Campaign) -> dict[str, Any]:
    """Records under ``runs/campaign/`` that no campaign source covers.

    Expected 0: the campaign sources are the chain's own job sets, so every
    record the chain wrote is in one.  A nonzero count is a record the chain
    made under a directory no source names — a stage the tally does not read
    — and is what issue I-24 looked like from the records' side.
    """
    root = Path(campaign.runs_dir) / CAMPAIGN_RUNS_SUBPATH
    if not root.exists():
        return {"n_records_under_runs_campaign": 0, "n_in_a_campaign_source": 0}
    inside: set[Path] = set()
    by_source: dict[str, int] = {}
    for source in SOURCES:
        if source.family != "campaign":
            continue
        rows, _ = source_rows(campaign, source)
        by_source[source.name] = len(rows)
        inside.update(row.path for row in rows)
    outside: list[str] = []
    total = 0
    for path in sorted(root.rglob("metrics.json")):
        total += 1
        if path not in inside:
            outside.append(str(path.parent.relative_to(root)))
    return {
        "n_records_under_runs_campaign": total,
        "n_in_a_campaign_source": len(inside),
        "n_outside_every_campaign_source": total - len(inside),
        "by_source": by_source,
        "outside": outside[:20],
    }


def records_outside_every_source(campaign: Campaign) -> dict[str, Any]:
    """Records under ``runs/gates/`` that no declared source covers.

    Counted and named rather than left out silently: a reader must be able to
    see that the tally read 28 of 150 records **because the other 122 are not
    a comparable set**, not because they were missed.  Under the shared pool
    most records sit in ``_runs/``; those are named by phase and arm from
    their own stamps, the rest by the gate directory they sit under.
    """
    root = Path(campaign.runs_dir) / GATE_RUNS_SUBPATH
    if not root.exists():
        return {"n_records_under_runs_gates": 0, "n_in_a_declared_source": 0}
    inside: set[Path] = set()
    for source in SOURCES:
        if source.family != "gate":
            continue
        for row in source_rows(campaign, source)[0]:
            inside.add(row.path)
    outside: dict[str, int] = {}
    total = 0
    for path in sorted(root.rglob("metrics.json")):
        total += 1
        if path in inside:
            continue
        relative = path.parent.relative_to(root)
        gate = relative.parts[0] if relative.parts else "."
        if gate == "_runs":
            record = records_mod.read(path.parent)
            gate = (
                f"_runs: phase {record.get('campaign_phase')} arm "
                f"{record.get('campaign_arm')}"
            )
        outside[gate] = outside.get(gate, 0) + 1
    return {
        "n_records_under_runs_gates": total,
        "n_in_a_declared_source": len(inside),
        "n_outside_every_declared_source": total - len(inside),
        "outside_by_gate": dict(sorted(outside.items())),
        "why": (
            "these records belong to gates that run the same arm at the same "
            "seed from different entries, or deliberately doctored.  They are "
            "each that gate's own comparison and are not a population a table "
            "may average over; they are named here so that the tally's smaller "
            "denominator is a stated choice and not an omission"
        ),
    }


# --------------------------------------------------------------------------
# the previous revision's published cells
# --------------------------------------------------------------------------


#: What each published cell **is**, in one phrase, keyed by the previous
#: revision's own dotted path.  Presentation only: the list of cells actually
#: compared is **derived**, per run, as the intersection of
#: ``reference.REFERENCE_FIELDS[phase]`` with the fields that run's entry
#: published.  Deriving it rather than writing it out means a later task that
#: drops a field from the compared set — task **A62 (exit-audit-restore)** will
#: drop the inherited audit residual when the audit instrument changes — drops
#: it here too, instead of leaving this module comparing a cell nobody compares
#: any more.
CELL_NAMES: dict[str, str] = {
    "node_calls_solve_phase": "node calls, solve phase",
    "node_calls_total": "node calls, whole run",
    "n_model_calls": "call_models evaluations",
    "node_calls_single_eval": "node calls, the one evaluation",
    "n_model_calls_sweeps": "sweeps of the one evaluation",
    "n_prime_calls": "arrangement-method calls",
    "exact.norm_objf": "objective at the optimum (hex)",
    "exact.objf": "objective at exit (hex)",
    "exit_audit.residual_max_hex": "exit-audit maximum (hex)",
    "module_solve_totals.n_call_models": "block-loop call_models",
    "module_solve_totals.block_sweeps": "block sweeps",
    "module_solve_totals.outer_pass_hist": "schedule passes per evaluation",
    "module_solve_totals.inner_sweeps_by_block": "sweeps by block",
    "n_solver_iterations": "iterations, final attempt",
    "mfile.ifail": "optimiser exit code",
    "exit_forensics.n_solver_iterations_summed_over_attempts": (
        "iterations, summed over attempts"
    ),
    "exit_forensics.n_attempts": "attempts",
    "exit_forensics.attempts[].n_solver_iterations": "iterations per attempt",
}

#: Cells this revision computes with **one of its own constructions** rather
#: than by reading the field the previous revision published.  Keyed by the
#: previous revision's path.
#:
#: This is what makes the comparison a stronger statement than the
#: reproduction gate's.  That gate asks *does this field equal that field*;
#: this asks *does the rule this revision declares, applied to this revision's
#: record, land on the number the previous revision published* — which is a
#: statement about the rule and not about a copy.
CONSTRUCTED: dict[str, Any] = {
    "n_solver_iterations": stats_mod.iterations_final_attempt,
    "exit_forensics.n_solver_iterations_summed_over_attempts": (
        stats_mod.iterations_summed_over_attempts
    ),
    "exit_forensics.n_attempts": stats_mod.n_attempts,
}

#: How each constructed cell is built, for the record and the report.
CONSTRUCTION_NOTES: dict[str, str] = {
    "n_solver_iterations": (
        "stats.iterations_final_attempt — the last element of attempts[]"
    ),
    "exit_forensics.n_solver_iterations_summed_over_attempts": (
        "stats.iterations_summed_over_attempts — the sum over attempts[], "
        "failed attempts included"
    ),
    "exit_forensics.n_attempts": (
        "stats.n_attempts — the length of attempts[]"
    ),
}


def cells_for(phase: str, published: Mapping[str, Any]) -> list[str]:
    """The previous revision's published cells this tally compares, in order.

    Derived: :func:`harness.gates.reference.compared_fields` — the reference's own
    field list **less what the reproduction gate excludes by name** — restricted
    to the fields the entry actually published.  A field named by the list and
    absent from the entry is **not** silently skipped (:func:`reference_cells`
    reports it) and a field the entry publishes that the list no longer names is
    reported too, because both are the compared set drifting away from what is
    on disk.

    It reads ``compared_fields`` and not ``REFERENCE_FIELDS`` because the two
    comparisons are one criterion implemented twice: the reproduction gate
    compares the reference entry against the record, and this compares the same
    cells recomputed through this revision's constructions.  A field the project
    has ruled not comparable — the optimisation phase's exit-audit residual,
    whose two sides were measured by **two instruments** (ruling D25, harness
    plan §7.1) — is not comparable in either of them.  Excluding it here is not
    a smaller comparison: :func:`reference_cells` names every excluded field with
    the reason the reference file records, exactly as the gate does.
    """
    return [
        path
        for path in reference_mod.compared_fields(phase)
        if path in published
    ]


def reproduction_run_directories(campaign: Campaign) -> dict[tuple[str, str, int], Path]:
    """Where each of the reproduction gate's twenty runs is, by (configuration, arm, seed).

    Resolved through the gate's own job set and the pool, not through a
    directory layout this module knows.
    """
    from harness.gates import reproduction as reproduction_mod  # noqa: PLC0415

    return reproduction_mod.planned_directories(campaign)


def reference_cells(
    campaign: Campaign,
    *,
    document: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Reproduce the previous revision's published cells, cell by cell.

    For each of the twenty reference runs the previous revision published a
    row of numbers.  This computes the **same cells from this revision's
    records** — through this revision's own constructions where there is one,
    and through the field-name map where a record field has been renamed — and
    compares them against the committed reference.  No tolerance on any cell.

    Three ways it refuses rather than reporting a zero:

    * a reference run whose record is missing is a failure, not one fewer
      comparison;
    * a record that does not carry a compared cell is a failure that names the
      cell;
    * an empty comparison is a failure: a gate that cannot find its reference
      must refuse, never pass over nothing (trap T11).
    """
    document = document or reference_mod.load()
    # The gate's runs, by their job identities; where the references are not
    # made yet no run is composable and every row reads as ``no_record``,
    # which the caller refuses on (trap T11), never as an empty comparison.
    try:
        directories = reproduction_run_directories(campaign)
    except Exception as exc:  # noqa: BLE001 - a missing prerequisite is stated
        if type(exc).__name__ not in ("GateError", "ReproductionError"):
            raise
        directories = {}
    rows: list[dict[str, Any]] = []

    for run in reference_mod.reference_set(campaign):
        entry = reference_mod.lookup(
            run.arm, run.configuration, run.seed, document=document
        )
        directory = directories.get(
            (run.configuration, run.arm, run.seed),
            Path(campaign.runs_dir) / "_no_such_run" / run.key,
        )
        record = records_mod.read(directory)
        published = entry["fields"]
        compared = cells_for(run.phase, published)
        declared_but_absent = [
            path
            for path in reference_mod.compared_fields(run.phase)
            if path not in published
        ]
        published_but_not_compared = [
            path
            for path in published
            if path not in set(reference_mod.REFERENCE_FIELDS[run.phase])
        ]
        # The fields the project has ruled not comparable, named one by one
        # with the value the reference holds and the reason recorded for the
        # exclusion.  Never dropped silently, and never counted as a match:
        # the gate's own practice, in the second implementation of the same
        # criterion.
        excluded_by_name = {
            path: {
                "in_the_reference": published[path],
                "why": why,
            }
            for path, why in reference_mod.FIELDS_NOT_COMPARED.get(
                run.phase, {}
            ).items()
            if path in published
        }
        cells: list[dict[str, Any]] = []
        for previous_path in compared:
            name = CELL_NAMES.get(previous_path, previous_path)
            how = CONSTRUCTION_NOTES.get(previous_path, "record field")
            expected = published[previous_path]
            this_path = reference_mod.field_name_map().get(
                previous_path, previous_path
            )
            if record.get("status") != "ok":
                cells.append(
                    {
                        "cell": name,
                        "previous_path": previous_path,
                        "this_path": this_path,
                        "expected": expected,
                        "found": f"<the run did not finish: "
                        f"{record.get('status')!r}>",
                        "matched": False,
                    }
                )
                continue
            constructor = CONSTRUCTED.get(previous_path)
            if constructor is not None:
                found: Any = constructor(record)
                how_found = f"construction: {how}"
            else:
                try:
                    found = records_mod.resolve_path(record, this_path)
                    how_found = f"record field {this_path}"
                except KeyError as exc:
                    found = f"<missing at {exc.args[0]}>"
                    how_found = f"record field {this_path}"
            cells.append(
                {
                    "cell": name,
                    "previous_path": previous_path,
                    "this_path": this_path,
                    "how": how_found,
                    "expected": expected,
                    "found": found,
                    "matched": found == expected,
                }
            )
        rows.append(
            {
                "key": run.key,
                "arm": run.arm,
                "previous_arm": entry["previous_arm"],
                "configuration": run.configuration,
                "seed": run.seed,
                "phase": run.phase,
                "status": record.get("status"),
                "audit_position": record.get("audit_position"),
                "n_cells": len(cells),
                "n_matched": sum(1 for c in cells if c["matched"]),
                "declared_but_not_published": declared_but_absent,
                "published_but_not_compared": published_but_not_compared,
                "n_excluded_by_name": len(excluded_by_name),
                "excluded_by_name": excluded_by_name,
                "cells": cells,
            }
        )
    n_cells = sum(row["n_cells"] for row in rows)
    n_matched = sum(row["n_matched"] for row in rows)
    constructed = sorted(
        {
            c["cell"]
            for row in rows
            for c in row["cells"]
            if c.get("previous_path") in CONSTRUCTED
        }
    )
    drift = sorted(
        {
            path
            for row in rows
            for key in ("declared_but_not_published", "published_but_not_compared")
            for path in row.get(key) or ()
        }
    )
    return {
        "rows": rows,
        "n_runs": len(rows),
        "n_cells_compared": n_cells,
        "n_cells_matched": n_matched,
        "n_cells_differing": n_cells - n_matched,
        "n_runs_reproduced": sum(
            1 for row in rows if row["n_matched"] == row["n_cells"] and row["n_cells"]
        ),
        "cells_by_construction": constructed,
        "compared_set_drift": drift,
        "n_cells_excluded_by_name": sum(
            row["n_excluded_by_name"] for row in rows
        ),
        "cells_excluded_by_name": sorted(
            {path for row in rows for path in row["excluded_by_name"]}
        ),
        "compared_set_is": (
            "derived per run as reference.compared_fields(phase) — the "
            "reference's own field list less what the reproduction gate "
            "excludes by name — intersected with the fields that run's entry "
            "published, so a field a later task drops from the compared set is "
            "dropped here too, and is named with its reason rather than "
            "silently lost"
        ),
        "reference": str(reference_mod.REFERENCE_PATH),
        "reference_source": (document.get("provenance") or {}).get("source"),
        "population": (
            f"{len(rows)} reference run(s) "
            f"({sum(1 for r in rows if r['phase'] == 'B')} optimisations + "
            f"{sum(1 for r in rows if r['phase'] == 'A')} evaluations) over "
            f"{len({r['configuration'] for r in rows})} configurations; "
            f"{n_cells} published cells, no tolerance on any of them"
        ),
        "audit_position": sorted(
            {str(row["audit_position"]) for row in rows if row["audit_position"]}
        ),
        "passed": bool(rows) and n_cells > 0 and n_matched == n_cells,
        "why_not": (
            "the comparison is empty: a gate that cannot find its reference "
            "must refuse, never pass over nothing"
            if not rows or n_cells == 0
            else None
        ),
    }
