"""Every declared setting of the experiment, in one place, as frozen data.

Derived from ``arch_surgery/MDA_partitioning_experiment_v3/v3_config.py`` at
``f2dc9243`` (task A47).  Two things changed against V3 and both are
deliberate:

* V3 kept its settings as module-level constants, so a stage could rebind one
  and nothing downstream would know.  Here they are fields of frozen
  dataclasses; a variation is a *new object*, and the object that produced a
  number can be recorded beside it.
* V3 named its three configurations in a tuple of strings and re-derived every
  artifact path from that string with a helper per artifact.  Here a
  ``Config`` carries its own paths, and the *list* of configurations is a
  campaign field — so removing one by a recorded decision is expressible
  (:meth:`Campaign.without_configuration`) and every population downstream
  re-derives from the list rather than being edited down by hand (trap T11).

A word on vocabulary, because it is load-bearing here.  A **configuration** is
one optimisation problem; its **input file** is the file that problem is read
from, either the *committed* one (never edited) or its *lifted* derived copy.
V3 called both "deck".  **"Frozen" is reserved** for the physics freeze and for
the convergence predicate's mode, and names no file, field or matrix cell.

The one module-level name is :data:`EXECUTION_APPROVED`.  It is the switch the
user flips, in the same commit that records the dated approval in
``EXPERIMENT_REPORT.md``'s status header.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

#: The package directory: ``…/MDA_partitioning_experiment_v4/harness``.
#: This module lives one level down, in ``harness/core/``.
HERE = Path(__file__).resolve().parent.parent

#: ``…/MDA_partitioning_experiment_v4``.
EXPERIMENT_DIR = HERE.parent

#: The repository root of the checkout this file belongs to.
REPO_ROOT = EXPERIMENT_DIR.parent.parent

#: Master switch.  While False the runner executes preflight, gates and smoke
#: work only and refuses every campaign stage.  The user flips it in the same
#: commit that records the dated approval in EXPERIMENT_REPORT.md.
EXECUTION_APPROVED = True  # the user, 2026-09-14: "You can run the experiment"; dated approval in EXPERIMENT_REPORT.md's header, this commit


# --------------------------------------------------------------------------
# one configuration = one optimisation problem
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Config:
    """One input file defining one optimisation problem.

    The configuration is the *problem*; its **input file** is the file the
    problem is read from (README §3).
    """

    #: Configuration name; also the committed input file's stem.
    name: str
    #: Pulsed plant (burn-time coupling present, k = 1) or steady state (k = 0).
    pulsed: bool
    #: PROCESS's ``minmax``: positive minimises, negative maximises.
    figure_of_merit: int
    #: PROCESS's own description of that figure of merit.
    figure_of_merit_name: str
    #: Iteration variables and constraints the committed input file declares.  The
    #: stencil regime's run count is 2 * (n_iteration_variables + 1) per arm,
    #: so this is read, never written into a table by hand.
    n_iteration_variables: int
    n_constraints: int
    #: The committed input file.  Never edited (D9: the committed input files
    #: are the experiment's fixed input).
    input_path: Path
    #: The committed coupling-state artifact: which fields make up ``y`` and
    #: the measured scale of each.  The driver reads it too.
    coupling_state_path: Path
    #: The committed per-node write sets used by the block solves.
    write_sets_path: Path
    #: The committed census test sets (driver change DR11): per loop and per
    #: block, the components the loop tests under the ``census`` test set.
    #: Made by ``experiment/test_sets.py`` (``--census``), validated by the
    #: artifact check; the driver reads it under ``PROCESS_ARCH_TEST_SETS``.
    test_sets_path: Path
    #: The per-run deferral set for a run of the **committed** input file —
    #: the unmarked default.  Phase A's block arms run the committed input
    #: file (a constant owns the burn time, and a constant plus the lifted
    #: input file is two owners, which the driver refuses), so this is the one
    #: they need.
    defer_per_run_path: Path
    #: The same node set, stamped for a run of the **lifted** input file.  On
    #: a steady-state configuration there is no lifted input file and this is
    #: the same file as above.
    defer_per_run_lifted_path: Path
    #: Components of the coupling state this configuration's artifact declares.
    n_coupling_components: int
    #: Arms inactive on this configuration, with the reason.  An arm listed
    #: here is *recorded as skipped*, never silently absent.
    skips: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "skips", MappingProxyType(dict(self.skips)))

    def artifact_roles(self) -> dict[str, Path]:
        """Role -> the file this configuration resolves for it."""
        return {
            "coupling_state": self.coupling_state_path,
            "write_sets": self.write_sets_path,
            "test_sets": self.test_sets_path,
            "defer_per_run": self.defer_per_run_path,
            "defer_per_run_lifted": self.defer_per_run_lifted_path,
        }

    def per_run_artifact(self, *, lifted_input_file: bool) -> Path:
        """The per-run deferral artifact stamped for the input file actually run.

        One rule instead of V3's phase test: V3 chose ``postsolve_nolift_*``
        in ``phase_a`` and ``postsolve_*`` in ``v3_runner``, which is the same
        decision written twice.
        """
        return (
            self.defer_per_run_lifted_path
            if lifted_input_file
            else self.defer_per_run_path
        )


@dataclass(frozen=True)
class Removal:
    """A configuration removed from the campaign by a recorded decision."""

    configuration: str
    decision: str
    reason: str
    date: str


# --------------------------------------------------------------------------
# the test set and its tolerance (driver change DR11; D32, D39, D23)
# --------------------------------------------------------------------------

#: The two things a block loop can stop on (``PROCESS_ARCH_TEST_SET``):
#: ``census`` — the read-before-write set measured at run time per loop and
#: block (decision D32, the V5 default) — and ``write_set`` — the block's
#: whole write set, exactly V4's predicate, kept as the fallback (decision
#: D39).
TEST_SETS: tuple[str, ...] = ("census", "write_set")

#: The tolerance each test set is declared at (V5 plan §3, §9; D23: one
#: tolerance for every converger in every arm and both phases).  The census
#: set at 1e-8 by the rule ε ≤ epsfcn³ (A89, confirmed by A93); the write set
#: at 1e-6, V4's.  A campaign composes ``PROCESS_ARCH_TAU`` from this table
#: unless an explicit ``--tau`` overrides it, and the override is stamped.
TAU_BY_TEST_SET: Mapping[str, float] = MappingProxyType({"census": 1e-8, "write_set": 1e-6})

#: The campaign default (decision D32; the user, 2026-09-29).
DEFAULT_TEST_SET = "census"

#: V4's predicate: the fallback.  A job under it carries V4's job identity
#: (``records.IDENTITY_DEFAULTS_WHEN_ABSENT``), which is what makes every
#: record made before DR11 a record of the fallback.
V4_TEST_SET = "write_set"


@dataclass(frozen=True)
class SupplementaryStage:
    """A declared stage reported **beside** the campaign under its own settings.

    V5 plan §3 and §10 after A96 (st-trajectory-ladder): ``B0`` and ``B2``
    under the census set at τ = 1e-12 on ``st_regression`` alone, the rung
    where the census loops read exact and the optimiser's path returns.  Its
    records are stamped ``run_kind == "supplementary"``, never pooled with
    the campaign's, and carry their own ``campaign_tau`` and
    ``campaign_test_set``; the tolerance is in the job identity, so they
    never resolve into the campaign's records of the same arm and seed.  The
    pool admits a job at these settings only when a declared stage matches
    its phase, configuration and arm (``pool.resolve_settings``).
    """

    name: str
    phase: str
    configurations: tuple[str, ...]
    arms: tuple[str, ...]
    test_set: str
    tau: float
    run_kind: str = "supplementary"
    why: str = ""

    def admits(self, *, phase: str, configuration: str, arm: str) -> bool:
        return (
            phase == self.phase
            and configuration in self.configurations
            and arm in self.arms
        )


#: The one declared supplementary stage.
SUPPLEMENTARY_STAGES: tuple[SupplementaryStage, ...] = (
    SupplementaryStage(
        name="st_census_exact",
        phase="B",
        configurations=("st_regression",),
        arms=("B0", "B2"),
        test_set="census",
        tau=1e-12,
        why=(
            "A96 (st-trajectory-ladder): on st_regression the census set at "
            "1e-8 moves the optimiser's path (the partitioned arm 1.7-4.2x "
            "longer, one seed lost); at 1e-12 the census loops read exact, the "
            "stable seeds' paths return and seed 1 holds its basin.  Reported "
            "beside the declared cell, labelled supplementary; the campaign's "
            "declared setting is unchanged"
        ),
    ),
)


# --------------------------------------------------------------------------
# the campaign: the declared shape of the whole experiment
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Campaign:
    """Every declared setting of EXPERIMENT_REPORT.md §3.10, plus the paths.

    ``tree`` is the tree the harness runs against — the directory holding the
    ``process`` package.  It is a parameter because V4 runs its *own copy* of
    PROCESS; the self-check constructs a campaign at another path to prove the
    refusals that keep it so.  Whichever it is, it is asserted for equality in
    every measurement subprocess (trap T6).
    """

    # --- what to run against -------------------------------------------
    #: Directory holding the ``process`` package under test.
    tree: Path
    #: Directory holding the committed per-configuration artifacts.
    data_dir: Path
    #: Directory holding the committed input files (never edited, D9).
    input_dir: Path
    #: Untracked bulk output.
    runs_dir: Path
    #: Derived (lifted) input files, produced by a committed stage.
    derived_input_dir: Path

    # --- what to run ----------------------------------------------------
    configurations: tuple[Config, ...]
    removed_configurations: tuple[Removal, ...] = ()

    # --- campaign shape (EXPERIMENT_REPORT.md §3.10) -----------------------
    #: Seeds per configuration per arm, both phases.
    n_seeds: int = 25
    #: The two Phase A entry regimes: a displaced entry at ``delta``, and the
    #: optimiser's own finite-difference stencil points.
    entry_regimes: tuple[str, ...] = ("delta", "stencil")
    #: Entry displacement of the delta regime, and the Phase B start
    #: displacement.
    delta: float = 0.10
    #: Which components every block loop tests (driver change DR11): one of
    #: :data:`TEST_SETS`, one value for every arm and both phases, never mixed
    #: within a campaign (D39).  The default is the census set (D32).
    test_set: str = DEFAULT_TEST_SET
    #: The one tolerance of every converger, both phases, every arm (D23:
    #: the flat loop and each block loop alike).  ``None`` — the default —
    #: means the test set's declared value, :data:`TAU_BY_TEST_SET`; a number
    #: is an explicit override (the runner's ``--tau``), resolved once here
    #: and stamped as such (:attr:`tau_overridden`).  There is no second
    #: tolerance; see switches.py on the retired inner-tolerance name.
    tau: float | None = None
    #: Whether ``tau`` was given explicitly rather than taken from the test
    #: set's declared value.  Derived in ``__post_init__``; never set by hand.
    tau_overridden: bool = False
    #: The declared supplementary stages, each with its own test set and
    #: tolerance (:class:`SupplementaryStage`).
    supplementary: tuple[SupplementaryStage, ...] = SUPPLEMENTARY_STAGES
    #: Similarity / same-optimum factor, applied to medians and p90s.
    similarity_factor: float = 10.0
    #: Floors.  ``objf_floor_rel`` is the relative floor on ``norm_objf``;
    #: ``cluster_gap_factor`` x that floor separates optima clusters.
    objf_floor_rel: float = 1e-6
    cluster_gap_factor: float = 10.0
    #: Bound on the median paired optimiser-iteration ratio.
    iteration_ratio_max: float = 1.05
    #: The declared median, stated so a report can quote it verbatim.
    median_construction: str = "nearest-rank upper-middle: sorted_values[n // 2]"
    #: Sweeps a block loop may take before the run is refused (not a budget:
    #: reaching it is a refusal).
    inner_sweep_cap: int = 20
    #: Passes upstream's own loop takes before it raises.
    upstream_pass_cap: int = 10
    #: Worker pool width.
    workers: int = 3
    #: Convergence-predicate modes an arm may compose.  V5 composes the frozen
    #: ruler alone: the ``mixed`` trial (V4's G8, driver change DR5) is dropped
    #: under list item 10 (D30's "or drop it") and its switch is retired in
    #: ``experiment/switches.py``.  The exit audit still *measures* on both
    #: rulers (``records.AUDIT_RULERS``, the record contract), which is a
    #: different thing from composing one.
    predicate_modes: tuple[str, ...] = ("frozen",)
    predicate_mode_default: str = "frozen"

    def __post_init__(self) -> None:
        if self.test_set not in TEST_SETS:
            raise ValueError(
                f"test_set {self.test_set!r} is not one of {TEST_SETS}; a "
                f"campaign whose loops test a set nobody declared measures "
                f"nothing anyone can name"
            )
        if self.tau is None:
            object.__setattr__(self, "tau", float(TAU_BY_TEST_SET[self.test_set]))
            object.__setattr__(self, "tau_overridden", False)
        else:
            object.__setattr__(self, "tau", float(self.tau))
            object.__setattr__(
                self,
                "tau_overridden",
                float(self.tau) != float(TAU_BY_TEST_SET[self.test_set]),
            )

    # --- derived --------------------------------------------------------
    @property
    def declared_tau(self) -> float:
        """The tolerance the test set is declared at, whatever ``tau`` is."""
        return float(TAU_BY_TEST_SET[self.test_set])

    def supplementary_stage_for(
        self, *, phase: str, configuration: str, arm: str, test_set: str, tau: float
    ) -> SupplementaryStage | None:
        """The declared stage admitting these settings for this job, or None."""
        for stage in self.supplementary:
            if (
                stage.test_set == test_set
                and float(stage.tau) == float(tau)
                and stage.admits(phase=phase, configuration=configuration, arm=arm)
            ):
                return stage
        return None

    @property
    def is_experiment_copy(self) -> bool:
        """Whether this campaign runs against the experiment's own copy.

        Records are only ever made against the copy.  A campaign pointed at
        another tree exists only as a self-check fixture; ``pool.run`` and
        every campaign stage refuse it, so a measurement of a tree nobody
        asked for cannot be produced by forgetting a flag.
        """
        return Path(self.tree).resolve() == (EXPERIMENT_DIR / "PROCESS").resolve()

    @property
    def pulsed(self) -> tuple[str, ...]:
        """Names of the pulsed configurations, derived, never listed."""
        return tuple(c.name for c in self.configurations if c.pulsed)

    @property
    def population(self) -> tuple[str, ...]:
        """The configuration names every count in every table is over."""
        return tuple(c.name for c in self.configurations)

    def configuration(self, name: str) -> Config:
        """The configuration called *name*; raises if it is not in the set.

        A lookup that misses must raise: a check with no population is how a
        zero gets published over nothing (trap T11).
        """
        for cfg in self.configurations:
            if cfg.name == name:
                return cfg
        raise KeyError(
            f"{name!r} is not in this campaign's configurations "
            f"{self.population}; removed: "
            f"{tuple(r.configuration for r in self.removed_configurations)}"
        )

    def without_configuration(
        self, name: str, *, decision: str, reason: str, date: str
    ) -> "Campaign":
        """A campaign with *name* removed and the removal recorded.

        This is the mechanism D22 needed: a configuration leaves the
        experiment by a recorded decision, and every population downstream
        re-derives from :attr:`population` rather than being patched.
        """
        self.configuration(name)  # raises if it was never here
        return replace(
            self,
            configurations=tuple(
                c for c in self.configurations if c.name != name
            ),
            removed_configurations=self.removed_configurations
            + (Removal(name, decision, reason, date),),
        )

# --------------------------------------------------------------------------
# the declared configuration set (D17), and the default campaign
# --------------------------------------------------------------------------

#: How the committed per-configuration artifacts are named, per naming scheme.
#:
#: ``harness`` is V4's own scheme and is what the experiment's ``data/``
#: directory holds: the file is named for the **role** it plays, with no task
#: token and no revision token (harness plan §11.1) and with the terms of
#: §11.2 — "coupling state", "write sets", "deferral per_run".  ``repository``
#: is the spelling the repository's shared data directory uses, kept so that
#: the harness can be pointed at those files unchanged.
#:
#: Two names are **not** in here because they are not the harness's to choose:
#: ``node_writesets.json`` and ``dsm_node_map.json`` are fixed by two path
#: constants inside the copied driver, and renaming either is a driver edit.
ARTIFACT_NAMES: dict[str, dict[str, str]] = {
    "harness": {
        "coupling_state": "coupling_state_{name}.json",
        "write_sets": "write_sets_{name}.json",
        "test_sets": "test_sets_{name}.json",
        "defer_per_run": "defer_per_run_{name}.json",
        "defer_per_run_lifted": "defer_per_run_lifted_{name}.json",
        "defer_per_run_steady_state": "defer_per_run_{name}.json",
    },
    "repository": {
        "coupling_state": "ystate_a26_{name}.json",
        "write_sets": "writeset_a26_{name}.json",
        # The repository's shared data directory never held census test sets
        # (they are V5's, made by this harness); the same spelling either way.
        "test_sets": "test_sets_{name}.json",
        "defer_per_run": "postsolve_nolift_{name}.json",
        "defer_per_run_lifted": "postsolve_{name}.json",
        "defer_per_run_steady_state": "postsolve_{name}.json",
    },
}


def artifact_file_names(
    configuration: str, *, pulsed: bool, naming: str = "harness"
) -> dict[str, str]:
    """Role -> file name, for one configuration under one naming scheme.

    A steady-state configuration has no lifted input file, so it has **one**
    per-run deferral artifact and both roles resolve to it.  Which of the two
    templates names that single file has to be stated rather than derived: the
    two schemes mark opposite members of the pair — V3 marked the committed
    input file's artifact (``postsolve_nolift_``) and left the lifted one
    unmarked, and V4 marks the lifted one and leaves the committed one
    unmarked, because the committed input file is what most arms run.
    """
    if naming not in ARTIFACT_NAMES:
        raise KeyError(
            f"{naming!r} is not a known artifact naming scheme; "
            f"expected one of {tuple(ARTIFACT_NAMES)}"
        )
    names = ARTIFACT_NAMES[naming]
    resolved = {
        "coupling_state": names["coupling_state"].format(name=configuration),
        "write_sets": names["write_sets"].format(name=configuration),
        "test_sets": names["test_sets"].format(name=configuration),
    }
    if pulsed:
        resolved["defer_per_run"] = names["defer_per_run"].format(name=configuration)
        resolved["defer_per_run_lifted"] = names["defer_per_run_lifted"].format(
            name=configuration
        )
    else:
        single = names["defer_per_run_steady_state"].format(name=configuration)
        resolved["defer_per_run"] = single
        resolved["defer_per_run_lifted"] = single
    return resolved

#: Artifacts whose file name a path constant in the copied driver fixes.
DRIVER_FIXED_ARTIFACTS: dict[str, str] = {
    "node_write_sets": "node_writesets.json",
    "node_map": "dsm_node_map.json",
}

#: Artifacts the **measurement layer** reads and the driver never does.
#: Empty since V5 list item 10 removed the one entry (``function_counts``,
#: the weight of task A88's function-weighted twin tables); the mechanism —
#: a data file entered with its own source commit, checked by the ``data``
#: gate — stays for the next such artifact.
MEASUREMENT_ARTIFACTS: dict[str, str] = {
    # The two prior populations of the census test set (driver change DR11;
    # A100 (v5-test-set)): A89's eight-entry read-before-write sets and A92's
    # optimisation-path sets, entered from their own source commits.  Read
    # by the census stage (``experiment/test_sets.py``) to compare and to
    # union with what this tree measures; never by the driver.
    "test_set_prior_eight_entry": "test_set_prior_eight_entry.json",
    "test_set_prior_optimisation_path": "test_set_prior_optimisation_path.json",
}

#: Where a measurement artifact is copied **from**, by its name here, where
#: that is not the repository's shared data directory.  The priors above are
#: the prototype trial's own files.
MEASUREMENT_ARTIFACT_SOURCES: dict[str, str] = {
    "test_set_prior_eight_entry.json": "arch_surgery/coupling_subset_trial/rbw_sets.json",
    "test_set_prior_optimisation_path.json": "arch_surgery/coupling_subset_trial/optimisation_path_sets.json",
}

#: Artifact roles **generated by this folder's own stages** and committed:
#: their source is themselves, at the commit they were committed, and the
#: data gate checks that the committed file is byte-identical to that commit.
#: The census test sets (``--census write``) are the one such role.
GENERATED_ARTIFACT_ROLES: tuple[str, ...] = ("test_sets",)


#: Arms inactive on a steady-state configuration, with the reason recorded.
#: On k = 0 there is no burn-time coupling: the ownership rung has nothing to
#: move, so the two arms that carry it collapse onto their predecessors.
_STEADY_STATE_SKIPS = {
    "A1": "steady state (no burn-time coupling): A1 composes to A0",
    "B1": "steady state (no burn-time coupling): B1 composes to B0",
}


def default_configurations(
    *, input_dir: Path, data_dir: Path, naming: str = "harness"
) -> tuple[Config, ...]:
    """The three declared configurations, in the order used in every table.

    Component counts and figure-of-merit codes are the artifacts' and the
    input files' own; they are asserted against the files at preflight rather
    than trusted from here.  *naming* selects which spelling of the artifact file
    names to resolve — see :data:`ARTIFACT_NAMES`.
    """
    def make(
        name: str,
        *,
        pulsed: bool,
        fom: int,
        fom_name: str,
        nvar: int,
        ncon: int,
        n_components: int,
    ) -> Config:
        files = artifact_file_names(name, pulsed=pulsed, naming=naming)
        return Config(
            name=name,
            pulsed=pulsed,
            figure_of_merit=fom,
            figure_of_merit_name=fom_name,
            n_iteration_variables=nvar,
            n_constraints=ncon,
            input_path=input_dir / f"{name}.IN.DAT",
            coupling_state_path=data_dir / files["coupling_state"],
            write_sets_path=data_dir / files["write_sets"],
            test_sets_path=data_dir / files["test_sets"],
            defer_per_run_path=data_dir / files["defer_per_run"],
            defer_per_run_lifted_path=data_dir / files["defer_per_run_lifted"],
            n_coupling_components=n_components,
            skips={} if pulsed else dict(_STEADY_STATE_SKIPS),
        )

    return (
        make(
            "large_tokamak_nof",
            pulsed=True,
            fom=1,
            fom_name="Plasma major radius (minimised)",
            nvar=20,
            ncon=26,
            n_components=840,
        ),
        make(
            "low_aspect_ratio_DEMO",
            pulsed=True,
            fom=-14,
            fom_name="Pulse length (maximised)",
            nvar=19,
            ncon=25,
            n_components=846,
        ),
        make(
            "st_regression",
            pulsed=False,
            fom=-5,
            fom_name="Fusion gain (maximised)",
            nvar=14,
            ncon=18,
            n_components=827,
        ),
    )


def default_campaign(
    *, test_set: str | None = None, tau: float | None = None
) -> Campaign:
    """The production campaign: V4's own copy of PROCESS and its own data.

    A function, not a module-level instance: a settings object that anything
    can reach and rebind is the module global this file exists to avoid.  The
    copy is created by the task that owns ``PROCESS/`` and ``harness/data/``;
    until it exists the preflight reports the absence rather than falling back
    to another tree, which would measure code nobody asked for.

    ``test_set`` selects the campaign's test set (the runner's ``--test-set``;
    the census set by default, the fallback ``write_set`` under D39) and
    ``tau`` overrides the tolerance the test set is declared at (the runner's
    ``--tau``); both reach every job the campaign composes, one value each.
    """
    data_dir = HERE / "data"
    return Campaign(
        test_set=DEFAULT_TEST_SET if test_set is None else test_set,
        tau=tau,
        tree=EXPERIMENT_DIR / "PROCESS",
        data_dir=data_dir,
        # The committed input files are copied into the experiment's own data
        # directory too, so that a run reads nothing from outside this folder.
        input_dir=data_dir,
        runs_dir=EXPERIMENT_DIR / "runs",
        derived_input_dir=EXPERIMENT_DIR / "runs" / "input_files",
        configurations=default_configurations(
            input_dir=data_dir, data_dir=data_dir, naming="harness"
        ),
    )

