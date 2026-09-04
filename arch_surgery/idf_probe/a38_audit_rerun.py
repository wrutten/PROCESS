#!/usr/bin/env python
"""A38 (audit-rerun) -- V2's Phase A design re-run unchanged under a corrected
similarity audit.

The question.  V2's Phase A similarity criterion (arms within a factor F = 10
of one another in audited distance to the fixed point) FAILED on every deck,
and the committed argmax census showed why: 75 of 75 A1 audit maxima were
components written by the post-solve nodes -- nodes A1 deliberately never
executes inside the measured call, whose delta-perturbed outputs the
whole-state audit still measures.  That is an accounting artifact of the
suppression, not a property of the block architecture.  The corrected
statistic is the same audit over the components the solve phase actually
writes (the in-loop write set).  V2's records held only max / argmax / count,
so the correction is a RE-RUN of the same design, not a re-tally.

What this script does (every published number of the task comes from it):

  preflight  -- the licence: the model tree, the driver tree, the fixed-point
                package and the data artifacts must be hash-identical between
                this tree and the two commits V2's Phase A records stamp
                (ba69c05d / 6d9ff4b9); V2's 150 records must be present and
                ok; the excluded component set per deck is derived and printed.
  smoke      -- the whole path on st_regression, seeds 1..2 (machinery only).
  campaign   -- per deck: the A0 cold reference, A36's entry-state and warm
                equivalence gates (V2's own functions, imported), the
                restricted-audit teeth (a post-solve-owned component doctored
                in the entry snapshot must move the whole-state audit and NOT
                the restricted one; an in-loop component must move both), then
                seeds 1..25 x {A0, A1} seed-paired from the reference snapshot
                at delta = 0.10 -- V2's design, V2's arms, V2's stream.
  tally      -- per deck: the identity gate against V2's records (counts,
                sweeps, objective hex, whole-state audit hex and the full exit
                state bit-for-bit, per run), the unrestricted similarity
                reproduced against V2's tally, the RESTRICTED similarity at
                median and p90 against F = 10, the per-run carrier closure
                against A35's coefficients, the parser teeth, cost ratio and
                weighting bracket (must reproduce V2's 0.522 / 0.568 / 0.502).

Pre-declared expectation (V3 plan section 4.1): the restricted similarity
still FAILS, on the carrier term alone -- A1 about 5e-4 scaled against A0
about 5e-9 on the traced decks.

Design constraints honoured: V2's directory is not edited (its machinery is
imported); the only runner change is additive (v2_eval_one.py writes the
per-component residual vector and, when asked, a restricted statistic); every
run is a fresh subprocess in its own directory with the exact tree asserted;
runs never retried; bulk artifacts under runs/a38/ stay untracked; V2's
records in the main checkout are read read-only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import statistics
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent            # arch_surgery/idf_probe
TREE = HERE.parent.parent
V2DIR = TREE / "arch_surgery" / "MDA_partitioning_experiment_v2"
sys.path.insert(0, str(V2DIR))
sys.path.insert(0, str(HERE))

import v2_config as cfg  # noqa: E402
import phase_a as pa  # noqa: E402  -- V2's Phase A machinery, imported, never edited
from v2_eval_one import perturb_factor  # noqa: E402

ROOT = HERE / "runs" / "a38"
#: V2's records, read read-only from the main checkout (never from a live
#: regeneration): the identity gate's reference.
MAIN_CHECKOUT = Path("/home/wrutten/projects/PROCESS_surgery")
V2_RECORDS = (MAIN_CHECKOUT / "arch_surgery" / "MDA_partitioning_experiment_v2"
              / "runs" / "phase_a")
V2_CAMPAIGN_COMMITS = ("ba69c05d", "6d9ff4b9")
LICENSED_TREES = ("process", "arch_surgery/fixedpoint", "arch_surgery/docs/data")
SEEDS = tuple(range(1, cfg.N_STARTS + 1))
ARMS = ("A0", "A1")
PAIR = ("build.dr_fw_inboard", "build.dr_fw_outboard")
KNOWN_CUT = PAIR + ("pf_power.vpfskv",)
#: A35's coefficient-exact closure: deck -> (top mover, raw image of the
#: pair's displacement).  lad has no traced coefficient (A35 scope gap).
CARRIER = {
    "large_tokamak_nof": ("build.dz_tf_upper_lower_midplane",
                          lambda din, dout: 0.5 * (din + dout)),
    "st_regression": ("build.dr_shld_vv_gap_outboard",
                      lambda din, dout: -dout),
}
TEETH_FACTOR = pa.TEETH_FACTOR


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=str(TREE), capture_output=True,
                          text=True, check=True).stdout.strip()


def _load(p: Path) -> dict:
    return json.loads(Path(p).read_text()) if Path(p).exists() else {}


def _metrics(outdir) -> dict:
    return _load(Path(outdir) / "metrics.json") or {"status": "missing"}


def _stamp(m: dict) -> dict:
    return {"tree_git_head": m.get("tree_git_head"),
            "tree_git_dirty": m.get("tree_git_dirty")}


def spec_components(deck: str) -> list[dict]:
    return json.loads(cfg.ystate_for(deck).read_text())["components"]


def excluded_keys(deck: str) -> tuple[set, list]:
    """The restricted audit's excluded set, derived exactly as the runner
    derives it: post-solve NODES -> written fields (run-time census) ->
    intersected with the a26 spec's keys."""
    nodes = json.loads(cfg.postsolve_for(deck).read_text())["post_solve_nodes"]
    census = json.loads((cfg.DATA / "node_writesets.json").read_text())
    per = census["per_scenario"][deck]
    wb = per["writes_by_node"]
    known = set(per.get("node_module") or ()) | set(wb)
    keys = {c["key"] for c in spec_components(deck)}
    excl: set = set()
    for n in nodes:
        if n not in known:
            raise RuntimeError(f"post-solve node {n!r} unknown to the {deck} write census")
        excl |= set(wb.get(n, ()))   # a known node without an entry wrote nothing (V5)
    return excl & keys, nodes


