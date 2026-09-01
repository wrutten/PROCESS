"""Module to call physics and engineering models"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from tabulate import tabulate

from process.core import _idf_probe, constants
from process.core import process_output as po
from process.core.io.mfile import MFile
from process.core.process_output import OutputFileManager, ovarre
from process.core.solver import constraints
from process.core.solver import module_solve
from process.core.solver.iteration_variables import set_scaled_iteration_variable
from process.core.solver.objectives import objective_function
from process.data_structure.blanket_variables import BlktModelTypes
from process.data_structure.numerics import FiguresOfMerit, PROCESSRunMode
from process.models.tfcoil.base import TFConductorModel
from process.models.tfcoil.superconducting import SuperconductingTFTurnType

if TYPE_CHECKING:
    from process.core.model import DataStructure
    from process.main import Models

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------
# VP1 (framework hook F7a) -- the model call sequence is a driver choice.
#
# The first three tokamak nodes are unconditional and adjacent, and they are
# the only part of the sequence VP1 currently varies, so the variant point is
# a list of node names that ``_call_models_once`` walks.  Everything after
# them is switch-selected on the input deck and is left exactly as upstream
# wrote it; this is a permutation of three calls, not a scheduler.
#
# ``upstream`` is the order upstream PROCESS uses and is the default: with
# ``PROCESS_ARCH_SEQUENCE`` unset the loop below issues ``plasma_geom``,
# ``build``, ``physics`` in that order, which is what the three straight-line
# statements it replaced did.
#
# ``build_after_physics`` (task A3) moves ``build`` -- DSM row 5, module M2
# Coils -- from inside M1 Physics' span to the head of M2's span, so that M1
# becomes contiguous in the call order and a per-module solver can wrap it.
# The selection is resolved once at import, never per call.
_SEQUENCE_HEADS: dict[str, tuple[str, ...]] = {
    "upstream": ("plasma_geom", "build", "physics"),
    "build_after_physics": ("plasma_geom", "physics", "build"),
}

SEQUENCE_NAME: str = os.environ.get("PROCESS_ARCH_SEQUENCE", "").strip() or "upstream"

if SEQUENCE_NAME not in _SEQUENCE_HEADS:
    raise RuntimeError(
        f"PROCESS_ARCH_SEQUENCE={SEQUENCE_NAME!r} is not a recognised model "
        f"sequence; expected one of {tuple(_SEQUENCE_HEADS)} (or unset for "
        f"{'upstream'!r})."
    )

#: Resolved node order for the head of the tokamak model sequence.
SEQUENCE_HEAD: tuple[str, ...] = _SEQUENCE_HEADS[SEQUENCE_NAME]


# --------------------------------------------------------------------------
# VP2 (framework hook F7b) -- the feed-forward tail runs once, after the
# fixed point, instead of on every sweep.
#
# Some model nodes feed nothing back: nothing they write is read by any model
# that runs before them inside the idempotence loop.  Running them on every
# sweep is wasted work -- their inputs are final only once the loop has
# settled, and their outputs affect nothing the loop is deciding.  The hoist
# defers them out of the sweep and runs them once, after ``call_models`` has
# reached its fixed point.
#
# ``off`` is the default and is upstream behaviour exactly: every node runs on
# every sweep, and the deferral list is never even created.
#
# The **node set is derived at run time, not hard-coded** (framework item
# C2a).  Membership comes from the committed DSM node map, so it follows the
# arm: when a later variant point lifts the burn-time coupler out of the loop,
# ``pulse`` joins the feed-forward tail and the derivation picks it up without
# a list edit here.  What *is* fixed in this file is which call sites were
# made deferrable at all; ``_HOIST_UNCOVERED`` below turns a node that should
# be hoisted but has no deferrable call site into an import-time error rather
# than a silent in-loop evaluation.
_HOIST_MODULES: dict[str, frozenset[str]] = {
    "off": frozenset(),
    "feedforward": frozenset({"FF"}),
}

HOIST_NAME: str = os.environ.get("PROCESS_ARCH_HOIST", "").strip() or "off"

if HOIST_NAME not in _HOIST_MODULES:
    raise RuntimeError(
        f"PROCESS_ARCH_HOIST={HOIST_NAME!r} is not a recognised hoist "
        f"setting; expected one of {tuple(_HOIST_MODULES)} (or unset for "
        f"{'off'!r})."
    )

#: Node-map modules whose nodes are deferred out of the sweep.
HOIST_MODULES: frozenset[str] = _HOIST_MODULES[HOIST_NAME]

#: True when any node is hoisted.  With the hoist off this guards every branch
#: the variant point adds, so the default path is upstream's.
HOIST_ENABLED: bool = bool(HOIST_MODULES)

#: Call sites in :meth:`Caller._call_models_once` routed through
#: :meth:`Caller._node` and therefore capable of being deferred.  This is a
#: property of *this file*, not of the arm: it says which statements were
#: rewritten, not which nodes are hoisted.
DEFERRABLE_NODES: tuple[str, ...] = ("pulse", "water_use", "costs")

#: Figures of merit whose objective metric reads a field the node writes, and
#: which therefore cannot have that node deferred: the idempotence loop in
#: :meth:`Caller.call_models` tests ``objf`` and ``conf``, so hoisting a node
#: the objective reads would leave the loop converging on state it has
#: deliberately stopped updating.  ``objectives.py`` reads ``costs.coe``
#: (figure of merit 6) and ``costs.cdirt``/``costs.concost`` (7); all three are
#: written by the ``costs`` model.  No other figure of merit, and no
#: constraint equation, reads a field written by a hoisted node -- measured,
#: not assumed (task A13).
_FOM_READS_NODE: dict[str, frozenset[int]] = {
    "costs": frozenset({
        int(FiguresOfMerit.COST_OF_ELECTRICITY),
        int(FiguresOfMerit.CAPITAL_COST),
    }),
}

#: Committed DSM node map (framework component C8).  Read only when the hoist
#: is on; never read live from the dependency-analysis repository (trap T9).
NODE_MAP_PATH = (
    Path(__file__).resolve().parents[2]
    / "arch_surgery"
    / "docs"
    / "data"
    / "dsm_node_map.json"
)


def _resolve_hoist_nodes() -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Nodes this arm hoists, and any it should hoist but cannot.

    Returns
    -------
    tuple
        ``(hoisted, uncovered)`` -- the deferrable nodes the node map assigns
        to a hoisted module, and the mapped nodes that a hoisted module claims
        but that have no deferrable call site.
    """
    if not HOIST_ENABLED:
        return (), ()
    if not NODE_MAP_PATH.exists():
        raise RuntimeError(
            f"PROCESS_ARCH_HOIST={HOIST_NAME!r} needs the committed DSM node "
            f"map at {NODE_MAP_PATH}, which is not present."
        )
    nodes = json.loads(NODE_MAP_PATH.read_text())["nodes"]
    hoisted = tuple(
        n for n in DEFERRABLE_NODES if nodes.get(n, {}).get("module") in HOIST_MODULES
    )
    uncovered = tuple(
        sorted(
            n
            for n, entry in nodes.items()
            if entry.get("module") in HOIST_MODULES
            and entry.get("in_call_models_once")
            and n not in DEFERRABLE_NODES
        )
    )
    return hoisted, uncovered


