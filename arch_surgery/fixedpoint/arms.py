"""The four arms, built from the node map and the measured node order.

======  ==========================================================  ==========
arm     what it is                                                  role
======  ==========================================================  ==========
R       ``Caller.call_models`` unmodified                           reference
A0      flat Gauss-Seidel over all in-loop nodes, floor 1           control
A0f     A0 with the floor kept at 2                                 isolator
A1      block: outer over the coupler, inner per M1 / M2 / M3       treatment
======  ==========================================================  ==========

R is a **reference, not a competitor**.  It measures two things at once -- the
size of the two-sweep artefact, and what the loose ``objf``/``conf`` predicate
lets through -- and those two act in opposite directions.  ``R -> A0f`` is the
predicate's cost alone, ``A0f -> A0`` is the floor removal alone, and
``R -> A0`` can only ever report their sum.  Without A0f a near-zero sum is
indistinguishable from neither effect existing.

**The feed-forward hoist is a toggle applied to every arm**, so that in the
first results it cancels and the comparison is purely topological.  When it is
on, the tail runs **once after the outer fixed point has converged** -- not
after each inner solve, which would put feed-forward work inside the loop it
was hoisted out of.

A26: the hoisted set is a property of the arm, not of the node map
------------------------------------------------------------------

A18 derived the hoisted set from the **static** node-map label alone: every
node labelled ``FF`` left the loop, whatever the deck or the arm.  That is
wrong in two measured ways, and both are now fixed here.

**The rule is *routing*, not exclusion, and it is keyed on measured read
sets.**  PROCESS's loop stops on ``objf`` and ``conf``, so what makes a node
unsafe to defer is that the **predicate layer** --- the objective *or* the
constraint layer --- reads something it writes.  A18 had no such rule at all;
A13 had one for the objective side only, and handled it by keeping the node
**in the loop**, which is correct but more conservative than necessary.  Plan
§4.1d/§4.1e replaces both with three slots:

======================  ==================================================
slot                    membership
======================  ==================================================
in the loop             the node feeds an in-loop model (node-map label
                        neither ``FF`` nor, post-lift, ``PULSE``)
pre-predicate, once     it does not, **but** the predicate layer reads
                        something it writes --- run once on the converged
                        state, *before* ``objf`` / ``conf``
post-predicate, once    neither --- run once, *after* ``conf``
======================  ==================================================

A node in the pre-predicate slot still leaves the sweep: it runs once per
optimiser evaluation instead of once per sweep, which is the whole saving.
What it does not do is let the predicate see a stale value.  Two consequences
worth naming:

* **I-13 closes on the decks it bound.**  On ``large_tokamak_eval`` (figure of
  merit 7, ``costs.cdirt`` / ``costs.concost``) A13's driver kept ``costs``
  inside the loop and A18's engine hoisted it anyway, so the two instruments
  measured two architectures.  Under the routing rule both put it in the
  pre-predicate slot and agree.
* **``pulse`` leaves the MDA under the lift** (plan §4.1d).  Post-lift its
  burn-time write is a no-op and its only other write on the pulsed decks,
  ``constraints.t_current_ramp_up_min``, is read by a constraint equation and
  by **no model**.  It is *not* feed-forward in the sense ``water_use`` is ---
  its output is consumed, by the predicate layer --- so it goes pre-predicate,
  never post.  Putting it after ``conf`` would hand the optimiser a constraint
  vector built from a stale value: a small, plausible, wrong ``conf``, the
  hardest kind of defect to catch.

The read set is measured in :mod:`fixedpoint.predicate_reads` --- exact on the
objective side (the active figure of merit's own branch) and a superset on the
constraint side (every registered constraint, not only the deck's ``icc``).
Over-reporting routes a node to the pre-predicate slot, which is never wrong.
"""

from __future__ import annotations

#: Order the blocks take in the partitioned sequence: all of M1, then all of
#: M2, then the articulation point, then M3, then the feed-forward tail.
BLOCK_ORDER = ("M1", "M2", "PULSE", "M3", "FF")

#: Blocks that are iterated to their own fixed point.  ``PULSE`` is a single
#: node and ``FF`` feeds nothing back, so an inner solve on either would be a
#: pass with a foregone answer.
ITERATED = {"M1", "M2", "M3"}

ARMS = ("R", "A0", "A0f", "A1")

#: Sentinel for ``routing``: run with **no** predicate-layer guard, which is
#: what A18, A22 and A23 did --- every ``FF`` node goes to the post-predicate
#: slot regardless of what reads it.  It exists so their recorded artifacts
#: stay reproducible and so that a caller has to *say* it is running unguarded;
#: :func:`describe` records it in every artifact.  It is not a default anybody
#: should reach for.
UNGUARDED = None


