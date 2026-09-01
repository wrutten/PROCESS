"""The coupling state ``y``, its categories, its scales and its predicate.

``y`` is **set (b)** of EXPERIMENT_FRAMEWORK.md §2.4: *all state written by
in-loop models*, taken from run-time instrumentation rather than from the DSM.
The harvest supplies it (``_idf_probe_harvest._y_keys``), which means it is
measured, not declared, and does not inherit the DSM's completeness.

Categories are decided **by measurement over the harvest**, never by hand:

============  ==============================  ================================
category      test                            decided by
============  ==============================  ================================
continuous    ``max|dy_i| / s_i < tau``       varies, and is float-valued
discrete      exact equality                  dtype is not float
constant      *excluded*, but asserted        identical at every design point
nan           *excluded*, and counted         NaN/inf somewhere in the harvest
============  ==============================  ================================

The third row is the point of the exercise.  It is the deliberate inverse of a
defect in PROCESS's own predicate, where ``np.allclose(..., equal_nan=True)``
reports a NaN state as converged.  A component excluded from the test must fail
**loudly** if it moves, never silently.  Here a moved constant marks the design
point **invalid for that arm** and is reported by name -- see
:class:`Residual`.

**The scale.**  ``s_i = median |y_i|`` over the harvested design points,
restricted to the points where the component is nonzero, so a component that is
zero at half the points is still scaled by its own working magnitude.  This is
what replaces 2 288 hand-set absolute tolerances, and it is also what avoids
inheriting ``numpy``'s hidden ``atol = 1e-8`` -- which, measured on this very
run's constraint vector, would make agreement unconditional for 1.7 % of
entries and would dominate ``rtol`` for a third of them.

**Arrays: per-array scale, element-wise test.**  Elements of one array share
units, so the array's characteristic magnitude (the median over design points
of ``max|elements|``) scales every element.  A per-element scale would make a
quiet element of a loud array hypersensitive and would manufacture stragglers.

**NaN is never converged.**  A component that is finite in the harvest and NaN
during a solve is a hard non-convergence, not an ``equal_nan`` pass.
"""

from __future__ import annotations

import hashlib
import math

import numpy as np

CONTINUOUS = "continuous"
DISCRETE = "discrete"
CONSTANT = "constant"
NAN_IN_HARVEST = "nan_in_harvest"


# --------------------------------------------------------------------------
# Value classification helpers
# --------------------------------------------------------------------------


def _float_view(v):
    """Return a 1-D float array view of ``v``, or ``None`` if not float-valued.

    ``bool`` is excluded deliberately: ``numpy`` will happily cast it, and a
    flag tested with a relative tolerance is a flag that can flip unnoticed.
    """
    c = v.__class__
    if c is bool:
        return None
    if isinstance(v, (float, np.floating)):
        return np.array([float(v)])
    if isinstance(v, np.ndarray):
        return v.ravel().astype(float, copy=False) if v.dtype.kind == "f" else None
    if isinstance(v, list) and v:
        try:
            a = np.asarray(v)
        except Exception:
            return None
        return a.ravel().astype(float, copy=False) if a.dtype.kind == "f" else None
    return None


def _same(a, b) -> bool:
    """Exact equality, NaN-aware, for any data-structure value."""
    if a is b:
        return True
    ca, cb = a.__class__, b.__class__
    if isinstance(a, np.ndarray) or isinstance(b, np.ndarray):
        try:
            if np.shape(a) != np.shape(b):
                return False
            return bool(np.array_equal(a, b, equal_nan=np.asarray(a).dtype.kind == "f"))
        except Exception:
            return False
    if ca is float and cb is float:
        return a == b or (math.isnan(a) and math.isnan(b))
    try:
        return bool(a == b)
    except Exception:
        return False


#: A constant array longer than this is recorded by summary plus a content
#: hash rather than element by element.  The point of the artifact is that a
#: reader can spot an absurd scale or a wrong exclusion; 32 elements is enough
#: to eyeball, and a 500-element constant printed in full would bury the
#: components that matter.  The hash keeps the record exact.
MAX_INLINE_ELEMENTS = 32


def _shape_of(v) -> dict:
    """Static description of a component: what kind of thing it is."""
    if isinstance(v, np.ndarray):
        return {"kind": "ndarray", "dtype": str(v.dtype), "shape": list(v.shape),
                "n_elements": int(v.size)}
    if isinstance(v, list):
        return {"kind": "list", "n_elements": len(v)}
    return {"kind": type(v).__name__}


