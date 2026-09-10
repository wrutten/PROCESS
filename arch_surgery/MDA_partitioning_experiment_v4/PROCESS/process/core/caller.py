"""Module to call physics and engineering models"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from tabulate import tabulate

from process.core import _idf_probe, constants
from process.core import process_output as po
from process.core.io.mfile import MFile
from process.core.process_output import OutputFileManager, ovarre
from process.core.solver import constraints
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
# VP1 (framework hook F7a) -- the model call sequence is a driver choice.
#
# The first three tokamak nodes are unconditional and adjacent, and they are
# the only part of the sequence VP1 currently varies, so the variant point is
# a list of node names that ``_call_models_once`` walks.  Everything after
# them is switch-selected on the input deck and is left exactly as upstream
# wrote it; this is a permutation of three calls, not a scheduler.
#
# ``upstream`` is the order upstream PROCESS uses and is the default: with
# ``PROCESS_ARCH_SEQUENCE`` unset the loop below issues ``plasma_geom``,
# ``build``, ``physics`` in that order, which is what the three straight-line
# statements it replaced did.
#
# ``build_after_physics`` (task A3) moves ``build`` -- DSM row 5, module M2
# Coils -- from inside M1 Physics' span to the head of M2's span, so that M1
# becomes contiguous in the call order and a per-module solver can wrap it.
# The selection is resolved once at import, never per call.
_SEQUENCE_HEADS: dict[str, tuple[str, ...]] = {
    "upstream": ("plasma_geom", "build", "physics"),
    "build_after_physics": ("plasma_geom", "physics", "build"),
}

SEQUENCE_NAME: str = os.environ.get("PROCESS_ARCH_SEQUENCE", "").strip() or "upstream"

if SEQUENCE_NAME not in _SEQUENCE_HEADS:
    raise RuntimeError(
        f"PROCESS_ARCH_SEQUENCE={SEQUENCE_NAME!r} is not a recognised model "
        f"sequence; expected one of {tuple(_SEQUENCE_HEADS)} (or unset for "
        f"{'upstream'!r})."
    )

#: Resolved node order for the head of the tokamak model sequence.
SEQUENCE_HEAD: tuple[str, ...] = _SEQUENCE_HEADS[SEQUENCE_NAME]


# --------------------------------------------------------------------------
# VP6 (D19, task A40) -- the first-wall geometry prime.
#
# A35 named the one cut edge that carries a displaced entry into a one-pass
# exit on the study decks: ``FirstWall`` (block M3) computes
# ``build.dr_fw_inboard`` / ``dr_fw_outboard`` -- a run-constant of two pure
# deck inputs (``fw.py:347-352`` at the base commit) -- and ``Build``
# (block M2, earlier in the executed schedule) reads the *previous* pass's
# values.  Under an iterating driver the lag costs at most one sweep; under
# a one-pass schedule it transmits exactly the entry displacement of the
# pair, once, with A35's measured linear coefficients.
#
# The prime executes that one method at the head of every sweep, so ``Build``
# reads this pass's value.  It is a driver choice about *when* an existing
# model method runs -- the same family as the VP1 reorder but finer-grained
# (a method, not a node); nothing under ``process/models/`` changes, and
# ``FirstWall``'s own execution is untouched (the prime *duplicates* a
# run-constant of two floating-point operations, identical bits each time).
#
# ``off`` is the default and is upstream behaviour exactly: the guard in
# ``_call_models_once`` is one module-level boolean read per sweep and the
# counter never moves (gate G1: byte identity with the switch unset).
#
# The call is deliberately NOT routed through :meth:`Caller._node`: it is
# not a node, it must add no counted node call, and every count comparison
# must stay commensurable with V2.  It is **stamped, not counted** -- the
# runners record :data:`PRIME_CALLS` as ``n_prime_calls`` in every run's
# metrics, published as a footnote beside the node-call tables and never
# pooled into them (V3 plan section 2; trap T11 -- no silent work).
_PRIME: dict[str, bool] = {"off": False, "fw_geometry": True}

PRIME_NAME: str = os.environ.get("PROCESS_ARCH_PRIME", "").strip() or "off"

if PRIME_NAME not in _PRIME:
    raise RuntimeError(
        f"PROCESS_ARCH_PRIME={PRIME_NAME!r} is not a recognised prime "
        f"setting; expected one of {tuple(_PRIME)} (or unset for "
        f"{'off'!r})."
    )

#: True when the first-wall geometry pair is primed at the sweep head.
PRIME_FW_GEOMETRY: bool = _PRIME[PRIME_NAME]

#: Invocation counter the runners read (the NODE_CALLS pattern: a one-cell
#: list, so a reader holds the live cell and not a stale int).  Incremented
#: only when the prime actually executes; stays 0 with the switch off.
PRIME_CALLS: list[int] = [0]


# --------------------------------------------------------------------------
# VP2 (framework hook F7b) -- the feed-forward tail runs once, after the
# fixed point, instead of on every sweep.
#
# Some model nodes feed nothing back: nothing they write is read by any model
# that runs before them inside the idempotence loop.  Running them on every
# sweep is wasted work -- their inputs are final only once the loop has
# settled, and their outputs affect nothing the loop is deciding.  The hoist
# defers them out of the sweep and runs them once, after ``call_models`` has
# reached its fixed point.
#
# ``off`` is the default and is upstream behaviour exactly: every node runs on
# every sweep, and the deferral list is never even created.
#
# The **node set is derived at run time, not hard-coded** (framework item
# C2a).  Membership comes from the committed DSM node map, so it follows the
# arm: when a later variant point lifts the burn-time coupler out of the loop,
# ``pulse`` joins the feed-forward tail and the derivation picks it up without
# a list edit here.  What *is* fixed in this file is which call sites were
# made deferrable at all; ``_HOIST_UNCOVERED`` below turns a node that should
# be hoisted but has no deferrable call site into an import-time error rather
# than a silent in-loop evaluation.
_HOIST_MODULES: dict[str, frozenset[str]] = {
    "off": frozenset(),
    "feedforward": frozenset({"FF"}),
    # FF, plus the burn-time articulation point once it has been lifted.
    "feedforward_lifted": frozenset({"FF", "PULSE"}),
}

#: Hoist arms that additionally require a lifted site, and which one.
#:
#: Plan §4.1d: once the burn time is a design variable, ``Pulse``'s burn-time
#: write is a no-op (``subsolve`` returns the design variable untouched) and
#: the only other field it writes on the pulsed decks,
#: ``constraints.t_current_ramp_up_min``, is read by a constraint equation and
#: by **no model**.  So post-lift ``pulse`` has no feedback into the MDA and
#: should run once per optimiser evaluation rather than once per sweep.  This
#: is the VP2 x VP5 composition the framework predicted and flagged as a latent
#: defect that fires only when two arms compose; it never fired because the
#: hoist keyed on the static node-map label and ``pulse`` is labelled
#: ``PULSE``.
#:
#: It is its **own arm name** rather than an automatic consequence of turning
#: the lift on, for two reasons.  A comparison must be able to vary one thing:
#: ``feedforward`` and ``feedforward_lifted`` with the same lift setting differ
#: only in whether ``pulse`` leaves the sweep, which is what makes the gate
#: below a one-variable comparison.  And an arm that silently changes meaning
#: with an unrelated environment variable is the failure mode this file already
#: refuses elsewhere.
_HOIST_REQUIRES_LIFT: dict[str, str] = {
    "feedforward_lifted": subsolve.SITE_BURN_TIME,
}

HOIST_NAME: str = os.environ.get("PROCESS_ARCH_HOIST", "").strip() or "off"

if HOIST_NAME not in _HOIST_MODULES:
    raise RuntimeError(
        f"PROCESS_ARCH_HOIST={HOIST_NAME!r} is not a recognised hoist "
        f"setting; expected one of {tuple(_HOIST_MODULES)} (or unset for "
        f"{'off'!r})."
    )

_needs = _HOIST_REQUIRES_LIFT.get(HOIST_NAME)
if _needs and not subsolve.is_lifted(_needs):
    raise RuntimeError(
        f"PROCESS_ARCH_HOIST={HOIST_NAME!r} hoists the burn-time articulation "
        f"point out of the sweep, which is only correct once that site is "
        f"lifted: with PROCESS_ARCH_LIFT={_needs!r} unset, Pulse still solves "
        f"the burn time in the model and the loop would stop updating it.  "
        f"Set PROCESS_ARCH_LIFT={_needs}, or use PROCESS_ARCH_HOIST=feedforward."
    )

#: Node-map modules whose nodes are deferred out of the sweep.
HOIST_MODULES: frozenset[str] = _HOIST_MODULES[HOIST_NAME]

#: True when any node is hoisted.  With the hoist off this guards every branch
#: the variant point adds, so the default path is upstream's.
HOIST_ENABLED: bool = bool(HOIST_MODULES)

#: Call sites in :meth:`Caller._call_models_once` routed through
#: :meth:`Caller._node` and therefore capable of being deferred.  This is a
#: property of *this file*, not of the arm: it says which statements were
#: rewritten, not which nodes are hoisted.
DEFERRABLE_NODES: tuple[str, ...] = ("pulse", "water_use", "costs")

#: **The hoist is a routing rule, not an exclusion rule** (plan §4.1d/§4.1e).
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
#: in the loop            the node-map module is not hoisted by this arm
#: pre-predicate, once    hoisted, and the predicate layer reads something
#:                        it writes
#: post-predicate, once   hoisted, and it reads nothing the predicate does
#: =====================  ===============================================
#:
#: This **generalises A13's figure-of-merit guard and replaces it.**  A13 kept
#: ``costs`` inside the loop on decks whose figure of merit reads it, which is
#: correct but more conservative than necessary: the pre-predicate slot does
#: the same job by running the node once instead of every sweep, so the deck
#: keeps the saving without the staleness.
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
#: by the ``modules`` write census.  Read only when the hoist is on; never
#: read live from a generated artifact (trap T9).
NODE_WRITESET_PATH = (
    Path(__file__).resolve().parents[2]
    / "arch_surgery"
    / "docs"
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
    constraint side is the **whole** layer, not only the deck's ``icc``.

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
        raise RuntimeError(
            f"{obj_src} has no objective_function; the hoist's routing rule "
            f"cannot be derived and must not be guessed."
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
        raise RuntimeError(
            f"{obj_src}'s figure-of-merit chain did not parse; the hoist's "
            f"routing rule cannot be derived and must not be guessed."
        )
    v = _Reads()
    v.visit(ast.parse(con_src.read_text(), filename=str(con_src)))
    fields.update(v.reads)
    return frozenset(fields)


def _node_write_sets() -> dict[str, frozenset[str]]:
    """Per-node write sets from the committed census."""
    if not NODE_WRITESET_PATH.exists():
        raise RuntimeError(
            f"PROCESS_ARCH_HOIST={HOIST_NAME!r} needs the committed per-node "
            f"write sets at {NODE_WRITESET_PATH}, which is not present.  "
            f"Generate with arch_surgery/fixedpoint/gen_node_writesets.py."
        )
    raw = json.loads(NODE_WRITESET_PATH.read_text())["writes_by_node_union"]
    return {k: frozenset(v) for k, v in raw.items()}


#: Committed DSM node map (framework component C8).  Read only when the hoist
#: is on; never read live from the dependency-analysis repository (trap T9).
NODE_MAP_PATH = (
    Path(__file__).resolve().parents[2]
    / "arch_surgery"
    / "docs"
    / "data"
    / "dsm_node_map.json"
)


def _resolve_hoist_nodes() -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Nodes this arm hoists, and any it should hoist but cannot.

    Returns
    -------
    tuple
        ``(hoisted, uncovered)`` -- the deferrable nodes the node map assigns
        to a hoisted module, and the mapped nodes that a hoisted module claims
        but that have no deferrable call site.
    """
    if not HOIST_ENABLED:
        return (), ()
    if not NODE_MAP_PATH.exists():
        raise RuntimeError(
            f"PROCESS_ARCH_HOIST={HOIST_NAME!r} needs the committed DSM node "
            f"map at {NODE_MAP_PATH}, which is not present."
        )
    nodes = json.loads(NODE_MAP_PATH.read_text())["nodes"]
    hoisted = tuple(
        n for n in DEFERRABLE_NODES if nodes.get(n, {}).get("module") in HOIST_MODULES
    )
    uncovered = tuple(
        sorted(
            n
            for n, entry in nodes.items()
            if entry.get("module") in HOIST_MODULES
            and entry.get("in_call_models_once")
            and n not in DEFERRABLE_NODES
        )
    )
    return hoisted, uncovered


