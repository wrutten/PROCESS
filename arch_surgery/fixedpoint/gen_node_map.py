#!/usr/bin/env python
"""Generate ``arch_surgery/docs/data/dsm_node_map.json`` (C8 / F4).

**Derived, not reinvented.**  The module assignment comes from
``process/core/_idf_probe_modules.py``'s ``NODE_MODULE``, which A2 built from
decision D8's collapsed-DSM decomposition and then validated against a
run-time census in four scenarios.  Writing a second hand-made list here is
exactly the drift the framework plan (§2.9) says to avoid, so this script reads
that one and adds the DSM-row information our own committed documents state.

**What this map cannot carry, and why.**  A per-node DSM *row number* exists
only in the dependency-analysis repository's generated exports, and trap T9
forbids reading those live.  Our own committed documents state the row *ranges*
per module (D8) and a handful of individual rows (``DSM_VALIDATION.md`` V1, V3,
V4, V5).  Those are recorded; every other node carries ``dsm_row: null`` and
the module's range.  Closing that gap needs a per-row name export from
``PROCESS_code_analysis``, requested rather than scraped.

Run it with ``PYTHONPATH`` pointing at the tree under test.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

TREE = Path(__file__).resolve().parent.parent.parent
OUT = TREE / "arch_surgery" / "docs" / "data" / "dsm_node_map.json"

#: D8's collapsed-DSM decomposition, as recorded in MASTER_TODO.md.
MODULES = {
    "M1": {
        "label": "Physics",
        "dsm_rows": [[4, 4], [6, 28]],
        "n_dsm_rows": 24,
        "in_loop": True,
    },
    "M2": {
        "label": "Coils",
        "dsm_rows": [[5, 5], [29, 37]],
        "n_dsm_rows": 10,
        "in_loop": True,
        "membership_note": (
            "M2 contains *the TF coil model, selected by i_tf_turn_type* -- not "
            "any one class. The switch chooses between the cable-in-conduit and "
            "cross-conductor superconducting turn models (caller.py:321 and "
            "caller.py:328), and both are M2 members. Per-scenario DSM "
            "regeneration by PROCESS_code_analysis (2026-09-01) shows "
            "st_regression substituting one for the other *within* M2, with no "
            "new cross-module cells; describing the module by the switch rather "
            "than by a class name is what makes that a non-event."
        ),
    },
    "M3": {
        "label": "Plant",
        "dsm_rows": [[40, 51]],
        "n_dsm_rows": 12,
        "in_loop": True,
    },
    "PULSE": {
        "label": "Pulse -- the articulation point, belonging to no module",
        "dsm_rows": [[39, 39]],
        "n_dsm_rows": 1,
        "in_loop": True,
    },
    "FF": {
        "label": "feed-forward tail (CsFatigue row 38; rows 52-55)",
        "dsm_rows": [[38, 38], [52, 55]],
        "n_dsm_rows": 5,
        "in_loop": False,
    },
    "X": {
        "label": "design-vector injection -- not a model, not a DSM row",
        "dsm_rows": [],
        "n_dsm_rows": 0,
        "in_loop": True,
    },
}

#: Individual DSM rows our own committed documents state.  Everything else is
#: null: see the module docstring.
KNOWN_ROWS = {
    "build": 5,  # DSM_VALIDATION V3
    "pulse": 39,  # D8, DSM_VALIDATION V5
    "fw": 41,  # DSM_VALIDATION V3 ("FirstWall (M3, row 41)")
    "power": 48,  # DSM_VALIDATION V4 ("Power (M3, row 48)")
}

#: Rows the collapsed DSM carries that are **not** executed inside a sweep.
#: An earlier revision of the partition plan used |all| = 56; the correct
#: figure is 52 (A2's correction, recorded in DSM_VALIDATION.md "Open").
NON_SWEEP_ROWS = {
    1: "COOR_SingleRun",
    2: "VMCON",
    3: "MDA_Idempotence",
    56: "MDA_Output",
}

#: Set (a) of EXPERIMENT_FRAMEWORK.md §2.4 -- the DSM's cross-module feedback
#: edges, used as a **cross-check** against the run-time coupling set, never as
#: the convergence predicate.  Sourced from A2's run-time census at ``c0ae5b28``
#: and from ``reports/DSM_VALIDATION.md`` V1-V5, both committed in this
#: repository.  Not scraped from the dependency-analysis repository's generated
#: exports (trap T9).
DSM_FEEDBACK_EDGES = {
    "provenance": (
        "A2's run-time cross-module back-edge census at c0ae5b28, cross-checked "
        "against the collapsed DSM in reports/DSM_VALIDATION.md V1-V5."
    ),
    "live": [
        {
            "field": "times.t_plant_pulse_burn",
            "writer": "pulse",
            "writer_module": "PULSE",
            "reader": "physics",
            "reader_module": "M1",
            "note": "A2's k = 1. Dead in st_regression (i_pulsed_plant = 0).",
        }
    ],
    "dead_in_this_deck": [
        {
            "field": "build.dr_fw_inboard",
            "writer": "fw",
            "writer_module": "M3",
            "reader": "build",
            "reader_module": "M2",
            "note": "V3: structurally present, never changes between sweeps",
        },
        {
            "field": "build.dr_fw_outboard",
            "writer": "fw",
            "writer_module": "M3",
            "reader": "build",
            "reader_module": "M2",
            "note": "V3",
        },
        {
            "field": "pf_power.vpfskv",
            "writer": "power",
            "writer_module": "M3",
            "reader": "pulse",
            "reader_module": "PULSE",
            "note": "V4: the value is the literal 20.0e0",
        },
    ],
    "withdrawn": [
        {
            "field": "physics.b_plasma_vertical_required",
            "note": "V1 / trap T1 -- the read is on an output() path only",
        },
        {
            "field": "times.t_plant_pulse_burn",
            "note": "V2 / trap T1 -- the pfcoil-side read is in PFCoil.outvolt()",
        },
    ],
}

#: How each node is invoked in ``Caller._call_models_once``.  Needed by the
#: replay, which must call the same thing the driver calls.
INVOCATION = {
    "power.acpow": "models.power.acpow(output=False)",
    "power.plant_electric_production": "models.power.plant_electric_production()",
    "<x_inject>": "set_scaled_iteration_variable(x, nvars, data)",
}


def main() -> int:
    from process.core import _idf_probe_modules as M

    head = subprocess.run(
        ["git", "-C", str(TREE), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()

    nodes = {}
    for name, mod in sorted(M.NODE_MODULE.items()):
        if name == "objective_constraints":
            # Not a model and not inside ``_call_models_once``: it is the
            # objective/constraint block that runs after the sweep returns.
            # Recorded so the map is complete, flagged so nothing loops it.
            nodes[name] = {
                "module": mod,
                "dsm_row": None,
                "dsm_row_range": MODULES[mod]["dsm_rows"],
                "kind": "objective_block",
                "invocation": "objective_function(...) + constraint_eqns(...)",
                "in_call_models_once": False,
            }
            continue
        nodes[name] = {
            "module": mod,
            "dsm_row": KNOWN_ROWS.get(name),
            "dsm_row_range": MODULES[mod]["dsm_rows"],
            "kind": "injection" if name == "<x_inject>" else "model_call",
            "invocation": INVOCATION.get(name, f"models.{name}.run()"),
            "in_call_models_once": True,
        }

    model_calls = sum(
        1 for e in nodes.values() if e["kind"] == "model_call"
    )
    payload = {
        "format": "a18-node-map-1",
        "generated_by": "arch_surgery/fixedpoint/gen_node_map.py",
        "derived_from": (
            "process/core/_idf_probe_modules.py NODE_MODULE -- A2's mapping, "
            "itself built from decision D8's collapsed-DSM decomposition and "
            "validated against a run-time node census in four scenarios. "
            "Not reinvented here."
        ),
        "tree_git_head": head or None,
        "dsm_pin": "PROCESS_at_36ac820e",
        "dsm_source_deck": "examples/data/large_tokamak_IN.DAT",
        "decision": "D8",
        "caveats": [
            "Configuration-specific in origin (DSM_VALIDATION.md V6): generated "
            "for the tool's tokamak preset, which matches large_tokamak_nof and "
            "large_tokamak_eval exactly. RESOLVED 2026-09-01 by per-scenario DSM "
            "regeneration in PROCESS_code_analysis (M100): the three-module "
            "partition survives on low_aspect_ratio_DEMO outright (identical "
            "52-node model layer, identical 55/55 cross-module cell set) and on "
            "st_regression up to two boundary-respecting model substitutions "
            "with zero new cross-module cells. The pre-committed withdrawal of "
            "the st_regression block-arm result is therefore NOT triggered.",
            "Neither substitution touches this map, because this map is derived "
            "from run-time instrumentation across all four scenarios rather than "
            "from the DSM's single-deck graph. The TF-turn substitution is "
            "already covered (both cicc_sctfcoil and croco_sctfcoil are M2 "
            "members), and ElectronCyclotron is not a node at this granularity "
            "-- it is constructed in main.py and consumed inside the "
            "physics-orchestrated block, never as a top-level run() in "
            "_call_models_once.",
            "Per-node DSM row numbers are not available in this repository. "
            "Trap T9 forbids reading the dependency-analysis repository's "
            "generated exports live. Only the rows our own committed "
            "documents state are filled in; the rest are null.",
            "DSM-row units and model-call units are NOT interchangeable: 52 "
            "sweep-executed rows against 26 model calls.",
        ],
        "units": {
            "dsm_rows": {
                "M1": 24,
                "M2": 10,
                "M3": 12,
                "PULSE": 1,
                "FF": 5,
                "executed_in_a_sweep": 52,
                "total_rows": 56,
                "not_executed_in_a_sweep": {
                    str(k): v for k, v in sorted(NON_SWEEP_ROWS.items())
                },
            },
            "model_calls": {
                "mapped_total": model_calls,
                "note": (
                    "Nodes the map names. A given deck executes a subset: the "
                    "TF-coil branch and the blanket branch are switch-selected "
                    "and models.tfcoil.run() is reached in none of the four "
                    "experiment decks."
                ),
            },
        },
        "module_order": dict(M.MODULE_ORDER),
        "dsm_feedback_edges": DSM_FEEDBACK_EDGES,
        "modules": MODULES,
        "nodes": nodes,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"wrote {OUT} -- {len(nodes)} nodes, {model_calls} model calls")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
