#!/usr/bin/env python
"""Run ONE scenario in ONE probe mode in a fresh interpreter.

Mandatory isolation: OutputFileManager's file handles are class attributes
(process-wide) and the global DataStructure is mutated by init_process, so at
most one PROCESS run may happen per interpreter.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--mode", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--tag", default="")
    args = ap.parse_args()

    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    src = HERE / "scenarios" / f"{args.scenario}.IN.DAT"
    dst = outdir / f"{args.scenario}.IN.DAT"
    shutil.copy(src, dst)

    # Probe configuration must be set before importing process.*
    probe_mode = "" if args.mode == "unpatched" else args.mode
    if probe_mode:
        os.environ["PROCESS_IDF_PROBE"] = probe_mode
        os.environ["PROCESS_IDF_PROBE_LOG"] = str(outdir / "probe.jsonl")
    else:
        os.environ.pop("PROCESS_IDF_PROBE", None)
        os.environ.pop("PROCESS_IDF_PROBE_LOG", None)

    result: dict = {
        "scenario": args.scenario,
        "mode": args.mode,
        "tag": args.tag,
        "outdir": str(outdir),
    }

    t0 = time.perf_counter()
    try:
        from process.core import _idf_probe
        from process.main import SingleRun

        sr = SingleRun(str(dst), solver="vmcon")
        sr.run()
        result["status"] = "ok"
        result["probe"] = _idf_probe.summary()
        result["epsfcn_final"] = float(sr.data.numerics.epsfcn)
        result["ncalls"] = int(sr.data.numerics.ncalls)
        result["nvar"] = int(sr.data.numerics.nvar)
        result["neqns"] = int(sr.data.numerics.neqns)
        result["nineqns"] = int(sr.data.numerics.nineqns)
    except Exception:
        result["status"] = "crashed"
        result["traceback"] = traceback.format_exc()
        try:
            from process.core import _idf_probe

            result["probe"] = _idf_probe.summary()
        except Exception:
            pass
    result["wall_s"] = time.perf_counter() - t0

    # Parse the MFILE regardless of status (it may exist even after a crash)
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
    print(json.dumps({k: v for k, v in result.items() if k != "mfile"}, indent=2)[:2000])
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
