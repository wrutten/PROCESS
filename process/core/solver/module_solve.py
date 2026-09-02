"""VP4 (framework hook F7c) -- the *shape* of the fixed-point loop is a driver
choice.

Upstream PROCESS solves its multidisciplinary analysis with **one flat loop**:
``Caller.call_models`` runs the whole model sequence, tests two derived scalars
(the objective and the constraint vector) for idempotence, and sweeps again if
they moved.  Every model is re-run on every sweep, whatever moved.

Variant point VP4 replaces that with a **block Gauss-Seidel** schedule over the
DSM's three modules.  Each module is iterated to *its own* fixed point before
the next module runs, and an outer loop over the modules closes whatever
cross-module coupling remains::

    outer:  [M1 solved]  [M2 solved]  [PULSE]  [M3 solved]  [FF]
            \\____________________ until y stops moving ______________/

``off`` is the default and is upstream behaviour exactly: :data:`ENABLED` is
``False``, ``Caller.call_models`` never consults anything here, and the module
is not even asked for its predicate.  An unrecognised value of
``PROCESS_ARCH_MODULE_SOLVE`` is an **import-time** error, not a silent
fallback to the baseline -- a misspelled arm that quietly runs the reference is
the failure mode that makes a whole measurement worthless (the pattern A3 set
for VP1 and A13 for VP2).

The predicate is Phase A's, not a new one
-----------------------------------------
Decision **D14(c)**, as revised by the user: *a per-module solver cannot use a
global objective/constraint test, because one module does not determine those
quantities.*  So the inner and outer tests here are Phase A's **coupling-state**
predicate --  ``max |dy_i| / s_i < tau`` over the continuous components, exact
equality over the discrete ones, and constants asserted rather than excluded --
with the categories and scales taken from the committed per-scenario artifact
``arch_surgery/docs/data/ystate_<scenario>.json``.

That artifact is *loaded*, and the predicate code is *imported from Phase A's
own module*, rather than either being reimplemented here.  Two implementations
of one predicate is how they drift, and the whole point of D14(c) is that the
variant is tested by the same rule Phase A measured.  The load is lazy and
happens only when VP4 is on, so ``process`` still imports standalone with the
variant point off.

The inner test is restricted to the module's own write set
----------------------------------------------------------
Exactly as Phase A's block arm restricts it (``arms.build_blocks``), and the
subsets come from a committed artifact ``writeset_<scenario>.json`` measured by
the ``modules`` probe's write census.

**A25 first tried to skip that**, on the argument that a component no running
node writes cannot move, so testing the whole vector must give the same answer.
The argument is wrong and the first variant run found it: ``ystate``'s
predicate scores a component ``inf`` whenever *either* snapshot is not
float-viewable, and in a fresh process every field no model has written yet is
exactly that.  An M1 inner solve was therefore held open by
``ccfe_hcpb.pnuc_tot_blk_sector`` -- a field M3 writes and M1 cannot touch --
for all twenty inner sweeps, and the run died at the cap.  Equality of *values*
is not equality of *scores*.  The subsets are not an optimisation; they are
load-bearing.

Two non-default arms, one predicate
-----------------------------------
``per_module`` is the block schedule above.  ``flat_state`` is the same
predicate on a **single block containing every in-loop node** --- one flat
sweep of the whole model sequence, repeated until the coupling state stops
moving.  It is decision **D18**'s predicate-matched control ``A0'``: the
baseline ``R`` and ``A0'`` differ only in the stopping rule, and ``A0'`` and
the variant ``A1'`` differ only in the architecture, so the two effects
Phase B previously measured as a sum can be separated.

The outer pass is **skipped** when one block covers every in-loop node, and
that is a correctness statement rather than an optimisation: the block's own
inner test already compares two successive full sweeps over the whole coupling
vector, which is exactly what the outer test would ask.  Paying it anyway costs
one extra full sweep per ``call_models`` --- ``y_outer_prev`` is the state at
*entry*, so outer pass 1 always fails and outer pass 2 always succeeds after
one sweep.  ``caller._call_models_by_module`` records whether the guard fired,
per call.

Selection
---------
``PROCESS_ARCH_MODULE_SOLVE``
    ``off`` (default), ``per_module``, or ``flat_state``.
``PROCESS_ARCH_TAU``
    Convergence tolerance for the coupling-state predicate.  Default ``1e-6``,
    Phase A's starting rung (decision D15).
``PROCESS_ARCH_INNER_TAU``
    Tolerance of an inner block solve, defaulting to ``PROCESS_ARCH_TAU``.
    Unset reproduces A25's arm exactly.  It exists because A26 established
    that arms must be compared at matched **achieved** accuracy rather than at
    matched tolerance, and the block arm's inner tolerance is the parameter
    that moves its achieved accuracy independently of its outer one.  Setting
    it under ``flat_state`` is an import-time error: that arm has one block and
    one tolerance.
``PROCESS_ARCH_YSTATE``
    Path to the committed ``ystate_<scenario>.json`` for the deck being run.
    **Required** when VP4 is on: there is no default, because a predicate
    silently taken from the wrong deck's scales is exactly the kind of quiet
    wrong answer this project gates against.
``PROCESS_ARCH_WRITESET``
    Path to the committed ``writeset_<scenario>.json`` for the same deck.  Also
    required, for the same reason, and cross-checked against the ystate
    artifact's ``components_sha256`` so the two cannot be from different
    generations of the same deck.
"""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path

