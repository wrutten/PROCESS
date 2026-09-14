"""Every run record under ``runs/``, by the commit it was made at.

The survey behind the sentence *"this press re-made no run"*.  Trap **T13**: a
``--resume`` that consults anything but the record is not a resume, and the one
way to tell a kept run from a re-made one afterwards is the commit stamped in
the record itself.  So: read ``tree_git_head`` out of every ``metrics.json``
under ``runs/``, print the histogram and the per-record list, and — with
``--against <path>`` — diff two surveys record by record.

Usage::

    python run_stamp_survey.py --json before.json
    python run_stamp_survey.py --json after.json --against before.json

A record with no ``tree_git_head`` at the top level is reported as such rather
than as a commit, because a provenance block one level down is invisible to a
top-level survey (I-22 (b), trap **T14**) and a survey that silently called it
"None" would hide that.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNS = HERE / "runs"


def survey(root: Path) -> dict:
    """``{relative path: commit or None}`` for every run record under *root*."""
    records: dict[str, str | None] = {}
    for path in sorted(root.rglob("metrics.json")):
        try:
            data = json.loads(path.read_text())
        except Exception:  # noqa: BLE001 - a half-written record is a finding
            records[str(path.relative_to(root))] = "UNREADABLE"
            continue
        head = data.get("tree_git_head")
        records[str(path.relative_to(root))] = head if isinstance(head, str) else None
    histogram: dict[str, int] = {}
    for head in records.values():
        key = head or "no top-level tree_git_head"
        histogram[key] = histogram.get(key, 0) + 1
    return {
        "root": str(root),
        "n_records": len(records),
        "by_commit": dict(sorted(histogram.items())),
        "records": records,
    }


def report(block: dict) -> None:
    print(f"run records under {block['root']}: {block['n_records']}")
    for commit, count in block["by_commit"].items():
        print(f"  {count:>4}  {commit}")


def compare(now: dict, before: dict) -> int:
    """0 when every record is unchanged; 1 naming each one that moved."""
    moved = [
        (path, before["records"].get(path), head)
        for path, head in now["records"].items()
        if before["records"].get(path) != head
    ]
    gone = sorted(set(before["records"]) - set(now["records"]))
    added = sorted(set(now["records"]) - set(before["records"]))
    print(
        f"\ncompared with {before['root']} "
        f"({before['n_records']} record(s) then, {now['n_records']} now):"
    )
    print(f"  records whose commit changed : {len(moved)}")
    print(f"  records that disappeared     : {len(gone)}")
    print(f"  records that are new         : {len(added)}")
    for path, was, now_head in moved:
        print(f"    MOVED {path}: {was} -> {now_head}")
    for path in gone:
        print(f"    GONE  {path}")
    for path in added:
        print(f"    NEW   {path}: {now['records'][path]}")
    return 0 if not (moved or gone or added) else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", default=str(RUNS), help="the runs root to survey")
    parser.add_argument("--json", help="write the survey here")
    parser.add_argument("--against", help="a survey written earlier, to compare with")
    args = parser.parse_args(argv)

    root = Path(args.runs)
    if not root.exists():
        print(f"no runs directory at {root}")
        return 2
    block = survey(root)
    report(block)
    if args.json:
        Path(args.json).write_text(json.dumps(block, indent=2))
    if args.against:
        return compare(block, json.loads(Path(args.against).read_text()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
