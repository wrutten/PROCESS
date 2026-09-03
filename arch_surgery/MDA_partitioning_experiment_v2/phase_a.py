#!/usr/bin/env python
"""V2 Phase A — per-call MDA cost, no optimiser (EXPERIMENT_PLAN.md §3).

A0 (flat) vs A1 (feed-forward blocks) at one shared τ, N = 25 seeded
coupling-state perturbations per deck, coupling pinned on the pulsed decks,
post-solve nodes absent from the measured call.  Implemented by task A36
under the **warm-entry design** (user decision 2026-09-03): every campaign
run starts from the deck's own FLAT-converged exit state (where the
coupling components are non-zero, so a multiplicative ±δ stream reaches
them — A34 §5 measured 767/799 continuous components identically zero at a
cold entry), and the perturbation acts multiplicatively around that warm
state.  Stages (protocol §15: every published number regenerates from this
committed entry point; failure paths are reachable from it):

``preflight``
    The instrumentation ledger (unchanged from the guarded-stub version).
    Each gap refuses by task name — never a silent skip.
``campaign``
    Per deck, in order, refusing on any gate failure (§12 teeth on every
    gate):

    1. REFERENCE — A0 single eval at the cold deck point, unperturbed:
       one ``call_models`` under ``flat_state`` = full flat MDA
       convergence.  Its cost is the once-per-run **cold-start term**; its
       exact exit snapshot (``y_exit.json``) is the warm reference.
    2. ENTRY GATE (the ``--entry-state`` extension's gate) — A0 relaunched
       from its OWN unperturbed exit snapshot must audit at or below the
       reference's own exit-audit residual and must do the minimal
       'already-converged' work (1 block sweep; node calls equal to one
       audit sweep).  Teeth: a hand-perturbed snapshot must produce a
       nonzero audit and more than the minimal work.
    3. WARM EQUIVALENCE GATE (supersedes A34's cold ``pin_gate``, whose
       FAIL was localised to the cold entry, not the pin) — A1 (the
       designed block architecture's per-call structure, Phase B's B2:
       resequenced per_module + trust + post-solve + lift/pin on pulsed
       decks) launched from the reference snapshot,
       unperturbed, pinned at the reference's exact burn time (hex
       round-trip).  Criterion, pre-declared: categorically clean AND
       cross-state max residual vs the reference < τ.  Expected PASS at
       the warm entry; a FAIL stops the campaign and is the result.
    4. SEEDS 1..25 — both arms from the reference snapshot at seeded
       ±δ multiplicative perturbations (seed-paired: identical entry
       states across arms, verified bit-for-bit per seed); on pulsed
       decks A1's pin per seed = the perturbed burn-time component value
       from the same stream.
``tally``
    Per deck, from the on-disk records: per-node counts (summed and
    per-run), the weighting-invariance bracket over nodes, the unweighted
    count ratio, audit similarity (median AND p90 within F = 10, full
    distributions kept), the lift residual distribution (reported
    separately — it is the pin, not an error), the cold-start term, and
    the failure taxonomy with denominators (every seed a row).
``smoke``
    The machinery test, NOT a measurement (the phase_b.stage_smoke
    pattern): the full campaign+tally path on ``st_regression`` only,
    seeds 1..2, under ``runs/phase_a/smoke/`` — runnable while
    ``EXECUTION_APPROVED`` is False, stamped ``machinery_smoke`` in every
    record.  The real campaign stage refuses while approval is False.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import statistics
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import v2_config as cfg  # noqa: E402
import v2_runner as vr  # noqa: E402  (also puts cfg.IDF_PROBE on sys.path)

from a34_instruments import _cross_residual, load_spec_offline  # noqa: E402
from v2_eval_one import perturb_factor, restore_snapshot  # noqa: E402

PA_RUNS = cfg.RUNS / "phase_a"

#: Phase A's arms (plan §3).  Not in v2_config (which carries PHASE_B_ARMS);
#: defined here per the A36 brief rather than editing the trunk-owned config.
PHASE_A_ARMS = ("A0", "A1")

#: The lifted/pinned coupling component (plan §3; A22: all pass-≥2 movement
#: on the pulsed decks is the burn time).
PIN_COMPONENT = "times.t_plant_pulse_burn"

#: Hand-perturbation factor for the entry gate's teeth: one continuous
#: component of the snapshot multiplied by this must produce a nonzero audit
#: and more than the minimal already-converged work.
TEETH_FACTOR = 1.5


def stage_preflight() -> int:
    PA_RUNS.mkdir(parents=True, exist_ok=True)
    ledger = {}
    ready = True
    for key in ("single_mda_eval", "trust_mode"):
        led = cfg.INSTRUMENTATION[key]
        ledger[key] = dict(led)
        if not led["available"]:
            ready = False
            print(f"  {key:20s} REFUSED  not built — {led['task']}")
        else:
            print(f"  {key:20s} ready")
    for deck in cfg.DECKS:
        entries = {"ystate_a26": cfg.ystate_for(deck).exists(),
                   "writeset_a26": cfg.writeset_for(deck).exists(),
                   "postsolve": cfg.postsolve_for(deck).exists()}
        if deck in cfg.PULSED:
            led = cfg.INSTRUMENTATION["pin"]
            entries["pin"] = led["available"]
            if not led["available"]:
                print(f"  {deck:24s} pin REFUSED — {led['task']}")
        for name, ok in entries.items():
            if not ok:
                ready = False
                print(f"  {deck:24s} {name} MISSING")
        if all(entries.values()):
            print(f"  {deck:24s} artifacts ready")
    record = {"ledger": ledger, "ready": ready,
              "execution_approved": cfg.EXECUTION_APPROVED}
    (PA_RUNS / "preflight.json").write_text(json.dumps(record, indent=2))
    print(f"\nphase A preflight: {'READY' if ready else 'NOT READY'}")
    return 0 if ready else 3


# --------------------------------------------------------------------------
# arm environments (A36 brief; composed here, not borrowed from Phase B's
# env_for, whose arm names the orchestrator owns on the trunk)
# --------------------------------------------------------------------------


def env_for_phase_a(deck: str, arm: str, *, pin_hex: str | None = None) -> dict:
    """The environment one Phase A arm runs under, built from nothing.

    Every architecture switch is cleared first (v2_runner's discipline: an
    inherited one would change what is measured without saying so).

    A0 = ``flat_state`` + a26 artifacts, NO post-solve (the flat
    architecture as shipped keeps those nodes in its loop — plan §3).
    A1 = the designed block architecture's per-call structure (Phase B's
    B2): resequenced ``per_module`` + trust + post-solve exclusion +
    (pulsed) lift and pin.  Pin chains run on the
    ORIGINAL deck (A34 decision (d): the lifted deck names ixc 178 and is
    refused — two owners).
    """
    env = dict(os.environ)
    env["PYTHONPATH"] = str(cfg.TREE)
    env["MPLCONFIGDIR"] = str(cfg.RUNS / "_mplconfig")
    for k in vr._ALL_ARCH_VARS:
        env.pop(k, None)
    env["PROCESS_ARCH_TAU"] = repr(cfg.TAU)
    env["PROCESS_ARCH_YSTATE"] = str(cfg.ystate_for(deck))
    env["PROCESS_ARCH_WRITESET"] = str(cfg.writeset_for(deck))
    if arm == "A0":
        env["PROCESS_ARCH_MODULE_SOLVE"] = "flat_state"
        return env
    if arm == "A1":
        env["PROCESS_ARCH_SEQUENCE"] = "build_after_physics"
        env["PROCESS_ARCH_MODULE_SOLVE"] = "per_module"
        env["PROCESS_ARCH_OUTER"] = "trust"
        env["PROCESS_ARCH_HOIST"] = (
            "feedforward_lifted" if deck in cfg.PULSED else "feedforward"
        )
        # Phase A's A1 runs the ORIGINAL deck (the pin owns the burn time;
        # A34 refuses pin + lifted deck as two owners), so its active
        # constraint set has no icc 93 and the post-solve artifact must be
        # the nolift derivation — same node set, stamped for the base set
        # (the lifted-stamp artifact is correctly refused at runtime; that
        # refusal fired on the first launch attempt, 2026-09-03 evening).
        if deck in cfg.PULSED:
            env["PROCESS_ARCH_POST_SOLVE"] = str(
                cfg.DATA / f"postsolve_nolift_{deck}.json")
        else:
            env["PROCESS_ARCH_POST_SOLVE"] = str(cfg.postsolve_for(deck))
        if deck in cfg.PULSED:
            env["PROCESS_ARCH_LIFT"] = "burn_time"
            if pin_hex is None:
                raise SystemExit(
                    f"A1 on pulsed deck {deck} needs a pin value: the pin "
                    f"replaces the optimiser as the lifted variable's owner "
                    f"(A34); running unpinned would measure a different arm."
                )
            env["PROCESS_ARCH_PIN_BURN_TIME"] = pin_hex
        return env
    raise SystemExit(f"unknown Phase A arm {arm!r}; known: {PHASE_A_ARMS}")


# --------------------------------------------------------------------------
# one isolated single-eval run (fresh subprocess, exact tree asserted)
# --------------------------------------------------------------------------


def run_eval_job(
    deck: str,
    arm: str,
    outdir: Path,
    *,
    entry_state: Path | None = None,
    delta: float | None = None,
    seed: int = 0,
    pin_hex: str | None = None,
    resume: bool = False,
    machinery_smoke: bool = False,
    timeout: int = 3600,
) -> dict:
    """One single-MDA-eval run through ``v2_eval_one.py``.  Counts are exact
    and concurrency-invariant; wall clock is progress information only."""
    mpath0 = outdir / "metrics.json"
    if resume and mpath0.exists():
        try:
            prev = json.loads(mpath0.read_text())
        except Exception:
            prev = {}
        if (prev.get("status") == "ok" and prev.get("v2_arm") == arm
                and prev.get("v2_deck") == deck
                and prev.get("v2_seed") == seed
                and prev.get("v2_delta") == delta
                and prev.get("v2_pin_hex") == pin_hex):
            print(f"  {deck:24s} {arm:3s} seed={seed:<3d} resumed "
                  f"(complete record kept)", flush=True)
            return {"deck": deck, "arm": arm, "seed": seed, "rc": 0,
                    "outdir": str(outdir), "resumed": True}
    if outdir.exists():
        shutil.rmtree(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable, str(cfg.IDF_PROBE / "v2_eval_one.py"),
        "--scenario", deck,
        "--input", str(cfg.IDF_PROBE / "scenarios" / f"{deck}.IN.DAT"),
        "--outdir", str(outdir),
        "--expect-tree", str(cfg.TREE),
        "--perturb-spec", str(cfg.ystate_for(deck)),
        "--exit-audit", str(cfg.ystate_for(deck)),
        "--seed", str(seed),
        "--node-census",
    ]
    if delta is not None:
        cmd += ["--delta", repr(delta)]
    if entry_state is not None:
        cmd += ["--entry-state", str(entry_state)]
    env = env_for_phase_a(deck, arm, pin_hex=pin_hex)
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
            "scenario": deck,
            "status": "timeout" if rc == 124 else "no_metrics",
            "returncode": rc, "delta": delta, "seed": seed,
        }, indent=2))
    rec = json.loads(mpath.read_text())
    rec["v2_phase"] = "A"
    rec["v2_arm"] = arm
    rec["v2_deck"] = deck
    rec["v2_seed"] = seed
    rec["v2_delta"] = delta
    rec["v2_tau"] = cfg.TAU
    rec["v2_pin_hex"] = pin_hex
    rec["v2_entry_state"] = str(entry_state) if entry_state else None
    rec["v2_machinery_smoke"] = machinery_smoke
    mpath.write_text(json.dumps(rec, indent=2))
    wall = time.perf_counter() - t0
    print(f"  {deck:24s} {arm:3s} seed={seed:<3d} rc={rc} "
          f"status={rec.get('status')} {wall:6.1f}s "
          f"(wall clock is progress information, not a measurement)",
          flush=True)
    return {"deck": deck, "arm": arm, "seed": seed, "rc": rc,
            "outdir": str(outdir), "status": rec.get("status")}


def run_pool(jobs: list[dict]) -> list[dict]:
    """W concurrent runs (v2_runner's pool shape; memory-bound, plan §2).
    Jobs are never retried: a crash is a taxonomy row."""
    results = []
    with ThreadPoolExecutor(max_workers=cfg.WORKERS) as pool:
        futures = [pool.submit(run_eval_job, **j) for j in jobs]
        for f in futures:
            results.append(f.result())
    return results


def _metrics(outdir: Path) -> dict:
    p = Path(outdir) / "metrics.json"
    return json.loads(p.read_text()) if p.exists() else {"status": "missing"}


def _stamp(m: dict) -> dict:
    """The clean-tree stamp a gate record must carry (protocol 15)."""
    return {"tree_git_head": m.get("tree_git_head"),
            "tree_git_dirty": m.get("tree_git_dirty")}


# --------------------------------------------------------------------------
# gate 1: the --entry-state extension gate (A36 deliverable 1, §12 teeth)
# --------------------------------------------------------------------------


def _doctor_snapshot(ref_snap: dict, deck: str, owned: list | None,
                     prefer: str | None, out: Path) -> dict:
    """A hand-perturbed copy of the reference snapshot, for the teeth.

    One CONTINUOUS float scalar component, non-zero, and NOT owned by the
    design vector (the sweep-head injection would silently reset it and the
    teeth would test nothing).  Preference: the reference audit's own argmax
    component — guaranteed live in the sweep.  Factor ``TEETH_FACTOR``.
    """
    art = json.loads(cfg.ystate_for(deck).read_text())
    cats = {c["key"]: c["category"] for c in art["components"]}
    owned_set = set(owned or ())
    st = ref_snap["state"]

    def eligible(name: str) -> bool:
        rec = st.get(name)
        return bool(
            rec and rec.get("k") == "f"
            and float.fromhex(rec["hex"]) != 0.0
            and cats.get(name) == "continuous"
            and name not in owned_set
        )

    comp = prefer if (prefer and eligible(prefer)) else next(
        (nm for nm in st if eligible(nm)), None
    )
    if comp is None:
        raise RuntimeError(
            "no eligible component for the entry-gate teeth: the snapshot "
            "holds no non-zero continuous float scalar outside the design "
            "vector — that is itself a finding, report it"
        )
    doctored = json.loads(json.dumps(ref_snap))
    before = float.fromhex(doctored["state"][comp]["hex"])
    after = before * TEETH_FACTOR
    doctored["state"][comp]["hex"] = after.hex()
    out.write_text(json.dumps(doctored))
    return {"component": comp, "factor": TEETH_FACTOR,
            "before_hex": before.hex(), "after_hex": after.hex()}


def entry_gate(deck: str, droot: Path, ref: dict,
               machinery_smoke: bool) -> dict:
    """A0 from its OWN unperturbed exit snapshot: the fixed point re-entered.

    Thresholds are DECLARED (printed and recorded) before the gate run:
      (i)   audit residual_max ≤ the reference run's own exit-audit
            residual (the state is already the fixed point; one call under
            flat_state finds nothing to move);
      (ii)  minimal already-converged cost: block_sweeps == 1 and
            node_calls_single_eval == the reference audit's node calls
            (one full sweep of the same in-loop node set);
      (iii) the entry state reproduces the snapshot exactly (in-process
            readback bit-exact, and y_entry.json == the reference's
            y_exit.json bit-for-bit).
    Teeth: a hand-perturbed snapshot must produce a NONZERO audit and more
    than the minimal work.
    """
    root = droot / "entry_gate"
    root.mkdir(parents=True, exist_ok=True)
    ref_m = ref["metrics"]
    ref_audit = ref_m.get("exit_audit") or {}
    declared = {
        "audit_residual_max_le_hex": ref_audit.get("residual_max_hex"),
        "audit_residual_max_le": ref_audit.get("residual_max"),
        "block_sweeps_eq": 1,
        "node_calls_single_eval_eq": ref_audit.get("audit_node_calls"),
        "declared": "before the gate run was launched (A36 brief, §12)",
    }
    print(f"  entry gate thresholds (declared before running): audit ≤ "
          f"{declared['audit_residual_max_le_hex']}, block_sweeps == 1, "
          f"node_calls == {declared['node_calls_single_eval_eq']}",
          flush=True)

    snap_path = Path(ref["outdir"]) / "y_exit.json"
    warm = run_eval_job(deck, "A0", root / "A0_warm",
                        entry_state=snap_path, seed=0,
                        machinery_smoke=machinery_smoke)
    wm = _metrics(warm["outdir"])
    w_audit = wm.get("exit_audit") or {}
    w_entry = wm.get("entry_state") or {}

    # entry exactness, belt and braces: the recorded entry state must BE the
    # snapshot, bit for bit (file-level, over every component).
    ref_state = json.loads(snap_path.read_text())["state"]
    ent_path = Path(warm["outdir"]) / "y_entry.json"
    entry_identical = None
    n_entry_mismatch = None
    if ent_path.exists():
        ent_state = json.loads(ent_path.read_text())["state"]
        n_entry_mismatch = sum(
            1 for nm in ref_state if ent_state.get(nm) != ref_state[nm]
        ) + sum(1 for nm in ent_state if nm not in ref_state)
        entry_identical = n_entry_mismatch == 0

    checks = {
        "run_ok": warm["rc"] == 0 and wm.get("status") == "ok",
        "entry_readback_bitexact": w_entry.get("readback_bitexact") is True,
        "entry_no_skipped_components": w_entry.get("n_skipped_repr") == 0,
        "entry_reproduces_snapshot_bitexact": entry_identical is True,
        "audit_at_or_below_reference": (
            w_audit.get("residual_max") is not None
            and ref_audit.get("residual_max") is not None
            and w_audit["residual_max"] <= ref_audit["residual_max"]
        ),
        "block_sweeps_minimal": (
            (wm.get("module_solve_stats") or {}).get("block_sweeps") == 1
        ),
        "node_calls_minimal": (
            wm.get("node_calls_single_eval")
            == declared["node_calls_single_eval_eq"]
        ),
    }

    # teeth: the doctored snapshot
    doc_path = root / "doctored_y_exit.json"
    ref_snap = json.loads(snap_path.read_text())
    doctor = _doctor_snapshot(
        ref_snap, deck, ref_m.get("spec_keys_owned_by_x"),
        (ref_audit.get("brief") or {}).get("argmax"), doc_path,
    )
    teeth_run = run_eval_job(deck, "A0", root / "A0_teeth",
                             entry_state=doc_path, seed=0,
                             machinery_smoke=machinery_smoke)
    tm = _metrics(teeth_run["outdir"])
    t_audit = tm.get("exit_audit") or {}
    teeth = {
        "hand_perturbation": doctor,
        "run_ok": teeth_run["rc"] == 0 and tm.get("status") == "ok",
        "audit_nonzero": bool(
            t_audit.get("residual_max") is not None
            and t_audit["residual_max"] > 0.0
        ),
        "audit_residual_max_hex": t_audit.get("residual_max_hex"),
        "more_than_minimal_work": (
            ((tm.get("module_solve_stats") or {}).get("block_sweeps") or 0)
            > 1
        ),
        "block_sweeps": (tm.get("module_solve_stats") or {}).get(
            "block_sweeps"
        ),
        "audit_above_declared_threshold_reported_unbound": (
            t_audit.get("residual_max") is not None
            and ref_audit.get("residual_max") is not None
            and t_audit["residual_max"] > ref_audit["residual_max"]
        ),
    }
    # EITHER signal proves the doctored snapshot was loaded and detected:
    # nonzero post-eval audit, OR more-than-minimal solver work.  On a deck
    # whose flat solve terminates at the exact fixed point (audit 0.0 —
    # low_aspect_ratio_DEMO, per A28's tables and attempt 2 on 2026-09-03),
    # the doctored state is fully re-converged and the audit tooth CANNOT
    # fire; the work tooth (3 sweeps vs the minimal 1) is the binding one.
    # A broken --entry-state loader that silently ignored the snapshot
    # would leave the doctored run identical to the clean one — zero audit
    # AND minimal work — so the OR still fails and §12's shown-able-to-fail
    # property is preserved.  (The AND conjunction was attempt 2's stop.)
    teeth["all_tripped"] = bool(
        teeth["run_ok"]
        and (teeth["audit_nonzero"] or teeth["more_than_minimal_work"])
    )

    record = {
        "gate": (
            "A36 --entry-state extension gate: A0 from its OWN unperturbed "
            "exit snapshot is already the fixed point — one call under "
            "flat_state finds nothing to move (§12, teeth)"
        ),
        "reference": {"outdir": ref["outdir"],
                      "audit_residual_max_hex": ref_audit.get(
                          "residual_max_hex"),
                      "audit_node_calls": ref_audit.get("audit_node_calls"),
                      **_stamp(ref_m)},
        "declared_thresholds": declared,
        "warm_run": {"outdir": warm["outdir"], "rc": warm["rc"],
                     "status": wm.get("status"),
                     "node_calls_single_eval": wm.get(
                         "node_calls_single_eval"),
                     "block_sweeps": (wm.get("module_solve_stats") or {}
                                      ).get("block_sweeps"),
                     "audit_residual_max_hex": w_audit.get(
                         "residual_max_hex"),
                     "n_entry_mismatch": n_entry_mismatch,
                     **_stamp(wm)},
        "checks": checks,
        "teeth": teeth,
        "machinery_smoke": machinery_smoke,
        "verdict": ("PASS" if (all(checks.values()) and teeth["all_tripped"])
                    else "FAIL"),
    }
    (root / "gate.json").write_text(json.dumps(record, indent=2))
    print(f"  entry gate {deck}: {record['verdict']} "
          f"(audit {w_audit.get('residual_max_hex')} vs threshold "
          f"{declared['audit_residual_max_le_hex']}; teeth audit "
          f"{t_audit.get('residual_max_hex')})", flush=True)
    return record


# --------------------------------------------------------------------------
# gate 2: the warm equivalence gate (supersedes A34's cold pin_gate)
# --------------------------------------------------------------------------


def _warm_teeth(spec, y_ref: list, y_a1: list) -> dict:
    """Comparator perturbations that must trip the criterion (the A34
    pin_gate teeth, unchanged in shape)."""
    trials = {}
    ys_cont = next(
        i for i in range(len(spec.keys))
        if spec.category[i] == "continuous" and isinstance(y_ref[i], float)
    )
    y_pert = list(y_ref)
    y_pert[ys_cont] = y_pert[ys_cont] + 3.0 * cfg.TAU * spec.scale[ys_cont]
    c1 = _cross_residual(spec, y_pert, y_a1, cfg.TAU)
    trials["continuous_bumped_3tau_scale"] = not (
        c1["max"] < cfg.TAU and c1["categorically_clean"]
    )
    ys_disc = next(
        (i for i in range(len(spec.keys)) if spec.category[i] == "discrete"),
        None,
    )
    if ys_disc is not None:
        y_pert = list(y_ref)
        v = y_pert[ys_disc]
        y_pert[ys_disc] = (not v) if isinstance(v, bool) else (
            (v + 1) if isinstance(v, int) else str(v) + "_x"
        )
        c2 = _cross_residual(spec, y_pert, y_a1, cfg.TAU)
        trials["discrete_flipped"] = not (
            c2["max"] < cfg.TAU and c2["categorically_clean"]
        )
    return {
        "n_perturbations": len(trials),
        "n_tripped": sum(bool(v) for v in trials.values()),
        "all_tripped": all(trials.values()),
        "per_perturbation": trials,
    }


def warm_gate(deck: str, droot: Path, ref: dict,
              machinery_smoke: bool) -> dict:
    """A1 from the reference snapshot, unperturbed, pinned at the
    reference's exact burn time (pulsed decks): must land on the reference
    fixed point.  Criterion, pre-declared (A34 decision (e), re-bound here
    for the warm entry): categorically clean AND cross-state max residual
    vs the reference < τ.  Expected PASS at the warm entry — a FAIL stops
    the campaign and IS the result."""
    root = droot / "warm_gate"
    root.mkdir(parents=True, exist_ok=True)
    ref_m = ref["metrics"]
    snap_path = Path(ref["outdir"]) / "y_exit.json"

    pin_hex = None
    if deck in cfg.PULSED:
        pin_hex = ref_m.get("t_plant_pulse_burn_hex")
        snap_burn = json.loads(snap_path.read_text())["state"].get(
            PIN_COMPONENT, {}).get("hex")
        if pin_hex is None or snap_burn != pin_hex:
            record = {
                "gate": "A36 warm equivalence gate",
                "verdict": "FAIL",
                "failed_at": (
                    f"pin value inconsistency: reference metrics say "
                    f"{pin_hex}, its snapshot says {snap_burn} for "
                    f"{PIN_COMPONENT} — configuration error, not a result"
                ),
            }
            (root / "gate.json").write_text(json.dumps(record, indent=2))
            return record

    print(f"  warm gate criterion (pre-declared): categorically clean AND "
          f"cross-state max residual vs the reference < tau = {cfg.TAU:g}"
          + (f"; pin = {pin_hex}" if pin_hex else ""), flush=True)

    a1 = run_eval_job(deck, "A1", root / "A1_warm",
                      entry_state=snap_path, seed=0, pin_hex=pin_hex,
                      machinery_smoke=machinery_smoke)
    m1 = _metrics(a1["outdir"])
    record: dict = {
        "gate": (
            "A36 warm equivalence gate (plan §3, warm-entry design; "
            "supersedes A34's cold pin_gate, whose FAIL was localised to "
            "the cold entry): one A1 run from the reference snapshot, "
            "pinned at the reference's converged burn time, must reproduce "
            "the reference fixed point within the audit's resolution"
        ),
        "criterion_bound": (
            "categorically clean AND cross_max < tau, under the a26 audit "
            "ruler (pre-declared; A34 decision (e))"
        ),
        "tau": cfg.TAU,
        "reference": {"outdir": ref["outdir"],
                      "t_plant_pulse_burn_hex": ref_m.get(
                          "t_plant_pulse_burn_hex"),
                      **_stamp(ref_m)},
        "a1_run": {
            "outdir": a1["outdir"], "rc": a1["rc"],
            "status": m1.get("status"),
            "node_calls_single_eval": m1.get("node_calls_single_eval"),
            "outer_passes": (m1.get("module_solve_stats") or {}).get(
                "outer_passes"),
            "block_sweeps": (m1.get("module_solve_stats") or {}).get(
                "block_sweeps"),
            "own_audit_residual_max_hex": (m1.get("exit_audit") or {}).get(
                "residual_max_hex"),
            "pin_intact_at_exit": m1.get("pin_intact_at_exit"),
            "arch_pin_burn_time_hex": m1.get("arch_pin_burn_time_hex"),
            "lift_residual": m1.get("lift_residual"),
            **_stamp(m1),
        },
        "machinery_smoke": machinery_smoke,
    }
    if a1["rc"] != 0 or m1.get("status") != "ok":
        record["verdict"] = "FAIL"
        record["failed_at"] = "the A1 chain did not complete"
        (root / "gate.json").write_text(json.dumps(record, indent=2))
        print(f"  warm gate {deck}: FAIL (A1 did not complete)", flush=True)
        return record

    spec = load_spec_offline(cfg.ystate_for(deck))
    y_ref = restore_snapshot(spec, json.loads(snap_path.read_text()))
    y_a1 = restore_snapshot(
        spec, json.loads((Path(a1["outdir"]) / "y_exit.json").read_text())
    )
    cross = _cross_residual(spec, y_ref, y_a1, cfg.TAU)
    teeth = _warm_teeth(spec, y_ref, y_a1)
    pin_bit_identical = None
    if deck in cfg.PULSED:
        idx = {spec.name(i): i for i in range(len(spec.keys))}
        li = idx.get(PIN_COMPONENT)
        if li is not None:
            pin_bit_identical = float(y_ref[li]) == float(y_a1[li])
    below_tau = cross["max"] < cfg.TAU
    record.update({
        "cross_state_residual": cross,
        "pin_component_bit_identical": {
            "component": PIN_COMPONENT,
            "expected": "True by construction on pulsed decks (hex pin)",
            "observed": pin_bit_identical,
        },
        "teeth": teeth,
        "verdict": (
            "PASS"
            if (below_tau and cross["categorically_clean"]
                and teeth["all_tripped"]
                and (deck not in cfg.PULSED
                     or m1.get("pin_intact_at_exit") is True))
            else "FAIL"
        ),
    })
    (root / "gate.json").write_text(json.dumps(record, indent=2))
    print(f"  warm gate {deck}: {record['verdict']} (cross max "
          f"{cross['max_hex']}, {cross['n_above_tau']} above tau, "
          f"clean={cross['categorically_clean']})", flush=True)
    return record


# --------------------------------------------------------------------------
# the campaign
# --------------------------------------------------------------------------


def pairing_check(droot: Path, seeds) -> dict:
    """Seed pairing, shown not assumed: the two arms' recorded entry states
    (y_entry.json, full coupling state as exact hex) must be bit-identical
    per seed — the A34 799/799 check transposed to the entry state, run for
    EVERY seed (the brief's once-per-deck minimum, exceeded cheaply)."""
    detail = {}
    n_id = 0
    compared = 0
    for k in seeds:
        pa = droot / "A0" / f"start{k:03d}" / "y_entry.json"
        pb = droot / "A1" / f"start{k:03d}" / "y_entry.json"
        if not (pa.exists() and pb.exists()):
            detail[str(k)] = {"compared": False, "why": "missing y_entry"}
            continue
        sa = json.loads(pa.read_text())["state"]
        sb = json.loads(pb.read_text())["state"]
        ident = sum(1 for nm in sa if sb.get(nm) == sa[nm])
        same = ident == len(sa) and len(sb) == len(sa)
        compared += 1
        n_id += bool(same)
        detail[str(k)] = {"compared": True, "n_rows": len(sa),
                          "n_bit_identical": ident, "identical": same}
    return {
        "what": "cross-arm bit-identity of the full recorded entry state",
        "n_seeds_compared": compared,
        "n_seeds_bit_identical": n_id,
        "all_identical": compared > 0 and n_id == compared,
        "per_seed": detail,
    }


def deck_campaign(deck: str, droot: Path, seeds,
                  machinery_smoke: bool) -> tuple[dict, bool]:
    """Reference, both gates, then the seeded runs.  Returns (record, ok);
    ok False stops the campaign (a failed gate is a result)."""
    droot.mkdir(parents=True, exist_ok=True)
    rec: dict = {"deck": deck}

    # sanity on the pulsed decks' pin component, before anything runs
    if deck in cfg.PULSED:
        art = json.loads(cfg.ystate_for(deck).read_text())
        cat = {c["key"]: c["category"] for c in art["components"]}.get(
            PIN_COMPONENT)
        if cat != "continuous":
            rec["refused"] = (
                f"{PIN_COMPONENT} is {cat!r} (not continuous) in "
                f"{cfg.ystate_for(deck).name}: the seed-paired pin cannot "
                f"be sourced from the perturbation stream"
            )
            return rec, False

    # 1. the reference: A0, cold deck point, unperturbed
    print(f"\n{deck}: reference (A0 cold deck point, unperturbed)",
          flush=True)
    ref_run = run_eval_job(deck, "A0", droot / "reference", seed=0,
                           machinery_smoke=machinery_smoke)
    ref_m = _metrics(ref_run["outdir"])
    ref = {"outdir": ref_run["outdir"], "metrics": ref_m}
    rec["reference"] = {
        "outdir": ref_run["outdir"], "rc": ref_run["rc"],
        "status": ref_m.get("status"),
        "cold_start_node_calls": ref_m.get("node_calls_single_eval"),
        "cold_start_sweeps": ref_m.get("n_model_calls_sweeps"),
        "audit_residual_max_hex": (ref_m.get("exit_audit") or {}).get(
            "residual_max_hex"),
        "audit_node_calls": (ref_m.get("exit_audit") or {}).get(
            "audit_node_calls"),
        "t_plant_pulse_burn_hex": ref_m.get("t_plant_pulse_burn_hex"),
        **_stamp(ref_m),
    }
    if ref_run["rc"] != 0 or ref_m.get("status") != "ok":
        rec["refused"] = ("the A0 reference did not converge at the deck "
                          "point: no warm snapshot exists — that failure "
                          "is a result")
        return rec, False
    snap_path = Path(ref_run["outdir"]) / "y_exit.json"
    if not snap_path.exists():
        rec["refused"] = "reference wrote no y_exit.json"
        return rec, False

    # 2. the extension gate
    rec["entry_gate"] = entry_gate(deck, droot, ref, machinery_smoke)
    if rec["entry_gate"]["verdict"] != "PASS":
        rec["refused"] = ("entry gate FAILED — the --entry-state extension "
                          "is not trusted; nothing runs on it")
        return rec, False

    # 3. the warm equivalence gate
    rec["warm_gate"] = warm_gate(deck, droot, ref, machinery_smoke)
    if rec["warm_gate"]["verdict"] != "PASS":
        rec["refused"] = ("warm equivalence gate FAILED — that failure is "
                          "the result (plan §3); the campaign stops here")
        return rec, False

    # 4. the seeded campaign, both arms, seed-paired
    ref_burn_hex = ref_m.get("t_plant_pulse_burn_hex")
    jobs = []
    pins: dict = {}
    for k in seeds:
        pin_hex = None
        if deck in cfg.PULSED:
            base = float.fromhex(ref_burn_hex)
            pin_hex = (
                base * perturb_factor(k, PIN_COMPONENT, cfg.DELTA)
            ).hex()
            pins[str(k)] = pin_hex
        jobs.append(dict(deck=deck, arm="A0",
                         outdir=droot / "A0" / f"start{k:03d}",
                         entry_state=snap_path, delta=cfg.DELTA, seed=k,
                         resume=True, machinery_smoke=machinery_smoke))
        jobs.append(dict(deck=deck, arm="A1",
                         outdir=droot / "A1" / f"start{k:03d}",
                         entry_state=snap_path, delta=cfg.DELTA, seed=k,
                         pin_hex=pin_hex, resume=True,
                         machinery_smoke=machinery_smoke))
    print(f"{deck}: campaign — {len(jobs)} runs "
          f"({len(list(seeds))} seeds x 2 arms), {cfg.WORKERS} workers",
          flush=True)
    results = run_pool(jobs)
    rec["seed_pins_hex"] = pins or None
    rec["runs"] = {
        f"{r['arm']}/start{r['seed']:03d}": {
            "rc": r["rc"], "status": r.get("status"),
        }
        for r in results
    }

    # 5. the pairing check
    rec["pairing"] = pairing_check(droot, seeds)
    (droot / "pairing.json").write_text(json.dumps(rec["pairing"], indent=2))
    if not rec["pairing"]["all_identical"]:
        rec["pairing_failure"] = (
            "the two arms' entry states are NOT bit-identical on every "
            "compared seed — the seed-paired design is broken for this "
            "deck; reported as a failure, not papered over"
        )
        return rec, False
    print(f"{deck}: pairing {rec['pairing']['n_seeds_bit_identical']}/"
          f"{rec['pairing']['n_seeds_compared']} seeds bit-identical "
          f"across arms", flush=True)
    return rec, True


def _campaign(root: Path, decks, seeds, machinery_smoke: bool) -> int:
    if stage_preflight() != 0:
        print("\nREFUSED: Phase A instrumentation missing — the ledger "
              "above names the task each gap belongs to.")
        return 3
    root.mkdir(parents=True, exist_ok=True)
    (cfg.RUNS / "_mplconfig").mkdir(parents=True, exist_ok=True)
    record: dict = {
        "phase": "A", "machinery_smoke": machinery_smoke,
        "design": "warm-entry (user decision 2026-09-03; task A36)",
        "tau": cfg.TAU, "delta": cfg.DELTA,
        "arms": list(PHASE_A_ARMS), "decks": list(decks),
        "seeds": list(seeds), "per_deck": {},
    }
    for deck in decks:
        drec, ok = deck_campaign(deck, root / deck, seeds, machinery_smoke)
        record["per_deck"][deck] = drec
        (root / "campaign.json").write_text(json.dumps(record, indent=2))
        if not ok:
            record["stopped_at"] = deck
            (root / "campaign.json").write_text(
                json.dumps(record, indent=2))
            print(f"\nphase A campaign STOPPED at {deck}: "
                  f"{drec.get('refused') or drec.get('pairing_failure')}")
            return 1
    (root / "campaign.json").write_text(json.dumps(record, indent=2))
    print(f"\nphase A campaign complete: {len(record['per_deck'])} decks; "
          f"records under {root}")
    return 0


def stage_campaign() -> int:
    if not cfg.EXECUTION_APPROVED:
        print("REFUSED: execution not approved "
              "(v2_config.EXECUTION_APPROVED).  Run 'smoke' for the "
              "machinery test.")
        return 3
    return _campaign(PA_RUNS / "campaign", cfg.DECKS,
                     tuple(range(1, cfg.N_STARTS + 1)),
                     machinery_smoke=False)


# --------------------------------------------------------------------------
# the tally
# --------------------------------------------------------------------------


def _p90(sorted_vals: list) -> float:
    """Nearest-rank p90 (declared: ceil(0.9 n), 1-indexed)."""
    n = len(sorted_vals)
    return sorted_vals[max(0, math.ceil(0.9 * n) - 1)]


def _similar(a: float | None, b: float | None, f: float):
    """The F-factor similarity verdict with the plan's zero clause."""
    if a is None or b is None:
        return None, "a distribution is empty"
    if a == 0 and b == 0:
        return True, "both zero: trivially similar (plan App. B item 2)"
    if a == 0 or b == 0:
        return False, "one arm zero, the other not: ratio unbounded"
    r = max(a, b) / min(a, b)
    return bool(r <= f), f"ratio {r:.4g} vs F = {f:g}"


def _row(m: dict) -> dict:
    stats = m.get("module_solve_stats") or {}
    audit = m.get("exit_audit") or {}
    return {
        "status": m.get("status"),
        "node_calls_single_eval": m.get("node_calls_single_eval"),
        "sweeps": m.get("n_model_calls_sweeps"),
        "block_sweeps": stats.get("block_sweeps"),
        "outer_passes": stats.get("outer_passes"),
        "audit_residual_max": audit.get("residual_max"),
        "audit_residual_max_hex": audit.get("residual_max_hex"),
        "node_census": m.get("node_census"),
        "lift_residual": m.get("lift_residual"),
        "pin_intact_at_exit": m.get("pin_intact_at_exit"),
        "objf_hex": (m.get("exact") or {}).get("objf"),
        "tree_git_head": m.get("tree_git_head"),
        "tree_git_dirty": m.get("tree_git_dirty"),
    }


def _census_total(row: dict) -> dict:
    nc = row.get("node_census") or {}
    out = dict(nc.get("counted") or {})
    for k, v in (nc.get("flat_tail") or {}).items():
        out[k] = out.get(k, 0) + v
    return out


def _tally(root: Path, out_path: Path) -> int:
    campf = root / "campaign.json"
    if not campf.exists():
        print("no Phase A campaign records — the campaign has not run")
        return 1
    camp = json.loads(campf.read_text())
    seeds = camp["seeds"]
    summary: dict = {
        "phase": "A",
        "machinery_smoke": camp.get("machinery_smoke"),
        "tau": camp["tau"], "delta": camp["delta"],
        "similarity_factor_F": cfg.SIMILARITY_FACTOR_F,
        "n_seeds_requested": len(seeds),
        "quantile_definitions": {
            "median": "statistics.median (even n: mean of the two central "
                      "order statistics)",
            "p90": "nearest-rank, element ceil(0.9 n) of the sorted list",
        },
        "per_deck": {},
    }
    lines = []
    for deck in camp["decks"]:
        droot = root / deck
        drec = camp["per_deck"].get(deck) or {}
        d: dict = {"gates": {
            "entry_gate": (drec.get("entry_gate") or {}).get("verdict"),
            "warm_gate": (drec.get("warm_gate") or {}).get("verdict"),
        }, "cold_start_term": {
            "node_calls": (drec.get("reference") or {}).get(
                "cold_start_node_calls"),
            "sweeps": (drec.get("reference") or {}).get("cold_start_sweeps"),
            "what": ("the once-per-run cost of the full flat MDA "
                     "convergence at the cold deck point (A0 reference); "
                     "holds for THIS deck's cold entry only"),
        }, "pairing": {
            k: v for k, v in (drec.get("pairing") or {}).items()
            if k != "per_seed"
        }}
        if drec.get("refused") or drec.get("pairing_failure"):
            d["stopped"] = drec.get("refused") or drec.get("pairing_failure")
        rows: dict = {}
        for arm in PHASE_A_ARMS:
            rows[arm] = {}
            for k in seeds:
                p = droot / arm / f"start{k:03d}" / "metrics.json"
                rows[arm][str(k)] = (
                    _row(json.loads(p.read_text())) if p.exists()
                    else {"status": "missing"}
                )
        d["per_run"] = rows

        # failure taxonomy: every requested seed a row, denominators named
        taxonomy = {arm: {} for arm in PHASE_A_ARMS}
        for arm in PHASE_A_ARMS:
            for k in seeds:
                st = str(rows[arm][str(k)].get("status"))
                taxonomy[arm][st] = taxonomy[arm].get(st, 0) + 1
        d["failure_taxonomy"] = {
            "denominator_per_arm": len(seeds),
            "by_arm": taxonomy,
            "per_seed": {
                str(k): {arm: rows[arm][str(k)].get("status")
                         for arm in PHASE_A_ARMS}
                for k in seeds
            },
        }

        paired_ok = [
            k for k in seeds
            if all(rows[a][str(k)].get("status") == "ok"
                   for a in PHASE_A_ARMS)
        ]
        d["n_paired_ok"] = len(paired_ok)
        d["paired_ok_seeds"] = paired_ok

        # per-node counts (summed over the identical-success set), the
        # weighting-invariance bracket, and the unweighted ratio
        sums = {arm: {} for arm in PHASE_A_ARMS}
        totals = {arm: 0 for arm in PHASE_A_ARMS}
        for arm in PHASE_A_ARMS:
            for k in paired_ok:
                r = rows[arm][str(k)]
                totals[arm] += r.get("node_calls_single_eval") or 0
                for nm, v in _census_total(r).items():
                    sums[arm][nm] = sums[arm].get(nm, 0) + v
        per_node = {}
        ratios = []
        for nm in sorted(set(sums["A0"]) | set(sums["A1"])):
            n0 = sums["A0"].get(nm, 0)
            n1 = sums["A1"].get(nm, 0)
            ratio = (n1 / n0) if n0 else (math.inf if n1 else None)
            per_node[nm] = {"A0": n0, "A1": n1, "ratio_A1_over_A0": ratio}
            if ratio is not None:
                ratios.append(ratio)
        d["per_node_counts_summed_paired_ok"] = per_node
        d["weighting_invariance_bracket"] = (
            [min(ratios), max(ratios)] if ratios else None
        )
        d["unweighted_count_ratio_A1_over_A0"] = (
            totals["A1"] / totals["A0"] if totals["A0"] else None
        )
        d["node_calls_total_paired_ok"] = totals

        # audit similarity (median AND p90 within F), lift residual apart
        d["audit_similarity"] = {}
        dists = {}
        for arm in PHASE_A_ARMS:
            vals = sorted(
                r.get("audit_residual_max")
                for r in (rows[arm][str(k)] for k in seeds)
                if r.get("status") == "ok"
                and r.get("audit_residual_max") is not None
            )
            dists[arm] = vals
        d["audit_similarity"]["distributions"] = {
            arm: {
                "n": len(vals),
                "values": vals,
                "values_hex": [float(v).hex() for v in vals],
                "median": statistics.median(vals) if vals else None,
                "p90": _p90(vals) if vals else None,
            }
            for arm, vals in dists.items()
        }
        med_ok, med_why = _similar(
            d["audit_similarity"]["distributions"]["A0"]["median"],
            d["audit_similarity"]["distributions"]["A1"]["median"],
            cfg.SIMILARITY_FACTOR_F,
        )
        p90_ok, p90_why = _similar(
            d["audit_similarity"]["distributions"]["A0"]["p90"],
            d["audit_similarity"]["distributions"]["A1"]["p90"],
            cfg.SIMILARITY_FACTOR_F,
        )
        d["audit_similarity"]["median_within_F"] = {"ok": med_ok,
                                                    "detail": med_why}
        d["audit_similarity"]["p90_within_F"] = {"ok": p90_ok,
                                                 "detail": p90_why}
        d["audit_similarity"]["similar"] = bool(med_ok and p90_ok)
        d["audit_similarity"]["note"] = (
            "each arm's own audited distance to its fixed point, over its "
            "ok runs of the requested seeds; the lift residual is excluded "
            "(reported separately below)"
        )

        # the lift residual, separate (the pin, not an error)
        if deck in cfg.PULSED:
            lr = {}
            for arm in PHASE_A_ARMS:
                vals = sorted(
                    abs((r.get("lift_residual") or {}).get("raw_s"))
                    for r in (rows[arm][str(k)] for k in seeds)
                    if r.get("status") == "ok"
                    and isinstance((r.get("lift_residual") or {}
                                    ).get("raw_s"), (int, float))
                )
                scaled = sorted(
                    (r.get("lift_residual") or {}).get("scaled_abs")
                    for r in (rows[arm][str(k)] for k in seeds)
                    if r.get("status") == "ok"
                    and isinstance((r.get("lift_residual") or {}
                                    ).get("scaled_abs"), (int, float))
                )
                lr[arm] = {
                    "n": len(vals),
                    "abs_raw_s": vals,
                    "abs_raw_s_median": (statistics.median(vals)
                                         if vals else None),
                    "scaled_abs": scaled,
                    "scaled_abs_median": (statistics.median(scaled)
                                          if scaled else None),
                }
            d["lift_residual_distribution"] = {
                "component": PIN_COMPONENT,
                "what": ("burn_time_residual (constraint 93's function) at "
                         "each run's exit; in A1 the pin's inconsistency, "
                         "in A0 the flat arm's converged context value; "
                         "excluded from the similarity statistic"),
                "by_arm": lr,
            }
        else:
            d["lift_residual_distribution"] = {
                "inactive": "k = 0 deck: nothing lifted or pinned"
            }
        summary["per_deck"][deck] = d

        b = d["weighting_invariance_bracket"]
        lines.append(
            f"{deck:24s} gates E:{d['gates']['entry_gate'] or '-':4s} "
            f"W:{d['gates']['warm_gate'] or '-':4s} "
            f"paired {len(paired_ok)}/{len(seeds)}  "
            f"ratio {d['unweighted_count_ratio_A1_over_A0'] and format(d['unweighted_count_ratio_A1_over_A0'], '.4f') or '-'}  "
            f"bracket {b and f'[{b[0]:.3f}, {b[1]:.3f}]' or '-'}  "
            f"similar {d['audit_similarity']['similar']}  "
            f"cold-start {d['cold_start_term']['node_calls']}"
        )

    out_path.write_text(json.dumps(summary, indent=2))
    print("\nPhase A tally"
          + (" (MACHINERY SMOKE — not a measurement)"
             if summary["machinery_smoke"] else "")
          + f" — {out_path}")
    print(f"{'deck':24s} {'gates':12s} {'paired':14s} "
          f"{'A1/A0':7s} {'bracket':17s} {'similar':8s} cold-start")
    for ln in lines:
        print(ln)
    return 0


def stage_tally() -> int:
    return _tally(PA_RUNS / "campaign", PA_RUNS / "tally.json")


# --------------------------------------------------------------------------
# smoke: machinery, not measurement (runnable while approval is False)
# --------------------------------------------------------------------------


def stage_smoke() -> int:
    """The full Phase A path on the cheapest deck, seeds 1..2, under
    ``runs/phase_a/smoke/`` — the phase_b.stage_smoke pattern.  Exercises:
    reference, extension gate (teeth included), warm equivalence gate,
    seed-paired runs, pairing check, tally.  Every record is stamped
    ``machinery_smoke``; its numbers are never published as measurements
    (the gate verdicts are real gate results on real runs)."""
    root = PA_RUNS / "smoke"
    rc = _campaign(root, ("st_regression",), (1, 2), machinery_smoke=True)
    if rc != 0:
        return rc
    return _tally(root, root / "tally.json")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", nargs="?", default="preflight",
                    choices=["preflight", "campaign", "tally", "smoke"])
    args = ap.parse_args()
    if args.stage == "preflight":
        return stage_preflight()
    if args.stage == "campaign":
        return stage_campaign()
    if args.stage == "smoke":
        return stage_smoke()
    return stage_tally()


if __name__ == "__main__":
    raise SystemExit(main())