HOIST_NODES, _HOIST_UNCOVERED = _resolve_hoist_nodes()

if _HOIST_UNCOVERED:
    raise RuntimeError(
        f"PROCESS_ARCH_HOIST={HOIST_NAME!r} would hoist {list(_HOIST_UNCOVERED)}, "
        f"but those nodes have no deferrable call site in Caller."
        f"_call_models_once. Add them to DEFERRABLE_NODES and route their "
        f"call sites through Caller._node."
    )


def resolved_hoist_tail(i_figure_merit: int) -> tuple[str, ...]:
    """The nodes actually deferred, for a run using *i_figure_merit*.

    The arm's node set less any node whose output the idempotence loop's own
    predicate reads.  Public so that a measurement harness can record the
    tail a run resolved without reconstructing the rule.
    """
    fom = abs(int(i_figure_merit))
    return tuple(
        n for n in HOIST_NODES if fom not in _FOM_READS_NODE.get(n, frozenset())
    )


# --------------------------------------------------------------------------
# VP4 (framework hook F7c) -- one flat loop, or a solve per module.
#
# Upstream runs the whole model sequence and tests two derived scalars for
# idempotence.  ``per_module`` instead iterates each DSM module to its own
# fixed point, in the block order A3's VP1 makes available by giving M1 a
# contiguous span, with an outer loop over whatever cross-module coupling
# remains.  The arm, its caps and its predicate live in
# ``process/core/solver/module_solve.py``; what lives here is the schedule and
# the node filter, because those are properties of *this* call sequence.
#
# ``off`` is the default and is upstream behaviour exactly: ``_active_nodes``
# stays ``None``, every node runs on every sweep, and ``call_models`` never
# enters the block path.
MODULE_SOLVE_NAME: str = module_solve.MODULE_SOLVE_NAME
MODULE_SOLVE_ENABLED: bool = module_solve.ENABLED

#: Model evaluations, counted as **individual model node calls** -- the unit
#: Phase A and A22 use (``engine.Budget.node_calls``), and the unit Phase B's
#: cost comparison is stated in.  ``numerics.n_model_calls`` counts *sweeps* of
#: ``_call_models_once``, which is not comparable between a flat loop and a
#: block schedule: a block sweep runs one module, not all of them.  A plain
#: integer increment per node call, on both arms, touching no float and
#: changing no branch a result depends on.
NODE_CALLS: list[int] = [0]

#: :data:`NODE_CALLS` at the moment the final-output path is entered.  The
#: cost figure Phase B compares is the **solve** phase: everything before
#: ``write_output_files``.  The output phase re-enters every model's ``run()``
#: from its ``output()`` (trap T7) and is identical work in both arms, so
#: pooling it into the cost would dilute the very quantity being compared.
NODE_CALLS_AT_OUTPUT: list[int | None] = [None]

#: Roll-up of the block schedule's own counts across every ``call_models`` of a
#: run.  Diagnostics: reported beside the cost figure, never gated on.
MODULE_SOLVE_TOTALS: dict = {
    "n_call_models": 0,
    "block_sweeps": 0,
    "outer_pass_hist": {},
    "inner_sweeps_by_block": {},
    "inner_solves_by_block": {},
    "moved_constants": set(),
    "n_call_models_with_moved_constant": 0,
    "n_failed": 0,
}


