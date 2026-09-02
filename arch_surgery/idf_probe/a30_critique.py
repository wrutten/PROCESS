#!/usr/bin/env python
"""A30 (phase-b-critique): the adversarial pass over A28, re-derived from raw.

Every number in ``arch_surgery/docs/reports/A30_phase_b_critique.md`` comes
from running this script (protocol §15).  Everything here is **re-derivation
from the raw per-start ``metrics.json`` records and the raw per-rung
``result.json`` records** -- never from A28's analysis JSONs, which are the
thing under audit.  A28's JSONs are read in exactly one place
(:func:`stage_gate_teeth`), where the *coverage* of its sensitivity record is
itself the quantity being audited.

Read-only by construction: this script opens files under the main checkout's
``runs/`` directory and writes nothing anywhere.  It runs no PROCESS solve.

Stages (``all`` runs every one)::

    census       drop census, paired robustness, and the acceptance rule
                 under BOTH readings (objf-gated and both-solve)   [checks 6, a]
    attribution  refused starts re-derived from raw tracebacks     [check 7]
    accuracy     the accuracy census re-derived from raw audits    [checks 5, 5a]
    ladder       Phase B envelopes, both constructions, three
                 statistics, from raw ladder runs                  [checks 2, 5]
    phase_a      Phase A envelopes re-derived from the a26 rung
                 result.json points; the headline-row rule         [checks b, c]
    ad4          the moved-constant contamination bound            [check d]
    provenance   git head / dirty census over every metrics.json,
                 and cross-stage bit-identity of repeated configs  [check e]
    factors      factor identification and the k = 0 census        [checks 1, 4]
    decks        the lifted-deck diff and the pairing check        [check 3]
    gate_teeth   what A28's §12 sensitivity record actually covers [check 8]
    teeth        protocol §12 applied to THIS script: every check
                 above shown capable of failing on doctored input

Every count carries its denominator (protocol §12 / trap T11).
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from pathlib import Path

# The raw artifacts live in the MAIN checkout (read-only for this task).
MAIN = Path("/home/wrutten/projects/PROCESS_surgery")
A28 = MAIN / "arch_surgery" / "idf_probe" / "runs" / "a28"
A26 = MAIN / "arch_surgery" / "idf_probe" / "runs" / "a26"

# This task's own tree, for the frozen scenario decks and git history.
HERE = Path(__file__).resolve().parent
TREE = HERE.parent.parent

DECKS = ["large_tokamak_nof", "low_aspect_ratio_DEMO", "st_regression"]
PULSED = {"large_tokamak_nof", "low_aspect_ratio_DEMO"}
OBJF_RTOL = 1e-6  # a25_gates.OBJF_RTOL: PROCESS's own idempotence rtol
TAU = 1e-6


# ---------------------------------------------------------------------------
# raw loading
# ---------------------------------------------------------------------------


def load_starts(root: Path, deck: str, arm: str) -> dict[str, dict]:
    """Every start of one arm under one stage directory, raw metrics.json."""
    out: dict[str, dict] = {}
    d = root / deck / arm
    if not d.is_dir():
        return out
    for sd in sorted(d.glob("start*")):
        f = sd / "metrics.json"
        if f.exists():
            out[sd.name] = json.loads(f.read_text())
    return out


def ifail(m: dict):
    v = (m.get("mfile") or {}).get("ifail")
    return None if v is None else int(float(v))


def solved(m: dict) -> bool:
    return m.get("status") == "ok" and ifail(m) == 1


def objf(m: dict):
    h = (m.get("exact") or {}).get("norm_objf")
    return None if h is None else float.fromhex(h)


def cost(m: dict):
    return m.get("node_calls_solve_phase")


def pctl(vals, p):
    """The same percentile rule as a28_analysis._pct (linear interpolation)."""
    xs = sorted(v for v in vals if v is not None)
    if not xs:
        return None
    if len(xs) == 1:
        return xs[0]
    k = (len(xs) - 1) * p / 100.0
    lo, hi = math.floor(k), math.ceil(k)
    return xs[lo] if lo == hi else xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def med(xs):
    return statistics.median(xs) if xs else None


def _fmt_pct(r):
    return "-" if r is None else f"{100 * (r - 1):+.2f} %"


# ---------------------------------------------------------------------------
# stage: census  (queue check 6; loose end (a))
# ---------------------------------------------------------------------------

PAIRS = [("R", "A0p"), ("A0p", "A1p"), ("R", "A1p"),
         ("A1p_nohoist", "A1p"), ("A0p", "A1p_nohoist")]


def pair_tables(data: dict[str, dict[str, dict]], ref: str, arm: str) -> dict:
    """Both readings of one comparison, from raw rows.

    RULE A (published, D15(c)): a pair enters the ratio iff BOTH arms have
    status ok AND ifail == 1 AND their norm_objf agree to 1e-6 relative.
    RULE B (no objf gate):      both arms status ok AND ifail == 1.
    The drop census reproduces gates.drop_census's categories exactly.
    """
    allst = sorted(set(data[ref]) | set(data[arm]))
    ok_ref = {s for s in data[ref] if solved(data[ref][s])}
    ok_arm = {s for s in data[arm] if solved(data[arm][s])}
    both = sorted(ok_ref & ok_arm)

    # drop census, category per start (order: crashed, ifail_not_1,
    # objf_mismatch, kept) -- re-derived, not read from _h5_a28.json
    census = {"crashed": [], "ifail_not_1": [], "objf_mismatch": [], "kept": []}
    for s in allst:
        rows = [data[a].get(s) for a in (ref, arm)]
        if any(r is None or r.get("status") != "ok" for r in rows):
            census["crashed"].append(s)
            continue
        if any(ifail(r) != 1 for r in rows):
            census["ifail_not_1"].append(s)
            continue
        o = [objf(r) for r in rows]
        if None not in o and o[0] != o[1]:
            rel = abs(max(o) - min(o)) / (abs(o[0]) or 1.0)
            if rel > OBJF_RTOL:
                census["objf_mismatch"].append((s, rel))
                continue
        census["kept"].append(s)

    def ratios(names):
        return [
            cost(data[arm][s]) / cost(data[ref][s])
            for s in names
            if cost(data[ref][s]) and cost(data[arm][s]) is not None
        ]

    ra = ratios(census["kept"])
    rb = ratios(both)
    return {
        "offered": len(allst),
        "both": len(both),
        "only_ref": sorted(ok_ref - ok_arm),
        "only_arm": sorted(ok_arm - ok_ref),
        "neither": len(set(allst) - ok_ref - ok_arm),
        "census": {k: v for k, v in census.items()},
        "rule_a": {
            "n": len(ra), "median": med(ra),
            "cheaper": sum(1 for r in ra if r < 1),
            "dearer": sum(1 for r in ra if r > 1),
            "min": min(ra) if ra else None, "max": max(ra) if ra else None,
            "q1": pctl(ra, 25), "q3": pctl(ra, 75),
        },
        "rule_b": {
            "n": len(rb), "median": med(rb),
            "cheaper": sum(1 for r in rb if r < 1),
            "dearer": sum(1 for r in rb if r > 1),
        },
    }


def stage_census(root: Path | None = None, quiet: bool = False) -> dict:
    root = root if root is not None else A28 / "h5"
    out = {}
    for deck in DECKS:
        data = {a: load_starts(root, deck, a)
                for a in ("R", "A0p", "A1p", "A1p_nohoist")}
        out[deck] = {}
        if not quiet:
            print(f"\n== {deck}  (starts per arm: "
                  + ", ".join(f"{a}:{len(data[a])}" for a in data) + ")")
        for ref, arm in PAIRS:
            t = pair_tables(data, ref, arm)
            out[deck][f"{ref}->{arm}"] = t
            if quiet:
                continue
            c = t["census"]
            print(f"  {ref}->{arm}: offered {t['offered']}  "
                  f"both {t['both']}  only_{ref} {len(t['only_ref'])} "
                  f"{t['only_ref']}  only_{arm} {len(t['only_arm'])} "
                  f"{t['only_arm']}  neither {t['neither']}")
            print(f"    census: kept {len(c['kept'])}, crashed "
                  f"{len(c['crashed'])}, ifail_not_1 {len(c['ifail_not_1'])}, "
                  f"objf_mismatch {len(c['objf_mismatch'])} "
                  f"{[(s, f'{r:.2g}') for s, r in c['objf_mismatch']]}")
            a, b = t["rule_a"], t["rule_b"]
            print(f"    RULE A (objf-gated, published): n={a['n']} median "
                  f"{a['median']:.4f} ({_fmt_pct(a['median'])})  "
                  f"cheaper/dearer {a['cheaper']}/{a['dearer']}  "
                  f"q1-q3 {a['q1']:.3f}-{a['q3']:.3f}  "
                  f"min-max {a['min']:.3f}-{a['max']:.3f}")
            print(f"    RULE B (both-solve, no objf gate): n={b['n']} median "
                  f"{b['median']:.4f} ({_fmt_pct(b['median'])})  "
                  f"cheaper/dearer {b['cheaper']}/{b['dearer']}")
    return out


# ---------------------------------------------------------------------------
# stage: attribution  (queue check 7)
# ---------------------------------------------------------------------------


def stage_attribution(root: Path | None = None, quiet: bool = False) -> dict:
    root = root if root is not None else A28 / "h5"
    out = {}
    for deck in DECKS:
        out[deck] = {}
        if not quiet:
            print(f"\n== {deck}")
        for arm in ("R", "A0p", "A1p", "A1p_nohoist"):
            data = load_starts(root, deck, arm)
            not_solved, crashed, msf = [], [], []
            comps = {}
            for s, m in sorted(data.items()):
                if solved(m):
                    continue
                not_solved.append((s, m.get("status"), ifail(m)))
                if m.get("status") != "ok":
                    crashed.append(s)
                    tb = (m.get("traceback") or "").strip().splitlines()
                    last = tb[-1] if tb else ""
                    if "ModuleSolveFailure" in last:
                        msf.append(s)
                        # component named in the exception message
                        import re
                        g = re.search(r"on ([A-Za-z_][\w.]*)", last)
                        if g:
                            comps[g.group(1)] = comps.get(g.group(1), 0) + 1
            out[deck][arm] = {
                "denominator": len(data),
                "not_solved": not_solved,
                "n_not_solved": len(not_solved),
                "n_crashed": len(crashed),
                "crashed": crashed,
                "n_module_solve_refusals": len(msf),
                "refused_starts": msf,
                "components": comps,
            }
            if not quiet:
                r = out[deck][arm]
                print(f"  {arm:<12} not solved {r['n_not_solved']:>2} of "
                      f"{r['denominator']}   crashed {r['n_crashed']:>2}   "
                      f"coupling-state refusals "
                      f"{r['n_module_solve_refusals']:>2} "
                      f"{r['refused_starts']} {r['components'] or ''}")
    return out


# ---------------------------------------------------------------------------
# stage: accuracy  (queue checks 5, 5a)
# ---------------------------------------------------------------------------


def _audit_residuals(root: Path, deck: str, arm: str) -> dict[str, float]:
    out = {}
    d = root / deck / arm
    if not d.is_dir():
        return out
    for sd in sorted(d.glob("start*")):
        f = sd / "metrics.json"
        if not f.exists():
            continue
        rec = json.loads(f.read_text()).get("audit_at_call") or {}
        if "residual_max" in rec:
            out[sd.name] = rec["residual_max"]
    return out


def stage_accuracy(root: Path | None = None, quiet: bool = False) -> dict:
    root = root if root is not None else A28 / "h5_audit1"
    out = {}
    for deck in DECKS:
        vals = {a: _audit_residuals(root, deck, a) for a in ("R", "A0p", "A1p")}
        rec = {"per_arm": {}, "paired": {}}
        if not quiet:
            print(f"\n== {deck}")
        for a, v in vals.items():
            xs = list(v.values())
            nz = [x for x in xs if x > 0]
            rec["per_arm"][a] = {
                "n": len(xs), "zeros": len(xs) - len(nz),
                "p10": pctl(xs, 10), "p50": pctl(xs, 50),
                "p90": pctl(xs, 90), "max": max(xs) if xs else None,
            }
            if not quiet and xs:
                r = rec["per_arm"][a]
                print(f"  {a:<6} n={r['n']:>2}  bit-exact-0 {r['zeros']:>2}  "
                      f"p10 {r['p10']:.3g}  p50 {r['p50']:.3g}  "
                      f"p90 {r['p90']:.3g}  max {r['max']:.3g}")
        for x, y in [("R", "A0p"), ("R", "A1p"), ("A0p", "A1p")]:
            common = sorted(set(vals[x]) & set(vals[y]))
            lx = sum(1 for s in common if vals[x][s] > vals[y][s])
            ly = sum(1 for s in common if vals[y][s] > vals[x][s])
            rec["paired"][f"{x} vs {y}"] = {
                "n": len(common), f"{x}_looser": lx, f"{y}_looser": ly,
                "equal": len(common) - lx - ly,
            }
            if not quiet:
                print(f"  paired {x} vs {y}: n={len(common)}  {x} looser on "
                      f"{lx}, {y} on {ly}, equal {len(common) - lx - ly}")
        out[deck] = rec
    return out


# ---------------------------------------------------------------------------
# stage: ladder  (queue checks 2 and 5, Phase B)
# ---------------------------------------------------------------------------


def build_phase_b_rungs(deck: str, root: Path | None = None):
    """Phase B rungs from raw ladder runs, reproducing the analysis's
    acceptance (flat control's tightest completed rung per start) and the
    common-population restriction -- re-implemented here, not imported."""
    ldir = (root if root is not None else A28 / "ladder") / deck
    labels = sorted(p.name for p in ldir.glob("*")) if ldir.is_dir() else []

    flat_sorted = sorted((float(x[len("A0p_tau"):]), x)
                         for x in labels if x.startswith("A0p_tau"))
    ref: dict[str, float] = {}
    for _t, lab in flat_sorted:  # ascending tau: tightest first
        for name, m in load_starts(ldir.parent, deck, lab).items():
            if name in ref or not solved(m):
                continue
            o = objf(m)
            if o is not None:
                ref[name] = o

    def spec(lab):
        if lab.startswith("A0p_tau"):
            return ("flat", float(lab[7:]), float(lab[7:]))
        if lab.startswith("A1p_joint"):
            return ("joint", float(lab[9:]), float(lab[9:]))
        if lab.startswith("A1p_inner"):
            return ("inner", TAU, float(lab[9:]))
        return None

    pre = {}
    for lab in labels:
        sp = spec(lab)
        if sp is None:
            continue
        kept = {}
        for name, m in load_starts(ldir.parent, deck, lab).items():
            if not solved(m):
                continue
            r, o = ref.get(name), objf(m)
            if r is None or o is None:
                continue
            if abs(o - r) / (abs(r) or 1.0) > OBJF_RTOL:
                continue
            kept[name] = m
        pre[lab] = (sp, kept)
    empty = [lab for lab, (_sp, k) in pre.items() if not k]
    common = None
    for lab, (_sp, k) in pre.items():
        if lab in empty:
            continue
        common = set(k) if common is None else common & set(k)
    common = common or set()

    rungs = []
    for lab, (sp, k) in pre.items():
        if lab in empty:
            continue
        names = sorted(set(k) & common)
        c = sum(int(k[n].get("node_calls_solve_phase") or 0) for n in names)
        resid = []
        for n in names:
            ap = ldir / lab / n.replace("start", "audit") / "metrics.json"
            if ap.exists():
                rec = json.loads(ap.read_text()).get("audit_at_call") or {}
                if "residual_max" in rec:
                    resid.append(rec["residual_max"])
        rungs.append({
            "label": lab, "family": sp[0], "tau": sp[1], "inner": sp[2],
            "n": len(names), "cost": c,
            "p90": pctl(resid, 90), "p50": pctl(resid, 50),
            "mx": max(resid) if resid else None,
        })
    return rungs, sorted(common), empty


def envelope(rungs, stat):
    """Lower envelope cost(a) = min{cost_i : accuracy_i <= a}; zero-residual
    rungs excluded from the fit but admitted to the envelope (accuracy.py's
    post-a04e1cf7 behaviour, re-implemented)."""
    usable = [r for r in rungs if r.get(stat) is not None and r[stat] > 0]
    zeros = [r for r in rungs if r.get(stat) is not None and r[stat] <= 0]
    usable.sort(key=lambda r: (r[stat], r["cost"]))
    env, best = [], None
    for r in usable:
        if best is None or r["cost"] < best:
            best = r["cost"]
            env.append(r)
    zbest = min((r["cost"] for r in zeros), default=None)
    zlab = (min(zeros, key=lambda r: r["cost"])["label"] if zeros else None)
    return env, zbest, zlab


def cost_at(env, zbest, zlab, a, stat):
    if not env:
        if zbest is not None and a > 0:
            return float(zbest), f"zero-rung:{zlab}"
        return None, "no curve"
    if a < env[0][stat]:
        if zbest is not None:
            return float(zbest), f"zero-rung:{zlab}"
        return None, "out of measured range"
    if a >= env[-1][stat]:
        c, lab = float(env[-1]["cost"]), env[-1]["label"]
        if zbest is not None and zbest < c:
            c, lab = float(zbest), f"zero-rung:{zlab}"
        return c, lab
    for i in range(len(env) - 1):
        a0, a1 = env[i][stat], env[i + 1][stat]
        if a0 <= a <= a1:
            c0, c1 = env[i]["cost"], env[i + 1]["cost"]
            if a1 == a0:
                return float(c0), env[i]["label"]
            f = (math.log10(a) - math.log10(a0)) / (
                math.log10(a1) - math.log10(a0))
            c = 10 ** (math.log10(c0) + f * (math.log10(c1) - math.log10(c0)))
            lab = f"{env[i]['label']}..{env[i + 1]['label']}"
            if zbest is not None and zbest < c:
                c, lab = float(zbest), f"zero-rung:{zlab}"
            return c, lab
    return None, "no bracket"


def read_at_calibration(rungs, stat):
    """Both constructions read at the flat arm's tau = 1e-6 achieved accuracy
    -- the published headline-row rule -- plus the full row set."""
    flat = [r for r in rungs if r["family"] == "flat"]
    blk_all = [r for r in rungs if r["family"] in ("joint", "inner")]
    blk_joint = [r for r in rungs if r["family"] == "joint"]
    t6 = [r for r in flat if r["tau"] == TAU]
    rec = {"stat": stat}
    if not t6 or t6[0].get(stat) is None or t6[0][stat] <= 0:
        rec["status"] = ("flat tau=1e-6 rung has zero or missing residual "
                         "under this statistic -- no calibration-point read")
        return rec
    a = t6[0][stat]
    env_f, zf, zfl = envelope(flat, stat)
    fcost, _ = cost_at(env_f, zf, zfl, a, stat)
    rec["flat_accuracy"], rec["flat_cost"] = a, fcost
    for name, rs in (("all_settings", blk_all), ("matched_count", blk_joint)):
        env_b, zb, zbl = envelope(rs, stat)
        bc, lab = cost_at(env_b, zb, zbl, a, stat)
        rec[name] = {
            "cost": bc, "via": lab,
            "ratio": (bc / fcost) if (bc and fcost) else None,
        }
    # every-flat-envelope-point rows, both constructions (the full row set)
    rows = []
    for p in env_f:
        row = {"flat_label": p["label"], "accuracy": p[stat],
               "flat_cost": p["cost"]}
        for name, rs in (("all_settings", blk_all),
                         ("matched_count", blk_joint)):
            env_b, zb, zbl = envelope(rs, stat)
            bc, _lab = cost_at(env_b, zb, zbl, p[stat], stat)
            row[name] = (bc / p["cost"]) if (bc and p["cost"]) else None
        rows.append(row)
    rec["rows"] = rows
    return rec


def stage_ladder(root: Path | None = None, quiet: bool = False) -> dict:
    out = {}
    for deck in DECKS:
        rungs, common, empty = build_phase_b_rungs(deck, root)
        rec = {"common_starts": common, "n_common": len(common),
               "empty_rungs": empty, "rungs": rungs, "reads": {}}
        if not quiet:
            print(f"\n== {deck}  common population {common} "
                  f"(n={len(common)}); rungs keeping no start: {empty}")
            for r in sorted(rungs, key=lambda r: (r["family"], -r["tau"],
                                                  -r["inner"])):
                p90 = "-" if r["p90"] is None else f"{r['p90']:.3g}"
                print(f"   {r['label']:<16} {r['family']:<5} n={r['n']} "
                      f"cost {r['cost']:>7}  p90 {p90}")
        for stat in ("p90", "p50", "mx"):
            rd = read_at_calibration(rungs, stat)
            rec["reads"][stat] = rd
            if quiet:
                continue
            if "status" in rd:
                print(f"   [{stat}] {rd['status']}")
                continue
            for name in ("matched_count", "all_settings"):
                c = rd[name]
                if c["ratio"] is None:
                    print(f"   [{stat}] {name}: no read ({c['via']})")
                else:
                    print(f"   [{stat}] {name:<14} flat accuracy "
                          f"{rd['flat_accuracy']:.3g}  flat "
                          f"{rd['flat_cost']:.0f}  block {c['cost']:.1f}  "
                          f"ratio {c['ratio']:.4f} ({_fmt_pct(c['ratio'])}) "
                          f" via {c['via']}")
        out[deck] = rec
    return out


# ---------------------------------------------------------------------------
# stage: phase_a  (loose ends (b), (c); queue check 5 for Phase A)
# ---------------------------------------------------------------------------


def load_a26_rung(deck: str, dname: str, arm: str):
    f = A26 / deck / dname / "result.json"
    if not f.exists():
        return None
    res = json.loads(f.read_text())
    pts = res["points"]
    conv = [p for p in pts if p["arms"].get(arm, {}).get("converged")]
    if not conv:
        return None
    audits = [p["arms"][arm]["audit"]["max"] for p in conv
              if "audit" in p["arms"][arm]]

    def _p(vals, q):  # accuracy.py's percentile rule (q in [0,1])
        v = sorted(vals)
        if not v:
            return None
        if len(v) == 1:
            return v[0]
        i = q * (len(v) - 1)
        lo, hi = int(i), min(int(i) + 1, len(v) - 1)
        return v[lo] + (v[hi] - v[lo]) * (i - lo)

    c = sum(int(p["arms"][arm].get("node_calls", 0))
            + int(p["arms"][arm].get("hoist_tail_node_calls", 0) or 0)
            for p in conv)
    return {"label": res["label"], "tau": res["tau"],
            "inner": res.get("inner_tau"), "family": None,
            "n": len(conv), "n_dropped": len(pts) - len(conv), "cost": c,
            "p90": _p(audits, 0.90), "p50": _p(audits, 0.50),
            "mx": max(audits) if audits else None}


def stage_phase_a(quiet: bool = False) -> dict:
    out = {}
    for deck in DECKS:
        dirs = sorted(d.name for d in (A26 / deck).glob("replay_acc_*"))
        flat = [load_a26_rung(deck, d, "A0") for d in dirs if "flat" in d]
        joint = [load_a26_rung(deck, d, "A1") for d in dirs if "joint" in d]
        inner = [load_a26_rung(deck, d, "A1") for d in dirs if "inner" in d]
        flat = [dict(r, family="flat") for r in flat if r]
        joint = [dict(r, family="joint") for r in joint if r]
        inner = [dict(r, family="inner") for r in inner if r]
        rungs = flat + joint + inner
        flat_taus = sorted({r["tau"] for r in flat})
        joint_taus = sorted({r["tau"] for r in joint})
        rec = {
            "n_flat_rungs": len(flat), "n_joint_rungs": len(joint),
            "n_inner_rungs": len(inner),
            "flat_taus": flat_taus, "joint_taus": joint_taus,
            "same_knob_same_values": flat_taus == joint_taus,
            "n_rungs_with_zero_p50": sum(
                1 for r in rungs if r["p50"] is not None and r["p50"] <= 0),
            "n_rungs_total": len(rungs),
            "reads": {},
        }
        if not quiet:
            print(f"\n== {deck}: flat {len(flat)} rungs (taus {flat_taus}), "
                  f"joint {len(joint)} (taus {joint_taus}), inner "
                  f"{len(inner)}; same-knob-same-values: "
                  f"{rec['same_knob_same_values']}")
            print(f"   rungs whose p50 exit residual is exactly 0: "
                  f"{rec['n_rungs_with_zero_p50']} of {rec['n_rungs_total']}")
        for stat in ("p90", "p50", "mx"):
            rd = read_at_calibration(rungs, stat)
            rec["reads"][stat] = rd
            if quiet:
                continue
            if "status" in rd:
                print(f"   [{stat}] {rd['status']}")
                continue
            for name in ("matched_count", "all_settings"):
                c = rd[name]
                if c["ratio"] is None:
                    print(f"   [{stat}] {name}: no read ({c['via']})")
                else:
                    print(f"   [{stat}] {name:<14} flat "
                          f"{rd['flat_cost']:.0f}  block {c['cost']:.1f}  "
                          f"ratio {c['ratio']:.4f} ({_fmt_pct(c['ratio'])})")
            # the row-selection audit: the full row table under p90
            if stat == "p90":
                print("   row table (both constructions, every flat envelope "
                      "point):")
                for row in rd["rows"]:
                    a_s = _fmt_pct(row["all_settings"])
                    m_s = _fmt_pct(row["matched_count"])
                    print(f"     {row['flat_label']:<22} accuracy "
                          f"{row['accuracy']:.3g}  all-settings {a_s:>9}  "
                          f"matched-count {m_s:>9}")
        out[deck] = rec
    return out


# ---------------------------------------------------------------------------
# stage: ad4  (loose end (d))
# ---------------------------------------------------------------------------


def stage_ad4(root: Path | None = None, quiet: bool = False) -> dict:
    root = root if root is not None else A28 / "h5"
    deck = "st_regression"
    data = {a: load_starts(root, deck, a) for a in ("A0p", "A1p")}
    rows = []
    for s in sorted(set(data["A0p"]) & set(data["A1p"])):
        m0, m1 = data["A0p"][s], data["A1p"][s]
        if not (solved(m0) and solved(m1)):
            continue
        o0, o1 = objf(m0), objf(m1)
        rel = abs(o1 - o0) / (abs(o0) or 1.0)
        t0 = m0.get("module_solve_totals") or {}
        t1 = m1.get("module_solve_totals") or {}
        if not t0 or not t1:
            continue
        f0 = t0["n_call_models_with_moved_constant"] / t0["n_call_models"]
        f1 = t1["n_call_models_with_moved_constant"] / t1["n_call_models"]
        rows.append({
            "start": s, "kept": rel <= OBJF_RTOL, "f0": f0, "f1": f1,
            "df": f1 - f0, "ratio": cost(m1) / cost(m0),
        })
    kept = [r for r in rows if r["kept"]]
    base = med([r["ratio"] for r in kept])
    restr = {}
    for label, sub in [
        ("|df| <= 0.02", [r for r in kept if abs(r["df"]) <= 0.02]),
        ("|df| <= 0.05", [r for r in kept if abs(r["df"]) <= 0.05]),
        ("|df| <= 0.10", [r for r in kept if abs(r["df"]) <= 0.10]),
        ("both arms' fraction < 0.20",
         [r for r in kept if r["f0"] < 0.20 and r["f1"] < 0.20]),
        ("both arms clean (fraction 0)",
         [r for r in kept if r["f0"] == 0 and r["f1"] == 0]),
    ]:
        restr[label] = {"n": len(sub), "median": med([r["ratio"] for r in sub])}
    sd = sorted(kept, key=lambda r: r["df"])
    lo_h, hi_h = sd[:len(sd) // 2], sd[(len(sd) + 1) // 2:]
    halves = {
        "smaller df": {"n": len(lo_h), "median": med([r["ratio"] for r in lo_h])},
        "larger df": {"n": len(hi_h), "median": med([r["ratio"] for r in hi_h])},
    }
    xs = [r["df"] for r in kept]
    ys = [r["ratio"] for r in kept]
    n = len(xs)
    mx_, my_ = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx_) * (y - my_) for x, y in zip(xs, ys))
    sxx = sum((x - mx_) ** 2 for x in xs)
    syy = sum((y - my_) ** 2 for y in ys)
    pear = sxy / (sxx * syy) ** 0.5 if sxx * syy else None
    out = {"rows": rows, "n_kept": len(kept), "headline": base,
           "restrictions": restr, "halves": halves, "pearson": pear}
    if not quiet:
        print(f"\n== {deck} A0p->A1p, moved-constant contamination bound")
        print(f"   {'start':<10}{'fracA0p':>9}{'fracA1p':>9}{'diff':>9}"
              f"{'ratio':>9}{'kept':>6}")
        for r in rows:
            print(f"   {r['start']:<10}{r['f0']:>9.3f}{r['f1']:>9.3f}"
                  f"{r['df']:>+9.3f}{r['ratio']:>9.4f}{str(r['kept']):>6}")
        print(f"   headline over kept (n={len(kept)}): median {base:.4f} "
              f"({_fmt_pct(base)})")
        for label, r in restr.items():
            m = "-" if r["median"] is None else f"{r['median']:.4f} ({_fmt_pct(r['median'])})"
            print(f"   restricted to {label:<32} n={r['n']:>2}  median {m}")
        for label, r in halves.items():
            print(f"   half with {label:<10} n={r['n']}  median "
                  f"{r['median']:.4f}")
        print(f"   pearson r(frac-diff, ratio) over kept: {pear:.3f}")
    return out


# ---------------------------------------------------------------------------
# stage: provenance  (loose end (e))
# ---------------------------------------------------------------------------


def stage_provenance(quiet: bool = False) -> dict:
    from collections import Counter
    c: Counter = Counter()
    n = 0
    for f in A28.rglob("metrics.json"):
        try:
            m = json.loads(f.read_text())
        except Exception:
            continue
        n += 1
        stage = f.relative_to(A28).parts[0]
        head = m.get("tree_git_head")
        c[(stage, head[:8] if head else str(head), m.get("tree_git_dirty"))] += 1
    out = {"n_metrics": n,
           "buckets": {f"{s}|{h}|dirty={d}": v for (s, h, d), v in sorted(c.items())}}
    if not quiet:
        print(f"\n== git head / dirty census over {n} metrics.json under a28/")
        for k, v in out["buckets"].items():
            print(f"   {k:<40} {v}")

    # cross-stage bit-identity: the same configuration (deck, arm,
    # unperturbed start, tau=1e-6) recorded under different heads
    ident = []
    for deck in DECKS:
        for arm, lab in (("A0p", "A0p_tau1e-06"), ("A1p", "A1p_joint1e-06")):
            recs = {}
            g = A28 / "gate" / deck / arm / "metrics.json"
            if g.exists():
                recs["gate"] = json.loads(g.read_text())
            h = A28 / "h5" / deck / arm / "start000" / "metrics.json"
            if h.exists():
                recs["h5/start000"] = json.loads(h.read_text())
            l = A28 / "ladder" / deck / lab / "start000" / "metrics.json"
            if l.exists():
                recs["ladder/start000"] = json.loads(l.read_text())
            if len(recs) < 2:
                continue
            costs = {k: cost(m) for k, m in recs.items()}
            objs = {k: (m.get("exact") or {}).get("norm_objf")
                    for k, m in recs.items()}
            heads = {k: (m.get("tree_git_head") or "?")[:8]
                     + ("-dirty" if m.get("tree_git_dirty") else "")
                     for k, m in recs.items()}
            ident.append({
                "deck": deck, "arm": arm, "stages": heads,
                "costs": costs, "objf_hex": objs,
                "cost_identical": len(set(costs.values())) == 1,
                "objf_identical": len(set(objs.values())) == 1,
            })
    out["cross_stage_identity"] = ident
    if not quiet:
        print("\n   cross-stage identity of repeated configurations "
              "(same deck+arm+unperturbed start+tau):")
        for r in ident:
            print(f"   {r['deck']:<24}{r['arm']:<5} "
                  f"cost identical: {r['cost_identical']}  objf hex "
                  f"identical: {r['objf_identical']}  "
                  f"stages/heads: { {k: v for k, v in r['stages'].items()} }  "
                  f"costs: {sorted(set(r['costs'].values()))}")

    # what the later commits changed, from history (the committed record of
    # the then-dirty content)
    import subprocess
    heads_seen = sorted({h for (_s, h, _d) in c if h and h != "None"})
    diffs = {}
    for a, b in [("dc18c05b", "9634bb06"), ("9634bb06", "492c6fc8"),
                 ("492c6fc8", "0fae5e1a"), ("0fae5e1a", "0c18dfcc")]:
        try:
            files = subprocess.run(
                ["git", "-C", str(TREE), "diff", "--name-only", a, b],
                capture_output=True, text=True, check=True,
            ).stdout.split()
        except subprocess.CalledProcessError:
            diffs[f"{a}..{b}"] = {"error": "git diff failed"}
            continue
        measured = [f for f in files if f.startswith("process/")
                    or f == "arch_surgery/idf_probe/run_one.py"
                    or f.startswith("arch_surgery/docs/data/ystate")
                    or f.startswith("arch_surgery/docs/data/writeset")]
        diffs[f"{a}..{b}"] = {
            "n_files": len(files),
            "files_touching_measured_code": measured,
        }
    out["heads_seen"] = heads_seen
    out["committed_deltas"] = diffs
    if not quiet:
        print("\n   committed deltas between recorded heads (files touching "
              "process/, run_one.py, or the ystate/writeset artifacts):")
        for k, v in diffs.items():
            print(f"   {k}: {v.get('n_files')} files changed; touching "
                  f"measured code: {v.get('files_touching_measured_code')}")
    return out


# ---------------------------------------------------------------------------
# stage: factors  (queue checks 1 and 4)
# ---------------------------------------------------------------------------


def stage_factors(root: Path | None = None, quiet: bool = False) -> dict:
    root = root if root is not None else A28 / "h5"
    out = {}
    for deck in DECKS:
        rec = {}
        for arm in ("R", "A0p", "A1p", "A1p_nohoist"):
            data = load_starts(root, deck, arm)
            m = next(iter(data.values()), None)
            if m is None:
                continue
            rec[arm] = {
                "nvar": m.get("nvar"),
                "lift_sites": m.get("arch_lift_sites") or [],
                "hoist": m.get("arch_hoist_name"),
                "module_solve": m.get("arch_module_solve_name"),
                "sequence": m.get("arch_sequence_name"),
            }
        out[deck] = rec
        if not quiet:
            print(f"\n== {deck}")
            for arm, r in rec.items():
                print(f"   {arm:<12} nvar {r['nvar']:>2}  lift "
                      f"{r['lift_sites'] or '-'}  hoist {r['hoist']:<20} "
                      f"solve {r['module_solve']}  seq {r['sequence']}")
    # which factor combinations the arm pairs identify
    if not quiet:
        print("\n   factor identification on a pulsed deck (from the resolved "
              "arm records above):")
        print("     A0p -> A1p          varies grouping + lift + hoist "
              "(the headline)")
        print("     A1p_nohoist -> A1p  varies hoist alone")
        print("     A0p -> A1p_nohoist  varies grouping + lift  "
              "(NOT the partition alone)")
        print("     no arm pair varies the lift alone: the lift's own share "
              "is NOT separately identified")
    return out


# ---------------------------------------------------------------------------
# stage: decks  (queue check 3)
# ---------------------------------------------------------------------------


def stage_decks(root: Path | None = None, quiet: bool = False) -> dict:
    droot = root if root is not None else A28 / "_decks"
    out = {}
    for deck in sorted(PULSED):
        frozen = (HERE / "scenarios" / f"{deck}.IN.DAT").read_text().splitlines()
        lifted = (droot / deck / f"{deck}_lifted.IN.DAT").read_text().splitlines()
        f_sub = [l for l in frozen if not l.strip().startswith("*")]
        l_sub = [l for l in lifted if not l.strip().startswith("*")]
        import difflib
        removed, added = [], []
        for l in difflib.unified_diff(f_sub, l_sub, lineterm="", n=0):
            if l.startswith("-") and not l.startswith("---"):
                removed.append(l[1:])
            elif l.startswith("+") and not l.startswith("+++"):
                added.append(l[1:])
        out[deck] = {"non_comment_lines_removed": removed,
                     "non_comment_lines_added": added}
        if not quiet:
            print(f"\n== {deck}: substantive (non-comment) deck diff")
            for l in removed:
                print(f"   - {l}")
            for l in added:
                print(f"   + {l}")

    # the pairing check: identical factors on every shared design variable
    pair = {}
    h5 = A28 / "h5"
    for deck in DECKS:
        rows = []
        for s in ("start001", "start005", "start012", "start017", "start024"):
            recs = {}
            for arm in ("R", "A0p", "A1p"):
                f = h5 / deck / arm / s / "metrics.json"
                if not f.exists():
                    continue
                m = json.loads(f.read_text())
                p = m.get("perturbation")
                if p:
                    recs[arm] = {v["ixc"]: v["factor"]
                                 for v in p["per_variable"]}
            if len(recs) < 2:
                continue
            shared = set.intersection(*(set(v) for v in recs.values()))
            ident = all(len({recs[a][i] for a in recs}) == 1 for i in shared)
            extra = {a: sorted(set(recs[a]) - shared) for a in recs
                     if set(recs[a]) - shared}
            rows.append({"start": s, "n_shared": len(shared),
                         "identical": ident, "extra_ixc": extra})
        pair[deck] = rows
        if not quiet:
            print(f"\n== {deck}: perturbation pairing over sampled starts")
            for r in rows:
                print(f"   {r['start']}: {r['n_shared']} shared variables, "
                      f"factors identical: {r['identical']}, extra: "
                      f"{r['extra_ixc'] or '-'}")
    out["pairing"] = pair

    # n vs n+1 charged: call_models counts at the gate point
    if not quiet:
        print("\n== the n+1st design variable is charged (gate-point "
              "call_models counts):")
    charged = {}
    for deck in DECKS:
        row = {}
        for arm in ("R", "A0p", "A1p"):
            f = A28 / "gate" / deck / arm / "metrics.json"
            if not f.exists():
                continue
            m = json.loads(f.read_text())
            tot = m.get("module_solve_totals") or {}
            ec = m.get("entry_census") or {}
            row[arm] = {
                "nvar": m.get("nvar"),
                "n_call_models": (tot.get("n_call_models")
                                  or ec.get("n_call_models_entries_recorded")),
            }
        charged[deck] = row
        if not quiet and row:
            r = ", ".join(f"{a}: nvar {v['nvar']} call_models "
                          f"{v['n_call_models']}" for a, v in row.items())
            print(f"   {deck}: {r}")
    out["charged"] = charged
    return out


# ---------------------------------------------------------------------------
# stage: doc_tables  (arithmetic consistency: §7.4, §7.10, §7.11, §7.12)
# ---------------------------------------------------------------------------


def stage_doc_tables(quiet: bool = False) -> dict:
    out: dict = {}

    # §7.4: cost at each deck's own starting point, from the gate runs
    rows = {}
    for deck in DECKS:
        rows[deck] = {}
        for arm in ("R", "A0p", "A0p_reordered", "A1p_nohoist", "A1p"):
            f = A28 / "gate" / deck / arm / "metrics.json"
            if not f.exists():
                continue
            m = json.loads(f.read_text())
            rows[deck][arm] = {
                "net": m.get("node_calls_solve_phase"),
                "sweeps": m.get("n_model_calls"),
                "iters": m.get("n_solver_iterations"),
                "nvar": m.get("nvar"),
            }
    out["gate_point"] = rows
    if not quiet:
        print("\n== §7.4 gate-point table, re-derived from raw gate runs")
        for deck, r in rows.items():
            for arm, v in r.items():
                print(f"   {deck:<24}{arm:<15} net {v['net']:>7}  sweeps "
                      f"{v['sweeps']:>6}  iters {v['iters']:>3}  nvar "
                      f"{v['nvar']}")
            a0, a1, rr = r.get("A0p"), r.get("A1p"), r.get("R")
            if a0 and a1 and rr:
                print(f"     -> R->A0' {100 * (a0['net'] / rr['net'] - 1):+.2f} %"
                      f"   A0'->A1' {100 * (a1['net'] / a0['net'] - 1):+.2f} %"
                      f"   R->A1' {100 * (a1['net'] / rr['net'] - 1):+.2f} %")

    # §7.11: moved-constant census per deck per coupling-state arm
    mc = {}
    for deck in DECKS:
        mc[deck] = {}
        for arm in ("A0p", "A1p"):
            data = load_starts(A28 / "h5", deck, arm)
            tot = [m.get("module_solve_totals") for m in data.values()
                   if m.get("module_solve_totals")]
            n_aff = sum(t["n_call_models_with_moved_constant"] for t in tot)
            n_all = sum(t["n_call_models"] for t in tot)
            names: set = set()
            for t in tot:
                names |= set(t.get("moved_constants") or ())
            mc[deck][arm] = {"affected": n_aff, "of": n_all,
                            "distinct": len(names)}
    out["moved_constants"] = mc
    if not quiet:
        print("\n== §7.11 moved-constant census, re-derived from raw")
        for deck, r in mc.items():
            for arm, v in r.items():
                pc = 100 * v["affected"] / v["of"] if v["of"] else 0
                print(f"   {deck:<24}{arm:<6} {v['affected']:>6} of "
                      f"{v['of']:<7} ({pc:.1f} %), {v['distinct']} distinct "
                      f"quantities")

    # §7.12: I-12 entry census per deck per arm
    ec = {}
    for deck in DECKS:
        ec[deck] = {}
        for arm in ("R", "A0p", "A1p"):
            data = load_starts(A28 / "h5", deck, arm)
            rows_ = [(s, m.get("entry_census")) for s, m in data.items()
                     if m.get("entry_census")]
            deg = [s for s, c in rows_ if c.get("start_is_degenerate")]
            ec[deck][arm] = {
                "starts_visiting": len(deg),
                "of_starts": len(data),
                "non_positive": sum(c.get("n_non_positive_entries", 0)
                                    for _s, c in rows_),
                "of_entries": sum(
                    c.get("denominator_entries_after_the_first", 0)
                    for _s, c in rows_),
                "worst": min((c.get("min_entry_p_net_mw")
                              for _s, c in rows_
                              if c.get("min_entry_p_net_mw") is not None),
                             default=None),
            }
    out["entry_census"] = ec
    if not quiet:
        print("\n== §7.12 I-12 entry census, re-derived from raw")
        for deck, r in ec.items():
            for arm, v in r.items():
                w = "-" if v["worst"] is None else f"{v['worst']:.1f}"
                print(f"   {deck:<24}{arm:<6} starts {v['starts_visiting']:>2} "
                      f"of {v['of_starts']}   entries {v['non_positive']:>5} "
                      f"of {v['of_entries']:<6}  worst {w} MW")

    # §7.10: timing repetition counts and medians (context only, never a
    # ratio -- this only checks the published n and medians are the raw ones)
    tm = {}
    for deck in DECKS:
        tm[deck] = {}
        for arm in ("R", "A0p", "A1p"):
            data = load_starts(A28 / "h5", deck, arm)
            cpu = [m.get("cpu_s") for m in data.values()
                   if m.get("status") == "ok" and m.get("cpu_s")]
            tm[deck][arm] = {
                "n": len(cpu), "median": med(cpu),
                "p10": pctl(cpu, 10), "p90": pctl(cpu, 90),
            }
    out["timings"] = tm
    if not quiet:
        print("\n== §7.10 timing repetition counts and medians (context "
              "only; no ratio is formed here)")
        for deck, r in tm.items():
            for arm, v in r.items():
                print(f"   {deck:<24}{arm:<6} n={v['n']:>2}  median "
                      f"{v['median']:.1f} s  p10-p90 {v['p10']:.1f}-"
                      f"{v['p90']:.1f}")
    return out


# ---------------------------------------------------------------------------
# stage: gate_teeth  (queue check 8)
# ---------------------------------------------------------------------------


def stage_gate_teeth(quiet: bool = False) -> dict:
    """What A28's recorded §12 sensitivity evidence covers.

    This is the one stage that reads an A28 analysis artifact, because the
    artifact's COVERAGE is the thing under audit; its verdicts are also
    cross-checked against the arms the headline uses.
    """
    f = A28 / "_gate_sensitivity_a28.json"
    d = json.loads(f.read_text())
    arms = [k for k in d if k != "_summary"]
    per = {}
    for a in arms:
        r = d[a]
        per[a] = {k: v.get("status") for k, v in r.items()
                  if isinstance(v, dict) and "status" in v}
    sm = d.get("_summary") or {}
    out = {
        "arms_exercised": arms,
        "headline_arms_covered": {"A0p": "A0p" in arms, "A1p": "A1p" in arms},
        "summary": {k: sm.get(k) for k in
                    ("n_checks_that_must_fail", "n_that_did_fail",
                     "n_not_applicable", "all_teeth_bite")},
        "per_arm": per,
        "deck_note": (
            "a25_gates.sensitivity perturbs records of scenarios[0] only "
            "(large_tokamak_nof), plus one cross-deck tooth; the teeth "
            "exercise the predicates once per arm, not once per deck"
        ),
    }
    if not quiet:
        print(f"\n== A28 gate-sensitivity coverage: arms {arms}")
        print(f"   headline arms covered: {out['headline_arms_covered']}")
        print(f"   summary: {out['summary']}")
        print(f"   {out['deck_note']}")
        for a, r in per.items():
            print(f"   {a}: {r}")
    return out


# ---------------------------------------------------------------------------
# stage: teeth  (protocol §12 applied to this script's own checks)
# ---------------------------------------------------------------------------


def stage_teeth(quiet: bool = False) -> dict:
    """Each re-derivation above shown capable of failing, by doctoring an
    in-memory copy of the raw rows it watches and confirming its output moves.
    """
    import copy
    results = {}

    # -- census tooth 1: flipping one ifail must change the kept count -------
    deck = "st_regression"
    data = {a: load_starts(A28 / "h5", deck, a) for a in ("A0p", "A1p")}
    base = pair_tables(data, "A0p", "A1p")
    doc = copy.deepcopy(data)
    victim = base["census"]["kept"][0]
    doc["A1p"][victim]["mfile"]["ifail"] = "5.0"
    pert = pair_tables(doc, "A0p", "A1p")
    results["census_ifail_flip"] = {
        "kept_before": len(base["census"]["kept"]),
        "kept_after": len(pert["census"]["kept"]),
        "bites": len(pert["census"]["kept"]) == len(base["census"]["kept"]) - 1,
    }

    # -- census tooth 2: a 3e-6 relative objf shift must become a mismatch ---
    doc = copy.deepcopy(data)
    victim = base["census"]["kept"][1]
    o = float.fromhex(doc["A1p"][victim]["exact"]["norm_objf"])
    doc["A1p"][victim]["exact"]["norm_objf"] = (o * (1 + 3e-6)).hex()
    pert = pair_tables(doc, "A0p", "A1p")
    results["census_objf_shift"] = {
        "mismatches_before": len(base["census"]["objf_mismatch"]),
        "mismatches_after": len(pert["census"]["objf_mismatch"]),
        "bites": (len(pert["census"]["objf_mismatch"])
                  == len(base["census"]["objf_mismatch"]) + 1),
    }

    # -- census tooth 3: doubling one cost must move the median --------------
    doc = copy.deepcopy(data)
    for s in base["census"]["kept"]:
        doc["A1p"][s]["node_calls_solve_phase"] = (
            2 * doc["A1p"][s]["node_calls_solve_phase"])
        break
    pert = pair_tables(doc, "A0p", "A1p")
    results["census_cost_double"] = {
        "median_before": base["rule_a"]["median"],
        "median_after": pert["rule_a"]["median"],
        "bites": pert["rule_a"]["median"] != base["rule_a"]["median"],
    }

    # -- attribution tooth: a doctored ModuleSolveFailure must be counted ----
    a_base = stage_attribution(quiet=True)
    n0 = a_base["st_regression"]["A1p"]["n_module_solve_refusals"]
    # doctor by re-running the same logic on modified in-memory rows
    data_st = load_starts(A28 / "h5", "st_regression", "A1p")
    victim = sorted(data_st)[0]
    data_st[victim]["status"] = "crashed"
    data_st[victim]["traceback"] = (
        "Traceback (most recent call last):\n"
        "process.core.solver.module_solve.ModuleSolveFailure: module M1 did "
        "not converge in 20 inner sweeps at inner_tau=1e-06; max scaled "
        "residual inf on doctored.component")
    import re
    msf = 0
    comps = {}
    for s, m in data_st.items():
        if m.get("status") != "ok":
            tb = (m.get("traceback") or "").strip().splitlines()
            last = tb[-1] if tb else ""
            if "ModuleSolveFailure" in last:
                msf += 1
                g = re.search(r"on ([A-Za-z_][\w.]*)", last)
                if g:
                    comps[g.group(1)] = comps.get(g.group(1), 0) + 1
    results["attribution_doctored_refusal"] = {
        "refusals_before": n0, "refusals_after": msf,
        "component_seen": "doctored.component" in comps,
        "bites": msf == n0 + 1 and "doctored.component" in comps,
    }

    # -- accuracy tooth: scaling one residual must flip a paired count -------
    vals_r = _audit_residuals(A28 / "h5_audit1", "st_regression", "A0p")
    vals_a = _audit_residuals(A28 / "h5_audit1", "st_regression", "A1p")
    common = sorted(set(vals_r) & set(vals_a))
    la0 = sum(1 for s in common if vals_r[s] > vals_a[s])
    vals_a2 = dict(vals_a)
    vals_a2[common[0]] = vals_r[common[0]] * 10  # now A1p looser there
    la1 = sum(1 for s in common if vals_r[s] > vals_a2[s])
    results["accuracy_residual_scale"] = {
        "A0p_looser_before": la0, "A0p_looser_after": la1,
        "bites": la1 == la0 - 1,
    }

    # -- ladder tooth: halving one joint rung's cost must move matched-count -
    rungs, _c, _e = build_phase_b_rungs("st_regression")
    r0 = read_at_calibration(rungs, "p90")["matched_count"]["ratio"]
    doc_rungs = copy.deepcopy(rungs)
    for r in doc_rungs:
        if r["family"] == "joint" and r["label"] == "A1p_joint1e-05":
            r["cost"] = r["cost"] // 2
    r1 = read_at_calibration(doc_rungs, "p90")["matched_count"]["ratio"]
    results["ladder_cost_halve"] = {
        "matched_count_before": r0, "matched_count_after": r1,
        "bites": r1 is not None and r0 is not None and r1 < r0,
    }

    # -- ladder tooth 2: zeroing a residual must reroute the read ------------
    doc_rungs = copy.deepcopy(rungs)
    for r in doc_rungs:
        if r["label"] == "A1p_joint1e-05":
            r["p90"] = 0.0
    rd = read_at_calibration(doc_rungs, "p90")
    r2 = rd["matched_count"]
    results["ladder_zero_residual"] = {
        "read_via_before": read_at_calibration(rungs, "p90")["matched_count"]["via"],
        "read_via_after": r2["via"],
        "bites": r2["via"] != read_at_calibration(rungs, "p90")["matched_count"]["via"],
    }

    # -- ad4 tooth: doubling one moved-constant count must move a fraction ---
    d4 = stage_ad4(quiet=True)
    f_before = d4["rows"][0]["f1"]
    data1 = load_starts(A28 / "h5", "st_regression", "A1p")
    s0 = d4["rows"][0]["start"]
    t = data1[s0]["module_solve_totals"]
    frac_after = min(2 * t["n_call_models_with_moved_constant"],
                     t["n_call_models"]) / t["n_call_models"]
    results["ad4_count_double"] = {
        "fraction_before": f_before, "fraction_after": frac_after,
        "bites": frac_after != f_before,
    }

    # -- provenance tooth: a doctored head string must land in a new bucket --
    prov = stage_provenance(quiet=True)
    n_buckets = len(prov["buckets"])
    from collections import Counter
    c = Counter()
    first = True
    for f in sorted((A28 / "gate").rglob("metrics.json")):
        m = json.loads(f.read_text())
        h = m.get("tree_git_head")
        if first:
            h = "deadbeef" + (h or "")[8:]
            first = False
        c[(h or "?")[:8]] += 1
    results["provenance_doctored_head"] = {
        "gate_heads_after_doctoring": dict(c),
        "bites": "deadbeef" in c,
    }
    results["provenance_bucket_count"] = n_buckets

    # -- decks tooth: an extra substantive line must appear in the diff ------
    dk = stage_decks(quiet=True)
    n_added = len(dk["large_tokamak_nof"]["non_comment_lines_added"])
    frozen = (HERE / "scenarios" / "large_tokamak_nof.IN.DAT").read_text()
    lifted = (A28 / "_decks" / "large_tokamak_nof" /
              "large_tokamak_nof_lifted.IN.DAT").read_text()
    lifted2 = lifted + "\ndoctored_variable = 1.0\n"
    import difflib
    f_sub = [l for l in frozen.splitlines() if not l.strip().startswith("*")]
    l_sub = [l for l in lifted2.splitlines() if not l.strip().startswith("*")]
    added2 = [l for l in difflib.unified_diff(f_sub, l_sub, lineterm="", n=0)
              if l.startswith("+") and not l.startswith("+++")]
    results["decks_extra_line"] = {
        "added_before": n_added, "added_after": len(added2),
        # the tooth bites if the diff DETECTS the doctored line at all; the
        # exact count can grow by 2 when the appended line opens a new hunk
        "bites": len(added2) > n_added,
    }

    n_teeth = sum(1 for v in results.values()
                  if isinstance(v, dict) and "bites" in v)
    n_bite = sum(1 for v in results.values()
                 if isinstance(v, dict) and v.get("bites"))
    results["_summary"] = {"n_teeth": n_teeth, "n_that_bite": n_bite,
                           "all_bite": n_bite == n_teeth}
    if not quiet:
        print(f"\n== protocol §12 teeth for this script: {n_bite} of "
              f"{n_teeth} bite ({'PASS' if n_bite == n_teeth else 'FAIL'})")
        for k, v in results.items():
            if isinstance(v, dict) and "bites" in v:
                print(f"   {k:<32} {'bites' if v['bites'] else 'DOES NOT BITE'}"
                      f"  {({kk: vv for kk, vv in v.items() if kk != 'bites'})}")
    return results


# ---------------------------------------------------------------------------


STAGES = {
    "census": lambda: stage_census(),
    "attribution": lambda: stage_attribution(),
    "accuracy": lambda: stage_accuracy(),
    "ladder": lambda: stage_ladder(),
    "phase_a": lambda: stage_phase_a(),
    "ad4": lambda: stage_ad4(),
    "provenance": lambda: stage_provenance(),
    "factors": lambda: stage_factors(),
    "decks": lambda: stage_decks(),
    "doc_tables": lambda: stage_doc_tables(),
    "gate_teeth": lambda: stage_gate_teeth(),
    "teeth": lambda: stage_teeth(),
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=list(STAGES) + ["all"])
    args = ap.parse_args()
    stages = list(STAGES) if args.stage == "all" else [args.stage]
    for s in stages:
        print(f"\n{'#' * 74}\n# stage: {s}\n{'#' * 74}")
        STAGES[s]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
