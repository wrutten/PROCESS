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
import shutil
import subprocess
import sys
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _hex(v):
    if v is None:
        return None
    return float(v).hex()


def _hexes(seq):
    return [float(v).hex() for v in seq]


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
        if expect not in process_file.parents:
            raise SystemExit(
                f"WRONG TREE: imported {process_file}, expected it under {expect}"
            )
    result["tree"] = str(process_file.parent.parent)
    try:
        result["tree_git_head"] = subprocess.run(
            ["git", "-C", result["tree"], "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip() or None
    except Exception:
        result["tree_git_head"] = None

    try:
        from process.core import _idf_probe
    except ImportError:
        # The 'pristine' arm is an untouched checkout of the base commit: the
        # probe module does not exist there at all.
        _idf_probe = None
    result["probe_enabled"] = bool(_idf_probe and _idf_probe.ENABLED)
    result["probe_mode"] = _idf_probe.MODE if _idf_probe else None
    result["probe_module_present"] = _idf_probe is not None

    from process.main import SingleRun

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
