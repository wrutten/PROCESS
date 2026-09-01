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


def loop_nodes(node_order, node_module, *, hoist: bool):
    """The nodes inside the loop, in driver order.

    ``<x_inject>`` is not a node: it is the design-vector injection, which
    every pass performs at its head.
    """
    out = []
    for n in node_order:
        if n == "<x_inject>":
            continue
        if hoist and node_module.get(n) == "FF":
            continue
        out.append(n)
    return out


def hoisted_nodes(node_order, node_module, *, hoist: bool):
    if not hoist:
        return []
    return [
        n
        for n in node_order
        if n != "<x_inject>" and node_module.get(n) == "FF"
    ]


def build_blocks(node_order, node_module, y_index_of_node, *, hoist: bool):
    """``[(label, nodes, y_subset, iterate), ...]`` for the block arm."""
    blocks = []
    for label in BLOCK_ORDER:
        if label == "FF" and hoist:
            continue
        nodes = [
            n
            for n in node_order
            if n != "<x_inject>" and node_module.get(n) == label
        ]
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


def describe(node_order, node_module, *, hoist: bool) -> dict:
    ln = loop_nodes(node_order, node_module, hoist=hoist)
    hn = hoisted_nodes(node_order, node_module, hoist=hoist)
    per_module: dict = {}
    for n in ln:
        per_module.setdefault(node_module.get(n, "?"), []).append(n)
    return {
        "hoist": hoist,
        "loop_nodes": ln,
        "n_loop_nodes": len(ln),
        "hoisted_nodes": hn,
        "loop_nodes_by_module": per_module,
        "model_calls_by_module": {k: len(v) for k, v in sorted(per_module.items())},
    }
