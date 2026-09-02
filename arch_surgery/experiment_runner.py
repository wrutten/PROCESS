#!/usr/bin/env python
"""The machinery both experiment entry points share.

``MDA_partition_experiment.py`` (Phase A) and ``MDA_partition_opt_experiment.py``
(Phase B) differ in **which phase they drive**, not in how they drive it.  Both
need the same things and neither should own them:

* a prerequisite check that fails immediately, naming the exact fix, rather
  than a traceback three frames deep;
* a provenance banner --- tree, branch, commit, dirty marker --- printed before
  anything runs, because a run against the wrong tree succeeds and produces
  numbers of the wrong program;
* an honest runtime and disk estimate printed *before* the first subprocess;
* a ``--quick`` smoke mode that exercises every stage in minutes, with what it
  does and does not verify said plainly;
* a subprocess environment with ``PYTHONPATH`` naming this tree, because a
  ``git worktree`` does not redirect an editable install (trap T6);
* a verification mode that compares a run's output against the published
  numbers, per deck, with denominators, and reports a disagreement loudly.

Nothing here measures anything.  Every number comes from code that was written,
reviewed and gated as its own task.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

TREE = Path(__file__).resolve().parent.parent

#: The interpreter this repository's PROCESS runs under.  Named rather than
#: assumed: there are sibling conda environments on this machine whose editable
#: installs point at **different clones of PROCESS at different commits**, and
#: they import without error.  Picking the wrong one is a silent failure, not
#: an error -- the run succeeds and the numbers are of the wrong tree.
EXPECTED_ENV = "PROCESS_surgery_env"
EXPECTED_PYTHON = (
    f"/home/wrutten/anaconda3/envs/{EXPECTED_ENV}/bin/python"
)


# ---------------------------------------------------------------------------
# provenance
# ---------------------------------------------------------------------------


def _git(*args) -> str | None:
    try:
        out = subprocess.run(
            ["git", "-C", str(TREE), *args],
            capture_output=True, text=True, timeout=30,
        )
        return out.stdout.strip() if out.returncode == 0 else None
    except Exception:
        return None


def provenance() -> dict:
    """Tree, branch, commit and dirty marker, as ``run_one.py`` prints them."""
    status = _git("status", "--porcelain")
    return {
        "tree": str(TREE),
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "commit": _git("rev-parse", "HEAD"),
        "commit_short": _git("rev-parse", "--short", "HEAD"),
        "dirty": bool(status),
        "n_dirty_paths": len(status.splitlines()) if status else 0,
        "describes_base_c0ae5b28": (
            _git("merge-base", "--is-ancestor", "c0ae5b28", "HEAD") is not None
        ),
    }


def print_provenance() -> dict:
    p = provenance()
    print("provenance")
    print(f"  tree            {p['tree']}")
    print(f"  branch          {p['branch']}")
    print(f"  commit          {p['commit_short']} "
          f"{'(DIRTY: ' + str(p['n_dirty_paths']) + ' paths)' if p['dirty'] else '(clean)'}")
    if not p["describes_base_c0ae5b28"]:
        print("  WARNING         this tree does not descend from the "
              "experiment's base commit c0ae5b28")
    return p


# ---------------------------------------------------------------------------
# prerequisites -- fail immediately, naming the exact fix
# ---------------------------------------------------------------------------


class Prerequisite(SystemExit):
    """A missing prerequisite, reported with the command that fixes it."""


def _fail(what: str, fix: str) -> None:
    raise Prerequisite(
        f"\nCANNOT RUN: {what}\n\nTHE FIX:\n    {fix}\n"
    )


def check_prerequisites(scenarios, *, need_artifacts=(), need_harvest=False,
                        runs_root: Path | None = None) -> dict:
    """Everything the run needs, checked before the first subprocess.

    Each failure names the exact command or path that fixes it.  A run that
    dies twenty minutes in because a deck was missing has wasted twenty
    minutes; a run that dies in a traceback has also wasted the reader's time
    working out what the traceback means.
    """
    rec: dict = {"checks": []}

    def ok(name, detail=""):
        rec["checks"].append({"check": name, "status": "ok", "detail": detail})

    # 1. the tree we are in
    if not (TREE / "arch_surgery").is_dir():
        _fail(
            f"{TREE} has no arch_surgery/ directory, so this is not this "
            f"project's branch.  main carries none of this project.",
            "git checkout architecture_surgery   # or work in a task worktree",
        )
    ok("tree has arch_surgery/")

    # 2. the interpreter
    exe = Path(sys.executable).resolve()
    try:
        import process  # noqa: PLC0415
        pf = Path(process.__file__).resolve()
    except Exception:
        _fail(
            f"this interpreter ({exe}) cannot import PROCESS.",
            f"PYTHONPATH={TREE} {EXPECTED_PYTHON} "
            f"{Path(sys.argv[0]).name} ...",
        )
    actual_tree = pf.parent.parent
    if actual_tree != TREE:
        _fail(
            f"'import process' resolves to {pf}\n             (tree "
            f"{actual_tree}), not to this tree {TREE}.\n             This is "
            f"trap T6: a git worktree does not redirect an editable install, "
            f"and\n             a prefix test would pass on the wrong tree.  "
            f"A run against the wrong\n             tree SUCCEEDS and produces "
            f"numbers of the wrong program.",
            f"PYTHONPATH={TREE} {EXPECTED_PYTHON} "
            f"{Path(sys.argv[0]).name} ...",
        )
    ok("import process resolves to this exact tree", str(pf))

    # The check above passes trivially when this script is run by path, because
    # Python puts the script's own directory first on sys.path.  The case that
    # actually matters is a **measurement subprocess**, which runs in its own
    # working directory and gets the tree only from PYTHONPATH -- and a
    # worktree does not redirect an editable install (trap T6).  So the
    # subprocess environment is checked as a subprocess, not asserted.
    probe = subprocess.run(
        [sys.executable, "-c",
         "import process,pathlib;"
         "print(pathlib.Path(process.__file__).resolve().parent.parent)"],
        env=subprocess_env(Path(runs_root or TREE)),
        cwd=str(Path(os.environ.get("TMPDIR", "/tmp"))),
        capture_output=True, text=True, timeout=120,
    )
    sub_tree = probe.stdout.strip()
    if sub_tree != str(TREE):
        _fail(
            f"a measurement subprocess imports PROCESS from {sub_tree!r},\n"
            f"             not from this tree {TREE}.  Every measurement "
            f"would be of the\n             wrong program, and it would "
            f"succeed rather than fail.",
            f"this is what PYTHONPATH is for; the runner sets it, so seeing "
            f"this means\n    the environment overrides it.  Unset "
            f"PYTHONPATH and re-run.",
        )
    ok("a measurement subprocess imports this exact tree", sub_tree)
    if EXPECTED_ENV not in str(exe):
        print(f"  NOTE: the interpreter is {exe}, which is not "
              f"{EXPECTED_ENV}.  'import process' still resolves to this "
              f"tree, so the run is valid, but PROCESS_env and func_PROCESS_env "
              f"point at different clones and would not.")
    rec["python"] = str(exe)
    rec["process_file"] = str(pf)

    # 3. the decks
    missing = [
        s for s in scenarios
        if not (TREE / "arch_surgery" / "idf_probe" / "scenarios"
                / f"{s}.IN.DAT").exists()
    ]
    if missing:
        _fail(
            f"input deck(s) not found for {missing}",
            f"the frozen decks live in "
            f"{TREE / 'arch_surgery' / 'idf_probe' / 'scenarios'}; pass "
            f"--scenarios with names that exist there",
        )
    ok(f"{len(scenarios)} input deck(s) present")

    # 4. committed data artifacts
    data = TREE / "arch_surgery" / "docs" / "data"
    for pat in need_artifacts:
        for s in scenarios:
            f = data / pat.format(scenario=s)
            if not f.exists():
                _fail(
                    f"committed artifact {f} is missing",
                    f"it is tracked in git; restore it with\n"
                    f"    git -C {TREE} checkout -- "
                    f"arch_surgery/docs/data/",
                )
    if need_artifacts:
        ok(f"{len(need_artifacts) * len(scenarios)} committed artifact(s) present")

    # 5. the recorded harvest, if this phase replays one
    if need_harvest and runs_root is not None:
        rec["harvest"] = harvest_status(runs_root, scenarios)
        ok("harvest checked", json.dumps(rec["harvest"]["summary"]))

    # 6. disk
    try:
        free_gb = shutil.disk_usage(str(TREE)).free / 2**30
        rec["free_disk_gb"] = round(free_gb, 1)
        if free_gb < 5:
            _fail(
                f"only {free_gb:.1f} GB free on the volume holding {TREE}",
                "free space, or pass --runs-root pointing at a volume with "
                "at least 5 GB",
            )
        ok(f"{free_gb:.0f} GB free disk")
    except Exception:
        pass
    return rec


def harvest_status(runs_root: Path, scenarios) -> dict:
    """Is A18's recorded harvest present, and is it usable?

    **Treated as a cache to be verified, not a dependency to be trusted.**  It
    is 35 MB per deck and is not duplicated per worktree, so a worktree usually
    reaches it through a symlink into the main checkout's untracked run tree.
    If it is absent the caller must rebuild it rather than skip the stage --- a
    silently skipped stage is the empty-set false pass this project has met
    before.
    """
    a18 = runs_root / "a18"
    per = {}
    for s in scenarios:
        h = a18 / s / "harvest" / "harvest.pkl"
        r = a18 / s / "replay_tau1e-06_hoist0" / "result.json"
        per[s] = {
            "harvest": str(h),
            "harvest_present": h.exists(),
            "harvest_bytes": h.stat().st_size if h.exists() else 0,
            "a18_reference_result_present": r.exists(),
        }
    n = sum(1 for v in per.values() if v["harvest_present"])
    return {
        "root": str(a18),
        "is_symlink": a18.is_symlink(),
        "resolves_to": str(a18.resolve()) if a18.exists() else None,
        "per_scenario": per,
        "summary": {
            "n_harvests_present": n,
            "n_scenarios": len(scenarios),
            "complete": n == len(scenarios),
        },
    }


# ---------------------------------------------------------------------------
# subprocess plumbing
# ---------------------------------------------------------------------------


def subprocess_env(runs_root: Path) -> dict:
    """PYTHONPATH names this tree; every architecture switch is cleared.

    An inherited ``PROCESS_ARCH_*`` would change what is being measured without
    saying so, so they are removed rather than assumed absent.
    """
    env = dict(os.environ)
    env["PYTHONPATH"] = str(TREE)
    env["MPLCONFIGDIR"] = str(runs_root / "_mplconfig")
    for k in (
        "PROCESS_IDF_PROBE", "PROCESS_ARCH_SEQUENCE", "PROCESS_ARCH_HOIST",
        "PROCESS_ARCH_LIFT", "PROCESS_ARCH_MODULE_SOLVE", "PROCESS_ARCH_TAU",
        "PROCESS_ARCH_INNER_TAU", "PROCESS_ARCH_YSTATE",
        "PROCESS_ARCH_WRITESET",
    ):
        env.pop(k, None)
    return env


def run_step(label: str, cmd: list[str], runs_root: Path) -> int:
    print(f"\n=== {label}\n    {' '.join(str(c) for c in cmd)}", flush=True)
    t0 = time.perf_counter()
    rc = subprocess.run(
        [str(c) for c in cmd], env=subprocess_env(runs_root), cwd=str(TREE)
    ).returncode
    dt = time.perf_counter() - t0
    # Elapsed time is progress information, not a measurement.  No conclusion
    # in this experiment rests on a timing, and identical work has been
    # observed to vary by up to 35 % in processor time on this machine (I-10).
    print(f"--- {label}: exit {rc} ({dt:.1f} s elapsed, not a measurement)",
          flush=True)
    return rc


# ---------------------------------------------------------------------------
# stages
# ---------------------------------------------------------------------------


@dataclass
class Stage:
    """One stage of an experiment, with what it costs before it is run."""

    name: str
    fn: object
    what: str
    minutes_full: float
    minutes_quick: float
    disk_mb: float = 0.0
    needs: tuple = ()
    quick_note: str = ""
    optional_reason: str = ""
    extra: dict = field(default_factory=dict)


def print_plan(title: str, stages, *, quick: bool, scenarios, runs_root: Path,
               skipped=()) -> None:
    """The honest estimate, printed before anything runs."""
    total = sum((s.minutes_quick if quick else s.minutes_full) for s in stages)
    disk = sum(s.disk_mb * (0.1 if quick else 1.0) for s in stages)
    print(f"\n{title}")
    print(f"  mode            {'QUICK SMOKE' if quick else 'FULL'}")
    print(f"  decks           {', '.join(scenarios)}")
    print(f"  artifacts       {runs_root}  (untracked; nothing is written to "
          f"the tracked tree)")
    print(f"\n  {'stage':<18}{'minutes':>9}  what it does")
    print(f"  {'-' * 18}{'-' * 9}  {'-' * 46}")
    for s in stages:
        m = s.minutes_quick if quick else s.minutes_full
        print(f"  {s.name:<18}{m:>9.0f}  {s.what}")
    for s in skipped:
        print(f"  {s.name:<18}{'skipped':>9}  {s.optional_reason}")
    print(f"  {'-' * 18}{'-' * 9}")
    print(f"  {'TOTAL':<18}{total:>9.0f}  minutes, on this machine, "
          f"serial-ish at the default job count")
    print(f"  {'disk':<18}{disk:>9.0f}  MB of untracked run artifacts")
    if quick:
        print(
            "\n  WHAT --quick DOES VERIFY: that every stage runs end to end, "
            "that the\n  arrangements import and resolve the variant points "
            "they claim, that every\n  gate executes and is shown capable of "
            "failing, and that the analysis reads\n  what the runs wrote."
            "\n  WHAT IT DOES NOT VERIFY: any published number.  It runs one "
            "test case with a\n  handful of starting points and a short "
            "ladder, so its counts are its own\n  and must not be compared "
            "with the report's.  Two checks are also weaker here\n  and say "
            "so where they run: a cross-test-case perturbation needs two test "
            "cases\n  and is reported NOT APPLICABLE on one, and the "
            "reproduction gate is NOT\n  truncated even in --quick, because "
            "comparing a shortened point set against a\n  full recording is "
            "a different comparison rather than a cheaper one."
        )
    print(flush=True)


def drive(title: str, stages, args, runs_root: Path, scenarios) -> int:
    """Run the selected stages in order, stopping at the first failure."""
    print_provenance()
    print_plan(title, stages, quick=args.quick, scenarios=scenarios,
               runs_root=runs_root)
    runs_root.mkdir(parents=True, exist_ok=True)
    (runs_root / "_mplconfig").mkdir(exist_ok=True)
    results: dict[str, int] = {}
    t0 = time.perf_counter()
    for s in stages:
        results[s.name] = s.fn(args, runs_root)
        if results[s.name] != 0:
            print(f"\nSTOPPING: stage '{s.name}' exited {results[s.name]}.  "
                  f"Later stages would report tables built on a partial "
                  f"result.", flush=True)
            break
    print("\n=== summary")
    for s in stages:
        v = results.get(s.name)
        print(f"  {s.name:<18}"
              + ("ok" if v == 0 else (f"FAILED ({v})" if v is not None
                                      else "not run")))
    print(f"  elapsed {(time.perf_counter() - t0) / 60:.1f} min "
          f"(progress information, not a measurement)")
    return 0 if results and all(v == 0 for v in results.values()) else 1


# ---------------------------------------------------------------------------
# verification against the published numbers
# ---------------------------------------------------------------------------


def _rel(a, b):
    if a is None or b is None:
        return None
    a, b = float(a), float(b)
    return abs(b - a) / (abs(a) if a else 1.0)


def verify_table(name: str, published: dict, measured: dict, *,
                 exact: bool = True, rtol: float = 0.0) -> dict:
    """Compare a run's numbers with the published ones, per deck.

    **A disagreement is a finding, not an error.**  It is reported loudly, with
    both numbers and the deck, and the caller's exit code says so --- but
    nothing is swallowed, retried or reconciled quietly.  Counts are compared
    exactly; a figure that is a ratio of counts is compared to *rtol* and the
    tolerance is stated in the record.
    """
    rows = []
    for deck in sorted(set(published) | set(measured)):
        p, m = published.get(deck), measured.get(deck)
        if p is None or m is None:
            rows.append({"deck": deck, "status": "MISSING",
                         "published": p, "measured": m})
            continue
        if exact:
            agree = p == m
            detail = None
        else:
            r = _rel(p, m)
            agree = r is not None and r <= rtol
            detail = {"relative_difference": r, "rtol": rtol}
        rows.append({
            "deck": deck, "published": p, "measured": m,
            "status": "AGREES" if agree else "DISAGREES", "detail": detail,
        })
    n_dec = sum(1 for r in rows if r["status"] in ("AGREES", "DISAGREES"))
    n_ok = sum(1 for r in rows if r["status"] == "AGREES")
    return {
        "table": name,
        "comparison": "exact" if exact else f"relative, rtol={rtol:g}",
        "n_decks_compared": n_dec,
        "n_decks_agreeing": n_ok,
        "denominator_decks_named": len(rows),
        "status": ("AGREES" if n_dec and n_ok == n_dec
                   else ("EMPTY" if not n_dec else "DISAGREES")),
        "per_deck": rows,
    }


def print_verification(records) -> int:
    """Print every comparison, per deck, with its denominator.  Loudly."""
    print("\n=== verification against the published numbers")
    print("    Counts and bit-comparisons are the acceptance quantities.")
    print("    Timings are context and are never compared.\n")
    bad = 0
    for rec in records:
        print(f"  {rec['table']}  ({rec['comparison']})")
        for r in rec["per_deck"]:
            mark = {"AGREES": "  ok  ", "DISAGREES": " DIFF ",
                    "MISSING": " MISS "}[r["status"]]
            print(f"    [{mark}] {r['deck']:<24} published "
                  f"{r['published']!s:>16}   measured {r['measured']!s:>16}"
                  + (f"   rel {r['detail']['relative_difference']:.3g}"
                     if r.get("detail") and
                     r["detail"].get("relative_difference") is not None
                     else ""))
        print(f"    -> {rec['n_decks_agreeing']} of "
              f"{rec['n_decks_compared']} decks agree "
              f"(of {rec['denominator_decks_named']} named)\n")
        if rec["status"] != "AGREES":
            bad += 1
    if bad:
        print(f"  {bad} table(s) DISAGREE with the published numbers.")
        print("  That is a FINDING and must be reported, not reconciled "
              "quietly.  The\n  most likely causes, in order: a different "
              "tree, a different deck list,\n  a partial run, or a real "
              "change in the code.  Check the provenance\n  banner above "
              "first.")
    else:
        print("  every compared table agrees with the published numbers.")
    return 1 if bad else 0
