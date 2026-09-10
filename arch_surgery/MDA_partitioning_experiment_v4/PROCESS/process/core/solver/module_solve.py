"""VP4 (framework hook F7c) -- the *shape* of the fixed-point loop is a driver
choice.

Upstream PROCESS solves its multidisciplinary analysis with **one flat loop**:
``Caller.call_models`` runs the whole model sequence, tests two derived scalars
(the objective and the constraint vector) for idempotence, and sweeps again if
they moved.  Every model is re-run on every sweep, whatever moved.

Variant point VP4 replaces that with a **block Gauss-Seidel** schedule over the
DSM's three modules.  Each module is iterated to *its own* fixed point, at the
one tolerance, and the schedule then runs **once**::

    one pass:  [M1 solved]  [M2 solved]  [PULSE]  [M3 solved]  [FF]

Upstream behaviour is the default: with ``PROCESS_ARCH_MDA`` unset
:data:`ENABLED` is ``False``, ``Caller.call_models`` never consults anything
here, and the module is not even asked for its predicate.  An unrecognised
value is an **import-time** refusal, not a silent fallback to the baseline -- a
misspelled arm that quietly runs the reference is the failure mode that makes a
whole measurement worthless (the pattern A3 set for VP1 and A13 for VP2).

**The schedule runs once, and that is not a setting.**  An earlier revision
offered a second policy in which the whole schedule repeated while a joint test
over the entire coupling state still saw movement -- a verification receipt the
arm paid for.  Task A43 (st-trust-gap) measured it: across 91 888 evaluations of
that arm, the verification pass triggered a further pass **zero times**.  The
user removed the arm that used it (decision D22) and fixed one tolerance for
every converger (decision D23), so there is no longer anything for a second
policy to select and the switch that selected it is retired.  What used to
verify the feed-forward assertion is the **uncharged exit audit**, taken outside
the arm, which is where it belonged: an in-loop receipt is a cost the arm pays
to tell the experimenter something the experimenter can measure for free.

The predicate is Phase A's, not a new one
-----------------------------------------
Decision **D14(c)**, as revised by the user: *a per-module solver cannot use a
global objective/constraint test, because one module does not determine those
quantities.*  So every block loop here stops on the **coupling-state**
predicate --  ``max |dy_i| / s_i < tau`` over the continuous components, exact
equality over the discrete ones, and constants asserted rather than excluded --
with the categories and scales taken from the committed per-configuration
artifact ``harness/data/coupling_state_<configuration>.json``.

That artifact is *loaded*, and the predicate code is *imported from Phase A's
own module*, rather than either being reimplemented here.  Two implementations
of one predicate is how they drift, and the whole point of D14(c) is that the
variant is tested by the same rule Phase A measured.  The load is lazy and
happens only when VP4 is on, so ``process`` still imports standalone with the
variant point off.

A block loop's test is restricted to that block's own write set
---------------------------------------------------------------
Exactly as the evaluation phase's block arm restricts it
(``arms.build_blocks``), and the subsets come from the committed artifact
``harness/data/write_sets_<configuration>.json`` measured by the write
census.

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

Two non-default arrangements, one predicate
------------------------------------------
``partitioned`` is the block schedule above.  ``flat`` is the same predicate on
a **single block containing every in-loop node** --- one flat sweep of the whole
model sequence, repeated until the coupling state stops moving.  It is decision
**D18**'s predicate-matched control ``A0'``: the reference arm and ``A0'``
differ only in the stopping rule, and ``A0'`` and the intervention differ only
in the arrangement, so the two effects an earlier revision measured as a sum can
be separated.

A block loop that covers every in-loop node has already compared two successive
full sweeps over the whole coupling vector when it stops, so there is nothing
left for a further pass to ask.  ``caller._call_models_partitioned`` records
whether that condition held, per call, from the schedule that was actually
built rather than from the arrangement's name.

Selection
---------
``PROCESS_ARCH_MDA``
    ``flat`` or ``partitioned``; unset is upstream's own loop.
``PROCESS_ARCH_TAU``
    Convergence tolerance for the coupling-state predicate -- **the one
    tolerance every converger in every arm uses** (decision D23), the flat loop
    and each block loop alike.  Default ``1e-6``, the evaluation phase's
    starting rung (decision D15).  There is no second, "inner" tolerance: the
    switch that offered one is retired, because comparisons are made at matched
    *achieved* accuracy, which the exit audit records per run, rather than at
    matched settings.
``PROCESS_ARCH_PREDICATE``
    ``frozen`` or ``mixed``; unset is ``frozen``.  Which denominator the
    coupling-state predicate scales a step by -- the measured scale alone, or
    the measured scale kept as a floor under the current magnitude
    (``max|dy_i| / max(|y_i|, s_i)``).  The two are bit-identical wherever the
    current magnitude is at or below the scale, and ``mixed`` is never tighter,
    so no count can go up.  The choice is passed to every predicate evaluation
    this arrangement makes -- the flat loop's single block and each block loop
    alike -- and read back as :data:`PREDICATE_MODE`; the test itself lives in
    the harness's coupling-state module and is not reimplemented here.  Driver
    change DR5, improvement item 5a's pre-declared trial.
``PROCESS_ARCH_COUPLING_STATE``
    Path to the committed coupling-state artifact for the configuration being
    run.  **Required** when this arrangement is on: there is no default, because
    a predicate silently taken from another configuration's scales is exactly
    the kind of quiet wrong answer this project gates against.
``PROCESS_ARCH_WRITE_SETS``
    Path to the committed per-block write sets for the same configuration.  Also
    required, for the same reason, and cross-checked against the coupling-state
    artifact's ``components_sha256`` so the two cannot be from different
    generations of the same configuration.
``PROCESS_ARCH_PASS_TRACE``
    **A31 (drift-diagnostic), observation only.**  Path of a JSONL file into
    which every *joint-test* residual evaluation is appended: with one block
    covering every in-loop node, that block's own inner residuals **are** the
    joint test.  Per evaluation it records the pass index, the residual max
    and argmax (with the moving element's before/after values as exact hex
    floats), and, from pass 2 on, **every** component at or above ``tau``
    with the same detail.  Pass-1 evaluations record the argmax and counts
    only: pass 1 is the solve pass, where movement is expected, and a full
    census there would be hundreds of components per optimiser evaluation
    saying nothing the diagnostic asks.  Unset — the default — every hook is
    a no-op and behaviour is byte-identical (gated, not asserted: protocol
    §12).  The trace observes; it never touches a float the run computes.
"""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path

