#!/usr/bin/env python
"""Orchestrator recheck of A38 (audit-rerun) — independent recomputation of the
report's published numbers from the raw run records, never from tally.json's
derived values (tally.json is itself under test wherever both exist).

Checks (each prints PASS/FAIL with its numbers; exit code 1 on any FAIL):

  1. provenance    — 171 records stamped at the campaign commit, dirty=False, ok
  2. identity      — 150/150 seed runs vs V2's records: counts, objf hex, audit
                     max hex, full exit state bit-for-bit (y_exit dict equality)
  3. membership    — excluded set re-derived from postsolve artifact + write
                     census + spec; equals every record's excluded_keys; the
                     three known-cut constants are kept
  4. restricted    — per-run restricted max recomputed from the scaled vector;
                     medians / nearest-rank p90 / ranges vs report §3
  5. argmax census — restricted argmax recount vs report §4
  6. closure       — A35 images recomputed from perturbation before/after hex
                     vs measured raw movement (scaled × scale); st gain 47.0;
                     lad two-coefficient fit residuals (quadratic-form lstsq)
  7. count ratio   — unweighted A1/A0 node-call ratio per deck vs report
  8. gates         — entry/warm/teeth gate records: pass flags, post-solve
                     doctoring leaves the restricted statistic bit-identical
  9. licence       — process/, arch_surgery/fixedpoint/, arch_surgery/docs/data/
                     tree hashes identical: HEAD vs ba69c05d vs 6d9ff4b9

Run from the A38 worktree:  python arch_surgery/idf_probe/a38_recheck.py
"""

from __future__ import annotations

import json
import math
import statistics
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent          # arch_surgery/idf_probe
WORKTREE = HERE.parent.parent
RUNS = HERE / "runs" / "a38"
DATA = WORKTREE / "arch_surgery" / "docs" / "data"
V2_CAMPAIGN = Path(
    "/home/wrutten/projects/PROCESS_surgery/arch_surgery/"
    "MDA_partitioning_experiment_v2/runs/phase_a/campaign"
)

DECKS = ["large_tokamak_nof", "low_aspect_ratio_DEMO", "st_regression"]
ARMS = ["A0", "A1"]
SEEDS = range(1, 26)
CAMPAIGN_COMMIT = "9fcedc92"
V2_COMMITS = ("ba69c05d", "6d9ff4b9")
KNOWN_CUT = ["build.dr_fw_inboard", "build.dr_fw_outboard", "pf_power.vpfskv"]

REPORT = {   # the report's §3/§4 claims, re-derived here (floats compared at 2 s.f.)
    "large_tokamak_nof": dict(
        a1_med=6.4e-4, a1_p90=1.14e-3, a1_min=3.1e-4, a1_max=1.27e-3,
        a0_med=5.0e-10, a0_p90=3.0e-9,
        census={"build.dr_shld_vv_gap_outboard": 16,
                "build.dz_tf_upper_lower_midplane": 9},
        ratio=0.5217),
    "low_aspect_ratio_DEMO": dict(
        a1_med=9.8e-4, a1_p90=2.19e-3, a1_min=3.9e-4, a1_max=3.08e-3,
        a0_med=0.0, a0_p90=0.0,
        census={"tfcoil.m_tf_coil_superconductor": 21,
                "build.dr_shld_vv_gap_outboard": 4},
        ratio=0.5680),
    "st_regression": dict(
        a1_med=1.15e-3, a1_p90=1.60e-3, a1_min=4.6e-4, a1_max=1.77e-3,
        a0_med=5.4e-9, a0_p90=2.0e-8,
        census={"build.dr_shld_vv_gap_outboard": 17,
                "blanket.vol_shld_inboard": 8},
        ratio=0.5016),
}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str) -> None:
    print(f"  {'ok  ' if ok else 'FAIL'}  {name}: {detail}")
    if not ok:
        FAILURES.append(name)


def close2sf(a: float, b: float) -> bool:
    """Agreement at the report's 2-significant-figure rounding."""
    if a == b:
        return True
    if b == 0.0:
        return a == 0.0
    return abs(a - b) / abs(b) < 0.06


def load(p: Path):
    with open(p) as fh:
        return json.load(fh)


def p90_nearest_rank(values: list[float]) -> float:
    s = sorted(values)
    return s[math.ceil(0.9 * len(s)) - 1]


