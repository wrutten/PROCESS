"""C9 -- the fixed-point engine.

Plain **Gauss-Seidel (Picard) iteration** over the model sequence.  It does not
reproduce PROCESS's idempotence loop; it replaces it with an implementation
whose convergence test is on the coupling state rather than on two derived
scalars.

Four things about it matter more than the code:

**The floor is 1 sweep, not 2.**  PROCESS's loop needs two sweeps only because
``objf`` and ``conf`` do not exist when it is entered, so it must evaluate once
purely to manufacture a comparand.  The entering state *is* ``y0``, so one
sweep gives ``y1 = G(y0)`` and ``||y1 - y0||`` is immediately testable.  Arm
``A0f`` keeps the floor at 2 on purpose, because that is the only way to
separate the floor's effect from the predicate's cost: they act in **opposite
directions**, so ``R -> A0`` alone cannot tell "neither effect exists" from
"two effects cancelled".

**No acceleration.**  Aitken or Anderson would be a legitimate variant point
and would confound with the topology change.  Not here.

**A cap is a detector, not a budget.**  Reaching the inner (20), outer (20) or
global (200 module-sweeps) cap marks the design point **invalid** for that arm.
The full sweep histogram is recorded so that pressure against a cap is visible
rather than inferred: if a noticeable fraction of points sit at a cap, the cap
has become a budget, and that is a reportable finding rather than something to
tune past.

**The exit audit is how matched final accuracy is enforced.**  On termination
every arm gets one further full sweep and the *same* global residual is
evaluated and recorded.  Accuracy is then verified per design point, never
assumed from a shared tolerance setting.
"""

from __future__ import annotations

import numpy as np

from .ystate import YSpec

INNER_CAP = 20
OUTER_CAP = 20
GLOBAL_MODULE_SWEEP_CAP = 200

#: PROCESS's own reference ceiling: ``Caller.call_models`` evaluates the models
#: up to 10 times and then raises.
REFERENCE_CAP = 10


class CapReached(Exception):
    def __init__(self, which: str):
        super().__init__(which)
        self.which = which


class Budget:
    """Counts, and the caps that make a count a detector."""

    def __init__(self, global_cap: int = GLOBAL_MODULE_SWEEP_CAP):
        self.node_calls = 0
        self.module_sweeps = 0
        self.global_cap = global_cap

    def charge_module_sweep(self) -> None:
        self.module_sweeps += 1
        if self.global_cap and self.module_sweeps > self.global_cap:
            raise CapReached("global")


# --------------------------------------------------------------------------
# The sweeper -- the only thing that touches PROCESS
# --------------------------------------------------------------------------