__all__ = [
    "BLOCK_ORDER",
    "ENABLED",
    "FLAT_BLOCK_LABEL",
    "FLAT_BLOCK_ORDER",
    "FLAT_ITERATED",
    "FLAT_STATE",
    "INNER_TAU",
    "GLOBAL_BLOCK_SWEEP_CAP",
    "INNER_CAP",
    "ITERATED",
    "MODULE_SOLVE_NAME",
    "OUTER_CAP",
    "TAU",
    "ModuleSolveFailure",
    "block_order",
    "iterated",
    "WRITESET_PATH",
    "YSTATE_PATH",
    "load_spec",
    "load_subsets",
]

# --------------------------------------------------------------------------
# Selection, resolved once at import
# --------------------------------------------------------------------------

_ARMS = ("off", "per_module", "flat_state")

MODULE_SOLVE_NAME: str = (
    os.environ.get("PROCESS_ARCH_MODULE_SOLVE", "").strip() or "off"
)

if MODULE_SOLVE_NAME not in _ARMS:
    raise RuntimeError(
        f"PROCESS_ARCH_MODULE_SOLVE={MODULE_SOLVE_NAME!r} is not a recognised "
        f"module-solve arm; expected one of {_ARMS} (or unset for 'off')."
    )

#: True when the driver runs a coupling-state fixed point instead of
#: upstream's ``objf``/``conf`` idempotence loop.  Both non-default arms set
#: it: they differ in the *schedule*, not in the predicate.
ENABLED: bool = MODULE_SOLVE_NAME != "off"

#: True when the schedule is a single block over every in-loop node --- the
#: predicate-matched flat control ``A0'`` of decision **D18**.
#:
#: A26 §10 asked whether this arm is the degenerate case of the block schedule
#: with one block containing every node, and answered *nearly*: the schedule
#: tables hardcoded the three-module partition, and the outer pass is redundant
#: with one block but was still paid.  Both are fixed here and in
#: ``caller.module_schedule`` / ``caller._call_models_by_module``; nothing else
#: about the arm is new.  It inherits the predicate, the spec loading, the
#: subset machinery and the failure policy unchanged.
FLAT_STATE: bool = MODULE_SOLVE_NAME == "flat_state"

#: Convergence tolerance of the coupling-state predicate (decision D15: Phase
#: A's first rung, 1e-6).
TAU: float = float(os.environ.get("PROCESS_ARCH_TAU", "1e-6"))

#: Tolerance of an **inner** block solve, defaulting to :data:`TAU`.
#:
#: A26's fix 1 established that comparing arms at matched *tolerance* is not a
#: comparison: the block arm solves each block against inputs that are about to
#: change, so at one nominal tau it delivers far more accuracy than the flat
#: arm and only the extra work shows up in the ratio.  Reading cost off at
#: matched **achieved** accuracy needs the inner tolerance to be a parameter,
#: which in the replay engine it already is (``engine.solve_block``).  This is
#: the same knob in the driver.
#:
#: The default is :data:`TAU`, so an unset variable reproduces A25's arm
#: exactly.  ``flat_state`` has a single block and therefore no separate inner
#: tolerance: setting one there is an import-time error rather than a value
#: that quietly does nothing.
INNER_TAU: float = float(
    os.environ.get("PROCESS_ARCH_INNER_TAU", "").strip() or TAU
)

if FLAT_STATE and os.environ.get("PROCESS_ARCH_INNER_TAU", "").strip():
    raise RuntimeError(
        "PROCESS_ARCH_INNER_TAU is set with "
        "PROCESS_ARCH_MODULE_SOLVE=flat_state, which has one block and "
        "therefore one tolerance.  A knob that silently does nothing is how a "
        "ladder rung ends up mislabelled; set PROCESS_ARCH_TAU instead."
    )

#: The deck's committed coupling-state artifact.  No default: see the module
#: docstring.
YSTATE_PATH: str | None = os.environ.get("PROCESS_ARCH_YSTATE") or None