def _resolve_node_modules() -> dict[str, str]:
    """``node -> DSM module`` from the committed node map.

    Read only when VP4 is on, from the same committed artifact the hoist uses
    and never live from the dependency-analysis repository (trap T9).
    """
    if not MODULE_SOLVE_ENABLED:
        return {}
    if not NODE_MAP_PATH.exists():
        raise RuntimeError(
            f"PROCESS_ARCH_MODULE_SOLVE={MODULE_SOLVE_NAME!r} needs the "
            f"committed DSM node map at {NODE_MAP_PATH}, which is not present."
        )
    nodes = json.loads(NODE_MAP_PATH.read_text())["nodes"]
    # ``in_call_models_once`` is load-bearing, not decoration.  The map names
    # ``objective_constraints`` as an FF-module node, but it is the
    # objective/constraint evaluation, not a call site inside
    # ``_call_models_once``.  Including it gave the FF block a non-empty node
    # set that executed nothing -- 789 block sweeps of pure no-ops on
    # large_tokamak_nof, charged against the schedule and invisible in the node
    # count.  Found by reading the block census, not by inspection.
    return {
        n: e["module"]
        for n, e in nodes.items()
        if e.get("module") and e.get("in_call_models_once")
    }


NODE_MODULE: dict[str, str] = _resolve_node_modules()


def module_schedule(i_figure_merit: int) -> tuple[tuple, ...]:
    """``((label, frozenset(nodes), iterate), ...)`` for one run's outer pass.

    Membership comes from the committed node map, so a node that this deck
    never executes simply never appears -- the filter in :meth:`Caller._node`
    is a predicate on names, not a list of calls to make.

    **The hoist composes here, and that composition is the thing to get
    right.**  With VP2 on, the feed-forward nodes the active figure of merit
    does *not* read are removed from the ``FF`` block and returned separately
    as the tail, to be run once after the outer fixed point.  Any FF node the
    figure of merit *does* read -- ``costs`` under figures of merit 6 and 7 --
    stays inside the loop, in the ``FF`` block, exactly as ``resolved_hoist_tail``
    already decides for the flat arm.  Getting that wrong would either hoist a
    node the predicate reads or leave the whole tail in the loop, and the two
    failures look alike from outside.

    Returns
    -------
    tuple
        ``(schedule, tail)`` -- the blocks of one outer pass, and the nodes
        deferred to after the fixed point (empty when VP2 is off).
    """
    tail = (
        frozenset(resolved_hoist_tail(i_figure_merit))
        if HOIST_ENABLED
        else frozenset()
    )
    by_module: dict[str, set[str]] = {}
    for node, mod in NODE_MODULE.items():
        by_module.setdefault(mod, set()).add(node)
    schedule = []
    for label in module_solve.BLOCK_ORDER:
        nodes = frozenset(by_module.get(label, set()) - tail)
        schedule.append((label, nodes, label in module_solve.ITERATED))
    return tuple(schedule), tail


def _roll_up(stats: dict) -> None:
    """Fold one ``call_models``'s block counts into the run's totals."""
    t = MODULE_SOLVE_TOTALS
    t["n_call_models"] += 1
    t["block_sweeps"] += stats["block_sweeps"]
    key = str(stats["outer_passes"])
    t["outer_pass_hist"][key] = t["outer_pass_hist"].get(key, 0) + 1
    for label, total in stats["inner_totals"].items():
        t["inner_sweeps_by_block"][label] = (
            t["inner_sweeps_by_block"].get(label, 0) + total
        )
    for label, counts in stats["inner_counts"].items():
        t["inner_solves_by_block"][label] = t["inner_solves_by_block"].get(
            label, 0
        ) + len([c for c in counts if c])
    if stats["moved_constants"]:
        t["n_call_models_with_moved_constant"] += 1
    t["moved_constants"].update(stats["moved_constants"])
    if not stats["converged"]:
        t["n_failed"] += 1


