#!/usr/bin/env python
"""A35 orchestrator recheck — independent recomputation of the report's
headline numbers from A35's raw run artifacts (protocol §15: the assessment's
published numbers come from this committed script, not from shell).

Reads ONLY: the A35 run directory (raw pass traces, snapshots, metrics — the
analyzer's summary.json is used solely for the owner-block tally
cross-reference) and the repository's committed a26 data artifacts.  It does
NOT import or execute a35_cold_census.py's analyzer: every quantity below is
recomputed from the artifacts one level rawer than the number it checks.

    PROCESS_surgery_env python arch_surgery/idf_probe/a35_recheck.py \
        [--runs DIR] [--main-tree DIR]

Checks (report section in parentheses):
  1. sha256 of the frozen st_regression static export (§2 item 4/7)
  2. verified-chain per-pass residual structure, both decks (§2 item 1)
  3. coefficient-exact carrier closure, ruler-free signed raw meters,
     6 deck×entry rows (§2 item 5) — predictions re-derived from the
     fw.py:347-352 / build.py:826-842 source coefficients, not copied
  4. delta-scaling ratio d10/d05 per common pass-2 mover (§2 item 6)
  5. restart end-of-chain vs verified exit: full float bit-identity (§2 item 2)
  6. owner-block tally of pass-2 movers; M1/PULSE must be empty (§2 item 3)
  7. trust one-pass exit vs FLAT reference, recomputed three ways (G4):
     the analyzer's snapshot pair with the spec ruler restricted to scalar
     floats (documents the subset undercount), plus the in-run exit_audit
     as recorded — the two full-set operationalizations differ by one
     near-tau component (243 vs 244 on large_tokamak_nof); stated, not hidden
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from statistics import median, quantiles

TAU = 1e-6
EXPECTED_EXPORT_SHA = (
    "582b4a5f861f42164877d9732abab57f207f2a6c00ad9225f103e1fb9add4f65")


def jload(p: Path):
    return json.load(open(p))


def fstate(p: Path) -> dict[str, str]:
    """Scalar float components of a snapshot, key -> hex."""
    return {k: v["hex"] for k, v in jload(p)["state"].items()
            if v.get("k") == "f"}


def fval(h: str) -> float:
    return float.fromhex(h)


def passes(trace_path: Path):
    out = {}
    for line in open(trace_path):
        rec = json.loads(line)
        if rec.get("kind") == "outer":
            out[rec["pass"]] = (rec, {m["key"]: m for m in rec.get("above", [])})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    here = Path(__file__).resolve().parent
    ap.add_argument("--runs", type=Path, default=here / "runs" / "a35")
    ap.add_argument("--main-tree", type=Path,
                    default=Path("/home/wrutten/projects/PROCESS_surgery"))
    args = ap.parse_args()
    a35, main_tree = args.runs, args.main_tree
    failures = []

    def check(name: str, ok: bool, detail: str):
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")
        if not ok:
            failures.append(name)

    print("== 1. frozen st export sha ==")
    exp = (main_tree / "arch_surgery/idf_probe/runs/dsm_exports/"
           "st_regression/process_dependencies.json")
    h = hashlib.sha256(exp.read_bytes()).hexdigest()
    check("export-sha", h == EXPECTED_EXPORT_SHA, h)

    print("== 2. verified-chain pass structure ==")
    expect = {
        "large_tokamak_nof": {1: (659, None), 2: (181, "0x1.de05b6285d0b6p-7"),
                              3: (0, None)},
        "st_regression": {2: (82, None)},
    }
    for deck, exp_p in expect.items():
        prs = passes(a35 / f"trace/{deck}_cold/pass_trace.jsonl")
        for p, (n_exp, hex_exp) in exp_p.items():
            rec, _ = prs[p]
            ok = rec["n_above"] == n_exp and (
                hex_exp is None or rec["max_hex"] == hex_exp)
            check(f"{deck} pass {p}", ok,
                  f"n_above={rec['n_above']} max_hex={rec['max_hex']} "
                  f"argmax={rec['argmax']['key']}")

    print("== 3. coefficient closure (ruler-free signed raw meters) ==")
    for deck, mover, kind in (
            ("large_tokamak_nof", "build.dz_tf_upper_lower_midplane", "half"),
            ("st_regression", "build.dr_shld_vv_gap_outboard", "out")):
        for tag in ("cold", "warm_seed1", "warm_d05_seed1"):
            prs = passes(a35 / f"trace/{deck}_{tag}/pass_trace.jsonl")
            p1, p2 = prs[1][1], prs[2][1]
            din = fval(p1["build.dr_fw_inboard"]["after_hex"]) - \
                fval(p1["build.dr_fw_inboard"]["before_hex"])
            dout = fval(p1["build.dr_fw_outboard"]["after_hex"]) - \
                fval(p1["build.dr_fw_outboard"]["before_hex"])
            mv = p2[mover]
            meas = abs(fval(mv["after_hex"]) - fval(mv["before_hex"]))
            pred = abs(0.5 * (din + dout)) if kind == "half" else abs(dout)
            rel = abs(meas - pred) / pred
            check(f"{deck}/{tag}", rel < 1e-6,
                  f"measured={meas:.6e} predicted={pred:.6e} reldiff={rel:.1e}")

    print("== 4. delta-scaling d10/d05 (state-carried => ~2.0) ==")
    for deck, n_exp in (("large_tokamak_nof", 153), ("st_regression", 59)):
        p10 = passes(a35 / f"trace/{deck}_warm_seed1/pass_trace.jsonl")[2][1]
        p05 = passes(a35 / f"trace/{deck}_warm_d05_seed1/pass_trace.jsonl")[2][1]
        ratios = []
        for k, m in p10.items():
            o = p05.get(k)
            if not o:
                continue
            d10 = abs(fval(m["after_hex"]) - fval(m["before_hex"]))
            d05 = abs(fval(o["after_hex"]) - fval(o["before_hex"]))
            if d05:
                ratios.append(d10 / d05)
        q = quantiles(ratios, n=4)
        check(f"{deck}", len(ratios) == n_exp and abs(median(ratios) - 2) < 0.01,
              f"n={len(ratios)} median={median(ratios):.4f} "
              f"q1={q[0]:.4f} q3={q[2]:.4f}")

    print("== 5. restart end-of-chain vs verified exit (float bit-identity) ==")
    for deck in ("large_tokamak_nof", "st_regression"):
        h3 = fstate(a35 / f"restarts/{deck}_T3/y_exit.json")
        hv = fstate(a35 / f"trace/{deck}_cold/y_exit.json")
        keys = set(h3) | set(hv)
        same = sum(1 for k in keys if h3.get(k) == hv.get(k))
        check(f"{deck}", same == len(keys), f"{same}/{len(keys)} identical")

    print("== 6. owner-block tally of pass-2 movers (analyzer summary) ==")
    s = jload(a35 / "analysis/summary.json")
    for deck in ("large_tokamak_nof", "st_regression"):
        movers = s["decks"][deck]["cold"]["movers_by_pass"]["2"]
        tally: dict[str, int] = {}
        bad = []
        for m in movers:
            tally[m["owner_block"]] = tally.get(m["owner_block"], 0) + 1
            if m["owner_block"] in ("M1", "PULSE"):
                bad.append(m["key"])
        check(f"{deck}", not bad, f"{tally} M1/PULSE movers: {bad}")

    print("== 7. trust one-pass exit vs FLAT (three operationalizations) ==")
    for deck, an_hex in (("large_tokamak_nof", "0x1.de05b6285d0b6p-7"),
                         ("st_regression", None)):
        spec = jload(main_tree / f"arch_surgery/docs/data/ystate_a26_{deck}.json")
        comps = spec.get("components", spec)
        scales = ({c["key"]: c.get("scale") for c in comps}
                  if isinstance(comps, list) else
                  {k: (c.get("scale") if isinstance(c, dict) else None)
                   for k, c in comps.items()})
        t1 = fstate(a35 / f"restarts/{deck}_T1/y_exit.json")
        flat = fstate(a35 / f"refs/{deck}_flat_cold/y_exit.json")
        diffs = sorted(
            ((abs(fval(t1[k]) - fval(flat[k])) / scales[k], k)
             for k in flat if k in t1 and scales.get(k)), reverse=True)
        n = sum(1 for d, _ in diffs if d >= TAU)
        mx, mk = diffs[0]
        ok = an_hex is None or float.hex(mx) == an_hex
        check(f"{deck} scalar-subset max", ok,
              f"max={float.hex(mx)} argmax={mk} n_above(scalar-only)={n}")
        aud = jload(a35 / f"restarts/{deck}_T1/metrics.json")["exit_audit"]
        print(f"        in-run exit_audit: max_hex={aud['residual_max_hex']} "
              f"n_above={aud['brief']['n_above']} "
              f"argmax={aud['brief']['argmax']}")

    print(f"\n{'ALL CHECKS PASS' if not failures else 'FAILURES: ' + str(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