def _pool(jobs: list[dict]) -> list[dict]:
    """W concurrent runs; never retried (a crash is a taxonomy row)."""
    out = []
    with ThreadPoolExecutor(max_workers=cfg.WORKERS) as pool:
        futs = [pool.submit(run_eval_job, **j) for j in jobs]
        for f in futs:
            out.append(f.result())
    return out


# --------------------------------------------------------------------------
# one isolated single-eval run, with the restricted audit requested
# --------------------------------------------------------------------------


def run_eval_job(deck: str, arm: str, outdir: Path, *, entry_state=None,
                 delta=None, seed: int = 0, pin_hex=None, resume: bool = False,
                 timeout: int = 3600) -> dict:
    """phase_a.run_eval_job's contract plus ``--audit-exclude-postsolve``:
    the deck's committed post-solve artifact, the same file for BOTH arms
    (the excluded set is a property of the deck, not of the arm, or the two
    arms' statistics would not be over the same components)."""
    outdir = Path(outdir)
    mp = outdir / "metrics.json"
    if resume and mp.exists():
        prev = _load(mp)
        if (prev.get("status") == "ok" and prev.get("a38_arm") == arm
                and prev.get("a38_deck") == deck
                and prev.get("a38_seed") == seed
                and prev.get("a38_delta") == delta
                and prev.get("a38_pin_hex") == pin_hex
                and (outdir / "audit_residual.json").exists()):
            print(f"  {deck:24s} {arm:3s} seed={seed:<3d} resumed", flush=True)
            return {"deck": deck, "arm": arm, "seed": seed, "rc": 0,
                    "outdir": str(outdir), "status": "ok", "resumed": True}
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
    env = pa.env_for_phase_a(deck, arm, pin_hex=pin_hex)
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
    if not mp.exists():
        mp.write_text(json.dumps({
            "scenario": deck, "status": "timeout" if rc == 124 else "no_metrics",
            "returncode": rc, "delta": delta, "seed": seed}, indent=2))
    rec = _load(mp)
    rec.update({"a38_arm": arm, "a38_deck": deck, "a38_seed": seed,
                "a38_delta": delta, "a38_tau": cfg.TAU, "a38_pin_hex": pin_hex,
                "a38_entry_state": str(entry_state) if entry_state else None,
                # V2's tally reads these names; kept so V2 helpers apply.
                "v2_phase": "A", "v2_arm": arm, "v2_deck": deck,
                "v2_seed": seed, "v2_delta": delta, "v2_tau": cfg.TAU,
                "v2_pin_hex": pin_hex, "v2_machinery_smoke": False})
    mp.write_text(json.dumps(rec, indent=2))
    print(f"  {deck:24s} {arm:3s} seed={seed:<3d} rc={rc} "
          f"status={rec.get('status')} {time.perf_counter() - t0:6.1f}s "
          f"(wall clock is progress information, not a measurement)",
          flush=True)
    return {"deck": deck, "arm": arm, "seed": seed, "rc": rc,
            "outdir": str(outdir), "status": rec.get("status")}


# --------------------------------------------------------------------------
# preflight: the licence and the excluded sets
# --------------------------------------------------------------------------


