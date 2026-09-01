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

    def _node(self, name: str, run) -> None:
        """Run one model node now, or defer it to the hoisted tail."""
        if self._pending is not None and name in self._hoist_tail:
            self._pending.append((name, run))
            return
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
        for _node in SEQUENCE_HEAD:
            getattr(self.models, _node).run()

        # Toroidal field coil model

        # Toroidal field coil resistive model
        if self.data.tfcoil.i_tf_sup == TFConductorModel.WATER_COOLED_COPPER:
            self.models.copper_tf_coil.run()

        # Toroidal field coil superconductor model
        if self.data.tfcoil.i_tf_sup == TFConductorModel.SUPERCONDUCTING:
            if (
                SuperconductingTFTurnType(
                    self.data.superconducting_tfcoil.i_tf_turn_type
                )
                == SuperconductingTFTurnType.CABLE_IN_CONDUIT
            ):
                self.models.cicc_sctfcoil.run()
            elif (
                SuperconductingTFTurnType(
                    self.data.superconducting_tfcoil.i_tf_turn_type
                )
                == SuperconductingTFTurnType.CROSS_CONDUCTOR
            ):
                self.models.croco_sctfcoil.run()

        if self.data.tfcoil.i_tf_sup == TFConductorModel.HELIUM_COOLED_ALUMINIUM:
            self.models.aluminium_tf_coil.run()

        # Poloidal field and central solenoid model
        self.models.pfcoil.run()

        # Pulsed reactor model.  Deferrable (VP2): ``pulse`` is the
        # articulation point and joins the feed-forward tail only once the
        # burn-time coupler is lifted out of the loop.
        self._node("pulse", self.models.pulse.run)

        self.models.divertor.run()

        # First wall model
        self.models.fw.run()

        self.models.shield.run()

        self.models.vacuum_vessel.run()

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
            self.models.ccfe_hcpb.run()

        elif self.data.fwbs.i_blanket_type == BlktModelTypes.DCLL:
            # DCLL model
            self.models.dcll.run()

        self.models.cryostat.run()

        # Structure Model
        self.models.structure.run()

        # Tight aspect ratio machine model
        if (
            self.data.physics.itart == 1
            and self.data.tfcoil.i_tf_sup != TFConductorModel.SUPERCONDUCTING
        ):
            self.models.tfcoil.run()

        # Power model
        self.models.power.run()

        # Vacuum model
        self.models.vacuum.run()

        # Buildings model
        self.models.buildings.run()

        # These two methods need to be run after vacuum/buildings otherwise
        # output changes quite a lot
        # TODO: split these two sections into a new model with a .run method
        # Plant AC power requirements
        self.models.power.acpow(output=False)

        # Plant heat transport pt 2 & 3
        self.models.power.plant_electric_production()

        # Availability model
        self.models.availability.run()

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
