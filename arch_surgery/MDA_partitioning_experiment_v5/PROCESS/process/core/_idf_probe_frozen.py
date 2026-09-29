"""Frozen-input convergence instrument for task A19.

Imported **only** when ``PROCESS_IDF_PROBE=frozen``.  With any other value the
file is never imported and costs nothing, so switch-neutrality holds by
construction (the same argument as ``_idf_probe_modules``).

The question
------------

A2 measured ``S_1``, ``S_2``, ``S_3`` -- sweeps to per-module convergence --
*inside the coupled loop*, where module M2 is evaluated on sweep ``s`` reading
M1's sweep-``s`` output.  M2 is therefore chasing a moving target.  Under the
proposed partition, with ``times.t_plant_pulse_burn`` lifted so that no live
cross-module back edge remains, M1 is solved to convergence **first** and M2
then sees a *fixed* input.  ``S_2`` and ``S_3`` measured in the coupled loop
may therefore be biased high, which would bias A2's gate arithmetic against
the partition.

This instrument answers that by **replay**.  It builds no partition, adds no
design variable and changes no solver.  For a sampled subset of
``Caller.call_models`` invocations it re-runs the modules in isolation from a
saved copy of the data structure and then restores the data structure exactly,
so the optimisation trajectory is untouched.  Neutrality is gated on a
byte-identical MFILE against the ``control`` arm.

What is replayed
----------------

Let ``entry`` be the data-structure state at the top of ``call_models`` -- the
*previous* design point's converged state -- and ``post`` the state when the
idempotence loop returns.  For a sampled loop, after recording A2's ordinary
coupled-loop numbers:

1. restore ``entry``;
2. inject the design vector and iterate **M1's nodes alone** until M1's own
   state agrees between consecutive sub-sweeps  ->  ``S1_alone``.
   This is the *validation control*: M1 runs first and, once
   ``t_plant_pulse_burn`` is lifted, has no live back edge, so ``S1_alone``
   should reproduce A2's coupled ``S_1``.  If it does not, the isolation is
   unsound and that is the finding.
3. from that state -- M1 converged, M2 still holding the previous design
   point's values, which is exactly the warm start a partitioned solver would
   have -- iterate **M2's nodes alone**  ->  ``S2_frozen``;
4. then likewise **M3's nodes alone**  ->  ``S3_frozen``;
5. restore ``entry`` once more and iterate **M1 + Pulse** as a diagnostic
   ->  ``S1_pulse``.  ``Pulse`` is the articulation point and writes the one
   live coupler; if ``S1_alone`` misses A2's ``S_1`` but ``S1_pulse`` hits it,
   the difference is the burn-time edge rather than leaking state.
6. restore ``post`` and verify the restore field by field.

Everything the replay does is undone.  The only permanent effect is this
module's own bookkeeping.
"""

from __future__ import annotations

import copy
import os
from dataclasses import fields as dc_fields

import numpy as np

from process.core import _idf_probe_modules as M

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

#: Sample every Nth ``call_models`` of the ``grad`` phase (finite-difference
#: perturbations, 94-96 % of all calls).  1 = every one.
GRAD_STRIDE = int(os.environ.get("PROCESS_IDF_PROBE_FROZEN_GRAD_STRIDE", "10"))

#: Sample every Nth ``call_models`` of every other phase (``fn``,
#: ``grad_reconcile``, ``init``).  These are few, so the default takes all.
OTHER_STRIDE = int(os.environ.get("PROCESS_IDF_PROBE_FROZEN_OTHER_STRIDE", "1"))

#: Ceiling on sub-sweeps, matching ``Caller.call_models``'s own ceiling of 10.
MAX_SUBSWEEPS = int(os.environ.get("PROCESS_IDF_PROBE_FROZEN_MAX_SUBSWEEPS", "10"))

#: Also run the M2/M3 sub-solves without re-injecting the design vector at the
#: head of each sub-sweep, to show the choice does not carry the result.
NO_INJECT_VARIANT = os.environ.get(
    "PROCESS_IDF_PROBE_FROZEN_NOINJECT", "1"
) not in ("0", "", "false")

