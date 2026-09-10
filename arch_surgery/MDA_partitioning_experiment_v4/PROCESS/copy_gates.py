"""Gates that prove this PROCESS copy is exactly what ``PROVENANCE.json`` claims.

V4 runs its own copy of the PROCESS package (decision D20 in the master
queue's decision register): the repository-root ``process/`` stays as the tree
V3's records were made against, and every V4 driver change is made here
instead.  A duplicated tree nobody checks is how a frozen model quietly stops
being frozen, so the copy comes with two gates, both implemented here and both
runnable at any later commit.

``copy-identity``
    Every file under ``PROCESS/process/`` is byte-identical to the same path at
    the **source commit** named in ``PROVENANCE.json``, except the permitted
    edits recorded there -- whose post-edit sha256 and whose exact hunks must
    match.  The file *set* is compared as well as the file contents, because a
    per-file hash loop that never compares the set passes on a removed and on
    an added file.

``frozen-physics`` (gate G0' of the harness implementation plan)
    Every file under ``PROCESS/process/models/`` has the sha256 it is supposed
    to have, where "supposed to" means: the byte content at the frozen base
    commit ``c0ae5b28`` (D5, the physics freeze), except for the model files
    the experiment has explicitly approved a structural edit to -- today
    exactly one, ``process/models/pulse.py`` under D14(b), whose expected
    content is pinned by sha256 as well, so a *further* edit to it fails too.

Both comparisons are made against the **commit**, read with ``git cat-file``,
never against a working tree: an uncommitted edit in the repository-root
``process/`` must not be able to ride along unnoticed, and a root-tree edit
must not be able to mask a copy-tree edit or the reverse.

Teeth (queue protocol section 12: a gate must be shown capable of failing
before its zeros are accepted).  Each gate is re-run against perturbed
*temporary copies* of the tree -- a one-byte change, a removed file, an added
file, and a change made to a file that is allowed to differ but in the wrong
place -- and each must FAIL.  The real tree is never modified.

New in A46 (process-copy); it derives from no earlier file.  Stdlib only, no
PROCESS run, runs in seconds.

Usage
-----
    python copy_gates.py all                # both gates + smoke import, with teeth
    python copy_gates.py copy-identity
    python copy_gates.py frozen-physics
    python copy_gates.py smoke-import       # PYTHONPATH selects the copy (trap T6)
    python copy_gates.py provenance --force # regenerate PROVENANCE.json

Exit status: 0 every gate passed, 1 a gate or a tooth failed, 2 setup error.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import difflib
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
COPY_ROOT = HERE  # holds process/ and PROVENANCE.json
PROVENANCE = HERE / "PROVENANCE.json"
SOURCE_PREFIX = "process"
MODELS_PREFIX = "process/models"

#: Where a gate record is written unless ``--records`` says otherwise.  Bulk run
#: artifacts are untracked by design (CLAUDE.md); only the report's verdict is
#: committed.
DEFAULT_RECORDS = HERE.parent / "runs" / "gates"

#: The complete set of files the copy is permitted to differ from its source
#: commit in, and the constant each edit re-points.  Adding a row here is not
#: enough to make an edit legal -- ``PROVENANCE.json`` must be regenerated so
#: the expected hunks and post-edit sha256 are recorded and reviewable.
PERMITTED_EDIT_FILES: dict[str, list[str]] = {
    "process/core/solver/module_solve.py": ["YSTATE_MODULE_PATH"],
    "process/core/caller.py": ["NODE_WRITESET_PATH", "NODE_MAP_PATH"],
}

#: Model files the experiment has approved a structural edit to, with the
#: decision that approved each.  Anything else differing from the base commit
#: is a finding, not something this gate absorbs.
APPROVED_MODEL_EDITS: dict[str, str] = {
    "process/models/pulse.py": (
        "D14(b), 2026-09-01 -- the burn-time residual extracted into a "
        "driver-solvable form (burn_time_root / burn_time_residual), the "
        "arithmetic verbatim; structural only, D11's approval rule satisfied"
    ),
}


# ---------------------------------------------------------------------------
# git access -- always the commit, never a working tree
# ---------------------------------------------------------------------------


def _git(*args: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(HERE), *args],
        check=True,
        stdout=subprocess.PIPE,
    ).stdout


def blobs_at(commit: str, prefix: str) -> dict[str, bytes]:
    """``{path: bytes}`` for every blob under ``prefix`` at ``commit``.

    Read with ``git cat-file``, so no checkout filter and no working tree can
    stand between the commit and the bytes compared.
    """
    listing = _git("ls-tree", "-r", "-z", "--full-tree", commit, prefix)
    entries: list[tuple[str, str]] = []  # (oid, path)
    for chunk in listing.split(b"\0"):
        if not chunk:
            continue
        meta, path = chunk.split(b"\t", 1)
        mode, kind, oid = meta.split()
        if kind != b"blob":
            raise SystemExit(
                f"{prefix} at {commit} contains a non-blob entry "
                f"({kind.decode()} at {path.decode()}); this gate handles "
                "regular files only."
            )
        if mode != b"100644":
            raise SystemExit(
                f"{path.decode()} at {commit} has mode {mode.decode()}, not "
                "100644; the copy's file modes are not covered by this gate."
            )
        entries.append((oid.decode(), path.decode()))

    proc = subprocess.run(
        ["git", "-C", str(HERE), "cat-file", "--batch"],
        input="".join(oid + "\n" for oid, _ in entries).encode(),
        check=True,
        stdout=subprocess.PIPE,
    )
    out, pos, result = proc.stdout, 0, {}
    for _oid, path in entries:
        nl = out.index(b"\n", pos)
        size = int(out[pos:nl].split()[2])
        start = nl + 1
        result[path] = out[start : start + size]
        pos = start + size + 1
    return result


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def on_disk(root: Path, prefix: str) -> dict[str, bytes]:
    """``{path: bytes}`` for every file under ``root / prefix``.

    ``__pycache__`` is excluded: it is generated, ignored by git, and never
    part of what the copy claims to be.
    """
    base = root / prefix
    files: dict[str, bytes] = {}
    for p in sorted(base.rglob("*")):
        if p.is_dir() or "__pycache__" in p.parts:
            continue
        files[str(p.relative_to(root))] = p.read_bytes()
    return files


def expected_hunks(source: bytes, copy: bytes, path: str) -> list[str]:
    """The unified diff of one permitted edit, zero context, as a line list.

    Zero context so the record shows the changed lines and their positions and
    nothing else; hunk headers are kept, so an edit that moved would not match
    a recorded one silently.
    """
    return [
        line.rstrip("\n")
        for line in difflib.unified_diff(
            source.decode().splitlines(keepends=True),
            copy.decode().splitlines(keepends=True),
            fromfile=f"source commit:{path}",
            tofile=f"copy:{path}",
            n=0,
        )
    ]


# ---------------------------------------------------------------------------
# gate results
# ---------------------------------------------------------------------------


@dataclass
class GateResult:
    """One gate's verdict and the numbers behind it."""

    gate: str
    label: str
    passed: bool = True
    compared: int = 0
    identical: int = 0
    detail: dict = field(default_factory=dict)
    failures: list[str] = field(default_factory=list)

    def fail(self, message: str) -> None:
        self.passed = False
        self.failures.append(message)

    def as_dict(self) -> dict:
        return {
            "gate": self.gate,
            "label": self.label,
            "verdict": "PASS" if self.passed else "FAIL",
            "files_compared": self.compared,
            "files_identical": self.identical,
            "failures": self.failures,
            **self.detail,
        }


