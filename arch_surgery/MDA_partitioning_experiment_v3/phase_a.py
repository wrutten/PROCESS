#!/usr/bin/env python
"""V3 Phase A — per-call MDA cost, no optimiser (V3 plan §3.1, §4.1).

Copied verbatim (task A41, first commit 913b89f0) from
arch_surgery/MDA_partitioning_experiment_v2/phase_a.py at commit b7dbd2a9,
then modified per V3_DEVELOPMENT_PLAN.md §3.1, §4.1, §5 (G4, G6), §6
(T-a, T-d, T-e) by task A41.  What changed against V2, and nothing else:

* THREE arms (plan §3.1): A0 (flat control, as V2), A1u (V2's A1 exactly —
  the corrected-audit arm A38 measured, the prime's counterfactual) and A1
  (A1u plus the prime, the V3 intervention's per-call structure).  A1
  refuses to compose while the prime instrument (task A40) is unavailable.
* Every run records the RESTRICTED audit (T-a): ``--audit-exclude-postsolve``
  with the deck's committed post-solve artifact — the same file for every
  arm (the excluded set is a property of the deck, A38 §1) — so each record
  carries the per-component residual vector (audit_residual.json) and a
  re-tally never needs a re-run.
* Gate G4 (restricted-audit teeth), A38's construction verbatim: a doctored
  post-solve-owned component must trip the whole-state audit and NOT the
  restricted one; a doctored in-loop component must trip both (OR
  semantics on work, as A36/A38); plus the tally-side parser tooth on a
  copy of a real residual vector.
* The tally adds: restricted similarity per arm pair A0/A1u and A0/A1 with
  the whole-state audit beside (T-a); the per-run carrier closure of the
  A1u arm against A35's coefficients from perturbation.json (T-e), with
  the downstream-gain analysis on the restricted argmax components; the
  per-block node-call split as a first-class tally artifact (T-d); and a
  record-completeness check — every ok record must carry the H3
  exit_forensics block, or the tally REFUSES (G7's Phase A contract).

Everything else — the warm-entry design, the entry gate and its teeth, the
warm equivalence gate (G6; run for BOTH block arms in V3), the seed-paired
delta-stream, the pin sourced from the same stream on pulsed decks, the
pairing check — is V2's, unchanged (entries per plan §3.1: V2's design).

Stages: ``preflight`` / ``campaign`` / ``tally`` / ``smoke`` (machinery
only, runnable while EXECUTION_APPROVED is False; runs the arms whose
instruments exist and records the refusals by task name).
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

import v3_config as cfg  # noqa: E402
import v3_runner as vr  # noqa: E402  (also puts cfg.IDF_PROBE on sys.path)

from a34_instruments import _cross_residual, load_spec_offline  # noqa: E402
from v2_eval_one import perturb_factor, restore_snapshot  # noqa: E402

PA_RUNS = cfg.RUNS / "phase_a"

#: Phase A's arms (plan §3.1), declared in v3_config.
PHASE_A_ARMS = cfg.PHASE_A_ARMS
BLOCK_ARMS = ("A1u", "A1")

#: The lifted/pinned coupling component (plan §3; A22: all pass-≥2 movement
#: on the pulsed decks is the burn time).
PIN_COMPONENT = "times.t_plant_pulse_burn"

#: Hand-perturbation factor for the gates' teeth (A36's value, unchanged).
TEETH_FACTOR = 1.5

#: T-e (plan §4.1): A35's coefficient-exact closure — deck -> (component,
#: raw image of the pair's entry displacement).  Carried from A38's merged
#: machinery (a38_audit_rerun.py); low_aspect_ratio_DEMO was NOT traced by
#: A35 — nof's coefficients are tested there as a hypothesis, which A38
#: confirmed 25/25 at 1e-11; its restricted argmax term
#: (tfcoil.m_tf_coil_superconductor) has no prediction and is G3c's.
PAIR = ("build.dr_fw_inboard", "build.dr_fw_outboard")
KNOWN_CUT = PAIR + ("pf_power.vpfskv",)
_MEAN = lambda din, dout: 0.5 * (din + dout)  # noqa: E731
_OUT = lambda din, dout: -dout  # noqa: E731
CARRIER = {
    "large_tokamak_nof": {"build.dz_tf_upper_lower_midplane": _MEAN,
                          "build.dr_shld_vv_gap_outboard": _OUT},
    "st_regression": {"build.dr_shld_vv_gap_outboard": _OUT},
    "low_aspect_ratio_DEMO": {"build.dz_tf_upper_lower_midplane": _MEAN,
                              "build.dr_shld_vv_gap_outboard": _OUT},
}
CARRIER_TRACED = {"large_tokamak_nof", "st_regression"}


def stage_preflight() -> int:
    PA_RUNS.mkdir(parents=True, exist_ok=True)
    ledger = {}
    ready = True
    for key in ("single_mda_eval", "trust_mode", "restricted_audit",
                "prime", "exit_forensics"):
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
                   "postsolve": cfg.postsolve_for(deck).exists(),
                   "postsolve_nolift": cfg.postsolve_nolift_for(deck).exists(),
                   "node_writesets": (cfg.DATA / "node_writesets.json").exists()}
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
# arm environments (plan §3.1; composed here, from nothing)
# --------------------------------------------------------------------------


def env_for_phase_a(deck: str, arm: str, *, pin_hex: str | None = None) -> dict:
    """The environment one Phase A arm runs under, built from nothing.

    Every architecture switch is cleared first (v3_runner's discipline: an
    inherited one would change what is measured without saying so).

    A0  = ``flat_state`` + a26 artifacts, NO post-solve (the flat
          architecture as shipped keeps those nodes in its loop — plan §3).
    A1u = V2's A1 EXACTLY (A38's measured arm): resequenced ``per_module``
          + trust + post-solve exclusion + (pulsed) lift and pin.  Pin
          chains run on the ORIGINAL deck (A34 decision (d)); the pulsed
          post-solve artifact is therefore the nolift derivation.
    A1  = A1u plus the prime (O4/D19).  Refuses while the prime instrument
          is unavailable: a predating tree would silently ignore the
          switch and measure A1u under A1's name.
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
    if arm in BLOCK_ARMS:
        env["PROCESS_ARCH_SEQUENCE"] = "build_after_physics"
        env["PROCESS_ARCH_MODULE_SOLVE"] = "per_module"
        env["PROCESS_ARCH_OUTER"] = "trust"
        env["PROCESS_ARCH_HOIST"] = (
            "feedforward_lifted" if deck in cfg.PULSED else "feedforward"
        )
        env["PROCESS_ARCH_POST_SOLVE"] = str(cfg.postsolve_nolift_for(deck))
        if deck in cfg.PULSED:
            env["PROCESS_ARCH_LIFT"] = "burn_time"
            if pin_hex is None:
                raise SystemExit(
                    f"{arm} on pulsed deck {deck} needs a pin value: the pin "
                    f"replaces the optimiser as the lifted variable's owner "
                    f"(A34); running unpinned would measure a different arm."
                )
            env["PROCESS_ARCH_PIN_BURN_TIME"] = pin_hex
        if arm in cfg.PRIMED_ARMS:
            led = cfg.INSTRUMENTATION["prime"]
            if not led["available"]:
                raise SystemExit(
                    f"arm {arm} carries the prime (O4) but the prime "
                    f"instrument is not available ({led['task']}) — "
                    f"refused, never composed silently"
                )
            env["PROCESS_ARCH_PRIME"] = cfg.PRIME_ENV_VALUE
        return env
    raise SystemExit(f"unknown Phase A arm {arm!r}; known: {PHASE_A_ARMS}")


