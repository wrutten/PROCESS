"""Every change this experiment has made to PROCESS, in one view.

V4 runs its own copy of the PROCESS package under ``PROCESS/`` (decision D20).
This script answers, in a minute of reading, the only question a reviewer has
before a driver change is merged: **what does the copy do differently from the
PROCESS it was copied from, and why?**

It reads ``PROCESS/PROVENANCE.json`` for the source commit, extracts that
commit's ``process/`` into a temporary directory, diffs the copy against it
with ``git diff --no-index`` -- against the commit, never against the
repository-root working tree -- and prints, per changed file, the lines added
and removed and, per hunk, the switch or mechanism it serves.  A hunk that the
annotation map does not claim is printed as **UNEXPLAINED** and the exit status
is non-zero: an unclaimed hunk is a change nobody wrote down.

It closes with the frozen-physics statement -- gate G0' re-run live against the
base commit ``c0ae5b28``, naming the one model edit the experiment has ever
approved.

Later driver-change tasks extend ``ANNOTATIONS`` by one line each and add a
paragraph to ``SUMMARIES``.

New in A46 (process-copy); it derives from no earlier file.  Stdlib only, no
PROCESS run, runs in seconds.

Usage
-----
    python PROCESS_diff.py             # the overview
    python PROCESS_diff.py --full      # the raw unified diff as well
    python PROCESS_diff.py --markdown  # a table a report can include

Exit status: 0 every hunk is claimed and G0' passes, 1 otherwise, 2 setup error.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
COPY_ROOT = HERE / "PROCESS"
PROVENANCE = COPY_ROOT / "PROVENANCE.json"
GATES = COPY_ROOT / "copy_gates.py"


@dataclass(frozen=True)
class Annotation:
    """One reason a hunk may exist: a marker in the hunk, and what it serves."""

    path: str
    marker: str
    serves: str


#: The annotation map.  A hunk in ``path`` whose text contains ``marker`` is
#: claimed by ``serves``.  One line per mechanism; adding a driver change means
#: adding a line here (and a paragraph to SUMMARIES below).
ANNOTATIONS: list[Annotation] = [
    Annotation("process/core/solver/module_solve.py", "YSTATE_MODULE_PATH", "harness path constant YSTATE_MODULE_PATH -> harness/ystate.py (D20, decision 2 option v)"),
    Annotation("process/core/caller.py", "NODE_WRITESET_PATH", "harness path constant NODE_WRITESET_PATH -> harness/data/ (D20, decision 3)"),
    Annotation("process/core/caller.py", "NODE_MAP_PATH", "harness path constant NODE_MAP_PATH -> harness/data/ (D20, decision 3)"),
]

#: One paragraph per changed driver file, for a reader who will not read the
#: diff.  Keyed by path; a file with no entry is reported as undocumented.
SUMMARIES: dict[str, str] = {
    "process/core/caller.py": (
        "Two path constants are re-pointed.  The driver reads two committed "
        "artifacts by absolute path -- the per-node write sets and the DSM "
        "node map -- and in the repository-root tree it resolves both under "
        "arch_surgery/docs/data/.  In the copy they resolve under "
        "MDA_partitioning_experiment_v4/harness/data/ instead, so V4's driver "
        "reads V4's artifacts and nothing outside the experiment folder.  The "
        "constants' adjacent comments record the move and note that the "
        "targets do not exist yet; a later harness task creates them.  No "
        "behaviour changes: the same code reads the same shape of file from a "
        "different place."
    ),
    "process/core/solver/module_solve.py": (
        "One path constant is re-pointed.  The per-module solver loads the "
        "coupling-state predicate as a module by path, because the research "
        "tree is not an importable package; in the repository-root tree that "
        "is arch_surgery/fixedpoint/ystate.py.  In the copy it is "
        "MDA_partitioning_experiment_v4/harness/ystate.py, the V4 harness's "
        "own copy of the predicate.  Same loader, same contract, different "
        "file; the target is created by a later harness task."
    ),
}


@dataclass
class FileDiff:
    """One changed file: its hunks, its line counts, and who claims them."""

    path: str
    added: int = 0
    removed: int = 0
    hunks: list[dict] = field(default_factory=list)

    @property
    def unexplained(self) -> list[dict]:
        return [h for h in self.hunks if not h["serves"]]


def load_gates():
    """Import ``copy_gates`` by path, so G0' has exactly one implementation."""
    spec = importlib.util.spec_from_file_location("_copy_gates", GATES)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {GATES}")
    module = importlib.util.module_from_spec(spec)
    # Registered before exec: @dataclass resolves annotations through
    # sys.modules[cls.__module__] and fails on a module that is not there.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def repo_root() -> Path:
    """The working tree's top level -- ``git archive``'s pathspec is relative."""
    return Path(
        subprocess.run(
            ["git", "-C", str(HERE), "rev-parse", "--show-toplevel"],
            check=True,
            stdout=subprocess.PIPE,
            text=True,
        ).stdout.strip()
    )


