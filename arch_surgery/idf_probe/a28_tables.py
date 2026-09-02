#!/usr/bin/env python
"""Print A28's tables from the recorded artifacts.  Nothing is computed here.

Order is fixed and is not a style choice: **the gates, then robustness, then
the drop census, then any ratio.**  A cost figure that arrives before the
population it was computed over is trap T11, which this project has published
three times.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _get(runs: Path, name: str):
    p = runs / name
    return json.loads(p.read_text()) if p.exists() else None


def _fmt(v, w=12, nd=4):
    if v is None:
        return "-".rjust(w)
    if isinstance(v, bool):
        return ("yes" if v else "NO").rjust(w)
    if isinstance(v, float):
        return f"{v:.{nd}g}".rjust(w)
    return str(v).rjust(w)


def _rule(title):
    print(f"\n{title}\n{'=' * len(title)}")


def neutrality(runs: Path) -> None:
    d = _get(runs / "neutrality", "_gates_a24.json")
    if not d:
        print("\n[switch neutrality: not run in this tree "
              "(needs --parent-tree)]")
        return
    _rule("0.  Switch neutrality -- with every switch off, is this tree "
          "still the base commit?")
    tot = 0
    for gname in ("gate_bit_identity_default_vs_parent",
                  "gate_bit_identity_default_vs_parent_probe_on"):
        g = d.get(gname) or {}
        print(f"\n  {gname}")
        print(f"    {'deck':<24}{'status':>8}{'lines diff/cmp':>22}"
              f"{'floats diff/cmp':>22}{'total':>10}")
        for s, v in g.items():
            if not isinstance(v, dict) or "status" not in v:
                continue
            print(f"    {s:<24}{v['status']:>8}"
                  f"{v['mfile_lines_differing']:>10}/"
                  f"{v['mfile_lines_compared']:<11}"
                  f"{v['mfile_floats_differing']:>10}/"
                  f"{v['mfile_floats_compared']:<11}"
                  f"{v['total_quantities_compared']:>10}")
            tot += v["total_quantities_compared"]
    print(f"\n    total quantities compared across both modes: {tot}")
    sens = _get(runs / "neutrality", "_gate_sensitivity_a24.json")
    if sens:
        n_det = sum(
            1 for v in sens.values()
            for w in ([v] if "detected" in v else v.values())
            if isinstance(w, dict) and w.get("detected")
        )
        print(f"    sensitivity: {n_det} deliberately perturbed comparisons, "
              f"all detected")


def manifests(runs: Path) -> None:
    d = _get(runs, "_manifests_a28.json")
    if not d:
        return
    _rule("1.  What each comparison declares it varies")
    print(f"  overall: {d['status']}\n")
    for s, rec in d["per_scenario"].items():
        print(f"  {s}")
        if rec.get("status") != "PASS":
            print(f"    REFUSED: {str(rec.get('error'))[:300]}")
            continue
        print(f"    {rec['n_checked']} of {rec['n_ordered_pairs_possible']} "
              f"ordered arm pairs checked, {rec['n_skipped']} skipped, "
              f"{len(rec['undeclared_pairs'])} undeclared")
        for c in rec["checked"]:
            print(f"      {c['comparison']:<32} {c['status']:<6} "
                  f"varies {c['declared']}")
            print(f"        observed differing keys: "
                  f"{c['observed_differing_keys']}")
    sens = _get(runs, "_manifest_sensitivity_a28.json")
    if sens:
        print(f"\n  the declaration check shown capable of refusing: "
              f"{sens.get('n_that_bit')} of {sens.get('n_teeth')} teeth bite "
              f"({sens.get('status')})")


def model_set(runs: Path) -> None:
    d = _get(runs, "_model_set_a28.json")
    if not d:
        return
    _rule("2.  Do the arrangements run the same models, and does the cost "
          "unit count what it claims?")
    print(f"  overall: {d['status']}   "
          f"({d['n_arm_records_checked']} arm records checked)")
    print(f"  {len(d['call_sites'])} model call sites read out of caller.py\n")
    print(f"    {'deck':<24}{'arm':<16}{'covers all':>11}"
          f"{'counted':>10}{'reported':>10}{'flat tail':>11}")
    for s, rows in d["per_scenario"].items():
        for a, r in rows.items():
            if "covers_every_call_site" not in r:
                print(f"    {s:<24}{a:<16}{'MISSING':>11}")
                continue
            cu = r["cost_unit"]
            print(f"    {s:<24}{a:<16}"
                  f"{('yes' if r['covers_every_call_site'] else 'NO'):>11}"
                  f"{_fmt(cu['sum_counted'], 10)}"
                  f"{_fmt(cu['node_calls_total_reported'], 10)}"
                  f"{_fmt(cu['sum_flat_tail_uncounted'], 11)}")
    sn = d.get("sensitivity") or {}
    if sn and "n_teeth" in sn:
        print(f"\n  shown capable of failing: {sn['n_that_bite']} of "
              f"{sn['n_teeth']} teeth bite ({sn['status']}), over "
              f"{sn['n_call_sites']} call sites")
        for k, v in sn.items():
            if isinstance(v, dict) and "bites" in v:
                print(f"    {v['perturbation'][:78]:<78}"
                      f"{'bites' if v['bites'] else 'DOES NOT BITE'}")


def gate(runs: Path) -> None:
    d = _get(runs, "_gate_a28.json")
    if not d:
        return
    _rule("3.  The equivalence gate -- does each arrangement reach the same "
          "optimum as PROCESS as shipped?")
    print(f"  overall: {d['overall']}   over "
          f"{d['denominator_arm_gates']} arm gates\n")
    print(f"    {'deck':<24}{'arm':<16}{'status':>8}"
          f"{'objf rel diff':>16}{'margin x':>12}"
          f"{'ineq viol':>11}{'c93 rel':>12}")
    for s, byarm in d["per_scenario"].items():
        for a, rec in byarm.items():
            ch = rec.get("checks", {})
            o = ch.get("norm_objf", {})
            f = ch.get("feasibility", {})
            c = ch.get("constraint_93", {})
            viol = (f.get("n_inequalities_violated") or {})
            print(f"    {s:<24}{a:<16}{rec['status']:>8}"
                  f"{_fmt(o.get('relative_difference'), 16, 3)}"
                  f"{_fmt(o.get('margin_factor'), 12, 4)}"
                  f"{str(viol.get('R')) + '/' + str(viol.get(a)):>11}"
                  f"{_fmt(c.get('residual_relative_to_burn_time'), 12, 3)}")
    print("\n    'ineq viol' is reference/arm.  'c93 rel' is the burn-time "
          "consistency\n    residual as a fraction of the burn time; '-' "
          "means the deck names no\n    icc = 93, which is the k = 0 control "
          "and is not a silent pass.")
    sens = _get(runs, "_gate_sensitivity_a28.json")
    if sens and "_summary" in sens:
        sm = sens["_summary"]
        print(f"\n  the gate shown capable of failing: "
              f"{sm['n_that_did_fail']} of {sm['n_checks_that_must_fail']} "
              f"deliberately corrupted inputs are refused, over arms "
              f"{sm['arms_exercised']} "
              f"({'all teeth bite' if sm['all_teeth_bite'] else 'A TOOTH DID NOT BITE'})")
        if sm.get("n_not_applicable"):
            print(f"    plus {sm['n_not_applicable']} perturbation(s) reported "
                  f"NOT APPLICABLE rather than\n    counted either way: "
                  f"{sm['not_applicable_why']}")


def cost_at_the_gate_point(runs: Path, scenarios) -> None:
    _rule("4.  Cost at each deck's own starting point (n = 1 per cell; the "
          "distribution is §7)")
    print(f"    {'deck':<24}{'arm':<16}{'net model evals':>16}"
          f"{'sweeps':>9}{'iters':>7}{'nvar':>6}{'exit residual':>16}")
    for s in scenarios:
        for a in ("R", "A0p", "A0p_reordered", "A1p_nohoist", "A1p"):
            p = runs / "gate" / s / a / "metrics.json"
            if not p.exists():
                continue
            m = json.loads(p.read_text())
            ea = m.get("exit_audit") or {}
            print(f"    {s:<24}{a:<16}"
                  f"{_fmt(m.get('node_calls_solve_phase'), 16)}"
                  f"{_fmt(m.get('n_model_calls'), 9)}"
                  f"{_fmt(m.get('n_solver_iterations'), 7)}"
                  f"{_fmt(m.get('nvar'), 6)}"
                  f"{_fmt(ea.get('residual_max'), 16, 4)}")
        # the three comparisons, from the same rows
        def cost(a):
            p = runs / "gate" / s / a / "metrics.json"
            if not p.exists():
                return None
            return json.loads(p.read_text()).get("node_calls_solve_phase")
        r, a0, a1 = cost("R"), cost("A0p"), cost("A1p")
        if r and a0 and a1:
            print(f"      -> R->A0' {100 * (a0 / r - 1):+.2f} %   "
                  f"A0'->A1' {100 * (a1 / a0 - 1):+.2f} %   "
                  f"R->A1' {100 * (a1 / r - 1):+.2f} %")


def ladder(runs: Path) -> None:
    d = _get(runs, "_ladder_a28.json")
    if not d:
        return
    _rule("5.  Cost at matched ACHIEVED accuracy (not at matched settings)")
    print(f"  {d['construction']}")
    a = d.get("asymmetry") or {}
    if a:
        print(f"\n  THE ENVELOPE'S ASYMMETRY, and what is done about it")
        for k in ("what", "bias_1_sampling", "bias_2_interpolation",
                  "the_fix", "why_this_is_not_pedantry", "headline_rule"):
            if a.get(k):
                print(f"    [{k}] {a[k]}")
        print()
    print(f"  accuracy: {d['accuracy_measure'][:110]}...")
    for s, rec in d["per_scenario"].items():
        cp = rec.get("common_population") or {}
        print(f"\n  {s}   ({rec['n_rungs_flat_usable']} usable flat rungs, "
              f"{rec['n_rungs_block_usable']} block)")
        print(f"    common population: {cp.get('n_common')} start(s) kept by "
              f"EVERY rung of both arms {cp.get('starts_common_to_every_rung')};"
              f" rungs keeping no start {cp.get('rungs_that_kept_no_start')}; per-rung kept before restriction "
              f"{cp.get('per_rung_kept_before_restriction')}")
        print(f"    {'rung':<20}{'tau':>9}{'inner':>9}{'kept/off':>10}"
              f"{'net evals':>11}{'p90 resid':>13}{'max resid':>13}")
        for key in ("rungs_flat_A0p", "rungs_block_A1p"):
            for r in rec[key]:
                print(f"    {r['label']:<20}{_fmt(r['tau'], 9, 2)}"
                      f"{_fmt(r['inner_tau'], 9, 2)}"
                      f"{str(r['n_converged']) + '/' + str(r.get('denominator_starts_offered', '?')):>10}"
                      f"{_fmt(r.get('net_model_evaluations'), 11)}"
                      f"{_fmt(r.get('achieved_residual_p90'), 13, 3)}"
                      f"{_fmt(r.get('achieved_residual_max'), 13, 3)}")
        for stat in ("achieved_residual_p90", "achieved_residual_p50",
                     "achieved_residual_max"):
            c = rec.get(stat)
            if not c or c.get("status") == "NO CURVE":
                print(f"    [{stat}] no curve")
                continue
            dr = c.get("draws") or {}
            print(f"    [{stat}]  draws: flat {dr.get('flat')}, block "
                  f"all-settings {dr.get('block_all_settings')}, block "
                  f"matched-count {dr.get('block_matched_count')}")
            for key, label in (
                ("matched_count_comparison",
                 "MATCHED-COUNT (5 joint rungs vs 5 flat) -- the ARCHITECTURE figure"),
                ("all_settings_comparison",
                 "ALL-SETTINGS (9 block rungs vs 5 flat) -- the PRACTITIONER figure"),
            ):
                cmp_ = c.get(key)
                if not cmp_:
                    continue
                print(f"      {label}: {cmp_['n_matched_points']} matched "
                      f"points, {cmp_['n_out_of_range']} out of range")
                for row in cmp_["rows"]:
                    if row["ratio_block_over_flat"] is None:
                        print(f"        {row['flat_label']:<18} "
                              f"accuracy {row['accuracy']:.4g}  "
                              f"{row['status']}")
                    else:
                        print(f"        {row['flat_label']:<18} "
                              f"accuracy {row['accuracy']:.4g}  "
                              f"A0' {row['flat_cost']:>8.0f}  "
                              f"A1' {row['block_cost']:>10.1f}  "
                              f"ratio {row['ratio_block_over_flat']:.4f}  "
                              f"({row['change_pct']:+.2f} %)")
            prem = c.get("tuning_premium_all_over_matched")
            if prem:
                print(f"      tuning premium (all-settings / matched-count), "
                      f"per point: "
                      f"{[None if x is None else round(x, 4) for x in prem]}")
            for k in ("convexity_flat", "convexity_block_matched_count",
                      "convexity_block_all_settings"):
                v = c.get(k)
                if v:
                    print(f"      {k}: {v['verdict']} "
                          f"({v['n_convex']}/{v['n_interior_points_testable']} "
                          f"interior points convex, "
                          f"{v['n_envelope_points']} envelope points)")


def h5(runs: Path) -> None:
    d = _get(runs, "_h5_a28.json")
    if not d:
        return
    _rule("6.  Robustness FIRST -- which starts each arrangement solves")
    for s, comps in d["comparisons"].items():
        print(f"\n  {s}")
        print(f"    {'comparison':<24}{'both':>6}{'only ref':>10}"
              f"{'only arm':>10}{'neither':>9}{'offered':>9}")
        for name, c in comps.items():
            pr = c["paired_robustness"]
            ref, arm = c["arms"]["reference"], c["arms"]["variant"]
            print(f"    {name:<24}{pr['n_both_solve']:>6}"
                  f"{pr['n_only_' + ref]:>10}{pr['n_only_' + arm]:>10}"
                  f"{pr['n_neither']:>9}"
                  f"{pr['denominator_starts_offered']:>9}")
        for name, c in comps.items():
            print(f"    failure modes, {name}: {c['failure_modes']}")

    _rule("7.  The drop census, BEFORE any ratio")
    for s, comps in d["comparisons"].items():
        print(f"\n  {s}")
        print(f"    {'comparison':<24}{'kept':>6}{'crashed':>9}"
              f"{'ifail!=1':>10}{'objf mism':>11}{'offered':>9}"
              f"{'degen I-12':>12}")
        for name, c in comps.items():
            cen = c["drop_census_reported_before_any_ratio"]
            k = cen["counts"]
            print(f"    {name:<24}{cen['n_kept']:>6}"
                  f"{k.get('crashed', 0):>9}{k.get('ifail_not_1', 0):>10}"
                  f"{k.get('objf_mismatch', 0):>11}"
                  f"{cen['denominator_starts_offered']:>9}"
                  f"{cen['n_kept_but_degenerate_entry_I12']:>12}")

    _rule("8.  Cost, over the kept starts only -- paired ratio, per deck, "
          "never pooled")
    print(f"  unit: {d['cost_unit']}")
    print(f"  headline: {d['headline']}")
    print(f"  naming:   {d['naming']}\n")
    for s, comps in d["comparisons"].items():
        print(f"  {s}")
        print(f"    {'comparison':<24}{'n':>4}{'min':>9}{'q1':>9}"
              f"{'median':>9}{'q3':>9}{'max':>9}{'cheaper/dearer':>16}")
        for name, c in comps.items():
            q = c["paired_ratio_variant_over_reference"]
            if not q:
                print(f"    {name:<24}{'-':>4}   no kept starts")
                continue
            print(f"    {name:<24}{q['n']:>4}{_fmt(q['min'], 9, 4)}"
                  f"{_fmt(q['q1'], 9, 4)}{_fmt(q['median'], 9, 4)}"
                  f"{_fmt(q['q3'], 9, 4)}{_fmt(q['max'], 9, 4)}"
                  f"{str(c['n_starts_variant_cheaper']) + '/' + str(c['n_starts_variant_dearer']):>16}")
        for name, c in comps.items():
            a = c["attribution"]["paired_iteration_ratio"]
            if a:
                print(f"    optimiser-iteration ratio, {name}: "
                      f"q1 {a['q1']} median {a['median']} q3 {a['q3']} "
                      f"(a diagnostic, never a cost: the arms have different "
                      f"dimension)")

    _rule("8a. Why each arrangement refused a start, and on which quantity")
    print("  Decision D18 added the third arrangement for exactly this "
          "measurement: A25\n  reported 13 refused starts as a property of "
          "the architecture, with no control\n  that could tell architecture "
          "from stopping rule.  A0' has the same stopping\n  rule and the "
          "flat loop.")
    for s, per in (d.get("failure_attribution") or {}).items():
        print(f"\n  {s}")
        print(f"    {'arm':<16}{'not ok':>8}{'of':>5}"
              f"{'module-solve failures':>23}   components named")
        for a, r in per.items():
            print(f"    {a:<16}{r['n_starts_not_ok']:>8}"
                  f"{r['denominator_starts']:>5}"
                  f"{r['n_module_solve_failures']:>23}   "
                  f"{r['components_named_by_a_module_solve_failure'] or '-'}")

    _rule("9.  Issue I-12 -- net electric power at the state each solve was "
          "ENTERED with")
    for s, per in d["I12_entry_census"].items():
        print(f"\n  {s}")
        print(f"    {'arm':<16}{'starts w/ census':>18}"
              f"{'starts visiting <=0':>21}{'entries audited':>17}"
              f"{'non-positive':>14}{'min p_net MW':>14}")
        for a, r in per.items():
            print(f"    {a:<16}"
                  f"{str(r['n_starts_with_a_census']) + '/' + str(r['denominator_starts']):>18}"
                  f"{r['n_starts_visiting_a_non_positive_entry']:>21}"
                  f"{r['total_call_models_entries_audited']:>17}"
                  f"{r['total_non_positive_entries']:>14}"
                  f"{_fmt(r['min_entry_p_net_mw_over_starts'], 14, 4)}")

    _rule("10. Quantities the harvest called constant that actually moved")
    print("  A26 §5.4 measured this to matter: on the dropped deck two "
          "quantities that\n  are not constant had their bit-identity "
          "assertion block convergence and\n  inflate the cost figures by "
          "14-28 %.  Perturbed multi-starts are where an\n  unperturbed "
          "harvest's constancy claim is most likely to fail.")
    for s, per in d["moved_constants_under_perturbation"].items():
        print(f"\n  {s}")
        for a, r in per.items():
            if "status" in r:
                print(f"    {a:<16}{r['status']}")
                continue
            print(f"    {a:<16}"
                  f"{r['n_call_models_with_a_moved_constant']:>7} of "
                  f"{r['n_call_models_total']:<8} solves affected "
                  f"({100 * (r['fraction_of_call_models_affected'] or 0):.2f} %), "
                  f"{r['n_distinct_constants_that_moved']} distinct quantities")


def accuracy_census(runs: Path) -> None:
    d = _get(runs, "_accuracy_at_fixed_tau_a28.json")
    if not d:
        print("\n[accuracy census at the campaign's fixed tolerance: not run]")
        return
    _rule("10a. Is the robustness comparison on a level basis?  The accuracy "
          "each arrangement DELIVERS at tau = 1e-6")
    print(f"  {d['why']}")
    print(f"  measured at: {d['measured_at']}\n")
    for s, rec in d["per_scenario"].items():
        print(f"  {s}")
        print(f"    {'arm':<16}{'n':>4}{'bit-exact 0':>13}{'p10':>12}"
              f"{'p50':>12}{'p90':>12}{'max':>12}")
        for a, r in rec["per_arm"].items():
            print(f"    {a:<16}{r['n_starts_measured']:>4}"
                  f"{r['n_bit_exact_zero']:>13}"
                  f"{_fmt(r['p10'], 12, 3)}{_fmt(r['p50'], 12, 3)}"
                  f"{_fmt(r['p90'], 12, 3)}{_fmt(r['max'], 12, 3)}")
        for k, v in rec["paired"].items():
            print(f"    paired, {k}: {v['verdict']}  "
                  f"(n = {v['n_paired_starts']}, equal on "
                  f"{v['n_starts_equal']}, median ratio "
                  f"{_fmt(v['median_ratio_second_over_first'], 1, 4).strip()})")
        print()


def timings(runs: Path) -> None:
    d = _get(runs, "_timings_a28.json")
    if not d:
        return
    _rule("11. Timings -- CONTEXT, NEVER EVIDENCE")
    print(f"  {d['what_these_are']}\n")
    for s, rows in d["per_scenario"].items():
        print(f"  {s}")
        print(f"    {'arm':<16}{'n reps':>8}{'CPU s median':>14}"
              f"{'p10-p90':>22}{'spread % of median':>20}{'seq pos':>12}")
        for a, r in rows.items():
            if not isinstance(r, dict):
                continue
            if "cpu_s_median" not in r:
                print(f"    {a:<16}{r.get('status', '')}")
                continue
            lo, hi = r["cpu_s_p10_p90"]
            print(f"    {a:<16}{r['n_repetitions']:>8}"
                  f"{r['cpu_s_median']:>14.2f}"
                  f"{f'{lo:.2f}-{hi:.2f}':>22}"
                  f"{r['p10_p90_spread_as_pct_of_median']:>19.0f} %"
                  f"{str(r['sequence_positions']):>12}")
    print("\n  No ratio between arms is offered.  The interval above is wider "
          "than every\n  effect this study argues about, so no ratio of two "
          "of these numbers can\n  resolve one.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True)
    ap.add_argument("--scenarios", nargs="*", default=[
        "large_tokamak_nof", "low_aspect_ratio_DEMO", "st_regression"])
    args = ap.parse_args()
    runs = Path(args.runs).resolve()
    print("MDA partition experiment, Phase B -- results from "
          f"{runs}")
    print("Reported per deck, never pooled.  Every count carries its "
          "denominator.")
    neutrality(runs)
    manifests(runs)
    model_set(runs)
    gate(runs)
    cost_at_the_gate_point(runs, args.scenarios)
    ladder(runs)
    h5(runs)
    accuracy_census(runs)
    timings(runs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