def stage_preflight() -> int:
    ROOT.mkdir(parents=True, exist_ok=True)
    head = _git("rev-parse", "HEAD")
    rec: dict = {"stage": "preflight", "tree": str(TREE), "head": head,
                 "licence": {}, "v2_records": {}, "excluded": {}}
    ok = True
    print("A38 preflight -- licence: sub-tree hashes vs V2's campaign commits")
    for sub in LICENSED_TREES:
        h = _git("rev-parse", f"HEAD:{sub}")
        ref = {c: _git("rev-parse", f"{c}:{sub}") for c in V2_CAMPAIGN_COMMITS}
        same = all(v == h for v in ref.values())
        rec["licence"][sub] = {"head": h, **ref, "identical": same}
        ok &= same
        print(f"  {'ok ' if same else 'FAIL'} {sub}: {h[:12]} "
              f"{'==' if same else '!='} {[v[:12] for v in ref.values()]}")
    # the runner itself: the diff against the campaign commits must be the
    # additive audit change only -- shown, not asserted (the identity gate
    # in the tally is what pins the claim).
    diff = subprocess.run(
        ["git", "diff", "--stat", V2_CAMPAIGN_COMMITS[0], "HEAD", "--",
         "arch_surgery/idf_probe/v2_eval_one.py", "arch_surgery/idf_probe/run_one.py",
         "arch_surgery/MDA_partitioning_experiment_v2/phase_a.py",
         "arch_surgery/MDA_partitioning_experiment_v2/v2_config.py"],
        cwd=str(TREE), capture_output=True, text=True).stdout.strip()
    rec["runner_diff_stat_vs_v2"] = diff
    print("  runner diff vs V2 campaign commit:\n    " + (diff.replace("\n", "\n    ") or "(none)"))

    n_ok = 0
    stamps: dict = {}
    for deck in cfg.DECKS:
        for arm in ARMS:
            for k in SEEDS:
                m = _load(V2_RECORDS / "campaign" / deck / arm / f"start{k:03d}" / "metrics.json")
                if m.get("status") == "ok":
                    n_ok += 1
                key = f"{deck}@{(m.get('tree_git_head') or '')[:8]} dirty={m.get('tree_git_dirty')}"
                stamps[key] = stamps.get(key, 0) + 1
    rec["v2_records"] = {"path": str(V2_RECORDS), "n_ok": n_ok,
                         "expected": len(cfg.DECKS) * len(ARMS) * len(SEEDS),
                         "stamps": stamps,
                         "tally_present": (V2_RECORDS / "tally.json").exists()}
    good = n_ok == rec["v2_records"]["expected"] and rec["v2_records"]["tally_present"]
    ok &= good
    print(f"  {'ok ' if good else 'FAIL'} V2 records: {n_ok}/{rec['v2_records']['expected']} ok; stamps {stamps}")

    for deck in cfg.DECKS:
        excl, nodes = excluded_keys(deck)
        n_spec = len(spec_components(deck))
        rec["excluded"][deck] = {
            "post_solve_nodes": nodes, "n_spec": n_spec, "n_excluded": len(excl),
            "n_kept": n_spec - len(excl),
            "excluded_sha256": hashlib.sha256("\n".join(sorted(excl)).encode()).hexdigest(),
            "known_cut_in_kept": [k for k in KNOWN_CUT if k not in excl],
        }
        print(f"  {deck:24s} spec {n_spec}, excluded {len(excl)} by {nodes}, "
              f"kept {n_spec - len(excl)}")
    for deck in cfg.DECKS:
        for art in (cfg.ystate_for(deck), cfg.writeset_for(deck), cfg.postsolve_for(deck)):
            if not art.exists():
                ok = False
                print(f"  FAIL missing artifact {art}")
    rec["ready"] = ok
    (ROOT / "preflight.json").write_text(json.dumps(rec, indent=2))
    print(f"A38 preflight: {'READY' if ok else 'NOT READY'}")
    return 0 if ok else 3


# --------------------------------------------------------------------------
# the restricted-audit teeth (protocol section 12)
# --------------------------------------------------------------------------


def _doctor(ref_snap: dict, deck: str, owned, candidates, out: Path) -> dict:
    """A copy of the reference snapshot with ONE eligible component from
    ``candidates`` (in order) multiplied by TEETH_FACTOR: continuous float
    scalar, non-zero, not owned by the design vector."""
    cats = {c["key"]: c["category"] for c in spec_components(deck)}
    owned = set(owned or ())
    st = ref_snap["state"]

    def eligible(name):
        r = st.get(name)
        return bool(r and r.get("k") == "f" and float.fromhex(r["hex"]) != 0.0
                    and cats.get(name) == "continuous" and name not in owned)

    comp = next((c for c in candidates if eligible(c)), None)
    if comp is None:
        raise RuntimeError("no eligible component among the candidates for the teeth")
    d = json.loads(json.dumps(ref_snap))
    before = float.fromhex(d["state"][comp]["hex"])
    after = before * TEETH_FACTOR
    d["state"][comp]["hex"] = after.hex()
    out.write_text(json.dumps(d))
    return {"component": comp, "factor": TEETH_FACTOR,
            "before_hex": before.hex(), "after_hex": after.hex()}


