#!/usr/bin/env python
"""The chain the experiment runs, and the one-seed pass that proves it runs.

There is **one** chain here, not two.  The smoke and the campaign are the same
sequence of stages with different arguments: how many seeds, which
configurations, which entry regimes, and what kind of record the runs are
stamped with.  Writing them twice is how a smoke comes to pass over a path the
campaign will take — the smoke would be exercising its own code and reporting
on the campaign's.

The sequence, in the experiment plan's order (§3.4, §3.5):

1. **entry references** — one flat evaluation per configuration from the input
   file's own design point.  Every Phase A entry is a displacement *of its exit
   state*, and the constant the pinned arms own is *its* converged burn time, so
   nothing in the evaluation phase can start until this has finished.  A
   reference that does not finish is a refusal, never a reason to enter from
   somewhere else.
2. **evaluation, displaced entries** — plan §3.4's δ regime: every active
   evaluation-phase arm, every seed, one ``call_models`` each from the displaced
   snapshot.
3. **evaluation, stencil points** — plan §3.4's second regime: the forward
   points ``x_i (1 + epsfcn)`` from the reference fixed point and the backward
   points ``x_i (1 − epsfcn)``, each entered from **its own forward point's
   exit**, which is the sequence the optimiser's evaluator executes.  Serial per
   column for that reason.
4. **optimisation** — plan §3.5: every active optimisation-phase arm, every
   start, one full optimisation each.
5. **the tally stages**, 6. **the tally's contract gate**, 7. **the analysis's
   own tables**, 8. **the analysis's verification** — ``--verify``, the gate
   named ``recomputation``, which recomputes every published cell through a
   second implementation and compares it with the tally's.

Stages 5–8 are the registry's; this module names them and refuses if the
registry does not hold one, rather than skipping a stage nobody notices is
gone.

Two separations, each with a refusal rather than a convention
------------------------------------------------------------
**A smoke record is never summarised as a measurement.**  A one-seed pass is a
test of the machinery; a table computed over it would be a table over a
population of one, published beside tables over twenty-five.  So the run kinds a
published population may contain are declared (``stats.MEASURABLE_RUN_KINDS``
and, independently, ``analysis.MEASURABLE_RUN_KINDS``) and a record of any other
kind is **refused** at the population's construction, not filtered out of it.

**A campaign record is never made by the smoke.**  ``EXECUTION_APPROVED`` is the
user's switch and the smoke does not reach it: :func:`plan_for` refuses a
campaign plan while the switch is False or while the tree is not the
experiment's own copy, and the smoke asks for the smoke plan by name.  Resume is
closed the same way — :func:`harness.records.is_complete_for` compares the run
kind, so a campaign record left in a directory cannot be kept as a smoke run's,
or the reverse.

Both directions are gate ``run_kind_separation``'s, below, with a tooth each.

Written by task **A55 (harness-smoke)** (harness implementation plan item H8).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Mapping, Sequence

from . import arms as arms_mod
from . import framework
from . import pool as pool_mod
from . import records as records_mod
from .config import EXECUTION_APPROVED, Campaign, Config
from .framework import Gate, GateError, Tooth

__all__ = [
    "ChainError",
    "ChainPlan",
    "plan_for",
    "smoke_plan",
    "campaign_plan",
    "cheapest_configuration",
    "stage_names",
    "run",
    "gate",
]


class ChainError(framework.GateError):
    """A refusal to compose or to run the chain.  Never a warning."""


#: The stages that read the records the run stages made.  Registry names, in
#: the order the chain runs them; ``kind`` says which of the two registries the
#: name must be in, so a name that has moved between them is a refusal rather
#: than a silent skip.
READING_STAGES: tuple[tuple[str, str, str], ...] = (
    (
        "tally_evaluation",
        "measurement",
        "the evaluation phase's tables of the plan's §4.2",
    ),
    (
        "tally_optimisation",
        "measurement",
        "the optimisation phase's tables of the plan's §4.3",
    ),
    (
        "tally_contracts",
        "gate",
        "the cells the tally must land on, and what a table may not be",
    ),
    (
        "recomputed_tables",
        "measurement",
        "the same cells, computed a second time, with their own captions",
    ),
    (
        "recomputation",
        "gate",
        "--verify: every published cell of the two implementations compared",
    ),
)


# --------------------------------------------------------------------------
# the plan: what one press of the chain runs
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class ChainPlan:
    """One parameterisation of the chain: the smoke's, or the campaign's.

    ``run_kind`` is what every record this plan makes is stamped with.  It is a
    field of the plan and not an argument threaded through the stages, because
    a run kind that can be passed separately from the plan is a run kind that
    can disagree with it.
    """

    name: str
    run_kind: str
    what: str
    configurations: tuple[Config, ...]
    #: Seeds of the evaluation phase's displaced-entry regime.  Seed 0 is the
    #: undisplaced entry (the reference's own exit state); the plan's campaign
    #: seeds are 1–25 and are all displaced (§3.4).
    evaluation_seeds: tuple[int, ...]
    #: Starts of the optimisation phase.  ``seed000`` is the unperturbed start
    #: and the rest are displaced (§3.5).
    optimisation_seeds: tuple[int, ...]
    #: Which evaluation-phase entry regimes run: "displaced", "stencil".
    entry_regimes: tuple[str, ...]
    #: How many stencil columns per arm, or None for every column.  The smoke
    #: takes one so that the path is exercised without paying for 2·nvar runs
    #: per arm; the restriction is printed and recorded, never assumed.
    stencil_columns: int | None
    #: Whether this plan needs the user's execution approval to run at all.
    needs_approval: bool

    @property
    def root_name(self) -> str:
        """The directory under ``runs/`` this plan's records live in."""
        return self.name

    def budget(self, campaign: Campaign) -> dict[str, int]:
        """How many runs each run stage of this plan would make."""
        displaced = stencil = optimisations = 0
        for config in self.configurations:
            evaluation_arms = [
                arm
                for arm in arms_mod.active_arms(config, "A")
                if arm in arms_mod.ARMS
            ]
            if "displaced" in self.entry_regimes:
                displaced += len(evaluation_arms) * len(self.evaluation_seeds)
            if "stencil" in self.entry_regimes:
                for arm in evaluation_arms:
                    stencil += 2 * len(self.stencil_column_set(config, arm))
            optimisations += len(arms_mod.active_arms(config, "B")) * len(
                self.optimisation_seeds
            )
        return {
            "entry_references": len(self.configurations),
            "evaluation_displaced": displaced,
            "evaluation_stencil": stencil,
            "optimisation": optimisations,
            "total": (
                len(self.configurations) + displaced + stencil + optimisations
            ),
        }

    def stencil_column_set(self, config: Config, arm: str) -> tuple[int, ...]:
        """The design-vector columns this plan visits for one arm.

        Derived, never written down: the committed input file's variable count,
        plus the one column the lifted input file adds where the arm reads it.
        The child refuses a column outside the design vector rather than
        clamping it, and each run stamps the ``nvar`` it actually saw, so a
        wrong count here is caught by the run and by :func:`_assert_columns`
        rather than by evaluating a different point under the right name.
        """
        lifted = (
            arms_mod.ARMS[arm].input_file == "lifted" and config.pulsed
        )
        columns = config.n_iteration_variables + (1 if lifted else 0)
        if self.stencil_columns is not None:
            columns = min(columns, self.stencil_columns)
        return tuple(range(columns))