from process.core.solver import ArchitectureRefusal

__all__ = [
    "BLOCK_ORDER",
    "COUPLING_STATE_PATH",
    "ENABLED",
    "FLAT",
    "FLAT_BLOCK_LABEL",
    "FLAT_BLOCK_ORDER",
    "FLAT_ITERATED",
    "GLOBAL_BLOCK_SWEEP_CAP",
    "INNER_CAP",
    "ITERATED",
    "MDA_MODE",
    "MDA_MODES",
    "PASS_TRACE_PATH",
    "PREDICATE_MODE",
    "PREDICATE_MODES",
    "TAU",
    "TRACE_ENABLED",
    "WRITE_SETS_PATH",
    "ModuleSolveFailure",
    "block_order",
    "iterated",
    "load_spec",
    "load_subsets",
    "trace_pass",
]

# --------------------------------------------------------------------------
# Selection, resolved once at import
# --------------------------------------------------------------------------

#: The shape of the analysis loop.  ``upstream`` is the variable unset.
MDA_MODES = ("upstream", "flat", "partitioned")

MDA_MODE: str = os.environ.get("PROCESS_ARCH_MDA", "").strip() or "upstream"

if MDA_MODE not in MDA_MODES:
    raise ArchitectureRefusal(
        f"PROCESS_ARCH_MDA={MDA_MODE!r} is not a recognised shape for the "
        f"analysis loop; expected one of {MDA_MODES} (or unset for "
        f"{'upstream'!r})."
    )