def restricted_teeth(deck: str, droot: Path, ref: dict) -> dict:
    """Three A1 runs from the reference snapshot, unperturbed, pinned:
    a restricted baseline; one with a post-solve-owned component doctored
    (whole-state audit must move by exactly the doctored displacement, the
    restricted audit must be bit-identical to the baseline); one with an
    in-loop component doctored (both must move)."""
    root = droot / "restricted_teeth"
    root.mkdir(parents=True, exist_ok=True)
    ref_m = ref["metrics"]
    snap_path = Path(ref["outdir"]) / "y_exit.json"
    snap = json.loads(snap_path.read_text())
    owned = ref_m.get("spec_keys_owned_by_x") or []
    pin_hex = ref_m.get("t_plant_pulse_burn_hex") if deck in cfg.PULSED else None
    excl, _nodes = excluded_keys(deck)
    scale = {c["key"]: c.get("scale") for c in spec_components(deck)}  # discrete: no scale

    base = run_eval_job(deck, "A1", root / "A1_warm_restricted",
                        entry_state=snap_path, seed=0, pin_hex=pin_hex)
    bm = _metrics(base["outdir"])
    b_aud = bm.get("exit_audit") or {}
    b_res = b_aud.get("restricted") or {}

    # (a) a post-solve-owned component: prefer costs.*, then any excluded key
    cand_ps = sorted(k for k in excl if k.startswith("costs.")) + sorted(excl)
    doc_ps = _doctor(snap, deck, owned, cand_ps, root / "doctored_postsolve.json")
    ps = run_eval_job(deck, "A1", root / "A1_doctored_postsolve",
                      entry_state=root / "doctored_postsolve.json", seed=0,
                      pin_hex=pin_hex)
    pm = _metrics(ps["outdir"])
    p_aud = pm.get("exit_audit") or {}
    p_res = p_aud.get("restricted") or {}
    p_vec = _load(Path(ps["outdir"]) / "audit_residual.json").get("scaled") or {}
    comp = doc_ps["component"]
    expected = abs(float.fromhex(doc_ps["after_hex"]) - float.fromhex(doc_ps["before_hex"])) / scale[comp]
    got = p_vec.get(comp)
    ps_checks = {
        "run_ok": pm.get("status") == "ok",
        "doctored_component_is_excluded": comp in excl,
        "doctored_component_residual_equals_displacement": (
            got is not None and expected > 0
            and abs(got - expected) <= 1e-9 * expected),
        "whole_state_max_moved": p_aud.get("residual_max_hex") != b_aud.get("residual_max_hex"),
        "whole_state_max_at_least_displacement": (
            p_aud.get("residual_max") is not None and p_aud["residual_max"] >= expected * (1 - 1e-9)),
        "restricted_max_bit_identical_to_baseline": (
            p_res.get("max_hex") is not None and p_res.get("max_hex") == b_res.get("max_hex")),
        "restricted_argmax_identical_to_baseline": p_res.get("argmax") == b_res.get("argmax"),
    }

    # (b) an in-loop component: prefer the reference audit's own argmax
    # The reference audit's own argmax is preferred as A36 does, but ONLY
    # if it is an in-loop component: on large_tokamak_nof that argmax is
    # costs.coecap, a post-solve-owned field, and doctoring it would test
    # the wrong thing (found by the tooth itself failing on that deck).
    ref_argmax = ((ref_m.get("exit_audit") or {}).get("brief") or {}).get("argmax")
    kept = [c["key"] for c in spec_components(deck) if c["key"] not in excl]
    cand_il = [c for c in ([ref_argmax] if ref_argmax else []) + kept if c not in excl]
    doc_il = _doctor(snap, deck, owned, cand_il, root / "doctored_inloop.json")
    il = run_eval_job(deck, "A1", root / "A1_doctored_inloop",
                      entry_state=root / "doctored_inloop.json", seed=0,
                      pin_hex=pin_hex)
    im = _metrics(il["outdir"])
    i_aud = im.get("exit_audit") or {}
    i_res = i_aud.get("restricted") or {}
    # OR semantics, as A36's entry-gate tooth (V2 launch fix 2): a doctored
    # in-loop component forces the owning block's inner solve to re-converge
    # it, which costs at least one extra block sweep; the re-converged exit
    # may differ from the baseline only in its last bits, or -- at a
    # bit-exact fixed point -- not at all.  The tooth binds on "the
    # restricted audit moved OR the measured call did more work".
    b_sw = (bm.get("module_solve_stats") or {}).get("block_sweeps")
    i_sw = (im.get("module_solve_stats") or {}).get("block_sweeps")
    il_checks = {
        "run_ok": im.get("status") == "ok",
        "doctored_component_is_in_loop": doc_il["component"] not in excl,
        "whole_state_max_moved": i_aud.get("residual_max_hex") != b_aud.get("residual_max_hex"),
        "restricted_max_moved": i_res.get("max_hex") != b_res.get("max_hex"),
        "more_block_sweeps_than_baseline": (
            isinstance(b_sw, int) and isinstance(i_sw, int) and i_sw > b_sw),
    }
    il_checks["restricted_moved_or_more_work"] = bool(
        il_checks["restricted_max_moved"] or il_checks["more_block_sweeps_than_baseline"])
    il_binding = {k: il_checks[k] for k in (
        "run_ok", "doctored_component_is_in_loop", "restricted_moved_or_more_work")}
    record = {
        "gate": ("A38 restricted-audit teeth: the restricted statistic must be "
                 "blind to a post-solve-owned displacement and sighted to an "
                 "in-loop one (protocol section 12)"),
        "baseline": {"outdir": base["outdir"], "status": bm.get("status"),
                     "whole_max_hex": b_aud.get("residual_max_hex"),
                     "restricted": b_res, **_stamp(bm)},
        "postsolve_doctored": {"doctored": doc_ps, "expected_scaled": expected,
                               "measured_scaled": got,
                               "whole_max_hex": p_aud.get("residual_max_hex"),
                               "restricted": p_res, "checks": ps_checks, **_stamp(pm)},
        "inloop_doctored": {"doctored": doc_il,
                            "whole_max_hex": i_aud.get("residual_max_hex"),
                            "restricted": i_res, "checks": il_checks, **_stamp(im)},
    }
    record["inloop_doctored"]["binding_checks"] = il_binding
    record["inloop_doctored"]["block_sweeps"] = {"baseline": b_sw, "doctored": i_sw}
    record["verdict"] = "PASS" if all(ps_checks.values()) and all(il_binding.values()) else "FAIL"
    (root / "gate.json").write_text(json.dumps(record, indent=2))
    print(f"  restricted teeth {deck}: {record['verdict']} "
          f"(post-solve doctored {comp}: whole {p_aud.get('residual_max_hex')} vs base "
          f"{b_aud.get('residual_max_hex')}, restricted {p_res.get('max_hex')} vs base "
          f"{b_res.get('max_hex')}; in-loop doctored {doc_il['component']}: restricted "
          f"{i_res.get('max_hex')})", flush=True)
    return record


