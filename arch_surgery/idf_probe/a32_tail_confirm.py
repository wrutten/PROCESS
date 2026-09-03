#!/usr/bin/env python
"""A32 (tail-confirm): run the confirming campaign A31 left derived.

The task
--------
A31 (drift-diagnostic) named the mechanism behind ``st_regression``'s
recurring 3rd-7th-outer-pass tail (A28: 2 802 of 54 480 ``A1'`` calls at
3+ passes): the A18-mode coupling-state spec asserts **exact equality** on
harvest-constants (``pf_power.srcktpm`` and the blanket geometry family),
which flicker by 1-2 ULPs at hostile states.  Under the committed a26-mode
spec (``arch_surgery/docs/data/ystate_a26_st_regression.json``, those
components reclassified continuous with measured scales) the flicker
scores ~4e-16 against tau = 1e-6, so the tail should dissolve.  A32
demonstrates that end-to-end: all 25 ``A1'`` starts plus three ``A0'``
starts, everything exactly A28's machinery except ``PROCESS_ARCH_YSTATE``
(and, forced by it, ``PROCESS_ARCH_WRITESET``) pointing at the a26-mode
generation.

History: the blocker (found and demonstrated at ``e8915f40``)
-------------------------------------------------------------
The campaign could not start on the driver as first committed, for two
independent reasons, both validation checks doing exactly what they were
built to do -- refuse a spec/write-set pairing nobody had generated:

**B1 -- the spec loader rebuilt every artifact as SPEC_MODE_A18.**
``process/core/solver/module_solve.py`` (``load_spec``) constructed
``YSpec(keys, category, scale, n, comps)`` with no ``mode`` and no
``scale_floor``, so the rebuilt spec hashed its components *without* the
mode preamble that ``arch_surgery/fixedpoint/ystate.py``'s
``components_sha256`` prepends for any non-A18 mode.  The a26 artifact's
committed sha includes that preamble, the A18-style rebuild does not, and
``load_spec`` raised "ystate artifact ... does not rebuild".  No a26-mode
artifact had ever been loaded by the in-tree driver: A26's SPEC_MODE_A26
measurements ran through ``arch_surgery/fixedpoint/replay.py``, offline.

**B2 -- there was no a26-generation write-set artifact.**
``load_subsets`` (same file) refuses any write set whose
``ystate_components_sha256`` differs from the loaded spec's; the only
committed write set pinned the A18 generation.

Both were lifted in the follow-up commit on this branch, under the
driver-scope rule (CLAUDE.md: ``process/core/solver/`` changes by
default; the physics under ``process/models/`` untouched): ``load_spec``
now passes the record's own ``spec_mode`` and ``scale_floor`` through to
``YSpec`` (an A18 artifact takes the byte-identical path -- **gated**, not
asserted, by re-running the ``gate`` stage on the fixed driver), and
``a25_writeset.py --spec-variant a26`` generated
``writeset_a26_st_regression.json`` from the same probe census that
reproduces the committed A18 write set exactly (every field but
``tree_git_head``) as its control.  The same pairing gap exists for the
a26 artifacts of the other three decks; V2 owns those.

Stages (protocol 15: every published number comes from executing this
committed script; failure paths are reachable from the same entry point)
------------------------------------------------------------------------
``gate``
    The protocol-12 reproduction gate, now doing double duty: one
    **A18-mode** ``A1'`` run at start000, exactly A28's configuration,
    must reproduce A28's recorded start000 bit-for-bit on three exact
    fields -- ``node_calls_solve_phase`` 37312, ``outer_pass_hist``
    {1:9, 2:560, 3:1}, ``norm_objf`` hex -- **on the fixed driver**, which
    gates the B1 change's switch-neutrality for A18-mode runs.  Teeth:
    each field's comparator perturbed by the smallest registrable amount
    must trip.
``preflight``
    The loadability record, kept as the campaign's precondition: sha
    rebuilds under both modes, both write-set pairings, ``load_spec`` in
    fresh subprocesses under the exact campaign environment, and (full
    mode) one campaign-style ``A1'`` start000 run under the a26 spec.
    While the blocker stood this demonstrated it four ways (the committed
    record at ``e8915f40``); on the fixed driver it must come back CLEAR.
``campaign``
    All 25 ``A1'`` starts (A28's exact enumeration: seed = k,
    delta = 0.10) under the a26-mode spec, then the tally.
``a0p``
    The three ``A0'`` starts heaviest in A28's records by the flat arm's
    own flicker signature.  The flat arm shows **no** 3+-pass tail
    anywhere in A28 (0 of 57 030 calls) -- its flicker appears as the
    moved-constant counter (13 817 of 57 030 calls) -- so these runs
    confirm THAT collapses, not a pass histogram.
``traced``
    One ``A1'`` run at start010 (A28's heaviest tail, 858 calls at 3+
    passes) with A31's env-switched pass trace on, under the a26 spec:
    per-call outer-pass counts from the trace verify BY CALL INDEX that
    any surviving 3+-pass call is the cold first call, and name what its
    extra pass converged.
``tally``
    Re-derive the comparison tables from the run records on disk (also
    run automatically at the end of ``campaign`` / ``a0p``).

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
A28_REF = MAIN / "arch_surgery/idf_probe/runs/a28/h5/st_regression"
A28_REF_DIR = A28_REF / "A1p"

SCENARIO = "st_regression"
#: D15's calibrated perturbation size, exactly as the A28 campaign ran it.
DELTA = 0.10

YSTATE_A18 = DATA / f"ystate_{SCENARIO}.json"
YSTATE_A26 = DATA / f"ystate_a26_{SCENARIO}.json"
WRITESET = DATA / f"writeset_{SCENARIO}.json"
#: The a26-generation write set (B2's fix): same measured subsets as the A18
#: generation -- regenerated by ``a25_writeset.py --spec-variant a26`` from
#: the same probe census, which reproduces the committed A18 artifact exactly
#: (every field but ``tree_git_head``) as its control -- stamped against the
#: a26 spec's ``components_sha256`` so ``load_subsets``'s pairing check holds.
WRITESET_A26 = DATA / f"writeset_a26_{SCENARIO}.json"

#: All 25 campaign starts, exactly A28's enumeration (``jobs_campaign``:
#: seed = k, delta = DELTA for every k including 0).
A1P_STARTS = tuple(range(25))
#: The flat arm shows **no** 3+-pass tail anywhere in A28's records (0 of
#: 57 030 calls) -- its share of the flicker appears as the moved-constant
#: counter instead (13 817 of 57 030 calls with >= 1 moved constant).  The
#: three A0' starts are therefore the heaviest by THAT phenomenon in A28's
#: records: start009 (3 868), start010 (3 637), start012 (1 588).
A0P_STARTS = (9, 10, 12)


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
    trace: bool = False,
    timeout: int = 5400,
) -> dict:
    """One isolated run, the A28 way, with the coupling-state spec explicit.

    Mirrors ``a31_drift_probe.run_one_a31`` (which the A31 neutrality gate
    proved reproduces A28 bit-for-bit) with two deliberate differences:
    ``PROCESS_ARCH_YSTATE`` is set from the ``ystate`` argument -- the one
    experimental variable of this task -- and the campaign runs untraced as
    A28's did (``trace`` exists only for the ``traced`` diagnostic stage).
    The exit audit stays on the **A18** artifact for every run, a26 runs
    included: it is the yardstick A28's recorded exit residuals were
    measured with, and changing it would change the ruler alongside the
    thing being measured.
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
    if ystate == YSTATE_A26:
        # load_subsets refuses a write set from another spec generation, so
        # an a26-spec run must carry the a26-generation write set (B2).
        env["PROCESS_ARCH_WRITESET"] = str(WRITESET_A26)
    if trace:
        env["PROCESS_ARCH_PASS_TRACE"] = str(outdir / "pass_trace.jsonl")
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
    rec["a32_traced"] = trace
    mpath.write_text(json.dumps(rec, indent=2))
    wall = time.perf_counter() - t0
    print(f"  {arm} seed={seed} ystate={ystate.name} rc={rc} {wall:6.1f}s "
          f"(wall clock is progress information, not a measurement)",
          flush=True)
    return {"arm": arm, "seed": seed, "rc": rc, "outdir": str(outdir),
            "wall_s": wall}