def available_arms() -> tuple[tuple, dict]:
    """The Phase A arms whose instruments exist, and the refusals by name
    (used by the smoke stage; the campaign refuses at preflight instead)."""
    refused = {}
    arms = []
    for arm in PHASE_A_ARMS:
        if arm in cfg.PRIMED_ARMS and not cfg.INSTRUMENTATION["prime"]["available"]:
            refused[arm] = (f"prime not available — "
                            f"{cfg.INSTRUMENTATION['prime']['task']}")
            continue
        arms.append(arm)
    return tuple(arms), refused


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
    and concurrency-invariant; wall clock is progress information only.
    Every run asks for the restricted audit (T-a): the deck's committed
    post-solve artifact, the SAME file for every arm."""
    mpath0 = outdir / "metrics.json"
    if resume and mpath0.exists():
        try:
            prev = json.loads(mpath0.read_text())
        except Exception:
            prev = {}
        if (prev.get("status") == "ok" and prev.get("v3_arm") == arm
                and prev.get("v3_deck") == deck
                and prev.get("v3_seed") == seed
                and prev.get("v3_delta") == delta
                and prev.get("v3_pin_hex") == pin_hex
                and (outdir / "audit_residual.json").exists()):
            print(f"  {deck:24s} {arm:3s} seed={seed:<3d} resumed "
                  f"(complete record kept)", flush=True)
            return {"deck": deck, "arm": arm, "seed": seed, "rc": 0,
                    "outdir": str(outdir), "resumed": True,
                    "status": "ok"}
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
        "--audit-exclude-postsolve", str(cfg.postsolve_for(deck)),
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
    rec["v3_phase"] = "A"
    rec["v3_arm"] = arm
    rec["v3_deck"] = deck
    rec["v3_seed"] = seed
    rec["v3_delta"] = delta
    rec["v3_tau"] = cfg.TAU
    rec["v3_pin_hex"] = pin_hex
    rec["v3_entry_state"] = str(entry_state) if entry_state else None
    rec["v3_machinery_smoke"] = machinery_smoke
    mpath.write_text(json.dumps(rec, indent=2))
    wall = time.perf_counter() - t0
    print(f"  {deck:24s} {arm:3s} seed={seed:<3d} rc={rc} "
          f"status={rec.get('status')} {wall:6.1f}s "
          f"(wall clock is progress information, not a measurement)",
          flush=True)
    return {"deck": deck, "arm": arm, "seed": seed, "rc": rc,
            "outdir": str(outdir), "status": rec.get("status")}


def run_pool(jobs: list[dict]) -> list[dict]:
    """W concurrent runs (v3_runner's pool shape; W from pool_workers()).
    Jobs are never retried: a crash is a taxonomy row."""
    results = []
    with ThreadPoolExecutor(max_workers=vr.pool_workers()) as pool:
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


def _load(p: Path) -> dict:
    return json.loads(Path(p).read_text()) if Path(p).exists() else {}


def spec_components(deck: str) -> list[dict]:
    return json.loads(cfg.ystate_for(deck).read_text())["components"]


def excluded_keys(deck: str) -> tuple[set, list]:
    """T-a's excluded set, derived exactly as the runner derives it (A38
    §1): post-solve NODES -> written fields (the committed run-time write
    census) -> intersected with the a26 spec's keys.  Never a prefix."""
    nodes = json.loads(cfg.postsolve_for(deck).read_text())["post_solve_nodes"]
    census = json.loads((cfg.DATA / "node_writesets.json").read_text())
    per = census["per_scenario"][deck]
    wb = per["writes_by_node"]
    known = set(per.get("node_module") or ()) | set(wb)
    keys = {c["key"] for c in spec_components(deck)}
    excl: set = set()
    for n in nodes:
        if n not in known:
            raise RuntimeError(
                f"post-solve node {n!r} unknown to the {deck} write census")
        excl |= set(wb.get(n, ()))  # a known node with no entry wrote nothing
    return excl & keys, nodes


# --------------------------------------------------------------------------
# gate 1: the --entry-state extension gate (A36 deliverable 1, §12 teeth)
# --------------------------------------------------------------------------


