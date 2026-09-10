#!/usr/bin/env python
"""A44 (transfer-gap): why Phase A's per-call ratio does not predict Phase B's
end-to-end ratio (queue issue I-17), from the V3 records plus one small,
pre-declared single-evaluation probe.

Every number the A44 report cites is produced by a stage of this script
(protocol section 15).  Stages, in order:

``factorise``   READ-ONLY over the frozen V3 campaign records (main checkout).
                The end-to-end node-call ratio of any two Phase B arms
                factorises, BY IDENTITY, as

                    R = N_b/N_a = [(N_b/C_b) / (N_a/C_a)] x [C_b/C_a]
                      =  rho_B  x  eps

                with N = ``node_calls_solve_phase`` (model-node executions in
                the solve phase, summed over the identical-converged seed
                set), C = ``sweeps_per_eval.n_evaluations`` (the number of
                ``call_models`` evaluations the optimiser made, same set;
                asserted equal to ``module_solve_totals.n_call_models``).
                Phase A's per-call ratio rho_A = sum(A1)/sum(A0) of
                ``node_calls_single_eval`` over the 25 seeds is what the
                transfer argument uses as a prediction of R, so the gap is

                    R / rho_A = (rho_B / rho_A) x eps

                exactly.  The identity is not a finding; the finding is which
                factor carries the config dependence.  The stage also
                separates, per config: the once-per-run post-solve executions
                inside N (carried as P, so N - P is the in-loop count); the
                2(nvar+1) evaluations per VMCON problem-call (1 base + 2 nvar
                central-difference + 1 reconcile, ``evaluators.fcnvmc2``),
                which makes eps = [(nvar_b+1)/(nvar_a+1)] x [problem-calls
                ratio]; retry-ladder attempts, whose failed-attempt
                evaluations are inside N and C but NOT inside the check-2
                statistic ``n_solver_iterations`` (final attempt only); the
                per-rung view B0->B1->B2->B3 and B1->B3; st's seeds split by
                rung (B0->B2 vs B2->B3, A43's half); and the nodes-per-sweep
                census that the regime probe's prediction rests on.  Teeth: a
                +1 on one record's N must break the exact-sum identity with
                the published sums; a +1 on one record's C must break the
                2(nvar+1) divisibility check.

``prepare``     RUNS PROCESS (fresh subprocess per run, exact tree asserted).
                Per config: the A0 cold reference at the deck point under
                THIS tree, compared bit-for-bit (counts, exit-audit hex, the
                whole y_exit state, the burn time) with V3's frozen reference
                -- the tree/instrument identity gate; then seed 1 at
                delta = 0.10 for A0 and A1 from that reference, compared
                with V3's seed-1 records (counts, per-block sweeps, audit
                hex) -- the gate that the copied runner with its new option
                UNSET is v2_eval_one.  Teeth for both: the same comparator
                against a different record (seed 1 vs reference; seed 2 vs
                seed 1) must FAIL.

``regime``      RUNS PROCESS.  The pre-declared probe (V4 list item 1a's
                question, asked as a diagnostic, not a campaign change):
                does Phase A's per-call ratio depend on the entry regime, and
                does it reach the in-loop value rho_B at an entry of the
                optimiser's own size?  Per config, arms A0 / A0p / A1 (A0p =
                flat + lift + pin: V4 item 1c, pulsed configs only; on st it
                composes to A0 and is recorded as skipped):
                  E0   the reference fixed point re-entered unperturbed
                       (seed 0) -- the floor of the predicate;
                  E2   the V3 delta-stream at delta = 0.01 and 0.001,
                       seeds 1-10 (the pin from the same stream, as V3);
                  E3   the gradient stencil's forward points: xcm[i] *
                       (1 + epsfcn) for every design variable i, coupling
                       state at the reference fixed point; on the pinned arms
                       also the lifted column, pin = ref * (1 + epsfcn);
                  E3b  the stencil's backward points entered from the forward
                       point's fixed point (A0's E3 exit for column i), i.e.
                       the 2 epsfcn step ``fcnvmc2`` actually takes.
                PRE-DECLARED PREDICTION (from ``factorise``): the in-loop
                flat arm averages 3.3-3.4 sweeps per evaluation and the block
                arm 2.1-2.8 per block, against Phase A's 5.0-5.8 and 3.0-5.8
                at delta = 0.10; a block sweep costs 4.1-4.6 nodes in Phase A
                and 4.4-5.2 in-loop because Phase A's extra sweeps land in
                the small blocks.  If the per-evaluation term of the gap is
                the entry regime, then at E3/E3b the ratio A1/A0 should move
                from rho_A(0.10) toward rho_B, and A1/A0p toward the in-loop
                B3/B1 ratio (eps = 1 exactly on that rung).
                PRE-DECLARED READING, per config: SUPPORTED if the E3b ratio
                is closer to rho_B than to rho_A(0.10) AND lies above
                rho_A(0.10); REFUTED if the E3b ratio is at or below
                rho_A(0.10) + 0.02 (the regime does not move it toward the
                in-loop value); INDETERMINATE otherwise.  Caution carried
                from the orchestrator's review: at a displacement of stencil
                size A0's own sweep count also drops toward its floor, so the
                movement is not guaranteed by the mechanism; that is exactly
                what the probe measures.  The delta-scan (E2) is read for
                monotonicity only.  No gate depends on this stage.

``tally``       READ-ONLY over the probe's records: per config x regime x arm
                the mean node calls per evaluation, sweeps, per-block sweeps;
                the ratios; the verdicts under the rule above; the committed
                summary JSON (docs/data) and the markdown tables the report
                pastes.

``all``         factorise, prepare, regime, tally.

Discipline: every PROCESS run is a fresh subprocess with PYTHONPATH pinned
to this script's own tree and ``process.__file__`` asserted against it
(traps T6/T10); counts only, wall clock stamped as progress information; no
run is retried; run records stay untracked under idf_probe/runs/a44/.  The
V3 records are read from the main checkout and never written.  Nothing
under arch_surgery/MDA_partitioning_experiment_v3/ is edited: its modules
are imported for the arm environments and the perturbation stream.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import statistics
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent                 # arch_surgery/idf_probe
TREE = HERE.parent.parent                              # this tree (worktree)
V3_DIR = TREE / "arch_surgery" / "MDA_partitioning_experiment_v3"
sys.path.insert(0, str(V3_DIR))
sys.path.insert(0, str(HERE))
import v3_config as cfg  # noqa: E402
import phase_a as pa  # noqa: E402  (env_for_phase_a, PIN_COMPONENT)
from v2_eval_one import perturb_factor  # noqa: E402

#: The frozen V3 campaign record: main checkout, untracked, READ ONLY.
V3_RECORDS = Path("/home/wrutten/projects/PROCESS_surgery/arch_surgery/"
                  "MDA_partitioning_experiment_v3/runs")
RUNS = HERE / "runs" / "a44"
SUMMARY = TREE / "arch_surgery" / "docs" / "data" / "a44_transfer_gap_summary.json"
DECKS = tuple(cfg.DECKS)
PULSED = tuple(cfg.PULSED)
SHORT = {"large_tokamak_nof": "nof", "low_aspect_ratio_DEMO": "lad",
         "st_regression": "st"}
B_ARMS = ("R", "B0", "B1", "B2", "B3")
A_ARMS = ("A0", "A0p", "A1")
#: V3 report section 5.5: node_calls_solve_phase sums over the identical-
#: converged set (exact integers, the identity check's reference).
PUBLISHED_SUMS = {
    "large_tokamak_nof": {"n": 22, "R": 912555, "B0": 935340, "B1": 942522,
                          "B2": 834951, "B3": 598124},
    "low_aspect_ratio_DEMO": {"n": 11, "R": 1869378, "B0": 1814967,
                              "B1": 1255695, "B2": 1134299, "B3": 817436},
    "st_regression": {"n": 22, "R": 2791089, "B0": 2332155, "B2": 1979117,
                      "B3": 1243161},
}
#: V3 report section 6: Phase A A0->A1 per-call ratio (ratio of sums).
PUBLISHED_RHO_A = {"large_tokamak_nof": 0.5217, "low_aspect_ratio_DEMO": 0.568,
                   "st_regression": 0.5016}
PROBE_DELTAS = (0.01, 0.001)
PROBE_SEEDS = tuple(range(1, 11))
REFUTE_MARGIN = 0.02


def _say(*a):
    print(*a, flush=True)


def _dump(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=False))


def _provenance() -> dict:
    def g(*args):
        try:
            return subprocess.run(["git", "-C", str(TREE), *args],
                                  capture_output=True, text=True,
                                  timeout=60).stdout.strip()
        except Exception:
            return None
    return {"tree": str(TREE), "git_head": g("rev-parse", "HEAD"),
            "git_branch": g("rev-parse", "--abbrev-ref", "HEAD"),
            "git_dirty": bool(g("status", "--porcelain",
                                "--untracked-files=no")),
            "python": sys.executable, "v3_records": str(V3_RECORDS)}


# --------------------------------------------------------------------------
# V3 record access (read-only)
# --------------------------------------------------------------------------


def _v3_runs(phase: str, deck: str, arm: str) -> dict:
    root = V3_RECORDS / phase / "campaign" / deck / arm
    out = {}
    for d in sorted(root.glob("start*")):
        m = d / "metrics.json"
        if m.exists():
            out[int(d.name[5:])] = json.loads(m.read_text())
    return out


def _conv(m: dict) -> bool:
    return (m.get("status") == "ok"
            and (m.get("mfile") or {}).get("ifail") == 1)


def _ok(m: dict) -> bool:
    return m.get("status") == "ok"


def _bfields(m: dict) -> dict:
    """The exact fields the factorisation divides, checked for consistency."""
    spe = m["sweeps_per_eval"]
    mst = m["module_solve_totals"] or {}
    # Arm R (PROCESS as shipped) runs with the module-solve driver off, so its
    # module_solve_totals are all zero; the driver's sweeps_per_eval counters
    # are the only evaluation count there and are taken as such.  On every
    # other arm the two counters must agree exactly.
    counters_cross_checked = bool(mst.get("n_call_models"))
    if counters_cross_checked:
        if spe["n_evaluations"] != mst["n_call_models"]:
            raise SystemExit(f"record {m['outdir']}: sweeps_per_eval.n_evaluations "
                             f"!= module_solve_totals.n_call_models")
        if spe["n_sweeps"] != mst["block_sweeps"]:
            raise SystemExit(f"record {m['outdir']}: n_sweeps != block_sweeps")
    pst = m.get("post_solve_totals") or {}
    P = len(pst.get("executed_once") or [])
    ef = m.get("exit_forensics") or {}
    return {
        "N": int(m["node_calls_solve_phase"]),
        "counters_cross_checked": counters_cross_checked,
        "P": P,
        "C": int(spe["n_evaluations"]),
        "S": int(spe["n_sweeps"]),
        "nvar": int(m["nvar"]),
        "iters": int(m["n_solver_iterations"]),
        "iters_summed": int(ef.get("n_solver_iterations_summed_over_attempts")
                            or m["n_solver_iterations"]),
        "attempts": int(ef.get("n_attempts") or 1),
        "ladder": ef.get("ladder_stage"),
        "blocks": dict(mst.get("inner_sweeps_by_block") or {}),
        "census": dict((m.get("node_census") or {}).get(
            "per_node_counted_through_Caller_node") or {}),
        "schedule": m.get("arch_block_schedule"),
        "hoist": m.get("arch_hoist_nodes"),
        "post_solve_nodes": pst.get("nodes"),
    }


def _problem_calls(f: dict) -> float:
    return f["C"] / (2 * (f["nvar"] + 1))


def _afields(m: dict) -> dict:
    mst = m["module_solve_totals"]
    return {"N": int(m["node_calls_single_eval"]),
            "S": int(m["n_model_calls_sweeps"]),
            "blocks": dict(mst.get("inner_sweeps_by_block") or {}),
            "census": dict((m.get("node_census") or {}).get("counted") or {})}


def _executing_nodes_per_block(f: dict) -> dict:
    """Executing (non-dispatch-dead) nodes per block from one run's census:
    a node counts as executing in its block when its census count is at
    least the block's sweep count (dispatch-conditional nodes such as
    aluminium_tf_coil never run on these decks and show 0)."""
    out = {}
    for name, nodes, _live in (f["schedule"] or []):
        sw = f["blocks"].get(name, 0)
        ex = [n for n in nodes if sw > 0 and f["census"].get(n, 0) >= sw]
        out[name] = {"n_executing": len(ex), "executing": ex,
                     "n_listed": len(nodes)}
    return out


def _rung(a: dict, b: dict) -> dict:
    """Factorisation of arm b against arm a over one seed set (sums given)."""
    R = b["N"] / a["N"]
    rho = (b["N"] / b["C"]) / (a["N"] / a["C"])
    rho_inloop = ((b["N"] - b["P"]) / b["C"]) / ((a["N"] - a["P"]) / a["C"])
    eps = b["C"] / a["C"]
    nv = (b["nvar"] + 1) / (a["nvar"] + 1)
    pc = b["pc"] / a["pc"]
    return {"R": R, "rho": rho, "rho_inloop": rho_inloop, "eps": eps,
            "eps_nvar_factor": nv, "eps_problem_call_factor": pc,
            "identity_R_equals_rho_times_eps": abs(R - rho * eps) < 1e-12,
            "identity_eps_equals_nv_times_pc": abs(eps - nv * pc) < 1e-12,
            "iters_ratio_final_attempt": b["iters"] / a["iters"],
            "iters_ratio_summed_attempts": b["iters_summed"] / a["iters_summed"]}


def _sums(runs: dict, fields: dict, seeds) -> dict:
    keys = ("N", "P", "C", "S", "iters", "iters_summed")
    out = {k: sum(fields[s][k] for s in seeds) for k in keys}
    out["pc"] = sum(_problem_calls(fields[s]) for s in seeds)
    out["nvar"] = sorted({fields[s]["nvar"] for s in seeds})
    if len(out["nvar"]) != 1:
        raise SystemExit(f"nvar differs within one arm: {out['nvar']}")
    out["nvar"] = out["nvar"][0]
    out["n_retried"] = sum(1 for s in seeds if fields[s]["attempts"] > 1)
    out["retried_seeds"] = [s for s in seeds if fields[s]["attempts"] > 1]
    out["n"] = len(seeds)
    blocks = {}
    for s in seeds:
        for k, v in fields[s]["blocks"].items():
            blocks[k] = blocks.get(k, 0) + v
    out["block_sweeps"] = blocks
    out["block_sweeps_per_eval"] = {k: v / out["C"] for k, v in blocks.items()}
    out["calls_per_eval"] = out["N"] / out["C"]
    out["inloop_calls_per_eval"] = (out["N"] - out["P"]) / out["C"]
    out["sweeps_per_eval"] = out["S"] / out["C"]
    out["nodes_per_sweep"] = (out["N"] - out["P"]) / out["S"]
    out["problem_calls_per_iter_final"] = out["pc"] / out["iters"]
    out["problem_calls_per_iter_summed"] = out["pc"] / out["iters_summed"]
    return out


def stage_factorise() -> int:
    if not V3_RECORDS.exists():
        raise SystemExit(f"V3 records not found at {V3_RECORDS}")
    rec = {"stage": "factorise", "provenance": _provenance(),
           "definitions": {
               "N": "node_calls_solve_phase (model-node executions before "
                    "write_output_files; includes the once-per-run "
                    "post-solve executions P, excludes MDA_Output's flat "
                    "sweeps and the uncharged exit audit)",
               "P": "len(post_solve_totals.executed_once): once-per-run "
                    "post-solve executions inside N (0 on flat arms)",
               "C": "sweeps_per_eval.n_evaluations == "
                    "module_solve_totals.n_call_models: call_models "
                    "evaluations in the solve phase, all attempts",
               "S": "sweeps_per_eval.n_sweeps == module_solve_totals."
                    "block_sweeps: dispatch sweeps (flat: 21 nodes each; "
                    "block: one block each)",
               "problem_calls": "C / (2 (nvar+1)): VMCON problem evaluations "
                                "(fcnvmc1 + fcnvmc2 = 1 + 2 nvar + 1 "
                                "call_models), asserted integer per run",
               "iters": "n_solver_iterations (final attempt: the check-2 "
                        "statistic); iters_summed adds failed attempts",
               "rho_A": "sum over 25 seeds of node_calls_single_eval, A1/A0 "
                        "(the V3 report section 6 construction)",
               "seed set": "identical-converged: status ok AND MFILE ifail "
                           "== 1 in BOTH arms of the pair (B0 and B3 for the "
                           "headline; the same B0/B3 set is used for every "
                           "rung so one n applies per config)",
           },
           "decks": {}}
    teeth = {}
    for deck in DECKS:
        d: dict = {"deck": deck}
        B = {a: _v3_runs("phase_b", deck, a) for a in B_ARMS}
        B = {a: r for a, r in B.items() if r}
        F = {a: {s: _bfields(m) for s, m in r.items() if _ok(m)}
             for a, r in B.items()}
        conv = {a: {s for s, m in r.items() if _conv(m)} for a, r in B.items()}
        S03 = sorted(conv["B0"] & conv["B3"])
        Sok = sorted(s for s in B["B0"] if s in B["B3"]
                     and _ok(B["B0"][s]) and _ok(B["B3"][s]))
        d["identical_converged_seeds"] = S03
        d["identical_ok_seeds"] = Sok
        # divisibility check: C = 2(nvar+1) * integer, every ok run
        bad = [(a, s) for a in F for s in F[a]
               if abs(_problem_calls(F[a][s]) - round(_problem_calls(F[a][s]))) > 1e-9]
        d["evaluations_per_problem_call_2nvar_plus_2_exact_everywhere"] = not bad
        d["divisibility_violations"] = bad
        # sums per arm over S03 (only arms converged on every seed of S03)
        sums = {}
        for a in F:
            if all(s in F[a] and s in conv[a] for s in S03):
                sums[a] = _sums(B[a], F[a], S03)
            else:
                missing = [s for s in S03 if not (s in F[a] and s in conv[a])]
                sums[a] = _sums(B[a], F[a], [s for s in S03 if s in F[a] and s in conv[a]])
                sums[a]["not_converged_on"] = missing
        d["sums_identical_converged"] = sums
        # identity with the published sums (exact integers)
        pub = PUBLISHED_SUMS[deck]
        ident = {a: (sums[a]["N"] == pub[a]) for a in pub if a != "n" and a in sums}
        ident["n"] = (len(S03) == pub["n"])
        d["published_sum_identity"] = ident
        d["published_sum_identity_all"] = all(ident.values())
        # rungs
        rungs = {}
        for a, b in (("B0", "B3"), ("B0", "B1"), ("B1", "B2"), ("B2", "B3"),
                     ("B1", "B3"), ("B0", "B2"), ("R", "B0")):
            if a in sums and b in sums and "not_converged_on" not in sums[a] \
                    and "not_converged_on" not in sums[b]:
                rungs[f"{a}->{b}"] = _rung(sums[a], sums[b])
        d["rungs"] = rungs
        # Phase A
        A = {a: _v3_runs("phase_a", deck, a) for a in ("A0", "A1u", "A1")}
        AF = {a: {s: _afields(m) for s, m in r.items() if _ok(m)}
              for a, r in A.items()}
        sa = sorted(set(AF["A0"]) & set(AF["A1"]))
        pa_sum = {}
        for a in AF:
            N = sum(AF[a][s]["N"] for s in sa)
            S_ = sum(AF[a][s]["S"] for s in sa)
            bl = {}
            for s in sa:
                for k, v in AF[a][s]["blocks"].items():
                    bl[k] = bl.get(k, 0) + v
            pa_sum[a] = {"n": len(sa), "N": N, "S": S_, "calls_per_eval": N / len(sa),
                         "sweeps_per_eval": S_ / len(sa), "nodes_per_sweep": N / S_,
                         "block_sweeps_per_eval": {k: v / len(sa) for k, v in bl.items()}}
        rho_A = pa_sum["A1"]["N"] / pa_sum["A0"]["N"]
        ratios = [AF["A1"][s]["N"] / AF["A0"][s]["N"] for s in sa]
        d["phase_a"] = {"seeds_n": len(sa), "arms": pa_sum,
                        "rho_A_ratio_of_sums": rho_A,
                        "rho_A_mean_of_ratios": statistics.mean(ratios),
                        "rho_A_median_of_ratios": statistics.median(ratios),
                        "rho_A_published": PUBLISHED_RHO_A[deck],
                        "rho_A_matches_published_4dp": round(rho_A, 4) == round(PUBLISHED_RHO_A[deck], 4)}
        # the gap
        g = rungs["B0->B3"]
        d["gap"] = {"R_over_rho_A": g["R"] / rho_A,
                    "rho_B_over_rho_A": g["rho"] / rho_A,
                    "rho_B_inloop_over_rho_A": g["rho_inloop"] / rho_A,
                    "eps": g["eps"],
                    "identity_holds": abs(g["R"] / rho_A - (g["rho"] / rho_A) * g["eps"]) < 1e-12,
                    "flat_shortening_calls_per_eval_A0_over_B0": pa_sum["A0"]["calls_per_eval"] / sums["B0"]["calls_per_eval"],
                    "block_shortening_calls_per_eval_A1_over_B3": pa_sum["A1"]["calls_per_eval"] / sums["B3"]["inloop_calls_per_eval"],
                    "flat_shortening_sweeps_A0_over_B0": pa_sum["A0"]["sweeps_per_eval"] / sums["B0"]["sweeps_per_eval"],
                    "block_shortening_sweeps_A1_over_B3": pa_sum["A1"]["sweeps_per_eval"] / sums["B3"]["sweeps_per_eval"],
                    "nodes_per_block_sweep_phase_a_A1": pa_sum["A1"]["nodes_per_sweep"],
                    "nodes_per_block_sweep_inloop_B3": sums["B3"]["nodes_per_sweep"],
                    "nodes_per_flat_sweep_phase_a_A0": pa_sum["A0"]["nodes_per_sweep"],
                    "nodes_per_flat_sweep_inloop_B0": sums["B0"]["nodes_per_sweep"]}
        d["gap"]["sweep_unit_asymmetry_prediction"] = (
            d["gap"]["flat_shortening_sweeps_A0_over_B0"]
            / d["gap"]["block_shortening_sweeps_A1_over_B3"])
        d["gap"]["node_unit_asymmetry"] = (
            d["gap"]["flat_shortening_calls_per_eval_A0_over_B0"]
            / d["gap"]["block_shortening_calls_per_eval_A1_over_B3"])
        d["executing_nodes_per_block_B3"] = _executing_nodes_per_block(F["B3"][S03[0]])
        d["hoist_B3"] = F["B3"][S03[0]]["hoist"]
        d["post_solve_nodes_B3"] = F["B3"][S03[0]]["post_solve_nodes"]
        d["executing_nodes_B0"] = sum(1 for v in F["B0"][S03[0]]["census"].values()
                                      if v >= F["B0"][S03[0]]["S"])
        # retry accounting: eps and R without any seed retried in either arm
        retried = sorted(set(sums["B0"]["retried_seeds"]) | set(sums["B3"]["retried_seeds"]))
        S_nr = [s for s in S03 if s not in retried]
        if retried:
            s0 = _sums(B["B0"], F["B0"], S_nr)
            s3 = _sums(B["B3"], F["B3"], S_nr)
            d["retry_accounting"] = {
                "retried_seeds_B0_or_B3": retried,
                "n_without": len(S_nr),
                "B0->B3_without_retried": _rung(s0, s3),
                "B0->B3_with_retried": g,
                "note": "the identical-converged construction COUNTS the "
                        "failed attempts' evaluations in N and C (they are "
                        "real cost to reach convergence) but check 2's "
                        "n_solver_iterations is the final attempt's only",
            }
        else:
            d["retry_accounting"] = {"retried_seeds_B0_or_B3": [], "note": "no retry in the set"}
        # per-seed table
        d["per_seed"] = {}
        for s in S03:
            row = {}
            for a in F:
                if s in F[a]:
                    f = F[a][s]
                    row[a] = {"N": f["N"], "C": f["C"], "problem_calls": round(_problem_calls(f)),
                              "iters": f["iters"], "iters_summed": f["iters_summed"],
                              "attempts": f["attempts"], "ladder": f["ladder"],
                              "converged": s in conv[a]}
            d["per_seed"][s] = row
        # pulsed: B1 == B2 == B3 per seed?
        if deck in PULSED:
            same = [s for s in S03 if all(
                s in F[a] and F[a][s]["C"] == F["B3"][s]["C"]
                and F[a][s]["iters"] == F["B3"][s]["iters"] for a in ("B1", "B2"))]
            d["B1_B2_B3_identical_C_and_iters_seeds"] = same
            d["B1_B2_B3_identical_on_all_converged_seeds"] = (len(same) == len(S03))
            diff01 = [s for s in S03 if F["B0"][s]["C"] // (2 * (F["B0"][s]["nvar"] + 1))
                      != F["B1"][s]["C"] // (2 * (F["B1"][s]["nvar"] + 1))]
            d["B0_B1_problem_calls_differ_seeds"] = diff01
        else:
            def pc(a, s):
                return round(_problem_calls(F[a][s]))
            d["st_rung_split"] = {
                "B0->B2_differ": [s for s in S03 if s in F["B2"] and pc("B0", s) != pc("B2", s)],
                "B2->B3_differ": [s for s in S03 if s in F["B2"] and pc("B2", s) != pc("B3", s)],
                "both_differ": [s for s in S03 if s in F["B2"] and pc("B0", s) != pc("B2", s) and pc("B2", s) != pc("B3", s)],
                "B0->B3_differ": [s for s in S03 if pc("B0", s) != pc("B3", s)],
                "B2_not_converged": [s for s in S03 if s not in conv.get("B2", set())],
                "note": "problem-calls (C / 2(nvar+1)) compared per seed; "
                        "A43 (st-trust-gap) owns the B2->B3 half",
            }
        rec["decks"][deck] = d
        # teeth (in memory only)
        f3 = dict(F["B3"][S03[0]]); f3["N"] += 1
        F3 = dict(F["B3"]); F3[S03[0]] = f3
        t_sum = _sums(B["B3"], F3, S03)["N"] == pub["B3"]
        fc = dict(F["B0"][S03[0]]); fc["C"] += 1
        t_div = abs(_problem_calls(fc) - round(_problem_calls(fc))) > 1e-9
        teeth[deck] = {"plus_one_node_call_breaks_published_sum_identity": (not t_sum),
                       "plus_one_evaluation_breaks_divisibility": t_div}
    rec["teeth"] = teeth
    rec["teeth_all_tripped"] = all(all(v.values()) for v in teeth.values())
    rec["verdict"] = ("PASS" if all(rec["decks"][d]["published_sum_identity_all"]
                                    and rec["decks"][d]["phase_a"]["rho_A_matches_published_4dp"]
                                    and rec["decks"][d]["evaluations_per_problem_call_2nvar_plus_2_exact_everywhere"]
                                    for d in DECKS) and rec["teeth_all_tripped"] else "FAIL")
    _dump(RUNS / "factorisation.json", rec)
    _say(_factorise_tables(rec))
    (RUNS / "factorisation.md").write_text(_factorise_tables(rec))
    _say(f"factorise: {rec['verdict']} -> {RUNS / 'factorisation.json'}")
    return 0 if rec["verdict"] == "PASS" else 1


def _factorise_tables(rec: dict) -> str:
    L = []
    L.append("| config | n | R_e2e = N_B3/N_B0 | rho_A | rho_B | rho_B/rho_A | eps | eps: (nvar+1) factor | eps: problem-call factor | gap R/rho_A |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    for deck in DECKS:
        d = rec["decks"][deck]; g = d["rungs"]["B0->B3"]; ga = d["gap"]
        L.append(f"| {SHORT[deck]} | {len(d['identical_converged_seeds'])} | {g['R']:.4f} | {d['phase_a']['rho_A_ratio_of_sums']:.4f} | {g['rho']:.4f} | {ga['rho_B_over_rho_A']:.4f} | {g['eps']:.4f} | {g['eps_nvar_factor']:.4f} | {g['eps_problem_call_factor']:.4f} | {ga['R_over_rho_A']:.4f} |")
    L.append("")
    L.append("| config | arm | calls/eval | in-loop calls/eval | sweeps/eval | nodes/sweep | block sweeps/eval | problem-calls | iters (final) | iters (summed) | retried seeds |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for deck in DECKS:
        d = rec["decks"][deck]
        for a in ("A0", "A1"):
            p = d["phase_a"]["arms"][a]
            bl = ", ".join(f"{k} {v:.2f}" for k, v in p["block_sweeps_per_eval"].items() if v)
            L.append(f"| {SHORT[deck]} | {a} (δ=0.10) | {p['calls_per_eval']:.2f} | {p['calls_per_eval']:.2f} | {p['sweeps_per_eval']:.2f} | {p['nodes_per_sweep']:.3f} | {bl} | — | — | — | — |")
        for a in B_ARMS:
            if a in d["sums_identical_converged"] and "not_converged_on" not in d["sums_identical_converged"][a]:
                s = d["sums_identical_converged"][a]
                bl = ", ".join(f"{k} {v:.2f}" for k, v in s["block_sweeps_per_eval"].items() if v)
                L.append(f"| {SHORT[deck]} | {a} | {s['calls_per_eval']:.2f} | {s['inloop_calls_per_eval']:.2f} | {s['sweeps_per_eval']:.2f} | {s['nodes_per_sweep']:.3f} | {bl} | {s['pc']:.0f} | {s['iters']} | {s['iters_summed']} | {s['retried_seeds']} |")
    L.append("")
    L.append("| config | rung | R | rho | eps | (nvar+1) factor | problem-call factor | iters ratio (final) | iters ratio (summed) |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for deck in DECKS:
        for k, g in rec["decks"][deck]["rungs"].items():
            L.append(f"| {SHORT[deck]} | {k} | {g['R']:.4f} | {g['rho']:.4f} | {g['eps']:.4f} | {g['eps_nvar_factor']:.4f} | {g['eps_problem_call_factor']:.4f} | {g['iters_ratio_final_attempt']:.4f} | {g['iters_ratio_summed_attempts']:.4f} |")
    L.append("")
    for deck in DECKS:
        ra = rec["decks"][deck]["retry_accounting"]
        if ra.get("retried_seeds_B0_or_B3"):
            w = ra["B0->B3_with_retried"]; wo = ra["B0->B3_without_retried"]
            L.append(f"- {SHORT[deck]} retry accounting: retried seeds {ra['retried_seeds_B0_or_B3']}; with: R {w['R']:.4f} rho {w['rho']:.4f} eps {w['eps']:.4f}; without (n={ra['n_without']}): R {wo['R']:.4f} rho {wo['rho']:.4f} eps {wo['eps']:.4f}")
    return "\n".join(L)


# --------------------------------------------------------------------------
# PROCESS runs: one isolated single evaluation
# --------------------------------------------------------------------------


def _env_for(deck: str, arm: str, pin_hex: str | None) -> dict:
    if arm in ("A0", "A1"):
        env = pa.env_for_phase_a(deck, arm, pin_hex=pin_hex)
    elif arm == "A0p":
        if deck not in PULSED:
            raise SystemExit("A0p composes to A0 on a k = 0 deck; skipped, never run")
        if pin_hex is None:
            raise SystemExit("A0p needs a pin value")
        env = pa.env_for_phase_a(deck, "A0")
        env["PROCESS_ARCH_LIFT"] = "burn_time"
        env["PROCESS_ARCH_PIN_BURN_TIME"] = pin_hex
    else:
        raise SystemExit(f"unknown arm {arm!r}")
    env["PYTHONPATH"] = str(TREE)
    env["MPLCONFIGDIR"] = str(RUNS / "_mplconfig")
    return env


def eval_job(deck: str, arm: str, outdir: Path, *, entry_state: Path | None = None,
             delta: float | None = None, seed: int = 0, pin_hex: str | None = None,
             x_fd: tuple | None = None, resume: bool = True, timeout: int = 1800) -> dict:
    key = {"a44_deck": deck, "a44_arm": arm, "a44_seed": seed, "a44_delta": delta,
           "a44_pin_hex": pin_hex, "a44_x_fd": list(x_fd) if x_fd else None,
           "a44_entry_state": str(entry_state) if entry_state else None}
    mpath = outdir / "metrics.json"
    if resume and mpath.exists():
        try:
            prev = json.loads(mpath.read_text())
        except Exception:
            prev = {}
        if prev.get("status") == "ok" and all(prev.get(k) == v for k, v in key.items()):
            return {"outdir": str(outdir), "rc": 0, "status": "ok", "resumed": True}
    if outdir.exists():
        shutil.rmtree(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    (RUNS / "_mplconfig").mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, str(HERE / "a44_eval_one.py"),
           "--scenario", deck,
           "--input", str(cfg.IDF_PROBE / "scenarios" / f"{deck}.IN.DAT"),
           "--outdir", str(outdir), "--expect-tree", str(TREE),
           "--perturb-spec", str(cfg.ystate_for(deck)),
           "--exit-audit", str(cfg.ystate_for(deck)),
           "--audit-exclude-postsolve", str(cfg.postsolve_for(deck)),
           "--seed", str(seed), "--node-census"]
    if delta is not None:
        cmd += ["--delta", repr(delta)]
    if entry_state is not None:
        cmd += ["--entry-state", str(entry_state)]
    if x_fd is not None:
        cmd += ["--x-fd-column", str(x_fd[0]), "--x-fd-sign", str(x_fd[1])]
    env = _env_for(deck, arm, pin_hex)
    t0 = time.perf_counter()
    try:
        proc = subprocess.run(cmd, env=env, capture_output=True, text=True,
                              cwd=str(outdir), timeout=timeout)
        rc = proc.returncode
        (outdir / "stdout.log").write_text(proc.stdout)
        (outdir / "stderr.log").write_text(proc.stderr)
    except subprocess.TimeoutExpired as exc:
        rc = 124
        (outdir / "stdout.log").write_text(exc.stdout or "")
        (outdir / "stderr.log").write_text((exc.stderr or "") + "\nTIMEOUT")
    if not mpath.exists():
        mpath.write_text(json.dumps({"status": "timeout" if rc == 124 else "no_metrics",
                                     "returncode": rc}, indent=2))
    rec = json.loads(mpath.read_text())
    rec.update(key)
    rec["a44_wall_s_progress_only"] = time.perf_counter() - t0
    mpath.write_text(json.dumps(rec, indent=2))
    _say(f"  {SHORT[deck]:3s} {arm:3s} {outdir.name:12s} rc={rc} status={rec.get('status')} "
         f"calls={rec.get('node_calls_single_eval')} sweeps={rec.get('n_model_calls_sweeps')} "
         f"{time.perf_counter() - t0:5.1f}s (progress only)")
    return {"outdir": str(outdir), "rc": rc, "status": rec.get("status")}


def _pool(jobs: list[dict], workers: int) -> list[dict]:
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = [pool.submit(eval_job, **j) for j in jobs]
        return [f.result() for f in futs]


def _metrics(outdir: Path) -> dict:
    return json.loads((Path(outdir) / "metrics.json").read_text())


def _state(path: Path) -> dict:
    return json.loads(Path(path).read_text())["state"]


def _compare_single(mine: dict, ref: dict) -> dict:
    """The identity comparator: exact counts, per-block sweeps, audit hex."""
    def g(m, *ks):
        v = m
        for k in ks:
            v = (v or {}).get(k) if isinstance(v, dict) else None
        return v
    cells = {
        "node_calls_single_eval": (mine.get("node_calls_single_eval"), ref.get("node_calls_single_eval")),
        "n_model_calls_sweeps": (mine.get("n_model_calls_sweeps"), ref.get("n_model_calls_sweeps")),
        "inner_sweeps_by_block": (g(mine, "module_solve_totals", "inner_sweeps_by_block"),
                                  g(ref, "module_solve_totals", "inner_sweeps_by_block")),
        "exit_audit_residual_max_hex": (g(mine, "exit_audit", "residual_max_hex"),
                                        g(ref, "exit_audit", "residual_max_hex")),
        "exit_audit_restricted_max_hex": (g(mine, "exit_audit", "restricted", "residual_max_hex"),
                                          g(ref, "exit_audit", "restricted", "residual_max_hex")),
        "t_plant_pulse_burn_hex": (mine.get("t_plant_pulse_burn_hex"), ref.get("t_plant_pulse_burn_hex")),
        "objf_hex": (g(mine, "exact", "objf"), g(ref, "exact", "objf")),
        "n_prime_calls": (mine.get("n_prime_calls"), ref.get("n_prime_calls")),
    }
    return {"cells": {k: {"mine": a, "ref": b, "equal": a == b} for k, (a, b) in cells.items()},
            "all_equal": all(a == b for a, b in cells.values()),
            "n_cells": len(cells)}


def stage_prepare(workers: int) -> int:
    rec = {"stage": "prepare", "provenance": _provenance(), "decks": {}}
    all_pass = True
    for deck in DECKS:
        d: dict = {}
        droot = RUNS / deck
        # 1. the reference under this tree
        _say(f"\n{deck}: reference (A0 cold deck point) under {TREE}")
        r = eval_job(deck, "A0", droot / "reference", seed=0)
        mine = _metrics(r["outdir"])
        v3ref_dir = V3_RECORDS / "phase_a" / "campaign" / deck / "reference"
        v3ref = json.loads((v3ref_dir / "metrics.json").read_text())
        cmp = _compare_single(mine, v3ref)
        st_mine = _state(Path(r["outdir"]) / "y_exit.json")
        st_ref = _state(v3ref_dir / "y_exit.json")
        cmp["y_exit_state_bit_identical"] = (st_mine == st_ref)
        cmp["y_exit_n_components"] = len(st_ref)
        cmp["y_exit_n_differing"] = sum(1 for k in st_ref if st_mine.get(k) != st_ref[k])
        cmp["all_equal"] = cmp["all_equal"] and cmp["y_exit_state_bit_identical"]
        # teeth: the same comparator, V3's reference vs V3's seed-1 A0 record
        v3s1 = json.loads((V3_RECORDS / "phase_a" / "campaign" / deck / "A0" / "start001" / "metrics.json").read_text())
        tooth = _compare_single(v3s1, v3ref)
        cmp["teeth_reference_vs_seed1_must_fail"] = (not tooth["all_equal"])
        d["reference_identity"] = cmp
        d["reference"] = {"outdir": r["outdir"], "status": mine.get("status"),
                          "node_calls": mine.get("node_calls_single_eval"),
                          "sweeps": mine.get("n_model_calls_sweeps"),
                          "t_plant_pulse_burn_hex": mine.get("t_plant_pulse_burn_hex"),
                          "epsfcn": mine.get("epsfcn"), "nvar": mine.get("nvar")}
        if mine.get("status") != "ok":
            d["refused"] = "reference did not converge under this tree"
            rec["decks"][deck] = d
            all_pass = False
            continue
        snap = Path(r["outdir"]) / "y_exit.json"
        ref_burn = float.fromhex(mine["t_plant_pulse_burn_hex"])
        # 2. seed 1 at delta = 0.10, A0 and A1, vs V3's records
        pin1 = (ref_burn * perturb_factor(1, pa.PIN_COMPONENT, cfg.DELTA)).hex() if deck in PULSED else None
        jobs = [dict(deck=deck, arm="A0", outdir=droot / "identity" / "A0" / "start001",
                     entry_state=snap, delta=cfg.DELTA, seed=1),
                dict(deck=deck, arm="A1", outdir=droot / "identity" / "A1" / "start001",
                     entry_state=snap, delta=cfg.DELTA, seed=1, pin_hex=pin1)]
        _say(f"{deck}: identity runs (seed 1, delta = {cfg.DELTA}, A0 + A1)")
        res = _pool(jobs, workers)
        d["identity"] = {}
        for j, rr in zip(jobs, res):
            arm = j["arm"]
            m = _metrics(rr["outdir"])
            v3 = json.loads((V3_RECORDS / "phase_a" / "campaign" / deck / arm / "start001" / "metrics.json").read_text())
            c = _compare_single(m, v3)
            if arm == "A1" and deck in PULSED:
                c["pin_hex_matches_v3"] = (m.get("env_PROCESS_ARCH_PIN_BURN_TIME") == v3.get("env_PROCESS_ARCH_PIN_BURN_TIME"))
                c["all_equal"] = c["all_equal"] and c["pin_hex_matches_v3"]
            v3s2 = json.loads((V3_RECORDS / "phase_a" / "campaign" / deck / arm / "start002" / "metrics.json").read_text())
            c["teeth_seed1_vs_seed2_must_fail"] = (not _compare_single(v3s2, v3)["all_equal"])
            d["identity"][arm] = c
        d["verdict"] = ("PASS" if cmp["all_equal"] and cmp["teeth_reference_vs_seed1_must_fail"]
                        and all(c["all_equal"] and c["teeth_seed1_vs_seed2_must_fail"]
                                for c in d["identity"].values()) else "FAIL")
        all_pass = all_pass and d["verdict"] == "PASS"
        _say(f"{deck}: prepare {d['verdict']}")
        rec["decks"][deck] = d
    rec["verdict"] = "PASS" if all_pass else "FAIL"
    _dump(RUNS / "prepare.json", rec)
    _say(f"prepare: {rec['verdict']} -> {RUNS / 'prepare.json'}")
    return 0 if all_pass else 1


def _arms_for(deck: str) -> tuple:
    return ("A0", "A0p", "A1") if deck in PULSED else ("A0", "A1")


def stage_regime(workers: int) -> int:
    prep = json.loads((RUNS / "prepare.json").read_text())
    if prep.get("verdict") != "PASS":
        raise SystemExit("prepare did not PASS; the regime probe does not run on an unverified tree")
    rec = {"stage": "regime", "provenance": _provenance(), "decks": {}}
    for deck in DECKS:
        droot = RUNS / deck
        ref = prep["decks"][deck]["reference"]
        snap = Path(ref["outdir"]) / "y_exit.json"
        ref_burn = float.fromhex(ref["t_plant_pulse_burn_hex"])
        eps = float(ref["epsfcn"])
        nvar = int(ref["nvar"])
        arms = _arms_for(deck)
        d = {"arms": list(arms), "epsfcn": eps, "nvar": nvar,
             "A0p_skipped": None if deck in PULSED else "k = 0 deck: A0p composes to A0"}
        pinned = lambda a: (a in ("A0p", "A1") and deck in PULSED)  # noqa: E731
        jobs = []
        # E0: the floor
        for a in arms:
            jobs.append(dict(deck=deck, arm=a, outdir=droot / "E0" / a / "seed000",
                             entry_state=snap, seed=0,
                             pin_hex=ref_burn.hex() if pinned(a) else None))
        # E2: the delta scan
        for delta in PROBE_DELTAS:
            for k in PROBE_SEEDS:
                pin = (ref_burn * perturb_factor(k, pa.PIN_COMPONENT, delta)).hex()
                for a in arms:
                    jobs.append(dict(deck=deck, arm=a,
                                     outdir=droot / f"E2_d{delta:g}" / a / f"seed{k:03d}",
                                     entry_state=snap, delta=delta, seed=k,
                                     pin_hex=pin if pinned(a) else None))
        # E3: forward stencil points
        for i in range(nvar):
            for a in arms:
                jobs.append(dict(deck=deck, arm=a, outdir=droot / "E3" / a / f"col{i:02d}p",
                                 entry_state=snap, seed=0, x_fd=(i, 1),
                                 pin_hex=ref_burn.hex() if pinned(a) else None))
        for a in arms:
            if pinned(a):
                jobs.append(dict(deck=deck, arm=a, outdir=droot / "E3" / a / "liftp",
                                 entry_state=snap, seed=0,
                                 pin_hex=(ref_burn * (1.0 + eps)).hex()))
        _say(f"\n{deck}: regime probe E0/E2/E3 — {len(jobs)} runs, {workers} workers")
        res = _pool(jobs, workers)
        d["E0_E2_E3"] = {"n_jobs": len(jobs), "n_ok": sum(1 for r in res if r["status"] == "ok"),
                         "failed": [r["outdir"] for r in res if r["status"] != "ok"]}
        # E3b: backward points from the forward point's fixed point (A0's exit)
        jobs = []
        for i in range(nvar):
            fwd = droot / "E3" / "A0" / f"col{i:02d}p" / "y_exit.json"
            if not fwd.exists():
                continue
            for a in arms:
                jobs.append(dict(deck=deck, arm=a, outdir=droot / "E3b" / a / f"col{i:02d}m",
                                 entry_state=fwd, seed=0, x_fd=(i, -1),
                                 pin_hex=ref_burn.hex() if pinned(a) else None))
        fwdl = droot / "E3" / "A0p" / "liftp" / "y_exit.json"
        if deck in PULSED and fwdl.exists():
            for a in arms:
                if pinned(a):
                    jobs.append(dict(deck=deck, arm=a, outdir=droot / "E3b" / a / "liftm",
                                     entry_state=fwdl, seed=0,
                                     pin_hex=(ref_burn * (1.0 - eps)).hex()))
        _say(f"{deck}: regime probe E3b — {len(jobs)} runs")
        res = _pool(jobs, workers)
        d["E3b"] = {"n_jobs": len(jobs), "n_ok": sum(1 for r in res if r["status"] == "ok"),
                    "failed": [r["outdir"] for r in res if r["status"] != "ok"]}
        rec["decks"][deck] = d
    _dump(RUNS / "regime.json", rec)
    _say(f"regime -> {RUNS / 'regime.json'}")
    return 0


def _regime_records(deck: str, regime: str, arm: str) -> list[dict]:
    root = RUNS / deck / regime / arm
    out = []
    for d in sorted(root.glob("*")):
        m = d / "metrics.json"
        if m.exists():
            out.append(json.loads(m.read_text()))
    return out


def _agg(records: list[dict]) -> dict | None:
    ok = [m for m in records if m.get("status") == "ok"]
    if not ok:
        return None
    N = sum(m["node_calls_single_eval"] for m in ok)
    S = sum(m["n_model_calls_sweeps"] for m in ok)
    bl = {}
    for m in ok:
        for k, v in (m["module_solve_totals"].get("inner_sweeps_by_block") or {}).items():
            bl[k] = bl.get(k, 0) + v
    return {"n_ok": len(ok), "n_records": len(records), "N": N, "S": S,
            "calls_per_eval": N / len(ok), "sweeps_per_eval": S / len(ok),
            "nodes_per_sweep": N / S if S else None,
            "block_sweeps_per_eval": {k: v / len(ok) for k, v in bl.items()},
            "calls_min": min(m["node_calls_single_eval"] for m in ok),
            "calls_max": max(m["node_calls_single_eval"] for m in ok),
            "failed": [m.get("outdir") for m in records if m.get("status") != "ok"]}


def stage_tally() -> int:
    fac = json.loads((RUNS / "factorisation.json").read_text())
    prep = json.loads((RUNS / "prepare.json").read_text())
    rec = {"stage": "tally", "provenance": _provenance(),
           "rule": {"supported": "E3b ratio A1/A0 closer to rho_B than to rho_A(0.10) AND above rho_A(0.10)",
                    "refuted": f"E3b ratio A1/A0 <= rho_A(0.10) + {REFUTE_MARGIN}",
                    "indeterminate": "otherwise"},
           "decks": {}}
    regimes = ["E0"] + [f"E2_d{d:g}" for d in PROBE_DELTAS] + ["E3", "E3b"]
    for deck in DECKS:
        f = fac["decks"][deck]
        rho_A = f["phase_a"]["rho_A_ratio_of_sums"]
        rho_B = f["rungs"]["B0->B3"]["rho_inloop"]
        rho_B13 = f["rungs"]["B1->B3"]["rho_inloop"] if "B1->B3" in f["rungs"] else None
        d = {"rho_A_0p10": rho_A, "rho_B_inloop_B3_over_B0": rho_B,
             "rho_inloop_B3_over_B1": rho_B13,
             "inloop_calls_per_eval": {a: f["sums_identical_converged"][a]["inloop_calls_per_eval"]
                                       for a in f["sums_identical_converged"]
                                       if "not_converged_on" not in f["sums_identical_converged"][a]},
             "inloop_sweeps_per_eval": {a: f["sums_identical_converged"][a]["sweeps_per_eval"]
                                        for a in f["sums_identical_converged"]
                                        if "not_converged_on" not in f["sums_identical_converged"][a]},
             "inloop_block_sweeps_per_eval_B3": f["sums_identical_converged"]["B3"]["block_sweeps_per_eval"],
             "regimes": {}}
        # the V3 regime row from the frozen records
        d["regimes"]["V3_d0.1"] = {a: {"calls_per_eval": f["phase_a"]["arms"][a]["calls_per_eval"],
                                       "sweeps_per_eval": f["phase_a"]["arms"][a]["sweeps_per_eval"],
                                       "nodes_per_sweep": f["phase_a"]["arms"][a]["nodes_per_sweep"],
                                       "block_sweeps_per_eval": f["phase_a"]["arms"][a]["block_sweeps_per_eval"],
                                       "n_ok": f["phase_a"]["arms"][a]["n"]}
                                   for a in ("A0", "A1")}
        d["regimes"]["V3_d0.1"]["ratio_A1_over_A0"] = rho_A
        for rg in regimes:
            row = {}
            for a in _arms_for(deck):
                ag = _agg(_regime_records(deck, rg, a))
                if ag:
                    row[a] = ag
            if "A0" in row and "A1" in row:
                row["ratio_A1_over_A0"] = row["A1"]["N"] / row["A0"]["N"] if row["A0"]["N"] else None
                row["n_pairs"] = min(row["A0"]["n_ok"], row["A1"]["n_ok"])
            if "A0p" in row and "A1" in row:
                row["ratio_A1_over_A0p"] = row["A1"]["N"] / row["A0p"]["N"]
            if "A0" in row and "A0p" in row:
                row["ratio_A0p_over_A0"] = row["A0p"]["N"] / row["A0"]["N"]
            d["regimes"][rg] = row
        # verdict
        r3 = (d["regimes"].get("E3b") or {}).get("ratio_A1_over_A0")
        r3f = (d["regimes"].get("E3") or {}).get("ratio_A1_over_A0")
        v = {}
        for name, r in (("E3b", r3), ("E3", r3f)):
            if r is None:
                v[name] = "NOT RUN"
            elif r <= rho_A + REFUTE_MARGIN:
                v[name] = "REFUTED"
            elif abs(r - rho_B) < abs(r - rho_A) and r > rho_A:
                v[name] = "SUPPORTED"
            else:
                v[name] = "INDETERMINATE"
        d["verdict_rule_on"] = "E3b (declared); E3 reported beside"
        d["verdict"] = v
        d["distance_to_inloop"] = {name: (None if r is None else r - rho_B) for name, r in (("E3b", r3), ("E3", r3f))}
        scan = [d["regimes"]["V3_d0.1"]["ratio_A1_over_A0"]] + [
            (d["regimes"].get(f"E2_d{dl:g}") or {}).get("ratio_A1_over_A0") for dl in PROBE_DELTAS]
        d["delta_scan_ratios_0.1_0.01_0.001"] = scan
        d["delta_scan_monotone_increasing"] = (all(x is not None for x in scan)
                                                and all(scan[i] < scan[i + 1] for i in range(len(scan) - 1)))
        rec["decks"][deck] = d
    _dump(RUNS / "tally.json", rec)
    md = _tally_tables(rec, fac)
    (RUNS / "tally.md").write_text(md)
    _say(md)
    summary = {"task": "A44 transfer-gap", "provenance": rec["provenance"],
               "factorise": {"verdict": fac["verdict"], "teeth_all_tripped": fac["teeth_all_tripped"],
                             "decks": {dk: {"n": len(fac["decks"][dk]["identical_converged_seeds"]),
                                            "rungs": fac["decks"][dk]["rungs"],
                                            "gap": fac["decks"][dk]["gap"],
                                            "phase_a": {k: v for k, v in fac["decks"][dk]["phase_a"].items() if k != "arms"},
                                            "retry_accounting": fac["decks"][dk]["retry_accounting"],
                                            "st_rung_split": fac["decks"][dk].get("st_rung_split"),
                                            "B1_B2_B3_identical_on_all_converged_seeds": fac["decks"][dk].get("B1_B2_B3_identical_on_all_converged_seeds"),
                                            "B0_B1_problem_calls_differ_seeds": fac["decks"][dk].get("B0_B1_problem_calls_differ_seeds")}
                                       for dk in DECKS}},
               "prepare": {"verdict": prep["verdict"],
                           "decks": {dk: {"verdict": prep["decks"][dk].get("verdict"),
                                          "reference": prep["decks"][dk].get("reference")} for dk in DECKS}},
               "regime": {dk: {"verdict": rec["decks"][dk]["verdict"],
                               "ratios": {rg: (rec["decks"][dk]["regimes"][rg].get("ratio_A1_over_A0"),
                                               rec["decks"][dk]["regimes"][rg].get("ratio_A1_over_A0p"))
                                          for rg in rec["decks"][dk]["regimes"]},
                               "rho_A_0p10": rec["decks"][dk]["rho_A_0p10"],
                               "rho_B_inloop": rec["decks"][dk]["rho_B_inloop_B3_over_B0"],
                               "rho_inloop_B3_over_B1": rec["decks"][dk]["rho_inloop_B3_over_B1"],
                               "delta_scan_ratios_0.1_0.01_0.001": rec["decks"][dk]["delta_scan_ratios_0.1_0.01_0.001"],
                               "per_arm": {rg: {a: {k: rec["decks"][dk]["regimes"][rg][a][k]
                                                    for k in ("n_ok", "calls_per_eval", "sweeps_per_eval", "nodes_per_sweep", "block_sweeps_per_eval")}
                                                for a in rec["decks"][dk]["regimes"][rg] if isinstance(rec["decks"][dk]["regimes"][rg][a], dict)}
                                           for rg in rec["decks"][dk]["regimes"]}}
                          for dk in DECKS}}
    _dump(SUMMARY, summary)
    _say(f"tally -> {RUNS / 'tally.json'}; committed summary -> {SUMMARY}")
    return 0


def _tally_tables(rec: dict, fac: dict) -> str:
    L = []
    L.append("| config | regime | n | A0 calls/eval | A0 sweeps | A0p calls/eval | A1 calls/eval | A1 sweeps | A1 blocks (M1/M2/M3) | A1/A0 | A1/A0p |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for deck in DECKS:
        d = rec["decks"][deck]
        for rg, row in d["regimes"].items():
            a0 = row.get("A0"); a1 = row.get("A1"); a0p = row.get("A0p")
            if not a0 or not a1:
                continue
            bl = a1["block_sweeps_per_eval"]
            blk = "/".join(f"{bl.get(k, 0):.2f}" for k in ("M1", "M2", "M3"))
            L.append(f"| {SHORT[deck]} | {rg} | {a1['n_ok']} | {a0['calls_per_eval']:.2f} | {a0['sweeps_per_eval']:.2f} | "
                     f"{a0p['calls_per_eval']:.2f} | " if a0p else f"| {SHORT[deck]} | {rg} | {a1['n_ok']} | {a0['calls_per_eval']:.2f} | {a0['sweeps_per_eval']:.2f} | — | ")
            L[-1] += (f"{a1['calls_per_eval']:.2f} | {a1['sweeps_per_eval']:.2f} | {blk} | {row.get('ratio_A1_over_A0'):.4f} | "
                      + (f"{row['ratio_A1_over_A0p']:.4f} |" if row.get("ratio_A1_over_A0p") else "— |"))
        ic = d["inloop_calls_per_eval"]; isw = d["inloop_sweeps_per_eval"]; b3 = d["inloop_block_sweeps_per_eval_B3"]
        blk = "/".join(f"{b3.get(k, 0):.2f}" for k in ("M1", "M2", "M3"))
        L.append(f"| {SHORT[deck]} | **in-loop (V3 Phase B)** | — | {ic['B0']:.2f} | {isw['B0']:.2f} | "
                 + (f"{ic['B1']:.2f} | " if "B1" in ic else "— | ")
                 + f"{ic['B3']:.2f} | {isw['B3']:.2f} | {blk} | **{d['rho_B_inloop_B3_over_B0']:.4f}** | "
                 + (f"**{d['rho_inloop_B3_over_B1']:.4f}** |" if d["rho_inloop_B3_over_B1"] else "— |"))
    L.append("")
    for deck in DECKS:
        d = rec["decks"][deck]
        L.append(f"- {SHORT[deck]}: verdict E3b **{d['verdict']['E3b']}**, E3 {d['verdict']['E3']}; "
                 f"rho_A(0.10) = {d['rho_A_0p10']:.4f}, rho_B in-loop = {d['rho_B_inloop_B3_over_B0']:.4f}; "
                 f"delta scan 0.1/0.01/0.001 = {['%.4f' % x if x else None for x in d['delta_scan_ratios_0.1_0.01_0.001']]} "
                 f"monotone: {d['delta_scan_monotone_increasing']}")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("stage", choices=("factorise", "prepare", "regime", "tally", "all"))
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--decks", nargs="*", default=None,
                    help="restrict the PROCESS-running stages to these decks (development only; the report runs all)")
    args = ap.parse_args()
    if "PROCESS_surgery_env" not in sys.executable:
        raise SystemExit(f"run under PROCESS_surgery_env, not {sys.executable}")
    if Path(cfg.TREE).resolve() != TREE:
        raise SystemExit(f"v3_config resolves TREE={cfg.TREE}, this script lives in {TREE}")
    global DECKS
    if args.decks:
        DECKS = tuple(args.decks)
    RUNS.mkdir(parents=True, exist_ok=True)
    stages = {"factorise": lambda: stage_factorise(),
              "prepare": lambda: stage_prepare(args.workers),
              "regime": lambda: stage_regime(args.workers),
              "tally": lambda: stage_tally()}
    order = ("factorise", "prepare", "regime", "tally") if args.stage == "all" else (args.stage,)
    rc = 0
    for s in order:
        rc = stages[s]()
        if rc != 0 and s in ("factorise", "prepare"):
            _say(f"{s} did not PASS; stopping (a failed gate is a result)")
            return rc
    return rc


if __name__ == "__main__":
    sys.exit(main())
