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
                    "prime_calls": m.get("n_prime_calls"),
                    "spe": m.get("sweeps_per_eval"),
                    "xcs": (m.get("exact") or {}).get("xcs"),
                    "itvar_names": m.get("itvar_names"),
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
            # EXPERIMENT_PLAN.md §4.2 check 1, restated from the plan text
            # (commit 29f642a1, pre-campaign): the accepted statistic is the
            # PER-PAIR RELATIVE difference
            #     r = |d norm_objf| / max(|objf_a|, |objf_b|)
            # accepted against  r_q <= max(F x yardstick_q, floor)  with the
            # PLAIN declared relative floor 1e-6 (O3, option A).  Until
            # orchestrator commit A42 this function recomputed an ABSOLUTE
            # delta against an ensemble-median-scaled floor -- the superseded
            # construction A41 reported and adjudication 10a2ff36 removed
            # from phase_b.py but not from here (I-18).  The absolute delta is
            # published beside, never accepted against.
            deltas, absolute_deltas, base_abs = [], [], []
            for k in range(cfg.N_STARTS):
                ra, rb = rows[a][k], rows[b][k]
                if conv(ra) and conv(rb):
                    fa, fb = hexf(ra["objf_hex"]), hexf(rb["objf_hex"])
                    if fa is not None and fb is not None:
                        denom = max(abs(fa), abs(fb))
                        deltas.append(abs(fb - fa) / denom if denom else 0.0)
                        absolute_deltas.append(abs(fb - fa))
                        base_abs.append(abs(fa))
            spreads[name] = {"n": len(deltas),
                             "statistic": ("per-pair relative: "
                                           "|d norm_objf| / "
                                           "max(|objf_a|, |objf_b|)"),
                             "median": rank_median(deltas),
                             "median_statistics_diagnostic": (
                                 statistics.median(deltas)
                                 if deltas else None),
                             "p90": p90(deltas),
                             "max": max(deltas) if deltas else None,
                             "floor_rel": cfg.OBJF_FLOOR_REL,
                             # beside; never the acceptance statistic
                             "absolute_median": rank_median(absolute_deltas),
                             "absolute_p90": p90(absolute_deltas),
                             "absolute_max": (max(absolute_deltas)
                                              if absolute_deltas else None),
                             "base_arm_abs_objf_median": rank_median(base_abs)}
        yard = spreads.get("R->B0")
        for name, e in spreads.items():
            if yard and name.startswith("B0->") and e["median"] is not None \
                    and yard["median"] is not None:
                bound_med = max(F * yard["median"], cfg.OBJF_FLOOR_REL)
                bound_p90 = max(F * (yard["p90"] or 0.0),
                                cfg.OBJF_FLOOR_REL)
                e["accept_median"] = e["median"] <= bound_med
                e["accept_p90"] = (e["p90"] is not None
                                   and e["p90"] <= bound_p90)
                e["bounds"] = {"median": bound_med, "p90": bound_p90}
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
        # EXPERIMENT_PLAN.md §4.2 check 1a, final sentence: "Within-cluster
        # agreement (check 1's statistics over same-cluster pairs) is
        # published beside the all-pairs construction."  Neither phase_b.py's
        # tally nor this recomputation implemented it before A42 (I-19) --
        # the same class of plan-vs-harness gap as I-18.  It is a declared
        # REPORTING rule with no acceptance threshold, so it is published
        # beside and never accepted against; check 1's verdict stays on the
        # all-pairs construction declared above.
        within = {}
        for name, (a, b) in pair_defs.items():
            if a not in rows or b not in rows:
                continue
            wd, wabs = [], []
            n_excluded = 0
            for k in range(cfg.N_STARTS):
                if (a, k) not in cluster_of or (b, k) not in cluster_of:
                    continue
                if cluster_of[(a, k)] != cluster_of[(b, k)]:
                    n_excluded += 1
                    continue
                fa = hexf(rows[a][k]["objf_hex"])
                fb = hexf(rows[b][k]["objf_hex"])
                denom = max(abs(fa), abs(fb))
                wd.append(abs(fb - fa) / denom if denom else 0.0)
                wabs.append(abs(fb - fa))
            within[name] = {"n": len(wd),
                            "n_excluded_as_hops": n_excluded,
                            "median": rank_median(wd),
                            "p90": p90(wd),
                            "max": max(wd) if wd else None,
                            "absolute_median": rank_median(wabs)}
        # the same acceptance arithmetic, applied to the within-cluster
        # statistic, for comparison only -- NOT check 1's verdict
        wyard = within.get("R->B0")
        for name, e in within.items():
            if wyard and name.startswith("B0->") and e["median"] is not None \
                    and wyard["median"] is not None:
                e["would_accept"] = bool(
                    e["median"] <= max(F * wyard["median"],
                                       cfg.OBJF_FLOOR_REL)
                    and e["p90"] is not None
                    and e["p90"] <= max(F * (wyard["p90"] or 0.0),
                                        cfg.OBJF_FLOOR_REL))
        # ------------------------------------------------------------------
        # B2 vs B3 under the prime: is the trust step FREE?
        #
        # B2 keeps the outer verification loop; B3 removes it.  Both carry the
        # prime (O4).  If the outer loop's only remaining job was repairing
        # the first-call deficit the prime now prevents, removing it should
        # change nothing -- and "nothing" is testable exactly, per seed, on
        # integer iteration counts.  This is the sharp form of the plan's
        # pre-declared lad B2->B3 question, which asked only for a median.
        # ------------------------------------------------------------------
        if "B2" in rows and "B3" in rows:
            same_it, diff_it, same_objf = 0, [], 0
            for k in range(cfg.N_STARTS):
                ra, rb = rows["B2"][k], rows["B3"][k]
                if not (conv(ra) and conv(rb)):
                    continue
                ia, ib = ra.get("iters"), rb.get("iters")
                if ia == ib:
                    same_it += 1
                else:
                    diff_it.append({"seed": k, "B2": ia, "B3": ib})
                if ra.get("objf_hex") == rb.get("objf_hex"):
                    same_objf += 1
            n = same_it + len(diff_it)
            d["b2_b3_trust_step_identity"] = {
                "what": ("per-seed identity of optimiser iteration counts "
                         "between B2 (verified outer loop) and B3 (trust), "
                         "both primed, over both-converged pairs; and "
                         "bit-identity of the objective beside it"),
                "n_pairs": n,
                "n_iterations_identical": same_it,
                "n_objf_bit_identical": same_objf,
                "differing_pairs": diff_it,
                "all_identical": (n > 0 and not diff_it),
            }

        # ------------------------------------------------------------------
        # OPTIMALITY vs LOCATION.  Check 1 compares |d norm_objf| -- how good
        # the optimum is.  It says nothing about WHERE the arms landed: two
        # arms can agree on the objective to 1e-15 and sit at materially
        # different design points, because a flat or non-identified direction
        # costs nothing in the objective.  D6 forbids GATING on iteration
        # variables for exactly that reason ("some are not identified by the
        # problem and differ at an unchanged optimum"), so this is a
        # DIAGNOSTIC, published beside, never an acceptance -- and it is the
        # only thing in this report that speaks to point agreement.
        #
        # Statistic: over the same both-converged pairs check 1 uses, the max
        # over iteration variables of the per-variable relative difference
        # |dx| / max(|x_a|, |x_b|), on the UNSCALED vector (xcs), plus the
        # argmax variable's name.  Reported beside the pair's objective
        # difference and its cluster verdict, so "same objective" and "same
        # point" can be read apart.
        # ------------------------------------------------------------------
        point = {}
        for name, (a, b) in pair_defs.items():
            if a not in rows or b not in rows:
                continue
            per_pair = []
            for k in range(cfg.N_STARTS):
                ra, rb = rows[a][k], rows[b][k]
                if not (conv(ra) and conv(rb)):
                    continue
                xa, xb = ra.get("xcs"), rb.get("xcs")
                na = ra.get("itvar_names") or []
                nb = rb.get("itvar_names") or []
                if not xa or not xb or not na or not nb:
                    continue
                # Match by NAME, never by index: the lift ADDS an iteration
                # variable, so B1/B2/B3 carry one more than B0 and a
                # positional zip would either crash or silently compare
                # different variables.  Variables present on only one side
                # are counted and named, never compared.
                ma = {n: hexf(h) for n, h in zip(na, xa)}
                mb = {n: hexf(h) for n, h in zip(nb, xb)}
                shared = [n for n in na if n in mb]
                only_a = [n for n in na if n not in mb]
                only_b = [n for n in nb if n not in ma]
                worst, worst_name = 0.0, None
                for n_ in shared:
                    va, vb = ma[n_], mb[n_]
                    if va is None or vb is None:
                        continue
                    den = max(abs(va), abs(vb))
                    r = (abs(vb - va) / den) if den else 0.0
                    if r > worst:
                        worst, worst_name = r, n_
                fa, fb = hexf(ra["objf_hex"]), hexf(rb["objf_hex"])
                den = max(abs(fa), abs(fb))
                per_pair.append({
                    "seed": k,
                    "max_rel_point_diff": worst,
                    "argmax_itvar": worst_name,
                    "n_shared_itvars": len(shared),
                    "itvars_only_in_a": only_a,
                    "itvars_only_in_b": only_b,
                    "rel_objf_diff": (abs(fb - fa) / den) if den else 0.0,
                    "same_objf_cluster": (
                        cluster_of.get((a, k)) == cluster_of.get((b, k))
                        if ((a, k) in cluster_of and (b, k) in cluster_of)
                        else None),
                })
            vals = sorted(e["max_rel_point_diff"] for e in per_pair)
            same = [e for e in per_pair if e["same_objf_cluster"]]
            same_v = sorted(e["max_rel_point_diff"] for e in same)
            point[name] = {
                "what": ("DIAGNOSTIC, never an acceptance (D6): max over "
                         "iteration variables of |dx| / max(|x_a|,|x_b|) on "
                         "the unscaled vector, per both-converged pair"),
                "n": len(vals),
                "median": rank_median(vals),
                "p90": p90(vals),
                "max": vals[-1] if vals else None,
                "n_same_objf_cluster": len(same),
                "median_within_objf_cluster": rank_median(same_v),
                "p90_within_objf_cluster": p90(same_v),
                "max_within_objf_cluster": same_v[-1] if same_v else None,
                "argmax_itvar_census": {
                    n: sum(1 for e in per_pair if e["argmax_itvar"] == n)
                    for n in sorted({e["argmax_itvar"] for e in per_pair
                                     if e["argmax_itvar"]})},
                "per_pair": per_pair,
            }
        d["diagnostic_point_agreement"] = point

        # ------------------------------------------------------------------
        # I-17 instrumentation (EXPERIMENT_PLAN §5 amendment, pre-declared
        # before the campaign with BOTH outcomes named as results).
        #
        # The hypothesis: Phase A over-predicts B3's saving because a Phase A
        # evaluation is a HARDER object than an in-loop one -- the delta-stream
        # displaces run-constants and post-solve-owned outputs that no
        # optimiser-driven call after call 1 displaces (plan §3.2's regime
        # disclosure), so it needs more sweeps to converge.  sweeps_per_eval
        # measures sweeps per call_models in the SAME unit on both arms.
        # ------------------------------------------------------------------
        spe: dict = {}
        for arm in cfg.PHASE_B_ARMS:
            if arm not in rows:
                continue
            hist: dict[str, int] = {}
            n_ev = n_sw = 0
            n_runs = 0
            for r in rows[arm]:
                h = r.get("spe")
                if not h or not h.get("hist"):
                    continue
                n_runs += 1
                n_ev += h.get("n_evaluations") or 0
                n_sw += h.get("n_sweeps") or 0
                for k, v in h["hist"].items():
                    hist[k] = hist.get(k, 0) + v
            if not n_runs:
                continue
            # cross-check: the binned total must equal the summed evaluations
            binned = sum(hist.values())
            spe[arm] = {
                "n_runs_contributing": n_runs,
                "n_evaluations": n_ev,
                "n_sweeps": n_sw,
                "mean_sweeps_per_eval": (n_sw / n_ev) if n_ev else None,
                "hist": dict(sorted(hist.items(), key=lambda kv: int(kv[0]))),
                "binned_total_equals_n_evaluations": binned == n_ev,
            }
        d["i17_sweeps_per_eval"] = spe

        # the prime's own call count, published because D19 keeps it OUT of
        # node_calls by declaration (trap T11: a denominator that excludes a
        # real cost must name it).  A prime call is ONE set_fw_geometry(),
        # not a node; the ratio below is a count ratio, never a cost ratio,
        # and no conclusion here rests on it.
        prime: dict = {}
        for arm in cfg.PHASE_B_ARMS:
            if arm not in rows:
                continue
            ok = [r for r in rows[arm] if r.get("status") == "ok"]
            pc = sum((r.get("prime_calls") or 0) for r in ok)
            nc = sum((r.get("node_solve") or 0) for r in ok)
            mc = sum((r.get("model_calls") or 0) for r in ok)
            prime[arm] = {"n_ok": len(ok), "prime_calls": pc,
                          "node_calls": nc, "model_calls": mc,
                          "prime_calls_per_model_call": (pc / mc) if mc else None,
                          "prime_calls_over_node_calls": (pc / nc) if nc else None}
        d["prime_call_census"] = prime

        # B1->B2 diagnostic (NOT a declared pair): needed only to attribute
        # lad's check-1 failure, where B0->B1, B0->B2 and B0->B3 all report
        # the same statistic.  Post-hoc, published as a diagnostic.
        if "B1" in rows and "B2" in rows:
            dd = []
            for k in range(cfg.N_STARTS):
                ra, rb = rows["B1"][k], rows["B2"][k]
                if conv(ra) and conv(rb):
                    fa, fb = hexf(ra["objf_hex"]), hexf(rb["objf_hex"])
                    if fa is not None and fb is not None:
                        den = max(abs(fa), abs(fb))
                        dd.append(abs(fb - fa) / den if den else 0.0)
            d["diagnostic_B1_to_B2"] = {
                "what": ("post-hoc, not a declared pair: per-pair relative "
                         "|d objf| between B1 and B2, to attribute which "
                         "ladder rung introduces a check-1 disagreement"),
                "n": len(dd), "median": rank_median(dd), "p90": p90(dd),
                "max": max(dd) if dd else None}

        d["check1a"] = {"n_clusters": len(groups),
                        "cluster_sizes": [len(g) for g in groups],
                        "hop_rates_per_pair": hops,
                        "within_cluster_check1": within,
                        "within_cluster_note": (
                            "plan §4.2 check 1a: published beside the "
                            "all-pairs construction, never accepted "
                            "against; 'would_accept' is the same arithmetic "
                            "applied to same-cluster pairs, for comparison "
                            "only")}

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

        # §5.3 R-referenced iteration table (user request, 2026-09-07).
        # ONE seed set per deck -- seeds where R, B0 AND B3 all converged --
        # so a single n applies to every cell of a row.  The pairwise sets
        # in check 2 differ per pair (lad's B0->R has 12 seeds, its B0->B3
        # 11), which is why that table could never carry a total across
        # columns.  Cells are MEAN optimiser iterations per seed.  B3/R is
        # published twice because the two answer different questions and
        # can disagree in direction (lad): the ratio of means (== ratio of
        # sums over the same seeds; campaign cost) and the DECLARED
        # nearest-rank median of per-seed ratios with its [min, max] seed
        # bracket (typical seed), beside the count of seeds where B3 took
        # strictly more iterations than R.  Diagnostic beside check 2, never
        # an acceptance: the declared check-2 pair is B0->B3 and its bound
        # is on the median in ``check2_iters`` above.
        vs_r: dict = {}
        r_arms = ("R", "B0", "B3")
        if all(a in rows for a in r_arms):
            seeds = [k for k in range(cfg.N_STARTS)
                     if all(conv(rows[a][k]) and rows[a][k]["iters"]
                            for a in r_arms)]
            n = len(seeds)
            its = {a: [rows[a][k]["iters"] for k in seeds] for a in r_arms}
            per_seed = [its["B3"][i] / its["R"][i] for i in range(n)]
            vs_r = {
                "seed_construction": ("seeds where R, B0 and B3 ALL "
                                      "converged (status ok AND ifail == 1) "
                                      "and recorded iterations; one set per "
                                      "deck"),
                "n": n,
                "seeds": seeds,
                "mean_iters_per_seed": {a: (sum(its[a]) / n if n else None)
                                        for a in r_arms},
                "sum_iters": {a: sum(its[a]) for a in r_arms},
                "seed_bracket": {a: ([min(its[a]), max(its[a])] if n
                                     else None) for a in r_arms},
                "B3_over_R": {
                    "ratio_of_means": ((sum(its["B3"]) / sum(its["R"]))
                                       if n and sum(its["R"]) else None),
                    "per_seed_median": rank_median(per_seed),
                    "per_seed_min": min(per_seed) if per_seed else None,
                    "per_seed_max": max(per_seed) if per_seed else None,
                    "n_B3_worse_than_R": sum(1 for r in per_seed
                                             if r > 1.0),
                    "median_construction": cfg.MEDIAN_CONSTRUCTION,
                },
            }
        d["check2_iters_vs_R"] = vs_r

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

    # A tooth for module_sweeps' within-group uniformity premise, which
    # --verify cannot reach: it is a refusal inside the recomputation, not a
    # cell compared against a tally.  Doctor one node of a group so its
    # members disagree, and require _sweeps to refuse rather than average.
    def uniformity_tooth() -> bool:
        mod = {"physics": "M1", "plasma_geom": "M1"}
        good = {"physics": 3, "plasma_geom": 3}
        try:
            _sweeps(good, mod, "tooth/baseline")
        except SystemExit:
            return False          # the undoctored case must NOT refuse
        try:
            _sweeps({"physics": 3, "plasma_geom": 4}, mod, "tooth/doctored")
        except SystemExit:
            return True
        return False

    rows.append({"tooth": "module_sweeps within-group uniformity",
                 "applied": True, "trips": uniformity_tooth()})

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