#: For the first N samples, record *which* fields keep a module live at each
#: sub-sweep, in both the full-sequence and the isolated replay.  This is what
#: identifies the mechanism when the two disagree.
TRACE_SAMPLES = int(os.environ.get("PROCESS_IDF_PROBE_FROZEN_TRACE", "8"))


# --------------------------------------------------------------------------
# State
# --------------------------------------------------------------------------

_models = None
_data = None
_seq: list | None = None  # [(node_name, callable), ...] in sweep order
_setx = None  # the *unwrapped* set_scaled_iteration_variable
_last_xc: list = [None]

_call_index = 0
_phase_counts: dict = {}
_sampled = False
_entry_state = None

_entry_burn: list = [None]
_samples: list = []
_live_full: dict = {}
_live_alone: dict = {}
_live_lift: dict = {}
_errors: list = []
_seq_check: dict = {}
_inject_overlap: dict = {}


# --------------------------------------------------------------------------
# Save / restore of the whole data structure
# --------------------------------------------------------------------------


def _save_state(data) -> list:
    """Exact copy of every data-structure field.

    Each entry keeps the *object* as well as its contents, so a restore puts
    back both the binding and the contents of the original array or list.  A
    model holding a direct reference to an array therefore still sees the
    restored values.
    """
    out = []
    for f in dc_fields(data):
        ns = getattr(data, f.name)
        for g in dc_fields(ns):
            v = object.__getattribute__(ns, g.name)
            if isinstance(v, np.ndarray):
                out.append((ns, g.name, v, v.copy()))
            elif isinstance(v, list):
                out.append((ns, g.name, v, copy.deepcopy(v)))
            else:
                out.append((ns, g.name, v, None))
    return out


def _restore_state(saved: list) -> None:
    prev_w, prev_r = M._CUR_WRITES, M._CUR_READS
    M._CUR_WRITES = None
    M._CUR_READS = None
    try:
        for ns, name, obj, content in saved:
            if content is not None:
                if isinstance(obj, np.ndarray):
                    obj[...] = content
                else:
                    obj[:] = copy.deepcopy(content)
            object.__setattr__(ns, name, obj)
    finally:
        M._CUR_WRITES = prev_w
        M._CUR_READS = prev_r


# --------------------------------------------------------------------------
# The model sequence, reproduced so that it can be filtered by module
# --------------------------------------------------------------------------