def _doctor_snapshot(ref_snap: dict, deck: str, owned: list | None,
                     candidates, out: Path) -> dict:
    """A hand-perturbed copy of the reference snapshot, for the teeth.

    One CONTINUOUS float scalar component, non-zero, and NOT owned by the
    design vector (the sweep-head injection would silently reset it and the
    teeth would test nothing), taken from ``candidates`` in order.  Factor
    ``TEETH_FACTOR``.
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

    comp = next((nm for nm in candidates if nm and eligible(nm)), None)
    if comp is None:
        raise RuntimeError(
            "no eligible component among the candidates for the teeth: "
            "that is itself a finding, report it"
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
    Teeth: a hand-perturbed snapshot must produce a NONZERO audit OR more
    than the minimal work (the A36 OR semantics; a broken loader shows
    neither).
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

    # teeth: the doctored snapshot (prefer the reference audit's argmax)
    doc_path = root / "doctored_y_exit.json"
    ref_snap = json.loads(snap_path.read_text())
    prefer = (ref_audit.get("brief") or {}).get("argmax")
    if isinstance(prefer, dict):
        prefer = prefer.get("key")
    all_names = list(ref_snap["state"])
    doctor = _doctor_snapshot(
        ref_snap, deck, ref_m.get("spec_keys_owned_by_x"),
        ([prefer] if prefer else []) + all_names, doc_path,
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
    # nonzero post-eval audit, OR more-than-minimal solver work (V2 launch
    # fix 2's OR semantics — on a deck whose flat solve terminates at the
    # exact fixed point the audit tooth cannot fire and the work tooth is
    # the binding one; a broken loader shows neither).
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
# gate 2: the warm equivalence gate (G6; V3 runs it for BOTH block arms)
# --------------------------------------------------------------------------


def _warm_teeth(spec, y_ref: list, y_arm: list) -> dict:
    """Comparator perturbations that must trip the criterion (the A34
    pin_gate teeth, unchanged in shape)."""
    trials = {}
    ys_cont = next(
        i for i in range(len(spec.keys))
        if spec.category[i] == "continuous" and isinstance(y_ref[i], float)
    )
    y_pert = list(y_ref)
    y_pert[ys_cont] = y_pert[ys_cont] + 3.0 * cfg.TAU * spec.scale[ys_cont]
    c1 = _cross_residual(spec, y_pert, y_arm, cfg.TAU)
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
        c2 = _cross_residual(spec, y_pert, y_arm, cfg.TAU)
        trials["discrete_flipped"] = not (
            c2["max"] < cfg.TAU and c2["categorically_clean"]
        )
    return {
        "n_perturbations": len(trials),
        "n_tripped": sum(bool(v) for v in trials.values()),
        "all_tripped": all(trials.values()),
        "per_perturbation": trials,
    }


def warm_gate(deck: str, droot: Path, ref: dict, arm: str,
              machinery_smoke: bool) -> dict:
    """One block arm from the reference snapshot, unperturbed, pinned at the
    reference's exact burn time (pulsed decks): must land on the reference
    fixed point.  Criterion, pre-declared (A34 decision (e), warm-entry
    binding): categorically clean AND cross-state max residual vs the
    reference < τ.  V3 runs this for BOTH block arms (G6): A1u re-checks
    V2's result at the V3 commit; A1 additionally establishes that the
    prime changes nothing at the warm fixed point (G2's harness-side
    shadow).  A FAIL stops the campaign and IS the result."""
    root = droot / f"warm_gate_{arm}"
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
                "gate": f"V3 warm equivalence gate ({arm})",
                "verdict": "FAIL",
                "failed_at": (
                    f"pin value inconsistency: reference metrics say "
                    f"{pin_hex}, its snapshot says {snap_burn} for "
                    f"{PIN_COMPONENT} — configuration error, not a result"
                ),
            }
            (root / "gate.json").write_text(json.dumps(record, indent=2))
            return record

    print(f"  warm gate [{arm}] criterion (pre-declared): categorically "
          f"clean AND cross-state max residual vs the reference < tau = "
          f"{cfg.TAU:g}" + (f"; pin = {pin_hex}" if pin_hex else ""),
          flush=True)

    a1 = run_eval_job(deck, arm, root / f"{arm}_warm",
                      entry_state=snap_path, seed=0, pin_hex=pin_hex,
                      machinery_smoke=machinery_smoke)
    m1 = _metrics(a1["outdir"])
    record: dict = {
        "gate": (
            f"V3 warm equivalence gate for arm {arm} (G6; A36's "
            f"construction re-run at the V3 commit): one {arm} run from "
            f"the reference snapshot, pinned at the reference's converged "
            f"burn time, must reproduce the reference fixed point within "
            f"the audit's resolution"
        ),
        "criterion_bound": (
            "categorically clean AND cross_max < tau, under the a26 audit "
            "ruler (pre-declared; A34 decision (e))"
        ),
        "tau": cfg.TAU,
        "arm": arm,
        "reference": {"outdir": ref["outdir"],
                      "t_plant_pulse_burn_hex": ref_m.get(
                          "t_plant_pulse_burn_hex"),
                      **_stamp(ref_m)},
        "arm_run": {
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
        record["failed_at"] = f"the {arm} chain did not complete"
        (root / "gate.json").write_text(json.dumps(record, indent=2))
        print(f"  warm gate [{arm}] {deck}: FAIL (chain did not complete)",
              flush=True)
        return record

    spec = load_spec_offline(cfg.ystate_for(deck))
    y_ref = restore_snapshot(spec, json.loads(snap_path.read_text()))
    y_arm = restore_snapshot(
        spec, json.loads((Path(a1["outdir"]) / "y_exit.json").read_text())
    )
    cross = _cross_residual(spec, y_ref, y_arm, cfg.TAU)
    teeth = _warm_teeth(spec, y_ref, y_arm)
    pin_bit_identical = None
    if deck in cfg.PULSED:
        idx = {spec.name(i): i for i in range(len(spec.keys))}
        li = idx.get(PIN_COMPONENT)
        if li is not None:
            pin_bit_identical = float(y_ref[li]) == float(y_arm[li])
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
    print(f"  warm gate [{arm}] {deck}: {record['verdict']} (cross max "
          f"{cross['max_hex']}, {cross['n_above_tau']} above tau, "
          f"clean={cross['categorically_clean']})", flush=True)
    return record


# --------------------------------------------------------------------------
# gate G4: the restricted-audit teeth (A38's construction; protocol §12)
# --------------------------------------------------------------------------


def restricted_teeth(deck: str, droot: Path, ref: dict, arm: str,
                     machinery_smoke: bool) -> dict:
    """Three ``arm`` runs from the reference snapshot, unperturbed, pinned:
    a restricted baseline; one with a post-solve-owned component doctored
    (whole-state audit must move by exactly the doctored displacement, the
    restricted audit must be bit-identical to the baseline); one with an
    in-loop component doctored (restricted moved OR more work — the A38 OR
    semantics: a re-converged component can land on identical bits at a
    bit-exact fixed point).  Runs under the prime-free block arm so the
    gate needs no instrument beyond A38's."""
    root = droot / "restricted_teeth"
    root.mkdir(parents=True, exist_ok=True)
    ref_m = ref["metrics"]
    snap_path = Path(ref["outdir"]) / "y_exit.json"
    snap = json.loads(snap_path.read_text())
    owned = ref_m.get("spec_keys_owned_by_x") or []
    pin_hex = (ref_m.get("t_plant_pulse_burn_hex")
               if deck in cfg.PULSED else None)
    excl, _nodes = excluded_keys(deck)
    scale = {c["key"]: c.get("scale") for c in spec_components(deck)}

    base = run_eval_job(deck, arm, root / f"{arm}_warm_restricted",
                        entry_state=snap_path, seed=0, pin_hex=pin_hex,
                        machinery_smoke=machinery_smoke)
    bm = _metrics(base["outdir"])
    b_aud = bm.get("exit_audit") or {}
    b_res = b_aud.get("restricted") or {}

    # (a) a post-solve-owned component: prefer costs.*, then any excluded key
    cand_ps = sorted(k for k in excl if k.startswith("costs.")) + sorted(excl)
    doc_ps = _doctor_snapshot(snap, deck, owned, cand_ps,
                              root / "doctored_postsolve.json")
    ps = run_eval_job(deck, arm, root / f"{arm}_doctored_postsolve",
                      entry_state=root / "doctored_postsolve.json", seed=0,
                      pin_hex=pin_hex, machinery_smoke=machinery_smoke)
    pm = _metrics(ps["outdir"])
    p_aud = pm.get("exit_audit") or {}
    p_res = p_aud.get("restricted") or {}
    p_vec = _load(Path(ps["outdir"]) / "audit_residual.json").get("scaled") or {}
    comp = doc_ps["component"]
    expected = abs(float.fromhex(doc_ps["after_hex"])
                   - float.fromhex(doc_ps["before_hex"])) / scale[comp]
    got = p_vec.get(comp)
    ps_checks = {
        "run_ok": pm.get("status") == "ok",
        "doctored_component_is_excluded": comp in excl,
        "doctored_component_residual_equals_displacement": (
            got is not None and expected > 0
            and abs(got - expected) <= 1e-9 * expected),
        "whole_state_max_moved": (
            p_aud.get("residual_max_hex") != b_aud.get("residual_max_hex")),
        "whole_state_max_at_least_displacement": (
            p_aud.get("residual_max") is not None
            and p_aud["residual_max"] >= expected * (1 - 1e-9)),
        "restricted_max_bit_identical_to_baseline": (
            p_res.get("max_hex") is not None
            and p_res.get("max_hex") == b_res.get("max_hex")),
        "restricted_argmax_identical_to_baseline": (
            p_res.get("argmax") == b_res.get("argmax")),
    }

    # (b) an in-loop component: prefer the reference audit's own argmax,
    # but ONLY if it is in-loop (on large_tokamak_nof that argmax is a
    # post-solve-owned field — A38 found this by its own tooth failing).
    ref_argmax = ((ref_m.get("exit_audit") or {}).get("brief") or {}
                  ).get("argmax")
    if isinstance(ref_argmax, dict):
        ref_argmax = ref_argmax.get("key")
    kept = [c["key"] for c in spec_components(deck) if c["key"] not in excl]
    cand_il = [c for c in ([ref_argmax] if ref_argmax else []) + kept
               if c not in excl]
    doc_il = _doctor_snapshot(snap, deck, owned, cand_il,
                              root / "doctored_inloop.json")
    il = run_eval_job(deck, arm, root / f"{arm}_doctored_inloop",
                      entry_state=root / "doctored_inloop.json", seed=0,
                      pin_hex=pin_hex, machinery_smoke=machinery_smoke)
    im = _metrics(il["outdir"])
    i_aud = im.get("exit_audit") or {}
    i_res = i_aud.get("restricted") or {}
    b_sw = (bm.get("module_solve_stats") or {}).get("block_sweeps")
    i_sw = (im.get("module_solve_stats") or {}).get("block_sweeps")
    il_checks = {
        "run_ok": im.get("status") == "ok",
        "doctored_component_is_in_loop": doc_il["component"] not in excl,
        "whole_state_max_moved": (
            i_aud.get("residual_max_hex") != b_aud.get("residual_max_hex")),
        "restricted_max_moved": (
            i_res.get("max_hex") != b_res.get("max_hex")),
        "more_block_sweeps_than_baseline": (
            isinstance(b_sw, int) and isinstance(i_sw, int) and i_sw > b_sw),
    }
    il_checks["restricted_moved_or_more_work"] = bool(
        il_checks["restricted_max_moved"]
        or il_checks["more_block_sweeps_than_baseline"])
    il_binding = {k: il_checks[k] for k in (
        "run_ok", "doctored_component_is_in_loop",
        "restricted_moved_or_more_work")}
    record = {
        "gate": ("G4 restricted-audit teeth (A38's construction): the "
                 "restricted statistic must be blind to a post-solve-owned "
                 "displacement and sighted to an in-loop one (§12)"),
        "arm": arm,
        "baseline": {"outdir": base["outdir"], "status": bm.get("status"),
                     "whole_max_hex": b_aud.get("residual_max_hex"),
                     "restricted": b_res, **_stamp(bm)},
        "postsolve_doctored": {"doctored": doc_ps,
                               "expected_scaled": expected,
                               "measured_scaled": got,
                               "whole_max_hex": p_aud.get("residual_max_hex"),
                               "restricted": p_res, "checks": ps_checks,
                               **_stamp(pm)},
        "inloop_doctored": {"doctored": doc_il,
                            "whole_max_hex": i_aud.get("residual_max_hex"),
                            "restricted": i_res, "checks": il_checks,
                            "binding_checks": il_binding,
                            "block_sweeps": {"baseline": b_sw,
                                             "doctored": i_sw},
                            **_stamp(im)},
        "machinery_smoke": machinery_smoke,
        "verdict": ("PASS" if all(ps_checks.values())
                    and all(il_binding.values()) else "FAIL"),
    }
    (root / "gate.json").write_text(json.dumps(record, indent=2))
    print(f"  G4 restricted teeth {deck}: {record['verdict']} "
          f"(post-solve doctored {comp}: whole "
          f"{p_aud.get('residual_max_hex')} vs base "
          f"{b_aud.get('residual_max_hex')}, restricted "
          f"{p_res.get('max_hex')} vs base {b_res.get('max_hex')}; in-loop "
          f"doctored {doc_il['component']}: restricted "
          f"{i_res.get('max_hex')}, sweeps {b_sw}->{i_sw})", flush=True)
    return record


