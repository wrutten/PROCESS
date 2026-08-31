#!/usr/bin/env python
"""A19 (frozen-input-convergence) analysis.

Reads ``runs/a19/<scenario>/<arm>/{metrics.json,probe_modules.json}`` and
produces:

* **gate N19** -- neutrality.  A19's replay mutates the data structure and
  restores it.  ``control`` and ``frozen`` must agree on the whole MFILE.
* **the method control** -- replaying the *whole* sweep sequence from the same
  entry state must reproduce the coupled-loop ``S_i`` exactly wherever they
  are not right-censored.  If it does not, nothing else here means anything.
* **the validation control** -- ``S_1`` with M1 iterated alone against the
  coupled ``S_1``, and against the coupled sequence with the one lifted
  coupler pinned.
* **the ordering hypothesis** -- per-``call_models`` distribution of
  ``S_1 <= S_2 <= S_3`` and of the gaps.
* **the gate** -- A2 section 5.1's arithmetic, recomputed with the frozen
  ``S_i``, under both weightings and both censoring treatments.

Usage:  python analyse_a19.py [--runs DIR] [--json OUT]
"""

from __future__ import annotations

import argparse
import json
import statistics as st
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent

SCENARIOS = [
    "large_tokamak_nof",
    "low_aspect_ratio_DEMO",
    "st_regression",
    "large_tokamak_eval",
]

#: Collapsed-DSM node counts (decision D8), as A2 used them.
NODE_COUNTS = {"M1": 24, "M2": 10, "M3": 12, "PULSE": 1, "FF": 5}

#: MFILE run-metadata keys excluded from the identity check, exactly as A2
#: excluded them (autonomous decision 6 of the A2 report).
SKIP = (
    "fileprefix", "process_runtime", "date", "time", "username",
    "procver", "tagno", "branch_name", "commsg",
)


def load(runs, scenario, arm, name="metrics.json"):
    p = runs / scenario / arm / name
    return json.loads(p.read_text()) if p.exists() else None


def mfile_lines(runs, scenario, arm):
    d = runs / scenario / arm
    cands = sorted(d.glob("*MFILE.DAT"))
    if not cands:
        return None
    return [
        ln for ln in cands[0].read_text().splitlines()
        if not any(f"({k})" in ln for k in SKIP)
    ]


def signature(m):
    e = m.get("exact") or {}
    return {k: e.get(k) for k in ("norm_objf", "sqsumsq", "xcs", "xcm", "rcm", "conf_l2")}


def sweep_shape(m):
    p = m.get("probe") or {}
    return {
        "sweeps_total": p.get("sweeps_total"),
        "call_models_total": p.get("call_models_total"),
        "by_phase": {k: v.get("hist") for k, v in (p.get("by_phase") or {}).items()},
        "n_retries": p.get("n_retries"),
    }


# --------------------------------------------------------------------------
# Gate N19 -- neutrality of the replay
# --------------------------------------------------------------------------


def gate_neutrality(runs, scenarios):
    out = {}
    for s in scenarios:
        c, f = load(runs, s, "control"), load(runs, s, "frozen")
        if c is None or f is None:
            out[s] = {"status": "MISSING"}
            continue
        lc, lf = mfile_lines(runs, s, "control"), mfile_lines(runs, s, "frozen")
        differing = None
        if lc is not None and lf is not None:
            differing = sum(1 for a, b in zip(lc, lf, strict=False) if a != b) + abs(len(lc) - len(lf))
        out[s] = {
            "run_status": {"control": c["status"], "frozen": f["status"]},
            "mfile_lines": len(lc) if lc else None,
            "mfile_differing": differing,
            "signature_identical": signature(c) == signature(f),
            "ifail": (f.get("mfile") or {}).get("ifail"),
            "sweep_shape_frozen": sweep_shape(f),
            "status": (
                "PASS" if differing == 0 and signature(c) == signature(f) else "FAIL"
            ),
        }
    return out


# --------------------------------------------------------------------------
# Per-call_models tables
# --------------------------------------------------------------------------


def samples(runs, scenario):
    mod = load(runs, scenario, "frozen", "probe_modules.json")
    return mod, (mod or {}).get("frozen", {}).get("samples", [])


def _stats(vals):
    vals = [v for v in vals if v is not None]
    if not vals:
        return None
    return {
        "n": len(vals),
        "mean": round(st.mean(vals), 4),
        "median": st.median(vals),
        "min": min(vals),
        "max": max(vals),
        "hist": dict(sorted(Counter(vals).items())),
    }


