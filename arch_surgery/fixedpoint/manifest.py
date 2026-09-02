#!/usr/bin/env python
"""A comparison must be able to say what it varies, or it does not run.

Why this exists
---------------

§6.3(iii) of the results report records the one confound this study nearly
published.  Building the blocked arrangement by grouping the models into
blocks also **transposed two adjacent models**, ``build`` and ``physics``, so
the flat-to-blocked comparison varied two things and not one.  Nobody named it
while the comparison was designed, built, run or written up.  What caught it
was an unrelated task's diff.

The null came out clean, and that is not the lesson.  The lesson is that a
headline comparison ran with an unnamed confound in it and **no check in the
design was capable of noticing**, because nothing in the design ever wrote down
what the comparison was supposed to be varying.

So: every arm-versus-arm comparison carries a **manifest** --- a declaration,
written by the person who designed the comparison, of exactly what differs
between the two arms.  At run time the manifest is checked against the arms as
they were actually built.  A difference the manifest does not declare is a
**refusal**, not a warning; a declared difference that is not present is also a
refusal, because a manifest that over-declares stops being a description.

What it can and cannot catch
----------------------------

It compares **the configuration two arms were built from**: their node
sequences, their block schedules, their tolerances, floors and caps, their
hoist and lift settings, their coupling-state spec.  The ``build``/``physics``
transposition is a difference in the node sequence and would have been caught,
because the manifest for ``A0 -> A1`` declares *grouping* and the sequences
would have differed by a transposition nobody declared.

It cannot catch a difference that is not in the configuration --- two arms
built identically but running against different data, or a defect inside a
solver that both arms share.  Those are what the replay-fidelity, restore and
determinism gates are for.  This is a guard against **undeclared** variation,
not against all variation.

Usage
-----
    m = Manifest("A0 -> A1", varies=["block_grouping"],
                 rationale="the module grouping alone; §4.4.4 controls order")
    m.check(descriptor_for_A0, descriptor_for_A1)   # raises on a surprise
"""

from __future__ import annotations

import json

#: The names a manifest may declare.  A closed vocabulary on purpose: a free
#: string would let a comparison declare "stuff" and pass.  Each name maps to
#: the descriptor keys it licenses to differ.
DIMENSIONS: dict[str, tuple[str, ...]] = {
    # the predicate and its floor
    "stopping_test": ("predicate",),
    "sweep_floor": ("floor",),
    # topology
    "block_grouping": ("schedule_shape", "block_schedule", "node_sequence"),
    "node_order": ("node_sequence",),
    # tolerances
    "tau": ("tau",),
    "inner_tau": ("inner_tau",),
    # node-set membership
    "hoist": ("hoist", "loop_nodes", "pre_predicate_tail",
              "post_predicate_tail", "block_schedule", "schedule_shape",
              "node_sequence"),
    "lift": ("lift", "loop_nodes", "pre_predicate_tail",
             "post_predicate_tail", "block_schedule", "schedule_shape",
             "node_sequence"),
    "predicate_routing": ("pre_predicate_tail", "post_predicate_tail"),
    # the coupling-state spec itself
    "spec": ("spec_mode", "scale_floor", "spec_sha256"),
    # caps are detectors; a comparison may legitimately vary them, but must say so
    "caps": ("inner_cap", "outer_cap", "global_cap"),
}


class ManifestViolation(AssertionError):
    """A comparison could not state what it varies."""


def arm_descriptor(
    *,
    name: str,
    predicate: str,
    node_sequence,
    block_schedule=None,
    floor,
    tau,
    inner_tau=None,
    hoist: bool,
    lift: bool = False,
    pre_predicate_tail=(),
    post_predicate_tail=(),
    loop_nodes=(),
    spec_mode: str,
    scale_floor: float,
    spec_sha256: str,
    inner_cap=None,
    outer_cap=None,
    global_cap=None,
) -> dict:
    """Everything about an arm that a comparison could be varying.

    Deliberately flat and deliberately complete: a key that is not here is a
    dimension the manifest cannot police, so adding an arm parameter without
    adding it here is the way this guard would be defeated.  ``schedule_shape``
    is derived rather than passed, so a block schedule cannot differ in shape
    while claiming not to.
    """
    sched = None if block_schedule is None else [
        {"label": b[0], "nodes": list(b[1]), "iterate": bool(b[3])}
        for b in block_schedule
    ]
    return {
        "name": name,
        "predicate": predicate,
        "node_sequence": list(node_sequence),
        "block_schedule": sched,
        "schedule_shape": None if sched is None else [
            (b["label"], len(b["nodes"]), b["iterate"]) for b in sched
        ],
        "floor": floor,
        "tau": tau,
        "inner_tau": inner_tau,
        "hoist": bool(hoist),
        "lift": bool(lift),
        "pre_predicate_tail": list(pre_predicate_tail),
        "post_predicate_tail": list(post_predicate_tail),
        "loop_nodes": list(loop_nodes),
        "spec_mode": spec_mode,
        "scale_floor": scale_floor,
        "spec_sha256": spec_sha256,
        "inner_cap": inner_cap,
        "outer_cap": outer_cap,
        "global_cap": global_cap,
    }


#: Descriptor keys that are identity rather than configuration.
_IGNORED = ("name",)


