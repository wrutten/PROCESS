"""Module to call physics and engineering models"""

from __future__ import annotations

import json
import logging
import os
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from tabulate import tabulate

from process.core import _idf_probe, constants
from process.core import process_output as po
from process.core.io.mfile import MFile
from process.core.process_output import OutputFileManager, ovarre
from process.core.solver import ArchitectureRefusal, constraints
from process.core.solver import module_solve, subsolve
from process.core.solver.iteration_variables import set_scaled_iteration_variable
from process.core.solver.objectives import objective_function
from process.data_structure.blanket_variables import BlktModelTypes
from process.data_structure.numerics import FiguresOfMerit, PROCESSRunMode
from process.models.tfcoil.base import TFConductorModel
from process.models.tfcoil.superconducting import SuperconductingTFTurnType

if TYPE_CHECKING:
    from process.core.model import DataStructure
    from process.main import Models

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------
# VP1 (framework hook F7a) -- arrangement at node granularity: *when* a model
# node runs is a driver choice.  Switch: ``PROCESS_ARCH_ARRANGEMENT_NODE``.
#
# The first three tokamak nodes are unconditional and adjacent, and they are
# the only part of the sequence VP1 currently varies, so the variant point is
# a list of node names that ``_call_models_once`` walks.  Everything after
# them is switch-selected on the input file and is left exactly as upstream
# wrote it; this is a permutation of three calls, not a scheduler.
#
# ``upstream`` is the order upstream PROCESS uses and is the default: with
# ``PROCESS_ARCH_ARRANGEMENT_NODE`` unset the loop below issues ``plasma_geom``,
# ``build``, ``physics`` in that order, which is what the three straight-line
# statements it replaced did.
#
# ``build_after_physics`` (task A3) moves ``build`` -- DSM row 5, module M2
# Coils -- from inside M1 Physics' span to the head of M2's span, so that M1
# becomes contiguous in the call order and a per-module solver can wrap it.
# The selection is resolved once at import, never per call.
_ARRANGEMENT_NODE_ORDERS: dict[str, tuple[str, ...]] = {
    "upstream": ("plasma_geom", "build", "physics"),
    "build_after_physics": ("plasma_geom", "physics", "build"),
}

ARRANGEMENT_NODE_NAME: str = (
    os.environ.get("PROCESS_ARCH_ARRANGEMENT_NODE", "").strip() or "upstream"
)

if ARRANGEMENT_NODE_NAME not in _ARRANGEMENT_NODE_ORDERS:
    raise ArchitectureRefusal(
        f"PROCESS_ARCH_ARRANGEMENT_NODE={ARRANGEMENT_NODE_NAME!r} is not a "
        f"recognised node arrangement; expected one of "
        f"{tuple(_ARRANGEMENT_NODE_ORDERS)} (or unset for {'upstream'!r})."
    )

#: Resolved node order for the head of the tokamak model sequence.
ARRANGEMENT_NODE_HEAD: tuple[str, ...] = _ARRANGEMENT_NODE_ORDERS[ARRANGEMENT_NODE_NAME]


# --------------------------------------------------------------------------
# VP6 (D19, task A40) -- arrangement at method granularity: *when* a model
# method runs is a driver choice.  Switch: ``PROCESS_ARCH_ARRANGEMENT_METHOD``.
# The mechanism's own name for it is the *prime*, and that word survives in
# these comments because it names what the code does, not what the arm is
# called.
#
# A35 named the one cut edge that carries a displaced entry into a one-pass
# exit on the study configurations: ``FirstWall`` (block M3) computes
# ``build.dr_fw_inboard`` / ``dr_fw_outboard`` -- a run-constant of two pure
# input-file values (``fw.py:347-352`` at the base commit) -- and ``Build``
# (block M2, earlier in the executed schedule) reads the *previous* pass's
# values.  Under an iterating driver the lag costs at most one sweep; under
# a one-pass schedule it transmits exactly the entry displacement of the
# pair, once, with A35's measured linear coefficients.
#
# The prime executes that one method **once per evaluation, before the first
# block** -- pre-processing of the sequenced schedule (DR10, V5 list item 8,
# task A99 (v5-schedule-and-prime); the user: "it is pre-processing before the
# partitioned MDAs can start") -- so ``Build`` reads this evaluation's value.
# V4 executed it at the head of every sweep instead (about 9-15 stamped calls
# per evaluation); the values are the same bits each time, so the exit states
# are identical (gate G2) and the stamped count becomes the evaluation count
# (gate GC).  It is a driver choice about *when* an existing model method runs
# -- the same family as the VP1 reorder but finer-grained (a method, not a
# node); nothing under ``process/models/`` changes, and ``FirstWall``'s own
# execution is untouched (the prime *duplicates* a run-constant of two
# floating-point operations, identical bits each time).
#
# ``off`` is the default and is upstream behaviour exactly: the guard in
# ``_call_models_inner`` is one module-level boolean read per evaluation and
# the counter never moves (gate G1: byte identity with the switch unset).
#
# The call is deliberately NOT routed through :meth:`Caller._node`: it is
# not a node, it must add no counted node call, and every count comparison
# must stay commensurable with earlier revisions.  It is **stamped, not
# counted** -- the runners record :data:`ARRANGEMENT_METHOD_CALLS` as
# ``n_prime_calls`` in every run's metrics, published as a footnote beside the
# node-call tables and never pooled into them (trap T11 -- no silent work).
_ARRANGEMENT_METHODS: dict[str, bool] = {"off": False, "fw_geometry": True}

ARRANGEMENT_METHOD_NAME: str = (
    os.environ.get("PROCESS_ARCH_ARRANGEMENT_METHOD", "").strip() or "off"
)

if ARRANGEMENT_METHOD_NAME not in _ARRANGEMENT_METHODS:
    raise ArchitectureRefusal(
        f"PROCESS_ARCH_ARRANGEMENT_METHOD={ARRANGEMENT_METHOD_NAME!r} is not a "
        f"recognised method arrangement; expected one of "
        f"{tuple(_ARRANGEMENT_METHODS)} (or unset for {'off'!r})."
    )

#: True when the first-wall geometry pair is primed once per evaluation,
#: before the first block.
ARRANGEMENT_METHOD_FW_GEOMETRY: bool = _ARRANGEMENT_METHODS[ARRANGEMENT_METHOD_NAME]

#: Invocation counter the runners read (the NODE_CALLS pattern: a one-cell
#: list, so a reader holds the live cell and not a stale int).  Incremented
#: only when the prime actually executes; stays 0 with the switch off.
ARRANGEMENT_METHOD_CALLS: list[int] = [0]


# --------------------------------------------------------------------------
# VP2 (framework hook F7b) -- deferral at *per-call* frequency: the
# feed-forward tail runs once per evaluation of the model set, after the fixed
# point, instead of once per sweep.  Switch: ``PROCESS_ARCH_DEFER_PER_CALL``.
# The mechanism's own name for it is the *hoist*, and that word survives in
# these comments for the same reason the prime's does.
#
# Some model nodes feed nothing back: nothing they write is read by any model
# that runs before them inside the idempotence loop.  Running them on every
# sweep is wasted work -- their inputs are final only once the loop has
# settled, and their outputs affect nothing the loop is deciding.  The deferral
# takes them out of the sweep and runs them once, after ``call_models`` has
# reached its fixed point.
#
# ``off`` is the default and is upstream behaviour exactly: every node runs on
# every sweep, and the deferral list is never even created.
#
# The **node set is derived at run time, not hard-coded** (framework item
# C2a).  Membership comes from the committed DSM node map, so it follows the
# arm: when the burn time leaves the loop, ``pulse`` joins the feed-forward
# tail and the derivation picks it up without a list edit here.  What *is*
# fixed in this file is which call sites were made deferrable at all;
# ``_DEFER_PER_CALL_UNCOVERED`` below turns a node that should be deferred but
# has no deferrable call site into an import-time refusal rather than a silent
# in-loop evaluation.
_DEFER_PER_CALL_MODULES: dict[str, frozenset[str]] = {
    "off": frozenset(),
    "feedforward": frozenset({"FF"}),
    # FF, plus the burn-time articulation point once that quantity is out of
    # the loop.
    "feedforward_lifted": frozenset({"FF", "PULSE"}),
}

#: Deferral settings that additionally require a site to be out of the loop,
#: and which site.
#:
#: Plan §4.1d: once the burn time is out of the loop, ``Pulse``'s burn-time
#: write is a no-op (``subsolve`` returns the value its owner put there) and
#: the only other field it writes on the pulsed configurations,
#: ``constraints.t_current_ramp_up_min``, is read by a constraint equation and
#: by **no model**.  So ``pulse`` then has no feedback into the analysis and
#: should run once per optimiser evaluation rather than once per sweep.  This
#: is the VP2 x VP5 composition the framework predicted and flagged as a latent
#: defect that fires only when two arms compose; it never fired because the
#: deferral keyed on the static node-map label and ``pulse`` is labelled
#: ``PULSE``.
#:
#: It is its **own value** rather than an automatic consequence of taking the
#: burn time out of the loop, for two reasons.  A comparison must be able to
#: vary one thing: ``feedforward`` and ``feedforward_lifted`` with the same
#: burn-time owner differ only in whether ``pulse`` leaves the sweep, which is
#: what makes the gate below a one-variable comparison.  And an arm that
#: silently changes meaning with an unrelated environment variable is the
#: failure mode this file refuses everywhere else.
_DEFER_PER_CALL_REQUIRES_BURN_TIME_OUT: dict[str, str] = {
    "feedforward_lifted": subsolve.SITE_BURN_TIME,
}

DEFER_PER_CALL_NAME: str = (
    os.environ.get("PROCESS_ARCH_DEFER_PER_CALL", "").strip() or "off"
)

if DEFER_PER_CALL_NAME not in _DEFER_PER_CALL_MODULES:
    raise ArchitectureRefusal(
        f"PROCESS_ARCH_DEFER_PER_CALL={DEFER_PER_CALL_NAME!r} is not a "
        f"recognised per-call deferral; expected one of "
        f"{tuple(_DEFER_PER_CALL_MODULES)} (or unset for {'off'!r})."
    )

_needs = _DEFER_PER_CALL_REQUIRES_BURN_TIME_OUT.get(DEFER_PER_CALL_NAME)
if _needs and not subsolve.is_out_of_loop(_needs):
    raise ArchitectureRefusal(
        f"PROCESS_ARCH_DEFER_PER_CALL={DEFER_PER_CALL_NAME!r} takes the "
        f"burn-time articulation point out of the sweep, which is only correct "
        f"once the burn time itself is out of the loop: with "
        f"PROCESS_ARCH_BURN_TIME_OWNER unset (or =loop) Pulse still solves the "
        f"burn time in the model and the loop would stop updating it.  Set "
        f"PROCESS_ARCH_BURN_TIME_OWNER=optimiser or =constant:<hex float>, or "
        f"use PROCESS_ARCH_DEFER_PER_CALL=feedforward."
    )

#: Node-map modules whose nodes are deferred out of the sweep.
DEFER_PER_CALL_MODULES: frozenset[str] = _DEFER_PER_CALL_MODULES[DEFER_PER_CALL_NAME]

#: True when any node is deferred.  With the deferral off this guards every
#: branch the variant point adds, so the default path is upstream's.
DEFER_PER_CALL_ENABLED: bool = bool(DEFER_PER_CALL_MODULES)

#: Call sites in :meth:`Caller._call_models_once` routed through
#: :meth:`Caller._node` and therefore capable of being deferred.  This is a
#: property of *this file*, not of the arm: it says which statements were
#: rewritten, not which nodes this arm defers.
DEFERRABLE_NODES: tuple[str, ...] = ("pulse", "water_use", "costs")

#: **The per-call deferral is a routing rule, not an exclusion rule** (plan
#: §4.1d/§4.1e).
#:
#: ``Caller.call_models`` stops when ``objf`` and ``conf`` agree between
#: sweeps, so what makes a node unsafe to defer is that the **predicate
#: layer** --- the objective *or* the constraint layer --- reads something it
#: writes.  A node like that must not run *after* ``conf`` is evaluated,
#: because the optimiser would then be handed a constraint vector built from a
#: stale value: a small, plausible, wrong ``conf``, which is the hardest kind
#: of defect to catch.  But it need not stay in the loop either.  It runs
#: **once, on the converged state, before** ``objf`` and ``conf``.
#:
#: Three slots, then:
#:
#: =====================  ===============================================
#: in the loop            the node-map module is not deferred by this arm
#: pre-predicate, once    deferred, and the predicate layer reads something
#:                        it writes
#: post-predicate, once   deferred, and it reads nothing the predicate does
#: =====================  ===============================================
#:
#: This **generalises A13's figure-of-merit guard and replaces it.**  A13 kept
#: ``costs`` inside the loop on configurations whose figure of merit reads it,
#: which is correct but more conservative than necessary: the pre-predicate
#: slot does the same job by running the node once instead of every sweep, so
#: the configuration keeps the saving without the staleness.
#:
#: Both inputs are **measured, not listed here.**  The predicate's read set is
#: taken from the driver's own source by
#: :func:`_predicate_read_fields`; each node's write set comes from the
#: committed run-time write census at :data:`NODE_WRITESET_PATH`.  Neither is a
#: hardcoded table that can drift from the code it describes.