class Sweeper:
    """Runs model nodes, in the order the driver runs them.

    The node order is **measured**, not reconstructed: it comes from the
    harvest, which recorded the nodes ``_idf_probe_modules`` saw execute inside
    ``Caller._call_models_once``.  A19 had to mirror ``_call_models_once``'s
    switch dispatch by hand, which is the one part of that instrument that
    could silently drift from the driver; this cannot.

    Trap T7 (ten models call their own ``run()`` from ``output()``) does not
    arise here: the replay process never calls ``output()`` at all.
    """

    def __init__(self, models, data, node_order, x, nvars, m=None, pin=None):
        self.models = models
        self.data = data
        self.x = np.asarray(x, dtype=float)
        self.nvars = int(nvars)
        self.node_order = [n for n in node_order]
        self._callables = self._resolve(models, self.node_order)
        # A22: ``pin`` holds a set of ``"namespace.field"`` names at the value
        # they had when this Sweeper was built -- i.e. at the harvested entry
        # state, after ``restore``.  It is re-imposed after **every** node
        # call, so a model that writes a pinned field has that write discarded
        # before any later model can read it.  This is the counterfactual for
        # "the quantity has been lifted onto the optimiser and is therefore an
        # input to the loop, constant within one solve".  Empty by default:
        # with ``pin=None`` this class behaves exactly as A18 wrote it.
        self._pin = []
        if pin:
            for f in pin:
                ns_name, _, fld = f.partition(".")
                obj = getattr(data, ns_name)
                self._pin.append((obj, fld, object.__getattribute__(obj, fld)))
        from process.core.solver import constraints as _constraints
        from process.core.solver.iteration_variables import (
            set_scaled_iteration_variable,
        )
        from process.core.solver.objectives import objective_function

        self._setx = set_scaled_iteration_variable
        self._objective_function = objective_function
        self._constraint_eqns = _constraints.constraint_eqns
        nums = data.numerics
        # The length of the constraint vector ``Caller.call_models`` compares.
        # It is not always ``n_equality + n_inequality``: on the fsolve path
        # ``solver.py:383`` calls ``fcnvmc1`` with ``meq`` alone, so an
        # evaluation run's idempotence loop compares a 2-vector while its final
        # call compares a 25-vector.  Arm R reproduces that loop, so it takes
        # the value the harvest recorded for this design point and only falls
        # back to the total when the harvest predates that record.
        self._m = (
            int(m)
            if m
            else int(nums.n_equality_constraints)
            + int(nums.n_inequality_constraints)
        )

    @staticmethod
    def _resolve(models, node_order) -> dict:
        out = {}
        for name in node_order:
            if name == "<x_inject>":
                continue
            if name == "power.acpow":
                out[name] = lambda: models.power.acpow(output=False)
            elif name == "power.plant_electric_production":
                out[name] = models.power.plant_electric_production
            else:
                obj = getattr(models, name, None)
                if obj is None or not hasattr(obj, "run"):
                    raise AssertionError(
                        f"node {name!r} observed in the harvest has no "
                        f"run() on the model registry"
                    )
                out[name] = obj.run
        return out

    def inject(self) -> None:
        self._setx(self.x, self.nvars, self.data)

    def run_nodes(self, names, budget: Budget) -> None:
        """One pass: inject the design vector, then run ``names`` in order.

        The design vector is re-injected at the head of every pass, matching
        what ``_call_models_once`` does.  A19 §5.3 measured the alternative
        (inject once) and found identical counts in every loop of every
        scenario, so the convention is recorded, not defended.
        """
        self.inject()
        for obj, fld, v in self._pin:
            object.__setattr__(obj, fld, v)
        for n in names:
            self._callables[n]()
            budget.node_calls += 1
            for obj, fld, v in self._pin:
                object.__setattr__(obj, fld, v)

    def eval_objective(self):
        objf = self._objective_function(
            self.data.numerics.i_figure_merit, self.data
        )
        conf = self._constraint_eqns(self._m, -1, self.data)[0]
        return objf, np.asarray(conf).copy()

    @staticmethod
    def check_agreement(previous, current) -> bool:
        """``Caller.check_agreement``, reproduced character for character.

        Including the hidden ``atol = 1e-8`` and ``equal_nan=True``, because
        arm R exists precisely to measure what that predicate costs and what
        it lets through.
        """
        if isinstance(previous, float) or previous.shape == current.shape:
            return bool(np.allclose(previous, current, rtol=1.0e-6, equal_nan=True))
        return False


# --------------------------------------------------------------------------
# Solvers
# --------------------------------------------------------------------------


def _result(**kw) -> dict:
    base = {
        "valid": True,
        "converged": False,
        "cap_hit": None,
        "sweeps": 0,
        "module_sweeps": 0,
        "node_calls": 0,
        "outer": 0,
        "inner": {},
        "residual_trace": [],
        "moved_constants": [],
        "cross_converged_at": None,
    }
    base.update(kw)
    return base


