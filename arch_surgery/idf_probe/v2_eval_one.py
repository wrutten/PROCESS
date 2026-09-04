#!/usr/bin/env python
"""Run ONE MDA evaluation -- one ``call_models`` -- with NO optimiser anywhere.

Phase A's entry point (V2 plan section 3, ``v2_config.INSTRUMENTATION``
``single_mda_eval``; built by task A34).  The per-call factor of the cost
decomposition is the cost of a single MDA evaluation under an architecture;
this script measures exactly that and nothing else:

1. initialise the deck exactly as a real run does (``SingleRun.__init__``,
   then the solver preamble ``load_iteration_variables`` /
   ``load_scaled_bounds`` -- everything a control optimisation executes
   before its first function evaluation, and nothing it does not);
2. optionally apply a seeded +/-delta perturbation to the COUPLING-STATE
   initial values, keyed on component NAME from a committed ystate artifact
   so every arm perturbs identically whatever its architecture switches;
3. execute EXACTLY ONE ``Caller.call_models`` at the deck's own design
   vector, under whatever architecture the environment selects
   (``PROCESS_ARCH_*`` -- this script sets none of them);
4. record the standard count fields for that single call;
5. take the UNCHARGED exit audit -- one further full sweep of the complete
   model set, the same instrument every arm gets, its node calls never
   charged to the arm -- and stop.

There is no optimiser in this process: no VMCON object is constructed, no
gradient is taken, no retry ladder exists.  Gate: the FLAT arm's single
eval at the unperturbed deck point reproduces the first solve-phase call of
A28's control optimisation bit-for-bit on the audit residual and the node
counts (``a34_instruments.py`` stage ``evalone_gate``, teeth included).

The perturbation
----------------
``--delta D --seed K`` multiplies every CONTINUOUS component of the
``--perturb-spec`` artifact by ``1 + D*u``, ``u`` in [-1, 1) drawn from a
hash of ``(K, "namespace.field")`` -- keyed on the component NAME, not its
index, so two arms whose specs enumerate identically perturb identically.
Following the house convention (``run_one.py``), ``--seed 0`` leaves the
deck's own point unperturbed even when ``--delta`` is given: start000 is
the deck point in every campaign this project has run.  Components whose
category is not CONTINUOUS are never touched (a perturbed discrete switch
is a different problem, not a perturbed start); a component that is
identically zero is unmoved by a multiplicative factor and is counted as
ineffective rather than pretended perturbed.  A pinned burn time is applied
AFTER the perturbation (Caller initialisation), so the pin owns the
variable regardless of the stream -- recorded, not silent.

Warm entry (A36)
----------------
``--entry-state <y_exit.json>`` writes a previous run's exact-hex exit
snapshot into the data structure at initialisation, BEFORE the seeded
perturbation, so the perturbation acts multiplicatively around the warm
state (at a cold initialisation 767/799 continuous components are
identically zero and a multiplicative stream cannot move them -- A34
section 5; at a warm state they are non-zero).  The snapshot must have
been taken against the SAME component spec as ``--perturb-spec``: the
loader sha-checks and refuses a mismatch.  After writing, the state is
read back and compared bit-for-bit against the snapshot
(``entry_state.readback_bitexact``), and the exact entry state
(post-restore, post-perturbation) is recorded to ``y_entry.json`` for the
campaign's cross-arm pairing check.  ``--node-census`` records per-node
evaluation counts for the measured single call (run_one's census pattern,
the I-10 insurance), frozen before the audit.

Isolation is mandatory, as everywhere: one run per process, own working
directory, ``PYTHONPATH`` pinned to the tree under test and the EXACT tree
asserted in-process (traps T6/T10).  Every quantity emitted is a count, a
name, a hash or a bit-exact hex float; wall/CPU time is context only.

Usage
-----
    PYTHONPATH=<tree> python v2_eval_one.py \
        --scenario st_regression --input <deck> --outdir <dir> \
        --expect-tree <tree> --perturb-spec <ystate_a26_*.json> \
        --exit-audit <ystate_*.json> [--delta 0.10 --seed 3] \
        [--entry-state <y_exit.json>] [--node-census]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import resource
import shutil
import sys
import time
import traceback
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from run_one import _hex, _hexes, _print_provenance, _provenance  # noqa: E402


# --------------------------------------------------------------------------
# exact snapshot serialisation (the pin gate compares two arms' exit states)
# --------------------------------------------------------------------------


def snap_value(v):
    """One coupling-state component, serialised exactly.

    Floats travel as hex literals (bit-exact); float arrays as hex element
    lists with dtype and shape; everything else in a form ``restore_value``
    rebuilds well enough for the ystate predicate's own ``_same`` /
    ``_float_view`` to test it.  Anything unrecognised is carried as a repr
    tagged as such -- visible, never silently dropped.
    """
    if isinstance(v, (float, np.floating)):
        return {"k": "f", "hex": float(v).hex()}
    if isinstance(v, (bool, np.bool_)):
        return {"k": "b", "v": bool(v)}
    if isinstance(v, (int, np.integer)):
        return {"k": "i", "v": int(v)}
    if v is None:
        return {"k": "none"}
    if isinstance(v, str):
        return {"k": "s", "v": v}
    if isinstance(v, np.ndarray):
        if v.dtype.kind == "f":
            return {
                "k": "af",
                "dtype": str(v.dtype),
                "shape": list(v.shape),
                "hex": [float(x).hex() for x in v.ravel().tolist()],
            }
        return {
            "k": "a",
            "dtype": str(v.dtype),
            "shape": list(v.shape),
            "v": v.ravel().tolist(),
        }
    if isinstance(v, list):
        return {"k": "l", "v": [snap_value(x) for x in v]}
    return {"k": "r", "v": repr(v)}


def restore_value(rec):
    """Inverse of :func:`snap_value`."""
    k = rec["k"]
    if k == "f":
        return float.fromhex(rec["hex"])
    if k == "b":
        return bool(rec["v"])
    if k == "i":
        return int(rec["v"])
    if k == "none":
        return None
    if k == "s":
        return rec["v"]
    if k == "af":
        a = np.array([float.fromhex(h) for h in rec["hex"]],
                     dtype=np.dtype(rec["dtype"]))
        return a.reshape(rec["shape"])
    if k == "a":
        return np.array(rec["v"], dtype=np.dtype(rec["dtype"])).reshape(
            rec["shape"]
        )
    if k == "l":
        return [restore_value(x) for x in rec["v"]]
    return rec["v"]  # "r": the repr string; exact-equality comparable


def _restricted_audit(artifact: str, scenario: str, tree: Path,
                      keys: list, vals: list, tau: float):
    """A38 (audit-rerun): the audit maximum over the in-loop write set.

    Membership is derived, never listed.  The post-solve artifact names
    NODES (the deck's committed classification -- the same file the driver
    validates); the committed run-time write census maps each node to the
    fields it writes for this scenario; the intersection with the audit
    spec's tested keys is the excluded set.  A prefix rule is deliberately
    not used: on ``st_regression`` the node list contains ``pulse``, which
    writes nothing there, and a prefix would either miss it or over-match.
    Returns ``(record, excluded_keys)``; the whole-state statistic is left
    exactly as it was.
    """
    art = json.loads(Path(artifact).read_text())
    nodes = list(art["post_solve_nodes"])
    census_path = tree / "arch_surgery" / "docs" / "data" / "node_writesets.json"
    census = json.loads(census_path.read_text())["per_scenario"]
    if scenario not in census:
        raise RuntimeError(
            f"{census_path} carries no write census for {scenario!r}; the "
            f"restricted audit would be guessed, so it is refused"
        )
    wb = census[scenario]["writes_by_node"]
    excl: set = set()
    for n in nodes:
        if n not in wb:
            raise RuntimeError(
                f"post-solve node {n!r} is absent from the {scenario} write "
                f"census {census_path}; refusing to derive the excluded set"
            )
        excl |= set(wb[n])
    excl_keys = excl & set(keys)
    kept = [(k, v) for k, v in zip(keys, vals) if k not in excl_keys]
    if kept:
        k_max, v_max = max(kept, key=lambda kv: kv[1])
    else:
        k_max, v_max = None, 0.0
    return {
        "artifact": str(artifact),
        "post_solve_nodes": nodes,
        "census": str(census_path),
        "n_excluded": len(excl_keys),
        "n_kept": len(kept),
        "excluded_sha256": hashlib.sha256(
            "\n".join(sorted(excl_keys)).encode()).hexdigest(),
        "max": v_max,
        "max_hex": _hex(v_max),
        "argmax": k_max,
        "n_above": sum(1 for _, v in kept if v >= tau),
        "tau": tau,
    }, excl_keys


def snapshot_record(spec, y):
    """The full exit state, keyed by component name, exactly."""
    return {
        "components_sha256": spec.components_sha256(),
        "n_components": len(spec.keys),
        "state": {spec.name(i): snap_value(y[i]) for i in range(len(y))},
    }


def restore_snapshot(spec, rec):
    """A snapshot file back into the list layout ``spec.residual`` takes."""
    if rec["components_sha256"] != spec.components_sha256():
        raise RuntimeError(
            "snapshot was taken against a different component spec: "
            f"{rec['components_sha256']} recorded, "
            f"{spec.components_sha256()} loaded"
        )
    st = rec["state"]
    return [restore_value(st[spec.name(i)]) for i in range(len(spec.keys))]


def write_entry_state(spec, data, rec) -> dict:
    """Write a snapshot's components into ``data`` at initialisation (A36).

    The warm-entry design: a run launched with ``--entry-state`` starts
    from a previous run's exact exit state.  :func:`restore_snapshot` has
    already refused a snapshot whose component spec sha does not match the
    run's spec.  Float arrays whose dtype and shape match the live value
    are written **element-wise in place** (preserving object identity, the
    way the perturbation multiplies in place); a component serialised as a
    bare ``repr`` cannot be rebuilt and is skipped BY NAME, loudly.  After
    writing, the whole state is read back and compared bit-for-bit against
    the snapshot: ``readback_bitexact`` is the extension gate's in-process
    evidence that the entry state IS the snapshot state.
    """
    y = restore_snapshot(spec, rec)
    bound = spec.bind(data)
    st = rec["state"]
    n_scalar = n_inplace = n_replaced = 0
    skipped_repr: list[str] = []
    replaced: list[str] = []
    for i, (ns, fld) in enumerate(bound):
        name = spec.name(i)
        if st[name]["k"] == "r":
            skipped_repr.append(name)
            continue
        target = y[i]
        if isinstance(target, np.ndarray):
            cur = object.__getattribute__(ns, fld)
            if (
                isinstance(cur, np.ndarray)
                and cur.shape == target.shape
                and cur.dtype == target.dtype
            ):
                cur[...] = target
                n_inplace += 1
            else:
                setattr(ns, fld, target)
                n_replaced += 1
                replaced.append(name)
        else:
            setattr(ns, fld, target)
            n_scalar += 1
    y_back = spec.read(bound)
    skipped = set(skipped_repr)
    mismatch = [
        spec.name(i)
        for i in range(len(y_back))
        if spec.name(i) not in skipped
        and snap_value(y_back[i]) != st[spec.name(i)]
    ]
    return {
        "n_components": len(spec.keys),
        "n_written_scalar": n_scalar,
        "n_written_array_inplace": n_inplace,
        "n_written_array_replaced": n_replaced,
        "array_identity_replaced": replaced,
        "n_skipped_repr": len(skipped_repr),
        "skipped_repr": skipped_repr,
        "readback_bitexact": not mismatch,
        "n_readback_mismatch": len(mismatch),
        "readback_mismatch_first": mismatch[:10],
    }


# --------------------------------------------------------------------------
# the perturbation stream
# --------------------------------------------------------------------------


def perturb_factor(seed: int, key: str, delta: float) -> float:
    """``1 + delta*u``, ``u`` in [-1, 1), from a hash of (seed, NAME).

    Keyed on the component NAME so that every arm of a phase applies the
    identical factor to the identical component, whatever its architecture
    switches or design-vector length (the a25 design, transposed from ixc
    numbers to coupling-component names).
    """
    h = hashlib.sha256(f"a34|{seed}|{key}".encode()).digest()
    u = int.from_bytes(h[:8], "big") / float(1 << 64)  # [0, 1)
    return 1.0 + delta * (2.0 * u - 1.0)


def apply_perturbation(spec, data, delta: float, seed: int) -> dict:
    """Multiply every CONTINUOUS component by its seeded factor, in place.

    Returns the full per-component record (factor, before/after hex of the
    argmax element for arrays), plus the census a report needs: how many
    components were eligible, moved, or were ineligible and why.
    """
    bound = spec.bind(data)
    rows = []
    n_moved = 0
    n_zero = 0
    skipped: dict[str, int] = {}
    for i, (ns, fld) in enumerate(bound):
        cat = spec.category[i]
        key = spec.name(i)
        if cat != "continuous":
            skipped[cat] = skipped.get(cat, 0) + 1
            continue
        f = perturb_factor(seed, key, delta)
        v = object.__getattribute__(ns, fld)
        if isinstance(v, (float, np.floating)):
            before = float(v)
            after = before * f
            setattr(ns, fld, after)
            moved = after != before
        elif isinstance(v, np.ndarray) and v.dtype.kind == "f":
            before_arr = v.copy()
            v *= f  # in place: preserves dtype, shape, object identity
            moved = bool(np.any(v != before_arr))
            j = int(np.argmax(np.abs(v - before_arr))) if v.size else 0
            before = float(before_arr.ravel()[j]) if v.size else 0.0
            after = float(v.ravel()[j]) if v.size else 0.0
        elif isinstance(v, list):
            try:
                arr = np.asarray(v)
            except Exception:
                skipped["continuous_unviewable"] = (
                    skipped.get("continuous_unviewable", 0) + 1
                )
                continue
            if arr.dtype.kind != "f":
                skipped["continuous_unviewable"] = (
                    skipped.get("continuous_unviewable", 0) + 1
                )
                continue
            new = [float(x) * f for x in v]
            setattr(ns, fld, new)
            moved = new != v
            before = float(v[0]) if v else 0.0
            after = float(new[0]) if new else 0.0
        else:
            skipped["continuous_unviewable"] = (
                skipped.get("continuous_unviewable", 0) + 1
            )
            continue
        n_moved += moved
        if not moved:
            n_zero += 1
        rows.append({
            "key": key,
            "factor": f,
            "factor_hex": float(f).hex(),
            "moved": bool(moved),
            "elem_before_hex": float(before).hex(),
            "elem_after_hex": float(after).hex(),
        })
    return {
        "delta": delta,
        "seed": seed,
        "keyed_on": "component NAME (sha256 of 'a34|<seed>|<name>')",
        "n_components_in_spec": len(spec.keys),
        "n_continuous_eligible": len(rows),
        "n_moved": n_moved,
        "n_unmoved_multiplicative_zero": n_zero,
        "n_skipped_by_category": skipped,
        "per_component": rows,
    }


# --------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--input", required=True,
                    help="the input deck (frozen scenario or derived deck)")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--expect-tree", required=True,
                    help="assert process.__file__ lives EXACTLY here (T6)")
    ap.add_argument(
        "--perturb-spec", required=True,
        help="committed ystate artifact whose component NAMES key the "
        "perturbation stream (the a26-mode artifact of the deck; loaded and "
        "validated even for an unperturbed run, so a wrong path fails "
        "loudly rather than silently on the first perturbed start)",
    )
    ap.add_argument("--delta", type=float, default=None,
                    help="perturbation size, e.g. 0.10")
    ap.add_argument("--seed", type=int, default=0,
                    help="start index; 0 leaves the deck point unperturbed "
                    "even when --delta is given (house convention)")
    ap.add_argument(
        "--entry-state", default=None,
        help="warm entry (A36): a y_exit.json snapshot from a previous "
        "run, written into the data structure at initialisation BEFORE the "
        "seeded perturbation, so the perturbation acts multiplicatively "
        "around the warm state.  Must have been taken against the SAME "
        "component spec as --perturb-spec (sha-checked; mismatch refused)",
    )
    ap.add_argument(
        "--node-census", action="store_true",
        help="record per-node evaluation counts for the measured single "
        "call (frozen before the audit; the audit's own extra counts are "
        "recorded separately) -- run_one's census pattern, the I-10 "
        "insurance",
    )
    ap.add_argument(
        "--exit-audit", required=True,
        help="committed ystate artifact the exit snapshot and the uncharged "
        "exit audit are measured with (may differ from --perturb-spec; a "
        "machinery gate against an A18-era record uses the A18 artifact "
        "here and says so)",
    )
    ap.add_argument(
        "--audit-exclude-postsolve", default=None,
        help="A38 (audit-rerun): the deck's committed post-solve artifact "
        "(postsolve_<deck>.json).  When given, the exit audit ALSO reports a "
        "RESTRICTED statistic over the components not written by that "
        "artifact's nodes -- node -> fields through the committed run-time "
        "write census (node_writesets.json), intersected with the audit "
        "spec's keys: the in-loop write set.  The whole-state statistic is "
        "computed exactly as before; this is additive",
    )
    args = ap.parse_args()

    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    src = Path(args.input)
    dst = outdir / f"{args.scenario}.IN.DAT"
    shutil.copy(src, dst)

    # A single-eval run is never a probe run; an inherited probe switch would
    # change what is measured without saying so.
    os.environ.pop("PROCESS_IDF_PROBE", None)

    result: dict = {
        "runner": "v2_eval_one",
        "scenario": args.scenario,
        "outdir": str(outdir),
        "input_file": str(src.resolve()),
        "python": sys.executable,
        "pythonpath": os.environ.get("PYTHONPATH"),
        "perturb_spec": str(args.perturb_spec),
        "exit_audit_spec": str(args.exit_audit),
        "audit_exclude_postsolve": args.audit_exclude_postsolve,
        "delta": args.delta,
        "seed": args.seed,
        "entry_state_arg": args.entry_state,
    }

    # ------------------------------------------------------------------
    # Prove which tree we imported before doing any work (traps T6/T10:
    # exact tree by path, never __version__, never a prefix test).
    # ------------------------------------------------------------------
    import process

    process_file = Path(process.__file__).resolve()
    result["process_file"] = str(process_file)
    expect = Path(args.expect_tree).resolve()
    actual_tree = process_file.parent.parent
    if actual_tree != expect:
        raise SystemExit(
            f"WRONG TREE: imported {process_file} (tree {actual_tree}), "
            f"expected exactly {expect}. Set PYTHONPATH={expect} for this "
            f"subprocess."
        )
    result["tree"] = str(actual_tree)
    result.update(_provenance(result["tree"]))
    _print_provenance(result)

    from process.core import caller as _caller
    from process.core.solver import module_solve as _module_solve
    from process.core.solver import subsolve as _subsolve

    # What the imported tree actually resolved (module attributes, never the
    # environment echoed back -- the A3/A13/A24 pattern).
    for k in ("PROCESS_ARCH_SEQUENCE", "PROCESS_ARCH_HOIST",
              "PROCESS_ARCH_LIFT", "PROCESS_ARCH_MODULE_SOLVE",
              "PROCESS_ARCH_TAU", "PROCESS_ARCH_INNER_TAU",
              "PROCESS_ARCH_YSTATE", "PROCESS_ARCH_WRITESET",
              "PROCESS_ARCH_OUTER", "PROCESS_ARCH_PIN_BURN_TIME"):
        result[f"env_{k}"] = os.environ.get(k)
    result["arch_sequence_name"] = getattr(_caller, "SEQUENCE_NAME", None)
    result["arch_hoist_name"] = getattr(_caller, "HOIST_NAME", None)
    result["arch_module_solve_name"] = getattr(
        _module_solve, "MODULE_SOLVE_NAME", None
    )
    result["arch_module_solve_tau"] = getattr(_module_solve, "TAU", None)
    result["arch_module_solve_inner_tau"] = getattr(
        _module_solve, "INNER_TAU", None
    )
    result["arch_outer_mode"] = getattr(_module_solve, "OUTER_MODE", None)
    result["arch_lift_sites"] = sorted(getattr(_subsolve, "LIFTED_SITES", ()))
    _pin = getattr(_subsolve, "PIN_BURN_TIME", None)
    result["arch_pin_burn_time"] = _pin
    result["arch_pin_burn_time_hex"] = _hex(_pin)
    result["arch_pin_enabled"] = bool(getattr(_subsolve, "PIN_ENABLED", False))

    from process.core.solver.iteration_variables import (
        load_iteration_variables,
        load_scaled_bounds,
    )
    from process.main import SingleRun

    ru0 = resource.getrusage(resource.RUSAGE_SELF)
    t0 = time.perf_counter()

    # ------------------------------------------------------------------
    # 1. Initialise exactly as a control run does, and stop where the
    #    control hands over to the optimiser.  SingleRun.__init__ reads the
    #    deck and initialises every variable; the solver preamble loads the
    #    iteration variables and their scaled bounds.  Nothing else runs
    #    before a control optimisation's first call_models, and nothing
    #    else runs here.
    # ------------------------------------------------------------------
    sr = SingleRun(str(dst), solver="vmcon", update_obsolete=True)
    data = sr.data
    load_iteration_variables(data)
    load_scaled_bounds(data)
    nums = data.numerics
    n = int(nums.n_iteration_variables)
    m = int(nums.n_equality_constraints) + int(nums.n_inequality_constraints)
    x = nums.xcm[:n]
    result["nvar"] = n
    result["n_constraints"] = m
    result["i_figure_merit"] = int(nums.i_figure_merit)

    # ------------------------------------------------------------------
    # 2. Warm entry (A36), then the coupling-state perturbation (or its
    #    recorded absence).  The order is fixed: the snapshot state is
    #    written FIRST, so a seeded perturbation acts multiplicatively
    #    around the warm state.
    # ------------------------------------------------------------------
    pspec, pprov = _module_solve.load_spec(args.perturb_spec)
    result["perturb_spec_provenance"] = pprov

    # Which spec components the design-vector injection owns at the head of
    # every sweep (identically in every arm, since deck and x are shared).
    # Recorded unconditionally (A36) so a gate that hand-perturbs a snapshot
    # can avoid components x would silently reset.
    try:
        from process.core.solver.iteration_variables import (
            ITERATION_VARIABLES,
        )

        itv_keys = set()
        for i in range(n):
            iv = ITERATION_VARIABLES[int(nums.ixc[i])]
            itv_keys.add(f"{iv.module}.{iv.target_name or iv.name}")
        spec_names = {pspec.name(i) for i in range(len(pspec.keys))}
        result["spec_keys_owned_by_x"] = sorted(itv_keys & spec_names)
    except Exception:
        result["spec_keys_owned_by_x"] = None

    result["entry_state"] = None
    if args.entry_state:
        snap_rec = json.loads(Path(args.entry_state).read_text())
        # restore_snapshot (inside write_entry_state) refuses a snapshot
        # whose component spec sha does not match the run's spec -- kept
        # deliberately: a wrong snapshot fails loudly, never silently.
        entry_census = write_entry_state(pspec, data, snap_rec)
        result["entry_state"] = {
            "path": str(Path(args.entry_state).resolve()),
            "components_sha256": snap_rec["components_sha256"],
            **entry_census,
        }

    perturbed = bool(args.delta) and bool(args.seed)
    if perturbed:
        pert = apply_perturbation(pspec, data, args.delta, args.seed)
        (outdir / "perturbation.json").write_text(json.dumps(pert, indent=2))
        result["perturbation"] = {
            k: v for k, v in pert.items() if k != "per_component"
        }
        result["perturbation"]["per_component_written_to"] = (
            "perturbation.json"
        )
        # Purely informational: perturbed components the design-vector
        # injection overwrites at the head of every sweep (identically in
        # every arm, since deck and x are shared).
        owned = result.get("spec_keys_owned_by_x")
        pert_keys = {r["key"] for r in pert["per_component"] if r["moved"]}
        result["perturbation"]["perturbed_keys_reinjected_from_x"] = (
            sorted(set(owned) & pert_keys) if owned is not None else None
        )
    else:
        result["perturbation"] = {
            "applied": False,
            "why": (
                "unperturbed point: --delta absent or --seed 0 (house "
                "convention: start000 is the unperturbed point -- the "
                "deck's own, or the snapshot's when --entry-state is given)"
            ),
        }

    # The exact coupling state this run is entered with (post-restore,
    # post-perturbation, before any Caller exists): the record Phase A's
    # cross-arm pairing check compares bit-for-bit (A36; the A34 799/799
    # check, transposed from perturbation rows to the full entry state).
    y_entry = pspec.read(pspec.bind(data))
    (outdir / "y_entry.json").write_text(
        json.dumps(snapshot_record(pspec, y_entry))
    )
    result["entry_state_recorded_to"] = "y_entry.json"

    # ------------------------------------------------------------------
    # 2b. Per-node census (A36; run_one's pattern, the I-10 insurance).
    #     Counts a node only when NODE_CALLS moved, so suppressed
    #     (post-solve) and deferred nodes are not miscounted.  Class-level,
    #     so the audit's fresh Caller is censused too; the measured call's
    #     census is FROZEN into the record before the audit runs.
    # ------------------------------------------------------------------
    result["node_census"] = None
    _ncounts: dict = {}
    _tailcounts: dict = {}
    if args.node_census:
        _orig_node = _caller.Caller._node

        def _node_censused(self, name, run):
            before = _caller.NODE_CALLS[0]
            _orig_node(self, name, run)
            if _caller.NODE_CALLS[0] != before:
                _ncounts[name] = _ncounts.get(name, 0) + 1

        _caller.Caller._node = _node_censused
        _orig_tail = _caller.Caller._run_hoisted_tail

        def _tail_censused(self, pending):
            for nm, _r in pending:
                _tailcounts[nm] = _tailcounts.get(nm, 0) + 1
            return _orig_tail(self, pending)

        _caller.Caller._run_hoisted_tail = _tail_censused

    # ------------------------------------------------------------------
    # 3. EXACTLY ONE call_models under the arm the environment selected.
    #    A failed call is a recorded taxonomy row, never a retry.
    # ------------------------------------------------------------------
    Caller = _caller.Caller  # noqa: N806
    node_calls_before = _caller.NODE_CALLS[0]
    status = "ok"
    objf = conf = None
    the_caller = None
    try:
        # Caller construction is inside the try: the pin's ixc-178 refusal
        # fires there, and a refusal is a recorded taxonomy row, not an
        # unhandled crash.
        the_caller = Caller(sr.models, data)
        objf, conf = the_caller.call_models(x, m)
    except _module_solve.ModuleSolveFailure:
        status = "unconverged"
        result["traceback"] = traceback.format_exc()
    except Exception:
        status = "crashed"
        result["traceback"] = traceback.format_exc()
    result["status"] = status
    result["wall_s"] = time.perf_counter() - t0
    ru1 = resource.getrusage(resource.RUSAGE_SELF)
    result["cpu_s"] = (ru1.ru_utime - ru0.ru_utime) + (
        ru1.ru_stime - ru0.ru_stime
    )
    result["maxrss_kb"] = ru1.ru_maxrss
    try:
        result["loadavg"] = os.getloadavg()
    except OSError:
        result["loadavg"] = None

    # ------------------------------------------------------------------
    # 4. The standard count fields, for this single call.
    # ------------------------------------------------------------------
    result["node_calls_single_eval"] = _caller.NODE_CALLS[0] - node_calls_before
    result["node_calls_counter_total"] = _caller.NODE_CALLS[0]
    result["n_model_calls_sweeps"] = int(nums.n_model_calls)
    if args.node_census:
        result["node_census"] = {
            "counted": dict(_ncounts),
            "flat_tail": dict(_tailcounts),
            "note": (
                "the measured single call only; frozen here, before the "
                "uncharged exit audit runs"
            ),
        }
    _tot = dict(_caller.MODULE_SOLVE_TOTALS)
    _tot["moved_constants"] = sorted(_tot.get("moved_constants", ()))
    result["module_solve_totals"] = _tot
    result["module_solve_stats"] = (
        the_caller.module_solve_stats if the_caller is not None else None
    )
    result["arch_block_schedule"] = (
        [
            [lab, sorted(ns), bool(it)]
            for lab, ns, it in _caller.module_schedule(nums.i_figure_merit)[0]
        ]
        if getattr(_caller, "MODULE_SOLVE_ENABLED", False)
        else None
    )
    if objf is not None:
        result["values"] = {
            "objf": float(objf),
            "conf_l2": float(np.sqrt(np.sum(np.square(conf)))),
        }
        result["exact"] = {
            "objf": _hex(objf),
            "conf": _hexes(conf),
        }
    result["t_plant_pulse_burn"] = float(data.times.t_plant_pulse_burn)
    result["t_plant_pulse_burn_hex"] = _hex(data.times.t_plant_pulse_burn)
    if result["arch_pin_enabled"]:
        result["pin_intact_at_exit"] = (
            float(data.times.t_plant_pulse_burn) == _pin
        )

    # ------------------------------------------------------------------
    # 4b. The lift residual (A36): the pinned/lifted component's
    #     inconsistency at the exit state, measured by the SAME function
    #     constraint 93 evaluates (``burn_time_residual`` -- a pure
    #     function; nothing runs, nothing mutates).  Read here, BEFORE the
    #     audit sweep mutates the state.  Reported separately and excluded
    #     from Phase A's similarity statistic (plan section 3: it is the
    #     pin, not an error).  Recorded for every arm: in a converged flat
    #     arm it reads ~0; in a pinned arm it is the price of the pin.
    # ------------------------------------------------------------------
    result["lift_residual"] = None
    if status == "ok":
        try:
            if int(data.pulse.i_pulsed_plant) == 1:
                from process.models.pulse import burn_time_residual

                raw = burn_time_residual(
                    float(data.times.t_plant_pulse_burn),
                    float(data.pf_coil.vs_cs_pf_total_burn),
                    float(data.physics.v_plasma_loop_burn),
                    float(data.times.t_plant_pulse_fusion_ramp),
                )
                comp = "times.t_plant_pulse_burn"
                scale = None
                for i in range(len(pspec.keys)):
                    if pspec.name(i) == comp:
                        scale = float(pspec.scale[i])
                        break
                result["lift_residual"] = {
                    "component": comp,
                    "raw_s": raw,
                    "raw_hex": _hex(raw),
                    "scale": scale,
                    "scaled_abs": (abs(raw) / scale) if scale else None,
                    "pinned": result["arch_pin_enabled"],
                    "note": (
                        "burn_time_residual (the function constraint 93 "
                        "evaluates) at the exit state; excluded from the "
                        "similarity statistic (plan section 3)"
                    ),
                }
            else:
                result["lift_residual"] = {
                    "inactive": (
                        "i_pulsed_plant != 1: Pulse writes no burn time "
                        "(A25 section 2.3); nothing lifted or pinned here"
                    ),
                }
        except Exception:
            result["lift_residual"] = {"error": traceback.format_exc()}

    # ------------------------------------------------------------------
    # 5. Exit snapshot + the uncharged exit audit, then stop.  The audit is
    #    the identical instrument every arm gets: a fresh Caller, nothing
    #    hoisted, no block filter, one further full sweep; its node calls
    #    are counted and reported and never charged to the arm (the count
    #    above was frozen before this line).  It runs only from a state the
    #    arm itself terminated in -- an unconverged or crashed call has no
    #    exit state to audit, and that absence is recorded, not papered
    #    over.
    # ------------------------------------------------------------------
    result["exit_state_written_to"] = None
    result["exit_audit"] = None
    if status == "ok":
        try:
            aspec, aprov = _module_solve.load_spec(args.exit_audit)
            abound = aspec.bind(data)
            y0 = aspec.read(abound)
            (outdir / "y_exit.json").write_text(
                json.dumps(snapshot_record(aspec, y0))
            )
            result["exit_state_written_to"] = "y_exit.json"
            n_before = _caller.NODE_CALLS[0]
            Caller(sr.models, data)._call_models_once(x)
            y1 = aspec.read(abound)
            res = aspec.residual(y0, y1)
            tau = getattr(_module_solve, "TAU", 1e-6)
            # A38 (audit-rerun): the per-component scaled residual vector is
            # ALWAYS written beside the record, so a differently restricted
            # statistic can be recomputed offline next time.  V2's records
            # held only max / argmax / count, which is why the corrected
            # statistic needed a re-run rather than a re-tally.
            vec_keys = [aspec.name(int(i)) for i in res.idx_c]
            vec_vals = [float(v) for v in res.scaled]
            audit_vec = {
                "components_sha256": aprov.get("components_sha256"),
                "n_components": aprov.get("n_components"),
                "n_continuous_tested": len(vec_keys),
                "tau": tau,
                "scaled": dict(zip(vec_keys, vec_vals)),
                "scaled_hex": {k: _hex(v) for k, v in zip(vec_keys, vec_vals)},
                "discrete_mismatch": [
                    aspec.name(i) for i in res.mismatch_discrete],
                "moved_constant": [aspec.name(i) for i in res.moved_constant],
                "nan_new": [aspec.name(i) for i in res.nan_new],
            }
            restricted = None
            if args.audit_exclude_postsolve:
                restricted, excl_keys = _restricted_audit(
                    args.audit_exclude_postsolve, args.scenario,
                    Path(result["tree"]), vec_keys, vec_vals, tau,
                )
                audit_vec["excluded_keys"] = sorted(excl_keys)
            (outdir / "audit_residual.json").write_text(json.dumps(audit_vec))
            result["exit_audit"] = {
                "ystate": str(args.exit_audit),
                "components_sha256": aprov.get("components_sha256"),
                "n_components": aprov.get("n_components"),
                "tau_for_the_brief": tau,
                "residual_max": res.max,
                "residual_max_hex": _hex(res.max),
                "brief": res.brief(tau),
                "residual_vector_written_to": "audit_residual.json",
                "restricted": restricted,
                "audit_node_calls": _caller.NODE_CALLS[0] - n_before,
                "node_census_audit_extra": (
                    {
                        k: v - (result["node_census"]["counted"].get(k, 0))
                        for k, v in _ncounts.items()
                        if v - (result["node_census"]["counted"].get(k, 0))
                    }
                    if args.node_census and result["node_census"]
                    else None
                ),
                "charged_to_the_arm": False,
                "note": (
                    "one further full sweep of the complete model set at the "
                    "single eval's exit; identical instrument in every arm; "
                    "node_calls_single_eval was frozen before it ran.  The "
                    "sweep mutates the state, which is why this runner stops "
                    "here and y_exit.json was written first."
                ),
            }
        except Exception:
            result["exit_audit"] = {"error": traceback.format_exc()}
    else:
        result["exit_audit"] = {
            "skipped": f"status {status!r}: no exit state to audit",
        }

    (outdir / "metrics.json").write_text(json.dumps(result, indent=2))
    brief = {k: v for k, v in result.items()
             if k not in ("exact", "traceback")}
    print(json.dumps(brief, indent=2, default=str))
    return 0 if status == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