class Caller:
    """Calls physics and engineering models."""

    def __init__(self, models: Models, data: DataStructure):
        """Initialise all physics and engineering models.

        To ensure that, at the start of a run, all physics/engineering
        variables are fully initialised with consistent values, the models are
        called with the initial optimisation parameters, x.

        Parameters
        ----------
        models :
            physics and engineering model objects
        data :
            data structure object to be passed on to the constraint evaluators
        """
        self.models = models
        self.data = data
        # VP2: the deferral list for the current sweep, or ``None`` when
        # nothing is deferred.  ``None`` is the default and the only value the
        # hoist-off path ever sees.
        self._pending: list | None = None
        # VP2: the tail resolved for the current ``call_models``.  Re-resolved
        # on every call rather than memoised: it depends on the deck's figure
        # of merit, and a scan may change the deck between calls.
        self._hoist_tail: frozenset[str] = frozenset()
        # VP4: the nodes the current block sweep may run, or ``None`` when the
        # whole sequence runs.  ``None`` is the default and the only value the
        # flat-loop path ever sees.
        self._active_nodes: frozenset[str] | None = None
        # VP4: the coupling-state spec, the per-module subsets its inner
        # solves test, and their provenance.  Loaded once.
        self._yspec = None
        self._yprov = None
        self._ysubsets: dict | None = None
        #: VP4 diagnostics for the last ``call_models`` -- block sweeps, outer
        #: passes and inner counts.  Reported, never gated on.
        self.module_solve_stats: dict | None = None

    # -- VP2 -------------------------------------------------------------

    def _resolve_hoist_tail(self) -> frozenset[str]:
        """The nodes this run defers out of the sweep.

        The arm's node set (``HOIST_NODES``) less any node the idempotence
        loop's own predicate reads.  ``call_models`` tests the objective
        function and the constraint residuals, so a node whose output the
        active figure of merit reads must keep running inside the loop --
        otherwise the loop would be testing state it has deliberately stopped
        updating, and would converge on a different criterion than upstream's.
        """
        if not HOIST_ENABLED:
            return frozenset()
        return frozenset(resolved_hoist_tail(self.data.numerics.i_figure_merit))

    def _acpow(self) -> None:
        """``power.acpow`` as a node callable.

        A method rather than a lambda so that the node table holds the same
        kind of object for every entry, and so nothing on the default path
        builds a closure per sweep.
        """
        self.models.power.acpow(output=False)

    def _node(self, name: str, run) -> None:
        """Run one model node now, defer it, or skip it for this block.

        Three variant points meet in these five lines, and the order matters:

        1. **VP4** -- when a block sweep is in progress, a node outside the
           block does not run at all.  This is checked first, so the hoist
           never collects a node during someone else's block.
        2. **VP2** -- a node in the resolved feed-forward tail is collected
           instead of run.  The block path never sets ``_pending``, because
           under VP4 the tail is a block of its own that runs once after the
           outer fixed point; this branch is the flat arm's.
        3. Otherwise the node runs, and is counted.
        """
        if self._active_nodes is not None and name not in self._active_nodes:
            return
        if self._pending is not None and name in self._hoist_tail:
            self._pending.append((name, run))
            return
        NODE_CALLS[0] += 1
        run()

    def _run_hoisted_tail(self, pending: list) -> None:
        """Run the deferred feed-forward nodes, once, in sequence order."""
        for _name, run in pending:
            run()

    @staticmethod
    def check_agreement(
        previous: float | np.ndarray, current: float | np.ndarray
    ) -> bool:
        """Compare previous and current arrays for agreement within a tolerance.

        Parameters
        ----------
        previous : float | np.ndarray
            value(s) from previous models evaluation
        current : float | np.ndarray
            value(s) from current models evaluation

        Returns
        -------
        bool
            whether values agree or not
        """
        # Check for same shape: mfile length can change between iterations
        if isinstance(previous, float) or previous.shape == current.shape:
            return np.allclose(previous, current, rtol=1.0e-6, equal_nan=True)
        return False

    # -- VP4 -------------------------------------------------------------

    def _sweep_block(self, xc: np.ndarray, nodes: frozenset) -> None:
        """One pass of ``_call_models_once`` restricted to *nodes*.

        The sequence itself is not duplicated: the same ``_call_models_once``
        walks the same switch dispatch in the same order, and ``_node`` drops
        the calls that do not belong to this block.  A second copy of the model
        sequence -- one measured, one not -- is how the variant silently stops
        computing what the baseline computes, so there is only ever one.
        """
        self._active_nodes = nodes
        try:
            self._call_models_once(xc)
        finally:
            self._active_nodes = None

    def _call_models_by_module(
        self, xc: np.ndarray, m: int
    ) -> tuple[float, np.ndarray]:
        """Block Gauss-Seidel over the DSM modules, then objective and constraints.

        Each iterated block is solved to its own fixed point on the coupling
        state before the next block runs; an outer loop closes the cross-module
        coupling.  The predicate is Phase A's, on ``y``, at ``tau`` -- never
        ``objf``/``conf``, which no single module determines (D14(c)).

        Raises
        ------
        ModuleSolveFailure
            if an inner solve, the outer loop or the global block budget hits
            its cap.  Decision **D15(d)**: a failed per-module solve raises and
            counts as a failed start, so the arms' failure modes are comparable.
        """
        if self.data.stellarator.istell != 0 or self.data.ife.ife != 0:
            raise module_solve.ModuleSolveFailure(
                "PROCESS_ARCH_MODULE_SOLVE is a tokamak-only variant point: "
                "the stellarator and IFE paths return from _call_models_once "
                "before any node the DSM partition names, so a block schedule "
                "over them would be a schedule over nothing."
            )

        if self._yspec is None:
            self._yspec, self._yprov = module_solve.load_spec()
            self._ysubsets, _ = module_solve.load_subsets(self._yspec)
        spec = self._yspec
        subsets = self._ysubsets
        tau = module_solve.TAU

        schedule, tail = module_schedule(self.data.numerics.i_figure_merit)
        bound = spec.bind(self.data)
        read = spec.read

        # VP4 never uses VP2's deferral list: under a block schedule the tail
        # is a block, run once after the outer fixed point.
        self._pending = None

        y_outer_prev = read(bound)
        block_sweeps = 0
        inner_counts: dict[str, list[int]] = {lab: [] for lab, _n, _i in schedule}
        outer_trace: list[dict] = []
        moved_constants: set = set()

        def charge() -> None:
            nonlocal block_sweeps
            block_sweeps += 1
            if block_sweeps > module_solve.GLOBAL_BLOCK_SWEEP_CAP:
                raise module_solve.ModuleSolveFailure(
                    f"global block-sweep cap "
                    f"({module_solve.GLOBAL_BLOCK_SWEEP_CAP}) reached at "
                    f"tau={tau:g}"
                )

        converged = False
        outer = 0
        for outer in range(1, module_solve.OUTER_CAP + 1):
            for label, nodes, iterate in schedule:
                if not nodes:
                    inner_counts[label].append(0)
                    continue
                if not iterate:
                    charge()
                    self._sweep_block(xc, nodes)
                    inner_counts[label].append(1)
                    continue
                # The inner test is restricted to the module's own write set,
                # as Phase A's block arm restricts it.  Not an optimisation:
                # ``ystate``'s predicate scores any component that is not
                # float-viewable in *either* snapshot as ``inf``, and in a
                # fresh process that is every field no model has written yet --
                # so an unrestricted inner test is held open for ever by a
                # field the running module cannot touch.
                subset = subsets.get(label)
                y_prev = read(bound)
                inner_ok = False
                s = 0
                for s in range(1, module_solve.INNER_CAP + 1):
                    charge()
                    self._sweep_block(xc, nodes)
                    y = read(bound)
                    res = spec.residual(y_prev, y, subset=subset)
                    moved_constants |= {
                        spec.name(i) for i in res.moved_constant
                    }
                    y_prev = y
                    if res.converged(tau):
                        inner_ok = True
                        break
                inner_counts[label].append(s)
                if not inner_ok:
                    self.module_solve_stats = self._module_stats(
                        block_sweeps, outer, inner_counts, outer_trace,
                        moved_constants, converged=False, cap_hit="inner",
                        tail=tail,
                    )
                    _roll_up(self.module_solve_stats)
                    raise module_solve.ModuleSolveFailure(
                        f"module {label} did not converge in "
                        f"{module_solve.INNER_CAP} inner sweeps at tau={tau:g}; "
                        f"max scaled residual {res.max:g} on "
                        f"{res.brief(tau)['argmax']}, "
                        f"{res.n_above(tau)} components above tau"
                    )
            y = read(bound)
            res = spec.residual(y_outer_prev, y)
            outer_trace.append(res.brief(tau))
            moved_constants |= {spec.name(i) for i in res.moved_constant}
            y_outer_prev = y
            if res.converged(tau):
                converged = True
                break

        if not converged:
            self.module_solve_stats = self._module_stats(
                block_sweeps, outer, inner_counts, outer_trace,
                moved_constants, converged=False, cap_hit="outer", tail=tail,
            )
            _roll_up(self.module_solve_stats)
            raise module_solve.ModuleSolveFailure(
                f"the outer loop over modules did not converge in "
                f"{module_solve.OUTER_CAP} passes at tau={tau:g}"
            )

        # VP2 inside VP4: the feed-forward tail runs once, on the converged
        # state.  Charged like any other block sweep.
        if tail:
            charge()
            self._sweep_block(xc, tail)

        if _idf_probe.ENABLED:
            _idf_probe.objective_begin()
        objf = objective_function(self.data.numerics.i_figure_merit, self.data)
        conf, _, _, _, _ = constraints.constraint_eqns(m, -1, self.data)
        if _idf_probe.ENABLED:
            _idf_probe.objective_end()

        self.module_solve_stats = self._module_stats(
            block_sweeps, outer, inner_counts, outer_trace, moved_constants,
            converged=True, cap_hit=None, tail=tail,
        )
        _roll_up(self.module_solve_stats)
        return objf, conf

    @staticmethod
    def _module_stats(
        block_sweeps, outer, inner_counts, outer_trace, moved_constants,
        *, converged, cap_hit, tail,
    ) -> dict:
        """The block schedule's own counts, for the run record."""
        return {
            "converged": converged,
            "cap_hit": cap_hit,
            "block_sweeps": block_sweeps,
            "outer_passes": outer,
            "inner_counts": {k: list(v) for k, v in inner_counts.items()},
            "inner_totals": {k: sum(v) for k, v in inner_counts.items()},
            "outer_residual_trace": outer_trace,
            "moved_constants": sorted(moved_constants),
            "hoisted_tail": sorted(tail),
        }

    def call_models(self, xc: np.ndarray, m: int) -> tuple[float, np.ndarray]:
        """Evaluate models until results are idempotent.

        Ensure objective function and constraints are idempotent before returning.

        Parameters
        ----------
        xc : np.ndarray
            optimisation parameters
        m : int
            number of constraints

        Returns
        -------
        Tuple[float, np.ndarray]
            objective function and constraints

        Raises
        ------
        RuntimeError
            if values are non-idempotent after successive
            evaluations
        """
        if _idf_probe.ENABLED:
            _idf_probe.call_models_begin()

        # VP4: the block schedule replaces the flat loop entirely -- including
        # its predicate, which decision D14(c) requires: a per-module solver
        # cannot test a global objective, because one module does not determine
        # it.  With VP4 off nothing below this line differs from upstream.
        if MODULE_SOLVE_ENABLED:
            objf, conf = self._call_models_by_module(xc, m)
            if _idf_probe.ENABLED:
                _idf_probe.call_models_end()
            return objf, conf

        objf_prev = None
        conf_prev = None

        # VP2: with the hoist on, the feed-forward nodes are collected instead
        # of run, and the last sweep's collection is run once the loop has
        # settled.  With the hoist off ``_pending`` stays ``None`` and nothing
        # below this line differs from upstream.
        if HOIST_ENABLED:
            self._hoist_tail = self._resolve_hoist_tail()
            pending: list | None = [] if self._hoist_tail else None
        else:
            pending = None

        # Evaluate models up to 10 times; any more implies non-converging values
        for _ in range(10):
            if pending is not None:
                pending.clear()
                self._pending = pending
            self._call_models_once(xc)
            self._pending = None
            # Evaluate objective function and constraints
            if _idf_probe.ENABLED:
                _idf_probe.objective_begin()
            objf = objective_function(self.data.numerics.i_figure_merit, self.data)
            conf, _, _, _, _ = constraints.constraint_eqns(m, -1, self.data)
            if _idf_probe.ENABLED:
                _idf_probe.objective_end()

            if objf_prev is None and conf_prev is None:
                # First run: run again to check idempotence
                logger.debug("New optimisation parameter vector being evaluated")
                objf_prev = objf
                conf_prev = conf
                continue

            # Check for idempotence
            if self.check_agreement(objf_prev, objf) and self.check_agreement(
                conf_prev, conf
            ):
                # Idempotent: no longer changing, so return
                logger.debug(
                    "Model evaluations idempotent, returning objective "
                    "function and constraints"
                )
                # VP2: the fixed point is reached, so the feed-forward tail
                # runs once, on the converged state.
                if pending:
                    self._run_hoisted_tail(pending)
                if _idf_probe.ENABLED:
                    _idf_probe.call_models_end()
                return objf, conf

            # Not idempotent: still changing, so evaluate models again
            logger.debug("Model evaluations not idempotent: evaluating again")
            objf_prev = objf
            conf_prev = conf

        if _idf_probe.ENABLED:
            _idf_probe.call_models_end(converged=False)

        raise RuntimeError(
            "After 10 model evaluations at the current optimisation parameter "
            "vector, values for the objective function and constraints haven't "
            "converged (don't produce idempotent values)."
        )

    def call_models_and_write_output(self, xc: np.ndarray, ifail: int):
        """Evaluate models until results are idempotent, then write output files.

        Ensure all outputs in mfile are idempotent before returning, by
        evaluating models multiple times. Typically used at the end of an
        optimisation, or in a non-optimising evaluation. Writes OUT.DAT and
        MFILE.DAT with final results.

        Parameters
        ----------
        xc : np.ndarray
            optimisation parameter
        ifail : int
            return code of solver

        Raises
        ------
        RuntimeError
            if values are non-idempotent after successive
            evaluations
        """
        # TODO The only way to ensure idempotence in all outputs is by comparing
        # mfiles at this stage
        previous_mfile_data = None

        # VP2: the hoist applies to the optimiser's evaluation path only.
        # This is the final-output path, where ``models.write`` re-enters every
        # model's ``run()`` from its ``output()`` anyway (trap T7), so nothing
        # is deferred here.
        self._pending = None

        try:  # noqa: PLW0717
            # Evaluate models up to 10 times; any more implies non-converging values
            for _ in range(10):
                # Divert OUT.DAT and MFILE.DAT output to scratch files for
                # idempotence checking
                OutputFileManager.open_idempotence_files(self.data.globals.output_prefix)
                self._call_models_once(xc)
                # Write mfile
                finalise(self.models, self.data, ifail)

                # Extract data from intermediate idempotence-checking mfile
                mfile_path = (self.data.globals.output_prefix) + "IDEM_MFILE.DAT"
                mfile = MFile(mfile_path)
                # Create mfile dict of float values: only compare floats
                mfile_data = {
                    var: val
                    for var in mfile.data
                    if isinstance(val := mfile.data[var].get_scan(-1), float)
                }

                if previous_mfile_data is None:
                    # First run: need another run to compare with
                    logger.debug(
                        "New mfile created: evaluating models again to check idempotence"
                    )
                    previous_mfile_data = mfile_data.copy()
                    continue

                # Compare previous and current mfiles for agreement
                nonconverged_vars = {}
                for var in previous_mfile_data:
                    previous_value = previous_mfile_data[var]
                    current_value = mfile_data.get(var, np.nan)
                    if self.check_agreement(previous_value, current_value):
                        continue
                    # Value has changed between previous and current mfiles
                    nonconverged_vars[var] = [
                        previous_value,
                        current_value,
                    ]

                if len(nonconverged_vars) == 0:
                    # Previous and current mfiles agree (idempotent)
                    logger.debug("Mfiles idempotent, returning")
                    # Divert OUT.DAT and MFILE.DAT output back to original files
                    # now idempotence checking complete
                    OutputFileManager.close_idempotence_files(
                        self.data.globals.output_prefix
                    )
                    # Write final output file and mfile
                    finalise(self.models, self.data, ifail)
                    return

                # Mfiles not yet idempotent: need to re-evaluate models
                logger.debug("Mfiles not idempotent, evaluating models again")
                previous_mfile_data = mfile_data.copy()

            # Values haven't all stabilised after 10 evaluations
            # Which variables are still changing?
            non_idempotent_warning = (
                "Model evaluations at the current optimisation parameter vector "
                "don't produce idempotent values in the final output."
            )
            non_idempotent_table = tabulate(
                [[k, v[0], v[1]] for k, v in nonconverged_vars.items()],
                headers=["Variable", "Previous value", "Current value"],
            )

            logger.warning(
                f"\033[93m{non_idempotent_warning}\n{non_idempotent_table}\033[0m",
                stacklevel=2,
            )

            # Close idempotence files, write final output file and mfile
            OutputFileManager.close_idempotence_files(self.data.globals.output_prefix)

        except Exception:
            # If exception in model evaluations delete intermediate idempotence
            # files to clean up
            OutputFileManager.close_idempotence_files(self.data.globals.output_prefix)
            raise
        else:
            finalise(
                self.models,
                self.data,
                ifail,
                non_idempotent_msg=non_idempotent_warning + "\n" + non_idempotent_table,
            )

    def _call_models_once(self, xc: np.ndarray):
        """Call the physics and engineering models.

        This method is the principal caller of all the physics and
        engineering models. Some are Fortran subroutines within modules, others
        will be methods on Python model objects.

        Parameters
        ----------
        xc : np.array
            Array of optimisation parameters
        """
        if _idf_probe.ENABLED:
            _idf_probe.sweep(self.models, self.data)

        # Number of active iteration variables
        nvars = len(xc)

        # Increment the call counter
        self.data.numerics.n_model_calls += 1

        # Convert variables
        set_scaled_iteration_variable(xc, nvars, self.data)

        # Perform the various function calls
        # Stellarator caller
        if self.data.stellarator.istell != 0:
            self.models.stellarator.run()
            # TODO Is this return safe?
            return

        # Inertial Fusion Energy calls
        if self.data.ife.ife != 0:
            self.models.ife.run()
            return

        # Tokamak calls
        # Plasma geometry model, machine build model (radial build) and
        # physics.  Their relative order is the VP1 variant point; see
        # SEQUENCE_HEAD at module level.  With PROCESS_ARCH_SEQUENCE unset
        # this is plasma_geom, build, physics -- the upstream order.
        for _head_node in SEQUENCE_HEAD:
            self._node(_head_node, getattr(self.models, _head_node).run)

        # Toroidal field coil model

        # Toroidal field coil resistive model
        if self.data.tfcoil.i_tf_sup == TFConductorModel.WATER_COOLED_COPPER:
            self._node("copper_tf_coil", self.models.copper_tf_coil.run)

        # Toroidal field coil superconductor model
        if self.data.tfcoil.i_tf_sup == TFConductorModel.SUPERCONDUCTING:
            if (
                SuperconductingTFTurnType(
                    self.data.superconducting_tfcoil.i_tf_turn_type
                )
                == SuperconductingTFTurnType.CABLE_IN_CONDUIT
            ):
                self._node("cicc_sctfcoil", self.models.cicc_sctfcoil.run)
            elif (
                SuperconductingTFTurnType(
                    self.data.superconducting_tfcoil.i_tf_turn_type
                )
                == SuperconductingTFTurnType.CROSS_CONDUCTOR
            ):
                self._node("croco_sctfcoil", self.models.croco_sctfcoil.run)

        if self.data.tfcoil.i_tf_sup == TFConductorModel.HELIUM_COOLED_ALUMINIUM:
            self._node("aluminium_tf_coil", self.models.aluminium_tf_coil.run)

        # Poloidal field and central solenoid model
        self._node("pfcoil", self.models.pfcoil.run)

        # Pulsed reactor model.  Deferrable (VP2): ``pulse`` is the
        # articulation point and joins the feed-forward tail only once the
        # burn-time coupler is lifted out of the loop.
        self._node("pulse", self.models.pulse.run)

        self._node("divertor", self.models.divertor.run)

        # First wall model
        self._node("fw", self.models.fw.run)

        self._node("shield", self.models.shield.run)

        self._node("vacuum_vessel", self.models.vacuum_vessel.run)

        # Blanket model
        """Blanket switch values
        No.  |  model
        ---- | ------
        1    |  CCFE HCPB model
        2    |  KIT HCPB model
        3    |  CCFE HCPB model with Tritium Breeding Ratio calculation
        4    |  KIT HCLL model
        5    |  DCLL model
        """
        if self.data.fwbs.i_blanket_type == BlktModelTypes.CCFE_HCPB:
            # CCFE HCPB model
            self._node("ccfe_hcpb", self.models.ccfe_hcpb.run)

        elif self.data.fwbs.i_blanket_type == BlktModelTypes.DCLL:
            # DCLL model
            self._node("dcll", self.models.dcll.run)

        self._node("cryostat", self.models.cryostat.run)

        # Structure Model
        self._node("structure", self.models.structure.run)

        # Tight aspect ratio machine model
        if (
            self.data.physics.itart == 1
            and self.data.tfcoil.i_tf_sup != TFConductorModel.SUPERCONDUCTING
        ):
            self._node("tfcoil", self.models.tfcoil.run)

        # Power model
        self._node("power", self.models.power.run)

        # Vacuum model
        self._node("vacuum", self.models.vacuum.run)

        # Buildings model
        self._node("buildings", self.models.buildings.run)

        # These two methods need to be run after vacuum/buildings otherwise
        # output changes quite a lot
        # TODO: split these two sections into a new model with a .run method
        # Plant AC power requirements
        self._node("power.acpow", self._acpow)

        # Plant heat transport pt 2 & 3
        self._node(
            "power.plant_electric_production",
            self.models.power.plant_electric_production,
        )

        # Availability model
        self._node("availability", self.models.availability.run)

        # Water usage in secondary cooling system.  Deferrable (VP2).
        self._node("water_use", self.models.water_use.run)

        # Costs model
        """Cost switch values
        No.  |  model
        ---- | ------
        0    |  1990 costs model
        1    |  2015 Kovari model
        2    |  Custom model
        """
        # Deferrable (VP2).
        self._node("costs", self.models.costs.run)

        # FISPACT and LOCA model (not used)- removed

        if _idf_probe.ENABLED:
            _idf_probe.sweep_end()