# ---------------------------------------------------------------------------
# gate 1 -- copy-identity
# ---------------------------------------------------------------------------


def check_copy_identity(prov: dict, root: Path) -> GateResult:
    """Every copied file is the source commit's, bar the permitted edits."""
    res = GateResult("copy-identity", "the copy is the source commit's process/")
    commit = prov["source"]["commit_full"]
    source = blobs_at(commit, SOURCE_PREFIX)
    copy = on_disk(root, SOURCE_PREFIX)
    permitted = prov["permitted_edits"]["files"]

    missing = sorted(set(source) - set(copy))
    extra = sorted(set(copy) - set(source))
    for p in missing:
        res.fail(f"file missing from the copy: {p}")
    for p in extra:
        res.fail(f"file present in the copy but not at the source commit: {p}")

    unexplained: list[str] = []
    for path in sorted(set(source) & set(copy)):
        res.compared += 1
        if source[path] == copy[path]:
            res.identical += 1
            if path in permitted:
                res.fail(
                    f"{path} is recorded as a permitted edit but is identical "
                    "to the source commit; the edit has been lost."
                )
            continue
        if path not in permitted:
            unexplained.append(path)
            res.fail(f"unexplained difference from the source commit: {path}")
            continue
        spec = permitted[path]
        got = sha256(copy[path])
        if got != spec["sha256_expected_in_copy"]:
            res.fail(
                f"{path} differs from the source commit AND from the expected "
                f"post-edit content (sha256 {got}, expected "
                f"{spec['sha256_expected_in_copy']}); something other than the "
                "recorded path constants has been changed in it."
            )
        got_hunks = expected_hunks(source[path], copy[path], path)
        if got_hunks != spec["expected_hunks"]:
            res.fail(
                f"{path}'s hunks do not match the ones recorded in "
                "PROVENANCE.json."
            )

    res.detail = {
        "source_commit": prov["source"]["commit"],
        "source_commit_full": commit,
        "files_at_source_commit": len(source),
        "files_in_copy": len(copy),
        "files_missing_from_copy": missing,
        "files_added_to_copy": extra,
        "permitted_edit_files": sorted(permitted),
        "unexplained_differences": unexplained,
    }
    return res