#: The deck's committed per-module write set.  No default, same reason.
WRITESET_PATH: str | None = os.environ.get("PROCESS_ARCH_WRITESET") or None

if ENABLED and not WRITESET_PATH:
    raise RuntimeError(
        f"PROCESS_ARCH_MODULE_SOLVE={MODULE_SOLVE_NAME!r} needs "
        f"PROCESS_ARCH_WRITESET to name the committed "
        f"writeset_<scenario>.json for the deck being run.  There is no "
        f"default: the inner solves test each module's own write set, and "
        f"another deck's subsets would silently test the wrong components."
    )

if ENABLED and not YSTATE_PATH:
    raise RuntimeError(
        f"PROCESS_ARCH_MODULE_SOLVE={MODULE_SOLVE_NAME!r} needs "
        f"PROCESS_ARCH_YSTATE to name the committed ystate_<scenario>.json "
        f"for the deck being run.  There is no default: the predicate's "
        f"scales are per-deck, and silently taking another deck's scales "
        f"would change what 'converged' means with no symptom."
    )

# --------------------------------------------------------------------------
# The block schedule
# --------------------------------------------------------------------------

#: Order the blocks take in the partitioned sequence.  This is Phase A's
#: ``arms.BLOCK_ORDER``, unchanged: all of M1, then all of M2, then the
#: articulation point, then M3, then the feed-forward tail.  A3's VP1
#: (``PROCESS_ARCH_SEQUENCE=build_after_physics``) is what makes M1 contiguous
#: in the driver's own call order, which is why this schedule needs no
#: reordering of its own.
BLOCK_ORDER: tuple[str, ...] = ("M1", "M2", "PULSE", "M3", "FF")

#: The single-block schedule of ``flat_state``.  One label, every in-loop node,
#: iterated --- which is a flat Gauss-Seidel sweep of the whole model sequence
#: tested on the coupling state, i.e. exactly Phase A's arm A0 living in
#: PROCESS's own driver.
FLAT_BLOCK_LABEL = "FLAT"
FLAT_BLOCK_ORDER: tuple[str, ...] = (FLAT_BLOCK_LABEL,)

#: Blocks iterated to their own fixed point.  ``PULSE`` is a single node and
#: ``FF`` feeds nothing back, so an inner solve on either would be one pass
#: with a foregone answer (Phase A's ``arms.ITERATED``).
ITERATED: frozenset[str] = frozenset({"M1", "M2", "M3"})

#: The one block ``flat_state`` iterates.
FLAT_ITERATED: frozenset[str] = frozenset({FLAT_BLOCK_LABEL})


def block_order() -> tuple[str, ...]:
    """The block labels this arm's outer pass walks, in order."""
    return FLAT_BLOCK_ORDER if FLAT_STATE else BLOCK_ORDER


def iterated() -> frozenset[str]:
    """The block labels this arm solves to their own fixed point."""
    return FLAT_ITERATED if FLAT_STATE else ITERATED

#: Caps are **detectors, not budgets** (Phase A's ``engine.py``).  Reaching one
#: raises; it never silently returns a half-solved state.
INNER_CAP = 20
OUTER_CAP = 20
GLOBAL_BLOCK_SWEEP_CAP = 200


class ModuleSolveFailure(RuntimeError):
    """A per-module solve did not converge within its cap.

    Decision **D15(d)**: a failed per-module solve *raises* and counts as a
    failed start, matching what ``Caller.call_models`` does when its own loop
    exhausts ten evaluations.  The two arms' failure modes are then comparable
    rather than one arm quietly returning an unconverged point.
    """


# --------------------------------------------------------------------------
# Phase A's predicate, imported rather than reimplemented
# --------------------------------------------------------------------------

#: ``arch_surgery/fixedpoint/ystate.py`` -- Phase A's coupling-state predicate.
#: Reached by path for the same reason ``caller.NODE_MAP_PATH`` is: the
#: research tree is not an importable package, and vendoring a second copy of
#: the predicate into ``process/`` would create exactly the drift D14(c) exists
#: to prevent.
YSTATE_MODULE_PATH = (
    Path(__file__).resolve().parents[3]
    / "arch_surgery"
    / "fixedpoint"
    / "ystate.py"
)

_ystate = None
_SPEC_CACHE: dict = {}
_SUBSET_CACHE: dict = {}