def _hash_of(v) -> str:
    """Content hash of a value, used where it is too large to inline."""
    h = hashlib.sha256()
    if isinstance(v, np.ndarray):
        h.update(str(v.dtype).encode())
        h.update(str(v.shape).encode())
        h.update(np.ascontiguousarray(v).tobytes())
    else:
        h.update(repr(v).encode())
    return h.hexdigest()


def _value_record(v):
    """The value a constant holds, exactly where that is reasonable.

    Floats carry their hex literal as well as their decimal form, so the
    record is exact rather than round-tripped.  Arrays and lists are inlined
    up to ``MAX_INLINE_ELEMENTS`` and otherwise summarised with a content
    hash -- never silently truncated.
    """
    if isinstance(v, (float, np.floating)):
        f = float(v)
        return {"value": f, "hex": f.hex()}
    if isinstance(v, (bool, np.bool_)):
        return {"value": bool(v)}
    if isinstance(v, (int, np.integer)):
        return {"value": int(v)}
    if v is None or isinstance(v, str):
        return {"value": v}
    if isinstance(v, (np.ndarray, list)):
        a = np.asarray(v)
        rec = {"n_elements": int(a.size), "sha256": _hash_of(v)}
        if a.size <= MAX_INLINE_ELEMENTS:
            rec["value"] = a.tolist()
        else:
            rec["elided"] = (
                f"{a.size} elements, summarised rather than inlined; "
                f"sha256 above is of the exact contents"
            )
            if a.dtype.kind in "fiu":
                finite = a[np.isfinite(a)] if a.dtype.kind == "f" else a
                if finite.size:
                    rec["min"] = float(np.min(finite))
                    rec["max"] = float(np.max(finite))
                    rec["n_nonzero"] = int(np.count_nonzero(a))
        return rec
    return {"repr": repr(v)[:200]}


def _n_distinct(vals) -> int | None:
    """How many distinct values a discrete component took over the harvest."""
    try:
        return len({repr(v) if not isinstance(v, np.ndarray) else _hash_of(v)
                    for v in vals})
    except Exception:
        return None


def _char_mag(fv) -> float:
    """Characteristic magnitude of one harvested value.

    Scalars: ``|v|``.  Arrays: ``max|elements|`` -- a per-array quantity, which
    is what the element-wise test is scaled by.
    """
    if fv is None or fv.size == 0:
        return 0.0
    finite = fv[np.isfinite(fv)]
    if finite.size == 0:
        return 0.0
    return float(np.max(np.abs(finite)))


# --------------------------------------------------------------------------
# The spec
# --------------------------------------------------------------------------