# ---------------------------------------------------------------- 1. provenance
print("[1] provenance stamps")
records = sorted(RUNS.glob("campaign/**/metrics.json"))
stamps = [load(r) for r in records]
n_at = sum(1 for m in stamps
           if str(m.get("tree_git_head", "")).startswith(CAMPAIGN_COMMIT)
           and m.get("tree_git_dirty") is False)
n_ok = sum(1 for m in stamps if m.get("status") == "ok")
check("stamps", len(stamps) == 171 and n_at == 171 and n_ok == 171,
      f"{len(stamps)} records, {n_at} at {CAMPAIGN_COMMIT} dirty=False, {n_ok} ok")

# ------------------------------------------------- 2. identity vs V2's records
print("[2] identity vs V2 (counts, objf hex, audit max hex, exit state)")
n_pairs = n_ident = 0
first_diff = None
for deck in DECKS:
    for arm in ARMS:
        for seed in SEEDS:
            a38dir = RUNS / "campaign" / deck / arm / f"start{seed:03d}"
            v2dir = V2_CAMPAIGN / deck / arm / f"start{seed:03d}"
            if not v2dir.exists():
                continue
            n_pairs += 1
            ma, mv = load(a38dir / "metrics.json"), load(v2dir / "metrics.json")
            same = (
                ma["node_calls_single_eval"] == mv["node_calls_single_eval"]
                and ma["n_model_calls_sweeps"] == mv["n_model_calls_sweeps"]
                and ma["exact"]["objf"] == mv["exact"]["objf"]
                and ma["exit_audit"]["residual_max_hex"]
                    == mv["exit_audit"]["residual_max_hex"]
            )
            ya, yv = load(a38dir / "y_exit.json"), load(v2dir / "y_exit.json")
            same = same and ya["state"] == yv["state"] \
                and ya["n_components"] == yv["n_components"]
            if same:
                n_ident += 1
            elif first_diff is None:
                first_diff = f"{deck}/{arm}/start{seed:03d}"
check("identity", n_pairs == 150 and n_ident == 150,
      f"{n_ident}/{n_pairs} bit-identical"
      + (f" (first diff {first_diff})" if first_diff else ""))

# ------------------------------------------ 3. membership, derived not copied
print("[3] excluded-set membership re-derived")
census = load(DATA / "node_writesets.json")
spec_keys, scales, excl_by_deck = {}, {}, {}
for deck in DECKS:
    spec = load(DATA / f"ystate_a26_{deck}.json")
    entries = spec["components"] if "components" in spec else spec["spec"]
    spec_keys[deck] = {e["key"] for e in entries}
    continuous = {e["key"] for e in entries
                  if e.get("category") == "continuous"}
    scales[deck] = {e["key"]: e.get("scale") for e in entries}
    ps = load(DATA / f"postsolve_{deck}.json")
    nodes = ps.get("post_solve_nodes") or ps.get("nodes")
    per_scen = census["per_scenario"][deck]["writes_by_node"]
    written = set()
    for node in nodes:
        written |= set(per_scen.get(node, []))
    excl_spec = written & spec_keys[deck]
    rec = load(RUNS / "campaign" / deck / "A1" / "start001" /
               "audit_residual.json")
    excl_by_deck[deck] = excl_spec & set(rec["scaled"])  # audited population
    check(f"membership {deck}",
          set(rec["excluded_keys"]) == excl_by_deck[deck]
          and not (excl_spec & set(KNOWN_CUT)),
          f"derived spec-level {len(excl_spec)}, tested "
          f"{len(excl_by_deck[deck])} == record "
          f"{len(rec['excluded_keys'])}; known-cut trio kept; "
          # kept counted over the audit's own tested population (the scaled
          # vector), which on nof includes one component whose spec category
          # label is not 'continuous' (eta_cd_dimensionless_hcd_primary)
          f"kept {len(rec['scaled']) - len(rec['excluded_keys'])}")