def smoke_plan(campaign: Campaign, *, configuration: str | None = None) -> ChainPlan:
    """The one-seed pass: the whole chain, on the cheapest configuration.

    It is not a small campaign and must never be read as one.  Every record it
    makes is stamped ``smoke``; the tally and the analysis refuse to summarise
    such a record; and its purpose is to answer one question — *does the button
    run the whole chain and land on 0 mismatches?* — which nothing else in the
    package answers.
    """
    config = (
        campaign.configuration(configuration)
        if configuration
        else cheapest_configuration(campaign)["configuration"]
    )
    return ChainPlan(
        name="smoke",
        run_kind="smoke",
        what=(
            "one seed end to end on the cheapest configuration: both phases, "
            "every arm of the matrix active on it, the unperturbed entry and "
            "one stencil column per arm.  A test of the chain, never a "
            "measurement"
        ),
        configurations=(config,),
        evaluation_seeds=(0,),
        optimisation_seeds=(0,),
        entry_regimes=("displaced", "stencil"),
        stencil_columns=1,
        needs_approval=False,
    )


def campaign_plan(campaign: Campaign) -> ChainPlan:
    """The campaign the experiment plan declares: every configuration, N seeds.

    Built whether or not it may run, because the budget and the stage list are
    what the preflight prints; :func:`plan_for` is what refuses to *run* it.
    """
    return ChainPlan(
        name="campaign",
        run_kind="campaign",
        what=(
            "the experiment plan's campaign: every configuration, every arm "
            "active on it, both evaluation-phase entry regimes, "
            f"{campaign.n_seeds} seeds per arm per phase"
        ),
        configurations=tuple(campaign.configurations),
        # §3.4: the evaluation phase's campaign seeds are 1..N and every one of
        # them is displaced; §3.5: the optimisation phase's starts are 0..N-1
        # with seed000 the unperturbed one.
        evaluation_seeds=tuple(range(1, campaign.n_seeds + 1)),
        optimisation_seeds=tuple(range(campaign.n_seeds)),
        entry_regimes=("displaced", "stencil"),
        stencil_columns=None,
        needs_approval=True,
    )


def plan_for(name: str, campaign: Campaign, **kwargs: Any) -> ChainPlan:
    """The plan called *name*, refusing the campaign until it may be run.

    The two refusals are the campaign's preconditions and nothing else can
    reach them: the smoke asks for ``"smoke"`` and gets a plan whose run kind
    is ``smoke``, so there is no argument it could pass that would make a
    campaign record.
    """
    builders = {"smoke": smoke_plan, "campaign": campaign_plan}
    if name not in builders:
        raise ChainError(
            f"{name!r} is not a plan of this chain; the plans are "
            f"{sorted(builders)}.  A plan nobody declared would run a stage "
            f"list nobody wrote down."
        )
    plan = builders[name](campaign, **kwargs) if name == "smoke" else builders[name](campaign)
    assert_may_run(plan, campaign)
    return plan


def assert_may_run(plan: ChainPlan, campaign: Campaign) -> None:
    """Refuse a plan that may not be run here, naming every reason.

    Both conditions are the campaign's, and both are checked on the plan rather
    than at the call site: a precondition that lives in the caller is a
    precondition a second caller does not have.
    """
    if plan.run_kind not in records_mod.RUN_KINDS:
        raise ChainError(
            f"the {plan.name!r} plan stamps its records "
            f"{plan.run_kind!r}, which is not one of {records_mod.RUN_KINDS}"
        )
    reasons = refusals(plan, campaign)
    if reasons:
        raise ChainError(
            f"the {plan.name!r} plan may not be run here: "
            + "; ".join(reasons)
        )


def refusals(plan: ChainPlan, campaign: Campaign) -> list[str]:
    """Why this plan may not run, in the caller's own words.  Empty is may."""
    reasons: list[str] = []
    if not campaign.is_experiment_copy:
        reasons.append(
            f"the tree is not the experiment's copy ({campaign.tree}); records "
            f"are only ever made against "
            f"{Path(__file__).resolve().parent.parent / 'PROCESS'}.  Pointing "
            f"the chain elsewhere is for preflight and the self-check"
        )
    if plan.needs_approval and not EXECUTION_APPROVED:
        reasons.append(
            "the plan's execution is not approved: the user flips "
            "EXECUTION_APPROVED in harness/config.py in the same commit that "
            "records the dated approval in EXPERIMENT_PLAN.md.  The smoke does "
            "not reach this switch — it runs the same chain with the run kind "
            "'smoke', one seed and one configuration"
        )
    if plan.run_kind == "campaign" and not EXECUTION_APPROVED:
        reasons.append(
            "a campaign record may not be made while EXECUTION_APPROVED is "
            "False, whichever stage asks for one"
        )
    return reasons


