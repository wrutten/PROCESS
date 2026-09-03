#!/usr/bin/env python
"""A32 (tail-confirm): run the confirming campaign A31 left derived -- and
report why it cannot run on the committed driver.

The task
--------
A31 (drift-diagnostic) named the mechanism behind ``st_regression``'s
recurring 3rd-7th-outer-pass tail (A28: 2 802 of 54 480 ``A1'`` calls at
3+ passes): the A18-mode coupling-state spec asserts **exact equality** on
the harvest-constant ``pf_power.srcktpm``, which flickers by 1-2 ULPs at
hostile states.  Under the committed a26-mode spec
(``arch_surgery/docs/data/ystate_a26_st_regression.json``, ``srcktpm``
reclassified continuous at scale 1106.688) the flicker scores 4.11e-16
against tau = 1e-6, so the tail should dissolve.  A32 was to demonstrate
that end-to-end: all 25 ``A1'`` starts plus the three heaviest ``A0'``
starts, everything exactly A28's machinery except ``PROCESS_ARCH_YSTATE``
pointing at the a26-mode spec.

The result (stage ``preflight``): **the campaign cannot start.**  The
committed driver refuses the a26-mode artifact before a single model runs,
for two independent reasons, and lifting either requires a change under
``process/`` -- which this task is forbidden to make ("no process/ change
of any kind ... if you find you do, stop and report").  This script
therefore demonstrates the blocker reproducibly instead of working around
it (a failed gate is a result, not an obstacle):

**B1 -- the spec loader rebuilds every artifact as SPEC_MODE_A18.**
``process/core/solver/module_solve.py`` (``load_spec``) constructs
``YSpec(keys, category, scale, n, comps)`` with no ``mode`` and no
``scale_floor``, so the rebuilt spec hashes its components *without* the
mode preamble that ``arch_surgery/fixedpoint/ystate.py``'s
``components_sha256`` prepends for any non-A18 mode
(``mode=a26|floor=0x1.0000000000000p+0\\n``).  The a26 artifact's committed
``components_sha256`` includes that preamble, the A18-style rebuild does
not, the two can never match, and ``load_spec`` raises "ystate artifact
... does not rebuild".  No a26-mode artifact has ever been loaded by the
in-tree driver: A26's SPEC_MODE_A26 measurements ran through
``arch_surgery/fixedpoint/replay.py``, which builds its specs offline via
``YSpec.from_harvest(mode=...)`` and only cross-checks the committed
record.

**B2 -- there is no a26-generation write-set artifact.**
``load_subsets`` (same file) refuses any write set whose
``ystate_components_sha256`` differs from the loaded spec's --
deliberately: "the two artifacts are not from the same deck and
generation".  The only committed write set for this deck,
``writeset_st_regression.json``, pins the A18 generation, and the
committed generator (``a25_writeset.py``) is hard-wired to
``ystate_<scenario>.json``.  Even with B1 fixed, the run refuses here.

Neither blocker is a defect in what it guards: both checks are doing
exactly what they were built to do -- refuse a spec/write-set pairing
nobody has generated.  The missing piece is (i) one line in ``load_spec``
passing the record's ``spec_mode`` and ``scale_floor`` through to
``YSpec`` (provably neutral for A18-mode artifacts: ``mode`` enters only
the sha preamble and the serialisation, never the residual -- but that is
to be *gated* per protocol 12 after the change, not asserted here), and
(ii) an a26-generation write set (same subsets -- the module write sets do
not depend on the spec's categorisation -- re-stamped against the a26
spec's sha).  Both need the user's authorisation.

Stages (protocol 15: every published number comes from executing this
committed script; failure paths are reachable from the same entry point)
------------------------------------------------------------------------
``gate``
    The brief's protocol-12 reproduction gate, run even though the
    campaign it licenses cannot start: one **A18-mode** ``A1'`` run at
    start000, exactly A28's configuration (via A31's proven recipe), must
    reproduce A28's recorded start000 bit-for-bit on three exact fields --
    ``node_calls_solve_phase`` 37312, ``outer_pass_hist`` {1:9, 2:560,
    3:1}, ``norm_objf`` hex.  Teeth: each field's comparator perturbed by
    the smallest registrable amount must trip.  This isolates the blocker:
    the harness is fine, the spec loader is the whole of what is missing.
``preflight``
    The blocker, demonstrated four ways, all recorded in
    ``runs/a32/preflight/blocker.json``:
    (a) both committed spec artifacts rebuilt in-process through
    ``fixedpoint/ystate.YSpec`` under both modes, ``components_sha256``
    per (artifact, mode) -- showing exactly which hash the loader computes
    and which the artifact carries;
    (b) the write-set pairing: the committed write set's recorded
    ``ystate_components_sha256`` against both specs;
    (c) ``module_solve.load_spec`` called in a fresh subprocess under the
    **exact campaign environment** (``run_a28.env_for``, ``PYTHONPATH``
    pinned, tree asserted -- traps T6/T10) on the A18 artifact (control:
    must load) and on the a26 artifact (must refuse, error captured);
    (d) one full campaign-style ``A1'`` start000 run attempted under the
    a26 spec -- the campaign's own first run, refusing at spec load with
    no model evaluated.
``campaign`` / ``a0p``
    Refuse with the blocker message while ``preflight`` finds B1 standing.
    They are the failure path made reachable, not stubs to be filled by
    editing this docstring's verdict away: when the driver change is
    authorised and merged, the follow-up task extends these stages and
    re-gates.

Isolation: every PROCESS run is a fresh subprocess in its own working
directory, ``PYTHONPATH`` pinned to this worktree and the exact tree
asserted inside the subprocess (traps T6/T10).  No conclusion rests on a
timing; every quantity this script emits is a count, a name, a hash or a
bit-exact float.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TREE = HERE.parent.parent
DATA = TREE / "arch_surgery" / "docs" / "data"
RUNS = HERE / "runs" / "a32"

sys.path.insert(0, str(HERE))
from run_a28 import TAU, deck_for, env_for  # noqa: E402
from a31_drift_probe import gate_compare, gate_extract, gate_teeth  # noqa: E402

#: The main checkout: A28's recorded metrics live there and are read,
#: never written.
MAIN = Path("/home/wrutten/projects/PROCESS_surgery")
A28_REF_DIR = MAIN / "arch_surgery/idf_probe/runs/a28/h5/st_regression/A1p"

SCENARIO = "st_regression"
#: D15's calibrated perturbation size, exactly as the A28 campaign ran it.
DELTA = 0.10

YSTATE_A18 = DATA / f"ystate_{SCENARIO}.json"
YSTATE_A26 = DATA / f"ystate_a26_{SCENARIO}.json"
WRITESET = DATA / f"writeset_{SCENARIO}.json"


# --------------------------------------------------------------------------
# running one PROCESS start (A31's recipe, parameterised on the spec)
# --------------------------------------------------------------------------


def run_one_a32(
    arm: str,
    outdir: Path,
    *,
    seed: int,
    delta: float | None,
    ystate: Path,
    timeout: int = 5400,
) -> dict:
    """One isolated run, the A28 way, with the coupling-state spec explicit.

    Mirrors ``a31_drift_probe.run_one_a31`` (which the A31 neutrality gate
    proved reproduces A28 bit-for-bit) with two deliberate differences:
    ``PROCESS_ARCH_YSTATE`` is set from the ``ystate`` argument -- the one
    experimental variable of this task -- and no trace is taken (A28's
    campaign ran untraced).  The exit audit stays on the **A18** artifact
    for every run, a26 runs included: it is the yardstick A28's recorded
    exit residuals were measured with, and changing it would change the
    ruler alongside the thing being measured.
    """
    if outdir.exists():
        shutil.rmtree(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(HERE / "run_one.py"),
        "--scenario", SCENARIO,
        "--mode", "control",
        "--outdir", str(outdir),
        "--expect-tree", str(TREE),
        "--input", str(deck_for(SCENARIO, arm, RUNS / "_decks")),
        "--exit-audit", str(YSTATE_A18),
        "--entry-census",
    ]
    if delta is not None:
        cmd += ["--perturb-delta", repr(delta), "--perturb-seed", str(seed)]
    env = env_for(SCENARIO, arm, RUNS, TAU, None)
    env.pop("PROCESS_ARCH_PASS_TRACE", None)
    env.pop("PROCESS_ARCH_PASS_TRACE_FULL_FROM", None)
    env["PROCESS_ARCH_YSTATE"] = str(ystate)
    t0 = time.perf_counter()
    try:
        proc = subprocess.run(
            cmd, env=env, capture_output=True, text=True, cwd=str(outdir),
            timeout=timeout,
        )
        rc, out, err = proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        rc, out, err = 124, exc.stdout or "", (exc.stderr or "") + "\nTIMEOUT"
    (outdir / "stdout.log").write_text(out)
    (outdir / "stderr.log").write_text(err)
    mpath = outdir / "metrics.json"
    if not mpath.exists():
        mpath.write_text(json.dumps({
            "scenario": SCENARIO, "mode": "control",
            "status": "no_metrics", "returncode": rc,
            "perturb_delta": delta, "perturb_seed": seed,
        }, indent=2))
    rec = json.loads(mpath.read_text())
    rec["a32_arm"] = arm
    rec["a32_tau"] = TAU
    rec["a32_delta"] = delta
    rec["a32_seed"] = seed
    rec["a32_ystate"] = str(ystate)
    mpath.write_text(json.dumps(rec, indent=2))
    wall = time.perf_counter() - t0
    print(f"  {arm} seed={seed} ystate={ystate.name} rc={rc} {wall:6.1f}s "
          f"(wall clock is progress information, not a measurement)",
          flush=True)
    return {"arm": arm, "seed": seed, "rc": rc, "outdir": str(outdir),
            "wall_s": wall}


# --------------------------------------------------------------------------
# stage: gate (the brief's protocol-12 reproduction gate, A18 mode)
# --------------------------------------------------------------------------


def stage_gate() -> int:
    """A18-mode A1' start000 must reproduce A28's record bit-for-bit."""
    outdir = RUNS / "gate" / "A1p_start000"
    r = run_one_a32("A1p", outdir, seed=0, delta=DELTA, ystate=YSTATE_A18)
    ref_path = A28_REF_DIR / "start000" / "metrics.json"
    ref = gate_extract(json.loads(ref_path.read_text()))
    got = gate_extract(json.loads((outdir / "metrics.json").read_text()))
    verdict = gate_compare(ref, got)
    teeth = gate_teeth(ref, got)
    record = {
        "gate": "A32 harness reproduction of A28 start000 (protocol 12)",
        "reference": {"path": str(ref_path)},
        "run": {"outdir": str(outdir), "rc": r["rc"]},
        "comparison": verdict,
        "teeth": teeth,
        "verdict": (
            "PASS" if (verdict["pass"] and teeth["all_tripped"] and r["rc"] == 0)
            else "FAIL"
        ),
    }
    (RUNS / "gate" / "gate.json").write_text(json.dumps(record, indent=2))
    print(json.dumps(record, indent=2))
    return 0 if record["verdict"] == "PASS" else 1


# --------------------------------------------------------------------------
# stage: preflight (the blocker, demonstrated)
# --------------------------------------------------------------------------


def _ystate_module():
    """``arch_surgery/fixedpoint/ystate.py``, loaded by path (not a package)."""
    p = TREE / "arch_surgery" / "fixedpoint" / "ystate.py"
    spec = importlib.util.spec_from_file_location("_a32_ystate", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _rebuild_shas(artifact: Path, ys) -> dict:
    """``components_sha256`` of the artifact rebuilt under each spec mode.

    This is the project's own hash (``YSpec.components_sha256``), not a
    re-implementation: the artifact's component list is fed to ``YSpec``
    once per mode, exactly as ``module_solve.load_spec`` would (mode a18,
    its hard default) and as a mode-aware loader would (the artifact's own
    ``spec_mode`` and ``scale_floor``).
    """
    rec = json.loads(artifact.read_text())
    keys, category, scale = [], [], []
    for c in rec["components"]:
        ns, _, fld = c["key"].partition(".")
        keys.append((ns, fld))
        category.append(c["category"])
        scale.append(float(c.get("scale", 0.0)))
    out = {
        "artifact": str(artifact),
        "spec_mode_in_artifact": rec.get("spec_mode"),
        "scale_floor_in_artifact": rec.get("scale_floor"),
        "committed_components_sha256": rec.get("components_sha256"),
        "n_components": rec.get("n_components"),
    }
    for mode in (ys.SPEC_MODE_A18, ys.SPEC_MODE_A26):
        spec = ys.YSpec(
            keys, category, scale, rec.get("n_components"),
            mode=mode,
            scale_floor=float(rec.get("scale_floor", ys.SCALE_FLOOR)),
        )
        out[f"rebuilt_as_{mode}"] = spec.components_sha256()
    out["loader_rebuild_matches_artifact"] = (
        out["rebuilt_as_a18"] == out["committed_components_sha256"]
    )
    out["mode_aware_rebuild_matches_artifact"] = (
        out[f"rebuilt_as_{rec.get('spec_mode')}"]
        == out["committed_components_sha256"]
    )
    return out


_SUBPROC_LOAD_SPEC = r"""
import json, sys
import process
tree = sys.argv[1]
assert process.__file__.startswith(tree + "/"), (
    "wrong tree: " + process.__file__)
