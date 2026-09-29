"""PROCESS's whole data structure: snapshot it, compare two, put one back.

The coupling state is the set of fields the in-loop models write and read from
each other — what the fixed-point loop converges, and what the harness already
serialises component by component in ``harness/child/predicate.py``.  It is a few
hundred fields.  The **data structure** is everything: every field of every
namespace of the object PROCESS threads through its models, some two thousand
of them, most of which no loop ever compares.

Why the harness needs the larger thing.  An instrument that evaluates the model
set *after* PROCESS's output path has run is evaluating a different map unless
everything the models read is where the loop left it — and PROCESS's output
path changes settings that are not coupling-state components and are never put
back (measured: ``tfcoil.n_rad_per_layer``, the TF-coil stress mesh, raised
100 → 500 by four latching writes, task A61 (insstrain-diagnosis)).  So the
exit audit snapshots the whole structure at the position it is taken from,
derives what has changed by the time its sweep starts, and puts that derived
set back.  **Derived, never listed**: a hand-written list of the one field
known today stops being right the moment a model latches another setting.

Three functions, and each publishes its own denominator.  A namespace that is
not a dataclass is *named* rather than dropped; a field that cannot be
serialised is carried as a tagged ``repr`` rather than omitted; a field that
cannot be written back is reported by name rather than counted as restored.
Nothing here claims "all".

Heritage: the three functions were written for the diagnosis trace of task
**A61 (insstrain-diagnosis)** (``harness/child/audit_map.py``, a gate
instrument refused on campaign runs; retired with its diagnosis stage by task
A73 under D27's item B3 once the attribution it made was recorded in A61's
and A62's reports and in ruling D25).  Ruling **D25** makes the same mechanism
part of the exit audit itself, which runs on every run, so it lives here.
Float serialisation is ``harness/child/predicate.py``'s, so
a data-structure snapshot and a coupling-state snapshot are bit-exact in the
same way and can be compared against each other.
"""

from __future__ import annotations

import dataclasses
import traceback
from typing import Any, Mapping, Sequence

import numpy as np

from . import predicate as predicate_mod


def snapshot(data) -> dict[str, Any]:
    """Every field of every namespace of the data structure, serialised exactly.

    Floats travel as hexadecimal literals and float arrays as hex element
    lists, by the same serialiser the coupling-state snapshot uses, so two
    snapshots compare bit for bit and a difference is a difference in the last
    bit rather than in a printed digit.

    A namespace that is not a dataclass is named in ``skipped_namespaces``
    rather than dropped: a silent omission would shrink the denominator of
    every count taken over this snapshot.
    """
    fields: dict[str, Any] = {}
    skipped: list[str] = []
    for namespace_field in dataclasses.fields(data):
        namespace = getattr(data, namespace_field.name)
        if not dataclasses.is_dataclass(namespace):
            skipped.append(namespace_field.name)
            continue
        for field in dataclasses.fields(namespace):
            name = f"{namespace_field.name}.{field.name}"
            try:
                fields[name] = predicate_mod.snap_value(
                    getattr(namespace, field.name)
                )
            except Exception:  # noqa: BLE001 - recorded, never raised
                fields[name] = {"k": "error", "v": traceback.format_exc()}
    return {
        "n_namespaces": len(dataclasses.fields(data)) - len(skipped),
        "n_fields": len(fields),
        "skipped_namespaces": skipped,
        "fields": fields,
    }


def differences(
    before: Mapping[str, Any], after: Mapping[str, Any]
) -> dict[str, Any]:
    """Which data-structure fields differ between two snapshots, and how many.

    The denominator is the number of fields **compared** — the two snapshots'
    common keys — and any key present in one and not the other is reported
    separately, because a field that appeared between the two is a difference
    of a different kind.
    """
    a, b = before["fields"], after["fields"]
    common = sorted(set(a) & set(b))
    differ = [name for name in common if a[name] != b[name]]
    return {
        "n_compared": len(common),
        "n_differ": len(differ),
        "only_before": sorted(set(a) - set(b)),
        "only_after": sorted(set(b) - set(a)),
        "differ": differ,
        "detail": {
            name: {"before": brief(a[name]), "after": brief(b[name])}
            for name in differ
        },
    }