def dsm_blocks(pa_records: Path | None, pb_records: Path | None) -> dict:
    """Node-call counts decomposed by **collapsed-DSM module**, not by the
    intervention's own block/post-solve grouping (user request, 2026-09-07).

    The two groupings differ and the difference is not cosmetic: the tally's
    ``per_block_*`` tables assign a node to ``post_solve`` FIRST and to its
    block second, so ``vacuum`` (DSM module **M3**) and ``costs`` /
    ``water_use`` (DSM module **FF**) are pooled into one "post_solve" row
    that spans three different DSM modules.  Aligning to the DSM lets a block
    row be read against the collapsed DSM's own rows.

    Row counts come from the committed ``dsm_node_map.json`` (decision D8):
    M1 24, M2 10, M3 12, PULSE 1, FF 5 — 52 executed in a sweep, of 56 total
    (rows 1/2/3/56 are drivers: COOR_SingleRun, VMCON, MDA_Idempotence,
    MDA_Output).

    **Why the per-block ratio is the fair comparison, and the total is not.**
    Within one block both arms execute the same node set, so that block's
    ratio is a pure *sweep* ratio and is INVARIANT to the unit — counting
    model calls or DSM rows gives the same number.  The TOTAL is a
    node-weighted average of those ratios and is therefore unit-DEPENDENT:
    re-weighting by DSM rows moves it, because M1 is 2 model calls but 24 DSM
    rows.  Both weightings are computed here so the size of that dependence
    is published rather than assumed away.
    """
    nm_p = cfg.DATA / "dsm_node_map.json"
    if not nm_p.exists():
        return {}
    nm = jload(nm_p)
    mod = {n: v.get("module") for n, v in (nm.get("nodes") or {}).items()
           if v.get("kind") == "model_call"}
    rows = (nm.get("units") or {}).get("dsm_rows") or {}
    order = ("M1", "M2", "M3", "PULSE", "FF")

    def _agg(census: dict) -> dict:
        out: dict[str, int] = {}
        for n, c in census.items():
            out.setdefault(mod.get(n, f"UNMAPPED:{n}"), 0)
            out[mod.get(n, f"UNMAPPED:{n}")] += c
        return out

    def _weighted(per_mod: dict, per_mod_nodes: dict) -> float | None:
        """Total re-expressed in DSM row-executions: for each module,
        (node calls / executing nodes) * dsm rows."""
        tot = 0.0
        for m, c in per_mod.items():
            nn = per_mod_nodes.get(m)
            r = rows.get(m)
            if not nn or not r:
                return None
            tot += (c / nn) * r
        return tot

    out: dict = {"row_counts": {m: rows.get(m) for m in order},
                 "note": ("counts grouped by collapsed-DSM module (D8), NOT "
                          "by the intervention's post-solve grouping; "
                          "vacuum is M3 and costs/water_use are FF"),
                 "phase_a": {}, "phase_b": {}}

    # ---- Phase A ----------------------------------------------------------
    if pa_records and (pa_records / "campaign.json").exists():
        camp = jload(pa_records / "campaign.json")
        for deck in camp["decks"]:
            per_arm, per_arm_nodes, per_arm_split = {}, {}, {}
            for arm in camp["arms"]:
                agg, nodes, split = {}, {}, {}
                for k in camp["seeds"]:
                    mp = pa_records / deck / arm / f"start{k:03d}" / "metrics.json"
                    if not mp.exists():
                        continue
                    m = jload(mp)
                    if m.get("status") != "ok":
                        continue
                    cen = ((m.get("node_census") or {}).get("counted")
                           or (m.get("node_census") or {})
                           .get("per_node_counted_through_Caller_node") or {})
                    for n, c in cen.items():
                        mm = mod.get(n, f"UNMAPPED:{n}")
                        agg[mm] = agg.get(mm, 0) + c
                        nodes.setdefault(mm, set()).add(n)
                        if n in _SPLIT_NODES:
                            split[n] = split.get(n, 0) + c
                if agg:
                    per_arm[arm] = agg
                    per_arm_nodes[arm] = {m_: len(v) for m_, v in nodes.items()}
                    per_arm_split[arm] = dict(split)
            if per_arm:
                d = _finish(per_arm, per_arm_nodes, order, rows, "A0",
                            _weighted)
                d["per_node_split"] = per_arm_split
                out["phase_a"][deck] = d

    # ---- Phase B ----------------------------------------------------------
    if pb_records and pb_records.exists():
        for deck in cfg.DECKS:
            arms = [a for a in cfg.PHASE_B_ARMS
                    if (pb_records / deck / a).exists()]
            if not arms:
                continue
            ok = [k for k in range(cfg.N_STARTS)
                  if all((pb_records / deck / a / f"start{k:03d}"
                          / "metrics.json").exists()
                         and jload(pb_records / deck / a / f"start{k:03d}"
                                   / "metrics.json").get("status") == "ok"
                         for a in arms)]
            per_arm, per_arm_nodes, per_arm_split = {}, {}, {}
            for arm in arms:
                agg, nodes, split = {}, {}, {}
                for k in ok:
                    m = jload(pb_records / deck / arm / f"start{k:03d}"
                              / "metrics.json")
                    cen = ((m.get("node_census") or {})
                           .get("per_node_counted_through_Caller_node") or {})
                    for n, c in cen.items():
                        mm = mod.get(n, f"UNMAPPED:{n}")
                        agg[mm] = agg.get(mm, 0) + c
                        nodes.setdefault(mm, set()).add(n)
                        if n in _SPLIT_NODES:
                            split[n] = split.get(n, 0) + c
                per_arm[arm] = agg
                per_arm_nodes[arm] = {m_: len(v) for m_, v in nodes.items()}
                per_arm_split[arm] = dict(split)
            d = _finish(per_arm, per_arm_nodes, order, rows, "B0", _weighted)
            d["per_node_split"] = per_arm_split
            d["n_seeds"] = len(ok)
            d["seeds"] = ok
            out["phase_b"][deck] = d
    return out