# ---------------------------------------------------------------------------
# gate 2 -- frozen-physics (G0')
# ---------------------------------------------------------------------------


def check_frozen_physics(prov: dict, root: Path) -> GateResult:
    """The copy's models/ is the frozen base commit's, bar approved edits."""
    res = GateResult("frozen-physics", "G0' -- the physics stays frozen in the copy")
    base = prov["frozen_physics"]["base_commit_full"]
    approved = {a["path"]: a for a in prov["frozen_physics"]["approved_differences"]}
    at_base = blobs_at(base, MODELS_PREFIX)
    copy = on_disk(root, MODELS_PREFIX)

    missing = sorted(set(at_base) - set(copy))
    extra = sorted(set(copy) - set(at_base))
    for p in missing:
        res.fail(f"model file missing from the copy: {p}")
    for p in extra:
        res.fail(f"model file present in the copy but not at {base[:8]}: {p}")

    differing: list[str] = []
    unapproved: list[str] = []
    for path in sorted(set(at_base) & set(copy)):
        res.compared += 1
        same = at_base[path] == copy[path]
        if same:
            res.identical += 1
        else:
            differing.append(path)
        if path in approved:
            got = sha256(copy[path])
            if got != approved[path]["sha256_expected_in_copy"]:
                res.fail(
                    f"{path} carries an approved edit ({approved[path]['decision']}) "
                    f"but its content is not the approved one (sha256 {got}, "
                    f"expected {approved[path]['sha256_expected_in_copy']})."
                )
        elif not same:
            unapproved.append(path)
            res.fail(
                f"{path} differs from the frozen base commit and no decision "
                "approves it; this is a finding, not something to absorb."
            )

    for path in approved:
        if path not in copy:
            res.fail(f"approved model edit {path} is not in the copy at all.")

    res.detail = {
        "base_commit": prov["frozen_physics"]["base_commit"],
        "base_commit_full": base,
        "model_files_at_base_commit": len(at_base),
        "model_files_in_copy": len(copy),
        "model_files_missing_from_copy": missing,
        "model_files_added_to_copy": extra,
        "model_files_differing_from_base": differing,
        "approved_differences": {p: a["decision"] for p, a in approved.items()},
        "unapproved_differences": unapproved,
    }
    return res