def solve_flat(
    sweeper: Sweeper,
    spec: YSpec,
    nodes,
    tau: float,
    *,
    floor: int = 1,
    cap: int = OUTER_CAP,
    global_cap: int = GLOBAL_MODULE_SWEEP_CAP,
    cross_subset=None,
) -> dict:
    """Flat Gauss-Seidel over ``nodes``, converging on ``y``.

    ``cross_subset`` is the **DSM cross-check** (C10).  The coupling set is
    computed two ways -- from run-time instrumentation (set (b), which decides
    convergence here) and from the DSM's feedback edges (set (a), passed in as
    component indices).  The sweep at which each *would have* declared
    convergence is recorded, and every disagreement is a finding about the DSM
    rather than a nuisance: it goes in ``reports/DSM_VALIDATION.md``.
    """
    budget = Budget(global_cap)
    bound = spec.bind(sweeper.data)
    y_prev = YSpec.read(bound)
    trace = []
    moved: set = set()
    converged = False
    cap_hit = None
    cross_at = None
    m = 0
    try:
        for m in range(1, cap + 1):
            budget.charge_module_sweep()
            sweeper.run_nodes(nodes, budget)
            y = YSpec.read(bound)
            res = spec.residual(y_prev, y)
            trace.append(res.brief(tau))
            moved |= {spec.name(i) for i in res.moved_constant}
            if cross_subset is not None and cross_at is None:
                xres = spec.residual(y_prev, y, subset=cross_subset)
                if m >= floor and xres.converged(tau):
                    cross_at = m
            y_prev = y
            if m >= floor and res.converged(tau):
                converged = True
                break
        else:
            cap_hit = "outer"
    except CapReached as exc:
        cap_hit = exc.which
    return _result(
        valid=converged,
        converged=converged,
        cap_hit=cap_hit,
        sweeps=m,
        module_sweeps=budget.module_sweeps,
        node_calls=budget.node_calls,
        outer=m,
        residual_trace=trace,
        moved_constants=sorted(moved),
        cross_converged_at=cross_at,
    )


def solve_reference(
    sweeper: Sweeper,
    nodes,
    *,
    cap: int = REFERENCE_CAP,
) -> dict:
    """Arm R: ``Caller.call_models`` reproduced exactly.

    A **reference, not a competitor**.  Its predicate is agreement of ``objf``
    and ``conf`` under ``np.allclose(rtol=1e-6)`` -- with numpy's hidden
    ``atol = 1e-8`` and ``equal_nan=True`` -- and its structural floor of 2
    sweeps, both of which are what Phase A exists to measure.
    """
    budget = Budget(0)
    objf_prev = None
    conf_prev = None
    converged = False
    cap_hit = None
    m = 0
    trace = []
    for m in range(1, cap + 1):
        budget.charge_module_sweep()
        sweeper.run_nodes(nodes, budget)
        objf, conf = sweeper.eval_objective()
        if objf_prev is None and conf_prev is None:
            objf_prev, conf_prev = objf, conf
            trace.append({"objf": float(objf), "agree": None})
            continue
        agree = sweeper.check_agreement(
            objf_prev, objf
        ) and sweeper.check_agreement(conf_prev, conf)
        trace.append({"objf": float(objf), "agree": bool(agree)})
        if agree:
            converged = True
            break
        objf_prev, conf_prev = objf, conf
    if not converged:
        cap_hit = "reference_10"
    return _result(
        valid=converged,
        converged=converged,
        cap_hit=cap_hit,
        sweeps=m,
        module_sweeps=budget.module_sweeps,
        node_calls=budget.node_calls,
        outer=m,
        residual_trace=trace,
    )


