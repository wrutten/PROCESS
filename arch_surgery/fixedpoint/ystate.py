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

A26: two categorisation modes, and why the second one exists
------------------------------------------------------------

The table above is ``SPEC_MODE_A18`` and is kept verbatim, because A18, A22 and
A23 measured under it and their recorded artifacts have to keep reproducing.
Its third and fourth rows *exclude* a component from the convergence test on
the grounds that it never varied across the harvest, or that the harvest itself
holds a non-finite value there.  §6.3(ii) of the results report names the
hazard that creates: **an excluded quantity that genuinely couples would be
invisible, and every arrangement would inherit the same false convergence with
no symptom.**  The run-time assertion that a constant stays constant is a real
guard, but it is a guard against a *move*, not a test the arm has to satisfy,
and it says nothing at all about the 555 of 840 components that
``large_tokamak_eval`` classified constant from ten design points.

``SPEC_MODE_A26`` removes both exclusions.  Every float-valued component is
tested, at a scale that is its own measured working magnitude where it has one
and an explicit, recorded **scale floor** where it does not; every non-float
component is tested by exact equality; and a component that is non-finite
somewhere in the harvest is tested on its finite entries with its non-finite
pattern required to be unchanged.  The only components excluded are the ones
named in :data:`ACCUMULATORS`, each with the justification that it accumulates
within a sweep and therefore cannot have a fixed point --- and that list is
**empty until a measurement puts something in it**.