def _build_sequence(models, data) -> list:
    """Mirror ``Caller._call_models_once``'s dispatch, as (name, callable).

    The callables are the *raw* bound methods captured before
    ``_idf_probe_modules.install`` wrapped them, so a replay does not enter
    A2's node accounting at all.
    """
    from process.data_structure.blanket_variables import BlktModelTypes
    from process.models.tfcoil.base import TFConductorModel
    from process.models.tfcoil.superconducting import SuperconductingTFTurnType

    raw = _raw_calls
    seq: list = [("<x_inject>", _inject)]

    seq.append(("plasma_geom", raw["plasma_geom"]))
    seq.append(("build", raw["build"]))
    seq.append(("physics", raw["physics"]))

    if data.tfcoil.i_tf_sup == TFConductorModel.WATER_COOLED_COPPER:
        seq.append(("copper_tf_coil", raw["copper_tf_coil"]))
    if data.tfcoil.i_tf_sup == TFConductorModel.SUPERCONDUCTING:
        turn = SuperconductingTFTurnType(data.superconducting_tfcoil.i_tf_turn_type)
        if turn == SuperconductingTFTurnType.CABLE_IN_CONDUIT:
            seq.append(("cicc_sctfcoil", raw["cicc_sctfcoil"]))
        elif turn == SuperconductingTFTurnType.CROSS_CONDUCTOR:
            seq.append(("croco_sctfcoil", raw["croco_sctfcoil"]))
    if data.tfcoil.i_tf_sup == TFConductorModel.HELIUM_COOLED_ALUMINIUM:
        seq.append(("aluminium_tf_coil", raw["aluminium_tf_coil"]))

    seq.append(("pfcoil", raw["pfcoil"]))
    seq.append(("pulse", raw["pulse"]))
    seq.append(("divertor", raw["divertor"]))
    seq.append(("fw", raw["fw"]))
    seq.append(("shield", raw["shield"]))
    seq.append(("vacuum_vessel", raw["vacuum_vessel"]))

    if data.fwbs.i_blanket_type == BlktModelTypes.CCFE_HCPB:
        seq.append(("ccfe_hcpb", raw["ccfe_hcpb"]))
    elif data.fwbs.i_blanket_type == BlktModelTypes.DCLL:
        seq.append(("dcll", raw["dcll"]))

    seq.append(("cryostat", raw["cryostat"]))
    seq.append(("structure", raw["structure"]))

    if data.physics.itart == 1 and data.tfcoil.i_tf_sup != TFConductorModel.SUPERCONDUCTING:
        seq.append(("tfcoil", raw["tfcoil"]))

    seq.append(("power", raw["power"]))
    seq.append(("vacuum", raw["vacuum"]))
    seq.append(("buildings", raw["buildings"]))
    seq.append(("power.acpow", _acpow))
    seq.append(("power.plant_electric_production", raw["power.plant_electric_production"]))
    seq.append(("availability", raw["availability"]))
    seq.append(("water_use", raw["water_use"]))
    seq.append(("costs", raw["costs"]))
    return seq


_raw_calls: dict = {}


def _inject():
    xc, nvars = _last_xc[0]
    _setx(xc, nvars, _data)


def _acpow():
    _raw_calls["power.acpow"](output=False)


def _capture_raw(models) -> None:
    """Grab unwrapped bound methods before A2's instrument wraps them."""
    for attr in M._WRAP_RUN:
        obj = getattr(models, attr, None)
        if obj is not None and hasattr(obj, "run"):
            _raw_calls[attr] = obj.run
    _raw_calls["costs"] = models.costs.run
    _raw_calls["power.acpow"] = models.power.acpow
    _raw_calls["power.plant_electric_production"] = models.power.plant_electric_production


#: value of the one live cross-module coupler at the entry to the sampled
#: ``call_models``; ``_pin_coupler`` holds it fixed, emulating the lift.
_pinned = [None]


def _pin_coupler():
    _data.times.t_plant_pulse_burn = _pinned[0]


def _lift_sequence() -> list:
    """The full sweep sequence with the one live coupler pinned.

    A2 measured ``k = 1``: ``times.t_plant_pulse_burn``, written by ``Pulse``
    and read by ``physics``, is the only field whose cross-module read on a
    ``run()`` path consumes a later module's write *and* changes between
    sweeps.  The partition lifts it to the optimiser, which makes it constant
    within a ``call_models``.  Pinning it here reproduces that, and nothing
    else, inside the otherwise untouched sequence.
    """
    out = []
    for n, f in _seq:
        out.append((n, f))
        if n == "<x_inject>":
            out.append(("<pin_coupler>", _pin_coupler))
    return out


def _m1_plus_build() -> list:
    """M1's nodes plus ``build``, in sweep order.

    ``build`` belongs to M2 but is executed *between* M1's two nodes in the
    current sequence, so it is the one M2 node whose output M1 could consume
    within a sweep.  Tracked as a diagnostic only; the partition would run it
    after M1.
    """
    return [
        (n, f)
        for n, f in _seq
        if n == "<x_inject>" or M.NODE_MODULE.get(n) == "M1" or n == "build"
    ]


def _module_nodes(modules: tuple, *, inject: bool = True) -> list:
    out = []
    for name, fn in _seq:
        if name == "<x_inject>":
            if inject:
                out.append((name, fn))
            continue
        if M.NODE_MODULE.get(name) in modules:
            out.append((name, fn))
    return out


