#!/usr/bin/env python
"""The fifth revision's folder is a copy of the fourth's: this makes it and proves it.

The user's ruling (2026-09-29): *"copy and then modify is suitable. I want to
move towards v5."*  The copy has to be exact, because the reproduction gate
(GR) is only meaningful on a copy that *is* the published V4 harness driving
the published V4 driver; a copy nobody checks is how a "reproduction" quietly
measures something else.  So the copy is made **from the commit, not from a
working tree** (the same discipline as ``PROCESS/copy_gates.py``), every file
is digested at the source commit and in the copy, and the manifest this writes
(``COPY_MANIFEST.json``) is what ``check`` compares the folder against later.

Three commands, one manifest::

    copy   --source-commit <c> --task <t>
        Extract every file git tracks under the source folder at <c> into this
        folder, at the same relative path, and write the manifest with each
        file's sha256 at the source commit.  Refuses if this folder already
        holds anything other than this script.
    record --task <t>
        Re-digest every manifest file as it stands in the copy.  The files whose
        copy digest differs from the source digest must be **exactly** the set
        declared in :data:`REPOINTED_FILES` -- a re-pointed self-reference is
        legal because it is declared and reviewable, never because a
        regeneration blessed it.  Every ``record`` appends one entry to the
        manifest's ``recorded`` history.
    check  [--no-teeth]
        Every manifest file is present in the copy with its recorded copy
        digest; every source digest re-derives from git at the recorded
        commit; the folder holds no file the manifest and :data:`OWN_FILES` do
        not name, and lacks none.  Then the teeth: a one-byte change, a removed
        file and an added file, each in a temporary copy of the folder, must
        each FAIL the same check.  Exit 0 on PASS with every tooth tripped.

What is deliberately outside the manifest: ``runs/`` (untracked bulk output,
gitignored by the copied ``.gitignore``), ``__pycache__`` and ``.claude/``.
Written for task A94 (v5-copy).
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "COPY_MANIFEST.json"

#: The repository root: every git path below is relative to it, so git runs
#: there and not in this folder (a `git ls-tree -- <path>` run here resolves
#: the path relative to here and lists nothing -- and a check over nothing
#: passes, trap T12).
TOPLEVEL = Path(
    subprocess.run(
        ["git", "-C", str(HERE), "rev-parse", "--show-toplevel"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
)

#: The folder the copy is taken from, relative to the repository root.
SOURCE_DIR = "arch_surgery/MDA_partitioning_experiment_v4"

#: Files that belong to this folder and not to the copy: never in the manifest,
#: never counted as an addition.
OWN_FILES: frozenset[str] = frozenset({"copy_manifest.py", "COPY_MANIFEST.json"})

#: Directories the file-set comparison never descends into.
SKIPPED_DIRS: frozenset[str] = frozenset({"runs", "__pycache__", ".claude"})

#: Copied files whose content is permitted to differ from the source commit,
#: each with the one reason: a self-reference the code *resolves* that had to
#: follow the folder's name.  ``record`` refuses any other difference.
REPOINTED_FILES: dict[str, str] = {
    "report_cells_preserved.py": (
        "the path `git show <base>:<path>` resolves the committed report at, "
        "arch_surgery/MDA_partitioning_experiment_v4/ -> _v5/ (one literal, "
        "line 342); with the V4 literal the script would compare this "
        "folder's rendering against the V4 report at <base>"
    ),
}


# ---------------------------------------------------------------------------
# git and digests
# ---------------------------------------------------------------------------


def _git(*args: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(TOPLEVEL), *args], check=True, capture_output=True
    ).stdout


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def blobs_at(commit: str, prefix: str) -> dict[str, tuple[str, bytes]]:
    """Relative path -> (mode, content) of every blob under *prefix* at *commit*.

    Read with ``git cat-file --batch`` so that no checkout filter and no
    working tree can stand between the commit and the bytes.
    """
    listing = _git("ls-tree", "-r", commit, "--", prefix).decode()
    entries: list[tuple[str, str, str]] = []  # (mode, oid, relpath)
    for line in listing.splitlines():
        meta, path = line.split("\t", 1)
        mode, kind, oid = meta.split()
        if kind != "blob":
            raise SystemExit(f"{path} at {commit} is a {kind}, not a blob")
        if not path.startswith(prefix + "/"):
            raise SystemExit(f"{path} is not under {prefix}/")
        entries.append((mode, oid, path[len(prefix) + 1 :]))
    if not entries:
        raise SystemExit(f"no blob under {prefix}/ at {commit}: a copy of nothing is not a copy")
    proc = subprocess.run(
        ["git", "-C", str(TOPLEVEL), "cat-file", "--batch"],
        input="".join(f"{oid}\n" for _, oid, _ in entries).encode(),
        check=True,
        capture_output=True,
    )
    out: dict[str, tuple[str, bytes]] = {}
    buf = proc.stdout
    pos = 0
    for mode, oid, rel in entries:
        nl = buf.index(b"\n", pos)
        header = buf[pos:nl].decode().split()
        if len(header) != 3 or header[0] != oid:
            raise SystemExit(f"cat-file header mismatch for {rel}: {header}")
        size = int(header[2])
        start = nl + 1
        out[rel] = (mode, buf[start : start + size])
        pos = start + size + 1
    return out


def on_disk(root: Path) -> dict[str, Path]:
    """Relative posix path -> file, for every file under *root* outside the skipped directories."""
    found: dict[str, Path] = {}
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if any(part in SKIPPED_DIRS for part in rel.parts):
            continue
        if path.is_symlink():
            raise SystemExit(f"{rel} is a symlink; the copy holds regular files only")
        if path.is_file():
            found[rel.as_posix()] = path
    return found


def load_manifest(path: Path = MANIFEST) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"{path} is not present; the copy has no manifest and nothing can be checked")
    return json.loads(path.read_text())


def write_manifest(manifest: dict[str, Any]) -> None:
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")


# ---------------------------------------------------------------------------
# copy
# ---------------------------------------------------------------------------


def do_copy(commit: str, task: str) -> int:
    present = set(on_disk(HERE)) - OWN_FILES
    if present:
        raise SystemExit(
            f"refusing to copy: {HERE} already holds {len(present)} file(s) "
            f"beyond {sorted(OWN_FILES)} (first: {sorted(present)[:3]})"
        )
    full = _git("rev-parse", commit).decode().strip()
    tree_sha1 = _git("rev-parse", f"{full}:{SOURCE_DIR}").decode().strip()
    blobs = blobs_at(full, SOURCE_DIR)
    files: dict[str, dict[str, Any]] = {}
    for rel, (mode, data) in sorted(blobs.items()):
        if mode != "100644":
            raise SystemExit(f"{rel} has mode {mode}; only regular files are copied")
        target = HERE / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        files[rel] = {
            "sha256_at_source_commit": sha256(data),
            "bytes": len(data),
            "sha256_in_copy": sha256(data),
            "repointed": False,
        }
    manifest = {
        "what": (
            "The fifth revision's folder is a byte-for-byte copy of the fourth's "
            "at the source commit below, made from the commit with git cat-file "
            "and never from a working tree.  Every copied file is listed with "
            "its sha256 at the source commit and in the copy; the files whose "
            "two digests differ are the declared re-pointed self-references and "
            "nothing else.  `copy_manifest.py check` compares the folder against "
            "this file and is runnable at any later commit."
        ),
        "task": task,
        "generated_by": "copy_manifest.py copy",
        "copy_date": _dt.date.today().isoformat(),
        "source": {
            "repository": "PROCESS_surgery (this repository), branch architecture_surgery",
            "path": SOURCE_DIR + "/",
            "commit": full[:8],
            "commit_full": full,
            "tree_sha1": tree_sha1,
            "file_count": len(files),
            "total_bytes": sum(f["bytes"] for f in files.values()),
            "read_with": "git ls-tree -r <commit> -- <path>; git cat-file --batch",
        },
        "copy": {
            "path": HERE.relative_to(TOPLEVEL).as_posix() + "/",
            "own_files": sorted(OWN_FILES),
            "skipped_directories": sorted(SKIPPED_DIRS),
        },
        "repointed_files": {},
        "recorded": [],
        "files": files,
    }
    write_manifest(manifest)
    print(f"wrote {MANIFEST}")
    print(f"  source {SOURCE_DIR}/ at {full} (tree {tree_sha1})")
    print(f"  {len(files)} files, {manifest['source']['total_bytes']} bytes copied into {HERE}")
    return 0


# ---------------------------------------------------------------------------
# record
# ---------------------------------------------------------------------------


def do_record(task: str) -> int:
    manifest = load_manifest()
    files = manifest["files"]
    differing: list[str] = []
    changed_since_last: list[str] = []
    for rel, entry in files.items():
        path = HERE / rel
        if not path.exists():
            raise SystemExit(f"refusing to record: {rel} is missing from the copy")
        digest = sha256(path.read_bytes())
        if digest != entry["sha256_in_copy"]:
            changed_since_last.append(rel)
        entry["sha256_in_copy"] = digest
        entry["repointed"] = digest != entry["sha256_at_source_commit"]
        if entry["repointed"]:
            differing.append(rel)
    if sorted(differing) != sorted(REPOINTED_FILES):
        raise SystemExit(
            "refusing to record: the files differing from the source commit are "
            f"{sorted(differing)}, but REPOINTED_FILES declares "
            f"{sorted(REPOINTED_FILES)}.  Recording must never be the way an "
            "undeclared edit becomes accepted."
        )
    manifest["repointed_files"] = dict(REPOINTED_FILES)
    manifest["recorded"].append(
        {
            "date": _dt.date.today().isoformat(),
            "task": task,
            "files_changed_since_last_record": sorted(changed_since_last),
            "repointed_files": sorted(differing),
        }
    )
    write_manifest(manifest)
    print(f"wrote {MANIFEST}")
    print(f"  {len(files)} files; {len(differing)} re-pointed: {sorted(differing)}")
    print(f"  changed since the last record: {sorted(changed_since_last)}")
    return 0


# ---------------------------------------------------------------------------
# check, and its teeth
# ---------------------------------------------------------------------------


def check(manifest: dict[str, Any], root: Path, *, source: dict[str, tuple[str, bytes]] | None) -> dict[str, Any]:
    """The verdict of the copy at *root* against *manifest*.

    *source* is the source commit's blobs (``None`` skips the re-derivation of
    the source digests, which the teeth do not need to repeat).
    """
    files = manifest["files"]
    if not files:
        raise SystemExit("the manifest names no file; a check over nothing is not a check (trap T12)")
    disk = on_disk(root)
    expected = set(files) | set(manifest["copy"]["own_files"])
    missing = sorted(set(files) - set(disk))
    added = sorted(set(disk) - expected)
    differing = sorted(
        rel for rel in files
        if rel in disk and sha256(disk[rel].read_bytes()) != files[rel]["sha256_in_copy"]
    )
    undeclared_repoints = sorted(
        rel for rel, entry in files.items()
        if entry["repointed"] and rel not in manifest["repointed_files"]
    )
    declared_not_repointed = sorted(
        rel for rel in manifest["repointed_files"]
        if rel not in files or not files[rel]["repointed"]
    )
    source_mismatch: list[str] = []
    source_set_mismatch: list[str] = []
    if source is not None:
        source_mismatch = sorted(
            rel for rel, entry in files.items()
            if rel not in source or sha256(source[rel][1]) != entry["sha256_at_source_commit"]
        )
        source_set_mismatch = sorted(set(source) ^ set(files))
    failures = []
    if missing:
        failures.append(f"{len(missing)} manifest file(s) missing from the copy: {missing[:5]}")
    if added:
        failures.append(f"{len(added)} file(s) in the folder the manifest does not name: {added[:5]}")
    if differing:
        failures.append(f"{len(differing)} file(s) differ from their recorded copy digest: {differing[:5]}")
    if undeclared_repoints:
        failures.append(f"{len(undeclared_repoints)} re-pointed file(s) not declared: {undeclared_repoints}")
    if declared_not_repointed:
        failures.append(f"{len(declared_not_repointed)} declared re-point(s) with no difference: {declared_not_repointed}")
    if source_mismatch:
        failures.append(f"{len(source_mismatch)} source digest(s) do not re-derive from git: {source_mismatch[:5]}")
    if source_set_mismatch:
        failures.append(f"the source commit's file set differs from the manifest's: {source_set_mismatch[:5]}")
    return {
        "verdict": "PASS" if not failures else "FAIL",
        "n_compared": len(files),
        "n_identical_to_record": len(files) - len(differing) - len(missing),
        "n_repointed": sum(1 for e in files.values() if e["repointed"]),
        "n_missing": len(missing),
        "n_added": len(added),
        "n_differing": len(differing),
        "n_source_digests_rederived": 0 if source is None else len(files) - len(source_mismatch),
        "failures": failures,
    }


def teeth(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    """Three perturbations of a temporary copy of the folder; each must FAIL."""
    results = []
    files = manifest["files"]
    victim = sorted(files)[len(files) // 2]

    def copy_tree(td: str) -> Path:
        root = Path(td) / "copy"
        root.mkdir()
        for rel, path in on_disk(HERE).items():
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
        return root

    perturbations = {
        "one_byte_changed": lambda root: (root / victim).write_bytes((root / victim).read_bytes() + b"\n#"),
        "one_file_removed": lambda root: (root / victim).unlink(),
        "one_file_added": lambda root: (root / "an_added_file_for_the_tooth.txt").write_text("tooth\n"),
    }
    for name, perturb in perturbations.items():
        with tempfile.TemporaryDirectory() as td:
            root = copy_tree(td)
            perturb(root)
            result = check(manifest, root, source=None)
        touched = "an_added_file_for_the_tooth.txt" if name == "one_file_added" else victim
        results.append(
            {
                "tooth": name,
                "perturbation": f"{name.replace('_', ' ')} ({touched}) in a temporary copy of the folder",
                "tooth_result": "TRIPPED" if result["verdict"] == "FAIL" else "DID NOT TRIP",
                "first_failure": (result["failures"] or [None])[0],
            }
        )
    return results


def do_check(*, run_teeth: bool) -> int:
    manifest = load_manifest()
    full = manifest["source"]["commit_full"]
    source = blobs_at(full, manifest["source"]["path"].rstrip("/"))
    result = check(manifest, HERE, source=source)
    print(f"=== copy check -- {HERE.name} against {MANIFEST.name}")
    print(f"    source            : {manifest['source']['path']} at {full}")
    print(f"    verdict           : {result['verdict']}")
    for key in (
        "n_compared", "n_identical_to_record", "n_repointed", "n_missing",
        "n_added", "n_differing", "n_source_digests_rederived",
    ):
        print(f"    {key:<28}: {result[key]}")
    for failure in result["failures"]:
        print(f"    FAILURE: {failure}")
    ok = result["verdict"] == "PASS"
    if run_teeth:
        for tooth in teeth(manifest):
            print(f"    tooth {tooth['tooth']:<22} {tooth['tooth_result']:<13} ({tooth['perturbation']})")
            ok = ok and tooth["tooth_result"] == "TRIPPED"
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("command", choices=["copy", "record", "check"])
    ap.add_argument("--source-commit", default=None, help="copy: the commit to copy from")
    ap.add_argument("--task", default=None, help="copy, record: the task doing it")
    ap.add_argument("--no-teeth", action="store_true", help="check: skip the teeth")
    args = ap.parse_args(argv)
    if args.command == "copy":
        if not args.source_commit or not args.task:
            raise SystemExit("copy needs --source-commit and --task")
        return do_copy(args.source_commit, args.task)
    if args.command == "record":
        if not args.task:
            raise SystemExit("record needs --task")
        return do_record(args.task)
    return do_check(run_teeth=not args.no_teeth)


if __name__ == "__main__":
    sys.exit(main())
