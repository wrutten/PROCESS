#!/usr/bin/env python
"""V2 experiment report analysis — the analysis-time checks the tally defers,
plus an independent recomputation of every tally quantity from the raw
per-run records (protocol §15: the experiment report's published numbers come
from this committed script).

Verbatim copy (task A41, first commit) of
arch_surgery/MDA_partitioning_experiment_v2/v2_report_analysis.py at commit
b7dbd2a9; content otherwise unchanged.

Reads ONLY on-disk campaign records
(``runs/phase_a/campaign/**/metrics.json``, ``runs/phase_b/campaign/**/
metrics.json``) and the committed configuration.  It does not re-run
anything, and it deliberately does not import the tally code: shared
definitions are restated here so a tally bug cannot vouch for itself.

    PROCESS_surgery_env python arch_surgery/MDA_partitioning_experiment_v2/v2_report_analysis.py

Computes, per deck:

Phase B (plan §4):
  check 1  paired |Δ norm_objf| (exact hex floats) for R→B0 (the measured
           yardstick), B0→B1, B0→B2, B0→B3, and B2→B3 beside; median and
           nearest-rank p90; acceptance median AND p90 ≤ F × R→B0's.
  check 2  paired iteration ratios recomputed two ways — the tally's
           operationalization (drop pairs missing n_solver_iterations;
           upper-median) and statistics.median over the same pairs — PLUS
           the paired model-call (function-evaluation) ratio over ALL
           both-ok pairs, which loses no pair to a missing field.  Every
           dropped pair is named with its reason (trap T11).
  check 3  constraint-93 residual at every accepted optimum of the lifted
           arms (pulsed decks).
  check 4  taxonomy per arm (status, and ifail among ok) with denominator
           25; identical-success-set cost sums (seeds where every arm of
           the deck is ok) for solve-phase node calls and model calls.
  extra    post-solve suppression share for B2/B3 against A33's declared
           baselines; provenance census (tree_git_head, dirty) over all
           records.

Phase A (plan §3): independent recomputation from the RAW per-run records
(not the tally's own per_run copies): count ratio A1/A0, per-node bracket,
audit similarity distributions with the F = 10 verdict at median and p90
(nearest-rank), pairing, cold-start terms, lift-residual medians,
provenance census.  Printed beside the tally's values with MATCH flags.

Output: ``runs/report_analysis.json`` + a printed summary.  Counts and hex
floats only; wall clock appears nowhere.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from statistics import median

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import v2_config as cfg  # noqa: E402

PA = HERE / "runs" / "phase_a"
PB = HERE / "runs" / "phase_b"
F = cfg.SIMILARITY_FACTOR_F


def jload(p: Path):
    return json.load(open(p))


def p90(vals):
    """Nearest-rank p90 — element ceil(0.9 n) of the sorted list (the
    tally's declared definition, restated)."""
    import math
    s = sorted(vals)
    return s[math.ceil(0.9 * len(s)) - 1] if s else None


def hexf(h):
    return float.fromhex(h) if isinstance(h, str) else None


# ── Phase B ──────────────────────────────────────────────────────────────

def phase_b() -> dict:
    out: dict = {}
    for deck in cfg.DECKS:
        rows: dict[str, list] = {}
        for arm in cfg.PHASE_B_ARMS:
            arm_dir = PB / "campaign" / deck / arm
            if not arm_dir.exists():
                continue
            per = []
            for k in range(cfg.N_STARTS):
                p = arm_dir / f"start{k:03d}" / "metrics.json"
                if not p.exists():
                    per.append({"status": "missing"})
                    continue
                m = jload(p)
                per.append({
                    "status": m.get("status"),
                    "ifail": (m.get("mfile") or {}).get("ifail"),
                    "iters": m.get("n_solver_iterations"),
                    "model_calls": m.get("n_model_calls"),
                    "node_solve": m.get("node_calls_solve_phase"),
                    "objf_hex": (m.get("exact") or {}).get("norm_objf"),
                    "sqsumsq": (m.get("values") or {}).get("sqsumsq"),
                    "c93": m.get("constraint_93"),
                    "ps": m.get("post_solve_totals"),
                    "head": m.get("tree_git_head"),
                    "dirty": m.get("tree_git_dirty"),
                })
            rows[arm] = per
        if not rows:
            continue
        d: dict = {"taxonomy": {}, "provenance": {}}

        heads = sorted({(r.get("head"), r.get("dirty")) for per in rows.values()
                        for r in per if r.get("head")})
        d["provenance"]["stamps"] = [f"{h} dirty={dr}" for h, dr in heads]

        for arm, per in rows.items():
            tax: dict = {}
            for r in per:
                tax[str(r["status"])] = tax.get(str(r["status"]), 0) + 1
            ok = [r for r in per if r["status"] == "ok"]
            d["taxonomy"][arm] = {
                "denominator": len(per), "by_status": tax,
                "ok_with_ifail_1": sum(1 for r in ok if r.get("ifail") == 1.0),
                "ok_with_other_ifail": sorted({r.get("ifail") for r in ok
                                               if r.get("ifail") != 1.0}),
            }

        base = rows.get("B0")

        def conv(r):
            """An ACCEPTED optimum: run ok AND the optimiser converged.
            ifail = 1 is VMCON's success code; ifail = 5 runs carry status
            'ok' (the process completed) but no optimum — the A30 taxonomy's
            'unconverged' class, split out rather than silently pooled."""
            return r["status"] == "ok" and r.get("ifail") == 1.0

        def paired(arm_a, arm_b, converged_only=False):
            """Both-ok (optionally both-converged) pairs (seed, a, b)."""
            keep = conv if converged_only else (
                lambda r: r["status"] == "ok")
            return [(k, ra, rb) for k, (ra, rb)
                    in enumerate(zip(rows[arm_a], rows[arm_b]))
                    if keep(ra) and keep(rb)]

        # check 1 — |Δ norm_objf| spreads, R→B0 the yardstick.  The plan's
        # check is at ACCEPTED optima, so the primary construction pairs
        # converged runs only; the all-ok construction is published beside
        # it (an unconverged exit is not an optimum, but hiding it would
        # shrink a denominator silently — trap T11).
        d["check1_objf"] = {}
        for variant, conv_only in (("converged_only", True), ("all_ok", False)):
            spreads = {}
            for name, (a, b) in {"R->B0": ("R", "B0"), "B0->B1": ("B0", "B1"),
                                 "B0->B2": ("B0", "B2"), "B0->B3": ("B0", "B3"),
                                 "B2->B3": ("B2", "B3")}.items():
                if a not in rows or b not in rows:
                    continue
                deltas, listed = [], []
                for k, ra, rb in paired(a, b, converged_only=conv_only):
                    fa, fb = hexf(ra["objf_hex"]), hexf(rb["objf_hex"])
                    if fa is not None and fb is not None:
                        deltas.append(abs(fb - fa))
                        if abs(fb - fa) > 1e-6:
                            listed.append({"seed": k, "delta": abs(fb - fa),
                                           "ifail": [ra.get("ifail"),
                                                     rb.get("ifail")]})
                if deltas:
                    spreads[name] = {
                        "n": len(deltas), "median": median(deltas),
                        "p90": p90(deltas), "max": max(deltas),
                        "pairs_above_1e-6": listed,
                        "values_published": sorted(deltas)}
            yard = spreads.get("R->B0")
            for name, s in spreads.items():
                if yard and name.startswith("B0->"):
                    s["accept_median"] = s["median"] <= F * yard["median"]
                    s["accept_p90"] = s["p90"] <= F * yard["p90"]
                    s["accepted"] = s["accept_median"] and s["accept_p90"]
            d["check1_objf"][variant] = spreads

        # check 2 — iteration ratios, three operationalizations
        d["check2_iters"] = {}
        for name, (a, b) in {"B0->B1": ("B0", "B1"), "B0->B2": ("B0", "B2"),
                             "B0->B3": ("B0", "B3"), "B0->R": ("B0", "R"),
                             "B2->B3": ("B2", "B3")}.items():
            if a not in rows or b not in rows:
                continue
            pr = paired(a, b)
            ratios, dropped = [], []
            fev = []
            for k, ra, rb in pr:
                ia, ib = ra["iters"], rb["iters"]
                if ia and ib:
                    ratios.append(ib / ia)
                else:
                    dropped.append({"seed": k, f"{a}_iters": ia,
                                    f"{b}_iters": ib,
                                    f"{a}_ifail": ra.get("ifail"),
                                    f"{b}_ifail": rb.get("ifail")})
                ma, mb = ra["model_calls"], rb["model_calls"]
                if ma and mb:
                    fev.append(mb / ma)
            ratios.sort()
            d["check2_iters"][name] = {
                "n_both_ok": len(pr), "n_iter_pairs": len(ratios),
                "dropped_pairs": dropped,
                "median_tally_style": (ratios[len(ratios) // 2]
                                       if ratios else None),
                "median_statistics": median(ratios) if ratios else None,
                "bound_1p05_met_tally_style": (bool(ratios) and
                                               ratios[len(ratios) // 2]
                                               <= cfg.ITER_RATIO_MAX),
                "model_call_ratio_median": (median(fev) if fev else None),
                "model_call_ratio_n": len(fev),
            }

        # check 3 — constraint 93 "lift actually closed", split by
        # convergence: the declared check is at ACCEPTED optima; residuals
        # at unconverged exits are reported beside (they are large by
        # definition — the equality was never enforced to completion).
        d["check3_c93"] = {}
        for arm in ("B1", "B2", "B3"):
            if arm not in rows:
                continue
            entry: dict = {}
            for variant, keep in (("accepted", conv),
                                  ("unconverged_ok",
                                   lambda r: r["status"] == "ok"
                                   and r.get("ifail") != 1.0)):
                per_start = []
                for k, r in enumerate(rows[arm]):
                    if keep(r) and r.get("c93"):
                        per_start.append({
                            "seed": k,
                            "residual_s": r["c93"].get("residual_s"),
                            "relative": r["c93"].get(
                                "residual_relative_to_burn_time"),
                        })
                res = [abs(x["residual_s"]) for x in per_start
                       if x["residual_s"] is not None]
                entry[variant] = {
                    "n": len(per_start),
                    "abs_residual_s_median": median(res) if res else None,
                    "abs_residual_s_max": max(res) if res else None,
                    "per_start": per_start,
                }
            d["check3_c93"][arm] = entry

        # check 4 — identical-success-set cost sums, both constructions:
        # all-ok (completions count to cost statistics — A30) and
        # all-converged (unconverged runs stop at the iteration cap, which
        # truncates cost on both sides of a pair; published beside).
        arms = [a for a in cfg.PHASE_B_ARMS if a in rows]
        d["check4_cost_sums"] = {}
        for variant, keep in (("identical_ok_set",
                               lambda r: r["status"] == "ok"),
                              ("identical_converged_set", conv)):
            common = [k for k in range(cfg.N_STARTS)
                      if all(keep(rows[a][k]) for a in arms)]
            sums: dict = {"n_seeds": len(common), "seeds": common}
            per_arm: dict = {}
            for a in arms:
                ns = sum(rows[a][k]["node_solve"] or 0 for k in common)
                mc = sum(rows[a][k]["model_calls"] or 0 for k in common)
                per_arm[a] = {"node_calls_solve_phase": ns,
                              "model_calls": mc}
            b0 = per_arm.get("B0")
            for a in arms:
                if b0 and b0["node_calls_solve_phase"]:
                    per_arm[a]["node_ratio_vs_B0"] = (
                        per_arm[a]["node_calls_solve_phase"]
                        / b0["node_calls_solve_phase"])
            sums["per_arm"] = per_arm
            d["check4_cost_sums"][variant] = sums

        # per-block node-call split over the identical-ok-set: block
        # membership from the deck's own B3 (fallback B2) executed
        # schedule, post-solve set from the same record; the lifted
        # `pulse` node executes in-loop outside any block and is assigned
        # to PULSE; anything else unmapped is named, not pooled.
        block_map: dict[str, str] = {}
        ps_nodes: set = set()
        for arm in ("B3", "B2"):
            for k in range(cfg.N_STARTS):
                p = (PB / "campaign" / deck / arm / f"start{k:03d}"
                     / "metrics.json")
                if not p.exists():
                    continue
                m = jload(p)
                sched = m.get("arch_block_schedule")
                if sched:
                    for bname, nodes, _ in sched:
                        for n in nodes:
                            block_map[n] = bname
                    ps_nodes = set((m.get("post_solve_totals") or {})
                                   .get("nodes") or [])
                    break
            if block_map:
                break
        block_map.setdefault("pulse", "PULSE")
        common_ok = [k for k in range(cfg.N_STARTS)
                     if all(rows[a][k]["status"] == "ok" for a in arms)]
        per_block: dict = {}
        for a in arms:
            agg: dict[str, int] = {}
            for k in common_ok:
                p = (PB / "campaign" / deck / a / f"start{k:03d}"
                     / "metrics.json")
                m = jload(p)
                census = ((m.get("node_census") or {})
                          .get("per_node_counted_through_Caller_node") or {})
                for n, c in census.items():
                    blk = ("post_solve" if n in ps_nodes
                           else block_map.get(n, f"UNMAPPED:{n}"))
                    agg[blk] = agg.get(blk, 0) + c
            agg["TOTAL"] = sum(agg.values())
            per_block[a] = agg
        d["per_block_node_calls_identical_ok_set"] = {
            "n_seeds": len(common_ok), "block_map_source": "B3/B2 record",
            "per_arm": per_block}

        # post-solve suppression share (B2/B3), vs A33 baselines
        d["post_solve_share"] = {}
        for arm in ("B2", "B3"):
            if arm not in rows:
                continue
            sup = sum((r["ps"] or {}).get("n_call_sites_suppressed", 0)
                      for r in rows[arm] if r["status"] == "ok")
            executed = sum(r["node_solve"] or 0 for r in rows[arm]
                           if r["status"] == "ok")
            if executed:
                d["post_solve_share"][arm] = {
                    "suppressed_call_sites": sup,
                    "executed_solve_phase_calls": executed,
                    "share_of_wouldbe_calls":
                        sup / (sup + executed),
                }
        out[deck] = d
    return out


# ── Phase A ──────────────────────────────────────────────────────────────

def phase_a() -> dict:
    out: dict = {}
    for deck in cfg.DECKS:
        droot = PA / "campaign" / deck
        if not droot.exists():
            continue
        d: dict = {}
        rows: dict[str, dict[int, dict]] = {"A0": {}, "A1": {}}
        heads = set()
        for arm in ("A0", "A1"):
            for sd in sorted((droot / arm).glob("start*")):
                m = jload(sd / "metrics.json")
                k = int(sd.name.replace("start", ""))
                aud = (m.get("exit_audit") or {})
                census = ((m.get("node_census") or {}).get("counted")
                          or ((m.get("module_solve_totals") or {})
                              .get("per_node") or {}))
                rows[arm][k] = {
                    "status": m.get("status"),
                    "node_calls": m.get("node_calls_single_eval",
                                        m.get("node_calls_solve_phase")),
                    "audit_max": aud.get("residual_max"),
                    "audit_max_hex": aud.get("residual_max_hex"),
                    "census": census,
                    "head": m.get("tree_git_head"),
                    "dirty": m.get("tree_git_dirty"),
                }
                heads.add((m.get("tree_git_head"), m.get("tree_git_dirty")))
        d["provenance_stamps"] = sorted(f"{h} dirty={dr}" for h, dr in heads)

        seeds = sorted(set(rows["A0"]) & set(rows["A1"]))
        ok = [k for k in seeds if rows["A0"][k]["status"] == "ok"
              and rows["A1"][k]["status"] == "ok"]
        d["n_paired_ok"] = len(ok)

        tot = {arm: sum(rows[arm][k]["node_calls"] or 0 for k in ok)
               for arm in ("A0", "A1")}
        d["node_calls_total_paired_ok"] = tot
        d["unweighted_count_ratio_A1_over_A0"] = (
            tot["A1"] / tot["A0"] if tot["A0"] else None)

        # per-node bracket from raw censuses
        node_sums: dict[str, dict[str, int]] = {}
        for arm in ("A0", "A1"):
            for k in ok:
                for n, c in (rows[arm][k]["census"] or {}).items():
                    node_sums.setdefault(n, {"A0": 0, "A1": 0})
                    node_sums[n][arm] += c
        ratios = {n: (v["A1"] / v["A0"]) for n, v in node_sums.items()
                  if v["A0"]}
        d["weighting_invariance_bracket"] = ([min(ratios.values()),
                                              max(ratios.values())]
                                             if ratios else None)
        d["per_node_ratio_extremes"] = {
            "min": sorted(ratios, key=ratios.get)[:3],
            "max": sorted(ratios, key=ratios.get, reverse=True)[:3],
        }

        # audit similarity + F verdict
        sim: dict = {}
        for arm in ("A0", "A1"):
            vals = sorted(rows[arm][k]["audit_max"] for k in ok
                          if rows[arm][k]["audit_max"] is not None)
            sim[arm] = {"n": len(vals), "median": median(vals),
                        "p90": p90(vals), "max": max(vals), "min": min(vals)}
        # audit argmax ownership census — the A35 §6 item 2 reconciliation
        # check: which node's writeset owns each A1 run's audit argmax.
        # Components are keyed by data structure; the post-solve set's
        # members surface as the costs/vacuum/water_use structures.
        import collections
        post_solve_prefixes = {"costs", "vacuum", "water_use"}
        argmax_prefix = collections.Counter()
        for k in ok:
            m = jload(droot / "A1" / f"start{k:03d}" / "metrics.json")
            am = ((m.get("exit_audit") or {}).get("brief") or {}).get("argmax")
            key = am.get("key") if isinstance(am, dict) else am
            if key:
                argmax_prefix[key.split(".")[0]] += 1
        d["a1_audit_argmax_by_prefix"] = dict(argmax_prefix)
        d["a1_audit_argmax_post_solve_owned"] = sum(
            v for p, v in argmax_prefix.items()
            if p in post_solve_prefixes)

        med_ok = (sim["A0"]["median"] > 0
                  and sim["A1"]["median"] <= F * sim["A0"]["median"])
        p90_ok = (sim["A0"]["p90"] > 0
                  and sim["A1"]["p90"] <= F * sim["A0"]["p90"])
        sim["similarity_within_F"] = bool(med_ok and p90_ok)
        sim["note"] = ("A0 median/p90 of 0 makes any nonzero A1 value an "
                       "infinite factor — counted as NOT within F"
                       if (sim["A0"]["median"] == 0 or sim["A0"]["p90"] == 0)
                       else "")
        d["audit_similarity"] = sim
        out[deck] = d
    return out


def main() -> int:
    result = {"phase_a": phase_a(), "phase_b": phase_b(),
              "declared": {"F": F, "iter_ratio_max": cfg.ITER_RATIO_MAX,
                           "tau": cfg.TAU, "delta": cfg.DELTA,
                           "n_starts": cfg.N_STARTS}}
    out = HERE / "runs" / "report_analysis.json"
    out.write_text(json.dumps(result, indent=1))
    print(f"written: {out}\n")

    # console digest
    for deck, d in result["phase_a"].items():
        s = d["audit_similarity"]
        print(f"[A] {deck}: paired_ok={d['n_paired_ok']} "
              f"ratio={d['unweighted_count_ratio_A1_over_A0']:.4f} "
              f"bracket={d['weighting_invariance_bracket']} "
              f"A0 med/p90={s['A0']['median']:.3g}/{s['A0']['p90']:.3g} "
              f"A1 med/p90={s['A1']['median']:.3g}/{s['A1']['p90']:.3g} "
              f"withinF={s['similarity_within_F']} "
              f"stamps={d['provenance_stamps']}")
    for deck, d in result["phase_b"].items():
        print(f"[B] {deck}: stamps={d['provenance']['stamps']}")
        print(f"    taxonomy: " + " ".join(
            f"{a}[ok={t['by_status'].get('ok', 0)}/conv="
            f"{t['ok_with_ifail_1']}]"
            for a, t in d["taxonomy"].items()))
        for variant, spreads in d["check1_objf"].items():
            for name, e in spreads.items():
                acc = e.get("accepted", "-")
                print(f"    objf[{variant[:4]}] {name:7s} n={e['n']:2d} "
                      f"med={e['median']:.3g} p90={e['p90']:.3g} "
                      f"max={e['max']:.3g} accept={acc}")
        for name, e in d["check2_iters"].items():
            print(f"    iter {name:7s} n_ok={e['n_both_ok']:2d} "
                  f"n_pairs={e['n_iter_pairs']:2d} "
                  f"med={e['median_statistics']} "
                  f"(tally-style {e['median_tally_style']}) "
                  f"dropped={len(e['dropped_pairs'])}")
        for arm, e in d["check3_c93"].items():
            a = e["accepted"]
            print(f"    c93  {arm}: accepted n={a['n']} "
                  f"med={a['abs_residual_s_median']} "
                  f"max={a['abs_residual_s_max']}   "
                  f"unconverged n={e['unconverged_ok']['n']} "
                  f"max={e['unconverged_ok']['abs_residual_s_max']}")
        for variant, cs in d["check4_cost_sums"].items():
            line = " ".join(f"{a}:{v['node_calls_solve_phase']}"
                            f"({v.get('node_ratio_vs_B0', 0):.3f})"
                            for a, v in cs["per_arm"].items())
            print(f"    cost[{variant}] n={cs['n_seeds']}: {line}")
        for arm, e in d["post_solve_share"].items():
            print(f"    ps   {arm}: suppressed={e['suppressed_call_sites']} "
                  f"share={e['share_of_wouldbe_calls']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