def extract(commit: str, dest: Path) -> Path:
    """The source commit's ``process/``, in a temporary directory."""
    dest.mkdir(parents=True, exist_ok=True)
    archive = subprocess.run(
        ["git", "-C", str(repo_root()), "archive", commit, "process"],
        check=True,
        stdout=subprocess.PIPE,
    ).stdout
    subprocess.run(["tar", "-x", "-C", str(dest)], input=archive, check=True)
    return dest / "process"


def diff_text(src: Path, copy: Path, context: int) -> str:
    proc = subprocess.run(
        [
            "git",
            "diff",
            "--no-index",
            f"--unified={context}",
            "--",
            str(src),
            str(copy),
        ],
        stdout=subprocess.PIPE,
        text=True,
    )
    if proc.returncode not in (0, 1):
        raise SystemExit(f"git diff --no-index failed ({proc.returncode})")
    return proc.stdout


def parse(raw: str, src: Path, copy: Path) -> list[FileDiff]:
    """Split a unified diff into files and hunks, and claim each hunk."""
    files: list[FileDiff] = []
    current: FileDiff | None = None
    hunk: dict | None = None

    def close_hunk() -> None:
        if current is not None and hunk is not None:
            text = "\n".join(hunk["lines"])
            claims = [
                a.serves
                for a in ANNOTATIONS
                if a.path == current.path and a.marker in text
            ]
            hunk["serves"] = "; ".join(dict.fromkeys(claims))
            current.hunks.append(hunk)

    def normalise(raw_path: str) -> str:
        """``+++ b/home/.../PROCESS/process/core/caller.py`` -> ``process/...``.

        ``git diff --no-index`` prefixes ``a/``/``b/`` and drops the leading
        slash of an absolute path, so both have to be put back before the
        package-relative name can be recovered.
        """
        s = raw_path.strip().split("\t")[0]
        if s.startswith(("a/", "b/")):
            s = s[2:]
        if s == "dev/null" or s == "/dev/null":
            return ""
        if not s.startswith("/"):
            s = "/" + s
        for root in (copy.parent, src.parent):
            s = s.removeprefix(str(root) + "/")
        return s

    pending_old = ""
    for line in raw.splitlines():
        if line.startswith("--- "):
            pending_old = normalise(line[4:])
        elif line.startswith("+++ "):
            close_hunk()
            hunk = None
            current = FileDiff(normalise(line[4:]) or pending_old)
            files.append(current)
        elif line.startswith("@@"):
            close_hunk()
            hunk = {"header": line, "lines": [], "serves": ""}
        elif current is not None and hunk is not None:
            hunk["lines"].append(line)
            if line.startswith("+") and not line.startswith("+++"):
                current.added += 1
            elif line.startswith("-") and not line.startswith("---"):
                current.removed += 1
    close_hunk()
    return [f for f in files if f.hunks]


def frozen_statement(gates, prov: dict) -> tuple[bool, list[str]]:
    """Gate G0' re-run live, restated for a reader."""
    res = gates.check_frozen_physics(prov, COPY_ROOT)
    fp = prov["frozen_physics"]
    lines = [
        f"The physics is frozen at base commit {fp['base_commit']} (decision D5). "
        f"Of the {res.compared} files under process/models/ in this copy, "
        f"{res.identical} are byte-identical to that commit and the file set "
        "matches exactly.",
    ]
    for a in fp["approved_differences"]:
        lines.append(
            f"The one file that differs is {a['path']}, and it is approved: "
            f"{a['decision']}."
        )
    if res.detail["unapproved_differences"]:
        lines.append(
            "UNAPPROVED model differences: "
            f"{res.detail['unapproved_differences']} -- this is a finding."
        )
    lines.append(f"Gate G0' verdict: {'PASS' if res.passed else 'FAIL'}.")
    return res.passed, lines


def wrap(text: str, width: int = 78, indent: str = "  ") -> str:
    import textwrap

    return textwrap.fill(text, width=width, initial_indent=indent, subsequent_indent=indent)


def render_text(prov: dict, files: list[FileDiff], frozen: list[str]) -> None:
    src = prov["source"]
    print("=" * 78)
    print("PROCESS_diff -- what V4's copy of PROCESS does differently")
    print("=" * 78)
    print(f"copy          : PROCESS/process/  ({src['file_count']} files)")
    print(f"source commit : {src['commit']}  ({src['commit_full']})")
    print(f"copied on     : {prov['copy_date']}  by {prov['task']}")
    print(f"changed files : {len(files)}")
    print()

    for f in files:
        print("-" * 78)
        print(f"{f.path}   +{f.added} / -{f.removed}   {len(f.hunks)} hunk(s)")
        summary = SUMMARIES.get(f.path)
        print(wrap(summary) if summary else "  (no summary written for this file)")
        print()
        for h in f.hunks:
            tag = h["serves"] or "UNEXPLAINED -- no annotation claims this hunk"
            print(f"  {h['header'].split('@@')[1].strip():<20} {tag}")
        print()

    print("=" * 78)
    print("FROZEN PHYSICS")
    print("=" * 78)
    for line in frozen:
        print(wrap(line, indent=""))
        print()