# --------------------------------------------------------------------------
# the campaign
# --------------------------------------------------------------------------


def deck_campaign(deck: str, droot: Path, seeds) -> tuple[dict, bool]:
    droot.mkdir(parents=True, exist_ok=True)
    rec: dict = {"deck": deck}
    print(f"\n{deck}: reference (A0 cold deck point, unperturbed)", flush=True)
    ref_run = run_eval_job(deck, "A0", droot / "reference", seed=0)
    ref_m = _metrics(ref_run["outdir"])
    ref = {"outdir": ref_run["outdir"], "metrics": ref_m}
    rec["reference"] = {
        "outdir": ref_run["outdir"], "status": ref_m.get("status"),
        "cold_start_node_calls": ref_m.get("node_calls_single_eval"),
        "cold_start_sweeps": ref_m.get("n_model_calls_sweeps"),
        "audit_residual_max_hex": (ref_m.get("exit_audit") or {}).get("residual_max_hex"),
        "t_plant_pulse_burn_hex": ref_m.get("t_plant_pulse_burn_hex"),
        **_stamp(ref_m)}
    if ref_m.get("status") != "ok":
        rec["refused"] = "the A0 reference did not converge at the deck point"
        return rec, False
    snap_path = Path(ref_run["outdir"]) / "y_exit.json"

    # V2's own gates, V2's own functions (they use phase_a.run_eval_job:
    # unrestricted runs, which is all these gates need).
    rec["entry_gate"] = pa.entry_gate(deck, droot, ref, False)
    if rec["entry_gate"]["verdict"] != "PASS":
        rec["refused"] = "entry gate FAILED"
        return rec, False
    rec["warm_gate"] = pa.warm_gate(deck, droot, ref, False)
    if rec["warm_gate"]["verdict"] != "PASS":
        rec["refused"] = "warm equivalence gate FAILED -- that failure is the result"
        return rec, False
    rec["restricted_teeth"] = restricted_teeth(deck, droot, ref)
    if rec["restricted_teeth"]["verdict"] != "PASS":
        rec["refused"] = "restricted-audit teeth FAILED -- the corrected statistic is not trusted"
        return rec, False

    ref_burn_hex = ref_m.get("t_plant_pulse_burn_hex")
    jobs, pins = [], {}
    for k in seeds:
        pin_hex = None
        if deck in cfg.PULSED:
            pin_hex = (float.fromhex(ref_burn_hex)
                       * perturb_factor(k, pa.PIN_COMPONENT, cfg.DELTA)).hex()
            pins[str(k)] = pin_hex
        for arm in ARMS:
            jobs.append(dict(deck=deck, arm=arm, outdir=droot / arm / f"start{k:03d}",
                             entry_state=snap_path, delta=cfg.DELTA, seed=k,
                             pin_hex=pin_hex if arm == "A1" else None, resume=True))
    print(f"{deck}: campaign -- {len(jobs)} runs ({len(list(seeds))} seeds x 2 arms), "
          f"{cfg.WORKERS} workers", flush=True)
    results = _pool(jobs)
    rec["seed_pins_hex"] = pins or None
    rec["runs"] = {f"{r['arm']}/start{r['seed']:03d}": {"rc": r["rc"], "status": r.get("status")}
                   for r in results}
    rec["pairing"] = pa.pairing_check(droot, seeds)
    (droot / "pairing.json").write_text(json.dumps(rec["pairing"], indent=2))
    if not rec["pairing"]["all_identical"]:
        rec["pairing_failure"] = "entry states not bit-identical across arms on every seed"
        return rec, False
    print(f"{deck}: pairing {rec['pairing']['n_seeds_bit_identical']}/"
          f"{rec['pairing']['n_seeds_compared']} seeds bit-identical", flush=True)
    return rec, True


def _campaign(root: Path, decks, seeds, smoke: bool) -> int:
    if stage_preflight() != 0:
        print("\nREFUSED: preflight not ready")
        return 3
    root.mkdir(parents=True, exist_ok=True)
    (cfg.RUNS / "_mplconfig").mkdir(parents=True, exist_ok=True)
    record: dict = {"task": "A38 audit-rerun", "machinery_smoke": smoke,
                    "design": "V2 Phase A, unchanged (warm-entry, delta-stream)",
                    "tau": cfg.TAU, "delta": cfg.DELTA, "arms": list(ARMS),
                    "decks": list(decks), "seeds": list(seeds), "per_deck": {}}
    for deck in decks:
        drec, ok = deck_campaign(deck, root / deck, seeds)
        record["per_deck"][deck] = drec
        (root / "campaign.json").write_text(json.dumps(record, indent=2))
        if not ok:
            record["stopped_at"] = deck
            (root / "campaign.json").write_text(json.dumps(record, indent=2))
            print(f"\nA38 campaign STOPPED at {deck}: {drec.get('refused') or drec.get('pairing_failure')}")
            return 1
    print(f"\nA38 campaign complete: {len(record['per_deck'])} decks; records under {root}")
    return 0