HOIST_NODES, _HOIST_UNCOVERED = _resolve_hoist_nodes()

if _HOIST_UNCOVERED:
    raise RuntimeError(
        f"PROCESS_ARCH_HOIST={HOIST_NAME!r} would hoist {list(_HOIST_UNCOVERED)}, "
        f"but those nodes have no deferrable call site in Caller."
        f"_call_models_once. Add them to DEFERRABLE_NODES and route their "
        f"call sites through Caller._node."
    )


def resolved_hoist_tails(i_figure_merit: int) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """``(pre_predicate, post_predicate)`` for a run using *i_figure_merit*.

    Every node the arm hoists is placed in one of the two slots by the routing
    rule: the predicate layer reads something it writes, or it does not.
    Nothing is dropped --- a hoisted node always runs exactly once.

    Public so that a measurement harness can record the tails a run resolved
    without reconstructing the rule.
    """
    if not HOIST_NODES:
        return (), ()
    reads = _predicate_read_fields(i_figure_merit)
    writes = _node_write_sets()
    pre, post = [], []
    for n in HOIST_NODES:
        (pre if (writes.get(n, frozenset()) & reads) else post).append(n)
    return tuple(pre), tuple(post)


def resolved_hoist_tail(i_figure_merit: int) -> tuple[str, ...]:
    """Every deferred node, pre-predicate group first.

    Kept because A13's harness records it.  Anything that has to place a node
    relative to the predicate evaluation must use :func:`resolved_hoist_tails`.
    """
    pre, post = resolved_hoist_tails(i_figure_merit)
    return pre + post