# --------------------------------------------------------------------------
# which configuration is cheapest, measured rather than assumed
# --------------------------------------------------------------------------


def cheapest_configuration(campaign: Campaign) -> dict[str, Any]:
    """The configuration the smoke runs, and the numbers that chose it.

    Cost is **model-node executions**, which are exact and reproduce bit for
    bit; the wall clock beside them is progress information and chooses
    nothing (I-10).  The measurement is over the gate runs already on disk:
    for each configuration, the median cost of one run of each arm the smoke
    would run, summed.  A configuration the records say nothing about falls
    back to the **declared** proxy — the arms it runs times its iteration
    variables — and the row says which route produced it, so a reader can tell
    a measurement from a derivation.
    """
    measured = _measured_arm_costs(campaign)
    rows: list[dict[str, Any]] = []
    for config in campaign.configurations:
        node_calls = 0.0
        wall = 0.0
        missing: list[str] = []
        n_runs = 0
        for phase in ("A", "B"):
            for arm in arms_mod.active_arms(config, phase):
                n_runs += 1
                cost = measured.get((config.name, phase, arm))
                if cost is None:
                    missing.append(f"{phase}/{arm}")
                    continue
                node_calls += cost["node_calls"]
                wall += cost["wall_s"]
        rows.append(
            {
                "configuration": config.name,
                "n_runs_in_the_smoke": n_runs,
                "n_arms_without_a_record": len(missing),
                "arms_without_a_record": missing,
                "node_calls": int(node_calls),
                "wall_s": round(wall, 1),
                "declared_proxy": n_runs * config.n_iteration_variables,
                "route": "measured" if not missing else "declared",
            }
        )
    complete = [row for row in rows if row["route"] == "measured"]
    if complete:
        chosen = min(complete, key=lambda row: row["node_calls"])
        basis = (
            "the median model-node executions of one run of each arm the smoke "
            "would run, read from the gate records on disk and summed"
        )
    else:
        chosen = min(rows, key=lambda row: row["declared_proxy"])
        basis = (
            "no gate record carries a cost for every arm, so the declared "
            "proxy was used: the arms this configuration runs times its "
            "iteration variables.  Press --gate all --resume first and the "
            "measured route applies"
        )
    return {
        "configuration": campaign.configuration(chosen["configuration"]),
        "basis": basis,
        "rows": rows,
        "chosen": chosen,
    }