# --------------------------------------------------------------------------
# stage: gate (the protocol-12 reproduction gate, A18 mode, fixed driver)
# --------------------------------------------------------------------------


def stage_gate() -> int:
    """A18-mode A1' start000 must reproduce A28's record bit-for-bit.

    On the fixed driver this is the switch-neutrality gate for the B1
    change: ``load_spec`` now passes ``spec_mode``/``scale_floor`` through,
    and an A18 artifact must take the byte-identical path.  If any field
    moves, the campaign does not run -- that failure is the result.
    """
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
# stage: preflight (the campaign's precondition; the blocker's record)
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
    once per mode, exactly as the old mode-blind loader would (mode a18)
    and as the fixed mode-aware loader does (the artifact's own
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
        out[f"rebuilt_as_{rec.get('spec_mode', 'a18')}"]
        == out["committed_components_sha256"]
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
    if ystate == YSTATE_A26:
        env["PROCESS_ARCH_WRITESET"] = str(WRITESET_A26)
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


def stage_preflight(quick: bool = False) -> int:
    """``quick=True`` skips (d), the full campaign-style run -- used by the
    campaign stages as their precondition so probes (a)-(c) still guard
    every run without paying a whole extra solve each time."""
    outdir = RUNS / "preflight"
    outdir.mkdir(parents=True, exist_ok=True)
    ys = _ystate_module()

    # (a) both artifacts, rebuilt under both modes, hashed by the project's
    # own code
    shas = {
        "a18": _rebuild_shas(YSTATE_A18, ys),
        "a26": _rebuild_shas(YSTATE_A26, ys),
    }

    # (b) the write-set pairings: the A18 generation's (A28's), and the a26
    # generation's (B2's fix; absent while B2 stood)
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
    if WRITESET_A26.exists():
        ws26 = json.loads(WRITESET_A26.read_text())
        writeset_a26 = {
            "path": str(WRITESET_A26),
            "exists": True,
            "ystate_components_sha256": ws26.get("ystate_components_sha256"),
            "pairs_with_a26_spec": (
                ws26.get("ystate_components_sha256")
                == shas["a26"]["committed_components_sha256"]
            ),
            "subsets_identical_to_a18_generation": (
                ws26.get("subsets") == ws.get("subsets")
            ),
        }
    else:
        writeset_a26 = {"path": str(WRITESET_A26), "exists": False,
                        "pairs_with_a26_spec": False}

    # (c) load_spec in a fresh subprocess under the exact campaign env
    load_a18 = _subprocess_load_spec(YSTATE_A18, outdir)
    load_a26 = _subprocess_load_spec(YSTATE_A26, outdir)

    b1_standing = not load_a26.get("loaded", False)
    b2_standing = not writeset_a26["pairs_with_a26_spec"]

    # (d) the campaign's own first run under the a26 spec -- the refused
    # attempt while the blocker stood; a full solve once lifted
    attempt: dict | None = None
    if not quick:
        attempt = run_one_a32(
            "A1p", outdir / "A1p_start000_a26_attempt",
            seed=0, delta=DELTA, ystate=YSTATE_A26,
        )
        # run_one.py catches a crash and stamps its traceback into
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

    record = {
        "preflight": "A32 a26-mode spec loadability (the campaign's precondition)",
        "quick": quick,
        "component_sha256_rebuilds": shas,
        "writeset_pairing": writeset,
        "writeset_a26_pairing": writeset_a26,
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
# stages: campaign / a0p (the confirming runs) and tally (the comparison)
# --------------------------------------------------------------------------

_BLOCKED_MSG = (
    "A32's campaign is blocked: the driver cannot load the a26-mode spec "
    "or its write set (see runs/a32/preflight/blocker.json and the report "
    "arch_surgery/docs/reports/A32_tail_confirm.md).  This stage refuses "
    "rather than working around a validation check (a failed gate is a "
    "result, not an obstacle)."
)


def _tail3(hist: dict | None) -> int:
    return sum(v for k, v in (hist or {}).items() if int(k) >= 3)


def _extract(metrics: dict) -> dict:
    t = metrics.get("module_solve_totals") or {}
    return {
        "status": metrics.get("status"),
        "hist": t.get("outer_pass_hist"),
        "tail3": _tail3(t.get("outer_pass_hist")),
        "n_call_models": t.get("n_call_models"),
        "n_moved_constant_calls": t.get("n_call_models_with_moved_constant"),
        "moved_constants": t.get("moved_constants"),
        "block_sweeps": t.get("block_sweeps"),
        "node_calls_solve_phase": metrics.get("node_calls_solve_phase"),
        "norm_objf_hex": (metrics.get("exact") or {}).get("norm_objf"),
    }


def _tally_arm(arm: str, starts, rundir: Path) -> dict:
    """Per-start comparison of the a26-spec runs against A28's records.

    Every start requested is a row whether or not its run produced metrics
    (trap T11: the denominator never shrinks silently).
    """
    rows = []
    for k in starts:
        name = f"start{k:03d}"
        ref = _extract(json.loads(
            (A28_REF / arm / name / "metrics.json").read_text()))
        mpath = rundir / name / "metrics.json"
        got = (_extract(json.loads(mpath.read_text())) if mpath.exists()
               else {"status": "missing", "hist": None, "tail3": None,
                     "n_call_models": None, "n_moved_constant_calls": None,
                     "moved_constants": None, "block_sweeps": None,
                     "node_calls_solve_phase": None, "norm_objf_hex": None})
        rows.append({
            "start": name,
            "a28": {k2: v for k2, v in ref.items() if k2 != "moved_constants"},
            "a32": {k2: v for k2, v in got.items() if k2 != "moved_constants"},
            "a32_moved_constants": got.get("moved_constants"),
            "norm_objf_hex_equal": (
                ref["norm_objf_hex"] is not None
                and ref["norm_objf_hex"] == got["norm_objf_hex"]
            ),
        })
    ok = [r for r in rows if r["a32"]["status"] == "ok"]
    totals = {
        "n_starts": len(rows),
        "n_ok": len(ok),
        "statuses": sorted({str(r["a32"]["status"]) for r in rows}),
        "a28_tail3_total": sum(r["a28"]["tail3"] for r in rows),
        "a28_call_models_total": sum(r["a28"]["n_call_models"] or 0
                                     for r in rows),
        "a32_tail3_total": sum(r["a32"]["tail3"] or 0 for r in ok),
        "a32_call_models_total": sum(r["a32"]["n_call_models"] or 0
                                     for r in ok),
        "a28_moved_constant_calls_total": sum(
            r["a28"]["n_moved_constant_calls"] or 0 for r in rows),
        "a32_moved_constant_calls_total": sum(
            r["a32"]["n_moved_constant_calls"] or 0 for r in ok),
        "n_norm_objf_hex_equal": sum(1 for r in ok if r["norm_objf_hex_equal"]),
    }
    return {"arm": arm, "rows": rows, "totals": totals}


def stage_tally() -> int:
    summary: dict = {"tau": TAU, "delta": DELTA, "ystate": str(YSTATE_A26)}
    out = []
    camp = RUNS / "campaign" / "A1p"
    if camp.exists():
        t = _tally_arm("A1p", A1P_STARTS, camp)
        summary["A1p"] = t
        out.append(("A1p", t["totals"]))
    a0p = RUNS / "a0p" / "A0p"
    if a0p.exists():
        t = _tally_arm("A0p", A0P_STARTS, a0p)
        summary["A0p"] = t
        out.append(("A0p", t["totals"]))
    if not out:
        print("no campaign or a0p runs found -- run those stages first")
        return 1
    (RUNS / "campaign_summary.json").write_text(json.dumps(summary, indent=2))
    for arm, tt in out:
        print(f"\n{arm}: {tt['n_ok']}/{tt['n_starts']} runs ok "
              f"(statuses {tt['statuses']})")
        print(f"  3+-pass calls   A28 {tt['a28_tail3_total']:6d} / "
              f"{tt['a28_call_models_total']}   ->   a26-spec "
              f"{tt['a32_tail3_total']:6d} / {tt['a32_call_models_total']}")
        print(f"  moved-constant  A28 {tt['a28_moved_constant_calls_total']:6d}"
              f" / {tt['a28_call_models_total']}   ->   a26-spec "
              f"{tt['a32_moved_constant_calls_total']:6d} / "
              f"{tt['a32_call_models_total']}")
        print(f"  norm_objf hex-equal to A28: {tt['n_norm_objf_hex_equal']}"
              f"/{tt['n_ok']} (bit-exactness is NOT expected across a spec "
              f"change; differences are reported, not judged, here)")
    print(f"\nsummary written to {RUNS / 'campaign_summary.json'}")
    return 0


def stage_campaign() -> int:
    if stage_preflight(quick=True) != 0:
        print(f"\n{_BLOCKED_MSG}")
        return 3
    root = RUNS / "campaign" / "A1p"
    for k in A1P_STARTS:
        run_one_a32("A1p", root / f"start{k:03d}",
                    seed=k, delta=DELTA, ystate=YSTATE_A26)
    return stage_tally()


def stage_a0p() -> int:
    if stage_preflight(quick=True) != 0:
        print(f"\n{_BLOCKED_MSG}")
        return 3
    root = RUNS / "a0p" / "A0p"
    for k in A0P_STARTS:
        run_one_a32("A0p", root / f"start{k:03d}",
                    seed=k, delta=DELTA, ystate=YSTATE_A26)
    return stage_tally()


# --------------------------------------------------------------------------
# stage: traced (which call still takes 3+ passes, by call index)
# --------------------------------------------------------------------------


def stage_traced() -> int:
    """One traced A1' start010 run under the a26 spec.

    start010 is A28's heaviest tail (858 of 11 370 calls at 3+ passes).
    The trace (A31's instrument, proven switch-neutral by its own gate)
    records every joint-test evaluation with its call and pass index, so
    this stage verifies BY CALL INDEX that any surviving 3+-pass call is
    the cold first call -- and names what its extra passes converged.
    """
    if stage_preflight(quick=True) != 0:
        print(f"\n{_BLOCKED_MSG}")
        return 3
    outdir = RUNS / "traced" / "A1p_start010"
    r = run_one_a32("A1p", outdir, seed=10, delta=DELTA,
                    ystate=YSTATE_A26, trace=True)
    tpath = outdir / "pass_trace.jsonl"
    if not tpath.exists():
        print("traced run produced no pass_trace.jsonl")
        return 1
    passes_by_call: dict[int, int] = {}
    argmax_by_call_pass: dict[tuple, dict] = {}
    with tpath.open() as fh:
        for line in fh:
            rec = json.loads(line)
            if rec.get("kind") != "outer":
                continue
            c, p = int(rec["call"]), int(rec["pass"])
            passes_by_call[c] = max(passes_by_call.get(c, 0), p)
            if p >= 3:
                argmax_by_call_pass[(c, p)] = rec.get("argmax") or {}
    calls_3plus = sorted(c for c, p in passes_by_call.items() if p >= 3)
    first_call = min(passes_by_call) if passes_by_call else None
    record = {
        "run": {"outdir": str(outdir), "rc": r["rc"]},
        "n_calls_traced": len(passes_by_call),
        "first_call_index": first_call,
        "calls_with_3plus_passes": calls_3plus,
        "n_calls_with_3plus_passes": len(calls_3plus),
        "all_3plus_are_first_call": (
            calls_3plus in ([], [first_call])
        ),
        "argmax_on_3plus_passes": {
            f"call{c}_pass{p}": {
                k2: v for k2, v in a.items()
                if k2 in ("key", "category", "scaled", "before_hex",
                          "after_hex")
            } for (c, p), a in sorted(argmax_by_call_pass.items())
        },
        "a28_reference_tail3_start010": 858,
    }
    (RUNS / "traced").mkdir(parents=True, exist_ok=True)
    (RUNS / "traced" / "traced.json").write_text(json.dumps(record, indent=2))
    print(json.dumps(record, indent=2))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("stage",
                    choices=["gate", "preflight", "campaign", "a0p",
                             "traced", "tally", "all"])
    args = ap.parse_args()
    RUNS.mkdir(parents=True, exist_ok=True)
    (RUNS / "_mplconfig").mkdir(exist_ok=True)

    if args.stage == "gate":
        return stage_gate()
    if args.stage == "preflight":
        return stage_preflight()
    if args.stage == "campaign":
        return stage_campaign()
    if args.stage == "a0p":
        return stage_a0p()
    if args.stage == "traced":
        return stage_traced()
    if args.stage == "tally":
        return stage_tally()
    # all: the gate first (it licenses everything), then the full pipeline;
    # any failure stops the chain with that stage's exit code.
    for fn in (stage_gate, lambda: stage_preflight(False), stage_campaign,
               stage_a0p, stage_traced):
        rc = fn()
        if rc != 0:
            return rc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