#: Nodes where the STATIC DSM module assignment and the MEASURED liveness
#: derivation disagree, or where the split matters to read a table.  ``vacuum``
#: is DSM module **M3** (rows 40-51, "Plant") but A33's backward crawl puts it
#: in the post-solve set: its 5 census writes have exactly one external read
#: site, inside ``costs`` -- itself a post-solve peer.  So the DSM's
#: feed-forward tail (``costs``, ``water_use``) and the measured feed-forward
#: set (``costs``, ``water_use``, ``vacuum``, +``pulse`` on st) differ by
#: ``vacuum``.  Both groupings are published; neither is silently preferred.
_SPLIT_NODES = ("vacuum", "costs", "water_use", "pulse")


def _finish(per_arm, per_arm_nodes, order, rows, base, weighted):
    """Ratios against *base*, per module, plus both total weightings."""
    d: dict = {"per_arm": per_arm, "executing_nodes": per_arm_nodes,
               "ratios_vs_" + base: {}, "totals": {}}
    b = per_arm.get(base) or {}
    for arm, agg in per_arm.items():
        d["ratios_vs_" + base][arm] = {
            m: ((agg.get(m, 0) / b[m]) if b.get(m) else None)
            for m in order if m in b or m in agg}
        node_tot = sum(agg.values())
        row_tot = weighted(agg, per_arm_nodes.get(arm) or {})
        d["totals"][arm] = {
            "node_calls": node_tot,
            "row_executions": row_tot,
            "node_weighted_ratio": (node_tot / sum(b.values())
                                    if b else None),
            "row_weighted_ratio": (
                (row_tot / weighted(b, per_arm_nodes.get(base) or {}))
                if b and row_tot is not None
                and weighted(b, per_arm_nodes.get(base) or {}) else None),
        }
    return d