#: True when the driver runs a coupling-state fixed point instead of
#: upstream's ``objf``/``conf`` idempotence loop.  Both non-default shapes set
#: it: they differ in the *schedule*, not in the predicate.
ENABLED: bool = MDA_MODE != "upstream"

#: True when the schedule is a single block over every in-loop node --- the
#: predicate-matched flat control ``A0'`` of decision **D18**.
#:
#: A26 §10 asked whether this arrangement is the degenerate case of the block
#: schedule with one block containing every node, and answered *nearly*: the
#: schedule tables hardcoded the three-module partition, and a further pass was
#: redundant with one block but was still paid.  Both are fixed here and in
#: ``caller.module_schedule`` / ``caller._call_models_partitioned``; nothing
#: else about it is new.  It inherits the predicate, the spec loading, the
#: subset machinery and the failure policy unchanged.
FLAT: bool = MDA_MODE == "flat"

#: Convergence tolerance of the coupling-state predicate, and **the only one**:
#: decision D23 (the user's ruling of 2026-09-10) fixes one tolerance for every
#: converger in every arm and both phases, so a block loop stops by the same
#: number a flat loop stops by.  Default 1e-6, the evaluation phase's first
#: rung (decision D15).
TAU: float = float(os.environ.get("PROCESS_ARCH_TAU", "1e-6"))

#: The two rulers the coupling-state predicate can scale a step by.  The names
#: are the harness module's own (``ystate.RULERS``); they are repeated here as
#: a literal rather than imported because this guard runs at *import*, before
#: any coupling state has been loaded, and a driver that could only refuse a
#: misspelt setting after it had found a file would refuse it too late.  That
#: the two lists agree is checked where the predicate is first used, below.
PREDICATE_MODES = ("frozen", "mixed")

#: Which denominator the coupling-state predicate scales a step by: ``frozen``
#: -- the measured scale alone, every earlier revision's ruler and the default
#: here -- or ``mixed``, the conventional scaled step with that scale kept as a
#: floor under the current magnitude.  Driver change DR5.
#:
#: It selects a denominator and nothing else.  The number of components each
#: evaluation compares is fixed by the block's write set, so
#: ``COMPONENTS_COMPARED`` is the same under both rulers for the same schedule
#: -- which is the free consistency check between them: a ``mixed`` run that
#: never crossed the tolerance differently must reproduce the ``frozen`` run's
#: counter exactly.
PREDICATE_MODE: str = (
    os.environ.get("PROCESS_ARCH_PREDICATE", "").strip() or "frozen"
)

if PREDICATE_MODE not in PREDICATE_MODES:
    raise ArchitectureRefusal(
        f"PROCESS_ARCH_PREDICATE={PREDICATE_MODE!r} is not a recognised "
        f"convergence ruler; expected one of {PREDICATE_MODES} (or unset for "
        f"{'frozen'!r}).  Refused rather than defaulted: a run of one "
        f"predicate recorded under the other's name cannot be told apart "
        f"afterwards."
    )

#: The configuration's committed coupling-state artifact.  No default: see the
#: module docstring.
COUPLING_STATE_PATH: str | None = (
    os.environ.get("PROCESS_ARCH_COUPLING_STATE") or None
)

#: The configuration's committed per-block write sets.  No default, same reason.
WRITE_SETS_PATH: str | None = os.environ.get("PROCESS_ARCH_WRITE_SETS") or None

if ENABLED and not WRITE_SETS_PATH:
    raise ArchitectureRefusal(
        f"PROCESS_ARCH_MDA={MDA_MODE!r} needs PROCESS_ARCH_WRITE_SETS to name "
        f"the committed per-block write sets for the configuration being run.  "
        f"There is no default: each block loop tests its own block's write "
        f"set, and another configuration's subsets would silently test the "
        f"wrong components."
    )

if ENABLED and not COUPLING_STATE_PATH:
    raise ArchitectureRefusal(
        f"PROCESS_ARCH_MDA={MDA_MODE!r} needs PROCESS_ARCH_COUPLING_STATE to "
        f"name the committed coupling-state artifact for the configuration "
        f"being run.  There is no default: the predicate's scales are "
        f"per-configuration, and silently taking another one's scales would "
        f"change what 'converged' means with no symptom."
    )

