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
``all``
    pairing, divergence, neutrality, trace, ladder, exitgap, classify,
    tables.

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
            census[arm] = {
                "n_runs": n_runs,
                "n_call_models_total": calls,
                "outer_pass_hist_total": dict(
                    sorted(agg.items(), key=lambda kv: int(kv[0]))),
                "n_call_models_needing_pass_3_or_more": sum(
                    v for a, v in agg.items() if int(a) >= 3),
                "n_block_solve_failures": n_failed,
                "per_seed": per_seed,
            }

        res["per_deck"][deck] = {
            "taxonomy_denominator": N_STARTS,
            "n_converged": {a: (tax.get(a) or {}).get("n_converged")
                            for a in ("R", "B0", "B1", "B2", "B3")
                            if a in tax},
            "b2_b3_trust_step_identity": ident,
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
            i20.append({
                "arm": arm, "seed": k,
                "PULSE_block_visits": visits,
                "PULSE_block_sweeps": sweeps,
                "pulse_call_sites_suppressed": suppressed,
                "pulse_node_executions_whole_run": nc.get("pulse"),
                "every_visit_executed_nothing": (
                    visits is not None and suppressed is not None
                    and sweeps == visits and suppressed >= visits),
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
        "per_run": i20,
    }

    jdump(res, out / "pairing.json")
    return res


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
        row = {
            "arm": "B2", "seed": k, "outdir": str(d),
            "status": m.get("status"),
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

    rows, pairs = [], []
    for k, (tname, tenv) in itertools.product(seeds, INNER_TAU_LADDER):
        snaps = {}
        for arm in ("B2", "B3"):
            d = RUNS / "exitgap" / f"seed{k:03d}" / tname / arm
            m = _eval_one(arm, k, d, delta, extra_env=tenv)
            aud = m.get("exit_audit") or {}
            mst = m.get("module_solve_totals") or m.get(
                "module_solve_stats") or {}
            rows.append({
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

    # --- static export join, for whatever moved above tau --------------
    static = None
    movers = sorted(above2, key=lambda k: -above2[k])
    if movers:
        maps = a31._load_static_maps()
        static = {"export_sha256": maps["export_sha256"],
                  "export_path": maps["export_path"], "per_component": []}
        for key in movers[:50]:
            field = key.split(".", 1)[-1]
            static["per_component"].append({
                "component": key,
                "static_writers": maps["writers"].get(field),
                "static_readers": maps["readers"].get(field),
            })

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
        "pass_ge2_above_tau_census": _classify(above2),
        "static_export_join_for_above_tau_movers": static,
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
    for name in ("pairing", "divergence", "neutrality", "trace", "ladder",
                 "exitgap", "classify"):
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
        md.append("| seed | B2 | B3 | Δ |")
        md.append("|---|---|---|---|")
        s2 = s3 = 0
        for e in ident.get("differing_pairs", []):
            s2 += e["B2"]
            s3 += e["B3"]
            md.append(f"| {e['seed']} | {e['B2']} | {e['B3']} | "
                      f"{e['B3'] - e['B2']:+d} |")
        md.append(f"| **sum, differing seeds only** | **{s2}** | **{s3}** | "
                  f"**{s3 - s2:+d}** |")
        md.append("")

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
        md.append("| seed | B2 it | B3 it | first differing entry | "
                  "rel. diff at entry 1 | first > 1e-12 | first > 1e-9 | "
                  "first > 1e-6 | first > 1e-3 | max rel. |")
        md.append("|---|---|---|---|---|---|---|---|---|---|")
        for r in dv["per_seed"]:
            if r.get("status") == "missing_entry_census":
                md.append(f"| {r['seed']} | — | — | *missing* | | | | | | |")
                continue
            fo = r["first_index_rel_over"]
            md.append(
                f"| {r['seed']} | {r['B2_iterations']} | {r['B3_iterations']} "
                f"| {r['first_index_differing_at_all']} | "
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
        md.append("**Pass ≥ 2 argmax census** (which component carries the "
                  "residual maximum; not the same question as which "
                  "components are above tau — A31 showed the argmax was an "
                  "innocent bystander on 89 % of its records):\n")
        md.append("| component | records | writing block |")
        md.append("|---|---|---|")
        for r in c["pass_ge2_argmax_census"][:15]:
            md.append(f"| `{r['component']}` | {_fmt(r['n_records'])} | "
                      f"{', '.join(r['writing_block_from_committed_write_subsets']) or '—'} |")
        md.append("")

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
                  "restricted audit max | argmax |")
        md.append("|---|---|---|---|---|---|---|")
        for r in eg["rows"]:
            md.append(
                f"| {r['seed']} | `{r['inner_tau_setting']}` | {r['arm']} | "
                f"{r['status']} | {_fmt(r['block_sweeps'])} | "
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
        md.append("| seed | inner tol. | n differing / 805 | n ≥ tau | "
                  "max scaled | argmax | argmax block | by block |")
        md.append("|---|---|---|---|---|---|---|---|")
        for q in eg["handover_difference"]:
            md.append(
                f"| {q['seed']} | `{q['inner_tau_setting']}` | "
                f"{q['n_components_differing_at_all']} | "
                f"**{q['n_components_at_or_above_tau']}** | "
                f"{_fmt(q['max_scaled'])} | `{q['argmax']}` | "
                f"{q['argmax_block']} | {q['movers_by_block']} |")
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
# entry point
# ==========================================================================

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="A43 (st-trust-gap): the st_regression B2/B3 gap")
    ap.add_argument("stage", choices=(
        "pairing", "divergence", "neutrality", "trace", "ladder", "exitgap",
        "classify", "tables", "all"))
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