def method_control(S):
    """Full-sequence replay must reproduce the coupled S_i where uncensored."""
    out = {}
    for i in (1, 2, 3):
        ok = bad = 0
        examples = []
        over = []
        for s in S:
            c = s.get(f"S{i}_coupled")
            r = s.get(f"S{i}_fullreplay")
            if c is None:
                over.append(r - s["s_global"])
                continue
            if c == r:
                ok += 1
            else:
                bad += 1
                if len(examples) < 8:
                    examples.append({"call": s["call_index"], "coupled": c,
                                     "replay": r, "s_global": s["s_global"]})
        out[f"M{i}"] = {
            "uncensored_compared": ok + bad,
            "match": ok,
            "mismatch": bad,
            "mismatch_examples": examples,
            "censored": len(over),
            "censored_excess_over_s_global": dict(sorted(Counter(over).items())),
        }
    return out


def validation_control(S):
    out = {}
    for a, b in (("S1_alone", "S1_coupled"), ("S1_alone", "S1_fullreplay"),
                 ("S1_alone", "S1_liftreplay"), ("S1_alone", "S1_pulse"),
                 ("S1_alone", "S1_build"), ("S2_frozen", "S2_liftreplay"),
                 ("S3_frozen", "S3_liftreplay")):
        pairs = [(s.get(a), s.get(b)) for s in S if s.get(a) is not None and s.get(b) is not None]
        eq = sum(1 for x, y in pairs if x == y)
        out[f"{a} vs {b}"] = {
            "n": len(pairs),
            "identical": eq,
            "frac_identical": round(eq / len(pairs), 4) if pairs else None,
            "diff_hist": dict(sorted(Counter(y - x for x, y in pairs).items())),
        }
    return out


def ordering(S):
    """S1 <= S2 <= S3, per call_models, for coupled and frozen counts."""
    out = {}
    for tag, keys in (
        ("coupled_uncensored", ("S1_fullreplay", "S2_fullreplay", "S3_fullreplay")),
        ("frozen", ("S1_alone", "S2_frozen", "S3_frozen")),
        ("lifted_coupled", ("S1_liftreplay", "S2_liftreplay", "S3_liftreplay")),
    ):
        rows = [tuple(s.get(k) for k in keys) for s in S]
        rows = [r for r in rows if all(v is not None for v in r)]
        if not rows:
            continue
        n = len(rows)
        out[tag] = {
            "n": n,
            "frac_S1<=S2<=S3": round(sum(1 for a, b, c in rows if a <= b <= c) / n, 4),
            "frac_S1<=S2": round(sum(1 for a, b, _ in rows if a <= b) / n, 4),
            "frac_S2<=S3": round(sum(1 for _, b, c in rows if b <= c) / n, 4),
            "frac_all_equal": round(sum(1 for a, b, c in rows if a == b == c) / n, 4),
            "S2-S1": dict(sorted(Counter(b - a for a, b, _ in rows).items())),
            "S3-S2": dict(sorted(Counter(c - b for _, b, c in rows).items())),
            "strictly_last": dict(Counter(
                ("M1" if a > max(b, c) else "M2" if b > max(a, c) else "M3" if c > max(a, b) else "none")
                for a, b, c in rows)),
            "joint_last": {
                "M1": sum(1 for a, b, c in rows if a == max(a, b, c)),
                "M2": sum(1 for a, b, c in rows if b == max(a, b, c)),
                "M3": sum(1 for a, b, c in rows if c == max(a, b, c)),
            },
        }
    return out


# --------------------------------------------------------------------------
# The gate -- A2 section 5.1's arithmetic
# --------------------------------------------------------------------------


def cost_weights(mod):
    """Measured per-module cost share inside a sweep, as A2 computed it."""
    tot = {}
    for n in mod.get("nodes", []):
        m = n.get("module")
        if m in ("X", "?", None):
            continue
        tot[m] = tot.get(m, 0.0) + float(n.get("seconds") or 0.0)
    s = sum(tot.values())
    return {k: v / s for k, v in tot.items()} if s else None


def gate(S, weights, si_keys, censor):
    """Return (total, hoist, partition) saving as fractions of C0.

    ``si_keys`` names the three per-call_models module sweep counts to use.
    ``censor`` is 'optimistic' or 'pessimistic': a module still changing when
    its criterion was never met is charged ``S_global`` or ``S_global + 1``
    (A2's treatment) -- which for the frozen counts only ever applies if a
    sub-solve hit its ceiling.
    """
    w = weights
    w_mod = w["M1"] + w["M2"] + w["M3"]
    w_ff = w.get("PULSE", 0.0) + w.get("FF", 0.0)
    c0 = ch = cp = 0.0
    n_censored = 0
    for s in S:
        sg = s["s_global"]
        vals = []
        for k, m in zip(si_keys, ("M1", "M2", "M3"), strict=True):
            v = s.get(k)
            conv = s.get(k + "_converged")
            if v is None or conv is False:
                n_censored += 1
                v = sg if censor == "optimistic" else sg + 1
            vals.append(v)
        c0 += sg * (w_mod + w_ff)
        ch += sg * w_mod + w_ff
        cp += vals[0] * w["M1"] + vals[1] * w["M2"] + vals[2] * w["M3"] + w_ff
    return {
        "total_pct": round(100 * (c0 - cp) / c0, 2),
        "hoist_pct": round(100 * (c0 - ch) / c0, 2),
        "partition_pct": round(100 * ((c0 - cp) - (c0 - ch)) / c0, 2),
        "n_censored_substitutions": n_censored,
    }