#: The two files that make up the idempotence predicate.
_PREDICATE_SOURCES = (
    Path(__file__).resolve().parent / "solver" / "objectives.py",
    Path(__file__).resolve().parent / "solver" / "constraints.py",
)

#: Committed per-node write sets (framework component C8's sibling), measured
#: by the write census.  Read only when a deferral is on; never
#: read live from a generated artifact (trap T9).  Re-pointed from
#: ``arch_surgery/docs/data/`` to the V4 harness beside this copy by
#: A46 (process-copy) under decision D20.
#: The target is a committed file of this experiment: its source, its sha256
#: and the check that the two are byte-identical are recorded in
#: ``harness/data/PROVENANCE.json``.
NODE_WRITESET_PATH = (
    Path(__file__).resolve().parents[3]
    / "harness"
    / "data"
    / "node_writesets.json"
)


def _predicate_read_fields(i_figure_merit: int) -> frozenset[str]:
    """``{"namespace.field"}`` the predicate layer reads, for this run.

    An AST walk for ``data.<namespace>.<field>`` in a **load** context, so a
    field that only ever appears on the left of an assignment is not collected
    (trap T2: ``= `` matches ``==`` when you use a regex; the parser does not
    have that problem).  The objective side is narrowed to the active figure of
    merit's own branch of ``objective_function``'s ``if``/``elif`` chain; the
    constraint side is the **whole** layer, not only this configuration's
    ``icc``.

    The asymmetry is deliberate.  Over-reporting routes a node to the
    pre-predicate slot, which is never wrong --- only occasionally
    unnecessary.  Under-reporting hands the optimiser a stale ``conf``.
    """
    import ast  # noqa: PLC0415

    fom_name = FiguresOfMerit(abs(int(i_figure_merit))).name
    fields: set[str] = set()

    class _Reads(ast.NodeVisitor):
        def __init__(self):
            self.reads: set[str] = set()

        def visit_Attribute(self, node):  # noqa: N802
            inner = node.value
            if (
                isinstance(inner, ast.Attribute)
                and isinstance(inner.value, ast.Name)
                and inner.value.id == "data"
                and isinstance(node.ctx, ast.Load)
            ):
                self.reads.add(f"{inner.attr}.{node.attr}")
            self.generic_visit(node)

    def _fom_of(test):
        if (
            isinstance(test, ast.Compare)
            and len(test.ops) == 1
            and isinstance(test.ops[0], ast.Eq)
            and isinstance(test.comparators[0], ast.Attribute)
            and isinstance(test.comparators[0].value, ast.Name)
            and test.comparators[0].value.id == "FiguresOfMerit"
        ):
            return test.comparators[0].attr
        return None

    obj_src, con_src = _PREDICATE_SOURCES
    fn = None
    for node in ast.walk(ast.parse(obj_src.read_text(), filename=str(obj_src))):
        if isinstance(node, ast.FunctionDef) and node.name == "objective_function":
            fn = node
            break
    if fn is None:
        raise ArchitectureRefusal(
            f"{obj_src} has no objective_function; the per-call deferral's "
            f"routing rule cannot be derived and must not be guessed."
        )
    seen_chain = False

    def walk(stmts):
        nonlocal seen_chain
        for st in stmts:
            name = _fom_of(st.test) if isinstance(st, ast.If) else None
            if name is not None:
                seen_chain = True
                if name == fom_name:
                    v = _Reads()
                    for b in st.body:
                        v.visit(b)
                    fields.update(v.reads)
                walk(st.orelse)
            else:
                v = _Reads()
                v.visit(st)
                fields.update(v.reads)

    walk(fn.body)
    if not seen_chain:
        raise ArchitectureRefusal(
            f"{obj_src}'s figure-of-merit chain did not parse; the per-call "
            f"deferral's routing rule cannot be derived and must not be "
            f"guessed."
        )
    v = _Reads()
    v.visit(ast.parse(con_src.read_text(), filename=str(con_src)))
    fields.update(v.reads)
    return frozenset(fields)


def _node_write_sets() -> dict[str, frozenset[str]]:
    """Per-node write sets from the committed census."""
    if not NODE_WRITESET_PATH.exists():
        raise ArchitectureRefusal(
            f"PROCESS_ARCH_DEFER_PER_CALL={DEFER_PER_CALL_NAME!r} needs the "
            f"committed per-node write sets at {NODE_WRITESET_PATH}, which is "
            f"not present.  "
            f"It is a committed file of this experiment, copied into "
            f"harness/data/ and recorded in harness/data/PROVENANCE.json."
        )
    raw = json.loads(NODE_WRITESET_PATH.read_text())["writes_by_node_union"]
    return {k: frozenset(v) for k, v in raw.items()}


#: Committed DSM node map (framework component C8).  Read only when a deferral
#: or a block schedule is on; never read live from the dependency-analysis
#: repository (trap T9).
#: Re-pointed from ``arch_surgery/docs/data/`` to the V4 harness beside this
#: copy by A46 (process-copy) under decision D20.
#: The target is a committed file of this experiment: its source, its sha256
#: and the check that the two are byte-identical are recorded in
#: ``harness/data/PROVENANCE.json``.
NODE_MAP_PATH = (
    Path(__file__).resolve().parents[3]
    / "harness"
    / "data"
    / "dsm_node_map.json"
)