class YSpec:
    """Categories and scales for the coupling state, measured from a harvest."""

    def __init__(self, keys, category, scale, n_points, detail=None):
        self.keys = list(keys)
        self.category = list(category)
        self.scale = list(scale)
        self.n_harvest_points = n_points
        #: Per-component audit detail, captured **as the categorisation is
        #: measured** rather than reconstructed afterwards, so the committed
        #: artifact cannot drift from the decision it records.
        self.detail = list(detail) if detail is not None else []
        self.idx_continuous = [
            i for i, c in enumerate(self.category) if c == CONTINUOUS
        ]
        self.idx_discrete = [i for i, c in enumerate(self.category) if c == DISCRETE]
        self.idx_constant = [i for i, c in enumerate(self.category) if c == CONSTANT]
        self.idx_nan = [i for i, c in enumerate(self.category) if c == NAN_IN_HARVEST]
        self._scale_cont = np.array(
            [self.scale[i] for i in self.idx_continuous], dtype=float
        )

    # -- construction ----------------------------------------------------

    @classmethod
    def from_harvest(cls, y_keys, points) -> YSpec:
        keys = [tuple(k) for k in y_keys]
        category: list[str] = []
        scale: list[float] = []
        detail: list[dict] = []
        states = [p["state"] for p in points]
        for key in keys:
            vals = [st.get(key) for st in states]
            fvs = [_float_view(v) for v in vals]
            is_float = all(fv is not None for fv in fvs) and bool(fvs)
            has_nan = any(
                fv is not None and not np.all(np.isfinite(fv)) for fv in fvs
            )
            constant = all(_same(vals[0], v) for v in vals[1:]) if vals else True
            rec = {"key": f"{key[0]}.{key[1]}", **_shape_of(vals[0] if vals else None)}

            if has_nan:
                category.append(NAN_IN_HARVEST)
                scale.append(0.0)
                rec["category"] = NAN_IN_HARVEST
                detail.append(rec)
                continue
            if constant:
                category.append(CONSTANT)
                scale.append(0.0)
                rec["category"] = CONSTANT
                rec["value"] = _value_record(vals[0] if vals else None)
                detail.append(rec)
                continue
            if not is_float:
                category.append(DISCRETE)
                scale.append(0.0)
                rec["category"] = DISCRETE
                rec["n_distinct_values"] = _n_distinct(vals)
                detail.append(rec)
                continue
            mags = [_char_mag(fv) for fv in fvs]
            nz = [m for m in mags if m > 0.0]
            s = float(np.median(nz)) if nz else 0.0
            degenerate = s <= 0.0
            if degenerate:
                # varies, but every harvested value is identically zero:
                # cannot happen for a float that varies, recorded rather than
                # assumed.  Fall back to an absolute test.
                s = 1.0
            category.append(CONTINUOUS)
            scale.append(s)
            rec["category"] = CONTINUOUS
            rec["scale"] = s
            rec["scale_hex"] = float(s).hex()
            rec["n_points_scale_measured_over"] = len(nz)
            rec["char_mag_min"] = float(min(mags)) if mags else None
            rec["char_mag_max"] = float(max(mags)) if mags else None
            if degenerate:
                rec["scale_fallback"] = (
                    "every harvested value is identically zero; scale set to 1.0, "
                    "making the test absolute rather than relative"
                )
            detail.append(rec)
        return cls(keys, category, scale, len(points), detail)

    # -- reporting -------------------------------------------------------

    def census(self) -> dict:
        return {
            "n_components": len(self.keys),
            "n_continuous": len(self.idx_continuous),
            "n_discrete": len(self.idx_discrete),
            "n_constant": len(self.idx_constant),
            "n_nan_in_harvest": len(self.idx_nan),
            "harvest_points_used": self.n_harvest_points,
            "nan_in_harvest_fields": [
                f"{self.keys[i][0]}.{self.keys[i][1]}" for i in self.idx_nan
            ],
            "discrete_fields": [
                f"{self.keys[i][0]}.{self.keys[i][1]}" for i in self.idx_discrete
            ],
        }

    def components_sha256(self) -> str:
        """Hash of the categorisation and scales, exactly.

        Covers every key, its category and its scale as a hex float literal,
        so two spec sets are identical iff this matches.  This is what makes
        the committed artifact checkable rather than decorative.
        """
        h = hashlib.sha256()
        for i, k in enumerate(self.keys):
            h.update(f"{k[0]}.{k[1]}|{self.category[i]}|".encode())
            h.update(float(self.scale[i]).hex().encode())
            h.update(b"\n")
        return h.hexdigest()

    def audit_record(self, *, scenario: str, harvest: dict) -> dict:
        """The committed artifact: what every component was decided to be.

        The convergence predicate depends on these scales, so without this
        nobody can inspect after the fact which scale a quantity received, or
        notice that one is absurd.  That matters more here than it usually
        would: the scales are exactly what separates an excluded quantity from
        an included one, and a wrong exclusion makes every architecture declare
        a convergence that has not happened, with no symptom.
        """
        return {
            "format": "a18-ystate-1",
            "scenario": scenario,
            "generated_by": "arch_surgery/fixedpoint/gen_ystate.py",
            "harvest": harvest,
            "scales_measured_over_n_design_points": self.n_harvest_points,
            "method": {
                "y_set": (
                    "set (b) of EXPERIMENT_FRAMEWORK.md 2.4: every "
                    "data-structure field written by a model node inside "
                    "Caller._call_models_once, from run-time instrumentation "
                    "rather than from the DSM."
                ),
                "scale": (
                    "s_i = median |y_i| over the harvested design points, "
                    "restricted to the points where the component is nonzero, "
                    "so a component that is zero at half the points is still "
                    "scaled by its own working magnitude."
                ),
                "array_scale": (
                    "Per-array, not per-element: the median over design points "
                    "of max|elements|. Elements of one array share units, and a "
                    "per-element scale would make a quiet element of a loud "
                    "array hypersensitive."
                ),
                "categories": {
                    CONTINUOUS: "float-valued and varies; tested as max|dy_i|/s_i < tau",
                    DISCRETE: "not float-valued; tested by exact equality",
                    CONSTANT: (
                        "identical at every harvested design point; excluded "
                        "from the tolerance test, but asserted to stay constant "
                        "at run time -- a move blocks convergence and is named"
                    ),
                    NAN_IN_HARVEST: (
                        "NaN or infinity somewhere in the harvest itself; "
                        "excluded and counted, never silently admitted"
                    ),
                },
                "max_inline_elements": MAX_INLINE_ELEMENTS,
            },
            "census": self.census(),
            "components_sha256": self.components_sha256(),
            "n_components": len(self.keys),
            "components": self.detail,
        }

    def name(self, i: int) -> str:
        return f"{self.keys[i][0]}.{self.keys[i][1]}"

    # -- binding and reading ---------------------------------------------

    def bind(self, data):
        """Resolve keys to ``(namespace object, field name)`` once."""
        return [(getattr(data, ns), fld) for ns, fld in self.keys]

    @staticmethod
    def read(bound) -> list:
        """Snapshot ``y``.  Arrays and lists are copied; scalars are not."""
        out = []
        ap = out.append
        for ns, fld in bound:
            v = object.__getattribute__(ns, fld)
            c = v.__class__
            if c is np.ndarray:
                v = v.copy()
            elif c is list:
                v = v[:]
            ap(v)
        return out

    # -- the predicate ---------------------------------------------------

    def residual(self, prev: list, cur: list, subset=None) -> Residual:
        """Scaled residual between two ``y`` snapshots.

        ``subset`` restricts the test to a set of component indices, which is
        how a block arm's inner solve tests only its own module's state.
        """
        idx_c = self.idx_continuous
        if subset is not None:
            sel = set(subset)
            idx_c = [i for i in idx_c if i in sel]
            idx_d = [i for i in self.idx_discrete if i in sel]
            idx_k = [i for i in self.idx_constant if i in sel]
        else:
            idx_d = self.idx_discrete
            idx_k = self.idx_constant

        scaled = np.zeros(len(idx_c), dtype=float)
        nan_new: list[int] = []
        for j, i in enumerate(idx_c):
            a, b = prev[i], cur[i]
            fa, fb = _float_view(a), _float_view(b)
            if fa is None or fb is None or fa.shape != fb.shape:
                scaled[j] = np.inf
                continue
            d = np.abs(fb - fa)
            if not np.all(np.isfinite(fb)):
                nan_new.append(i)
                scaled[j] = np.inf
                continue
            scaled[j] = float(np.max(d)) / self.scale[i]

        mismatch_d = [i for i in idx_d if not _same(prev[i], cur[i])]
        moved_k = [i for i in idx_k if not _same(prev[i], cur[i])]

        return Residual(self, idx_c, scaled, mismatch_d, moved_k, nan_new)


