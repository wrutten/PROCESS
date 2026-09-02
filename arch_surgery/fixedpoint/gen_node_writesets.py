#!/usr/bin/env python
"""Commit the measured write set of every model node, per deck.

**Why the driver needs this.**  Plan §4.1d/§4.1e make the hoist a *routing*
rule: a node that leaves the sweep goes into the **pre-predicate** slot if the
objective or the constraint layer reads anything it writes, and into the
**post-predicate** slot otherwise.  The predicate's read set the driver can
compute from its own source; what a node *writes* it cannot, without running.

So it is measured once, here, from the same run-time write census the
experiment already takes (``PROCESS_IDF_PROBE=modules``, harvested into
``writes_by_node``), and committed as tracked data --- the same status as
``dsm_node_map.json``, which ``caller.py`` already reads, and for the same
reason (trap T9: never read a generated artifact live).

**Per node, not per module.**  ``arch_surgery/docs/data/writeset_<deck>.json``
already records write sets per *module*, which is what A25's per-module solves
need.  The FF module holds ``water_use`` and ``costs`` together, and the whole
point of the routing rule is that those two go to different slots on a deck
whose figure of merit reads ``costs``.  A module-level set cannot express that.

Usage
-----
    PYTHONPATH=<tree> python gen_node_writesets.py
    PYTHONPATH=<tree> python gen_node_writesets.py --check
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pickle
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TREE = HERE.parent.parent
RUNS = TREE / "arch_surgery" / "idf_probe" / "runs" / "a18"
OUT = TREE / "arch_surgery" / "docs" / "data" / "node_writesets.json"

SCENARIOS = [
    "large_tokamak_nof",
    "low_aspect_ratio_DEMO",
    "st_regression",
    "large_tokamak_eval",
]


def build(scenarios) -> dict:
    per_scenario: dict = {}
    union: dict = {}
    modules: dict = {}
    for s in scenarios:
        hp = RUNS / s / "harvest" / "harvest.pkl"
        if not hp.exists():
            continue
        with open(hp, "rb") as fh:
            h = pickle.load(fh)
        wb = {k: sorted(v) for k, v in h["writes_by_node"].items() if v}
        per_scenario[s] = {
            "node_module": dict(h["node_module"]),
            "writes_by_node": wb,
            "n_nodes": len(wb),
        }
        for n, fields in wb.items():
            union.setdefault(n, set()).update(fields)
        for n, m in h["node_module"].items():
            if n in modules and modules[n] != m:
                raise AssertionError(
                    f"node {n!r} is labelled {modules[n]!r} on one deck and "
                    f"{m!r} on another; the routing rule cannot use a label "
                    f"that is not a property of the code"
                )
            modules[n] = m
    rec = {
        "format": "a26-node-writesets-1",
        "generated_by": "arch_surgery/fixedpoint/gen_node_writesets.py",
        "derived_from": (
            "PROCESS_IDF_PROBE=modules write census, per model node, inside "
            "Caller._call_models_once, from each deck's committed A18 harvest. "
            "Trap T1/T7: the census closes the sweep at the boundary of "
            "_call_models_once, so output() traffic is not in it."
        ),
        "scenarios": sorted(per_scenario),
        "node_module": dict(sorted(modules.items())),
        "writes_by_node_union": {
            k: sorted(v) for k, v in sorted(union.items())
        },
        "per_scenario": per_scenario,
    }
    h = hashlib.sha256()
    for n, fields in sorted(rec["writes_by_node_union"].items()):
        h.update(f"{n}|{','.join(fields)}\n".encode())
    rec["union_sha256"] = h.hexdigest()
    rec["tree_git_head"] = (
        subprocess.run(["git", "-C", str(TREE), "rev-parse", "HEAD"],
                       capture_output=True, text=True, check=False)
        .stdout.strip() or None
    )
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenarios", nargs="*", default=SCENARIOS)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    rec = build(args.scenarios)
    if args.check:
        if not OUT.exists():
            print(f"MISSING {OUT}")
            return 1
        cur = json.loads(OUT.read_text())
        same = cur.get("union_sha256") == rec["union_sha256"]
        print(f"{'MATCH' if same else 'DIFFERS'}  {OUT.name}  "
              f"union_sha256 committed={cur.get('union_sha256', '')[:12]} "
              f"live={rec['union_sha256'][:12]}")
        return 0 if same else 1
    OUT.write_text(json.dumps(rec, indent=1, sort_keys=False))
    print(f"{OUT}  {len(rec['writes_by_node_union'])} nodes  "
          f"sha={rec['union_sha256'][:12]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
