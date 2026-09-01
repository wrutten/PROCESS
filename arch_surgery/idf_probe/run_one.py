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
    except Exception:
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
    result["arch_module_solve_yspec"] = None
    if _module_solve is not None and getattr(_module_solve, "ENABLED", False):
        try:
            result["arch_module_solve_yspec"] = _module_solve.load_spec()[1]
        except Exception:
            result["arch_module_solve_yspec"] = {"error": traceback.format_exc()}

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
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