# --------------------------------------------------------------------------
# the tally
# --------------------------------------------------------------------------


def _p90(vals: list) -> float:
    return vals[max(0, math.ceil(0.9 * len(vals)) - 1)]


def _dist(vals: list) -> dict:
    vals = sorted(vals)
    return {"n": len(vals), "values": vals, "values_hex": [float(v).hex() for v in vals],
            "median": statistics.median(vals) if vals else None,
            "p90": _p90(vals) if vals else None}


def _similarity(d0: dict, d1: dict) -> dict:
    med_ok, med_why = pa._similar(d0["median"], d1["median"], cfg.SIMILARITY_FACTOR_F)
    p90_ok, p90_why = pa._similar(d0["p90"], d1["p90"], cfg.SIMILARITY_FACTOR_F)
    return {"median_within_F": {"ok": med_ok, "detail": med_why},
            "p90_within_F": {"ok": p90_ok, "detail": p90_why},
            "similar": bool(med_ok and p90_ok)}


def _identity_vs_v2(deck: str, droot: Path, seeds) -> dict:
    """Per run, this re-run against V2's record: counts, sweeps, objective
    hex, whole-state audit hex, and the full exit state bit-for-bit."""
    fields = ("node_calls_single_eval", "n_model_calls_sweeps")
    per: dict = {}
    n_cmp = n_id = 0
    for arm in ARMS:
        for k in seeds:
            mine = droot / arm / f"start{k:03d}"
            theirs = V2_RECORDS / "campaign" / deck / arm / f"start{k:03d}"
            a, b = _metrics(mine), _metrics(theirs)
            if a.get("status") != "ok" or b.get("status") != "ok":
                per[f"{arm}/{k}"] = {"compared": False, "mine": a.get("status"), "v2": b.get("status")}
                continue
            checks = {f: a.get(f) == b.get(f) for f in fields}
            sa, sb = a.get("module_solve_stats") or {}, b.get("module_solve_stats") or {}
            checks["block_sweeps"] = sa.get("block_sweeps") == sb.get("block_sweeps")
            checks["outer_passes"] = sa.get("outer_passes") == sb.get("outer_passes")
            checks["objf_hex"] = (a.get("exact") or {}).get("objf") == (b.get("exact") or {}).get("objf")
            checks["audit_max_hex"] = ((a.get("exit_audit") or {}).get("residual_max_hex")
                                       == (b.get("exit_audit") or {}).get("residual_max_hex"))
            ya = _load(mine / "y_exit.json").get("state") or {}
            yb = _load(theirs / "y_exit.json").get("state") or {}
            n_mis = sum(1 for nm in yb if ya.get(nm) != yb[nm]) + sum(1 for nm in ya if nm not in yb)
            checks["y_exit_bit_identical"] = bool(ya) and bool(yb) and n_mis == 0
            same = all(checks.values())
            n_cmp += 1
            n_id += same
            per[f"{arm}/{k}"] = {"compared": True, "identical": same, "checks": checks,
                                 "y_exit_n_components": len(yb), "y_exit_mismatches": n_mis,
                                 "v2_stamp": _stamp(b), "mine_stamp": _stamp(a)}
    return {"what": ("this re-run vs V2's Phase A record, per run: node calls, sweeps, "
                     "block sweeps, outer passes, objective hex, whole-state audit hex, "
                     "full exit state bit-for-bit"),
            "n_compared": n_cmp, "n_identical": n_id,
            "all_identical": n_cmp > 0 and n_cmp == n_id, "per_run": per}


def _parser_teeth(vec_path: Path) -> dict:
    """The tally's own restriction logic must be shown to fail: on a copy of
    a real residual vector, an excluded key set to 10x the whole-state max
    must move the whole-state max and not the restricted one; a kept key so
    doctored must move both."""
    v = _load(vec_path)
    scaled, excl = dict(v.get("scaled") or {}), set(v.get("excluded_keys") or [])
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
    s1 = dict(scaled); s1[kx] = big; w1, r1 = stats(s1)
    s2 = dict(scaled); s2[kk] = big; w2, r2 = stats(s2)
    checks = {"excluded_doctored_moves_whole": w1 != w0, "excluded_doctored_keeps_restricted": r1 == r0,
              "kept_doctored_moves_whole": w2 != w0, "kept_doctored_moves_restricted": r2 != r0}
    return {"vector": str(vec_path), "doctored_excluded": kx, "doctored_kept": kk,
            "checks": checks, "verdict": "PASS" if all(checks.values()) else "FAIL"}


