#!/usr/bin/env python
"""V2 Phase B — the optimisation comparison (EXPERIMENT_PLAN.md §4).

Arms R / B0 / B1 / B2 across the three decks, N = 25 seed-paired starts, all
on the a26-mode spec generation.  Stages (protocol §15: every published
number regenerates from this committed entry point; failure paths are
reachable from it):

``preflight``
    The instrumentation and artifact ledger, per arm and deck: which arms
    can run on the committed driver, and which refuse naming their task.
    Exit 0 only when every arm of the full campaign is runnable.
``smoke``
    The machinery test, NOT a measurement: one baseline run per currently
    runnable arm-family — R and B0 on ``st_regression`` (a26 artifacts, the
    real configuration), and B1 on ``large_tokamak_nof`` against the **A18**
    artifacts (machinery only, stamped as such: the lifted-deck +
    ``flat_state`` + lift combination has never been run by any earlier
    task, and its executability is what this smoke establishes; its numbers
    are not for use).  B2 is reported as refused while trust-mode (A34) and
    the post-solve capability (A33) are missing.
``campaign``
    The full 4-arm × 3-deck × 25-start campaign.  Refuses while
    ``EXECUTION_APPROVED`` is False, while any arm's instrumentation is
    missing, or while any deck's a26 write set is absent.
``tally``
    The §4 checks from the on-disk records: paired |Δ norm_objf| (hex kept),
    paired iteration ratios, the A30 failure taxonomy, per-node count sums.

Run from VSCode (F5): no arguments needed — the default stage is ``smoke``
while execution is unapproved, ``all`` after.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import v2_config as cfg  # noqa: E402
import v2_runner as vr  # noqa: E402

PB_RUNS = cfg.RUNS / "phase_b"
DECKS_DIR = cfg.RUNS / "_decks"


# --------------------------------------------------------------------------
# preflight: the ledger
# --------------------------------------------------------------------------


def arm_status(deck: str, arm: str) -> tuple[bool, str]:
    """(runnable, reason).  An arm refuses by name, never silently."""
    if arm in ("B1", "B2") and deck not in cfg.PULSED:
        if arm == "B1":
            return False, "k = 0: B1 degenerates to B0 on this deck (plan §4) — skipped by design"
    if arm != "R":
        if not cfg.ystate_for(deck).exists():
            return False, f"missing {cfg.ystate_for(deck).name}"
        if not cfg.writeset_for(deck).exists():
            led = cfg.INSTRUMENTATION["pulsed_a26_writesets"]
            return False, (f"missing {cfg.writeset_for(deck).name} — "
                           f"{led['task']}")
    if arm == "B2":
        for key in ("trust_mode", "post_solve"):
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
        # Machinery-only: lifted deck + flat_state + lift has no precedent in
        # any merged task; a26 write sets for pulsed decks are A33's, so this
        # smoke runs on the A18 generation and says so in its record.
        dict(deck="large_tokamak_nof", arm="B1",
             outdir=PB_RUNS / "smoke" / "large_tokamak_nof_B1_a18smoke",
             seed=0, delta=None, decks_dir=DECKS_DIR,
             a18_machinery_smoke=True),
    ]
    results = vr.run_pool(jobs)
    verdicts = {}
    failed = 0
    for r in results:
        m = json.loads((Path(r["outdir"]) / "metrics.json").read_text())
        ok = (r["rc"] == 0 and m.get("status") == "ok"
              and m.get("node_calls_solve_phase")
              and (m.get("exact") or {}).get("norm_objf"))
        verdicts[f"{r['deck']}/{r['arm']}"] = {
            "rc": r["rc"], "status": m.get("status"),
            "node_calls_solve_phase": m.get("node_calls_solve_phase"),
            "norm_objf_hex": (m.get("exact") or {}).get("norm_objf"),
            "machinery_ok": bool(ok),
        }
        failed += 0 if ok else 1
    b2_ok, b2_why = arm_status("st_regression", "B2")
    verdicts["B2 (any deck)"] = {"machinery_ok": False, "refused": b2_why}
    (PB_RUNS / "smoke" / "smoke.json").write_text(json.dumps(verdicts, indent=2))
    print(json.dumps(verdicts, indent=2))
    print(f"\nphase B smoke: {len(results) - failed}/{len(results)} machinery "
          f"runs ok; B2 refused as expected ({b2_why}); smoke numbers are "
          f"not measurements")
    return 0 if failed == 0 else 1


# --------------------------------------------------------------------------
# gate: driver neutrality at the V2 commit (plan §6)
# --------------------------------------------------------------------------

#: The three exact fields the gate compares — counts and a bit-comparison.
GATE_FIELDS = ("node_calls_solve_phase", "n_model_calls", "norm_objf_hex")


def _gate_extract(m: dict) -> dict:
    return {
        "node_calls_solve_phase": m.get("node_calls_solve_phase"),
        "n_model_calls": m.get("n_model_calls"),
        "norm_objf_hex": (m.get("exact") or {}).get("norm_objf"),
    }


def stage_gate() -> int:
    """R start000 per deck must reproduce A28's recorded R start000
    bit-for-bit on the current (V2) driver.

    R sets no architecture switch, so its path must be untouched by every
    driver change any V2 task merges — this is the strongest neutrality
    statement available, and it uses A28's records directly (R reads no
    ystate artifact, so the A18/a26 generation change cannot reach it).
    Teeth: each field's comparator, fed a minimally perturbed value, must
    trip (protocol §12 — a gate is shown able to fail before its zeros
    mean anything).
    """
    a28 = cfg.TREE / "arch_surgery" / "idf_probe" / "runs" / "a28" / "h5"
    (cfg.RUNS / "_mplconfig").mkdir(parents=True, exist_ok=True)
    record: dict = {"gate": "V2 driver neutrality: R start000 vs A28 (protocol §12)"}
    all_pass = True
    for deck in cfg.DECKS:
        ref_path = a28 / deck / "R" / "start000" / "metrics.json"
        if not ref_path.exists():
            record[deck] = {"verdict": "FAIL", "reason": f"no A28 reference at {ref_path}"}
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
    (PB_RUNS / "gate" / "gate.json").write_text(json.dumps(record, indent=2))
    print(f"\nphase B driver-neutrality gate: "
          f"{'PASS' if all_pass else 'FAIL'} "
          f"(record: {PB_RUNS / 'gate' / 'gate.json'})")
    return 0 if all_pass else 1


def stage_armgate() -> int:
    """The combined-switch equivalence gate (post-merge integration check).

    B2 runs trust mode AND the post-solve exclusion together — a pairing
    neither A33 nor A34 gated alone.  A33 proved the exclusion behaviour-
    neutral under the verified outer loop; this gate proves the same under
    trust mode: per deck, one B2-config run WITH the post-solve artifact vs
    one WITHOUT (both trust) must agree bit-for-bit on everything except
    the suppressed nodes' own calls.  Teeth: each comparator fed a
    perturbed reading must trip.
    """
    (cfg.RUNS / "_mplconfig").mkdir(parents=True, exist_ok=True)
    vr.derive_lifted_decks(DECKS_DIR)
    record: dict = {"gate": "B2 combined-switch equivalence: post-solve ON vs "
                            "OFF under trust mode (per deck)"}
    all_pass = True
    for deck in cfg.DECKS:
        pair = {}
        for tag, with_ps in (("with", True), ("without", False)):
            env_override = None if with_ps else {"PROCESS_ARCH_POST_SOLVE": None}
            r = vr.run_job(deck, "B2",
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
            "n_call_models": ta.get("n_call_models") == tb.get("n_call_models"),
            "outer_pass_hist": (ta.get("outer_pass_hist")
                                == tb.get("outer_pass_hist")),
            "exit_audit_hex": ((a.get("exit_audit") or {}).get("residual_max_hex")
                               == (b.get("exit_audit") or {}).get("residual_max_hex")),
            "statuses_ok": (a.get("status") == "ok" and b.get("status") == "ok"),
        }
        teeth = {
            "norm_objf_hex": (((a.get("exact") or {}).get("norm_objf") or "") + "0")
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
    (PB_RUNS / "armgate" / "armgate.json").write_text(
        json.dumps(record, indent=2))
    print(f"\nB2 combined-switch gate: {'PASS' if all_pass else 'FAIL'}")
    return 0 if all_pass else 1


# --------------------------------------------------------------------------
# campaign and tally
# --------------------------------------------------------------------------


def stage_campaign() -> int:
    if not cfg.EXECUTION_APPROVED:
        print("REFUSED: EXPERIMENT_PLAN.md is a draft — execution is not "
              "approved (v2_config.EXECUTION_APPROVED).  Run 'smoke'.")
        return 3
    if stage_preflight() != 0:
        print("REFUSED: instrumentation or artifacts missing — see the "
              "ledger above.")
        return 3
    if stage_gate() != 0:
        print("REFUSED: the driver-neutrality gate failed — that failure is "
              "the result; nothing runs on an ungated driver.")
        return 1
    if stage_armgate() != 0:
        print("REFUSED: the B2 combined-switch equivalence gate failed — "
              "that failure is the result.")
        return 1
    vr.derive_lifted_decks(DECKS_DIR)
    jobs = []
    for deck in cfg.DECKS:
        for arm in cfg.PHASE_B_ARMS:
            ok, why = arm_status(deck, arm)
            if not ok:
                continue  # only the by-design k=0 A1 skip reaches here
            for k in range(cfg.N_STARTS):
                jobs.append(dict(
                    deck=deck, arm=arm,
                    outdir=PB_RUNS / "campaign" / deck / arm / f"start{k:03d}",
                    seed=k, delta=cfg.DELTA, decks_dir=DECKS_DIR,
                    resume=True,
                ))
    print(f"campaign: {len(jobs)} runs, {cfg.WORKERS} workers")
    vr.run_pool(jobs)
    return stage_tally()


def _extract(m: dict) -> dict:
    return {
        "status": m.get("status"),
        "ifail": (m.get("mfile") or {}).get("ifail"),
        "norm_objf_hex": (m.get("exact") or {}).get("norm_objf"),
        "n_solver_iterations": m.get("n_solver_iterations"),
        "n_model_calls": m.get("n_model_calls"),
        "node_calls_solve_phase": m.get("node_calls_solve_phase"),
        "node_census": m.get("node_census"),
        "constraint_93": m.get("constraint_93"),
        "exit_audit": m.get("exit_audit"),
        "entry_census": m.get("entry_census"),
    }


def stage_tally() -> int:
    """The §4 checks from on-disk records.  Every requested start is a row —
    a denominator that shrinks without saying so is trap T11."""
    root = PB_RUNS / "campaign"
    if not root.exists():
        print("no campaign records — run the campaign stage first")
        return 1
    summary: dict = {"tau": cfg.TAU, "delta": cfg.DELTA,
                     "n_starts": cfg.N_STARTS}
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
        deck_summary: dict = {}
        for arm, rows in deck_rows.items():
            n_ok = sum(1 for r in rows if r.get("status") == "ok")
            taxonomy: dict = {}
            for r in rows:
                taxonomy[str(r.get("status"))] = (
                    taxonomy.get(str(r.get("status")), 0) + 1)
            deck_summary[arm] = {
                "n_ok": n_ok, "taxonomy": taxonomy,
                "call_models_total": sum(r.get("n_model_calls") or 0
                                         for r in rows),
                "node_calls_total": sum(r.get("node_calls_solve_phase") or 0
                                        for r in rows),
            }
        # paired iteration ratios and objective pairs against A0
        base = deck_rows.get("B0")
        if base:
            for arm in ("B1", "B2", "R"):
                rows = deck_rows.get(arm)
                if not rows:
                    continue
                pairs, obj_pairs = [], []
                for rb, ra in zip(base, rows, strict=True):
                    if rb.get("status") == "ok" and ra.get("status") == "ok":
                        ib, ia = (rb.get("n_solver_iterations"),
                                  ra.get("n_solver_iterations"))
                        if ib and ia:
                            pairs.append(ia / ib)
                        obj_pairs.append((rb.get("norm_objf_hex"),
                                          ra.get("norm_objf_hex")))
                pairs.sort()
                med = pairs[len(pairs) // 2] if pairs else None
                deck_summary[f"B0->{arm}"] = {
                    "n_pairs": len(pairs),
                    "iter_ratio_median": med,
                    "iter_ratio_q1_q3": ([pairs[len(pairs) // 4],
                                          pairs[3 * len(pairs) // 4]]
                                         if len(pairs) >= 4 else None),
                    "iter_bound_1p05_met": (med is not None
                                            and med <= cfg.ITER_RATIO_MAX),
                    "norm_objf_hex_equal": sum(
                        1 for a, b in obj_pairs if a and a == b),
                    "norm_objf_pairs": len(obj_pairs),
                }
        summary[deck] = deck_summary
    out = PB_RUNS / "tally.json"
    out.write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    print(f"\ntally written to {out} (the |Δ norm_objf| yardstick — the "
          f"R->A0 spread — and the audit-based checks are computed at "
          f"analysis time from these records)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    default = "all" if cfg.EXECUTION_APPROVED else "smoke"
    ap.add_argument("stage", nargs="?", default=default,
                    choices=["preflight", "gate", "armgate", "smoke",
                             "campaign", "tally", "all"])
    args = ap.parse_args()
    if args.stage == "preflight":
        return stage_preflight()
    if args.stage == "gate":
        return stage_gate()
    if args.stage == "armgate":
        return stage_armgate()
    if args.stage == "smoke":
        return stage_smoke()
    if args.stage == "campaign":
        return stage_campaign()
    if args.stage == "tally":
        return stage_tally()
    rc = stage_preflight()
    if rc != 0:
        print("\n'all' stops at preflight while instrumentation is missing.")
        return rc
    return stage_campaign()


if __name__ == "__main__":
    raise SystemExit(main())