# ---------------------------------------------------------------------------
# teeth -- each perturbation must make the gate FAIL
# ---------------------------------------------------------------------------


def _staged(root: Path, tmp: Path) -> Path:
    """A throwaway copy of the tree.  The real tree is never perturbed."""
    dest = tmp / "process"
    shutil.copytree(root / "process", dest, ignore=shutil.ignore_patterns("__pycache__"))
    return tmp


def _flip_one_byte(path: Path) -> str:
    """Change exactly one byte, in place, without changing the file's length."""
    data = bytearray(path.read_bytes())
    for i, b in enumerate(data):
        if 0x61 <= b <= 0x7A:  # first lowercase ASCII letter
            data[i] = b - 0x20
            path.write_bytes(bytes(data))
            return f"byte {i} of {path.name}: {chr(b)!r} -> {chr(b - 0x20)!r}"
    raise SystemExit(f"no byte to flip in {path}")


def run_teeth(prov: dict, root: Path, gate: str) -> list[dict]:
    """Perturb, re-run the gate, and require FAIL each time."""
    check = check_copy_identity if gate == "copy-identity" else check_frozen_physics
    sub = "process/models" if gate == "frozen-physics" else "process/core"
    victim = (
        "process/models/vacuum.py"
        if gate == "frozen-physics"
        else "process/core/constants.py"
    )
    teeth: list[tuple[str, str]] = [
        ("one_byte_changed", victim),
        ("file_removed", victim),
        ("file_added", f"{sub}/_tooth_added.py"),
    ]
    # A fourth tooth per gate: a change to a file that IS allowed to differ,
    # made somewhere other than the approved place.  Without it, "the permitted
    # edit list" would be a blanket pardon for those files.
    if gate == "copy-identity":
        teeth.append(("permitted_file_changed_elsewhere", "process/core/caller.py"))
    else:
        teeth.append(("approved_file_changed_further", "process/models/pulse.py"))

    results = []
    for kind, target in teeth:
        with tempfile.TemporaryDirectory() as td:
            staged = _staged(root, Path(td))
            p = staged / target
            if kind == "file_removed":
                p.unlink()
                what = f"removed {target}"
            elif kind == "file_added":
                p.write_text("# a file the source commit does not have\n")
                what = f"added {target}"
            else:
                what = _flip_one_byte(p)
            res = check(prov, staged)
            results.append(
                {
                    "tooth": kind,
                    "perturbation": what,
                    "gate_verdict": "PASS" if res.passed else "FAIL",
                    "tooth_result": "TRIPPED" if not res.passed else "DID NOT TRIP",
                    "first_failure": res.failures[0] if res.failures else None,
                }
            )
    return results


# ---------------------------------------------------------------------------
# smoke import -- the copy is the tree that would actually run
# ---------------------------------------------------------------------------