def finalise(models, data, ifail: int, non_idempotent_msg: str | None = None):
    """Routine to print out the final point in the scan.

    Writes to OUT.DAT and MFILE.DAT.

    Parameters
    ----------
    models : process.main.Models
        physics and engineering model objects
    data: DataStructure
        data structure object to provide data to evaluate the constraints
    ifail : int
        error flag
    non_idempotent_msg : None | str, optional
        warning about non-idempotent variables, defaults to None
    """
    if ifail == 1:
        po.oheadr(constants.NOUT, "Final Feasible Point")
    else:
        po.oheadr(constants.NOUT, "Final UNFEASIBLE Point")

    # Output relevant to no optimisation
    if data.numerics.i_process_run_mode == PROCESSRunMode.EVALUATION:
        output_evaluation(data)

    # Print non-idempotence warning to OUT.DAT only
    if non_idempotent_msg:
        po.oheadr(constants.NOUT, "NON-IDEMPOTENT VARIABLES")
        po.ocmmnt(constants.NOUT, non_idempotent_msg)

    # Write output to OUT.DAT and MFILE.DAT
    models.write(data, constants.NOUT)


def output_evaluation(data):
    """Write output for an evaluation run of PROCESS

    Parameters
    ----------
    data: DataStructure
        data structure object to provide data to evaluate the constraints
    """
    po.oheadr(constants.NOUT, "Numerics")
    po.ocmmnt(constants.NOUT, "PROCESS has performed an evaluation run.")
    po.oblnkl(constants.NOUT)

    # Evaluate objective function
    norm_objf = objective_function(data.numerics.i_figure_merit, data)
    po.ovarre(constants.MFILE, "Normalised objective function", "(norm_objf)", norm_objf)

    # Print the residuals of the constraint equations

    residual_error, value, residual, symbols, units = constraints.constraint_eqns(
        data.numerics.n_equality_constraints + data.numerics.n_inequality_constraints,
        -1,
        data,
    )

    labels = [
        data.numerics.lablcc[j - 1]
        for j in data.numerics.icc[
            : data.numerics.n_equality_constraints
            + data.numerics.n_inequality_constraints
        ]
    ]

    def _fmt(a, units):
        return [f"{c} {u}" for c, u in zip(a, units, strict=False)]

    po.write(
        constants.NOUT,
        tabulate(
            {
                "Constraint Name": labels,
                "Constraint Type": symbols,
                "Physical constraint": _fmt(value, units),
                "Constraint residual": _fmt(residual, units),
                "Normalised residual": residual_error,
            },
            headers="keys",
        ),
    )

    for i in range(data.numerics.n_equality_constraints):
        constraint_id = data.numerics.icc[i]
        po.ovarre(
            constants.MFILE,
            f"{labels[i]} normalised residue",
            f"(eq_con{constraint_id:03d})",
            residual_error[i],
        )

    for i in range(data.numerics.n_inequality_constraints):
        constraint_id = data.numerics.icc[data.numerics.n_equality_constraints + i]
        po.ovarre(
            constants.MFILE,
            f"{labels[data.numerics.n_equality_constraints + i]}",
            f"(ineq_con{constraint_id:03d})",
            residual_error[data.numerics.n_equality_constraints + i],
        )


def write_output_files(
    models: Models, data: DataStructure, ifail: int, *, runtime: float | None = None
):
    """Evaluate models and write output files (OUT.DAT and MFILE.DAT).

    Parameters
    ----------
    models : Models
        physics and engineering models
    data: DataStructure
        data structure object
    ifail : int
        solver return code
    """
    # VP4 accounting: the solve phase ends here.  One integer read, on both
    # arms; see NODE_CALLS_AT_OUTPUT.
    if NODE_CALLS_AT_OUTPUT[0] is None:
        NODE_CALLS_AT_OUTPUT[0] = NODE_CALLS[0]
    n = data.numerics.n_iteration_variables
    x = data.numerics.xcm[:n]
    # Call models, ensuring output mfiles are fully idempotent
    caller = Caller(models, data)
    if runtime is not None:
        ovarre(
            constants.MFILE,
            "Runtime of PROCESS in seconds",
            "(process_runtime)",
            runtime,
        )
    caller.call_models_and_write_output(
        xc=x,
        ifail=ifail,
    )
