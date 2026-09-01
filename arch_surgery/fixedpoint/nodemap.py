"""C8 / F4 -- the DSM node map, and its one assertion.

The map answers *model attribute -> DSM row -> module*.  It is committed as
data in ``arch_surgery/docs/data/dsm_node_map.json`` and never read live from
the dependency-analysis repository (trap T9: that repository regenerates its
exports at every merge, so a live read races with their tooling and silently
re-pins us to whatever their tree holds that day).

**Validation is three lines, not a subsystem.**  Assert that the nodes observed
executing are a *subset* of the nodes the map names -- never equality.  Per
``DSM_VALIDATION.md`` V6 the map is configuration-specific: ``Pulse`` writes
nothing under ``i_pulsed_plant = 0`` and ``models.tfcoil.run()`` is reached in
none of the four decks, so an equality check would fail on a correct run.  An
observed node the map does not name is the real error, and that is what raises.

**Two unit systems, deliberately both carried.**  The collapsed DSM's 56 rows do
not map one-to-one onto the 26 ``run()`` calls in ``_call_models_once``
(``DSM_VALIDATION.md``, "Open").  Node-count weighting in DSM-row units
(``|M1| = 24``, ``|M2| = 10``, ``|M3| = 12``, ``|all| = 52``) is a different
quantity from node-count weighting in model-call units, and conflating them in
a cost argument is an easy error.  The map therefore records both, and never
lets a caller ask for "the node count" without naming the unit.
"""

from __future__ import annotations

import json
from pathlib import Path

DEFAULT_PATH = (
    Path(__file__).resolve().parent.parent / "docs" / "data" / "dsm_node_map.json"
)


class NodeMap:
    """The committed model attribute -> DSM row -> module map."""

    def __init__(self, raw: dict):
        self.raw = raw
        self.nodes: dict = raw["nodes"]
        self.modules: dict = raw["modules"]

    # -- loading ---------------------------------------------------------

    @classmethod
    def load(cls, path: str | Path | None = None) -> NodeMap:
        p = Path(path) if path else DEFAULT_PATH
        return cls(json.loads(p.read_text()))

    # -- the assertion ---------------------------------------------------

    def assert_observed_subset(self, observed) -> dict:
        """Raise if a node executed that the map does not name.

        Subset, not equality -- see the module docstring.
        """
        obs = {n for n in observed if n not in ("<x_inject>",)}
        unmapped = sorted(obs - set(self.nodes))
        if unmapped:
            raise AssertionError(
                "observed nodes are not a subset of the DSM node map: "
                f"{unmapped} execute but are not named in {DEFAULT_PATH.name}"
            )
        return {
            "n_observed": len(obs),
            "n_mapped": len(self.nodes),
            "mapped_not_observed": sorted(set(self.nodes) - obs),
            "unmapped_observed": unmapped,
        }

    # -- lookups ---------------------------------------------------------

    def feedback_fields(self, *, include_dead: bool = True) -> list[str]:
        """Set (a): the DSM's cross-module feedback-edge variables.

        The cross-check, never the predicate.  ``withdrawn`` entries are the
        trap-T1 false positives and are deliberately absent.
        """
        e = self.raw.get("dsm_feedback_edges", {})
        out = [x["field"] for x in e.get("live", [])]
        if include_dead:
            out += [x["field"] for x in e.get("dead_in_this_deck", [])]
        return sorted(set(out))

    def module_of(self, node: str) -> str:
        entry = self.nodes.get(node)
        return entry["module"] if entry else "?"

    def counts(self, observed=None) -> dict:
        """Module sizes in **both** unit systems.

        ``dsm_rows`` is the collapsed DSM's row count per module, as decided in
        D8.  ``model_calls`` counts the ``run()`` calls the map assigns to the
        module -- optionally restricted to the nodes actually observed, which
        is the only figure that means anything for a particular deck.
        """
        out = {}
        for mod, spec in self.modules.items():
            mapped = [n for n, e in self.nodes.items() if e["module"] == mod]
            obs = (
                [n for n in mapped if n in set(observed)]
                if observed is not None
                else None
            )
            out[mod] = {
                "label": spec.get("label"),
                "dsm_rows": spec.get("n_dsm_rows"),
                "dsm_row_ranges": spec.get("dsm_rows"),
                "model_calls_mapped": len(mapped),
                "model_calls_observed": None if obs is None else len(obs),
            }
        return out
