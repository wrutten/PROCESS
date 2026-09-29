#!/usr/bin/env python
"""Function-level (submodel) feedback sets from the DSM, against the census cut set.

The user, 2026-09-29, on V5 improvement item 6: *"we did not evaluate the DSM
based feedback decoupling using the expanded sequenced DSM: so a SCC based
decoupling on a function level. How close does that come to the cut-set
derived with the census?"*

Three DSM-derived sets of coupling-state components, per configuration, read
from the sibling's per-configuration export at submodel level (its "expanded"
DSM: 417 submodels on the tokamak, each with ``submodel_execution_order`` and
data edges to the variables it reads and writes):

``function_feedback_code_order``
    a component written by submodel W and read by a submodel R that executes
    before W in the export's submodel execution order (the code order at
    function level) — the function-level analogue of ``test_sets.json``'s
    model-level ``feedback`` set;
``cycle_variables``
    a component carried by an edge inside a strongly connected component of
    the submodel graph — a variable that lies on some cycle.  Under *any*
    sequencing, a tear set is a subset of this set, so it bounds the SCC-based
    decoupling from above without computing the sibling's sequenced order;
``function_feedback_min_order``
    the feedback set under a cheap sequencing of each SCC: the submodels of
    a component ordered by execution order, with the feedback set recomputed
    after moving each submodel to the position that minimises the number of
    feedback variables (a greedy pass; the sibling's own sequencing may do
    better — this is a floor on how much a sequencing can shrink the set, not
    the optimum).

Each is compared with the census cut set (``rbw_sets.json``, flat loop, arm
``A0``) and with the model-level DSM feedback set (``test_sets.json``).

Read-only over the sibling's exports (trap T9: digests recorded).  Output
``function_level_sets.json`` beside this script; the summary is printed.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
SIBLING = Path("/home/wrutten/projects/PROCESS_code_analysis")
DSM_EXPORT = {"large_tokamak_nof": "tokamak", "low_aspect_ratio_DEMO": "low_aspect_ratio_DEMO",
              "st_regression": "st_regression"}
OUT = HERE / "function_level_sets.json"


def sccs(succ: dict[str, set[str]]) -> list[set[str]]:
    """Tarjan, iterative."""
    index: dict[str, int] = {}
    low: dict[str, int] = {}
    on: set[str] = set()
    stack: list[str] = []
    out: list[set[str]] = []
    counter = [0]
    for root in succ:
        if root in index:
            continue
        work = [(root, iter(succ[root]))]
        index[root] = low[root] = counter[0]; counter[0] += 1
        stack.append(root); on.add(root)
        while work:
            v, it = work[-1]
            advanced = False
            for w in it:
                if w not in index:
                    index[w] = low[w] = counter[0]; counter[0] += 1
                    stack.append(w); on.add(w)
                    work.append((w, iter(succ[w])))
                    advanced = True
                    break
                elif w in on:
                    low[v] = min(low[v], index[w])
            if advanced:
                continue
            work.pop()
            if work:
                low[work[-1][0]] = min(low[work[-1][0]], low[v])
            if low[v] == index[v]:
                comp = set()
                while True:
                    w = stack.pop(); on.discard(w); comp.add(w)
                    if w == v:
                        break
                out.append(comp)
    return out


def feedback_under(order: dict[str, int], writers, readers, keys):
    out = set()
    for k in keys:
        ws, rs = writers.get(k, ()), readers.get(k, ())
        if any(order[r] < order[w] for w in ws for r in rs if r != w):
            out.add(k)
    return out


def derive(configuration: str, y_keys: list[str]) -> dict:
    path = SIBLING / "output" / DSM_EXPORT[configuration] / "process_dependencies.json"
    raw = path.read_bytes()
    d = json.loads(raw)
    N, E = d["nodes"], d["edges"]
    info = lambda u: N[u]["annotations"].get("PROCESS_ast_info", {})  # noqa: E731
    subs = {u for u, n in N.items() if n["kind"] == "model" and info(u).get("level") == "submodel"
            and info(u).get("submodel_execution_order") is not None}
    order = {u: int(info(u)["submodel_execution_order"]) for u in subs}
    name = lambda u: f"{info(u).get('parent_model')}.{info(u).get('function_name')}"  # noqa: E731
    writers, readers = defaultdict(set), defaultdict(set)
    for e in E.values():
        if e["kind"] != "data_interface":
            continue
        s, t = e["source"], e["target"]
        if s in subs and N[t]["kind"] == "variable":
            writers[N[t]["name"]].add(s)
        elif t in subs and N[s]["kind"] == "variable":
            readers[N[s]["name"]].add(t)
    y = set(y_keys)
    fb_code = feedback_under(order, writers, readers, y)
    # submodel graph on y: W -> R for every y component W writes and R reads
    succ = {u: set() for u in subs}
    var_edges = defaultdict(set)
    for k in y:
        for w in writers.get(k, ()):
            for r in readers.get(k, ()):
                if r != w:
                    succ[w].add(r); var_edges[(w, r)].add(k)
    comps = [c for c in sccs(succ) if len(c) > 1]
    comp_of = {u: i for i, c in enumerate(comps) for u in c}
    cycle_vars = set()
    for (w, r), ks in var_edges.items():
        if w in comp_of and comp_of.get(r) == comp_of[w]:
            cycle_vars |= ks
    # greedy sequencing within each SCC: move one submodel at a time to the
    # position that minimises the feedback count, until no move helps
    best_order = dict(order)
    for comp in comps:
        members = sorted(comp, key=lambda u: best_order[u])
        improved = True
        while improved:
            improved = False
            for u in list(members):
                current = len(feedback_under(best_order, writers, readers, cycle_vars))
                best_pos, best_val = None, current
                for pos in range(len(members)):
                    trial = [m for m in members if m != u]
                    trial.insert(pos, u)
                    slots = sorted(best_order[m] for m in members)
                    o = dict(best_order); o.update({m: s for m, s in zip(trial, slots)})
                    val = len(feedback_under(o, writers, readers, cycle_vars))
                    if val < best_val:
                        best_pos, best_val = pos, val
                if best_pos is not None:
                    trial = [m for m in members if m != u]; trial.insert(best_pos, u)
                    slots = sorted(best_order[m] for m in members)
                    best_order.update({m: s for m, s in zip(trial, slots)})
                    members = trial; improved = True
    fb_min = feedback_under(best_order, writers, readers, y)
    return {
        "export": {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest()},
        "n_submodels_ordered": len(subs),
        "n_sccs_on_y": len(comps),
        "scc_sizes": sorted((len(c) for c in comps), reverse=True),
        "sets": {"function_feedback_code_order": sorted(fb_code),
                 "cycle_variables": sorted(cycle_vars),
                 "function_feedback_min_order": sorted(fb_min)},
        "submodel_names_by_scc": [sorted(name(u) for u in c) for c in comps],
    }


def main() -> None:
    ts = json.loads((HERE / "test_sets.json").read_text())["configurations"]
    rbw = json.loads((HERE / "rbw_sets.json").read_text())["configurations"]
    out = {"format": "function-level-sets-1",
           "generated_by": "arch_surgery/coupling_subset_trial/derive_function_level_sets.py",
           "configurations": {}}
    for c in DSM_EXPORT:
        y_keys = list(ts[c]["components"])
        r = derive(c, y_keys)
        census = set(rbw[c]["A0"]["sets"]["FLAT"])
        model_fb = set(ts[c]["sets"]["feedback"])
        comp = {}
        for label, keys in r["sets"].items():
            s = set(keys)
            comp[label] = {"n": len(s), "in_census": len(s & census),
                           "census_not_in_set": sorted(census - s),
                           "set_not_in_census": len(s - census),
                           "in_model_feedback": len(s & model_fb)}
        r["against"] = {"census_n": len(census), "model_feedback_n": len(model_fb), "sets": comp}
        out["configurations"][c] = r
        print(c, "census", len(census), "model-level DSM feedback", len(model_fb),
              "| SCCs", r["n_sccs_on_y"], r["scc_sizes"][:4])
        for label, v in comp.items():
            print(f"   {label:30s} n {v['n']:4d}  ∩census {v['in_census']:3d}  census missed {len(v['census_not_in_set']):3d}  extra {v['set_not_in_census']:4d}")
    OUT.write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    main()
