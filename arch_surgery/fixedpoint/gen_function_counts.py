#!/usr/bin/env python
"""Generate ``arch_surgery/docs/data/dsm_function_counts.json`` — the number of
**functions** behind each collapsed-DSM row of each module, per configuration.

**Why this file exists.**  The per-module sweep tables of the V4 report weight
their total by ``models`` — the collapsed-DSM row count of each module — and
the user asked (2026-09-17) to see the same total weighted **per function**:
*"You can find the nr of functions per module from the DSM decomposition.
Each module contains the specified nr of DSM rows (models) and each model has
a set of submodels (individual functions) defined with the parent-child
relations in the DSM."*  This script reads those parent-child relations once,
from the dependency-analysis study's own per-configuration exports, and
commits the counts as data.  The harness reads **only the committed file**
(trap T9: a sibling repository's generated output is never read live by a
measurement), exactly as it reads ``dsm_node_map.json``, which
``gen_node_map.py`` beside this script generated the same way.

**What a function is.**  A *submodel* of the dependency analysis: a node of
``kind = "model"`` whose ``parent`` is set — one callable of a supermodel
(``PROCESS_code_analysis/docs/TERMINOLOGY.md`` §2; the hierarchy is exactly
two deep, which this script checks).  A supermodel with **no** submodel counts
as **one** function — its entry method is the one callable it has.  So
``functions(row) = max(1, n_submodels(row))``.  The **alternative** reading —
``1 + n_submodels``, the entry method counted beside its callables — is
recorded beside it in every row and module, so the report can say whether the
definition matters.  A *subdriver* (``kind = "workflow_driver"`` with a parent;
an embedded root-finder) sequences rather than computes (TERMINOLOGY §1) and is
counted separately and **not** as a function; there are three per
configuration.

**Which row is which model — the sibling's own ordering, never a guess.**
Decision D8's row numbers (M1 = rows 4, 6–28; M2 = 5, 29–37; M3 = 40–51;
``Pulse`` 39; ``CsFatigue`` 38 and 52–55 feed-forward) are the row order of
the sibling's *unsequenced collapsed* figure ``dsm_collapsed.html``
(``docs/plans/MDA_PARTITION_EXPERIMENT.md`` §2).  That figure's rows are the
top-level actors sorted by ``PROCESS_DSM.output.figures.driver_order`` with
``interleave_drivers=True`` — each actor's **first** position on the process
line (``walk_rank``: ``process_line_order`` read with ``setdefault``, so a
model the MDA runs and ``MDA_Output`` runs again sits where it first ran).
This script derives that order from the export's own ``process_line_order``
annotation by the same rule **and** runs the sibling's ``driver_order`` itself
on the same export, in the sibling's own environment (``ESL_env``, read-only,
``PYTHONDONTWRITEBYTECODE=1``, working directory in scratch), and **refuses if
the two orders differ**.  A row with no model, or a model with no row, is
named in the output and is never invented.

**Where the module of a row comes from.**  On the ``tokamak`` export — the
analysis preset that matches ``large_tokamak_nof`` exactly (node map caveat
V6) — from the committed node map's row ranges (``modules.*.dsm_rows``),
which is D8.  The other two configurations' exports carry their **own** row
order (their conditionals resolve differently), so there the module is
assigned **by model name** from the tokamak assignment; a model the tokamak
export does not have is placed only by a documented substitution recorded in
the node map's own caveats (``ElectronCyclotron`` → M1, inside the
physics-orchestrated block; ``CROCOSuperconductingTFCoil`` → M2, the TF-coil
model selected by ``i_tf_turn_type``), and anything else is a refusal.
Whether the tokamak row ranges also hold on that export is recorded per
configuration (``row_ranges_of_the_node_map_apply``) with the first row on
which they do not.

**The once-per-run nodes.**  The per-module tables group the configuration's
deferred nodes (``costs``, ``vacuum``, ``water_use``; ``pulse`` on
``st_regression``) into one *once per run* row and publish the total as an
interval over two attributions of their rows (``[v = 1, v = 0]``).  The
function-weighted twin needs each such node's **own** function count, so the
node → DSM row mapping is derived here, not typed: the driver's model
container (``process/main.py``, ``Models``) is parsed by the harness's own
``postsolve.container_classes`` for the classes each ``models.<attribute>``
can be, intersected with the export's supermodel names; a once-per-run node
that resolves to anything but exactly one row is a refusal, and the row's
module must be the module the node map places the node in.

**Provenance recorded.**  The sibling's ``HEAD`` and working-tree state, the
pin name read from its ``config.py`` (never a hash typed here), each export's
sha256, size and modification time, whether the export is tracked there (it is
not — ``output/`` is gitignored — so "the committed state" of an export is the
sibling's HEAD at the time of reading plus the export's own digest), and the
sha256 of the node map this script read.  Re-running the script on the same
exports reproduces the file byte for byte; a changed export changes the
recorded digest, so a silent re-pin is visible.

Run it with ``PYTHONPATH`` pointing at the tree under test, from any directory::

    python arch_surgery/fixedpoint/gen_function_counts.py

Task **A88 (function-weighted-sweeps)**, 2026-09-17.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

TREE = Path(__file__).resolve().parent.parent.parent
V4 = TREE / "arch_surgery" / "MDA_partitioning_experiment_v4"
OUT = TREE / "arch_surgery" / "docs" / "data" / "dsm_function_counts.json"
#: The node map this script reads its module ranges from — the repository's
#: shared copy, which ``harness/data/dsm_node_map.json`` is a byte-identical
#: copy of (``harness/data/PROVENANCE.json``).
NODE_MAP = TREE / "arch_surgery" / "docs" / "data" / "dsm_node_map.json"

#: The sibling dependency-analysis repository — read-only.  Its per-deck
#: exports are the source; its ``config.py`` names the pin.
SIBLING = Path("/home/wrutten/projects/PROCESS_code_analysis")
SIBLING_CONFIG = SIBLING / "src" / "PROCESS_DSM" / "inputs" / "config.py"
SIBLING_SRC = SIBLING / "src"

#: Which sibling export configuration serves each of this experiment's
#: configurations.  ``tokamak`` is the analysis preset, which matches
#: ``large_tokamak_nof`` exactly (node map caveat V6, resolved 2026-09-01 by
#: the sibling's per-scenario regeneration, their M100); the other two have
#: per-deck exports of their own.  The same table ``idf_probe/a33_postsolve.py``
#: read the exports with.
DSM_EXPORT: dict[str, str] = {
    "large_tokamak_nof": "tokamak",
    "low_aspect_ratio_DEMO": "low_aspect_ratio_DEMO",
    "st_regression": "st_regression",
}

#: The interpreter the sibling's pipeline runs in.  Found beside this
#: environment, never hard-coded to a user's path elsewhere; refused if absent,
#: because the row order is cross-checked with the sibling's own function and
#: a file written without that check would be a guess with a provenance block.
ESL_PYTHON = Path(sys.prefix).parent / "ESL_env" / "bin" / "python"

#: A supermodel one configuration's export has and the tokamak export does
#: not, with the module it belongs to and the committed sentence that places
#: it.  Anything not in this table is refused, never placed.
SUBSTITUTIONS: dict[str, tuple[str, str]] = {
    "ElectronCyclotron": (
        "M1",
        "node map caveat 2: 'ElectronCyclotron is not a node at this "
        "granularity -- it is constructed in main.py and consumed inside the "
        "physics-orchestrated block'; as a collapsed-DSM row it sits inside "
        "M1's span (DSM_VALIDATION.md V6: a boundary-respecting substitution "
        "with zero new cross-module cells)",
    ),
    "CROCOSuperconductingTFCoil": (
        "M2",
        "node map modules.M2.membership_note: 'M2 contains the TF coil model, "
        "selected by i_tf_turn_type -- not any one class ... both are M2 "
        "members'; st_regression substitutes it for CICCSuperconductingTFCoil "
        "within M2 (DSM_VALIDATION.md V6)",
    ),
    "Constraints": (
        "FF",
        "decision D8's row 55 (MDA_PARTITION_EXPERIMENT.md section 2: rows 52-55 "
        "are WaterUse, Costs, Objective, Constraints -- feed-forward outputs); "
        "the tokamak export read here no longer has a row of that name because "
        "the sibling has since split it (see KNOWN_DRIFT)",
    ),
}

#: Rows the exports carry that the node map's D8 table does not know, each
#: with what is known about it.  Named in the output as unassigned; never
#: placed in a module's count.
KNOWN_DRIFT: dict[str, str] = {
    "EngineeringConstraints": (
        "the sibling's M125 (its queue, 2026-09-17: 'the three constraint "
        "blocks') split D8's single 'Constraints' row into ConsistencyConstraints "
        "(row 55, inside FF's range) and EngineeringConstraints (row 56, outside "
        "every range of the node map, where D8 placed MDA_Output).  A "
        "feed-forward row; in no module the sweep tables print and in no total"
    ),
}

#: The cross-check script the sibling's own environment runs: the collapsed
#: figure's row order by the sibling's own ``driver_order``, printed one name
#: per line.  Nothing is written anywhere by it.
_SIBLING_ORDER_SCRIPT = r"""
import sys
sys.path.insert(0, sys.argv[1])
from ragraph.io.json import from_json
from PROCESS_DSM.output import figures
graph = from_json(sys.argv[2])
rows = [n for n in graph.nodes
        if n.kind in ("model", "workflow_driver") and n.parent is None]
