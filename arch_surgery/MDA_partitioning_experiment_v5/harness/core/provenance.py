"""Which interpreter, which tree, which commit — refused if wrong, not warned.

Derived from ``arch_surgery/idf_probe/run_one.py::_provenance`` and
``arch_surgery/MDA_partitioning_experiment_v3/run_experiment.py::
_assert_interpreter`` at ``f2dc9243`` (task A47), with one change: the single
"is the tree dirty" boolean is split into *tracked modifications* and
*untracked paths*, recorded separately.

Why the split.  A run stamped dirty because a draft file sits beside the
runner tells a reader nothing, and task A44 (transfer-gap) produced a whole
set of records stamped that way while the measured code was clean.  A
modified tracked file can change a measurement; an untracked one cannot.  The
old boolean survives, derived from the tracked half only, so a campaign
refusing on scratch files is no longer possible and a campaign passing over a
modified tracked file still is not.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

#: The experiment's base commit.  Every number is rederived here; anything
#: measured elsewhere is not comparable (D2, D4).
BASE_COMMIT = "c0ae5b28"

#: How many paths a stamp lists before it starts counting instead.
_LIST_CAP = 20


class ProvenanceError(RuntimeError):
    """A refusal to start.  Never downgraded to a warning."""


# --------------------------------------------------------------------------
# the interpreter
# --------------------------------------------------------------------------


def assert_interpreter(tree: Path) -> str:
    """Refuse before any subprocess if this interpreter cannot run PROCESS.

    Every measurement subprocess is launched with ``sys.executable``, so the
    interpreter that starts the runner decides the interpreter for all of
    them.  Started under the wrong one, the first run dies and every later one
    would too — and on 2026-09-04 that was reported as "the reference arm did
    not converge", a machinery failure wearing a physics result's clothes.
    """
    probe = "import process, sys; sys.stdout.write(process.__file__)"
    result = subprocess.run(
        [sys.executable, "-c", probe],
        capture_output=True,
        text=True,
        env={**_clean_pythonpath(), "PYTHONPATH": str(tree)},
    )
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    why = (result.stderr or "").strip().splitlines()
    raise ProvenanceError(
        "refusing to start: this interpreter cannot import PROCESS.\n"
        f"  interpreter : {sys.executable}\n"
        f"  version     : {sys.version.split()[0]}\n"
        f"  error       : {why[-1] if why else (result.stdout or 'unknown')}\n"
        f"  needs       : process importable from {tree}\n"
        "  Every measurement subprocess inherits this interpreter, so starting\n"
        "  here would fail every run identically.  Use the project environment:\n"
        "    /home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python"
    )


def _clean_pythonpath() -> dict[str, str]:
    import os

    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    return env


# --------------------------------------------------------------------------
# the tree
# --------------------------------------------------------------------------


def assert_tree(expected: Path) -> Path:
    """Refuse unless the imported PROCESS is *exactly* the expected tree.

    Equality of the directory holding the package, not a prefix match: the
    editable install points at the main checkout, so a prefix test passes on
    the main tree even when the run is meant to measure a worktree (trap T6).

    ``process.__version__`` is never consulted.  It is written when a tree is
    archived and frozen with it, so it can report a different commit than the
    one the tree actually contains — a check that fails by agreeing with a
    plausible wrong answer is worse than no check (trap T10).
    """
    import process

    actual_file = Path(process.__file__).resolve()
    actual_tree = actual_file.parent.parent
    expected = Path(expected).resolve()
    if actual_tree != expected:
        raise ProvenanceError(
            f"wrong tree: imported {actual_file} (tree {actual_tree}), "
            f"expected exactly {expected}.  Set PYTHONPATH={expected}."
        )
    return actual_file


# --------------------------------------------------------------------------
# the commit
# --------------------------------------------------------------------------


def _git(path: Path, *args: str) -> str | None:
    """One git command against *path*; its stripped output, or None."""
    try:
        out = subprocess.run(
            ["git", "-C", str(path), *args],
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception:
        return None
    if out.returncode != 0:
        return None
    return out.stdout.strip() or None


def _status_paths(path: Path, *, untracked: str) -> list[str]:
    raw = _git(path, "status", "--porcelain", f"--untracked-files={untracked}")
    return [line for line in (raw or "").splitlines() if line.strip()]


def _descends_from(path: Path, commit: str) -> bool | None:
    """True if HEAD descends from *commit*; None if it cannot be told.

    ``merge-base --is-ancestor`` answers through its exit status and prints
    nothing, so it needs its own call rather than :func:`_git`.
    """
    try:
        return (
            subprocess.run(
                ["git", "-C", str(path), "merge-base", "--is-ancestor", commit, "HEAD"],
                capture_output=True,
                check=False,
            ).returncode
            == 0
        )
    except Exception:
        return None


def git_stamp(path: Path) -> dict[str, Any]:
    """Head, branch, describe, base-commit descent, and the two dirt kinds.

    ``tree_modified_tracked`` lists modifications to tracked files — the only
    kind that can change a measurement.  ``tree_untracked_paths`` lists what
    git has never seen, as context; a draft file beside the runner belongs
    here and marks nothing dirty.
    """
    path = Path(path)
    branch = _git(path, "rev-parse", "--abbrev-ref", "HEAD")
    if branch == "HEAD":
        branch = "(detached)"
    tracked = _status_paths(path, untracked="no")
    everything = _status_paths(path, untracked="normal")
    untracked = [line[3:] for line in everything if line.startswith("??")]
    return {
        "tree": str(path),
        "repository": _git(path, "rev-parse", "--show-toplevel"),
        "tree_git_head": _git(path, "rev-parse", "HEAD"),
        "tree_git_branch": branch,
        "tree_git_describe": _git(path, "describe", "--always", "--dirty"),
        "tree_modified_tracked": tracked[:_LIST_CAP],
        "tree_modified_tracked_n": len(tracked),
        "tree_untracked_paths": untracked[:_LIST_CAP],
        "tree_untracked_paths_n": len(untracked),
        # Derived from the tracked half only, deliberately.
        "tree_git_dirty": bool(tracked),
        "tree_contains_base_commit": _descends_from(path, BASE_COMMIT),
        "base_commit": BASE_COMMIT,
    }


def stamp(tree: Path, *, process_file: str | None = None) -> dict[str, Any]:
    """The full provenance block a record carries."""
    record = git_stamp(tree)
    record.update(
        {
            "python": sys.executable,
            "python_version": sys.version.split()[0],
            "process_file": process_file,
        }
    )
    return record


def banner(record: Mapping[str, Any]) -> str:
    """The provenance lines printed at startup.

    Provenance only written to a file is provenance nobody reads in time.
    """
    head = record.get("tree_git_head") or "unknown"
    lines = [
        f"  tree       {record.get('tree')}",
        f"  branch     {record.get('tree_git_branch') or 'unknown'}",
        f"  commit     {head[:12]}",
        f"  modified   {record.get('tree_modified_tracked_n', 0)} tracked file(s)"
        + ("  [THIS CAN CHANGE A MEASUREMENT]" if record.get("tree_git_dirty") else ""),
        f"  untracked  {record.get('tree_untracked_paths_n', 0)} path(s)  "
        f"(context only; does not mark the tree dirty)",
    ]
    if record.get("tree_contains_base_commit") is False:
        lines.append(
            f"  WARNING    this tree does not descend from the base commit "
            f"{BASE_COMMIT}; numbers from it are not comparable with the "
            f"rest of the study."
        )
    return "\n".join(lines)
