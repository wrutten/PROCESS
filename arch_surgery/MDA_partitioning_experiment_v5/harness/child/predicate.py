"""A thin layer over the coupling state: rebuild, snapshot, restore, compare.

Derived from ``arch_surgery/idf_probe/a34_instruments.py``
(``load_spec_offline``, ``_cross_residual``) and
``arch_surgery/idf_probe/v2_eval_one.py`` (``snap_value``, ``restore_value``,
``snapshot_record``, ``restore_snapshot``, ``write_entry_state``), both read at
``9a8defa6``; task **A50 (harness-run)**.  Two things changed and both are
deliberate:

* the previous revision reached the coupling-state module through an
  ``importlib`` load of a file two directories away, and reached
  ``_cross_residual`` by importing a **private** name across a package
  boundary.  Here the module is :mod:`harness.child.ystate`, imported normally, and
  the cross-state comparison is public;
* the spec rebuild caches nothing.  The driver's own ``load_spec`` caches, and
  a harness-side cache keyed on a path would be a second, differently-keyed
  copy of the same decision (D14(c): one implementation of a shared
  definition).

What lives here
---------------
The **coupling state** ``y`` is the measured set of state fields the in-loop
models write; a **coupling-state artifact** is the committed file naming those
fields and the measured scale of each.  A **snapshot** is one exact
serialisation of ``y`` — floats as hex literals, so a state written to disk and
read back is the identical state, bit for bit.  The **cross-state residual** is
the scaled difference between two states, which is how "did this arm land on
the same fixed point" is answered.

Nothing here starts a PROCESS run, and nothing here imports the driver.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from . import ystate


class PredicateError(RuntimeError):
    """A refusal to compare.  Never downgraded into a warning."""


# --------------------------------------------------------------------------
# rebuilding a spec from a committed artifact
# --------------------------------------------------------------------------


def load_spec(path: Path | str) -> ystate.YSpec:
    """Rebuild a :class:`~harness.child.ystate.YSpec` from a committed artifact.

    The artifact carries, per component, its key, its category and (for a
    continuous one) its scale — which is the whole of what the predicate needs.
    ``components_sha256`` is recomputed from the rebuilt spec and checked
    against the value the file records, so a spec rebuilt from a truncated,
    reordered or hand-edited artifact is **refused** rather than quietly used.
    """
    path = Path(path)
    record = json.loads(path.read_text())
    keys, category, scale = [], [], []
    for component in record["components"]:
        namespace, _, field = component["key"].partition(".")
        keys.append((namespace, field))
        category.append(component["category"])
        scale.append(float(component.get("scale", 0.0)))
    spec = ystate.YSpec(
        keys,
        category,
        scale,
        record.get("n_components"),
        record["components"],
        mode=record.get("spec_mode", ystate.SPEC_MODE_A18),
        scale_floor=float(record.get("scale_floor", ystate.SCALE_FLOOR)),
    )
    committed = record.get("components_sha256")
    if committed and spec.components_sha256() != committed:
        raise PredicateError(
            f"{path} does not rebuild: the spec built from it hashes to "
            f"{spec.components_sha256()}, the file records {committed}.  A "
            f"spec that does not rebuild is refused, never used."
        )
    return spec


# --------------------------------------------------------------------------
# exact serialisation of one state
# --------------------------------------------------------------------------


def snap_value(value) -> dict[str, Any]:
    """One coupling-state component, serialised exactly.

    Floats travel as hex literals and float arrays as hex element lists with
    their dtype and shape, so a state is bit-exact across the file.  Anything
    unrecognised is carried as a tagged ``repr`` — visible, never silently
    dropped.
    """
    if isinstance(value, (float, np.floating)):
        return {"k": "f", "hex": float(value).hex()}
    if isinstance(value, (bool, np.bool_)):
        return {"k": "b", "v": bool(value)}
    if isinstance(value, (int, np.integer)):
        return {"k": "i", "v": int(value)}
    if value is None:
        return {"k": "none"}
    if isinstance(value, str):
        return {"k": "s", "v": value}
    if isinstance(value, np.ndarray):
        if value.dtype.kind == "f":
            return {
                "k": "af",
                "dtype": str(value.dtype),
                "shape": list(value.shape),
                "hex": [float(x).hex() for x in value.ravel().tolist()],
            }
        return {
            "k": "a",
            "dtype": str(value.dtype),
            "shape": list(value.shape),
            "v": value.ravel().tolist(),
        }
    if isinstance(value, list):
        return {"k": "l", "v": [snap_value(x) for x in value]}
    return {"k": "r", "v": repr(value)}


def restore_value(record: Mapping[str, Any]):
    """Inverse of :func:`snap_value`."""
    kind = record["k"]
    if kind == "f":
        return float.fromhex(record["hex"])
    if kind == "b":
        return bool(record["v"])
    if kind == "i":
        return int(record["v"])
    if kind == "none":
        return None
    if kind == "s":
        return record["v"]
    if kind == "af":
        array = np.array(
            [float.fromhex(h) for h in record["hex"]],
            dtype=np.dtype(record["dtype"]),
        )
        return array.reshape(record["shape"])
    if kind == "a":
        return np.array(record["v"], dtype=np.dtype(record["dtype"])).reshape(
            record["shape"]
        )
    if kind == "l":
        return [restore_value(x) for x in record["v"]]
    return record["v"]  # "r": the repr string; exact-equality comparable


def snapshot_record(
    spec: ystate.YSpec, y: list, *, predicate_mode: str | None = None
) -> dict[str, Any]:
    """The whole state, keyed by component name, exactly.

    ``predicate_mode`` goes into the preamble when the caller knows it: which
    ruler the run that produced this state stopped on.  A state written by a
    run under one ruler is not distinguishable afterwards from one written
    under the other unless the file says so (improvement item 5a's trap (i)),
    and the state itself carries no trace of the denominator it converged
    against.  It is a **preamble** field only: nothing here reads it back, and
    :func:`restore_snapshot` pairs snapshots by ``components_sha256`` as
    before, so a snapshot written before the field existed still restores.
    """
    record: dict[str, Any] = {
        "components_sha256": spec.components_sha256(),
        "n_components": len(spec.keys),
    }
    if predicate_mode is not None:
        record["predicate_mode"] = predicate_mode
    record["state"] = {spec.name(i): snap_value(y[i]) for i in range(len(y))}
    return record


def restore_snapshot(spec: ystate.YSpec, record: Mapping[str, Any]) -> list:
    """A snapshot back into the list layout :meth:`YSpec.residual` takes.

    A snapshot taken against a different component spec is refused: comparing
    two states enumerated differently would compare components pairwise by
    position and report a residual over a mapping nobody chose.
    """
    if record["components_sha256"] != spec.components_sha256():
        raise PredicateError(
            "the snapshot was taken against a different component spec: "
            f"{record['components_sha256']} recorded, "
            f"{spec.components_sha256()} loaded"
        )
    state = record["state"]
    return [restore_value(state[spec.name(i)]) for i in range(len(spec.keys))]


def write_entry_state(
    spec: ystate.YSpec, data, record: Mapping[str, Any]
) -> dict[str, Any]:
    """Write a snapshot's components into *data*, and prove the write took.

    Float arrays whose dtype and shape match the live value are written
    **element-wise in place**, preserving object identity the way the
    displacement multiplies in place; a component that was serialised as a bare
    ``repr`` cannot be rebuilt and is skipped **by name**, loudly.  Afterwards
    the whole state is read back and compared bit for bit against the snapshot:
    ``readback_bitexact`` is the in-process evidence that the entry state *is*
    the snapshot state, rather than the assumption that writing it worked.
    """
    y = restore_snapshot(spec, record)
    bound = spec.bind(data)
    state = record["state"]
    n_scalar = n_inplace = n_replaced = 0
    skipped_repr: list[str] = []
    replaced: list[str] = []
    for i, (namespace, field) in enumerate(bound):
        name = spec.name(i)
        if state[name]["k"] == "r":
            skipped_repr.append(name)
            continue
        target = y[i]
        if isinstance(target, np.ndarray):
            current = object.__getattribute__(namespace, field)
            if (
                isinstance(current, np.ndarray)
                and current.shape == target.shape
                and current.dtype == target.dtype
            ):
                current[...] = target
                n_inplace += 1
            else:
                setattr(namespace, field, target)
                n_replaced += 1
                replaced.append(name)
        else:
            setattr(namespace, field, target)
            n_scalar += 1
    read_back = spec.read(bound)
    skipped = set(skipped_repr)
    mismatch = [
        spec.name(i)
        for i in range(len(read_back))
        if spec.name(i) not in skipped
        and snap_value(read_back[i]) != state[spec.name(i)]
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
# comparing two states
# --------------------------------------------------------------------------


def _one_cross_residual(
    spec: ystate.YSpec, y_reference: list, y_other: list, tau: float, ruler: str
) -> dict[str, Any]:
    """One cross-state residual, on one named ruler."""
    residual = spec.residual(y_reference, y_other, ruler=ruler)
    return {
        "ruler": ruler,
        "max": residual.max,
        "max_hex": float(residual.max).hex(),
        "argmax": (
            None if residual.argmax is None else spec.name(residual.argmax)
        ),
        "tau": tau,
        "n_above_tau": residual.n_above(tau),
        "n_discrete_mismatch": len(residual.mismatch_discrete),
        "n_constant_moved": len(residual.moved_constant),
        "n_nan_new": len(residual.nan_new),
        "n_bound_by_the_current_value": len(residual.binding_components()),
        "categorically_clean": not (
            residual.mismatch_discrete
            or residual.moved_constant
            or residual.nan_new
        ),
    }


def cross_residual(
    spec: ystate.YSpec,
    y_reference: list,
    y_other: list,
    tau: float,
    *,
    ruler: str = ystate.RULER_DEFAULT,
) -> dict[str, Any]:
    """The scaled residual between two states, summarised, on **both** rulers.

    ``max`` alone cannot tell "one straggler" from "five hundred components
    still moving", so the count above the tolerance travels with it, and so
    does whether anything left its category — a moved constant, a changed
    discrete or a new NaN makes the comparison *categorically unclean*
    regardless of how small the maximum is.

    The top-level fields are ``ruler``'s — ``frozen`` unless the caller says
    otherwise, so an existing caller reads exactly what it read before — and
    ``rulers`` carries the same summary computed on **each** ruler.  Both are
    always present: the mixed ruler reads lower wherever its denominator binds,
    by construction, so a comparison published on one ruler alone would report
    a change of ruler as a change of agreement (improvement item 5a's trap
    (ii)).  Computing the second costs one further pass over two states already
    in memory; no model runs.
    """
    rulers = {
        name: _one_cross_residual(spec, y_reference, y_other, tau, name)
        for name in ystate.RULERS
    }
    summary = dict(rulers[ystate.assert_ruler(ruler)])
    summary["rulers"] = rulers
    return summary


def component_index(spec: ystate.YSpec, name: str) -> int | None:
    """Where *name* sits in the spec, or None.  Never a guess by prefix."""
    for i in range(len(spec.keys)):
        if spec.name(i) == name:
            return i
    return None