def _closure(deck: str, droot: Path, seeds) -> dict:
    """Per A1 run: the pair's recorded entry displacement (perturbation.json),
    A35's predicted raw image on the deck's top mover, and the measured raw
    movement of that component in the restricted audit."""
    scale = {c["key"]: c.get("scale") for c in spec_components(deck)}  # discrete: no scale
    top = CARRIER.get(deck)
    rows = {}
    rel = []
    for k in seeds:
        d = droot / "A1" / f"start{k:03d}"
        pert = _load(d / "perturbation.json").get("per_component") or []
        pc = {e["key"]: e for e in pert}
        disp = {}
        for key in KNOWN_CUT:
            e = pc.get(key)
            if e:
                b, a = float.fromhex(e["elem_before_hex"]), float.fromhex(e["elem_after_hex"])
                disp[key] = {"before_hex": e["elem_before_hex"], "after_hex": e["elem_after_hex"],
                             "delta_raw": a - b, "factor": e.get("factor")}
        row = {"known_cut_entry_displacement": disp}
        vec = _load(d / "audit_residual.json").get("scaled") or {}
        if top and all(p in disp for p in PAIR):
            name, f = top
            din, dout = disp[PAIR[0]]["delta_raw"], disp[PAIR[1]]["delta_raw"]
            pred = abs(f(din, dout))
            meas = vec.get(name, 0.0) * scale[name]
            r = abs(meas - pred) / pred if pred else None
            row.update({"top_mover": name, "predicted_raw": pred, "measured_raw": meas,
                        "predicted_scaled": pred / scale[name], "measured_scaled": vec.get(name),
                        "rel_diff": r})
            if r is not None:
                rel.append(r)
        m = _metrics(d)
        res = (m.get("exit_audit") or {}).get("restricted") or {}
        row["restricted_argmax"] = res.get("argmax")
        row["restricted_max"] = res.get("max")
        row["restricted_argmax_is_top_mover"] = (top is not None and res.get("argmax") == top[0])
        rows[str(k)] = row
    return {"what": ("A35 coefficient closure per run: predicted raw image of the pair's "
                     "entry displacement vs the top mover's measured raw movement in the "
                     "restricted audit (lad: no traced coefficient, displacement only)"),
            "top_mover": top[0] if top else None,
            "rel_diff_median": statistics.median(rel) if rel else None,
            "rel_diff_max": max(rel) if rel else None,
            "n_runs_restricted_argmax_is_top_mover": sum(
                1 for r in rows.values() if r.get("restricted_argmax_is_top_mover")),
            "per_run": rows}