# --------------------------------------------------------------------------
# VP2c (task A33, V2 plan section 1 / Appendix A item 3a) -- the post-solve
# hoist: nodes whose outputs the optimiser never consumes leave the per-call
# path entirely.
#
# VP2 (above) moves a feed-forward node out of the sweep but still runs it
# once per optimiser evaluation.  VP2c goes further for the nodes that earn
# it: a node whose outputs reach NO objective read, NO active-constraint read
# and NO solve-phase model read cannot change anything the optimiser decides,
# so running it even once per call is pure cost.  Such nodes are excluded from
# every solve-phase sweep and executed **exactly once per run**, at the
# accepted optimum, before the output phase begins.
#
# Membership is **derived, not asserted**: the committed per-deck artifact
# ``arch_surgery/docs/data/postsolve_<scenario>.json`` is produced by
# ``arch_surgery/idf_probe/a33_postsolve.py classify`` from the deck's
# objective/constraint read sets (AST), the run-time write census and a
# backward crawl of the collapsed DSM, and is validated here on load:
#
# * ``nodes_sha256`` must match a recomputation over the load-bearing fields,
#   so a hand-edited artifact is refused rather than trusted;
# * the artifact must be for THIS deck -- ``i_figure_merit`` and the active
#   ``icc`` list are checked against the run's own numerics at first use,
#   because another deck's exclusion list is a silently wrong answer;
# * every listed node must exist in the committed node map as a
#   ``_call_models_once`` call site;
# * a node whose measured write set intersects the predicate layer's read set
#   (the deck's objective branch plus the whole constraint layer, the same
#   rule VP2's routing uses) is refused: that node is one the deck keeps
#   per-call, and excluding it would hand the optimiser a stale objective or
#   constraint vector -- the quiet wrong answer this file refuses everywhere.
#
# ``off`` (the variable unset) is the default and is byte-identical to the
# behaviour without this section -- gated against A32's record (protocol
# section 12), not asserted.
POST_SOLVE_PATH: str | None = os.environ.get("PROCESS_ARCH_POST_SOLVE") or None
POST_SOLVE_ENABLED: bool = POST_SOLVE_PATH is not None

if POST_SOLVE_ENABLED and not Path(POST_SOLVE_PATH).exists():
    raise RuntimeError(
        f"PROCESS_ARCH_POST_SOLVE={POST_SOLVE_PATH!r} does not exist.  There "
        f"is no default and no fallback: a run asked to exclude nodes must "
        f"refuse rather than silently run everything."
    )

#: Diagnostics for the run record.  Integer counts and names only.
POST_SOLVE_TOTALS: dict = {
    "artifact": POST_SOLVE_PATH,
    "nodes": None,                      # filled after validation
    "n_call_sites_suppressed": 0,       # solve-phase _node sites skipped
    "suppressed_by_node": {},
    "executed_once": None,              # set by write_output_files
    "validated": False,
}

_POST_SOLVE_CACHE: dict = {}