# the sibling's import prints a line of its own; everything before the
# sentinel is theirs and is not a row
print("---rows---")
for node in figures.driver_order(graph, rows, interleave_drivers=True):
    print(node.name)
"""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(*args: str, cwd: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(cwd), *args],
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()


def _pin_name() -> str:
    """``ANALYSIS_PIN_NAME`` read from the sibling's config, never typed."""
    text = SIBLING_CONFIG.read_text()
    found = re.search(r'^ANALYSIS_PIN_NAME\s*=\s*"([^"]+)"', text, re.M)
    if not found:
        raise SystemExit(f"{SIBLING_CONFIG}: no ANALYSIS_PIN_NAME assignment found")
    return found.group(1)


def _export_tracked(path: Path) -> bool:
    out = subprocess.run(
        ["git", "-C", str(SIBLING), "ls-files", "--error-unmatch", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    return out.returncode == 0


def _ignored_by(path: Path) -> str | None:
    out = subprocess.run(
        ["git", "-C", str(SIBLING), "check-ignore", "-v", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    return out.stdout.strip() or None


def _ast(node: dict[str, Any]) -> dict[str, Any]:
    return (node.get("annotations") or {}).get("PROCESS_ast_info") or {}


def first_visit_order(process_line_order: list[str]) -> list[str]:
    """The rule ``figures.walk_rank`` applies: each name at its first position."""
    seen: dict[str, int] = {}
    for position, name in enumerate(process_line_order):
        seen.setdefault(name, position)
    return [name for _, name in sorted((p, n) for n, p in seen.items())]


def sibling_order(export: Path) -> list[str]:
    """The same order by the sibling's own ``driver_order``, in ``ESL_env``."""
    if not ESL_PYTHON.exists():
        raise SystemExit(
            f"{ESL_PYTHON} is not present: the row order is cross-checked with "
            f"the sibling's own PROCESS_DSM.output.figures.driver_order and "
            f"the file is not written without that check"
        )
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    with tempfile.TemporaryDirectory(prefix="gen_function_counts_") as scratch:
        out = subprocess.run(
            [str(ESL_PYTHON), "-c", _SIBLING_ORDER_SCRIPT, str(SIBLING_SRC), str(export)],
            capture_output=True,
            text=True,
            check=False,
            cwd=scratch,
            env=env,
        )
    if out.returncode != 0:
        raise SystemExit(
            f"the sibling's driver_order could not be run on {export}:\n{out.stderr}"
        )
    lines = out.stdout.splitlines()
    if "---rows---" not in lines:
        raise SystemExit(f"the sibling's driver_order printed no row sentinel:\n{out.stdout}")
    return [line.strip() for line in lines[lines.index("---rows---") + 1 :] if line.strip()]


def module_ranges(node_map: dict[str, Any]) -> dict[str, list[tuple[int, int]]]:
    return {
        module: [(int(a), int(b)) for a, b in entry.get("dsm_rows") or []]
        for module, entry in (node_map.get("modules") or {}).items()
    }


def module_of_row(row: int, ranges: dict[str, list[tuple[int, int]]]) -> str | None:
    hits = [m for m, spans in ranges.items() if any(a <= row <= b for a, b in spans)]
    if len(hits) > 1:
        raise SystemExit(f"row {row} falls in two module ranges: {hits}")
    return hits[0] if hits else None


def once_per_run_nodes(configuration: str) -> list[str]:
    """The configuration's deferred nodes, from the harness's committed
    per-run artifacts (both variants where a pulsed configuration has two;
    their sets must agree)."""
    names = [f"defer_per_run_{configuration}.json", f"defer_per_run_lifted_{configuration}.json"]
    sets: dict[str, list[str]] = {}
    for name in names:
        path = V4 / "harness" / "data" / name
        if path.exists():
            sets[name] = sorted(str(n) for n in json.loads(path.read_text())["post_solve_nodes"])
    if not sets:
        raise SystemExit(f"{configuration}: no per-run artifact in harness/data/")
    if len({tuple(v) for v in sets.values()}) != 1:
        raise SystemExit(f"{configuration}: the per-run artifacts disagree: {sets}")
    return next(iter(sets.values()))


def container_owned_classes() -> tuple[dict[str, set[str]], str]:
    """``models.<attribute>`` → the classes it can be, from the copied driver's
    own model container, by the harness's own derivation."""
    sys.path.insert(0, str(V4))
    from harness.child.postsolve import container_classes  # noqa: PLC0415

    tree = V4 / "PROCESS"
    owned, _diagnostics = container_classes(tree)
    return owned, _sha256(tree / "process" / "main.py")


def node_attribute(invocation: str) -> str | None:
    found = re.match(r"models\.(\w+)", invocation)
    return found.group(1) if found else None


def build_configuration(
    configuration: str,
    node_map: dict[str, Any],
    tokamak_assignment: dict[str, str] | None,
    owned: dict[str, set[str]],
) -> dict[str, Any]:
    export = SIBLING / "output" / DSM_EXPORT[configuration] / "process_dependencies.json"
    data = json.loads(export.read_text())
    nodes: dict[str, dict[str, Any]] = data["nodes"]
    by_name = {n["name"]: n for n in nodes.values() if n["kind"] in ("model", "workflow_driver")}
    if len(by_name) != sum(1 for n in nodes.values() if n["kind"] in ("model", "workflow_driver")):
        raise SystemExit(f"{configuration}: two actors share a name; the mapping by name is refused")

    # --- the hierarchy is exactly two deep --------------------------------
    deeper = sorted(
        nodes[c]["name"]
        for n in nodes.values()
        if n["kind"] in ("model", "workflow_driver") and n.get("parent") is None
        for c in n.get("children") or []
        if nodes[c].get("children")
    )
    if deeper:
        raise SystemExit(
            f"{configuration}: sub-actors with children of their own: {deeper}; "
            f"the hierarchy is stated to be exactly two deep and is not"
        )

    # --- the row order: the export's own annotation, by the sibling's rule,
    #     cross-checked with the sibling's own function ---------------------
    line = _ast(data).get("process_line_order") or []
    order = first_visit_order([str(n) for n in line])
    top = sorted(n["name"] for n in by_name.values() if n.get("parent") is None)
    off_walk = sorted(set(top) - set(order))
    not_top = sorted(set(order) - set(top))
    if off_walk or not_top:
        raise SystemExit(
            f"{configuration}: top-level actors off the process line {off_walk}; "
            f"names on the line that are not top-level actors {not_top}"
        )
    theirs = sibling_order(export)
    if theirs != order:
        raise SystemExit(
            f"{configuration}: the sibling's driver_order gives a different row "
            f"order from the first-visit rule over process_line_order; first "
            f"difference at row "
            f"{next(i + 1 for i, (a, b) in enumerate(zip(theirs, order)) if a != b) if any(a != b for a, b in zip(theirs, order)) else min(len(theirs), len(order)) + 1}"
        )

    ranges = module_ranges(node_map)
    drivers_by_row = {
        int(k): v for k, v in ((node_map["units"]["dsm_rows"].get("not_executed_in_a_sweep") or {}).items())
    }

    rows: list[dict[str, Any]] = []
    assignment_here: dict[str, str] = {}
    unassigned: list[dict[str, Any]] = []
    ranges_apply = True
    first_disagreement: dict[str, Any] | None = None
    for index, name in enumerate(order, start=1):
        node = by_name[name]
        info = _ast(node)
        children = [nodes[c] for c in node.get("children") or []]
        n_sub = sum(1 for c in children if c["kind"] == "model")
        n_subdrivers = sum(1 for c in children if c["kind"] == "workflow_driver")
        by_range = module_of_row(index, ranges)
        entry: dict[str, Any] = {
            "row": index,
            "model": name,
            "kind": node["kind"],
            "class_name": info.get("class_name"),
            "entry_method": info.get("entry_method"),
            "model_type": info.get("model_type"),
            "submodels": n_sub,
            "subdrivers": n_subdrivers,
            "functions": max(1, n_sub) if node["kind"] == "model" else 0,
            "functions_alternative": (1 + n_sub) if node["kind"] == "model" else 0,
        }
        if node["kind"] == "workflow_driver":
            expected = drivers_by_row.get(index)
            entry["module"] = None
            entry["assigned_by"] = (
                f"a top-level driver row; the node map's not_executed_in_a_sweep "
                f"names row {index} {expected!r}"
            )
            if expected != name:
                ranges_apply = False
                first_disagreement = first_disagreement or {
                    "row": index, "model": name, "node_map_says": expected,
                }
            rows.append(entry)
            continue
        if tokamak_assignment is None:
            # the tokamak export: the node map's own row ranges are D8
            module = by_range
            entry["module"] = module
            entry["assigned_by"] = "the node map's row ranges (decision D8)"
            if module is None:
                ranges_apply = False
                first_disagreement = first_disagreement or {
                    "row": index, "model": name, "module_by_the_node_map_row_range": None,
                }
                unassigned.append({
                    "row": index,
                    "model": name,
                    "note": KNOWN_DRIFT.get(
                        name,
                        "a model row outside every module range of the node "
                        "map; not in any module's count",
                    ),
                })
            else:
                assignment_here[name] = module
        else:
            module = tokamak_assignment.get(name)
            if module is not None:
                entry["assigned_by"] = "model name, from the tokamak export's D8 assignment"
            elif name in SUBSTITUTIONS:
                module, reason = SUBSTITUTIONS[name]
                entry["assigned_by"] = f"documented substitution: {reason}"
            else:
                entry["assigned_by"] = "NOT ASSIGNED: not in the tokamak export and no documented substitution"
                unassigned.append({
                    "row": index,
                    "model": name,
                    "note": KNOWN_DRIFT.get(
                        name,
                        "a model the tokamak export does not have and no "
                        "committed sentence places",
                    ),
                })
            entry["module"] = module
            if module is not None:
                assignment_here[name] = module
            if by_range != module:
                ranges_apply = False
                first_disagreement = first_disagreement or {
                    "row": index,
                    "model": name,
                    "module_by_name": module,
                    "module_by_the_node_map_row_range": by_range,
                }
        entry["module_by_the_node_map_row_range"] = by_range
        rows.append(entry)

    # --- per module -----------------------------------------------------
    modules: dict[str, dict[str, Any]] = {}
    for module in ("M1", "M2", "M3", "PULSE", "FF"):
        members = [r for r in rows if r.get("module") == module]
        modules[module] = {
            "label": node_map["modules"][module]["label"],
            "n_dsm_rows": len(members),
            "n_dsm_rows_in_the_node_map": int(node_map["modules"][module]["n_dsm_rows"]),
            "submodels": sum(r["submodels"] for r in members),
            "subdrivers": sum(r["subdrivers"] for r in members),
            "functions": sum(r["functions"] for r in members),
            "functions_alternative": sum(r["functions_alternative"] for r in members),
            "rows": [r["row"] for r in members],
            "models": [r["model"] for r in members],
        }

    # --- the nodes: driver node -> DSM row(s), derived -------------------
    node_rows: dict[str, Any] = {}
    for node_name, spec in (node_map.get("nodes") or {}).items():
        if spec.get("kind") != "model_call":
            continue
        attribute = node_attribute(str(spec.get("invocation") or ""))
        classes = sorted(owned.get(attribute or "", set()))
        here = [r for r in rows if r["kind"] == "model" and r["class_name"] in classes]
        node_rows[node_name] = {
            "attribute": attribute,
            "module_in_the_node_map": spec.get("module"),
            "classes_the_container_can_make_it": classes,
            "rows_in_this_export": [r["row"] for r in here],
            "models": [r["model"] for r in here],
            "modules_of_those_rows": sorted({str(r["module"]) for r in here}),
            "functions": sum(r["functions"] for r in here),
            "functions_alternative": sum(r["functions_alternative"] for r in here),
            "one_row": len(here) == 1,
        }

    once = once_per_run_nodes(configuration)
    once_check: list[dict[str, Any]] = []
    for node_name in once:
        spec = node_rows.get(node_name)
        if spec is None or not spec["one_row"]:
            raise SystemExit(
                f"{configuration}: once-per-run node {node_name!r} resolves to "
                f"{spec and spec['models']}; exactly one DSM row is required for "
                f"the v = 1 attribution and it is not guessed"
            )
        home = spec["module_in_the_node_map"]
        row_module = spec["modules_of_those_rows"][0]
        if home != row_module:
            raise SystemExit(
                f"{configuration}: once-per-run node {node_name!r} is in module "
                f"{home!r} by the node map and its DSM row {spec['rows_in_this_export']} "
                f"is in {row_module!r}; the two attributions must agree"
            )
        once_check.append({
            "node": node_name,
            "row": spec["rows_in_this_export"][0],
            "model": spec["models"][0],
            "module": home,
            "functions": spec["functions"],
            "functions_alternative": spec["functions_alternative"],
        })

    stat = export.stat()
    return {
        "dsm_configuration": DSM_EXPORT[configuration],
        "export": {
            "path": str(export),
            "sha256": _sha256(export),
            "bytes": stat.st_size,
            "mtime_utc": _dt.datetime.fromtimestamp(stat.st_mtime, _dt.timezone.utc).isoformat(),
            "tracked_in_the_sibling": _export_tracked(export),
            "ignored_by": _ignored_by(export),
            "graph_name": data.get("name"),
            "n_nodes": len(nodes),
            "n_top_level_actors": len(order),
            "n_supermodels": sum(1 for r in rows if r["kind"] == "model"),
            "n_top_level_drivers": sum(1 for r in rows if r["kind"] == "workflow_driver"),
            "n_submodels": sum(r["submodels"] for r in rows),
            "n_subdrivers": sum(r["subdrivers"] for r in rows),
        },
        "row_order": {
            "rule": (
                "each top-level actor at its first position on the export's "
                "annotations.PROCESS_ast_info.process_line_order (the sibling's "
                "figures.walk_rank), which is the row order of its unsequenced "
                "collapsed figure (figures.driver_order, interleave_drivers=True)"
            ),
            "cross_checked_with": (
                "PROCESS_DSM.output.figures.driver_order run on this export in "
                "the sibling's own environment; the two orders agree row for row"
            ),
            "row_ranges_of_the_node_map_apply": ranges_apply,
            "first_row_on_which_they_do_not": first_disagreement,
        },
        "once_per_run_nodes": once_check,
        "modules": modules,
        "unassigned_rows": unassigned,
        "rows": rows,
        "nodes": node_rows,
    }


def main() -> int:
    node_map = json.loads(NODE_MAP.read_text())
    owned, main_sha = container_owned_classes()
    sibling_head = _git("rev-parse", "HEAD", cwd=SIBLING)
    sibling_dirty = _git("status", "--porcelain", cwd=SIBLING)
    pin = _pin_name()
    if pin != node_map.get("dsm_pin"):
        raise SystemExit(
            f"the sibling's pin is {pin!r} and the node map was generated at "
            f"{node_map.get('dsm_pin')!r}; two coordinate systems"
        )

    configurations: dict[str, Any] = {}
    tokamak = build_configuration("large_tokamak_nof", node_map, None, owned)
    tokamak_assignment = {
        r["model"]: r["module"] for r in tokamak["rows"] if r.get("module") is not None
    }
    configurations["large_tokamak_nof"] = tokamak
    for configuration in ("low_aspect_ratio_DEMO", "st_regression"):
        configurations[configuration] = build_configuration(
            configuration, node_map, tokamak_assignment, owned
        )

    # --- the printed assertions -------------------------------------------
    expected = {m: int(node_map["modules"][m]["n_dsm_rows"]) for m in ("M1", "M2", "M3", "PULSE", "FF")}
    for configuration, block in configurations.items():
        counts = {m: block["modules"][m]["n_dsm_rows"] for m in expected}
        applies = block["row_order"]["row_ranges_of_the_node_map_apply"]
        print(f"{configuration}: {block['export']['n_top_level_actors']} actor rows; "
              f"rows per module {counts} (node map {expected}); "
              f"row ranges apply: {applies}")
        if configuration == "large_tokamak_nof":
            in_sweep = {m: counts[m] for m in ("M1", "M2", "M3", "PULSE")}
            want = {m: expected[m] for m in in_sweep}
            if in_sweep != want:
                raise SystemExit(
                    f"{configuration}: the four in-sweep modules count {in_sweep} "
                    f"rows by the node map's ranges, the map states {want}"
                )
            if counts["FF"] != expected["FF"]:
                raise SystemExit(
                    f"{configuration}: FF counts {counts['FF']} rows by range, the map states {expected['FF']}"
                )
        for u in block["unassigned_rows"]:
            print(f"  UNASSIGNED row {u['row']} {u['model']}: {u['note']}")
        if block["row_order"]["first_row_on_which_they_do_not"]:
            print(f"  first row on which the node map's ranges do not hold: "
                  f"{block['row_order']['first_row_on_which_they_do_not']}")
        for m in expected:
            b = block["modules"][m]
            print(f"  {m:5} rows {b['n_dsm_rows']:2}  functions {b['functions']:4}  "
                  f"(1 + submodels: {b['functions_alternative']:4}; subdrivers {b['subdrivers']})")
        for o in block["once_per_run_nodes"]:
            print(f"  once per run: {o['node']:10} -> row {o['row']:2} {o['model']:10} "
                  f"({o['module']}) functions {o['functions']} / {o['functions_alternative']}")

    payload: dict[str, Any] = {
        "format": "dsm-function-counts-1",
        "generated_by": "arch_surgery/fixedpoint/gen_function_counts.py",
        "what": (
            "the number of functions behind each collapsed-DSM row of each "
            "module, per configuration, from the dependency-analysis study's "
            "per-configuration exports; the weight of the function-weighted "
            "twin of the per-module sweep tables"
        ),
        "definition": {
            "function": (
                "a submodel of the dependency analysis: a node of kind 'model' "
                "with a parent -- one callable of a supermodel (TERMINOLOGY.md "
                "section 2); a supermodel with no submodel counts as one function, "
                "its entry method.  functions(row) = max(1, submodels(row))"
            ),
            "alternative": (
                "1 + submodels(row): the entry method counted beside its "
                "callables.  Recorded as functions_alternative on every row, "
                "module and node so the report can state whether the "
                "definition matters; not the weight the tables use"
            ),
            "subdrivers": (
                "a workflow_driver with a parent (an embedded root-finder) "
                "sequences rather than computes (TERMINOLOGY.md section 1) and "
                "is counted beside the functions, never among them"
            ),
            "row": (
                "one top-level actor of the unsequenced collapsed DSM at its "
                "first position on the process line; rows 1-3 and the last row "
                "are the top-level drivers and are in no module"
            ),
        },
        # No commit of this tree is stamped: the file must reproduce byte for
        # byte on a re-run, and the commit that adds it is its stamp
        # (harness/data/PROVENANCE.json records the source commit of the copy).
        "dsm_pin": pin,
        "dsm_pin_read_from": str(SIBLING_CONFIG.relative_to(SIBLING)),
        "node_map": {
            "path": str(NODE_MAP.relative_to(TREE)),
            "sha256": _sha256(NODE_MAP),
            "dsm_pin": node_map.get("dsm_pin"),
            "tree_git_head": node_map.get("tree_git_head"),
            "n_dsm_rows_per_module": expected,
        },
        "sibling": {
            "repository": str(SIBLING),
            "git_head": sibling_head,
            "working_tree_clean": sibling_dirty == "",
            "exports_are_tracked_there": False,
            "note": (
                "the exports under output/ are gitignored in the sibling, so they "
                "have no committed state of their own; 'their committed state' "
                "is the sibling's HEAD at the time of reading together with each "
                "export's own sha256 and modification time recorded per "
                "configuration below.  A re-run against a regenerated export "
                "changes the digest, so a re-pin is visible rather than silent "
                "(trap T9)"
            ),
            "row_order_function": "PROCESS_DSM.output.figures.driver_order(interleave_drivers=True)",
            "row_order_environment": "ESL_env, PYTHONDONTWRITEBYTECODE=1, working directory in scratch",
        },
        "driver_model_container": {
            "path": "arch_surgery/MDA_partitioning_experiment_v4/PROCESS/process/main.py",
            "sha256": main_sha,
            "derived_by": "harness.child.postsolve.container_classes",
        },
        "substitutions": {
            name: {"module": module, "why": why} for name, (module, why) in SUBSTITUTIONS.items()
        },
        "known_drift": KNOWN_DRIFT,
        "configurations": configurations,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2) + "\n"
    OUT.write_text(text)
    print(f"wrote {OUT}")
    print(f"  sha256 {hashlib.sha256(text.encode()).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