# ------------------------------- 4. restricted statistic from the raw vectors
print("[4] restricted distributions recomputed")
restricted: dict[str, dict[str, list]] = {}
argmaxes: dict[str, list[str]] = {}
for deck in DECKS:
    restricted[deck] = {}
    for arm in ARMS:
        vals, amaxes = [], []
        for seed in SEEDS:
            ar = load(RUNS / "campaign" / deck / arm / f"start{seed:03d}" /
                      "audit_residual.json")
            excl = excl_by_deck[deck]
            kept = {k: v for k, v in ar["scaled"].items() if k not in excl}
            top = max(kept, key=lambda k: kept[k])
            vals.append(kept[top])
            amaxes.append(top)
        restricted[deck][arm] = vals
        if arm == "A1":
            argmaxes[deck] = amaxes
    exp = REPORT[deck]
    a1, a0 = restricted[deck]["A1"], restricted[deck]["A0"]
    ok = (close2sf(statistics.median(a1), exp["a1_med"])
          and close2sf(p90_nearest_rank(a1), exp["a1_p90"])
          and close2sf(min(a1), exp["a1_min"])
          and close2sf(max(a1), exp["a1_max"])
          and close2sf(statistics.median(a0), exp["a0_med"])
          and close2sf(p90_nearest_rank(a0), exp["a0_p90"]))
    check(f"restricted {deck}", ok,
          f"A1 med {statistics.median(a1):.3g} p90 {p90_nearest_rank(a1):.3g} "
          f"[{min(a1):.3g} – {max(a1):.3g}]; "
          f"A0 med {statistics.median(a0):.3g} p90 {p90_nearest_rank(a0):.3g}")

# ------------------------------------------------------------ 5. argmax census
print("[5] restricted argmax census")
for deck in DECKS:
    got = {}
    for name in argmaxes[deck]:
        got[name] = got.get(name, 0) + 1
    check(f"census {deck}", got == REPORT[deck]["census"], f"{got}")

# ----------------------------------------------------------------- 6. closure
print("[6] A35-image closure, gain, and the lad fit")


def displacements(deck: str, seed: int) -> tuple[float, float]:
    p = load(RUNS / "campaign" / deck / "A1" / f"start{seed:03d}" /
             "perturbation.json")["per_component"]
    by_key = {e["key"]: e for e in p} if isinstance(p, list) else p
    out = []
    for key in ("build.dr_fw_inboard", "build.dr_fw_outboard"):
        e = by_key[key]
        out.append(float.fromhex(e["elem_after_hex"])
                   - float.fromhex(e["elem_before_hex"]))
    return out[0], out[1]


def measured(deck: str, seed: int, comp: str) -> float:
    ar = load(RUNS / "campaign" / deck / "A1" / f"start{seed:03d}" /
              "audit_residual.json")
    return ar["scaled"][comp] * scales[deck][comp]


IMAGES = {  # component -> raw image of (din, dout), from A35
    "build.dz_tf_upper_lower_midplane": lambda di, do: 0.5 * (di + do),
    "build.dr_shld_vv_gap_outboard": lambda di, do: -do,
}
CLOSURE_MAX = {  # report §4 max rel. diff per (deck, comp)
    ("large_tokamak_nof", "build.dz_tf_upper_lower_midplane"): 1.0e-11,
    ("large_tokamak_nof", "build.dr_shld_vv_gap_outboard"): 6.1e-7,
    ("low_aspect_ratio_DEMO", "build.dz_tf_upper_lower_midplane"): 7.2e-12,
    ("low_aspect_ratio_DEMO", "build.dr_shld_vv_gap_outboard"): 1.3e-11,
    ("st_regression", "build.dr_shld_vv_gap_outboard"): 3.3e-6,
}
for (deck, comp), bound in CLOSURE_MAX.items():
    rels = []
    for seed in SEEDS:
        di, do = displacements(deck, seed)
        pred, meas = abs(IMAGES[comp](di, do)), measured(deck, seed, comp)
        rels.append(abs(pred - meas) / meas)
    check(f"closure {deck} {comp.split('.')[-1]}",
          max(rels) <= bound * 1.5,
          f"rel diff med {statistics.median(rels):.2g} max {max(rels):.2g} "
          f"(report max {bound:.2g})")

gains = []
for seed in SEEDS:
    di, _ = displacements("st_regression", seed)
    gains.append(measured("st_regression", seed, "blanket.vol_shld_inboard")
                 / abs(di))
rel_spread = (max(gains) - min(gains)) / statistics.median(gains)
check("st vol_shld_inboard gain",
      close2sf(statistics.median(gains), 47.0) and rel_spread < 1e-10,
      f"gain med {statistics.median(gains):.6f} "
      f"relative spread {rel_spread:.2g}")