def _post_solve_nodes(data) -> frozenset[str]:
    """The validated exclusion set for this run.  Cached after first use.

    Validation needs the run's own deck (figure of merit, active constraint
    list), so it happens on the first ``call_models`` rather than at import.
    Every check refuses loudly; none falls back.
    """
    cached = _POST_SOLVE_CACHE.get("nodes")
    if cached is not None:
        return cached

    import hashlib  # noqa: PLC0415 - validation path only

    record = json.loads(Path(POST_SOLVE_PATH).read_text())
    if record.get("format") != "a33-postsolve-1":
        raise RuntimeError(
            f"post-solve artifact {POST_SOLVE_PATH} has format "
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
        raise RuntimeError(
            f"post-solve artifact {POST_SOLVE_PATH} does not rebuild: "
            f"nodes_sha256 is {rebuilt} recomputed against {committed} "
            f"recorded in the file.  The exclusion list would not be the "
            f"derived one."
        )

    # (2) the artifact must be for THIS deck.
    ifm = int(data.numerics.i_figure_merit)
    want_ifm = record["deck"]["i_figure_merit_expected"]
    if ifm != want_ifm:
        raise RuntimeError(
            f"post-solve artifact {POST_SOLVE_PATH} was derived for "
            f"i_figure_merit={want_ifm} but this run has {ifm}: wrong deck."
        )
    m_all = int(data.numerics.n_equality_constraints) + int(
        data.numerics.n_inequality_constraints
    )
    icc = sorted(int(v) for v in data.numerics.icc[:m_all])
    want_icc = sorted(record["deck"]["icc_expected_at_runtime"])
    if icc != want_icc:
        raise RuntimeError(
            f"post-solve artifact {POST_SOLVE_PATH} was derived for the "
            f"active constraint set {want_icc} but this run has {icc}: "
            f"wrong deck, or the deck changed under the artifact."
        )

    # (3) every listed node must be a known _call_models_once call site.
    if not NODE_MAP_PATH.exists():
        raise RuntimeError(
            f"PROCESS_ARCH_POST_SOLVE needs the committed DSM node map at "
            f"{NODE_MAP_PATH}, which is not present."
        )
    known = {
        n
        for n, e in json.loads(NODE_MAP_PATH.read_text())["nodes"].items()
        if e.get("in_call_models_once")
    }
    unknown = sorted(set(nodes) - known)
    if unknown:
        raise RuntimeError(
            f"post-solve artifact {POST_SOLVE_PATH} names {unknown}, which "
            f"are not _call_models_once call sites in the committed node map."
        )

    # (4) a node the deck keeps per-call is refused: its measured writes must
    # not intersect what the predicate layer reads for this figure of merit.
    scenario = record.get("scenario")
    per_scenario = json.loads(NODE_WRITESET_PATH.read_text())["per_scenario"]
    if scenario not in per_scenario:
        raise RuntimeError(
            f"post-solve artifact {POST_SOLVE_PATH} names scenario "
            f"{scenario!r}, which has no run-time write census in "
            f"{NODE_WRITESET_PATH}."
        )
    writes_by_node = per_scenario[scenario]["writes_by_node"]
    reads = _predicate_read_fields(ifm)
    for n in nodes:
        overlap = sorted(set(writes_by_node.get(n, ())) & reads)
        if overlap:
            raise RuntimeError(
                f"post-solve artifact {POST_SOLVE_PATH} lists {n!r}, but the "
                f"predicate layer reads {overlap[:5]} out of its measured "
                f"write set: this deck keeps {n!r} per-call, and excluding "
                f"it would hand the optimiser a stale objective or "
                f"constraint vector."
            )

    resolved = frozenset(nodes)
    _POST_SOLVE_CACHE["nodes"] = resolved
    POST_SOLVE_TOTALS["nodes"] = sorted(resolved)
    POST_SOLVE_TOTALS["validated"] = True
    POST_SOLVE_TOTALS["scenario"] = scenario
    POST_SOLVE_TOTALS["nodes_sha256"] = committed
    return resolved


# --------------------------------------------------------------------------
# VP4 (framework hook F7c) -- one flat loop, or a solve per module.
#
# Upstream runs the whole model sequence and tests two derived scalars for
# idempotence.  ``per_module`` instead iterates each DSM module to its own
# fixed point, in the block order A3's VP1 makes available by giving M1 a
# contiguous span, with an outer loop over whatever cross-module coupling
# remains.  The arm, its caps and its predicate live in
# ``process/core/solver/module_solve.py``; what lives here is the schedule and
# the node filter, because those are properties of *this* call sequence.
#
# ``flat_state`` is the same predicate on **one block containing every in-loop
# node** --- decision D18's predicate-matched control ``A0'``.  It exists so
# that the two things ``R -> A1'`` measures as a sum, the stopping rule and the
# architecture, can be measured apart: ``R -> A0'`` is the predicate alone and
# ``A0' -> A1'`` is the architecture alone.
#
# ``off`` is the default and is upstream behaviour exactly: ``_active_nodes``
# stays ``None``, every node runs on every sweep, and ``call_models`` never
# enters the block path.
MODULE_SOLVE_NAME: str = module_solve.MODULE_SOLVE_NAME
MODULE_SOLVE_ENABLED: bool = module_solve.ENABLED

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
#: I-17: the A→B transfer over-predicts B3's saving on all three decks
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
_SWEEP_CALLS: list[int] = [0]

#: :data:`NODE_CALLS` at the moment the final-output path is entered.  The
#: cost figure Phase B compares is the **solve** phase: everything before
#: ``write_output_files``.  The output phase re-enters every model's ``run()``
#: from its ``output()`` (trap T7) and is identical work in both arms, so
#: pooling it into the cost would dilute the very quantity being compared.
NODE_CALLS_AT_OUTPUT: list[int | None] = [None]

#: Roll-up of the block schedule's own counts across every ``call_models`` of a
#: run.  Diagnostics: reported beside the cost figure, never gated on.
MODULE_SOLVE_TOTALS: dict = {
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


def _resolve_node_modules() -> dict[str, str]:
    """``node -> DSM module`` from the committed node map.

    Read only when VP4 is on, from the same committed artifact the hoist uses
    and never live from the dependency-analysis repository (trap T9).
    """
    if not MODULE_SOLVE_ENABLED:
        return {}
    if not NODE_MAP_PATH.exists():
        raise RuntimeError(
            f"PROCESS_ARCH_MODULE_SOLVE={MODULE_SOLVE_NAME!r} needs the "
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
    """``((label, frozenset(nodes), iterate), ...)`` for one run's outer pass.

    Membership comes from the committed node map, so a node that this deck
    never executes simply never appears -- the filter in :meth:`Caller._node`
    is a predicate on names, not a list of calls to make.

    **The hoist composes here, and that composition is the thing to get
    right.**  With VP2 on, every deferred node is removed from its block and
    returned as the tail, to be run once after the outer fixed point --- both
    slots, because a per-module schedule's outer test is on the coupling state
    and not on ``objf``/``conf``, so nothing here is at risk of reading a
    stale predicate input.  The **placement** of the two groups relative to
    the predicate evaluation is ``call_models``'s business, not the
    schedule's; :func:`resolved_hoist_tails` is the one place that decides
    which group a node is in.

    Returns
    -------
    tuple
        ``(schedule, tail)`` -- the blocks of one outer pass, and the nodes
        deferred to after the fixed point (empty when VP2 is off).
    """
    tail = (
        frozenset(resolved_hoist_tail(i_figure_merit))
        if HOIST_ENABLED
        else frozenset()
    )
    # ``flat_state`` (decision D18's control arm A0') is one block over every
    # in-loop node: the same predicate, the same caps, the same failure policy,
    # a different schedule.  It is written as a branch here rather than as a
    # second solver because A26 §10 measured that it is the degenerate case of
    # the block schedule, and two implementations of one loop is how they
    # drift.
    if module_solve.FLAT_STATE:
        return (
            (module_solve.FLAT_BLOCK_LABEL, _loop_node_set(tail), True),
        ), tail
    by_module: dict[str, set[str]] = {}
    for node, mod in NODE_MODULE.items():
        by_module.setdefault(mod, set()).add(node)
    schedule = []
    for label in module_solve.BLOCK_ORDER:
        nodes = frozenset(by_module.get(label, set()) - tail)
        schedule.append((label, nodes, label in module_solve.ITERATED))
    return tuple(schedule), tail


def _loop_node_set(tail=()) -> frozenset[str]:
    """Every node a block schedule may run, less the hoisted tail.

    Restricted to the labels :data:`module_solve.BLOCK_ORDER` names, so the
    single-block arm covers **exactly** what the per-module arm's blocks cover
    between them --- which is what makes ``A0' -> A1'`` a comparison of the
    schedule and not of the model set.  The node map also carries
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
    """Does one iterated block hold every node the loop would sweep?

    When it does, the outer residual test is **redundant with the block's own
    inner test** and skipping it is a correctness statement, not an
    optimisation.  The inner test compares two successive sweeps of that block
    over the whole coupling vector; the outer test asks the same question of
    the same index set.  Paying it anyway costs exactly one extra full sweep
    per ``call_models``, because ``y_outer_prev`` is the state at *entry*: pass
    1 compares the entry state against the converged one and fails, pass 2
    re-runs the block (one sweep, converging immediately) and passes.

    Measured on the block arm as the wasted-pass effect A0f -> A0, 1.53-1.79 %
    of model evaluations (A18/A26).  Recorded per call rather than assumed, so
    a schedule that stops satisfying the condition stops taking the guard.
    """
    live = [(lab, nodes, it) for lab, nodes, it in schedule if nodes]
    if len(live) != 1:
        return False
    _lab, nodes, iterate = live[0]
    return bool(iterate) and nodes == _loop_node_set(tail)


def _roll_up(stats: dict) -> None:
    """Fold one ``call_models``'s block counts into the run's totals."""
    t = MODULE_SOLVE_TOTALS
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
    if stats.get("single_block_outer_test_skipped"):
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
        # hoist-off path ever sees.
        self._pending: list | None = None
        # VP2: the tail resolved for the current ``call_models``.  Re-resolved
        # on every call rather than memoised: it depends on the deck's figure
        # of merit, and a scan may change the deck between calls.
        self._hoist_tail: frozenset[str] = frozenset()
        # VP2 / plan §4.1d: the deferred nodes split into a group that runs
        # before ``objf``/``conf`` and one that runs after.  Both empty on the
        # default path.
        self._hoist_pre: frozenset[str] = frozenset()
        self._hoist_post: frozenset[str] = frozenset()
        # VP2c (A33): the post-solve exclusion set for the current
        # ``call_models``, or ``None`` when nothing is excluded.  ``None`` is
        # the default and the only value the switch-off path ever sees; it is
        # also what the output-phase and audit Callers keep, because they
        # never enter ``call_models`` -- which is what lets the one-shot
        # post-solve execution and the exit audit run the very nodes the
        # solve phase excluded.
        self._post_solve: frozenset[str] | None = None
        # VP4: the nodes the current block sweep may run, or ``None`` when the
        # whole sequence runs.  ``None`` is the default and the only value the
        # flat-loop path ever sees.
        self._active_nodes: frozenset[str] | None = None
        # VP4: the coupling-state spec, the per-module subsets its inner
        # solves test, and their provenance.  Loaded once.
        self._yspec = None
        self._yprov = None
        self._ysubsets: dict | None = None
        #: VP4 diagnostics for the last ``call_models`` -- block sweeps, outer
        #: passes and inner counts.  Reported, never gated on.
        self.module_solve_stats: dict | None = None
        # A34 (pin instrument): the burn-time coupling held at the
        # env-supplied value, written once here -- "fixed at initialisation"
        # -- and never overwritten during the solve phase (the tripwire at the
        # end of ``_call_models_once`` raises on any bit-level change).  With
        # PROCESS_ARCH_PIN_BURN_TIME unset this branch is dead and nothing
        # differs from upstream.
        if subsolve.PIN_ENABLED:
            self._apply_burn_time_pin()

    def _apply_burn_time_pin(self) -> None:
        """Write the pinned burn time into the data structure, refusing decks
        that would fight over it.

        The pin replaces the optimiser as the variable's owner (the lifted
        architecture's per-call structure without an optimiser -- V2 plan
        section 3).  A deck that names ``ixc = 178`` hands the same variable
        to the design-vector injection at the head of every sweep, which
        would silently overwrite the pin; two owners is a refusal, not a
        race.
        """
        nums = self.data.numerics
        n = int(nums.n_iteration_variables)
        ixc = [int(v) for v in nums.ixc[:n]]
        if subsolve.BURN_TIME_IXC in ixc:
            raise RuntimeError(
                f"PROCESS_ARCH_PIN_BURN_TIME={subsolve.PIN_BURN_TIME!r} is "
                f"set, but this deck names ixc = {subsolve.BURN_TIME_IXC} "
                f"(the lifted burn time), so the design-vector injection at "
                f"the head of every sweep would overwrite the pin.  The pin "
                f"replaces the optimiser as the variable's owner: run it on "
                f"a deck without ixc = {subsolve.BURN_TIME_IXC}."
            )
        self.data.times.t_plant_pulse_burn = subsolve.PIN_BURN_TIME

    # -- VP2 -------------------------------------------------------------

    def _resolve_hoist_tails(self) -> tuple[frozenset[str], frozenset[str]]:
        """``(pre_predicate, post_predicate)`` for this run.

        ``call_models`` stops on ``objf`` and ``conf``, so a node whose output
        the predicate layer reads cannot run *after* they are evaluated --- the
        optimiser would get a constraint vector built from a stale value.  It
        runs **once, before** them, on the converged state.  Everything else
        runs once after, as A13 built it.  Either way the node leaves the
        sweep, which is where the saving is.
        """
        if not HOIST_ENABLED:
            return frozenset(), frozenset()
        pre, post = resolved_hoist_tails(self.data.numerics.i_figure_merit)
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
           block does not run at all.  This is checked first, so the hoist
           never collects a node during someone else's block.
        2. **VP2c** -- a node in the validated post-solve set does not run in
           any solve-phase sweep at all; it runs once per run, at the accepted
           optimum (``write_output_files``).  Checked before VP2's collection
           so an excluded node is never gathered into the per-call tail
           either.  ``_post_solve`` is set only inside ``call_models``, so the
           output path and the exit audit -- which call
           ``_call_models_once`` on their own Callers -- still run everything.
        3. **VP2** -- a node in the resolved feed-forward tail is collected
           instead of run.  The block path never sets ``_pending``, because
           under VP4 the tail is a block of its own that runs once after the
           outer fixed point; this branch is the flat arm's.
        4. Otherwise the node runs, and is counted.
        """
        if self._active_nodes is not None and name not in self._active_nodes:
            return
        if self._post_solve is not None and name in self._post_solve:
            POST_SOLVE_TOTALS["n_call_sites_suppressed"] += 1
            by = POST_SOLVE_TOTALS["suppressed_by_node"]
            by[name] = by.get(name, 0) + 1
            return
        if self._pending is not None and name in self._hoist_tail:
            self._pending.append((name, run))
            return
        NODE_CALLS[0] += 1
        run()

    def _run_hoisted_tail(self, pending: list) -> None:
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

    def _call_models_by_module(
        self, xc: np.ndarray, m: int
    ) -> tuple[float, np.ndarray]:
        """Block Gauss-Seidel over the DSM modules, then objective and constraints.

        Each iterated block is solved to its own fixed point on the coupling
        state before the next block runs; an outer loop closes the cross-module
        coupling.  The predicate is Phase A's, on ``y``, at ``tau`` -- never
        ``objf``/``conf``, which no single module determines (D14(c)).

        Raises
        ------
        ModuleSolveFailure
            if an inner solve, the outer loop or the global block budget hits
            its cap.  Decision **D15(d)**: a failed per-module solve raises and
            counts as a failed start, so the arms' failure modes are comparable.
        """
        if self.data.stellarator.istell != 0 or self.data.ife.ife != 0:
            raise module_solve.ModuleSolveFailure(
                "PROCESS_ARCH_MODULE_SOLVE is a tokamak-only variant point: "
                "the stellarator and IFE paths return from _call_models_once "
                "before any node the DSM partition names, so a block schedule "
                "over them would be a schedule over nothing."
            )

        if self._yspec is None:
            self._yspec, self._yprov = module_solve.load_spec()
            self._ysubsets, _ = module_solve.load_subsets(self._yspec)
        spec = self._yspec
        subsets = self._ysubsets
        tau = module_solve.TAU

        inner_tau = module_solve.INNER_TAU

        schedule, tail = module_schedule(self.data.numerics.i_figure_merit)
        # A26 §10, item 1: with one block covering every in-loop node the outer
        # residual test asks exactly what the block's own inner test has just
        # answered, and paying it costs one extra full sweep per call.  The
        # condition is evaluated from the schedule that was actually built, not
        # from the arm name, so an arm whose schedule stops being a single
        # block stops taking the guard.
        single_block = _single_block_covers_loop(schedule, tail)
        bound = spec.bind(self.data)
        read = spec.read

        # VP4 never uses VP2's deferral list: under a block schedule the tail
        # is a block, run once after the outer fixed point.
        self._pending = None

        # A31 (drift-diagnostic): the joint-test trace's call index.  With
        # PROCESS_ARCH_PASS_TRACE unset TRACE_ENABLED is False, the index is
        # never computed and no hook below runs — neutrality is gated against
        # A28's recorded counts (protocol §12), not asserted.
        trace_call = (
            MODULE_SOLVE_TOTALS["n_call_models"] + 1
            if module_solve.TRACE_ENABLED
            else 0
        )

        y_outer_prev = read(bound)
        block_sweeps = 0
        inner_counts: dict[str, list[int]] = {lab: [] for lab, _n, _i in schedule}
        outer_trace: list[dict] = []
        moved_constants: set = set()

        def charge() -> None:
            nonlocal block_sweeps
            block_sweeps += 1
            if block_sweeps > module_solve.GLOBAL_BLOCK_SWEEP_CAP:
                raise module_solve.ModuleSolveFailure(
                    f"global block-sweep cap "
                    f"({module_solve.GLOBAL_BLOCK_SWEEP_CAP}) reached at "
                    f"tau={tau:g}"
                )

        converged = False
        outer = 0
        for outer in range(1, module_solve.OUTER_CAP + 1):
            for label, nodes, iterate in schedule:
                if not nodes:
                    inner_counts[label].append(0)
                    continue
                if not iterate:
                    charge()
                    self._sweep_block(xc, nodes)
                    inner_counts[label].append(1)
                    continue
                # The inner test is restricted to the module's own write set,
                # as Phase A's block arm restricts it.  Not an optimisation:
                # ``ystate``'s predicate scores any component that is not
                # float-viewable in *either* snapshot as ``inf``, and in a
                # fresh process that is every field no model has written yet --
                # so an unrestricted inner test is held open for ever by a
                # field the running module cannot touch.
                subset = subsets.get(label)
                y_prev = read(bound)
                inner_ok = False
                s = 0
                for s in range(1, module_solve.INNER_CAP + 1):
                    charge()
                    self._sweep_block(xc, nodes)
                    y = read(bound)
                    res = spec.residual(y_prev, y, subset=subset)
                    moved_constants |= {
                        spec.name(i) for i in res.moved_constant
                    }
                    # A31: under the single-block guard the outer test below
                    # is skipped, so THIS residual is the joint test — the
                    # flat arm's movement lives here.  Full snapshots: the
                    # single block has no subset in the write-set artifact.
                    if module_solve.TRACE_ENABLED and single_block:
                        module_solve.trace_pass(
                            "flat_inner", trace_call, s, spec, y_prev, y,
                            res, tau,
                        )
                    y_prev = y
                    if res.converged(inner_tau):
                        inner_ok = True
                        break
                inner_counts[label].append(s)
                if not inner_ok:
                    self.module_solve_stats = self._module_stats(
                        block_sweeps, outer, inner_counts, outer_trace,
                        moved_constants, converged=False, cap_hit="inner",
                        tail=tail, single_block=single_block,
                        inner_tau=inner_tau,
                    )
                    _roll_up(self.module_solve_stats)
                    raise module_solve.ModuleSolveFailure(
                        f"module {label} did not converge in "
                        f"{module_solve.INNER_CAP} inner sweeps at "
                        f"inner_tau={inner_tau:g}; max scaled residual "
                        f"{res.max:g} on {res.brief(inner_tau)['argmax']}, "
                        f"{res.n_above(inner_tau)} components above inner_tau"
                    )
            if single_block:
                # The block's own inner test has just compared two successive
                # full sweeps over the whole coupling vector at ``tau``.  The
                # outer test would compare the same index set by the same rule;
                # running it compares the *entry* state instead and therefore
                # always fails once, buying one wasted sweep.
                converged = True
                break
            # A34 (trust mode): with PROCESS_ARCH_OUTER=trust the schedule has
            # now run exactly once -- every iterated block converged at its
            # own inner tolerance -- and the outer joint predicate below is
            # never evaluated: no outer pass 2, no verification receipt.
            # ``outer`` stays 1, so the run record's outer_pass_hist shows
            # {1: n} and a tally can see the mode.  Whether the feed-forward
            # assertion held is measured by the uncharged exit audit, outside
            # the arm.  With the variable unset TRUST_OUTER is False and this
            # is one attribute read per outer pass -- neutrality gated against
            # A32's record (protocol 12), not asserted.
            if module_solve.TRUST_OUTER:
                converged = True
                break
            y = read(bound)
            res = spec.residual(y_outer_prev, y)
            outer_trace.append(res.brief(tau))
            moved_constants |= {spec.name(i) for i in res.moved_constant}
            # A31 (drift-diagnostic): record this joint-test evaluation —
            # which components moved past tau across the pass, before/after
            # as hex floats — before y_outer_prev is overwritten.
            if module_solve.TRACE_ENABLED:
                module_solve.trace_pass(
                    "outer", trace_call, outer, spec, y_outer_prev, y,
                    res, tau,
                )
            y_outer_prev = y
            if res.converged(tau):
                converged = True
                break

        if not converged:
            self.module_solve_stats = self._module_stats(
                block_sweeps, outer, inner_counts, outer_trace,
                moved_constants, converged=False, cap_hit="outer", tail=tail,
                single_block=single_block, inner_tau=inner_tau,
            )
            _roll_up(self.module_solve_stats)
            raise module_solve.ModuleSolveFailure(
                f"the outer loop over modules did not converge in "
                f"{module_solve.OUTER_CAP} passes at tau={tau:g}"
            )

        # VP2 inside VP4: the feed-forward tail runs once, on the converged
        # state.  Charged like any other block sweep.
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
            block_sweeps, outer, inner_counts, outer_trace, moved_constants,
            converged=True, cap_hit=None, tail=tail,
            single_block=single_block, inner_tau=inner_tau,
        )
        _roll_up(self.module_solve_stats)
        return objf, conf

    @staticmethod
    def _module_stats(
        block_sweeps, outer, inner_counts, outer_trace, moved_constants,
        *, converged, cap_hit, tail, single_block=False, inner_tau=None,
    ) -> dict:
        """The block schedule's own counts, for the run record."""
        return {
            "converged": converged,
            "cap_hit": cap_hit,
            "single_block_outer_test_skipped": bool(single_block),
            "inner_tau": inner_tau,
            "block_sweeps": block_sweeps,
            "outer_passes": outer,
            "inner_counts": {k: list(v) for k, v in inner_counts.items()},
            "inner_totals": {k: sum(v) for k, v in inner_counts.items()},
            "outer_residual_trace": outer_trace,
            "moved_constants": sorted(moved_constants),
            "hoisted_tail": sorted(tail),
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
        _sweeps_at_entry = _SWEEP_CALLS[0]
        try:
            return self._call_models_inner(xc, m)
        finally:
            _n = _SWEEP_CALLS[0] - _sweeps_at_entry
            _k = str(_n)
            SWEEPS_PER_EVAL_HIST[_k] = SWEEPS_PER_EVAL_HIST.get(_k, 0) + 1

    def _call_models_inner(self, xc: np.ndarray, m: int) -> tuple[float, np.ndarray]:
        """The body of :meth:`call_models`; see it for the contract.

        Split out only so the I-17 sweep histogram can bin on every exit path
        without wrapping the body in an indent-changing ``try``.  No behaviour
        of its own.
        """
        # VP2c: resolve (and on first use validate) the post-solve exclusion
        # set.  With the switch off ``_post_solve`` stays ``None`` and nothing
        # below this line differs.
        if POST_SOLVE_ENABLED:
            self._post_solve = _post_solve_nodes(self.data)

        # VP4: the block schedule replaces the flat loop entirely -- including
        # its predicate, which decision D14(c) requires: a per-module solver
        # cannot test a global objective, because one module does not determine
        # it.  With VP4 off nothing below this line differs from upstream.
        if MODULE_SOLVE_ENABLED:
            objf, conf = self._call_models_by_module(xc, m)
            if _idf_probe.ENABLED:
                _idf_probe.call_models_end()
            return objf, conf

        objf_prev = None
        conf_prev = None

        # VP2: with the hoist on, the feed-forward nodes are collected instead
        # of run, and the last sweep's collection is run once the loop has
        # settled.  With the hoist off ``_pending`` stays ``None`` and nothing
        # below this line differs from upstream.
        if HOIST_ENABLED:
            self._hoist_pre, self._hoist_post = self._resolve_hoist_tails()
            self._hoist_tail = self._hoist_pre | self._hoist_post
            pending: list | None = [] if self._hoist_tail else None
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
            if self.check_agreement(objf_prev, objf) and self.check_agreement(
                conf_prev, conf
            ):
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
                    pre = [t for t in pending if t[0] in self._hoist_pre]
                    post = [t for t in pending if t[0] not in self._hoist_pre]
                    if pre:
                        self._run_hoisted_tail(pre)
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
                        self._run_hoisted_tail(post)
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

        # VP2: the hoist applies to the optimiser's evaluation path only.
        # This is the final-output path, where ``models.write`` re-enters every
        # model's ``run()`` from its ``output()`` anyway (trap T7), so nothing
        # is deferred here.
        self._pending = None

        try:  # noqa: PLW0717
            # Evaluate models up to 10 times; any more implies non-converging values
            for _ in range(10):
                # Divert OUT.DAT and MFILE.DAT output to scratch files for
                # idempotence checking
                OutputFileManager.open_idempotence_files(self.data.globals.output_prefix)
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
        _SWEEP_CALLS[0] += 1

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

        # VP6 (D19, task A40): prime the first-wall geometry pair at the
        # head of the sweep, so Build (which the schedule runs before
        # FirstWall) reads this pass's value instead of the previous
        # pass's.  Not a node, not routed through _node, not counted in
        # NODE_CALLS -- stamped via PRIME_CALLS (see the module-level
        # comment).  Because it sits here, it is on every path that walks
        # the model sequence: the flat loop, every VP4 block sweep
        # (Caller._sweep_block runs blocks through this method), the
        # output phase and the exit audit (harmless, idempotent -- the
        # write is the same run-constant every time).
        if PRIME_FW_GEOMETRY:
            PRIME_CALLS[0] += 1
            self.models.fw.set_fw_geometry()

        # Tokamak calls
        # Plasma geometry model, machine build model (radial build) and
        # physics.  Their relative order is the VP1 variant point; see
        # SEQUENCE_HEAD at module level.  With PROCESS_ARCH_SEQUENCE unset
        # this is plasma_geom, build, physics -- the upstream order.
        for _head_node in SEQUENCE_HEAD:
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
        # burn-time coupler is lifted out of the loop.
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

        # A34 (pin instrument): the tripwire.  A pinned burn time that any
        # model call moved is named at the sweep that moved it -- a check,
        # never a re-pin, because re-forcing the value would mask the writer.
        # Dead branch with the pin unset.
        if subsolve.PIN_ENABLED:
            subsolve.assert_burn_time_pinned(self.data)

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
    # arms; see NODE_CALLS_AT_OUTPUT.
    if NODE_CALLS_AT_OUTPUT[0] is None:
        NODE_CALLS_AT_OUTPUT[0] = NODE_CALLS[0]
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
    # ``caller`` here never enters ``call_models``, so its ``_post_solve`` is
    # ``None`` and the exclusion does not apply to this sweep -- nor to the
    # output phase below, which re-runs every model to MFILE idempotence
    # exactly as upstream does.
    if POST_SOLVE_ENABLED:
        ps = _post_solve_nodes(data)
        POST_SOLVE_TOTALS["executed_once"] = sorted(ps)
        POST_SOLVE_TOTALS["executed_once_at_node_calls"] = NODE_CALLS[0]
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