# --------------------------------------------------------------------------
# A31 (drift-diagnostic): the per-pass joint-test trace.  Observation only.
# --------------------------------------------------------------------------

#: Where the trace lands, or ``None`` (the default) for no trace at all.
PASS_TRACE_PATH: str | None = os.environ.get("PROCESS_ARCH_PASS_TRACE") or None

#: True when a trace file is named.  Every call site in ``caller.py`` guards
#: on this, so with the variable unset the hooks cost one module-attribute
#: read per joint test and touch nothing else — and that neutrality is
#: **gated** against A28's recorded counts, not asserted (protocol §12).
TRACE_ENABLED: bool = PASS_TRACE_PATH is not None

if TRACE_ENABLED and not ENABLED:
    raise ArchitectureRefusal(
        "PROCESS_ARCH_PASS_TRACE is set with PROCESS_ARCH_MDA unset, so the "
        "run uses upstream's own loop and has no joint test to trace.  A "
        "trace that silently records nothing is how a diagnostic reports an "
        "absence it never measured."
    )

#: The pass index from which the full above-tau census is recorded.  Below
#: it, only the argmax and the counts are kept: pass 1 is the solve pass,
#: where movement is expected and a full census would bury the diagnostic.
TRACE_FULL_FROM: int = int(
    os.environ.get("PROCESS_ARCH_PASS_TRACE_FULL_FROM", "").strip() or "2"
)

#: Cap on fully-recorded components per evaluation — a disk guard, not a
#: filter.  When it binds, the record says how many entries were dropped;
#: the diagnostic population (pass >= 2 exceedances) is measured in units,
#: not thousands, so a bound record is itself a finding.
TRACE_MAX_ABOVE = 5000

_TRACE_FILE = None


def _trace_fh(spec):
    """The trace file, opened once, with a self-describing header line."""
    global _TRACE_FILE
    if _TRACE_FILE is None:
        _TRACE_FILE = open(PASS_TRACE_PATH, "a")  # noqa: SIM115 - held open
        _TRACE_FILE.write(json.dumps({
            "kind": "header",
            "mda": MDA_MODE,
            "tau": TAU,
            "full_from": TRACE_FULL_FROM,
            "n_components": len(spec.keys),
            "components_sha256": spec.components_sha256(),
        }) + "\n")
    return _TRACE_FILE


def _trace_component(spec, i, a, b, scaled, tau):
    """One component's movement, exactly: hex floats, argmax element.

    ``a``/``b`` are the component's value in the previous and current
    snapshot.  For an array the record names the element of maximum
    absolute change and carries *its* before/after pair — the whole array
    would bury the moving element under hundreds of quiet ones, and the
    residual is a max, so the argmax element is the movement.

    ``scaled`` is ``None`` for a component outside the scaled test — a
    moved constant or a discrete mismatch, which fail by exact equality
    and have no scale.  Their before/after pair is the whole record.
    """
    import numpy as np  # noqa: PLC0415 - trace path only

    ys = _ystate_module()
    rec: dict = {
        "i": int(i),
        "key": spec.name(i),
        "category": spec.category[i],
    }
    if scaled is not None:
        rec["scaled"] = float(scaled)
        rec["scaled_hex"] = float(scaled).hex()
        rec["scale"] = float(spec.scale[i])
    try:
        fa, fb = ys._float_view(a), ys._float_view(b)
        if fa is None or fb is None or fa.shape != fb.shape:
            rec["note"] = "not float-viewable in both snapshots, or reshaped"
            rec["before_repr"] = repr(a)[:160]
            rec["after_repr"] = repr(b)[:160]
            return rec
        d = np.abs(fb - fa)
        # A NaN difference must surface as the argmax, not vanish under it.
        d = np.where(np.isnan(d), np.inf, d)
        j = int(np.argmax(d))
        rec["n_elements"] = int(fa.size)
        if fa.size > 1:
            rec["elem"] = j
            s = float(spec.scale[i])
            if s > 0.0:
                rec["n_elem_above"] = int(
                    np.count_nonzero(d[np.isfinite(d)] / s >= tau)
                )
        va, vb = float(fa[j]), float(fb[j])
        rec["before"] = va
        rec["after"] = vb
        rec["before_hex"] = va.hex()
        rec["after_hex"] = vb.hex()
    except Exception as exc:  # noqa: BLE001 - the trace must not kill the run
        rec["error"] = f"{type(exc).__name__}: {exc}"
    return rec


