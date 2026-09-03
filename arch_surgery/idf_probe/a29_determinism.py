#!/usr/bin/env python
"""A29 (replication-verify): bit-for-bit comparison of one re-run stage.

Compares two directory trees produced by running the SAME experiment stage
twice, and reports -- with denominators -- how many quantities are identical
as bits and every one that is not.

What is compared, and what is excluded, is stated here rather than buried:

* ``*.json``            every leaf value, compared as exact Python equality
                        (which for floats parsed by ``json`` is bit equality),
                        EXCLUDING leaves whose path contains a timing key
                        (``wall_s``, ``cpu_user_s``, ``cpu_sys_s``, ``cpu_s``,
                        ``process_runtime``, ``wall_s_subprocess``) or a git
                        provenance key (``tree_git_head``, ``tree_git_describe``,
                        ``tree_git_dirty``, ``tree_git_branch``) -- a commit made
                        between the two runs changes those without changing any
                        measured quantity.  Excluded leaves are COUNTED and
                        reported, never silently dropped.
* ``*MFILE.DAT``        every line, EXCLUDING lines tagged ``(date)``,
                        ``(time)`` or ``(process_runtime)`` -- the three
                        volatile tags in an MFILE.
* ``*OUT.DAT``          every line, EXCLUDING lines containing ``Date of run``,
                        ``Time of run`` or ``Runtime of PROCESS``.
* logs (``*.log``), ``_mplconfig``: not compared (they carry timings and
  progress text by design); counted as skipped.

Exit code 0 if every compared quantity agrees, 1 otherwise.

A comparator that has never failed is an assertion, not a measurement
(protocol section 12), so ``selftest`` copies a tree, flips one float's last
digit in one JSON and one MFILE line, and confirms both flips are caught.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

TIMING_KEYS = ("wall_s", "cpu_user_s", "cpu_sys_s", "cpu_s",
               "process_runtime", "wall_s_subprocess")
PROVENANCE_KEYS = ("tree_git_head", "tree_git_describe", "tree_git_dirty",
                   "tree_git_branch")
MFILE_VOLATILE = ("(date)", "(time)", "(process_runtime)")
OUT_VOLATILE = ("Date of run", "Time of run", "Runtime of PROCESS")


def _leaves(o, path=""):
    if isinstance(o, dict):
        for k, v in sorted(o.items()):
            yield from _leaves(v, f"{path}/{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from _leaves(v, f"{path}[{i}]")
    else:
        yield path, o


def _excluded(path: str) -> bool:
    last = path.rsplit("/", 1)[-1].split("[", 1)[0]
    return last in TIMING_KEYS or last in PROVENANCE_KEYS


def compare_json(a: Path, b: Path):
    da, db = json.loads(a.read_text()), json.loads(b.read_text())
    la = dict(_leaves(da))
    lb = dict(_leaves(db))
    n_cmp = n_diff = n_excl = 0
    diffs = []
    for p in sorted(set(la) | set(lb)):
        if _excluded(p):
            n_excl += 1
            continue
        n_cmp += 1
        va, vb = la.get(p, "<ABSENT>"), lb.get(p, "<ABSENT>")
        same = (va == vb) or (isinstance(va, float) and isinstance(vb, float)
                              and va != va and vb != vb)  # NaN == NaN here
        if not same:
            n_diff += 1
            diffs.append({"path": p, "first": repr(va), "second": repr(vb)})
    return n_cmp, n_diff, n_excl, diffs


def compare_lines(a: Path, b: Path, volatile):
    la = a.read_text(errors="replace").splitlines()
    lb = b.read_text(errors="replace").splitlines()
    n_cmp = n_diff = n_excl = 0
    diffs = []
    for i in range(max(len(la), len(lb))):
        va = la[i] if i < len(la) else "<ABSENT LINE>"
        vb = lb[i] if i < len(lb) else "<ABSENT LINE>"
        if any(t in va for t in volatile) and any(t in vb for t in volatile):
            n_excl += 1
            continue
        n_cmp += 1
        if va != vb:
            n_diff += 1
            if len(diffs) < 50:
                diffs.append({"line": i + 1, "first": va, "second": vb})
    return n_cmp, n_diff, n_excl, diffs


def compare_trees(first: Path, second: Path):
    rep = {"first": str(first), "second": str(second), "files": [],
           "totals": {"json_leaves_compared": 0, "json_leaves_differing": 0,
                      "json_leaves_excluded_timing_or_provenance": 0,
                      "mfile_lines_compared": 0, "mfile_lines_differing": 0,
                      "mfile_lines_excluded_volatile": 0,
                      "out_lines_compared": 0, "out_lines_differing": 0,
                      "out_lines_excluded_volatile": 0,
                      "files_only_in_first": 0, "files_only_in_second": 0,
                      "files_skipped_logs": 0}}
    fa = {p.relative_to(first) for p in first.rglob("*") if p.is_file()}
    fb = {p.relative_to(second) for p in second.rglob("*") if p.is_file()}
    t = rep["totals"]
    for rel in sorted(fa - fb):
        t["files_only_in_first"] += 1
        rep["files"].append({"file": str(rel), "status": "ONLY IN FIRST"})
    for rel in sorted(fb - fa):
        t["files_only_in_second"] += 1
        rep["files"].append({"file": str(rel), "status": "ONLY IN SECOND"})
    for rel in sorted(fa & fb):
        a, b = first / rel, second / rel
        name = rel.name
        if "_mplconfig" in str(rel) or name.endswith(".log"):
            t["files_skipped_logs"] += 1
            continue
        if name.endswith(".json"):
            c, d, e, diffs = compare_json(a, b)
            t["json_leaves_compared"] += c
            t["json_leaves_differing"] += d
            t["json_leaves_excluded_timing_or_provenance"] += e
            kind = "json"
        elif "MFILE" in name:
            c, d, e, diffs = compare_lines(a, b, MFILE_VOLATILE)
            t["mfile_lines_compared"] += c
            t["mfile_lines_differing"] += d
            t["mfile_lines_excluded_volatile"] += e
            kind = "mfile"
        elif "OUT.DAT" in name:
            c, d, e, diffs = compare_lines(a, b, OUT_VOLATILE)
            t["out_lines_compared"] += c
            t["out_lines_differing"] += d
            t["out_lines_excluded_volatile"] += e
            kind = "out"
        else:
            same = a.read_bytes() == b.read_bytes()
            rep["files"].append({"file": str(rel), "kind": "bytes",
                                 "identical": same})
            if not same:
                rep["files"][-1]["status"] = "DIFFERS (byte compare)"
                t.setdefault("other_files_differing", 0)
                t["other_files_differing"] += 1
            continue
        entry = {"file": str(rel), "kind": kind, "compared": c,
                 "differing": d, "excluded": e}
        if diffs:
            entry["diffs"] = diffs
        rep["files"].append(entry)
    return rep


def verdict(rep) -> int:
    t = rep["totals"]
    bad = (t["json_leaves_differing"] + t["mfile_lines_differing"]
           + t["out_lines_differing"] + t.get("other_files_differing", 0)
           + t["files_only_in_first"] + t["files_only_in_second"])
    print(json.dumps(t, indent=2))
    if bad:
        print(f"\nNOT BIT-IDENTICAL: {bad} differing quantities/files.  "
              f"Every one is listed in the JSON report.")
        for f in rep["files"]:
            for d in (f.get("diffs") or [])[:10]:
                print(f"  {f['file']}: {d}")
    else:
        print("\nBIT-IDENTICAL on every compared quantity "
              "(exclusions counted above).")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("compare")
    c.add_argument("--first", required=True)
    c.add_argument("--second", required=True)
    c.add_argument("--out", default=None)
    s = sub.add_parser("selftest")
    s.add_argument("--tree", required=True)
    s.add_argument("--work", required=True)
    args = ap.parse_args()

    if args.cmd == "compare":
        rep = compare_trees(Path(args.first), Path(args.second))
        if args.out:
            Path(args.out).write_text(json.dumps(rep, indent=2))
            print(f"wrote {args.out}")
        return verdict(rep)

    # selftest: the comparator shown capable of failing (protocol section 12)
    src = Path(args.tree)
    work = Path(args.work)
    if work.exists():
        shutil.rmtree(work)
    shutil.copytree(src, work)
    flips = 0
    for j in sorted(work.rglob("*.json")):
        txt = j.read_text()
        m = re.search(r"(\d)(\.\d+e[+-]\d+)?([,\s\]}])", txt)
        num = re.search(r"(-?\d+\.\d+(?:e[+-]?\d+)?)", txt)
        if num:
            old = num.group(1)
            new = old[:-1] + ("1" if old[-1] != "1" else "2")
            j.write_text(txt.replace(old, new, 1))
            print(f"selftest: flipped {old!r} -> {new!r} in {j.name}")
            flips += 1
            break
    for mf in sorted(work.rglob("*MFILE.DAT")):
        lines = mf.read_text().splitlines(keepends=True)
        for i, ln in enumerate(lines):
            if re.search(r"\d\.\d{17}e[+-]\d\d", ln) and not any(
                    t in ln for t in MFILE_VOLATILE):
                lines[i] = re.sub(r"(\d)(e[+-]\d\d)",
                                  lambda m: ("1" if m.group(1) != "1" else "2")
                                  + m.group(2), ln, count=1)
                mf.write_text("".join(lines))
                print(f"selftest: perturbed line {i + 1} of {mf.name}")
                flips += 1
                break
        break
    rep = compare_trees(src, work)
    rc = verdict(rep)
    t = rep["totals"]
    # The first version of this selftest forgot to write the MFILE back and
    # then declared "both caught" on the strength of the JSON flip alone
    # (protocol section 12: a gate must be shown capable of failing PER
    # THING IT CLAIMS TO WATCH).  So each channel is now required separately.
    ok = (flips == 2 and rc != 0
          and t["json_leaves_differing"] >= 1
          and t["mfile_lines_differing"] >= 1)
    if not ok:
        print(f"SELFTEST FAILED: flips={flips}, rc={rc}, "
              f"json_diff={t['json_leaves_differing']}, "
              f"mfile_diff={t['mfile_lines_differing']}; the comparator "
              f"cannot be trusted to catch a real difference.")
        return 2
    print(f"\nSELFTEST PASSED: {flips} deliberate flips, each caught in its "
          f"own channel (json {t['json_leaves_differing']}, "
          f"mfile {t['mfile_lines_differing']}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