#: DSM row counts per module (D8, ``dsm_node_map.json``): the number of
#: *models* the collapsed DSM resolves inside each module.  ``M3`` holds 12
#: rows; ``vacuum`` is one of its nodes but per-node row attribution is NOT
#: available in this repository (trap T9 forbids reading the dependency
#: analysis repo's exports live, and only ``build``/``fw``/``power``/``pulse``
#: carry a pinned row).  So ``vacuum``'s share of M3's 12 rows is an
#: assumption, and the total is published as a BRACKET over v in {0, 1}
#: rather than as a point: v = 0 counts ``vacuum`` with M3 (it then inherits
#: M3's sweep count, which the measured liveness says it does not have),
#: v = 1 gives it a row of its own.  Every per-module ratio is unaffected.
_VACUUM_ROW_CASES = (0, 1)


def _module_group(node: str, mod: dict) -> str | None:
    """Model node -> table row group.  ``vacuum`` is split out of M3 because
    the intervention hoists it while M3's other members keep iterating: the
    two have different call counts in every block arm, and a group whose
    members differ is not a sweep."""
    if node == "vacuum":
        return "vacuum"
    m = mod.get(node)
    return "M3 live" if m == "M3" else m


def _sweeps(census: dict, mod: dict, where: str) -> dict:
    """Per-node census -> {group: sweeps for that group}.

    REFUSES if any group's members disagree.  This is the premise the whole
    table rests on: within a group every model is executed the same number of
    times, so the cell is a *sweep count* and its ratio is invariant to
    whether one counts model calls or DSM rows.  Measured to hold in 100 % of
    V3 records; if it ever stops holding the sweep unit is invalid and this
    must fail loudly rather than average over the difference.
    """
    byg: dict[str, dict] = {}
    for n, c in census.items():
        g = _module_group(n, mod)
        if g is None:
            raise SystemExit(f"REFUSED: {where}: node {n!r} is in no DSM "
                             f"module; unmapped nodes are named, never pooled")
        byg.setdefault(g, {})[n] = c
    out = {}
    for g, dd in byg.items():
        vals = set(dd.values())
        if len(vals) != 1:
            raise SystemExit(
                f"REFUSED: {where}: group {g} is not uniform: {dd}. "
                f"The sweep unit assumes every model in a group runs the "
                f"same number of times; it does not here, so no cell of "
                f"this table is meaningful.")
        out[g] = vals.pop()
    return out


