#!/usr/bin/env python
"""A34 (phase-a-instruments): the three remaining V2 instrument capabilities,
each env-switched, each a no-op when unset, each gated with teeth.

What this task builds (V2 plan Appendix A items 2/3; ``v2_config.py``
``INSTRUMENTATION`` entries ``trust_mode``, ``pin``, ``single_mda_eval``):

(i) **Trust mode** -- ``PROCESS_ARCH_OUTER=trust``: with
    ``PROCESS_ARCH_MODULE_SOLVE=per_module`` the block schedule runs exactly
    once (inner solves converge at their inner tau as now, feed-forward tail
    as now) and the outer joint predicate is never evaluated -- no outer
    pass 2, no verification receipt.  ``outer_pass_hist`` records ``{1: n}``.
    Driver change: ``process/core/solver/module_solve.py`` (env parse) and
    one guarded break in ``process/core/caller.py``.

(ii) **Pin instrument** -- ``PROCESS_ARCH_PIN_BURN_TIME=<float|hexfloat>``:
    the burn-time coupling held at the supplied value through a feed-forward
    block solve -- the lifted architecture's per-call structure without an
    optimiser.  Requires ``PROCESS_ARCH_LIFT=burn_time`` (the lift is what
    makes Pulse's write the identity); refuses a deck that names ixc 178
    (two owners); tripwired at the end of every sweep, value and fact of
    pinning stamped into metrics.  Driver change: ``subsolve.py`` +
    ``caller.py``.

(iii) **Single-MDA-eval mode** -- ``v2_eval_one.py`` (harness-side, beside
    ``run_one.py``): initialise the deck, optionally perturb the
    coupling-state initial values (seeded, keyed on component NAME from the
    a26 spec), run EXACTLY ONE ``call_models`` under the arm the environment
    selects, record the standard counts, take the uncharged exit audit,
    stop.  No optimiser anywhere in the process.

Stages (protocol 15: every published number comes from executing this
committed script; failure paths are reachable from the same entry point;
protocol 12: every gate's teeth are shown before its zeros are believed)
------------------------------------------------------------------------
``trust_gate``
    Switch-neutrality of everything this task added to the driver: with the
    new variables unset, the a26-spec ``A1'`` ``st_regression`` start000 run
    must reproduce A32's recorded start000 **bit-for-bit** on
    ``node_calls_solve_phase``, ``outer_pass_hist`` and ``norm_objf`` hex
    (the A31/A32 gate machinery, teeth included).
``trust_demo``
    The same configuration with ``PROCESS_ARCH_OUTER=trust``: must run to
    completion with ``outer_pass_hist`` all 1s (teeth on that check), and
    its ``norm_objf`` hex and uncharged exit-audit residual are reported
    BESIDE A32's -- differences reported, never judged (comparing arms at
    matched accuracy is V2's job, on V2's pre-declared rules).
``evalone_gate``
    The single-eval mode against the control: the FLAT arm's single eval at
    the UNPERTURBED ``st_regression`` deck point must agree with the first
    solve-phase call of A28's recorded control optimisation
    (``runs/a28/h5_audit1/st_regression/A0p/start000``) on the node-call
    count of that call, the audit's own node calls, the audit residual as
    an exact hex float, and the audit argmax component.  Teeth per field.
``perturb_demo``
    The perturbation stream's cross-arm identity, shown not assumed: the
    FLAT and BLOCKS+trust arms at the same (delta, seed) must record
    **bit-identical** per-component factors and before/after values
    (keyed on NAME -- the property Phase A's pairing rests on).  Also the
    first end-to-end run of the Phase-A BLOCKS chain (per_module + trust)
    on the one deck whose a26 artifacts are complete.
``pin_gate``
    The plan section-3 equivalence gate, on ``large_tokamak_nof``: the FLAT
    arm's single eval converges the MDA at the deck point; the
    BLOCKS+pin+trust chain, pinned at EXACTLY that run's converged burn
    time, must land on the same fixed point -- the cross-state residual
    between the two exit snapshots, measured by the audit instrument, at
    the audit's resolution.  Teeth: comparator perturbations that must
    trip.  **A18-generation artifacts** (the pulsed decks' a26 write sets
    are task A33's): this is a machinery gate, not a V2 measurement.
``pin_refusals``
    The pin's two refusal paths, demonstrated: pin without lift is an
    import-time error; pin on a deck that names ixc 178 (the derived lifted
    deck) is a Caller refusal.  Failure paths reachable, per protocol 15.
``all``
    Everything above, in order; the first failing stage's exit code stops
    the chain.

Isolation: every PROCESS run is a fresh subprocess in its own working
directory, ``PYTHONPATH`` pinned to this worktree, the EXACT tree asserted
in-process (traps T6/T10).  No conclusion rests on a timing.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TREE = HERE.parent.parent
DATA = TREE / "arch_surgery" / "docs" / "data"
RUNS = HERE / "runs" / "a34"

sys.path.insert(0, str(HERE))
from a31_drift_probe import gate_compare, gate_extract, gate_teeth  # noqa: E402
from run_a28 import TAU, deck_for, env_for  # noqa: E402
from v2_eval_one import restore_snapshot  # noqa: E402

#: The main checkout: reference records live there and are read, never
#: written.
MAIN = Path("/home/wrutten/projects/PROCESS_surgery")
A32_REF = (
    MAIN / "arch_surgery/idf_probe/runs/a32/campaign/A1p/start000/metrics.json"
)
A28_AUDIT1_REF = (
    MAIN
    / "arch_surgery/idf_probe/runs/a28/h5_audit1/st_regression/A0p/start000"
    / "metrics.json"
)

#: D15's calibrated perturbation size, exactly as A28/A32 ran it.
DELTA = 0.10

#: The new environment variables this task adds.  Popped from every run's
#: environment first and set only where a stage means to set them -- an
#: inherited switch would change what is measured without saying so.
NEW_VARS = ("PROCESS_ARCH_OUTER", "PROCESS_ARCH_PIN_BURN_TIME")

YSTATE_A18_ST = DATA / "ystate_st_regression.json"
YSTATE_A26_ST = DATA / "ystate_a26_st_regression.json"
WRITESET_A26_ST = DATA / "writeset_a26_st_regression.json"
YSTATE_A18_NOF = DATA / "ystate_large_tokamak_nof.json"
YSTATE_A26_NOF = DATA / "ystate_a26_large_tokamak_nof.json"


# --------------------------------------------------------------------------
# runners (fresh subprocess each, the A31/A32 recipe)
# --------------------------------------------------------------------------


def _env(scenario: str, arm: str, extra: dict | None = None) -> dict:
    env = env_for(scenario, arm, RUNS, TAU, None)
    env.pop("PROCESS_ARCH_PASS_TRACE", None)
    env.pop("PROCESS_ARCH_PASS_TRACE_FULL_FROM", None)
    for k in NEW_VARS:
        env.pop(k, None)
    if extra:
        env.update(extra)
    return env


def _launch(cmd, env, outdir: Path, timeout: int) -> int:
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
    print(f"  rc={rc} {time.perf_counter() - t0:6.1f}s -> {outdir} "
          f"(wall clock is progress information, not a measurement)",
          flush=True)
    return rc


def run_full(arm: str, outdir: Path, *, seed: int, extra_env: dict | None,
             timeout: int = 5400) -> dict:
    """One full ``st_regression`` run, EXACTLY the A32 campaign recipe
    (a26-mode spec, A18-artifact exit audit, entry census, delta 0.10),
    plus whatever ``extra_env`` a stage means to set."""
    if outdir.exists():
        shutil.rmtree(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable, str(HERE / "run_one.py"),
        "--scenario", "st_regression",
        "--mode", "control",
        "--outdir", str(outdir),
        "--expect-tree", str(TREE),
        "--input", str(deck_for("st_regression", arm, RUNS / "_decks")),
        "--exit-audit", str(YSTATE_A18_ST),
        "--entry-census",
        "--perturb-delta", repr(DELTA),
        "--perturb-seed", str(seed),
    ]
    env = _env("st_regression", arm, {
        "PROCESS_ARCH_YSTATE": str(YSTATE_A26_ST),
        "PROCESS_ARCH_WRITESET": str(WRITESET_A26_ST),
        **(extra_env or {}),
    })
    rc = _launch(cmd, env, outdir, timeout)
    mpath = outdir / "metrics.json"
    metrics = json.loads(mpath.read_text()) if mpath.exists() else {
        "status": "no_metrics", "returncode": rc,
    }
    return {"rc": rc, "outdir": str(outdir), "metrics": metrics}


def run_eval(scenario: str, arm: str, outdir: Path, *, deck: Path,
             perturb_spec: Path, exit_audit: Path, delta: float | None,
             seed: int, extra_env: dict | None,
             timeout: int = 3600) -> dict:
    """One single-MDA-eval run through ``v2_eval_one.py``."""
    if outdir.exists():
        shutil.rmtree(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable, str(HERE / "v2_eval_one.py"),
        "--scenario", scenario,
        "--input", str(deck),
        "--outdir", str(outdir),
        "--expect-tree", str(TREE),
        "--perturb-spec", str(perturb_spec),
        "--exit-audit", str(exit_audit),
        "--seed", str(seed),
    ]
    if delta is not None:
        cmd += ["--delta", repr(delta)]
    env = _env(scenario, arm, extra_env)
    rc = _launch(cmd, env, outdir, timeout)
    mpath = outdir / "metrics.json"
    metrics = json.loads(mpath.read_text()) if mpath.exists() else {
        "status": "no_metrics", "returncode": rc,
    }
    return {"rc": rc, "outdir": str(outdir), "metrics": metrics}


# --------------------------------------------------------------------------
# offline spec loading (for the cross-state residual; never imports process)
# --------------------------------------------------------------------------


def _ystate_module():
    p = TREE / "arch_surgery" / "fixedpoint" / "ystate.py"
    spec = importlib.util.spec_from_file_location("_a34_ystate", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_spec_offline(path: Path):
    """Rebuild a committed ystate artifact into a YSpec, sha-checked."""
    ys = _ystate_module()
    rec = json.loads(path.read_text())
    keys, category, scale = [], [], []
    for c in rec["components"]:
        ns, _, fld = c["key"].partition(".")
        keys.append((ns, fld))
        category.append(c["category"])
        scale.append(float(c.get("scale", 0.0)))
    spec = ys.YSpec(
        keys, category, scale, rec.get("n_components"), rec["components"],
        mode=rec.get("spec_mode", ys.SPEC_MODE_A18),
        scale_floor=float(rec.get("scale_floor", ys.SCALE_FLOOR)),
    )
    committed = rec.get("components_sha256")
    if committed and spec.components_sha256() != committed:
        raise RuntimeError(
            f"{path} does not rebuild: {spec.components_sha256()} vs "
            f"{committed} committed"
        )
    return spec


# --------------------------------------------------------------------------
# stage: trust_gate -- (i)(a), switch-neutrality vs A32's record, teeth
# --------------------------------------------------------------------------


def stage_trust_gate() -> int:
    print("trust_gate: env unset must reproduce A32's a26-spec start000 "
          "bit-for-bit", flush=True)
    outdir = RUNS / "trust_gate" / "A1p_start000"
    r = run_full("A1p", outdir, seed=0, extra_env=None)
    ref = gate_extract(json.loads(A32_REF.read_text()))
    got = gate_extract(r["metrics"])
    verdict = gate_compare(ref, got)
    teeth = gate_teeth(ref, got)
    record = {
        "gate": (
            "A34 switch-neutrality: PROCESS_ARCH_OUTER and "
            "PROCESS_ARCH_PIN_BURN_TIME unset, driver carrying both "
            "capabilities, must reproduce A32's recorded a26-spec A1' "
            "start000 (protocol 12)"
        ),
        "reference": str(A32_REF),
        "run": {"outdir": r["outdir"], "rc": r["rc"],
                "status": r["metrics"].get("status")},
        "comparison": verdict,
        "teeth": teeth,
        "verdict": (
            "PASS"
            if (verdict["pass"] and teeth["all_tripped"] and r["rc"] == 0)
            else "FAIL"
        ),
    }
    (RUNS / "trust_gate" / "gate.json").write_text(
        json.dumps(record, indent=2)
    )
    print(json.dumps({k: v for k, v in record.items() if k != "run"},
                     indent=2))
    return 0 if record["verdict"] == "PASS" else 1


# --------------------------------------------------------------------------
# stage: trust_demo -- (i)(b), trust on, hist all 1s, reported beside A32
# --------------------------------------------------------------------------


def _hist_all_ones(hist: dict | None) -> bool:
    return bool(hist) and set(hist.keys()) == {"1"}


def _all_ones_teeth(hist: dict) -> dict:
    """The all-1s check must be able to fail: two comparator perturbations."""
    n = sum(hist.values())
    trials = {
        "one_call_moved_to_2_passes": not _hist_all_ones(
            {"1": n - 1, "2": 1}
        ),
        "all_calls_at_2_passes": not _hist_all_ones({"2": n}),
    }
    return {
        "n_perturbations": len(trials),
        "n_tripped": sum(bool(v) for v in trials.values()),
        "all_tripped": all(trials.values()),
        "per_perturbation": trials,
    }


def stage_trust_demo() -> int:
    print("trust_demo: PROCESS_ARCH_OUTER=trust, same configuration",
          flush=True)
    outdir = RUNS / "trust_demo" / "A1p_start000_trust"
    r = run_full("A1p", outdir, seed=0,
                 extra_env={"PROCESS_ARCH_OUTER": "trust"})
    m = r["metrics"]
    ref = json.loads(A32_REF.read_text())
    hist = (m.get("module_solve_totals") or {}).get("outer_pass_hist") or {}
    all_ones = _hist_all_ones(hist)
    teeth = _all_ones_teeth(hist) if hist else {
        "all_tripped": False, "note": "no histogram recorded"
    }
    last_trace = (m.get("module_solve_stats") or {}).get(
        "outer_residual_trace"
    )
    record = {
        "demo": (
            "A34 trust mode end-to-end: a26-spec A1' st_regression start000 "
            "with the outer joint predicate never evaluated"
        ),
        "run": {"outdir": r["outdir"], "rc": r["rc"],
                "status": m.get("status"),
                "arch_outer_mode": m.get("arch_outer_mode")},
        "outer_pass_hist": hist,
        "outer_pass_hist_all_ones": all_ones,
        "n_call_models": (m.get("module_solve_totals") or {}).get(
            "n_call_models"
        ),
        "last_call_outer_residual_trace_empty": (
            last_trace == [] if last_trace is not None else None
        ),
        "teeth_on_the_all_ones_check": teeth,
        "reported_beside_A32_never_judged": {
            "what": (
                "differences below are REPORTED, not judged: comparing the "
                "trust arm against the verified arm at matched accuracy is "
                "V2's job, on V2's pre-declared rules (plan section 3)"
            ),
            "norm_objf_hex": {
                "trust": (m.get("exact") or {}).get("norm_objf"),
                "a32_verified": (ref.get("exact") or {}).get("norm_objf"),
                "equal": (
                    (m.get("exact") or {}).get("norm_objf")
                    == (ref.get("exact") or {}).get("norm_objf")
                ),
            },
            "uncharged_exit_audit_residual_max_hex": {
                "trust": (m.get("exit_audit") or {}).get("residual_max_hex"),
                "a32_verified": (ref.get("exit_audit") or {}).get(
                    "residual_max_hex"
                ),
                "instrument_note": (
                    "both are run_one's POST-RUN exit audit on the A18 "
                    "artifact -- the same ruler A32 used.  run_one.py's own "
                    "help records that the post-run audit reads at or near "
                    "zero for every arm because the output path re-converges "
                    "the state to MFILE idempotence; it is reported here "
                    "because the task names it, with that caveat attached."
                ),
            },
            "node_calls_solve_phase": {
                "trust": m.get("node_calls_solve_phase"),
                "a32_verified": ref.get("node_calls_solve_phase"),
            },
            "n_solver_iterations": {
                "trust": m.get("n_solver_iterations"),
                "a32_verified": ref.get("n_solver_iterations"),
            },
            "ifail": {
                "trust": (m.get("mfile") or {}).get("ifail"),
                "a32_verified": (ref.get("mfile") or {}).get("ifail"),
            },
        },
        "verdict": (
            "PASS"
            if (r["rc"] == 0 and m.get("status") == "ok" and all_ones
                and teeth.get("all_tripped"))
            else "FAIL"
        ),
    }
    (RUNS / "trust_demo" / "demo.json").write_text(
        json.dumps(record, indent=2)
    )
    print(json.dumps(record, indent=2))
    return 0 if record["verdict"] == "PASS" else 1


# --------------------------------------------------------------------------
# stage: evalone_gate -- (iii) vs A28's audit-at-call-1 record, teeth
# --------------------------------------------------------------------------

EVALONE_FIELDS = (
    "node_calls_of_call_1",
    "audit_node_calls",
    "audit_residual_max_hex",
    "audit_argmax",
)


def _evalone_extract_ref(metrics: dict) -> dict:
    a = metrics.get("audit_at_call") or {}
    return {
        "node_calls_of_call_1": a.get("node_calls_before_audit"),
        "audit_node_calls": a.get("audit_node_calls"),
        "audit_residual_max_hex": a.get("residual_max_hex"),
        "audit_argmax": (a.get("brief") or {}).get("argmax"),
    }


def _evalone_extract_got(metrics: dict) -> dict:
    a = metrics.get("exit_audit") or {}
    return {
        "node_calls_of_call_1": metrics.get("node_calls_single_eval"),
        "audit_node_calls": a.get("audit_node_calls"),
        "audit_residual_max_hex": a.get("residual_max_hex"),
        "audit_argmax": (a.get("brief") or {}).get("argmax"),
    }


def _evalone_compare(ref: dict, got: dict) -> dict:
    per_field = {
        f: {"ref": ref[f], "got": got[f], "match": ref[f] == got[f]}
        for f in EVALONE_FIELDS
    }
    return {
        "fields_compared": len(EVALONE_FIELDS),
        "fields_matching": sum(1 for v in per_field.values() if v["match"]),
        "pass": all(v["match"] for v in per_field.values()),
        "per_field": per_field,
    }


def _evalone_teeth(ref: dict, got: dict) -> dict:
    trials = {}
    p = dict(ref)
    p["node_calls_of_call_1"] = (p["node_calls_of_call_1"] or 0) + 1
    trials["node_calls_of_call_1+1"] = not _evalone_compare(p, got)["pass"]
    p = dict(ref)
    p["audit_node_calls"] = (p["audit_node_calls"] or 0) + 1
    trials["audit_node_calls+1"] = not _evalone_compare(p, got)["pass"]
    p = dict(ref)
    v = float.fromhex(p["audit_residual_max_hex"])
    p["audit_residual_max_hex"] = math.nextafter(v, math.inf).hex()
    trials["audit_residual+1ulp"] = not _evalone_compare(p, got)["pass"]
    p = dict(ref)
    p["audit_argmax"] = str(p["audit_argmax"]) + "_x"
    trials["audit_argmax_renamed"] = not _evalone_compare(p, got)["pass"]
    return {
        "n_perturbations": len(trials),
        "n_tripped": sum(bool(v) for v in trials.values()),
        "all_tripped": all(trials.values()),
        "per_perturbation": trials,
    }


def stage_evalone_gate() -> int:
    print("evalone_gate: FLAT single eval at the unperturbed deck point vs "
          "A28's control-optimisation call 1", flush=True)
    outdir = RUNS / "evalone_gate" / "A0p_start000_eval"
    r = run_eval(
        "st_regression", "A0p", outdir,
        deck=HERE / "scenarios" / "st_regression.IN.DAT",
        perturb_spec=YSTATE_A26_ST,
        # The A18 artifact, deliberately: it is the ruler A28's
        # audit-at-call-1 record was measured with, and a bit-comparison
        # against that record must use the same ruler.
        exit_audit=YSTATE_A18_ST,
        delta=None, seed=0, extra_env=None,
    )
    ref = _evalone_extract_ref(json.loads(A28_AUDIT1_REF.read_text()))
    got = _evalone_extract_got(r["metrics"])
    verdict = _evalone_compare(ref, got)
    teeth = _evalone_teeth(ref, got)
    record = {
        "gate": (
            "A34 single-MDA-eval mode vs the control's first solve-phase "
            "call (protocol 12)"
        ),
        "reference": str(A28_AUDIT1_REF),
        "run": {"outdir": r["outdir"], "rc": r["rc"],
                "status": r["metrics"].get("status")},
        "comparison": verdict,
        "teeth": teeth,
        "what_this_comparison_is_and_is_not": (
            "A28's audit-at-call-1 machinery ran a REAL optimisation and "
            "stopped it at the return of call_models #1, recording that "
            "call's node-call count and a one-sweep coupling-state audit of "
            "its exit state (827 components, A18 spec).  The single-eval "
            "runner reproduces the initialisation and the one call with no "
            "optimiser in the process at all.  Bit-identity of the audit "
            "residual (an exact hex float over the full coupling state) "
            "plus equality of both node-call counts and the audit argmax is "
            "the strongest agreement the recorded reference supports; the "
            "reference does NOT record objf/conf at call 1, so those are "
            "not compared -- stated rather than papered over."
        ),
        "verdict": (
            "PASS"
            if (verdict["pass"] and teeth["all_tripped"] and r["rc"] == 0)
            else "FAIL"
        ),
    }
    (RUNS / "evalone_gate" / "gate.json").write_text(
        json.dumps(record, indent=2)
    )
    print(json.dumps({k: v for k, v in record.items() if k != "run"},
                     indent=2))
    return 0 if record["verdict"] == "PASS" else 1


# --------------------------------------------------------------------------
# stage: perturb_demo -- the cross-arm identity of the perturbation stream
# --------------------------------------------------------------------------


def stage_perturb_demo(seed: int = 3) -> int:
    print(f"perturb_demo: FLAT and BLOCKS+trust at (delta={DELTA}, "
          f"seed={seed}) must record bit-identical perturbations",
          flush=True)
    root = RUNS / "perturb_demo"
    deck = HERE / "scenarios" / "st_regression.IN.DAT"
    # The a26 spec pair for BOTH arms: st_regression is the one deck whose
    # a26-generation artifacts are complete (A32), and V2 runs everything on
    # the a26 spec.
    a26_pair = {
        "PROCESS_ARCH_YSTATE": str(YSTATE_A26_ST),
        "PROCESS_ARCH_WRITESET": str(WRITESET_A26_ST),
    }
    runs = {}
    for arm, extra in (
        ("A0p", a26_pair),
        ("A1p", {**a26_pair, "PROCESS_ARCH_OUTER": "trust"}),
    ):
        runs[arm] = run_eval(
            "st_regression", arm, root / f"{arm}_seed{seed:03d}",
            deck=deck, perturb_spec=YSTATE_A26_ST, exit_audit=YSTATE_A26_ST,
            delta=DELTA, seed=seed, extra_env=extra,
        )
    perts = {}
    for arm in ("A0p", "A1p"):
        p = Path(runs[arm]["outdir"]) / "perturbation.json"
        perts[arm] = json.loads(p.read_text()) if p.exists() else None
    identical = (
        perts["A0p"] is not None
        and perts["A0p"]["per_component"] == perts["A1p"]["per_component"]
    )
    n_rows = len((perts["A0p"] or {}).get("per_component", []))
    m0, m1 = runs["A0p"]["metrics"], runs["A1p"]["metrics"]
    trust_stats = m1.get("module_solve_stats") or {}
    record = {
        "demo": (
            "A34 perturbation stream: cross-arm identity (keyed on "
            "component NAME), plus the first end-to-end Phase-A BLOCKS "
            "chain (per_module + trust) on the deck whose a26 artifacts "
            "are complete"
        ),
        "delta": DELTA,
        "seed": seed,
        "runs": {
            arm: {"outdir": runs[arm]["outdir"], "rc": runs[arm]["rc"],
                  "status": runs[arm]["metrics"].get("status")}
            for arm in runs
        },
        "per_component_rows_compared": n_rows,
        "per_component_records_bit_identical": identical,
        "flat_arm": {
            "node_calls_single_eval": m0.get("node_calls_single_eval"),
            "exit_audit_residual_max_hex": (m0.get("exit_audit") or {}).get(
                "residual_max_hex"
            ),
        },
        "blocks_trust_arm": {
            "node_calls_single_eval": m1.get("node_calls_single_eval"),
            "outer_passes_of_the_single_call": trust_stats.get(
                "outer_passes"
            ),
            "outer_residual_trace_empty": (
                trust_stats.get("outer_residual_trace") == []
            ),
            "inner_totals": trust_stats.get("inner_totals"),
            "exit_audit_residual_max_hex": (m1.get("exit_audit") or {}).get(
                "residual_max_hex"
            ),
        },
        "note": (
            "the two arms' counts and audit residuals are context for the "
            "instrument's health, not a Phase-A result: N = 1 start, no "
            "pre-declared acceptance applied here"
        ),
    }
    # Context, reported not judged: how far apart the two arms' exit states
    # sit on this k = 0 deck, under the same instrument the pin gate uses.
    try:
        spec = load_spec_offline(YSTATE_A26_ST)
        y0 = restore_snapshot(
            spec,
            json.loads(
                (Path(runs["A0p"]["outdir"]) / "y_exit.json").read_text()
            ),
        )
        y1 = restore_snapshot(
            spec,
            json.loads(
                (Path(runs["A1p"]["outdir"]) / "y_exit.json").read_text()
            ),
        )
        record["cross_state_residual_flat_vs_blocks_trust"] = (
            _cross_residual(spec, y0, y1, TAU)
        )
    except Exception as exc:  # noqa: BLE001 - context, not a verdict input
        record["cross_state_residual_flat_vs_blocks_trust"] = {
            "error": f"{type(exc).__name__}: {exc}"
        }
    record["verdict"] = (
        "PASS"
        if (runs["A0p"]["rc"] == 0 and runs["A1p"]["rc"] == 0
            and identical and n_rows > 0
            and trust_stats.get("outer_passes") == 1)
        else "FAIL"
    )
    (root / "demo.json").write_text(json.dumps(record, indent=2))
    print(json.dumps(record, indent=2))
    return 0 if record["verdict"] == "PASS" else 1


# --------------------------------------------------------------------------
# stage: pin_gate -- (ii), the plan section-3 equivalence gate (machinery)
# --------------------------------------------------------------------------


def _cross_residual(spec, y_flat, y_blocks, tau) -> dict:
    res = spec.residual(y_flat, y_blocks)
    return {
        "max": res.max,
        "max_hex": float(res.max).hex(),
        "argmax": None if res.argmax is None else spec.name(res.argmax),
        "n_above_tau": res.n_above(tau),
        "n_discrete_mismatch": len(res.mismatch_discrete),
        "n_constant_moved": len(res.moved_constant),
        "n_nan_new": len(res.nan_new),
        "categorically_clean": not (
            res.mismatch_discrete or res.moved_constant or res.nan_new
        ),
    }


def stage_pin_gate() -> int:
    print("pin_gate: large_tokamak_nof -- FLAT fixed point vs BLOCKS+pin+"
          "trust chain pinned at its converged burn time "
          "(A18-generation artifacts: MACHINERY gate, not a V2 measurement)",
          flush=True)
    root = RUNS / "pin_gate"
    deck = HERE / "scenarios" / "large_tokamak_nof.IN.DAT"

    # 1. the FLAT arm's MDA to convergence at the deck point
    flat = run_eval(
        "large_tokamak_nof", "A0p", root / "flat_deckpoint",
        deck=deck, perturb_spec=YSTATE_A26_NOF, exit_audit=YSTATE_A18_NOF,
        delta=None, seed=0, extra_env=None,
    )
    mf = flat["metrics"]
    if flat["rc"] != 0 or mf.get("status") != "ok":
        record = {
            "gate": "A34 pin equivalence (plan section 3)",
            "verdict": "FAIL",
            "failed_at": "FLAT arm did not converge at the deck point",
            "flat": {"rc": flat["rc"], "status": mf.get("status")},
        }
        root.mkdir(parents=True, exist_ok=True)
        (root / "gate.json").write_text(json.dumps(record, indent=2))
        print(json.dumps(record, indent=2))
        return 1
    burn_hex = mf["t_plant_pulse_burn_hex"]

    # 2. the BLOCKS+pin+trust chain, pinned at EXACTLY that value (hex --
    #    no decimal round trip), on the ORIGINAL deck: the pin replaces the
    #    optimiser as the variable's owner, so the derived lifted deck
    #    (ixc 178) is refused by design -- see stage pin_refusals.
    blocks = run_eval(
        "large_tokamak_nof", "A1p", root / "blocks_pin_trust",
        deck=deck, perturb_spec=YSTATE_A26_NOF, exit_audit=YSTATE_A18_NOF,
        delta=None, seed=0,
        extra_env={
            "PROCESS_ARCH_OUTER": "trust",
            "PROCESS_ARCH_PIN_BURN_TIME": burn_hex,
        },
    )
    mb = blocks["metrics"]

    # 2b. the localisation control: the SAME pinned chain with the outer
    #     verification loop ON.  Not part of the gate's verdict -- it is
    #     what separates "the pin is broken" from "one schedule pass from
    #     this entry does not reach the joint fixed point".  If the
    #     verified chain reproduces the FLAT point and the trust chain does
    #     not, the gap is the outer loop's genuine convergence work at this
    #     entry, not the pin.
    verified = run_eval(
        "large_tokamak_nof", "A1p", root / "blocks_pin_verified",
        deck=deck, perturb_spec=YSTATE_A26_NOF, exit_audit=YSTATE_A18_NOF,
        delta=None, seed=0,
        extra_env={"PROCESS_ARCH_PIN_BURN_TIME": burn_hex},
    )
    mv = verified["metrics"]

    record: dict = {
        "gate": (
            "A34 pin equivalence (V2 plan section 3): one BLOCKS run pinned "
            "at the FLAT arm's converged coupling value must reproduce the "
            "FLAT fixed point within the audit's resolution"
        ),
        "artifact_generation": (
            "A18 (ystate_large_tokamak_nof / writeset_large_tokamak_nof): "
            "the pulsed decks' a26-generation write sets are task A33's "
            "deliverable, so this gate exercises the MACHINERY under the "
            "committed A18 pair and is labelled a machinery gate, not a V2 "
            "measurement.  V2 reruns it under the a26 pair when A33 lands."
        ),
        "deck": str(deck),
        "flat": {
            "outdir": flat["outdir"], "rc": flat["rc"],
            "status": mf.get("status"),
            "node_calls_single_eval": mf.get("node_calls_single_eval"),
            "t_plant_pulse_burn_hex": burn_hex,
            "own_audit_residual_max_hex": (mf.get("exit_audit") or {}).get(
                "residual_max_hex"
            ),
        },
        "blocks_pin_trust": {
            "outdir": blocks["outdir"], "rc": blocks["rc"],
            "status": mb.get("status"),
            "node_calls_single_eval": mb.get("node_calls_single_eval"),
            "arch_pin_burn_time_hex": mb.get("arch_pin_burn_time_hex"),
            "pin_intact_at_exit": mb.get("pin_intact_at_exit"),
            "t_plant_pulse_burn_hex": mb.get("t_plant_pulse_burn_hex"),
            "outer_passes_of_the_single_call": (
                mb.get("module_solve_stats") or {}
            ).get("outer_passes"),
            "own_audit_residual_max_hex": (mb.get("exit_audit") or {}).get(
                "residual_max_hex"
            ),
        },
        "blocks_pin_verified_control": {
            "outdir": verified["outdir"], "rc": verified["rc"],
            "status": mv.get("status"),
            "node_calls_single_eval": mv.get("node_calls_single_eval"),
            "pin_intact_at_exit": mv.get("pin_intact_at_exit"),
            "outer_passes_of_the_single_call": (
                mv.get("module_solve_stats") or {}
            ).get("outer_passes"),
            "own_audit_residual_max_hex": (mv.get("exit_audit") or {}).get(
                "residual_max_hex"
            ),
        },
    }
    if blocks["rc"] != 0 or mb.get("status") != "ok":
        record["verdict"] = "FAIL"
        record["failed_at"] = "BLOCKS+pin+trust chain did not complete"
        (root / "gate.json").write_text(json.dumps(record, indent=2))
        print(json.dumps(record, indent=2))
        return 1

    flat_hex = (mf.get("exit_audit") or {}).get("residual_max_hex")
    blocks_hex = (mb.get("exit_audit") or {}).get("residual_max_hex")
    if not flat_hex or not blocks_hex:
        record["verdict"] = "FAIL"
        record["failed_at"] = (
            "an arm's own exit audit produced no residual; the gate has no "
            "resolution to state the comparison at"
        )
        (root / "gate.json").write_text(json.dumps(record, indent=2))
        print(json.dumps(record, indent=2))
        return 1

    # 3. the cross-state residual, measured by the audit instrument
    spec = load_spec_offline(YSTATE_A18_NOF)
    y_flat = restore_snapshot(
        spec, json.loads((Path(flat["outdir"]) / "y_exit.json").read_text())
    )
    y_blocks = restore_snapshot(
        spec,
        json.loads((Path(blocks["outdir"]) / "y_exit.json").read_text()),
    )
    cross = _cross_residual(spec, y_flat, y_blocks, TAU)
    cross_verified = None
    if verified["rc"] == 0 and mv.get("status") == "ok":
        y_ver = restore_snapshot(
            spec,
            json.loads(
                (Path(verified["outdir"]) / "y_exit.json").read_text()
            ),
        )
        cross_verified = _cross_residual(spec, y_flat, y_ver, TAU)
        # top movers of the trust chain's cross residual, for the record:
        # WHICH components the skipped outer pass would have converged.
        res = spec.residual(y_flat, y_blocks)
        movers = sorted(
            zip(res.idx_c, res.scaled.tolist()), key=lambda t: -t[1]
        )[:15]
        record["trust_cross_residual_top_movers"] = [
            {"key": spec.name(i), "scaled": s, "scaled_hex": float(s).hex(),
             "category": spec.category[i]}
            for i, s in movers if s >= TAU
        ]

    flat_own = float.fromhex(flat_hex)
    blocks_own = float.fromhex(blocks_hex)
    noise_floor = max(flat_own, blocks_own)

    # Pre-declared criterion.  Both arms ran at the same tau and claim
    # tau-grade convergence; "reproduces the FLAT fixed point within the
    # audit's resolution" is bound here as: categorically clean (no discrete
    # mismatch, no moved constant, no new NaN) AND cross_max < tau under the
    # audit's own scaled metric.  The stricter reading -- cross_max at or
    # below the larger of the two arms' own one-more-sweep residuals, i.e.
    # indistinguishable at the instrument's noise floor -- is reported
    # beside it, unbound; V2's review owns the choice between them (design
    # decision recorded in the A34 report).
    below_tau = cross["max"] < TAU
    at_noise_floor = cross["max"] <= noise_floor
    lift_component = "times.t_plant_pulse_burn"
    idx = {spec.name(i): i for i in range(len(spec.keys))}
    li = idx.get(lift_component)
    lift_diff_zero = None
    if li is not None:
        a, b = y_flat[li], y_blocks[li]
        lift_diff_zero = float(a) == float(b)

    # teeth: comparator perturbations that must trip the criterion
    trials = {}
    ys_cont = next(
        i for i in range(len(spec.keys))
        if spec.category[i] == "continuous"
        and isinstance(y_flat[i], float)
    )
    y_pert = list(y_flat)
    y_pert[ys_cont] = y_pert[ys_cont] + 3.0 * TAU * spec.scale[ys_cont]
    c1 = _cross_residual(spec, y_pert, y_blocks, TAU)
    trials["continuous_bumped_3tau_scale"] = not (
        c1["max"] < TAU and c1["categorically_clean"]
    )
    ys_disc = next(
        (i for i in range(len(spec.keys)) if spec.category[i] == "discrete"),
        None,
    )
    if ys_disc is not None:
        y_pert = list(y_flat)
        v = y_pert[ys_disc]
        y_pert[ys_disc] = (not v) if isinstance(v, bool) else (
            (v + 1) if isinstance(v, int) else str(v) + "_x"
        )
        c2 = _cross_residual(spec, y_pert, y_blocks, TAU)
        trials["discrete_flipped"] = not (
            c2["max"] < TAU and c2["categorically_clean"]
        )
    teeth = {
        "n_perturbations": len(trials),
        "n_tripped": sum(bool(v) for v in trials.values()),
        "all_tripped": all(trials.values()),
        "per_perturbation": trials,
    }

    record.update({
        "cross_state_residual": cross,
        "cross_state_residual_verified_control": cross_verified,
        "localisation": (
            "the verified control isolates the cause of any gate failure: "
            "pin ON in both chains, only the outer policy differs.  A "
            "verified chain at the FLAT point with a trust chain off it "
            "says the gap is the outer loop's genuine convergence work "
            "from this entry state, not the pin."
        ),
        "tau": TAU,
        "own_audit_noise_floor_max_hex": float(noise_floor).hex(),
        "criterion_bound": (
            "categorically clean AND cross_max < tau (see comment in "
            "a34_instruments.py stage_pin_gate)"
        ),
        "cross_max_below_tau": below_tau,
        "cross_max_at_or_below_own_audit_noise_floor_reported_unbound": (
            at_noise_floor
        ),
        "lift_component_bit_identical": {
            "component": lift_component,
            "expected": (
                "True by construction: the pin is the FLAT run's converged "
                "value passed as an exact hex float"
            ),
            "observed": lift_diff_zero,
        },
        "teeth": teeth,
        "verdict": (
            "PASS"
            if (below_tau and cross["categorically_clean"]
                and teeth["all_tripped"]
                and mb.get("pin_intact_at_exit") is True)
            else "FAIL"
        ),
    })
    (root / "gate.json").write_text(json.dumps(record, indent=2))
    print(json.dumps(record, indent=2))
    return 0 if record["verdict"] == "PASS" else 1


# --------------------------------------------------------------------------
# stage: pin_refusals -- the failure paths, demonstrated
# --------------------------------------------------------------------------


def stage_pin_refusals() -> int:
    print("pin_refusals: the two refusal paths must actually refuse",
          flush=True)
    root = RUNS / "pin_refusals"
    root.mkdir(parents=True, exist_ok=True)

    # (a) pin without lift: an import-time error in subsolve
    env = _env("large_tokamak_nof", "R",
               {"PROCESS_ARCH_PIN_BURN_TIME": "7200.0"})
    proc = subprocess.run(
        [sys.executable, "-c",
         "import process.core.solver.subsolve"],
        env=env, capture_output=True, text=True, cwd=str(root), timeout=600,
    )
    refused_a = (
        proc.returncode != 0
        and "PROCESS_ARCH_PIN_BURN_TIME" in proc.stderr
        and "PROCESS_ARCH_LIFT" in proc.stderr
    )
    rec_a = {
        "case": "pin set, lift unset -> import-time RuntimeError",
        "returncode": proc.returncode,
        "refused": refused_a,
        "stderr_tail": proc.stderr[-800:],
    }

    # (b) pin on a deck that names ixc 178: derive the lifted deck the
    #     run_a28 way, then the Caller refusal
    decks = root / "_decks" / "large_tokamak_nof"
    decks.mkdir(parents=True, exist_ok=True)
    denv = _env("large_tokamak_nof", "R")
    dproc = subprocess.run(
        [sys.executable, str(HERE / "a25_variant_deck.py"),
         "--scenario", "large_tokamak_nof", "--outdir", str(decks),
         "--expect-tree", str(TREE)],
        env=denv, cwd=str(decks), capture_output=True, text=True,
        timeout=3600,
    )
    (decks / "derive.log").write_text(dproc.stdout + dproc.stderr)
    lifted = decks / "large_tokamak_nof_lifted.IN.DAT"
    rec_b: dict = {"case": "pin on the lifted deck (ixc 178) -> Caller "
                           "refusal", "deck_derived": lifted.exists(),
                   "derive_rc": dproc.returncode}
    if lifted.exists():
        r = run_eval(
            "large_tokamak_nof", "A1p", root / "lifted_deck_refusal",
            deck=lifted, perturb_spec=YSTATE_A26_NOF,
            exit_audit=YSTATE_A18_NOF, delta=None, seed=0,
            extra_env={
                "PROCESS_ARCH_OUTER": "trust",
                "PROCESS_ARCH_PIN_BURN_TIME": "7200.0",
            },
        )
        tb = r["metrics"].get("traceback") or ""
        rec_b.update({
            "rc": r["rc"],
            "status": r["metrics"].get("status"),
            "refused": (
                r["metrics"].get("status") == "crashed"
                and "ixc = 178" in tb
                and "PROCESS_ARCH_PIN_BURN_TIME" in tb
            ),
            "traceback_tail": tb[-600:],
        })
    else:
        rec_b["refused"] = False

    record = {
        "stage": "A34 pin refusal paths (protocol 15: failure paths "
                 "reachable from the committed entry point)",
        "pin_without_lift": rec_a,
        "pin_on_lifted_deck": rec_b,
        "verdict": (
            "PASS" if (refused_a and rec_b.get("refused")) else "FAIL"
        ),
    }
    (root / "refusals.json").write_text(json.dumps(record, indent=2))
    print(json.dumps(record, indent=2))
    return 0 if record["verdict"] == "PASS" else 1


# --------------------------------------------------------------------------


STAGES = {
    "trust_gate": stage_trust_gate,
    "trust_demo": stage_trust_demo,
    "evalone_gate": stage_evalone_gate,
    "perturb_demo": stage_perturb_demo,
    "pin_gate": stage_pin_gate,
    "pin_refusals": stage_pin_refusals,
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=[*STAGES, "all"])
    args = ap.parse_args()
    RUNS.mkdir(parents=True, exist_ok=True)
    (RUNS / "_mplconfig").mkdir(exist_ok=True)
    if args.stage != "all":
        return STAGES[args.stage]()
    for name, fn in STAGES.items():
        print(f"\n=== {name} ===", flush=True)
        rc = fn()
        if rc != 0:
            print(f"stage {name} FAILED (rc {rc}); stopping -- a failed "
                  f"gate is a result, not an obstacle", flush=True)
            return rc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