**The floor is a judgement with consequences and is stated as one.**  A
component that is identically zero at every harvested design point has no
observed magnitude, so no relative scale can be measured for it and some
absolute one has to be chosen.  :data:`SCALE_FLOOR` is that choice; a smaller
floor makes those components harder to converge and a larger one makes them
easier, and A26's report measures what a decade in each direction does.
"""

from __future__ import annotations

import hashlib
import math

import numpy as np

CONTINUOUS = "continuous"
DISCRETE = "discrete"
CONSTANT = "constant"
NAN_IN_HARVEST = "nan_in_harvest"
#: A26.  Float-valued, and non-finite somewhere in the harvest.  **Tested**,
#: not excluded: the non-finite pattern must be unchanged and the finite
#: entries must satisfy the scaled test.
NONFINITE = "nonfinite"
#: A26.  Excluded, with a justification recorded per quantity.  The *only*
#: admissible justification is that the quantity accumulates within a sweep and
#: therefore has no fixed point.  See :data:`ACCUMULATORS`.
EXCLUDED_ACCUMULATOR = "excluded_accumulator"

#: A18/A22/A23's categorisation, reproduced exactly.  Kept so their recorded
#: artifacts stay reproducible; not the mode A26 and later work measure under.
SPEC_MODE_A18 = "a18"
#: A26 §6.3(ii): no exclusion on the grounds of never having varied.
SPEC_MODE_A26 = "a26"
SPEC_MODES = (SPEC_MODE_A18, SPEC_MODE_A26)

#: The scale given to a component with **no observed magnitude** -- identically
#: zero at every harvested design point, so ``median |y_i|`` over its nonzero
#: points does not exist.  With ``s_i = 1.0`` the test on such a component is
#: ``max|dy_i| < tau`` in the component's own units, i.e. absolute rather than
#: relative.
#:
#: **Why 1.0 and not something smaller.**  It is the value A18 already used for
#: the one case it met (a float that varies but is identically zero at every
#: harvested point), so adopting it keeps one convention rather than two; it is
#: the only choice that does not require asserting a magnitude for a quantity
#: whose magnitude was never observed; and a floor far below 1 makes a
#: quantity that ought to be inert unconvergeable, which manufactures invalid
#: design points rather than measuring them.  It is a judgement, it is recorded
#: in every artifact, and A26 reports the effect of moving it a decade each
#: way.
SCALE_FLOOR = 1.0

#: Components excluded from the convergence test in ``SPEC_MODE_A26``, keyed by
#: ``"namespace.field"``, with the justification recorded per quantity.
#:
#: **The bar is deliberately high and there is exactly one admissible
#: justification**: the quantity accumulates within a sweep (a counter, a
#: running sum) and therefore has no fixed point to converge to, so including
#: it would make every arm fail everywhere for a reason that is not about
#: architecture.  "It never varied across the harvest" is *not* admissible ---
#: that is precisely the exclusion §6.3(ii) rules out.
#:
#: **Empty, and that is the measured result, not an oversight.**  A26 searched
#: the harvested write sets for accumulation and found nothing that qualifies;
#: see the A26 report.  An entry added here must carry the evidence.
ACCUMULATORS: dict[str, str] = {}


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

    def __init__(self, keys, category, scale, n_points, detail=None, *,
                 mode: str = SPEC_MODE_A18, scale_floor: float = SCALE_FLOOR):
        if mode not in SPEC_MODES:
            raise ValueError(f"unknown spec mode {mode!r}; expected {SPEC_MODES}")
        self.keys = list(keys)
        self.category = list(category)
        self.scale = list(scale)
        self.mode = mode
        self.scale_floor = float(scale_floor)
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
        self.idx_nonfinite = [
            i for i, c in enumerate(self.category) if c == NONFINITE
        ]
        self.idx_excluded_accumulator = [
            i for i, c in enumerate(self.category) if c == EXCLUDED_ACCUMULATOR
        ]
        #: Every component index that is *tested* by some part of the
        #: predicate.  Its complement is the exclusion set, and in
        #: ``SPEC_MODE_A26`` that complement is exactly
        #: :attr:`idx_excluded_accumulator`.
        self.idx_tested = sorted(
            set(self.idx_continuous) | set(self.idx_discrete)
            | set(self.idx_nonfinite)
        )
        self._scale_cont = np.array(
            [self.scale[i] for i in self.idx_continuous], dtype=float
        )

    # -- construction ----------------------------------------------------

    @classmethod
    def from_harvest(cls, y_keys, points, *, mode: str = SPEC_MODE_A18,
                     scale_floor: float = SCALE_FLOOR) -> YSpec:
        """Categorise and scale every coupling component from the harvest.

        ``mode`` selects the categorisation.  ``SPEC_MODE_A18`` reproduces what
        A18 measured, byte for byte; ``SPEC_MODE_A26`` tests every component
        (§6.3(ii)) and excludes only the quantities named in
        :data:`ACCUMULATORS`.
        """
        if mode == SPEC_MODE_A26:
            return cls._from_harvest_a26(y_keys, points, scale_floor)
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
        return cls(keys, category, scale, len(points), detail,
                   mode=SPEC_MODE_A18, scale_floor=scale_floor)

    # -- A26: the same measurement, without the exclusions ----------------

    @classmethod
    def _from_harvest_a26(cls, y_keys, points, scale_floor: float) -> YSpec:
        """``SPEC_MODE_A26``: test everything, floor the unmeasurable scales.

        The measurement is identical to ``SPEC_MODE_A18``'s -- the same
        ``_float_view``, the same ``_char_mag``, the same median over the
        nonzero points.  What changes is only what is *done* with the result:

        * a float-valued component is ``CONTINUOUS`` whether or not it varied,
          with ``s_i = median|y_i|`` over its nonzero points and ``s_i =
          scale_floor`` when it has none;
        * a non-float component is ``DISCRETE`` whether or not it varied, and
          is tested by exact equality, which a constant satisfies trivially and
          a mover fails loudly;
        * a component holding a non-finite value somewhere in the harvest is
          ``NONFINITE`` and is *tested*, on its finite entries and on its
          non-finite pattern, instead of being dropped;
        * only a component named in :data:`ACCUMULATORS` is excluded, and its
          justification is carried into the artifact.

        Every ``rec`` keeps ``a18_category``, so the artifact says which
        components changed hands and a reader can reconstruct A18's set.
        """
        keys = [tuple(k) for k in y_keys]
        category: list[str] = []
        scale: list[float] = []
        detail: list[dict] = []
        states = [p["state"] for p in points]
        for key in keys:
            name = f"{key[0]}.{key[1]}"
            vals = [st.get(key) for st in states]
            fvs = [_float_view(v) for v in vals]
            is_float = all(fv is not None for fv in fvs) and bool(fvs)
            has_nan = any(
                fv is not None and not np.all(np.isfinite(fv)) for fv in fvs
            )
            constant = all(_same(vals[0], v) for v in vals[1:]) if vals else True
            rec = {"key": name, **_shape_of(vals[0] if vals else None)}
            rec["a18_category"] = (
                NAN_IN_HARVEST if has_nan
                else CONSTANT if constant
                else DISCRETE if not is_float
                else CONTINUOUS
            )
            rec["constant_over_harvest"] = bool(constant)

            if name in ACCUMULATORS:
                category.append(EXCLUDED_ACCUMULATOR)
                scale.append(0.0)
                rec["category"] = EXCLUDED_ACCUMULATOR
                rec["exclusion_justification"] = ACCUMULATORS[name]
                detail.append(rec)
                continue

            if not is_float:
                category.append(DISCRETE)
                scale.append(0.0)
                rec["category"] = DISCRETE
                rec["n_distinct_values"] = _n_distinct(vals)
                if constant:
                    rec["value"] = _value_record(vals[0] if vals else None)
                detail.append(rec)
                continue

            mags = [_char_mag(fv) for fv in fvs]
            nz = [m for m in mags if m > 0.0]
            measured = float(np.median(nz)) if nz else None
            s = measured if measured and measured > 0.0 else float(scale_floor)
            category.append(NONFINITE if has_nan else CONTINUOUS)
            scale.append(s)
            rec["category"] = NONFINITE if has_nan else CONTINUOUS
            rec["scale"] = s
            rec["scale_hex"] = float(s).hex()
            rec["scale_measured"] = measured
            rec["scale_from_floor"] = measured is None or measured <= 0.0
            rec["n_points_scale_measured_over"] = len(nz)
            rec["char_mag_min"] = float(min(mags)) if mags else None
            rec["char_mag_max"] = float(max(mags)) if mags else None
            if rec["scale_from_floor"]:
                rec["scale_fallback"] = (
                    "no nonzero value at any harvested design point, so no "
                    "working magnitude could be measured; scale set to the "
                    f"recorded floor {scale_floor!r}, making the test "
                    "absolute rather than relative"
                )
            if constant:
                rec["value"] = _value_record(vals[0] if vals else None)
            detail.append(rec)
        return cls(keys, category, scale, len(points), detail,
                   mode=SPEC_MODE_A26, scale_floor=scale_floor)

    # -- reporting -------------------------------------------------------

    def census(self) -> dict:
        n_excl = len(self.idx_constant) + len(self.idx_nan) + len(
            self.idx_excluded_accumulator
        )
        return {
            "spec_mode": self.mode,
            "scale_floor": self.scale_floor,
            "n_components": len(self.keys),
            "n_continuous": len(self.idx_continuous),
            "n_discrete": len(self.idx_discrete),
            "n_constant": len(self.idx_constant),
            "n_nan_in_harvest": len(self.idx_nan),
            "n_nonfinite": len(self.idx_nonfinite),
            "n_excluded_accumulator": len(self.idx_excluded_accumulator),
            # The two numbers a reader of §6.3(ii) actually wants: how many
            # components the predicate tests, and how many it does not.
            "n_tested": len(self.idx_tested),
            "n_excluded": n_excl,
            "n_scale_from_floor": sum(
                1 for d in self.detail if d.get("scale_from_floor")
            ),
            "excluded_accumulator_fields": {
                f"{self.keys[i][0]}.{self.keys[i][1]}": ACCUMULATORS.get(
                    f"{self.keys[i][0]}.{self.keys[i][1]}"
                )
                for i in self.idx_excluded_accumulator
            },
            "harvest_points_used": self.n_harvest_points,
            "nan_in_harvest_fields": [
                f"{self.keys[i][0]}.{self.keys[i][1]}" for i in self.idx_nan
            ],
            "nonfinite_fields": [
                f"{self.keys[i][0]}.{self.keys[i][1]}" for i in self.idx_nonfinite
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
        # The A18 hash is left exactly as A18 computed it, so the committed
        # records for that mode keep validating; only a non-A18 mode adds its
        # own preamble.  A hash that changed for every mode would have made
        # this change silently invalidate three merged tasks' artifacts.
        if self.mode != SPEC_MODE_A18:
            h.update(
                f"mode={self.mode}|floor={float(self.scale_floor).hex()}\n".encode()
            )
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
            "format": "a18-ystate-1" if self.mode == SPEC_MODE_A18
            else "a26-ystate-1",
            "spec_mode": self.mode,
            "scale_floor": self.scale_floor,
            "scale_floor_hex": float(self.scale_floor).hex(),
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
                        "excluded and counted, never silently admitted "
                        "(SPEC_MODE_A18 only)"
                    ),
                    NONFINITE: (
                        "SPEC_MODE_A26: non-finite somewhere in the harvest, "
                        "and tested rather than excluded -- the non-finite "
                        "pattern must be unchanged and the finite entries "
                        "must satisfy the scaled test"
                    ),
                    EXCLUDED_ACCUMULATOR: (
                        "SPEC_MODE_A26: excluded, with a per-quantity "
                        "justification that it accumulates within a sweep and "
                        "so has no fixed point.  The only admissible "
                        "justification; 'it never varied' is not one"
                    ),
                },
                "a26_note": (
                    "In SPEC_MODE_A26 nothing is excluded for never having "
                    "varied.  Every float component is tested at its own "
                    "measured magnitude, or at the recorded scale floor where "
                    "it has none; every non-float component is tested by exact "
                    "equality.  ACCUMULATORS is the whole exclusion set."
                ),
                "accumulators": dict(ACCUMULATORS),
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

    def subset_indices(self, subset) -> list:
        """A subset of component indices, as a sorted list.

        Sorted because :meth:`_residual_aligned` and :class:`Residual` report
        indices in ascending order, and because ``argmax`` ties must break the
        same way they did when the whole set was read.
        """
        if subset is None:
            return list(range(len(self.keys)))
        return sorted(int(i) for i in subset)

    def bind_subset(self, data, sel) -> list:
        """:meth:`bind`, restricted to ``sel`` and aligned with it."""
        return [
            (getattr(data, self.keys[i][0]), self.keys[i][1]) for i in sel
        ]

    @staticmethod
    def read(bound) -> list:
        """Snapshot ``y``, or the part of it ``bound`` names.

        Arrays and lists are copied; scalars are not.

        **Read only what is about to be tested.**  ``bound`` used to be the
        whole coupling state --- 827 to 846 components, every array copied and
        every list sliced --- even when the caller was an inner block solve
        that then compared fifty of them and discarded the rest.  A25 measured
        ~17 500 such reads on one deck's gate run, and that bookkeeping is a
        large part of why the block arm's *wall clock* looked bad while its
        model-evaluation count did not.  Passing a subset-bound list instead
        changes nothing about which components are compared, what the residual
        is, or what any arm decides --- it removes copying whose result was
        thrown away.  A26 gates that as a **bit-comparison** rather than
        asserting it: every arm reproduces its own residual traces, counts,
        converged flags and exit audits exactly.
        """
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
        """Scaled residual between two **full** ``y`` snapshots.

        ``subset`` restricts the test to a set of component indices, which is
        how a block arm's inner solve tests only its own module's state.  When
        the caller already holds a subset-aligned pair --- which is what
        reading only the subset gives it --- :meth:`residual_over` is the
        entry point that does not need the full lists at all.
        """
        sel = self.subset_indices(subset)
        if subset is None:
            return self._residual_aligned(sel, prev, cur)
        return self._residual_aligned(
            sel, [prev[i] for i in sel], [cur[i] for i in sel]
        )

    def residual_over(self, sel, prev_a: list, cur_a: list) -> Residual:
        """The same residual, from snapshots already aligned with ``sel``.

        ``sel`` must be the sorted index list :meth:`subset_indices` returned
        and ``prev_a`` / ``cur_a`` must be what :meth:`read` returned for
        :meth:`bind_subset` on that same ``sel``.  The :class:`Residual` it
        builds carries **absolute** component indices, so everything
        downstream --- ``spec.name(i)``, ``res.above(tau)``, the moved-constant
        report --- is unchanged.
        """
        return self._residual_aligned(sel, prev_a, cur_a)

    def _residual_aligned(self, sel, prev_a: list, cur_a: list) -> Residual:
        """One pass over ``sel``, dispatching on each component's category.

        Written as one loop rather than three so that a component's category
        decides its test in exactly one place.  The ordering of every output
        list is ascending component index, which is what the previous
        three-loop form produced and what ``argmax`` tie-breaking depends on.
        """
        idx_c: list[int] = []
        scaled_l: list[float] = []
        nan_new: list[int] = []
        mismatch_d: list[int] = []
        moved_k: list[int] = []
        cat = self.category
        scale = self.scale
        for j, i in enumerate(sel):
            c = cat[i]
            a, b = prev_a[j], cur_a[j]
            if c == CONTINUOUS:
                idx_c.append(i)
                fa, fb = _float_view(a), _float_view(b)
                if fa is None or fb is None or fa.shape != fb.shape:
                    scaled_l.append(np.inf)
                    continue
                d = np.abs(fb - fa)
                if not np.all(np.isfinite(fb)):
                    nan_new.append(i)
                    scaled_l.append(np.inf)
                    continue
                scaled_l.append(float(np.max(d)) / scale[i])
            elif c == NONFINITE:
                # A26.  Tested rather than excluded: the non-finite pattern
                # must be unchanged, and the finite entries must satisfy the
                # scaled test.  A component that was NaN and is now a number,
                # or the reverse, is a hard non-convergence and is named.
                idx_c.append(i)
                fa, fb = _float_view(a), _float_view(b)
                if fa is None or fb is None or fa.shape != fb.shape:
                    scaled_l.append(np.inf)
                    continue
                ma, mb = np.isfinite(fa), np.isfinite(fb)
                if not np.array_equal(ma, mb):
                    nan_new.append(i)
                    scaled_l.append(np.inf)
                    continue
                if not ma.any():
                    scaled_l.append(0.0)
                    continue
                d = np.abs(fb[mb] - fa[ma])
                scaled_l.append(float(np.max(d)) / scale[i])
            elif c == DISCRETE:
                if not _same(a, b):
                    mismatch_d.append(i)
            elif c == CONSTANT:
                if not _same(a, b):
                    moved_k.append(i)
            # NAN_IN_HARVEST and EXCLUDED_ACCUMULATOR are not tested.  The
            # first exists only in SPEC_MODE_A18; the second only ever holds
            # quantities with a recorded justification for accumulating.
        scaled = np.asarray(scaled_l, dtype=float)
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
