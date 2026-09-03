"""V2 shared runner: arm environments, isolated runs, the worker pool.

Imports the idf_probe machinery rather than duplicating it (plan Appendix A
item 6): decks derive through ``run_a28.stage_decks``'s path conventions,
runs execute through ``run_one.py`` in a fresh subprocess each (isolation is
mandatory — OutputFileManager holds handles as class attributes), and the
environment is built from nothing with every architecture switch cleared
first, exactly ``run_a28.env_for``'s discipline.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import v2_config as cfg

sys.path.insert(0, str(cfg.IDF_PROBE))
from run_a28 import _ARCH_VARS, PULSED as A28_PULSED  # noqa: E402

#: Three more switches than A28 knew about (A33's and A34's); cleared
#: alongside the rest so an inherited value can never change what is being
#: measured.
_ALL_ARCH_VARS = tuple(_ARCH_VARS) + (
    "PROCESS_ARCH_POST_SOLVE",   # A33: post-solve exclusion artifact
    "PROCESS_ARCH_OUTER",        # A34: trust mode (no outer loop)
    "PROCESS_ARCH_PIN_BURN_TIME",  # A34: Phase A pin
)


def deck_for(deck: str, arm: str, decks_dir: Path) -> Path:
    """A1/A2 on a pulsed deck take the derived lifted deck; everyone else the
    frozen scenario (D9: the frozen scenarios are never edited)."""
    if arm in ("B1", "B2", "B3") and deck in cfg.PULSED:
        return decks_dir / deck / f"{deck}_lifted.IN.DAT"
    return cfg.IDF_PROBE / "scenarios" / f"{deck}.IN.DAT"


def derive_lifted_decks(decks_dir: Path) -> None:
    """Derive the lifted decks from the frozen scenarios via the committed
    A28 stage (never copied, never hand-edited)."""
    proc = subprocess.run(
        [sys.executable, str(cfg.IDF_PROBE / "run_a28.py"), "decks",
         "--runs", str(cfg.RUNS / "_a28runs"), "--decks", str(decks_dir),
         "--scenarios", *[d for d in cfg.DECKS if d in cfg.PULSED]],
        capture_output=True, text=True, timeout=1200,
    )
    if proc.returncode != 0:
        raise SystemExit(
            f"lifted-deck derivation failed (rc={proc.returncode}):\n"
            f"{proc.stdout[-2000:]}\n{proc.stderr[-2000:]}"
        )


def env_for(deck: str, arm: str, *, a18_machinery_smoke: bool = False) -> dict:
    """The environment one V2 arm runs under, built from nothing.

    ``a18_machinery_smoke`` runs the arm against the A18-generation artifacts
    instead of the a26 ones — used ONLY by the smoke stage for a pulsed deck
    whose a26 write set A33 has not yet delivered.  Smoke numbers are never
    published; the flag exists so machinery can be exercised before every
    artifact lands, and it is stamped into the record.
    """
    env = dict(os.environ)
    env["PYTHONPATH"] = str(cfg.TREE)
    env["MPLCONFIGDIR"] = str(cfg.RUNS / "_mplconfig")
    for k in _ALL_ARCH_VARS:
        env.pop(k, None)

    if arm == "R":
        return env

    if a18_machinery_smoke:
        ystate = cfg.DATA / f"ystate_{deck}.json"
        writeset = cfg.DATA / f"writeset_{deck}.json"
    else:
        ystate, writeset = cfg.ystate_for(deck), cfg.writeset_for(deck)
    env["PROCESS_ARCH_TAU"] = repr(cfg.TAU)
    env["PROCESS_ARCH_YSTATE"] = str(ystate)
    env["PROCESS_ARCH_WRITESET"] = str(writeset)

    if arm == "B0":
        env["PROCESS_ARCH_MODULE_SOLVE"] = "flat_state"
        return env

    if arm == "B1":
        # Flat solve + the lift, nothing else: B0 -> B1 varies the lift alone
        # (upstream node order kept; resequencing belongs to B1 -> B2).
        env["PROCESS_ARCH_MODULE_SOLVE"] = "flat_state"
        if deck in cfg.PULSED:
            env["PROCESS_ARCH_LIFT"] = "burn_time"
        return env

    if arm in ("B2", "B3"):
        # B2 and B3 share everything -- resequenced per-module blocks, the
        # lift on pulsed decks, the hoist, the post-solve exclusion -- and
        # differ in exactly one switch: B3 sets trust mode (no outer loop),
        # B2 keeps the verified outer loop (driver default).  The phase
        # script refuses these arms while an instrument is missing, so
        # reaching here with one unavailable is a bug, not a configuration.
        env["PROCESS_ARCH_SEQUENCE"] = "build_after_physics"
        env["PROCESS_ARCH_MODULE_SOLVE"] = "per_module"
        if deck in cfg.PULSED:
            env["PROCESS_ARCH_LIFT"] = "burn_time"
        env["PROCESS_ARCH_HOIST"] = (
            "feedforward_lifted" if deck in cfg.PULSED else "feedforward"
        )
        if cfg.INSTRUMENTATION["post_solve"]["available"]:
            env["PROCESS_ARCH_POST_SOLVE"] = str(cfg.postsolve_for(deck))
        if arm == "B3" and cfg.INSTRUMENTATION["trust_mode"]["available"]:
            env["PROCESS_ARCH_OUTER"] = "trust"
        return env

    raise SystemExit(f"unknown arm {arm!r}")


def run_job(
    deck: str,
    arm: str,
    outdir: Path,
    *,
    seed: int,
    delta: float | None,
    decks_dir: Path,
    node_census: bool = True,
    a18_machinery_smoke: bool = False,
    resume: bool = False,
    drop_env: dict | None = None,
    timeout: int = 5400,
) -> dict:
    """One isolated PROCESS run.  Counts are exact and concurrency-invariant;
    wall clock is stamped as progress information only (plan §2).

    ``resume=True`` skips a run whose directory already holds a complete,
    stamped record for the SAME (deck, arm, seed) — run_a28's --resume
    semantics: an interrupted run is re-run; a directory alone is not taken
    as evidence of a completed run.
    """
    mpath0 = outdir / "metrics.json"
    if resume and mpath0.exists():
        try:
            prev = json.loads(mpath0.read_text())
        except Exception:
            prev = {}
        if (prev.get("status") == "ok" and prev.get("v2_arm") == arm
                and prev.get("v2_seed") == seed
                and prev.get("v2_deck") == deck):
            print(f"  {deck:24s} {arm:3s} seed={seed:<3d} resumed "
                  f"(complete record kept)", flush=True)
            return {"deck": deck, "arm": arm, "seed": seed, "rc": 0,
                    "outdir": str(outdir), "resumed": True}
    if outdir.exists():
        shutil.rmtree(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    audit = (cfg.DATA / f"ystate_{deck}.json") if a18_machinery_smoke \
        else cfg.ystate_for(deck)
    cmd = [
        sys.executable, str(cfg.IDF_PROBE / "run_one.py"),
        "--scenario", deck,
        "--mode", "control",
        "--outdir", str(outdir),
        "--expect-tree", str(cfg.TREE),
        "--input", str(deck_for(deck, arm, decks_dir)),
        "--exit-audit", str(audit),
        "--entry-census",
    ]
    if node_census:
        # Plan §3: per-node counts recorded for every campaign run (the I-10
        # insurance).  The census adds a Python frame per model call, which
        # pollutes timings, never counts — V2's timing context comes from the
        # separate SERIAL repetition block, which runs without it.
        cmd.append("--node-census")
    if delta is not None:
        cmd += ["--perturb-delta", repr(delta), "--perturb-seed", str(seed)]
    env = env_for(deck, arm, a18_machinery_smoke=a18_machinery_smoke)
    # drop_env: gate-stage overrides on top of the arm's composed
    # environment (a value of None removes the variable) — used by the
    # combined-switch equivalence gate to run an arm with one switch off.
    for k, v in (drop_env or {}).items():
        if v is None:
            env.pop(k, None)
        else:
            env[k] = str(v)
    t0 = time.perf_counter()
    try:
        proc = subprocess.run(cmd, env=env, capture_output=True, text=True,
                              cwd=str(outdir), timeout=timeout)
        rc = proc.returncode
        (outdir / "stdout.log").write_text(proc.stdout)
        (outdir / "stderr.log").write_text(proc.stderr)
    except subprocess.TimeoutExpired as exc:
        rc = 124
        (outdir / "stdout.log").write_text(exc.stdout or "")
        (outdir / "stderr.log").write_text((exc.stderr or "") + "\nTIMEOUT")
    mpath = outdir / "metrics.json"
    if not mpath.exists():
        mpath.write_text(json.dumps({
            "scenario": deck, "status": "timeout" if rc == 124 else "no_metrics",
            "returncode": rc, "perturb_delta": delta, "perturb_seed": seed,
        }, indent=2))
    rec = json.loads(mpath.read_text())
    rec["v2_arm"] = arm
    rec["v2_deck"] = deck
    rec["v2_seed"] = seed
    rec["v2_delta"] = delta
    rec["v2_tau"] = cfg.TAU
    rec["v2_a18_machinery_smoke"] = a18_machinery_smoke
    mpath.write_text(json.dumps(rec, indent=2))
    wall = time.perf_counter() - t0
    print(f"  {deck:24s} {arm:3s} seed={seed:<3d} rc={rc} {wall:6.1f}s "
          f"(wall clock is progress information, not a measurement)",
          flush=True)
    return {"deck": deck, "arm": arm, "seed": seed, "rc": rc,
            "outdir": str(outdir)}


def run_pool(jobs: list[dict]) -> list[dict]:
    """W concurrent runs (memory-bound, plan §2).  The job list is
    deterministic and jobs are never retried: a crash is a taxonomy row."""
    results = []
    with ThreadPoolExecutor(max_workers=cfg.WORKERS) as pool:
        futures = [pool.submit(run_job, **j) for j in jobs]
        for f in futures:
            results.append(f.result())
    return results