# --------------------------------------------------------------------------
# the campaign
# --------------------------------------------------------------------------


def pairing_check(droot: Path, seeds, arms) -> dict:
    """Seed pairing, shown not assumed: ALL arms' recorded entry states
    (y_entry.json, full coupling state as exact hex) must be bit-identical
    per seed (plan §3.1: pairing across all three arms)."""
    detail = {}
    n_id = 0
    compared = 0
    base_arm = arms[0]
    for k in seeds:
        paths = {a: droot / a / f"start{k:03d}" / "y_entry.json"
                 for a in arms}
        if not all(p.exists() for p in paths.values()):
            detail[str(k)] = {"compared": False, "why": "missing y_entry"}
            continue
        states = {a: json.loads(p.read_text())["state"]
                  for a, p in paths.items()}
        sa = states[base_arm]
        same = True
        rows = {}
        for a in arms[1:]:
            sb = states[a]
            ident = sum(1 for nm in sa if sb.get(nm) == sa[nm])
            arm_same = ident == len(sa) and len(sb) == len(sa)
            rows[a] = {"n_bit_identical": ident, "identical": arm_same}
            same &= arm_same
        compared += 1
        n_id += bool(same)
        detail[str(k)] = {"compared": True, "n_rows": len(sa),
                          "vs_" + base_arm: rows, "identical": same}
    return {
        "what": ("cross-arm bit-identity of the full recorded entry state, "
                 "all arms against " + base_arm + ", every seed"),
        "arms": list(arms),
        "n_seeds_compared": compared,
        "n_seeds_bit_identical": n_id,
        "all_identical": compared > 0 and n_id == compared,
        "per_seed": detail,
    }


