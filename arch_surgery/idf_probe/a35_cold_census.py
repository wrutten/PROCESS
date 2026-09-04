#!/usr/bin/env python
"""A35 (cold-census): name the CARRIER of the displacement-scaled
cross-block transient -- the mechanism by which a one-pass feed-forward
block chain's exit state differs from the flat MDA's fixed point when the
validated DSM says inter-block edges are forward-only.

Plan: ``arch_surgery/docs/plans/A35_INVESTIGATION_PLAN.md`` (committed
before this script ran; the four candidate carriers (a)-(d) and their
discriminating signatures are declared there, in advance).

Stages (protocol section 15: every published number comes from executing
this committed script; failure paths are reachable from the same entry
point; nothing is retried with different settings)
-----------------------------------------------------------------------
``refs``
    Per deck, one FLAT (``flat_state``) cold single-eval, traced with
    ``PROCESS_ARCH_PASS_TRACE`` (+ ``FULL_FROM=1``): the flat cold-control
    trace, the reference exit snapshot (warm base), and the converged
    burn-time hex (the pin value on ``large_tokamak_nof``).
``gates``
    G1 trace-inertness (verified cold chain traced vs untraced, four exact
    fields, comparator teeth) and G2 entry-restore fidelity on
    ``large_tokamak_nof`` (relaunch from own exit snapshot; doctored-
    snapshot tooth).  A FAIL stops the dependent stages and is the result.
``trace``
    The core measurement: per deck x {cold, displaced-warm (delta = 0.10,
    seed 1)}, the A1' block chain with the VERIFIED outer (trust emits no
    outer-test records), traced with the full census from pass 1.
``restarts``
    The candidate-(d) discriminator: chained trust-mode runs from the cold
    entry, each a fresh subprocess re-entered at the previous exit
    snapshot (T1 -> Y1, T2(Y1) -> Y2, ...), chain length = the traced
    verified run's own outer-pass count.
``flatctl``
    The flat-arm symmetry control from the displaced-warm entry (the cold
    flat control is the refs run).
``analyze``
    No PROCESS runs.  Mover classification (block ownership, dynamic
    writer authority, earliest-block attribution, view-reconstruction),
    the chain/restart bit-identity checks with their doctored-input teeth
    (G3), the pin-gate reconciliation cross-residuals (G4), the flat
    symmetry census, and the static-export reader join on
    ``st_regression`` (frozen export, read-only, sha recorded).

Discipline: every PROCESS run is a fresh subprocess in its own working
directory with ``PYTHONPATH`` pinned to THIS worktree and the exact tree
asserted in-process (traps T6/T10); at most ONE PROCESS subprocess exists
at any time (the V2 campaign owns the machine's workers -- everything here
is serial by construction); every published quantity is a count, a name or
a bit-exact hex float; wall clock is progress information, never evidence
(trap T5).  a26-generation ystate + writeset artifacts everywhere (driver
predicate, perturbation spec and exit audit are the same artifact per
deck, so exit snapshots chain into ``--entry-state`` under the sha check).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
TREE = HERE.parent.parent
DATA = TREE / "arch_surgery" / "docs" / "data"
RUNS = HERE / "runs" / "a35"

sys.path.insert(0, str(HERE))
from a34_instruments import _cross_residual, load_spec_offline  # noqa: E402
from run_a28 import TAU, env_for  # noqa: E402
from v2_eval_one import perturb_factor  # noqa: E402

#: The main checkout: the frozen static export lives there and is read,
#: never written (its runs/ belong to the executing V2 campaign).
MAIN = Path("/home/wrutten/projects/PROCESS_surgery")
ST_DSM_EXPORT = (
    MAIN / "arch_surgery/idf_probe/runs/dsm_exports/st_regression"
    / "process_dependencies.json"
)

DECKS = ("large_tokamak_nof", "st_regression")
PULSED = {"large_tokamak_nof"}
DELTA = 0.10
#: Pre-declared displaced-entry seed; fallback used ONLY if the seed-1 run
#: crashes, and the substitution is reported (plan section 8).
SEED = 1
FALLBACK_SEED = 2
PIN_COMPONENT = "times.t_plant_pulse_burn"
BLOCK_ORDER = ("M1", "M2", "PULSE", "M3", "FF")
BLOCK_INDEX = {b: i for i, b in enumerate(BLOCK_ORDER)}

#: The known mover for the G3 tooth (iii): A34 pin_gate's top mover on the
#: cold large_tokamak_nof entry.  A trace without it is broken, not a
#: discovery (plan section 6).
KNOWN_MOVER = "build.dz_tf_upper_lower_midplane"

#: Environment variables this task sets per stage -- popped from every run
#: first, so an inherited value never leaks into a run that did not mean
#: to set it (the a34 discipline).
CLEARED = (
    "PROCESS_ARCH_OUTER",
    "PROCESS_ARCH_PIN_BURN_TIME",
    "PROCESS_ARCH_PASS_TRACE",
    "PROCESS_ARCH_PASS_TRACE_FULL_FROM",
)


def a26_ystate(scn: str) -> Path:
    return DATA / f"ystate_a26_{scn}.json"


def a26_writeset(scn: str) -> Path:
    return DATA / f"writeset_a26_{scn}.json"


def deck_path(scn: str) -> Path:
    """The ORIGINAL frozen deck, both arms: pin chains refuse the derived
    lifted deck (ixc 178) by design -- two owners (A34 decision (d))."""
    return HERE / "scenarios" / f"{scn}.IN.DAT"


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


# --------------------------------------------------------------------------
# one isolated single-eval run (serial; ONE subprocess at a time)
# --------------------------------------------------------------------------


def env_a35(scn: str, arm: str, *, outer: str | None = None,
            pin_hex: str | None = None, trace_path: Path | None = None,
            ) -> dict:
    """One arm's environment: run_a28's composition (cleared-first), the
    a26 driver artifacts substituted, this task's switches added."""
    env = env_for(scn, arm, RUNS, TAU, None)
    for k in CLEARED:
        env.pop(k, None)
    env["PROCESS_ARCH_YSTATE"] = str(a26_ystate(scn))
    env["PROCESS_ARCH_WRITESET"] = str(a26_writeset(scn))
    if outer is not None:
        env["PROCESS_ARCH_OUTER"] = outer
    if pin_hex is not None:
        env["PROCESS_ARCH_PIN_BURN_TIME"] = pin_hex
    if trace_path is not None:
        env["PROCESS_ARCH_PASS_TRACE"] = str(trace_path)
        # Full above-tau census from pass 1: the view-reconstruction rule
        # (plan section 5) needs the pass-1 deltas.
        env["PROCESS_ARCH_PASS_TRACE_FULL_FROM"] = "1"
    return env