def a2_gate_from_calls(calls, weights, censor):
    """A2's own gate, from the coupled per-call_models record, for comparison."""
    w = weights
    w_mod = w["M1"] + w["M2"] + w["M3"]
    w_ff = w.get("PULSE", 0.0) + w.get("FF", 0.0)
    c0 = ch = cp = 0.0
    for c in calls:
        sg = c["s_global"]
        vals = []
        for m in ("M1", "M2", "M3"):
            v = c.get(m)
            if v is None:
                v = sg if censor == "optimistic" else sg + 1
            vals.append(v)
        c0 += sg * (w_mod + w_ff)
        ch += sg * w_mod + w_ff
        cp += vals[0] * w["M1"] + vals[1] * w["M2"] + vals[2] * w["M3"] + w_ff
    return {
        "total_pct": round(100 * (c0 - cp) / c0, 2),
        "hoist_pct": round(100 * (c0 - ch) / c0, 2),
        "partition_pct": round(100 * ((c0 - cp) - (c0 - ch)) / c0, 2),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default=str(HERE / "runs" / "a19"))
    ap.add_argument("--json", default=None)
    ap.add_argument("--scenarios", nargs="*", default=SCENARIOS)
    args = ap.parse_args()
    runs = Path(args.runs)

    report = {"gate_neutrality": gate_neutrality(runs, args.scenarios), "scenarios": {}}

    for sc in args.scenarios:
        mod, S = samples(runs, sc)
        if not S:
            report["scenarios"][sc] = {"status": "MISSING"}
            continue
        fz = mod["frozen"]
        calls = mod["calls"]
        wc = cost_weights(mod)
        wn = {k: v / sum(NODE_COUNTS.values()) for k, v in NODE_COUNTS.items()}

        block = {
            "call_models_total": len(calls),
            "samples": len(S),
            "sampled_all_calls": len(S) == len(calls) - 1 or len(S) == len(calls),
            "phase_counts": fz["phase_counts"],
            "sequence_check": fz["sequence_check"],
            "inject_overlap": fz["inject_overlap"],
            "restore_mismatches": sum(1 for s in S if s.get("restore_mismatch")),
            "subsolve_errors": [
                e for s in S
                for e in (s.get("S1_alone_error"), s.get("S2_frozen_error"),
                          s.get("S3_frozen_error"), s.get("fullreplay_error"))
                if e
            ][:10],
            "fatal": [s["fatal"] for s in S if s.get("fatal")][:5],
            "weights_measured_cost": {k: round(v, 4) for k, v in (wc or {}).items()},
            "method_control": method_control(S),
            "validation_control": validation_control(S),
            "ordering": ordering(S),
        }

        # sweep-count summaries, overall and split by phase
        keys = ["s_global", "S1_coupled", "S2_coupled", "S3_coupled",
                "S1_fullreplay", "S2_fullreplay", "S3_fullreplay",
                "S1_liftreplay", "S2_liftreplay", "S3_liftreplay",
                "S1_alone", "S1_pulse", "S1_build", "S2_frozen", "S3_frozen",
                "S1_alone_noinject", "S2_frozen_noinject", "S3_frozen_noinject"]
        block["sweeps"] = {k: _stats([s.get(k) for s in S]) for k in keys}
        block["sweeps_by_phase"] = {
            ph: {k: _stats([s.get(k) for s in S if s["phase"] == ph]) for k in keys}
            for ph in sorted({s["phase"] for s in S})
        }

        gates = {}
        for wname, w in (("node_counts", wn), ("measured_cost", wc)):
            if w is None:
                continue
            for censor in ("optimistic", "pessimistic"):
                gates[f"frozen/{wname}/{censor}"] = gate(
                    S, w, ("S1_alone", "S2_frozen", "S3_frozen"), censor)
                gates[f"coupled_uncensored/{wname}/{censor}"] = gate(
                    S, w, ("S1_fullreplay", "S2_fullreplay", "S3_fullreplay"), censor)
                gates[f"a2_coupled/{wname}/{censor}"] = a2_gate_from_calls(
                    calls, w, censor)
        block["gates"] = gates
        report["scenarios"][sc] = block

    out = json.dumps(report, indent=2, default=str)
    if args.json:
        Path(args.json).write_text(out)
        print(f"written {args.json}")
    else:
        print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
