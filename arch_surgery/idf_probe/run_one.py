#!/usr/bin/env python
"""Run ONE scenario, in ONE probe mode, in a fresh interpreter.

Isolation is mandatory, not a nicety: ``OutputFileManager`` holds its file
handles as *class* attributes (process-wide) and ``init.init_process`` mutates
a global data structure.  Two PROCESS runs in one interpreter contaminate each
other.  So: one run per process, each in its own working directory.

This script must be launched with ``PYTHONPATH`` pointing at the tree under
test -- see ``run_stage0.py`` and the README.  It asserts the tree it actually
imported and refuses to run if it is the wrong one.

Usage
-----
    PYTHONPATH=<tree> python run_one.py \
        --scenario large_tokamak_nof --mode baseline --outdir <dir> \
        --expect-tree <tree>
"""

from __future__ import annotations

import argparse
import json
import os
import resource
import shutil
import subprocess
import sys
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent

#: The study's frozen base commit (decision D2).  Every number is rederived
#: here; a tree that does not descend from it is measuring something else.
BASE_COMMIT = "c0ae5b28"


def _hex(v):
    if v is None:
        return None
    return float(v).hex()


def _hexes(seq):
    return [float(v).hex() for v in seq]


def _git(tree, *args):
    """Run one git command in *tree*; return its stripped output, or None."""
    try:
        out = subprocess.run(
            ["git", "-C", tree, *args],
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception:
        return None
    return out.stdout.strip() or None


def _provenance(tree):
    """Which tree, branch and commit this run is actually using.

    Recorded in every run's metrics and printed at startup.  Issue I-11: a task
    agent's working copy was once created from the wrong starting commit, and
    nothing in the output would have said so -- the code compiles, the run
    succeeds, and the numbers look reasonable.  Provenance that is only written
    to a file is provenance nobody reads in time, so it is printed too.
    """
    branch = _git(tree, "rev-parse", "--abbrev-ref", "HEAD")
    if branch == "HEAD":  # detached
        branch = "(detached)"
    status = _git(tree, "status", "--porcelain")
    return {
        "tree_git_head": _git(tree, "rev-parse", "HEAD"),
        "tree_git_branch": branch,
        "tree_git_describe": _git(tree, "describe", "--always", "--dirty"),
        "tree_git_dirty": bool(status),
        # Every number in this study is rederived at this commit; anything
        # measured elsewhere is not comparable.  See decisions D2 and D4.
        "tree_contains_base_commit": _descends_from(tree, BASE_COMMIT),
    }


def _descends_from(tree, commit):
    """True if *tree*'s HEAD descends from *commit*; None if it cannot be told.

    ``merge-base --is-ancestor`` answers through its exit status and prints
    nothing, so it needs its own runner rather than :func:`_git`.
    """
    try:
        return (
            subprocess.run(
                ["git", "-C", tree, "merge-base", "--is-ancestor", commit, "HEAD"],
                capture_output=True,
                check=False,
            ).returncode
            == 0
        )
    except Exception:
        return None


def _print_provenance(result):
    """Print the provenance banner, so a wrong tree is visible immediately."""
    head = result.get("tree_git_head") or "unknown"
    lines = [
        "-" * 68,
        f"  tree     {result['tree']}",
        f"  branch   {result.get('tree_git_branch') or 'unknown'}",
        f"  commit   {head[:12]}"
        + ("  [UNCOMMITTED CHANGES]" if result.get("tree_git_dirty") else ""),
    ]
    if result.get("tree_contains_base_commit") is False:
        lines.append(
            f"  WARNING  this tree does not descend from the base commit "
            f"{BASE_COMMIT[:8]}."
        )
        lines.append(
            "           Numbers from it are not comparable with the rest of "
            "the study."
        )
    lines.append("-" * 68)
    print("\n".join(lines), flush=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", required=True)
    ap.add_argument(
        "--mode",
        required=True,
        help="'control' (probe env var unset) or a PROCESS_IDF_PROBE mode "
        "such as 'baseline'. Any mode name may carry a '_repN' suffix, which "
        "is stripped before being passed to the probe.",
    )
    ap.add_argument("--outdir", required=True)
    ap.add_argument(
        "--input",
        default=None,
        help="override the scenario IN.DAT (default: scenarios/<scenario>.IN.DAT). "
        "Used for the diagnostic re-run of st_regression against the base "
        "commit's own regression input.",
    )
    ap.add_argument(
        "--expect-tree",
        default=None,
        help="assert process.__file__ lives under this directory",
    )
    ap.add_argument(
        "--perturb-delta",
        type=float,
        default=None,
        help="A25/D15: multi-start perturbation size, e.g. 0.05 for 5 %%. "
        "Each iteration variable's initial value is multiplied by 1 + delta*u "
        "with u drawn in [-1, 1] from a hash of (--perturb-seed, ixc number) "
        "-- keyed on the VARIABLE NUMBER, not on its position, so the two arms "
        "give bit-identical factors to every variable they share even though "
        "the variant's design vector is one longer.",
    )
    ap.add_argument(
        "--perturb-seed",
        type=int,
        default=0,
        help="start index of the multi-start campaign; 0 leaves the deck's own "
        "point unperturbed even when --perturb-delta is given.",
    )
    ap.add_argument(
        "--exit-audit",
        default=None,
        help="A28: path to the deck's committed ystate_<scenario>.json.  "
        "After the run finishes, take ONE further full sweep of the complete "
        "model set and record the coupling-state residual it moves by -- the "
        "accuracy the arm actually ACHIEVED, which is what arms must be "
        "compared at (A26 fix 1).  Identical for every arm: a fresh Caller "
        "with nothing hoisted and no block filter, so all arms audit the same "
        "model set.  Its model calls are counted and reported separately and "
        "are never charged to the arm (accounting.py).",
    )
    ap.add_argument(
        "--exit-audit-at-call",
        type=int,
        default=0,
        help="A28: take the exit audit at the return of the Nth call_models "
        "of the SOLVE phase, then stop the run.  This is the accuracy "
        "measure, and the post-run audit is not: after SingleRun.run() the "
        "output path has re-converged the state to MFILE idempotence, which "
        "is stricter than any arm's own test, so a post-run audit reads zero "
        "for every arm at every tolerance and discriminates nothing "
        "(measured, not assumed).  The audit sweep MUTATES the state, so a "
        "run that takes one cannot be allowed to continue: it stops, and its "
        "cost figure is not used.  Cost comes from the un-audited run of the "
        "same setting and the same start.",
    )
    ap.add_argument(
        "--node-census",
        action="store_true",
        help="A28: count model node calls PER NODE NAME, harness-side, by "
        "wrapping Caller._node.  This is how the cost unit is checked rather "
        "than asserted: the per-name counts must sum to "
        "node_calls_solve_phase, and a hoisted node must run exactly once per "
        "call_models.  A26 §7.3 found the opposite accounting error by "
        "publishing a difference whose composition it could not state.  Not "
        "for the campaign -- it adds a Python frame per model call.",
    )
    ap.add_argument(
        "--entry-census",
        action="store_true",
        help="A28 / issue I-12: record net electric power at the state each "
        "call_models is ENTERED with, and count the non-positive ones.  "
        "PROCESS's 1990 cost model diverges where net electric power is not "
        "positive, which makes a median-scaled relative test arbitrarily "
        "tight there; perturbed multi-starts visit such states by design.  "
        "Harness-side and identical in every arm: it reads one float per "
        "call and touches nothing.",
    )
    args = ap.parse_args()

    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    src = (
        Path(args.input)
        if args.input
        else HERE / "scenarios" / f"{args.scenario}.IN.DAT"
    )
    dst = outdir / f"{args.scenario}.IN.DAT"
    shutil.copy(src, dst)

    # Probe mode: 'control' means the switch is unset.  '<mode>_repN' is a
    # replicate of '<mode>'.
    base_mode = args.mode.split("_rep")[0]
    probe_mode = "" if base_mode == "control" else base_mode
    if probe_mode:
        os.environ["PROCESS_IDF_PROBE"] = probe_mode
    else:
        os.environ.pop("PROCESS_IDF_PROBE", None)

    result: dict = {
        "scenario": args.scenario,
        "mode": args.mode,
        "probe_env": os.environ.get("PROCESS_IDF_PROBE"),
        "outdir": str(outdir),
        "input_file": str(src.resolve()),
        "python": sys.executable,
        "pythonpath": os.environ.get("PYTHONPATH"),
    }

    # ------------------------------------------------------------------
    # The setup trap: `pip show process` points the editable install at a
    # *different* clone.  Prove which tree we actually imported before doing
    # any work at all.
    # ------------------------------------------------------------------
    import process

    process_file = Path(process.__file__).resolve()
    result["process_file"] = str(process_file)
    if args.expect_tree:
        expect = Path(args.expect_tree).resolve()
        # Trap T6: the editable install points at the *main* checkout, so a
        # worktree's code is only imported when PYTHONPATH says so.  A prefix
        # test ("is it under a directory called PROCESS_surgery?") passes for
        # the main checkout as well and would silently measure the wrong tree.
        # Require the exact tree: <expect>/process/__init__.py.
        actual_tree = process_file.parent.parent
        if actual_tree != expect:
            raise SystemExit(
                f"WRONG TREE: imported {process_file} (tree {actual_tree}), "
                f"expected exactly {expect}. Set "
                f"PYTHONPATH={expect} for this subprocess."
            )
    result["tree"] = str(process_file.parent.parent)
    result.update(_provenance(result["tree"]))
    _print_provenance(result)

    try:
        from process.core import _idf_probe
    except ImportError:
        # The 'pristine' arm is an untouched checkout of the base commit: the
        # probe module does not exist there at all.
        _idf_probe = None
    result["probe_enabled"] = bool(_idf_probe and _idf_probe.ENABLED)
    result["probe_mode"] = _idf_probe.MODE if _idf_probe else None
    result["probe_module_present"] = _idf_probe is not None

    # VP1 (A3): which model-call sequence the imported tree actually resolved.
    # Recorded from the imported module, not from the environment variable, so
    # that a run against a tree that predates the variant point says so instead
    # of silently reporting the arm the driver *asked* for.
    from process.core import caller as _caller

    # VP2 (A13): whether the imported tree resolved a feed-forward hoist, and
    # which nodes it resolved.  Read from the module, not the environment, so a
    # tree that predates the variant point reports ``None`` rather than the arm
    # the driver asked for.
    result["arch_hoist_env"] = os.environ.get("PROCESS_ARCH_HOIST")
    result["arch_hoist_name"] = getattr(_caller, "HOIST_NAME", None)
    hoist_nodes = getattr(_caller, "HOIST_NODES", None)
    result["arch_hoist_nodes"] = list(hoist_nodes) if hoist_nodes is not None else None

    # VP5 (A24): whether the imported tree resolved a lifted sub-solve site,
    # and which sites.  Read from the module rather than the environment, so a
    # tree that predates the variant point -- the ``parent`` arm, where the
    # module does not exist at all -- reports ``None`` instead of echoing back
    # the arm the driver asked for.
    result["arch_lift_env"] = os.environ.get("PROCESS_ARCH_LIFT")
    try:
        from process.core.solver import subsolve as _subsolve
    except ImportError:
        _subsolve = None
    result["arch_lift_module_present"] = _subsolve is not None
    result["arch_lift_sites"] = (
        sorted(_subsolve.LIFTED_SITES) if _subsolve is not None else None
    )
    result["arch_lift_known_sites"] = (
        list(_subsolve.SITES) if _subsolve is not None else None
    )

    # VP4 (A25): whether the imported tree resolved a per-module solve arm, at
    # what tolerance, and against which deck's coupling-state artifact.  Read
    # from the modules, not from the environment (the A3/A13/A24 pattern).
    result["arch_module_solve_env"] = os.environ.get("PROCESS_ARCH_MODULE_SOLVE")
    result["arch_tau_env"] = os.environ.get("PROCESS_ARCH_TAU")
    result["arch_ystate_env"] = os.environ.get("PROCESS_ARCH_YSTATE")
    try:
        from process.core.solver import module_solve as _module_solve
    except ImportError:
        _module_solve = None
    result["arch_module_solve_module_present"] = _module_solve is not None
    result["arch_module_solve_name"] = (
        getattr(_module_solve, "MODULE_SOLVE_NAME", None)
        if _module_solve is not None
        else None
    )
    result["arch_module_solve_tau"] = (
        getattr(_module_solve, "TAU", None) if _module_solve is not None else None
    )
    result["arch_inner_tau_env"] = os.environ.get("PROCESS_ARCH_INNER_TAU")
    result["arch_module_solve_inner_tau"] = (
        getattr(_module_solve, "INNER_TAU", None)
        if _module_solve is not None
        else None
    )
    result["arch_module_solve_flat_state"] = (
        getattr(_module_solve, "FLAT_STATE", None)
        if _module_solve is not None
        else None
    )

    # VP2c (A33): whether the imported tree resolved a post-solve exclusion,
    # and from which artifact.  Read from the module, not the environment
    # (the A3/A13/A24 pattern); a tree that predates the variant point
    # reports ``None`` rather than echoing the arm the driver asked for.
    result["arch_post_solve_env"] = os.environ.get("PROCESS_ARCH_POST_SOLVE")
    result["arch_post_solve_enabled"] = getattr(
        _caller, "POST_SOLVE_ENABLED", None
    )
    result["arch_post_solve_artifact"] = getattr(
        _caller, "POST_SOLVE_PATH", None
    )

    # A28: what the loop and the block schedule actually resolved to, read
    # from the imported modules and the committed node map rather than from
    # the environment.  These are the descriptor a comparison manifest is
    # checked against (fixedpoint/manifest.py), so they must describe the run
    # and not the intention.
    try:
        _nm = json.loads(_caller.NODE_MAP_PATH.read_text())["nodes"]
        # The same restriction ``caller._loop_node_set`` applies, so that every
        # arm reports the same node set and a comparison of two arms compares
        # schedules rather than bookkeeping.  ``<x_inject>`` (module ``X``) is
        # excluded: it is the design-vector injection at the head of
        # ``_call_models_once``, not a model, it is not routed through
        # ``Caller._node``, and it runs unconditionally on every sweep of every
        # arm.
        _labels = set(_module_solve.BLOCK_ORDER) if _module_solve else set()
        _loop_all = sorted(
            n for n, e in _nm.items()
            if e.get("module") in _labels and e.get("in_call_models_once")
        )
    except Exception:
        _loop_all = None
    result["arch_node_map_loop_nodes"] = _loop_all
    _tail_resolved = []
    try:
        if getattr(_caller, "HOIST_ENABLED", False):
            _tail_resolved = list(_caller.HOIST_NODES)
    except Exception:
        _tail_resolved = []
    result["arch_loop_nodes"] = (
        None if _loop_all is None
        else sorted(set(_loop_all) - set(_tail_resolved))
    )

    result["arch_sequence_env"] = os.environ.get("PROCESS_ARCH_SEQUENCE")
    result["arch_sequence_name"] = getattr(_caller, "SEQUENCE_NAME", None)
    head = getattr(_caller, "SEQUENCE_HEAD", None)
    result["arch_sequence_head"] = list(head) if head is not None else None

    # ------------------------------------------------------------------
    # D15(a) multi-start: perturb the *initial design vector*, identically in
    # both arms.  The hook wraps ``load_scaled_bounds`` rather than
    # ``load_iteration_variables`` because it must run after BOTH: the scaled
    # bounds are what a perturbed start is clamped into, and a start outside
    # its own box is not a start, it is a different problem.
    #
    # Nothing under ``process/`` is touched: this is a harness monkeypatch on
    # the measurement side, applied identically to baseline and variant.
    # ------------------------------------------------------------------
    result["perturb_delta"] = args.perturb_delta
    result["perturb_seed"] = args.perturb_seed
    if args.perturb_delta and args.perturb_seed:
        import hashlib

        import process.core.solver.solver_handler as _sh

        _orig_bounds = _sh.load_scaled_bounds
        _record: dict = {}

        def _factor(seed: int, ivar: int, delta: float) -> float:
            """``1 + delta*u``, ``u`` in [-1, 1), from a hash of (seed, ivar).

            Keyed on the iteration-variable NUMBER so that the arms agree on
            every shared variable regardless of how many variables each has.
            """
            h = hashlib.sha256(f"a25|{seed}|{ivar}".encode()).digest()
            u = int.from_bytes(h[:8], "big") / float(1 << 64)  # [0, 1)
            return 1.0 + delta * (2.0 * u - 1.0)

        def _perturbed(data):
            _orig_bounds(data)
            nums = data.numerics
            n = int(nums.n_iteration_variables)
            rows = []
            n_clamped = 0
            for i in range(n):
                ivar = int(nums.ixc[i])
                f = _factor(args.perturb_seed, ivar, args.perturb_delta)
                before = float(nums.xcm[i])
                want = before * f
                lo = float(nums.itv_scaled_lower_bounds[i])
                hi = float(nums.itv_scaled_upper_bounds[i])
                got = min(max(want, lo), hi)
                if got != want:
                    n_clamped += 1
                nums.xcm[i] = got
                rows.append({
                    "ixc": ivar,
                    "factor": f,
                    "scaled_before": before,
                    "scaled_after": got,
                    "clamped": got != want,
                })
            _record["per_variable"] = rows
            _record["n_variables"] = n
            _record["n_clamped_to_bounds"] = n_clamped

        _sh.load_scaled_bounds = _perturbed
        result["perturbation"] = _record

    # ------------------------------------------------------------------
    # I-12: net electric power at the state each ``call_models`` is entered
    # with.  A22 found 7 of st_regression's 144 design points needing 4-7
    # outer passes where every other point needs 2, and on 6 of them the
    # ENTRY state has negative net electric power, which sends costs.coe to
    # ~1e21 and makes our median-scaled test ~1e18 times tighter than
    # intended.  D15's perturbed multi-starts visit infeasible entry states
    # by design, so this is expected to recur and is measured rather than
    # hoped against.
    #
    # Harness-side, at class level, before any Caller exists, and applied
    # identically to every arm: it reads one float and appends it to a list.
    # ------------------------------------------------------------------
    result["node_census"] = None
    if args.node_census:
        _ncounts: dict = {}
        _orig_node = _caller.Caller._node

        def _node_censused(self, name, run):
            before = _caller.NODE_CALLS[0]
            _orig_node(self, name, run)
            if _caller.NODE_CALLS[0] != before:
                _ncounts[name] = _ncounts.get(name, 0) + 1

        _caller.Caller._node = _node_censused
        _orig_tail = _caller.Caller._run_hoisted_tail
        _tailcounts: dict = {}

        def _tail_censused(self, pending):
            for nm, _r in pending:
                _tailcounts[nm] = _tailcounts.get(nm, 0) + 1
            return _orig_tail(self, pending)

        _caller.Caller._run_hoisted_tail = _tail_censused
        result["node_census"] = {"counted": _ncounts, "flat_tail": _tailcounts}

    result["entry_census"] = None
    if args.entry_census:
        _entry: dict = {"p_plant_electric_net_mw_at_entry": []}
        _orig_call_models = _caller.Caller.call_models

        def _call_models_censused(self, xc, m):
            try:
                _entry["p_plant_electric_net_mw_at_entry"].append(
                    float(self.data.heat_transport.p_plant_electric_net_mw)
                )
            except Exception:  # noqa: BLE001 - a census must never break a run
                _entry["p_plant_electric_net_mw_at_entry"].append(None)
            return _orig_call_models(self, xc, m)

        _caller.Caller.call_models = _call_models_censused
        result["entry_census"] = _entry

    # ------------------------------------------------------------------
    # A28: the accuracy measure -- how converged the plant state is when the
    # arm hands the optimiser its objective and constraints.  That is what tau
    # controls and what differs between arms, and it can only be measured
    # where the arm actually stops.
    # ------------------------------------------------------------------
    result["audit_at_call"] = None
    if args.exit_audit_at_call:
        if not args.exit_audit:
            raise SystemExit(
                "--exit-audit-at-call needs --exit-audit to name the deck's "
                "committed ystate artifact"
            )

        class _AuditStop(Exception):
            """The audit has been taken; the run must not continue."""

        _acc: dict = {"n": 0}
        _orig_cm = _caller.Caller.call_models

        def _call_models_audited(self, xc, m):
            objf, conf = _orig_cm(self, xc, m)
            _acc["n"] += 1
            if _acc["n"] < args.exit_audit_at_call:
                return objf, conf
            try:
                from process.core.solver import module_solve as _ms
                spec, prov = _ms.load_spec(args.exit_audit)
                bound = spec.bind(self.data)
                y0 = spec.read(bound)
                n_before = _caller.NODE_CALLS[0]
                # A fresh Caller with nothing hoisted and no block filter, so
                # every arm audits the same model set.
                _caller.Caller(self.models, self.data)._call_models_once(xc)
                y1 = spec.read(bound)
                res = spec.residual(y0, y1)
                tau = getattr(_ms, "TAU", 1e-6)
                _acc["record"] = {
                    "at_call_models": _acc["n"],
                    "components_sha256": prov.get("components_sha256"),
                    "n_components": prov.get("n_components"),
                    "tau_for_the_brief": tau,
                    "residual_max": res.max,
                    "residual_max_hex": _hex(res.max),
                    "brief": res.brief(tau),
                    "audit_node_calls": _caller.NODE_CALLS[0] - n_before,
                    "node_calls_before_audit": n_before,
                    "note": (
                        "one further full sweep of the complete model set at "
                        "the return of this call_models; the run is stopped "
                        "immediately afterwards because the sweep mutates the "
                        "state.  This run's cost figure is NOT a cost figure"
                    ),
                }
            except Exception:
                _acc["record"] = {"error": traceback.format_exc()}
            raise _AuditStop

        _caller.Caller.call_models = _call_models_audited

    from process.main import SingleRun

    # I-8 diagnostic: CPU time beside wall clock.  If the CPU-time spread
    # across replicates is much narrower than the wall-clock spread, the
    # variance is machine contention rather than the code.
    ru0 = resource.getrusage(resource.RUSAGE_SELF)
    t0 = time.perf_counter()
    try:
        sr = SingleRun(str(dst), solver="vmcon", update_obsolete=True)
        sr.run()
        result["status"] = "ok"
    except Exception as exc:
        if args.exit_audit_at_call and type(exc).__name__ == "_AuditStop":
            # Not a crash: the audit was taken and the run was stopped on
            # purpose.  Named so the census cannot mistake it for a failure.
            result["status"] = "audit_stop"
            result["audit_at_call"] = _acc.get("record")
        else:
            sr = None
            result["status"] = "crashed"
            result["traceback"] = traceback.format_exc()
    result["wall_s"] = time.perf_counter() - t0
    ru1 = resource.getrusage(resource.RUSAGE_SELF)
    result["cpu_user_s"] = ru1.ru_utime - ru0.ru_utime
    result["cpu_sys_s"] = ru1.ru_stime - ru0.ru_stime
    result["cpu_s"] = result["cpu_user_s"] + result["cpu_sys_s"]
    result["maxrss_kb"] = ru1.ru_maxrss
    try:
        result["loadavg"] = os.getloadavg()
    except OSError:
        result["loadavg"] = None

    # VP4 cost unit: individual model node calls, split at the solve/output
    # boundary.  Recorded on both arms.
    result["node_calls_total"] = getattr(_caller, "NODE_CALLS", [None])[0]
    result["node_calls_solve_phase"] = getattr(
        _caller, "NODE_CALLS_AT_OUTPUT", [None]
    )[0]
    _tot = getattr(_caller, "MODULE_SOLVE_TOTALS", None)
    if _tot is not None:
        _tot = dict(_tot)
        _tot["moved_constants"] = sorted(_tot.get("moved_constants", ()))
        result["module_solve_totals"] = _tot
    # VP2c (A33): the post-solve exclusion's own counts -- how many solve-
    # phase call sites were suppressed, per node, and the one-shot execution
    # record.  Absent (None) on trees that predate the variant point;
    # reported only when the switch resolved, so the switch-off record is
    # unchanged in content.
    _pst = getattr(_caller, "POST_SOLVE_TOTALS", None)
    result["post_solve_totals"] = (
        dict(_pst)
        if (_pst is not None and getattr(_caller, "POST_SOLVE_ENABLED", False))
        else None
    )
    result["arch_module_solve_yspec"] = None
    if _module_solve is not None and getattr(_module_solve, "ENABLED", False):
        try:
            result["arch_module_solve_yspec"] = _module_solve.load_spec()[1]
        except Exception:
            result["arch_module_solve_yspec"] = {"error": traceback.format_exc()}

    # ------------------------------------------------------------------
    # A28 / A26 fix 1: the accuracy the arm ACHIEVED.
    #
    # One further full sweep of the complete model set, past termination,
    # measuring how far the coupling state still moves.  Phase A's exit audit
    # in the driver.  It is the same instrument for every arm at every
    # setting -- a fresh Caller, nothing hoisted, no block filter -- which is
    # what makes "compare at matched achieved accuracy" mean anything.
    #
    # Its own model calls are recorded and NEVER charged to the arm: the cost
    # figure is frozen at the entry to write_output_files, and charging the
    # measurement to what is measured is the accounting error accounting.py
    # exists to prevent.
    # ------------------------------------------------------------------
    result["exit_audit"] = None
    if args.exit_audit and not args.exit_audit_at_call:
        try:
            _n_before = getattr(_caller, "NODE_CALLS", [0])[0]
            if sr is None:
                raise RuntimeError("the run crashed; there is no exit state")
            if _module_solve is None:
                raise RuntimeError("module_solve is absent from this tree")
            _spec, _sprov = _module_solve.load_spec(args.exit_audit)
            _nx = int(sr.data.numerics.n_iteration_variables)
            _x = sr.data.numerics.xcm[:_nx]
            _bound = _spec.bind(sr.data)
            _y0 = _spec.read(_bound)
            _audit_caller = _caller.Caller(sr.models, sr.data)
            _audit_caller._call_models_once(_x)
            _y1 = _spec.read(_bound)
            _res = _spec.residual(_y0, _y1)
            _tau = getattr(_module_solve, "TAU", 1e-6)
            result["exit_audit"] = {
                "ystate": str(args.exit_audit),
                "scenario": _sprov.get("scenario"),
                "components_sha256": _sprov.get("components_sha256"),
                "n_components": _sprov.get("n_components"),
                "tau_for_the_brief": _tau,
                "residual_max": _res.max,
                "residual_max_hex": _hex(_res.max),
                "brief": _res.brief(_tau),
                "audit_node_calls": (
                    getattr(_caller, "NODE_CALLS", [0])[0] - _n_before
                ),
                "charged_to_the_arm": False,
                "note": (
                    "one further full sweep of the complete model set past "
                    "termination; identical instrument in every arm; its node "
                    "calls are excluded from node_calls_solve_phase, which was "
                    "frozen at the entry to write_output_files"
                ),
            }
        except Exception:
            result["exit_audit"] = {"error": traceback.format_exc()}

    result["probe"] = (
        _idf_probe.summary()
        if _idf_probe
        else {"enabled": False, "mode": None, "module_absent": True}
    )

    if sr is not None:
        nums = sr.data.numerics
        n = int(nums.n_iteration_variables)
        meq = int(nums.n_equality_constraints)
        mineq = int(nums.n_inequality_constraints)
        m = meq + mineq
        rcm = list(nums.rcm[:m])
        result.update({
            "solver_name": sr.solver,
            "nvar": n,
            "n_equality_constraints": meq,
            "n_inequality_constraints": mineq,
            "n_constraints": m,
            "n_solver_iterations": int(nums.n_solver_iterations),
            "n_model_calls": int(nums.n_model_calls),
            "epsfcn_final": float(nums.epsfcn),
            "i_process_run_mode": int(nums.i_process_run_mode),
            "i_figure_merit": int(nums.i_figure_merit),
            # VP2 (A13): the tail this run actually deferred -- the arm's node
            # set less any node the active figure of merit reads.  Recorded
            # per run because it depends on the deck, not only on the arm.
            "arch_hoist_tail_resolved": (
                list(_caller.resolved_hoist_tail(nums.i_figure_merit))
                if hasattr(_caller, "resolved_hoist_tail")
                else None
            ),
            # A28: the two hoist slots separately (plan §4.1d/§4.1e), and the
            # block schedule this deck's figure of merit resolved.
            "arch_hoist_tails_resolved": (
                [list(t) for t in
                 _caller.resolved_hoist_tails(nums.i_figure_merit)]
                if hasattr(_caller, "resolved_hoist_tails")
                else None
            ),
            "arch_block_schedule": (
                [
                    [lab, sorted(ns), bool(it)]
                    for lab, ns, it in
                    _caller.module_schedule(nums.i_figure_merit)[0]
                ]
                if getattr(_caller, "MODULE_SOLVE_ENABLED", False)
                else None
            ),
            "itvar_names": [
                str(nums.lablxc[int(nums.ixc[i]) - 1]).strip() for i in range(n)
            ],
        })
        norm_objf = nums.norm_objf
        result["values"] = {
            "norm_objf": None if norm_objf is None else float(norm_objf),
            "sqsumsq": float(nums.sqsumsq),
            "xcs": [float(v) for v in nums.xcs[:n]],
            "xcm": [float(v) for v in nums.xcm[:n]],
            "rcm": [float(v) for v in rcm],
            "conf_l2": float(sum(r * r for r in rcm) ** 0.5),
        }
        # Bit-exact representation: what gates (a) and (b) actually compare.
        result["exact"] = {
            "norm_objf": _hex(norm_objf),
            "sqsumsq": _hex(nums.sqsumsq),
            "xcs": _hexes(nums.xcs[:n]),
            "xcm": _hexes(nums.xcm[:n]),
            "rcm": _hexes(rcm),
            "conf_l2": _hex(sum(r * r for r in rcm) ** 0.5),
        }

    # A25 / plan section 2.5: **the variant must satisfy its own consistency
    # residual.**  Without this check the variant could "win" by returning a
    # point that is not on the burn-time consistency manifold at all, which is
    # not a solution to the same problem.  Computed directly from the returned
    # state through the model's own extracted relation, not read back from a
    # table, and recorded whenever the deck names icc = 93 -- so a deck that
    # does not name it reports ``null`` rather than a silent pass.
    result["constraint_93"] = None
    if sr is not None:
        try:
            nums = sr.data.numerics
            m_all = int(nums.n_equality_constraints) + int(
                nums.n_inequality_constraints
            )
            icc = [int(v) for v in nums.icc[:m_all]]
            if 93 in icc:
                from process.models.pulse import burn_time_residual

                t_burn = float(sr.data.times.t_plant_pulse_burn)
                res_s = float(
                    burn_time_residual(
                        t_burn,
                        sr.data.pf_coil.vs_cs_pf_total_burn,
                        sr.data.physics.v_plasma_loop_burn,
                        sr.data.times.t_plant_pulse_fusion_ramp,
                    )
                )
                j = icc.index(93)
                result["constraint_93"] = {
                    "position_in_icc": j,
                    "is_in_equality_block": j < int(nums.n_equality_constraints),
                    "n_equality_constraints": int(nums.n_equality_constraints),
                    "t_plant_pulse_burn_s": t_burn,
                    "residual_s": res_s,
                    "residual_relative_to_burn_time": (
                        abs(res_s) / abs(t_burn) if t_burn else None
                    ),
                    "normalised_residual_rcm": float(nums.rcm[j]),
                }
        except Exception:
            result["constraint_93"] = {"error": traceback.format_exc()}

    # MFILE is the independent cross-check (and the only source of ifail).
    try:
        sys.path.insert(0, str(HERE))
        from metrics import parse_mfile

        mf = outdir / f"{args.scenario}MFILE.DAT"
        if not mf.exists():
            cand = sorted(outdir.glob("*MFILE.DAT"))
            mf = cand[0] if cand else mf
        result["mfile"] = parse_mfile(mf) if mf.exists() else {"error": "no MFILE"}
    except Exception:
        result["mfile"] = {"error": traceback.format_exc()}

    if result.get("node_census") is not None:
        _nc = result["node_census"]
        _counted_total = sum(_nc["counted"].values())
        _tail_total = sum(_nc["flat_tail"].values())
        result["node_census"] = {
            "per_node_counted_through_Caller_node": dict(
                sorted(_nc["counted"].items())
            ),
            "per_node_run_through_flat_hoisted_tail_UNCOUNTED": dict(
                sorted(_nc["flat_tail"].items())
            ),
            "sum_counted": _counted_total,
            "sum_flat_tail_uncounted": _tail_total,
            "node_calls_total_reported": result.get("node_calls_total"),
            "node_calls_solve_phase_reported": result.get(
                "node_calls_solve_phase"
            ),
            "audit_node_calls": (
                (result.get("exit_audit") or {}).get("audit_node_calls")
            ),
            # node_calls_total is read at the END OF THE RUN, before the exit
            # audit takes its extra sweep -- and that sweep goes through
            # Caller._node like any other, so the per-node census sees it and
            # the reported total does not.  The identity below is therefore the
            # check, and it is a stronger one than equality would have been: it
            # says both that nothing is uncounted AND that the audit's cost is
            # exactly what the audit reports and is excluded from the arm's.
            "counted_matches_node_calls_total": (
                _counted_total
                == (result.get("node_calls_total") or 0)
                + int((result.get("exit_audit") or {}).get(
                    "audit_node_calls") or 0)
            ),
            "why": (
                "the cost unit checked rather than asserted.  Caller._node "
                "increments NODE_CALLS; Caller._run_hoisted_tail calls each "
                "model directly and does NOT, which is the accounting error "
                "A26 §7.3 found by publishing a difference whose composition "
                "it could not state.  Under a block schedule the tail is run "
                "as a block sweep and therefore goes through _node; under the "
                "flat loop it does not.  sum_flat_tail_uncounted must be 0 "
                "for any arm whose cost figure is quoted as net model "
                "evaluations without adding the tail back.  The identity "
                "checked is sum_counted == node_calls_total + "
                "audit_node_calls, because the exit audit's sweep runs "
                "through _node after node_calls_total is read."
            ),
        }

    if result.get("entry_census") is not None:
        _vals = result["entry_census"]["p_plant_electric_net_mw_at_entry"]
        _fin = [v for v in _vals if v is not None]
        # The FIRST entry is not a physical state: the very first call_models
        # of a run is entered before any model has run, with
        # p_plant_electric_net_mw at its declared default of 0.0.  Counting it
        # as a degenerate entry would report a degenerate start on every run
        # of every arm -- a zero denominator dressed as a finding.  It is
        # reported separately rather than silently dropped.
        _rest = _fin[1:]
        _neg = [v for v in _rest if v <= 0.0]
        result["entry_census"] = {
            "n_call_models_entries_recorded": len(_vals),
            "n_recorded_as_float": len(_fin),
            "first_entry_p_net_mw": _fin[0] if _fin else None,
            "first_entry_excluded_because": (
                "entered before any model has run; the field is at its "
                "declared default and is not a state the loop reached"
            ),
            "denominator_entries_after_the_first": len(_rest),
            "n_non_positive_entries": len(_neg),
            "min_entry_p_net_mw": min(_rest) if _rest else None,
            "max_entry_p_net_mw": max(_rest) if _rest else None,
            "start_is_degenerate": bool(_neg),
            "why": (
                "issue I-12: PROCESS's 1990 cost model diverges where net "
                "electric power is not positive, so a median-scaled relative "
                "convergence test becomes arbitrarily tight there.  Reported "
                "with its denominator beside every cost figure."
            ),
        }
        (outdir / "entry_census_series.json").write_text(json.dumps(_vals))

    probe_block = result.get("probe") or {}
    modules_block = probe_block.pop("modules", None) if isinstance(probe_block, dict) else None
    if modules_block:
        (outdir / "probe_modules.json").write_text(json.dumps(modules_block, indent=2))
        probe_block["modules_written_to"] = "probe_modules.json"
    (outdir / "metrics.json").write_text(json.dumps(result, indent=2))
    brief = {
        k: v
        for k, v in result.items()
        if k not in ("mfile", "values", "exact", "traceback", "itvar_names")
    }
    brief["ifail"] = result.get("mfile", {}).get("ifail")
    print(json.dumps(brief, indent=2, default=str))
    return 0 if result["status"] in ("ok", "audit_stop") else 1


if __name__ == "__main__":
    raise SystemExit(main())
