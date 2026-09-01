#!/usr/bin/env python
"""A23 (flat-arm-permutation) driver: one replay subprocess per scenario.

Reuses A18's harvested design points rather than re-harvesting.  **A22 licensed
that reuse by comparing git tree hashes and finding them equal; that test no
longer passes**, because ``process/`` has changed twice since A18 -- A3
(build-reorder) rewrote three call sites in ``process/core/caller.py`` as a list
the caller walks, and A13 (feedforward-hoist) added the deferral hook and routed
three more call sites through a helper.  So this driver answers the underlying
question instead, and records the evidence in ``_licence.json`` rather than
asserting it in a docstring:

1.  **Which files under ``process/`` differ** between the commit the harvest was
    taken at -- read from the harvest run's own ``metrics.json``, not assumed --
    and this tree's ``HEAD``.  The claim to be checked is not "nothing changed"
    but "nothing the replay executes changed".
2.  **What the replay executes**: the ``run()`` methods of the model objects,
    plus ``process/core/solver/{constraints,iteration_variables,objectives}``,
    ``process/main`` and ``process/data_structure``.  The replay never enters
    ``Caller._call_models_once`` -- it calls the node callables directly -- so a
    change confined to ``caller.py`` is not on its path.  That also means A3's
    and A13's bit-identical gates, which gated ``_call_models_once``, do not by
    themselves license this reuse; the file-level disjointness does.
3.  **The committed coupling-state record** (``arch_surgery/docs/data/
    ystate_<scenario>.json``) is compared against the harvest by content hash
    inside the replay itself, which binds the scales and categories in use to
    the harvest they were measured from.
4.  **The empirical half**: arm ``A0`` is re-run in A18's own node order and
    must reproduce A18's recorded ``A0`` bit-for-bit on every design point.  If
    the models had moved under the harvest, that would not be zero.

Every subprocess is fresh, has its own working directory, gets an explicit
``PYTHONPATH`` naming the tree under test, and asserts the **exact** tree it
imported (trap T6: in a ``git worktree`` the editable install still points at
the main checkout).
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TREE = HERE.parent.parent
PROBE = TREE / "arch_surgery" / "idf_probe"
RUNS = PROBE / "runs" / "a23"
SCENARIOS_DIR = PROBE / "scenarios"

SCENARIOS = [
    "large_tokamak_nof",
    "low_aspect_ratio_DEMO",
    "st_regression",
    "large_tokamak_eval",
]

TAU = 1e-6

#: Files under ``process/`` that may differ from the harvest commit without
#: affecting a replay, each with the reason.  The test is framed as an
#: **exemption list, not a whitelist of replay paths**: any changed file not
#: named here fails the licence, so a file nobody thought about cannot slip
#: through by failing to match a prefix.
#:
#: The exemption for ``caller.py`` is the load-bearing one, and it is not taken
#: on faith: ``a23_permute.py`` counts entries to ``Caller.call_models``,
#: ``Caller._call_models_once`` and ``Caller._node`` across the whole replay and
#: records them.  The licence requires those counts to be zero.
EXEMPT_CHANGED_FILES = {
    "process/core/caller.py": (
        "A3 (VP1) and A13 (VP2). The replay calls each node's run() directly "
        "and never enters Caller; the entry counters in a23_permute.py measure "
        "that rather than assuming it. Both switches also default to upstream "
        "and are asserted unset."
    ),
    "process/core/_idf_probe_harvest.py": (
        "A18's harvest probe. Active only with PROCESS_IDF_PROBE set, which "
        "the replay refuses to run under."
    ),
    "process/core/_idf_probe.py": "probe, inert with PROCESS_IDF_PROBE unset",
    "process/core/_idf_probe_frozen.py": "probe, inert with the switch unset",
    "process/core/_idf_probe_modules.py": "probe, inert with the switch unset",
}


def _sha256(path: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(TREE), *args],
        capture_output=True, text=True, check=True,
    ).stdout.strip()


def licence(a18_runs: Path, scenarios: list[str]) -> dict:
    """Assemble the documentary half of the harvest-reuse argument."""
    head = _git("rev-parse", "HEAD")
    harvest_commits = {}
    for s in scenarios:
        m = a18_runs / s / "harvest" / "metrics.json"
        if m.exists():
            d = json.loads(m.read_text())
            harvest_commits[s] = {
                "tree_git_head": d.get("tree_git_head"),
                "tree": d.get("tree"),
                "process_file": d.get("process_file"),
                "probe_enabled": d.get("probe_enabled"),
                "probe_mode": d.get("probe_mode"),
                "n_model_calls": d.get("n_model_calls"),
                "status": d.get("status"),
            }
    commits = sorted({v["tree_git_head"] for v in harvest_commits.values()
                      if v.get("tree_git_head")})

    out = {
        "head": head,
        "head_describe": _git("log", "-1", "--format=%h %s", "HEAD"),
        "harvest_commits_by_scenario": harvest_commits,
        "distinct_harvest_commits": commits,
        "per_commit": {},
        "exempt_changed_files": EXEMPT_CHANGED_FILES,
    }
    for c in commits:
        changed = [
            f for f in _git("diff", "--name-only", c, head, "--",
                            "process").splitlines() if f
        ]
        on_path = [f for f in changed if f not in EXEMPT_CHANGED_FILES]
        out["per_commit"][c] = {
            "process_files_changed": changed,
            "n_process_files_changed": len(changed),
            "changed_and_not_exempt": on_path,
            "n_changed_on_replay_path": len(on_path),
            "models_tree_same": (
                _git("rev-parse", f"{c}:process/models")
                == _git("rev-parse", f"{head}:process/models")
            ),
            "solver_tree_same": (
                _git("rev-parse", f"{c}:process/core/solver")
                == _git("rev-parse", f"{head}:process/core/solver")
            ),
            "data_structure_tree_same": (
                _git("rev-parse", f"{c}:process/data_structure")
                == _git("rev-parse", f"{head}:process/data_structure")
            ),
        }
    # The committed coupling-state records postdate the harvests -- they were
    # generated *from* them -- so comparing ``arch_surgery/docs/data`` at a
    # harvest commit is the wrong question and would fail for the right reason.
    # What matters is that nothing has touched them since A18 committed them,
    # which is the last commit to touch the path; and, more strongly, that each
    # record's stored harvest content hash still matches the harvest being
    # replayed, which ``_check_ystate`` verifies inside every subprocess.
    out["docs_data_last_touched"] = _git(
        "log", "-1", "--format=%H %h %ad %s", "--date=iso", head, "--",
        "arch_surgery/docs/data",
    )
    out["licensed_by_disjointness"] = bool(commits) and all(
        v["n_changed_on_replay_path"] == 0
        and v["models_tree_same"]
        and v["solver_tree_same"]
        and v["data_structure_tree_same"]
        for v in out["per_commit"].values()
    )
    out["worktree_dirty"] = bool(_git("status", "--porcelain"))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--a18-runs", required=True,
                    help="A18's runs/a18 directory: the harvests and the A0 "
                         "of record")
    ap.add_argument("--scenarios", nargs="*", default=SCENARIOS)
    ap.add_argument("--tau", type=float, default=TAU)
    ap.add_argument("--max-points", type=int, default=0)
    ap.add_argument("--sensitivity", action="store_true")
    ap.add_argument("--tag", default="")
    args = ap.parse_args()

    a18 = Path(args.a18_runs).resolve()
    runs = RUNS if not args.tag else RUNS.parent / f"a23_{args.tag}"
    runs.mkdir(parents=True, exist_ok=True)
    (runs / "_mplconfig").mkdir(exist_ok=True)

    lic = licence(a18, args.scenarios)
    (runs / "_licence.json").write_text(json.dumps(lic, indent=2))
    print("harvest-reuse licence:", json.dumps(
        {k: lic[k] for k in ("head", "distinct_harvest_commits",
                             "licensed_by_disjointness", "worktree_dirty")},
        indent=2), flush=True)

    rows = []
    for s in args.scenarios:
        out = runs / s
        if out.exists():
            shutil.rmtree(out)
        out.mkdir(parents=True)
        shutil.copy(SCENARIOS_DIR / f"{s}.IN.DAT", out / f"{s}.IN.DAT")
        src = a18 / s / "harvest" / "harvest.pkl"
        ref = a18 / s / f"replay_tau{args.tau:g}_hoist0" / "result.json"
        if not src.exists():
            print(f"  MISSING harvest for {s}: {src}", flush=True)
            rows.append({"scenario": s, "returncode": 127})
            continue
        # The harvest is copied into this tree because the committed
        # coupling-state record identifies it by a path relative to the tree as
        # well as by content hash.  Both digests are recorded and must agree, so
        # the copy is provably the same bytes as A18's artifact.
        (out / "harvest").mkdir()
        harvest = out / "harvest" / "harvest.pkl"
        shutil.copy(src, harvest)
        d_src, d_dst = _sha256(src), _sha256(harvest)
        if d_src != d_dst:
            print(f"  COPY MISMATCH for {s}: {d_src} != {d_dst}", flush=True)
            rows.append({"scenario": s, "returncode": 126})
            continue
        cmd = [
            sys.executable, str(HERE / "a23_permute.py"),
            "--harvest", str(harvest),
            "--scenario", s,
            "--input", f"{s}.IN.DAT",
            "--out", str(out / "result.json"),
            "--expect-tree", str(TREE),
            "--tau", repr(args.tau),
        ]
        if ref.exists():
            cmd += ["--a18", str(ref)]
        if args.max_points:
            cmd += ["--max-points", str(args.max_points)]
        if args.sensitivity:
            cmd += ["--sensitivity"]
        env = dict(os.environ)
        env["PYTHONPATH"] = str(TREE)
        env["MPLCONFIGDIR"] = str(runs / "_mplconfig")
        env.pop("PROCESS_IDF_PROBE", None)
        env.pop("PROCESS_ARCH_SEQUENCE", None)
        env.pop("PROCESS_ARCH_HOIST", None)
        t0 = time.perf_counter()
        proc = subprocess.run(cmd, env=env, cwd=str(out), capture_output=True,
                              text=True)
        (out / "run.stdout.log").write_text(proc.stdout)
        (out / "run.stderr.log").write_text(proc.stderr)
        rows.append({"scenario": s, "returncode": proc.returncode,
                     "wall_s": time.perf_counter() - t0,
                     "harvest_sha256": d_src,
                     "harvest_source": str(src),
                     "a18_reference": str(ref) if ref.exists() else None})
        print(f"  replay {s:24s} rc={proc.returncode}", flush=True)
        print(proc.stdout[-4000:] if proc.returncode == 0
              else proc.stderr[-3000:], flush=True)
    (runs / "_log.json").write_text(json.dumps(rows, indent=2))
    return 0 if all(r["returncode"] == 0 for r in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