def deck_campaign(deck: str, droot: Path, seeds, arms,
                  machinery_smoke: bool) -> tuple[dict, bool]:
    """Reference, the gates, then the seeded runs.  Returns (record, ok);
    ok False stops the campaign (a failed gate is a result)."""
    droot.mkdir(parents=True, exist_ok=True)
    rec: dict = {"deck": deck, "arms": list(arms)}

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

    # 3. the warm equivalence gate, per block arm present (G6)
    for arm in [a for a in BLOCK_ARMS if a in arms]:
        rec[f"warm_gate_{arm}"] = warm_gate(deck, droot, ref, arm,
                                            machinery_smoke)
        if rec[f"warm_gate_{arm}"]["verdict"] != "PASS":
            rec["refused"] = (f"warm equivalence gate ({arm}) FAILED — "
                              f"that failure is the result (plan §3); the "
                              f"campaign stops here")
            return rec, False

    # 4. gate G4: the restricted-audit teeth (prime-free block arm)
    g4_arm = "A1u" if "A1u" in arms else arms[-1]
    rec["restricted_teeth"] = restricted_teeth(deck, droot, ref, g4_arm,
                                               machinery_smoke)
    if rec["restricted_teeth"]["verdict"] != "PASS":
        rec["refused"] = ("G4 restricted-audit teeth FAILED — the "
                          "corrected statistic is not trusted")
        return rec, False

    # 5. the seeded campaign, all arms, seed-paired
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
        for arm in arms:
            jobs.append(dict(deck=deck, arm=arm,
                             outdir=droot / arm / f"start{k:03d}",
                             entry_state=snap_path, delta=cfg.DELTA, seed=k,
                             pin_hex=pin_hex if arm in BLOCK_ARMS else None,
                             resume=True,
                             machinery_smoke=machinery_smoke))
    print(f"{deck}: campaign — {len(jobs)} runs "
          f"({len(list(seeds))} seeds x {len(arms)} arms), "
          f"{vr.pool_workers()} workers", flush=True)
    results = run_pool(jobs)
    rec["seed_pins_hex"] = pins or None
    rec["workers"] = vr.pool_workers()
    rec["runs"] = {
        f"{r['arm']}/start{r['seed']:03d}": {
            "rc": r["rc"], "status": r.get("status"),
        }
        for r in results
    }

    # 6. the pairing check, all arms
    rec["pairing"] = pairing_check(droot, seeds, arms)
    (droot / "pairing.json").write_text(json.dumps(rec["pairing"], indent=2))
    if not rec["pairing"]["all_identical"]:
        rec["pairing_failure"] = (
            "the arms' entry states are NOT bit-identical on every "
            "compared seed — the seed-paired design is broken for this "
            "deck; reported as a failure, not papered over"
        )
        return rec, False
    print(f"{deck}: pairing {rec['pairing']['n_seeds_bit_identical']}/"
          f"{rec['pairing']['n_seeds_compared']} seeds bit-identical "
          f"across arms", flush=True)
    return rec, True


def _campaign(root: Path, decks, seeds, arms, machinery_smoke: bool) -> int:
    root.mkdir(parents=True, exist_ok=True)
    (cfg.RUNS / "_mplconfig").mkdir(parents=True, exist_ok=True)
    record: dict = {
        "phase": "A", "machinery_smoke": machinery_smoke,
        "design": ("warm-entry, V2's entries unchanged (V3 plan §3.1); "
                   "three arms A0/A1u/A1"),
        "tau": cfg.TAU, "delta": cfg.DELTA,
        "arms": list(arms), "decks": list(decks),
        "seeds": list(seeds), "workers": vr.pool_workers(),
        "per_deck": {},
    }
    for deck in decks:
        drec, ok = deck_campaign(deck, root / deck, seeds, arms,
                                 machinery_smoke)
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
              "(v3_config.EXECUTION_APPROVED).  Run 'smoke' for the "
              "machinery test.")
        return 3
    if stage_preflight() != 0:
        print("\nREFUSED: Phase A instrumentation missing — the ledger "
              "above names the task each gap belongs to.")
        return 3
    return _campaign(PA_RUNS / "campaign", cfg.DECKS,
                     tuple(range(1, cfg.N_STARTS + 1)),
                     PHASE_A_ARMS, machinery_smoke=False)