from process.core.solver import module_solve
try:
    spec, prov = module_solve.load_spec()
    print(json.dumps({
        "loaded": True,
        "spec_mode_attr": spec.mode,
        "components_sha256": prov["components_sha256"],
        "n_components": prov["n_components"],
    }))
except Exception as exc:
    print(json.dumps({
        "loaded": False,
        "error_type": type(exc).__name__,
        "error": str(exc),
    }))
"""


def _subprocess_load_spec(ystate: Path, outdir: Path) -> dict:
    """``module_solve.load_spec`` under the exact campaign environment."""
    env = env_for(SCENARIO, "A1p", RUNS, TAU, None)
    env["PROCESS_ARCH_YSTATE"] = str(ystate)
    proc = subprocess.run(
        [sys.executable, "-c", _SUBPROC_LOAD_SPEC, str(TREE)],
        env=env, capture_output=True, text=True, cwd=str(outdir),
        timeout=600,
    )
    try:
        rec = json.loads(proc.stdout.strip().splitlines()[-1])
    except Exception:
        rec = {"loaded": False, "error_type": "subprocess_failure",
               "error": (proc.stderr or proc.stdout)[-2000:]}
    rec["ystate"] = str(ystate)
    rec["returncode"] = proc.returncode
    return rec


def stage_preflight() -> int:
    outdir = RUNS / "preflight"
    outdir.mkdir(parents=True, exist_ok=True)
    ys = _ystate_module()

    # (a) both artifacts, rebuilt under both modes, hashed by the project's
    # own code
    shas = {
        "a18": _rebuild_shas(YSTATE_A18, ys),
        "a26": _rebuild_shas(YSTATE_A26, ys),
    }

    # (b) the write-set pairing
    ws = json.loads(WRITESET.read_text())
    writeset = {
        "path": str(WRITESET),
        "ystate_components_sha256": ws.get("ystate_components_sha256"),
        "pairs_with_a18_spec": (
            ws.get("ystate_components_sha256")
            == shas["a18"]["committed_components_sha256"]
        ),
        "pairs_with_a26_spec": (
            ws.get("ystate_components_sha256")
            == shas["a26"]["committed_components_sha256"]
        ),
    }

    # (c) load_spec in a fresh subprocess under the exact campaign env
    load_a18 = _subprocess_load_spec(YSTATE_A18, outdir)
    load_a26 = _subprocess_load_spec(YSTATE_A26, outdir)

    # (d) the campaign's own first run, attempted under the a26 spec
    attempt = run_one_a32(
        "A1p", outdir / "A1p_start000_a26_attempt",
        seed=0, delta=DELTA, ystate=YSTATE_A26,
    )
    # run_one.py catches the crash and stamps its traceback into
    # metrics.json (status "crashed"); stderr carries nothing.
    attempt_metrics = json.loads(
        (Path(attempt["outdir"]) / "metrics.json").read_text()
    )
    tb = attempt_metrics.get("traceback") or ""
    attempt["status"] = attempt_metrics.get("status")
    attempt["refused_at_spec_load"] = (
        "module_solve.load_spec()" in tb and "does not rebuild" in tb
    )
    attempt["zero_models_evaluated"] = (
        attempt_metrics.get("node_calls_solve_phase") is None
        and attempt_metrics.get("n_model_calls") is None
    )
    attempt["traceback_tail"] = tb[-1200:]

    b1_standing = not load_a26.get("loaded", False)
    b2_standing = not writeset["pairs_with_a26_spec"]
    record = {
        "preflight": "A32 a26-mode spec loadability (the campaign's precondition)",
        "component_sha256_rebuilds": shas,
        "writeset_pairing": writeset,
        "load_spec_subprocess_a18_control": load_a18,
        "load_spec_subprocess_a26": load_a26,
        "campaign_first_run_attempt_a26": attempt,
        "blocker_B1_spec_loader_mode_blind": b1_standing,
        "blocker_B2_no_a26_generation_writeset": b2_standing,
        "verdict": (
            "BLOCKED" if (b1_standing or b2_standing) else "CLEAR"
        ),
    }
    (outdir / "blocker.json").write_text(json.dumps(record, indent=2))
    print(json.dumps({k: v for k, v in record.items()
                      if k != "campaign_first_run_attempt_a26"}, indent=2))
    print(f"\npreflight verdict: {record['verdict']} "
          f"(B1 {'standing' if b1_standing else 'clear'}, "
          f"B2 {'standing' if b2_standing else 'clear'}); "
          f"full record in {outdir / 'blocker.json'}")
    return 0 if record["verdict"] == "CLEAR" else 3


# --------------------------------------------------------------------------
# stages: campaign / a0p (refuse while the blocker stands)
# --------------------------------------------------------------------------

_BLOCKED_MSG = (
    "A32's campaign is blocked: the committed driver cannot load the "
    "a26-mode spec (see runs/a32/preflight/blocker.json, and the report "
    "arch_surgery/docs/reports/A32_tail_confirm.md).  Lifting the blocker "
    "requires a change under process/ (module_solve.load_spec must pass "
    "the record's spec_mode and scale_floor through to YSpec) plus an "
    "a26-generation write-set artifact -- both need the user's "
    "authorisation.  This stage refuses rather than working around a "
    "validation check (a failed gate is a result, not an obstacle)."
)


def stage_campaign() -> int:
    if stage_preflight() != 0:
        print(f"\n{_BLOCKED_MSG}")
        return 3
    raise SystemExit(
        "preflight is CLEAR: the blocker has been lifted since this script "
        "was written.  The campaign stage was deliberately not implemented "
        "on an untestable path -- extend it (all 25 A1' starts + A0' "
        "starts 010/005/015, run_one_a32 with ystate=YSTATE_A26) and "
        "re-gate per protocol 12 before publishing any number."
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("stage",
                    choices=["gate", "preflight", "campaign", "a0p", "all"])
    args = ap.parse_args()
    RUNS.mkdir(parents=True, exist_ok=True)
    (RUNS / "_mplconfig").mkdir(exist_ok=True)

    if args.stage == "gate":
        return stage_gate()
    if args.stage == "preflight":
        return stage_preflight()
    if args.stage in ("campaign", "a0p"):
        return stage_campaign()
    rc = stage_gate()
    return stage_preflight() or rc


if __name__ == "__main__":
    raise SystemExit(main())
