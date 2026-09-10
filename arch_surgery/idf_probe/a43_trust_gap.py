#!/usr/bin/env python
"""A43 (st-trust-gap): what the outer verification loop actually does on
``st_regression``, and why arms B2 and B3 differ there.

The question, exactly
---------------------
V3's Phase B ran two partitioned arms that differ in ONE switch:

``B2``  per-module block solves, then an **outer verification loop** -- after
        the block schedule has run once, the joint convergence predicate is
        evaluated over the whole 827-component coupling-state vector and
        another whole-schedule pass is taken if anything moved by more than
        tau = 1e-6 (``PROCESS_ARCH_OUTER`` unset -> "verify").
``B3``  identical, but **trust mode** (``PROCESS_ARCH_OUTER=trust``): one
        schedule pass, no verification, no outer pass 2
        (``process/core/caller.py``, the ``TRUST_OUTER`` break).

On the two pulsed configs B2 -> B3 is exactly free: identical optimiser
iteration counts, seed for seed.  On ``st_regression`` -- the k = 0 config,
nothing lifted, nothing pinned -- it is not: 7 of 23 both-converged seeds
differ.  The V3 report offered an untested hypothesis: *"another coupling
still needs it.  Which coupling is not identified here."*

Two candidate explanations were put to this task, exactly one of which had
to be wrong:

(a) the per-scenario collapsed dependency-structure matrix (DSM) for
    ``st_regression`` **misses a live cross-block feedback edge** that the
    resequencing + prime intervention does not cut; or
(b) the Phase B methodology or harness **manufactures** the B2/B3
    difference by something that is not a coupling.

A third outcome had to be recognisable if the data said so: the verify pass
finds **nothing above tau** yet relaxes the state by a **sub-tau** amount
that the optimiser, on a config with several nearly-degenerate optima, is
sensitive to.  That is a statement about the handover tolerance, and it
belongs under (b) as a methodology finding, not under "a coupling".

Stages (protocol 15: every published number comes from executing this
committed script; the failure paths are reachable from the same entry point)
---------------------------------------------------------------------------
``pairing``
    From the committed V3 campaign records ONLY (read-only, in the main
    checkout).  Recomputes the B2/B3 pairing under V3's own declared
    construction by importing ``v3_report_analysis.phase_b`` rather than
    reinventing it, and adds the campaign-wide outer-pass census: how many
    outer passes the verification loop actually took, per config, per arm,
    over every seed -- with denominators.  Also settles I-20's open
    sub-question (can an empty block visit move state?) from the same
    records.
``divergence``
    Also records-only: where B2's and B3's trajectories part.  The
    per-``call_models`` entry census (net electric power at the state each
    call is entered with) is recorded in every campaign run, so the two
    arms' series can be compared index by index for the same seed.  The
    first index at which they differ, and by how much, is the handover gap
    propagating.
``neutrality``
    Reruns of B2 in THIS worktree, untraced and traced, compared against the
    main checkout's campaign records on exact fields (integer counts, the
    outer-pass histogram, and ``norm_objf`` / ``sqsumsq`` as hex floats).
    The gate's teeth are shown per field: the smallest perturbation that
    should register -- +1 on an integer, one ULP on a hex float, +1 on one
    histogram bucket -- must trip the comparator (protocol 12).
``trace``
    Traced B2 runs (``PROCESS_ARCH_PASS_TRACE``, A31's instrument) over the
    seeds, composed through V3's own ``v3_runner.env_for`` / ``run_job`` so
    the only difference from the campaign is the trace -- which the same
    comparator then gates, per run, with a denominator.  One traced B3 run
    beside them: trust mode evaluates the joint test zero times, and a
    trace file with no joint-test record is what that must look like.
``exitgap``
    What each arm actually hands the optimiser.  ONE ``call_models`` per
    arm from a common initialisation, through Phase A's single-evaluation
    instrument, with the uncharged exit audit (whole-state and restricted
    to the in-loop write set) -- the accuracy each arm ACHIEVES, not the
    tolerance it was set -- and then the exact component-by-component
    difference between the two arms' recorded handover states.  That
    difference is not a proxy for the B2/B3 gap; it is the gap.
``tooth``
    The plumbing tooth for the B3 control's zero: with the trace variable
    still set and ``PROCESS_ARCH_MODULE_SOLVE=off`` the instrument must
    refuse at import naming ``PROCESS_ARCH_PASS_TRACE``.  Two cases,
    because ``module_solve``'s guard order matters and the first version of
    this tooth was pre-empted by an earlier guard -- both are recorded.
``ladder``
    The discriminator.  Two knobs, moved one at a time, on small seeds:
    lowering the OUTER tolerance (``PROCESS_ARCH_TAU``) while the inner
    block tolerance stays as the campaign ran it exposes the full census of
    what is still moving below tau and how fast it contracts; tightening the
    INNER tolerance (``PROCESS_ARCH_INNER_TAU``) while tau stays at 1e-6
    asks whether the pass-2 movement is cross-block feedback at all or just
    each block's own inner-tolerance slack.  These are diagnostics about
    mechanism.  They are not arms and no cost number comes from them.
``classify``
    Every pass >= 2 record from every trace, aggregated: the full above-tau
    set (not only the argmax -- A31 showed the argmax was an innocent
    bystander on 89 % of its records), the argmax census, and each moving
    component joined to (i) the committed per-block write subsets
    (``writeset_a26_st_regression.json``), (ii) the run's own recorded block
    schedule, and (iii) the frozen per-deck static dependency export.  The
    join reuses A31's mapping code rather than a second copy of it.
``tables``
    Emits every table the report cites, as markdown and JSON.
``verify``
    Checks every figure the report states against the stage artifacts it
    claims to come from, floats by hex, and shows the checker failing when
    an artifact value is perturbed by one ULP or one count.  No PROCESS
    run: this is the "re-verify without re-running" lane.
``all``
    pairing, divergence, neutrality, trace, tooth, ladder, exitgap,
    classify, tables.

Isolation, trees, tolerances
----------------------------
Every PROCESS run is a fresh subprocess in its own working directory,
launched through V3's own ``run_job``; ``PYTHONPATH`` is pinned to THIS
worktree and the exact tree is asserted inside the subprocess (traps T6 and
T10 -- the editable install points at the main checkout, and a prefix test
would pass there).  The V3 harness directory is imported, never written.
Run artifacts land under ``arch_surgery/idf_probe/runs/a43/`` and stay
untracked.

No conclusion rests on a timing.  Every quantity emitted here is a count, a
component name, or a bit-exact float.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import os
import statistics
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
TREE = HERE.parent.parent
DATA = TREE / "arch_surgery" / "docs" / "data"
V3DIR = TREE / "arch_surgery" / "MDA_partitioning_experiment_v3"
RUNS = HERE / "runs" / "a43"

#: The main checkout.  The V3 campaign's run records and the frozen per-deck
#: static dependency export live there and are READ, never written.
MAIN = Path("/home/wrutten/projects/PROCESS_surgery")
CAMPAIGN = MAIN / "arch_surgery/MDA_partitioning_experiment_v3/runs/phase_b/campaign"

DECK = "st_regression"
N_STARTS = 25

sys.path.insert(0, str(HERE))
sys.path.insert(0, str(V3DIR))


def _v3():
    """The V3 harness modules, imported from this worktree (never edited)."""
    import v3_config  # noqa: PLC0415
    import v3_report_analysis  # noqa: PLC0415
    import v3_runner  # noqa: PLC0415

    return v3_config, v3_runner, v3_report_analysis


def sha256_of(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def jload(p: Path):
    return json.loads(Path(p).read_text())


def jdump(obj, p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, sort_keys=False, default=str))
    print(f"  wrote {p}")


def _stats(vals: list) -> dict:
    """min / median / p90 / max over a list, with its own n.

    The median is ``statistics.median``; nothing here is a check-2 style
    acceptance statistic, so V3's nearest-rank declaration (which binds the
    Phase B checks) does not apply and is not silently borrowed.
    """
    if not vals:
        return {"n": 0}
    s = sorted(vals)
    k = max(0, min(len(s) - 1, math.ceil(0.90 * len(s)) - 1))
    return {
        "n": len(s),
        "min": s[0],
        "median": statistics.median(s),
        "p90": s[k],
        "max": s[-1],
    }


# ==========================================================================
# stage: pairing -- committed campaign records only
# ==========================================================================

def _campaign_metrics(deck: str, arm: str, seed: int) -> dict | None:
    p = CAMPAIGN / deck / arm / f"start{seed:03d}" / "metrics.json"
    return jload(p) if p.exists() else None


def stage_pairing(out: Path) -> dict:
    cfg, _runner, rep = _v3()
    if not CAMPAIGN.exists():
        raise SystemExit(
            f"the V3 campaign records are not at {CAMPAIGN}; this stage reads "
            f"them and cannot proceed without them"
        )

    # V3's own declared construction, imported rather than reimplemented.
    pb = rep.phase_b(root=CAMPAIGN)
    res: dict = {
        "what": (
            "the B2 (verified outer loop) vs B3 (trust) pairing recomputed "
            "from the committed V3 Phase B campaign records under V3's own "
            "declared construction (v3_report_analysis.phase_b, conv = "
            "status 'ok' AND MFILE ifail == 1), plus the campaign-wide "
            "outer-pass census"
        ),
        "campaign_root": str(CAMPAIGN),
        "n_starts": N_STARTS,
        "per_deck": {},
    }

    for deck in cfg.DECKS:
        d = pb.get(deck) or {}
        ident = d.get("b2_b3_trust_step_identity") or {}
        tax = d.get("taxonomy") or {}

        # --- the outer-pass census, over EVERY seed of every arm ----------
        census: dict = {}
        for arm in ("B2", "B3"):
            agg: dict = {}
            n_runs = 0
            n_failed = 0
            calls = 0
            sweeps_tot = 0
            by_block: dict = defaultdict(int)
            per_seed = {}
            for k in range(N_STARTS):
                m = _campaign_metrics(deck, arm, k)
                if m is None:
                    continue
                n_runs += 1
                t = m.get("module_solve_totals") or {}
                h = t.get("outer_pass_hist") or {}
                per_seed[k] = {str(a): b for a, b in h.items()}
                for a, b in h.items():
                    agg[str(a)] = agg.get(str(a), 0) + b
                n_failed += t.get("n_failed") or 0
                calls += t.get("n_call_models") or 0
                sweeps_tot += t.get("block_sweeps") or 0
                for lab, v in (t.get("inner_sweeps_by_block") or {}).items():
                    by_block[lab] += v
            census[arm] = {
                "n_runs": n_runs,
                "n_call_models_total": calls,
                "block_sweeps_total": sweeps_tot,
                "block_sweeps_per_call_models": (
                    sweeps_tot / calls if calls else None),
                "inner_sweeps_by_block_total": dict(sorted(by_block.items())),
                "outer_pass_hist_total": dict(
                    sorted(agg.items(), key=lambda kv: int(kv[0]))),
                "n_call_models_needing_pass_3_or_more": sum(
                    v for a, v in agg.items() if int(a) >= 3),
                "n_block_solve_failures": n_failed,
                "per_seed": per_seed,
            }

        # --- clusters and hops, per seed --------------------------------
        # V3's check 1a clusters accepted optima by norm_objf: a RELATIVE gap
        # wider than CLUSTER_GAP_FLOOR_FACTOR x OBJF_FLOOR_REL between
        # adjacent sorted values separates clusters.  v3_report_analysis
        # publishes only the hop COUNT per pair, and this task needs to know
        # WHICH seeds hopped -- so the construction is repeated here and then
        # cross-checked against the imported analysis's own count.  A
        # disagreement would mean the repeat is not the declared
        # construction, and is reported rather than reconciled.
        cluster_of, hop_seeds, hop_check = _clusters(deck, pb)

        res["per_deck"][deck] = {
            "taxonomy_denominator": N_STARTS,
            "clusters_B2_B3": {
                "construction": (
                    "V3 check 1a, repeated here for per-seed detail: accepted "
                    "optima (status ok AND ifail == 1) sorted by norm_objf; a "
                    "relative gap > CLUSTER_GAP_FLOOR_FACTOR x OBJF_FLOOR_REL "
                    "= 1e-5 between adjacent values opens a new cluster"),
                "per_seed": cluster_of,
                "hop_seeds_B2_to_B3": hop_seeds,
                "cross_check_against_v3_report_analysis": hop_check,
            },
            "n_converged": {a: (tax.get(a) or {}).get("n_converged")
                            for a in ("R", "B0", "B1", "B2", "B3")
                            if a in tax},
            "b2_b3_trust_step_identity": ident,
            "sign_test_on_differing_pairs": _sign_test(
                ident.get("differing_pairs") or []),
            "retry_analysis": _retry_analysis(deck, ident),
            "outer_pass_census": census,
        }

    # --- I-20's open sub-question, from the same records -----------------
    # On st the PULSE block survives in the schedule with `pulse` as its only
    # member, and `pulse` is on the post-solve exclusion list -- so every
    # PULSE block visit should execute exactly nothing.  "Should" is not a
    # measurement; the run records carry both counts.
    i20 = []
    for arm in ("B2", "B3"):
        for k in range(N_STARTS):
            m = _campaign_metrics(DECK, arm, k)
            if m is None:
                continue
            t = m.get("module_solve_totals") or {}
            ps = m.get("post_solve_totals") or {}
            visits = (t.get("inner_solves_by_block") or {}).get("PULSE")
            sweeps = (t.get("inner_sweeps_by_block") or {}).get("PULSE")
            suppressed = (ps.get("suppressed_by_node") or {}).get("pulse")
            nc = (m.get("node_census") or {}).get(
                "per_node_counted_through_Caller_node") or {}
            ncm = t.get("n_call_models")
            sup = ps.get("suppressed_by_node") or {}
            tail = m.get("arch_hoist_tail_resolved") or []
            i20.append({
                "arm": arm, "seed": k,
                "PULSE_block_visits": visits,
                "PULSE_block_sweeps": sweeps,
                "pulse_call_sites_suppressed": suppressed,
                "pulse_node_executions_whole_run": nc.get("pulse"),
                "every_visit_executed_nothing": (
                    visits is not None and suppressed is not None
                    and sweeps == visits and suppressed >= visits),
                # The feed-forward tail runs once per call_models, AFTER the
                # outer loop has converged.  On st both its members are on
                # the post-solve exclusion list, so that sweep executes
                # nothing -- which is what makes the outer pass-2 residual
                # exactly the difference between the two arms' handover
                # states rather than a proxy for it.  Checked, not asserted.
                "n_call_models": ncm,
                "feedforward_tail": tail,
                "tail_members_suppressed_once_per_call": (
                    bool(tail) and ncm is not None
                    and all(sup.get(n) == ncm for n in tail)),
            })
    res["i20_empty_block_visits"] = {
        "what": (
            "issue I-20(a): on st_regression the PULSE block keeps `pulse` as "
            "its only member while the post-solve exclusion suppresses every "
            "call site of that node inside the solve.  Per run: how many "
            "times the block was visited, how many call sites of `pulse` the "
            "exclusion suppressed, and how many times the node executed in "
            "the whole run (solve + post-solve + output path)."
        ),
        "n_runs": len(i20),
        "n_runs_where_every_visit_executed_nothing": sum(
            1 for r in i20 if r["every_visit_executed_nothing"]),
        "n_runs_where_the_feedforward_tail_executed_nothing": sum(
            1 for r in i20 if r["tail_members_suppressed_once_per_call"]),
        "per_run": i20,
    }

    jdump(res, out / "pairing.json")
    return res




#: Where task A44 (transfer-gap) publishes its own factorisation of the same
#: campaign records.  Read-only, untracked, and IN FLIGHT while that task is
#: open: it is used as a cross-check on seed lists, never as a source of a
#: number, and its sha256 and modification time are recorded so a later
#: reader can tell which version was cross-checked.
A44_FACTORISATION = Path(
    "/home/wrutten/projects/PROCESS_surgery_worktrees/A44-transfer-gap"
    "/arch_surgery/idf_probe/runs/a44/factorisation.json")


def _attempts(deck: str, arm: str, seed: int) -> dict:
    """One run's solver-attempt record (V3 H3 exit forensics, task A41).

    ``n_solver_iterations`` in a run record is the FINAL attempt's count.
    When the retry ladder fires -- VMCON exits ifail != 1 and the driver
    retries with epsfcn x10, then x0.1, then a reset Hessian -- the failed
    attempts' iterations are real work that the reported number does not
    carry.  Two runs whose reported counts differ may therefore differ
    because one of them retried, which is a different object from two clean
    runs taking different numbers of steps.
    """
    m = _campaign_metrics(deck, arm, seed)
    if m is None:
        return {"status": "missing"}
    fx = m.get("exit_forensics") or {}
    return {
        "status": m.get("status"),
        "ifail": (m.get("mfile") or {}).get("ifail"),
        "n_attempts": fx.get("n_attempts"),
        "ladder_stage": fx.get("ladder_stage"),
        "iterations_final_attempt": fx.get("n_solver_iterations"),
        "iterations_summed_over_attempts": fx.get(
            "n_solver_iterations_summed_over_attempts"),
        "attempts": [
            {"attempt": a.get("attempt"),
             "stage": a.get("ladder_stage_positional"),
             "epsfcn_at_entry": a.get("epsfcn_at_entry"),
             "ifail": a.get("ifail"),
             "n_solver_iterations": a.get("n_solver_iterations")}
            for a in (fx.get("attempts") or [])],
    }


def _retry_analysis(deck: str, ident: dict) -> dict:
    """The B2/B3 comparison on BOTH iteration statistics.

    V3's check 2 uses ``n_solver_iterations`` -- the final attempt.  The
    same records also carry the sum over attempts, which is the total
    optimiser work the run actually did.  Where one arm retried and the
    other did not, the two statistics can disagree in SIGN, and a reader
    told only one of them would be misled.  Both are published here with
    the same pair set and the same sign test.
    """
    att = {arm: {k: _attempts(deck, arm, k) for k in range(N_STARTS)}
           for arm in ("B2", "B3")}
    retried = {arm: [k for k in range(N_STARTS)
                     if (att[arm][k].get("n_attempts") or 0) > 1]
               for arm in ("B2", "B3")}
    # over the both-converged pair set only -- the population a B2 -> B3
    # comparison is actually made on, and the one a B0-anchored study will
    # report, so the two lists can be compared without a population argument
    retried_in_pairs = {arm: [] for arm in ("B2", "B3")}

    # V3's own pair set, taken from the imported analysis's result rather
    # than rebuilt, so the two statistics are compared over the SAME pairs.
    pair_seeds = sorted(
        {e["seed"] for e in (ident.get("differing_pairs") or [])})
    # every both-converged pair, differing or not
    allpairs = [k for k in range(N_STARTS)
                if all(att[a][k].get("status") == "ok"
                       and att[a][k].get("ifail") == 1.0 for a in ("B2", "B3"))]

    for arm in ("B2", "B3"):
        retried_in_pairs[arm] = [
            k for k in retried[arm]
            if all(att[a][k].get("status") == "ok"
                   and att[a][k].get("ifail") == 1.0 for a in ("B2", "B3"))]

    def _sum(arm, field, seeds):
        return sum((att[arm][k].get(field) or 0) for k in seeds)

    per_pair = []
    for k in allpairs:
        a, b = att["B2"][k], att["B3"][k]
        per_pair.append({
            "seed": k,
            "B2_attempts": a.get("n_attempts"),
            "B3_attempts": b.get("n_attempts"),
            "same_number_of_attempts": a.get("n_attempts") == b.get(
                "n_attempts"),
            "B2_final": a.get("iterations_final_attempt"),
            "B3_final": b.get("iterations_final_attempt"),
            "B2_summed": a.get("iterations_summed_over_attempts"),
            "B3_summed": b.get("iterations_summed_over_attempts"),
            "differs_on_final": (a.get("iterations_final_attempt")
                                 != b.get("iterations_final_attempt")),
            "differs_on_summed": (a.get("iterations_summed_over_attempts")
                                  != b.get("iterations_summed_over_attempts")),
        })

    def _sign(field_a, field_b, which):
        d = [{"seed": e["seed"], "B2": e[field_a], "B3": e[field_b]}
             for e in per_pair if e[which]]
        return _sign_test(d), d

    st_final, d_final = _sign("B2_final", "B3_final", "differs_on_final")
    st_sum, d_sum = _sign("B2_summed", "B3_summed", "differs_on_summed")

    # --- the clean subset: pairs where NEITHER arm used the retry ladder --
    clean = [e for e in per_pair if e["B2_attempts"] == 1
             and e["B3_attempts"] == 1]
    clean_diff_final = [{"seed": e["seed"], "B2": e["B2_final"],
                         "B3": e["B3_final"]}
                        for e in clean if e["differs_on_final"]]
    clean_stats = {
        "what": ("the same comparison restricted to pairs where NEITHER arm "
                 "invoked the retry ladder, so both numbers count one "
                 "uninterrupted VMCON solve and the final-attempt and "
                 "summed statistics coincide"),
        "n_clean_pairs": len(clean),
        "clean_seeds": [e["seed"] for e in clean],
        "n_differing": len(clean_diff_final),
        "differing_pairs": clean_diff_final,
        "sum_B2": sum(e["B2_final"] for e in clean),
        "sum_B3": sum(e["B3_final"] for e in clean),
        "ratio_B3_over_B2": (
            sum(e["B3_final"] for e in clean)
            / sum(e["B2_final"] for e in clean)
            if sum(e["B2_final"] for e in clean) else None),
        "sign_test": _sign_test(clean_diff_final),
    }

    a44 = {"path": str(A44_FACTORISATION), "present": A44_FACTORISATION.exists()}
    if A44_FACTORISATION.exists():
        a44["sha256"] = sha256_of(A44_FACTORISATION)
        a44["mtime"] = A44_FACTORISATION.stat().st_mtime
        try:
            fj = jload(A44_FACTORISATION)
            sd = ((fj.get("decks") or {}).get(deck) or {})
            theirs = (sd.get("st_rung_split") or {}).get("B2->B3_differ")
            mine = sorted(e["seed"] for e in per_pair
                          if e["differs_on_final"])
            a44["their_B2_B3_differing_seeds"] = theirs
            a44["my_B2_B3_differing_seeds_final_attempt"] = mine
            a44["their_population"] = sd.get("identical_converged_seeds")
            a44["my_population"] = allpairs
            a44["in_mine_not_theirs"] = (
                sorted(set(mine) - set(theirs or [])) if theirs else None)
            a44["in_theirs_not_mine"] = (
                sorted(set(theirs or []) - set(mine)) if theirs else None)
            a44["reconciliation"] = (
                "their statistic is problem-calls over the identical-CONVERGED "
                "B0/B3 seed set; mine is optimiser iterations over the "
                "both-converged B2/B3 pair set that V3 check 2 declared.  A "
                "seed present in mine and absent from theirs is a seed where "
                "B2 and B3 both converged but B0 did not, so it cannot enter "
                "a B0-anchored set.")
            a44["seeds_where_B0_did_not_converge"] = [
                k for k in range(N_STARTS)
                if not (( _campaign_metrics(deck, "B0", k) or {}
                         ).get("status") == "ok"
                        and (((_campaign_metrics(deck, "B0", k) or {}
                               ).get("mfile") or {}).get("ifail") == 1.0))]
            spl = sd.get("st_rung_split") or {}
            a44["their_retried_seeds_by_arm"] = spl.get(
                "retried_seeds_by_arm")
            a44["their_B2_B3_differ_without_retry"] = spl.get(
                "B2->B3_differ_without_B2_or_B3_retried")
            a44["my_retried_seeds_by_arm_all_seeds"] = retried
            a44["my_retried_seeds_by_arm_pair_set"] = retried_in_pairs
            a44["retried_seed_lists_agree_on_the_pair_set"] = (
                (spl.get("retried_seeds_by_arm") or {}).get("B2")
                == retried_in_pairs["B2"] and
                (spl.get("retried_seeds_by_arm") or {}).get("B3")
                == retried_in_pairs["B3"]
                if spl.get("retried_seeds_by_arm") else None)
            a44["my_clean_differing_seeds"] = [
                e["seed"] for e in clean_diff_final]
            a44["clean_differing_reconciliation"] = (
                "any seed in my clean differing list and absent from theirs "
                "is a seed their B0-anchored population excludes; a B2 -> B3 "
                "comparison does not need B0 to have converged, so it stays "
                "in mine.  Stated as a derived disagreement, not resolved "
                "by adopting either list.")
            a44["their_retried_seeds_if_findable"] = _find_retried(fj, deck)
        except Exception as exc:  # noqa: BLE001
            a44["read_error"] = f"{type(exc).__name__}: {exc}"
        a44["note"] = (
            "task A44 (transfer-gap) factorises the same campaign records "
            "independently and publishes its own retried-seed lists.  Its "
            "artifact is untracked and IN FLIGHT while that task is open, so "
            "it is cross-checked here, never cited: every number in this "
            "file is derived from the campaign records by this script.")
    return {
        "what": (
            "the B2 vs B3 optimiser-iteration comparison on both available "
            "statistics: the FINAL attempt's count (which is what "
            "n_solver_iterations records and what V3 check 2 used) and the "
            "SUM over all attempts of the retry ladder (the total optimiser "
            "work the run did).  Where one arm retried and the other did "
            "not, the two can disagree in sign."),
        "n_both_converged_pairs": len(allpairs),
        "both_converged_pairs": allpairs,
        "retried_seeds": retried,
        "retried_seeds_within_the_both_converged_pair_set": retried_in_pairs,
        "sum_final_attempt": {a: _sum(a, "iterations_final_attempt", allpairs)
                              for a in ("B2", "B3")},
        "sum_over_attempts": {
            a: _sum(a, "iterations_summed_over_attempts", allpairs)
            for a in ("B2", "B3")},
        "ratio_B3_over_B2_final": (
            _sum("B3", "iterations_final_attempt", allpairs)
            / _sum("B2", "iterations_final_attempt", allpairs)
            if _sum("B2", "iterations_final_attempt", allpairs) else None),
        "ratio_B3_over_B2_summed": (
            _sum("B3", "iterations_summed_over_attempts", allpairs)
            / _sum("B2", "iterations_summed_over_attempts", allpairs)
            if _sum("B2", "iterations_summed_over_attempts", allpairs)
            else None),
        "n_pairs_with_unequal_attempt_counts": sum(
            1 for e in per_pair if not e["same_number_of_attempts"]),
        "clean_subset_no_retry_either_arm": clean_stats,
        "sign_test_final_attempt": st_final,
        "sign_test_summed_over_attempts": st_sum,
        "differing_pairs_final_attempt": d_final,
        "differing_pairs_summed_over_attempts": d_sum,
        "v3_declared_differing_seeds": pair_seeds,
        "per_pair": per_pair,
        "per_run_attempts": att,
        "a44_cross_check": a44,
    }


def _find_retried(fj: dict, deck: str) -> dict:
    """Pull A44's retried-seed lists for one config out of their JSON,
    whatever shape it has: a recursive search for a mapping that carries
    both an arm-like key and a 'retried' key.  A miss is reported as a
    miss; nothing here depends on finding it."""
    found: dict = {}

    def walk(o, ctx):
        if isinstance(o, dict):
            for k, v in o.items():
                if "retr" in str(k).lower() and isinstance(v, list):
                    found[f"{ctx}/{k}"] = v
                walk(v, f"{ctx}/{k}")
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, f"{ctx}[{i}]")

    walk(fj, "")
    return {k: v for k, v in found.items() if deck in k or "st" in k}


def _sign_test(differing: list) -> dict:
    """Is the DIRECTION of the iteration difference established?

    Over the pairs whose iteration counts differ, count how many go each
    way and give the exact one-sided binomial tail against a fair-coin
    null.  The null is the right one if the mechanism is a sub-tolerance
    perturbation of the optimiser's path, which has no reason to be signed;
    it is the wrong one if the mechanism is a systematically less accurate
    handover, which does.  Reported so a reader can see which claims the
    data support and which they do not, rather than reading a summed
    percentage as a direction.
    """
    n = len(differing)
    worse = sum(1 for e in differing if (e.get("B3") or 0) > (e.get("B2") or 0))
    better = n - worse
    k = max(worse, better)
    tail = sum(math.comb(n, j) for j in range(k, n + 1)) / (2 ** n) if n else None
    return {
        "what": ("direction of the B2 -> B3 iteration change over the pairs "
                 "that differ at all, with the exact one-sided binomial tail "
                 "against a fair-coin null"),
        "n_differing_pairs": n,
        "n_B3_worse": worse,
        "n_B3_better": better,
        "sum_B2": sum(e.get("B2") or 0 for e in differing),
        "sum_B3": sum(e.get("B3") or 0 for e in differing),
        "one_sided_p_fair_coin": tail,
        "significant_at_0_05": (tail is not None and tail <= 0.05),
    }


def _clusters(deck: str, pb: dict):
    """V3 check 1a's clusters, per seed, cross-checked against the count
    v3_report_analysis publishes for the same pair."""
    cfg, _runner, rep = _v3()
    accepted = []
    for arm in cfg.PHASE_B_ARMS:
        for k in range(N_STARTS):
            m = _campaign_metrics(deck, arm, k)
            if m is None:
                continue
            if not (m.get("status") == "ok"
                    and (m.get("mfile") or {}).get("ifail") == 1.0):
                continue
            h = (m.get("exact") or {}).get("norm_objf")
            if h is None:
                continue
            accepted.append((arm, k, float.fromhex(h)))
    gap = cfg.CLUSTER_GAP_FLOOR_FACTOR * cfg.OBJF_FLOOR_REL
    order = sorted(range(len(accepted)), key=lambda i: accepted[i][2])
    groups: list = []
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
    cof = {(accepted[i][0], accepted[i][1]): ci
           for ci, g in enumerate(groups) for i in g}
    per_seed = {
        str(k): {a: cof.get((a, k)) for a in cfg.PHASE_B_ARMS
                 if (a, k) in cof}
        for k in range(N_STARTS)}
    hop_seeds = [k for k in range(N_STARTS)
                 if (("B2", k) in cof and ("B3", k) in cof
                     and cof[("B2", k)] != cof[("B3", k)])]
    declared = (((pb.get(deck) or {}).get("check1a") or {})
                .get("hop_rates_per_pair") or {}).get("B2->B3") or {}
    check = {
        "n_clusters_over_all_accepted_runs": len(groups),
        "declared_n_pairs": declared.get("n_pairs"),
        "declared_n_hops": declared.get("n_hops"),
        "repeated_n_hops": len(hop_seeds),
        "agrees": (declared.get("n_hops") == len(hop_seeds)
                   if declared else None),
    }
    return per_seed, hop_seeds, check


# ==========================================================================
# stage: divergence -- committed campaign records only
# ==========================================================================

def stage_divergence(out: Path) -> dict:
    """Where B2's and B3's trajectories part, from the entry census."""
    thresholds = (1e-15, 1e-12, 1e-9, 1e-6, 1e-3)
    rows = []
    for k in range(N_STARTS):
        pa = CAMPAIGN / DECK / "B2" / f"start{k:03d}"
        pb = CAMPAIGN / DECK / "B3" / f"start{k:03d}"
        sa, sb = pa / "entry_census_series.json", pb / "entry_census_series.json"
        if not (sa.exists() and sb.exists()):
            rows.append({"seed": k, "status": "missing_entry_census"})
            continue
        a, b = jload(sa), jload(sb)
        ma, mb = jload(pa / "metrics.json"), jload(pb / "metrics.json")
        n = min(len(a), len(b))
        first_bit = None
        first_over = {t: None for t in thresholds}
        maxrel = 0.0
        rel_at_1 = None
        for i in range(n):
            va, vb = a[i], b[i]
            if va != vb and first_bit is None:
                first_bit = i
            m = max(abs(va), abs(vb))
            r = (abs(va - vb) / m) if m > 0 else 0.0
            if i == 1:
                rel_at_1 = r
            if r > maxrel:
                maxrel = r
            for t in thresholds:
                if first_over[t] is None and r > t:
                    first_over[t] = i
        rows.append({
            "seed": k,
            "B2_iterations": ma.get("n_solver_iterations"),
            "B3_iterations": mb.get("n_solver_iterations"),
            "B2_calls": len(a),
            "B3_calls": len(b),
            "common_prefix": n,
            "first_index_differing_at_all": first_bit,
            "rel_diff_at_entry_1": rel_at_1,
            "first_index_rel_over": {f"{t:g}": first_over[t]
                                     for t in thresholds},
            "max_rel_over_common_prefix": maxrel,
            "B2_objf_hex": (ma.get("exact") or {}).get("norm_objf"),
            "B3_objf_hex": (mb.get("exact") or {}).get("norm_objf"),
            "B2_ifail": (ma.get("mfile") or {}).get("ifail"),
            "B3_ifail": (mb.get("mfile") or {}).get("ifail"),
        })

    ok = [r for r in rows if r.get("common_prefix")]
    res = {
        "what": (
            "per seed, where B2's and B3's optimiser trajectories part.  The "
            "entry census records net electric power (MW) at the state each "
            "call_models is ENTERED with; entry i is therefore the state "
            "call i-1 handed over.  Compared index by index over the common "
            "prefix of the two arms' series, as a relative difference "
            "|a-b| / max(|a|,|b|).  Records-only: no run was taken for this "
            "table."
        ),
        "n_seeds": len(rows),
        "n_seeds_with_both_series": len(ok),
        "n_seeds_differing_at_entry_1": sum(
            1 for r in ok if r["first_index_differing_at_all"] == 1),
        "rel_diff_at_entry_1": _stats(
            [r["rel_diff_at_entry_1"] for r in ok
             if r["rel_diff_at_entry_1"] is not None]),
        "per_seed": rows,
    }
    jdump(res, out / "divergence.json")
    return res


# ==========================================================================
# the comparator, and its teeth
# ==========================================================================

#: The exact fields a rerun must reproduce.  Every one is an integer, a
#: dict of integers, or a hex float -- nothing here is a timing.
COMPARE_FIELDS = (
    ("n_solver_iterations", lambda m: m.get("n_solver_iterations")),
    ("n_model_calls", lambda m: m.get("n_model_calls")),
    ("node_calls_solve_phase", lambda m: m.get("node_calls_solve_phase")),
    ("block_sweeps",
     lambda m: (m.get("module_solve_totals") or {}).get("block_sweeps")),
    ("outer_pass_hist",
     lambda m: {str(k): v for k, v in
                ((m.get("module_solve_totals") or {})
                 .get("outer_pass_hist") or {}).items()}),
    ("norm_objf_hex", lambda m: (m.get("exact") or {}).get("norm_objf")),
    ("sqsumsq_hex", lambda m: (m.get("exact") or {}).get("sqsumsq")),
    ("mfile_ifail", lambda m: (m.get("mfile") or {}).get("ifail")),
)


def compare_to_reference(cand: dict, ref: dict) -> dict:
    """Field-by-field exact comparison.  Every count carries a denominator."""
    fields = {}
    for name, get in COMPARE_FIELDS:
        a, b = get(cand), get(ref)
        fields[name] = {"candidate": a, "reference": b, "match": a == b}
    n = len(fields)
    bad = [k for k, v in fields.items() if not v["match"]]
    return {
        "n_fields_compared": n,
        "n_fields_matching": n - len(bad),
        "mismatching_fields": bad,
        "identical": not bad,
        "fields": fields,
    }


def _bite(name: str, m: dict) -> dict | None:
    """The smallest perturbation of ``name`` that must register.

    Returns a copy of ``m`` with exactly that one field moved, or ``None``
    when the field is absent from the record (which is itself reported --
    a tooth that cannot bite because its field is missing is not a passing
    tooth).
    """
    import copy  # noqa: PLC0415

    c = copy.deepcopy(m)
    if name in ("n_solver_iterations", "n_model_calls",
                "node_calls_solve_phase"):
        if c.get(name) is None:
            return None
        c[name] = c[name] + 1
        return c
    if name == "block_sweeps":
        t = c.get("module_solve_totals") or {}
        if t.get("block_sweeps") is None:
            return None
        t["block_sweeps"] += 1
        return c
    if name == "outer_pass_hist":
        t = (c.get("module_solve_totals") or {}).get("outer_pass_hist") or {}
        if not t:
            return None
        k = sorted(t, key=lambda s: int(s))[0]
        t[k] += 1
        return c
    if name in ("norm_objf_hex", "sqsumsq_hex"):
        key = "norm_objf" if name.startswith("norm") else "sqsumsq"
        e = c.get("exact") or {}
        if not e.get(key):
            return None
        v = float.fromhex(e[key])
        # one ULP away from zero -- the smallest change a hex float can carry
        e[key] = math.nextafter(v, math.inf if v >= 0 else -math.inf).hex()
        return c
    if name == "mfile_ifail":
        f = c.get("mfile") or {}
        if f.get("ifail") is None:
            return None
        f["ifail"] = f["ifail"] + 1.0
        return c
    raise RuntimeError(f"no tooth defined for field {name!r}")


def comparator_teeth(ref: dict) -> dict:
    """Protocol 12: show the comparator can fail, per field, before its
    zeros are accepted.  Each tooth perturbs the comparator's OWN input by
    the smallest amount that should register and requires a mismatch."""
    teeth = {}
    for name, _get in COMPARE_FIELDS:
        bitten = _bite(name, ref)
        if bitten is None:
            teeth[name] = {"bit": False, "reason": "field absent from record",
                           "caught": None}
            continue
        r = compare_to_reference(bitten, ref)
        teeth[name] = {
            "bit": True,
            "caught": (not r["identical"]) and r["mismatching_fields"] == [name],
            "mismatching_fields": r["mismatching_fields"],
        }
    n = len(teeth)
    return {
        "what": (
            "each field of the run comparator, perturbed by the smallest "
            "amount that should register (+1 on an integer count, +1 on one "
            "outer-pass histogram bucket, one ULP on a hex float, +1 on "
            "ifail); the comparator must report exactly that field and no "
            "other"
        ),
        "n_teeth": n,
        "n_bit": sum(1 for v in teeth.values() if v["bit"]),
        "n_caught": sum(1 for v in teeth.values() if v["caught"]),
        "all_caught": all(v["caught"] for v in teeth.values()),
        "per_field": teeth,
    }


# ==========================================================================
# running PROCESS -- always through V3's own composition
# ==========================================================================

def run_arm(arm: str, seed: int, outdir: Path, *, trace: bool,
            extra_env: dict | None = None, timeout: int = 7200) -> dict:
    """One isolated run of a V3 Phase B arm on ``st_regression``.

    Composed by ``v3_runner.env_for`` and executed by ``v3_runner.run_job``
    -- V3's own code, imported from this worktree, so the environment is the
    campaign's environment and the only difference is what ``extra_env``
    adds.  ``MPLCONFIGDIR`` is redirected out of the V3 harness directory:
    that directory is the frozen record of what ran and this task writes
    nothing into it.
    """
    cfg, runner, _rep = _v3()
    outdir.mkdir(parents=True, exist_ok=True)
    env: dict = {"MPLCONFIGDIR": str(RUNS / "_mplconfig")}
    if trace:
        env["PROCESS_ARCH_PASS_TRACE"] = str(outdir / "pass_trace.jsonl")
        # Pass 1 is the solve pass; from pass 2 on the trace records EVERY
        # component at or above tau, which is the diagnostic population.
        env["PROCESS_ARCH_PASS_TRACE_FULL_FROM"] = "2"
    env.update(extra_env or {})
    (RUNS / "_mplconfig").mkdir(parents=True, exist_ok=True)
    return runner.run_job(
        DECK, arm, outdir, seed=seed, delta=cfg.DELTA,
        decks_dir=RUNS / "_decks", node_census=True, resume=False,
        drop_env=env, timeout=timeout,
    )


def _assert_tree() -> None:
    """This script may only drive runs of the tree it lives in (trap T6)."""
    expect = TREE
    if not (expect / "process" / "__init__.py").exists():
        raise SystemExit(f"no process/ under {expect}")
    if not (expect / "arch_surgery").exists():
        raise SystemExit(
            f"{expect} has no arch_surgery/ -- wrong branch (I-11); stop")


# ==========================================================================
# stage: neutrality
# ==========================================================================

def stage_neutrality(out: Path, seed: int) -> dict:
    _assert_tree()
    ref = _campaign_metrics(DECK, "B2", seed)
    if ref is None:
        raise SystemExit(
            f"no campaign record for B2 seed {seed}; the neutrality gate "
            f"compares against it and cannot run without it")

    teeth = comparator_teeth(ref)

    runs = {}
    for label, traced in (("untraced", False), ("traced", True)):
        d = RUNS / "neutrality" / f"seed{seed:03d}_{label}"
        r = run_arm("B2", seed, d, trace=traced)
        mp = d / "metrics.json"
        m = jload(mp) if mp.exists() else {"status": "no_metrics"}
        cmp_ = compare_to_reference(m, ref)
        runs[label] = {
            "outdir": str(d),
            "rc": r.get("rc"),
            "status": m.get("status"),
            "tree": m.get("tree"),
            "process_file": m.get("process_file"),
            "tree_git_head": m.get("tree_git_head"),
            "tree_git_dirty": m.get("tree_git_dirty"),
            "comparison": cmp_,
        }

    res = {
        "what": (
            "does this worktree reproduce the V3 campaign run bit for bit, "
            "and is the per-pass trace observation-only?  One untraced and "
            "one traced rerun of B2 on st_regression at the named seed, each "
            "compared against the main checkout's campaign record on eight "
            "exact fields.  The campaign ran at commit 362c0b47; "
            "`git diff 362c0b47 HEAD -- process/` is empty at this branch's "
            "tip, so a mismatch would be non-determinism or a trace effect, "
            "not a code change."
        ),
        "seed": seed,
        "reference": str(
            CAMPAIGN / DECK / "B2" / f"start{seed:03d}" / "metrics.json"),
        "reference_tree_git_head": ref.get("tree_git_head"),
        "teeth": teeth,
        "runs": runs,
        "gate": (
            teeth["all_caught"]
            and all(v["comparison"]["identical"] for v in runs.values())
        ),
    }
    jdump(res, out / "neutrality.json")
    return res


# ==========================================================================
# stage: trace
# ==========================================================================

def _trace_records(path: Path):
    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def summarise_trace(path: Path, tau: float = 1e-6) -> dict:
    """Aggregate one trace file: per outer-pass index, with denominators."""
    header = None
    per_pass: dict = defaultdict(lambda: {
        "n_records": 0,
        "maxes": [],
        "n_zero": 0,
        "n_above_total": 0,
        "n_records_with_any_above": 0,
        "n_discrete_mismatch_total": 0,
        "n_constant_moved_total": 0,
        "n_nan_new_total": 0,
        "argmax_census": defaultdict(int),
        # A residual of exactly 0.0 has no argmax: numpy's argmax over an
        # all-zero array returns index 0, so the spec's FIRST component is
        # reported as the mover on every such record.  On this deck that is
        # blanket.deg_blkt_inboard_poloidal_plasma, and it is not moving.
        # The two populations are counted apart so the artifact cannot be
        # read as a finding (A31's lesson, one level down).
        "argmax_census_nonzero": defaultdict(int),
        "argmax_census_on_zero_residual": defaultdict(int),
        "argmax_residuals": defaultdict(list),
        "above_census": defaultdict(int),
        "above_detail": [],
    })
    kinds: dict = defaultdict(int)
    n_lines = 0
    for rec in _trace_records(path):
        n_lines += 1
        if rec.get("kind") == "header":
            header = rec
            continue
        kinds[rec.get("kind")] += 1
        p = per_pass[int(rec["pass"])]
        p["n_records"] += 1
        p["maxes"].append(rec["max"])
        if rec["max"] == 0.0:
            p["n_zero"] += 1
        na = int(rec.get("n_above") or 0)
        p["n_above_total"] += na
        if na:
            p["n_records_with_any_above"] += 1
        p["n_discrete_mismatch_total"] += int(
            rec.get("n_discrete_mismatch") or 0)
        p["n_constant_moved_total"] += int(rec.get("n_constant_moved") or 0)
        p["n_nan_new_total"] += int(rec.get("n_nan_new") or 0)
        am = rec.get("argmax")
        if am:
            p["argmax_census"][am.get("key")] += 1
            if rec["max"] == 0.0:
                p["argmax_census_on_zero_residual"][am.get("key")] += 1
            else:
                p["argmax_census_nonzero"][am.get("key")] += 1
                p["argmax_residuals"][am.get("key")].append(rec["max"])
        for c in rec.get("above") or []:
            p["above_census"][c.get("key")] += 1
            if len(p["above_detail"]) < 200:
                p["above_detail"].append(
                    {"call": rec["call"], "pass": rec["pass"], **c})
    out = {
        "path": str(path),
        "n_lines": n_lines,
        "header": header,
        "record_kinds": dict(kinds),
        "per_pass": {},
    }
    for k in sorted(per_pass):
        p = per_pass[k]
        out["per_pass"][str(k)] = {
            "n_records": p["n_records"],
            "residual_max": _stats(p["maxes"]),
            "n_records_with_residual_exactly_zero": p["n_zero"],
            "n_components_above_tau_total": p["n_above_total"],
            "n_records_with_any_component_above_tau":
                p["n_records_with_any_above"],
            "n_discrete_mismatch_total": p["n_discrete_mismatch_total"],
            "n_constant_moved_total": p["n_constant_moved_total"],
            "n_nan_new_total": p["n_nan_new_total"],
            "argmax_census": dict(sorted(p["argmax_census"].items(),
                                         key=lambda kv: -kv[1])),
            "n_records_with_nonzero_residual": sum(
                p["argmax_census_nonzero"].values()),
            "argmax_census_nonzero_residual": dict(sorted(
                p["argmax_census_nonzero"].items(), key=lambda kv: -kv[1])),
            "argmax_census_on_zero_residual": dict(sorted(
                p["argmax_census_on_zero_residual"].items(),
                key=lambda kv: -kv[1])),
            "argmax_residual_stats_by_component": {
                k: _stats(v) for k, v in sorted(
                    p["argmax_residuals"].items(), key=lambda kv: -len(kv[1]))
            },
            "above_census": dict(sorted(p["above_census"].items(),
                                        key=lambda kv: -kv[1])),
            "above_detail_first_200": p["above_detail"],
        }
    out["tau"] = tau
    return out


def stage_trace(out: Path, seeds: list, jobs: int) -> dict:
    _assert_tree()
    os.environ["V3_WORKERS"] = str(max(1, min(3, jobs)))
    _cfg, runner, _rep = _v3()

    jobs_list = []
    for k in seeds:
        d = RUNS / "trace" / "B2" / f"start{k:03d}"
        jobs_list.append({
            "deck": DECK, "arm": "B2", "outdir": d, "seed": k, "delta": 0.10,
            "decks_dir": RUNS / "_decks", "node_census": True, "resume": False,
            "drop_env": {
                "MPLCONFIGDIR": str(RUNS / "_mplconfig"),
                "PROCESS_ARCH_PASS_TRACE": str(d / "pass_trace.jsonl"),
                "PROCESS_ARCH_PASS_TRACE_FULL_FROM": "2",
            },
            "timeout": 7200,
        })
    # One traced B3 beside them: trust mode never evaluates the joint test,
    # so its trace must contain no joint-test record at all.  A trace file
    # that is empty for the RIGHT reason is worth measuring; A31's own
    # instrument raises rather than record silence when the arm has no
    # joint test to trace, and this is the complementary check.
    b3seed = seeds[0]
    d3 = RUNS / "trace" / "B3" / f"start{b3seed:03d}"
    jobs_list.append({
        "deck": DECK, "arm": "B3", "outdir": d3, "seed": b3seed, "delta": 0.10,
        "decks_dir": RUNS / "_decks", "node_census": True, "resume": False,
        "drop_env": {
            "MPLCONFIGDIR": str(RUNS / "_mplconfig"),
            "PROCESS_ARCH_PASS_TRACE": str(d3 / "pass_trace.jsonl"),
            "PROCESS_ARCH_PASS_TRACE_FULL_FROM": "2",
        },
        "timeout": 7200,
    })
    (RUNS / "_mplconfig").mkdir(parents=True, exist_ok=True)
    for j in jobs_list:
        Path(j["outdir"]).mkdir(parents=True, exist_ok=True)
        (Path(j["outdir"]) / "a43_job_env.json").write_text(json.dumps({
            "arm": j["arm"], "seed": j["seed"], "delta": j["delta"],
            "composed_by": "v3_runner.env_for + these additions",
            "additions": j["drop_env"],
        }, indent=2))
    runner.run_pool(jobs_list)

    per_run = []
    n_identical = 0
    for k in seeds:
        d = RUNS / "trace" / "B2" / f"start{k:03d}"
        mp, tp = d / "metrics.json", d / "pass_trace.jsonl"
        m = jload(mp) if mp.exists() else {"status": "no_metrics"}
        ref = _campaign_metrics(DECK, "B2", k)
        cmp_ = compare_to_reference(m, ref) if ref else {
            "identical": None, "n_fields_compared": 0}
        if cmp_.get("identical"):
            n_identical += 1
        fx = m.get("exit_forensics") or {}
        row = {
            "arm": "B2", "seed": k, "outdir": str(d),
            "status": m.get("status"),
            # The retry ladder splits a run into attempts and
            # n_solver_iterations records only the last one, so every traced
            # run carries its attempt list: a B2/B3 difference that begins
            # inside a retried attempt is a different object from one that
            # begins in a clean solve.
            "n_attempts": fx.get("n_attempts"),
            "ladder_stage": fx.get("ladder_stage"),
            "iterations_summed_over_attempts": fx.get(
                "n_solver_iterations_summed_over_attempts"),
            "attempts": [
                {"attempt": a.get("attempt"),
                 "stage": a.get("ladder_stage_positional"),
                 "epsfcn_at_entry": a.get("epsfcn_at_entry"),
                 "ifail": a.get("ifail"),
                 "n_solver_iterations": a.get("n_solver_iterations")}
                for a in (fx.get("attempts") or [])],
            "n_solver_iterations": m.get("n_solver_iterations"),
            "n_call_models": (m.get("module_solve_totals") or {}).get(
                "n_call_models"),
            "reproduces_campaign_record": cmp_.get("identical"),
            "comparison": cmp_,
            "trace_present": tp.exists(),
        }
        if tp.exists():
            row["trace"] = summarise_trace(tp)
            row["trace_bytes"] = tp.stat().st_size
        per_run.append(row)

    b3 = {"arm": "B3", "seed": b3seed, "outdir": str(d3)}
    m3p, t3p = d3 / "metrics.json", d3 / "pass_trace.jsonl"
    if m3p.exists():
        m3 = jload(m3p)
        ref3 = _campaign_metrics(DECK, "B3", b3seed)
        b3["status"] = m3.get("status")
        b3["comparison"] = (compare_to_reference(m3, ref3) if ref3 else None)
        b3["reproduces_campaign_record"] = (
            b3["comparison"] or {}).get("identical")
    b3["trace_present"] = t3p.exists()
    if t3p.exists():
        s = summarise_trace(t3p)
        b3["trace"] = s
        b3["n_joint_test_records"] = sum(
            v["n_records"] for v in s["per_pass"].values())
    else:
        b3["n_joint_test_records"] = 0

    # --- the plumbing tooth for that zero -----------------------------
    # "B3 produced no trace record" is only evidence that trust mode never
    # evaluates the joint test if the trace variable actually REACHED the
    # subprocess.  module_solve refuses at import when a trace is requested
    # of an arm that has no joint test at all
    # (PROCESS_ARCH_MODULE_SOLVE=off), so the same environment plumbing with
    # that one extra variable must make the run DIE with that message.  A
    # run that instead succeeds would mean the trace variable never arrived,
    # and B3's zero would be an artifact.
    dt = RUNS / "trace" / "B3_plumbing_tooth"
    tooth = run_arm(
        "B3", b3seed, dt, trace=True,
        extra_env={"PROCESS_ARCH_MODULE_SOLVE": "off"}, timeout=900)
    err = (dt / "stderr.log").read_text() if (dt / "stderr.log").exists() else ""
    mt = dt / "metrics.json"
    tooth_status = jload(mt).get("status") if mt.exists() else None
    res_tooth = {
        "what": (
            "the same environment plumbing as the B3 control, plus "
            "PROCESS_ARCH_MODULE_SOLVE=off; module_solve refuses at import "
            "when a trace is asked of an arm with no joint test, so this run "
            "must die with that refusal.  If it did not, the trace variable "
            "was never reaching the subprocess and B3's zero would be an "
            "artifact of the harness, not a property of trust mode."
        ),
        "rc": tooth.get("rc"),
        "status": tooth_status,
        "refused_with_the_expected_message": (
            "PROCESS_ARCH_PASS_TRACE is set with "
            "PROCESS_ARCH_MODULE_SOLVE=off" in err),
        "stderr_tail": err[-800:],
        "outdir": str(dt),
    }
    b3["plumbing_tooth"] = res_tooth

    res = {
        "what": (
            "traced B2 runs on st_regression, composed through V3's own "
            "env_for/run_job with PROCESS_ARCH_PASS_TRACE added, plus one "
            "traced B3.  Each run is compared against its campaign record on "
            "the same eight exact fields the neutrality gate uses -- so the "
            "trace's observation-only property is gated once per run, with a "
            "denominator, not asserted."
        ),
        "seeds": seeds,
        "n_runs": len(seeds),
        "n_runs_reproducing_campaign_record": n_identical,
        "per_run": per_run,
        "b3_control": b3,
    }
    jdump(res, out / "trace.json")
    return res


# ==========================================================================
# stage: tooth -- can B3's zero trace records be an artifact of the harness?
# ==========================================================================

def stage_tooth(out: Path, seed: int) -> dict:
    """Show that ``PROCESS_ARCH_PASS_TRACE`` actually reaches the subprocess.

    Trust mode never evaluates the joint test, so a traced B3 run writes no
    joint-test record and the trace file is never even created.  That zero
    is only evidence about trust mode if the trace variable ARRIVED.
    ``module_solve`` refuses at import when a trace is requested of an arm
    with no joint test at all (``PROCESS_ARCH_MODULE_SOLVE=off``), so the
    same plumbing plus that one extra variable must kill the run with that
    specific message.

    Two runs, because the guards are ordered and the first one wins:

    ``trust_and_off``
        B3's environment plus ``MODULE_SOLVE=off``.  ``module_solve`` checks
        ``TRUST_OUTER and not ENABLED`` BEFORE it checks the trace, so this
        dies on the trust guard.  It proves the arm switches arrive; it says
        nothing about the trace variable.  Recorded because the first
        version of this tooth was exactly this and it does not bite.
    ``trace_and_off``
        the same, with ``PROCESS_ARCH_OUTER`` removed so the trace guard is
        the first one reached.  This is the tooth: it must die naming
        ``PROCESS_ARCH_PASS_TRACE``.
    """
    _assert_tree()
    want_trace = ("PROCESS_ARCH_PASS_TRACE is set with "
                  "PROCESS_ARCH_MODULE_SOLVE=off")
    want_trust = ("PROCESS_ARCH_OUTER=trust is set with "
                  "PROCESS_ARCH_MODULE_SOLVE=off")
    cases = {
        "trust_and_off": ({"PROCESS_ARCH_MODULE_SOLVE": "off"}, want_trust),
        "trace_and_off": ({"PROCESS_ARCH_MODULE_SOLVE": "off",
                           "PROCESS_ARCH_OUTER": None}, want_trace),
    }
    rows = {}
    for name, (env, want) in cases.items():
        d = RUNS / "tooth" / name
        r = run_arm("B3", seed, d, trace=True, extra_env=env, timeout=900)
        err = (d / "stderr.log").read_text() if (d / "stderr.log").exists() \
            else ""
        mp = d / "metrics.json"
        st = jload(mp).get("status") if mp.exists() else None
        rows[name] = {
            "env_added": {k: v for k, v in env.items()},
            "rc": r.get("rc"),
            "status": st,
            "expected_message": want,
            "refused_with_the_expected_message": want in err,
            "refused_at_all": (r.get("rc") not in (0, None)),
            "stderr_tail": err[-700:],
            "outdir": str(d),
        }
    return_ = {
        "what": (
            "the plumbing tooth for B3's zero: with the same environment "
            "plus PROCESS_ARCH_MODULE_SOLVE=off the trace instrument must "
            "refuse at import, naming PROCESS_ARCH_PASS_TRACE.  If it did "
            "not, the trace variable was never reaching the subprocess and "
            "B3's zero would be a harness artifact rather than a property "
            "of trust mode."),
        "seed": seed,
        "cases": rows,
        "gate": bool(rows["trace_and_off"]["refused_with_the_expected_message"]),
        "note": (
            "`trust_and_off` is recorded because it was the first version of "
            "this tooth and it does NOT bite: module_solve's guard order puts "
            "the trust-mode check before the trace check, so that run dies on "
            "the wrong guard.  A tooth pre-empted by an earlier guard proves "
            "the wrong thing, and saying so is cheaper than quietly replacing "
            "it."),
    }
    jdump(return_, out / "tooth.json")
    return return_


# ==========================================================================
# stage: ladder -- the discriminator
# ==========================================================================

#: Diagnostic settings.  Each moves ONE tolerance away from the campaign's,
#: with the other held where the campaign had it.  These are not arms.
LADDER = (
    ("as_run", {}),
    ("outer_tau_1e-9", {"PROCESS_ARCH_TAU": "1e-09",
                        "PROCESS_ARCH_INNER_TAU": "1e-06"}),
    ("outer_tau_1e-12", {"PROCESS_ARCH_TAU": "1e-12",
                         "PROCESS_ARCH_INNER_TAU": "1e-06"}),
    ("inner_tau_1e-8", {"PROCESS_ARCH_INNER_TAU": "1e-08"}),
    ("inner_tau_1e-10", {"PROCESS_ARCH_INNER_TAU": "1e-10"}),
)


def stage_ladder(out: Path, seeds: list, jobs: int) -> dict:
    _assert_tree()
    os.environ["V3_WORKERS"] = str(max(1, min(3, jobs)))
    _cfg, runner, _rep = _v3()

    jl = []
    for k in seeds:
        for label, extra in LADDER:
            d = RUNS / "ladder" / f"start{k:03d}" / label
            env = {
                "MPLCONFIGDIR": str(RUNS / "_mplconfig"),
                "PROCESS_ARCH_PASS_TRACE": str(d / "pass_trace.jsonl"),
                "PROCESS_ARCH_PASS_TRACE_FULL_FROM": "2",
            }
            env.update(extra)
            jl.append({
                "deck": DECK, "arm": "B2", "outdir": d, "seed": k,
                "delta": 0.10, "decks_dir": RUNS / "_decks",
                "node_census": True, "resume": False, "drop_env": env,
                "timeout": 7200,
            })
    (RUNS / "_mplconfig").mkdir(parents=True, exist_ok=True)
    runner.run_pool(jl)

    rows = []
    for k in seeds:
        for label, extra in LADDER:
            d = RUNS / "ladder" / f"start{k:03d}" / label
            mp, tp = d / "metrics.json", d / "pass_trace.jsonl"
            m = jload(mp) if mp.exists() else {"status": "no_metrics"}
            t = m.get("module_solve_totals") or {}
            row = {
                "seed": k,
                "setting": label,
                "env_delta": extra,
                "status": m.get("status"),
                "tau": m.get("arch_module_solve_tau"),
                "inner_tau": m.get("arch_module_solve_inner_tau"),
                "n_solver_iterations": m.get("n_solver_iterations"),
                "n_call_models": t.get("n_call_models"),
                "outer_pass_hist": {str(a): b for a, b in
                                    (t.get("outer_pass_hist") or {}).items()},
                "n_block_solve_failures": t.get("n_failed"),
                "block_sweeps": t.get("block_sweeps"),
                "inner_sweeps_by_block": t.get("inner_sweeps_by_block"),
                "ifail": (m.get("mfile") or {}).get("ifail"),
                "objf_hex": (m.get("exact") or {}).get("norm_objf"),
                "outdir": str(d),
                "stderr_tail": None,
            }
            if m.get("status") != "ok":
                se = d / "stderr.log"
                if se.exists():
                    row["stderr_tail"] = se.read_text()[-1500:]
            if tp.exists():
                row["trace"] = summarise_trace(tp)
            rows.append(row)

    res = {
        "what": (
            "the discriminator.  B2 on st_regression with ONE tolerance "
            "moved at a time.  Lowering the OUTER tolerance tau while the "
            "inner block tolerance stays at the campaign's 1e-6 makes the "
            "verification loop keep going, so the trace's above-tau census "
            "at the lower tau enumerates what is still moving BELOW the "
            "campaign's tau and how fast it contracts per pass.  Tightening "
            "the INNER tolerance while tau stays at 1e-6 asks the opposite "
            "question: if pass-2 movement is each block's own inner-solve "
            "slack rather than cross-block feedback, a tighter inner "
            "tolerance must shrink it.  Every setting here changes the "
            "optimiser's trajectory, so NO cost or iteration number from "
            "this stage speaks to B2 vs B3; only the residual structure does."
        ),
        "seeds": seeds,
        "settings": [label for label, _ in LADDER],
        "rows": rows,
    }
    jdump(res, out / "ladder.json")
    return res


# ==========================================================================
# stage: exitgap -- what each arm actually hands the optimiser
# ==========================================================================

def _spec_for_deck():
    """The committed a26 coupling-state spec, loaded from THIS tree.

    ``import process`` resolves through the editable install, which points
    at the MAIN checkout (trap T6), so the tree is put on the path first and
    the import is then asserted against it -- on the path, never on
    ``__version__`` (trap T10).
    """
    if str(TREE) not in sys.path:
        sys.path.insert(0, str(TREE))
    import process  # noqa: PLC0415

    got = Path(process.__file__).resolve().parent.parent
    if got != TREE:
        raise SystemExit(
            f"WRONG TREE: imported {process.__file__} (tree {got}), expected "
            f"exactly {TREE}")
    from process.core.solver import module_solve as ms  # noqa: PLC0415

    spec, prov = ms.load_spec(str(DATA / f"ystate_a26_{DECK}.json"))
    return spec, prov


def _eval_one(arm: str, seed: int, outdir: Path, delta: float,
              extra_env: dict | None = None, timeout: int = 1800) -> dict:
    """ONE ``call_models`` under an arm's environment, no optimiser.

    ``v2_eval_one.py`` is Phase A's own single-evaluation instrument (task
    A34, gated by ``a34_instruments.py``): it initialises the deck exactly
    as a real run does, optionally perturbs the COUPLING STATE on a seeded
    name-keyed stream, executes exactly one ``Caller.call_models`` under
    whatever ``PROCESS_ARCH_*`` the environment selects, writes the exact
    exit state to ``y_exit.json``, and then takes the uncharged exit audit.
    It sets no architecture switch of its own, so handing it V3's own
    ``env_for`` output measures V3's own arm.
    """
    import shutil  # noqa: PLC0415

    cfg, runner, _rep = _v3()
    if outdir.exists():
        shutil.rmtree(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    env = runner.env_for(DECK, arm)
    env["MPLCONFIGDIR"] = str(RUNS / "_mplconfig")
    for kk, vv in (extra_env or {}).items():
        env[kk] = str(vv)
    (RUNS / "_mplconfig").mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable, str(HERE / "v2_eval_one.py"),
        "--scenario", DECK,
        "--input", str(runner.deck_for(DECK, arm, RUNS / "_decks")),
        "--outdir", str(outdir),
        "--expect-tree", str(TREE),
        "--perturb-spec", str(cfg.ystate_for(DECK)),
        "--exit-audit", str(cfg.ystate_for(DECK)),
        "--audit-exclude-postsolve", str(cfg.postsolve_for(DECK)),
        "--node-census",
        "--delta", repr(delta), "--seed", str(seed),
    ]
    (outdir / "a43_cmd.json").write_text(json.dumps(
        {"cmd": cmd,
         "arch_env": {k: v for k, v in env.items()
                      if k.startswith("PROCESS_ARCH")}}, indent=2))
    proc = subprocess.run(cmd, env=env, capture_output=True, text=True,
                          cwd=str(outdir), timeout=timeout)
    (outdir / "stdout.log").write_text(proc.stdout)
    (outdir / "stderr.log").write_text(proc.stderr)
    mp = outdir / "metrics.json"
    m = jload(mp) if mp.exists() else {"status": "no_metrics",
                                       "returncode": proc.returncode}
    m["_rc"] = proc.returncode
    return m


#: Inner block tolerances the single-evaluation handover measurement is
#: repeated at.  The outer tolerance tau stays at the campaign's 1e-6
#: throughout, so exactly one knob moves.  If the B2/B3 handover gap is each
#: block's own inner-solve slack it must collapse as the inner tolerance
#: tightens; if it is cross-block feedback that one schedule pass cannot
#: carry, it must not.
INNER_TAU_LADDER = (
    ("as_run_1e-6", {}),
    ("inner_1e-8", {"PROCESS_ARCH_INNER_TAU": "1e-08"}),
    ("inner_1e-10", {"PROCESS_ARCH_INNER_TAU": "1e-10"}),
    ("inner_1e-12", {"PROCESS_ARCH_INNER_TAU": "1e-12"}),
    ("inner_1e-14", {"PROCESS_ARCH_INNER_TAU": "1e-14"}),
)


def stage_exitgap(out: Path, seeds: list, delta: float = 0.10) -> dict:
    """The matched handover measurement, and the exact difference between
    the two arms' handover states.

    For each seed, ONE ``call_models`` is run under B2's environment and one
    under B3's, from the same initialisation and the same seeded
    coupling-state perturbation.  Two things are then read:

    1. the **uncharged exit audit** of each arm -- one further full sweep of
       the complete model set through a fresh ``Caller``, the same
       instrument in both arms, reported whole-state and restricted to the
       in-loop write set (A38's statistic, post-solve nodes' fields
       excluded because no arm has run them during the solve);
    2. the **exact difference between the two arms' handover states**,
       computed by running the project's own predicate over the two
       ``y_exit.json`` snapshots.  That is not a proxy for the B2/B3 gap; it
       IS the B2/B3 gap, component by component.
    """
    _assert_tree()
    import v2_eval_one as v2e  # noqa: PLC0415

    spec, prov = _spec_for_deck()
    tau = 1e-6
    subsets = jload(DATA / f"writeset_a26_{DECK}.json")["subsets"]
    block_of: dict = {}
    for mod, keys in subsets.items():
        for k in keys:
            block_of[k] = mod
    # Denominators for the per-block mover counts.  "M1: 0 movers" only
    # means anything beside "M1 owns N of the tested components" (trap T11).
    tested_by_block: dict = defaultdict(int)
    for i in range(len(spec.keys)):
        if spec.category[i] == "continuous":
            tested_by_block[block_of.get(spec.name(i), "UNMAPPED")] += 1
    owned_by_block = {m: len(v) for m, v in subsets.items()}

    rows, pairs = [], []
    for k, (tname, tenv) in itertools.product(seeds, INNER_TAU_LADDER):
        snaps = {}
        for arm in ("B2", "B3"):
            d = RUNS / "exitgap" / f"seed{k:03d}" / tname / arm
            m = _eval_one(arm, k, d, delta, extra_env=tenv)
            aud = m.get("exit_audit") or {}
            mst = m.get("module_solve_totals") or {}
            mss = m.get("module_solve_stats") or {}
            rows.append({
                # inner_counts is per OUTER PASS: [sweeps on pass 1, sweeps
                # on pass 2, ...] for each block.  A block that takes ONE
                # inner sweep on pass 2 moved less than inner_tau in that
                # sweep and stopped -- the second pass buying one sweep of
                # slack per block, not solving anything new.
                "inner_counts_per_outer_pass": mss.get("inner_counts"),
                "outer_residual_trace": mss.get("outer_residual_trace"),
                "cap_hit": mss.get("cap_hit"),
                "seed": k, "inner_tau_setting": tname, "arm": arm,
                "status": m.get("status"), "rc": m.get("_rc"),
                "arch_outer_mode": m.get("arch_outer_mode"),
                "tau": m.get("arch_module_solve_tau"),
                "inner_tau": m.get("arch_module_solve_inner_tau"),
                "node_calls_single_eval": m.get("node_calls_single_eval"),
                "block_sweeps": mst.get("block_sweeps"),
                "outer_passes": mst.get("outer_passes",
                                        mst.get("outer_pass_hist")),
                "inner_sweeps_by_block": mst.get("inner_totals",
                                                 mst.get(
                                                     "inner_sweeps_by_block")),
                "audit_whole_state_max": aud.get("residual_max"),
                "audit_whole_state_max_hex": aud.get("residual_max_hex"),
                "audit_whole_state_brief": aud.get("brief"),
                "audit_restricted_max": (aud.get("restricted") or {}).get(
                    "max"),
                "audit_restricted_argmax": (aud.get("restricted") or {}).get(
                    "argmax"),
                "audit_restricted_n_above": (aud.get("restricted") or {}).get(
                    "n_above"),
                "audit_error": aud.get("error"),
                "outdir": str(d),
            })
            sp = d / "y_exit.json"
            if sp.exists():
                snaps[arm] = jload(sp)

        if len(snaps) == 2:
            y2 = v2e.restore_snapshot(spec, snaps["B2"])
            y3 = v2e.restore_snapshot(spec, snaps["B3"])
            res = spec.residual(y3, y2)   # B3 -> B2: what the extra pass did
            scaled = {spec.name(int(i)): float(v)
                      for i, v in zip(res.idx_c, res.scaled)}
            moved = {kk: v for kk, v in scaled.items() if v > 0.0}
            top = sorted(moved.items(), key=lambda kv: -kv[1])[:40]
            per_block: dict = defaultdict(int)
            for kk in moved:
                per_block[block_of.get(kk, "UNMAPPED")] += 1
            pairs.append({
                "seed": k,
                "inner_tau_setting": tname,
                "what": ("the exact scaled difference between the state B3 "
                         "hands the objective and the state B2 hands it, "
                         "from the two arms' y_exit.json snapshots through "
                         "the project's own predicate"),
                "n_components_tested": len(scaled),
                "n_components_differing_at_all": len(moved),
                "n_components_at_or_above_tau": res.n_above(tau),
                "components_at_or_above_tau": [
                    spec.name(i) for i in res.above(tau)],
                "n_discrete_mismatch": len(res.mismatch_discrete),
                "n_constant_moved": len(res.moved_constant),
                "max_scaled": res.max,
                "max_scaled_hex": float(res.max).hex(),
                "argmax": (None if res.argmax is None
                           else spec.name(res.argmax)),
                "argmax_block": (
                    None if res.argmax is None
                    else block_of.get(spec.name(res.argmax), "UNMAPPED")),
                "movers_by_block": dict(sorted(per_block.items())),
                "continuous_components_tested_by_block":
                    dict(sorted(tested_by_block.items())),
                "components_owned_by_block": dict(sorted(
                    owned_by_block.items())),
                "top_movers": [
                    {"component": kk, "scaled": v,
                     "block": block_of.get(kk, "UNMAPPED")}
                    for kk, v in top],
            })

    res_out = {
        "what": (
            "ONE call_models per arm from a common initialisation, through "
            "Phase A's single-evaluation instrument (v2_eval_one.py) under "
            "V3's own B2 / B3 environments.  Per arm: the uncharged exit "
            "audit, whole-state and restricted to the in-loop write set.  "
            "Per seed: the exact component-by-component difference between "
            "the two arms' handover states.  No optimiser runs, so no "
            "iteration or cost number comes from this stage."
        ),
        "seeds": seeds, "delta": delta,
        "inner_tau_ladder": [n for n, _ in INNER_TAU_LADDER],
        "spec": {"path": str(DATA / f"ystate_a26_{DECK}.json"),
                 "components_sha256": prov.get("components_sha256"),
                 "n_components": prov.get("n_components")},
        "tau": tau,
        "rows": rows,
        "handover_difference": pairs,
    }
    jdump(res_out, out / "exitgap.json")
    return res_out


# ==========================================================================
# stage: classify
# ==========================================================================

def stage_classify(out: Path) -> dict:
    """Join every pass >= 2 mover to its block, and to the static export."""
    import a31_drift_probe as a31  # noqa: PLC0415

    ws = jload(DATA / f"writeset_a26_{DECK}.json")
    subsets = ws["subsets"]
    mod_of = a31._component_module(subsets)

    tr = out / "trace.json"
    lr = out / "ladder.json"
    if not tr.exists():
        raise SystemExit(f"{tr} missing; run the trace stage first")
    trace = jload(tr)
    ladder = jload(lr) if lr.exists() else {"rows": []}

    # --- the campaign-setting population -------------------------------
    tot = {
        "n_runs": 0, "n_calls_traced": 0, "n_pass1": 0, "n_pass_ge2": 0,
        "n_components_above_tau_at_pass_ge2": 0,
        "n_records_with_any_above_at_pass_ge2": 0,
        "n_discrete_mismatch_at_pass_ge2": 0,
        "n_constant_moved_at_pass_ge2": 0,
        "n_nan_new_at_pass_ge2": 0,
        "max_pass_index_seen": 0,
    }
    pass2_max = []
    pass1_max = []
    argmax2: dict = defaultdict(int)
    argmax2_nz: dict = defaultdict(int)
    argmax2_zero: dict = defaultdict(int)
    argmax2_mag: dict = defaultdict(list)
    argmax1: dict = defaultdict(int)
    above2: dict = defaultdict(int)
    for row in trace.get("per_run", []):
        t = row.get("trace")
        if not t:
            continue
        tot["n_runs"] += 1
        for pk, p in t["per_pass"].items():
            pi = int(pk)
            tot["max_pass_index_seen"] = max(tot["max_pass_index_seen"], pi)
            if pi == 1:
                tot["n_pass1"] += p["n_records"]
                pass1_max.append(p["residual_max"])
                for k, v in p["argmax_census"].items():
                    argmax1[k] += v
            else:
                tot["n_pass_ge2"] += p["n_records"]
                tot["n_components_above_tau_at_pass_ge2"] += \
                    p["n_components_above_tau_total"]
                tot["n_records_with_any_above_at_pass_ge2"] += \
                    p["n_records_with_any_component_above_tau"]
                tot["n_discrete_mismatch_at_pass_ge2"] += \
                    p["n_discrete_mismatch_total"]
                tot["n_constant_moved_at_pass_ge2"] += \
                    p["n_constant_moved_total"]
                tot["n_nan_new_at_pass_ge2"] += p["n_nan_new_total"]
                pass2_max.append(p["residual_max"])
                for k, v in p["argmax_census"].items():
                    argmax2[k] += v
                for k, v in (p.get("argmax_census_nonzero_residual")
                             or {}).items():
                    argmax2_nz[k] += v
                for k, v in (p.get("argmax_census_on_zero_residual")
                             or {}).items():
                    argmax2_zero[k] += v
                for k, st in (p.get("argmax_residual_stats_by_component")
                              or {}).items():
                    if st.get("n"):
                        argmax2_mag[k].append(st)
                for k, v in p["above_census"].items():
                    above2[k] += v
    tot["n_calls_traced"] = tot["n_pass1"]

    def _pooled(seq_of_stats):
        """Pool per-run min/median/p90/max summaries: min of mins, max of
        maxes, and the (n-weighted) mean of the medians / p90s -- stated as
        such because a median of medians is not a median."""
        ns = [s["n"] for s in seq_of_stats if s.get("n")]
        if not ns:
            return {"n": 0}
        return {
            "n": sum(ns),
            "n_runs": len(ns),
            "min_of_run_minima": min(s["min"] for s in seq_of_stats if s["n"]),
            "max_of_run_maxima": max(s["max"] for s in seq_of_stats if s["n"]),
            "n_weighted_mean_of_run_medians": sum(
                s["median"] * s["n"] for s in seq_of_stats if s["n"]) / sum(ns),
            "n_weighted_mean_of_run_p90s": sum(
                s["p90"] * s["n"] for s in seq_of_stats if s["n"]) / sum(ns),
        }

    def _classify(keys: dict) -> list:
        rows = []
        for key, n in sorted(keys.items(), key=lambda kv: -kv[1]):
            blocks = mod_of.get(key) or []
            rows.append({
                "component": key,
                "n_records": n,
                "writing_block_from_committed_write_subsets": blocks,
            })
        return rows

    # --- the ladder population: what moves below the campaign's tau -----
    ladder_rows = []
    for r in ladder.get("rows", []):
        t = r.get("trace")
        entry = {
            "seed": r["seed"], "setting": r["setting"],
            "status": r["status"], "tau": r["tau"],
            "inner_tau": r["inner_tau"],
            "outer_pass_hist": r["outer_pass_hist"],
            "n_block_solve_failures": r.get("n_block_solve_failures"),
        }
        if t:
            pp = {}
            for pk, p in sorted(t["per_pass"].items(), key=lambda kv: int(kv[0])):
                pp[pk] = {
                    "n_records": p["n_records"],
                    "residual_max": p["residual_max"],
                    "n_components_above_tau_total":
                        p["n_components_above_tau_total"],
                    "argmax_top": dict(list(p["argmax_census"].items())[:8]),
                    "above_top": dict(list(p["above_census"].items())[:15]),
                }
            entry["per_pass"] = pp
        ladder_rows.append(entry)

    # --- static export join --------------------------------------------
    # Two populations are joined, and they are different questions.
    #   (i) whatever moved AT OR ABOVE tau at pass >= 2 -- the components a
    #       missed feedback edge would have to carry;
    #   (ii) the components that differ between the two arms' HANDOVER
    #       states at all, above tau or not -- the sub-tau movers, which is
    #       where the B2/B3 difference actually lives.
    # For each, every static writer and reader is mapped to the block it
    # runs in under the run's OWN recorded schedule, and a pair whose writer
    # block runs AFTER its reader block within one pass is flagged: that is
    # what "loop-carried cross-block edge" means under a block schedule, and
    # it is the only shape that would make hypothesis (a) live.
    egp = out / "exitgap.json"
    subtau_movers: list = []
    if egp.exists():
        eg = jload(egp)
        seen: dict = {}
        for q in eg.get("handover_difference", []):
            for mv in q.get("top_movers", []):
                seen[mv["component"]] = max(
                    seen.get(mv["component"], 0.0), mv["scaled"])
        subtau_movers = sorted(seen.items(), key=lambda kv: -kv[1])[:40]

    movers = sorted(above2, key=lambda k: -above2[k])
    static = None
    if movers or subtau_movers:
        maps = a31._load_static_maps()
        # the block each driver node runs in, from a run's own schedule
        ref = _campaign_metrics(DECK, "B2", 0) or {}
        node_block = a31._node_block(
            ref.get("arch_block_schedule") or [],
            ref.get("arch_hoist_tails_resolved") or [[], []])
        order = {lab: i for i, (lab, _n, _it)
                 in enumerate(ref.get("arch_block_schedule") or [])}

        def _join(key: str, extra: dict) -> dict:
            # The export names variables fully qualified
            # ("superconducting_tfcoil.a_tf_plasma_case"), the same way the
            # ystate spec does, so the key joins directly.  The bare field
            # name is tried only as a fallback and the record says which
            # matched -- a silent miss would read as "no edge" and that is
            # exactly the failure this join exists to avoid.
            match = "qualified"
            w = maps["writers"].get(key)
            r = maps["readers"].get(key)
            if w is None and r is None:
                field = key.split(".", 1)[-1]
                w, r = maps["writers"].get(field), maps["readers"].get(field)
                match = "bare_field" if (w or r) else "NOT_FOUND"
            w, r = w or [], r or []
            extra = {"export_name_match": match, **extra}
            wb = sorted({node_block.get(n, f"not-in-schedule:{n}") for n in w})
            rb = sorted({node_block.get(n, f"not-in-schedule:{n}") for n in r})
            # Only blocks of the executed schedule take part.  The export's
            # workflow drivers -- COOR_SingleRun (the input loader) and the
            # MDA_Output / MDA_Idempotence pseudo-nodes -- are HUBS: models
            # writing loop-tested state connect in and models reading it
            # connect out, and the pairing is lost (DSM register V14
            # follow-up 2 withdrew a three-pathway claim built on exactly
            # that artifact).  They are kept in the record, named, and
            # excluded from the pairing.
            carried = sorted({
                f"{x}->{y}" for x in wb for y in rb
                if x in order and y in order and order[x] > order[y]})
            return {
                "component": key,
                "writing_block_from_committed_write_subsets":
                    mod_of.get(key) or [],
                "static_writers": w, "static_writer_blocks": wb,
                "static_readers": r, "static_reader_blocks": rb,
                "loop_carried_cross_block_pairs": carried,
                **extra,
            }

        static = {
            "export_sha256": maps["export_sha256"],
            "export_path": maps["export_path"],
            "block_schedule_used": ref.get("arch_block_schedule"),
            "above_tau_movers": [
                _join(k, {"n_records": above2[k]}) for k in movers[:50]],
            "subtau_handover_movers": [
                _join(k, {"max_scaled_over_exitgap_rows": v})
                for k, v in subtau_movers],
        }
        static["n_subtau_movers_with_a_loop_carried_cross_block_pair"] = sum(
            1 for e in static["subtau_handover_movers"]
            if e["loop_carried_cross_block_pairs"])
        static["n_above_tau_movers_with_a_loop_carried_cross_block_pair"] = sum(
            1 for e in static["above_tau_movers"]
            if e["loop_carried_cross_block_pairs"])

    res = {
        "what": (
            "every outer-pass record from the traced campaign-setting runs, "
            "aggregated with denominators, and every above-tau mover joined "
            "to the block that writes it (committed per-block write "
            "subsets, 827 components, 0 uncovered, no overlaps) and to the "
            "frozen per-deck static dependency export."
        ),
        "totals": tot,
        "pass1_residual_max_pooled": _pooled(pass1_max),
        "pass_ge2_residual_max_pooled": _pooled(pass2_max),
        "pass1_argmax_census": _classify(argmax1),
        "pass_ge2_argmax_census": _classify(argmax2),
        "pass_ge2_n_records_with_zero_residual": sum(argmax2_zero.values()),
        "pass_ge2_n_records_with_nonzero_residual": sum(argmax2_nz.values()),
        "pass_ge2_argmax_census_on_zero_residual": _classify(argmax2_zero),
        "pass_ge2_argmax_census_nonzero_residual": [
            {**row,
             "residual_min": min(st["min"] for st in argmax2_mag[row["component"]]),
             "residual_max": max(st["max"] for st in argmax2_mag[row["component"]]),
             "n_weighted_mean_of_run_medians": (
                 sum(st["median"] * st["n"] for st in argmax2_mag[row["component"]])
                 / sum(st["n"] for st in argmax2_mag[row["component"]]))}
            for row in _classify(argmax2_nz)
            if row["component"] in argmax2_mag],
        "zero_residual_argmax_note": (
            "a residual of exactly 0.0 has no argmax: numpy's argmax over an "
            "all-zero array returns index 0, so the spec's FIRST component is "
            "named on every such record.  On this deck that is "
            "blanket.deg_blkt_inboard_poloidal_plasma and it is not moving.  "
            "The two populations are reported apart; only the non-zero one "
            "is a census of movers."),
        "pass_ge2_above_tau_census": _classify(above2),
        "static_export_join": static,
        "ladder": ladder_rows,
        "write_subset_provenance": {
            "artifact": str(DATA / f"writeset_a26_{DECK}.json"),
            "sha256": sha256_of(DATA / f"writeset_a26_{DECK}.json"),
            "n_components": ws.get("n_y_components"),
            "census": ws.get("census"),
        },
    }
    jdump(res, out / "classify.json")
    return res


# ==========================================================================
# stage: tables
# ==========================================================================

def _fmt(x, nd=3):
    if x is None:
        return "—"
    if isinstance(x, bool):
        return "yes" if x else "no"
    if isinstance(x, int):
        return f"{x:,}".replace(",", " ")
    if isinstance(x, float):
        if x == 0:
            return "0"
        return f"{x:.{nd}e}"
    return str(x)


def stage_tables(out: Path) -> dict:
    md = []
    art = {}
    for name in ("pairing", "divergence", "neutrality", "trace", "tooth",
                 "ladder", "exitgap", "classify"):
        p = out / f"{name}.json"
        art[name] = jload(p) if p.exists() else None

    # T1 outer-pass census
    if art["pairing"]:
        md.append("### T1 — outer-pass census, whole V3 Phase B campaign\n")
        md.append(
            "*Caption: how many whole-schedule passes the outer verification "
            "loop took, summed over every `call_models` of every seed. A row "
            "is one (config, arm); columns are the number of calls that "
            "terminated at that pass index. `pass >= 3` counts calls where "
            "the joint predicate still found something at or above tau = 1e-6 "
            "after a second full pass. Arm B3 (trust) never evaluates the "
            "predicate, so all of its calls terminate at pass 1 by "
            "construction. Units: calls. Source: committed V3 campaign "
            "records, `module_solve_totals.outer_pass_hist`; stage "
            "`pairing`.*\n")
        md.append("| config | arm | runs | calls | pass 1 | pass 2 | "
                  "pass ≥ 3 | block-solve failures |")
        md.append("|---|---|---|---|---|---|---|---|")
        for deck, d in art["pairing"]["per_deck"].items():
            for arm, c in d["outer_pass_census"].items():
                h = c["outer_pass_hist_total"]
                md.append(
                    f"| `{deck}` | {arm} | {c['n_runs']} | "
                    f"{_fmt(c['n_call_models_total'])} | "
                    f"{_fmt(h.get('1', 0))} | {_fmt(h.get('2', 0))} | "
                    f"**{_fmt(c['n_call_models_needing_pass_3_or_more'])}** | "
                    f"{_fmt(c['n_block_solve_failures'])} |")
        md.append("")

    # T2 the differing seeds
    if art["pairing"]:
        d = art["pairing"]["per_deck"].get(DECK, {})
        ident = d.get("b2_b3_trust_step_identity") or {}
        md.append("### T2 — B2 → B3 per-seed iteration identity on "
                  "`st_regression`\n")
        md.append(
            "*Caption: optimiser iterations per seed for B2 (verified outer "
            "loop) and B3 (trust), over both-converged pairs (`status == ok` "
            "AND MFILE `ifail == 1`) — V3's own declared construction, "
            "recomputed by importing `v3_report_analysis.phase_b`. Iteration "
            "counts are integers, so 'identical' is exact. Units: optimiser "
            "iterations. Source: committed campaign records; stage "
            "`pairing`.*\n")
        md.append(f"Pairs: **{ident.get('n_pairs')}** of {N_STARTS} seeds. "
                  f"Identical iterations: **{ident.get('n_iterations_identical')}"
                  f"/{ident.get('n_pairs')}**. Objective bit-identical: "
                  f"**{ident.get('n_objf_bit_identical')}/"
                  f"{ident.get('n_pairs')}**.\n")
        cl = (d.get("clusters_B2_B3") or {})
        per_seed_cl = cl.get("per_seed") or {}
        hops = set(cl.get("hop_seeds_B2_to_B3") or [])
        md.append("| seed | B2 | B3 | \u0394 | B2 cluster | B3 cluster | "
                  "attractor hop |")
        md.append("|---|---|---|---|---|---|---|")
        s2 = s3 = 0
        for e in ident.get("differing_pairs", []):
            s2 += e["B2"]
            s3 += e["B3"]
            c = per_seed_cl.get(str(e["seed"])) or {}
            md.append(f"| {e['seed']} | {e['B2']} | {e['B3']} | "
                      f"{e['B3'] - e['B2']:+d} | {c.get('B2')} | "
                      f"{c.get('B3')} | "
                      f"{'**yes**' if e['seed'] in hops else 'no'} |")
        md.append(f"| **sum, differing seeds only** | **{s2}** | **{s3}** | "
                  f"**{s3 - s2:+d}** | | | |")
        md.append("")
        st = d.get("sign_test_on_differing_pairs") or {}
        xc = cl.get("cross_check_against_v3_report_analysis") or {}
        md.append(
            f"Direction: B3 worse on **{st.get('n_B3_worse')}** of "
            f"**{st.get('n_differing_pairs')}** differing pairs, better on "
            f"**{st.get('n_B3_better')}**; exact one-sided binomial tail "
            f"against a fair-coin null **p = "
            f"{_fmt(st.get('one_sided_p_fair_coin'), 3)}** \u2014 "
            f"{'significant' if st.get('significant_at_0_05') else 'NOT significant'}"
            f" at 0.05. Cross-check of the cluster repeat against "
            f"`v3_report_analysis`'s own hop count for B2\u2192B3: "
            f"{_fmt(xc.get('agrees'))} ({xc.get('repeated_n_hops')} vs "
            f"{xc.get('declared_n_hops')}).\n")

    # T2b retry analysis
    if art["pairing"]:
        ra = ((art["pairing"]["per_deck"].get(DECK) or {})
              .get("retry_analysis") or {})
        if ra:
            md.append("### T2b — the same records, three defensible "
                      "constructions, two signs\n")
            md.append(
                "*Caption: the B2 → B3 optimiser-iteration comparison on "
                "`st_regression`, over the same 23 both-converged pairs, "
                "under three constructions. **final attempt** is "
                "`n_solver_iterations`, what V3 check 2 used: the last VMCON "
                "attempt only. **summed over attempts** adds the iterations "
                "of every attempt the retry ladder discarded (VMCON exits "
                "`ifail != 1`, the driver retries with `epsfcn` × 10, then × "
                "0.1, then a reset Hessian). **clean pairs** restricts to "
                "pairs where neither arm invoked the ladder, where the two "
                "statistics coincide. `p` is the exact one-sided binomial "
                "tail on the direction over the differing pairs, against a "
                "fair-coin null. Units: optimiser iterations. Source: "
                "committed campaign records, `exit_forensics`; stage "
                "`pairing`.*\n")
            cs = ra["clean_subset_no_retry_either_arm"]
            sf = ra["sign_test_final_attempt"]
            ss = ra["sign_test_summed_over_attempts"]
            md.append("| construction | pairs | Σ B2 | Σ B3 | B3/B2 | "
                      "differing | B3 worse | B3 better | p |")
            md.append("|---|---|---|---|---|---|---|---|---|")
            md.append(
                f"| final attempt (V3 check 2) | "
                f"{ra['n_both_converged_pairs']} | "
                f"{ra['sum_final_attempt']['B2']} | "
                f"{ra['sum_final_attempt']['B3']} | "
                f"**{ra['ratio_B3_over_B2_final']:.4f}** | "
                f"{sf['n_differing_pairs']} | {sf['n_B3_worse']} | "
                f"{sf['n_B3_better']} | {_fmt(sf['one_sided_p_fair_coin'])} |")
            md.append(
                f"| summed over attempts | {ra['n_both_converged_pairs']} | "
                f"{ra['sum_over_attempts']['B2']} | "
                f"{ra['sum_over_attempts']['B3']} | "
                f"**{ra['ratio_B3_over_B2_summed']:.4f}** | "
                f"{ss['n_differing_pairs']} | {ss['n_B3_worse']} | "
                f"{ss['n_B3_better']} | {_fmt(ss['one_sided_p_fair_coin'])} |")
            md.append(
                f"| clean pairs (no retry either arm) | "
                f"{cs['n_clean_pairs']} | {cs['sum_B2']} | {cs['sum_B3']} | "
                f"**{cs['ratio_B3_over_B2']:.4f}** | {cs['n_differing']} | "
                f"{cs['sign_test']['n_B3_worse']} | "
                f"{cs['sign_test']['n_B3_better']} | "
                f"{_fmt(cs['sign_test']['one_sided_p_fair_coin'])} |")
            md.append("")
            md.append(
                f"Retried seeds (more than one VMCON attempt): B2 "
                f"{ra['retried_seeds']['B2']}, B3 "
                f"{ra['retried_seeds']['B3']}; pairs where the two arms took "
                f"different numbers of attempts: "
                f"**{ra['n_pairs_with_unequal_attempt_counts']}** of "
                f"{ra['n_both_converged_pairs']}.\n")
            md.append("| seed | B2 attempts (stage : iterations : ifail) | "
                      "B3 attempts | B2 final | B3 final | B2 summed | "
                      "B3 summed |")
            md.append("|---|---|---|---|---|---|---|")
            att = ra["per_run_attempts"]
            for e in ra["per_pair"]:
                if e["same_number_of_attempts"] and not e["differs_on_final"]:
                    continue
                k = e["seed"]

                def _a(arm, k=k):
                    return "; ".join(
                        f"{x['stage']}:{x['n_solver_iterations']}:{x['ifail']}"
                        for x in att[arm][str(k)]["attempts"]) if str(k) in att[arm] \
                        else "; ".join(
                            f"{x['stage']}:{x['n_solver_iterations']}:{x['ifail']}"
                            for x in att[arm][k]["attempts"])
                md.append(
                    f"| {k} | {_a('B2')} | {_a('B3')} | {e['B2_final']} | "
                    f"{e['B3_final']} | {e['B2_summed']} | {e['B3_summed']} |")
            md.append("")
            a44 = ra.get("a44_cross_check") or {}
            if a44.get("present"):
                md.append(
                    f"**Cross-check against task A44 (transfer-gap)**, which "
                    f"factorised the same records independently on a "
                    f"different statistic (problem-calls) over a different "
                    f"population (the identical-converged B0/B3 set of "
                    f"{len(a44.get('their_population') or [])}): their "
                    f"B2→B3 differing seeds {a44.get('their_B2_B3_differing_seeds')} "
                    f"against mine "
                    f"{a44.get('my_B2_B3_differing_seeds_final_attempt')}. "
                    f"In mine and not theirs: "
                    f"**{a44.get('in_mine_not_theirs')}**; in theirs and not "
                    f"mine: {a44.get('in_theirs_not_mine')}. Derived here, "
                    f"not taken from them: B0 did not converge on seeds "
                    f"{a44.get('seeds_where_B0_did_not_converge')}, so those "
                    f"seeds cannot enter a B0-anchored set — which is the "
                    f"whole difference. Their artifact is untracked and was "
                    f"in flight; sha256 `{(a44.get('sha256') or '')[:16]}…`. "
                    f"No number in this report comes from it.\n")

    # T3 divergence
    if art["divergence"]:
        dv = art["divergence"]
        md.append("### T3 — where B2 and B3 part\n")
        md.append(
            "*Caption: per seed, the first index of the per-call entry census "
            "at which the two arms' series differ at all, and the first index "
            "at which they differ by more than a relative threshold. Entry "
            "index i holds net electric power (MW) at the state `call_models` "
            "number i was entered with — i.e. the state call i−1 handed over; "
            "index 0 is the pre-run default and index 1 is the first handover. "
            "Comparison runs over the common prefix of the two series only. "
            "Units: call index (dimensionless). Population: all 25 seeds. "
            "Source: committed campaign `entry_census_series.json`; stage "
            "`divergence`.*\n")
        _ra = ((art["pairing"] or {}).get("per_deck", {}).get(DECK) or {}
               ).get("retry_analysis") or {}
        _r2 = (_ra.get("retried_seeds") or {}).get("B2") or []
        _r3 = (_ra.get("retried_seeds") or {}).get("B3") or []
        md.append(
            f"Retry note: the series of a run that invoked the retry ladder "
            f"spans more than one VMCON attempt, and the two arms' series "
            f"are then not step-for-step comparable past the first attempt's "
            f"end. Retried on this config: B2 {_r2}, B3 {_r3}.\n")
        md.append("| seed | B2 it | B3 it | B2/B3 attempts | "
                  "first differing entry | "
                  "rel. diff at entry 1 | first > 1e-12 | first > 1e-9 | "
                  "first > 1e-6 | first > 1e-3 | max rel. |")
        md.append("|---|---|---|---|---|---|---|---|---|---|---|")
        _att = _ra.get("per_run_attempts") or {}
        for r in dv["per_seed"]:
            if r.get("status") == "missing_entry_census":
                md.append(f"| {r['seed']} | — | — | — | *missing* | | | | | | |")
                continue
            fo = r["first_index_rel_over"]
            _na = "/".join(
                str(((_att.get(a) or {}).get(str(r['seed'])) or {})
                    .get("n_attempts")) for a in ("B2", "B3"))
            md.append(
                f"| {r['seed']} | {r['B2_iterations']} | {r['B3_iterations']} "
                f"| {_na} | {r['first_index_differing_at_all']} | "
                f"{_fmt(r['rel_diff_at_entry_1'])} | {_fmt(fo.get('1e-12'))} | "
                f"{_fmt(fo.get('1e-09'))} | {_fmt(fo.get('1e-06'))} | "
                f"{_fmt(fo.get('0.001'))} | "
                f"{_fmt(r['max_rel_over_common_prefix'])} |")
        md.append("")

    # T4 neutrality
    if art["neutrality"]:
        n = art["neutrality"]
        md.append("### T4 — neutrality gate, with teeth\n")
        md.append(
            "*Caption: two reruns of B2 on `st_regression` at seed "
            f"{n['seed']} in this worktree — one untraced, one with the "
            "per-pass trace on — each compared against the main checkout's "
            "campaign record on eight exact fields. A row is one rerun; "
            "`fields matching` is out of eight. The teeth block below shows "
            "the comparator failing when its own input is perturbed by the "
            "smallest amount that should register. Units: field counts. "
            "Source: stage `neutrality`.*\n")
        md.append("| rerun | status | fields matching | identical |")
        md.append("|---|---|---|---|")
        for lab, r in n["runs"].items():
            c = r["comparison"]
            md.append(f"| {lab} | {r['status']} | "
                      f"{c['n_fields_matching']}/{c['n_fields_compared']} | "
                      f"{_fmt(c['identical'])} |")
        md.append("")
        t = n["teeth"]
        md.append(f"Teeth: **{t['n_caught']}/{t['n_teeth']}** bit and caught "
                  f"(bit: {t['n_bit']}).\n")
        md.append("| field | tooth applied | comparator caught it |")
        md.append("|---|---|---|")
        for f, v in t["per_field"].items():
            md.append(f"| `{f}` | {_fmt(v['bit'])} | {_fmt(v['caught'])} |")
        md.append("")

    # T5 the pass census
    if art["classify"]:
        c = art["classify"]
        t = c["totals"]
        md.append("### T5 — what the verification pass found, with "
                  "denominators\n")
        md.append(
            "*Caption: every joint-test evaluation recorded by the per-pass "
            "trace across the traced B2 runs at the campaign's own settings. "
            "A pass-1 record compares the state `call_models` was ENTERED "
            "with against the state after one whole schedule pass; a pass-2 "
            "record compares the state after pass 1 against the state after "
            "pass 2 — and since `st_regression`'s feed-forward tail executes "
            "nothing during the solve, the pass-2 record is exactly the "
            "distance between the state B3 hands to the objective and the "
            "state B2 hands to it. Residuals are the predicate's scaled "
            "residual (dimensionless); tau = 1e-6. Source: stage `trace` "
            "aggregated by stage `classify`.*\n")
        md.append(f"- runs traced: **{t['n_runs']}**")
        md.append(f"- `call_models` traced: **{_fmt(t['n_calls_traced'])}**")
        md.append(f"- pass-1 records: **{_fmt(t['n_pass1'])}**")
        md.append(f"- pass ≥ 2 records: **{_fmt(t['n_pass_ge2'])}**")
        md.append(f"- highest pass index seen: **{t['max_pass_index_seen']}**")
        md.append(f"- components at or above tau at pass ≥ 2: "
                  f"**{_fmt(t['n_components_above_tau_at_pass_ge2'])}** "
                  f"(over {_fmt(t['n_pass_ge2'])} records × 827 components)")
        md.append(f"- pass ≥ 2 records with any component above tau: "
                  f"**{_fmt(t['n_records_with_any_above_at_pass_ge2'])}**")
        md.append(f"- discrete mismatches at pass ≥ 2: "
                  f"**{_fmt(t['n_discrete_mismatch_at_pass_ge2'])}**; moved "
                  f"constants: **{_fmt(t['n_constant_moved_at_pass_ge2'])}**; "
                  f"new NaNs: **{_fmt(t['n_nan_new_at_pass_ge2'])}**\n")
        p1 = c["pass1_residual_max_pooled"]
        p2 = c["pass_ge2_residual_max_pooled"]
        md.append("| pass | records | min | n-weighted mean of run medians | "
                  "n-weighted mean of run p90s | max |")
        md.append("|---|---|---|---|---|---|")
        for lab, s in (("1", p1), ("≥ 2", p2)):
            if not s.get("n"):
                continue
            md.append(
                f"| {lab} | {_fmt(s['n'])} | {_fmt(s['min_of_run_minima'])} | "
                f"{_fmt(s['n_weighted_mean_of_run_medians'])} | "
                f"{_fmt(s['n_weighted_mean_of_run_p90s'])} | "
                f"{_fmt(s['max_of_run_maxima'])} |")
        md.append("")
        md.append(
            f"**Pass \u2265 2 argmax census.** Of the "
            f"{_fmt(c['pass_ge2_n_records_with_zero_residual'] + c['pass_ge2_n_records_with_nonzero_residual'])} "
            f"pass-2 records, "
            f"**{_fmt(c['pass_ge2_n_records_with_zero_residual'])}** have a "
            f"residual of **exactly 0.0** \u2014 the second pass moved the "
            f"state by not one bit \u2014 and those records have no argmax: "
            f"numpy's `argmax` over an all-zero array returns index 0, so the "
            f"spec's first component "
            f"(`blanket.deg_blkt_inboard_poloidal_plasma`) is named on every "
            f"one of them and is not moving. The census below is over the "
            f"**{_fmt(c['pass_ge2_n_records_with_nonzero_residual'])}** "
            f"records that did move. Which component holds the maximum is "
            f"not the same question as which components are above tau \u2014 "
            f"A31 showed the argmax was an innocent bystander on 89 % of its "
            f"records \u2014 and here the answer to the second question is "
            f"*none*.\n")
        md.append("| component | records | share | writing block | "
                  "residual: n-weighted mean of run medians | max |")
        md.append("|---|---|---|---|---|---|")
        nznz = c["pass_ge2_n_records_with_nonzero_residual"] or 1
        for r in c["pass_ge2_argmax_census_nonzero_residual"][:12]:
            md.append(
                f"| `{r['component']}` | {_fmt(r['n_records'])} | "
                f"{100.0 * r['n_records'] / nznz:.2f} % | "
                f"{', '.join(r['writing_block_from_committed_write_subsets']) or '—'} | "
                f"{_fmt(r['n_weighted_mean_of_run_medians'])} | "
                f"{_fmt(r['residual_max'])} |")
        md.append("")

    # T5b per-seed pass-2 census
    if art["trace"]:
        tr = art["trace"]
        md.append("### T5b — the verification pass, per seed\n")
        md.append(
            "*Caption: one row per traced B2 run on `st_regression` at the "
            "campaign's own settings (tau = inner tau = 1e-6). `pass-2 "
            "records` is the number of `call_models` that took a second "
            "whole-schedule pass; the rest terminated at pass 1 because the "
            "state they were entered with was already at the fixed point. "
            "`residual max` columns are the scaled joint-test residual the "
            "second pass measured (dimensionless), over that run's pass-2 "
            "records. `≥ tau` is how many coupling-state components, summed "
            "over those records, were at or above tau = 1e-6 — the count a "
            "third pass would have been taken for. `reproduces campaign` "
            "compares the run against its committed campaign record on the "
            "eight exact fields of the neutrality comparator. Source: stage "
            "`trace`.*\n")
        md.append("| seed | iters | calls | pass-1 only | pass-2 records | "
                  "residual max med | residual max p90 | residual max | "
                  "≥ tau | zero-residual pass-2 records | reproduces "
                  "campaign |")
        md.append("|---|---|---|---|---|---|---|---|---|---|---|")
        for r in tr.get("per_run", []):
            t = r.get("trace") or {}
            pp = t.get("per_pass") or {}
            p1 = pp.get("1") or {}
            p2 = pp.get("2") or {}
            rm = p2.get("residual_max") or {}
            md.append(
                f"| {r['seed']} | {_fmt(r['n_solver_iterations'])} | "
                f"{_fmt(r['n_call_models'])} | "
                f"{_fmt((p1.get('n_records') or 0) - (p2.get('n_records') or 0))} | "
                f"{_fmt(p2.get('n_records'))} | {_fmt(rm.get('median'))} | "
                f"{_fmt(rm.get('p90'))} | {_fmt(rm.get('max'))} | "
                f"**{_fmt(p2.get('n_components_above_tau_total'))}** | "
                f"{_fmt(p2.get('n_records_with_residual_exactly_zero'))} | "
                f"{_fmt(r.get('reproduces_campaign_record'))} |")
        md.append("")
        b3 = tr.get("b3_control") or {}
        md.append(
            f"**B3 control** (seed {b3.get('seed')}, trust mode): joint-test "
            f"records written by the trace = **{b3.get('n_joint_test_records')}**"
            f" (trace file created: {_fmt(b3.get('trace_present'))}); the run "
            f"reproduces its campaign record: "
            f"{_fmt(b3.get('reproduces_campaign_record'))}.\n")
        th = art.get("tooth") or {}
        if th:
            md.append(
                "*Plumbing tooth for that zero (stage `tooth`): the same "
                "environment plus `PROCESS_ARCH_MODULE_SOLVE=off`, which the "
                "trace instrument must refuse at import. A row is one case; "
                "`refused with the expected message` requires the refusal to "
                "name the variable being tested.*\n")
            md.append("| case | env added | rc | refused at all | refused "
                      "naming `PROCESS_ARCH_PASS_TRACE`\u2020 |")
            md.append("|---|---|---|---|---|")
            for nm, c in (th.get("cases") or {}).items():
                md.append(
                    f"| `{nm}` | `{c['env_added']}` | {c['rc']} | "
                    f"{_fmt(c['refused_at_all'])} | "
                    f"{_fmt(c['refused_with_the_expected_message'])} |")
            md.append("")
            md.append(
                "† for `trust_and_off` the expected message is the "
                "trust-mode guard's, not the trace guard's — that case is "
                "recorded because it was the first version of this tooth "
                "and it is pre-empted by an earlier guard, so it proves the "
                "wrong thing. `trace_and_off` is the tooth. Gate: "
                f"**{'PASS' if th.get('gate') else 'FAIL'}**.\n")

    # T6 ladder
    if art["ladder"]:
        md.append("### T6 — the discriminator: one tolerance at a time\n")
        md.append(
            "*Caption: B2 on `st_regression` with the outer tolerance tau or "
            "the inner block tolerance moved, one at a time, from the "
            "campaign's 1e-6/1e-6. A row is one (seed, setting) run. "
            "`outer passes` is the histogram of how many whole-schedule "
            "passes each `call_models` took. `pass-2 residual` is the pooled "
            "scaled residual the second pass measured. Every setting changes "
            "the optimiser's trajectory, so no iteration or cost number here "
            "compares to B2/B3; only the residual structure does. Units: "
            "calls, and dimensionless scaled residual. Source: stage "
            "`ladder`.*\n")
        md.append("| seed | setting | tau | inner tau | status | calls | "
                  "outer passes | pass-2 max residual (med / max) | "
                  "components ≥ tau at pass ≥ 2 |")
        md.append("|---|---|---|---|---|---|---|---|---|")
        for r in art["classify"]["ladder"] if art["classify"] else []:
            pp = r.get("per_pass") or {}
            p2 = pp.get("2") or {}
            rm = p2.get("residual_max") or {}
            above = sum(v.get("n_components_above_tau_total", 0)
                        for k, v in pp.items() if int(k) >= 2)
            calls = sum(v.get("n_records", 0) for k, v in pp.items()
                        if int(k) == 1)
            md.append(
                f"| {r['seed']} | `{r['setting']}` | {_fmt(r['tau'])} | "
                f"{_fmt(r['inner_tau'])} | {r['status']} | {_fmt(calls)} | "
                f"{r['outer_pass_hist']} | {_fmt(rm.get('median'))} / "
                f"{_fmt(rm.get('max'))} | {_fmt(above)} |")
        md.append("")

    # T8 / T9 exitgap
    if art["exitgap"]:
        eg = art["exitgap"]
        md.append("### T8 — the handover: what each arm achieves, at matched "
                  "inner tolerance\n")
        md.append(
            "*Caption: ONE `call_models` per arm from a common "
            "initialisation and the same seeded coupling-state perturbation, "
            "with no optimiser anywhere (Phase A's `v2_eval_one.py` under "
            "V3's own B2 / B3 environments). `restricted audit max` is the "
            "scaled coupling-state residual moved by one further full sweep "
            "of the complete model set through a fresh `Caller`, over the "
            "in-loop write set only (post-solve nodes' fields excluded — no "
            "arm runs them during the solve) — i.e. the accuracy the arm "
            "ACHIEVED, dimensionless. `block sweeps` is the arm's own cost "
            "for that one evaluation. A row is one (seed, inner tolerance, "
            "arm). The outer tolerance tau is 1e-6 in every row; only the "
            "inner block tolerance moves. Source: stage `exitgap`.*\n")
        md.append("| seed | inner tol. | arm | status | block sweeps | "
                  "inner sweeps per outer pass | restricted audit max | "
                  "argmax |")
        md.append("|---|---|---|---|---|---|---|---|")
        for r in eg["rows"]:
            ic = r.get("inner_counts_per_outer_pass") or {}
            icu = "; ".join(f"{b}:{v}" for b, v in ic.items()
                            if b != "FF") if ic else "\u2014"
            md.append(
                f"| {r['seed']} | `{r['inner_tau_setting']}` | {r['arm']} | "
                f"{r['status']} | {_fmt(r['block_sweeps'])} | {icu} | "
                f"{_fmt(r['audit_restricted_max'])} | "
                f"`{r['audit_restricted_argmax']}` |")
        md.append("")

        md.append("### T9 — the exact difference between the two arms' "
                  "handover states\n")
        md.append(
            "*Caption: the state B3 hands the objective against the state B2 "
            "hands it, at the same seed and the same inner tolerance, "
            "compared component by component through the project's own "
            "predicate over the two runs' recorded exit snapshots. This is "
            "not a proxy for the B2/B3 gap; it is the gap. `n differing` "
            "counts components whose scaled difference is strictly positive, "
            "out of the 805 continuous components tested (827 total, 22 "
            "discrete). `n ≥ tau` counts those at or above tau = 1e-6 — the "
            "tolerance the outer loop is set to. `by block` attributes each "
            "differing component to the block that writes it, from the "
            "committed per-block write subsets. Source: stage `exitgap`.*\n")
        den = ((eg.get("handover_difference") or [{}])[0]
               .get("continuous_components_tested_by_block") or {})
        md.append("Continuous components tested, by writing block: "
                  + ", ".join(f"{b} {n}" for b, n in den.items()) + ".\n")
        md.append("| seed | inner tol. | n differing / 805 | n \u2265 tau | "
                  "max scaled | argmax | argmax block | movers by block |")
        md.append("|---|---|---|---|---|---|---|---|")
        for q in eg["handover_difference"]:
            md.append(
                f"| {q['seed']} | `{q['inner_tau_setting']}` | "
                f"{q['n_components_differing_at_all']} | "
                f"**{q['n_components_at_or_above_tau']}** | "
                f"{_fmt(q['max_scaled'])} | `{q['argmax']}` | "
                f"{q['argmax_block']} | {q['movers_by_block']} |")
        md.append("")

    # T10 static export join
    if art["classify"] and art["classify"].get("static_export_join"):
        sj = art["classify"]["static_export_join"]
        md.append("### T10 — the movers against the static dependency "
                  "export\n")
        md.append(
            "*Caption: every component that differs between the two arms' "
            "handover states (the sub-tau movers, top 40 by magnitude), "
            "joined to the frozen per-deck static dependency export. "
            "`writer blocks` / `reader blocks` map each static writer and "
            "reader of the field to the block it runs in under the run's own "
            "recorded block schedule. `loop-carried` lists any (writer block "
            "→ reader block) pair whose writer runs AFTER its reader within "
            "one schedule pass — the only shape that makes a component a "
            "cross-block feedback carrier under a block schedule. Export "
            f"sha256 `{sj['export_sha256'][:16]}…`. Source: stage "
            "`classify`.*\n")
        md.append(
            f"**{sj.get('n_subtau_movers_with_a_loop_carried_cross_block_pair')}"
            f"/{len(sj.get('subtau_handover_movers') or [])}** sub-tau movers "
            f"have any loop-carried cross-block writer→reader pair; "
            f"**{sj.get('n_above_tau_movers_with_a_loop_carried_cross_block_pair')}"
            f"/{len(sj.get('above_tau_movers') or [])}** above-tau movers do."
            "\n")
        md.append("| component | write subset | writer blocks | reader blocks "
                  "| loop-carried |")
        md.append("|---|---|---|---|---|")
        for e in (sj.get("subtau_handover_movers") or [])[:25]:
            md.append(
                f"| `{e['component']}` | "
                f"{', '.join(e['writing_block_from_committed_write_subsets']) or '—'} | "
                f"{', '.join(e['static_writer_blocks']) or '—'} | "
                f"{', '.join(e['static_reader_blocks']) or '—'} | "
                f"{', '.join(e['loop_carried_cross_block_pairs']) or '**none**'} |")
        md.append("")

    # T7 I-20
    if art["pairing"]:
        i = art["pairing"]["i20_empty_block_visits"]
        md.append("### T7 — I-20(a): can an empty block visit move state?\n")
        md.append(
            "*Caption: on `st_regression` the `PULSE` block keeps `pulse` as "
            "its only member while the post-solve exclusion suppresses every "
            "call site of that node inside the solve. Per run: block visits, "
            "suppressed call sites, and how often the node executed in the "
            "whole run. A run counts as 'every visit executed nothing' when "
            "the block took exactly one sweep per visit and the exclusion "
            "suppressed at least that many call sites. Units: counts. "
            "Population: 25 seeds × 2 arms. Source: committed campaign "
            "records; stage `pairing`.*\n")
        md.append(f"**{i['n_runs_where_every_visit_executed_nothing']}/"
                  f"{i['n_runs']}** runs: every `PULSE` block visit executed "
                  "nothing.\n")

    text = "\n".join(md) + "\n"
    (out / "tables.md").write_text(text)
    print(f"  wrote {out / 'tables.md'}")
    return {"tables_md": str(out / "tables.md"), "n_lines": len(md)}


# ==========================================================================
# stage: verify -- the report's published figures against the artifacts
# ==========================================================================

#: Every figure the report A43_st_trust_gap.md states, as (label, path into
#: the stage artifacts, expected value).  A path is a list of keys/indices;
#: a callable computes a derived quantity from the loaded artifacts.  This
#: is the "re-verify without re-running" lane V3's own analysis has: it
#: reads the committed stage JSONs and refuses to agree with a report that
#: has drifted from them.
def _verify_cells(art: dict) -> list:
    pa, tr, cl, eg = art["pairing"], art["trace"], art["classify"], art["exitgap"]
    ne, to, la = art["neutrality"], art["tooth"], art.get("ladder") or {}
    st = pa["per_deck"][DECK]
    opc = st["outer_pass_census"]
    ra = st["retry_analysis"]
    cs = ra["clean_subset_no_retry_either_arm"]
    hd = {(q["seed"], q["inner_tau_setting"]): q
          for q in eg["handover_difference"]}
    rows = {(r["seed"], r["inner_tau_setting"], r["arm"]): r
            for r in eg["rows"]}
    t = cl["totals"]
    p2 = cl["pass_ge2_residual_max_pooled"]
    sj = cl["static_export_join"]
    i20 = pa["i20_empty_block_visits"]

    def _sum(field, key):
        return sum(v["outer_pass_census"]["B2"][field] if key is None
                   else v["outer_pass_census"]["B2"][field].get(key, 0)
                   for v in pa["per_deck"].values())

    cells = [
        # section 3
        ("s3.B2_calls_all_configs", _sum("n_call_models_total", None), 91888),
        ("s3.second_passes_all_configs",
         _sum("outer_pass_hist_total", "2"), 90398),
        ("s3.third_passes_all_configs",
         _sum("n_call_models_needing_pass_3_or_more", None), 0),
        ("s3.st_calls", opc["B2"]["n_call_models_total"], 48960),
        ("s3.st_second_passes", opc["B2"]["outer_pass_hist_total"]["2"], 47967),
        ("s3.st_pass1", opc["B2"]["outer_pass_hist_total"]["1"], 993),
        ("s3.tok_pass1", pa["per_deck"]["large_tokamak_nof"]
         ["outer_pass_census"]["B2"]["outer_pass_hist_total"]["1"], 149),
        ("s3.lad_pass1", pa["per_deck"]["low_aspect_ratio_DEMO"]
         ["outer_pass_census"]["B2"]["outer_pass_hist_total"]["1"], 348),
        # section 4
        ("s4.sum_final_B2", ra["sum_final_attempt"]["B2"], 501),
        ("s4.sum_final_B3", ra["sum_final_attempt"]["B3"], 587),
        ("s4.sum_attempts_B2", ra["sum_over_attempts"]["B2"], 643),
        ("s4.sum_attempts_B3", ra["sum_over_attempts"]["B3"], 587),
        ("s4.clean_pairs", cs["n_clean_pairs"], 21),
        ("s4.clean_sum_B2", cs["sum_B2"], 426),
        ("s4.clean_sum_B3", cs["sum_B3"], 456),
        ("s4.p_final", ra["sign_test_final_attempt"]
         ["one_sided_p_fair_coin"], 0.0625),
        ("s4.p_summed", ra["sign_test_summed_over_attempts"]
         ["one_sided_p_fair_coin"], 0.5),
        ("s4.p_clean", cs["sign_test"]["one_sided_p_fair_coin"], 0.1875),
        ("s4.retried_B2", ra[
            "retried_seeds_within_the_both_converged_pair_set"]["B2"], [1, 15]),
        ("s4.retried_B3", ra[
            "retried_seeds_within_the_both_converged_pair_set"]["B3"], []),
        ("s4.a44_only_seed_10", ra["a44_cross_check"]
         .get("in_mine_not_theirs"), [10]),
        ("s4.B0_not_converged", ra["a44_cross_check"]
         .get("seeds_where_B0_did_not_converge"), [10, 17]),
        # section 5
        ("s5.runs_traced", t["n_runs"], 25),
        ("s5.calls_traced", t["n_pass1"], 48960),
        ("s5.pass_ge2_records", t["n_pass_ge2"], 47967),
        ("s5.components_above_tau",
         t["n_components_above_tau_at_pass_ge2"], 0),
        ("s5.discrete_mismatch", t["n_discrete_mismatch_at_pass_ge2"], 0),
        ("s5.moved_constants", t["n_constant_moved_at_pass_ge2"], 0),
        ("s5.new_nans", t["n_nan_new_at_pass_ge2"], 0),
        ("s5.max_pass_index", t["max_pass_index_seen"], 2),
        ("s5.zero_residual_records",
         cl["pass_ge2_n_records_with_zero_residual"], 18720),
        ("s5.nonzero_records",
         cl["pass_ge2_n_records_with_nonzero_residual"], 29247),
        ("s5.pass2_max", p2["max_of_run_maxima"], 2.1558933211330034e-07),
        ("s5.runs_reproducing_campaign",
         tr["n_runs_reproducing_campaign_record"], 25),
        ("s5.neutrality_gate", ne["gate"], True),
        ("s5.teeth_caught", ne["teeth"]["n_caught"], 8),
        ("s5.teeth_total", ne["teeth"]["n_teeth"], 8),
        ("s5.b3_joint_records", tr["b3_control"]["n_joint_test_records"], 0),
        ("s5.b3_trace_file_created", tr["b3_control"]["trace_present"], False),
        ("s5.tooth_gate", to["gate"], True),
        # section 6
        ("s6.seed0_differing", hd[(0, "as_run_1e-6")]
         ["n_components_differing_at_all"], 183),
        ("s6.seed0_max", hd[(0, "as_run_1e-6")]["max_scaled"],
         3.2755368506261723e-09),
        ("s6.seed0_movers_by_block", hd[(0, "as_run_1e-6")]
         ["movers_by_block"], {"M2": 108, "M3": 75}),
        ("s6.all_rungs_zero_above_tau",
         sum(q["n_components_at_or_above_tau"]
             for q in eg["handover_difference"]), 0),
        ("s6.inner_1e-14_all_zero",
         sorted({q["n_components_differing_at_all"]
                 for q in eg["handover_difference"]
                 if q["inner_tau_setting"] == "inner_1e-14"}), [0]),
        ("s6.tested_by_block", hd[(0, "as_run_1e-6")]
         ["continuous_components_tested_by_block"],
         {"FF": 120, "M1": 265, "M2": 204, "M3": 216}),
        ("s6.identity_B3_1e8_eq_B2_1e6",
         sorted({rows[(s, "as_run_1e-6", "B2")]["audit_restricted_max"]
                 for s in eg["seeds"]}
                | {rows[(s, "inner_1e-8", "B3")]["audit_restricted_max"]
                   for s in eg["seeds"]}), [1.1161527574246441e-10]),
        ("s6.identity_B3_1e12_eq_B2_1e10",
         sorted({rows[(s, "inner_1e-10", "B2")]["audit_restricted_max"]
                 for s in eg["seeds"]}
                | {rows[(s, "inner_1e-12", "B3")]["audit_restricted_max"]
                   for s in eg["seeds"]}), [6.458955838497905e-14]),
        ("s6.B2_1e6_sweeps",
         rows[(0, "as_run_1e-6", "B2")]["block_sweeps"], 21),
        ("s6.B3_1e12_sweeps",
         rows[(0, "inner_1e-12", "B3")]["block_sweeps"], 21),
        ("s6.n_exitgap_runs", len(eg["rows"]), 50),
        ("s6.exitgap_all_ok",
         sorted({r["status"] for r in eg["rows"]}), ["ok"]),
        ("s6.static_movers_joined", len(sj["subtau_handover_movers"]), 40),
        ("s6.static_loop_carried",
         sj["n_subtau_movers_with_a_loop_carried_cross_block_pair"], 0),
        ("s6.export_sha_prefix", sj["export_sha256"][:16],
         "582b4a5f861f4216"),
        # section 7
        ("s7.tok_objf_identical", pa["per_deck"]["large_tokamak_nof"]
         ["b2_b3_trust_step_identity"]["n_objf_bit_identical"], 20),
        ("s7.lad_objf_identical", pa["per_deck"]["low_aspect_ratio_DEMO"]
         ["b2_b3_trust_step_identity"]["n_objf_bit_identical"], 0),
        ("s7.st_objf_identical",
         st["b2_b3_trust_step_identity"]["n_objf_bit_identical"], 0),
        ("s7.lad_iters_identical", pa["per_deck"]["low_aspect_ratio_DEMO"]
         ["b2_b3_trust_step_identity"]["n_iterations_identical"], 11),
        ("s7.st_iters_identical",
         st["b2_b3_trust_step_identity"]["n_iterations_identical"], 16),
        ("s7.i20_empty_visits",
         i20["n_runs_where_every_visit_executed_nothing"], 50),
        ("s7.i20_tail_empty",
         i20["n_runs_where_the_feedforward_tail_executed_nothing"], 50),
        ("s7.pulse_B2", opc["B2"]["inner_sweeps_by_block_total"]["PULSE"],
         96927),
        ("s7.pulse_B3", opc["B3"]["inner_sweeps_by_block_total"]["PULSE"],
         47040),
        ("s7.sweeps_B2", opc["B2"]["block_sweeps_total"], 636194),
        ("s7.sweeps_B3", opc["B3"]["block_sweeps_total"], 423109),
    ]
    if la.get("rows"):
        hists = {r["setting"]: r["outer_pass_hist"] for r in la["rows"]
                 if r["seed"] == 21}
        cells += [
            ("s5.5.as_run_hist_pass2_only",
             sorted(hists.get("as_run", {})), ["1", "2"]),
            ("s5.5.inner_1e-8_hist_pass2_only",
             sorted(hists.get("inner_tau_1e-8", {})), ["1", "2"]),
            ("s5.5.outer_1e-9_reaches_pass_4",
             "4" in (hists.get("outer_tau_1e-9") or {}), True),
        ]
    return cells


def stage_verify(out: Path) -> dict:
    """Check every figure the report publishes against the stage artifacts.

    Reads only the committed stage JSONs: no PROCESS run, seconds to run.
    Its teeth mutate a cell's ARTIFACT value by the smallest amount that
    should register and require the check to fail -- a verifier that has
    never been seen to fail is an assertion (protocol 12).
    """
    art = {}
    for name in ("pairing", "divergence", "neutrality", "trace", "tooth",
                 "ladder", "exitgap", "classify"):
        f = out / f"{name}.json"
        art[name] = jload(f) if f.exists() else None
    missing = [k for k in ("pairing", "trace", "classify", "exitgap",
                           "neutrality", "tooth") if art[k] is None]
    if missing:
        raise SystemExit(f"cannot verify: missing stage artifacts {missing}")

    def compare(cells):
        bad = []
        for label, got, want in cells:
            ok = (got == want)
            if not ok and isinstance(got, float) and isinstance(want, float):
                ok = float(got).hex() == float(want).hex()
            if not ok:
                bad.append({"cell": label, "artifact": got, "report": want})
        return bad

    cells = _verify_cells(art)
    bad = compare(cells)

    # --- teeth: the verifier must be able to fail ----------------------
    import copy  # noqa: PLC0415
    teeth = []
    for target in ("s3.third_passes_all_configs", "s5.components_above_tau",
                   "s6.seed0_max", "s6.identity_B3_1e8_eq_B2_1e6"):
        mutated = copy.deepcopy(art)
        if target == "s3.third_passes_all_configs":
            (mutated["pairing"]["per_deck"][DECK]["outer_pass_census"]["B2"]
             ["n_call_models_needing_pass_3_or_more"]) += 1
        elif target == "s5.components_above_tau":
            mutated["classify"]["totals"][
                "n_components_above_tau_at_pass_ge2"] += 1
        elif target == "s6.seed0_max":
            for q in mutated["exitgap"]["handover_difference"]:
                if q["seed"] == 0 and q["inner_tau_setting"] == "as_run_1e-6":
                    q["max_scaled"] = math.nextafter(q["max_scaled"], math.inf)
        elif target == "s6.identity_B3_1e8_eq_B2_1e6":
            for r in mutated["exitgap"]["rows"]:
                if (r["seed"] == 0 and r["arm"] == "B3"
                        and r["inner_tau_setting"] == "inner_1e-8"):
                    r["audit_restricted_max"] = math.nextafter(
                        r["audit_restricted_max"], math.inf)
        caught = [b["cell"] for b in compare(_verify_cells(mutated))]
        teeth.append({
            "cell": target,
            "perturbation": ("+1 on an integer count" if "max" not in target
                             else "one ULP on the artifact's float"),
            "caught": target in caught,
            "cells_reported": caught,
        })

    res = {
        "what": (
            "every figure the report A43_st_trust_gap.md publishes, checked "
            "against the stage artifacts it claims to come from.  Floats are "
            "compared by hex.  No PROCESS run: this is the re-verify lane."),
        "n_cells": len(cells),
        "n_mismatches": len(bad),
        "mismatches": bad,
        "teeth": {
            "n_teeth": len(teeth),
            "n_caught": sum(1 for t in teeth if t["caught"]),
            "all_caught": all(t["caught"] for t in teeth),
            "per_tooth": teeth,
        },
        "gate": (not bad) and all(t["caught"] for t in teeth),
    }
    jdump(res, out / "verify.json")
    return res


# ==========================================================================
# entry point
# ==========================================================================

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="A43 (st-trust-gap): the st_regression B2/B3 gap")
    ap.add_argument("stage", choices=(
        "pairing", "divergence", "neutrality", "trace", "tooth", "ladder",
        "exitgap", "classify", "tables", "verify", "all"))
    ap.add_argument("--out", default=str(RUNS / "out"),
                    help="where the stage JSON/markdown artifacts land")
    ap.add_argument("--seeds", default=None,
                    help="comma-separated seed list for trace (default: all "
                         f"0..{N_STARTS - 1})")
    ap.add_argument("--ladder-seeds", default="21,19",
                    help="seeds for the tolerance-ladder diagnostic")
    ap.add_argument("--neutrality-seed", type=int, default=21)
    ap.add_argument("--exitgap-seeds", default="0,1,2,3,4",
                    help="coupling-state perturbation seeds for the "
                         "single-evaluation handover measurement")
    ap.add_argument("--jobs", type=int, default=3,
                    help="concurrent runs (campaign width is 3)")
    args = ap.parse_args(argv)

    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    seeds = ([int(s) for s in args.seeds.split(",")] if args.seeds
             else list(range(N_STARTS)))
    lseeds = [int(s) for s in args.ladder_seeds.split(",")]
    eseeds = [int(s) for s in args.exitgap_seeds.split(",")]

    print(f"A43 (st-trust-gap) stage={args.stage} tree={TREE}")
    print(f"  out={out}")

    if args.stage in ("pairing", "all"):
        print("\n== stage pairing ==")
        stage_pairing(out)
    if args.stage in ("divergence", "all"):
        print("\n== stage divergence ==")
        stage_divergence(out)
    if args.stage in ("neutrality", "all"):
        print("\n== stage neutrality ==")
        r = stage_neutrality(out, args.neutrality_seed)
        print(f"  gate: {'PASS' if r['gate'] else 'FAIL'}")
    if args.stage in ("trace", "all"):
        print("\n== stage trace ==")
        r = stage_trace(out, seeds, args.jobs)
        print(f"  {r['n_runs_reproducing_campaign_record']}/{r['n_runs']} "
              f"traced runs reproduce their campaign record exactly")
    if args.stage in ("tooth", "all"):
        print("\n== stage tooth ==")
        r = stage_tooth(out, args.neutrality_seed)
        print(f"  tooth: {'PASS' if r['gate'] else 'FAIL'}")
    if args.stage in ("ladder", "all"):
        print("\n== stage ladder ==")
        stage_ladder(out, lseeds, args.jobs)
    if args.stage in ("exitgap", "all"):
        print("\n== stage exitgap ==")
        stage_exitgap(out, eseeds)
    if args.stage in ("classify", "all"):
        print("\n== stage classify ==")
        stage_classify(out)
    if args.stage in ("tables", "all"):
        print("\n== stage tables ==")
        stage_tables(out)
    if args.stage in ("verify", "all"):
        print("\n== stage verify ==")
        r = stage_verify(out)
        print(f"  {r['n_cells'] - r['n_mismatches']}/{r['n_cells']} cells "
              f"agree; teeth {r['teeth']['n_caught']}/"
              f"{r['teeth']['n_teeth']}; gate: "
              f"{'PASS' if r['gate'] else 'FAIL'}")
        if r["mismatches"]:
            for m in r["mismatches"]:
                print(f"    MISMATCH {m['cell']}: artifact {m['artifact']!r} "
                      f"vs report {m['report']!r}")
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