def run_eval(scn: str, arm: str, outdir: Path, *,
             entry_state: Path | None = None, delta: float | None = None,
             seed: int = 0, outer: str | None = None,
             pin_hex: str | None = None, trace: bool = False,
             reuse: bool = True, timeout: int = 3600) -> dict:
    """One ``v2_eval_one.py`` run, fresh subprocess, own directory.

    ``reuse=True`` returns an existing completed record instead of
    re-running (stage composition: the gates stage produces the traced
    verified cold run in its canonical ``trace/`` location and the trace
    stage reuses it).  Deleting ``runs/a35`` regenerates everything.
    """
    mpath = outdir / "metrics.json"
    if reuse and mpath.exists():
        rec = json.loads(mpath.read_text())
        print(f"  [reused] {outdir.relative_to(RUNS)} "
              f"status={rec.get('status')}")
        return {"rc": 0 if rec.get("status") == "ok" else 1,
                "outdir": str(outdir), "metrics": rec, "reused": True}
    if outdir.exists():
        shutil.rmtree(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    spec = a26_ystate(scn)
    cmd = [
        sys.executable, str(HERE / "v2_eval_one.py"),
        "--scenario", scn,
        "--input", str(deck_path(scn)),
        "--outdir", str(outdir),
        "--expect-tree", str(TREE),
        "--perturb-spec", str(spec),
        "--exit-audit", str(spec),
        "--seed", str(seed),
        "--node-census",
    ]
    if delta is not None:
        cmd += ["--delta", repr(delta)]
    if entry_state is not None:
        cmd += ["--entry-state", str(entry_state)]
    env = env_a35(scn, arm, outer=outer, pin_hex=pin_hex,
                  trace_path=(outdir / "pass_trace.jsonl") if trace else None)
    t0 = time.perf_counter()
    try:
        proc = subprocess.run(cmd, env=env, capture_output=True, text=True,
                              cwd=str(outdir), timeout=timeout)
        rc, out, err = proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        rc, out, err = 124, exc.stdout or "", (exc.stderr or "") + "\nTIMEOUT"
    (outdir / "stdout.log").write_text(out)
    (outdir / "stderr.log").write_text(err)
    print(f"  rc={rc} {time.perf_counter() - t0:6.1f}s -> "
          f"{outdir.relative_to(RUNS)} (wall clock is progress "
          f"information, not a measurement)", flush=True)
    metrics = json.loads(mpath.read_text()) if mpath.exists() else {
        "status": "no_metrics", "returncode": rc,
    }
    return {"rc": rc, "outdir": str(outdir), "metrics": metrics,
            "reused": False}


# --------------------------------------------------------------------------
# stage: refs
# --------------------------------------------------------------------------


def refs_dir(scn: str) -> Path:
    return RUNS / "refs" / f"{scn}_flat_cold"


def stage_refs() -> int:
    """Per deck: one FLAT cold single-eval, traced (the flat cold control
    AND the reference exit snapshot AND the pin source)."""
    rc = 0
    for scn in DECKS:
        print(f"refs: {scn} FLAT cold (traced)", flush=True)
        r = run_eval(scn, "A0p", refs_dir(scn), trace=True)
        m = r["metrics"]
        if r["rc"] != 0 or m.get("status") != "ok":
            print(f"  FAILURE PATH: FLAT cold on {scn} did not complete "
                  f"(status {m.get('status')}); dependent stages for this "
                  f"deck will refuse")
            rc = 1
    return rc


def _ref_metrics(scn: str) -> dict:
    p = refs_dir(scn) / "metrics.json"
    if not p.exists():
        raise SystemExit(f"refs stage has not produced {p}; run 'refs' first")
    m = json.loads(p.read_text())
    if m.get("status") != "ok":
        raise SystemExit(
            f"reference FLAT run on {scn} has status {m.get('status')!r}: "
            f"the deck's cell is not measured (pre-declared failure path)"
        )
    return m


def _pin_hex(scn: str, *, displaced_seed: int | None = None,
             delta: float = DELTA) -> str | None:
    """The pin value: the flat-converged burn time (cold), or that value
    times the displaced component's own stream factor (warm displaced) --
    bit-identical to what the in-run perturbation computes."""
    if scn not in PULSED:
        return None
    burn = float.fromhex(_ref_metrics(scn)["t_plant_pulse_burn_hex"])
    if displaced_seed is not None:
        burn = burn * perturb_factor(displaced_seed, PIN_COMPONENT, delta)
    return float(burn).hex()


# --------------------------------------------------------------------------
# stage: gates (G1 trace-inertness, G2 entry-restore fidelity)
# --------------------------------------------------------------------------


def trace_dir(scn: str, entry: str) -> Path:
    return RUNS / "trace" / f"{scn}_{entry}"


G1_FIELDS = ("node_calls_single_eval", "outer_passes",
             "exit_audit_residual_max_hex", "objf_hex")


def _g1_extract(m: dict) -> dict:
    return {
        "node_calls_single_eval": m.get("node_calls_single_eval"),
        "outer_passes": (m.get("module_solve_stats") or {}).get(
            "outer_passes"),
        "exit_audit_residual_max_hex": (m.get("exit_audit") or {}).get(
            "residual_max_hex"),
        "objf_hex": (m.get("exact") or {}).get("objf"),
    }


def _g1_compare(a: dict, b: dict) -> dict:
    per = {f: {"traced": a[f], "untraced": b[f], "match": a[f] == b[f]}
           for f in G1_FIELDS}
    return {"fields_compared": len(G1_FIELDS),
            "fields_matching": sum(1 for v in per.values() if v["match"]),
            "pass": all(v["match"] for v in per.values()),
            "per_field": per}


def _g1_teeth(a: dict, b: dict) -> dict:
    trials = {}
    p = dict(a)
    p["node_calls_single_eval"] = (p["node_calls_single_eval"] or 0) + 1
    trials["node_calls+1"] = not _g1_compare(p, b)["pass"]
    p = dict(a)
    p["outer_passes"] = (p["outer_passes"] or 0) + 1
    trials["outer_passes+1"] = not _g1_compare(p, b)["pass"]
    for f in ("exit_audit_residual_max_hex", "objf_hex"):
        p = dict(a)
        if p[f] is None:
            trials[f + "+1ulp"] = False  # a None field cannot bite
            continue
        v = float.fromhex(p[f])
        p[f] = math.nextafter(v, math.inf).hex()
        trials[f + "+1ulp"] = not _g1_compare(p, b)["pass"]
    return {"n_perturbations": len(trials),
            "n_tripped": sum(1 for v in trials.values() if v),
            "all_tripped": all(trials.values()),
            "per_perturbation": trials}


def stage_gates() -> int:
    root = RUNS / "gates"
    root.mkdir(parents=True, exist_ok=True)
    verdicts = {}

    # ---- G1: trace-inertness --------------------------------------------
    scn = "large_tokamak_nof"
    pin = _pin_hex(scn)
    print("gates/G1: verified cold chain traced (canonical trace/ "
          "location) vs untraced twin", flush=True)
    traced = run_eval(scn, "A1p", trace_dir(scn, "cold"), pin_hex=pin,
                      trace=True)
    untraced = run_eval(scn, "A1p", root / "g1_untraced_nof_cold",
                        pin_hex=pin, trace=False)
    ok = (traced["rc"] == 0 and untraced["rc"] == 0
          and traced["metrics"].get("status") == "ok"
          and untraced["metrics"].get("status") == "ok")
    if ok:
        a = _g1_extract(traced["metrics"])
        b = _g1_extract(untraced["metrics"])
        cmpres = _g1_compare(a, b)
        teeth = _g1_teeth(a, b)
        g1 = {"gate": "G1 trace-inertness", "comparison": cmpres,
              "teeth": teeth,
              "verdict": ("PASS" if cmpres["pass"] and teeth["all_tripped"]
                          else "FAIL")}
    else:
        g1 = {"gate": "G1 trace-inertness", "verdict": "FAIL",
              "failed_at": "a run did not complete",
              "traced_status": traced["metrics"].get("status"),
              "untraced_status": untraced["metrics"].get("status")}
    verdicts["G1"] = g1
    print(f"  G1: {g1['verdict']}")

    # ---- G2: entry-restore fidelity on large_tokamak_nof ----------------
    print("gates/G2: FLAT relaunched from its own exit snapshot "
          "(+ doctored-snapshot tooth)", flush=True)
    ref_m = _ref_metrics(scn)
    ref_audit = float.fromhex(
        (ref_m.get("exit_audit") or {})["residual_max_hex"])
    snap_path = refs_dir(scn) / "y_exit.json"
    warm = run_eval(scn, "A0p", root / "g2_warm_reentry",
                    entry_state=snap_path)
    wm = warm["metrics"]
    entry = wm.get("entry_state") or {}
    stats = wm.get("module_solve_stats") or {}
    audit_hex = (wm.get("exit_audit") or {}).get("residual_max_hex")
    binding = {
        "readback_bitexact": entry.get("readback_bitexact") is True,
        "n_skipped_repr_zero": entry.get("n_skipped_repr") == 0,
        "block_sweeps_1": stats.get("block_sweeps") == 1,
        "audit_le_reference": (
            audit_hex is not None
            and float.fromhex(audit_hex) <= ref_audit
        ),
    }

    # the tooth: one continuous, non-zero, scalar component outside
    # spec_keys_owned_by_x, multiplied by 1.5 -- must produce a NONZERO
    # audit AND more than one sweep (A36's binding form: re-convergence
    # can tighten an audit, it cannot fake 1-sweep cost).
    snap = json.loads(snap_path.read_text())
    spec_rec = json.loads(a26_ystate(scn).read_text())
    owned = set(ref_m.get("spec_keys_owned_by_x") or [])
    prefer = "superconducting_tfcoil.a_tf_plasma_case"
    doctor_key = None
    cats = {c["key"]: c["category"] for c in spec_rec["components"]}
    candidates = ([prefer] if prefer in snap["state"] else []) + [
        c["key"] for c in spec_rec["components"]
    ]
    for key in candidates:
        rec = snap["state"].get(key)
        if (rec and rec.get("k") == "f" and cats.get(key) == "continuous"
                and key not in owned):
            v = float.fromhex(rec["hex"])
            if v != 0.0 and math.isfinite(v):
                doctor_key = key
                break
    if doctor_key is None:
        raise SystemExit(
            "G2 tooth: no continuous non-zero scalar component outside "
            "spec_keys_owned_by_x found in the reference snapshot -- the "
            "tooth cannot bite and the gate cannot be trusted; stopping "
            "(pre-declared failure path, plan section 8)"
        )
    doctored = json.loads(snap_path.read_text())
    dv = float.fromhex(doctored["state"][doctor_key]["hex"]) * 1.5
    doctored["state"][doctor_key]["hex"] = float(dv).hex()
    dpath = root / "g2_doctored_snapshot.json"
    dpath.write_text(json.dumps(doctored))
    tooth = run_eval(scn, "A0p", root / "g2_doctored_reentry",
                     entry_state=dpath)
    tm = tooth["metrics"]
    t_audit = ((tm.get("exit_audit") or {}).get("residual_max_hex"))
    t_sweeps = (tm.get("module_solve_stats") or {}).get("block_sweeps")
    teeth_ok = (t_audit is not None and float.fromhex(t_audit) != 0.0
                and (t_sweeps or 0) > 1)
    g2 = {
        "gate": "G2 entry-restore fidelity (large_tokamak_nof)",
        "binding": binding,
        "warm_reentry": {
            "block_sweeps": stats.get("block_sweeps"),
            "node_calls": wm.get("node_calls_single_eval"),
            "audit_hex": audit_hex,
            "reference_audit_hex": (ref_m.get("exit_audit") or {}).get(
                "residual_max_hex"),
            "entry_state": entry,
        },
        "tooth": {
            "doctored_component": doctor_key,
            "factor": 1.5,
            "audit_hex": t_audit,
            "block_sweeps": t_sweeps,
            "tripped": teeth_ok,
        },
        "verdict": ("PASS" if all(binding.values()) and teeth_ok
                    else "FAIL"),
    }
    verdicts["G2"] = g2
    print(f"  G2: {g2['verdict']} (binding {binding}, tooth "
          f"tripped={teeth_ok})")

    (root / "gates.json").write_text(json.dumps(verdicts, indent=2))
    ok = all(v["verdict"] == "PASS" for v in verdicts.values())
    print(f"gates: {'PASS' if ok else 'FAIL'} -> {root / 'gates.json'}")
    return 0 if ok else 1


# --------------------------------------------------------------------------
# stage: trace (the core measurement)
# --------------------------------------------------------------------------


def stage_trace() -> int:
    rc = 0
    for scn in DECKS:
        ref_snap = refs_dir(scn) / "y_exit.json"
        # cold
        print(f"trace: {scn} verified cold", flush=True)
        r = run_eval(scn, "A1p", trace_dir(scn, "cold"),
                     pin_hex=_pin_hex(scn), trace=True)
        rc = rc or (0 if r["metrics"].get("status") == "ok" else 1)
        # displaced warm (seed 1; fallback seed 2 only on a crash,
        # reported -- plan section 8)
        for seed in (SEED, FALLBACK_SEED):
            print(f"trace: {scn} verified warm-displaced delta={DELTA} "
                  f"seed={seed}", flush=True)
            r = run_eval(scn, "A1p", trace_dir(scn, f"warm_seed{seed}"),
                         entry_state=ref_snap, delta=DELTA, seed=seed,
                         pin_hex=_pin_hex(scn, displaced_seed=seed),
                         trace=True)
            st = r["metrics"].get("status")
            if st == "crashed":
                print(f"  FAILURE PATH: seed {seed} crashed; "
                      f"{'falling back once' if seed == SEED else 'no further fallback'}")
                continue
            break
        rc = rc or (0 if st in ("ok", "unconverged") else 1)
        # plan section 2a (user-directed, 2026-09-04): the delta-scaling
        # sub-discriminator's third displacement point -- delta = 0.05,
        # same seed, same stream (state-carried staleness scales ~2x
        # between the warm runs; seed-type staleness does not scale).
        print(f"trace: {scn} verified warm-displaced delta=0.05 "
              f"seed={SEED}", flush=True)
        r = run_eval(scn, "A1p", trace_dir(scn, f"warm_d05_seed{SEED}"),
                     entry_state=ref_snap, delta=0.05, seed=SEED,
                     pin_hex=_pin_hex(scn, displaced_seed=SEED,
                                      delta=0.05),
                     trace=True)
        rc = rc or (0 if r["metrics"].get("status") in ("ok", "unconverged")
                    else 1)
    return rc


# --------------------------------------------------------------------------
# stage: restarts (the candidate-(d) discriminator)
# --------------------------------------------------------------------------


def restarts_dir(scn: str, i: int) -> Path:
    return RUNS / "restarts" / f"{scn}_T{i}"


def stage_restarts() -> int:
    rc = 0
    for scn in DECKS:
        vm_path = trace_dir(scn, "cold") / "metrics.json"
        if not vm_path.exists():
            print(f"restarts: no traced verified cold run for {scn}; run "
                  f"'trace' first")
            rc = 1
            continue
        vm = json.loads(vm_path.read_text())
        k = ((vm.get("module_solve_stats") or {}).get("outer_passes"))
        if not k:
            print(f"restarts: verified cold run on {scn} has no outer-pass "
                  f"count (status {vm.get('status')}); cell not measured")
            rc = 1
            continue
        k = min(int(k), 5)
        pin = _pin_hex(scn)
        entry = None
        print(f"restarts: {scn} trust chain T1..T{k} (verified needed "
              f"{k} outer passes)", flush=True)
        for i in range(1, k + 1):
            r = run_eval(scn, "A1p", restarts_dir(scn, i),
                         entry_state=entry, outer="trust", pin_hex=pin)
            if r["metrics"].get("status") != "ok":
                print(f"  FAILURE PATH: T{i} on {scn} status "
                      f"{r['metrics'].get('status')}; chain stops here")
                rc = 1
                break
            entry = restarts_dir(scn, i) / "y_exit.json"
    return rc


# --------------------------------------------------------------------------
# stage: flatctl (flat symmetry control from the displaced entry)
# --------------------------------------------------------------------------


def flatctl_dir(scn: str, seed: int) -> Path:
    return RUNS / "flatctl" / f"{scn}_warm_seed{seed}"


def stage_flatctl() -> int:
    rc = 0
    for scn in DECKS:
        # use whichever displaced seed the trace stage measured
        seed = None
        for s in (SEED, FALLBACK_SEED):
            if (trace_dir(scn, f"warm_seed{s}") / "metrics.json").exists():
                seed = s
                break
        if seed is None:
            print(f"flatctl: no displaced traced run for {scn}; run "
                  f"'trace' first")
            rc = 1
            continue
        print(f"flatctl: {scn} FLAT warm-displaced seed={seed} (traced)",
              flush=True)
        r = run_eval(scn, "A0p", flatctl_dir(scn, seed),
                     entry_state=refs_dir(scn) / "y_exit.json",
                     delta=DELTA, seed=seed, trace=True)
        rc = rc or (0 if r["metrics"].get("status") == "ok" else 1)
    return rc


# --------------------------------------------------------------------------
# analysis helpers
# --------------------------------------------------------------------------


def load_trace(path: Path) -> list[dict]:
    out = []
    with path.open() as fh:
        for line in fh:
            out.append(json.loads(line))
    return out


def load_state(path: Path) -> dict:
    """y_exit/y_entry snapshot -> {component name: value record}."""
    rec = json.loads(path.read_text())
    return rec["state"]


def state_elem_hex(state: dict, key: str, elem: int | None) -> str | None:
    """The hex of one component (element ``elem`` of a float array, or the
    scalar).  None when the component is not float-valued in the snapshot
    -- reported by the caller, never silently equal."""
    rec = state.get(key)
    if rec is None:
        return None
    if rec["k"] == "f":
        return rec["hex"]
    if rec["k"] == "af":
        j = elem or 0
        if j < len(rec["hex"]):
            return rec["hex"][j]
    if rec["k"] == "l":
        j = elem or 0
        if j < len(rec["v"]) and rec["v"][j].get("k") == "f":
            return rec["v"][j]["hex"]
    return None


def trace_movers(rec: dict) -> list[dict]:
    """Every fully-recorded mover of one joint-test record (continuous
    above-tau + discrete mismatches; the a26 spec has no constants)."""
    out = list(rec.get("above") or [])
    out += list(rec.get("discrete_mismatch_detail") or [])
    out += list(rec.get("moved_constant_detail") or [])
    return out


class Joins:
    """The committed classification data for one deck."""

    def __init__(self, scn: str, metrics: dict):
        ws = json.loads(a26_writeset(scn).read_text())
        self.comp_block: dict[str, str] = {}
        for mod, keys in ws["subsets"].items():
            for k in keys:
                # V11: a partition -- assert rather than assume
                if k in self.comp_block:
                    raise RuntimeError(
                        f"{k} in two module subsets ({self.comp_block[k]}, "
                        f"{mod}): V11's partition property is violated -- "
                        f"a finding, not a classification input")
                self.comp_block[k] = mod
        nw = json.loads((DATA / "node_writesets.json").read_text())
        wbn = nw["per_scenario"][scn]["writes_by_node"]
        self.writers: dict[str, list] = defaultdict(list)
        for node, keys in wbn.items():
            for k in keys:
                self.writers[k].append(node)
        self.node_block: dict[str, str] = {}
        for lab, nodes, _it in metrics.get("arch_block_schedule") or []:
            for n in nodes:
                self.node_block[n] = lab
        for n in (metrics.get("module_solve_stats") or {}).get(
                "hoisted_tail") or []:
            self.node_block[n] = "TAIL"

    def mover_row(self, mv: dict) -> dict:
        key = mv["key"]
        wr = self.writers.get(key, [])
        wblocks = sorted({self.node_block.get(n, f"?{n}") for n in wr})
        return {
            "key": key,
            "category": mv.get("category"),
            "scaled": mv.get("scaled"),
            "before_hex": mv.get("before_hex"),
            "after_hex": mv.get("after_hex"),
            "elem": mv.get("elem"),
            "owner_block": self.comp_block.get(key),
            "writer_nodes": wr,
            "writer_blocks": wblocks,
        }


def _passes(records: list[dict], kind: str) -> dict[int, dict]:
    return {r["pass"]: r for r in records if r.get("kind") == kind}


def chain_check(movers_by_pass: dict[int, list[dict]],
                y_of_pass: dict[int, dict]) -> dict:
    """G3 check (i): every pass-p mover's before_hex must equal the
    chained trust exit Y_{p-1}; its after_hex must equal Y_p (the restart
    identity).  Returns both verdicts with every mismatch named."""
    before_mismatch, after_mismatch, unverifiable = [], [], []
    n_before = n_after = 0
    for p, movers in movers_by_pass.items():
        yb = y_of_pass.get(p - 1)
        ya = y_of_pass.get(p)
        for mv in movers:
            key, elem = mv["key"], mv.get("elem")
            if mv.get("before_hex") is None:
                unverifiable.append({"pass": p, "key": key,
                                     "why": "no before/after in record"})
                continue
            if yb is not None:
                got = state_elem_hex(yb, key, elem)
                n_before += 1
                if got != mv["before_hex"]:
                    before_mismatch.append({
                        "pass": p, "key": key, "elem": elem,
                        "trace_before_hex": mv["before_hex"],
                        "snapshot_hex": got,
                    })
            if ya is not None:
                got = state_elem_hex(ya, key, elem)
                n_after += 1
                if got != mv["after_hex"]:
                    after_mismatch.append({
                        "pass": p, "key": key, "elem": elem,
                        "trace_after_hex": mv["after_hex"],
                        "snapshot_hex": got,
                    })
    return {
        "n_before_compared": n_before,
        "n_after_compared": n_after,
        "before_mismatches": before_mismatch,
        "after_mismatches": after_mismatch,
        "unverifiable": unverifiable,
        "before_ok": not before_mismatch,
        "after_ok": not after_mismatch,
    }


def full_state_compare(a: dict, b: dict) -> dict:
    keys = set(a) | set(b)
    diffs = [k for k in sorted(keys) if a.get(k) != b.get(k)]
    return {"n_components": len(keys), "n_differing": len(diffs),
            "differing_first_20": diffs[:20]}


def scaled_recompute_check(movers_by_pass: dict[int, list[dict]]) -> dict:
    """G3 check (ii): |after-before|/scale must reproduce the recorded
    scaled residual for every fully-recorded scalar mover (exact float64
    arithmetic; a tolerance of 0)."""
    n = bad = 0
    examples = []
    for p, movers in movers_by_pass.items():
        for mv in movers:
            if (mv.get("scaled") is None or mv.get("before_hex") is None
                    or mv.get("elem") is not None):
                continue  # arrays: the max may sit on another element
            n += 1
            rec = abs(float.fromhex(mv["after_hex"])
                      - float.fromhex(mv["before_hex"])) / mv["scale"]
            if rec != mv["scaled"]:
                bad += 1
                if len(examples) < 5:
                    examples.append({"pass": p, "key": mv["key"],
                                     "recorded": mv["scaled"],
                                     "recomputed": rec})
    return {"n_checked": n, "n_mismatch": bad, "ok": bad == 0,
            "examples": examples}


# ---- static export join (st_regression only; frozen copy, read-only) -----


def st_static_maps() -> dict | None:
    """Reader/writer maps from the frozen per-deck export, via A31's
    loader (its supermodel-order map is st_regression-specific and
    file-checked).  None (reported) when the export is absent."""
    if not ST_DSM_EXPORT.exists():
        return None
    import a31_drift_probe as a31
    return a31._load_static_maps()


# --------------------------------------------------------------------------
# stage: analyze
# --------------------------------------------------------------------------


def analyze_deck(scn: str, entry: str, run_dir: Path,
                 y_chain: dict[int, dict] | None,
                 static_maps: dict | None) -> dict:
    """Classify every pass >= 2 mover of one traced verified run."""
    m = json.loads((run_dir / "metrics.json").read_text())
    records = load_trace(run_dir / "pass_trace.jsonl")
    outer = _passes(records, "outer")
    joins = Joins(scn, m)

    movers_by_pass: dict[int, list[dict]] = {}
    rows_by_pass: dict[int, list[dict]] = {}
    for p, rec in sorted(outer.items()):
        if p < 2:
            continue
        movers = trace_movers(rec)
        if movers:
            movers_by_pass[p] = movers
            rows_by_pass[p] = [joins.mover_row(mv) for mv in movers]

    # earliest-block attribution + view reconstruction (plan section 5)
    pass1 = outer.get(1) or {}
    pass1_movers = trace_movers(pass1)
    pass1_keys_by_block: dict[str, list[str]] = defaultdict(list)
    for mv in pass1_movers:
        pass1_keys_by_block[
            joins.comp_block.get(mv["key"], "?")].append(mv["key"])

    attribution = {}
    for p, rows in rows_by_pass.items():
        wblocks = [b for r in rows for b in r["writer_blocks"]
                   if b in BLOCK_INDEX]
        if not wblocks:
            attribution[str(p)] = {"note": "no mover with an in-schedule "
                                   "writer block"}
            continue
        bmin = min(wblocks, key=lambda b: BLOCK_INDEX[b])
        bmin_rows = [r for r in rows if bmin in r["writer_blocks"]]
        later = [b for b in BLOCK_ORDER
                 if BLOCK_INDEX[b] > BLOCK_INDEX[bmin]]
        # candidate carriers: components owned by LATER blocks that moved
        # in the PREVIOUS pass (what b_min's view gained between its two
        # executions); for p = 2 that is the pass-1 census.
        prev = outer.get(p - 1) or {}
        prev_movers = trace_movers(prev)
        candidates = sorted({
            mv["key"] for mv in prev_movers
            if joins.comp_block.get(mv["key"]) in later
        })
        own_prev = sorted({
            mv["key"] for mv in prev_movers
            if joins.comp_block.get(mv["key"]) == bmin
        })
        entry_rec = {
            "earliest_block": bmin,
            "n_movers_at_earliest_block": len(bmin_rows),
            "earliest_block_movers_top": sorted(
                bmin_rows, key=lambda r: -(r["scaled"] or 0))[:10],
            "carrier_candidates_later_block_prev_pass_movers": candidates,
            "own_block_prev_pass_movers_n": len(own_prev),
        }
        # reader evidence, st_regression only: which candidates are read
        # (per the frozen export) by the earliest-block movers' writers
        if static_maps is not None:
            wr_nodes = sorted({n for r in bmin_rows
                               for n in r["writer_nodes"]})
            readers = static_maps["readers"]
            read_by_writer = {}
            for v in candidates:
                rd = set(readers.get(v, ()))
                hit = sorted(rd & set(wr_nodes))
                if hit:
                    read_by_writer[v] = hit
            entry_rec["export_confirmed_reads_of_candidates"] = (
                read_by_writer)
            entry_rec["export_sha256"] = static_maps["export_sha256"]
        attribution[str(p)] = entry_rec

    # chain / restart identity (cold entries only, where the chain ran)
    identity = None
    if y_chain:
        identity = chain_check(movers_by_pass, y_chain)
        k = (m.get("module_solve_stats") or {}).get("outer_passes")
        if k and k in y_chain:
            ver_exit = load_state(run_dir / "y_exit.json")
            identity["full_state_Yk_vs_verified_exit"] = full_state_compare(
                y_chain[k], ver_exit)

    return {
        "run_dir": str(run_dir),
        "status": m.get("status"),
        "outer_passes": (m.get("module_solve_stats") or {}).get(
            "outer_passes"),
        "outer_max_by_pass": {
            str(p): {"max": r.get("max"), "max_hex": r.get("max_hex"),
                     "n_above": r.get("n_above"),
                     "argmax": (r.get("argmax") or {}).get("key")}
            for p, r in sorted(outer.items())
        },
        "movers_by_pass": {str(p): rows for p, rows in rows_by_pass.items()},
        "attribution": attribution,
        "scaled_recompute": scaled_recompute_check(movers_by_pass),
        "identity": identity,
        "pin": {"enabled": m.get("arch_pin_enabled"),
                "intact": m.get("pin_intact_at_exit"),
                "hex": m.get("arch_pin_burn_time_hex")},
    }


def analyze_flat(scn: str, run_dir: Path,
                 block_pass2_keys: set[str]) -> dict:
    """Flat symmetry: per-sweep movement census + overlap with the block
    arm's pass-2 mover set."""
    if not (run_dir / "pass_trace.jsonl").exists():
        return {"missing": str(run_dir)}
    records = load_trace(run_dir / "pass_trace.jsonl")
    sweeps = _passes(records, "flat_inner")
    per_sweep = {}
    union: set[str] = set()
    for s, rec in sorted(sweeps.items()):
        keys = {mv["key"] for mv in trace_movers(rec)}
        if s >= 2:
            union |= keys
        per_sweep[str(s)] = {
            "max": rec.get("max"), "max_hex": rec.get("max_hex"),
            "n_above": rec.get("n_above"),
            "argmax": (rec.get("argmax") or {}).get("key"),
        }
    overlap = sorted(block_pass2_keys & union)
    return {
        "run_dir": str(run_dir),
        "n_sweeps_traced": len(sweeps),
        "per_sweep": per_sweep,
        "block_pass2_movers": len(block_pass2_keys),
        "flat_sweep2plus_mover_union": len(union),
        "overlap_n": len(overlap),
        "overlap_fraction_of_block_movers": (
            len(overlap) / len(block_pass2_keys) if block_pass2_keys
            else None),
        "block_movers_absent_from_flat": sorted(
            block_pass2_keys - union)[:20],
    }


def _analyze_teeth(scn: str, run_dir: Path,
                   y_chain: dict[int, dict]) -> dict:
    """G3 teeth: a doctored trace line and a doctored snapshot must each
    be CAUGHT by the chain check (plan section 6)."""
    records = load_trace(run_dir / "pass_trace.jsonl")
    outer = _passes(records, "outer")
    movers2 = trace_movers(outer.get(2) or {})
    target = next((mv for mv in movers2
                   if mv.get("before_hex") is not None), None)
    if target is None or 1 not in y_chain:
        return {"skipped": "no pass-2 mover with hex detail, or no Y1"}
    # tooth A: flip the trace's before_hex by one ULP
    doct = json.loads(json.dumps(target))
    v = float.fromhex(doct["before_hex"])
    doct["before_hex"] = math.nextafter(v, math.inf).hex()
    res_a = chain_check({2: [doct]}, y_chain)
    # tooth B: doctor the snapshot instead
    y1d = json.loads(json.dumps(y_chain[1]))
    rec = y1d[target["key"]]
    if rec["k"] == "f":
        rec["hex"] = math.nextafter(
            float.fromhex(rec["hex"]), math.inf).hex()
    elif rec["k"] == "af":
        j = target.get("elem") or 0
        rec["hex"][j] = math.nextafter(
            float.fromhex(rec["hex"][j]), math.inf).hex()
    res_b = chain_check({2: [target]}, {1: y1d, 2: y_chain.get(2)})
    return {
        "doctored_component": target["key"],
        "tooth_doctored_trace_caught": not res_a["before_ok"],
        "tooth_doctored_snapshot_caught": not res_b["before_ok"],
        "all_tripped": (not res_a["before_ok"]) and (not res_b["before_ok"]),
    }


def stage_analyze() -> int:
    out_root = RUNS / "analysis"
    out_root.mkdir(parents=True, exist_ok=True)
    static_maps = st_static_maps()
    summary: dict = {
        "tau": TAU,
        "artifact_generation": "a26 (driver predicate, perturbation spec "
                               "and exit audit are the same artifact per "
                               "deck)",
        "static_export": (
            {"path": str(ST_DSM_EXPORT),
             "sha256": static_maps["export_sha256"]}
            if static_maps else
            {"absent": str(ST_DSM_EXPORT),
             "note": "frozen st_regression export not present; the reader "
                     "join is skipped and reported as such"}),
        "decks": {},
    }
    rc = 0
    for scn in DECKS:
        deck_rec: dict = {}
        # chained trust exits Y1..Yk
        y_chain: dict[int, dict] = {}
        i = 1
        while (restarts_dir(scn, i) / "y_exit.json").exists():
            y_chain[i] = load_state(restarts_dir(scn, i) / "y_exit.json")
            i += 1
        deck_rec["restart_chain_length"] = len(y_chain)

        # traced verified runs
        for entry in (["cold"] + [f"warm_seed{s}" for s in (SEED,
                                                            FALLBACK_SEED)]
                      + [f"warm_d05_seed{SEED}"]):
            d = trace_dir(scn, entry)
            if not (d / "pass_trace.jsonl").exists():
                continue
            deck_rec[entry] = analyze_deck(
                scn, entry, d,
                y_chain if entry == "cold" else None,
                static_maps if scn == "st_regression" else None)

        # G3 teeth on the cold run (needs Y1)
        if "cold" in deck_rec and y_chain:
            deck_rec["g3_teeth"] = _analyze_teeth(
                scn, trace_dir(scn, "cold"), y_chain)

        # known-mover tooth (large_tokamak_nof cold; plan G3(iii))
        if scn == "large_tokamak_nof" and "cold" in deck_rec:
            keys = {r["key"]
                    for rows in deck_rec["cold"]["movers_by_pass"].values()
                    for r in rows}
            deck_rec["g3_known_mover_present"] = KNOWN_MOVER in keys

        # G4 reconciliation: cross-residuals vs the FLAT reference exit
        try:
            spec = load_spec_offline(a26_ystate(scn))
            from v2_eval_one import restore_snapshot as _restore
            y_flat = _restore(spec, json.loads(
                (refs_dir(scn) / "y_exit.json").read_text()))
            g4 = {}
            for label, d in (
                ("verified_cold", trace_dir(scn, "cold")),
                ("trust_T1", restarts_dir(scn, 1)),
            ):
                p = d / "y_exit.json"
                if p.exists():
                    y = _restore(spec, json.loads(p.read_text()))
                    g4[label + "_vs_flat"] = _cross_residual(
                        spec, y_flat, y, TAU)
            deck_rec["g4_cross_residuals"] = g4
        except Exception as exc:  # noqa: BLE001 - reported, not fatal
            deck_rec["g4_cross_residuals"] = {"error": repr(exc)}

        # plan section 2a: the lagged-edge census verdict and the
        # delta-scaling sub-discriminator (state-carried vs seed-type)
        scaled_at_2: dict[str, dict[str, float]] = defaultdict(dict)
        for entry in ("cold", f"warm_seed{SEED}", f"warm_seed{FALLBACK_SEED}",
                      f"warm_d05_seed{SEED}"):
            a = deck_rec.get(entry)
            if not a:
                continue
            for r in a["movers_by_pass"].get("2", []):
                if r.get("scaled") is not None:
                    scaled_at_2[r["key"]][entry] = r["scaled"]
        d10, d05 = f"warm_seed{SEED}", f"warm_d05_seed{SEED}"
        ratios = []
        rows = []
        for key, by in sorted(scaled_at_2.items()):
            row = {"key": key, **{e: by.get(e) for e in
                                  ("cold", d10, d05)}}
            if by.get(d10) and by.get(d05):
                row["ratio_d10_over_d05"] = by[d10] / by[d05]
                ratios.append(row["ratio_d10_over_d05"])
            rows.append(row)
        ratios.sort()
        deck_rec["delta_scaling_pass2"] = {
            "per_component": rows,
            "n_with_both_warm_points": len(ratios),
            "ratio_d10_over_d05_median": (
                ratios[len(ratios) // 2] if ratios else None),
            "ratio_d10_over_d05_q1_q3": (
                [ratios[len(ratios) // 4],
                 ratios[(3 * len(ratios)) // 4]] if ratios else None),
            "expectation": ("~2 for state-carried staleness (linear "
                            "regime); ~1 for a hard-coded-seed "
                            "first-evaluation error (plan section 2a)"),
        }

        # flat symmetry controls
        block2 = set()
        if "cold" in deck_rec:
            block2 = {r["key"] for r in deck_rec["cold"][
                "movers_by_pass"].get("2", [])}
        deck_rec["flat_symmetry_cold"] = analyze_flat(
            scn, refs_dir(scn), block2)
        for s in (SEED, FALLBACK_SEED):
            warm_key = f"warm_seed{s}"
            if warm_key in deck_rec:
                bw = {r["key"] for r in deck_rec[warm_key][
                    "movers_by_pass"].get("2", [])}
                deck_rec["flat_symmetry_warm"] = analyze_flat(
                    scn, flatctl_dir(scn, s), bw)
                break

        summary["decks"][scn] = deck_rec

    out = out_root / "summary.json"
    out.write_text(json.dumps(summary, indent=2))
    print(f"analysis written to {out}\n")

    # console digest
    for scn, dr in summary["decks"].items():
        print(f"=== {scn} ===")
        for entry in ("cold",) + tuple(
                f"warm_seed{s}" for s in (SEED, FALLBACK_SEED)) + (
                f"warm_d05_seed{SEED}",):
            if entry not in dr:
                continue
            a = dr[entry]
            print(f"  {entry}: outer_passes={a['outer_passes']} "
                  f"status={a['status']}")
            for p, mx in a["outer_max_by_pass"].items():
                print(f"    pass {p}: max={mx['max']:.3e} "
                      f"n_above={mx['n_above']} argmax={mx['argmax']}")
            for p, att in a["attribution"].items():
                if "earliest_block" in att:
                    print(f"    pass {p}: earliest block "
                          f"{att['earliest_block']} "
                          f"({att['n_movers_at_earliest_block']} movers); "
                          f"{len(att['carrier_candidates_later_block_prev_pass_movers'])} "
                          f"later-block candidates")
            if a.get("identity"):
                idn = a["identity"]
                print(f"    identity: before_ok={idn['before_ok']} "
                      f"after_ok={idn['after_ok']} "
                      f"(n={idn['n_before_compared']}/"
                      f"{idn['n_after_compared']})")
                fs = idn.get("full_state_Yk_vs_verified_exit")
                if fs:
                    print(f"    full-state Yk vs verified exit: "
                          f"{fs['n_differing']} differing of "
                          f"{fs['n_components']}")
        if "g3_teeth" in dr:
            print(f"  G3 teeth: {dr['g3_teeth']}")
        if "g3_known_mover_present" in dr:
            print(f"  G3 known mover ({KNOWN_MOVER}): "
                  f"{dr['g3_known_mover_present']}")
        print(f"  G4: { {k: v.get('max_hex') if isinstance(v, dict) else v for k, v in (dr.get('g4_cross_residuals') or {}).items()} }")
        ds = dr.get("delta_scaling_pass2") or {}
        if ds.get("n_with_both_warm_points"):
            print(f"  delta-scaling: median d10/d05 ratio "
                  f"{ds['ratio_d10_over_d05_median']:.3f} over "
                  f"{ds['n_with_both_warm_points']} movers "
                  f"(q1-q3 {ds['ratio_d10_over_d05_q1_q3']})")
        for k in ("flat_symmetry_cold", "flat_symmetry_warm"):
            f = dr.get(k) or {}
            if "overlap_n" in f:
                print(f"  {k}: overlap {f['overlap_n']}/"
                      f"{f['block_pass2_movers']} of block pass-2 movers "
                      f"seen in flat sweeps>=2")
    return rc


# --------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["refs", "gates", "trace", "restarts",
                                      "flatctl", "analyze", "all"])
    args = ap.parse_args()
    RUNS.mkdir(parents=True, exist_ok=True)
    (RUNS / "_mplconfig").mkdir(exist_ok=True)

    if args.stage == "refs":
        return stage_refs()
    if args.stage == "gates":
        return stage_gates()
    if args.stage == "trace":
        return stage_trace()
    if args.stage == "restarts":
        return stage_restarts()
    if args.stage == "flatctl":
        return stage_flatctl()
    if args.stage == "analyze":
        return stage_analyze()
    rc = stage_refs()
    if rc:
        return rc
    rc = stage_gates()
    if rc:
        # a failed gate stops the dependent stages and is the result
        return rc
    rc = stage_trace() or rc
    rc = stage_restarts() or rc
    rc = stage_flatctl() or rc
    return stage_analyze() or rc


if __name__ == "__main__":
    raise SystemExit(main())