# --------------------------------------------------------------------------
# The sub-solve
# --------------------------------------------------------------------------


def _iterate(nodes: list, track: tuple, trace: dict | None = None) -> dict:
    """Iterate ``nodes`` until every module in ``track`` stops changing.

    The criterion is A2's, which is ``Caller.check_agreement``'s: for every
    node of the module, every field the node wrote on either of two
    consecutive sub-sweeps must satisfy ``np.allclose(rtol=1e-6, atol=1e-8)``
    when compared at that node's exit.  A count therefore has the same
    two-sweep floor and the same meaning as ``S_global``.

    Returns ``{module: {"S": int, "converged": bool}}`` plus ``"error"``.
    """
    got: dict = {}
    err = None
    prev: dict | None = None
    for s in range(1, MAX_SUBSWEEPS + 1):
        cur: dict = {}
        last = M._snapshot()
        for name, fn in nodes:
            writes: set = set()
            M._CUR_WRITES = writes
            try:
                fn()
            except Exception as exc:  # a module that cannot be iterated alone
                err = f"{name}: {type(exc).__name__}: {exc}"
            finally:
                M._CUR_WRITES = None
            if err:
                break
            vals = M._snapshot()
            writes |= M._diff_keys(last, vals)
            cur[name] = (vals, writes)
            last = vals
        if err:
            break
        if prev is not None:
            for mod in track:
                if mod in got:
                    continue
                live = False
                for name, (vals, wkeys) in cur.items():
                    if M.NODE_MODULE.get(name) != mod:
                        continue
                    p = prev.get(name)
                    if p is None:
                        live = True
                        break
                    pvals, pwkeys = p
                    for k in wkeys | pwkeys:
                        i = M._key_index[k]
                        if not M._agrees(pvals[i], vals[i]):
                            live = True
                            break
                    if live:
                        break
                if trace is not None:
                    diffs = []
                    for name, (vals, wkeys) in cur.items():
                        if M.NODE_MODULE.get(name) != mod:
                            continue
                        p = prev.get(name)
                        if p is None:
                            continue
                        pvals, pwkeys = p
                        diffs += [
                            f"{name}|{k[0]}.{k[1]}"
                            for k in sorted(wkeys | pwkeys)
                            if not M._agrees(pvals[M._key_index[k]], vals[M._key_index[k]])
                        ]
                    trace.setdefault(mod, {})[s] = diffs[:40]
                if not live:
                    got[mod] = {"S": s, "converged": True}
            if len(got) == len(track):
                break
        prev = cur
    out = {m: got.get(m, {"S": MAX_SUBSWEEPS, "converged": False}) for m in track}
    out["error"] = err
    return out


def _one(nodes: list, module: str, trace: dict | None = None) -> tuple:
    r = _iterate(nodes, (module,), trace)
    return r[module]["S"], r[module]["converged"], r["error"]


# --------------------------------------------------------------------------
# Hooks -- everything A2's instrument does, plus the replay
# --------------------------------------------------------------------------


def sweep(models=None, data=None) -> None:
    global _models, _data, _seq, _setx
    if models is not None and _models is None:
        import process.core.caller as _caller

        _models = models
        _data = data
        _setx = _caller.set_scaled_iteration_variable

        def _record_x(xc, nvars, dat):
            _last_xc[0] = (np.asarray(xc).copy(), int(nvars))
            return _setx(xc, nvars, dat)

        _caller.set_scaled_iteration_variable = _record_x
        _capture_raw(models)
    M.sweep(models, data)
    if _seq is None and _models is not None:
        _seq = _build_sequence(_models, _data)


def sweep_end() -> None:
    M.sweep_end()


def objective_begin() -> None:
    M.objective_begin()


def objective_end() -> None:
    M.objective_end()


