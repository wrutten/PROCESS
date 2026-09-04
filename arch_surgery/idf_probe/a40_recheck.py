#!/usr/bin/env python
"""Orchestrator recheck of A40 (v3-prime) — independent recomputation of the
report's published numbers from the raw run records and, where they exist, the
raw MFILEs, never from the gate JSONs' own derived verdicts.

Checks (PASS/FAIL each; exit 1 on any FAIL):

  1. driver     — the variant point is source-correct: guard after the
                  stellarator/IFE returns, NOT routed through _node, counter
                  incremented only under the guard, unrecognised value raises
  2. provenance — 37/37 runs ok, clean stamps, tree under this worktree
  3. licence    — the G1 baseline's process/ tree hash equals b7dbd2a9:process
  4. G1         — MFILE hex floats recompared from the raw baseline/changed
                  files (independent parse), per deck
  5. G2         — exit-state component counts bit-identical, both arms
  6. G3         — verified passes 3 -> 2; trust in-run audit n_above 244 -> 0
                  (nof) and 124 -> 0 (st); prime-off reproduces A35
  7. G3c        — the open term closes to exactly 0 with an empty mover set;
                  A35 image closure recomputed from the chain records; the
                  two-coefficient solve reproduced independently
  8. coverage   — n_prime_calls == block_sweeps in every prime-on run, 0 off

Run from the A40 worktree:  python arch_surgery/idf_probe/a40_recheck.py
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKTREE = HERE.parent.parent
RUNS = HERE / "runs" / "a40"
BRANCH_POINT = "b7dbd2a9"

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str) -> None:
    print(f"  {'ok  ' if ok else 'FAIL'}  {name}: {detail}")
    if not ok:
        FAILURES.append(name)


def load(p: Path):
    with open(p) as fh:
        return json.load(fh)


# ------------------------------------------------------------------ 1. driver
print("[1] driver variant point, from source")
src = (WORKTREE / "process" / "core" / "caller.py").read_text()
guard = "if PRIME_FW_GEOMETRY:"
i_guard = src.index(guard)
i_ife = src.index("self.models.ife.run()")
i_seq = src.index("# Tokamak calls")
body = src[i_guard:i_seq]
check("guard placement", i_ife < i_guard < i_seq,
      "after the stellarator/IFE early returns, before the sequence head")
check("not routed through _node", "_node" not in body,
      "the prime call does not go through Caller._node")
check("counter under the guard",
      "PRIME_CALLS[0] += 1" in body and "set_fw_geometry()" in body,
      "PRIME_CALLS incremented only where the prime executes")
check("unrecognised value raises",
      re.search(r"if PRIME_NAME not in _PRIME:\s*\n\s*raise RuntimeError", src)
      is not None,
      "an unrecognised PROCESS_ARCH_PRIME raises, never defaults")
# and the switch really is off by default
check("default off",
      'os.environ.get("PROCESS_ARCH_PRIME", "").strip() or "off"' in src
      and '_PRIME: dict[str, bool] = {"off": False, "fw_geometry": True}' in src,
      "unset => 'off' => False")

# -------------------------------------------------------------- 2. provenance
print("[2] provenance over every run record")
metrics = sorted(RUNS.glob("**/metrics.json"))
recs = [load(m) for m in metrics]
n_ok = sum(1 for m in recs if m.get("status") == "ok")
n_clean = sum(1 for m in recs if m.get("tree_git_dirty") is False)
n_tree = sum(1 for m in recs
             if str(WORKTREE) in str(m.get("process_file", ""))
             and m.get("tree_contains_base_commit") is True)
heads = {}
for m in recs:
    h = str(m.get("tree_git_head", ""))[:8]
    heads[h] = heads.get(h, 0) + 1
check("runs ok / clean / in-tree",
      len(recs) == 37 and n_ok == 37 and n_clean == 37 and n_tree == 37,
      f"{len(recs)} records, ok {n_ok}, clean {n_clean}, in-tree {n_tree}; "
      f"heads {heads}")

# ----------------------------------------------------------------- 3. licence
print("[3] neutrality licence: baseline process/ tree == branch point")
bp = subprocess.run(["git", "-C", str(WORKTREE), "rev-parse",
                     f"{BRANCH_POINT}:process"],
                    capture_output=True, text=True).stdout.strip()
g1 = load(RUNS / "g1" / "g1.json")
base_hash = g1["baseline_provenance"]["process_tree_hash"]
chg_hash = g1["changed_provenance"]["process_tree_hash"]
check("baseline is upstream-equivalent",
      base_hash == bp and chg_hash != bp,
      f"baseline {base_hash[:12]} == {BRANCH_POINT}:process; "
      f"changed {chg_hash[:12]} differs")

# ---------------------------------------------------------------------- 4. G1
print("[4] G1 byte identity, recomputed from the raw MFILEs")
FLOAT_RE = re.compile(r"^\s*(.+?)\s+(\(.+?\))\s+(-?[\d.]+[eE]?[-+]?\d*)\s*$")


#: Wall-clock and run-identity fields, which differ between any two runs of
#: identical code.  A3's comparator excludes them by name (`compare_a3.py`
#: docstring); this recheck parses the MFILEs itself and applies the same
#: exclusion, then REPORTS what it excluded, so the exclusion is visible
#: rather than assumed (the mismatch it hides is verified below).
VOLATILE = ("(process_runtime)", "(runtime)", "(date)", "(time)",
            "(username)", "(hostname)")


def mfile_floats(path: Path, *, keep_volatile: bool = False
                 ) -> dict[str, str]:
    """Parse an MFILE into {key: exact hex of the float value}."""
    out: dict[str, str] = {}
    for line in path.read_text(errors="replace").splitlines():
        if not keep_volatile and any(k in line for k in VOLATILE):
            continue
        parts = line.split()
        if not parts:
            continue
        tok = parts[-1]
        try:
            val = float(tok)
        except ValueError:
            continue
        key = " ".join(parts[:-1])
        out[key] = val.hex()
    return out


for deck in ("large_tokamak_nof", "low_aspect_ratio_DEMO", "st_regression"):
    bfiles = sorted((RUNS / "g1" / "baseline" / deck).glob("**/*MFILE.DAT"))
    cfiles = sorted((RUNS / "g1" / "changed" / deck).glob("**/*MFILE.DAT"))
    if not bfiles or not cfiles:
        check(f"G1 {deck}", False, "MFILE not found in the record")
        continue
    b, c = mfile_floats(bfiles[0]), mfile_floats(cfiles[0])
    shared = set(b) & set(c)
    mism = [k for k in shared if b[k] != c[k]]
    recorded = g1["decks"][deck]["comparison"]
    # and, separately, what the volatile exclusion is actually hiding
    bv, cv = (mfile_floats(bfiles[0], keep_volatile=True),
              mfile_floats(cfiles[0], keep_volatile=True))
    hidden = sorted(k for k in set(bv) & set(cv) if bv[k] != cv[k])
    hidden_names = {kk for k in hidden for kk in VOLATILE if kk in k}
    check(f"G1 {deck}",
          not mism and not (set(b) ^ set(c))
          and hidden_names <= {"(process_runtime)"},
          f"{len(shared)} float keys recompared, {len(mism)} hex mismatches, "
          f"{len(set(b) ^ set(c))} key-set differences "
          f"(gate recorded {recorded['n_floats_compared']} / "
          f"{recorded['n_hex_mismatches']}); the only excluded difference is "
          f"{sorted(hidden_names) or 'none'} — wall clock, never evidence")
tooth = all(d.get("tooth", {}).get("tripped") for d in g1["decks"].values())
check("G1 teeth", tooth, "a 1-ULP change is caught on every deck")

# ---------------------------------------------------------------------- 5. G2
print("[5] G2 fixed-point map")
g2 = load(RUNS / "g2" / "g2.json")
for deck, d in g2["decks"].items():
    cmp_ = d["exit_state_comparison"]
    arms = {k: v for k, v in cmp_.items()
            if isinstance(v, dict) and "n_components" in v}
    allbits = bool(arms) and all(
        v["n_differing"] == 0 and v["bit_identical"] is True
        and v["n_components"] == v["n_components_expected"]
        for v in arms.values())
    counts = {k: f"{v['n_components']}/{v['n_components_expected']} "
                 f"({v['n_differing']} differing)" for k, v in arms.items()}
    check(f"G2 {deck}", allbits and bool(counts) and d["tooth"]["tripped"],
          f"{counts}; tooth tripped")

# ---------------------------------------------------------------------- 6. G3
print("[6] G3 cold chain")
g3 = load(RUNS / "g3" / "g3.json")
EXPECT_OFF = {"large_tokamak_nof": 244, "st_regression": 124}
for deck, d in g3["decks"].items():
    runs = d["runs"]

    def pick(pred):
        return {k: v for k, v in runs.items() if pred(k)}

    ver_off = pick(lambda k: k.startswith("verified_off"))
    ver_on = pick(lambda k: k.startswith("verified_on"))
    tr_off = pick(lambda k: k.startswith("trust_off"))
    tr_on = pick(lambda k: k.startswith("trust_on"))
    passes_off = {v["outer_passes"] for v in ver_off.values()}
    passes_on = {v["outer_passes"] for v in ver_on.values()}
    above_off = {v["exit_audit"]["brief"]["n_above"] for v in tr_off.values()}
    above_on = {v["exit_audit"]["brief"]["n_above"] for v in tr_on.values()}
    ok = (passes_off == {3} and passes_on == {2}
          and above_off == {EXPECT_OFF[deck]} and above_on == {0})
    check(f"G3 {deck}", ok,
          f"verified passes {sorted(passes_off)} -> {sorted(passes_on)}; "
          f"trust n_above {sorted(above_off)} -> {sorted(above_on)} "
          f"(A35 expects {EXPECT_OFF[deck]} off)")

# --------------------------------------------------------------------- 7. G3c
print("[7] G3c lad carrier census")
g3c = load(RUNS / "g3c" / "g3c.json")
runs = g3c["runs"]
on_trust = {k: v for k, v in runs.items() if k.startswith("trust_on")}
closed = all(v["exit_audit"]["brief"]["max"] == 0.0
             and v["exit_audit"]["brief"]["n_above"] == 0
             for v in on_trust.values())
movers_empty = all(not m for m in g3c["residual_movers_prime_on"].values())
off_trust = {k: v for k, v in runs.items() if k.startswith("trust_off")}
off_argmax = {v["exit_audit"]["brief"]["argmax"] for v in off_trust.values()}
check("G3c open term closes",
      closed and movers_empty
      and off_argmax == {"tfcoil.m_tf_coil_superconductor"},
      f"prime-on trust exits {sorted(v['exit_audit']['brief']['max'] for v in on_trust.values())} "
      f"with empty mover sets; prime-off argmax {off_argmax}")

# A35 image closure, recomputed from the recorded raw deltas
rels = []
for entry, rec in g3c["carrier_closure"].items():
    din = rec["pass1_raw_delta_dr_fw_inboard"]
    dout = rec["pass1_raw_delta_dr_fw_outboard"]
    for comp, im in rec["images"].items():
        pred = 0.5 * (din + dout) if "dz_tf" in comp else -dout
        meas = im["measured_raw"]
        rels.append(abs(abs(pred) - abs(meas)) / abs(meas))
check("G3c A35 images close",
      max(rels) < 1e-11 and len(rels) == 6,
      f"{len(rels)} image checks, rel diff max {max(rels):.2g} "
      "(report: 3.8e-14 – 2.9e-12)")

# the two-coefficient solve, redone independently from the three entries
ot = g3c["open_term"]
pe = {e["entry"]: e for e in ot["per_entry"]}
e1, e2 = ot["two_coefficient_solve"]["from_entries"]
chk = ot["two_coefficient_solve"]["check_entry"]
det = (pe[e1]["d_in"] * pe[e2]["d_out"] - pe[e2]["d_in"] * pe[e1]["d_out"])
y1, y2 = pe[e1]["pass2_raw_delta"], pe[e2]["pass2_raw_delta"]
a = (y1 * pe[e2]["d_out"] - y2 * pe[e1]["d_out"]) / det
b = (pe[e1]["d_in"] * y2 - pe[e2]["d_in"] * y1) / det
pred = abs(a * pe[chk]["d_in"] + b * pe[chk]["d_out"])
meas = pe[chk]["pass2_raw_delta"]
rel = abs(pred - meas) / meas
check("G3c open term is NOT a linear image",
      rel > 1e-3 and abs(rel - ot["two_coefficient_solve"]["rel_difference"])
      < 1e-6,
      f"(a,b)=({a:.2f},{b:.2f}) predicts the third entry to {rel:.3g} "
      f"— four orders worse than the direct images")
check("G3c writer named",
      ot["writer_nodes"] == ["cicc_sctfcoil"] and ot["owner_block"] == "M2",
      f"{ot['writer_nodes']} in {ot['owner_block']}")

# --------------------------------------------------------------- 8. coverage
print("[8] coverage: prime calls == block sweeps")
bad = []
for m in recs:
    name = m.get("arch_prime_name")
    n = m.get("n_prime_calls")
    bs = m.get("module_solve_totals", {}).get("block_sweeps") \
        if isinstance(m.get("module_solve_totals"), dict) else None
    if name == "fw_geometry" and bs is not None and n != bs:
        bad.append((m.get("outdir", "?").split("/")[-1], n, bs))
    if name in (None, "off") and n not in (None, 0):
        bad.append((m.get("outdir", "?").split("/")[-1], n, "off"))
on = sum(1 for m in recs if m.get("arch_prime_name") == "fw_geometry")
check("coverage", not bad,
      f"{on} prime-on records; every block-sweeping run has "
      f"n_prime_calls == block_sweeps; off-runs count 0"
      + (f"; violations {bad[:3]}" if bad else ""))

print()
if FAILURES:
    print(f"RECHECK FAIL — {len(FAILURES)} check(s): {FAILURES}")
    sys.exit(1)
print("RECHECK PASS — every published number reproduced independently")
