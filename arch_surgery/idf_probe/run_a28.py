#!/usr/bin/env python
"""A28 (phase-b-rerun) driver: three arms, on the instrument A26 left behind.

What changed since A25, and why
-------------------------------
A25 ran Phase B with **two** arms and compared the variant directly against
PROCESS as shipped.  Decision **D18** records why that could not answer the
question it was asked: the two arms stop on **different predicates**, so their
cost ratio is architecture *plus* stopping rule, summed, and Phase A had
measured the stopping rule alone at −3.4 % to +8.6 % against a Phase B result
of +2.0 %.  The predicate term can dominate the answer and can flip its sign.

So this driver runs **three** arms:

``R``
    PROCESS as shipped.  Every variant point unset, the existing
    ``objf``/``conf`` idempotence test, the existing flat loop, the frozen
    scenario deck.  **The relevance anchor**: it is what a user of PROCESS
    actually runs.  Phase A's own ``arms.py`` says "R is a reference, not a
    competitor", and this driver never quotes ``R -> A1'`` as the
    architecture's cost.
``A0'`` (``A0p`` on the command line)
    **The predicate-matched control.**  Flat fixed-point iteration on the
    coupling state at ``tau``, in ``caller.py`` --- one block containing every
    in-loop node, the same predicate the variant uses, the **upstream** node
    order, no hoist, no lift, the frozen deck.  A26 §10 asked whether this is
    the degenerate single-block case of A25's ``module_solve.py`` and answered
    *nearly*, naming two blockers; both are now fixed there, so it is that
    degenerate case and not a second solver.
``A1'`` (``A1p``)
    **The proposed architecture**: per-module block solves, the burn-time
    lift, and the feed-forward hoist, all at once (decision D15(b)).  Its
    headline is therefore *the proposed architecture* and never *the
    partition's benefit* (plan §7a) --- the hoist is separable and is measured
    separately by ``A1p_nohoist``.

Two diagnostic arms, run where the budget allows and never in a headline:

``A0p_reordered``
    ``A0'`` with ``PROCESS_ARCH_SEQUENCE=build_after_physics``.  Grouping the
    models into blocks also transposes ``build`` and ``physics``, so
    ``A0' -> A1'`` varies the grouping *and* that transposition.  This arm
    measures the transposition on its own instead of leaving it as a caveat.
``A1p_nohoist``
    The proposed architecture minus the hoist, so the hoist's share is
    measured **inside this architecture** rather than quoted from A13's
    measurement of the flat one (which would be a units error of the kind trap
    T11 records).

The comparisons, and what each one contains
-------------------------------------------
``A0' -> A1'``   the architecture alone, at matched predicate.  **The headline.**
``R -> A1'``     architecture plus stopping rule.  The user-facing figure only.
``R -> A0'``     the stopping rule alone --- what the predicate costs in
                 production.

Every ordered pair of arms actually run must carry a declaration of what it
varies, checked at run time against the arms as they were built
(``fixedpoint/manifest.py``).  That is what stops a third arm being added and
quietly compared with no declaration.

The hoist arm name, and why it is not ``feedforward``
-----------------------------------------------------
A26 §11.9: the variant uses ``PROCESS_ARCH_HOIST=feedforward_lifted``.  Once
the burn time is a design variable, ``Pulse``'s burn-time write is a no-op and
the only other field it writes is read by a constraint equation and by no
model, so iterating it inside the MDA is wasted work --- worth 3.35 % and
3.31 % of net model evaluations, gated by A26 at 0 of 1 710 recorded predicate
values differing as exact hex floats.  Leaving ``pulse`` in the loop would make
the arm **not the architecture this study claims to be testing**.

``st_regression`` has no burn-time coupler at all (``i_pulsed_plant = 0``, and
its measured ``PULSE`` write set is empty), so it takes no lift and therefore
``feedforward``, not ``feedforward_lifted`` --- which is an import-time error
without the lift.  It is the ``k = 0`` control, not a third replicate, and the
driver records that per run rather than leaving a report to remember it.

Isolation
---------
Every run is a fresh subprocess in its own working directory, ``PYTHONPATH``
pinned to this worktree, and the **exact** tree asserted inside the subprocess
(trap T6: a worktree does not redirect an editable install, and a prefix test
passes for the main checkout).  The first run in a fresh environment is
discarded --- numba JIT compilation dominates it.

No conclusion rests on a timing.  Wall clock is recorded as progress
information and is reported with a median, an interval, a repetition count and
the run's position in the sequence; issue I-10 measured identical work varying
by up to 35 % in CPU-seconds on this machine with the cause unknown, and A26
measured a p10-p90 band of 50-143 % of the median against 4 % effects.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
TREE = HERE.parent.parent
DATA = TREE / "arch_surgery" / "docs" / "data"

#: **Three decks, from 2026-09-02 (D17).**  ``large_tokamak_eval`` is dropped:
#: it runs 0 solver iterations, so it cannot inform a study about how an
#: architecture behaves when the optimiser reacts; its inequality constraints
#: are never enforced, so its "solution" is not a feasible optimum; and A22
#: found its evidence weaker than the other pulsed decks.  A26 §5.4 then found
#: two quantities on that deck that are not constant, whose bit-identity
#: assertion was blocking convergence and inflating its cost figures.
#: **Already-merged four-deck tables stand as the record of what was run.**
DROPPED_2026_09_02 = ("large_tokamak_eval",)

SCENARIOS = [
    "large_tokamak_nof",
    "low_aspect_ratio_DEMO",
    "st_regression",
]

#: Decks with a burn-time coupler.  ``st_regression`` has ``i_pulsed_plant = 0``
#: so ``Pulse`` writes nothing (measured: its PULSE write set is empty, A25
#: §2.3) and there is nothing to lift.
PULSED = {"large_tokamak_nof", "low_aspect_ratio_DEMO"}

#: The three arms a headline may be built from, in reporting order.
CORE_ARMS = ("R", "A0p", "A1p")

#: Diagnostics.  Never in a headline; each answers one caveat by measuring it.
DIAGNOSTIC_ARMS = ("A0p_reordered", "A1p_nohoist")

ALL_ARMS = CORE_ARMS + DIAGNOSTIC_ARMS

#: Phase A's first rung and decision D15's starting tolerance.
TAU = 1e-6

#: A26 fix 1: cost must be read off at matched **achieved** accuracy, so both
#: arms are run across ladders and each run's achieved exit residual is
#: recorded beside its cost.  The flat control has one tolerance; the block arm
#: has two, because an inner block solve is a thing the flat arm does not have.
#: That asymmetry is inherent to the architecture and is reported, not hidden:
#: it gives the block arm more settings tried, which A26 bounded rather than
#: eliminated.
LADDER_FLAT_TAUS = (1e-3, 1e-4, 1e-5, 1e-6, 1e-8)
LADDER_BLOCK_JOINT_TAUS = (1e-3, 1e-4, 1e-5, 1e-6, 1e-8)
LADDER_BLOCK_INNER_TAUS = (1e-1, 1e-2, 1e-3, 1e-4)


def deck_for(scenario: str, arm: str, decks: Path) -> Path:
    """The input deck an arm runs.

    Only the lifted arms take the derived deck, and only on a deck that has a
    burn-time coupler.  The frozen scenarios are never edited (D9).
    """
    if arm in ("A1p", "A1p_nohoist") and scenario in PULSED:
        return decks / scenario / f"{scenario}_lifted.IN.DAT"
    return HERE / "scenarios" / f"{scenario}.IN.DAT"


_ARCH_VARS = (
    "PROCESS_IDF_PROBE",
    "PROCESS_ARCH_SEQUENCE",
    "PROCESS_ARCH_HOIST",
    "PROCESS_ARCH_LIFT",
    "PROCESS_ARCH_MODULE_SOLVE",
    "PROCESS_ARCH_TAU",
    "PROCESS_ARCH_INNER_TAU",
    "PROCESS_ARCH_YSTATE",
    "PROCESS_ARCH_WRITESET",
    # A31 / A33: later variant points' switches are cleared here too, so an
    # inherited one can never change what an arm measures without saying so.
    "PROCESS_ARCH_PASS_TRACE",
    "PROCESS_ARCH_PASS_TRACE_FULL_FROM",
    "PROCESS_ARCH_POST_SOLVE",
)


def env_for(
    scenario: str,
    arm: str,
    runs: Path,
    tau: float,
    inner_tau: float | None = None,
) -> dict:
    """The environment one arm runs under, built from nothing.

    Every architecture switch is **cleared first** rather than assumed absent:
    an inherited one would change what is being measured without saying so.
    """
    env = dict(os.environ)
    env["PYTHONPATH"] = str(TREE)
    env["MPLCONFIGDIR"] = str(runs / "_mplconfig")
    for k in _ARCH_VARS:
        env.pop(k, None)

    if arm == "R":
        return env

    if arm not in ALL_ARMS:
        raise SystemExit(f"unknown arm {arm!r}; known: {list(ALL_ARMS)}")

    # Both non-baseline families use the same predicate, the same artifacts and
    # the same tolerance.  What differs is the schedule and the node-set
    # membership -- which is the whole point of the three-arm design.
    env["PROCESS_ARCH_TAU"] = repr(tau)
    env["PROCESS_ARCH_YSTATE"] = str(DATA / f"ystate_{scenario}.json")
    env["PROCESS_ARCH_WRITESET"] = str(DATA / f"writeset_{scenario}.json")

    if arm in ("A0p", "A0p_reordered"):
        env["PROCESS_ARCH_MODULE_SOLVE"] = "flat_state"
        # A0' takes the **upstream** node order, so that R -> A0' varies the
        # stopping rule and nothing else.  A0p_reordered is the diagnostic that
        # measures the transposition on its own.
        if arm == "A0p_reordered":
            env["PROCESS_ARCH_SEQUENCE"] = "build_after_physics"
        return env

    # A1' and its no-hoist twin.
    env["PROCESS_ARCH_SEQUENCE"] = "build_after_physics"
    env["PROCESS_ARCH_MODULE_SOLVE"] = "per_module"
    if inner_tau is not None:
        env["PROCESS_ARCH_INNER_TAU"] = repr(inner_tau)
    if scenario in PULSED:
        env["PROCESS_ARCH_LIFT"] = "burn_time"
    if arm == "A1p":
        # A26 §11.9.  ``feedforward_lifted`` is an import-time error without
        # the lift, which is why the k = 0 deck takes ``feedforward``.
        env["PROCESS_ARCH_HOIST"] = (
            "feedforward_lifted" if scenario in PULSED else "feedforward"
        )
    return env


_SEQ = [0]


def run_one(
    scenario: str,
    arm: str,
    outdir: Path,
    runs: Path,
    decks: Path,
    *,
    tau: float,
    inner_tau: float | None = None,
    delta: float | None = None,
    seed: int = 0,
    timeout: int = 3600,
    exit_audit: bool = True,
    entry_census: bool = True,
    node_census: bool = False,
    audit_at_call: int = 0,
) -> dict:
    if outdir.exists():
        shutil.rmtree(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(HERE / "run_one.py"),
        "--scenario", scenario,
        "--mode", "control",
        "--outdir", str(outdir),
        "--expect-tree", str(TREE),
        "--input", str(deck_for(scenario, arm, decks)),
    ]
    if delta is not None:
        cmd += ["--perturb-delta", repr(delta), "--perturb-seed", str(seed)]
    if exit_audit:
        cmd += ["--exit-audit", str(DATA / f"ystate_{scenario}.json")]
    if entry_census:
        cmd += ["--entry-census"]
    if node_census:
        cmd += ["--node-census"]
    if audit_at_call:
        cmd += ["--exit-audit-at-call", str(audit_at_call)]
    _SEQ[0] += 1
    seq = _SEQ[0]
    t0 = time.perf_counter()
    try:
        proc = subprocess.run(
            cmd,
            env=env_for(scenario, arm, runs, tau, inner_tau),
            capture_output=True,
            text=True,
            cwd=str(outdir),
            timeout=timeout,
        )
        rc, out, err = proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        rc, out, err = 124, exc.stdout or "", (exc.stderr or "") + "\nTIMEOUT"
    (outdir / "stdout.log").write_text(
        out if isinstance(out, str) else out.decode()
    )
    (outdir / "stderr.log").write_text(
        err if isinstance(err, str) else err.decode()
    )
    mpath = outdir / "metrics.json"
    if not mpath.exists():
        # A timeout or an import-time refusal leaves no metrics.  Write a row
        # so the census sees the start rather than silently losing it -- a
        # denominator that shrinks without saying so is trap T11.
        mpath.write_text(json.dumps({
            "scenario": scenario, "mode": "control",
            "status": "timeout" if rc == 124 else "no_metrics",
            "perturb_delta": delta, "perturb_seed": seed,
            "returncode": rc,
        }, indent=2))
    else:
        # Stamp the arm and its sequence position into the record, so an
        # analysis never has to infer either from a directory name.
        rec = json.loads(mpath.read_text())
        rec["a28_arm"] = arm
        rec["a28_sequence_position"] = seq
        rec["a28_tau"] = tau
        rec["a28_inner_tau"] = inner_tau
        rec["a28_deck"] = str(deck_for(scenario, arm, decks))
        mpath.write_text(json.dumps(rec, indent=2))
    return {
        "scenario": scenario,
        "arm": arm,
        "seed": seed,
        "delta": delta,
        "tau": tau,
        "inner_tau": inner_tau,
        "rc": rc,
        "sequence_position": seq,
        "wall_s": time.perf_counter() - t0,
    }


def warm(runs: Path, decks: Path, tau: float) -> None:
    """The discarded first run: numba JIT compilation dominates a cold process."""
    wd = runs / "_warmup"
    print("Warming JIT caches (this run is discarded):", flush=True)
    r = run_one("large_tokamak_nof", "R", wd, runs, decks, tau=tau,
                exit_audit=False, entry_census=False)
    print(f"  rc={r['rc']} {r['wall_s']:.1f}s", flush=True)


# --------------------------------------------------------------------------
# stages
# --------------------------------------------------------------------------


def stage_decks(runs: Path, scenarios, decks: Path) -> int:
    """Derive the lifted decks from the frozen scenarios (never editing them)."""
    rc = 0
    for s in scenarios:
        if s not in PULSED:
            print(f"  {s:24s} no burn-time coupler (k = 0): no lifted deck",
                  flush=True)
            continue
        out = decks / s
        out.mkdir(parents=True, exist_ok=True)
        env = dict(os.environ)
        env["PYTHONPATH"] = str(TREE)
        env["MPLCONFIGDIR"] = str(runs / "_mplconfig")
        for k in _ARCH_VARS:
            env.pop(k, None)
        proc = subprocess.run(
            [sys.executable, str(HERE / "a25_variant_deck.py"),
             "--scenario", s, "--outdir", str(out), "--expect-tree", str(TREE)],
            env=env, cwd=str(out), capture_output=True, text=True,
        )
        (out / "derive.log").write_text(proc.stdout + proc.stderr)
        print(f"  {s:24s} rc={proc.returncode}", flush=True)
        rc = rc or proc.returncode
    return rc


def jobs_gate(runs: Path, scenarios, arms) -> list[tuple]:
    root = runs / "gate"
    return [
        (s, a, root / s / a, None, 0, TAU, None, 0)
        for s in scenarios for a in arms
    ]


def jobs_calibrate(runs: Path, scenarios, deltas, starts) -> list[tuple]:
    root = runs / "calibrate"
    out = []
    for s in scenarios:
        for d in deltas:
            tag = f"delta{int(round(d * 1000)):04d}"
            for k in range(1, starts + 1):
                out.append(
                    (s, "R", root / s / tag / f"start{k:03d}", d, k, TAU,
                     None, 0)
                )
    return out


def jobs_ladder(runs: Path, scenarios, starts, flat_taus=None,
                joint_taus=None, inner_taus=None, delta=0.10) -> list[tuple]:
    """Cost against achieved accuracy, per arm, per rung, per start.

    The flat control's ladder is a plain tau ladder.  The block arm's is two
    families --- the joint ladder (outer = inner) and an inner-only ladder at
    the calibrated outer tau --- because the inner tolerance is the parameter
    that moves its achieved accuracy independently of its outer one.  Both
    families give (cost, achieved accuracy) points and the curve is read off
    the two together, as A26's was.
    """
    root = runs / "ladder"
    flat_taus = LADDER_FLAT_TAUS if flat_taus is None else flat_taus
    joint_taus = LADDER_BLOCK_JOINT_TAUS if joint_taus is None else joint_taus
    inner_taus = LADDER_BLOCK_INNER_TAUS if inner_taus is None else inner_taus
    out = []
    for s in scenarios:
        for k in range(starts):
            d = None if k == 0 else delta
            rungs = (
                [("A0p", f"A0p_tau{t:g}", t, None) for t in flat_taus]
                + [("A1p", f"A1p_joint{t:g}", t, None) for t in joint_taus]
                + [("A1p", f"A1p_inner{t:g}", TAU, t) for t in inner_taus]
            )
            for arm, label, tau, itau in rungs:
                # Two runs per (rung, start), and they measure different
                # things.  The COST run goes to completion and is never
                # audited.  The ACCURACY run takes one further full sweep at
                # the first optimiser evaluation and then STOPS, because that
                # sweep mutates the state and a run that continues after it is
                # no longer the arm being measured.  Same arm, same start,
                # same tolerance; the population is therefore identical, which
                # is what a (cost, accuracy) point needs.
                out.append((s, arm, root / s / label / f"start{k:03d}",
                            d, k, tau, itau, 0))
                out.append((s, arm, root / s / label / f"audit{k:03d}",
                            d, k, tau, itau, 1))
    return out


def jobs_campaign(runs: Path, scenarios, arms, starts, delta,
                  inner_tau=None, tag: str = "h5") -> list[tuple]:
    """The paired multi-start campaign.

    ``inner_tau`` and ``tag`` exist for **the matched-accuracy robustness
    re-run**: the campaign compares robustness at a fixed tolerance, and a
    fixed tolerance is not a fixed accuracy.  Where the ladder shows one arm
    delivering systematically more accuracy at the campaign's tau, that arm is
    re-run at the setting its own ladder says delivers the OTHER arm's
    accuracy, into its own directory, and **both readings are reported side by
    side with the tolerance each was measured at named**.  Never one instead of
    the other.
    """
    root = runs / tag
    return [
        (s, a, root / s / a / f"start{k:03d}", delta, k, TAU, inner_tau, 0)
        for s in scenarios for a in arms for k in range(0, starts + 1)
    ]


def jobs_audit(runs: Path, scenarios, arms, starts, delta,
               at_call: int = 1) -> list[tuple]:
    """The accuracy each arm DELIVERS at the campaign's own setting.

    **The campaign compares robustness at a fixed tolerance, and a fixed
    tolerance is not a fixed accuracy.**  That is the same objection A26
    demonstrated for cost, where reading at matched tolerance instead of
    matched achieved accuracy flipped the sign of the answer.  An arm that
    converges to a looser final state at tau = 1e-6 is being asked an easier
    question, and its success rate is not comparable to the other's.

    So the accuracy is measured rather than assumed: for every start the
    campaign ran, one further full sweep of the complete model set at the
    return of the ``at_call``-th optimiser evaluation, from the **same entry
    state** in every arm.  These runs stop immediately afterwards --- the sweep
    mutates the state --- so they are cheap, and their cost figures are not
    cost figures.

    The direction is not assumed either.  A looser effective convergence could
    raise a success rate (an easier test to satisfy) or lower it (a worse point
    handed to the optimiser).  It is measured.
    """
    root = runs / f"h5_audit{at_call}"
    return [
        (s, a, root / s / a / f"start{k:03d}", delta, k, TAU, None, at_call)
        for s in scenarios for a in arms for k in range(0, starts + 1)
    ]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "mode",
        choices=["decks", "gate", "calibrate", "ladder", "campaign", "audit"],
    )
    ap.add_argument("--runs", default=str(HERE / "runs" / "a28"))
    ap.add_argument("--decks", default=None,
                    help="directory of derived decks (default <runs>/_decks)")
    ap.add_argument("--scenarios", nargs="*", default=SCENARIOS)
    ap.add_argument("--arms", nargs="*", default=list(CORE_ARMS))
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--starts", type=int, default=24)
    ap.add_argument("--ladder-starts", type=int, default=1)
    ap.add_argument("--flat-taus", nargs="*", type=float, default=None)
    ap.add_argument("--joint-taus", nargs="*", type=float, default=None)
    ap.add_argument("--inner-taus", nargs="*", type=float, default=None)
    ap.add_argument("--deltas", nargs="*", type=float,
                    default=[0.01, 0.05, 0.10])
    ap.add_argument("--delta", type=float, default=None)
    ap.add_argument("--timeout", type=int, default=3600)
    ap.add_argument("--skip-warm", action="store_true")
    ap.add_argument("--inner-tau", type=float, default=None,
                    help="campaign mode: the block arm's inner tolerance, for "
                         "the matched-accuracy robustness re-run")
    ap.add_argument("--tag", default="h5",
                    help="campaign mode: the directory the runs land in, so a "
                         "re-run at another setting does not overwrite the "
                         "first reading")
    ap.add_argument("--audit-at-call", type=int, default=1,
                    help="which optimiser evaluation the accuracy census "
                         "audits (mode 'audit')")
    ap.add_argument("--resume", action="store_true",
                    help="skip runs that already have a complete, "
                         "driver-stamped metrics.json.  An interrupted run is "
                         "re-run; a directory alone is not taken as evidence "
                         "of a completed run")
    args = ap.parse_args()

    runs = Path(args.runs).resolve()
    runs.mkdir(parents=True, exist_ok=True)
    (runs / "_mplconfig").mkdir(exist_ok=True)
    decks = Path(args.decks).resolve() if args.decks else runs / "_decks"

    if args.mode == "decks":
        return stage_decks(runs, args.scenarios, decks)

    if not args.skip_warm:
        warm(runs, decks, TAU)

    if args.mode == "gate":
        jobs = jobs_gate(runs, args.scenarios, args.arms)
    elif args.mode == "calibrate":
        jobs = jobs_calibrate(runs, args.scenarios, args.deltas, args.starts)
    elif args.mode == "ladder":
        jobs = jobs_ladder(runs, args.scenarios, args.ladder_starts,
                           args.flat_taus, args.joint_taus, args.inner_taus,
                           delta=(args.delta if args.delta is not None
                                  else 0.10))
    else:
        if args.delta is None:
            raise SystemExit(
                "campaign needs --delta, and it comes from the calibration "
                "stage (D15(a): the perturbation size is calibrated, not "
                "chosen)"
            )
        if args.mode == "audit":
            jobs = jobs_audit(runs, args.scenarios, args.arms, args.starts,
                              args.delta, args.audit_at_call)
        else:
            jobs = jobs_campaign(
                runs, args.scenarios, args.arms, args.starts, args.delta,
                inner_tau=args.inner_tau, tag=args.tag,
            )

    if args.resume:
        # A run is complete only if run_one wrote its metrics AND the driver
        # stamped the arm into it afterwards; anything less was interrupted
        # mid-flight and is re-run.  Skipping on the presence of a directory,
        # or on a metrics file the driver never stamped, would silently keep a
        # partial record in the population.
        keep = []
        for job in jobs:
            m = job[2] / "metrics.json"
            if m.exists():
                try:
                    if "a28_arm" in json.loads(m.read_text()):
                        continue
                except Exception:
                    pass
            keep.append(job)
        print(f"resume: {len(jobs) - len(keep)} of {len(jobs)} already "
              f"complete, {len(keep)} to run", flush=True)
        jobs = keep

    print(f"{args.mode}: {len(jobs)} runs, {args.jobs} at a time", flush=True)
    log: list[dict] = []
    t0 = time.perf_counter()

    def do(job):
        s, a, outdir, d, k, tau, itau, audit = job
        r = run_one(
            s, a, outdir, runs, decks,
            tau=tau, inner_tau=itau, delta=d, seed=k, timeout=args.timeout,
            # The per-node cost-unit census is a gate-only instrument: it adds
            # a Python frame per model call, so it never runs in the campaign
            # whose counts are the result.
            node_census=(args.mode == "gate"),
            audit_at_call=audit,
        )
        print(
            f"  {s:22s} {a:14s} tau={tau:g} itau={itau} d={d} k={k:3d} "
            f"{'AUDIT' if audit else '     '} rc={r['rc']} "
            f"{r['wall_s']:6.1f}s",
            flush=True,
        )
        return r

    with ThreadPoolExecutor(max_workers=args.jobs) as ex:
        log.extend(ex.map(do, jobs))

    dt = time.perf_counter() - t0
    print(f"total {dt:.1f}s elapsed (progress information, not a measurement)",
          flush=True)
    (runs / f"_driver_log_{args.mode}.json").write_text(
        json.dumps({"mode": args.mode, "wall_s_total": dt, "runs": log},
                   indent=2)
    )
    # A29 (replication-verify): the exit code must not conflate "the
    # instrument failed" with "a perturbed start failed to solve".  In the
    # measurement modes -- calibrate, campaign, audit, ladder -- a start that
    # crashes or refuses IS the datum: the published calibration table reads
    # "11 / 12 (1 crashed)" and "7 / 12 (4 fail, 1 crashed)" at delta = 10 %,
    # and this driver reproduces exactly those crashes.  Returning 1 for them
    # made the one-command experiment stop at the first stage whose measured
    # system ever fails, while the stage-by-stage path in the results
    # document's section 8 sailed past the same exit code unnoticed -- the
    # two paths were NOT two paths to the same numbers, which the entry
    # point's own docstring declares a finding.  Failed runs stay recorded,
    # per run, in _driver_log_<mode>.json, and the analysis stages do the
    # drop census before any ratio.
    #
    # 'gate' keeps the strict policy: there a failure is an arrangement
    # failing its own deck's unperturbed point, and nothing downstream is
    # comparable.  And if EVERY run failed, that is an instrument failure in
    # any mode -- proceeding would hand the analysis an empty population,
    # the false pass this project has met before -- so it stays fatal too.
    n_bad = sum(1 for r in log if r["rc"] != 0)
    if n_bad:
        print(f"{n_bad} of {len(log)} runs did not solve; each is recorded "
              f"in _driver_log_{args.mode}.json.  In mode '{args.mode}' "
              + ("that is a measured result, not an instrument failure, and "
                 "the analysis stage reports it before any ratio."
                 if args.mode != "gate" else
                 "that is fatal: an arrangement failed its own deck's "
                 "unperturbed point."),
              flush=True)
    if args.mode == "gate":
        return 0 if n_bad == 0 else 1
    if n_bad == len(log) and log:
        print("EVERY run failed, which is an instrument failure in any "
              "mode, not a measured robustness result.  Stopping.",
              flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
