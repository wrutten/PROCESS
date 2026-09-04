#!/usr/bin/env python
"""V3 Phase B — the optimisation comparison (V3 plan §3.2, §4.2).

Copied verbatim (task A41, first commit 913b89f0) from
arch_surgery/MDA_partitioning_experiment_v2/phase_b.py at commit b7dbd2a9,
then modified per V3_DEVELOPMENT_PLAN.md §4.2, §5 (G0, G5, G7), §6
(T-b, T-c, T-d) by task A41.  What changed against V2, and nothing else:

* Arms as V2's ladder (R / B0 / B1 / B2 / B3); B2 and B3 now carry the
  prime (O4/D19) through v3_runner.env_for, which REFUSES a primed arm
  while the prime instrument (task A40) is unavailable.
* Gate G0 (driver neutrality) compares R start000 per deck against V2's
  OWN campaign records, read read-only from the main checkout (the A38
  pattern) — V2's records are the V3 plan's named comparator.
* NEW gate G7 (record completeness, §5): one deliberately-unconverged run
  (R at a forced iteration cap) must carry every H3 exit-forensics field —
  n_solver_iterations, ifail, ladder stage, constraint residual vector,
  active set; teeth: the completeness checker, fed a copy of the record
  with each field deleted in turn, must refuse each time.  The tally
  applies the same checker to EVERY ok campaign record and REFUSES on a
  missing field.
* The tally adds the declared constructions: T-b (both-converged pairing;
  failure taxonomy with denominators; the deck-invalid-seed statistic — a
  seed with no accepted optimum in ANY arm is excluded from per-arm rates
  and counted separately); T-c (same-optimum check with yardstick = the
  R->B0 spread, acceptance spread <= max(F x yardstick, the 1e-6 relative
  floor, O3), and the multi-attractor clustering with hop rates per arm
  pair, check 1a); T-d (the per-block node-call split as a first-class
  tally artifact); the iteration multiplier (check 2) with the DECLARED
  nearest-rank median (upper-middle, sorted[n // 2]; orchestrator
  correction 0a8f5af2 — statistics.median published beside as a
  diagnostic, never as the check value).

Stages: ``preflight`` / ``gate`` (G0) / ``armgate`` (G5) / ``g7gate`` /
``smoke`` / ``campaign`` / ``tally`` / ``timing`` / ``all``.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import v3_config as cfg  # noqa: E402
import v3_runner as vr  # noqa: E402

PB_RUNS = cfg.RUNS / "phase_b"
DECKS_DIR = cfg.RUNS / "_decks"

#: V2's Phase B campaign records — G0's comparator (plan §5), read
#: READ-ONLY from the main checkout, never regenerated here (A38 pattern).
MAIN_CHECKOUT = Path("/home/wrutten/projects/PROCESS_surgery")
V2_PB_RECORDS = (MAIN_CHECKOUT / "arch_surgery"
                 / "MDA_partitioning_experiment_v2" / "runs" / "phase_b")

#: H3's five fields (V3 plan §6 H3): the completeness contract every ok
#: optimisation record must satisfy (G7; refused by the tally otherwise).
FORENSICS_FIELDS = ("n_solver_iterations", "ifail", "ladder_stage",
                    "constraint_residual_vector", "active_set")


def rank_median(sorted_vals: list):
    """The DECLARED median for every Phase B check statistic: nearest-rank
    upper-middle, sorted_values[n // 2] (v3_config.MEDIAN_CONSTRUCTION;
    orchestrator correction 0a8f5af2)."""
    return sorted_vals[len(sorted_vals) // 2] if sorted_vals else None


def p90(sorted_vals: list):
    """Nearest-rank p90: element ceil(0.9 n) of the sorted list."""
    n = len(sorted_vals)
    return sorted_vals[max(0, math.ceil(0.9 * n) - 1)] if n else None


def forensics_check(m: dict) -> tuple[bool, str]:
    """(complete, why-not).  The G7 contract on ONE record: the H3 block is
    present and every field of FORENSICS_FIELDS is non-null; a record whose
    run never reached a solver attempt (n_attempts == 0) is exempt from
    the solver-owned fields but must still carry the block."""
    f = m.get("exit_forensics")
    if not isinstance(f, dict):
        return False, "exit_forensics block missing"
    if (f.get("n_attempts") or 0) < 1:
        return False, "no solver attempt recorded (n_attempts < 1)"
    for k in FORENSICS_FIELDS:
        if f.get(k) is None:
            return False, f"field {k!r} missing or null"
    return True, "complete"


# --------------------------------------------------------------------------
# preflight: the ledger
# --------------------------------------------------------------------------


def arm_status(deck: str, arm: str) -> tuple[bool, str]:
    """(runnable, reason).  An arm refuses by name, never silently."""
    if arm == "B1" and deck not in cfg.PULSED:
        return False, ("k = 0: B1 degenerates to B0 on this deck (plan §3.2)"
                       " — skipped by design")
    if arm != "R":
        if not cfg.ystate_for(deck).exists():
            return False, f"missing {cfg.ystate_for(deck).name}"
        if not cfg.writeset_for(deck).exists():
            led = cfg.INSTRUMENTATION["pulsed_a26_writesets"]
            return False, (f"missing {cfg.writeset_for(deck).name} — "
                           f"{led['task']}")
    if arm in ("B2", "B3"):
        needed = ["post_solve"] + (["trust_mode"] if arm == "B3" else [])
        if arm in cfg.PRIMED_ARMS:
            needed.append("prime")
        for key in needed:
            led = cfg.INSTRUMENTATION[key]
            if not led["available"]:
                return False, f"{key} not built — {led['task']}"
        if not cfg.postsolve_for(deck).exists():
            return False, (f"missing {cfg.postsolve_for(deck).name} — "
                           f"{cfg.INSTRUMENTATION['post_solve']['task']}")
    return True, "ready"


def stage_preflight() -> int:
    PB_RUNS.mkdir(parents=True, exist_ok=True)
    ledger = {}
    all_ready = True
    for deck in cfg.DECKS:
        for arm in cfg.PHASE_B_ARMS:
            ok, why = arm_status(deck, arm)
            ledger[f"{deck}/{arm}"] = {"runnable": ok, "reason": why}
            skipped_by_design = "skipped by design" in why
            if not ok and not skipped_by_design:
                all_ready = False
            print(f"  {deck:24s} {arm:3s} "
                  f"{'ready' if ok else 'REFUSED':8s} {why}")
    led = cfg.INSTRUMENTATION["exit_forensics"]
    ledger["exit_forensics"] = dict(led)
    if not led["available"]:
        all_ready = False
        print(f"  {'exit_forensics':28s} REFUSED  not gated — {led['task']}")
    else:
        print(f"  {'exit_forensics':28s} ready")
    record = {"ledger": ledger, "all_ready": all_ready,
              "execution_approved": cfg.EXECUTION_APPROVED}
    (PB_RUNS / "preflight.json").write_text(json.dumps(record, indent=2))
    print(f"\nphase B preflight: {'READY' if all_ready else 'NOT READY'} "
          f"(execution approved: {cfg.EXECUTION_APPROVED}); "
          f"ledger in {PB_RUNS / 'preflight.json'}")
    return 0 if all_ready else 3


# --------------------------------------------------------------------------
# smoke: machinery, not measurement
# --------------------------------------------------------------------------


def stage_smoke() -> int:
    """One baseline optimisation per currently runnable arm-family on the
    cheapest configurations: R and B0 on ``st_regression`` (the real a26
    configuration).  B1's lifted-deck machinery is exercised on
    ``large_tokamak_nof`` (a26 artifacts — V2's A18 stand-in is gone since
    A33 delivered every deck's write set).  B2/B3 are reported as refused
    while the prime (A40) is missing.  Numbers are never measurements."""
    PB_RUNS.mkdir(parents=True, exist_ok=True)
    (cfg.RUNS / "_mplconfig").mkdir(parents=True, exist_ok=True)
    vr.derive_lifted_decks(DECKS_DIR)
    jobs = [
        dict(deck="st_regression", arm="R",
             outdir=PB_RUNS / "smoke" / "st_regression_R",
             seed=0, delta=None, decks_dir=DECKS_DIR),
        dict(deck="st_regression", arm="B0",
             outdir=PB_RUNS / "smoke" / "st_regression_B0",
             seed=0, delta=None, decks_dir=DECKS_DIR),
        dict(deck="large_tokamak_nof", arm="B1",
             outdir=PB_RUNS / "smoke" / "large_tokamak_nof_B1",
             seed=0, delta=None, decks_dir=DECKS_DIR),
    ]
    results = vr.run_pool(jobs)
    verdicts = {}
    failed = 0
    for r in results:
        m = json.loads((Path(r["outdir"]) / "metrics.json").read_text())
        complete, why = forensics_check(m)
        ok = (r["rc"] == 0 and m.get("status") == "ok"
              and m.get("node_calls_solve_phase")
              and (m.get("exact") or {}).get("norm_objf")
              and complete)
        verdicts[f"{r['deck']}/{r['arm']}"] = {
            "rc": r["rc"], "status": m.get("status"),
            "node_calls_solve_phase": m.get("node_calls_solve_phase"),
            "norm_objf_hex": (m.get("exact") or {}).get("norm_objf"),
            "exit_forensics": why,
            "machinery_ok": bool(ok),
        }
        failed += 0 if ok else 1
    for arm in ("B2", "B3"):
        ok_b, why_b = arm_status("st_regression", arm)
        if not ok_b:
            verdicts[f"{arm} (any deck)"] = {"machinery_ok": False,
                                             "refused": why_b}
    (PB_RUNS / "smoke").mkdir(parents=True, exist_ok=True)
    (PB_RUNS / "smoke" / "smoke.json").write_text(
        json.dumps(verdicts, indent=2))
    print(json.dumps(verdicts, indent=2))
    print(f"\nphase B smoke: {len(results) - failed}/{len(results)} "
          f"machinery runs ok; smoke numbers are not measurements")
    return 0 if failed == 0 else 1


# --------------------------------------------------------------------------
# gate G0: driver neutrality at the V3 commit (plan §5)
# --------------------------------------------------------------------------

#: The exact fields the gate compares — counts and a bit-comparison.
GATE_FIELDS = ("node_calls_solve_phase", "n_model_calls", "norm_objf_hex")


def _gate_extract(m: dict) -> dict:
    return {
        "node_calls_solve_phase": m.get("node_calls_solve_phase"),
        "n_model_calls": m.get("n_model_calls"),
        "norm_objf_hex": (m.get("exact") or {}).get("norm_objf"),
    }


def stage_gate() -> int:
    """G0: R start000 per deck at the V3 driver commit must reproduce V2's
    recorded R start000 bit-exactly on count fields and objective hex
    (plan §5).  R sets no architecture switch, so its path must be
    untouched by every driver change any V3 task merges.  The comparator
    is V2's OWN campaign record, read read-only from the main checkout.
    Teeth: each field's comparator, fed a minimally perturbed value, must
    trip (§12 — a gate is shown able to fail before its zeros mean
    anything)."""
    (cfg.RUNS / "_mplconfig").mkdir(parents=True, exist_ok=True)
    record: dict = {"gate": ("G0 V3 driver neutrality: R start000 vs V2's "
                             "campaign records (protocol §12)"),
                    "reference_root": str(V2_PB_RECORDS)}
    all_pass = True
    for deck in cfg.DECKS:
        ref_path = (V2_PB_RECORDS / "campaign" / deck / "R" / "start000"
                    / "metrics.json")
        if not ref_path.exists():
            record[deck] = {"verdict": "FAIL",
                            "reason": f"no V2 reference at {ref_path}"}
            all_pass = False
            continue
        r = vr.run_job(deck, "R", PB_RUNS / "gate" / deck,
                       seed=0, delta=cfg.DELTA, decks_dir=DECKS_DIR,
                       node_census=False)
        ref = _gate_extract(json.loads(ref_path.read_text()))
        got = _gate_extract(json.loads(
            (Path(r["outdir"]) / "metrics.json").read_text()))
        per_field = {f: {"ref": ref[f], "got": got[f],
                         "match": ref[f] == got[f]} for f in GATE_FIELDS}
        # teeth: a perturbed reading must trip each field's comparison
        teeth = {
            "node_calls_solve_phase": (
                ((got["node_calls_solve_phase"] or 0) + 1)
                != ref["node_calls_solve_phase"]),
            "n_model_calls": (((got["n_model_calls"] or 0) + 1)
                              != ref["n_model_calls"]),
            "norm_objf_hex": (((got["norm_objf_hex"] or "") + "0")
                              != ref["norm_objf_hex"]),
        }
        ok = (r["rc"] == 0 and all(v["match"] for v in per_field.values())
              and all(teeth.values()))
        record[deck] = {"reference": str(ref_path), "per_field": per_field,
                        "teeth_tripped": teeth,
                        "verdict": "PASS" if ok else "FAIL"}
        all_pass = all_pass and ok
        print(f"  gate {deck:24s} {'PASS' if ok else 'FAIL'}")
    (PB_RUNS / "gate").mkdir(parents=True, exist_ok=True)
    (PB_RUNS / "gate" / "gate.json").write_text(json.dumps(record, indent=2))
    print(f"\nG0 driver-neutrality gate: {'PASS' if all_pass else 'FAIL'} "
          f"(record: {PB_RUNS / 'gate' / 'gate.json'})")
    return 0 if all_pass else 1


def stage_armgate() -> int:
    """G5: the combined-switch equivalence gate, re-run with the prime in
    the switch set (plan §5).  B3 runs trust mode AND the post-solve
    exclusion AND (V3) the prime together; per deck, one B3-config run
    WITH the post-solve artifact vs one WITHOUT (both trust, both primed)
    must agree bit-for-bit on everything except the suppressed nodes' own
    calls.  Teeth: each comparator fed a perturbed reading must trip."""
    (cfg.RUNS / "_mplconfig").mkdir(parents=True, exist_ok=True)
    vr.derive_lifted_decks(DECKS_DIR)
    record: dict = {"gate": "G5 B3 combined-switch equivalence: post-solve "
                            "ON vs OFF under trust mode + prime (per deck)"}
    all_pass = True
    for deck in cfg.DECKS:
        pair = {}
        for tag, with_ps in (("with", True), ("without", False)):
            env_override = (None if with_ps
                            else {"PROCESS_ARCH_POST_SOLVE": None})
            r = vr.run_job(deck, "B3",
                           PB_RUNS / "armgate" / deck / tag,
                           seed=0, delta=None, decks_dir=DECKS_DIR,
                           node_census=False, drop_env=env_override)
            pair[tag] = json.loads(
                (Path(r["outdir"]) / "metrics.json").read_text())
        a, b = pair["with"], pair["without"]
        ta = a.get("module_solve_totals") or {}
        tb = b.get("module_solve_totals") or {}
        checks = {
            "norm_objf_hex": ((a.get("exact") or {}).get("norm_objf")
                              == (b.get("exact") or {}).get("norm_objf")),
            "ifail": ((a.get("mfile") or {}).get("ifail")
                      == (b.get("mfile") or {}).get("ifail")),
            "n_solver_iterations": (a.get("n_solver_iterations")
                                    == b.get("n_solver_iterations")),
            "n_call_models": (ta.get("n_call_models")
                              == tb.get("n_call_models")),
            "outer_pass_hist": (ta.get("outer_pass_hist")
                                == tb.get("outer_pass_hist")),
            "exit_audit_hex": (
                (a.get("exit_audit") or {}).get("residual_max_hex")
                == (b.get("exit_audit") or {}).get("residual_max_hex")),
            "statuses_ok": (a.get("status") == "ok"
                            and b.get("status") == "ok"),
        }
        teeth = {
            "norm_objf_hex": (
                ((a.get("exact") or {}).get("norm_objf") or "") + "0")
            != (b.get("exact") or {}).get("norm_objf"),
            "n_call_models": ((ta.get("n_call_models") or 0) + 1)
            != tb.get("n_call_models"),
        }
        delta_calls = ((b.get("node_calls_solve_phase") or 0)
                       - (a.get("node_calls_solve_phase") or 0))
        ok = all(checks.values()) and all(teeth.values())
        record[deck] = {"checks": checks, "teeth_tripped": teeth,
                        "suppressed_node_calls": delta_calls,
                        "verdict": "PASS" if ok else "FAIL"}
        all_pass = all_pass and ok
        print(f"  armgate {deck:24s} {'PASS' if ok else 'FAIL'} "
              f"(suppressed calls: {delta_calls})")
    (PB_RUNS / "armgate").mkdir(parents=True, exist_ok=True)
    (PB_RUNS / "armgate" / "armgate.json").write_text(
        json.dumps(record, indent=2))
    print(f"\nG5 combined-switch gate: {'PASS' if all_pass else 'FAIL'}")
    return 0 if all_pass else 1


# --------------------------------------------------------------------------
# gate G7: record completeness at an unconverged exit (plan §5; H3, A41)
# --------------------------------------------------------------------------


def stage_g7gate() -> int:
    """G7: a deliberately unconverged run must carry every H3 field, and
    the tally's completeness checker must REFUSE a record with a field
    missing.  One R run on the cheapest deck at a forced iteration cap
    (--force-maxcal 2: the solver exits its full retry ladder unconverged)
    — a gate run, never a measurement, stamped force_maxcal in its record.
    Teeth: the checker is fed a copy of the real record with each of the
    five fields deleted in turn (and once with the whole block deleted)
    and must refuse each time, naming the field."""
    (cfg.RUNS / "_mplconfig").mkdir(parents=True, exist_ok=True)
    root = PB_RUNS / "g7gate"
    r = vr.run_job("st_regression", "R", root / "unconverged_run",
                   seed=0, delta=None, decks_dir=DECKS_DIR,
                   node_census=False, force_maxcal=2)
    m = json.loads((Path(r["outdir"]) / "metrics.json").read_text())
    f = m.get("exit_forensics") or {}
    complete, why = forensics_check(m)
    unconverged = f.get("ifail") is not None and f.get("ifail") != 1
    fields = {k: ("present" if f.get(k) is not None else "MISSING")
              for k in FORENSICS_FIELDS}

    # teeth: delete each field in turn; the checker must refuse each time
    teeth = {}
    for k in FORENSICS_FIELDS:
        doctored = json.loads(json.dumps(m))
        doctored["exit_forensics"][k] = None
        ok_d, why_d = forensics_check(doctored)
        teeth[f"deleted_{k}"] = {"refused": not ok_d, "why": why_d,
                                 "names_the_field": k in why_d}
    doctored = json.loads(json.dumps(m))
    del doctored["exit_forensics"]
    ok_d, why_d = forensics_check(doctored)
    teeth["deleted_block"] = {"refused": not ok_d, "why": why_d,
                              "names_the_field": "missing" in why_d}
    teeth_ok = all(t["refused"] and t["names_the_field"]
                   for t in teeth.values())

    verdict = ("PASS" if (r["rc"] == 0 and m.get("status") == "ok"
                          and unconverged and complete and teeth_ok)
               else "FAIL")
    record = {
        "gate": ("G7 record completeness (plan §5): a deliberately "
                 "unconverged run carries n_solver_iterations, ifail, "
                 "ladder stage, constraint residual vector and active "
                 "set; the tally refuses a record with a field missing"),
        "run": {"outdir": r["outdir"], "rc": r["rc"],
                "status": m.get("status"),
                "force_maxcal": m.get("force_maxcal"),
                "ifail": f.get("ifail"),
                "unconverged": unconverged,
                "ladder_stage": f.get("ladder_stage"),
                "n_attempts": f.get("n_attempts"),
                "n_solver_iterations": f.get("n_solver_iterations"),
                "fields": fields,
                "complete": complete, "why": why,
                "tree_git_head": m.get("tree_git_head"),
                "tree_git_dirty": m.get("tree_git_dirty")},
        "teeth": teeth,
        "verdict": verdict,
    }
    root.mkdir(parents=True, exist_ok=True)
    (root / "gate.json").write_text(json.dumps(record, indent=2))
    print(f"\nG7 record-completeness gate: {verdict} "
          f"(ifail {f.get('ifail')}, ladder {f.get('ladder_stage')}, "
          f"attempts {f.get('n_attempts')}, fields "
          f"{sum(v == 'present' for v in fields.values())}/"
          f"{len(FORENSICS_FIELDS)}; teeth "
          f"{sum(t['refused'] for t in teeth.values())}/{len(teeth)} "
          f"refused)")
    return 0 if verdict == "PASS" else 1


# --------------------------------------------------------------------------
# campaign and tally
# --------------------------------------------------------------------------


def stage_timing() -> int:
    """Context-only timings (D17): SERIAL repetitions at the baseline start,
    no node census, one arm-deck at a time.  Never an acceptance quantity —
    published with median, range, repetition count and the disclaimer that
    every run pays per-process JIT identically."""
    reps = 3
    vr.derive_lifted_decks(DECKS_DIR)
    rows = {}
    for deck in cfg.DECKS:
        for arm in cfg.PHASE_B_ARMS:
            ok, _ = arm_status(deck, arm)
            if not ok:
                continue
            walls = []
            for i in range(reps):
                r = vr.run_job(deck, arm,
                               PB_RUNS / "timing" / deck / arm / f"rep{i}",
                               seed=0, delta=None, decks_dir=DECKS_DIR,
                               node_census=False)
                m = json.loads(
                    (Path(r["outdir"]) / "metrics.json").read_text())
                if m.get("wall_s"):
                    walls.append(m["wall_s"])
            walls.sort()
            rows[f"{deck}/{arm}"] = {
                "reps_requested": reps, "walls_s": walls,
                "median_s": walls[len(walls) // 2] if walls else None,
                "range_s": [walls[0], walls[-1]] if walls else None,
            }
    record = {"note": ("context only, never evidence (D17/I-10): serial, "
                       "baseline start, per-process JIT included identically "
                       "in every run"), "rows": rows}
    (PB_RUNS / "timing").mkdir(parents=True, exist_ok=True)
    (PB_RUNS / "timing" / "timing.json").write_text(
        json.dumps(record, indent=2))
    for k, v in rows.items():
        print(f"  timing {k:30s} median {v['median_s']:8.1f}s "
              f"range {v['range_s']}  (context, not a measurement)")
    return 0


def stage_campaign() -> int:
    if not cfg.EXECUTION_APPROVED:
        print("REFUSED: EXPERIMENT_PLAN.md is a draft — execution is not "
              "approved (v3_config.EXECUTION_APPROVED).  Run 'smoke'.")
        return 3
    if stage_preflight() != 0:
        print("REFUSED: instrumentation or artifacts missing — see the "
              "ledger above.")
        return 3
    if stage_gate() != 0:
        print("REFUSED: the G0 driver-neutrality gate failed — that failure "
              "is the result; nothing runs on an ungated driver.")
        return 1
    if stage_armgate() != 0:
        print("REFUSED: the G5 combined-switch equivalence gate failed — "
              "that failure is the result.")
        return 1
    if stage_g7gate() != 0:
        print("REFUSED: the G7 record-completeness gate failed — the "
              "campaign's forensic fields cannot be trusted.")
        return 1
    vr.derive_lifted_decks(DECKS_DIR)
    jobs = []
    for deck in cfg.DECKS:
        for arm in cfg.PHASE_B_ARMS:
            ok, why = arm_status(deck, arm)
            if not ok:
                continue  # only the by-design k=0 B1 skip reaches here
            for k in range(cfg.N_STARTS):
                jobs.append(dict(
                    deck=deck, arm=arm,
                    outdir=PB_RUNS / "campaign" / deck / arm / f"start{k:03d}",
                    seed=k, delta=cfg.DELTA, decks_dir=DECKS_DIR,
                    resume=True,
                ))
    print(f"campaign: {len(jobs)} runs, {vr.pool_workers()} workers")
    vr.run_pool(jobs)
    return stage_tally()


def _extract(m: dict) -> dict:
    complete, why = forensics_check(m)
    return {
        "status": m.get("status"),
        "ifail": (m.get("mfile") or {}).get("ifail"),
        "forensics_ifail": (m.get("exit_forensics") or {}).get("ifail"),
        "ladder_stage": (m.get("exit_forensics") or {}).get("ladder_stage"),
        "forensics_complete": complete,
        "forensics_why": why,
        "norm_objf_hex": (m.get("exact") or {}).get("norm_objf"),
        "n_solver_iterations": m.get("n_solver_iterations"),
        "n_model_calls": m.get("n_model_calls"),
        "node_calls_solve_phase": m.get("node_calls_solve_phase"),
        "node_census": m.get("node_census"),
        "constraint_93": m.get("constraint_93"),
        "post_solve_totals": m.get("post_solve_totals"),
        "arch_block_schedule": m.get("arch_block_schedule"),
        "exit_audit_max_hex": (m.get("exit_audit") or {}).get(
            "residual_max_hex"),
        "tree_git_head": m.get("tree_git_head"),
        "tree_git_dirty": m.get("tree_git_dirty"),
    }


def _conv(r: dict) -> bool:
    """An ACCEPTED optimum: run ok AND the optimiser converged (ifail = 1,
    VMCON's success code, from the MFILE — the independent source)."""
    return r.get("status") == "ok" and r.get("ifail") == 1.0


def _clusters(values: list[float]) -> list[list[int]]:
    """Check 1a's declared clustering: indices of ``values`` grouped by
    sorted norm_objf, split where the relative gap between adjacent sorted
    values exceeds CLUSTER_GAP_FLOOR_FACTOR x OBJF_FLOOR_REL (relative to
    the larger magnitude of the two)."""
    if not values:
        return []
    order = sorted(range(len(values)), key=lambda i: values[i])
    gap = cfg.CLUSTER_GAP_FLOOR_FACTOR * cfg.OBJF_FLOOR_REL
    groups = [[order[0]]]
    for i in order[1:]:
        prev = values[groups[-1][-1]]
        cur = values[i]
        denom = max(abs(prev), abs(cur))
        rel = (abs(cur - prev) / denom) if denom else 0.0
        if rel > gap:
            groups.append([i])
        else:
            groups[-1].append(i)
    return groups


def stage_tally() -> int:
    """The §4.2 checks from on-disk records (T-b, T-c, T-d).  Every
    requested start is a row — a denominator that shrinks without saying so
    is trap T11.  Every ok record must satisfy the G7 completeness
    contract, or the tally REFUSES."""
    root = PB_RUNS / "campaign"
    if not root.exists():
        print("no campaign records — run the campaign stage first")
        return 1
    summary: dict = {
        "tau": cfg.TAU, "delta": cfg.DELTA, "n_starts": cfg.N_STARTS,
        "declared": {
            "median_construction": cfg.MEDIAN_CONSTRUCTION,
            "p90": "nearest-rank, element ceil(0.9 n) of the sorted list",
            "accepted_optimum": "status ok AND MFILE ifail == 1",
            "pairing": "both-converged pairs (declared primary; both-ok "
                       "published beside)",
            "check1_statistic": ("per-pair relative |d norm_objf| / "
                                 "max(|objf_a|, |objf_b|); the absolute "
                                 "delta is published beside, never accepted "
                                 "against"),
            "objf_floor": (f"{cfg.OBJF_FLOOR_REL:g} relative on norm_objf "
                           f"(O3), applied directly to the per-pair relative "
                           f"statistic"),
            "acceptance": "spread <= max(F x yardstick, floor); yardstick "
                          "= the R->B0 relative spread",
            "cluster_gap": (f"relative gap > "
                            f"{cfg.CLUSTER_GAP_FLOOR_FACTOR:g} x "
                            f"{cfg.OBJF_FLOOR_REL:g} between adjacent "
                            f"sorted accepted optima separates clusters"),
            "deck_invalid_seed": "a seed with no accepted optimum in ANY "
                                 "arm of the deck; excluded from per-arm "
                                 "rates and counted separately (T-b)",
        },
    }
    refusals: list[str] = []
    for deck in cfg.DECKS:
        deck_rows = {}
        for arm in cfg.PHASE_B_ARMS:
            arm_dir = root / deck / arm
            if not arm_dir.exists():
                continue
            rows = []
            for k in range(cfg.N_STARTS):
                p = arm_dir / f"start{k:03d}" / "metrics.json"
                rows.append(_extract(json.loads(p.read_text()))
                            if p.exists() else {"status": "missing"})
            deck_rows[arm] = rows
        if not deck_rows:
            continue
        arms = [a for a in cfg.PHASE_B_ARMS if a in deck_rows]
        deck_summary: dict = {}

        # G7's contract on every ok record
        for arm in arms:
            for k, r in enumerate(deck_rows[arm]):
                if (r.get("status") == "ok"
                        and not r.get("forensics_complete")):
                    refusals.append(
                        f"{deck}/{arm}/start{k:03d}: "
                        f"{r.get('forensics_why')} — the tally REFUSES "
                        f"(G7)")

        # T-b: taxonomy with denominators; the deck-invalid-seed statistic
        invalid_seeds = [
            k for k in range(cfg.N_STARTS)
            if not any(_conv(deck_rows[a][k]) for a in arms)
        ]
        deck_summary["deck_invalid_seeds"] = {
            "seeds": invalid_seeds, "n": len(invalid_seeds),
            "what": summary["declared"]["deck_invalid_seed"],
        }
        valid = [k for k in range(cfg.N_STARTS) if k not in invalid_seeds]
        for arm in arms:
            rows = deck_rows[arm]
            tax: dict = {}
            for r in rows:
                tax[str(r.get("status"))] = tax.get(str(r.get("status")), 0) + 1
            ok_rows = [r for r in rows if r.get("status") == "ok"]
            ifails: dict = {}
            for r in ok_rows:
                ifails[str(r.get("ifail"))] = (
                    ifails.get(str(r.get("ifail")), 0) + 1)
            n_conv_valid = sum(1 for k in valid if _conv(rows[k]))
            deck_summary[arm] = {
                "n_ok": len(ok_rows),
                "n_converged": sum(1 for r in rows if _conv(r)),
                "taxonomy_by_status": tax,
                "taxonomy_ifail_among_ok": ifails,
                "denominator": cfg.N_STARTS,
                "per_arm_failure_rate_excl_deck_invalid": {
                    "n_not_converged": len(valid) - n_conv_valid,
                    "denominator": len(valid),
                },
                "ladder_stage_census": {
                    st: sum(1 for r in rows
                            if r.get("ladder_stage") == st)
                    for st in sorted({r.get("ladder_stage") for r in rows}
                                     - {None})},
                "ifail_mfile_vs_forensics_mismatch": [
                    k for k, r in enumerate(rows)
                    if r.get("status") == "ok"
                    and r.get("forensics_ifail") is not None
                    and r.get("ifail") is not None
                    and float(r["forensics_ifail"]) != float(r["ifail"])],
                "call_models_total": sum(r.get("n_model_calls") or 0
                                         for r in rows),
                "node_calls_total": sum(r.get("node_calls_solve_phase") or 0
                                        for r in rows),
            }

        # T-c: same-optimum check with yardstick, floor, clustering
        def hexf(h):
            return float.fromhex(h) if isinstance(h, str) else None

        pair_defs = {"R->B0": ("R", "B0"), "B0->B1": ("B0", "B1"),
                     "B0->B2": ("B0", "B2"), "B0->B3": ("B0", "B3"),
                     "B2->B3": ("B2", "B3")}
        objf_pairs: dict = {}
        for name, (a, b) in pair_defs.items():
            if a not in deck_rows or b not in deck_rows:
                continue
            deltas, absolute_deltas, base_absobjf, dropped = [], [], [], []
            for k in range(cfg.N_STARTS):
                ra, rb = deck_rows[a][k], deck_rows[b][k]
                if not (_conv(ra) and _conv(rb)):
                    dropped.append({"seed": k,
                                    a: {"status": ra.get("status"),
                                        "ifail": ra.get("ifail")},
                                    b: {"status": rb.get("status"),
                                        "ifail": rb.get("ifail")}})
                    continue
                fa, fb = hexf(ra["norm_objf_hex"]), hexf(rb["norm_objf_hex"])
                if fa is None or fb is None:
                    dropped.append({"seed": k, "why": "no norm_objf hex"})
                    continue
                # EXPERIMENT_PLAN.md §4.2 check 1: the accepted statistic is
                # the PER-PAIR RELATIVE difference, denominator the larger
                # magnitude of the two sides (the same form check 1a already
                # uses for its cluster gaps).  An absolute delta compared
                # against an ensemble-median-scaled floor is a DIFFERENT
                # construction: it is not per-pair, and O3's floor is
                # declared relative.  Orchestrator adjudication 2026-09-04 on
                # A41's reported divergence -- the plan is authoritative, and
                # the absolute delta stays published beside, never accepted
                # against.
                denom = max(abs(fa), abs(fb))
                deltas.append(abs(fb - fa) / denom if denom else 0.0)
                absolute_deltas.append(abs(fb - fa))
                base_absobjf.append(abs(fa))
            deltas.sort()
            absolute_deltas.sort()
            base_absobjf.sort()
            objf_pairs[name] = {
                "statistic": ("per-pair relative: |d norm_objf| / "
                              "max(|objf_a|, |objf_b|)"),
                "n_pairs": len(deltas),
                "n_dropped": len(dropped),
                "dropped_pairs": dropped,
                "median": rank_median(deltas),
                "median_statistics_diagnostic": (
                    statistics.median(deltas) if deltas else None),
                "p90": p90(deltas),
                "max": deltas[-1] if deltas else None,
                "values_published": deltas,
                "floor_rel": cfg.OBJF_FLOOR_REL,
                # published beside; never the acceptance statistic
                "absolute_median": rank_median(absolute_deltas),
                "absolute_p90": p90(absolute_deltas),
                "absolute_max": (absolute_deltas[-1] if absolute_deltas
                                 else None),
                "base_arm_abs_objf_median": rank_median(base_absobjf),
            }
        yard = objf_pairs.get("R->B0")
        for name, e in objf_pairs.items():
            if not name.startswith("B0->") or not yard:
                continue
            if e["median"] is None or yard["median"] is None:
                e["accepted"] = None
                continue
            # both sides relative now, and the floor is the plain declared
            # relative tolerance (O3): spread <= max(F x yardstick, 1e-6)
            bound_med = max(cfg.SIMILARITY_FACTOR_F * yard["median"],
                            cfg.OBJF_FLOOR_REL)
            bound_p90 = max(cfg.SIMILARITY_FACTOR_F * (yard["p90"] or 0.0),
                            cfg.OBJF_FLOOR_REL)
            e["accept_median"] = e["median"] <= bound_med
            e["accept_p90"] = (e["p90"] is not None
                               and e["p90"] <= bound_p90)
            e["bounds"] = {"median": bound_med, "p90": bound_p90}
            e["accepted"] = bool(e["accept_median"] and e["accept_p90"])
        deck_summary["check1_objf_pairs"] = objf_pairs

        # check 1a: multi-attractor clustering and hop rates
        accepted: list[tuple[str, int, float]] = []
        for arm in arms:
            for k in range(cfg.N_STARTS):
                r = deck_rows[arm][k]
                if _conv(r):
                    v = hexf(r["norm_objf_hex"])
                    if v is not None:
                        accepted.append((arm, k, v))
        groups = _clusters([v for _, _, v in accepted])
        cluster_of = {}
        for ci, g in enumerate(groups):
            for idx in g:
                arm, k, _v = accepted[idx]
                cluster_of[(arm, k)] = ci
        cluster_rows = []
        for ci, g in enumerate(groups):
            vals = sorted(accepted[i][2] for i in g)
            by_arm: dict = {}
            for i in g:
                by_arm[accepted[i][0]] = by_arm.get(accepted[i][0], 0) + 1
            cluster_rows.append({"cluster": ci, "n": len(g),
                                 "norm_objf_min": vals[0],
                                 "norm_objf_max": vals[-1],
                                 "by_arm": by_arm})
        hop_rates = {}
        for name, (a, b) in pair_defs.items():
            if a not in deck_rows or b not in deck_rows:
                continue
            both = [k for k in range(cfg.N_STARTS)
                    if (a, k) in cluster_of and (b, k) in cluster_of]
            hops = [k for k in both
                    if cluster_of[(a, k)] != cluster_of[(b, k)]]
            hop_rates[name] = {"n_pairs": len(both), "n_hops": len(hops),
                               "hop_seeds": hops}
        deck_summary["check1a_clusters"] = {
            "n_clusters": len(groups),
            "clusters": cluster_rows,
            "hop_rates_per_pair": hop_rates,
            "comparator": "R->B0's hop rate (plan §4.2 check 1a)",
        }

        # check 2: iteration multiplier, declared nearest-rank median
        iter_pairs: dict = {}
        for name, (a, b) in {"B0->B1": ("B0", "B1"), "B0->B2": ("B0", "B2"),
                             "B0->B3": ("B0", "B3"), "B0->R": ("B0", "R"),
                             "B2->B3": ("B2", "B3")}.items():
            if a not in deck_rows or b not in deck_rows:
                continue
            ratios, fev, dropped = [], [], []
            # EXPERIMENT_PLAN.md §4.2 amendment (2026-09-04): absolute
            # iterations over exactly the ratio-contributing pairs, because a
            # median of per-pair ratios and the ratio of the sums can point in
            # OPPOSITE directions -- V2's lad B0->B1 reads 0.833 as a median
            # and 1.009 as a sum ratio (228 vs 230 iterations), since two
            # seeds blow up and repay what eight save.  Acceptance stays on
            # the median; the sums are published so "typical seed" is never
            # read as "total work".  Contributing seeds are named so a total
            # is never carried across arm pairs with different pair sets.
            iters_a, iters_b, contributing = [], [], []
            for k in range(cfg.N_STARTS):
                ra, rb = deck_rows[a][k], deck_rows[b][k]
                if not (_conv(ra) and _conv(rb)):
                    continue
                ia, ib = ra.get("n_solver_iterations"), rb.get(
                    "n_solver_iterations")
                if ia and ib:
                    ratios.append(ib / ia)
                    iters_a.append(ia)
                    iters_b.append(ib)
                    contributing.append(k)
                else:
                    dropped.append({"seed": k, f"{a}_iters": ia,
                                    f"{b}_iters": ib})
                ma, mb = ra.get("n_model_calls"), rb.get("n_model_calls")
                if ma and mb:
                    fev.append(mb / ma)
            ratios.sort()
            fev.sort()
            med = rank_median(ratios)
            iter_pairs[name] = {
                "n_both_converged": sum(
                    1 for k in range(cfg.N_STARTS)
                    if _conv(deck_rows[a][k]) and _conv(deck_rows[b][k])),
                "n_iter_pairs": len(ratios),
                "dropped_pairs": dropped,
                "median": med,
                "median_statistics_diagnostic": (
                    statistics.median(ratios) if ratios else None),
                "q1_q3": ([ratios[len(ratios) // 4],
                           ratios[3 * len(ratios) // 4]]
                          if len(ratios) >= 4 else None),
                "bound_1p05_met": (med is not None
                                   and med <= cfg.ITER_RATIO_MAX),
                "model_call_ratio_median": rank_median(fev),
                "model_call_ratio_n": len(fev),
                # absolute iterations over the ratio-contributing pairs only
                "arm_a": a,
                "arm_b": b,
                "iters_a_sum": (sum(iters_a) if iters_a else None),
                "iters_b_sum": (sum(iters_b) if iters_b else None),
                "iters_a_median": rank_median(sorted(iters_a)),
                "iters_b_median": rank_median(sorted(iters_b)),
                "iters_sum_ratio": ((sum(iters_b) / sum(iters_a))
                                    if iters_a and sum(iters_a) else None),
                "contributing_seeds": contributing,
                "sum_vs_median_directions_agree": (
                    None if not iters_a or not sum(iters_a) or med is None
                    else ((sum(iters_b) / sum(iters_a) - 1.0) * (med - 1.0)
                          >= 0.0)),
            }
        deck_summary["check2_iteration_multiplier"] = iter_pairs

        # check 3: the lift closed — c93 residual at accepted optima
        c93: dict = {}
        for arm in ("B1", "B2", "B3"):
            if arm not in deck_rows:
                continue
            per_start = []
            for k, r in enumerate(deck_rows[arm]):
                if _conv(r) and r.get("constraint_93"):
                    per_start.append({
                        "seed": k,
                        "residual_s": r["constraint_93"].get("residual_s"),
                        "relative": r["constraint_93"].get(
                            "residual_relative_to_burn_time")})
            res = sorted(abs(x["residual_s"]) for x in per_start
                         if x["residual_s"] is not None)
            c93[arm] = {"n_accepted": len(per_start),
                        "abs_residual_s_median": rank_median(res),
                        "abs_residual_s_max": res[-1] if res else None,
                        "per_start": per_start}
        deck_summary["check3_c93_at_accepted"] = c93

        # check 4: identical-success-set cost sums, both constructions
        cost: dict = {}
        for variant, keep in (
                ("identical_ok_set", lambda r: r.get("status") == "ok"),
                ("identical_converged_set", _conv)):
            common = [k for k in range(cfg.N_STARTS)
                      if all(keep(deck_rows[a][k]) for a in arms)]
            per_arm: dict = {}
            for a in arms:
                ns = sum(deck_rows[a][k].get("node_calls_solve_phase") or 0
                         for k in common)
                mc = sum(deck_rows[a][k].get("n_model_calls") or 0
                         for k in common)
                per_arm[a] = {"node_calls_solve_phase": ns,
                              "model_calls": mc}
            b0 = per_arm.get("B0")
            for a in arms:
                if b0 and b0["node_calls_solve_phase"]:
                    per_arm[a]["node_ratio_vs_B0"] = (
                        per_arm[a]["node_calls_solve_phase"]
                        / b0["node_calls_solve_phase"])
            cost[variant] = {"n_seeds": len(common), "seeds": common,
                             "per_arm": per_arm}
        deck_summary["check4_cost_sums"] = cost

        # T-d: the per-block node-call split, first-class
        block_map: dict[str, str] = {}
        ps_nodes: set = set()
        for arm in ("B3", "B2"):
            if arm not in deck_rows:
                continue
            for k in range(cfg.N_STARTS):
                sched = deck_rows[arm][k].get("arch_block_schedule")
                if sched:
                    for bname, nodes, _it in sched:
                        for n in nodes:
                            block_map[n] = bname
                    ps_nodes = set(
                        (deck_rows[arm][k].get("post_solve_totals") or {})
                        .get("nodes") or [])
                    break
            if block_map:
                break
        block_map.setdefault("pulse", "PULSE")
        common_ok = [k for k in range(cfg.N_STARTS)
                     if all(deck_rows[a][k].get("status") == "ok"
                            for a in arms)]
        per_block: dict = {}
        for a in arms:
            agg: dict[str, int] = {}
            for k in common_ok:
                census = ((deck_rows[a][k].get("node_census") or {})
                          .get("per_node_counted_through_Caller_node") or {})
                for n, c in census.items():
                    blk = ("post_solve" if n in ps_nodes
                           else block_map.get(n, f"UNMAPPED:{n}"))
                    agg[blk] = agg.get(blk, 0) + c
            agg["TOTAL"] = sum(agg.values())
            per_block[a] = agg
        deck_summary["per_block_node_calls_identical_ok_set"] = {
            "what": ("T-d: node calls per block over the identical-ok "
                     "seed set; block membership from the deck's own "
                     "B3/B2 executed schedule, post-solve set from the "
                     "same record; the lifted pulse node is PULSE; "
                     "unmapped nodes are named, never pooled"),
            "n_seeds": len(common_ok),
            "per_arm": per_block}

        # provenance census
        stamps = sorted({f"{r.get('tree_git_head')} "
                         f"dirty={r.get('tree_git_dirty')}"
                         for rows in deck_rows.values() for r in rows
                         if r.get("tree_git_head")})
        deck_summary["provenance_stamps"] = stamps
        summary[deck] = deck_summary

    summary["tally_refusals"] = refusals
    out = PB_RUNS / "tally.json"
    out.write_text(json.dumps(summary, indent=2))
    print(f"\ntally written to {out}")
    if refusals:
        for r in refusals:
            print(f"TALLY REFUSED: {r}")
        return 2
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    default = "all" if cfg.EXECUTION_APPROVED else "smoke"
    ap.add_argument("stage", nargs="?", default=default,
                    choices=["preflight", "gate", "armgate", "g7gate",
                             "smoke", "campaign", "tally", "timing", "all"])
    args = ap.parse_args()
    if args.stage == "preflight":
        return stage_preflight()
    if args.stage == "gate":
        return stage_gate()
    if args.stage == "armgate":
        return stage_armgate()
    if args.stage == "g7gate":
        return stage_g7gate()
    if args.stage == "smoke":
        return stage_smoke()
    if args.stage == "campaign":
        return stage_campaign()
    if args.stage == "tally":
        return stage_tally()
    if args.stage == "timing":
        return stage_timing()
    rc = stage_preflight()
    if rc != 0:
        print("\n'all' stops at preflight while instrumentation is missing.")
        return rc
    return stage_campaign()


if __name__ == "__main__":
    raise SystemExit(main())