def _resolve_defer_per_call_nodes() -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Nodes this arm defers per call, and any it should defer but cannot.

    Returns
    -------
    tuple
        ``(deferred, uncovered)`` -- the deferrable nodes the node map assigns
        to a deferred module, and the mapped nodes that a deferred module
        claims but that have no deferrable call site.
    """
    if not DEFER_PER_CALL_ENABLED:
        return (), ()
    if not NODE_MAP_PATH.exists():
        raise ArchitectureRefusal(
            f"PROCESS_ARCH_DEFER_PER_CALL={DEFER_PER_CALL_NAME!r} needs the "
            f"committed DSM node map at {NODE_MAP_PATH}, which is not present."
        )
    nodes = json.loads(NODE_MAP_PATH.read_text())["nodes"]
    deferred = tuple(
        n for n in DEFERRABLE_NODES if nodes.get(n, {}).get("module") in DEFER_PER_CALL_MODULES
    )
    uncovered = tuple(
        sorted(
            n
            for n, entry in nodes.items()
            if entry.get("module") in DEFER_PER_CALL_MODULES
            and entry.get("in_call_models_once")
            and n not in DEFERRABLE_NODES
        )
    )
    return deferred, uncovered


DEFER_PER_CALL_NODES, _DEFER_PER_CALL_UNCOVERED = _resolve_defer_per_call_nodes()

if _DEFER_PER_CALL_UNCOVERED:
    raise ArchitectureRefusal(
        f"PROCESS_ARCH_DEFER_PER_CALL={DEFER_PER_CALL_NAME!r} would defer "
        f"{list(_DEFER_PER_CALL_UNCOVERED)}, "
        f"but those nodes have no deferrable call site in Caller."
        f"_call_models_once. Add them to DEFERRABLE_NODES and route their "
        f"call sites through Caller._node."
    )


def resolved_defer_per_call_tails(i_figure_merit: int) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """``(pre_predicate, post_predicate)`` for a run using *i_figure_merit*.

    Every node the arm defers is placed in one of the two slots by the routing
    rule: the predicate layer reads something it writes, or it does not.
    Nothing is dropped --- a deferred node always runs exactly once.

    Public so that a measurement harness can record the tails a run resolved
    without reconstructing the rule.
    """
    pre, post, _schedule, _tail = resolve_schedule(i_figure_merit)
    return pre, post


def resolved_defer_per_call_tail(i_figure_merit: int) -> tuple[str, ...]:
    """Every deferred node, pre-predicate group first.

    Kept because A13's harness records it.  Anything that has to place a node
    relative to the predicate evaluation must use :func:`resolved_defer_per_call_tails`.
    """
    pre, post = resolved_defer_per_call_tails(i_figure_merit)
    return pre + post


# --------------------------------------------------------------------------
# VP2c (task A33) -- deferral at *per-run* frequency: nodes whose outputs the
# optimiser never consumes leave the per-call path entirely.  Switch:
# ``PROCESS_ARCH_DEFER_PER_RUN``.
#
# VP2 (above) moves a feed-forward node out of the sweep but still runs it
# once per optimiser evaluation.  VP2c goes further for the nodes that earn
# it: a node whose outputs reach NO objective read, NO active-constraint read
# and NO solve-phase model read cannot change anything the optimiser decides,
# so running it even once per call is pure cost.  Such nodes are excluded from
# every solve-phase sweep and executed **exactly once per run**, at the
# accepted optimum, before the output phase begins.
#
# Membership is **derived, not asserted**: the committed per-configuration
# artifact
# ``harness/data/defer_per_run[_lifted]_<configuration>.json`` is produced by
# the per-run classifier from the configuration's objective/constraint read
# sets (AST), the run-time write census and a backward crawl of the collapsed
# DSM, and is validated here on load:
#
# * ``nodes_sha256`` must match a recomputation over the load-bearing fields,
#   so a hand-edited artifact is refused rather than trusted;
# * the artifact must be for THIS configuration -- ``i_figure_merit`` and the
#   active ``icc`` list are checked against the run's own numerics at first
#   use, because another configuration's exclusion list is a silently wrong
#   answer;
# * every listed node must exist in the committed node map as a
#   ``_call_models_once`` call site;
# * a node whose measured write set intersects the predicate layer's read set
#   (the configuration's objective branch plus the whole constraint layer, the
#   same rule the per-call deferral's routing uses) is refused: that node is
#   one the configuration keeps per-call, and excluding it would hand the
#   optimiser a stale objective or constraint vector -- the quiet wrong answer
#   this file refuses everywhere.
#
# ``off`` (the variable unset) is the default and is byte-identical to the
# behaviour without this section -- gated against A32's record (protocol
# section 12), not asserted.
DEFER_PER_RUN_PATH: str | None = (
    os.environ.get("PROCESS_ARCH_DEFER_PER_RUN") or None
)
DEFER_PER_RUN_ENABLED: bool = DEFER_PER_RUN_PATH is not None

if DEFER_PER_RUN_ENABLED and not Path(DEFER_PER_RUN_PATH).exists():
    raise ArchitectureRefusal(
        f"PROCESS_ARCH_DEFER_PER_RUN={DEFER_PER_RUN_PATH!r} does not exist.  "
        f"There is no default and no fallback: a run asked to exclude nodes must "
        f"refuse rather than silently run everything."
    )

#: Diagnostics for the run record.  Integer counts and names only.
DEFER_PER_RUN_TOTALS: dict = {
    "artifact": DEFER_PER_RUN_PATH,
    "nodes": None,                      # filled after validation
    "n_call_sites_suppressed": 0,       # solve-phase _node sites skipped
    "suppressed_by_node": {},
    "executed_once": None,              # set by write_output_files
    "validated": False,
}

_DEFER_PER_RUN_CACHE: dict = {}


def _defer_per_run_nodes(data) -> frozenset[str]:
    """The validated exclusion set for this run.  Cached after first use.

    Validation needs the run's own input file (figure of merit, active
    constraint list), so it happens on the first ``call_models`` rather than at
    import.
    Every check refuses loudly; none falls back.
    """
    cached = _DEFER_PER_RUN_CACHE.get("nodes")
    if cached is not None:
        return cached

    import hashlib  # noqa: PLC0415 - validation path only

    record = json.loads(Path(DEFER_PER_RUN_PATH).read_text())
    if record.get("format") != "a33-postsolve-1":
        raise ArchitectureRefusal(
            f"per-run deferral artifact {DEFER_PER_RUN_PATH} has format "
            f"{record.get('format')!r}, expected 'a33-postsolve-1'."
        )
    nodes = list(record["post_solve_nodes"])

    # (1) the artifact must rebuild its own hash: a truncated, reordered or
    # hand-edited file is refused.
    payload = json.dumps(
        {
            "scenario": record.get("scenario"),
            "i_figure_merit": record.get("deck", {}).get(
                "i_figure_merit_expected"
            ),
            "icc": record.get("deck", {}).get("icc_expected_at_runtime"),
            "post_solve_nodes": nodes,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    rebuilt = hashlib.sha256(payload).hexdigest()
    committed = record.get("nodes_sha256")
    if rebuilt != committed:
        raise ArchitectureRefusal(
            f"per-run deferral artifact {DEFER_PER_RUN_PATH} does not rebuild: "
            f"nodes_sha256 is {rebuilt} recomputed against {committed} "
            f"recorded in the file.  The exclusion list would not be the "
            f"derived one."
        )

    # (2) the artifact must be for THIS configuration.  Its own JSON keys
    # still spell that 'deck'; the file format is data this task does not
    # rewrite, so the key is read under the name it has and the vocabulary
    # changes only where this file speaks for itself.
    ifm = int(data.numerics.i_figure_merit)
    want_ifm = record["deck"]["i_figure_merit_expected"]
    if ifm != want_ifm:
        raise ArchitectureRefusal(
            f"per-run deferral artifact {DEFER_PER_RUN_PATH} was derived for "
            f"i_figure_merit={want_ifm} but this run has {ifm}: it is "
            f"another configuration's artifact."
        )
    m_all = int(data.numerics.n_equality_constraints) + int(
        data.numerics.n_inequality_constraints
    )
    icc = sorted(int(v) for v in data.numerics.icc[:m_all])
    want_icc = sorted(record["deck"]["icc_expected_at_runtime"])
    if icc != want_icc:
        raise ArchitectureRefusal(
            f"per-run deferral artifact {DEFER_PER_RUN_PATH} was derived for the "
            f"active constraint set {want_icc} but this run has {icc}: it is "
            f"another configuration's artifact, or the input file changed "
            f"under it."
        )

    # (3) every listed node must be a known _call_models_once call site.
    if not NODE_MAP_PATH.exists():
        raise ArchitectureRefusal(
            f"PROCESS_ARCH_DEFER_PER_RUN needs the committed DSM node map at "
            f"{NODE_MAP_PATH}, which is not present."
        )
    known = {
        n
        for n, e in json.loads(NODE_MAP_PATH.read_text())["nodes"].items()
        if e.get("in_call_models_once")
    }
    unknown = sorted(set(nodes) - known)
    if unknown:
        raise ArchitectureRefusal(
            f"per-run deferral artifact {DEFER_PER_RUN_PATH} names {unknown}, which "
            f"are not _call_models_once call sites in the committed node map."
        )

    # (4) a node the configuration keeps per-call is refused: its measured
    # writes must
    # not intersect what the predicate layer reads for this figure of merit.
    scenario = record.get("scenario")
    if not NODE_WRITESET_PATH.exists():
        raise ArchitectureRefusal(
            f"PROCESS_ARCH_DEFER_PER_RUN needs the committed per-node write "
            f"sets at {NODE_WRITESET_PATH}, which is not present.  Its "
            f"origin is recorded in harness/data/PROVENANCE.json."
        )
    per_scenario = json.loads(NODE_WRITESET_PATH.read_text())["per_scenario"]
    if scenario not in per_scenario:
        raise ArchitectureRefusal(
            f"per-run deferral artifact {DEFER_PER_RUN_PATH} names scenario "
            f"{scenario!r}, which has no run-time write census in "
            f"{NODE_WRITESET_PATH}."
        )
    writes_by_node = per_scenario[scenario]["writes_by_node"]
    reads = _predicate_read_fields(ifm)
    for n in nodes:
        overlap = sorted(set(writes_by_node.get(n, ())) & reads)
        if overlap:
            raise ArchitectureRefusal(
                f"per-run deferral artifact {DEFER_PER_RUN_PATH} lists {n!r}, but the "
                f"predicate layer reads {overlap[:5]} out of its measured "
                f"write set: this configuration keeps {n!r} per-call, and "
                f"excluding "
                f"it would hand the optimiser a stale objective or "
                f"constraint vector."
            )

    resolved = frozenset(nodes)
    _DEFER_PER_RUN_CACHE["nodes"] = resolved
    DEFER_PER_RUN_TOTALS["nodes"] = sorted(resolved)
    DEFER_PER_RUN_TOTALS["validated"] = True
    DEFER_PER_RUN_TOTALS["scenario"] = scenario
    DEFER_PER_RUN_TOTALS["nodes_sha256"] = committed
    return resolved


# --------------------------------------------------------------------------
# VP4 (framework hook F7c) -- the shape of the analysis loop: upstream's own,
# one flat block, or a solve per module.  Switch: ``PROCESS_ARCH_MDA``.
#
# Upstream runs the whole model sequence and tests two derived scalars for
# idempotence.  ``partitioned`` instead iterates each DSM module to its own
# fixed point, in the block order A3's VP1 makes available by giving M1 a
# contiguous span, and runs that schedule **once** -- feed-forward
# partitioning asserts there is no cross-block coupling left to close, and
# whether that assertion holds is measured by the uncharged exit audit outside
# the arm rather than by an in-loop receipt the arm pays for.  The
# arrangement, its caps and its predicate live in
# ``process/core/solver/module_solve.py``; what lives here is the schedule and
# the node filter, because those are properties of *this* call sequence.
#
# ``flat`` is the same predicate on **one block containing every in-loop
# node** --- decision D18's predicate-matched control ``A0'``.  It exists so
# that the two things the reference-to-intervention step measures as a sum,
# the stopping rule and the arrangement, can be measured apart.
#
# Unset is the default and is upstream behaviour exactly: ``_active_nodes``
# stays ``None``, every node runs on every sweep, and ``call_models`` never
# enters the block path.
MDA_MODE: str = module_solve.MDA_MODE
MDA_ENABLED: bool = module_solve.ENABLED

#: Model evaluations, counted as **individual model node calls** -- the unit
#: Phase A and A22 use (``engine.Budget.node_calls``), and the unit Phase B's
#: cost comparison is stated in.  ``numerics.n_model_calls`` counts *sweeps* of
#: ``_call_models_once``, which is not comparable between a flat loop and a
#: block schedule: a block sweep runs one module, not all of them.  A plain
#: integer increment per node call, on both arms, touching no float and
#: changing no branch a result depends on.
NODE_CALLS: list[int] = [0]

#: Sweeps of ``_call_models_once`` executed inside ONE ``call_models`` — that
#: is, per optimiser-driven evaluation — binned over the run.
#:
#: I-17: the A→B transfer over-predicts B3's saving on all three
#: configurations
#: (nof +22.6 %, lad +6.0 %, st +41.8 %), and the standing hypothesis is that
#: a Phase A evaluation is not the same object as an in-loop one — Phase A
#: enters from a δ = 0.10 perturbed point and takes ≈ 5.5 sweeps, while a
#: gradient-stencil evaluation enters from a point displaced by a tiny FD step
#: and should sit near the two-sweep floor.  V2 could not test that: nothing
#: recorded the in-loop sweep distribution.  This histogram is that
#: measurement, and it is the same unit on both arms (sweeps of the dispatch
#: body), so the flat and block schedules are directly comparable.
#:
#: Same discipline as :data:`NODE_CALLS` above: a plain integer increment,
#: touching no float and changing no branch a result depends on.  The output
#: path calls ``_call_models_once`` directly rather than through
#: ``call_models``, so its sweeps are counted by neither — which is correct,
#: since only optimiser-driven evaluations are the object here.
SWEEPS_PER_EVAL_HIST: dict[str, int] = {}

#: Sweeps of the dispatch body ``_call_models_once``, over the **whole** run:
#: every sweep of every arm, on every path that walks the model sequence — the
#: analysis loop, every block sweep, the output-time loop and the exit audit.
#: The histogram above bins the same sweeps *per evaluation* and therefore sees
#: only the optimiser-driven ones; this is the run total.
#:
#: DR4 (task A58 (driver-predicate-counters)) gave it this name.  It was
#: private and existed only to be differenced across ``call_models``:
#: the per-sweep-overhead question asks what one sweep costs besides its model
#: calls, and it cannot be asked of a counter the harness has to reach into the
#: module's private names to read.  Same cell, same increment, public name.
DISPATCH_SWEEPS: list[int] = [0]

#: :data:`NODE_CALLS` at the moment the final-output path is entered.  The
#: cost figure Phase B compares is the **solve** phase: everything before
#: ``write_output_files``.  The output phase re-enters every model's ``run()``
#: from its ``output()`` (trap T7) and is identical work in both arms, so
#: pooling it into the cost would dilute the very quantity being compared.
NODE_CALLS_AT_OUTPUT: list[int | None] = [None]

#: :data:`DISPATCH_SWEEPS` at the same moment, frozen by the same statement.
#: The sweep total's solve-phase half, and the total the per-attempt sweep
#: counts of :data:`ATTEMPT_STAMPS` must add up to -- exactly as the
#: per-attempt node calls add up to :data:`NODE_CALLS_AT_OUTPUT`.  Without it
#: a per-attempt sweep count would have no whole to decompose: the run total
#: includes the output-time loop and the exit audit, neither of which belongs
#: to any attempt.
DISPATCH_SWEEPS_AT_OUTPUT: list[int | None] = [None]

#: Roll-up of the block schedule's own counts across every ``call_models`` of a
#: run.  Diagnostics: reported beside the cost figure, never gated on.
MDA_TOTALS: dict = {
    "n_call_models": 0,
    "block_sweeps": 0,
    "outer_pass_hist": {},
    "inner_sweeps_by_block": {},
    "inner_solves_by_block": {},
    "moved_constants": set(),
    "n_call_models_with_moved_constant": 0,
    "n_failed": 0,
    # A26 §10: how often the single-block guard fired.  Recorded rather than
    # inferred from the arm name, so a schedule change that stops satisfying
    # the condition is visible in the run record.
    "n_call_models_single_block": 0,
}


# --------------------------------------------------------------------------
# DR2 (task A57 (driver-output-path)) -- the output path: whether the accepted
# state is re-solved before it is written out.  Switch:
# ``PROCESS_ARCH_OUTPUT_LOOP``.
#
# Upstream writes its output files through a *second* flat idempotence loop:
# ``call_models_and_write_output`` evaluates the whole model set, writes an
# MFILE to a scratch file, and repeats -- up to ten times -- until two
# successive MFILEs agree float by float at ``rtol = 1e-6``, then writes the
# real files.  That loop is a property of the incumbent's stopping rule, not of
# the models: an arm whose solve phase already converged the coupling state to
# its own tolerance has nothing left for it to find, and re-solving the state
# before writing it means the numbers in the output files are not the numbers
# the optimiser accepted.
#
# ``upstream`` is the default and is upstream behaviour exactly: with the
# variable unset the output path is the loop above, unchanged line for line.
# ``none`` calls :func:`finalise` **once** on the accepted state and runs no
# output-time sweep at all, so the output files are written from the state the
# solve handed over.
#
# The counters below are the same discipline as :data:`NODE_CALLS`: plain
# integer increments, touching no float and changing no branch a result depends
# on.  ``OUTPUT_LOOP_SWEEPS`` is what the experiment publishes as the
# output-time loop's own cost, and it is 0 under ``none`` by construction
# rather than by assertion.
_OUTPUT_LOOPS: dict[str, bool] = {"upstream": True, "none": False}

OUTPUT_LOOP_NAME: str = (
    os.environ.get("PROCESS_ARCH_OUTPUT_LOOP", "").strip() or "upstream"
)

if OUTPUT_LOOP_NAME not in _OUTPUT_LOOPS:
    raise ArchitectureRefusal(
        f"PROCESS_ARCH_OUTPUT_LOOP={OUTPUT_LOOP_NAME!r} is not a recognised "
        f"output path; expected one of {tuple(_OUTPUT_LOOPS)} (or unset for "
        f"{'upstream'!r})."
    )

#: True when the output path re-solves the accepted state through upstream's
#: own output-time idempotence loop.
OUTPUT_LOOP_UPSTREAM: bool = _OUTPUT_LOOPS[OUTPUT_LOOP_NAME]

#: Which output path this run took, in the words the experiment's records use.
OUTPUT_PATH_NAME: str = "mda_output" if OUTPUT_LOOP_UPSTREAM else "finalise_once"

#: Sweeps of ``_call_models_once`` the output-time loop actually ran, summed
#: over every entry to :func:`write_output_files`.  Exactly 0 under ``none``.
OUTPUT_LOOP_SWEEPS: list[int] = [0]

#: Entries to :func:`write_output_files`.  One per scan point; the
#: configurations this experiment runs are single problems and enter once, and
#: a record carrying more than one says so rather than silently describing its
#: first point.
OUTPUT_PATH_ENTRIES: list[int] = [0]


# --------------------------------------------------------------------------
# DR4 (task A58 (driver-predicate-counters)) -- what the convergence test
# costs, counted rather than timed.
#
# The intervention runs many more sweeps of the dispatch body than the control
# while executing far fewer model nodes, and the earlier revision found it no
# faster.  That can only be true if a sweep costs something that is not
# proportional to the nodes it runs, and the convergence test is the prime
# suspect: a flat block loop compares the **whole** coupling state -- 827 to
# 846 components, depending on the configuration -- on every one of its sweeps,
# while a block loop compares only its own block's write set.
#
# The question is settled on counts, not on a clock, because no conclusion in
# this experiment may rest on a timing: identical work has been measured
# varying by up to 35 % in CPU-seconds on this machine (issue I-10).  So the
# driver counts two things: how many times a convergence test was evaluated,
# and how many components each of those tests walked.  Their ratio is the
# average width of the test, which is the number the per-sweep-overhead
# hypothesis is about.
#
# Two predicates exist and they are counted separately rather than pooled,
# because they are not the same test and an arm runs exactly one of them:
#
#   * the **coupling-state** predicate, which the flat and partitioned
#     arrangements stop on (``PREDICATE_EVALUATIONS`` / ``COMPONENTS_COMPARED``);
#   * upstream's own **idempotence** test on the objective and the constraint
#     vector, which the reference arms stop on
#     (``UPSTREAM_PREDICATE_EVALUATIONS`` / ``UPSTREAM_COMPONENTS_COMPARED``).
#     Counting it is what keeps the reference arm's row in the published table
#     a measurement rather than a zero: the reference arm does evaluate a
#     stopping test, over about 27 components rather than 840, and that
#     contrast is the whole point of the question.
#
# All of them are counted **in the solve phase only**.  The output-time loop
# calls ``check_agreement`` too -- once per MFILE variable, in
# ``call_models_and_write_output`` -- and that is a different loop with a
# different predicate; it is counted by neither, exactly as the sweep
# histogram excludes it.
#
# Same discipline as :data:`NODE_CALLS` and :data:`OUTPUT_LOOP_SWEEPS`: plain
# integer increments, touching no float and changing no branch a result depends
# on.  With every switch unset every counter here stays at zero except the
# upstream pair, which counts the loop upstream was already running -- and gate
# G1 is what proves that, rather than this comment.

#: Evaluations of the **coupling-state** convergence test during the solve
#: phase: one per block-loop sweep that reaches its test.  In the flat
#: arrangement there is one block holding every in-loop node, so this counts
#: that loop's stopping tests; in the partitioned arrangement it counts every
#: block loop's.  Zero in the reference arms, which never enter the block path.
PREDICATE_EVALUATIONS: list[int] = [0]

#: Summed over those evaluations, the number of coupling-state components each
#: one walked: the block's own write set where the block has one, and the whole
#: coupling state where it does not (which is the flat arrangement's single
#: block).  ``COMPONENTS_COMPARED / PREDICATE_EVALUATIONS`` is the average
#: width of the test.
COMPONENTS_COMPARED: list[int] = [0]

#: The same two counts, per block label, so that a partitioned run's test width
#: can be read per block instead of only as a run average.  Keys appear the
#: first time a block's loop runs.
PREDICATE_EVALUATIONS_BY_BLOCK: dict[str, int] = {}
COMPONENTS_COMPARED_BY_BLOCK: dict[str, int] = {}

#: How many times the block schedule visited each block, over the whole run.
#: One entry per label of the schedule that was actually built, counted whether
#: or not the visit executed anything.
BLOCK_VISITS: dict[str, int] = {}

#: Of those visits, how many executed **no model node at all** -- measured on
#: :data:`NODE_CALLS`, not on the block's membership, because the two differ
#: and the difference is the point.
#:
#: This is issue I-20(a) in live form.  On ``st_regression`` the ``PULSE``
#: block still *has* its member in the schedule: the per-run deferral moves
#: ``pulse`` out of the loop at the call site, not out of the block, so the
#: block is visited, a sweep of the dispatch body is charged for it, and
#: nothing runs.  Membership would have called that visit non-empty.  A block
#: whose membership the per-call deferral has emptied -- the feed-forward tail
#: under the intervention arms -- is empty too, and costs nothing at all, which
#: is why the two cases are separated by :data:`EMPTY_BLOCK_SWEEPS` below
#: rather than summed into one number.
#:
#: The user ruled (decision D21) that this is **not repaired**: it is one of
#: PROCESS's oddities this experiment does not undertake to fix, and dropping
#: the block would change the node weights the comparison rests on.  It is
#: **counted and disclaimed** instead, so that every table which weights sweeps
#: can state how many of them were empty.
EMPTY_BLOCK_VISITS: dict[str, int] = {}

#: Sweeps of the dispatch body spent inside those empty visits.  A block the
#: schedule visits with no members costs **no** sweep; a block whose members
#: are all skipped at the call site costs a full walk of the dispatch body --
#: the design-vector injection at its head and the switch dispatch through
#: every call site -- executing no model.
#: That is the cost the empty visit actually has, and it is the number a
#: per-sweep-overhead table needs; the visit count alone would overstate it.
EMPTY_BLOCK_SWEEPS: dict[str, int] = {}

#: Evaluations of **upstream's** stopping test during the solve phase: the
#: ``check_agreement`` pair in ``_call_models_inner`` that compares the
#: objective and the constraint vector against the previous sweep's.  One per
#: test, not one per ``check_agreement`` call.
UPSTREAM_PREDICATE_EVALUATIONS: list[int] = [0]

#: Summed over those tests, the number of values each one actually compared:
#: the objective, plus the constraint vector **when the objective agreed**.
#: The pair short-circuits -- a moved objective means the constraint vector is
#: never looked at -- so counting the declared width would overstate it, and a
#: count published wider than the comparison it describes is this project's own
#: trap T11.
UPSTREAM_COMPONENTS_COMPARED: list[int] = [0]


# --------------------------------------------------------------------------
# DR7 (task A60 (driver-attempts)) -- what each optimiser attempt cost.
#
# The optimiser is not tried once.  ``SolverHandler.run`` runs a **retry
# ladder**: it calls the optimiser, and on an exit code other than "converged"
# it calls it again with a larger finite-difference step, then again with a
# smaller one, and finally -- on exit code 5 with fewer than two iterations --
# once more from a reset second-derivative matrix.  Every one of those attempts
# evaluates the model set, and every one of those evaluations is in the run's
# node-call total.
#
# Until this change the record could say **how many** attempts there were, what
# each one's exit code was and how many optimiser iterations each took -- the
# solver-owned half, which a measurement harness can get by wrapping ``solve``
# -- but the **cost** half was a single run total.  So a run that failed its
# first attempt and converged on the retry charged both attempts' evaluations
# to one number while reporting the iterations of the last attempt only.  That
# mismatch is not hypothetical: it is most of one configuration's published
# cost ratio in the previous revision (0.450 with the one retried seed, 0.659
# without it), and the experiment plan now requires the ratio to be published
# with and without retried seeds -- which cannot be done from a run total.
#
# What is added here is the cost half, at the only place it can be taken: the
# **attempt boundary**, inside the ladder.  At the entry to and the exit from
# every attempt the run's cost counters are read and appended to
# :data:`ATTEMPT_STAMPS`.  The measurement harness differences consecutive
# stamps to get each attempt's own cost and refuses a record whose parts do not
# add up to the whole they decompose.
#
# Same discipline as every counter above, and it is the discipline that makes
# the change switch-neutral: four integer reads and two dict copies per
# boundary, at most eight boundaries in a run; no float is touched, no
# arithmetic a result depends on is done, and nothing here is reachable from a
# branch any model or solver takes.  Gate G1 is what proves that rather than
# this comment.
#
# The ladder itself is untouched: which attempts run, in which order, with
# which settings, is exactly what it was.  The stage names live beside the
# ladder in ``process/core/solver/solver_handler.py``; this module only records
# what it is told, so that a ladder that gains a rung cannot silently keep the
# old vocabulary here.

#: Ladders entered: one per call of ``SolverHandler.run``.  A single problem
#: enters one; a parameter scan enters one per scan point, and a record whose
#: stamps span more than one says so rather than describing its first point as
#: if it were the run.
ATTEMPT_LADDERS: list[int] = [0]

#: The boundary stamps themselves, in the order they were taken: two per
#: attempt -- ``entry`` and ``exit`` -- each carrying the cost counters as they
#: stood at that instant.  Read back by the measurement harness; never read by
#: the driver, and never acted on.
ATTEMPT_STAMPS: list[dict] = []


def open_ladder() -> int:
    """Begin a retry ladder, and return its number.  One integer increment."""
    ATTEMPT_LADDERS[0] += 1
    return ATTEMPT_LADDERS[0]


def _stamp_attempt(boundary: str, ladder: int, index: int, stage: str) -> None:
    """Read the cost counters at one attempt boundary and record them."""
    ATTEMPT_STAMPS.append({
        "boundary": boundary,
        "ladder": ladder,
        "attempt": index,
        "stage": stage,
        "node_calls": NODE_CALLS[0],
        "dispatch_sweeps": DISPATCH_SWEEPS[0],
        "sweeps_per_eval_hist": dict(SWEEPS_PER_EVAL_HIST),
        "sweeps_by_block": dict(MDA_TOTALS["inner_sweeps_by_block"]),
    })


@contextmanager
def attempt(stage: str):
    """One attempt of the retry ladder, stamped at both of its boundaries.

    The exit stamp is taken in a ``finally``, so an attempt that **raises** is
    still bounded: a decomposition missing its last attempt would be a partial
    one, and a partial decomposition cannot be summed.
    """
    ladder = ATTEMPT_LADDERS[0]
    index = 1 + sum(
        1
        for stamp in ATTEMPT_STAMPS
        if stamp["ladder"] == ladder and stamp["boundary"] == "exit"
    )
    _stamp_attempt("entry", ladder, index, stage)
    try:
        yield
    finally:
        _stamp_attempt("exit", ladder, index, stage)


# --------------------------------------------------------------------------
# The exit-audit snapshot hook (task A57 (driver-output-path); the experiment
# plan's section 3.3 implementation note).
#
# The experiment audits the accuracy each arm achieved by taking **one further
# full sweep of the model set past termination** and measuring how far the
# coupling state moved.  The plan declares that this must be measured at one
# position in every arm: the **entry to** :func:`write_output_files`, before
# any output-time sweep -- the state the solve handed over.
#
# The audit sweep mutates the state it measures, so it cannot simply be *run*
# there: the output path would then write out an audited state the optimiser
# never accepted.  What is done instead is to **snapshot** the coupling state
# at that entry and compute the residual after the run has written its outputs,
# from the restored snapshot.  The driver's part is the position; the shape of
# a snapshot belongs to the harness's own coupling-state layer, so the driver
# holds a **hook** rather than a serialiser, and the measurement subprocess
# installs the callable.  Nothing here reads an environment variable, nothing
# here calls a model, and with the hook uninstalled -- which is every run of
# PROCESS that is not being measured -- the whole mechanism is two ``is None``
# tests per run.
#
# The hook is called with ``(models, data, where)`` and its return value is
# kept in :data:`EXIT_SNAPSHOTS` under ``where``.  Two positions are offered:
#
# ``entry_to_write_output_files``
#     the declared audit position: the state the solve handed over, before the
#     per-run deferred nodes and before any output-time sweep.
# ``before_finalise``
#     the state actually written to the output files, taken immediately before
#     the single :func:`finalise` call that writes them.  Under ``none`` the
#     two differ only by the per-run deferred nodes' own writes, which is what
#     gate G9 checks; under ``upstream`` the difference is what the
#     output-time loop moved.
#
# A hook that raises is recorded and does not stop the run: an instrument that
# can change a measurement's outcome is not an instrument.  The harness refuses
# to report an audit whose snapshot carries an error.
EXIT_SNAPSHOT_POSITIONS: tuple[str, ...] = (
    "entry_to_write_output_files",
    "before_finalise",
)

#: The installed callable, or None.  A one-cell list so a reader holds the
#: live cell and not a stale binding (the :data:`NODE_CALLS` pattern).
EXIT_SNAPSHOT_HOOK: list = [None]

#: ``where -> whatever the hook returned``, filled at most once per position.
EXIT_SNAPSHOTS: dict = {}

#: ``where -> the exception the hook raised``, for the same positions.
EXIT_SNAPSHOT_ERRORS: dict = {}


def _take_exit_snapshot(models, data, where: str) -> None:
    """Call the installed snapshot hook at *where*, at most once per position.

    Recorded rather than raised, deliberately: this is instrumentation on the
    output path of a run whose numbers are the point of the run.
    """
    hook = EXIT_SNAPSHOT_HOOK[0]
    if hook is None or where in EXIT_SNAPSHOTS or where in EXIT_SNAPSHOT_ERRORS:
        return
    try:
        EXIT_SNAPSHOTS[where] = hook(models, data, where)
    except Exception as exc:  # noqa: BLE001 - recorded, never raised
        EXIT_SNAPSHOT_ERRORS[where] = f"{type(exc).__name__}: {exc}"


def _resolve_node_modules() -> dict[str, str]:
    """``node -> DSM module`` from the committed node map.

    Read only when a block schedule is on, from the same committed artifact
    the deferrals use, and never live from the dependency-analysis repository
    (trap T9).
    """
    if not MDA_ENABLED:
        return {}
    if not NODE_MAP_PATH.exists():
        raise ArchitectureRefusal(
            f"PROCESS_ARCH_MDA={MDA_MODE!r} needs the "
            f"committed DSM node map at {NODE_MAP_PATH}, which is not present."
        )
    nodes = json.loads(NODE_MAP_PATH.read_text())["nodes"]
    # ``in_call_models_once`` is load-bearing, not decoration.  The map names
    # ``objective_constraints`` as an FF-module node, but it is the
    # objective/constraint evaluation, not a call site inside
    # ``_call_models_once``.  Including it gave the FF block a non-empty node
    # set that executed nothing -- 789 block sweeps of pure no-ops on
    # large_tokamak_nof, charged against the schedule and invisible in the node
    # count.  Found by reading the block census, not by inspection.
    return {
        n: e["module"]
        for n, e in nodes.items()
        if e.get("module") and e.get("in_call_models_once")
    }


NODE_MODULE: dict[str, str] = _resolve_node_modules()


def module_schedule(i_figure_merit: int) -> tuple[tuple, ...]:
    """``((label, frozenset(nodes), iterate), ...)`` for one schedule pass.

    Membership comes from the committed node map, so a node this configuration
    never executes simply never appears -- the filter in :meth:`Caller._node`
    is a predicate on names, not a list of calls to make.

    **The per-call deferral composes here, and that composition is the thing to
    get right.**  With it on, every deferred node is removed from its block and
    returned as the tail, to be run once after the schedule --- both slots,
    because a block schedule stops on the coupling state and not on
    ``objf``/``conf``, so nothing here is at risk of reading a stale predicate
    input.  The **placement** of the two groups relative to the predicate
    evaluation is ``call_models``'s business, not the schedule's;
    :func:`resolved_defer_per_call_tails` is the one place that decides which
    group a node is in.

    Returns
    -------
    tuple
        ``(schedule, tail)`` -- the blocks of the schedule pass, and the nodes
        deferred to after it (empty when the per-call deferral is off).
    """
    _pre, _post, schedule, tail = resolve_schedule(i_figure_merit)
    return schedule, tail


def _loop_node_set(tail=()) -> frozenset[str]:
    """Every node a block schedule may run, less the deferred tail.

    Restricted to the labels :data:`module_solve.BLOCK_ORDER` names, so the
    single-block arrangement covers **exactly** what the partitioned one's
    blocks cover between them --- which is what makes ``A0' -> A1'`` a
    comparison of the schedule and not of the model set.  The node map also carries
    ``<x_inject>`` (module ``X``): that is the design-vector injection at the
    head of ``_call_models_once``, not a model, it is not routed through
    :meth:`Caller._node`, and it runs unconditionally on every sweep of every
    arm.  Including it would put a name in the filter that no call site ever
    presents.
    """
    labels = set(module_solve.BLOCK_ORDER)
    return frozenset(
        n for n, mod in NODE_MODULE.items() if mod in labels
    ) - frozenset(tail)


def _single_block_covers_loop(schedule, tail) -> bool:
    """Does one iterated block hold every node the schedule would sweep?

    When it does, a further joint test over the whole coupling state would be
    **redundant with the block's own test**, which has just compared two
    successive sweeps of that block over the whole vector.  Since the schedule
    now runs exactly once in every arrangement (decisions D22 and D23), this is
    no longer a guard that skips anything: it is a **recorded property of the
    schedule that was actually built**, so a reader of a run record can tell a
    single-block run from a partitioned one without trusting the arm's name.

    Measured earlier, when a further pass was still paid, as the wasted-pass
    effect A0f -> A0: 1.53-1.79 % of model evaluations (A18/A26).
    """
    live = [(lab, nodes, it) for lab, nodes, it in schedule if nodes]
    if len(live) != 1:
        return False
    _lab, nodes, iterate = live[0]
    return bool(iterate) and nodes == _loop_node_set(tail)


# --------------------------------------------------------------------------
# DR9 (V5 list item 7, decision D31; task A99 (v5-schedule-and-prime)) -- the
# block schedule and the deferral sets are resolved ONCE PER RUN.
#
# Until this change every ``call_models`` re-derived which nodes it defers:
# ``_predicate_read_fields`` walked the objective and constraint sources with
# ``ast`` and ``_node_write_sets`` re-read the committed write census, on
# every evaluation of every deferring arm -- 8-11 ms before any model ran, 0
# in the arms that defer nothing (issue I-30, measured by A91).  Not the
# architecture: the models, their order and every count are identical with or
# without it, and a driver written for the partitioned order would resolve
# its schedule once at start-up.  The user ruled it fixed in V5 (D31).
#
# The resolution depends on exactly one run-time input, the figure of merit
# (``_predicate_read_fields`` narrows the objective side to its branch), and
# on things fixed for the process: the two predicate sources, the write
# census, the node map, and the switches resolved at import.  So it is keyed
# on the figure of merit alone and memoised in :data:`_SCHEDULE_CACHE`; a scan
# that changed the figure of merit between calls would resolve a second entry
# rather than reuse a wrong one.  :data:`SCHEDULE_RESOLUTION` is the stamp the
# harness records once per run: what was resolved, from what (the digests of
# the files read), and how many times the resolver ran -- 1 in every run of
# this experiment, which gate GC checks beside every other count.
#
# With every switch unset nothing here executes: ``module_schedule`` is only
# reached under a block schedule and the deferral tails only under a per-call
# deferral, so the default path never touches the cache (gate G1).

#: The once-per-run resolution, by figure of merit.
_SCHEDULE_CACHE: dict[int, tuple] = {}

#: The stamp: integer counts, names and digests only.  ``resolutions`` holds
#: one entry per figure of merit the run resolved -- one, in this experiment.
SCHEDULE_RESOLUTION: dict = {
    "n_resolutions": 0,
    "resolutions": [],
}


def _sha256_of(path: Path) -> str:
    import hashlib  # noqa: PLC0415 - the resolution path only, once per run

    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_schedule(
    i_figure_merit: int,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[tuple, ...], frozenset[str]]:
    """``(pre_predicate, post_predicate, schedule, tail)`` for *i_figure_merit*, once.

    The one place the routing rule (which slot a deferred node runs in) and
    the block membership are computed.  Memoised on the figure of merit: the
    first call for a value does the work and stamps the resolution, every
    later call returns the same objects.  ``schedule`` is empty when no block
    schedule is on; the tails are empty when nothing is deferred.
    """
    key = int(i_figure_merit)
    hit = _SCHEDULE_CACHE.get(key)
    if hit is not None:
        return hit
    pre: list[str] = []
    post: list[str] = []
    inputs: dict = {}
    if DEFER_PER_CALL_NODES:
        reads = _predicate_read_fields(key)
        writes = _node_write_sets()
        for n in DEFER_PER_CALL_NODES:
            (pre if (writes.get(n, frozenset()) & reads) else post).append(n)
        inputs["predicate_sources"] = {
            p.name: _sha256_of(p) for p in _PREDICATE_SOURCES
        }
        inputs["node_write_sets"] = {
            NODE_WRITESET_PATH.name: _sha256_of(NODE_WRITESET_PATH)
        }
        inputs["n_predicate_read_fields"] = len(reads)
    tail = frozenset(pre) | frozenset(post)
    schedule: tuple[tuple, ...] = ()
    if MDA_ENABLED:
        # ``flat`` (decision D18's control arm A0') is one block over every
        # in-loop node: the same predicate, the same caps, the same failure
        # policy, a different schedule.  It is written as a branch here rather
        # than as a second solver because A26 §10 measured that it is the
        # degenerate case of the block schedule, and two implementations of
        # one loop is how they drift.
        if module_solve.FLAT:
            schedule = (
                (module_solve.FLAT_BLOCK_LABEL, _loop_node_set(tail), True),
            )
        else:
            by_module: dict[str, set[str]] = {}
            for node, mod in NODE_MODULE.items():
                by_module.setdefault(mod, set()).add(node)
            schedule = tuple(
                (
                    label,
                    frozenset(by_module.get(label, set()) - tail),
                    label in module_solve.ITERATED,
                )
                for label in module_solve.BLOCK_ORDER
            )
        inputs["node_map"] = {NODE_MAP_PATH.name: _sha256_of(NODE_MAP_PATH)}
    resolved = (tuple(pre), tuple(post), schedule, tail)
    _SCHEDULE_CACHE[key] = resolved
    SCHEDULE_RESOLUTION["n_resolutions"] += 1
    SCHEDULE_RESOLUTION["resolutions"].append(
        {
            "i_figure_merit": key,
            "figure_of_merit": FiguresOfMerit(abs(key)).name,
            "defer_per_call": DEFER_PER_CALL_NAME,
            "mda": MDA_MODE,
            "pre_predicate": list(pre),
            "post_predicate": list(post),
            "schedule": [
                [label, sorted(nodes), bool(iterate)]
                for label, nodes, iterate in schedule
            ],
            "single_block_covers_loop": (
                _single_block_covers_loop(schedule, tail) if schedule else None
            ),
            "inputs": inputs,
        }
    )
    return resolved


def _roll_up(stats: dict) -> None:
    """Fold one ``call_models``'s block counts into the run's totals."""
    t = MDA_TOTALS
    t["n_call_models"] += 1
    t["block_sweeps"] += stats["block_sweeps"]
    key = str(stats["outer_passes"])
    t["outer_pass_hist"][key] = t["outer_pass_hist"].get(key, 0) + 1
    for label, total in stats["inner_totals"].items():
        t["inner_sweeps_by_block"][label] = (
            t["inner_sweeps_by_block"].get(label, 0) + total
        )
    for label, counts in stats["inner_counts"].items():
        t["inner_solves_by_block"][label] = t["inner_solves_by_block"].get(
            label, 0
        ) + len([c for c in counts if c])
    if stats["moved_constants"]:
        t["n_call_models_with_moved_constant"] += 1
    t["moved_constants"].update(stats["moved_constants"])
    if stats.get("single_block_covers_loop"):
        t["n_call_models_single_block"] += 1
    if not stats["converged"]:
        t["n_failed"] += 1


class Caller:
    """Calls physics and engineering models."""

    def __init__(self, models: Models, data: DataStructure):
        """Initialise all physics and engineering models.

        To ensure that, at the start of a run, all physics/engineering
        variables are fully initialised with consistent values, the models are
        called with the initial optimisation parameters, x.

        Parameters
        ----------
        models :
            physics and engineering model objects
        data :
            data structure object to be passed on to the constraint evaluators
        """
        self.models = models
        self.data = data
        # VP2: the deferral list for the current sweep, or ``None`` when
        # nothing is deferred.  ``None`` is the default and the only value the
        # deferral-off path ever sees.
        self._pending: list | None = None
        # VP2: the tail resolved for the current ``call_models``.  Resolved
        # once per run (DR9, :func:`resolve_schedule`) and looked up per call;
        # keyed on the configuration's figure of merit, so a scan that changed
        # it between calls would resolve a second entry, never reuse a wrong one.
        self._deferred_tail: frozenset[str] = frozenset()
        # VP2 / plan §4.1d: the deferred nodes split into a group that runs
        # before ``objf``/``conf`` and one that runs after.  Both empty on the
        # default path.
        self._defer_per_call_pre: frozenset[str] = frozenset()
        self._defer_per_call_post: frozenset[str] = frozenset()
        # VP2c (A33): the per-run exclusion set for the current
        # ``call_models``, or ``None`` when nothing is excluded.  ``None`` is
        # the default and the only value the switch-off path ever sees; it is
        # also what the output-phase and audit Callers keep, because they
        # never enter ``call_models`` -- which is what lets the once-per-run
        # execution and the exit audit run the very nodes the solve phase
        # excluded.
        self._defer_per_run: frozenset[str] | None = None
        # VP4: the nodes the current block sweep may run, or ``None`` when the
        # whole sequence runs.  ``None`` is the default and the only value the
        # flat-loop path ever sees.
        self._active_nodes: frozenset[str] | None = None
        # VP4: the coupling-state spec, the per-module subsets its inner
        # solves test, and their provenance.  Loaded once.
        self._yspec = None
        self._yprov = None
        self._ysubsets: dict | None = None
        #: VP4 diagnostics for the last ``call_models`` -- block sweeps,
        #: schedule passes and per-block sweep counts.  Reported, never gated
        #: on.
        self.module_solve_stats: dict | None = None
        # A34: the burn-time coupling held at the constant its owner named,
        # written once here -- "fixed at initialisation" -- and never
        # overwritten during the solve phase (the tripwire at the end of
        # ``_call_models_once`` raises on any bit-level change).  With
        # PROCESS_ARCH_BURN_TIME_OWNER unset this branch is dead and nothing
        # differs from upstream.
        if subsolve.CONSTANT_OWNS_BURN_TIME:
            self._apply_burn_time_constant()

    def _apply_burn_time_constant(self) -> None:
        """Write the constant-owned burn time in, refusing an input file that
        would fight over it.

        The constant replaces the optimiser as the variable's owner: it is how
        the evaluation phase runs the out-of-loop arrangement with no optimiser
        present.  An input file that names ``ixc = 178`` hands the same
        variable to the design-vector injection at the head of every sweep,
        which would silently overwrite the constant; two owners is a refusal,
        not a race.
        """
        nums = self.data.numerics
        n = int(nums.n_iteration_variables)
        ixc = [int(v) for v in nums.ixc[:n]]
        if subsolve.BURN_TIME_IXC in ixc:
            raise ArchitectureRefusal(
                f"PROCESS_ARCH_BURN_TIME_OWNER names the constant "
                f"{subsolve.BURN_TIME_CONSTANT!r} as the burn time's owner, "
                f"but this input file names ixc = {subsolve.BURN_TIME_IXC} "
                f"(the burn time as a design variable), so the design-vector "
                f"injection at the head of every sweep would overwrite it.  "
                f"Two owners is a refusal, not a race: run this arm on an "
                f"input file without ixc = {subsolve.BURN_TIME_IXC}, or set "
                f"PROCESS_ARCH_BURN_TIME_OWNER=optimiser."
            )
        self.data.times.t_plant_pulse_burn = subsolve.BURN_TIME_CONSTANT

    # -- VP2 -------------------------------------------------------------

    def _resolve_defer_per_call_tails(self) -> tuple[frozenset[str], frozenset[str]]:
        """``(pre_predicate, post_predicate)`` for this run.

        ``call_models`` stops on ``objf`` and ``conf``, so a node whose output
        the predicate layer reads cannot run *after* they are evaluated --- the
        optimiser would get a constraint vector built from a stale value.  It
        runs **once, before** them, on the converged state.  Everything else
        runs once after, as A13 built it.  Either way the node leaves the
        sweep, which is where the saving is.
        """
        if not DEFER_PER_CALL_ENABLED:
            return frozenset(), frozenset()
        pre, post = resolved_defer_per_call_tails(self.data.numerics.i_figure_merit)
        return frozenset(pre), frozenset(post)

    def _acpow(self) -> None:
        """``power.acpow`` as a node callable.

        A method rather than a lambda so that the node table holds the same
        kind of object for every entry, and so nothing on the default path
        builds a closure per sweep.
        """
        self.models.power.acpow(output=False)

    def _node(self, name: str, run) -> None:
        """Run one model node now, defer it, or skip it for this block.

        Four variant points meet in these lines, and the order matters:

        1. **VP4** -- when a block sweep is in progress, a node outside the
           block does not run at all.  This is checked first, so the deferral
           never collects a node during someone else's block.
        2. **VP2c** -- a node in the validated post-solve set does not run in
           any solve-phase sweep at all; it runs once per run, at the accepted
           optimum (``write_output_files``).  Checked before VP2's collection
           so an excluded node is never gathered into the per-call tail
           either.  ``_defer_per_run`` is set only inside ``call_models``, so the
           output path and the exit audit -- which call
           ``_call_models_once`` on their own Callers -- still run everything.
        3. **VP2** -- a node in the resolved feed-forward tail is collected
           instead of run.  The block path never sets ``_pending``, because
           under a block schedule the tail is a block of its own that runs once
           at the end of the schedule; this branch is the flat loop's.
        4. Otherwise the node runs, and is counted.
        """
        if self._active_nodes is not None and name not in self._active_nodes:
            return
        if self._defer_per_run is not None and name in self._defer_per_run:
            DEFER_PER_RUN_TOTALS["n_call_sites_suppressed"] += 1
            by = DEFER_PER_RUN_TOTALS["suppressed_by_node"]
            by[name] = by.get(name, 0) + 1
            return
        if self._pending is not None and name in self._deferred_tail:
            self._pending.append((name, run))
            return
        NODE_CALLS[0] += 1
        run()

    def _run_deferred_tail(self, pending: list) -> None:
        """Run the deferred feed-forward nodes, once, in sequence order."""
        for _name, run in pending:
            run()

    @staticmethod
    def check_agreement(
        previous: float | np.ndarray, current: float | np.ndarray
    ) -> bool:
        """Compare previous and current arrays for agreement within a tolerance.

        Parameters
        ----------
        previous : float | np.ndarray
            value(s) from previous models evaluation
        current : float | np.ndarray
            value(s) from current models evaluation

        Returns
        -------
        bool
            whether values agree or not
        """
        # Check for same shape: mfile length can change between iterations
        if isinstance(previous, float) or previous.shape == current.shape:
            return np.allclose(previous, current, rtol=1.0e-6, equal_nan=True)
        return False

    # -- VP4 -------------------------------------------------------------

    def _sweep_block(self, xc: np.ndarray, nodes: frozenset) -> None:
        """One pass of ``_call_models_once`` restricted to *nodes*.

        The sequence itself is not duplicated: the same ``_call_models_once``
        walks the same switch dispatch in the same order, and ``_node`` drops
        the calls that do not belong to this block.  A second copy of the model
        sequence -- one measured, one not -- is how the variant silently stops
        computing what the baseline computes, so there is only ever one.
        """
        self._active_nodes = nodes
        try:
            self._call_models_once(xc)
        finally:
            self._active_nodes = None

    def _call_models_partitioned(
        self, xc: np.ndarray, m: int
    ) -> tuple[float, np.ndarray]:
        """Block Gauss-Seidel over the DSM modules, then objective and constraints.

        Each iterated block is solved to its own fixed point on the coupling
        state before the next block runs, at the one tolerance, and the
        schedule then runs **exactly once**.  The predicate is the
        coupling-state one, on ``y``, at ``tau`` -- never ``objf``/``conf``,
        which no single module determines (D14(c)).

        **There is no loop over schedule passes, and that is a decision rather
        than an omission.**  Feed-forward partitioning asserts that nothing is
        left to close between the blocks; an earlier revision paid for a
        verification pass that checked the assertion in-loop, and A43
        (st-trust-gap) measured that pass triggering a further one **zero times
        in 91 888 evaluations**.  The user removed the arm that used it (D22)
        and fixed one tolerance for every converger (D23), so the schedule runs
        once and the assertion is checked outside the arm, by the uncharged
        exit audit, which every arm pays for equally and none pays for twice.

        Raises
        ------
        ModuleSolveFailure
            if a block loop or the global block budget hits its cap.  Decision
            **D15(d)**: a failed block solve raises and counts as a failed
            start, so the arms' failure modes are comparable.
        """
        if self.data.stellarator.istell != 0 or self.data.ife.ife != 0:
            raise module_solve.ModuleSolveFailure(
                "PROCESS_ARCH_MDA is a tokamak-only variant point: "
                "the stellarator and IFE paths return from _call_models_once "
                "before any node the DSM partition names, so a block schedule "
                "over them would be a schedule over nothing."
            )

        if self._yspec is None:
            self._yspec, self._yprov = module_solve.load_spec()
            self._ysubsets, _ = module_solve.load_subsets(self._yspec)
        spec = self._yspec
        subsets = self._ysubsets
        # One tolerance, for every block loop of every arm (D23).  The switch
        # that used to set a second, "inner" one is retired: comparisons are
        # made at matched *achieved* accuracy, which the exit audit records per
        # run, not at matched settings.
        tau = module_solve.TAU

        schedule, tail = module_schedule(self.data.numerics.i_figure_merit)
        # Recorded, not acted on: whether one block covers every in-loop node.
        # Evaluated from the schedule that was actually built rather than from
        # the arm's name, so a run record says what the schedule was.
        single_block = _single_block_covers_loop(schedule, tail)
        bound = spec.bind(self.data)
        read = spec.read

        # The block schedule never uses the per-call deferral's pending list:
        # under a block schedule the deferred tail is a block, run once at the
        # end of the schedule.
        self._pending = None

        # A31 (drift-diagnostic): the joint-test trace's call index.  With
        # PROCESS_ARCH_PASS_TRACE unset TRACE_ENABLED is False, the index is
        # never computed and no hook below runs — neutrality is gated against
        # A28's recorded counts (protocol §12), not asserted.
        trace_call = (
            MDA_TOTALS["n_call_models"] + 1
            if module_solve.TRACE_ENABLED
            else 0
        )

        block_sweeps = 0
        inner_counts: dict[str, list[int]] = {lab: [] for lab, _n, _i in schedule}
        moved_constants: set = set()
        # A90 (m2-phasea-vs-phaseb): per block, each sweep's residual split by
        # module.  ``None`` with PROCESS_ARCH_BLOCK_TRACE unset, and then no
        # hook below runs.
        block_trace = {} if module_solve.BLOCK_TRACE_ENABLED else None
        trace_modules = (
            module_solve.block_trace_modules(spec, subsets)
            if block_trace is not None
            else None
        )

        def charge() -> None:
            nonlocal block_sweeps
            block_sweeps += 1
            if block_sweeps > module_solve.GLOBAL_BLOCK_SWEEP_CAP:
                raise module_solve.ModuleSolveFailure(
                    f"global block-sweep cap "
                    f"({module_solve.GLOBAL_BLOCK_SWEEP_CAP}) reached at "
                    f"tau={tau:g}"
                )

        # The schedule runs once.  ``schedule_passes`` is kept as a name and as
        # a recorded quantity because the run record publishes the distribution
        # of it, and a constant 1 is a statement -- "the schedule was not
        # repeated in this run" -- where a missing field would be a silence.
        # DR4 (A58): every visit the schedule makes to a block, and the subset
        # of those that executed no model node -- measured on NODE_CALLS across
        # the visit, because a block can be visited with its member still in it
        # and have that member skipped at the call site (issue I-20a's PULSE
        # block).  Counted, never acted on: decision D21 keeps the empty visits
        # and disclaims them.
        def close_visit(label: str, nodes_before: int, sweeps_before: int) -> None:
            if NODE_CALLS[0] != nodes_before:
                return
            EMPTY_BLOCK_VISITS[label] = EMPTY_BLOCK_VISITS.get(label, 0) + 1
            spent = DISPATCH_SWEEPS[0] - sweeps_before
            if spent:
                EMPTY_BLOCK_SWEEPS[label] = (
                    EMPTY_BLOCK_SWEEPS.get(label, 0) + spent
                )

        schedule_passes = 1
        for label, nodes, iterate in schedule:
            BLOCK_VISITS[label] = BLOCK_VISITS.get(label, 0) + 1
            visit_nodes = NODE_CALLS[0]
            visit_sweeps = DISPATCH_SWEEPS[0]
            if not nodes:
                close_visit(label, visit_nodes, visit_sweeps)
                inner_counts[label].append(0)
                continue
            if not iterate:
                charge()
                self._sweep_block(xc, nodes)
                inner_counts[label].append(1)
                close_visit(label, visit_nodes, visit_sweeps)
                continue
            # A block loop's test is restricted to that block's own write set,
            # as the evaluation phase's block arm restricts it.  Not an
            # optimisation: the coupling-state predicate scores any component
            # that is not float-viewable in *either* snapshot as ``inf``, and
            # in a fresh process that is every field no model has written yet
            # -- so an unrestricted test is held open for ever by a field the
            # running block cannot touch.
            subset = subsets.get(label)
            # DR4 (A58): how wide this block's convergence test is.  The
            # predicate walks exactly the indices the subset names, and the
            # whole component list when there is no subset -- which is the flat
            # arrangement's single block.  One integer, resolved once per block
            # rather than per sweep.
            width = len(subset) if subset is not None else len(spec.keys)
            y_prev = read(bound)
            inner_ok = False
            s = 0
            for s in range(1, module_solve.INNER_CAP + 1):
                charge()
                self._sweep_block(xc, nodes)
                y = read(bound)
                # DR5 (A59): every predicate evaluation this arrangement makes
                # -- the flat arrangement's single block and each block loop of
                # the partitioned one alike -- is taken on the ruler the run
                # asked for.  There is exactly one call site, so there is
                # exactly one place the choice can be made, and no path where a
                # loop stops on a ruler the record does not name.  The ruler
                # picks the denominator; it does not change which components
                # are compared, which is why COMPONENTS_COMPARED below is the
                # free consistency check between the two.
                res = spec.residual(
                    y_prev, y, subset=subset,
                    ruler=module_solve.PREDICATE_MODE,
                )
                # DR4 (A58): one convergence test, of this many components.
                PREDICATE_EVALUATIONS[0] += 1
                COMPONENTS_COMPARED[0] += width
                PREDICATE_EVALUATIONS_BY_BLOCK[label] = (
                    PREDICATE_EVALUATIONS_BY_BLOCK.get(label, 0) + 1
                )
                COMPONENTS_COMPARED_BY_BLOCK[label] = (
                    COMPONENTS_COMPARED_BY_BLOCK.get(label, 0) + width
                )
                moved_constants |= {
                    spec.name(i) for i in res.moved_constant
                }
                # A31: with one block covering every in-loop node, THIS
                # residual is the joint test -- the flat arrangement's movement
                # lives here.  Full snapshots: the single block has no subset
                # in the write-set artifact.
                if module_solve.TRACE_ENABLED and single_block:
                    module_solve.trace_pass(
                        "flat_inner", trace_call, s, spec, y_prev, y,
                        res, tau,
                    )
                if block_trace is not None:
                    block_trace.setdefault(label, []).append(
                        module_solve.block_trace_sweep(res, trace_modules, tau)
                    )
                y_prev = y
                if res.converged(tau):
                    inner_ok = True
                    break
            inner_counts[label].append(s)
            close_visit(label, visit_nodes, visit_sweeps)
            if not inner_ok:
                self.module_solve_stats = self._module_stats(
                    block_sweeps, schedule_passes, inner_counts,
                    moved_constants, converged=False, cap_hit="block",
                    single_block=single_block,
                )
                _roll_up(self.module_solve_stats)
                if block_trace is not None:
                    self._block_trace_line(xc, inner_counts, block_trace, False)
                raise module_solve.ModuleSolveFailure(
                    f"block {label} did not converge in "
                    f"{module_solve.INNER_CAP} sweeps at tau={tau:g}; max "
                    f"scaled residual {res.max:g} on "
                    f"{res.brief(tau)['argmax']}, {res.n_above(tau)} "
                    f"components above tau"
                )

        # The per-call deferral inside the block schedule: the feed-forward
        # tail runs once, on the state the schedule left.  Charged like any
        # other block sweep.
        if tail:
            charge()
            self._sweep_block(xc, tail)

        if _idf_probe.ENABLED:
            _idf_probe.objective_begin()
        objf = objective_function(self.data.numerics.i_figure_merit, self.data)
        conf, _, _, _, _ = constraints.constraint_eqns(m, -1, self.data)
        if _idf_probe.ENABLED:
            _idf_probe.objective_end()

        self.module_solve_stats = self._module_stats(
            block_sweeps, schedule_passes, inner_counts, moved_constants,
            converged=True, cap_hit=None, single_block=single_block,
        )
        _roll_up(self.module_solve_stats)
        if block_trace is not None:
            self._block_trace_line(xc, inner_counts, block_trace, True)
        return objf, conf

    def _block_trace_line(self, xc, inner_counts, block_trace, converged) -> None:
        """A90 (m2-phasea-vs-phaseb): one evaluation's line of the block trace.

        Called only with PROCESS_ARCH_BLOCK_TRACE set.  Reads and consumes the
        evaluation kind the optimiser's evaluator set; writes nothing the run
        computes with.
        """
        module_solve.block_trace_write({
            "call": MDA_TOTALS["n_call_models"],
            "evaluation": module_solve.EVALUATION_KIND,
            "iteration": int(self.data.numerics.n_solver_iterations),
            "x": [float(v).hex() for v in xc],
            "converged": converged,
            "sweeps": {k: sum(v) for k, v in inner_counts.items()},
            "per_sweep": block_trace,
        })
        module_solve.EVALUATION_KIND = None

    @staticmethod
    def _module_stats(
        block_sweeps, schedule_passes, inner_counts, moved_constants,
        *, converged, cap_hit, single_block=False,
    ) -> dict:
        """The block schedule's own counts, for the run record.

        ``outer_passes`` keeps its name: it is the key the committed
        reproduction reference and every earlier record use for the number of
        schedule passes, and renaming a recorded field is a change to the
        record schema rather than to the driver.  It is 1 in every arm.  The
        deferred tail is no longer stamped here per call: it is resolved once
        per run and stamped once, in :data:`SCHEDULE_RESOLUTION` (DR9).
        """
        return {
            "converged": converged,
            "cap_hit": cap_hit,
            "single_block_covers_loop": bool(single_block),
            "block_sweeps": block_sweeps,
            "outer_passes": schedule_passes,
            "inner_counts": {k: list(v) for k, v in inner_counts.items()},
            "inner_totals": {k: sum(v) for k, v in inner_counts.items()},
            "moved_constants": sorted(moved_constants),
        }

    def call_models(self, xc: np.ndarray, m: int) -> tuple[float, np.ndarray]:
        """Evaluate models until results are idempotent.

        Ensure objective function and constraints are idempotent before returning.

        Parameters
        ----------
        xc : np.ndarray
            optimisation parameters
        m : int
            number of constraints

        Returns
        -------
        Tuple[float, np.ndarray]
            objective function and constraints

        Raises
        ------
        RuntimeError
            if values are non-idempotent after successive
            evaluations
        """
        if _idf_probe.ENABLED:
            _idf_probe.call_models_begin()

        # I-17 instrument: sweeps taken by THIS evaluation, binned on exit by
        # every path (normal return, the VP4 early return, or a raise).
        _sweeps_at_entry = DISPATCH_SWEEPS[0]
        try:
            return self._call_models_inner(xc, m)
        finally:
            _n = DISPATCH_SWEEPS[0] - _sweeps_at_entry
            _k = str(_n)
            SWEEPS_PER_EVAL_HIST[_k] = SWEEPS_PER_EVAL_HIST.get(_k, 0) + 1

    def _call_models_inner(self, xc: np.ndarray, m: int) -> tuple[float, np.ndarray]:
        """The body of :meth:`call_models`; see it for the contract.

        Split out only so the I-17 sweep histogram can bin on every exit path
        without wrapping the body in an indent-changing ``try``.  No behaviour
        of its own.
        """
        # VP6 (D19, task A40; DR10, V5 list item 8, task A99): the
        # arrangement's method-level move is PRE-PROCESSING of the evaluation.
        # The first-wall geometry pair is a run-constant of two input-file
        # values; priming it once here, before the first block of the schedule
        # (or the first sweep of the flat loop), is what lets Build -- which
        # the partitioned schedule runs before FirstWall -- read this
        # evaluation's value rather than the previous one's.  V4 primed at the
        # head of every sweep; the bits are the same each time, so the exit
        # states are unchanged (gate G2) and the stamped count becomes the
        # evaluation count (gate GC).  Not a node, not routed through _node,
        # not counted in NODE_CALLS -- stamped via ARRANGEMENT_METHOD_CALLS.
        # With the switch unset this is one boolean read (gate G1).
        if ARRANGEMENT_METHOD_FW_GEOMETRY:
            ARRANGEMENT_METHOD_CALLS[0] += 1
            self.models.fw.set_fw_geometry()

        # VP2c: resolve (and on first use validate) the post-solve exclusion
        # set.  With the switch off ``_defer_per_run`` stays ``None`` and nothing
        # below this line differs.
        if DEFER_PER_RUN_ENABLED:
            self._defer_per_run = _defer_per_run_nodes(self.data)

        # VP4: the block schedule replaces the flat loop entirely -- including
        # its predicate, which decision D14(c) requires: a per-module solver
        # cannot test a global objective, because one module does not determine
        # it.  With VP4 off nothing below this line differs from upstream.
        if MDA_ENABLED:
            objf, conf = self._call_models_partitioned(xc, m)
            if _idf_probe.ENABLED:
                _idf_probe.call_models_end()
            return objf, conf

        objf_prev = None
        conf_prev = None

        # VP2: with the per-call deferral on, the feed-forward nodes are
        # collected instead of run, and the last sweep's collection is run once
        # the loop has settled.  With it off ``_pending`` stays ``None`` and
        # nothing below this line differs from upstream.
        if DEFER_PER_CALL_ENABLED:
            (
                self._defer_per_call_pre,
                self._defer_per_call_post,
            ) = self._resolve_defer_per_call_tails()
            self._deferred_tail = self._defer_per_call_pre | self._defer_per_call_post
            pending: list | None = [] if self._deferred_tail else None
        else:
            pending = None

        # Evaluate models up to 10 times; any more implies non-converging values
        for _ in range(10):
            if pending is not None:
                pending.clear()
                self._pending = pending
            self._call_models_once(xc)
            self._pending = None
            # Evaluate objective function and constraints
            if _idf_probe.ENABLED:
                _idf_probe.objective_begin()
            objf = objective_function(self.data.numerics.i_figure_merit, self.data)
            conf, _, _, _, _ = constraints.constraint_eqns(m, -1, self.data)
            if _idf_probe.ENABLED:
                _idf_probe.objective_end()

            if objf_prev is None and conf_prev is None:
                # First run: run again to check idempotence
                logger.debug("New optimisation parameter vector being evaluated")
                objf_prev = objf
                conf_prev = conf
                continue

            # Check for idempotence
            #
            # DR4 (A58): upstream's own stopping test, counted here so that the
            # reference arms carry a measured predicate cost instead of a zero.
            # ``check_agreement`` is a pure comparison, so evaluating the
            # objective half into a name and then using it is the same
            # evaluation in the same order; what it buys is an exact width,
            # since the pair short-circuits and the constraint vector is not
            # compared when the objective has moved.
            _objf_agrees = self.check_agreement(objf_prev, objf)
            UPSTREAM_PREDICATE_EVALUATIONS[0] += 1
            UPSTREAM_COMPONENTS_COMPARED[0] += 1 + (len(conf) if _objf_agrees else 0)
            if _objf_agrees and self.check_agreement(conf_prev, conf):
                # Idempotent: no longer changing, so return
                logger.debug(
                    "Model evaluations idempotent, returning objective "
                    "function and constraints"
                )
                # VP2, split by plan §4.1d.  The fixed point is reached, so
                # the deferred nodes run once on the converged state --- but
                # the **pre-predicate** group has to run before ``objf`` and
                # ``conf`` are the values this call returns, because the
                # predicate layer reads something it writes.  So it runs, and
                # then the predicate is re-evaluated on the state it produced.
                # The post-predicate group runs after, as A13 built it.
                #
                # The extra evaluation of the predicate is not an extra sweep:
                # it is one call to ``objective_function`` and one to
                # ``constraint_eqns``, on a state that has just converged.
                if pending:
                    pre = [t for t in pending if t[0] in self._defer_per_call_pre]
                    post = [t for t in pending if t[0] not in self._defer_per_call_pre]
                    if pre:
                        self._run_deferred_tail(pre)
                        if _idf_probe.ENABLED:
                            _idf_probe.objective_begin()
                        objf = objective_function(
                            self.data.numerics.i_figure_merit, self.data
                        )
                        conf, _, _, _, _ = constraints.constraint_eqns(
                            m, -1, self.data
                        )
                        if _idf_probe.ENABLED:
                            _idf_probe.objective_end()
                    if post:
                        self._run_deferred_tail(post)
                if _idf_probe.ENABLED:
                    _idf_probe.call_models_end()
                return objf, conf

            # Not idempotent: still changing, so evaluate models again
            logger.debug("Model evaluations not idempotent: evaluating again")
            objf_prev = objf
            conf_prev = conf

        if _idf_probe.ENABLED:
            _idf_probe.call_models_end(converged=False)

        raise RuntimeError(
            "After 10 model evaluations at the current optimisation parameter "
            "vector, values for the objective function and constraints haven't "
            "converged (don't produce idempotent values)."
        )

    def call_models_and_write_output(self, xc: np.ndarray, ifail: int):
        """Evaluate models until results are idempotent, then write output files.

        Ensure all outputs in mfile are idempotent before returning, by
        evaluating models multiple times. Typically used at the end of an
        optimisation, or in a non-optimising evaluation. Writes OUT.DAT and
        MFILE.DAT with final results.

        Parameters
        ----------
        xc : np.ndarray
            optimisation parameter
        ifail : int
            return code of solver

        Raises
        ------
        RuntimeError
            if values are non-idempotent after successive
            evaluations
        """
        # TODO The only way to ensure idempotence in all outputs is by comparing
        # mfiles at this stage
        previous_mfile_data = None

        # VP2: the per-call deferral applies to the optimiser's evaluation path
        # only.
        # This is the final-output path, where ``models.write`` re-enters every
        # model's ``run()`` from its ``output()`` anyway (trap T7), so nothing
        # is deferred here.
        self._pending = None

        # DR2 (A57): the output path without the output-time loop.  The solve
        # phase of this arm handed over a state it has already converged on the
        # coupling state at the shared tolerance, so there is nothing for a
        # second idempotence loop to find; re-solving that state before writing
        # it out is a property of the incumbent's stopping rule and not of the
        # architecture under test.  ``finalise`` is called **once**, on the
        # accepted state, and no output-time sweep runs -- which is why
        # ``OUTPUT_LOOP_SWEEPS`` is 0 here by construction and not by
        # assertion.  Nothing is diverted to the idempotence scratch files,
        # because nothing is compared.
        if not OUTPUT_LOOP_UPSTREAM:
            _take_exit_snapshot(self.models, self.data, "before_finalise")
            finalise(self.models, self.data, ifail)
            return

        try:  # noqa: PLW0717
            # Evaluate models up to 10 times; any more implies non-converging values
            for _ in range(10):
                # Divert OUT.DAT and MFILE.DAT output to scratch files for
                # idempotence checking
                OutputFileManager.open_idempotence_files(self.data.globals.output_prefix)
                # DR2 (A57): one integer per sweep of the output-time loop, so
                # that what the incumbent's second loop costs is a measured
                # column of the cost table rather than a term nobody counted.
                OUTPUT_LOOP_SWEEPS[0] += 1
                self._call_models_once(xc)
                # Write mfile
                finalise(self.models, self.data, ifail)

                # Extract data from intermediate idempotence-checking mfile
                mfile_path = (self.data.globals.output_prefix) + "IDEM_MFILE.DAT"
                mfile = MFile(mfile_path)
                # Create mfile dict of float values: only compare floats
                mfile_data = {
                    var: val
                    for var in mfile.data
                    if isinstance(val := mfile.data[var].get_scan(-1), float)
                }

                if previous_mfile_data is None:
                    # First run: need another run to compare with
                    logger.debug(
                        "New mfile created: evaluating models again to check idempotence"
                    )
                    previous_mfile_data = mfile_data.copy()
                    continue

                # Compare previous and current mfiles for agreement
                nonconverged_vars = {}
                for var in previous_mfile_data:
                    previous_value = previous_mfile_data[var]
                    current_value = mfile_data.get(var, np.nan)
                    if self.check_agreement(previous_value, current_value):
                        continue
                    # Value has changed between previous and current mfiles
                    nonconverged_vars[var] = [
                        previous_value,
                        current_value,
                    ]

                if len(nonconverged_vars) == 0:
                    # Previous and current mfiles agree (idempotent)
                    logger.debug("Mfiles idempotent, returning")
                    # Divert OUT.DAT and MFILE.DAT output back to original files
                    # now idempotence checking complete
                    OutputFileManager.close_idempotence_files(
                        self.data.globals.output_prefix
                    )
                    # Write final output file and mfile
                    _take_exit_snapshot(self.models, self.data, "before_finalise")
                    finalise(self.models, self.data, ifail)
                    return

                # Mfiles not yet idempotent: need to re-evaluate models
                logger.debug("Mfiles not idempotent, evaluating models again")
                previous_mfile_data = mfile_data.copy()

            # Values haven't all stabilised after 10 evaluations
            # Which variables are still changing?
            non_idempotent_warning = (
                "Model evaluations at the current optimisation parameter vector "
                "don't produce idempotent values in the final output."
            )
            non_idempotent_table = tabulate(
                [[k, v[0], v[1]] for k, v in nonconverged_vars.items()],
                headers=["Variable", "Previous value", "Current value"],
            )

            logger.warning(
                f"\033[93m{non_idempotent_warning}\n{non_idempotent_table}\033[0m",
                stacklevel=2,
            )

            # Close idempotence files, write final output file and mfile
            OutputFileManager.close_idempotence_files(self.data.globals.output_prefix)

        except Exception:
            # If exception in model evaluations delete intermediate idempotence
            # files to clean up
            OutputFileManager.close_idempotence_files(self.data.globals.output_prefix)
            raise
        else:
            _take_exit_snapshot(self.models, self.data, "before_finalise")
            finalise(
                self.models,
                self.data,
                ifail,
                non_idempotent_msg=non_idempotent_warning + "\n" + non_idempotent_table,
            )

    def _call_models_once(self, xc: np.ndarray):
        """Call the physics and engineering models.

        This method is the principal caller of all the physics and
        engineering models. Some are Fortran subroutines within modules, others
        will be methods on Python model objects.

        Parameters
        ----------
        xc : np.array
            Array of optimisation parameters
        """
        # I-17 instrument: one sweep of the dispatch body.  Integer only.
        DISPATCH_SWEEPS[0] += 1

        if _idf_probe.ENABLED:
            _idf_probe.sweep(self.models, self.data)

        # Number of active iteration variables
        nvars = len(xc)

        # Increment the call counter
        self.data.numerics.n_model_calls += 1

        # Convert variables
        set_scaled_iteration_variable(xc, nvars, self.data)

        # Perform the various function calls
        # Stellarator caller
        if self.data.stellarator.istell != 0:
            self.models.stellarator.run()
            # TODO Is this return safe?
            return

        # Inertial Fusion Energy calls
        if self.data.ife.ife != 0:
            self.models.ife.run()
            return

        # VP6 (D19, task A40): the first-wall geometry prime used to sit
        # here, at the head of every sweep; DR10 (A99) moved it to the head
        # of ``_call_models_inner`` -- once per evaluation, before the first
        # block.  The output path and the exit audit call this method
        # directly and no longer prime: FirstWall has run by then and the
        # pair holds the same bits.

        # Tokamak calls
        # Plasma geometry model, machine build model (radial build) and
        # physics.  Their relative order is the VP1 variant point; see
        # ARRANGEMENT_NODE_HEAD at module level.  With
        # PROCESS_ARCH_ARRANGEMENT_NODE unset
        # this is plasma_geom, build, physics -- the upstream order.
        for _head_node in ARRANGEMENT_NODE_HEAD:
            self._node(_head_node, getattr(self.models, _head_node).run)

        # Toroidal field coil model

        # Toroidal field coil resistive model
        if self.data.tfcoil.i_tf_sup == TFConductorModel.WATER_COOLED_COPPER:
            self._node("copper_tf_coil", self.models.copper_tf_coil.run)

        # Toroidal field coil superconductor model
        if self.data.tfcoil.i_tf_sup == TFConductorModel.SUPERCONDUCTING:
            if (
                SuperconductingTFTurnType(
                    self.data.superconducting_tfcoil.i_tf_turn_type
                )
                == SuperconductingTFTurnType.CABLE_IN_CONDUIT
            ):
                self._node("cicc_sctfcoil", self.models.cicc_sctfcoil.run)
            elif (
                SuperconductingTFTurnType(
                    self.data.superconducting_tfcoil.i_tf_turn_type
                )
                == SuperconductingTFTurnType.CROSS_CONDUCTOR
            ):
                self._node("croco_sctfcoil", self.models.croco_sctfcoil.run)

        if self.data.tfcoil.i_tf_sup == TFConductorModel.HELIUM_COOLED_ALUMINIUM:
            self._node("aluminium_tf_coil", self.models.aluminium_tf_coil.run)

        # Poloidal field and central solenoid model
        self._node("pfcoil", self.models.pfcoil.run)

        # Pulsed reactor model.  Deferrable (VP2): ``pulse`` is the
        # articulation point and joins the feed-forward tail only once the
        # burn time is out of the loop.
        self._node("pulse", self.models.pulse.run)

        self._node("divertor", self.models.divertor.run)

        # First wall model
        self._node("fw", self.models.fw.run)

        self._node("shield", self.models.shield.run)

        self._node("vacuum_vessel", self.models.vacuum_vessel.run)

        # Blanket model
        """Blanket switch values
        No.  |  model
        ---- | ------
        1    |  CCFE HCPB model
        2    |  KIT HCPB model
        3    |  CCFE HCPB model with Tritium Breeding Ratio calculation
        4    |  KIT HCLL model
        5    |  DCLL model
        """
        if self.data.fwbs.i_blanket_type == BlktModelTypes.CCFE_HCPB:
            # CCFE HCPB model
            self._node("ccfe_hcpb", self.models.ccfe_hcpb.run)

        elif self.data.fwbs.i_blanket_type == BlktModelTypes.DCLL:
            # DCLL model
            self._node("dcll", self.models.dcll.run)

        self._node("cryostat", self.models.cryostat.run)

        # Structure Model
        self._node("structure", self.models.structure.run)

        # Tight aspect ratio machine model
        if (
            self.data.physics.itart == 1
            and self.data.tfcoil.i_tf_sup != TFConductorModel.SUPERCONDUCTING
        ):
            self._node("tfcoil", self.models.tfcoil.run)

        # Power model
        self._node("power", self.models.power.run)

        # Vacuum model
        self._node("vacuum", self.models.vacuum.run)

        # Buildings model
        self._node("buildings", self.models.buildings.run)

        # These two methods need to be run after vacuum/buildings otherwise
        # output changes quite a lot
        # TODO: split these two sections into a new model with a .run method
        # Plant AC power requirements
        self._node("power.acpow", self._acpow)

        # Plant heat transport pt 2 & 3
        self._node(
            "power.plant_electric_production",
            self.models.power.plant_electric_production,
        )

        # Availability model
        self._node("availability", self.models.availability.run)

        # Water usage in secondary cooling system.  Deferrable (VP2).
        self._node("water_use", self.models.water_use.run)

        # Costs model
        """Cost switch values
        No.  |  model
        ---- | ------
        0    |  1990 costs model
        1    |  2015 Kovari model
        2    |  Custom model
        """
        # Deferrable (VP2).
        self._node("costs", self.models.costs.run)

        # FISPACT and LOCA model (not used)- removed

        # A34: the tripwire.  A constant-owned burn time that any model call
        # moved is named at the sweep that moved it -- a check, never a
        # rewrite, because re-forcing the value would mask the writer.  Dead
        # branch unless a constant owns the burn time.
        if subsolve.CONSTANT_OWNS_BURN_TIME:
            subsolve.assert_burn_time_constant(self.data)

        if _idf_probe.ENABLED:
            _idf_probe.sweep_end()


def finalise(models, data, ifail: int, non_idempotent_msg: str | None = None):
    """Routine to print out the final point in the scan.

    Writes to OUT.DAT and MFILE.DAT.

    Parameters
    ----------
    models : process.main.Models
        physics and engineering model objects
    data: DataStructure
        data structure object to provide data to evaluate the constraints
    ifail : int
        error flag
    non_idempotent_msg : None | str, optional
        warning about non-idempotent variables, defaults to None
    """
    if ifail == 1:
        po.oheadr(constants.NOUT, "Final Feasible Point")
    else:
        po.oheadr(constants.NOUT, "Final UNFEASIBLE Point")

    # Output relevant to no optimisation
    if data.numerics.i_process_run_mode == PROCESSRunMode.EVALUATION:
        output_evaluation(data)

    # Print non-idempotence warning to OUT.DAT only
    if non_idempotent_msg:
        po.oheadr(constants.NOUT, "NON-IDEMPOTENT VARIABLES")
        po.ocmmnt(constants.NOUT, non_idempotent_msg)

    # Write output to OUT.DAT and MFILE.DAT
    models.write(data, constants.NOUT)


def output_evaluation(data):
    """Write output for an evaluation run of PROCESS

    Parameters
    ----------
    data: DataStructure
        data structure object to provide data to evaluate the constraints
    """
    po.oheadr(constants.NOUT, "Numerics")
    po.ocmmnt(constants.NOUT, "PROCESS has performed an evaluation run.")
    po.oblnkl(constants.NOUT)

    # Evaluate objective function
    norm_objf = objective_function(data.numerics.i_figure_merit, data)
    po.ovarre(constants.MFILE, "Normalised objective function", "(norm_objf)", norm_objf)

    # Print the residuals of the constraint equations

    residual_error, value, residual, symbols, units = constraints.constraint_eqns(
        data.numerics.n_equality_constraints + data.numerics.n_inequality_constraints,
        -1,
        data,
    )

    labels = [
        data.numerics.lablcc[j - 1]
        for j in data.numerics.icc[
            : data.numerics.n_equality_constraints
            + data.numerics.n_inequality_constraints
        ]
    ]

    def _fmt(a, units):
        return [f"{c} {u}" for c, u in zip(a, units, strict=False)]

    po.write(
        constants.NOUT,
        tabulate(
            {
                "Constraint Name": labels,
                "Constraint Type": symbols,
                "Physical constraint": _fmt(value, units),
                "Constraint residual": _fmt(residual, units),
                "Normalised residual": residual_error,
            },
            headers="keys",
        ),
    )

    for i in range(data.numerics.n_equality_constraints):
        constraint_id = data.numerics.icc[i]
        po.ovarre(
            constants.MFILE,
            f"{labels[i]} normalised residue",
            f"(eq_con{constraint_id:03d})",
            residual_error[i],
        )

    for i in range(data.numerics.n_inequality_constraints):
        constraint_id = data.numerics.icc[data.numerics.n_equality_constraints + i]
        po.ovarre(
            constants.MFILE,
            f"{labels[data.numerics.n_equality_constraints + i]}",
            f"(ineq_con{constraint_id:03d})",
            residual_error[data.numerics.n_equality_constraints + i],
        )


def write_output_files(
    models: Models, data: DataStructure, ifail: int, *, runtime: float | None = None
):
    """Evaluate models and write output files (OUT.DAT and MFILE.DAT).

    Parameters
    ----------
    models : Models
        physics and engineering models
    data: DataStructure
        data structure object
    ifail : int
        solver return code
    """
    # VP4 accounting: the solve phase ends here.  One integer read, on both
    # arms; see NODE_CALLS_AT_OUTPUT.  DR7 (A60) freezes the sweep counter in
    # the same statement and for the same reason: the per-attempt sweep counts
    # need a solve-phase whole to add up to, and the run total contains the
    # output-time loop and the exit audit, which belong to no attempt.
    if NODE_CALLS_AT_OUTPUT[0] is None:
        NODE_CALLS_AT_OUTPUT[0] = NODE_CALLS[0]
        DISPATCH_SWEEPS_AT_OUTPUT[0] = DISPATCH_SWEEPS[0]
    # A57: the exit audit's declared position (experiment plan section 3.3).
    # HERE -- at the entry, before the per-run deferred nodes below and before
    # any output-time sweep -- is the state the solve handed over, and it is
    # the one position every arm's accuracy is compared at.  The snapshot is
    # taken; the residual is computed after the run, from the restored
    # snapshot, because the audit's own sweep would otherwise hand the output
    # path a state the optimiser never accepted.
    OUTPUT_PATH_ENTRIES[0] += 1
    _take_exit_snapshot(models, data, "entry_to_write_output_files")
    n = data.numerics.n_iteration_variables
    x = data.numerics.xcm[:n]
    # Call models, ensuring output mfiles are fully idempotent
    caller = Caller(models, data)
    # VP2c (A33): the excluded nodes run exactly once per run, HERE -- after
    # the optimiser has accepted, before any output work.  The mechanism is
    # the block sweep: the same ``_call_models_once`` walks the same dispatch
    # in sequence order and ``_node`` drops everything outside the set.  This
    # is the same pattern the output path applies to every node (inject the
    # accepted x, sweep); it is counted in ``node_calls_total`` but lands
    # after the solve-phase counter was frozen above, so the skipped nodes'
    # own calls are visible in the total and absent from the solve phase.
    # ``caller`` here never enters ``call_models``, so its ``_defer_per_run`` is
    # ``None`` and the exclusion does not apply to this sweep -- nor to the
    # output phase below, which re-runs every model to MFILE idempotence
    # exactly as upstream does.
    if DEFER_PER_RUN_ENABLED:
        ps = _defer_per_run_nodes(data)
        DEFER_PER_RUN_TOTALS["executed_once"] = sorted(ps)
        DEFER_PER_RUN_TOTALS["executed_once_at_node_calls"] = NODE_CALLS[0]
        if ps:
            caller._sweep_block(x, ps)
    if runtime is not None:
        ovarre(
            constants.MFILE,
            "Runtime of PROCESS in seconds",
            "(process_runtime)",
            runtime,
        )
    caller.call_models_and_write_output(
        xc=x,
        ifail=ifail,
    )