def solve_block(
    sweeper: Sweeper,
    spec: YSpec,
    blocks,
    tau: float,
    *,
    floor: int = 1,
    inner_cap: int = INNER_CAP,
    outer_cap: int = OUTER_CAP,
    global_cap: int = GLOBAL_MODULE_SWEEP_CAP,
    recorder=None,
) -> dict:
    """Block Gauss-Seidel: an outer loop over blocks, inner solves inside.

    ``blocks`` is an ordered list of ``(label, nodes, y_subset, iterate)``.
    ``iterate`` is False for a block that feeds nothing back within itself --
    the articulation point ``Pulse`` and the feed-forward tail -- where an
    inner solve would be a pass with a guaranteed answer.

    **``k = 0`` is handled by falling out, not by a special case.**
    ``recorder`` (A22) is an optional object with ``inner(outer, label, s,
    res)`` and ``outer_pass(outer, res)`` methods.  It is handed the same
    :class:`Residual` objects the predicate already computed, so it can name
    the fields above ``tau`` without changing what is computed or when.  With
    ``recorder=None`` -- the default, and what every A18 arm passes -- this
    function is byte-for-byte the routine A18 measured.

    ``st_regression`` has ``i_pulsed_plant = 0``, so ``Pulse`` writes nothing
    and there is no coupler at all; the outer loop then converges on its first
    iteration because nothing a later block writes moves an earlier block's
    state.  That is a measurement, not an assumption, and the recorded outer
    count is what says whether it held.
    """
    budget = Budget(global_cap)
    bound = spec.bind(sweeper.data)
    y_outer_prev = YSpec.read(bound)
    inner_counts: dict = {lab: [] for lab, _n, _s, _it in blocks}
    inner_capped: dict = {lab: 0 for lab, _n, _s, _it in blocks}
    trace = []
    moved: set = set()
    converged = False
    cap_hit = None
    outer = 0
    try:
        for outer in range(1, outer_cap + 1):
            for label, nodes, subset, iterate in blocks:
                if not nodes:
                    inner_counts[label].append(0)
                    continue
                if not iterate:
                    budget.charge_module_sweep()
                    sweeper.run_nodes(nodes, budget)
                    inner_counts[label].append(1)
                    continue
                y_prev = YSpec.read(bound)
                s = 0
                inner_ok = False
                for s in range(1, inner_cap + 1):
                    budget.charge_module_sweep()
                    sweeper.run_nodes(nodes, budget)
                    y = YSpec.read(bound)
                    res = spec.residual(y_prev, y, subset=subset)
                    if recorder is not None:
                        recorder.inner(outer, label, s, res)
                    moved |= {spec.name(i) for i in res.moved_constant}
                    y_prev = y
                    if s >= floor and res.converged(tau):
                        inner_ok = True
                        break
                inner_counts[label].append(s)
                if not inner_ok:
                    inner_capped[label] += 1
                    raise CapReached("inner")
            y = YSpec.read(bound)
            res = spec.residual(y_outer_prev, y)
            trace.append(res.brief(tau))
            if recorder is not None:
                recorder.outer_pass(outer, res)
            moved |= {spec.name(i) for i in res.moved_constant}
            y_outer_prev = y
            if outer >= floor and res.converged(tau):
                converged = True
                break
        else:
            cap_hit = "outer"
    except CapReached as exc:
        cap_hit = exc.which
    return _result(
        valid=converged,
        converged=converged,
        cap_hit=cap_hit,
        sweeps=outer,
        module_sweeps=budget.module_sweeps,
        node_calls=budget.node_calls,
        outer=outer,
        inner={
            "counts": inner_counts,
            "capped": inner_capped,
            "total": {k: sum(v) for k, v in inner_counts.items()},
        },
        residual_trace=trace,
        moved_constants=sorted(moved),
    )


# --------------------------------------------------------------------------
# The exit audit -- matched final accuracy, verified per design point
# --------------------------------------------------------------------------


def exit_audit(sweeper: Sweeper, spec: YSpec, audit_nodes, tau: float) -> dict:
    """One further full sweep, and the same global residual for every arm.

    ``audit_nodes`` is the flat loop node set for the active hoist setting, so
    the audit is identical across arms at that setting.  The extra sweep is
    **not** charged to the arm's count; it is an audit, and its cost is
    reported separately.
    """
    bound = spec.bind(sweeper.data)
    y0 = YSpec.read(bound)
    # The values the arm would hand back, taken **at termination**, before the
    # audit sweep relaxes the state any further.  These are what the tau ladder
    # calibrates on: an ``objf`` measured after an extra sweep would understate
    # how much tau moved the answer.
    objf0, conf0 = sweeper.eval_objective()
    budget = Budget(0)
    sweeper.run_nodes(audit_nodes, budget)
    y1 = YSpec.read(bound)
    res = spec.residual(y0, y1)
    objf, conf = sweeper.eval_objective()
    out = res.brief(tau)
    out["converged_at_tau"] = res.converged(tau)
    out["objf_at_exit"] = float(objf0)
    out["conf_l2_at_exit"] = float(np.linalg.norm(conf0))
    out["conf_linf_at_exit"] = float(np.max(np.abs(conf0))) if conf0.size else 0.0
    out["objf"] = float(objf)
    out["conf_l2"] = float(np.linalg.norm(conf))
    out["conf_linf"] = float(np.max(np.abs(conf))) if conf.size else 0.0
    out["audit_node_calls"] = budget.node_calls
    out["above_tau_fields"] = [spec.name(i) for i in res.above(tau)[:20]]
    out["moved_constant_fields"] = [
        spec.name(i) for i in res.moved_constant[:20]
    ]
    out["discrete_mismatch_fields"] = [
        spec.name(i) for i in res.mismatch_discrete[:20]
    ]
    out["nan_new_fields"] = [spec.name(i) for i in res.nan_new[:20]]
    return out