class Routing:
    """The measured inputs the pre/post-predicate routing rule needs.

    ``predicate_reads``
        ``{"namespace.field"}`` the objective or the constraint layer reads,
        from :mod:`fixedpoint.predicate_reads`.
    ``writes_by_node``
        ``{node: ["namespace.field", ...]}``, straight from the harvest, so the
        rule is keyed on what a node was *measured* to write rather than on a
        label somebody assigned it.
    """

    def __init__(self, predicate_reads, writes_by_node):
        self.predicate_reads = frozenset(predicate_reads)
        self.writes_by_node = {k: frozenset(v or ()) for k, v in
                               writes_by_node.items()}

    def feeds_predicate(self, node: str) -> frozenset:
        """The fields *this* node writes that the predicate layer reads."""
        return self.writes_by_node.get(node, frozenset()) & self.predicate_reads

    def describe(self) -> dict:
        return {
            "n_predicate_read_fields": len(self.predicate_reads),
            "n_nodes_with_write_sets": len(self.writes_by_node),
        }


def hoist_split(node_order, node_module, *, hoist: bool, routing=UNGUARDED,
                lift: bool = False):
    """``(loop_nodes, pre_predicate_tail, post_predicate_tail)``.

    The single place the arm's node partition is decided.  ``loop_nodes`` is
    what a sweep runs; the two tails run once each, in the order named --- the
    pre-predicate group before ``objf`` / ``conf`` are evaluated, the
    post-predicate group after.

    ``<x_inject>`` is not a node: it is the design-vector injection, which
    every pass performs at its head.
    """
    loop, pre, post = [], [], []
    for n in node_order:
        if n == "<x_inject>":
            continue
        mod = node_module.get(n)
        hoistable = hoist and (mod == "FF" or (lift and mod == "PULSE"))
        if not hoistable:
            loop.append(n)
        elif routing is not None and routing.feeds_predicate(n):
            pre.append(n)
        else:
            post.append(n)
    return loop, pre, post


def loop_nodes(node_order, node_module, *, hoist: bool, routing=UNGUARDED,
               lift: bool = False):
    """The nodes inside the loop, in driver order."""
    return hoist_split(node_order, node_module, hoist=hoist,
                       routing=routing, lift=lift)[0]


def hoisted_nodes(node_order, node_module, *, hoist: bool, routing=UNGUARDED,
                  lift: bool = False):
    """Every hoisted node, pre-predicate group first.

    Kept for callers that only need "what left the loop"; anything that has to
    place the nodes relative to the predicate evaluation must use
    :func:`hoist_split` instead.
    """
    _loop, pre, post = hoist_split(node_order, node_module, hoist=hoist,
                                   routing=routing, lift=lift)
    return pre + post


def build_blocks(node_order, node_module, y_index_of_node, *, hoist: bool,
                 routing=UNGUARDED, lift: bool = False):
    """``[(label, nodes, y_subset, iterate), ...]`` for the block arm.

    Built from :func:`hoist_split`'s loop set, so the block arm and the flat
    arm provably run the same nodes: a node either tail takes is in no block,
    and a node the loop keeps is in one.
    """
    loop, pre, post = hoist_split(node_order, node_module, hoist=hoist,
                                  routing=routing, lift=lift)
    in_loop = set(loop)
    hoisted = set(pre) | set(post)
    blocks = []
    for label in BLOCK_ORDER:
        labelled = [
            n for n in node_order
            if n != "<x_inject>" and node_module.get(n) == label
        ]
        nodes = [n for n in labelled if n in in_loop]
        if labelled and not nodes and set(labelled) <= hoisted:
            # The block had nodes and the hoist took all of them, so it is not
            # part of this arm's schedule at all.  Dropped rather than kept as
            # an empty block, which is what A18 did for FF and what its
            # recorded artifacts contain --- the schedule is the arm, and a
            # block with nothing in it is not one.
            continue
        if not nodes:
            # e.g. PULSE under i_pulsed_plant = 0 in a deck where the node
            # still executes but writes nothing -- kept as an empty block so
            # the schedule shape is the same and the k = 0 case is visible.
            blocks.append((label, [], set(), False))
            continue
        subset = set()
        for n in nodes:
            subset |= y_index_of_node.get(n, set())
        blocks.append((label, nodes, subset, label in ITERATED))
    return blocks


def describe(node_order, node_module, *, hoist: bool, routing=UNGUARDED,
             lift: bool = False) -> dict:
    ln, pre, post = hoist_split(node_order, node_module, hoist=hoist,
                                routing=routing, lift=lift)
    per_module: dict = {}
    for n in ln:
        per_module.setdefault(node_module.get(n, "?"), []).append(n)
    return {
        "hoist": hoist,
        "lift": lift,
        "routing": (
            "UNGUARDED -- no predicate-layer guard; every hoistable node goes "
            "to the post-predicate slot (A18 behaviour)"
            if routing is None else routing.describe()
        ),
        "routing_reasons": (
            {} if routing is None else
            {n: sorted(routing.feeds_predicate(n)) for n in pre + post}
        ),
        "loop_nodes": ln,
        "n_loop_nodes": len(ln),
        "hoisted_nodes": pre + post,
        "pre_predicate_tail": pre,
        "post_predicate_tail": post,
        "loop_nodes_by_module": per_module,
        "model_calls_by_module": {k: len(v) for k, v in sorted(per_module.items())},
    }