def _ratio_stats(num: list, den: list) -> dict:
    """Pooled ratio (sum/sum, the total-work statistic) beside the per-run
    distribution.  The two answer different questions and can disagree
    sharply when the per-run cost is heavy-tailed, so both are published."""
    if not den or not sum(den):
        return {"pooled": None, "per_seed_median": None, "per_seed_min": None,
                "per_seed_max": None, "n_worse_than_base": None, "n": len(den)}
    rs = sorted(n / d for n, d in zip(num, den) if d)
    return {"pooled": sum(num) / sum(den),
            "per_seed_median": statistics.median(rs),
            "per_seed_min": rs[0], "per_seed_max": rs[-1],
            "n_worse_than_base": sum(1 for r in rs if r > 1.0),
            "n": len(rs)}


def module_sweeps(pa_records: Path | None, pb_records: Path | None) -> dict:
    """Per-module **sweeps per run** with a seed bracket, and the total as a
    model-weighted average (user request, 2026-09-07).

    Three changes from ``dsm_blocks``, which this supersedes as the report's
    §4.5 / §5.5.1 source:

    1. **Cells are per run, not summed over the seed set.**  The sums hid two
       different denominators (Phase A 25; Phase B 22 / 20 / 25 for
       identical-ok, 22 / 11 / 22 for identical-converged) and invited
       cross-reading rows that are not comparable in magnitude.
    2. **Cells are sweeps, not node calls.**  Within a group every model runs
       the same number of times (refused above if not), so the cell is the
       number of times that group was executed, and ``total calls =
       sum over groups of sweeps x models``.  A group's ratio is then
       unit-invariant; only the total depends on the unit.
    3. **Each cell carries its seed bracket, and each ratio its per-run
       distribution** including the count of runs where the arm is WORSE than
       the baseline.  A pooled ratio can be well below 1 while individual
       runs are above it, and on two of three decks it is.
    """
    nm_p = cfg.DATA / "dsm_node_map.json"
    if not nm_p.exists():
        return {}
    nm = jload(nm_p)
    mod = {n: v.get("module") for n, v in (nm.get("nodes") or {}).items()
           if v.get("kind") == "model_call"}
    m_rows = {m: (v.get("n_dsm_rows") or 0)
              for m, v in (nm.get("modules") or {}).items()}
    order = ("M1", "M2", "M3 live", "vacuum", "PULSE", "FF")

    def models_per_group(v: int) -> dict:
        return {"M1": m_rows.get("M1", 0), "M2": m_rows.get("M2", 0),
                "M3 live": m_rows.get("M3", 0) - v, "vacuum": v,
                "PULSE": m_rows.get("PULSE", 0), "FF": m_rows.get("FF", 0)}

    def build(records: Path, deck: str, arms: list, seeds: list,
              base: str, census_key: str) -> dict:
        per: dict = {}
        for arm in arms:
            acc = {g: [] for g in order}
            for k in seeds:
                mp = records / deck / arm / f"start{k:03d}" / "metrics.json"
                m = jload(mp)
                cen = ((m.get("node_census") or {}).get(census_key) or {})
                sw = _sweeps(cen, mod, f"{deck}/{arm}/start{k:03d}")
                for g in order:
                    acc[g].append(sw.get(g, 0))
            per[arm] = acc
        d: dict = {"n_seeds": len(seeds), "seeds": list(seeds),
                   "models_per_group": {f"v={v}": models_per_group(v)
                                        for v in _VACUUM_ROW_CASES},
                   "base": base, "per_arm": {}, "totals": {}}
        for arm in arms:
            cells = {}
            for g in order:
                vals = per[arm][g]
                cells[g] = {
                    "sweeps_per_run_mean": statistics.mean(vals),
                    "sweeps_per_run_min": min(vals),
                    "sweeps_per_run_max": max(vals),
                    "sweeps_sum": sum(vals),
                    "ratio_vs_base": _ratio_stats(vals, per[base][g]),
                }
            d["per_arm"][arm] = cells
            tot = {}
            for v in _VACUUM_ROW_CASES:
                mg = models_per_group(v)
                mine = [sum(per[arm][g][i] * mg[g] for g in order)
                        for i in range(len(seeds))]
                theirs = [sum(per[base][g][i] * mg[g] for g in order)
                          for i in range(len(seeds))]
                tot[f"v={v}"] = {
                    "total_calls_per_run_mean": statistics.mean(mine),
                    "total_calls_per_run_min": min(mine),
                    "total_calls_per_run_max": max(mine),
                    "ratio_vs_base": _ratio_stats(mine, theirs)}
            d["totals"][arm] = tot
        return d

    out: dict = {"note": ("per-module SWEEPS PER RUN; a group's ratio is "
                          "unit-invariant, the total is not; the total is "
                          "bracketed over vacuum's unknown DSM row count "
                          "(trap T9)"),
                 "vacuum_row_cases": list(_VACUUM_ROW_CASES),
                 "phase_a": {}, "phase_b": {}}

    if pa_records and (pa_records / "campaign.json").exists():
        camp = jload(pa_records / "campaign.json")
        for deck in camp["decks"]:
            seeds = [k for k in camp["seeds"]
                     if all((pa_records / deck / a / f"start{k:03d}"
                             / "metrics.json").exists()
                            and jload(pa_records / deck / a / f"start{k:03d}"
                                      / "metrics.json").get("status") == "ok"
                            for a in camp["arms"])]
            if seeds:
                out["phase_a"][deck] = build(
                    pa_records, deck, list(camp["arms"]), seeds, "A0",
                    "counted")

    if pb_records and pb_records.exists():
        for deck in cfg.DECKS:
            arms = [a for a in cfg.PHASE_B_ARMS
                    if (pb_records / deck / a).exists()]
            if not arms:
                continue
            ok = [k for k in range(cfg.N_STARTS)
                  if all((pb_records / deck / a / f"start{k:03d}"
                          / "metrics.json").exists()
                         and jload(pb_records / deck / a / f"start{k:03d}"
                                   / "metrics.json").get("status") == "ok"
                         for a in arms)]
            if ok:
                out["phase_b"][deck] = build(
                    pb_records, deck, arms, ok, "B0",
                    "per_node_counted_through_Caller_node")
    return out


