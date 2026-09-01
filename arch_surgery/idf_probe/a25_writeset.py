#!/usr/bin/env python
"""Generate the committed per-module write set (framework component C8b).

Phase A's block arm restricts each inner solve's convergence test to the
**module's own write set** (``fixedpoint/arms.build_blocks``), and Phase B's
per-module solver must do the same.  A25 first tried to take the test over the
whole coupling vector, on the argument that a component no running node writes
cannot move.  **That argument is wrong**, and it was the first thing the run
found: ``ystate``'s predicate scores a component ``inf`` whenever either
snapshot is not float-viewable, which is the case for every component that no
model has written yet in a fresh process -- so an M1 inner solve was held open by ``ccfe_hcpb.pnuc_tot_blk_sector``, a field M3 writes and M1 cannot
touch.  Twenty inner sweeps, cap reached, run dead.  Equality of *values* is
not equality of *scores*.

So the subsets are measured, exactly as Phase A measured them, and committed
as data:

* ``PROCESS_IDF_PROBE=modules`` attributes every data-structure write to the
  model node executing at the time.  Writes are captured both by overriding
  ``__setattr__`` (so an assignment of an unchanged value still counts) and by
  differencing snapshots at node boundaries (so in-place array mutation
  counts).  It is a **write** census, not a movement census -- which is what
  the subset needs.
* Each node is mapped to its module through the committed DSM node map.
* The union per module, intersected with the deck's ``ystate`` component set,
  is the subset the inner solve tests.

Recording is confined to ``Caller._call_models_once`` (traps T1 and T7), so no
``output()``-path write can enter a subset.

Usage
-----
    python a25_writeset.py --probe-runs <dir> --out arch_surgery/docs/data
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
TREE = HERE.parent.parent
DATA = TREE / "arch_surgery" / "docs" / "data"

SCENARIOS = [
    "large_tokamak_nof",
    "low_aspect_ratio_DEMO",
    "st_regression",
    "large_tokamak_eval",
]


def _git_head() -> str | None:
    try:
        return subprocess.run(
            ["git", "-C", str(TREE), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=False,
        ).stdout.strip() or None
    except Exception:
        return None


def build(scenario: str, probe_runs: Path) -> dict:
    node_map = json.loads((DATA / "dsm_node_map.json").read_text())
    nodes = node_map["nodes"]

    ystate = json.loads((DATA / f"ystate_{scenario}.json").read_text())
    y_keys = [c["key"] for c in ystate["components"]]
    y_index = {k: i for i, k in enumerate(y_keys)}

    probe = json.loads(
        (probe_runs / scenario / "probe_modules.json").read_text()
    )
    writes = probe["writes_by_node"]

    unmapped = sorted(
        n for n, f in writes.items() if f and n not in nodes and n != "<x_inject>"
    )
    if unmapped:
        raise AssertionError(
            f"{scenario}: nodes {unmapped} wrote state but are not named in "
            f"dsm_node_map.json"
        )

    by_module: dict[str, set[str]] = {}
    for node, fields in writes.items():
        if node == "<x_inject>":
            continue
        mod = nodes.get(node, {}).get("module")
        if not mod:
            continue
        by_module.setdefault(mod, set()).update(fields)

    subsets: dict[str, list[int]] = {}
    key_lists: dict[str, list[str]] = {}
    for mod, fields in sorted(by_module.items()):
        idx = sorted(y_index[f] for f in fields if f in y_index)
        subsets[mod] = idx
        key_lists[mod] = [y_keys[i] for i in idx]

    covered = set()
    for idx in subsets.values():
        covered.update(idx)
    uncovered = sorted(set(range(len(y_keys))) - covered)

    overlaps = {}
    mods = sorted(subsets)
    for i, a in enumerate(mods):
        for b in mods[i + 1 :]:
            both = set(subsets[a]) & set(subsets[b])
            if both:
                overlaps[f"{a}&{b}"] = sorted(y_keys[i] for i in both)

    h = hashlib.sha256()
    for mod in sorted(key_lists):
        h.update(mod.encode())
        for k in key_lists[mod]:
            h.update(b"|")
            h.update(k.encode())

    return {
        "format": "a25-writeset-1",
        "scenario": scenario,
        "generated_by": "arch_surgery/idf_probe/a25_writeset.py",
        "derived_from": (
            "PROCESS_IDF_PROBE=modules write census over a baseline run of "
            "this deck, mapped to modules through the committed DSM node map "
            "and intersected with the deck's committed ystate component set."
        ),
        "tree_git_head": _git_head(),
        "ystate_components_sha256": ystate.get("components_sha256"),
        "n_y_components": len(y_keys),
        "probe": {
            "n_sweeps": probe.get("n_sweeps"),
            "nodes_with_writes": sorted(n for n, f in writes.items() if f),
        },
        "census": {
            "n_by_module": {m: len(v) for m, v in sorted(subsets.items())},
            "n_covered": len(covered),
            "n_uncovered": len(uncovered),
            "uncovered_keys": [y_keys[i] for i in uncovered],
            "overlaps_between_modules": {
                k: len(v) for k, v in sorted(overlaps.items())
            },
        },
        "overlap_keys": overlaps,
        "subsets_sha256": h.hexdigest(),
        "subsets": {m: key_lists[m] for m in sorted(key_lists)},
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe-runs", required=True)
    ap.add_argument("--out", default=str(DATA))
    ap.add_argument("--scenarios", nargs="*", default=SCENARIOS)
    args = ap.parse_args()

    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    probe_runs = Path(args.probe_runs).resolve()

    for s in args.scenarios:
        rec = build(s, probe_runs)
        (out / f"writeset_{s}.json").write_text(json.dumps(rec, indent=2))
        c = rec["census"]
        print(
            f"{s:24s} by module {c['n_by_module']}  covered "
            f"{c['n_covered']}/{rec['n_y_components']}  uncovered "
            f"{c['n_uncovered']}  overlaps {c['overlaps_between_modules']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