# --------------------------------------------------------------------------
# the tally (T-a, T-d, T-e; G7's Phase A completeness contract)
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
    res = audit.get("restricted") or {}
    return {
        "status": m.get("status"),
        "node_calls_single_eval": m.get("node_calls_single_eval"),
        "sweeps": m.get("n_model_calls_sweeps"),
        "block_sweeps": stats.get("block_sweeps"),
        "outer_passes": stats.get("outer_passes"),
        "audit_residual_max": audit.get("residual_max"),
        "audit_residual_max_hex": audit.get("residual_max_hex"),
        "restricted_max": res.get("max"),
        "restricted_max_hex": res.get("max_hex"),
        "restricted_argmax": res.get("argmax"),
        "restricted_n_above": res.get("n_above"),
        "restricted_n_excluded": res.get("n_excluded"),
        "restricted_n_kept": res.get("n_kept"),
        "excluded_sha256": res.get("excluded_sha256"),
        "whole_argmax": (audit.get("brief") or {}).get("argmax"),
        "node_census": m.get("node_census"),
        "lift_residual": m.get("lift_residual"),
        "pin_intact_at_exit": m.get("pin_intact_at_exit"),
        "objf_hex": (m.get("exact") or {}).get("objf"),
        "has_exit_forensics": "exit_forensics" in m,
        "arch_block_schedule": m.get("arch_block_schedule"),
        "tree_git_head": m.get("tree_git_head"),
        "tree_git_dirty": m.get("tree_git_dirty"),
    }


def _census_total(row: dict) -> dict:
    nc = row.get("node_census") or {}
    out = dict(nc.get("counted") or {})
    for k, v in (nc.get("flat_tail") or {}).items():
        out[k] = out.get(k, 0) + v
    return out


def _parser_teeth(vec_path: Path) -> dict:
    """The tally's own restriction logic must be shown to fail (G4's
    tally-side tooth, A38's construction): on a COPY of a real residual
    vector, an excluded key set to 10x the whole-state max must move the
    whole-state max and not the restricted one; a kept key so doctored
    must move both."""
    v = _load(vec_path)
    scaled = dict(v.get("scaled") or {})
    excl = set(v.get("excluded_keys") or [])
    if not scaled or not excl:
        return {"verdict": "FAIL", "why": "no vector or no excluded keys"}

    def stats(sc):
        whole = max(sc.values())
        kept = {k: x for k, x in sc.items() if k not in excl}
        return whole, max(kept.values())

    w0, r0 = stats(scaled)
    big = 10.0 * w0 + 1.0
    kx = next(iter(sorted(excl & set(scaled))))
    kk = next(iter(sorted(set(scaled) - excl)))
    s1 = dict(scaled)
    s1[kx] = big
    w1, r1 = stats(s1)
    s2 = dict(scaled)
    s2[kk] = big
    w2, r2 = stats(s2)
    checks = {"excluded_doctored_moves_whole": w1 != w0,
              "excluded_doctored_keeps_restricted": r1 == r0,
              "kept_doctored_moves_whole": w2 != w0,
              "kept_doctored_moves_restricted": r2 != r0}
    return {"vector": str(vec_path), "doctored_excluded": kx,
            "doctored_kept": kk, "checks": checks,
            "verdict": "PASS" if all(checks.values()) else "FAIL"}


def _closure(deck: str, droot: Path, seeds, arm: str) -> dict:
    """T-e: per ``arm`` run, the pair's recorded entry displacement
    (perturbation.json), A35's predicted raw image on the deck's closed
    components, and the measured raw movement of those components in the
    audit vector — no re-run needed (list item 6: the records already hold
    the factor and before/after hex)."""
    scale = {c["key"]: c.get("scale") for c in spec_components(deck)}
    preds = CARRIER.get(deck) or {}
    rows = {}
    rel_by = {nm: [] for nm in preds}
    n_closed_argmax = 0
    for k in seeds:
        d = droot / arm / f"start{k:03d}"
        pert = _load(d / "perturbation.json").get("per_component") or []
        pc = {e["key"]: e for e in pert}
        disp = {}
        for key in KNOWN_CUT:
            e = pc.get(key)
            if e:
                b, a = (float.fromhex(e["elem_before_hex"]),
                        float.fromhex(e["elem_after_hex"]))
                disp[key] = {"before_hex": e["elem_before_hex"],
                             "after_hex": e["elem_after_hex"],
                             "delta_raw": a - b, "factor": e.get("factor")}
        row = {"known_cut_entry_displacement": disp, "images": {}}
        vec = _load(d / "audit_residual.json").get("scaled") or {}
        if all(p in disp for p in PAIR):
            din = disp[PAIR[0]]["delta_raw"]
            dout = disp[PAIR[1]]["delta_raw"]
            for name, f in preds.items():
                if scale.get(name) is None or name not in vec:
                    continue
                pred = abs(f(din, dout))
                meas = vec[name] * scale[name]
                r = abs(meas - pred) / pred if pred else None
                row["images"][name] = {
                    "predicted_raw": pred, "measured_raw": meas,
                    "predicted_scaled": pred / scale[name],
                    "measured_scaled": vec[name], "rel_diff": r}
                if r is not None:
                    rel_by[name].append(r)
        m = _metrics(d)
        res = (m.get("exit_audit") or {}).get("restricted") or {}
        row["restricted_argmax"] = res.get("argmax")
        row["restricted_max"] = res.get("max")
        row["restricted_argmax_is_closed_image"] = res.get("argmax") in preds
        n_closed_argmax += bool(row["restricted_argmax_is_closed_image"])
        rows[str(k)] = row
    return {"what": (f"T-e carrier closure per {arm} run: for every closed "
                     f"image of the pair on this deck, the predicted raw "
                     f"movement from the pair's recorded entry displacement "
                     f"vs the component's measured raw movement in the "
                     f"audit; and whether the restricted argmax is one of "
                     f"those images"),
            "arm": arm,
            "traced_by_A35": deck in CARRIER_TRACED,
            "images": {nm: {"n": len(v),
                            "rel_diff_median": (statistics.median(v)
                                                if v else None),
                            "rel_diff_max": max(v) if v else None}
                       for nm, v in rel_by.items()},
            "n_runs_restricted_argmax_is_closed_image": n_closed_argmax,
            "per_run": rows}


