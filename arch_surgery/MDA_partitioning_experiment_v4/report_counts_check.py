#!/usr/bin/env python
"""Every count the report states, re-derived from the run records and printed
beside the report's figure.

Task **A80 (report-accuracy-audit)**, pass 7 of its brief: *every ratio's
population is the one its caption states*.  The report's denominators — 949 /
921 / 28 records, 25 runs per arm per evaluation-phase source, the seed sets
22 / 11 / 22, the crash taxonomy, the retried-seed counts, the 30 gates and
167 teeth — are here re-derived from the records **through the harness**
(``records.read`` applies the arm-name translation of 2026-09-15, trap T16;
``tally.published_sources`` names the populations) and printed beside the
number the report carries, with a ``same`` / ``DIFFERS`` mark.  Where the
report's wording turned out to be wrong the line says what the records say
instead, so the corrected sentence has its derivation on the page.

Also here, because the audit needed them and no table carried them:

- the two ``y_exit.json`` files under the campaign tree that are not campaign
  records (the lifted-input derivation's baseline evaluations) — the
  923-against-921 question of the brief;
- the arrangement-method (prime) call count per run against the run's dispatch
  sweeps on the partitioned arm, which is what makes "one prime call per
  sweep" a checked statement rather than a recollection;
- the per-seed equality of the evaluation count ε between ``B1`` and ``B2`` on
  the pulsed configurations — the pre-declared ``ε = 1`` expectation of the
  plan's §3.5, per seed;
- the pooled ``AR/A0`` per-call ratio and the ``AR``-to-``A0`` residual factor
  on each configuration, which the report's §5.3 and §6 state as ranges;
- the frozen-to-mixed ratio of the predicate trial's audit columns, which
  §5.6 states as "up to 8×";
- **the per-arm success counts** of §4.3, §5.7 and Table 11 — accepted
  optima of the 25 starts offered, every other start by outcome class and the
  starts lost that another arm accepted — re-derived here from ``status``,
  ``mfile.ifail``, ``failure_class`` and the traceback **without the tally's
  constructions**, and printed beside the cells the tally published in
  ``runs/gates/tally_optimisation/measurements.json`` (task **A82
  (per-arm-success)**, 2026-09-15).

Usage::

    python report_counts_check.py
    python report_counts_check.py --canonical /path/to/idf_probe/runs/campaign_57dc0c14

No PROCESS run.  Exit status 0 when every re-derived count equals the report's
figure it is printed beside, 3 otherwise.  A DIFFERS line is a finding, not a
failure of this script.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from harness.core import records as records_mod  # noqa: E402
from harness.core.config import default_campaign  # noqa: E402
from harness.measurement import stats as stats_mod  # noqa: E402
from harness.measurement import tally as tally_mod  # noqa: E402

CONFIGS = ("large_tokamak_nof", "low_aspect_ratio_DEMO", "st_regression")
PULSED = ("large_tokamak_nof", "low_aspect_ratio_DEMO")

_differs = 0


def line(label: str, derived, reported, note: str = "") -> None:
    """One comparison line; counts the disagreements."""
    global _differs
    same = derived == reported
    if not same:
        _differs += 1
    mark = "same   " if same else "DIFFERS"
    print(f"  {mark}  {label:<62} records: {derived!s:<28} report: {reported!s}")
    if note:
        print(f"           {note}")


def gather(campaign):
    """``{source name: [records]}`` for every published source, via the harness."""
    out: dict[str, list[dict]] = {}
    for source in tally_mod.published_sources(campaign):
        rows, refusals = tally_mod.source_rows(campaign, source)
        if refusals:
            raise SystemExit(f"record contract refusals in {source.name}: {refusals[:3]}")
        out[source.name] = [dict(r.record) for r in rows]
    return out


def by_config_arm_seed(records):
    """``{configuration: {arm: {pairing key: record}}}``; the key is the seed,
    or the design-vector column in a stencil source (the tally pairs the same way)."""
    idx: dict[str, dict[str, dict[int, dict]]] = defaultdict(lambda: defaultdict(dict))
    for r in records:
        identity = r.get("job_identity") or {}
        key = identity.get("stencil_column") if identity.get("regime") == "stencil" else r["campaign_seed"]
        idx[r["campaign_configuration"]][r["campaign_arm"]][int(key)] = r
    return idx


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--canonical",
        type=Path,
        default=None,
        help="the campaign's canonical records directory (untracked), to count its y_exit.json files beside this tree's",
    )
    args = parser.parse_args()

    campaign = default_campaign()
    sources = gather(campaign)

    print("\n== 1. The population (report header, §4 intro, D.0) ==")
    n_total = sum(len(v) for v in sources.values())
    line("campaign records, every published source", n_total, 949)
    for name, expected in (
        ("campaign_entry_references", 3),
        ("campaign_displaced", 275),
        ("campaign_stencil_forward", 198),
        ("campaign_stencil_backward", 198),
        ("campaign_optimisation", 275),
    ):
        line(f"records in {name}", len(sources.get(name, [])), expected)
    status = Counter(r["status"] for v in sources.values() for r in v)
    line("records with status ok", status.get("ok", 0), 921)
    line("records with status crashed (the harness's word)", status.get("crashed", 0), 28)
    failure_class = Counter(
        r.get("failure_class") for r in sources["campaign_optimisation"] if r["status"] != "ok"
    )
    line(
        "  of which failure_class crashed (PROCESS RuntimeError)",
        failure_class.get("crashed", 0),
        28,
        "the report's 'twenty-eight … crashed, all with PROCESS's own RuntimeError' — the records split them",
    )
    line("  of which failure_class unconverged (ModuleSolveFailure)", failure_class.get("unconverged", 0), 0)
    ifail5 = Counter(
        r["campaign_configuration"]
        for r in sources["campaign_optimisation"]
        if r["status"] == "ok" and (r.get("mfile") or {}).get("ifail") != 1.0
    )
    print(f"           status ok with ifail != 1 (finished, not accepted), by configuration: {dict(ifail5)}")

    print("\n== 2. Evaluation phase: 25 per arm; 2·nvar stencil points per arm (§3.4, §3.10, Tables 7 and 8, D.5) ==")
    for name in ("campaign_displaced",):
        idx = by_config_arm_seed(sources[name])
        for config in CONFIGS:
            counts = {arm: len(seeds) for arm, seeds in sorted(idx[config].items())}
            ok = {arm: sum(1 for r in seeds.values() if r["status"] == "ok") for arm, seeds in sorted(idx[config].items())}
            line(f"{name} {config}: runs per arm", counts, {a: 25 for a in counts})
            line(f"{name} {config}: ok per arm", ok, {a: 25 for a in ok})
    nvar = {c.name: c.n_iteration_variables for c in campaign.configurations}
    for name in ("campaign_stencil_forward", "campaign_stencil_backward"):
        idx = by_config_arm_seed(sources[name])
        for config in CONFIGS:
            counts = {arm: len(seeds) for arm, seeds in sorted(idx[config].items())}
            line(
                f"{name} {config}: points per arm (Table D.13: vars per configuration)",
                counts,
                {a: nvar[config] for a in counts},
                "the plan's §3.4 says 2(nvar + 1) per arm 'plus the lifted column on the pinned arms'; as built every Phase A arm reads the committed input file and has nvar points per sign",
            )
    n_stencil = len(sources["campaign_stencil_forward"]) + len(sources["campaign_stencil_backward"])
    line("stencil evaluations in all (plan §3.10 budget: 418)", n_stencil, 418)

    print("\n== 3. Optimisation phase: the seed sets, configuration-invalid seeds, retries (§4.3, Tables 11 and D.12) ==")
    idx = by_config_arm_seed(sources["campaign_optimisation"])
    reported_n = {"large_tokamak_nof": 22, "low_aspect_ratio_DEMO": 11, "st_regression": 22}
    reported_invalid = {"large_tokamak_nof": 3, "low_aspect_ratio_DEMO": 13, "st_regression": 1}
    reported_retried = {
        "large_tokamak_nof": {"BR": 0, "B0": 0, "B1": 0, "B2": 0},
        "low_aspect_ratio_DEMO": {"BR": 12, "B0": 10, "B1": 10, "B2": 10},
        "st_regression": {"BR": 5, "B0": 3, "B2": 2},
    }
    for config in CONFIGS:
        by_arm = idx[config]
        seeds = sorted({s for rows in by_arm.values() for s in rows})
        converged = stats_mod.every_arm_converged(by_arm, seeds)
        invalid = stats_mod.configuration_invalid_seeds(by_arm, seeds)
        line(f"{config}: seeds offered", len(seeds), 25)
        line(f"{config}: n (every arm reached an accepted optimum)", len(converged), reported_n[config])
        line(f"{config}: configuration-invalid seeds (no arm accepted)", len(invalid), reported_invalid[config])
        outside = [s for s in seeds if s not in converged]
        print(f"           seeds outside the set: {outside}; configuration-invalid: {invalid}")
        accepted = {arm: sum(1 for r in rows.values() if stats_mod.accepted_optimum(r)) for arm, rows in sorted(by_arm.items())}
        finished = {arm: sum(1 for r in rows.values() if r["status"] == "ok") for arm, rows in sorted(by_arm.items())}
        print(f"           accepted optima per arm (status ok AND ifail == 1): {accepted}; finished (status ok): {finished}")
        retried_all = {arm: len(stats_mod.retried_seeds(rows)) for arm, rows in sorted(by_arm.items())}
        line(f"{config}: retried seeds per arm over every seed offered", retried_all, reported_retried[config])
        retried_in_set = {
            arm: len([s for s in converged if stats_mod.retried(rows[s])]) for arm, rows in sorted(by_arm.items())
        }
        print(f"           retried seeds per arm inside the seed set: {retried_in_set}")
        # the disposition of every seed outside the set, per arm
        for s in outside:
            disp = []
            for arm in sorted(by_arm):
                r = by_arm[arm].get(s)
                if r is None:
                    disp.append(f"{arm}: no record")
                    continue
                ifail = (r.get("mfile") or {}).get("ifail")
                disp.append(
                    f"{arm}: {r['status']}/{r.get('failure_class')}, ifail {ifail}, attempts {stats_mod.n_attempts(r)}"
                )
            print(f"             seed {s:>2}: " + "; ".join(disp))

    print("\n== 4. The crash taxonomy: which seeds, which arms (§4.3, §5.7, Tables 11 and D.12; companion F.6) ==")
    for config in CONFIGS:
        by_arm = idx[config]
        crashed = {arm: sorted(s for s, r in rows.items() if r.get("failure_class") == "crashed") for arm, rows in sorted(by_arm.items())}
        unconv = {arm: sorted(s for s, r in rows.items() if r.get("failure_class") == "unconverged") for arm, rows in sorted(by_arm.items())}
        print(f"  {config}: crashed (RuntimeError) {crashed}")
        print(f"  {config}: unconverged (ModuleSolveFailure) {unconv}")
        last_lines = Counter(
            (r.get("exit_forensics") or {}).get("traceback_last_line") or (r.get("exit_forensics") or {}).get("last_line")
            for rows in by_arm.values()
            for r in rows.values()
            if r["status"] != "ok"
        )
        for text, n in last_lines.items():
            print(f"      {n} × {str(text)[:160]}")
    line(
        "large_tokamak_nof: seeds crashed in all four arms",
        sorted(set.intersection(*[set(s for s, r in rows.items() if r.get("failure_class") == "crashed") for rows in idx["large_tokamak_nof"].values()])),
        [5, 20, 21],
    )
    line(
        "low_aspect_ratio_DEMO: seeds crashed in all four arms",
        sorted(set.intersection(*[set(s for s, r in rows.items() if r.get("failure_class") == "crashed") for rows in idx["low_aspect_ratio_DEMO"].values()])),
        [3, 21],
        "the report gives the count (2), not the seeds",
    )

    print("\n== 5. y_exit.json: campaign records against every file under the tree (the brief's 923 vs 921) ==")
    roots = [("this tree's runs/", Path(campaign.runs_dir))]
    if args.canonical is not None:
        roots.append((f"canonical {args.canonical}", args.canonical))
    for label, root in roots:
        if not root.exists():
            print(f"  {label}: absent")
            continue
        files = sorted(root.rglob("y_exit.json"))
        under_campaign = [p for p in files if "campaign" in p.relative_to(root).parts[:1]]
        others = [str(p.relative_to(root)) for p in files if p not in under_campaign]
        gate_others = [o for o in others if o.startswith("gates/")]
        print(
            f"  {label}: {len(files)} y_exit.json in all; {len(under_campaign)} under campaign/; "
            f"{len(gate_others)} under gates/ (the gates' own runs); the others:"
        )
        for o in others:
            if o not in gate_others:
                print(f"      {o}")
        if "campaign" in str(root) or label.startswith("this"):
            line(f"{label}: y_exit.json under campaign/ (= ok records: 674 evaluations + 247 optimisations)", len(under_campaign), 921)

    print("\n== 6. One prime (arrangement-method) call per dispatch sweep on the partitioned optimisation arm (§4.3, §5.8, D.17 and D.19) ==")
    for config in CONFIGS:
        rows = idx[config].get("B2", {})
        seeds = sorted({s for arm_rows in idx[config].values() for s in arm_rows})
        converged = stats_mod.every_arm_converged(idx[config], seeds)
        diffs = Counter()
        total = 0
        for s in converged:
            r = rows[s]
            diffs[int(r["n_arrangement_method_calls"]) - int(r["dispatch_sweeps"])] += 1
            total += int(r["n_arrangement_method_calls"])
        print(f"  {config} B2 over the seed set (n = {len(converged)}): n_arrangement_method_calls − dispatch_sweeps, histogram {dict(diffs)}")
        line(f"{config} B2: Σ arrangement-method calls over the seed set (Table D.20's cell)", total, {"large_tokamak_nof": 117281, "low_aspect_ratio_DEMO": 157504, "st_regression": 280776}[config])
        print(f"           per run: mean {total / max(len(converged), 1):.1f}; per evaluation (Σ calls / Σ ε): {total / max(sum(stats_mod.n_evaluations(rows[s]) or 0 for s in converged), 1):.2f}  — the report's §4.3 said 13.2 / 12.9 / 14.8 (the evaluation phase's figure)")
    # the evaluation phase's figure, for the record
    idxA = by_config_arm_seed(sources["campaign_displaced"])
    for config in CONFIGS:
        rows = idxA[config]["A2"]
        calls = sum(int(r["n_arrangement_method_calls"]) for r in rows.values())
        sweeps = sum(int(r["n_model_calls_sweeps"]) for r in rows.values())
        print(f"  {config} A2 displaced: prime calls per evaluation {calls / len(rows):.2f}; sweeps per evaluation {sweeps / len(rows):.2f}")

    print("\n== 7. ε on B1 → B2 per seed, pulsed configurations (the plan's §3.5 pre-declared ε = 1) ==")
    for config in PULSED:
        seeds = sorted({s for arm_rows in idx[config].values() for s in arm_rows})
        converged = stats_mod.every_arm_converged(idx[config], seeds)
        equal = sum(
            1 for s in converged
            if stats_mod.n_evaluations(idx[config]["B1"][s]) == stats_mod.n_evaluations(idx[config]["B2"][s])
        )
        iters_equal = sum(
            1 for s in converged
            if stats_mod.iterations_summed_over_attempts(idx[config]["B1"][s]) == stats_mod.iterations_summed_over_attempts(idx[config]["B2"][s])
        )
        sweeps_ratio = [idx[config]["B2"][s]["n_model_calls"] / idx[config]["B1"][s]["n_model_calls"] for s in converged]
        line(f"{config}: seeds with ε(B1) == ε(B2) exactly, of n", f"{equal} of {len(converged)}", f"{len(converged)} of {len(converged)}")
        print(f"           seeds with summed iterations equal: {iters_equal} of {len(converged)}; sweeps ratio B2/B1 median {stats_mod.median(sweeps_ratio):.4f}")
        # and the stencil column: ε(B1)/ε(B0) per seed against (nvar+2)/(nvar+1)
        col = [stats_mod.n_evaluations(idx[config]["B1"][s]) / stats_mod.n_evaluations(idx[config]["B0"][s]) for s in converged]
        print(f"           ε(B1)/ε(B0) median {stats_mod.median(col):.4f} against the stencil factor (nvar+2)/(nvar+1) = {(nvar[config] + 2) / (nvar[config] + 1):.4f}")

    print("\n== 8. AR against A0, displaced regime: pooled per-call ratio and the residual factor (§5.1, §5.3, §6 RQ4) ==")
    for config in CONFIGS:
        ar, a0 = idxA[config]["AR"], idxA[config]["A0"]
        pooled = sum(r["node_calls_single_eval"] for r in ar.values()) / sum(r["node_calls_single_eval"] for r in a0.values())
        def restricted(r):
            block = stats_mod.restricted_statistic(r, ruler="frozen")
            return block.get("max") if block.get("present", True) else None
        med_ar = stats_mod.median([restricted(r) for r in ar.values() if restricted(r) is not None])
        med_a0 = stats_mod.median([restricted(r) for r in a0.values() if restricted(r) is not None])
        factor = (med_ar / med_a0) if (med_ar and med_a0) else None
        print(f"  {config}: AR/A0 pooled {pooled:.4f} (saving {100 * (1 - pooled):.1f} %); AR restricted median {med_ar!s} / A0 {med_a0!s} = {('%.1f' % factor) if factor else '—'}×")
    print("           the report's §5.3/§6 range for the saving: 3–16 %; for the residual factor: 30–50×")

    print("\n== 9. The predicate trial's audit columns: frozen / mixed per pair (§5.6's 'up to 8×') ==")
    verdict = json.loads((Path(campaign.runs_dir) / "gates" / "predicate_mode" / "gate.json").read_text())
    pairs = verdict.get("runs") or []
    ratios = []
    for p in pairs:
        audit = (p.get("audit") or {}).get("frozen") or {}
        f, m = audit.get("frozen"), audit.get("mixed")
        try:
            fv, mv = float.fromhex(f) if isinstance(f, str) else float(f), float.fromhex(m) if isinstance(m, str) else float(m)
        except (TypeError, ValueError):
            continue
        if mv > 0:
            ratios.append((fv / mv, p.get("configuration"), p.get("arm"), p.get("seed")))
    if ratios:
        worst = max(ratios)
        print(f"  pairs read: {len(ratios)}; largest frozen/mixed audit ratio {worst[0]:.2f}× on {worst[1]} {worst[2]} seed {worst[3]}; all: " + ", ".join(f"{r[0]:.2f}" for r in ratios))
    else:
        print(f"  could not read the audit pair from the verdict record (keys: {sorted(verdict)[:20]}) — read companion Table F.5's exit-audit columns instead")

    print("\n== 10. The gate table: 30 gates, 167 teeth (§4.1, D.1) ==")
    gate_table = json.loads((Path(campaign.runs_dir) / "gates" / "gate_table" / "measurements.json").read_text())
    line("registered gates", gate_table["n_gates"], 30)
    line("PASS", gate_table["n_pass"], 30)
    # 161 until task A85 (v3-table-formats) gave `tally_contracts` two more.
    line("teeth declared", gate_table["n_teeth"], 167)
    line("teeth tripped", gate_table["n_teeth_tripped"], 167)
    nonzero = [(r["gate"], r["n_mismatched"]) for r in gate_table["rows"] if r.get("n_mismatched")]
    line("PASS rows with a nonzero mismatched count", nonzero, [("g0prime", 1)], "§4.1 names one such row; copy_identity's 7 are its recorded permitted-edit files")
    summed = [(r["gate"], r["denominators_summed"]) for r in gate_table["rows"] if len(r.get("denominators_summed") or []) > 1]
    print(f"           rows whose 'compared' sums more than one count: {summed}")

    print("\n== 11. Check 1 per seed on low_aspect_ratio_DEMO: how many pairs exceed the 1e-6 floor, and the worst (§5.1 (a), §6) ==")
    seeds = sorted({s for arm_rows in idx["low_aspect_ratio_DEMO"].values() for s in arm_rows})
    converged = stats_mod.every_arm_converged(idx["low_aspect_ratio_DEMO"], seeds)
    for arm in ("B1", "B2"):
        pairs = []
        for s in converged:
            a = float.fromhex(idx["low_aspect_ratio_DEMO"]["B0"][s]["exact"]["norm_objf"])
            b = float.fromhex(idx["low_aspect_ratio_DEMO"][arm][s]["exact"]["norm_objf"])
            pairs.append((abs(a - b) / max(abs(a), abs(b)), s))
        pairs.sort()
        above = [(r, s) for r, s in pairs if r > 1e-6]
        print(
            f"  B0 → {arm}: {len(above)} of {len(pairs)} pairs above the floor "
            f"(seeds {[s for _, s in above]}; r = {', '.join(f'{r:.3e}' for r, _ in above)}); "
            f"worst {pairs[-1][0]:.3e} at seed {pairs[-1][1]}"
            f" (B0 attempts {stats_mod.n_attempts(idx['low_aspect_ratio_DEMO']['B0'][pairs[-1][1]])})"
        )
    print("           the report's §5.1 (a) said 'a slightly different optimum on 2 of 11 seeds'; §6 said 'within 2.2e-6 relative' (the p90)")

    print("\n== 12. Per-arm success: the accepted optima of 25 per arm, by a second route (§4.3, §5.7, Table 11) ==")
    published = {
        t["table"]: t
        for t in json.loads(
            (Path(campaign.runs_dir) / "gates" / "tally_optimisation" / "measurements.json").read_text()
        )["tables"]
    }
    reported_accepted = {
        "large_tokamak_nof": {"BR": 22, "B0": 22, "B1": 22, "B2": 22},
        "low_aspect_ratio_DEMO": {"BR": 12, "B0": 12, "B1": 11, "B2": 11},
        "st_regression": {"BR": 24, "B0": 23, "B2": 23},
    }
    for config in CONFIGS:
        by_arm = idx[config]
        arms = sorted(by_arm, key=lambda a: ("BR", "B0", "B1", "B2").index(a))
        seeds = sorted({s for rows in by_arm.values() for s in rows})
        # the classification, written out here rather than imported
        def outcome(r):
            if r["status"] == "ok" and (r.get("mfile") or {}).get("ifail") == 1.0:
                return "accepted"
            if r["status"] == "ok":
                ifail = (r.get("mfile") or {}).get("ifail")
                return f"finished, ifail = {int(ifail) if isinstance(ifail, float) else ifail}"
            text = (r.get("traceback") or "").strip().splitlines()
            head = (text[-1].strip().split(":", 1)[0] if text else "no traceback")
            if r.get("failure_class") == "unconverged":
                return "coupling-loop cap (ModuleSolveFailure)"
            if r.get("failure_class") == "crashed":
                return f"crashed ({head.rsplit('.', 1)[-1]})"
            return str(r.get("failure_class"))
        labels = {(arm, s): outcome(by_arm[arm][s]) for arm in arms for s in seeds if s in by_arm[arm]}
        accepted_here = {
            arm: sum(1 for s in seeds if labels.get((arm, s)) == "accepted") for arm in arms
        }
        line(f"{config}: accepted optima per arm of 25 offered", accepted_here, reported_accepted[config])
        table_name = (
            f"per-arm success — {config} — campaign_optimisation · "
            + "·".join(arms)
        )
        block = published.get(table_name)
        if block is None:
            print(f"           the tally published no table named {table_name!r}")
            continue
        published_rows = {row["arm"]: row for row in block["rows"]}
        line(
            f"{config}: accepted optima per arm — this script beside the table's cells",
            accepted_here,
            {arm: published_rows[arm]["accepted"] for arm in arms},
        )
        classes = [c for c in block["columns"] if c["key"] not in {
            "arm", "offered", "accepted", "lost_another_arm_accepted", "seed_set",
            "seeds_not_accepted", "lost_seeds",
        }]
        for column in classes:
            label = column["key"]
            here = {arm: sum(1 for s in seeds if labels.get((arm, s)) == label) for arm in arms}
            line(
                f"{config}: {label} per arm",
                here,
                {arm: published_rows[arm][label] for arm in arms},
            )
        accepted_at = {s: [a for a in arms if labels.get((a, s)) == "accepted"] for s in seeds}
        lost_here = {
            arm: sorted(
                s for s in seeds
                if (arm, s) in labels and labels[(arm, s)] != "accepted" and accepted_at[s]
            )
            for arm in arms
        }
        line(
            f"{config}: starts lost that another arm accepted",
            {arm: len(v) for arm, v in lost_here.items()},
            {arm: published_rows[arm]["lost_another_arm_accepted"] for arm in arms},
        )
        print(f"           the lost starts, by arm: { {a: v for a, v in lost_here.items() if v} }")
        offered_here = {arm: sum(1 for s in seeds if (arm, s) in labels) for arm in arms}
        line(
            f"{config}: starts offered per arm",
            offered_here,
            {arm: published_rows[arm]["offered"] for arm in arms},
        )
        sums = {
            arm: published_rows[arm]["accepted"]
            + sum(published_rows[arm][c["key"]] for c in classes)
            for arm in arms
        }
        line(
            f"{config}: accepted + the class columns sum to the starts offered",
            sums,
            offered_here,
        )

    print(f"\n{_differs} line(s) DIFFER from the report's figure.")
    return 0 if _differs == 0 else 3


if __name__ == "__main__":
    sys.exit(main())
