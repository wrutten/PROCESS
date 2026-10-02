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
    **Retired** (driver change DR11, task A100 (v5-test-set); decision D30
    and the V5 plan's §12 Q5).  There is one ruler, ``frozen`` --
    ``max|dy_i| / s_i`` with the measured scale alone -- and it is not a
    setting: :data:`PREDICATE_MODE` names it for the record and the second
    ruler of driver change DR5 (``mixed``, the scale kept as a floor under
    the current magnitude) is removed from the coupling-state module.  The
    name raises at import if set (``process.core.solver.RETIRED_SWITCHES``).
``PROCESS_ARCH_TEST_SET``
    ``census`` or ``write_set``; **required** when this arrangement is on
    and refused when it is off.  Which components of ``y`` each block loop
    **tests** for convergence (driver change DR11, V5 list item 6):

    * ``write_set`` -- the block's whole write set from the committed write
      sets, at whatever ``PROCESS_ARCH_TAU`` says.  This is **exactly V4's
      predicate**, kept selectable as the fallback (decision D39, the user:
      "the option to run the convergence on the state with the 10e-6
      tolerance, like v4 -- as a fallback").  Nothing on this path differs
      from the copy before DR11.
    * ``census`` -- the block's **census test set**: the components a sweep
      of the block reads before it first writes them and writes later in the
      same sweep, measured at run time over whole optimisations in the arm's
      own execution order (decision D32; the harness's
      ``experiment/test_sets.py`` measures and commits them).  The loop stops
      on those components alone; the write sets are still loaded, because
      the block trace and the harness's exit audit read them, but the loop's
      stopping subset is the test set.  A block the census never saw sweep
      has no set and tests nothing: it converges at its first pass.

    There is no default: a run that relied on one could not be told apart
    afterwards from a run that asked for the other.  Which set the loop bound,
    its width per block and the artifact's digests are stamped once per run
    in :data:`LOOP_TEST_SETS` for the record.
``PROCESS_ARCH_TEST_SETS``
    Path to the committed census test-set artifact for the configuration
    being run (``harness/data/test_sets_<configuration>.json``).  Required
    when ``PROCESS_ARCH_TEST_SET=census`` and refused otherwise, for the same
    reason the write sets have no default; cross-checked against the
    coupling-state artifact's ``components_sha256`` so the two cannot be from
    different generations of the same configuration.  The artifact is keyed
    by **loop** -- ``<mda>/<burn-time owner>`` as this driver resolved them --
    because the driver never knows an arm's name and that pair is what
    distinguishes the loops the census measured.
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
``PROCESS_ARCH_BLOCK_TRACE``
    **A90 (m2-phasea-vs-phaseb), observation only.**  Path of a JSONL file with
    one line per ``call_models`` under a block schedule: what the optimiser's
    evaluator asked for (a function evaluation, a gradient column and sign, or
    the reconcile call), the design vector as exact hex floats, and for every
    block its sweep count and, per sweep, each module's maximum scaled step
    and whether that module's own components would still fail the test.  In
    the flat arrangement that says which module held the one loop open last;
    in the partitioned one, how much each block was disturbed.  Unset — the
    default — every hook is a no-op (gate G1).

    **Driver change DR13 (A115 (v5-sweep-residual-trace)), trace path only.**
    Every sweep is also scored on two **parts** of the block's write set,
    each with its worst component named: ``census`` (the block's census test
    set) and ``non_census`` (the rest of the block's write set; the flat
    block's write set is the whole coupling state).  Under
    ``PROCESS_ARCH_TEST_SET=census`` the first part is what the loop tested
    and the second is everything it did not; under ``write_set`` the two
    split what it tested.  The test's own worst component is named beside its
    maximum, and the evaluation's line carries the objective and the
    constraint vector as hex floats.  The parts are scored from the two
    snapshots the loop already read for its own test, with the predicate's
    untimed ``residual`` -- no state is read that the loop does not read, no
    counter or timer is touched, no branch changes.
``PROCESS_ARCH_BLOCK_TRACE_CENSUS_SETS``
    **DR13, observation only.**  Under ``PROCESS_ARCH_TEST_SET=write_set``
    the census sets are not loaded by the loop, so the trace's split needs
    them named: the configuration's committed census test-set artifact,
    loaded with :func:`load_test_sets`' own checks for the loop this driver
    runs.  Refused without the block trace (a setting that changes nothing)
    and refused under ``census`` (the loop's own sets are the split there,
    and a second source could disagree with them).  Unset under
    ``write_set``, the trace scores one part, ``write_set``, and its header
    says the split was not asked for.
"""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path

from process.core.solver import ArchitectureRefusal

__all__ = [
    "BLOCK_ORDER",
    "BLOCK_TRACE_ENABLED",
    "BLOCK_TRACE_PATH",
    "COUPLING_STATE_PATH",
    "ENABLED",
    "FLAT",
    "FLAT_BLOCK_LABEL",
    "FLAT_BLOCK_ORDER",
    "FLAT_ITERATED",
    "GLOBAL_BLOCK_SWEEP_CAP",
    "INNER_CAP",
    "ITERATED",
    "LOOP_TEST_SETS",
    "MDA_MODE",
    "MDA_MODES",
    "PASS_TRACE_PATH",
    "PREDICATE_MODE",
    "PREDICATE_MODES",
    "TAU",
    "TEST_SET",
    "TEST_SETS",
    "TEST_SETS_PATH",
    "TRACE_ENABLED",
    "WRITE_SETS_PATH",
    "ModuleSolveFailure",
    "block_order",
    "iterated",
    "load_loop_tests",
    "load_spec",
    "load_subsets",
    "load_test_sets",
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

#: The rulers the coupling-state predicate can scale a step by: **one**.  The
#: name is the harness module's own (``ystate.RULERS``); it is repeated here
#: as a literal rather than imported because the check that the two lists
#: agree runs where the predicate is first used, below, and a driver whose
#: guard disagreed with the module implementing the ruler would be accepting
#: a setting the predicate ignores.  DR11 (A100 (v5-test-set)) removed the
#: second ruler of driver change DR5 (``mixed``: the measured scale kept as a
#: floor under the current magnitude) under decision D30 and the V5 plan's
#: §12 Q5, and retired the switch that selected it
#: (``process.core.solver.RETIRED_SWITCHES``).
PREDICATE_MODES = ("frozen",)

#: The one denominator the coupling-state predicate scales a step by: the
#: measured scale alone, ``max|dy_i| / s_i`` -- every revision's ruler.  Not
#: a setting since DR11: named here so the record can say which ruler its
#: loops stopped on, and passed to every predicate evaluation this
#: arrangement makes (the flat loop's single block and each block loop alike).
PREDICATE_MODE: str = "frozen"

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
# DR11 (A100 (v5-test-set)): which components each block loop tests
# --------------------------------------------------------------------------

#: The two things a block loop can stop on.  ``write_set`` is V4's predicate
#: exactly -- the block's whole write set -- kept as the fallback (decision
#: D39); ``census`` is the measured test set (decision D32).
TEST_SETS = ("census", "write_set")

#: Which of the two this run's loops test, or ``None`` with the variable
#: unset -- which is a refusal when the arrangement is on and the only legal
#: state when it is off.
TEST_SET: str | None = os.environ.get("PROCESS_ARCH_TEST_SET", "").strip() or None

if TEST_SET is not None and TEST_SET not in TEST_SETS:
    raise ArchitectureRefusal(
        f"PROCESS_ARCH_TEST_SET={TEST_SET!r} is not a recognised test set; "
        f"expected one of {TEST_SETS}.  Refused rather than defaulted: a run "
        f"that tested one set under the other's name could not be told apart "
        f"afterwards."
    )

if ENABLED and TEST_SET is None:
    raise ArchitectureRefusal(
        f"PROCESS_ARCH_MDA={MDA_MODE!r} needs PROCESS_ARCH_TEST_SET to say "
        f"which components each block loop tests: 'census' (the measured "
        f"test set, decision D32) or 'write_set' (the block's whole write "
        f"set, V4's predicate, the fallback of decision D39).  There is no "
        f"default, so that no run relies on one."
    )

if TEST_SET is not None and not ENABLED:
    raise ArchitectureRefusal(
        f"PROCESS_ARCH_TEST_SET={TEST_SET!r} is set with PROCESS_ARCH_MDA "
        f"unset, so the run uses upstream's own loop and has no block loop "
        f"to hand a test set to.  A setting that changes nothing under the "
        f"right name is refused."
    )

#: The configuration's committed census test-set artifact.  Required with
#: ``census``, refused with ``write_set``; no default, as the write sets.
TEST_SETS_PATH: str | None = os.environ.get("PROCESS_ARCH_TEST_SETS") or None

if TEST_SET == "census" and not TEST_SETS_PATH:
    raise ArchitectureRefusal(
        "PROCESS_ARCH_TEST_SET='census' needs PROCESS_ARCH_TEST_SETS to name "
        "the committed census test-set artifact for the configuration being "
        "run.  There is no default: another configuration's sets would "
        "silently test the wrong components."
    )

if TEST_SETS_PATH and TEST_SET != "census":
    raise ArchitectureRefusal(
        f"PROCESS_ARCH_TEST_SETS is set with PROCESS_ARCH_TEST_SET="
        f"{TEST_SET!r}: a census artifact named for a loop that tests the "
        f"write set (or for no loop at all) would be a setting that changes "
        f"nothing under the right name.  Refused."
    )

#: What the loops bound, stamped once per run when the sets are first loaded
#: (``load_loop_tests``): the test set, its source artifact and digests, the
#: loop key the artifact was selected by, and the width per block.  Read by
#: the harness into the run record as ``loop_test_sets``; null there with
#: the arrangement off, when this is never filled.
LOOP_TEST_SETS: dict = {"test_set": TEST_SET, "loaded": False}

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
# A90 (m2-phasea-vs-phaseb): the per-evaluation block trace.  Observation only.
# --------------------------------------------------------------------------

#: Where the block trace lands, or ``None`` (the default) for no trace.
BLOCK_TRACE_PATH: str | None = os.environ.get("PROCESS_ARCH_BLOCK_TRACE") or None

#: True when a block-trace file is named.  Every call site guards on it, so
#: with the variable unset the hooks cost one module-attribute read per
#: evaluation and touch nothing else; switch neutrality is gated (G1).
BLOCK_TRACE_ENABLED: bool = BLOCK_TRACE_PATH is not None

if BLOCK_TRACE_ENABLED and not ENABLED:
    raise ArchitectureRefusal(
        "PROCESS_ARCH_BLOCK_TRACE is set with PROCESS_ARCH_MDA unset, so the "
        "run uses upstream's own loop and has no block to trace.  A trace "
        "that silently records nothing is how a diagnostic reports an "
        "absence it never measured."
    )

#: DR13 (A115 (v5-sweep-residual-trace)): the census test-set artifact the
#: block trace splits a write-set loop's score by.  Trace path only.
BLOCK_TRACE_CENSUS_PATH: str | None = (
    os.environ.get("PROCESS_ARCH_BLOCK_TRACE_CENSUS_SETS") or None
)

if BLOCK_TRACE_CENSUS_PATH and not BLOCK_TRACE_ENABLED:
    raise ArchitectureRefusal(
        "PROCESS_ARCH_BLOCK_TRACE_CENSUS_SETS is set without "
        "PROCESS_ARCH_BLOCK_TRACE: it is read by the block trace alone, so "
        "without it the setting would change nothing under the right name."
    )

if BLOCK_TRACE_CENSUS_PATH and TEST_SET != "write_set":
    raise ArchitectureRefusal(
        f"PROCESS_ARCH_BLOCK_TRACE_CENSUS_SETS is set with "
        f"PROCESS_ARCH_TEST_SET={TEST_SET!r}: under 'census' the trace splits "
        f"by the loop's own census sets, and a second artifact could disagree "
        f"with them.  It is for a 'write_set' loop only."
    )

#: How many component names a part lists per sweep at or above tau: a disk
#: guard, not a filter.  When it binds, the part says how many it dropped.
BLOCK_TRACE_MAX_NAMED = 40

#: What the optimiser's evaluator asked for, set immediately before each
#: ``call_models`` and consumed (reset to ``None``) by the trace line that
#: evaluation writes: ``["function"]``, ``["gradient", column, sign]`` or
#: ``["reconcile"]``.  ``None`` at a call no evaluator labelled.
EVALUATION_KIND: list | None = None

_BLOCK_TRACE_FILE = None


_BLOCK_TRACE_MODULES: dict = {}


def block_trace_modules(spec, subsets) -> tuple:
    """``(module names, component -> module index)`` from the committed write sets.

    Built once per write-set object and cached: the lookup array is what makes
    splitting a sweep's residual by module one vectorised pass instead of a
    membership test per component.  Components no module writes read -1
    (``load_subsets`` refuses a write set that leaves any, so none exist).
    """
    import numpy as np  # noqa: PLC0415 - trace path only

    cached = _BLOCK_TRACE_MODULES.get(id(subsets))
    if cached is not None:
        return cached
    names = sorted(subsets)
    lookup = np.full(len(spec.keys), -1, dtype=int)
    for k, mod in enumerate(names):
        members = sorted(subsets[mod])
        if members:
            lookup[members] = k
    _BLOCK_TRACE_MODULES[id(subsets)] = (names, lookup)
    return names, lookup


#: DR13: the parts each block's sweep is scored on, by block label, built once
#: per run (``block_trace_parts``) and written into the trace's header.
_BLOCK_TRACE_PARTS: dict = {}
_BLOCK_TRACE_PARTS_INFO: dict = {}
_BLOCK_TRACE_CENSUS: dict = {}


def block_trace_census_sets(spec, tests, *, loop_key: str):
    """DR13: the census sets the trace splits a block's write set by, or None.

    Under ``census`` they are the loop's own test sets (*tests*).  Under
    ``write_set`` they are read from :data:`BLOCK_TRACE_CENSUS_PATH` with
    :func:`load_test_sets` -- the same two checks, the same loop key -- or
    are ``None`` when no artifact was named (one part only).  Trace path
    only; nothing here is read by a loop.
    """
    if TEST_SET == "census":
        return tests
    if not BLOCK_TRACE_CENSUS_PATH:
        return None
    cached = _BLOCK_TRACE_CENSUS.get(loop_key)
    if cached is None:
        cached, _prov = load_test_sets(spec, BLOCK_TRACE_CENSUS_PATH, loop_key=loop_key)
        _BLOCK_TRACE_CENSUS[loop_key] = cached
    return cached


def block_trace_parts(spec, label, write_subset, census_sets) -> dict:
    """DR13: ``{part name: sorted component indices}`` for one block.

    The block's write set is *write_subset* (``None``: the whole coupling
    state, which is the flat block's).  With *census_sets* the parts are
    ``census`` -- the block's census set as the census loop tests it -- and
    ``non_census`` -- the write set less it; without, one part,
    ``write_set``.  Built once per block label and cached; the header of the
    trace records each part's size and the census components that lie
    outside the block's write set.
    """
    cached = _BLOCK_TRACE_PARTS.get(label)
    if cached is not None:
        return cached
    write = (
        list(range(len(spec.keys))) if write_subset is None
        else sorted(int(i) for i in write_subset)
    )
    if census_sets is None:
        parts = {"write_set": write}
        info = {"write_set": len(write), "census_split": False}
    else:
        census = sorted(int(i) for i in (census_sets.get(label) or ()))
        cset = set(census)
        parts = {
            "census": census,
            "non_census": [i for i in write if i not in cset],
        }
        wset = set(write)
        info = {
            "census": len(census),
            "non_census": len(parts["non_census"]),
            "write_set": len(write),
            "census_split": True,
            "census_outside_write_set": sorted(
                spec.name(i) for i in census if i not in wset
            ),
        }
    _BLOCK_TRACE_PARTS[label] = parts
    _BLOCK_TRACE_PARTS_INFO[label] = info
    return parts


def _block_trace_part(spec, y_prev, y, sel, tau) -> dict:
    """DR13: one part's score for one sweep, from the loop's own snapshots.

    The predicate's own untimed ``residual`` over *sel*: its maximum, the
    component it is on, how many components reach ``tau`` and, up to
    :data:`BLOCK_TRACE_MAX_NAMED`, their names; the discrete mismatches,
    moved constants and new NaNs by name.  An empty part reads 0.
    """
    if not sel:
        return {"max": 0.0, "argmax": None, "n_above": 0}
    res = spec.residual(y_prev, y, subset=sel, ruler=PREDICATE_MODE)
    above = res.above(tau)
    out: dict = {
        "max": res.max,
        "argmax": None if res.argmax is None else spec.name(res.argmax),
        "n_above": len(above),
    }
    if above:
        out["above"] = [spec.name(i) for i in above[:BLOCK_TRACE_MAX_NAMED]]
        if len(above) > BLOCK_TRACE_MAX_NAMED:
            out["above_truncated"] = len(above) - BLOCK_TRACE_MAX_NAMED
    for key, idx in (
        ("discrete_mismatch", res.mismatch_discrete),
        ("moved_constant", res.moved_constant),
        ("nan_new", res.nan_new),
    ):
        if idx:
            out[key] = [spec.name(i) for i in idx[:BLOCK_TRACE_MAX_NAMED]]
    return out


def block_trace_sweep(
    res, modules, tau, *, spec=None, y_prev=None, y=None, parts=None
) -> dict:
    """One sweep's residual, split by module: its max and whether it is open.

    A module is *open* after a sweep when its own components would fail the
    convergence test at ``tau``: a scaled step at or above ``tau``, or a
    discrete mismatch, a moved constant or a new NaN among them.  Only the
    modules the residual scored appear.

    DR13: with *parts* (and the two snapshots the loop compared), the sweep
    is also scored on each part of the block's write set
    (:func:`block_trace_parts`), and the test's own worst component is named.
    """
    import numpy as np  # noqa: PLC0415 - trace path only

    if parts is not None:
        out = _block_trace_sweep_modules(res, modules, tau, np)
        out["test_argmax"] = (
            None if res.argmax is None else spec.name(res.argmax)
        )
        out["parts"] = {
            name: _block_trace_part(spec, y_prev, y, sel, tau)
            for name, sel in parts.items()
        }
        return out
    return _block_trace_sweep_modules(res, modules, tau, np)


def _block_trace_sweep_modules(res, modules, tau, np) -> dict:
    """The per-module split of one sweep's test residual (A90)."""

    names, lookup = modules
    idx_c = np.asarray(res.idx_c, dtype=int)
    labels = lookup[idx_c] if idx_c.size else np.zeros(0, dtype=int)
    flagged_mods = {
        int(lookup[i])
        for i in (*res.mismatch_discrete, *res.moved_constant, *res.nan_new)
    }
    out_max: dict = {}
    open_: list = []
    for k, mod in enumerate(names):
        mask = labels == k
        has = bool(mask.any())
        if not has and k not in flagged_mods:
            continue
        m = float(np.max(res.scaled[mask])) if has else 0.0
        out_max[mod] = m
        if m >= tau or k in flagged_mods:
            open_.append(mod)
    return {"max": out_max, "open": open_}


def block_trace_write(record: dict) -> None:
    """Append one evaluation's line to the block trace."""
    global _BLOCK_TRACE_FILE
    if _BLOCK_TRACE_FILE is None:
        _BLOCK_TRACE_FILE = open(BLOCK_TRACE_PATH, "a")  # noqa: SIM115 - held open
        _BLOCK_TRACE_FILE.write(json.dumps({
            "kind": "header",
            "mda": MDA_MODE,
            "tau": TAU,
            "predicate_mode": PREDICATE_MODE,
            # DR13 (A115): what each block's parts are, and from where.
            "test_set": TEST_SET,
            "census_sets_for_the_split": (
                TEST_SETS_PATH if TEST_SET == "census"
                else BLOCK_TRACE_CENSUS_PATH
            ),
            "parts_by_block": dict(_BLOCK_TRACE_PARTS_INFO),
        }) + "\n")
    _BLOCK_TRACE_FILE.write(json.dumps(record) + "\n")
    _BLOCK_TRACE_FILE.flush()

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

#: ``harness/child/ystate.py`` -- the coupling-state predicate in both of its
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
    / "child"
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
    # DR5, kept under DR11 with one ruler: the ruler list is a literal here
    # (there is nothing to read a file for before the predicate is loaded), so
    # the literal is checked against the module that actually implements it
    # the first time that module is loaded.  A driver whose list disagreed
    # with the predicate's would be naming a ruler the predicate ignores.
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
        # trap (i)).  DR11 adds the third part: which set the loops test.
        "predicate_mode": PREDICATE_MODE,
        "test_set": TEST_SET,
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


_TEST_SET_CACHE: dict = {}


def load_test_sets(spec, path: str | Path | None = None, *, loop_key: str):
    """``{block: frozenset(y indices)}`` from the committed census test sets.

    DR11 (A100 (v5-test-set)).  The artifact holds one entry per **loop** --
    keyed ``<mda>/<burn-time owner>`` -- and each entry one key list per
    block.  The same two things are checked as for the write sets, and for
    the same reason (a set that silently misses components is a convergence
    test that silently passes early):

    * the artifact's ``ystate_components_sha256`` must equal the spec's own
      ``components_sha256`` -- one configuration, one generation;
    * every key named in a block's set must resolve to a component of the
      spec.

    Coverage is **not** required, and that is the point: a test set is a
    subset of the block's write set, and a block the census never saw sweep
    has no list at all and tests nothing (V5 plan §3).  The entry for
    *loop_key* must exist; a loop the artifact does not know is refused, not
    given another loop's sets.
    """
    p = Path(path or TEST_SETS_PATH)
    cache_key = (str(p), loop_key)
    cached = _TEST_SET_CACHE.get(cache_key)
    if cached is not None:
        return cached
    record = json.loads(p.read_text())

    spec_sha = spec.components_sha256()
    art_sha = record.get("ystate_components_sha256")
    if art_sha != spec_sha:
        raise ArchitectureRefusal(
            f"census test sets {p} were built against ystate components "
            f"{art_sha} but the loaded spec is {spec_sha}: the two artifacts "
            f"are not from the same configuration and generation."
        )
    entry = (record.get("sets") or {}).get(loop_key)
    if entry is None:
        raise ArchitectureRefusal(
            f"census test sets {p} carry no entry for loop {loop_key!r}; the "
            f"loops it knows are {sorted(record.get('sets') or {})}.  Another "
            f"loop's sets would silently test the wrong components, so the "
            f"run is refused."
        )

    index = {f"{ns}.{fld}": i for i, (ns, fld) in enumerate(spec.keys)}
    tests: dict[str, frozenset] = {}
    unknown: list[str] = []
    for block, keys in entry["blocks"].items():
        idx = set()
        for k in keys:
            i = index.get(k)
            if i is None:
                unknown.append(k)
            else:
                idx.add(i)
        tests[block] = frozenset(idx)
    if unknown:
        raise ArchitectureRefusal(
            f"census test sets {p} name {len(unknown)} keys the coupling-state "
            f"spec does not have, e.g. {sorted(unknown)[:5]}"
        )

    provenance = {
        "path": str(p),
        "scenario": record.get("scenario"),
        "format": record.get("format"),
        "loop_key": loop_key,
        "census_arm": entry.get("census_arm"),
        "sets_sha256": record.get("sets_sha256"),
        "ystate_components_sha256": art_sha,
        "n_by_block": {b: len(v) for b, v in sorted(tests.items())},
        "n_components": len(spec.keys),
    }
    _TEST_SET_CACHE[cache_key] = (tests, provenance)
    return tests, provenance


def load_loop_tests(spec, write_sets: dict, *, loop_key: str):
    """The subsets each block loop **tests**, under the test set the run asked for.

    DR11.  Under ``write_set`` this is *write_sets* itself -- V4's predicate,
    the block's whole write set, the fallback of decision D39 -- and nothing
    is read.  Under ``census`` it is :func:`load_test_sets` for *loop_key*,
    with every block of the schedule that the artifact does not list given
    an **empty** set, so that such a block tests nothing rather than
    everything (the predicate scores an unwritten component ``inf``, so
    "everything" would hold a loop open for ever; see ``load_subsets``).

    Either way the choice is stamped once, in :data:`LOOP_TEST_SETS`, so the
    record says what the loops bound.
    """
    if TEST_SET == "write_set":
        tests = write_sets
        provenance = {
            "test_set": TEST_SET,
            "loop_key": loop_key,
            "source": "the committed write sets (V4's predicate, decision D39)",
            "path": WRITE_SETS_PATH,
            "n_by_block": {b: len(v) for b, v in sorted(write_sets.items())},
        }
    elif TEST_SET == "census":
        loaded, loaded_prov = load_test_sets(spec, loop_key=loop_key)
        tests = dict(loaded)
        for block in write_sets:
            tests.setdefault(block, frozenset())
        provenance = {
            "test_set": TEST_SET,
            **loaded_prov,
            "n_by_block": {b: len(v) for b, v in sorted(tests.items())},
            "blocks_never_censused": sorted(
                b for b in write_sets if b not in loaded
            ),
        }
    else:  # pragma: no cover - the import-time guard refuses this
        raise ArchitectureRefusal(
            f"PROCESS_ARCH_TEST_SET={TEST_SET!r}: no test set to bind"
        )
    if not LOOP_TEST_SETS.get("loaded"):
        LOOP_TEST_SETS.clear()
        LOOP_TEST_SETS.update(provenance)
        LOOP_TEST_SETS["tau"] = TAU
        LOOP_TEST_SETS["predicate_mode"] = PREDICATE_MODE
        LOOP_TEST_SETS["loaded"] = True
    return tests, provenance