def _per_block_split(deck: str, droot: Path, seeds, arms,
                     rows: dict) -> dict:
    """T-d: the per-block node-call split as a first-class tally artifact.
    Block membership from a block arm's own executed schedule
    (arch_block_schedule in its record); the post-solve node set from the
    deck's committed artifact; anything unmapped is named, not pooled."""
    block_map: dict[str, str] = {}
    for arm in reversed([a for a in arms if a in BLOCK_ARMS]):
        for k in seeds:
            sched = rows.get(arm, {}).get(str(k), {}).get(
                "arch_block_schedule")
            if sched:
                for bname, nodes, _it in sched:
                    for n in nodes:
                        block_map[n] = bname
                break
        if block_map:
            break
    ps_nodes = set(json.loads(cfg.postsolve_for(deck).read_text())
                   ["post_solve_nodes"])
    block_map.setdefault("pulse", "PULSE")
    per_block: dict = {}
    for arm in arms:
        agg: dict[str, int] = {}
        for k in seeds:
            r = rows.get(arm, {}).get(str(k)) or {}
            if r.get("status") != "ok":
                continue
            for n, c in _census_total(r).items():
                blk = ("post_solve" if n in ps_nodes
                       else block_map.get(n, f"UNMAPPED:{n}"))
                agg[blk] = agg.get(blk, 0) + c
        agg["TOTAL"] = sum(agg.values())
        per_block[arm] = agg
    return {"what": ("T-d: node calls summed per block over the ok runs of "
                     "the requested seeds; block membership from a block "
                     "arm's executed schedule, post-solve set from the "
                     "deck's committed artifact; unmapped nodes are named"),
            "block_map_nodes": len(block_map),
            "per_arm": per_block}


