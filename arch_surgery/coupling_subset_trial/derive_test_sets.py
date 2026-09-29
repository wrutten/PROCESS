#!/usr/bin/env python
"""Derive the two narrowed convergence-test sets from the DSM's data interfaces.

Task A89 (coupling-subset-trial), 2026-09-29, at the user's request: V4 stops
every coupling-state loop on the whole measured state ``y`` (every field an
in-loop model writes; 840 / 846 / 827 components).  This script selects two
subsets of ``y`` from the dependency analysis's data interfaces, so a trial can
stop the same loops on each and compare:

``interface``
    a component of ``y`` that the DSM shows **written by one model and read by
    a different model**;
``feedback``
    of those, a component read by a model that runs **before** its writer in
    the DSM's execution order (``supermodel_execution_order``) — the variables
    carried backwards from one sweep to the next.

"Model" is a DSM supermodel that has an execution order.  The two constraint
blocks (``ConsistencyConstraints``, ``EngineeringConstraints``) have none: they
are the optimiser's reads, not a model in the loop, so they neither write nor
read for this purpose and are listed per component as ``driver_readers``.
The DSM's function-library supermodels (``physics.physics_functions`` and the
like) do carry an order and count as models, exactly as the DSM draws them.

Nothing here is a decision.  The DSM's own diagnostics say what it cannot see
(a model reading its own previous output is a *self read*; the DSM cannot tell
a read of the previous sweep's value from a read of a value written earlier in
the same sweep), so every component carries its writers, readers and a
``self_read`` flag, and the trial reports what its audit finds against them.

Inputs, read once (trap T9):

* the sibling's per-configuration exports, ``PROCESS_code_analysis/output/
  <export>/process_dependencies.json``, **read-only**; the sibling's HEAD, the
  pin its ``config.py`` names and each export's sha256, size and mtime are
  recorded, because the exports are gitignored there and have no committed
  state of their own;
* V4's committed coupling-state artifacts (``harness/data/coupling_state_
  <configuration>.json``), read-only — the component list and its sha256.

Output: ``test_sets.json`` beside this script.  Re-running against unchanged
inputs reproduces it byte for byte.

Usage::

    python arch_surgery/coupling_subset_trial/derive_test_sets.py
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
TREE = HERE.parent.parent
V4_DATA = TREE / "arch_surgery" / "MDA_partitioning_experiment_v4" / "harness" / "data"
OUT = HERE / "test_sets.json"

SIBLING = Path("/home/wrutten/projects/PROCESS_code_analysis")
SIBLING_CONFIG = SIBLING / "src" / "PROCESS_DSM" / "inputs" / "config.py"

#: Which sibling export serves each configuration — the table
#: ``arch_surgery/fixedpoint/gen_function_counts.py`` reads them with.
DSM_EXPORT: dict[str, str] = {
    "large_tokamak_nof": "tokamak",
    "low_aspect_ratio_DEMO": "low_aspect_ratio_DEMO",
    "st_regression": "st_regression",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sibling_provenance() -> dict:
    head = subprocess.run(
        ["git", "-C", str(SIBLING), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    dirty = subprocess.run(
        ["git", "-C", str(SIBLING), "status", "--porcelain"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    pin = re.search(
        r'^ANALYSIS_PIN_NAME\s*=\s*"([^"]+)"', SIBLING_CONFIG.read_text(), re.M
    )
    return {
        "repository": str(SIBLING),
        "git_head": head,
        "working_tree_clean": not dirty,
        "dsm_pin": pin.group(1) if pin else None,
        "dsm_pin_read_from": "src/PROCESS_DSM/inputs/config.py",
        "exports_are_tracked_there": False,
    }


def derive(configuration: str) -> dict:
    export_path = SIBLING / "output" / DSM_EXPORT[configuration] / "process_dependencies.json"
    y_path = V4_DATA / f"coupling_state_{configuration}.json"
    export = json.loads(export_path.read_text())
    y_art = json.loads(y_path.read_text())
    y_keys = [c["key"] for c in y_art["components"]]
    y_set = set(y_keys)

    nodes, edges = export["nodes"], export["edges"]

    def info(uuid: str) -> dict:
        return nodes[uuid]["annotations"].get("PROCESS_ast_info", {})

    def model_name(uuid: str) -> str:
        return info(uuid).get("class_name") or nodes[uuid]["name"]

    supermodels = {
        u for u, n in nodes.items()
        if n["kind"] == "model" and info(u).get("level") == "supermodel"
    }
    order = {u: info(u).get("supermodel_execution_order") for u in supermodels}
    models = {u for u in supermodels if order[u] is not None}
    unordered = sorted(model_name(u) for u in supermodels if order[u] is None)

    writers: dict[str, set[str]] = defaultdict(set)
    readers: dict[str, set[str]] = defaultdict(set)
    driver_readers: dict[str, set[str]] = defaultdict(set)
    for e in edges.values():
        if e["kind"] != "data_interface":
            continue
        s, t = e["source"], e["target"]
        if s in supermodels and nodes[t]["kind"] == "variable":
            if s in models:
                writers[nodes[t]["name"]].add(s)
        elif t in supermodels and nodes[s]["kind"] == "variable":
            (readers if t in models else driver_readers)[nodes[s]["name"]].add(t)

    variables = {n["name"] for n in nodes.values() if n["kind"] == "variable"}

    components = {}
    interface, feedback = [], []
    for key in y_keys:
        ws, rs = writers.get(key, set()), readers.get(key, set())
        other = {r for r in rs if any(r != w for w in ws)}
        back = sorted(
            {
                (model_name(r), model_name(w))
                for w in ws for r in rs
                if r != w and order[r] < order[w]
            }
        )
        is_interface = bool(other)
        is_feedback = bool(back)
        if is_interface:
            interface.append(key)
        if is_feedback:
            feedback.append(key)
        components[key] = {
            "in_dsm": key in variables,
            "writers": sorted(model_name(w) for w in ws),
            "readers": sorted(model_name(r) for r in rs),
            "driver_readers": sorted(model_name(r) for r in driver_readers.get(key, ())),
            "self_read": bool(ws & rs),
            "interface": is_interface,
            "feedback": is_feedback,
            "feedback_pairs_reader_writer": [list(p) for p in back],
        }

    self_read_only = [
        k for k, c in components.items() if c["self_read"] and not c["interface"]
    ]
    return {
        "coupling_state_artifact": str(y_path.relative_to(TREE)),
        "coupling_state_components_sha256": y_art["components_sha256"],
        "n_y": len(y_keys),
        "export": {
            "name": DSM_EXPORT[configuration],
            "path": str(export_path),
            "sha256": sha256(export_path),
            "size": export_path.stat().st_size,
            "mtime": export_path.stat().st_mtime,
        },
        "dsm_models_with_order": len(models),
        "dsm_supermodels_without_order_excluded": unordered,
        "census": {
            "y_not_a_dsm_variable": sorted(y_set - variables),
            "y_written_by_no_dsm_model": sorted(k for k in y_keys if not writers.get(k)),
            "n_interface": len(interface),
            "n_feedback": len(feedback),
            "n_self_read": sum(c["self_read"] for c in components.values()),
            "n_self_read_not_interface": len(self_read_only),
            "n_written_read_by_no_other_model": len(y_keys) - len(interface),
        },
        "sets": {"interface": interface, "feedback": feedback},
        "components": components,
    }


def main() -> None:
    out = {
        "format": "coupling-subset-test-sets-1",
        "generated_by": "arch_surgery/coupling_subset_trial/derive_test_sets.py",
        "task": "A89 (coupling-subset-trial)",
        "definition": {
            "interface": "component of y written by one DSM model and read by a different DSM model",
            "feedback": "interface component read by a DSM model whose supermodel_execution_order is below its writer's",
            "model": "DSM supermodel with a supermodel_execution_order; the constraint blocks have none and are driver readers",
        },
        "sibling": sibling_provenance(),
        "configurations": {c: derive(c) for c in DSM_EXPORT},
    }
    OUT.write_text(json.dumps(out, indent=1, sort_keys=False) + "\n")
    for c, d in out["configurations"].items():
        print(c, d["n_y"], d["census"]["n_interface"], d["census"]["n_feedback"],
              "self-read", d["census"]["n_self_read"],
              "not-in-dsm", len(d["census"]["y_not_a_dsm_variable"]),
              "unwritten", len(d["census"]["y_written_by_no_dsm_model"]))


if __name__ == "__main__":
    main()