def trace_pass(kind, call_idx, pass_idx, spec, y_prev, y_cur, res, tau):
    """Append one joint-test evaluation to the trace.

    ``y_prev``/``y_cur`` must be **full** snapshots (a subset=None residual),
    indexable by the absolute component indices ``res`` carries — which is
    what both call sites hold: the outer test reads the whole vector, and
    the flat arm's single block has no subset in the write-set artifact.
    Callers guard on :data:`TRACE_ENABLED`; this function assumes it.
    """
    fh = _trace_fh(spec)
    scaled_by_idx = dict(zip(res.idx_c, res.scaled.tolist(), strict=True))
    rec: dict = {
        "kind": kind,
        "call": int(call_idx),
        "pass": int(pass_idx),
        "max": res.max,
        "max_hex": float(res.max).hex(),
        "n_above": res.n_above(tau),
        "n_discrete_mismatch": len(res.mismatch_discrete),
        "n_constant_moved": len(res.moved_constant),
        "n_nan_new": len(res.nan_new),
    }
    if res.argmax is not None:
        rec["argmax"] = _trace_component(
            spec, res.argmax, y_prev[res.argmax], y_cur[res.argmax],
            scaled_by_idx[res.argmax], tau,
        )
    if pass_idx >= TRACE_FULL_FROM:
        above = res.above(tau)
        rec["above"] = [
            _trace_component(spec, i, y_prev[i], y_cur[i],
                             scaled_by_idx[i], tau)
            for i in above[:TRACE_MAX_ABOVE]
        ]
        if len(above) > TRACE_MAX_ABOVE:
            rec["above_truncated"] = len(above) - TRACE_MAX_ABOVE
        if res.mismatch_discrete:
            rec["discrete_mismatch"] = [
                spec.name(i) for i in res.mismatch_discrete
            ]
            rec["discrete_mismatch_detail"] = [
                _trace_component(spec, i, y_prev[i], y_cur[i], None, tau)
                for i in res.mismatch_discrete[:TRACE_MAX_ABOVE]
            ]
        if res.moved_constant:
            rec["moved_constant"] = [spec.name(i) for i in res.moved_constant]
            # The exact-equality assertion has no tolerance, so *how far* a
            # constant moved is the mechanism question — recorded as hex.
            rec["moved_constant_detail"] = [
                _trace_component(spec, i, y_prev[i], y_cur[i], None, tau)
                for i in res.moved_constant[:TRACE_MAX_ABOVE]
            ]
        if res.nan_new:
            rec["nan_new"] = [spec.name(i) for i in res.nan_new]
    else:
        rec["above_elided"] = True
    fh.write(json.dumps(rec) + "\n")
    fh.flush()

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

#: The one block the flat arrangement iterates.
FLAT_ITERATED: frozenset[str] = frozenset({FLAT_BLOCK_LABEL})


def block_order() -> tuple[str, ...]:
    """The block labels this arrangement's single schedule pass walks."""
    return FLAT_BLOCK_ORDER if FLAT else BLOCK_ORDER


def iterated() -> frozenset[str]:
    """The block labels this arrangement solves to their own fixed point."""
    return FLAT_ITERATED if FLAT else ITERATED

#: Caps are **detectors, not budgets** (Phase A's ``engine.py``).  Reaching one
#: raises; it never silently returns a half-solved state.  There is no cap on
#: schedule passes because there is only ever one of them.
INNER_CAP = 20
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

