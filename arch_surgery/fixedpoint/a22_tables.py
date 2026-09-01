#!/usr/bin/env python
"""A22 (outer-pass-census): turn the census JSONs into the report's tables.

Prints, per scenario and never pooled across scenarios:

1. the outer-pass distribution for each arm, with the population;
2. for the block arm, which blocks move on outer pass 2 or later -- the
   unambiguous coupling detector, because a block that converged in pass 1 can
   only move again if something outside it changed;
3. the fields above tolerance on the residual that forced each extra pass,
   ranked by how often they are moving, with the model that writes each;
4. whether pinning the burn time removes the movement.
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNS = HERE.parent.parent / "arch_surgery" / "idf_probe" / "runs" / "a22"
SCENARIOS = ["large_tokamak_nof", "low_aspect_ratio_DEMO", "st_regression",
             "large_tokamak_eval"]
ARMS = ["A1", "A1pin", "A1ffit"]


def module_of(field, writer_of, node_module):
    nodes = writer_of.get(field, [])
    mods = sorted({node_module.get(n, "?") for n in nodes})
    return ("/".join(nodes) if nodes else "<unwritten>",
            "/".join(mods) if mods else "?")


def report(scenario):
    d = json.loads((RUNS / scenario / "census.json").read_text())
    writer_of = d["writer_of"]
    node_module = d["node_module"]
    n = d["n_points"]
    print("=" * 78)
    print("%s -- %d harvested design points, tau = %g, block arm"
          % (scenario, n, d["tau"]))
    print("  gate (A1 reproduces A18 exactly): %s  (%d/%d points compared)"
          % (d["gate_reproduces_a18"].get("pass"),
             d["gate_reproduces_a18"].get("n_compared", 0), n))
    print("  pulse writes the burn time in this deck: %s"
          % d["pulse_writes_burn_time"])

    for arm in ARMS:
        dist = Counter(p["arms"][arm]["outer"] for p in d["points"]
                       if p["arms"][arm].get("converged"))
        tot = sum(dist.values())
        mean = sum(k * v for k, v in dist.items()) / tot
        ge2 = sum(v for k, v in dist.items() if k >= 2)
        ge3 = sum(v for k, v in dist.items() if k >= 3)
        print("  %-7s outer passes: mean %.4f over %d/%d converged points; "
              "dist %s; >=2 passes on %d/%d; >=3 on %d/%d"
              % (arm, mean, tot, n, dict(sorted(dist.items())), ge2, n, ge3, n))

    for arm in ARMS:
        # blocks that move on outer pass >= 2
        mv = Counter()
        pts_with = set()
        for p in d["points"]:
            a = p["arms"][arm]
            if not a.get("converged"):
                continue
            for lab, lst in a["inner"]["counts"].items():
                for i, v in enumerate(lst):
                    if i >= 1 and v > 1:
                        mv[(lab, i + 1)] += 1
                        pts_with.add(p["call_index"])
        print("  %-7s blocks re-solving on outer pass >=2: %s  "
              "(on %d/%d design points)"
              % (arm, dict(sorted(mv.items())) or "none", len(pts_with), n))

    # -- which fields are moving on the residual that forced an extra pass --
    for arm in ARMS:
        print("  --- %s: fields above tau on outer pass >= 2 ---" % arm)
        per_pass = defaultdict(Counter)
        pop = Counter()
        for p in d["points"]:
            a = p["arms"][arm]
            if not a.get("converged"):
                continue
            for r in a["outer_records"]:
                if r["outer"] < 2 or r["n_above"] == 0:
                    continue
                pop[r["outer"]] += 1
                for f, _v in r["above"]:
                    per_pass[r["outer"]][f] += 1
        if not pop:
            print("      no outer pass from 2 onwards has any field above tau "
                  "on any of the %d points" % n)
            continue
        for k in sorted(pop):
            print("      outer pass %d: %d/%d design points had a non-empty "
                  "residual here" % (k, pop[k], n))
            for f, c in per_pass[k].most_common(25):
                node, mod = module_of(f, writer_of, node_module)
                print("         %5d/%-5d %-52s %-30s %s"
                      % (c, pop[k], f, node, mod))

    # -- M1's own re-solve on outer pass 2: the unambiguous back edge --------
    for arm in ARMS:
        rows = Counter()
        pop = 0
        for p in d["points"]:
            a = p["arms"][arm]
            if not a.get("converged"):
                continue
            hit = False
            for r in a["inner_records"]:
                if r["outer"] == 2 and r["block"] == "M1" and r["s"] == 1 \
                        and r["n_above"]:
                    hit = True
                    for f, _v in r["above"]:
                        rows[f] += 1
            pop += 1 if hit else 0
        print("  --- %s: fields M1 itself rewrote on its first inner sweep of "
              "outer pass 2 (%d/%d design points) ---" % (arm, pop, n))
        for f, c in rows.most_common(25):
            node, mod = module_of(f, writer_of, node_module)
            print("         %5d/%-5d %-52s %-30s %s" % (c, pop, f, node, mod))


def main() -> int:
    for s in (sys.argv[1:] or SCENARIOS):
        report(s)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
