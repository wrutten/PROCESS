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

The one module-level name is :data:`EXECUTION_APPROVED`.  It is the switch the
user flips, in the same commit that records the dated approval in
``EXPERIMENT_PLAN.md``'s status header.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

#: This file's directory: ``…/MDA_partitioning_experiment_v4/harness``.
HERE = Path(__file__).resolve().parent

#: ``…/MDA_partitioning_experiment_v4``.
EXPERIMENT_DIR = HERE.parent

#: The repository root of the checkout this file belongs to.
REPO_ROOT = EXPERIMENT_DIR.parent.parent

#: Master switch.  While False the runner executes preflight, gates and smoke
#: work only and refuses every campaign stage.  The user flips it in the same
#: commit that records the dated approval in EXPERIMENT_PLAN.md.
EXECUTION_APPROVED = False


# --------------------------------------------------------------------------
# one configuration = one optimisation problem
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Config:
    """One input file defining one optimisation problem.

    "Configuration" is V4's word for what V3 called a *deck* (terminology,
    README §3).  The deck is the *file*; the configuration is the *problem*.
    """

    #: Configuration name; also the frozen input file's stem.
    name: str
    #: Pulsed plant (burn-time coupling present, k = 1) or steady state (k = 0).
    pulsed: bool
    #: PROCESS's ``minmax``: positive minimises, negative maximises.
    figure_of_merit: int
    #: PROCESS's own description of that figure of merit.
    figure_of_merit_name: str
    #: Iteration variables and constraints the frozen deck declares.  The
    #: stencil regime's run count is 2 * (n_iteration_variables + 1) per arm,
    #: so this is read, never written into a table by hand.
    n_iteration_variables: int
    n_constraints: int
    #: The frozen configuration file.  Never edited (D9: the committed
    #: scenarios are the experiment's fixed input).
    input_path: Path
    #: The committed coupling-state artifact: which fields make up ``y`` and
    #: the measured scale of each.  The driver reads it too.
    coupling_state_path: Path
    #: The committed per-node write sets used by the block solves.
    write_sets_path: Path
    #: The per-run deferral set for a run of the *lifted* deck.
    defer_per_run_path: Path
    #: The per-run deferral set for a run of the *frozen* deck on a pulsed
    #: configuration — the same node set, stamped for the base constraint set.
    #: Phase A's block arms run the frozen deck (the pin owns the burn time,
    #: and pin + lifted deck is two owners, which the driver refuses), so they
    #: need this one.  On a steady-state configuration it is the same file.
    defer_per_run_frozen_deck_path: Path
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
            "defer_per_run": self.defer_per_run_path,
            "defer_per_run_frozen_deck": self.defer_per_run_frozen_deck_path,
        }

    def per_run_artifact(self, *, lifted_deck: bool) -> Path:
        """The per-run deferral artifact stamped for the deck actually run.

        One rule instead of V3's phase test: V3 chose ``postsolve_nolift_*``
        in ``phase_a`` and ``postsolve_*`` in ``v3_runner``, which is the same
        decision written twice.
        """
        return (
            self.defer_per_run_path
            if lifted_deck
            else self.defer_per_run_frozen_deck_path
        )


@dataclass(frozen=True)
class Removal:
    """A configuration removed from the campaign by a recorded decision."""

    configuration: str
    decision: str
    reason: str
    date: str


# --------------------------------------------------------------------------
# the campaign: the declared shape of the whole experiment
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Campaign:
    """Every declared setting of EXPERIMENT_PLAN.md §3.10, plus the paths.

    ``tree`` is the tree the harness runs against — the directory holding the
    ``process`` package.  It is a parameter because V4 runs its *own copy* of
    PROCESS and because a task testing the harness may point it at the
    repository root instead.  Whichever it is, it is asserted for equality in
    every measurement subprocess (trap T6).
    """

    # --- what to run against -------------------------------------------
    #: Directory holding the ``process`` package under test.
    tree: Path
    #: Directory holding the committed per-configuration artifacts.
    data_dir: Path
    #: Directory holding the frozen configuration files (never edited, D9).
    scenario_dir: Path
    #: Untracked bulk output.
    runs_dir: Path
    #: Derived (lifted) decks, produced by a committed stage.
    derived_decks_dir: Path

    # --- what to run ----------------------------------------------------
    configurations: tuple[Config, ...]
    removed_configurations: tuple[Removal, ...] = ()

    # --- campaign shape (EXPERIMENT_PLAN.md §3.10) -----------------------
    #: Seeds per configuration per arm, both phases.
    n_seeds: int = 25
    #: The two Phase A entry regimes: a displaced entry at ``delta``, and the
    #: optimiser's own finite-difference stencil points.
    entry_regimes: tuple[str, ...] = ("delta", "stencil")
    #: Entry displacement of the delta regime, and the Phase B start
    #: displacement.
    delta: float = 0.10
    #: The one tolerance of every converger, both phases, every arm (D23:
    #: the flat loop and each block loop alike).  There is no second
    #: tolerance; see switches.py on the retired inner-tolerance name.
    tau: float = 1e-6
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
    #: Convergence-predicate modes: the frozen ruler, and the trial that lets
    #: the denominator move.
    predicate_modes: tuple[str, ...] = ("frozen", "mixed")
    predicate_mode_default: str = "frozen"

    # --- derived --------------------------------------------------------
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

    def stencil_runs(self, config: Config) -> int:
        """Stencil-regime evaluations per arm on *config*: 2 (nvar + 1)."""
        return 2 * (config.n_iteration_variables + 1)


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
        "defer_per_run": "defer_per_run_{name}.json",
        "defer_per_run_frozen_deck": "defer_per_run_frozen_deck_{name}.json",
    },
    "repository": {
        "coupling_state": "ystate_a26_{name}.json",
        "write_sets": "writeset_a26_{name}.json",
        "defer_per_run": "postsolve_{name}.json",
        "defer_per_run_frozen_deck": "postsolve_nolift_{name}.json",
    },
}

