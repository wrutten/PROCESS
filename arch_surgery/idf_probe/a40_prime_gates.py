#!/usr/bin/env python
"""A40 (v3-prime): gates G1, G2, G3, G3c for the ``PROCESS_ARCH_PRIME``
variant point (V3 plan section 5; decision D19).

The variant point (task scope, V3 plan section 2): ``caller.py`` gains a
module-level prime selection and, when ``PROCESS_ARCH_PRIME=fw_geometry``,
calls ``models.fw.set_fw_geometry()`` at the head of every
``_call_models_once`` -- after the stellarator/IFE early returns, before the
SEQUENCE_HEAD loop, NOT routed through ``Caller._node`` (it adds no counted
node call).  This script gates that change; every published A40 number comes
from executing it (protocol section 15).

Stages, in execution order across TWO commits (section 15 staging: the gate
script is committed before any published run; the baseline side runs BEFORE
the ``caller.py`` change is committed, the changed side after, so both sides
carry clean stamps at their respective commits)
-----------------------------------------------------------------------
``g1base``
    3 runs (one full R optimisation per deck, ``run_one.py --mode control``,
    every architecture switch cleared).  REFUSES to run if the imported
    tree's ``caller.py`` already contains the prime; asserts the worktree's
    ``process/`` git tree hash equals the branch point ``b7dbd2a9``'s.
``g1``
    3 runs at the changed commit (identical construction, env still unset),
    then the comparison: every MFILE float as a hex literal (A3's comparator,
    ``compare_a3._floats``) plus whole-line identity, baseline vs changed.
    Teeth: a 1-ULP change to one float on a COPY of a changed-side MFILE
    must be caught by the same comparator.  REFUSES to run if the imported
    tree's ``caller.py`` does not contain the prime.
``g2``
    Prime-on fixed-point map.  Per deck, from the V2 Phase A reference exit
    snapshot (main checkout, read-only): one ``flat_state`` single eval and
    one ``per_module`` single eval, prime off vs prime on (4 runs/deck,
    12 total).  Exit states must be bit-identical on N/N components
    (840 / 846 / 827).  Teeth: a doctored copy of one exit-state component
    (1 ULP) must trip the comparison.
``g3``
    Prime-on cold chain, ``large_tokamak_nof`` + ``st_regression`` (A35's
    ``trace`` and ``restarts`` constructions: verified A1' chain from the
    cold deck entry, traced with the full census from pass 1; one trust-mode
    run from the same entry).  Expectation: verified outer passes 3 -> 2;
    trust-run IN-RUN ``exit_audit`` (one further full sweep at the exit,
    a26 ystate ruler -- the operationalization A35 section 9 names, which
    reads 244/124 in-run; the snapshot-pair construction reads 243 on nof
    and is NOT what this gate computes) 0 components above tau with the
    prime on.  Teeth: the prime-off runs must reproduce A35's 3 passes and
    244 / 124 exactly.  Coverage (plan section 2): in every prime-on run the
    stamped ``n_prime_calls`` must equal that run's block-sweep count.
    Any residual mover is named.
``g3c``
    The lad carrier census (A35's declared scope gap; the O1 alternative).
    On ``low_aspect_ratio_DEMO``: flat cold reference (traced), verified
    chains traced from the cold entry and from displaced-warm entries
    (delta = 0.10 and 0.05, seed 1 -- A35's stream), trust runs from the
    cold and delta = 0.10 entries; each prime off, and the cold/verified +
    both trust entries prime on.  Deliverables: the carrier coefficients on
    this deck (the A35 images, source-grounded from the traced chain), the
    mechanism census for A38's open term ``tfcoil.m_tf_coil_superconductor``
    (pass-2 mover rows, writer chain, two-coefficient solve from cold+warm
    checked on the third displacement point), and the verdict: does the term
    CLOSE under the prime or SURVIVE it (then it is a residual mover,
    named).  Teeth: as G3's parser teeth -- a doctored trace line (1 ULP on
    a before-hex) must be caught by the scaled-recompute check.
``analyze``
    No PROCESS runs.  Collates the per-gate records into
    ``runs/a40/analysis/summary.json``.

Discipline: every PROCESS run is a fresh subprocess in its own working
directory, ``PYTHONPATH`` pinned to THIS worktree, exact tree asserted
in-process (traps T6/T10); strictly serial -- at most ONE PROCESS subprocess
exists at any time; every published quantity is a count, a name or a
bit-exact hex float; wall clock is progress information, never evidence
(trap T5).  A failed gate stops and is reported with its numbers; nothing is
retried with different settings (protocol section 12).  Runs live under
``arch_surgery/idf_probe/runs/a40/`` (untracked; summaries committed).
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
from pathlib import Path

HERE = Path(__file__).resolve().parent
TREE = HERE.parent.parent
DATA = TREE / "arch_surgery" / "docs" / "data"
RUNS = HERE / "runs" / "a40"

sys.path.insert(0, str(HERE))
from a35_cold_census import (  # noqa: E402  -- A35's committed constructions
    Joins,
    _passes,
    analyze_deck,
    full_state_compare,
    load_state,
    load_trace,
    trace_movers,
)
from compare_a3 import _floats, _lines  # noqa: E402  -- A3's comparator
from run_a28 import PULSED, TAU, env_for  # noqa: E402
from v2_eval_one import perturb_factor  # noqa: E402

#: The main checkout: V2's Phase A reference records are read from here,
#: READ-ONLY (the task never writes outside its own worktree).
MAIN = Path("/home/wrutten/projects/PROCESS_surgery")
V2_PHASE_A = MAIN / "arch_surgery" / "MDA_partitioning_experiment_v2" / (
    "runs") / "phase_a" / "campaign"

#: The branch point.  g1base asserts the worktree's process/ tree equals
#: this commit's, so "baseline at the pre-change commit" is a git fact in
#: the record, not a claim.
BRANCH_POINT = "b7dbd2a9"

ALL_DECKS = ("large_tokamak_nof", "low_aspect_ratio_DEMO", "st_regression")
G3_DECKS = ("large_tokamak_nof", "st_regression")
LAD = "low_aspect_ratio_DEMO"

#: Full a26 spec component counts per deck (V2/A38 record).
N_COMPONENTS = {
    "large_tokamak_nof": 840,
    "low_aspect_ratio_DEMO": 846,
    "st_regression": 827,
}

#: A35's published cold-chain quantities, the G3 teeth (in-run exit_audit
#: operationalization; A35 report section 9).
A35_OUTER_PASSES = {"large_tokamak_nof": 3, "st_regression": 3}
A35_INRUN_N_ABOVE = {"large_tokamak_nof": 244, "st_regression": 124}
#: nof's in-run max is printed in full in A35 section 9; st's only by its
#: printed tail there ("...f0afff76"), so st is checked by that tail.
A35_INRUN_MAX_HEX_NOF = "0x1.de05b6285d3f4p-7"
A35_INRUN_MAX_HEX_TAIL_ST = "f0afff76"

#: A38's open term on lad (G3c's question) and A35's two carrier images.
OPEN_TERM = "tfcoil.m_tf_coil_superconductor"
CARRIER_PAIR = ("build.dr_fw_inboard", "build.dr_fw_outboard")
IMAGE_PREDICTIONS = {
    # component: lambda d_in, d_out -> predicted |pass-2 raw delta|
    "build.dz_tf_upper_lower_midplane": lambda d_in, d_out: 0.5 * (
        d_in + d_out),
    "build.dr_shld_vv_gap_outboard": lambda d_in, d_out: d_out,
}

DELTA = 0.10
DELTA2 = 0.05
SEED = 1
PIN_COMPONENT = "times.t_plant_pulse_burn"

#: Environment variables this task sets per run -- popped from every run's
#: environment first (the a34/a35 discipline).  PROCESS_ARCH_PRIME is also
#: in run_a28._ARCH_VARS since A40; popped here too so this script is
#: self-contained about what it clears.
CLEARED = (
    "PROCESS_ARCH_OUTER",
    "PROCESS_ARCH_PIN_BURN_TIME",
    "PROCESS_ARCH_PASS_TRACE",
    "PROCESS_ARCH_PASS_TRACE_FULL_FROM",
    "PROCESS_ARCH_PRIME",
)


# --------------------------------------------------------------------------
# provenance
# --------------------------------------------------------------------------


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(TREE), *args],
        capture_output=True, text=True, check=True,
    ).stdout.strip()


def provenance() -> dict:
    return {
        "tree": str(TREE),
        "git_head": _git("rev-parse", "HEAD"),
        "git_dirty": bool(_git("status", "--porcelain")),
        "process_tree_hash": _git("rev-parse", "HEAD:process"),
        "branch_point_process_tree_hash": _git(
            "rev-parse", f"{BRANCH_POINT}:process"),
    }


def caller_has_prime() -> bool:
    return "PROCESS_ARCH_PRIME" in (
        TREE / "process" / "core" / "caller.py").read_text()


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


# --------------------------------------------------------------------------
# runners (fresh subprocess each, strictly serial; the a35 recipe)
# --------------------------------------------------------------------------


def deck_path(scn: str) -> Path:
    """The ORIGINAL frozen deck, every run: pin chains refuse the derived
    lifted deck (ixc 178) by design (A34 decision (d); A35's construction)."""
    return HERE / "scenarios" / f"{scn}.IN.DAT"


def a26_ystate(scn: str) -> Path:
    return DATA / f"ystate_a26_{scn}.json"


def env_a40(scn: str, arm: str, *, outer: str | None = None,
            pin_hex: str | None = None, trace_path: Path | None = None,
            prime: bool = False) -> dict:
    """One arm's environment: run_a28's composition (cleared-first), the
    a26 driver artifacts substituted, this task's switches added.  Exactly
    A35's ``env_a35`` plus the ``prime`` switch."""
    env = env_for(scn, arm, RUNS, TAU, None)
    for k in CLEARED:
        env.pop(k, None)
    if arm != "R":
        env["PROCESS_ARCH_YSTATE"] = str(a26_ystate(scn))
        env["PROCESS_ARCH_WRITESET"] = str(
            DATA / f"writeset_a26_{scn}.json")
    if outer is not None:
        env["PROCESS_ARCH_OUTER"] = outer
    if pin_hex is not None:
        env["PROCESS_ARCH_PIN_BURN_TIME"] = pin_hex
    if trace_path is not None:
        env["PROCESS_ARCH_PASS_TRACE"] = str(trace_path)
        env["PROCESS_ARCH_PASS_TRACE_FULL_FROM"] = "1"
    if prime:
        env["PROCESS_ARCH_PRIME"] = "fw_geometry"
    return env


def run_eval(scn: str, arm: str, outdir: Path, *,
             entry_state: Path | None = None, delta: float | None = None,
             seed: int = 0, outer: str | None = None,
             pin_hex: str | None = None, trace: bool = False,
             prime: bool = False, reuse: bool = True,
             timeout: int = 3600) -> dict:
    """One ``v2_eval_one.py`` single-MDA-evaluation run (A35's recipe),
    fresh subprocess, own working directory."""
    mpath = outdir / "metrics.json"
    if reuse and mpath.exists():
        rec = json.loads(mpath.read_text())
        print(f"  [reused] {outdir.relative_to(RUNS)} "
              f"status={rec.get('status')}", flush=True)
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
    env = env_a40(scn, arm, outer=outer, pin_hex=pin_hex, prime=prime,
                  trace_path=(outdir / "pass_trace.jsonl") if trace
                  else None)
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


def run_r(scn: str, outdir: Path, *, reuse: bool = True,
          timeout: int = 3600) -> dict:
    """One full R optimisation (``run_one.py --mode control``), every
    architecture switch cleared -- run_a28's R construction."""
    mpath = outdir / "metrics.json"
    if reuse and mpath.exists():
        rec = json.loads(mpath.read_text())
        print(f"  [reused] {outdir.relative_to(RUNS)} "
              f"status={rec.get('status')}", flush=True)
        return {"rc": 0 if rec.get("status") == "ok" else 1,
                "outdir": str(outdir), "metrics": rec, "reused": True}
    if outdir.exists():
        shutil.rmtree(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable, str(HERE / "run_one.py"),
        "--scenario", scn,
        "--mode", "control",
        "--outdir", str(outdir),
        "--expect-tree", str(TREE),
        "--input", str(deck_path(scn)),
    ]
    env = env_a40(scn, "R")
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


def mfile_of(outdir: Path) -> Path | None:
    cand = sorted(Path(outdir).glob("*MFILE.DAT"))
    return cand[0] if cand else None


# --------------------------------------------------------------------------
# G1: prime unset, byte identity across the change
# --------------------------------------------------------------------------


def g1_dir(side: str, scn: str) -> Path:
    return RUNS / "g1" / side / scn


def stage_g1base() -> int:
    if caller_has_prime():
        print("REFUSED: caller.py already contains PROCESS_ARCH_PRIME -- "
              "the g1base stage must run at the PRE-change commit "
              "(section 15 staging).")
        return 1
    prov = provenance()
    if prov["git_dirty"]:
        print("REFUSED: worktree dirty; commit first so the baseline "
              "carries a clean stamp.")
        return 1
    if prov["process_tree_hash"] != prov["branch_point_process_tree_hash"]:
        print(f"REFUSED: process/ tree hash {prov['process_tree_hash']} "
              f"differs from {BRANCH_POINT}:process "
              f"{prov['branch_point_process_tree_hash']} -- the baseline "
              f"would not be the pre-change driver.")
        return 1
    rc = 0
    for scn in ALL_DECKS:
        print(f"g1base: {scn} R (all switches cleared)", flush=True)
        r = run_r(scn, g1_dir("baseline", scn))
        if r["rc"] != 0 or r["metrics"].get("status") != "ok":
            print(f"  FAILURE PATH: baseline R on {scn} status "
                  f"{r['metrics'].get('status')}")
            rc = 1
    (RUNS / "g1" / "baseline_provenance.json").write_text(
        json.dumps(prov, indent=2))
    print(f"g1base: provenance {prov['git_head'][:8]} "
          f"process/ == {BRANCH_POINT}:process")
    return rc


def _doctor_mfile_copy(src: Path, dst: Path) -> dict:
    """Copy *src* to *dst* with exactly ONE float value moved by 1 ULP.

    The doctored line is chosen as the first data line whose value field
    parses to a finite nonzero float; the value token is replaced by the
    17-significant-digit rendering of ``nextafter`` (a double's 17-digit
    decimal round-trips exactly, so the re-parsed double differs by 1 ULP).
    """
    lines = src.read_text(errors="replace").splitlines(keepends=True)
    for i, ln in enumerate(lines):
        parts = ln.split()
        if len(parts) < 3 or not (parts[1].startswith("(")
                                  and parts[1].rstrip("_").endswith(")")):
            continue
        tok = parts[2].strip('"')
        try:
            v = float(tok)
        except ValueError:
            continue
        if not math.isfinite(v) or v == 0.0:
            continue
        v2 = math.nextafter(v, math.inf)
        # The value field is the LAST occurrence of the token on the line
        # (descriptions may in principle contain the same digits).
        idx = ln.rfind(tok)
        lines[i] = ln[:idx] + f"{v2:.17e}" + ln[idx + len(tok):]
        dst.write_text("".join(lines))
        return {"line_index": i, "token": tok, "doctored_to": f"{v2:.17e}",
                "before_hex": v.hex(), "after_hex": v2.hex()}
    raise SystemExit(f"G1 tooth: no doctorable float line in {src}")


def _g1_compare_pair(base_mf: Path, changed_mf: Path) -> dict:
    fa, fb = _floats(base_mf), _floats(changed_mf)
    only_a = sorted(set(fa) - set(fb))
    only_b = sorted(set(fb) - set(fa))
    mismatch = sorted(k for k in fa if k in fb and fa[k] != fb[k])
    la, lb = _lines(base_mf), _lines(changed_mf)
    n_line_diff = sum(1 for a, b in zip(la, lb) if a != b) + abs(
        len(la) - len(lb))
    return {
        "n_floats_compared": len(set(fa) & set(fb)),
        "n_hex_mismatches": len(mismatch),
        "mismatched_keys_first_20": mismatch[:20],
        "keys_only_in_baseline": only_a[:20],
        "keys_only_in_changed": only_b[:20],
        "n_lines_compared": len(la),
        "n_differing_lines": n_line_diff,
        "identical": (not mismatch and not only_a and not only_b
                      and n_line_diff == 0),
    }


def stage_g1() -> int:
    if not caller_has_prime():
        print("REFUSED: caller.py does not contain PROCESS_ARCH_PRIME -- "
              "the g1 stage runs at the changed commit.")
        return 1
    prov = provenance()
    if prov["git_dirty"]:
        print("REFUSED: worktree dirty; commit first so the changed side "
              "carries a clean stamp.")
        return 1
    base_prov_path = RUNS / "g1" / "baseline_provenance.json"
    if not base_prov_path.exists():
        print("REFUSED: no baseline runs -- run 'g1base' at the pre-change "
              "commit first.")
        return 1
    base_prov = json.loads(base_prov_path.read_text())
    rc = 0
    record: dict = {
        "gate": "G1 prime-unset byte identity",
        "baseline_provenance": base_prov,
        "changed_provenance": prov,
        "decks": {},
    }
    for scn in ALL_DECKS:
        print(f"g1: {scn} R at the changed commit (env unset)", flush=True)
        r = run_r(scn, g1_dir("changed", scn))
        m = r["metrics"]
        base_m_path = g1_dir("baseline", scn) / "metrics.json"
        base_m = json.loads(base_m_path.read_text())
        row: dict = {
            "baseline_status": base_m.get("status"),
            "changed_status": m.get("status"),
            "baseline_stamp": {
                "git_head": base_m.get("tree_git_head"),
                "dirty": base_m.get("tree_git_dirty"),
                "arch_prime_name": base_m.get("arch_prime_name"),
                "env_PROCESS_ARCH_PRIME": base_m.get(
                    "env_PROCESS_ARCH_PRIME"),
                "n_prime_calls": base_m.get("n_prime_calls"),
            },
            "changed_stamp": {
                "git_head": m.get("tree_git_head"),
                "dirty": m.get("tree_git_dirty"),
                "arch_prime_name": m.get("arch_prime_name"),
                "env_PROCESS_ARCH_PRIME": m.get("env_PROCESS_ARCH_PRIME"),
                "n_prime_calls": m.get("n_prime_calls"),
            },
        }
        if (r["rc"] != 0 or m.get("status") != "ok"
                or base_m.get("status") != "ok"):
            row["verdict"] = "FAIL (a side's run did not complete)"
            record["decks"][scn] = row
            rc = 1
            continue
        base_mf = mfile_of(g1_dir("baseline", scn))
        changed_mf = mfile_of(g1_dir("changed", scn))
        if base_mf is None or changed_mf is None:
            row["verdict"] = "FAIL (an MFILE is missing)"
            record["decks"][scn] = row
            rc = 1
            continue
        cmpres = _g1_compare_pair(base_mf, changed_mf)
        row["comparison"] = cmpres
        # teeth: 1 ULP on a copy of the changed MFILE must be caught.
        dst = g1_dir("changed", scn) / "MFILE_doctored_copy.DAT"
        doc = _doctor_mfile_copy(changed_mf, dst)
        tooth = _g1_compare_pair(base_mf, dst)
        row["tooth"] = {
            "doctored": doc,
            "n_hex_mismatches": tooth["n_hex_mismatches"],
            "tripped": not tooth["identical"],
        }
        # the changed side must have resolved the prime OFF, and the prime
        # counter must have stayed at zero over the whole run.
        stamps_ok = (m.get("arch_prime_name") == "off"
                     and m.get("env_PROCESS_ARCH_PRIME") is None
                     and m.get("n_prime_calls") == 0)
        row["changed_stamps_ok"] = stamps_ok
        ok = cmpres["identical"] and row["tooth"]["tripped"] and stamps_ok
        row["verdict"] = "PASS" if ok else "FAIL"
        if not ok:
            rc = 1
        record["decks"][scn] = row
        print(f"  {scn}: {row['verdict']} "
              f"({cmpres['n_floats_compared']} floats, "
              f"{cmpres['n_hex_mismatches']} mismatches, tooth "
              f"tripped={row['tooth']['tripped']})")
    record["verdict"] = ("PASS" if all(
        d.get("verdict") == "PASS" for d in record["decks"].values())
        else "FAIL")
    (RUNS / "g1" / "g1.json").write_text(json.dumps(record, indent=2))
    print(f"g1: {record['verdict']} -> {RUNS / 'g1' / 'g1.json'}")
    return rc


# --------------------------------------------------------------------------
# G2: prime on, fixed-point map bit-identical
# --------------------------------------------------------------------------


def v2_reference(scn: str) -> tuple[Path, dict]:
    ref = V2_PHASE_A / scn / "reference"
    snap = ref / "y_exit.json"
    if not snap.exists():
        raise SystemExit(
            f"V2 reference exit snapshot missing: {snap} (main checkout, "
            f"read-only) -- G2 cannot run")
    return snap, json.loads((ref / "metrics.json").read_text())


def g2_dir(scn: str, arm: str, prime: bool) -> Path:
    return RUNS / "g2" / scn / f"{arm}_{'on' if prime else 'off'}"


def stage_g2() -> int:
    if not caller_has_prime():
        print("REFUSED: caller.py does not contain PROCESS_ARCH_PRIME.")
        return 1
    rc = 0
    record: dict = {"gate": "G2 prime-on fixed-point map",
                    "provenance": provenance(), "decks": {}}
    for scn in ALL_DECKS:
        snap, ref_m = v2_reference(scn)
        pin = (ref_m.get("t_plant_pulse_burn_hex")
               if scn in PULSED else None)
        row: dict = {
            "reference_snapshot": str(snap),
            "reference_snapshot_sha256": sha256_of(snap),
            "reference_stamp": {
                "git_head": ref_m.get("tree_git_head"),
                "dirty": ref_m.get("tree_git_dirty"),
            },
            "pin_hex": pin,
            "arms": {},
        }
        states: dict[tuple[str, bool], dict] = {}
        ok_all = True
        for arm, arm_label in (("A0p", "flat_state"), ("A1p", "per_module")):
            for prime in (False, True):
                print(f"g2: {scn} {arm_label} prime="
                      f"{'on' if prime else 'off'}", flush=True)
                r = run_eval(scn, arm, g2_dir(scn, arm_label, prime),
                             entry_state=snap,
                             pin_hex=(pin if arm == "A1p" else None),
                             prime=prime)
                m = r["metrics"]
                arm_rec = {
                    "status": m.get("status"),
                    "arch_prime_name": m.get("arch_prime_name"),
                    "n_prime_calls": m.get("n_prime_calls"),
                    "block_sweeps": (m.get("module_solve_stats") or {}
                                     ).get("block_sweeps"),
                    "outer_passes": (m.get("module_solve_stats") or {}
                                     ).get("outer_passes"),
                    "exit_audit_max_hex": (m.get("exit_audit") or {}
                                           ).get("residual_max_hex"),
                }
                row["arms"][f"{arm_label}_"
                            f"{'on' if prime else 'off'}"] = arm_rec
                if r["rc"] != 0 or m.get("status") != "ok":
                    ok_all = False
                    continue
                states[(arm_label, prime)] = load_state(
                    Path(r["outdir"]) / "y_exit.json")
                # coverage bookkeeping: prime-on counts equal block sweeps;
                # prime-off counts are zero.
                n_pc, bs = arm_rec["n_prime_calls"], arm_rec["block_sweeps"]
                arm_rec["prime_count_ok"] = (
                    (n_pc == bs and n_pc > 0) if prime else n_pc == 0)
                if not arm_rec["prime_count_ok"]:
                    ok_all = False
        comps = {}
        for arm_label in ("flat_state", "per_module"):
            a = states.get((arm_label, False))
            b = states.get((arm_label, True))
            if a is None or b is None:
                comps[arm_label] = {"missing": "a run did not complete"}
                ok_all = False
                continue
            c = full_state_compare(a, b)
            c["n_components_expected"] = N_COMPONENTS[scn]
            c["bit_identical"] = (
                c["n_differing"] == 0
                and c["n_components"] == N_COMPONENTS[scn])
            comps[arm_label] = c
            if not c["bit_identical"]:
                ok_all = False
        row["exit_state_comparison"] = comps
        # teeth: a doctored copy of one exit-state component must trip.
        tooth = None
        b = states.get(("per_module", True))
        if b is not None:
            doctored = json.loads(json.dumps(b))
            key = next(k for k, v in sorted(doctored.items())
                       if v.get("k") == "f"
                       and math.isfinite(float.fromhex(v["hex"]))
                       and float.fromhex(v["hex"]) != 0.0)
            v0 = float.fromhex(doctored[key]["hex"])
            doctored[key]["hex"] = math.nextafter(v0, math.inf).hex()
            t = full_state_compare(b, doctored)
            tooth = {"doctored_component": key,
                     "before_hex": v0.hex(),
                     "after_hex": doctored[key]["hex"],
                     "n_differing": t["n_differing"],
                     "tripped": t["n_differing"] == 1}
            if not tooth["tripped"]:
                ok_all = False
        row["tooth"] = tooth
        row["verdict"] = "PASS" if ok_all else "FAIL"
        if not ok_all:
            rc = 1
        record["decks"][scn] = row
        print(f"  {scn}: {row['verdict']}")
    record["verdict"] = ("PASS" if all(
        d.get("verdict") == "PASS" for d in record["decks"].values())
        else "FAIL")
    (RUNS / "g2").mkdir(parents=True, exist_ok=True)
    (RUNS / "g2" / "g2.json").write_text(json.dumps(record, indent=2))
    print(f"g2: {record['verdict']} -> {RUNS / 'g2' / 'g2.json'}")
    return rc


# --------------------------------------------------------------------------
# G3 (nof + st) and G3c (lad): the chain stages
# --------------------------------------------------------------------------


def refs_dir(scn: str) -> Path:
    return RUNS / "refs" / f"{scn}_flat_cold"


def chain_dir(scn: str, name: str) -> Path:
    return RUNS / "chains" / scn / name


def _ensure_ref(scn: str) -> dict:
    print(f"refs: {scn} FLAT cold (traced)", flush=True)
    r = run_eval(scn, "A0p", refs_dir(scn), trace=True)
    m = r["metrics"]
    if r["rc"] != 0 or m.get("status") != "ok":
        raise SystemExit(
            f"FAILURE PATH: FLAT cold reference on {scn} did not complete "
            f"(status {m.get('status')}); the deck's gates cannot run")
    return m


def _pin_hex(scn: str, ref_m: dict, *, displaced_seed: int | None = None,
             delta: float = DELTA) -> str | None:
    """A35's pin: the flat-converged burn time, times the displaced
    component's own stream factor on a warm displaced entry."""
    if scn not in PULSED:
        return None
    burn = float.fromhex(ref_m["t_plant_pulse_burn_hex"])
    if displaced_seed is not None:
        burn = burn * perturb_factor(displaced_seed, PIN_COMPONENT, delta)
    return float(burn).hex()


def _audit_summary(m: dict) -> dict:
    ea = m.get("exit_audit") or {}
    return {
        "residual_max_hex": ea.get("residual_max_hex"),
        "brief": ea.get("brief"),
    }


def _above_tau(outdir: Path) -> dict[str, float]:
    """Named components >= tau in a run's recorded audit residual vector."""
    vec = json.loads((Path(outdir) / "audit_residual.json").read_text())
    return {k: v for k, v in vec["scaled"].items() if v >= TAU}


def _prime_counts_row(m: dict) -> dict:
    return {
        "arch_prime_name": m.get("arch_prime_name"),
        "n_prime_calls": m.get("n_prime_calls"),
        "block_sweeps": (m.get("module_solve_stats") or {}).get(
            "block_sweeps"),
        "outer_passes": (m.get("module_solve_stats") or {}).get(
            "outer_passes"),
    }


def stage_g3() -> int:
    if not caller_has_prime():
        print("REFUSED: caller.py does not contain PROCESS_ARCH_PRIME.")
        return 1
    rc = 0
    record: dict = {"gate": "G3 prime-on cold chain (nof + st)",
                    "provenance": provenance(),
                    "operationalization": (
                        "IN-RUN exit_audit: one further full sweep of the "
                        "complete model set at the run's exit, residual on "
                        "the a26 ystate ruler, count = brief.n_above at "
                        "tau=1e-6 (A35 section 9's in-run construction, "
                        "244/124; NOT the snapshot-pair construction, "
                        "which reads 243 on nof)"),
                    "decks": {}}
    for scn in G3_DECKS:
        ref_m = _ensure_ref(scn)
        pin = _pin_hex(scn, ref_m)
        row: dict = {"runs": {}}
        runs = {}
        for name, outer, prime in (
            ("verified_off", None, False),
            ("verified_on", None, True),
            ("trust_off", "trust", False),
            ("trust_on", "trust", True),
        ):
            print(f"g3: {scn} {name} cold", flush=True)
            r = run_eval(scn, "A1p", chain_dir(scn, name), pin_hex=pin,
                         outer=outer, prime=prime,
                         trace=(outer is None))
            m = r["metrics"]
            runs[name] = r
            row["runs"][name] = {
                "status": m.get("status"),
                **_prime_counts_row(m),
                "exit_audit": _audit_summary(m),
                "pin_intact": m.get("pin_intact_at_exit"),
            }
            if r["rc"] != 0 or m.get("status") != "ok":
                rc = 1
        # ---- teeth: prime-off must reproduce A35 exactly ----------------
        v_off = row["runs"]["verified_off"]
        t_off = row["runs"]["trust_off"]
        t_off_brief = (t_off["exit_audit"] or {}).get("brief") or {}
        teeth = {
            "verified_off_outer_passes": v_off["outer_passes"],
            "a35_outer_passes": A35_OUTER_PASSES[scn],
            "trust_off_inrun_n_above": t_off_brief.get("n_above"),
            "a35_inrun_n_above": A35_INRUN_N_ABOVE[scn],
            "trust_off_inrun_max_hex": t_off["exit_audit"].get(
                "residual_max_hex"),
        }
        teeth["passes_reproduced"] = (
            v_off["outer_passes"] == A35_OUTER_PASSES[scn])
        teeth["n_above_reproduced"] = (
            t_off_brief.get("n_above") == A35_INRUN_N_ABOVE[scn])
        if scn == "large_tokamak_nof":
            teeth["max_hex_reproduced"] = (
                teeth["trust_off_inrun_max_hex"] == A35_INRUN_MAX_HEX_NOF)
            teeth["a35_inrun_max_hex"] = A35_INRUN_MAX_HEX_NOF
        else:
            # A35 section 9 prints st's in-run max only by its MANTISSA tail
            # ("...f0afff76"); a hex literal carries a "p<exp>" suffix after
            # the mantissa, so the tail is checked on the mantissa, not on
            # the full literal.  (First revision of this check applied
            # endswith to the full literal and failed on its own defect;
            # fixed with the measured value unchanged -- see the report's
            # change log.)
            mantissa = (teeth["trust_off_inrun_max_hex"] or "").split("p")[0]
            teeth["max_hex_tail_reproduced"] = mantissa.endswith(
                A35_INRUN_MAX_HEX_TAIL_ST)
            teeth["a35_inrun_max_hex_printed_tail"] = (
                A35_INRUN_MAX_HEX_TAIL_ST)
        row["teeth_a35_reproduction"] = teeth
        # ---- criteria ---------------------------------------------------
        v_on = row["runs"]["verified_on"]
        t_on = row["runs"]["trust_on"]
        t_on_brief = (t_on["exit_audit"] or {}).get("brief") or {}
        residual_movers = (
            _above_tau(runs["trust_on"]["outdir"])
            if runs["trust_on"]["metrics"].get("status") == "ok" else None)
        row["criteria"] = {
            "verified_on_outer_passes": v_on["outer_passes"],
            "expected_on_outer_passes": A35_OUTER_PASSES[scn] - 1,
            "passes_reduced": (
                v_on["outer_passes"] == A35_OUTER_PASSES[scn] - 1),
            "trust_on_inrun_n_above": t_on_brief.get("n_above"),
            "trust_on_inrun_max_hex": t_on["exit_audit"].get(
                "residual_max_hex"),
            "zero_above_tau": t_on_brief.get("n_above") == 0,
            "residual_movers_named": residual_movers,
        }
        # ---- coverage (plan section 2) ----------------------------------
        cov = {}
        for name, rr in row["runs"].items():
            on = name.endswith("_on")
            cov[name] = {
                "n_prime_calls": rr["n_prime_calls"],
                "block_sweeps": rr["block_sweeps"],
                "ok": ((rr["n_prime_calls"] == rr["block_sweeps"]
                        and (rr["n_prime_calls"] or 0) > 0) if on
                       else rr["n_prime_calls"] == 0),
            }
        row["coverage_prime_calls_eq_block_sweeps"] = cov
        ok = (all(v for k, v in teeth.items()
                  if k.endswith("_reproduced"))
              and row["criteria"]["passes_reduced"]
              and row["criteria"]["zero_above_tau"]
              and all(c["ok"] for c in cov.values())
              and all(r["status"] == "ok" for r in row["runs"].values()))
        row["verdict"] = "PASS" if ok else "FAIL"
        if not ok:
            rc = 1
        record["decks"][scn] = row
        print(f"  {scn}: {row['verdict']} (off passes "
              f"{v_off['outer_passes']}, on passes {v_on['outer_passes']}, "
              f"trust-off n_above {t_off_brief.get('n_above')}, trust-on "
              f"n_above {t_on_brief.get('n_above')})")
    record["verdict"] = ("PASS" if all(
        d.get("verdict") == "PASS" for d in record["decks"].values())
        else "FAIL")
    (RUNS / "g3").mkdir(parents=True, exist_ok=True)
    (RUNS / "g3" / "g3.json").write_text(json.dumps(record, indent=2))
    print(f"g3: {record['verdict']} -> {RUNS / 'g3' / 'g3.json'}")
    return rc


# --------------------------------------------------------------------------
# G3c: the lad carrier census
# --------------------------------------------------------------------------


def _raw_delta(mv: dict) -> float | None:
    if mv.get("before_hex") is None or mv.get("after_hex") is None:
        return None
    return abs(float.fromhex(mv["after_hex"])
               - float.fromhex(mv["before_hex"]))


def _pass_movers(run_dir: Path, p: int) -> dict[str, dict]:
    recs = load_trace(Path(run_dir) / "pass_trace.jsonl")
    outer = _passes(recs, "outer")
    return {mv["key"]: mv for mv in trace_movers(outer.get(p) or {})}


def _closure_for_entry(run_dir: Path) -> dict:
    """A35's carrier-closure construction on one traced verified run:
    pass-1 raw deltas of the pair, measured vs predicted pass-2 raw deltas
    of the two A35 images, and the open term's row."""
    p1 = _pass_movers(run_dir, 1)
    p2 = _pass_movers(run_dir, 2)
    d_in = _raw_delta(p1[CARRIER_PAIR[0]]) if CARRIER_PAIR[0] in p1 else None
    d_out = (_raw_delta(p1[CARRIER_PAIR[1]])
             if CARRIER_PAIR[1] in p1 else None)
    rec: dict = {
        "pass1_raw_delta_dr_fw_inboard": d_in,
        "pass1_raw_delta_dr_fw_outboard": d_out,
        "n_pass2_movers": len(p2),
        "images": {},
    }
    for key, predict in IMAGE_PREDICTIONS.items():
        mv = p2.get(key)
        if mv is None or d_in is None or d_out is None:
            rec["images"][key] = {"present_in_pass2": mv is not None}
            continue
        measured = _raw_delta(mv)
        predicted = predict(d_in, d_out)
        rec["images"][key] = {
            "measured_raw": measured,
            "measured_hex": float(measured).hex(),
            "predicted_raw": predicted,
            "predicted_hex": float(predicted).hex(),
            "rel_difference": (abs(measured - predicted) / measured
                               if measured else None),
        }
    mv = p2.get(OPEN_TERM)
    rec["open_term"] = None
    if mv is not None:
        rec["open_term"] = {
            "key": OPEN_TERM,
            "pass2_raw_delta": _raw_delta(mv),
            "scaled": mv.get("scaled"),
            "before_hex": mv.get("before_hex"),
            "after_hex": mv.get("after_hex"),
            "elem": mv.get("elem"),
        }
    return rec


def _parser_tooth(run_dir: Path) -> dict:
    """G3's parser tooth transposed (A35 G3 tooth (ii) lineage): the
    scaled-recompute check must catch a 1-ULP doctoring of a before-hex."""
    p2 = _pass_movers(run_dir, 2)
    scalar = next((mv for mv in p2.values()
                   if mv.get("scaled") is not None
                   and mv.get("elem") is None
                   and mv.get("before_hex") is not None), None)
    if scalar is None:
        return {"tripped": False, "why": "no scalar pass-2 mover to doctor"}
    ok_clean = (abs(float.fromhex(scalar["after_hex"])
                    - float.fromhex(scalar["before_hex"]))
                / scalar["scale"] == scalar["scaled"])
    v = float.fromhex(scalar["before_hex"])
    doctored = abs(float.fromhex(scalar["after_hex"])
                   - math.nextafter(v, math.inf)) / scalar["scale"]
    return {
        "component": scalar["key"],
        "clean_recompute_matches": ok_clean,
        "doctored_recompute_matches": doctored == scalar["scaled"],
        "tripped": ok_clean and doctored != scalar["scaled"],
    }


def stage_g3c() -> int:
    if not caller_has_prime():
        print("REFUSED: caller.py does not contain PROCESS_ARCH_PRIME.")
        return 1
    scn = LAD
    rc = 0
    ref_m = _ensure_ref(scn)
    ref_snap = refs_dir(scn) / "y_exit.json"
    record: dict = {"gate": "G3c lad carrier census",
                    "provenance": provenance(), "runs": {}}
    runs: dict[str, dict] = {}
    plan = (
        # name, entry, delta, outer, prime, trace
        ("verified_off_cold", None, None, None, False, True),
        ("verified_off_warm10", ref_snap, DELTA, None, False, True),
        ("verified_off_warm05", ref_snap, DELTA2, None, False, True),
        ("trust_off_cold", None, None, "trust", False, False),
        ("trust_off_warm10", ref_snap, DELTA, "trust", False, False),
        ("verified_on_cold", None, None, None, True, True),
        ("trust_on_cold", None, None, "trust", True, False),
        ("trust_on_warm10", ref_snap, DELTA, "trust", True, False),
    )
    for name, entry, delta, outer, prime, trace in plan:
        print(f"g3c: {scn} {name}", flush=True)
        pin = _pin_hex(scn, ref_m,
                       displaced_seed=(SEED if delta is not None else None),
                       delta=(delta if delta is not None else DELTA))
        r = run_eval(scn, "A1p", chain_dir(scn, name),
                     entry_state=entry, delta=delta,
                     seed=(SEED if delta is not None else 0),
                     outer=outer, pin_hex=pin, prime=prime, trace=trace)
        m = r["metrics"]
        runs[name] = r
        record["runs"][name] = {
            "status": m.get("status"),
            **_prime_counts_row(m),
            "exit_audit": _audit_summary(m),
            "pin_intact": m.get("pin_intact_at_exit"),
        }
        if r["rc"] != 0 or m.get("status") != "ok":
            print(f"  FAILURE PATH: {name} status {m.get('status')}")
            rc = 1
    if rc:
        (RUNS / "g3c").mkdir(parents=True, exist_ok=True)
        record["verdict"] = "FAIL (a run did not complete)"
        (RUNS / "g3c" / "g3c.json").write_text(json.dumps(record, indent=2))
        return rc

    # ---- A35's full mover classification on the traced chains -----------
    census = {}
    for name in ("verified_off_cold", "verified_off_warm10",
                 "verified_off_warm05", "verified_on_cold"):
        census[name] = analyze_deck(scn, name, Path(runs[name]["outdir"]),
                                    None, None)
    record["census"] = census

    # ---- carrier closure (the coefficients on this deck) ----------------
    closure = {}
    for name in ("verified_off_cold", "verified_off_warm10",
                 "verified_off_warm05"):
        closure[name] = _closure_for_entry(Path(runs[name]["outdir"]))
    record["carrier_closure"] = closure

    # ---- the open term ---------------------------------------------------
    joins = Joins(scn, runs["verified_off_cold"]["metrics"])
    open_term: dict = {
        "key": OPEN_TERM,
        "writer_nodes": joins.writers.get(OPEN_TERM, []),
        "writer_blocks": sorted({
            joins.node_block.get(n, f"?{n}")
            for n in joins.writers.get(OPEN_TERM, [])}),
        "owner_block": joins.comp_block.get(OPEN_TERM),
    }
    # two-coefficient solve a*d_in + b*d_out from the cold and warm10
    # entries, checked on warm05 (whose pair displacement is exactly half
    # warm10's on the same seed).
    rows = []
    for name in ("verified_off_cold", "verified_off_warm10",
                 "verified_off_warm05"):
        c = closure[name]
        ot = c.get("open_term")
        rows.append((name, c["pass1_raw_delta_dr_fw_inboard"],
                     c["pass1_raw_delta_dr_fw_outboard"],
                     None if ot is None else ot["pass2_raw_delta"]))
    open_term["per_entry"] = [
        {"entry": n, "d_in": di, "d_out": do, "pass2_raw_delta": mvd}
        for n, di, do, mvd in rows]
    (n1, di1, do1, m1), (n2, di2, do2, m2), (n3, di3, do3, m3) = rows
    if None not in (di1, do1, m1, di2, do2, m2):
        det = di1 * do2 - di2 * do1
        if det != 0.0:
            a = (m1 * do2 - m2 * do1) / det
            b = (di1 * m2 - di2 * m1) / det
            open_term["two_coefficient_solve"] = {
                "from_entries": [n1, n2],
                "a_on_d_in": a,
                "b_on_d_out": b,
                "note": ("|a*d_in + b*d_out| solved exactly from two "
                         "entries; the third entry is the consistency "
                         "check -- a linear image of the pair must "
                         "predict it"),
            }
            if None not in (di3, do3, m3):
                pred3 = abs(a * di3 + b * do3)
                open_term["two_coefficient_solve"]["check_entry"] = n3
                open_term["two_coefficient_solve"]["predicted_raw"] = pred3
                open_term["two_coefficient_solve"]["measured_raw"] = m3
                open_term["two_coefficient_solve"]["rel_difference"] = (
                    abs(m3 - pred3) / m3 if m3 else None)
    # delta-scaling of the open term (state-carried linearity: ~2x between
    # warm10 and warm05 on the same seed).
    if m2 is not None and m3:
        open_term["delta_ratio_warm10_over_warm05"] = m2 / m3
    # survival: is the open term above tau at the trust exits, prime off
    # and prime on?
    surv = {}
    for name in ("trust_off_cold", "trust_off_warm10", "trust_on_cold",
                 "trust_on_warm10"):
        above = _above_tau(runs[name]["outdir"])
        vec = json.loads((Path(runs[name]["outdir"])
                          / "audit_residual.json").read_text())
        surv[name] = {
            "n_above_tau": len(above),
            "open_term_scaled": vec["scaled"].get(OPEN_TERM),
            "open_term_scaled_hex": vec["scaled_hex"].get(OPEN_TERM),
            "open_term_above_tau": vec["scaled"].get(OPEN_TERM, 0.0) >= TAU,
            "top_movers": dict(sorted(above.items(),
                                      key=lambda kv: -kv[1])[:10]),
        }
    open_term["trust_exit_survival"] = surv
    open_term["verdict"] = (
        "CLOSES under the prime"
        if (surv["trust_off_warm10"]["open_term_above_tau"]
            and not surv["trust_on_warm10"]["open_term_above_tau"]
            and not surv["trust_on_cold"]["open_term_above_tau"])
        else ("SURVIVES the prime (residual mover)"
              if (surv["trust_on_warm10"]["open_term_above_tau"]
                  or surv["trust_on_cold"]["open_term_above_tau"])
              else "NOT ABOVE TAU at any trust exit (see numbers)"))
    record["open_term"] = open_term

    # residual movers with the prime on, named (the G3c deliverable).
    record["residual_movers_prime_on"] = {
        "trust_on_cold": _above_tau(runs["trust_on_cold"]["outdir"]),
        "trust_on_warm10": _above_tau(runs["trust_on_warm10"]["outdir"]),
    }

    # ---- teeth (parser integrity, A35 G3 lineage) ------------------------
    record["teeth"] = {
        "parser_tooth": _parser_tooth(
            Path(runs["verified_off_cold"]["outdir"])),
        "scaled_recompute_all_traced": {
            n: census[n]["scaled_recompute"] for n in census},
    }

    # ---- coverage --------------------------------------------------------
    cov = {}
    for name, rr in record["runs"].items():
        on = name.startswith(("verified_on", "trust_on"))
        cov[name] = {
            "n_prime_calls": rr["n_prime_calls"],
            "block_sweeps": rr["block_sweeps"],
            "ok": ((rr["n_prime_calls"] == rr["block_sweeps"]
                    and (rr["n_prime_calls"] or 0) > 0) if on
                   else rr["n_prime_calls"] == 0),
        }
    record["coverage_prime_calls_eq_block_sweeps"] = cov

    ok = (record["teeth"]["parser_tooth"].get("tripped")
          and all(v["ok"] for v in cov.values())
          and all(c["scaled_recompute"]["ok"] for c in census.values()))
    record["verdict"] = "PASS" if ok else "FAIL"
    if not ok:
        rc = 1
    (RUNS / "g3c").mkdir(parents=True, exist_ok=True)
    (RUNS / "g3c" / "g3c.json").write_text(json.dumps(record, indent=2))
    print(f"g3c: {record['verdict']} (open term: "
          f"{open_term['verdict']}) -> {RUNS / 'g3c' / 'g3c.json'}")
    return rc


# --------------------------------------------------------------------------
# analyze: collate
# --------------------------------------------------------------------------


def stage_analyze() -> int:
    out: dict = {"provenance": provenance(), "gates": {}}
    for name, path in (("G1", RUNS / "g1" / "g1.json"),
                       ("G2", RUNS / "g2" / "g2.json"),
                       ("G3", RUNS / "g3" / "g3.json"),
                       ("G3c", RUNS / "g3c" / "g3c.json")):
        if path.exists():
            rec = json.loads(path.read_text())
            out["gates"][name] = {"verdict": rec.get("verdict"),
                                  "record": str(path)}
        else:
            out["gates"][name] = {"verdict": "NOT RUN"}
    out["all_pass"] = all(g["verdict"] == "PASS"
                          for g in out["gates"].values())
    (RUNS / "analysis").mkdir(parents=True, exist_ok=True)
    (RUNS / "analysis" / "summary.json").write_text(
        json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
    return 0 if out["all_pass"] else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("stage", choices=["g1base", "g1", "g2", "g3", "g3c",
                                      "analyze"])
    args = ap.parse_args()
    RUNS.mkdir(parents=True, exist_ok=True)
    (RUNS / "g1").mkdir(parents=True, exist_ok=True)
    return {
        "g1base": stage_g1base,
        "g1": stage_g1,
        "g2": stage_g2,
        "g3": stage_g3,
        "g3c": stage_g3c,
        "analyze": stage_analyze,
    }[args.stage]()


if __name__ == "__main__":
    raise SystemExit(main())