def call_models_begin() -> None:
    global _sampled, _entry_state, _call_index
    M.call_models_begin()
    _call_index += 1
    _sampled = False
    _entry_state = None
    if _seq is None:
        return
    from process.core import _idf_probe as _p

    phase = _p._phase
    n = _phase_counts.get(phase, 0)
    _phase_counts[phase] = n + 1
    stride = GRAD_STRIDE if phase == "grad" else OTHER_STRIDE
    if stride > 0 and n % stride == 0:
        _sampled = True
        _entry_state = _save_state(_data)
        _entry_burn[0] = _data.times.t_plant_pulse_burn


def call_models_end(phase: str, converged: bool = True) -> None:
    M.call_models_end(phase, converged)
    if not _sampled or _entry_state is None:
        return
    rec = M._calls[-1] if M._calls else {}
    _replay(phase, rec)


def _replay(phase: str, coupled: dict) -> None:
    global _entry_state
    entry = _entry_state
    _entry_state = None

    post_vals = M._snapshot()
    post_state = _save_state(_data)

    out = {
        "call_index": _call_index,
        "phase": phase,
        "s_global": coupled.get("s_global"),
        "S1_coupled": coupled.get("M1"),
        "S2_coupled": coupled.get("M2"),
        "S3_coupled": coupled.get("M3"),
    }
    try:
        # (a) METHOD CONTROL.  Replay the *whole* sweep sequence from the same
        #     entry state and measure the same three modules.  This must
        #     reproduce the coupled-loop S_i exactly wherever they are not
        #     right-censored; where they are, it supplies the uncensored value
        #     the loop's own exit test never let us see.  If this does not
        #     reproduce them, the replay machinery is at fault and nothing
        #     below means anything.
        tr_full: dict = {}
        tr_alone: dict = {}
        tr_lift: dict = {}
        _restore_state(entry)
        full = _iterate(
            _module_nodes(("M1", "M2", "PULSE", "M3", "FF")), M.MODULES, tr_full
        )
        for mod in M.MODULES:
            out[f"S{mod[1]}_fullreplay"] = full[mod]["S"]
            out[f"S{mod[1]}_fullreplay_converged"] = full[mod]["converged"]
        out["fullreplay_error"] = full["error"]

        # (b) THE PARTITION CHAIN.  M1 alone, then M2 alone on M1's converged
        #     output with M2 warm-started from the previous design point, then
        #     M3 alone.
        _restore_state(entry)
        s1, c1, e1 = _one(_module_nodes(("M1",)), "M1", tr_alone)
        out.update({"S1_alone": s1, "S1_alone_converged": c1, "S1_alone_error": e1})

        s2, c2, e2 = _one(_module_nodes(("M2",)), "M2", tr_alone)
        out.update({"S2_frozen": s2, "S2_frozen_converged": c2, "S2_frozen_error": e2})

        s3, c3, e3 = _one(_module_nodes(("M3",)), "M3", tr_alone)
        out.update({"S3_frozen": s3, "S3_frozen_converged": c3, "S3_frozen_error": e3})

        # (c) DIAGNOSTICS on what M1 alone leaves out.  ``Pulse`` writes the
        #     one live cross-module coupler; ``build`` is the M2 node that runs
        #     *between* M1's two nodes in the current sequence.
        _restore_state(entry)
        sp, cp, ep = _one(_module_nodes(("M1", "PULSE")), "M1")
        out.update({"S1_pulse": sp, "S1_pulse_converged": cp, "S1_pulse_error": ep})

        _restore_state(entry)
        sb, cb, eb = _one(_m1_plus_build(), "M1")
        out.update({"S1_build": sb, "S1_build_converged": cb, "S1_build_error": eb})

        # (d) THE LIFT, emulated.  Same full sequence, but the one live
        #     coupler is pinned -- which is what lifting it to the optimiser
        #     does.  If the coupled-vs-isolated gap in M1 is the burn-time
        #     cycle rather than leaking state, this must land on S1_alone.
        _pinned[0] = _entry_burn[0]
        _restore_state(entry)
        lift = _iterate(_lift_sequence(), M.MODULES, tr_lift)
        for mod in M.MODULES:
            out[f"S{mod[1]}_liftreplay"] = lift[mod]["S"]
            out[f"S{mod[1]}_liftreplay_converged"] = lift[mod]["converged"]

        for acc, tr in ((_live_full, tr_full), (_live_alone, tr_alone), (_live_lift, tr_lift)):
            for mod, per_sweep in tr.items():
                d = acc.setdefault(mod, {})
                for fields in per_sweep.values():
                    for f in fields:
                        d[f] = d.get(f, 0) + 1
        if len(_samples) < TRACE_SAMPLES:
            out["trace_full"] = tr_full
            out["trace_alone"] = tr_alone
            out["trace_lift"] = tr_lift

        if NO_INJECT_VARIANT:
            # Same chain, but the design vector is injected once at the head
            # instead of at every sub-sweep.  The two can only differ if a
            # model overwrites a field the injection writes; ``inject_overlap``
            # in the summary reports whether any does.
            _restore_state(entry)
            _inject()
            a1, _, _ = _one(_module_nodes(("M1",), inject=False), "M1")
            a2, _, _ = _one(_module_nodes(("M2",), inject=False), "M2")
            a3, _, _ = _one(_module_nodes(("M3",), inject=False), "M3")
            out.update({
                "S1_alone_noinject": a1,
                "S2_frozen_noinject": a2,
                "S3_frozen_noinject": a3,
            })
    except Exception as exc:  # never let the replay break the run
        out["fatal"] = f"{type(exc).__name__}: {exc}"
        _errors.append(out["fatal"])
    finally:
        _restore_state(post_state)

    after = M._snapshot()
    bad = M._diff_keys(post_vals, after)
    out["restore_mismatch"] = len(bad)
    if bad:
        out["restore_mismatch_fields"] = sorted(f"{a}.{b}" for a, b in list(bad)[:20])
    _samples.append(out)


