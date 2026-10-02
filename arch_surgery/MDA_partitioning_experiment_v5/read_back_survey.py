"""Every run record under one run ID's folder, by the read-back key set it carries.

A record's ``resolved_switches`` block holds one entry per driver read-back the
harness's switch registry named **when the record was made**
(``harness/child/child.py:resolved_switches``, built from
``switches.default_readbacks()``).  A driver change that adds a switch adds a
read-back, so every record made before it carries one key fewer than a record
made after it, though nothing about the run differs.  ``--resume`` does not look
at this key set (``pool.why_not_kept``: the identity, the stamps, the
completeness contract and the composed switch *terms*), so a kept record and a
fresh one can differ here and nowhere else.

This survey answers, read-only, from the records alone: per area of the run ID's
folder (campaign, traced runs, the shared pool, each gate's own root, the rest),
how many records carry exactly today's read-back key set and how many do not,
which keys they lack or carry beyond today's, and the commits they were made at.
It is the measurement behind the question *"what would a resume rule that
refuses a record whose read-back set is not today's re-make?"*.  With
``--digests`` it also prints, for the named job digests (by their first sixteen
hex digits, as the pool's directory names carry them), each record's commit and
its read-back key count.

Written by task A117 (v5-switch-composition-one-commit), issue I-46.  Nothing is
written into ``runs/``; ``--json`` writes the survey where it is told.

Usage::

    python read_back_survey.py --runs runs/census_tau1e-08 [--json out.json] [--digests 159053e9aa48a93d ...]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from harness.experiment import switches as switches_mod  # noqa: E402


def todays_keys() -> frozenset[str]:
    """The read-back keys a record made by this tree's harness carries."""
    return frozenset(f"{m}.{a}" for m, a in switches_mod.default_readbacks())


def area_of(relative: Path) -> str:
    """Which part of a run ID's folder a record sits in."""
    parts = relative.parts
    if not parts:
        return "."
    if parts[0] == "gates" and len(parts) > 1:
        return "gates/_runs (shared pool)" if parts[1] == "_runs" else f"gates/{parts[1]}"
    return parts[0]


def survey(root: Path, digests: list[str]) -> dict:
    today = todays_keys()
    by_area: dict[str, Counter] = defaultdict(Counter)
    by_area_commit: dict[str, Counter] = defaultdict(Counter)
    lacking: Counter = Counter()
    beyond: Counter = Counter()
    named: list[dict] = []
    n = 0
    for path in sorted(root.rglob("metrics.json")):
        relative = path.parent.relative_to(root)
        try:
            record = json.loads(path.read_text())
        except Exception:  # noqa: BLE001 - a half-written record is a finding
            by_area[area_of(relative)]["unreadable"] += 1
            continue
        n += 1
        area = area_of(relative)
        resolved = record.get("resolved_switches")
        head = str(record.get("tree_git_head") or "no top-level tree_git_head")[:8]
        if not isinstance(resolved, dict):
            state = "no resolved_switches block"
        else:
            keys = frozenset(resolved)
            if keys == today:
                state = "today's key set"
            else:
                state = "another key set"
                for k in sorted(today - keys):
                    lacking[k] += 1
                for k in sorted(keys - today):
                    beyond[k] += 1
        by_area[area][state] += 1
        if state == "another key set":
            by_area_commit[area][head] += 1
        digest = str(record.get("job_digest") or "")
        if digest[:16] in digests:
            named.append({
                "digest": digest[:16],
                "path": str(relative),
                "tree_git_head": head,
                "n_read_back_keys": len(resolved) if isinstance(resolved, dict) else None,
                "todays_key_set": isinstance(resolved, dict) and frozenset(resolved) == today,
            })
    return {
        "root": str(root),
        "n_records": n,
        "n_todays_read_back_keys": len(today),
        "by_area": {a: dict(c) for a, c in sorted(by_area.items())},
        "another_key_set_by_area_and_commit": {a: dict(c) for a, c in sorted(by_area_commit.items())},
        "keys_lacking_against_today": dict(lacking),
        "keys_beyond_today": dict(beyond),
        "named_digests": named,
    }


def report(block: dict) -> None:
    print(f"run records under {block['root']}: {block['n_records']}; today's read-back key set: "
          f"{block['n_todays_read_back_keys']} key(s)")
    total = Counter()
    for area, states in block["by_area"].items():
        total.update(states)
        cells = ", ".join(f"{k} {v}" for k, v in sorted(states.items()))
        print(f"  {area:40s} {cells}")
    print(f"  {'(all)':40s} " + ", ".join(f"{k} {v}" for k, v in sorted(total.items())))
    print("  records with another key set, by area and commit:")
    for area, commits in block["another_key_set_by_area_and_commit"].items():
        print(f"    {area:38s} " + ", ".join(f"{c} {v}" for c, v in sorted(commits.items())))
    print(f"  keys today's set has and such records lack: {block['keys_lacking_against_today']}")
    print(f"  keys such records carry beyond today's set: {block['keys_beyond_today']}")
    for row in block["named_digests"]:
        print(f"  digest {row['digest']}  {row['tree_git_head']}  {row['n_read_back_keys']} key(s)"
              f"  {'today' if row['todays_key_set'] else 'NOT today'}  {row['path']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--runs", required=True, help="one run ID's folder, e.g. runs/census_tau1e-08")
    parser.add_argument("--json", help="write the survey here")
    parser.add_argument("--digests", nargs="*", default=[], help="job digests (16 hex digits) to list")
    args = parser.parse_args(argv)
    root = Path(args.runs)
    if not root.is_dir():
        print(f"no such folder: {root}")
        return 2
    block = survey(root, [d[:16] for d in args.digests])
    report(block)
    if args.json:
        Path(args.json).write_text(json.dumps(block, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