def render_markdown(prov: dict, files: list[FileDiff], frozen: list[str]) -> None:
    src = prov["source"]
    print(
        "*Caption: one row per file in which V4's copy of the PROCESS package "
        f"differs from its source commit `{src['commit']}`. Columns: the file's "
        "path inside the package; lines added and removed by `git diff` against "
        "the commit (not against any working tree); the number of hunks; and, "
        "per hunk, the switch or mechanism the annotation map in "
        "`PROCESS_diff.py` says it serves. `UNEXPLAINED` means no annotation "
        "claims the hunk. Population: all "
        f"{src['file_count']} files of the copied package.*"
    )
    print()
    print("| file | + | − | hunks | serves |")
    print("|---|---:|---:|---:|---|")
    for f in files:
        serves = "; ".join(
            dict.fromkeys(h["serves"] or "**UNEXPLAINED**" for h in f.hunks)
        )
        print(f"| `{f.path}` | {f.added} | {f.removed} | {len(f.hunks)} | {serves} |")
    print()
    for f in files:
        if SUMMARIES.get(f.path):
            print(f"**`{f.path}`** — {SUMMARIES[f.path]}")
            print()
    print("**Frozen physics.** " + " ".join(frozen))


def analyse(prov: dict, package: Path, context: int) -> tuple[str, list[FileDiff]]:
    """Diff ``package`` against the source commit and claim every hunk."""
    with tempfile.TemporaryDirectory() as td:
        src = extract(prov["source"]["commit_full"], Path(td) / "source")
        raw = diff_text(src, package, context)
        return raw, parse(raw, src, package)


def teeth(prov: dict, context: int) -> dict:
    """An unannotated change must be reported UNEXPLAINED.

    Protocol section 12: a check whose failure mode has never been exercised is
    an assertion, not a measurement.  A throwaway copy of the package gains one
    line no annotation claims; the real tree is never touched.
    """
    with tempfile.TemporaryDirectory() as td:
        staged = Path(td) / "process"
        shutil.copytree(
            COPY_ROOT / "process",
            staged,
            ignore=shutil.ignore_patterns("__pycache__"),
        )
        victim = staged / "core" / "constants.py"
        victim.write_text(victim.read_text() + "\n# a change nobody wrote down\n")
        _, files = analyse(prov, staged, context)
    unexplained = [(f.path, h["header"]) for f in files for h in f.unexplained]
    return {
        "tooth": "unannotated_hunk",
        "perturbation": "one unclaimed line appended to process/core/constants.py",
        "unexplained_hunks": unexplained,
        "tooth_result": "TRIPPED" if unexplained else "DID NOT TRIP",
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--full", action="store_true", help="print the raw unified diff")
    ap.add_argument("--markdown", action="store_true", help="print a report table")
    ap.add_argument("--context", type=int, default=3, help="diff context lines")
    ap.add_argument(
        "--teeth",
        action="store_true",
        help="show that an unannotated hunk is caught, then exit",
    )
    args = ap.parse_args(argv)

    if not PROVENANCE.exists():
        raise SystemExit(f"{PROVENANCE} is not present; nothing to diff against.")
    prov = json.loads(PROVENANCE.read_text())
    gates = load_gates()

    if args.teeth:
        t = teeth(prov, args.context)
        print(f"tooth {t['tooth']}: {t['tooth_result']}")
        print(f"  perturbation      : {t['perturbation']}")
        for path, header in t["unexplained_hunks"]:
            print(f"  reported UNEXPLAINED: {path}  {header}")
        return 0 if t["tooth_result"] == "TRIPPED" else 1

    raw, files = analyse(prov, COPY_ROOT / "process", args.context)
    frozen_ok, frozen = frozen_statement(gates, prov)

    if args.markdown:
        render_markdown(prov, files, frozen)
    else:
        render_text(prov, files, frozen)
        if args.full:
            print("=" * 78)
            print("RAW UNIFIED DIFF")
            print("=" * 78)
            print(raw)

    unexplained = [(f.path, h["header"]) for f in files for h in f.unexplained]
    undocumented = [f.path for f in files if f.path not in SUMMARIES]
    if unexplained:
        print("\nUNEXPLAINED HUNKS:", file=sys.stderr)
        for path, header in unexplained:
            print(f"  {path}  {header}", file=sys.stderr)
    if undocumented:
        print(f"\nFILES WITHOUT A SUMMARY: {undocumented}", file=sys.stderr)
    return 0 if (frozen_ok and not unexplained and not undocumented) else 1


if __name__ == "__main__":
    sys.exit(main())