def exclusion_stakes(pa_records: Path | None) -> dict:
    """What the Phase A headline WOULD read if the restricted audit's
    exclusion set were wrong -- per excluded namespace, from each run's own
    ``audit_residual.json`` (user question 2026-09-07, settled by an
    independent runtime read census: ``vacuum`` is feed-forward on all three
    decks, its only reader being ``costs``, itself post-solve).

    The point is not that these components move -- they are excluded
    precisely because nothing live reads them, so their movement is the
    designed signature of the post-solve hoist.  The point is HOW MUCH they
    move: it quantifies what the exclusion set is load-bearing for.  If any
    of these were wrongly excluded, the restricted headline would read the
    number below instead of ~1e-8.
    """
    out: dict = {}
    if not pa_records or not (pa_records / "campaign.json").exists():
        return out
    camp = jload(pa_records / "campaign.json")
    for deck in camp["decks"]:
        excl = excluded_keys(deck)
        ns = sorted({k.split(".", 1)[0] for k in excl})
        d: dict = {"n_excluded": len(excl),
                   "excluded_namespaces": {n: sum(1 for k in excl
                                                  if k.startswith(n + "."))
                                           for n in ns},
                   "per_arm": {}}
        for arm in camp["arms"]:
            per_ns_max: dict[str, list] = {n: [] for n in ns}
            all_excl_max: list = []
            restricted_max: list = []
            for k in camp["seeds"]:
                ap = pa_records / deck / arm / f"start{k:03d}" / "audit_residual.json"
                if not ap.exists():
                    continue
                a = jload(ap)
                sc = a.get("scaled") or {}
                for n in ns:
                    vals = [v for key, v in sc.items()
                            if key.startswith(n + ".") and key in excl
                            and isinstance(v, (int, float))]
                    per_ns_max[n].append(max(vals) if vals else 0.0)
                ev = [v for key, v in sc.items() if key in excl
                      and isinstance(v, (int, float))]
                all_excl_max.append(max(ev) if ev else 0.0)
                kv = [v for key, v in sc.items() if key not in excl
                      and isinstance(v, (int, float))]
                restricted_max.append(max(kv) if kv else 0.0)
            d["per_arm"][arm] = {
                "n_runs": len(all_excl_max),
                "restricted_p90": p90(sorted(restricted_max)),
                "excluded_all_p90": p90(sorted(all_excl_max)),
                "excluded_by_namespace_p90": {
                    n: p90(sorted(v)) for n, v in per_ns_max.items() if v},
                "excluded_by_namespace_n_nonzero_runs": {
                    n: sum(1 for x in v if x > 0)
                    for n, v in per_ns_max.items() if v},
            }
        out[deck] = d
    return out


