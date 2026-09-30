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


def launch_summary(root: Path, *, load_above: float, windows: list[tuple[str, str]]) -> dict:
    """The conditions every record under *root* was made in: the commit and the
    dirty flag, the worker count and the load average the pool stamped at the
    child's spawn and return (``launcher``), per ``<phase directory>/<configuration>``;
    the records that saw a one-minute load average above *load_above*; and the
    records whose spawn-to-return interval overlaps a declared window (the
    machine's suspend, say), by name.  Added by A102 (v5-campaign)."""
    import datetime as _dt  # noqa: PLC0415
    import statistics as _st  # noqa: PLC0415

    def epoch(text: str) -> float:
        return _dt.datetime.fromisoformat(text).timestamp()

    spans = [(a, b, epoch(a), epoch(b)) for a, b in windows]
    groups: dict[str, dict] = {}
    loaded: list[dict] = []
    straddling: list[dict] = []
    for path in sorted(root.rglob("metrics.json")):
        data = json.loads(path.read_text())
        rel = path.parent.relative_to(root)
        parts = rel.parts
        key = "/".join(parts[:2]) if len(parts) >= 2 else str(rel)
        launcher = data.get("launcher") or {}
        spawn = (launcher.get("loadavg_at_spawn") or [None])[0]
        ret = (launcher.get("loadavg_at_return") or [None])[0]
        g = groups.setdefault(key, {"n": 0, "by_commit": {}, "by_workers": {}, "dirty": 0, "load_spawn": [], "load_return": []})
        g["n"] += 1
        head = str(data.get("tree_git_head"))[:8]
        g["by_commit"][head] = g["by_commit"].get(head, 0) + 1
        w = str(launcher.get("workers"))
        g["by_workers"][w] = g["by_workers"].get(w, 0) + 1
        g["dirty"] += int(bool(data.get("tree_git_dirty")))
        if spawn is not None:
            g["load_spawn"].append(float(spawn))
        if ret is not None:
            g["load_return"].append(float(ret))
        peak = max([v for v in (spawn, ret) if v is not None], default=None)
        if peak is not None and peak > load_above:
            loaded.append({"record": str(rel), "loadavg_1min_spawn": spawn, "loadavg_1min_return": ret})
        a, b = launcher.get("spawned_at"), launcher.get("returned_at")
        for w_start, w_end, e0, e1 in spans:
            if a is not None and b is not None and float(a) < e1 and float(b) > e0:
                straddling.append({"record": str(rel), "window": [w_start, w_end],
                                   "spawned": _dt.datetime.fromtimestamp(float(a)).isoformat(timespec="seconds"),
                                   "returned": _dt.datetime.fromtimestamp(float(b)).isoformat(timespec="seconds")})

    def band(values: list[float]) -> list | None:
        return [round(min(values), 2), round(_st.median(values), 2), round(max(values), 2)] if values else None

    out = {
        "root": str(root),
        "load_above": load_above,
        "windows": windows,
        "groups": {
            k: {"n": g["n"], "by_commit": g["by_commit"], "by_workers": g["by_workers"], "dirty": g["dirty"],
                "loadavg_1min_at_spawn_min_median_max": band(g["load_spawn"]),
                "loadavg_1min_at_return_min_median_max": band(g["load_return"])}
            for k, g in sorted(groups.items())
        },
        "n_records": sum(g["n"] for g in groups.values()),
        "n_above_load": len(loaded),
        "above_load": loaded,
        "straddling_a_window": straddling,
    }
    print(f"\nlaunch conditions under {root}: {out['n_records']} record(s)")
    for k, g in out["groups"].items():
        print(f"  {k:48s} n={g['n']:>3}  commits {g['by_commit']}  W {g['by_workers']}  dirty {g['dirty']}  "
              f"load@spawn {g['loadavg_1min_at_spawn_min_median_max']}  load@return {g['loadavg_1min_at_return_min_median_max']}")
    print(f"  records with a one-minute load average above {load_above} at spawn or return: {len(loaded)}")
    for r in loaded:
        print(f"    {r['record']}: {r['loadavg_1min_spawn']} -> {r['loadavg_1min_return']}")
    for r in straddling:
        print(f"  overlaps window {r['window']}: {r['record']} ({r['spawned']} -> {r['returned']})")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", default=str(RUNS), help="the runs root to survey")
    parser.add_argument("--json", help="write the survey here")
    parser.add_argument("--against", help="a survey written earlier, to compare with")
    parser.add_argument("--launch-summary", action="append", default=[],
                        help="a directory under the runs root (repeatable): print the commits, worker counts, "
                        "dirty flags and load averages its records were made with")
    parser.add_argument("--load-above", type=float, default=1.5,
                        help="for --launch-summary: name every record whose one-minute load average exceeded this")
    parser.add_argument("--window", nargs=2, action="append", default=[], metavar=("START", "END"),
                        help="for --launch-summary: an ISO local-time window (a suspend, say); name every record "
                        "whose spawn-to-return interval overlaps it")
    args = parser.parse_args(argv)

    root = Path(args.runs)
    if not root.exists():
        print(f"no runs directory at {root}")
        return 2
    block = survey(root)
    report(block)
    if args.launch_summary:
        block["launch_summaries"] = {
            sub: launch_summary(root / sub, load_above=args.load_above, windows=[tuple(w) for w in args.window])
            for sub in args.launch_summary
        }
    if args.json:
        Path(args.json).write_text(json.dumps(block, indent=2))
    if args.against:
        return compare(block, json.loads(Path(args.against).read_text()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