def summary() -> dict:
    base = M.summary()

    # Self-check: the replay's reconstruction of the model sequence must name
    # exactly the nodes A2's instrument saw execute inside a sweep.
    seen = {n for n, c in M._node_calls.items() if c and n != "objective_constraints"}
    mine = {n for n, _ in (_seq or [])}
    _seq_check.update({
        "nodes_seen_by_a2_instrument": sorted(seen),
        "nodes_in_replay_sequence": sorted(mine),
        "only_in_a2": sorted(seen - mine),
        "only_in_replay": sorted(mine - seen),
        "match": sorted(seen) == sorted(mine),
    })

    # Does re-injecting the design vector matter?  Only if a model overwrites
    # a field the injection writes.
    inj = set(M._writes_all.get("<x_inject>", ()))
    others: set = set()
    for n, ks in M._writes_all.items():
        if n != "<x_inject>":
            others |= ks
    _inject_overlap.update({
        "n_injected_fields": len(inj),
        "n_also_written_by_a_model": len(inj & others),
        "overlap": sorted(f"{a}.{b}" for a, b in (inj & others))[:40],
    })

    base["frozen"] = {
        "grad_stride": GRAD_STRIDE,
        "other_stride": OTHER_STRIDE,
        "max_subsweeps": MAX_SUBSWEEPS,
        "noinject_variant": NO_INJECT_VARIANT,
        "call_models_seen": _call_index,
        "phase_counts": dict(_phase_counts),
        "n_samples": len(_samples),
        "sequence_check": dict(_seq_check),
        "inject_overlap": dict(_inject_overlap),
        "errors": list(_errors)[:40],
        "live_fields_full": {m: dict(sorted(v.items(), key=lambda kv: -kv[1])[:60]) for m, v in _live_full.items()},
        "live_fields_alone": {m: dict(sorted(v.items(), key=lambda kv: -kv[1])[:60]) for m, v in _live_alone.items()},
        "live_fields_lift": {m: dict(sorted(v.items(), key=lambda kv: -kv[1])[:60]) for m, v in _live_lift.items()},
        "samples": _samples,
    }
    return base