def brief(record: Mapping[str, Any]) -> Any:
    """One serialised value, short enough to read in a report."""
    kind = record.get("k")
    if kind in {"f", "b", "i", "s", "none"}:
        return record.get("hex", record.get("v"))
    if kind in {"af", "a"}:
        values = record.get("hex", record.get("v")) or []
        return {
            "kind": kind,
            "dtype": record.get("dtype"),
            "shape": record.get("shape"),
            "n_elements": len(values),
            "head": list(values[:4]),
        }
    if kind == "l":
        return {"kind": "l", "n_elements": len(record.get("v") or [])}
    return {"kind": kind}


def restore(
    data, snapshot_record: Mapping[str, Any], *, only: Sequence[str] | None = None
) -> dict[str, Any]:
    """Write a data-structure snapshot back, and prove the write took.

    Float arrays whose dtype and shape match the live value are written
    element-wise in place, preserving object identity; a value that was
    serialised as a bare ``repr`` cannot be rebuilt and is skipped **by name**;
    a field that refuses assignment is recorded **by name**.  Afterwards every
    field written is read back and compared against the snapshot, so
    ``readback_bitexact`` is evidence rather than an assumption.
    """
    fields = snapshot_record["fields"]
    names = list(fields) if only is None else [n for n in only if n in fields]
    skipped_repr: list[str] = []
    refused: dict[str, str] = {}
    written: list[str] = []
    for name in names:
        record = fields[name]
        if record.get("k") in {"r", "error"}:
            skipped_repr.append(name)
            continue
        namespace_name, _, field = name.partition(".")
        namespace = getattr(data, namespace_name)
        try:
            target = predicate_mod.restore_value(record)
            current = getattr(namespace, field)
            if (
                isinstance(target, np.ndarray)
                and isinstance(current, np.ndarray)
                and current.shape == target.shape
                and current.dtype == target.dtype
            ):
                current[...] = target
            else:
                setattr(namespace, field, target)
            written.append(name)
        except Exception:  # noqa: BLE001 - recorded, never raised
            refused[name] = traceback.format_exc(limit=1).strip()
    mismatch = []
    for name in written:
        namespace_name, _, field = name.partition(".")
        value = getattr(getattr(data, namespace_name), field)
        if predicate_mod.snap_value(value) != fields[name]:
            mismatch.append(name)
    return {
        "n_asked": len(names),
        "n_written": len(written),
        "n_skipped_repr": len(skipped_repr),
        "skipped_repr": skipped_repr[:20],
        "n_refused": len(refused),
        "refused": dict(list(refused.items())[:20]),
        "readback_bitexact": not mismatch,
        "n_readback_mismatch": len(mismatch),
        "readback_mismatch_first": mismatch[:10],
        # What the restore actually put back, as against what it was asked
        # for.  ``n_restored`` counts the fields that are, after the write,
        # bit-identical to the snapshot; ``not_restorable`` names every field
        # that is not, whatever the reason — never absorbed into a claim of
        # "all" (ruling D25).
        "n_restored": len(written) - len(mismatch),
        "n_not_restorable": len(skipped_repr) + len(refused) + len(mismatch),
        "not_restorable": sorted(set(skipped_repr) | set(refused) | set(mismatch)),
    }


def round_trip_census(snapshot_record: Mapping[str, Any]) -> dict[str, Any]:
    """Which fields of a snapshot could not survive being written back at all.

    Measured on the snapshot alone — nothing is written into the data
    structure — so it is a property of the serialisation and can be reported on
    every run whatever the restored set happens to contain.  Two ways a field
    fails: it was carried as a bare ``repr`` (or as a recorded error), so there
    is nothing to rebuild it from; or it rebuilds into a value that does not
    serialise back to what was stored.

    The count and the names go in the record together.  A restore that reports
    only what it restored, over a denominator it chose, would be exactly the
    "zero over a quietly smaller population" this project keeps finding in its
    own work (trap T11).
    """
    fields = snapshot_record["fields"]
    not_rebuildable = sorted(
        name for name, record in fields.items() if record.get("k") in {"r", "error"}
    )
    not_round_tripping: list[str] = []
    for name, record in fields.items():
        if name in set(not_rebuildable):
            continue
        try:
            if predicate_mod.snap_value(predicate_mod.restore_value(record)) != record:
                not_round_tripping.append(name)
        except Exception:  # noqa: BLE001 - recorded, never raised
            not_round_tripping.append(name)
    return {
        "n_fields": len(fields),
        "n_not_rebuildable": len(not_rebuildable),
        "not_rebuildable": not_rebuildable,
        "n_not_round_tripping": len(not_round_tripping),
        "not_round_tripping": sorted(not_round_tripping),
    }