def _ystate_module():
    """Phase A's ``ystate`` module, loaded once, on the VP4-on path only."""
    global _ystate
    if _ystate is not None:
        return _ystate
    if not YSTATE_MODULE_PATH.exists():
        raise RuntimeError(
            f"PROCESS_ARCH_MODULE_SOLVE={MODULE_SOLVE_NAME!r} needs Phase A's "
            f"coupling-state predicate at {YSTATE_MODULE_PATH}, which is not "
            f"present."
        )
    spec = importlib.util.spec_from_file_location(
        "_arch_surgery_ystate", YSTATE_MODULE_PATH
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _ystate = mod
    return mod


def load_spec(path: str | Path | None = None):
    """Rebuild Phase A's :class:`YSpec` from a committed ystate artifact.

    The artifact records, per component, the key, the category and (for a
    continuous component) the scale -- which is the whole of what the predicate
    needs.  ``components_sha256`` is recomputed from the rebuilt spec and
    checked against the value the artifact carries, so a spec reconstructed
    from a truncated, reordered or hand-edited file is refused rather than
    quietly used.

    Returns
    -------
    tuple
        ``(spec, provenance)`` -- the spec, and what it was built from.
    """
    p = Path(path or YSTATE_PATH)
    cached = _SPEC_CACHE.get(str(p))
    if cached is not None:
        return cached
    ys = _ystate_module()
    record = json.loads(p.read_text())
    comps = record["components"]

    keys, category, scale = [], [], []
    for c in comps:
        ns, _, fld = c["key"].partition(".")
        keys.append((ns, fld))
        category.append(c["category"])
        scale.append(float(c.get("scale", 0.0)))

    spec = ys.YSpec(keys, category, scale, record.get("n_components"), comps)

    rebuilt = spec.components_sha256()
    committed = record.get("components_sha256")
    if committed and rebuilt != committed:
        raise RuntimeError(
            f"ystate artifact {p} does not rebuild: components_sha256 is "
            f"{rebuilt} from the rebuilt spec against {committed} recorded in "
            f"the file.  The predicate would not be Phase A's."
        )

    provenance = {
        "path": str(p),
        "scenario": record.get("scenario"),
        "format": record.get("format"),
        "n_components": len(keys),
        "components_sha256": rebuilt,
        "components_sha256_matches_artifact": bool(
            committed and rebuilt == committed
        ),
        "census": record.get("census"),
        "tau": TAU,
    }
    _SPEC_CACHE[str(p)] = (spec, provenance)
    return spec, provenance


def load_subsets(spec, path: str | Path | None = None):
    """``{module: frozenset(y indices)}`` from the committed write set.

    The artifact stores *keys*, not indices, so a subset can only be built
    against a component list it actually matches.  Two things are checked
    rather than trusted, because a subset that silently misses components is a
    convergence test that silently passes early:

    * the artifact's ``ystate_components_sha256`` must equal the spec's own
      ``components_sha256`` -- one deck, one generation, both files;
    * every key named in a subset must resolve to a component of the spec, and
      the union of the subsets must cover every component of the spec.
    """
    p = Path(path or WRITESET_PATH)
    cached = _SUBSET_CACHE.get(str(p))
    if cached is not None:
        return cached
    record = json.loads(p.read_text())

    spec_sha = spec.components_sha256()
    art_sha = record.get("ystate_components_sha256")
    if art_sha and art_sha != spec_sha:
        raise RuntimeError(
            f"write set {p} was built against ystate components {art_sha} but "
            f"the loaded spec is {spec_sha}: the two artifacts are not from "
            f"the same deck and generation."
        )

    index = {f"{ns}.{fld}": i for i, (ns, fld) in enumerate(spec.keys)}
    subsets: dict[str, frozenset] = {}
    unknown: list[str] = []
    covered: set[int] = set()
    for mod, keys in record["subsets"].items():
        idx = set()
        for k in keys:
            i = index.get(k)
            if i is None:
                unknown.append(k)
            else:
                idx.add(i)
        subsets[mod] = frozenset(idx)
        covered |= idx
    if unknown:
        raise RuntimeError(
            f"write set {p} names {len(unknown)} keys the coupling-state spec "
            f"does not have, e.g. {sorted(unknown)[:5]}"
        )
    missing = len(spec.keys) - len(covered)
    if missing:
        raise RuntimeError(
            f"write set {p} covers {len(covered)} of {len(spec.keys)} "
            f"coupling components; {missing} are written by no module, so an "
            f"inner solve would never test them."
        )

    provenance = {
        "path": str(p),
        "scenario": record.get("scenario"),
        "format": record.get("format"),
        "subsets_sha256": record.get("subsets_sha256"),
        "n_by_module": {m: len(v) for m, v in sorted(subsets.items())},
        "n_covered": len(covered),
        "n_components": len(spec.keys),
        "overlaps_between_modules": record.get("census", {}).get(
            "overlaps_between_modules"
        ),
    }
    _SUBSET_CACHE[str(p)] = (subsets, provenance)
    return subsets, provenance