class Residual:
    """One scaled residual, with everything ``max`` alone cannot say.

    ``max`` cannot distinguish "one straggler holds up eight sweeps" from
    "five hundred components are still moving", so the count above ``tau`` is
    carried alongside it and both are reported.
    """

    def __init__(self, spec, idx_c, scaled, mismatch_d, moved_k, nan_new):
        self.spec = spec
        self.idx_c = idx_c
        self.scaled = scaled
        self.mismatch_discrete = mismatch_d
        self.moved_constant = moved_k
        self.nan_new = nan_new
        self.max = float(np.max(scaled)) if scaled.size else 0.0
        self.argmax = (
            int(idx_c[int(np.argmax(scaled))]) if scaled.size else None
        )

    def n_above(self, tau: float) -> int:
        return int((self.scaled >= tau).sum()) if self.scaled.size else 0

    def above(self, tau: float) -> list[int]:
        if not self.scaled.size:
            return []
        return [self.idx_c[j] for j in np.nonzero(self.scaled >= tau)[0]]

    def converged(self, tau: float) -> bool:
        if self.nan_new or self.mismatch_discrete or self.moved_constant:
            return False
        return self.max < tau

    def brief(self, tau: float) -> dict:
        return {
            "max": self.max,
            "argmax": None if self.argmax is None else self.spec.name(self.argmax),
            "n_above": self.n_above(tau),
            "n_discrete_mismatch": len(self.mismatch_discrete),
            "n_constant_moved": len(self.moved_constant),
            "n_nan_new": len(self.nan_new),
        }