def transfer(pa: dict, pb: dict, roots: dict) -> dict:
    """I-17: Phase A's per-call ratio against Phase B's realised end-to-end
    ratio (EXPERIMENT_PLAN §5, amended pre-campaign).

    The plan is explicit that **no V3 number is derived through the
    transfer** — every end-to-end figure is the measured node-call ratio.
    This function exists only to republish the over- or under-prediction
    beside V3's own numbers, as §5 requires, and to carry the sweeps_per_eval
    comparison that V2 could not make.

    Phase A's A0->A1 unweighted count ratio is the per-call prediction;
    Phase B's B0->B3 node-call ratio over the identical-CONVERGED set is the
    realised figure.  Both come from the committed tallies this same script
    verifies cell by cell.
    """
    out: dict = {}
    pa_tally_p, pb_tally_p = roots["pa_tally"], roots["pb_tally"]
    if not (pa_tally_p.exists() and pb_tally_p.exists()):
        return out
    ta, tb = jload(pa_tally_p), jload(pb_tally_p)
    for deck in cfg.DECKS:
        tda = (ta.get("per_deck") or {}).get(deck) or {}
        tdb = tb.get(deck) or {}
        cr = (tda.get("count_ratios") or {}).get("A0->A1") or {}
        pred = cr.get("unweighted_count_ratio")
        row: dict = {"phase_a_per_call_ratio_A0_to_A1": pred}
        for setname in ("identical_ok_set", "identical_converged_set"):
            per = (((tdb.get("check4_cost_sums") or {}).get(setname) or {})
                   .get("per_arm") or {})
            b0 = (per.get("B0") or {}).get("node_calls_solve_phase")
            b3 = (per.get("B3") or {}).get("node_calls_solve_phase")
            realised = (b3 / b0) if (b0 and b3) else None
            row[setname] = {
                "n_seeds": (((tdb.get("check4_cost_sums") or {})
                             .get(setname) or {}).get("n_seeds")),
                "realised_B0_to_B3_node_ratio": realised,
                "over_prediction_fraction": (
                    (realised / pred - 1.0)
                    if (realised is not None and pred) else None),
            }
        # sweeps per evaluation: Phase A's evaluation against an in-loop one,
        # same unit.  Phase A's sweep count is per arm in its own tally.
        swa = {}
        for arm in ("A0", "A1u", "A1"):
            vals = [v.get("sweeps")
                    for v in ((tda.get("per_run") or {}).get(arm) or {}).values()
                    if v.get("status") == "ok" and v.get("sweeps")]
            if vals:
                swa[arm] = {"n": len(vals), "mean": sum(vals) / len(vals),
                            "min": min(vals), "max": max(vals)}
        spe = (pb.get(deck) or {}).get("i17_sweeps_per_eval") or {}
        row["sweeps_per_eval"] = {
            "phase_a": swa,
            "phase_b_mean": {a: e["mean_sweeps_per_eval"]
                             for a, e in spe.items()},
            "phase_a_over_phase_b_flat": (
                (swa["A0"]["mean"] / spe["B0"]["mean_sweeps_per_eval"])
                if ("A0" in swa and "B0" in spe
                    and spe["B0"]["mean_sweeps_per_eval"]) else None),
            "phase_a_over_phase_b_block": (
                (swa["A1"]["mean"] / spe["B3"]["mean_sweeps_per_eval"])
                if ("A1" in swa and "B3" in spe
                    and spe["B3"]["mean_sweeps_per_eval"]) else None),
        }
        out[deck] = row
    return out


#: Deck abbreviations used in the report's tables (user request 2026-09-07:
#: ``nof`` -> ``tok``).  The deck IDENTIFIERS are unchanged everywhere else --
#: this is a display label only.
DECK_ABBR = {"large_tokamak_nof": "tok",
             "low_aspect_ratio_DEMO": "lad",
             "st_regression": "st"}


def _cell(c: dict) -> str:
    """A sweeps-per-run cell: mean, plus its seed bracket when the runs are
    not all identical.  A bare integer means every run agreed exactly."""
    m, lo, hi = (c["sweeps_per_run_mean"], c["sweeps_per_run_min"],
                 c["sweeps_per_run_max"])
    if float(m).is_integer() or m >= 100:
        s = f"{m:.0f}"
    else:
        s = f"{m:.2f}".rstrip("0")
    return s if lo == hi else f"{s} [{lo},{hi}]"


def _rat(r: dict, bold: bool = False) -> str:
    if r.get("pooled") is None:
        return "—"
    s = f"{r['pooled']:.3f}"
    return f"**{s}**" if bold else s