#: Artifacts whose file name a path constant in the copied driver fixes.
DRIVER_FIXED_ARTIFACTS: dict[str, str] = {
    "node_write_sets": "node_writesets.json",
    "node_map": "dsm_node_map.json",
}


#: Arms inactive on a steady-state configuration, with the reason recorded.
#: On k = 0 there is no burn-time coupling: the ownership rung has nothing to
#: move, so the two arms that carry it collapse onto their predecessors.
_STEADY_STATE_SKIPS = {
    "A0p": "steady state (no burn-time coupling): A0p composes to A0",
    "B1": "steady state (no burn-time coupling): B1 composes to B0",
}


def default_configurations(
    *, scenario_dir: Path, data_dir: Path, naming: str = "harness"
) -> tuple[Config, ...]:
    """The three declared configurations, in the order used in every table.

    Component counts and figure-of-merit codes are the artifacts' and the
    decks' own; they are asserted against the files at preflight rather than
    trusted from here.  *naming* selects which spelling of the artifact file
    names to resolve — see :data:`ARTIFACT_NAMES`.
    """
    if naming not in ARTIFACT_NAMES:
        raise KeyError(
            f"{naming!r} is not a known artifact naming scheme; "
            f"expected one of {tuple(ARTIFACT_NAMES)}"
        )
    names = ARTIFACT_NAMES[naming]

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
        per_run = data_dir / names["defer_per_run"].format(name=name)
        return Config(
            name=name,
            pulsed=pulsed,
            figure_of_merit=fom,
            figure_of_merit_name=fom_name,
            n_iteration_variables=nvar,
            n_constraints=ncon,
            input_path=scenario_dir / f"{name}.IN.DAT",
            coupling_state_path=data_dir / names["coupling_state"].format(name=name),
            write_sets_path=data_dir / names["write_sets"].format(name=name),
            defer_per_run_path=per_run,
            defer_per_run_frozen_deck_path=(
                data_dir / names["defer_per_run_frozen_deck"].format(name=name)
                if pulsed
                else per_run
            ),
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


def default_campaign() -> Campaign:
    """The production campaign: V4's own copy of PROCESS and its own data.

    A function, not a module-level instance: a settings object that anything
    can reach and rebind is the module global this file exists to avoid.  The
    copy is created by the task that owns ``PROCESS/`` and ``harness/data/``;
    until it exists the preflight reports the absence rather than falling back
    to another tree, which would measure code nobody asked for.
    """
    tree = EXPERIMENT_DIR / "PROCESS"
    data_dir = HERE / "data"
    return Campaign(
        tree=tree,
        data_dir=data_dir,
        scenario_dir=REPO_ROOT / "arch_surgery" / "idf_probe" / "scenarios",
        runs_dir=EXPERIMENT_DIR / "runs",
        derived_decks_dir=EXPERIMENT_DIR / "runs" / "decks",
        configurations=default_configurations(
            scenario_dir=REPO_ROOT / "arch_surgery" / "idf_probe" / "scenarios",
            data_dir=data_dir,
            naming="harness",
        ),
    )


def repository_tree_campaign() -> Campaign:
    """The same campaign pointed at the repository's own tree and artifacts.

    Used by the self-check while V4's copy of PROCESS does not exist yet, and
    by anyone asking "does the harness still compose against the tree V3
    measured?".  It is never the production target: the production target is
    the copy, so that a driver change made for V4 cannot reach V2's or V3's
    numbers.
    """
    data_dir = REPO_ROOT / "arch_surgery" / "docs" / "data"
    scenario_dir = REPO_ROOT / "arch_surgery" / "idf_probe" / "scenarios"
    return Campaign(
        tree=REPO_ROOT,
        data_dir=data_dir,
        scenario_dir=scenario_dir,
        runs_dir=EXPERIMENT_DIR / "runs",
        derived_decks_dir=EXPERIMENT_DIR / "runs" / "decks",
        configurations=default_configurations(
            scenario_dir=scenario_dir, data_dir=data_dir, naming="repository"
        ),
    )