def _measured_arm_costs(campaign: Campaign) -> dict[tuple[str, str, str], dict[str, float]]:
    """Median cost per (configuration, phase, arm) over the gate records."""
    root = Path(campaign.runs_dir) / framework.GATES_SUBPATH
    gathered: dict[tuple[str, str, str], list[tuple[float, float]]] = {}
    if not root.exists():
        return {}
    for path in sorted(root.rglob("metrics.json")):
        try:
            record = json.loads(path.read_text())
        except Exception:  # noqa: BLE001 - a half-written record is not a row
            continue
        if record.get("status") != "ok":
            continue
        key = (
            str(record.get("campaign_configuration")),
            str(record.get("campaign_phase")),
            str(record.get("campaign_arm")),
        )
        gathered.setdefault(key, []).append(
            (
                float(record.get("node_calls_total") or 0),
                float(record.get("wall_s") or 0),
            )
        )
    out: dict[tuple[str, str, str], dict[str, float]] = {}
    for key, values in gathered.items():
        calls = sorted(v[0] for v in values)
        walls = sorted(v[1] for v in values)
        out[key] = {
            "node_calls": calls[len(calls) // 2],
            "wall_s": walls[len(walls) // 2],
            "n_records": len(values),
        }
    return out


# --------------------------------------------------------------------------
# the run stages
# --------------------------------------------------------------------------


def chain_root(campaign: Campaign, plan: ChainPlan) -> Path:
    """Where this plan's records live.  Never under ``runs/gates/``.

    The tally reads *declared sources* under ``runs/gates/``; putting the
    chain's own records anywhere under that tree would offer them to a stage
    that must refuse them, which is a refusal waiting to be tripped by a
    directory layout rather than by a decision.
    """
    return Path(campaign.runs_dir) / plan.root_name


def entry_reference_directory(root: Path, configuration: str) -> Path:
    return Path(root) / "entry_references" / configuration


def stage_entry_references(
    campaign: Campaign, plan: ChainPlan, *, resume: bool
) -> dict[str, Any]:
    """One flat evaluation per configuration, from the input file's own point.

    Its exit state is what every displaced entry and every stencil point is
    entered from, and its converged burn time is the constant the pinned arms
    own.  A reference that does not finish stops the chain: there is nothing to
    enter from, and entering from somewhere else would be a different
    experiment reported under this one's name.
    """
    root = chain_root(campaign, plan)
    jobs = [
        pool_mod.Job(
            phase="A",
            arm="A0",
            config=config,
            seed=0,
            outdir=entry_reference_directory(root, config.name),
            regime="unperturbed",
            delta=None,
            run_kind=plan.run_kind,
        )
        for config in plan.configurations
    ]
    results = pool_mod.run_all(jobs, campaign, resume=resume)
    references: dict[str, dict[str, Any]] = {}
    for job in jobs:
        record = records_mod.read(job.outdir)
        if record.get("status") != "ok":
            raise ChainError(
                f"the evaluation-phase reference for {job.config.name} did not "
                f"finish (status {record.get('status')!r}, taxonomy row "
                f"{record.get('failure_class')!r}).  Every entry of the "
                f"evaluation phase is a displacement of its exit state, so the "
                f"chain stops here rather than entering from somewhere else."
            )
        references[job.config.name] = {
            "outdir": str(job.outdir),
            "snapshot": str(Path(job.outdir) / "y_exit.json"),
            "t_plant_pulse_burn_hex": record.get("t_plant_pulse_burn_hex"),
            "cold_start_node_calls": record.get("node_calls_single_eval"),
            "cold_start_sweeps": record.get("n_model_calls_sweeps"),
            "audit_residual_max_hex": (record.get("exit_audit") or {}).get(
                "residual_max_hex"
            ),
        }
    return {
        "stage": "entry_references",
        "what": (
            "one flat evaluation per configuration from the input file's own "
            "design point; its exit state is every later entry's origin and "
            "its converged burn time is the constant the pinned arms own.  Its "
            "cost is the once-per-run cold-start term, reported beside and "
            "never pooled (plan §3.4)"
        ),
        "n_runs": len(jobs),
        "references": references,
        "results": _result_summary(results),
    }


def _pin_for(
    config: Config,
    arm: str,
    reference: Mapping[str, Any],
    *,
    seed: int,
    delta: float | None,
) -> str | None:
    """The constant the arm owns at this entry, or None where it owns none.

    At an undisplaced entry it is the reference's own converged burn time; at a
    displaced one it rides the **same** stream the coupling state rides, so the
    constant and the state the run is entered with move together.  Both routes
    are the harness's one implementation of that rule.
    """
    from . import reproduction as reproduction_mod  # noqa: PLC0415

    if not config.pulsed:
        return None
    if arms_mod.ARMS[arm].burn_time_owner != "constant":
        return None
    reference_hex = reference["t_plant_pulse_burn_hex"]
    if not delta or seed == 0:
        return reference_hex
    return reproduction_mod.pin_for(reference_hex, seed, delta)


def stage_evaluation_displaced(
    campaign: Campaign,
    plan: ChainPlan,
    references: Mapping[str, Any],
    *,
    resume: bool,
) -> dict[str, Any]:
    """Plan §3.4's δ regime: every arm, every seed, one evaluation each.

    Every arm is entered from the **same** displaced state at the same seed —
    the reference arm included.  That is what makes the published cost ratios
    paired differences rather than a mixture of the entry and the arm, and it
    is the reason the plan's binding rule on `AR → A0` (§3.3) can be stated at
    all: the two arms differ in their stopping rule and in nothing else.
    """
    root = chain_root(campaign, plan) / "evaluation"
    jobs: list[pool_mod.Job] = []
    for config in plan.configurations:
        reference = references[config.name]
        for arm in arms_mod.active_arms(config, "A"):
            for seed in plan.evaluation_seeds:
                displaced = seed != 0
                jobs.append(
                    pool_mod.Job(
                        phase="A",
                        arm=arm,
                        config=config,
                        seed=seed,
                        outdir=(
                            root
                            / config.name
                            / arm
                            / pool_mod.seed_directory(seed)
                        ),
                        regime="perturbed" if displaced else "unperturbed",
                        delta=campaign.delta,
                        pin_hex=_pin_for(
                            config,
                            arm,
                            reference,
                            seed=seed,
                            delta=campaign.delta if displaced else None,
                        ),
                        entry_state=Path(reference["snapshot"]),
                        run_kind=plan.run_kind,
                    )
                )
    results = pool_mod.run_all(jobs, campaign, resume=resume)
    return {
        "stage": "evaluation_displaced",
        "what": (
            "the evaluation phase's displaced-entry regime at δ = "
            f"{campaign.delta}: every arm active on the configuration entered "
            "from the same seeded displacement of the reference fixed point, "
            "one call_models each (plan §3.4)"
        ),
        "n_runs": len(jobs),
        "seeds": list(plan.evaluation_seeds),
        "results": _result_summary(results),
    }


def stage_evaluation_stencil(
    campaign: Campaign,
    plan: ChainPlan,
    references: Mapping[str, Any],
    *,
    resume: bool,
) -> dict[str, Any]:
    """Plan §3.4's stencil regime: the optimiser's own finite-difference points.

    One column at a time: the forward point ``x_i (1 + epsfcn)`` entered from
    the reference fixed point, then the backward point ``x_i (1 − epsfcn)``
    entered from **that forward point's exit**, which is the order
    ``fcnvmc2`` executes.  The pair is therefore run serially; different columns
    are independent and go through the pool.

    A column outside the design vector is refused by the child rather than
    clamped, and every record stamps the ``nvar`` it saw, so the column set
    derived here is checked against the runs it produced instead of trusted.
    """
    root = chain_root(campaign, plan) / "evaluation_stencil"
    chains: list[list[pool_mod.Job]] = []
    planned: list[dict[str, Any]] = []
    for config in plan.configurations:
        reference = references[config.name]
        for arm in arms_mod.active_arms(config, "A"):
            columns = plan.stencil_column_set(config, arm)
            for column in columns:
                forward = root / config.name / arm / f"column{column:03d}_forward"
                backward = root / config.name / arm / f"column{column:03d}_backward"
                pin = _pin_for(config, arm, reference, seed=0, delta=None)
                chains.append(
                    [
                        pool_mod.Job(
                            phase="A",
                            arm=arm,
                            config=config,
                            seed=0,
                            outdir=forward,
                            regime="stencil",
                            delta=None,
                            pin_hex=pin,
                            entry_state=Path(reference["snapshot"]),
                            stencil_column=column,
                            stencil_sign=1,
                            run_kind=plan.run_kind,
                        ),
                        pool_mod.Job(
                            phase="A",
                            arm=arm,
                            config=config,
                            seed=0,
                            outdir=backward,
                            regime="stencil",
                            delta=None,
                            pin_hex=pin,
                            entry_state=forward / "y_exit.json",
                            stencil_column=column,
                            stencil_sign=-1,
                            run_kind=plan.run_kind,
                        ),
                    ]
                )
                planned.append(
                    {
                        "configuration": config.name,
                        "arm": arm,
                        "column": column,
                        "n_columns_planned": len(columns),
                    }
                )
    results: list[dict[str, Any]] = []
    for pair in chains:
        results.extend(pool_mod.run_serially(pair, campaign, resume=resume))
    restriction = (
        None
        if plan.stencil_columns is None
        else (
            f"{plan.stencil_columns} column(s) per arm instead of every "
            f"column: this plan exercises the stencil path rather than "
            f"measuring the regime, and the restriction is recorded here so "
            f"that no table is ever computed over it as if it were the regime"
        )
    )
    return {
        "stage": "evaluation_stencil",
        "what": (
            "the evaluation phase's stencil regime: the forward point "
            "x_i (1 + epsfcn) from the reference fixed point and the backward "
            "point x_i (1 − epsfcn) from that forward point's exit, per design "
            "variable, per arm (plan §3.4)"
        ),
        "n_runs": sum(len(pair) for pair in chains),
        "columns": planned,
        "column_restriction": restriction,
        "column_check": _assert_columns(planned, chains),
        "results": _result_summary(results),
    }


def _assert_columns(
    planned: Sequence[Mapping[str, Any]], chains: Sequence[Sequence[pool_mod.Job]]
) -> dict[str, Any]:
    """Check the derived column count against the ``nvar`` the runs stamped.

    The derivation adds one column where the arm reads the lifted input file.
    That is a rule about two files, and a rule about two files can be wrong
    about one of them; the run's own ``nvar`` is the tree's answer, so it is
    compared rather than assumed.  A mismatch is a refusal: a column set that
    does not match the design vector evaluates a different point under the
    right name.
    """
    disagreements: list[str] = []
    compared = 0
    for pair in chains:
        job = pair[0]
        record = records_mod.read(job.outdir)
        nvar = record.get("nvar")
        if not isinstance(nvar, int):
            continue
        compared += 1
        if job.stencil_column is not None and job.stencil_column >= nvar:
            disagreements.append(
                f"{job.config.name}/{job.arm}: column {job.stencil_column} "
                f"planned against nvar = {nvar} the run stamped"
            )
    if disagreements:
        raise ChainError(
            "the stencil column set does not match the design vector the runs "
            "saw: " + "; ".join(disagreements)
        )
    return {
        "n_columns_compared_against_the_run": compared,
        "n_disagreements": 0,
        "what": (
            "every planned column checked against the nvar its own run "
            "stamped; a column outside the design vector is refused by the "
            "child rather than clamped"
        ),
    }


def stage_optimisation(
    campaign: Campaign, plan: ChainPlan, *, resume: bool
) -> dict[str, Any]:
    """Plan §3.5: every optimisation-phase arm, every start, one solve each."""
    root = chain_root(campaign, plan) / "optimisation"
    jobs: list[pool_mod.Job] = []
    for config in plan.configurations:
        for arm in arms_mod.active_arms(config, "B"):
            for seed in plan.optimisation_seeds:
                jobs.append(
                    pool_mod.Job(
                        phase="B",
                        arm=arm,
                        config=config,
                        seed=seed,
                        outdir=(
                            root
                            / config.name
                            / arm
                            / pool_mod.seed_directory(seed)
                        ),
                        regime="perturbed" if seed != 0 else "unperturbed",
                        delta=campaign.delta,
                        run_kind=plan.run_kind,
                    )
                )
    results = pool_mod.run_all(jobs, campaign, resume=resume)
    return {
        "stage": "optimisation",
        "what": (
            "the optimisation phase: every arm active on the configuration, "
            f"one full optimisation per start, seed000 unperturbed and the "
            f"rest displaced at δ = {campaign.delta} on the iteration "
            "variables' initial values (plan §3.5)"
        ),
        "n_runs": len(jobs),
        "seeds": list(plan.optimisation_seeds),
        "results": _result_summary(results),
    }


def _result_summary(results: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Counts by outcome, with the denominator, and the runs that were kept."""
    by_status: dict[str, int] = {}
    for result in results:
        key = str(result.get("status"))
        by_status[key] = by_status.get(key, 0) + 1
    resumed = [r["key"] for r in results if r.get("resumed")]
    wall = sum(float(r.get("wall_s") or 0) for r in results)
    return {
        "n_runs": len(results),
        "by_status": dict(sorted(by_status.items())),
        "n_resumed": len(resumed),
        "resumed": resumed,
        "wall_s_summed_in_child": round(wall, 1),
        "wall_clock_is": (
            "progress information, never evidence: the acceptance quantities "
            "of this experiment are counts and bit-comparisons (I-10)"
        ),
    }


# --------------------------------------------------------------------------
# the whole chain
# --------------------------------------------------------------------------


def stage_names(plan: ChainPlan) -> list[dict[str, str]]:
    """Every stage of the chain, in order, with what it does.

    Printed by the preflight and by the chain itself, so that "what does one
    press run?" is answered in one place rather than by reading the code.
    """
    stages = [
        {
            "stage": "entry_references",
            "kind": "runs",
            "what": "one flat evaluation per configuration (plan §3.4)",
        },
        {
            "stage": "evaluation_displaced",
            "kind": "runs",
            "what": "the evaluation phase's displaced-entry regime (plan §3.4)",
            "skipped": (
                "" if "displaced" in plan.entry_regimes else "not in this plan"
            ),
        },
        {
            "stage": "evaluation_stencil",
            "kind": "runs",
            "what": "the evaluation phase's stencil regime (plan §3.4)",
            "skipped": (
                "" if "stencil" in plan.entry_regimes else "not in this plan"
            ),
        },
        {
            "stage": "optimisation",
            "kind": "runs",
            "what": "the optimisation phase (plan §3.5)",
        },
    ]
    stages += [
        {"stage": name, "kind": kind, "what": what}
        for name, kind, what in READING_STAGES
    ]
    return stages


def assert_stages_exist(campaign: Campaign) -> dict[str, Any]:
    """Refuse if the registry does not hold every reading stage, by name.

    A chain that skips a stage the registry has lost is a chain that reports
    success over fewer stages than it names.  The refusal says which name is
    missing and which registry it was looked for in.
    """
    from . import gates as gates_mod  # noqa: PLC0415

    available_gates = gates_mod.gates_only(campaign)
    available_stages = gates_mod.measurements(campaign)
    missing: list[str] = []
    for name, kind, _ in READING_STAGES:
        holder = available_gates if kind == "gate" else available_stages
        if name not in holder:
            missing.append(
                f"{name} (declared a {kind}; the registry's {kind}s are "
                f"{sorted(holder)})"
            )
    if missing:
        raise ChainError(
            "the chain names stage(s) the registry does not hold: "
            + "; ".join(missing)
            + ".  A stage that is silently skipped turns a chain that ran "
            "eight stages into a chain that reports on eight and ran seven."
        )
    return {
        "n_reading_stages": len(READING_STAGES),
        "stages": [name for name, _, _ in READING_STAGES],
    }


def run(
    campaign: Campaign,
    plan: ChainPlan,
    *,
    resume: bool = False,
    records_dir: Path | None = None,
    teeth: bool = True,
) -> dict[str, Any]:
    """One press of the chain: the runs, then the stages that read them.

    Returns the whole press as a record.  A stage that refuses stops the chain
    and the refusal is returned rather than raised past the caller, because a
    failed stage is a **result** and the entry point has to be able to report
    it (protocol §15, §6).
    """
    assert_may_run(plan, campaign)
    registry_check = assert_stages_exist(campaign)
    records_dir = Path(
        records_dir or (Path(campaign.runs_dir) / framework.GATES_SUBPATH)
    )
    press: dict[str, Any] = {
        "plan": plan.name,
        "run_kind": plan.run_kind,
        "what": plan.what,
        "configurations": [c.name for c in plan.configurations],
        "budget": plan.budget(campaign),
        "registry": registry_check,
        "resumed": bool(resume),
        "stages": [],
        "refused": None,
        "tree_git_head": framework.git_head(),
    }

    try:
        references_block = stage_entry_references(campaign, plan, resume=resume)
        press["stages"].append(references_block)
        references = references_block["references"]
        if "displaced" in plan.entry_regimes:
            press["stages"].append(
                stage_evaluation_displaced(
                    campaign, plan, references, resume=resume
                )
            )
        if "stencil" in plan.entry_regimes:
            press["stages"].append(
                stage_evaluation_stencil(
                    campaign, plan, references, resume=resume
                )
            )
        press["stages"].append(stage_optimisation(campaign, plan, resume=resume))
    except (ChainError, pool_mod.PoolError, GateError) as exc:
        press["refused"] = f"{type(exc).__name__}: {exc}"
        return press

    press["run_records"] = _survey_own_records(campaign, plan)

    from . import gates as gates_mod  # noqa: PLC0415

    available_gates = gates_mod.gates_only(campaign)
    available_stages = gates_mod.measurements(campaign)
    for name, kind, what in READING_STAGES:
        try:
            if kind == "gate":
                verdict = available_gates[name].run(
                    records_dir=records_dir, teeth=teeth, resume=resume
                )
                block = {
                    "stage": name,
                    "kind": kind,
                    "what": what,
                    "verdict": verdict.get("verdict"),
                    "n_compared": verdict.get("n_compared"),
                    "n_mismatched": verdict.get("n_mismatched"),
                    "n_teeth": len(verdict.get("teeth") or []),
                    "n_teeth_tripped": sum(
                        1 for t in verdict.get("teeth") or [] if t.get("caught")
                    ),
                    "runs_provenance": verdict.get("runs_provenance"),
                    "record": verdict.get("record"),
                }
            else:
                emitted = available_stages[name].run(
                    records_dir=records_dir, resume=resume
                )
                block = {
                    "stage": name,
                    "kind": kind,
                    "what": what,
                    "verdict": None,
                    "n_tables": emitted.get("n_tables"),
                    "population": emitted.get("population"),
                    "runs_provenance": emitted.get("runs_provenance"),
                    "record": emitted.get("record"),
                }
        except (GateError, FileNotFoundError, KeyError) as exc:
            press["refused"] = f"stage {name}: {type(exc).__name__}: {exc}"
            return press
        press["stages"].append(block)
        if block.get("verdict") not in (None, "PASS"):
            press["refused"] = (
                f"gate {name!r} did not pass; the chain stops here.  A failed "
                f"gate is a result, not an obstacle: nothing below is re-run "
                f"with different settings."
            )
            return press
    return press


def _survey_own_records(campaign: Campaign, plan: ChainPlan) -> dict[str, Any]:
    """What this plan's own records are, and what kind they are stamped.

    The kind is surveyed rather than assumed: the point of the run-kind
    separation is that a record's stamp is the only thing that says what it may
    be used for, and a stamp nobody reads back is a stamp nobody checked.
    """
    root = chain_root(campaign, plan)
    provenance = framework.survey_heads([root])
    by_kind: dict[str, int] = {}
    for path in sorted(root.rglob("metrics.json")):
        try:
            kind = str(json.loads(path.read_text()).get("campaign_run_kind"))
        except Exception:  # noqa: BLE001 - a half-written record is not a row
            continue
        by_kind[kind] = by_kind.get(kind, 0) + 1
    unexpected = {k: v for k, v in by_kind.items() if k != plan.run_kind}
    if unexpected:
        raise ChainError(
            f"the {plan.name!r} plan's own records under {root} carry run "
            f"kind(s) {sorted(unexpected)} beside {plan.run_kind!r}.  A run "
            f"kind is what says whether a record may be summarised as a "
            f"measurement, so a directory holding two kinds is a population "
            f"nobody can state."
        )
    return {
        "root": str(root),
        "n_records": provenance["n_records"],
        "records_by_head": provenance["records_by_head"],
        "records_by_run_kind": dict(sorted(by_kind.items())),
    }


def print_press(press: Mapping[str, Any]) -> None:
    """One press on the terminal: every stage, with its ``runs read`` line."""
    print(f"\n  plan       {press['plan']}  (records stamped "
          f"{press['run_kind']!r})")
    print(f"  {press['what']}")
    print(f"  configurations: {', '.join(press['configurations'])}")
    budget = press["budget"]
    print(
        f"  budget     {budget['entry_references']} entry reference(s) + "
        f"{budget['evaluation_displaced']} displaced-entry evaluation(s) + "
        f"{budget['evaluation_stencil']} stencil evaluation(s) + "
        f"{budget['optimisation']} optimisation(s) = {budget['total']} run(s)"
    )
    for block in press["stages"]:
        print(f"\n  --- stage {block['stage']}")
        print(f"      {block['what']}")
        if "results" in block:
            results = block["results"]
            print(
                f"      runs made : {results['n_runs']} "
                f"({results['by_status']}); {results['n_resumed']} resumed"
            )
            print(
                f"      wall clock: {results['wall_s_summed_in_child']} s "
                f"summed in child — {results['wall_clock_is']}"
            )
            if block.get("column_restriction"):
                print(f"      restricted: {block['column_restriction']}")
        provenance = block.get("runs_provenance") or {}
        if provenance:
            print(
                f"      runs read : {provenance.get('n_records')} record(s) at "
                f"{provenance.get('heads')}"
            )
        if block.get("verdict") is not None:
            print(
                f"      verdict   : {block['verdict']}  "
                f"compared {block.get('n_compared')}  "
                f"mismatched {block.get('n_mismatched')}  "
                f"teeth {block.get('n_teeth_tripped')}/{block.get('n_teeth')}"
            )
        elif block.get("n_tables") is not None:
            print(f"      tables    : {block['n_tables']}")
            print(f"      population: {block.get('population')}")
    own = press.get("run_records")
    if own:
        print(
            f"\n  this plan's own records: {own['n_records']} under "
            f"{own['root']}, by commit {own['records_by_head']}, by run kind "
            f"{own['records_by_run_kind']}"
        )
    if press.get("refused"):
        print(f"\n  REFUSED — {press['refused']}")
    else:
        print("\n  every stage of the chain ran and every gate passed.")


# --------------------------------------------------------------------------
# gate run_kind_separation — the two directions, each with a tooth
# --------------------------------------------------------------------------


def _doctored(kind: str) -> dict[str, Any]:
    """The smallest record a population would accept, stamped *kind*."""
    return {
        "campaign_arm": "A0",
        "campaign_configuration": "large_tokamak_nof",
        "campaign_seed": 0,
        "campaign_phase": "A",
        "campaign_run_kind": kind,
        "status": "ok",
        "failure_class": "ok",
    }


def _tooth_tally_refuses_a_smoke_record() -> tuple[bool, str]:
    from . import stats as stats_mod  # noqa: PLC0415

    try:
        stats_mod.Population.of(
            [_doctored("smoke")], what="a doctored population, for the tooth"
        )
    except stats_mod.StatsError as exc:
        return True, f"the tally's population refused it: {exc}"
    return False, (
        "the tally's population accepted a record stamped 'smoke'; a one-seed "
        "test of the machinery would then be summarised beside measurements"
    )


def _tooth_analysis_refuses_a_smoke_record() -> tuple[bool, str]:
    from . import analysis as analysis_mod  # noqa: PLC0415

    try:
        analysis_mod.Population.of(
            [_doctored("smoke")], what="a doctored population, for the tooth"
        )
    except analysis_mod.AnalysisError as exc:
        return True, f"the analysis's population refused it: {exc}"
    return False, (
        "the analysis's population accepted a record stamped 'smoke'.  The two "
        "implementations declare this rule separately on purpose; one of them "
        "has stopped declaring it"
    )


def _tooth_a_measurable_record_is_still_accepted() -> tuple[bool, str]:
    """The other half: the refusal must not refuse everything.

    A refusal that fires on every record would pass both teeth above and make
    every table empty.  This is the positive control.
    """
    from . import stats as stats_mod  # noqa: PLC0415

    try:
        population = stats_mod.Population.of(
            [_doctored("gate")], what="a doctored population, for the tooth"
        )
    except stats_mod.StatsError as exc:
        return False, f"a gate record was refused as well: {exc}"
    return len(population.records) == 1, (
        f"a record stamped 'gate' is still summarised: "
        f"{len(population.records)} of 1 kept"
    )


def _tooth_campaign_plan_refused(campaign: Campaign):
    def check() -> tuple[bool, str]:
        try:
            plan_for("campaign", campaign)
        except ChainError as exc:
            return True, f"the campaign plan refused to compose: {exc}"
        return False, (
            "a campaign plan composed while EXECUTION_APPROVED is False; the "
            "chain would make campaign records nobody approved"
        )

    return check


def _tooth_smoke_plan_cannot_be_a_campaign(campaign: Campaign):
    def check() -> tuple[bool, str]:
        smoke = smoke_plan(campaign)
        forged = replace(smoke, run_kind="campaign", needs_approval=True)
        try:
            assert_may_run(forged, campaign)
        except ChainError as exc:
            return True, (
                f"the smoke's own plan, forged to stamp campaign records, was "
                f"refused: {exc}"
            )
        return False, (
            "the smoke's plan was accepted with run kind 'campaign'; the smoke "
            "path could then write a campaign record"
        )

    return check


def _tooth_resume_does_not_cross_run_kinds() -> tuple[bool, str]:
    record = dict(_doctored("campaign"))
    record["regime"] = "unperturbed"
    kept = records_mod.is_complete_for(
        record,
        arm="A0",
        configuration="large_tokamak_nof",
        seed=0,
        phase="A",
        regime="unperturbed",
        run_kind="smoke",
    )
    return (not kept), (
        "a record stamped 'campaign' is not kept by --resume for a smoke run "
        f"(is_complete_for returned {kept})"
    )


def separation_body(campaign: Campaign, *, resume: bool = False) -> dict[str, Any]:
    """Every record under ``runs/``, by run kind, against what may be there.

    Two statements, both over a stated denominator:

    * **no record a declared tally source covers is of a kind the tally may not
      summarise** — the source declarations are the tally's own, so this is a
      statement about the tree the tally will actually read;
    * **no record anywhere under ``runs/`` is stamped ``campaign``** while
      ``EXECUTION_APPROVED`` is False.  That is the whole-tree version, and it
      is what catches a campaign record made by a path nobody thought to check.
    """
    from . import stats as stats_mod  # noqa: PLC0415
    from . import tally as tally_mod  # noqa: PLC0415

    root = Path(campaign.runs_dir)
    by_kind: dict[str, int] = {}
    campaign_records: list[str] = []
    total = 0
    for path in sorted(root.rglob("metrics.json")):
        try:
            record = json.loads(path.read_text())
        except Exception:  # noqa: BLE001 - a half-written record is not a row
            continue
        total += 1
        kind = str(record.get("campaign_run_kind"))
        by_kind[kind] = by_kind.get(kind, 0) + 1
        if kind == "campaign":
            campaign_records.append(str(path.relative_to(root)))

    in_sources: dict[str, int] = {}
    unsummarisable: list[str] = []
    n_in_sources = 0
    for source in tally_mod.SOURCES:
        rows, _ = tally_mod.source_rows(campaign, source)
        for row in rows:
            n_in_sources += 1
            kind = str(row.record.get("campaign_run_kind"))
            in_sources[kind] = in_sources.get(kind, 0) + 1
            if kind not in stats_mod.MEASURABLE_RUN_KINDS:
                unsummarisable.append(f"{source.name}: {row.path} is {kind!r}")

    approved_campaign_records = EXECUTION_APPROVED
    failures: list[str] = []
    if unsummarisable:
        failures.append(
            f"{len(unsummarisable)} record(s) a declared tally source covers "
            f"are of a kind the tally may not summarise: "
            f"{unsummarisable[:5]}"
        )
    if campaign_records and not approved_campaign_records:
        failures.append(
            f"{len(campaign_records)} campaign record(s) exist while "
            f"EXECUTION_APPROVED is False: {campaign_records[:5]}"
        )
    return {
        "passed": not failures,
        "population": (
            f"{total} run record(s) under {root.name}/, of which "
            f"{n_in_sources} are covered by one of the tally's "
            f"{len(tally_mod.SOURCES)} declared source(s); run kinds counted "
            f"on every one"
        ),
        "n_compared": total + n_in_sources,
        "n_mismatched": len(unsummarisable) + (
            0 if approved_campaign_records else len(campaign_records)
        ),
        "records_by_run_kind": dict(sorted(by_kind.items())),
        "declared_source_records_by_run_kind": dict(sorted(in_sources.items())),
        "measurable_run_kinds": list(stats_mod.MEASURABLE_RUN_KINDS),
        "execution_approved": EXECUTION_APPROVED,
        "detail": failures
        or [
            f"every record under {root.name}/ is of a declared kind; nothing a "
            f"tally source covers is unsummarisable; no campaign record exists "
            f"while EXECUTION_APPROVED is False"
        ],
    }


def gate(campaign: Campaign) -> Gate:
    """Gate ``run_kind_separation``: the smoke and the campaign stay apart."""
    from . import tally as tally_mod  # noqa: PLC0415

    return Gate(
        name="run_kind_separation",
        binds=(
            "every record this package makes, and every population the tally "
            "and the analysis build"
        ),
        what_it_proves=(
            "that a one-seed test of the machinery is never summarised as a "
            "measurement, and that a campaign record is never made by a path "
            "the user has not approved"
        ),
        body=lambda *, resume=False: separation_body(campaign, resume=resume),
        needs_runs=False,
        # Derived from the tally's own source declarations rather than retyped:
        # ``runs_under`` is relative to ``runs/gates/`` and a ``Source.subpath``
        # to ``runs/``, and pasting one into the other surveys a directory that
        # does not exist and prints "0 record(s)" where the straddle belongs
        # (trap T12).
        runs_under=tuple(
            str(Path(source.subpath).relative_to("gates"))
            for source in tally_mod.SOURCES
        ),
        teeth=(
            Tooth(
                name="a smoke record offered to the tally",
                what="a record stamped 'smoke' handed to stats.Population.of",
                must="REFUSE",
                check=_tooth_tally_refuses_a_smoke_record,
            ),
            Tooth(
                name="a smoke record offered to the analysis",
                what="the same record handed to analysis.Population.of",
                must="REFUSE",
                check=_tooth_analysis_refuses_a_smoke_record,
            ),
            Tooth(
                name="a gate record is still summarised",
                what="a record stamped 'gate' handed to the same population",
                must="BE KEPT — the positive control for the refusal above",
                check=_tooth_a_measurable_record_is_still_accepted,
            ),
            Tooth(
                name="a campaign plan without approval",
                what="the campaign plan composed while EXECUTION_APPROVED is False",
                must="REFUSE",
                check=_tooth_campaign_plan_refused(campaign),
            ),
            Tooth(
                name="the smoke's plan forged into a campaign",
                what="the smoke plan with its run kind changed to 'campaign'",
                must="REFUSE",
                check=_tooth_smoke_plan_cannot_be_a_campaign(campaign),
            ),
            Tooth(
                name="resume across run kinds",
                what="a record stamped 'campaign' offered to a smoke run's resume",
                must="NOT BE KEPT",
                check=_tooth_resume_does_not_cross_run_kinds,
            ),
        ),
    )