def _spread(r: dict, n: int) -> tuple:
    if r.get("pooled") is None:
        return "—", "—"
    return (f"{r['per_seed_median']:.3f} "
            f"[{r['per_seed_min']:.3f}, {r['per_seed_max']:.3f}]",
            f"{r['n_worse_than_base']}/{n}")


def print_tables(res: dict) -> None:
    """Emit the report's §5.3, §4.5 and §5.5.1 tables as markdown, so the
    published tables are literally this script's output (protocol §15)."""
    print("\n===== §5.3 Phase B: optimiser iterations per seed, "
          "R-referenced =====\n")
    print("| config | n | R | B0 | B3 | B3/R mean | B3/R median [min, max] "
          "| B3/R > 1 |")
    print("|---" * 8 + "|")
    for deck, d in (res.get("phase_b") or {}).items():
        e = d.get("check2_iters_vs_R") or {}
        n = e.get("n")
        if not n:
            continue
        m, r = e["mean_iters_per_seed"], e["B3_over_R"]
        print(f"| `{DECK_ABBR.get(deck, deck)}` | {n} | {m['R']:.2f} "
              f"| {m['B0']:.2f} | {m['B3']:.2f} | {r['ratio_of_means']:.3f} "
              f"| {r['per_seed_median']:.3f} [{r['per_seed_min']:.3f}, "
              f"{r['per_seed_max']:.3f}] | {r['n_B3_worse_than_R']}/{n} |")
    print()

    ms = res.get("module_sweeps") or {}
    order = ("M1", "M2", "M3 live", "vacuum", "PULSE", "FF")
    print("\n===== §4.5 Phase A: module sweeps per run =====\n")
    for deck, d in (ms.get("phase_a") or {}).items():
        arms = list(d["per_arm"])
        mg = d["models_per_group"]["v=1"]
        print(f"**`{DECK_ABBR.get(deck, deck)}`** (n = {d['n_seeds']})\n")
        print("| module | models | " + " | ".join(arms) + " | A1/A0 |")
        print("|---" * (len(arms) + 3) + "|")
        for g in order:
            cells = [_cell(d["per_arm"][a][g]) for a in arms]
            r = _rat(d["per_arm"]["A1"][g]["ratio_vs_base"], True)
            print(f"| {g} | {mg[g]} | " + " | ".join(cells) + f" | {r} |")
        tt = {a: d["totals"][a] for a in arms}
        cells = [f"{tt[a]['v=1']['total_calls_per_run_mean']:.1f}"
                 for a in arms]
        lo = tt["A1"]["v=1"]["ratio_vs_base"]["pooled"]
        hi = tt["A1"]["v=0"]["ratio_vs_base"]["pooled"]
        print(f"| **total calls** | {sum(mg.values())} | " + " | ".join(cells)
              + f" | **[{min(lo, hi):.3f}, {max(lo, hi):.3f}]** |")
        print()
    print("\n===== §5.5.1 Phase B: module sweeps per run =====\n")
    for deck, d in (ms.get("phase_b") or {}).items():
        arms = list(d["per_arm"])
        mg = d["models_per_group"]["v=1"]
        n = d["n_seeds"]
        print(f"**`{DECK_ABBR.get(deck, deck)}`** (n = {n})\n")
        print("| module | models | " + " | ".join(arms)
              + " | B3/B0 | per-run med [min, max] | runs B3 > B0 |")
        print("|---" * (len(arms) + 5) + "|")
        for g in order:
            cells = [_cell(d["per_arm"][a][g]) for a in arms]
            r = d["per_arm"]["B3"][g]["ratio_vs_base"]
            sp, worse = _spread(r, n)
            print(f"| {g} | {mg[g]} | " + " | ".join(cells)
                  + f" | {_rat(r, True)} | {sp} | {worse} |")
        tt = {a: d["totals"][a] for a in arms}
        cells = [f"{tt[a]['v=1']['total_calls_per_run_mean']:.0f}"
                 for a in arms]
        r1 = tt["B3"]["v=1"]["ratio_vs_base"]
        r0 = tt["B3"]["v=0"]["ratio_vs_base"]
        sp, worse = _spread(r1, n)
        lo, hi = sorted((r1["pooled"], r0["pooled"]))
        print(f"| **total calls** | {sum(mg.values())} | " + " | ".join(cells)
              + f" | **[{lo:.3f}, {hi:.3f}]** | {sp} | {worse} |")
        print()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true",
                    help="compare the recomputation against the committed "
                         "tallies and exit nonzero on any mismatch")
    ap.add_argument("--teeth", action="store_true",
                    help="run --verify, then the verifier's own teeth: "
                         "doctored recomputations that must each be "
                         "refused (protocol §12)")
    ap.add_argument("--tables", action="store_true",
                    help="print the report's §5.3 / §4.5 / §5.5.1 markdown tables "
                         "from the recomputation and exit")
    ap.add_argument("--mode", choices=("campaign", "smoke"),
                    default="campaign",
                    help="which records to recompute from: 'campaign' (the "
                         "default, A42's) or 'smoke' (the machinery smokes, "
                         "so --verify is exercisable before the campaign "
                         "exists; smoke numbers are never measurements)")
    args = ap.parse_args()

    roots = roots_for(args.mode)
    pa_res = phase_a(roots["pa_records"])
    pb_res = phase_b(roots["pb_records"])
    result = {"mode": args.mode,
              "phase_a": pa_res,
              "phase_b": pb_res,
              "i17_transfer": transfer(pa_res, pb_res, roots),
              "dsm_blocks": dsm_blocks(roots["pa_records"],
                                       roots["pb_records"]),
              "module_sweeps": module_sweeps(roots["pa_records"],
                                             roots["pb_records"]),
              "exclusion_stakes": exclusion_stakes(roots["pa_records"]),
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

    if args.tables:
        print_tables(result)
        return 0

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
                  f"p90={e['p90']} floor_rel={e['floor_rel']} "
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