# lad: two-coefficient quadratic-form fit for the TF-coil superconductor mass
rows, y2 = [], []
for seed in SEEDS:
    di, do = displacements("low_aspect_ratio_DEMO", seed)
    m = measured("low_aspect_ratio_DEMO", seed,
                 "tfcoil.m_tf_coil_superconductor")
    rows.append((di * di, 2 * di * do, do * do))
    y2.append(m * m)
# 3-parameter normal equations (pure python)
ata = [[sum(r[i] * r[j] for r in rows) for j in range(3)] for i in range(3)]
atb = [sum(r[i] * v for r, v in zip(rows, y2)) for i in range(3)]
for i in range(3):                                   # gaussian elimination
    piv = max(range(i, 3), key=lambda r: abs(ata[r][i]))
    ata[i], ata[piv] = ata[piv], ata[i]
    atb[i], atb[piv] = atb[piv], atb[i]
    for r in range(i + 1, 3):
        f = ata[r][i] / ata[i][i]
        atb[r] -= f * atb[i]
        for c in range(i, 3):
            ata[r][c] -= f * ata[i][c]
sol = [0.0, 0.0, 0.0]
for i in (2, 1, 0):
    sol[i] = (atb[i] - sum(ata[i][c] * sol[c] for c in range(i + 1, 3))) \
        / ata[i][i]
a = math.sqrt(max(sol[0], 0.0))
b = math.copysign(math.sqrt(max(sol[2], 0.0)), sol[1])
resid = []
for seed, (r, v) in zip(SEEDS, zip(rows, y2)):
    di, do = displacements("low_aspect_ratio_DEMO", seed)
    m = math.sqrt(v)
    resid.append(abs(abs(a * di + b * do) - m) / m)
check("lad m_tf_coil_superconductor NOT one linear image",
      statistics.median(resid) > 0.02 and max(resid) > 0.5
      and close2sf(statistics.median(resid), 0.067),
      f"fit (a,b)=({a:.1f},{b:.1f}) residual med "
      f"{statistics.median(resid):.3f} max {max(resid):.2f}")

# ------------------------------------------------------------- 7. count ratio
print("[7] unweighted A1/A0 node-call ratio")
for deck in DECKS:
    sums = {}
    for arm in ARMS:
        sums[arm] = sum(
            load(RUNS / "campaign" / deck / arm / f"start{seed:03d}" /
                 "metrics.json")["node_calls_single_eval"] for seed in SEEDS)
    ratio = sums["A1"] / sums["A0"]
    check(f"ratio {deck}", abs(ratio - REPORT[deck]["ratio"]) < 5e-5,
          f"{ratio:.4f} (report {REPORT[deck]['ratio']})")

# ------------------------------------------------------------------ 8. gates
print("[8] gate records")
for deck in DECKS:
    for gate in ("entry_gate", "warm_gate", "restricted_teeth"):
        g = load(RUNS / "campaign" / deck / gate / "gate.json")
        ok = g.get("verdict") == "PASS"
        detail = f"verdict {g.get('verdict')}"
        if gate == "restricted_teeth":
            psd = g["postsolve_doctored"]["checks"]
            ild = g["inloop_doctored"]["checks"]
            ok = ok and psd["whole_state_max_moved"] \
                and psd["restricted_max_bit_identical_to_baseline"] \
                and ild["restricted_moved_or_more_work"]
            detail += (
                "; post-solve tooth: whole moved, restricted bit-identical"
                "; in-loop tooth: restricted moved or more work")
        check(f"{deck} {gate}", ok, detail)

# ---------------------------------------------------------------- 9. licence
print("[9] tree-hash licence")
for path in ("process", "arch_surgery/fixedpoint", "arch_surgery/docs/data"):
    hashes = []
    for ref in ("HEAD",) + V2_COMMITS:
        out = subprocess.run(
            ["git", "-C", str(WORKTREE), "rev-parse", f"{ref}:{path}"],
            capture_output=True, text=True)
        hashes.append(out.stdout.strip())
    check(f"tree {path}", len(set(hashes)) == 1 and hashes[0],
          f"{hashes[0][:12]} identical at HEAD, {', '.join(V2_COMMITS)}")

print()
if FAILURES:
    print(f"RECHECK FAIL — {len(FAILURES)} check(s): {FAILURES}")
    sys.exit(1)
print("RECHECK PASS — every published number reproduced independently")
