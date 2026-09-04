#!/usr/bin/env python
"""V3 experiment report analysis — an independent recomputation of every
tally quantity from the raw per-run records (protocol §15: the experiment
report's published numbers come from a committed script), plus ``--verify``.

Copied verbatim (task A41, first commit 913b89f0) from
arch_surgery/MDA_partitioning_experiment_v2/v2_report_analysis.py at commit
b7dbd2a9, then rewritten for the V3 constructions (T-a … T-e, checks 1,
1a, 2, 3, 4) by task A41.

Reads ONLY on-disk campaign records
(``runs/phase_a/campaign/**``, ``runs/phase_b/campaign/**``) and the
committed configuration and data artifacts.  It does not re-run anything,
and it deliberately does not import the tally code: every shared
definition is RESTATED here so a tally bug cannot vouch for itself.  In
particular:

* the restricted audit's excluded set is re-derived independently
  (post-solve nodes -> run-time write census -> spec keys, never a
  prefix), and each run's restricted maximum is recomputed from the raw
  per-component vector (``audit_residual.json``) rather than read from the
  runner's own ``exit_audit.restricted`` — the two must agree bit-for-bit;
* every Phase B check statistic uses the DECLARED nearest-rank median
  (upper-middle, sorted[n // 2]; orchestrator correction 0a8f5af2), with
  statistics.median printed beside as a diagnostic;
* the O3 floor, the check-1a clustering and the deck-invalid-seed
  statistic are restated from their declarations in v3_config.

``--verify`` additionally compares the recomputation against the committed
tallies (``runs/phase_a/tally.json``, ``runs/phase_b/tally.json``) cell by
cell and exits nonzero on any mismatch — the report cites numbers only
after this passes.  ``--mode smoke`` points the same recomputation and the
same comparison at the machinery-smoke records
(``runs/phase_*/smoke/``), which is how the verifier is exercised before
the campaign exists: with no records it checks ZERO cells and exits 0, and
a check that cannot fail is not a check (protocol §12).  Smoke numbers are
machinery, never measurements.

Output: ``runs/report_analysis.json`` (``runs/report_analysis_smoke.json``
in smoke mode) + a printed summary.  Counts and hex floats only; wall clock
appears nowhere.
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import v3_config as cfg  # noqa: E402

PA = HERE / "runs" / "phase_a"
PB = HERE / "runs" / "phase_b"
F = cfg.SIMILARITY_FACTOR_F


def roots_for(mode: str) -> dict:
    """Where a run mode's per-run records and its committed tally live.

    ``campaign`` (default) is the real thing: A42's records under
    ``runs/phase_*/campaign/`` against the tallies the phase scripts write
    beside them.  ``smoke`` points the SAME recomputation at the machinery
    smokes, so ``--verify`` is exercisable before the campaign exists —
    without it the verifier checks zero cells and exits 0, which is a pass
    that cannot fail (protocol §12).  Smoke numbers are machinery, never
    measurements; the smoke run writes its own output file.
    """
    if mode == "smoke":
        return {"pa_records": PA / "smoke",
                "pa_tally": PA / "smoke" / "tally.json",
                "pb_records": PB / "smoke",
                "pb_tally": PB / "smoke" / "tally.json",
                "out": HERE / "runs" / "report_analysis_smoke.json"}
    return {"pa_records": PA / "campaign", "pa_tally": PA / "tally.json",
            "pb_records": PB / "campaign", "pb_tally": PB / "tally.json",
            "out": HERE / "runs" / "report_analysis.json"}

FORENSICS_FIELDS = ("n_solver_iterations", "ifail", "ladder_stage",
                    "constraint_residual_vector", "active_set")


def jload(p: Path):
    return json.load(open(p))


def rank_median(vals):
    """DECLARED (restated): nearest-rank upper-middle, sorted[n // 2]."""
    s = sorted(vals)
    return s[len(s) // 2] if s else None


def p90(vals):
    """Nearest-rank p90 (restated): element ceil(0.9 n) of the sorted
    list."""
    s = sorted(vals)
    return s[math.ceil(0.9 * len(s)) - 1] if s else None


def hexf(h):
    return float.fromhex(h) if isinstance(h, str) else None


def excluded_keys(deck: str) -> set:
    """T-a's excluded set, re-derived independently: post-solve NODES ->
    written fields (committed run-time census) -> intersected with the a26
    spec keys.  Never a prefix (st's ``pulse`` writes nothing there)."""
    nodes = json.loads(cfg.postsolve_for(deck).read_text())[
        "post_solve_nodes"]
    census = json.loads((cfg.DATA / "node_writesets.json").read_text())[
        "per_scenario"][deck]
    wb = census["writes_by_node"]
    known = set(census.get("node_module") or ()) | set(wb)
    keys = {c["key"] for c in json.loads(
        cfg.ystate_for(deck).read_text())["components"]}
    excl: set = set()
    for n in nodes:
        if n not in known:
            raise RuntimeError(f"post-solve node {n!r} unknown to the "
                               f"{deck} write census")
        excl |= set(wb.get(n, ()))
    return excl & keys


# ── Phase A ──────────────────────────────────────────────────────────────


def phase_a(camp_root: Path | None = None) -> dict:
    out: dict = {}
    camp_root = camp_root or (PA / "campaign")
    campf = camp_root / "campaign.json"
    if not campf.exists():
        return out
    camp = jload(campf)
    arms = tuple(camp["arms"])
    seeds = camp["seeds"]
    for deck in camp["decks"]:
        droot = camp_root / deck
        if not droot.exists():
            continue
        excl = excluded_keys(deck)
        d: dict = {"arms": list(arms)}
        rows: dict[str, dict[int, dict]] = {a: {} for a in arms}
        heads = set()
        restricted_mismatch = []
        for arm in arms:
            for k in seeds:
                sd = droot / arm / f"start{k:03d}"
                mp = sd / "metrics.json"
                if not mp.exists():
                    rows[arm][k] = {"status": "missing"}
                    continue
                m = jload(mp)
                aud = m.get("exit_audit") or {}
                rec_res = (aud.get("restricted") or {})
                # recompute the restricted max from the raw vector
                vecp = sd / "audit_residual.json"
                r_max = r_arg = None
                if vecp.exists():
                    scaled = jload(vecp).get("scaled") or {}
                    kept = {nm: v for nm, v in scaled.items()
                            if nm not in excl}
                    if kept:
                        r_arg = max(kept, key=kept.get)
                        r_max = kept[r_arg]
                if (rec_res.get("max") is not None and r_max is not None
                        and float(rec_res["max"]).hex()
                        != float(r_max).hex()):
                    restricted_mismatch.append(f"{arm}/start{k:03d}")
                census = ((m.get("node_census") or {}).get("counted") or {})
                rows[arm][k] = {
                    "status": m.get("status"),
                    "node_calls": m.get("node_calls_single_eval"),
                    "audit_max": aud.get("residual_max"),
                    "restricted_max_recomputed": r_max,
                    "restricted_argmax_recomputed": r_arg,
                    "census": census,
                    "has_forensics": "exit_forensics" in m,
                    "head": m.get("tree_git_head"),
                    "dirty": m.get("tree_git_dirty"),
                }
                heads.add((m.get("tree_git_head"), m.get("tree_git_dirty")))
        d["provenance_stamps"] = sorted(
            f"{h} dirty={dr}" for h, dr in heads)
        d["restricted_recompute_mismatches"] = restricted_mismatch
        d["n_excluded_keys_rederived"] = len(excl)

        ok = [k for k in seeds
              if all(rows[a][k].get("status") == "ok" for a in arms)]
        d["n_paired_ok"] = len(ok)
        d["forensics_missing_ok_records"] = [
            f"{a}/start{k:03d}" for a in arms for k in ok
            if not rows[a][k].get("has_forensics")]

        tot = {a: sum(rows[a][k]["node_calls"] or 0 for k in ok)
               for a in arms}
        d["node_calls_total_paired_ok"] = tot
        d["count_ratios"] = {}
        node_sums: dict[str, dict[str, int]] = {}
        for a in arms:
            for k in ok:
                for n, c in (rows[a][k]["census"] or {}).items():
                    node_sums.setdefault(n, {x: 0 for x in arms})
                    node_sums[n][a] += c
        for base, var in [("A0", a) for a in arms if a != "A0"] + (
                [("A1u", "A1")] if {"A1u", "A1"} <= set(arms) else []):
            ratios = [v[var] / v[base] for v in node_sums.values()
                      if v.get(base)]
            d["count_ratios"][f"{base}->{var}"] = {
                "unweighted_count_ratio": (tot[var] / tot[base]
                                           if tot.get(base) else None),
                "weighting_invariance_bracket": (
                    [min(ratios), max(ratios)] if ratios else None),
            }

        # T-a similarity, both statistics, per pair against A0
        sim: dict = {}
        for stat, field in (("whole_state", "audit_max"),
                            ("restricted", "restricted_max_recomputed")):
            dists = {}
            for a in arms:
                vals = sorted(rows[a][k][field] for k in ok
                              if rows[a][k].get(field) is not None)
                dists[a] = {"n": len(vals),
                            "median": (statistics.median(vals)
                                       if vals else None),
                            "p90": p90(vals)}
            entry: dict = {"distributions": dists}
            for a in [x for x in arms if x != "A0"]:
                m0, m1 = dists["A0"]["median"], dists[a]["median"]
                q0, q1 = dists["A0"]["p90"], dists[a]["p90"]

                def within(x, y):
                    if x is None or y is None:
                        return None
                    if x == 0 and y == 0:
                        return True
                    if x == 0 or y == 0:
                        return False
                    return max(x, y) / min(x, y) <= F
                entry[f"A0/{a}"] = {
                    "median_within_F": within(m0, m1),
                    "p90_within_F": within(q0, q1),
                    "similar": bool(within(m0, m1) and within(q0, q1)),
                }
            sim[stat] = entry
        d["audit_similarity"] = sim

        # restricted argmax census (recomputed), per block arm
        d["argmax_census_restricted"] = {
            a: {nm: sum(1 for k in ok
                        if rows[a][k].get("restricted_argmax_recomputed")
                        == nm)
                for nm in sorted({rows[a][k].get(
                    "restricted_argmax_recomputed") for k in ok} - {None})}
            for a in arms if a != "A0"}
        out[deck] = d
    return out


# ── Phase B ──────────────────────────────────────────────────────────────


def phase_b(root: Path | None = None) -> dict:
    out: dict = {}
    root = root or (PB / "campaign")
    if not root.exists():
        return out
    for deck in cfg.DECKS:
        rows: dict[str, list] = {}
        for arm in cfg.PHASE_B_ARMS:
            arm_dir = root / deck / arm
            if not arm_dir.exists():
                continue
            per = []
            for k in range(cfg.N_STARTS):
                p = arm_dir / f"start{k:03d}" / "metrics.json"
                if not p.exists():
                    per.append({"status": "missing"})
                    continue
                m = jload(p)
                fx = m.get("exit_forensics") or {}
                per.append({
                    "status": m.get("status"),
                    "ifail": (m.get("mfile") or {}).get("ifail"),
                    "iters": m.get("n_solver_iterations"),
                    "model_calls": m.get("n_model_calls"),
                    "node_solve": m.get("node_calls_solve_phase"),
                    "objf_hex": (m.get("exact") or {}).get("norm_objf"),
                    "c93": m.get("constraint_93"),
                    "forensics_ok": all(
                        fx.get(f) is not None for f in FORENSICS_FIELDS)
                    and (fx.get("n_attempts") or 0) >= 1,
                    "ladder_stage": fx.get("ladder_stage"),
                    "head": m.get("tree_git_head"),
                    "dirty": m.get("tree_git_dirty"),
                })
            rows[arm] = per
        if not rows:
            continue
        arms = [a for a in cfg.PHASE_B_ARMS if a in rows]
        d: dict = {}
        heads = sorted({(r.get("head"), r.get("dirty"))
                        for per in rows.values() for r in per
                        if r.get("head")})
        d["provenance_stamps"] = [f"{h} dirty={dr}" for h, dr in heads]

        def conv(r):
            return r.get("status") == "ok" and r.get("ifail") == 1.0

        # T-b: taxonomy, forensics completeness, deck-invalid seeds
        d["forensics_incomplete_ok_records"] = [
            f"{a}/start{k:03d}" for a in arms
            for k, r in enumerate(rows[a])
            if r.get("status") == "ok" and not r.get("forensics_ok")]
        invalid = [k for k in range(cfg.N_STARTS)
                   if not any(conv(rows[a][k]) for a in arms)]
        d["deck_invalid_seeds"] = {"seeds": invalid, "n": len(invalid)}
        valid = [k for k in range(cfg.N_STARTS) if k not in invalid]
        d["taxonomy"] = {}
        for a in arms:
            tax: dict = {}
            for r in rows[a]:
                tax[str(r.get("status"))] = tax.get(str(r.get("status")),
                                                    0) + 1
            d["taxonomy"][a] = {
                "denominator": cfg.N_STARTS,
                "by_status": tax,
                "n_converged": sum(1 for r in rows[a] if conv(r)),
                "n_not_converged_excl_deck_invalid": (
                    len(valid) - sum(1 for k in valid if conv(rows[a][k]))),
                "denominator_excl_deck_invalid": len(valid),
            }

        # T-c / check 1: spreads with yardstick and O3 floor
        pair_defs = {"R->B0": ("R", "B0"), "B0->B1": ("B0", "B1"),
                     "B0->B2": ("B0", "B2"), "B0->B3": ("B0", "B3"),
                     "B2->B3": ("B2", "B3")}
        spreads: dict = {}
        for name, (a, b) in pair_defs.items():
            if a not in rows or b not in rows:
                continue
            deltas, base_abs = [], []
            for k in range(cfg.N_STARTS):
                ra, rb = rows[a][k], rows[b][k]
                if conv(ra) and conv(rb):
                    fa, fb = hexf(ra["objf_hex"]), hexf(rb["objf_hex"])
                    if fa is not None and fb is not None:
                        deltas.append(abs(fb - fa))
                        base_abs.append(abs(fa))
            floor_abs = (cfg.OBJF_FLOOR_REL * rank_median(base_abs)
                         if base_abs else None)
            spreads[name] = {"n": len(deltas),
                             "median": rank_median(deltas),
                             "median_statistics_diagnostic": (
                                 statistics.median(deltas)
                                 if deltas else None),
                             "p90": p90(deltas),
                             "max": max(deltas) if deltas else None,
                             "floor_abs": floor_abs}
        yard = spreads.get("R->B0")
        for name, e in spreads.items():
            if yard and name.startswith("B0->") and e["median"] is not None \
                    and yard["median"] is not None:
                bound_med = max(F * yard["median"], e["floor_abs"] or 0.0)
                bound_p90 = max(F * (yard["p90"] or 0.0),
                                e["floor_abs"] or 0.0)
                e["accept_median"] = e["median"] <= bound_med
                e["accept_p90"] = (e["p90"] is not None
                                   and e["p90"] <= bound_p90)
                e["accepted"] = bool(e["accept_median"] and e["accept_p90"])
        d["check1_objf"] = spreads

        # check 1a: clustering + hop rates (declaration restated)
        accepted = [(a, k, hexf(rows[a][k]["objf_hex"]))
                    for a in arms for k in range(cfg.N_STARTS)
                    if conv(rows[a][k])
                    and hexf(rows[a][k]["objf_hex"]) is not None]
        gap = cfg.CLUSTER_GAP_FLOOR_FACTOR * cfg.OBJF_FLOOR_REL
        order = sorted(range(len(accepted)), key=lambda i: accepted[i][2])
        groups: list[list[int]] = []
        for i in order:
            if groups:
                prev = accepted[groups[-1][-1]][2]
                cur = accepted[i][2]
                denom = max(abs(prev), abs(cur))
                if denom and abs(cur - prev) / denom > gap:
                    groups.append([i])
                    continue
                groups[-1].append(i)
            else:
                groups.append([i])
        cluster_of = {(accepted[i][0], accepted[i][1]): ci
                      for ci, g in enumerate(groups) for i in g}
        hops = {}
        for name, (a, b) in pair_defs.items():
            if a not in rows or b not in rows:
                continue
            both = [k for k in range(cfg.N_STARTS)
                    if (a, k) in cluster_of and (b, k) in cluster_of]
            hops[name] = {
                "n_pairs": len(both),
                "n_hops": sum(1 for k in both
                              if cluster_of[(a, k)] != cluster_of[(b, k)])}
        d["check1a"] = {"n_clusters": len(groups),
                        "cluster_sizes": [len(g) for g in groups],
                        "hop_rates_per_pair": hops}

        # check 2: iteration multiplier, declared nearest-rank median
        iters: dict = {}
        for name, (a, b) in {"B0->B1": ("B0", "B1"),
                             "B0->B2": ("B0", "B2"),
                             "B0->B3": ("B0", "B3"),
                             "B0->R": ("B0", "R"),
                             "B2->B3": ("B2", "B3")}.items():
            if a not in rows or b not in rows:
                continue
            ratios, fev, dropped = [], [], []
            for k in range(cfg.N_STARTS):
                ra, rb = rows[a][k], rows[b][k]
                if not (conv(ra) and conv(rb)):
                    continue
                ia, ib = ra["iters"], rb["iters"]
                if ia and ib:
                    ratios.append(ib / ia)
                else:
                    dropped.append({"seed": k, f"{a}_iters": ia,
                                    f"{b}_iters": ib})
                ma, mb = ra["model_calls"], rb["model_calls"]
                if ma and mb:
                    fev.append(mb / ma)
            iters[name] = {
                "n_iter_pairs": len(ratios),
                "dropped": dropped,
                "median": rank_median(ratios),
                "median_statistics_diagnostic": (
                    statistics.median(ratios) if ratios else None),
                "bound_1p05_met": (rank_median(ratios) is not None
                                   and rank_median(ratios)
                                   <= cfg.ITER_RATIO_MAX),
                "model_call_ratio_median": rank_median(fev),
            }
        d["check2_iters"] = iters

        # check 3: c93 at accepted optima
        c93: dict = {}
        for a in ("B1", "B2", "B3"):
            if a not in rows:
                continue
            res = sorted(abs(r["c93"]["residual_s"])
                         for r in rows[a]
                         if conv(r) and r.get("c93")
                         and r["c93"].get("residual_s") is not None)
            c93[a] = {"n": len(res),
                      "abs_residual_s_median": rank_median(res),
                      "abs_residual_s_max": res[-1] if res else None}
        d["check3_c93"] = c93

        # check 4: identical-set cost sums
        cost: dict = {}
        for variant, keep in (
                ("identical_ok_set",
                 lambda r: r.get("status") == "ok"),
                ("identical_converged_set", conv)):
            common = [k for k in range(cfg.N_STARTS)
                      if all(keep(rows[a][k]) for a in arms)]
            per_arm = {}
            for a in arms:
                ns = sum(rows[a][k]["node_solve"] or 0 for k in common)
                per_arm[a] = {"node_calls_solve_phase": ns}
            b0 = per_arm.get("B0")
            for a in arms:
                if b0 and b0["node_calls_solve_phase"]:
                    per_arm[a]["node_ratio_vs_B0"] = (
                        per_arm[a]["node_calls_solve_phase"]
                        / b0["node_calls_solve_phase"])
            cost[variant] = {"n_seeds": len(common), "per_arm": per_arm}
        d["check4_cost_sums"] = cost
        out[deck] = d
    return out


# ── verify ───────────────────────────────────────────────────────────────


def _match(label: str, a, b, mismatches: list) -> None:
    same = a == b
    if not same:
        mismatches.append(f"{label}: analysis {a!r} vs tally {b!r}")


def verify(result: dict, roots: dict | None = None) -> int:
    """Compare the independent recomputation against the committed tallies
    cell by cell.  Exit nonzero on any mismatch (the report cites numbers
    only after this passes).

    A run with no records checks zero cells; that is REPORTED as such and
    is not a pass — the caller decides whether zero cells is acceptable
    (before the campaign it is not: see ``roots_for``).
    """
    roots = roots or roots_for("campaign")
    mismatches: list[str] = []
    checked = 0

    pa_tally_p = roots["pa_tally"]
    if pa_tally_p.exists() and result["phase_a"]:
        t = jload(pa_tally_p)
        for deck, d in result["phase_a"].items():
            td = (t.get("per_deck") or {}).get(deck) or {}
            _match(f"A/{deck}/n_paired_ok", d["n_paired_ok"],
                   td.get("n_paired_ok"), mismatches)
            checked += 1
            for pair, e in d["count_ratios"].items():
                te = (td.get("count_ratios") or {}).get(pair) or {}
                _match(f"A/{deck}/count_ratio[{pair}]",
                       e["unweighted_count_ratio"],
                       te.get("unweighted_count_ratio"), mismatches)
                checked += 1
            for stat in ("whole_state", "restricted"):
                for a, dist in d["audit_similarity"][stat][
                        "distributions"].items():
                    tdist = (((td.get("audit_similarity") or {}).get(stat)
                              or {}).get("distributions") or {}).get(a) or {}
                    _match(f"A/{deck}/{stat}/{a}/median",
                           dist["median"], tdist.get("median"), mismatches)
                    _match(f"A/{deck}/{stat}/{a}/p90",
                           dist["p90"], tdist.get("p90"), mismatches)
                    checked += 2
            if d["restricted_recompute_mismatches"]:
                mismatches.append(
                    f"A/{deck}: recomputed restricted max differs from the "
                    f"runner's on "
                    f"{len(d['restricted_recompute_mismatches'])} runs")
            checked += 1
    elif result["phase_a"]:
        mismatches.append("phase A tally.json missing")

    pb_tally_p = roots["pb_tally"]
    if pb_tally_p.exists() and result["phase_b"]:
        t = jload(pb_tally_p)
        for deck, d in result["phase_b"].items():
            td = t.get(deck) or {}
            _match(f"B/{deck}/deck_invalid_seeds",
                   d["deck_invalid_seeds"]["seeds"],
                   (td.get("deck_invalid_seeds") or {}).get("seeds"),
                   mismatches)
            checked += 1
            for name, e in d["check1_objf"].items():
                te = (td.get("check1_objf_pairs") or {}).get(name) or {}
                _match(f"B/{deck}/check1[{name}]/median", e["median"],
                       te.get("median"), mismatches)
                _match(f"B/{deck}/check1[{name}]/p90", e["p90"],
                       te.get("p90"), mismatches)
                _match(f"B/{deck}/check1[{name}]/accepted",
                       e.get("accepted"), te.get("accepted"), mismatches)
                checked += 3
            for name, e in d["check2_iters"].items():
                te = (td.get("check2_iteration_multiplier") or {}).get(
                    name) or {}
                _match(f"B/{deck}/check2[{name}]/median", e["median"],
                       te.get("median"), mismatches)
                _match(f"B/{deck}/check2[{name}]/bound",
                       e["bound_1p05_met"], te.get("bound_1p05_met"),
                       mismatches)
                checked += 2
            _match(f"B/{deck}/check1a/n_clusters",
                   d["check1a"]["n_clusters"],
                   (td.get("check1a_clusters") or {}).get("n_clusters"),
                   mismatches)
            checked += 1
            for name, e in d["check1a"]["hop_rates_per_pair"].items():
                te = ((td.get("check1a_clusters") or {})
                      .get("hop_rates_per_pair") or {}).get(name) or {}
                _match(f"B/{deck}/hop[{name}]",
                       (e["n_pairs"], e["n_hops"]),
                       (te.get("n_pairs"), te.get("n_hops")), mismatches)
                checked += 1
            if d["forensics_incomplete_ok_records"]:
                mismatches.append(
                    f"B/{deck}: "
                    f"{len(d['forensics_incomplete_ok_records'])} ok "
                    f"records fail the G7 completeness contract")
            checked += 1
    elif result["phase_b"]:
        mismatches.append("phase B tally.json missing")

    print(f"\n--verify: {checked} cells checked, "
          f"{len(mismatches)} mismatches")
    for msg in mismatches:
        print(f"  MISMATCH {msg}")
    if checked == 0:
        print("  NOTE: zero cells checked — there are no records under "
              f"{roots['pa_records']} / {roots['pb_records']}.  This is "
              "not a verification; --mode smoke exercises the same "
              "recomputation against the machinery smokes.")
    return 1 if mismatches else 0


def teeth(result: dict, roots: dict) -> int:
    """The verifier's own teeth (protocol §12): a recomputation that
    DISAGREES with the committed tally must be refused.

    Each tooth doctors ONE cell of the recomputed result — never the
    records, never the tally on disk — and requires :func:`verify` to
    return nonzero and to name that cell.  A tooth that does not trip is
    reported as a FAIL, not silently passed over.
    """
    baseline = verify(result, roots)
    rows: list[dict] = []

    def tooth(name: str, mutate) -> None:
        doctored = copy.deepcopy(result)
        if not mutate(doctored):
            rows.append({"tooth": name, "applied": False,
                         "why": "no such cell in these records",
                         "trips": None})
            return
        rc = verify(doctored, roots)
        rows.append({"tooth": name, "applied": True, "trips": rc != 0})

    def _first_deck(r: dict, phase: str):
        return next(iter(r[phase].values())) if r.get(phase) else None

    def bump_paired_ok(r: dict) -> bool:
        d = _first_deck(r, "phase_a")
        if d is None:
            return False
        d["n_paired_ok"] += 1
        return True

    def scale_restricted_median(r: dict) -> bool:
        d = _first_deck(r, "phase_a")
        if d is None:
            return False
        dist = d["audit_similarity"]["restricted"]["distributions"]
        arm = next((a for a, v in dist.items() if v["median"]), None)
        if arm is None:
            return False
        dist[arm]["median"] = dist[arm]["median"] * 1.5
        return True

    def bump_count_ratio(r: dict) -> bool:
        d = _first_deck(r, "phase_a")
        if d is None or not d["count_ratios"]:
            return False
        pair = next(iter(d["count_ratios"]))
        cur = d["count_ratios"][pair]["unweighted_count_ratio"]
        if cur is None:
            return False
        d["count_ratios"][pair]["unweighted_count_ratio"] = cur + 1e-12
        return True

    def flag_restricted_mismatch(r: dict) -> bool:
        d = _first_deck(r, "phase_a")
        if d is None:
            return False
        d["restricted_recompute_mismatches"] = ["A1u/start001"]
        return True

    def bump_iter_median(r: dict) -> bool:
        d = _first_deck(r, "phase_b")
        if d is None or not d.get("check2_iters"):
            return False
        name = next(iter(d["check2_iters"]))
        cur = d["check2_iters"][name]["median"]
        if cur is None:
            return False
        d["check2_iters"][name]["median"] = cur * 1.5
        return True

    tooth("phase_a n_paired_ok +1", bump_paired_ok)
    tooth("phase_a restricted median x1.5", scale_restricted_median)
    tooth("phase_a unweighted count ratio +1e-12", bump_count_ratio)
    tooth("phase_a restricted-recompute mismatch injected",
          flag_restricted_mismatch)
    tooth("phase_b check-2 median x1.5", bump_iter_median)

    applied = [r for r in rows if r["applied"]]
    tripped = [r for r in applied if r["trips"]]
    verdict = ("PASS" if baseline == 0 and applied and
               len(tripped) == len(applied) else "FAIL")
    print("\n--teeth: the verifier's own teeth "
          f"({len(tripped)}/{len(applied)} applied teeth trip; "
          f"baseline rc={baseline}) — {verdict}")
    for r in rows:
        state = ("trips" if r["trips"] else
                 ("DOES NOT TRIP" if r["applied"] else
                  f"not applied ({r['why']})"))
        print(f"    {r['tooth']:52s} {state}")
    rec = {"mode": result.get("mode"), "baseline_verify_rc": baseline,
           "teeth": rows, "verdict": verdict,
           "what": ("each tooth doctors one recomputed cell and requires "
                    "--verify to refuse it; the records and the on-disk "
                    "tallies are never modified")}
    (roots["out"].parent / (roots["out"].stem + "_teeth.json")).write_text(
        json.dumps(rec, indent=1))
    return 0 if verdict == "PASS" else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true",
                    help="compare the recomputation against the committed "
                         "tallies and exit nonzero on any mismatch")
    ap.add_argument("--teeth", action="store_true",
                    help="run --verify, then the verifier's own teeth: "
                         "doctored recomputations that must each be "
                         "refused (protocol §12)")
    ap.add_argument("--mode", choices=("campaign", "smoke"),
                    default="campaign",
                    help="which records to recompute from: 'campaign' (the "
                         "default, A42's) or 'smoke' (the machinery smokes, "
                         "so --verify is exercisable before the campaign "
                         "exists; smoke numbers are never measurements)")
    args = ap.parse_args()

    roots = roots_for(args.mode)
    result = {"mode": args.mode,
              "phase_a": phase_a(roots["pa_records"]),
              "phase_b": phase_b(roots["pb_records"]),
              "declared": {"F": F, "iter_ratio_max": cfg.ITER_RATIO_MAX,
                           "tau": cfg.TAU, "delta": cfg.DELTA,
                           "n_starts": cfg.N_STARTS,
                           "objf_floor_rel": cfg.OBJF_FLOOR_REL,
                           "cluster_gap_floor_factor":
                               cfg.CLUSTER_GAP_FLOOR_FACTOR,
                           "median_construction": cfg.MEDIAN_CONSTRUCTION}}
    out = roots["out"]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=1))
    print(f"written: {out}  (mode: {args.mode})\n")

    for deck, d in result["phase_a"].items():
        sim = d["audit_similarity"]
        line = " ".join(
            f"{a}:med={v['median'] if v['median'] is None else format(v['median'], '.3g')}"
            for a, v in sim["restricted"]["distributions"].items())
        print(f"[A] {deck}: paired_ok={d['n_paired_ok']} restricted {line} "
              f"recompute_mismatches="
              f"{len(d['restricted_recompute_mismatches'])} "
              f"stamps={d['provenance_stamps']}")
    for deck, d in result["phase_b"].items():
        print(f"[B] {deck}: invalid_seeds={d['deck_invalid_seeds']['n']} "
              f"stamps={d['provenance_stamps']}")
        for name, e in d["check1_objf"].items():
            print(f"    objf {name:7s} n={e['n']:2d} med={e['median']} "
                  f"p90={e['p90']} floor={e['floor_abs']} "
                  f"accept={e.get('accepted', '-')}")
        for name, e in d["check2_iters"].items():
            print(f"    iter {name:7s} n={e['n_iter_pairs']:2d} "
                  f"med(nearest-rank)={e['median']} "
                  f"(statistics.median diagnostic "
                  f"{e['median_statistics_diagnostic']}) "
                  f"bound_met={e['bound_1p05_met']}")

    if args.teeth:
        return teeth(result, roots)
    if args.verify:
        return verify(result, roots)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
