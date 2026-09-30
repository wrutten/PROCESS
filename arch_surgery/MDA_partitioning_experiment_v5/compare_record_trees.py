"""Two record trees of the same optimisation jobs, compared per arm and seed.

A determinism check: two presses of the same job (the same arm,
configuration, seed, test set and tolerance, possibly of different run kinds
or at different commits whose driver is the same) must agree to the bit on
every count and on the objective.  Compared per ``<configuration>/<arm>/seedNNN``
directory present in both trees:

* ``status``, ``mfile.ifail``, ``n_solver_iterations``,
  ``sweeps_per_eval.n_evaluations``, ``node_calls_solve_phase``,
  ``exact.norm_objf`` (hex), and the iterations and ``ifail`` of every attempt
  of the optimiser's retry ladder.

Records are read through the harness (``records.read``: the recorded arm
names are translated, trap T16), never by loading the JSON by hand.  Exit 0
when every compared job agrees on every field, 1 naming each that does not.
Written by A102 (v5-campaign): the supplementary stage's first press made
smoke records (the runner's ``--run-kind`` defaulted to ``smoke``) before it
was stopped; the stage's records made after the fix are compared with them.

Usage::

    python compare_record_trees.py <tree A> <tree B> [--json out.json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from harness.core import records as records_mod  # noqa: E402

FIELDS: tuple[str, ...] = (
    "status",
    "mfile.ifail",
    "n_solver_iterations",
    "sweeps_per_eval.n_evaluations",
    "node_calls_solve_phase",
    "exact.norm_objf",
)


def _at(record, path):
    return records_mod.resolve_path(record, path) if records_mod.has_path(record, path) else None


def fields_of(record) -> dict:
    out = {path: _at(record, path) for path in FIELDS}
    out["attempts"] = [(a.get("n_iterations"), a.get("ifail")) for a in record.get("attempts") or []]
    return out


def jobs(root: Path) -> dict[str, Path]:
    return {
        str(p.parent.relative_to(root)): p.parent
        for p in sorted(root.rglob("metrics.json"))
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("tree_a", type=Path)
    parser.add_argument("tree_b", type=Path)
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args(argv)
    a, b = jobs(args.tree_a), jobs(args.tree_b)
    common = sorted(set(a) & set(b))
    rows = []
    for key in common:
        ra, rb = records_mod.read(a[key]), records_mod.read(b[key])
        fa, fb = fields_of(ra), fields_of(rb)
        differing = sorted(k for k in fa if fa[k] != fb[k])
        rows.append(
            {
                "job": key,
                "identical": not differing,
                "differing": {k: [fa[k], fb[k]] for k in differing},
                "run_kind": [ra.get("campaign_run_kind"), rb.get("campaign_run_kind")],
                "tree_git_head": [str(ra.get("tree_git_head"))[:8], str(rb.get("tree_git_head"))[:8]],
                "campaign_tau": [ra.get("campaign_tau"), rb.get("campaign_tau")],
            }
        )
    n_diff = sum(1 for r in rows if not r["identical"])
    print(f"tree A: {args.tree_a} ({len(a)} record(s)); tree B: {args.tree_b} ({len(b)} record(s))")
    print(f"jobs in both: {len(common)}; only in A: {len(set(a) - set(b))}; only in B: {len(set(b) - set(a))}")
    print(f"fields compared per job: {len(FIELDS) + 1} ({', '.join(FIELDS)}, attempts)")
    for r in rows:
        mark = "identical" if r["identical"] else f"DIFFERS on {sorted(r['differing'])}"
        print(f"  {r['job']:40s} {mark}  kinds {r['run_kind']}  at {r['tree_git_head']}  tau {r['campaign_tau']}")
    print(f"{len(common) - n_diff} of {len(common)} job(s) identical on every field; {n_diff} differ")
    if args.json:
        args.json.write_text(json.dumps({"tree_a": str(args.tree_a), "tree_b": str(args.tree_b), "only_in_a": sorted(set(a) - set(b)), "only_in_b": sorted(set(b) - set(a)), "rows": rows}, indent=2) + "\n")
    return 0 if n_diff == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