def _tally(root: Path, out_path: Path) -> int:
    campf = root / "campaign.json"
    if not campf.exists():
        print("no Phase A campaign records — the campaign has not run")
        return 1
    camp = json.loads(campf.read_text())
    seeds = camp["seeds"]
    arms = tuple(camp["arms"])
    summary: dict = {
        "phase": "A",
        "machinery_smoke": camp.get("machinery_smoke"),
        "tau": camp["tau"], "delta": camp["delta"],
        "similarity_factor_F": cfg.SIMILARITY_FACTOR_F,
        "arms": list(arms),
        "n_seeds_requested": len(seeds),
        "quantile_definitions": {
            "median": "statistics.median (even n: mean of the two central "
                      "order statistics) — Phase A distributions only; "
                      "Phase B check statistics use nearest-rank",
            "p90": "nearest-rank, element ceil(0.9 n) of the sorted list",
        },
        "per_deck": {},
    }
    lines = []
    refusals = []
    for deck in camp["decks"]:
        droot = root / deck
        drec = camp["per_deck"].get(deck) or {}
        d: dict = {"gates": {
            "entry_gate": (drec.get("entry_gate") or {}).get("verdict"),
            **{f"warm_gate_{a}": (drec.get(f"warm_gate_{a}") or {}).get(
                "verdict") for a in BLOCK_ARMS if f"warm_gate_{a}" in drec},
            "restricted_teeth": (drec.get("restricted_teeth") or {}).get(
                "verdict"),
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
        for arm in arms:
            rows[arm] = {}
            for k in seeds:
                p = droot / arm / f"start{k:03d}" / "metrics.json"
                rows[arm][str(k)] = (
                    _row(json.loads(p.read_text())) if p.exists()
                    else {"status": "missing"}
                )
        d["per_run"] = rows

        # G7's Phase A contract: every ok record carries exit_forensics.
        missing_forensics = [
            f"{arm}/start{k:03d}" for arm in arms for k in seeds
            if rows[arm][str(k)].get("status") == "ok"
            and not rows[arm][str(k)].get("has_exit_forensics")
        ]
        if missing_forensics:
            refusals.append(
                f"{deck}: {len(missing_forensics)} ok records carry no "
                f"exit_forensics block (first: {missing_forensics[0]}) — "
                f"the tally REFUSES (G7)")
        d["exit_forensics_complete"] = not missing_forensics

        # failure taxonomy: every requested seed a row, denominators named
        taxonomy = {arm: {} for arm in arms}
        for arm in arms:
            for k in seeds:
                st = str(rows[arm][str(k)].get("status"))
                taxonomy[arm][st] = taxonomy[arm].get(st, 0) + 1
        d["failure_taxonomy"] = {
            "denominator_per_arm": len(seeds),
            "by_arm": taxonomy,
            "per_seed": {
                str(k): {arm: rows[arm][str(k)].get("status")
                         for arm in arms}
                for k in seeds
            },
        }

        paired_ok = [
            k for k in seeds
            if all(rows[a][str(k)].get("status") == "ok" for a in arms)
        ]
        d["n_paired_ok"] = len(paired_ok)
        d["paired_ok_seeds"] = paired_ok

        # per-node counts (summed over the identical-success set), the
        # weighting-invariance bracket, and the unweighted ratio, per pair
        sums = {arm: {} for arm in arms}
        totals = {arm: 0 for arm in arms}
        for arm in arms:
            for k in paired_ok:
                r = rows[arm][str(k)]
                totals[arm] += r.get("node_calls_single_eval") or 0
                for nm, v in _census_total(r).items():
                    sums[arm][nm] = sums[arm].get(nm, 0) + v
        d["node_calls_total_paired_ok"] = totals
        d["count_ratios"] = {}
        for base, var in [("A0", a) for a in arms if a != "A0"] + (
                [("A1u", "A1")] if {"A1u", "A1"} <= set(arms) else []):
            ratios = []
            per_node = {}
            for nm in sorted(set(sums[base]) | set(sums[var])):
                n0 = sums[base].get(nm, 0)
                n1 = sums[var].get(nm, 0)
                ratio = (n1 / n0) if n0 else (math.inf if n1 else None)
                per_node[nm] = {base: n0, var: n1, "ratio": ratio}
                if ratio is not None and ratio != math.inf:
                    ratios.append(ratio)
            d["count_ratios"][f"{base}->{var}"] = {
                "unweighted_count_ratio": (
                    totals[var] / totals[base] if totals[base] else None),
                "weighting_invariance_bracket": (
                    [min(ratios), max(ratios)] if ratios else None),
                "per_node": per_node,
            }

        # T-a: audit similarity — whole-state AND restricted, per pair
        def dist(vals):
            vals = sorted(vals)
            return {"n": len(vals), "values": vals,
                    "values_hex": [float(v).hex() for v in vals],
                    "median": statistics.median(vals) if vals else None,
                    "p90": _p90(vals) if vals else None}

        whole = {arm: dist([
            r.get("audit_residual_max")
            for r in (rows[arm][str(k)] for k in seeds)
            if r.get("status") == "ok"
            and r.get("audit_residual_max") is not None]) for arm in arms}
        restr = {arm: dist([
            r.get("restricted_max")
            for r in (rows[arm][str(k)] for k in seeds)
            if r.get("status") == "ok"
            and r.get("restricted_max") is not None]) for arm in arms}

        def pair_verdict(dists, a, b):
            med_ok, med_why = _similar(dists[a]["median"],
                                       dists[b]["median"],
                                       cfg.SIMILARITY_FACTOR_F)
            p90_ok, p90_why = _similar(dists[a]["p90"], dists[b]["p90"],
                                       cfg.SIMILARITY_FACTOR_F)
            return {"median_within_F": {"ok": med_ok, "detail": med_why},
                    "p90_within_F": {"ok": p90_ok, "detail": p90_why},
                    "similar": bool(med_ok and p90_ok)}

        d["audit_similarity"] = {
            "whole_state": {"distributions": whole},
            "restricted": {"distributions": restr},
            "note": ("T-a: the restricted statistic (components not owned "
                     "by the post-solve set, derived node->fields->spec) "
                     "is the declared construction (plan §4.1); the "
                     "whole-state audit is published beside it.  The lift "
                     "residual is excluded (reported separately)."),
        }
        for a, b in [("A0", x) for x in arms if x != "A0"]:
            d["audit_similarity"]["whole_state"][f"{a}/{b}"] = pair_verdict(
                whole, a, b)
            d["audit_similarity"]["restricted"][f"{a}/{b}"] = pair_verdict(
                restr, a, b)

        # restricted / whole argmax census per block arm
        d["argmax_census"] = {}
        for arm in [a for a in arms if a != "A0"]:
            d["argmax_census"][arm] = {
                "whole_state": {
                    nm: sum(1 for k in paired_ok
                            if rows[arm][str(k)].get("whole_argmax") == nm)
                    for nm in sorted({rows[arm][str(k)].get("whole_argmax")
                                      for k in paired_ok} - {None})},
                "restricted": {
                    nm: sum(1 for k in paired_ok
                            if rows[arm][str(k)].get("restricted_argmax")
                            == nm)
                    for nm in sorted({rows[arm][str(k)].get(
                        "restricted_argmax") for k in paired_ok} - {None})},
            }

        # T-e: carrier closure on the prime-free arm (and, when present,
        # the primed arm — whose images are expected to vanish)
        d["closure"] = {}
        for arm in [a for a in BLOCK_ARMS if a in arms]:
            d["closure"][arm] = _closure(deck, droot, paired_ok, arm)

        # T-d: the per-block split, first-class
        d["per_block_split"] = _per_block_split(deck, droot, paired_ok,
                                                arms, rows)

        # G4's tally-side parser tooth, on a copy of a real vector
        first_block_arm = next((a for a in BLOCK_ARMS if a in arms), None)
        if first_block_arm and paired_ok:
            d["parser_teeth"] = _parser_teeth(
                droot / first_block_arm / f"start{paired_ok[0]:03d}"
                / "audit_residual.json")
            if d["parser_teeth"]["verdict"] != "PASS":
                refusals.append(f"{deck}: parser teeth FAILED")

        # the lift residual, separate (the pin, not an error)
        if deck in cfg.PULSED:
            lr = {}
            for arm in arms:
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
                         "each run's exit; in the block arms the pin's "
                         "inconsistency, in A0 the flat arm's converged "
                         "context value; excluded from the similarity "
                         "statistic"),
                "by_arm": lr,
            }
        else:
            d["lift_residual_distribution"] = {
                "inactive": "k = 0 deck: nothing lifted or pinned"
            }
        summary["per_deck"][deck] = d

        r_a1 = (d["count_ratios"].get("A0->A1") or
                d["count_ratios"].get("A0->A1u") or {})
        lines.append(
            f"{deck:24s} gates {d['gates']}  "
            f"paired {len(paired_ok)}/{len(seeds)}  "
            f"ratio {r_a1.get('unweighted_count_ratio') and format(r_a1['unweighted_count_ratio'], '.4f') or '-'}  "
            f"cold-start {d['cold_start_term']['node_calls']}"
        )

    summary["tally_refusals"] = refusals
    out_path.write_text(json.dumps(summary, indent=2))
    print("\nPhase A tally"
          + (" (MACHINERY SMOKE — not a measurement)"
             if summary["machinery_smoke"] else "")
          + f" — {out_path}")
    for ln in lines:
        print(ln)
    if refusals:
        for r in refusals:
            print(f"TALLY REFUSED: {r}")
        return 2
    return 0


def stage_tally() -> int:
    return _tally(PA_RUNS / "campaign", PA_RUNS / "tally.json")


# --------------------------------------------------------------------------
# smoke: machinery, not measurement (runnable while approval is False)
# --------------------------------------------------------------------------


def stage_smoke() -> int:
    """The full Phase A path on the cheapest deck, seeds 1..2, under
    ``runs/phase_a/smoke/``.  Runs the arms whose instruments exist and
    records the refusals by task name (while the prime is unbuilt, A1
    refuses and the smoke runs A0 + A1u).  Every record is stamped
    ``machinery_smoke``; its numbers are never published as measurements
    (the gate verdicts are real gate results on real runs)."""
    root = PA_RUNS / "smoke"
    arms, refused = available_arms()
    if refused:
        for arm, why in refused.items():
            print(f"  smoke: arm {arm} REFUSED — {why}")
    rc = _campaign(root, ("st_regression",), (1, 2), arms,
                   machinery_smoke=True)
    camp = _load(root / "campaign.json")
    camp["arms_refused"] = refused
    (root / "campaign.json").write_text(json.dumps(camp, indent=2))
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