def _tally(root: Path, out_path: Path) -> int:
    camp = _load(root / "campaign.json")
    if not camp:
        print("no A38 campaign records")
        return 1
    seeds = camp["seeds"]
    v2_tally = _load(V2_RECORDS / "tally.json").get("per_deck") or {}
    summary: dict = {"task": "A38 audit-rerun", "machinery_smoke": camp.get("machinery_smoke"),
                     "tau": camp["tau"], "delta": camp["delta"],
                     "similarity_factor_F": cfg.SIMILARITY_FACTOR_F,
                     "n_seeds_requested": len(seeds), "per_deck": {}}
    lines = []
    for deck in camp["decks"]:
        droot = root / deck
        drec = camp["per_deck"].get(deck) or {}
        d: dict = {"gates": {"entry_gate": (drec.get("entry_gate") or {}).get("verdict"),
                             "warm_gate": (drec.get("warm_gate") or {}).get("verdict"),
                             "restricted_teeth": (drec.get("restricted_teeth") or {}).get("verdict")},
                   "cold_start_term": {"node_calls": (drec.get("reference") or {}).get("cold_start_node_calls"),
                                       "sweeps": (drec.get("reference") or {}).get("cold_start_sweeps")},
                   "pairing": {k: v for k, v in (drec.get("pairing") or {}).items() if k != "per_seed"}}
        if drec.get("refused") or drec.get("pairing_failure"):
            d["stopped"] = drec.get("refused") or drec.get("pairing_failure")
        rows = {arm: {} for arm in ARMS}
        for arm in ARMS:
            for k in seeds:
                m = _metrics(droot / arm / f"start{k:03d}")
                r = pa._row(m)
                res = (m.get("exit_audit") or {}).get("restricted") or {}
                r.update({"restricted_max": res.get("max"), "restricted_max_hex": res.get("max_hex"),
                          "restricted_argmax": res.get("argmax"), "restricted_n_above": res.get("n_above"),
                          "restricted_n_excluded": res.get("n_excluded"), "restricted_n_kept": res.get("n_kept"),
                          "excluded_sha256": res.get("excluded_sha256"),
                          "whole_argmax": ((m.get("exit_audit") or {}).get("brief") or {}).get("argmax")})
                rows[arm][str(k)] = r
        d["per_run"] = rows
        paired = [k for k in seeds if all(rows[a][str(k)].get("status") == "ok" for a in ARMS)]
        d["n_paired_ok"] = len(paired)
        d["failure_taxonomy"] = {"denominator_per_arm": len(seeds), "by_arm": {
            arm: {st: sum(1 for k in seeds if str(rows[arm][str(k)].get("status")) == st)
                  for st in sorted({str(rows[arm][str(k)].get("status")) for k in seeds})}
            for arm in ARMS}}

        # counts: ratio and bracket, as V2
        sums = {arm: {} for arm in ARMS}
        totals = {arm: 0 for arm in ARMS}
        for arm in ARMS:
            for k in paired:
                r = rows[arm][str(k)]
                totals[arm] += r.get("node_calls_single_eval") or 0
                for nm, v in pa._census_total(r).items():
                    sums[arm][nm] = sums[arm].get(nm, 0) + v
        ratios = []
        for nm in sorted(set(sums["A0"]) | set(sums["A1"])):
            n0, n1 = sums["A0"].get(nm, 0), sums["A1"].get(nm, 0)
            if n0:
                ratios.append(n1 / n0)
        d["unweighted_count_ratio_A1_over_A0"] = totals["A1"] / totals["A0"] if totals["A0"] else None
        d["weighting_invariance_bracket"] = [min(ratios), max(ratios)] if ratios else None
        d["node_calls_total_paired_ok"] = totals
        v2d = v2_tally.get(deck) or {}
        d["v2_count_ratio"] = v2d.get("unweighted_count_ratio_A1_over_A0")
        d["count_ratio_reproduces_v2"] = (d["unweighted_count_ratio_A1_over_A0"] == d["v2_count_ratio"])

        # identity gate vs V2's records
        d["identity_vs_v2"] = _identity_vs_v2(deck, droot, seeds)

        # audits: unrestricted (must reproduce V2's tally) and restricted
        whole = {arm: _dist([rows[arm][str(k)]["audit_residual_max"] for k in seeds
                             if rows[arm][str(k)].get("status") == "ok"
                             and rows[arm][str(k)].get("audit_residual_max") is not None])
                 for arm in ARMS}
        restr = {arm: _dist([rows[arm][str(k)]["restricted_max"] for k in seeds
                             if rows[arm][str(k)].get("status") == "ok"
                             and rows[arm][str(k)].get("restricted_max") is not None])
                 for arm in ARMS}
        v2w = ((v2d.get("audit_similarity") or {}).get("distributions") or {})
        d["whole_state_audit"] = {"distributions": whole, **_similarity(whole["A0"], whole["A1"]),
                                  "reproduces_v2_tally": {
                                      arm: (bool(v2w.get(arm)) and v2w[arm].get("values_hex") == whole[arm]["values_hex"])
                                      for arm in ARMS}}
        d["restricted_audit"] = {"distributions": restr, **_similarity(restr["A0"], restr["A1"]),
                                 "n_excluded": rows["A1"][str(seeds[0])].get("restricted_n_excluded"),
                                 "n_kept": rows["A1"][str(seeds[0])].get("restricted_n_kept"),
                                 "excluded_sha256_uniform": len({rows[a][str(k)].get("excluded_sha256")
                                                                 for a in ARMS for k in paired}) == 1,
                                 "ratio_of_medians": (restr["A1"]["median"] / restr["A0"]["median"]
                                                      if restr["A0"]["median"] else None)}
        d["argmax_census"] = {
            "whole_state_A1": {nm: sum(1 for k in paired if rows["A1"][str(k)].get("whole_argmax") == nm)
                               for nm in sorted({rows["A1"][str(k)].get("whole_argmax") for k in paired})},
            "restricted_A1": {nm: sum(1 for k in paired if rows["A1"][str(k)].get("restricted_argmax") == nm)
                              for nm in sorted({rows["A1"][str(k)].get("restricted_argmax") for k in paired})}}
        d["closure"] = _closure(deck, droot, paired)
        first = droot / "A1" / f"start{seeds[0]:03d}" / "audit_residual.json"
        d["parser_teeth"] = _parser_teeth(first)
        summary["per_deck"][deck] = d
        b = d["weighting_invariance_bracket"]
        lines.append(
            f"{deck:24s} E:{d['gates']['entry_gate'] or '-':4s} W:{d['gates']['warm_gate'] or '-':4s} "
            f"T:{d['gates']['restricted_teeth'] or '-':4s} paired {len(paired)}/{len(seeds)} "
            f"identity {d['identity_vs_v2']['n_identical']}/{d['identity_vs_v2']['n_compared']} "
            f"ratio {d['unweighted_count_ratio_A1_over_A0']:.4f} "
            f"whole A0 {whole['A0']['median']:.3g}/{whole['A0']['p90']:.3g} A1 {whole['A1']['median']:.3g}/{whole['A1']['p90']:.3g} "
            f"restricted A0 {restr['A0']['median']:.3g}/{restr['A0']['p90']:.3g} A1 {restr['A1']['median']:.3g}/{restr['A1']['p90']:.3g} "
            f"similar {d['restricted_audit']['similar']} closure rel {d['closure']['rel_diff_median']}")
    out_path.write_text(json.dumps(summary, indent=2))
    print(f"\nA38 tally -> {out_path}")
    for ln in lines:
        print(ln)
    return 0


# --------------------------------------------------------------------------
# entry point
# --------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("stage", nargs="?", default="preflight",
                    choices=["preflight", "smoke", "campaign", "tally", "all"])
    a = ap.parse_args()
    if a.stage == "preflight":
        return stage_preflight()
    if a.stage == "smoke":
        root = ROOT / "smoke"
        rc = _campaign(root, ("st_regression",), (1, 2), smoke=True)
        return rc if rc else _tally(root, root / "tally.json")
    if a.stage == "campaign":
        return _campaign(ROOT / "campaign", cfg.DECKS, SEEDS, smoke=False)
    if a.stage == "tally":
        return _tally(ROOT / "campaign", ROOT / "tally.json")
    rc = _campaign(ROOT / "campaign", cfg.DECKS, SEEDS, smoke=False)
    return rc if rc else _tally(ROOT / "campaign", ROOT / "tally.json")


if __name__ == "__main__":
    raise SystemExit(main())