class Manifest:
    """What a comparison declares it varies, checked against what it does."""

    def __init__(self, comparison: str, *, varies, rationale: str):
        unknown = [d for d in varies if d not in DIMENSIONS]
        if unknown:
            raise ManifestViolation(
                f"{comparison}: undeclarable dimension(s) {unknown}; the "
                f"vocabulary is {sorted(DIMENSIONS)}.  If a comparison really "
                f"varies something new, add it to DIMENSIONS with the "
                f"descriptor keys it licenses -- do not widen an existing one."
            )
        if not rationale.strip():
            raise ManifestViolation(
                f"{comparison}: a manifest without a rationale is a list, not "
                f"a declaration"
            )
        self.comparison = comparison
        self.varies = tuple(varies)
        self.rationale = rationale
        self.licensed = set()
        for d in varies:
            self.licensed |= set(DIMENSIONS[d])

    def diff(self, a: dict, b: dict) -> list:
        """Descriptor keys on which the two arms actually differ."""
        keys = sorted(set(a) | set(b))
        return [
            k for k in keys
            if k not in _IGNORED and a.get(k) != b.get(k)
        ]

    def check(self, a: dict, b: dict, *, strict_unused: bool = True) -> dict:
        """Refuse the comparison unless the manifest describes it.

        ``strict_unused`` also refuses a manifest that declares a dimension
        none of whose keys differ.  On by default: an over-declared manifest
        launders exactly the confound this class exists to catch, by making
        "grouping and order" cover a comparison that was supposed to vary only
        grouping.
        """
        observed = self.diff(a, b)
        undeclared = [k for k in observed if k not in self.licensed]
        unused = []
        if strict_unused:
            for d in self.varies:
                if not (set(DIMENSIONS[d]) & set(observed)):
                    unused.append(d)
        record = {
            "comparison": self.comparison,
            "declared": list(self.varies),
            "rationale": self.rationale,
            "observed_differing_keys": observed,
            "undeclared_differences": undeclared,
            "declared_but_absent": unused,
            "n_descriptor_keys_compared": len(
                [k for k in set(a) | set(b) if k not in _IGNORED]
            ),
            "status": "PASS" if not undeclared and not unused else "REFUSED",
        }
        if record["status"] != "PASS":
            raise ManifestViolation(
                f"{self.comparison}: "
                + (
                    f"varies {undeclared} without declaring it. "
                    if undeclared else ""
                )
                + (
                    f"declares {unused} but does not vary it. "
                    if unused else ""
                )
                + "A comparison that cannot state what it varies does not run. "
                + json.dumps(record["observed_differing_keys"])
            )
        return record


def check_all(manifests, descriptors, *, require_all_pairs: bool = True) -> dict:
    """Run every declared comparison in a run, and record all of them.

    ``manifests`` is ``{comparison: Manifest}``; the comparison name reads
    ``"<arm a> -> <arm b>"`` with both arms in ``descriptors``.  A comparison
    whose arms are not present is skipped and **named** in the record, because
    a silently skipped guard is the empty-set false pass this project has met
    before.

    **Any number of arms.**  Phase B runs three (decision D18) --- ``R``, a
    predicate-matched flat control ``A0'``, and the architecture ``A1'`` ---
    with three comparisons that mean three different things: ``R -> A0'``
    varies the predicate alone, ``A0' -> A1'`` varies the architecture alone,
    and ``R -> A1'`` varies both and is only meaningful as the user-facing
    figure.  Nothing here assumes two arms, and ``require_all_pairs`` makes
    that structural: every **ordered pair of arms that were actually run** must
    have a manifest, or the run is refused.  That is what stops a third arm
    being added and quietly compared against the other two with no declaration
    --- the exact shape of §6.3(iii)'s confound, one level up.

    ``require_all_pairs`` may be turned off only where a pair is deliberately
    never compared; if you do, say which pair and why in the calling code, not
    here.
    """
    out = {"checked": [], "skipped": [], "undeclared_pairs": []}
    for name, man in manifests.items():
        a, _, b = name.partition("->")
        a, b = a.strip(), b.strip()
        if a not in descriptors or b not in descriptors:
            out["skipped"].append(
                {"comparison": name,
                 "reason": f"arm(s) not run: "
                           f"{[x for x in (a, b) if x not in descriptors]}"}
            )
            continue
        out["checked"].append(man.check(descriptors[a], descriptors[b]))

    declared = set()
    for name in manifests:
        a, _, b = name.partition("->")
        declared.add((a.strip(), b.strip()))
    run_arms = sorted(descriptors)
    for i, a in enumerate(run_arms):
        for b in run_arms[i + 1:]:
            if (a, b) not in declared and (b, a) not in declared:
                out["undeclared_pairs"].append(f"{a} -> {b}")

    out["arms_run"] = run_arms
    out["n_arms"] = len(run_arms)
    out["n_ordered_pairs_possible"] = len(run_arms) * (len(run_arms) - 1) // 2
    out["n_checked"] = len(out["checked"])
    out["n_skipped"] = len(out["skipped"])
    out["require_all_pairs"] = require_all_pairs
    bad_pairs = require_all_pairs and out["undeclared_pairs"]
    out["status"] = (
        "EMPTY" if not out["checked"]
        else "REFUSED -- undeclared arm pair(s)" if bad_pairs
        else "PASS" if all(c["status"] == "PASS" for c in out["checked"])
        else "REFUSED"
    )
    if bad_pairs:
        raise ManifestViolation(
            f"arms {run_arms} were run but "
            f"{out['undeclared_pairs']} have no manifest.  Every pair of arms "
            f"in one run is comparable, so every pair needs a declaration of "
            f"what it varies -- or an explicit statement that it is never "
            f"compared."
        )
    return out