def smoke_import() -> dict:
    """``import process`` in a fresh subprocess must resolve under the copy.

    Trap T6: a git worktree does not redirect the editable install, and the
    editable install in this environment points at the repository-root
    package.  Setting PYTHONPATH to the copy's directory is what selects the
    copy, and ``process.__file__`` -- the path, never ``__version__``, which
    trap T10 shows can report a different commit than the tree holds -- is what
    proves it.  Run from a directory that is neither tree, so cwd cannot be
    what resolves the import.

    The tooth is the same subprocess without PYTHONPATH: it must resolve
    somewhere other than the copy, or PYTHONPATH was not what selected it.
    """
    code = "import process; print(process.__file__)"
    neutral = tempfile.mkdtemp()
    results = {}
    for name, env_extra in (("with_pythonpath", str(COPY_ROOT)), ("tooth_without_pythonpath", None)):
        env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
        if env_extra:
            env["PYTHONPATH"] = env_extra
        proc = subprocess.run(
            [sys.executable, "-c", code],
            cwd=neutral,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        results[name] = {
            "returncode": proc.returncode,
            "process_file": proc.stdout.strip(),
            "stderr": proc.stderr.strip()[-400:],
        }
    shutil.rmtree(neutral, ignore_errors=True)

    under_copy = results["with_pythonpath"]["process_file"].startswith(
        str(COPY_ROOT / "process") + "/"
    )
    tooth_elsewhere = not results["tooth_without_pythonpath"][
        "process_file"
    ].startswith(str(COPY_ROOT / "process") + "/")
    results["python"] = sys.executable
    results["cwd_used"] = neutral
    results["verdict"] = "PASS" if under_copy and tooth_elsewhere else "FAIL"
    results["tooth_result"] = "TRIPPED" if tooth_elsewhere else "DID NOT TRIP"
    return results


# ---------------------------------------------------------------------------
# PROVENANCE.json
# ---------------------------------------------------------------------------


def build_provenance(commit: str, base: str, root: Path) -> dict:
    """Assemble the provenance record from the commits and the copy on disk."""
    full = _git("rev-parse", commit).decode().strip()
    base_full = _git("rev-parse", base).decode().strip()
    source = blobs_at(full, SOURCE_PREFIX)
    copy = on_disk(root, SOURCE_PREFIX)

    differing = sorted(p for p in source if p in copy and source[p] != copy[p])
    if differing != sorted(PERMITTED_EDIT_FILES):
        raise SystemExit(
            "refusing to write PROVENANCE.json: the files differing from the "
            f"source commit are {differing}, but the permitted-edit list names "
            f"{sorted(PERMITTED_EDIT_FILES)}.  Regenerating provenance must "
            "never be the way an unapproved edit becomes approved."
        )

    at_base = blobs_at(base_full, MODELS_PREFIX)
    approved = []
    for path, decision in sorted(APPROVED_MODEL_EDITS.items()):
        approved.append(
            {
                "path": path,
                "decision": decision,
                "sha256_at_base_commit": sha256(at_base[path]),
                "sha256_expected_in_copy": sha256(copy[path]),
            }
        )
    model_diff = sorted(p for p in at_base if at_base[p] != copy.get(p))
    if model_diff != sorted(APPROVED_MODEL_EDITS):
        raise SystemExit(
            "refusing to write PROVENANCE.json: models/ differs from "
            f"{base} in {model_diff}, the approved set is "
            f"{sorted(APPROVED_MODEL_EDITS)}."
        )

    return {
        "what": (
            "Provenance of V4's own copy of the PROCESS package.  The copy was "
            "extracted from the source commit below, not from a working tree, "
            "and receives exactly the permitted edits listed here.  Gates "
            "copy-identity and frozen-physics (G0') in copy_gates.py check "
            "both claims and are runnable at any later commit."
        ),
        "task": "A46 (process-copy)",
        "decision": (
            "D20, 2026-09-10 -- V4 runs its own copy of PROCESS and owes V3 no "
            "backward compatibility"
        ),
        "generated_by": "PROCESS/copy_gates.py provenance",
        "copy_date": _dt.date.today().isoformat(),
        "source": {
            "repository": "PROCESS_surgery (this repository), branch architecture_surgery",
            "path": "process/  -- the PROCESS package at the repository root",
            "commit": full[:8],
            "commit_full": full,
            "tree_sha1": _git("rev-parse", f"{full}:{SOURCE_PREFIX}").decode().strip(),
            "file_count": len(source),
            "total_bytes": sum(len(b) for b in source.values()),
            "extracted_with": f"git archive {full[:8]} process | tar -x -C PROCESS/",
        },
        "frozen_physics": {
            "what": (
                "D5 freezes the physics and engineering models at the base "
                "commit; D11 permits minimal structural edits under "
                "process/models/ with the user's approval.  Gate G0' checks "
                "the copy's models/ against the base commit and refuses any "
                "difference outside the approved list."
            ),
            "base_commit": base_full[:8],
            "base_commit_full": base_full,
            "scope": f"{MODELS_PREFIX}/",
            "model_file_count": len(at_base),
            "approved_differences": approved,
        },
        "permitted_edits": {
            "what": (
                "The complete set of changes the copy receives (harness "
                "implementation plan section 3.3 as amended by section 11).  "
                "Three path constants are re-pointed from the repository-root "
                "research tree at the V4 harness beside the copy; nothing "
                "else in the copied tree differs from the source commit.  The "
                "three targets do not exist yet -- later harness tasks create "
                "harness/ystate.py and harness/data/."
            ),
            "files": {
                path: {
                    "constants": [
                        {
                            "name": name,
                            "was": WAS[name],
                            "now": NOW[name],
                        }
                        for name in PERMITTED_EDIT_FILES[path]
                    ],
                    "sha256_at_source_commit": sha256(source[path]),
                    "sha256_expected_in_copy": sha256(copy[path]),
                    "expected_hunks": expected_hunks(source[path], copy[path], path),
                }
                for path in sorted(PERMITTED_EDIT_FILES)
            },
        },
        "files": {
            "what": (
                "sha256 of every copied file as it stands at the source "
                "commit.  The two permitted-edit files differ in the copy; "
                "their expected post-edit sha256 is above."
            ),
            "sha256_at_source_commit": {p: sha256(b) for p, b in sorted(source.items())},
        },
    }


#: What each re-pointed constant resolved to before and after, written out so
#: PROVENANCE.json reads without opening the source.
WAS = {
    "YSTATE_MODULE_PATH": 'Path(__file__).resolve().parents[3] / "arch_surgery" / "fixedpoint" / "ystate.py"',
    "NODE_WRITESET_PATH": 'Path(__file__).resolve().parents[2] / "arch_surgery" / "docs" / "data" / "node_writesets.json"',
    "NODE_MAP_PATH": 'Path(__file__).resolve().parents[2] / "arch_surgery" / "docs" / "data" / "dsm_node_map.json"',
}
NOW = {
    "YSTATE_MODULE_PATH": 'Path(__file__).resolve().parents[4] / "harness" / "ystate.py"',
    "NODE_WRITESET_PATH": 'Path(__file__).resolve().parents[3] / "harness" / "data" / "node_writesets.json"',
    "NODE_MAP_PATH": 'Path(__file__).resolve().parents[3] / "harness" / "data" / "dsm_node_map.json"',
}


# ---------------------------------------------------------------------------
# entry point
# ---------------------------------------------------------------------------


def load_provenance() -> dict:
    if not PROVENANCE.exists():
        raise SystemExit(
            f"{PROVENANCE} is not present; the copy has no provenance and no "
            "gate can be run against it."
        )
    return json.loads(PROVENANCE.read_text())


def report(res: GateResult, teeth: list[dict] | None) -> None:
    print(f"\n=== gate {res.gate} -- {res.label}")
    print(f"    verdict           : {'PASS' if res.passed else 'FAIL'}")
    print(f"    files compared    : {res.compared}")
    print(f"    files identical   : {res.identical}")
    for key in (
        "files_missing_from_copy",
        "files_added_to_copy",
        "unexplained_differences",
        "model_files_missing_from_copy",
        "model_files_added_to_copy",
        "model_files_differing_from_base",
        "unapproved_differences",
    ):
        if key in res.detail:
            value = res.detail[key]
            print(f"    {key:<34}: {value if value else '(none)'}")
    for f in res.failures:
        print(f"    FAILURE: {f}")
    if teeth is not None:
        for t in teeth:
            print(
                f"    tooth {t['tooth']:<34} {t['tooth_result']:<13} "
                f"({t['perturbation']})"
            )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "command",
        choices=[
            "all",
            "copy-identity",
            "frozen-physics",
            "smoke-import",
            "provenance",
        ],
    )
    ap.add_argument("--no-teeth", action="store_true", help="skip the teeth")
    ap.add_argument("--records", default=str(DEFAULT_RECORDS), help="gate record dir")
    ap.add_argument("--force", action="store_true", help="provenance: overwrite")
    ap.add_argument(
        "--source-commit",
        default=None,
        help="provenance: the commit the copy was taken from (defaults to the "
        "one already recorded, which never changes for a given copy)",
    )
    ap.add_argument("--base-commit", default="c0ae5b28", help="provenance: base")
    args = ap.parse_args(argv)

    if args.command == "provenance":
        if PROVENANCE.exists() and not args.force:
            raise SystemExit(
                f"{PROVENANCE} already exists.  Regenerating it re-blesses "
                "whatever the tree currently holds, so it needs --force and a "
                "reviewer who reads the resulting diff."
            )
        source = args.source_commit
        if source is None:
            if not PROVENANCE.exists():
                raise SystemExit(
                    "no PROVENANCE.json to take the source commit from; pass "
                    "--source-commit explicitly."
                )
            source = json.loads(PROVENANCE.read_text())["source"]["commit_full"]
        prov = build_provenance(source, args.base_commit, COPY_ROOT)
        PROVENANCE.write_text(json.dumps(prov, indent=2) + "\n")
        print(f"wrote {PROVENANCE}")
        print(f"  source commit {prov['source']['commit_full']}")
        print(f"  {prov['source']['file_count']} files, "
              f"{prov['source']['total_bytes']} bytes")
        return 0

    prov = load_provenance()

    if args.command in ("all", "smoke-import"):
        s = smoke_import()
        print("\n=== smoke import -- the copy is the tree that would run")
        print(f"    python            : {s['python']}")
        print(f"    verdict           : {s['verdict']}")
        print(f"    with PYTHONPATH   : {s['with_pythonpath']['process_file']}")
        print(
            f"    tooth (no PYTHONPATH, must differ): "
            f"{s['tooth_without_pythonpath']['process_file']}  "
            f"[{s['tooth_result']}]"
        )
        out = Path(args.records) / "smoke_import" / "gate.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(s, indent=2) + "\n")
        print(f"    record            : {out}")
        if args.command == "smoke-import":
            return 0 if s["verdict"] == "PASS" else 1
        if s["verdict"] != "PASS":
            print("\nGATE FAILURE")
            return 1

    gates = (
        ["copy-identity", "frozen-physics"] if args.command == "all" else [args.command]
    )
    ok = True
    for gate in gates:
        check = check_copy_identity if gate == "copy-identity" else check_frozen_physics
        res = check(prov, COPY_ROOT)
        teeth = None if args.no_teeth else run_teeth(prov, COPY_ROOT, gate)
        report(res, teeth)
        blunt = [t for t in (teeth or []) if t["tooth_result"] != "TRIPPED"]
        if blunt:
            ok = False
            print(f"    TEETH FAILED: {[t['tooth'] for t in blunt]}")
        ok = ok and res.passed
        out = Path(args.records) / gate.replace("-", "_") / "gate.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(
                {
                    **res.as_dict(),
                    "teeth": teeth,
                    "teeth_all_tripped": teeth is not None and not blunt,
                    "run_at": _dt.datetime.now().isoformat(timespec="seconds"),
                },
                indent=2,
            )
            + "\n"
        )
        print(f"    record            : {out}")

    print(f"\n{'ALL GATES PASS' if ok else 'GATE FAILURE'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