#: ``harness/ystate.py`` -- the coupling-state predicate in both of its
#: rulers, in the V4 harness beside this copy.  Reached by path for the same reason
#: ``caller.NODE_MAP_PATH`` is: the harness is not an importable package.
#: Re-pointed from ``arch_surgery/fixedpoint/ystate.py`` by A46 (process-copy)
#: under decision D20 -- V4 runs its own copy of PROCESS, so the copy reaches
#: for the V4 harness and not for V3's research tree.
#: The target is a committed file of this experiment: its source, its sha256
#: and the check that the two are byte-identical are recorded in
#: ``harness/data/PROVENANCE.json``.
YSTATE_MODULE_PATH = (
    Path(__file__).resolve().parents[4]
    / "harness"
    / "ystate.py"
)

_ystate = None
_SPEC_CACHE: dict = {}
_SUBSET_CACHE: dict = {}


def _ystate_module():
    """The coupling-state module, loaded once, on the non-upstream path only."""
    global _ystate
    if _ystate is not None:
        return _ystate
    if not YSTATE_MODULE_PATH.exists():
        raise ArchitectureRefusal(
            f"PROCESS_ARCH_MDA={MDA_MODE!r} needs the coupling-state "
            f"predicate at {YSTATE_MODULE_PATH}, which is not present."
        )
    spec = importlib.util.spec_from_file_location(
        "_arch_surgery_ystate", YSTATE_MODULE_PATH
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    # DR5.  The ruler names are guarded at import from a literal (the refusal
    # has to happen before any file is read), so the literal is checked against
    # the module that actually implements them the first time that module is
    # loaded.  A driver that accepted a setting the predicate does not know
    # would refuse nothing and run the default under the other's name.
    rulers = getattr(mod, "RULERS", None)
    if rulers is None or tuple(rulers) != tuple(PREDICATE_MODES):
        raise ArchitectureRefusal(
            f"the coupling-state module at {YSTATE_MODULE_PATH} implements "
            f"rulers {rulers!r}, this driver guards "
            f"{tuple(PREDICATE_MODES)!r}.  The two must be the same list: "
            f"there is one implementation of the predicate per revision of "
            f"this experiment, and a driver whose guard disagreed with it "
            f"would accept a setting the predicate ignores."
        )
    _ystate = mod
    return mod


def load_spec(path: str | Path | None = None):
    """Rebuild the coupling-state :class:`YSpec` from its committed artifact.

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
    p = Path(path or COUPLING_STATE_PATH)
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

    spec = ys.YSpec(
        keys, category, scale, record.get("n_components"), comps,
        mode=record.get("spec_mode", ys.SPEC_MODE_A18),
        scale_floor=float(record.get("scale_floor", ys.SCALE_FLOOR)),
    )

    rebuilt = spec.components_sha256()
    committed = record.get("components_sha256")
    if committed and rebuilt != committed:
        raise ArchitectureRefusal(
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
        # DR5.  The tolerance and the ruler together are what "converged"
        # means; a block that carried one and not the other would leave a
        # record naming half of its own stopping rule (improvement item 5a's
        # trap (i)).
        "predicate_mode": PREDICATE_MODE,
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
      ``components_sha256`` -- one configuration, one generation, both files;
    * every key named in a subset must resolve to a component of the spec, and
      the union of the subsets must cover every component of the spec.
    """
    p = Path(path or WRITE_SETS_PATH)
    cached = _SUBSET_CACHE.get(str(p))
    if cached is not None:
        return cached
    record = json.loads(p.read_text())

    spec_sha = spec.components_sha256()
    art_sha = record.get("ystate_components_sha256")
    if art_sha and art_sha != spec_sha:
        raise ArchitectureRefusal(
            f"write set {p} was built against ystate components {art_sha} but "
            f"the loaded spec is {spec_sha}: the two artifacts are not from "
            f"the same configuration and generation."
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
        raise ArchitectureRefusal(
            f"write set {p} names {len(unknown)} keys the coupling-state spec "
            f"does not have, e.g. {sorted(unknown)[:5]}"
        )
    missing = len(spec.keys) - len(covered)
    if missing:
        raise ArchitectureRefusal(
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
