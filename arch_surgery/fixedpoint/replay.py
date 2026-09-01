#!/usr/bin/env python
"""Replay one scenario's harvested design points through the Phase A arms.

Runs in a **fresh subprocess with its own working directory** (mandatory:
``OutputFileManager`` holds file handles as class attributes and
initialisation mutates a global data structure) and asserts the **exact** tree
it imported, not a path prefix -- trap T6, because in a ``git worktree`` the
editable install still points at the main checkout.

``SingleRun.__init__`` builds ``models`` and ``data`` without solving anything,
which is all the replay needs: every field of ``data`` is then overwritten from
the harvested entry state, so the freshly initialised values do not survive and
cannot influence a result.  The optimiser is never constructed.  That is what
"the optimiser absent" means in Phase A.

Usage
-----
    PYTHONPATH=<tree> python replay.py --harvest H.pkl --scenario S \\
        --input S.IN.DAT --out result.json --tau 1e-6 --arms R A0 A0f A1
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import sys
import time
import traceback
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from fixedpoint import arms as A  # noqa: E402
from fixedpoint import engine as E  # noqa: E402
from fixedpoint.gen_ystate import OUT_DIR as YSTATE_DIR  # noqa: E402
from fixedpoint.gen_ystate import harvest_identity  # noqa: E402
from fixedpoint.nodemap import NodeMap  # noqa: E402
from fixedpoint.ystate import YSpec, _same  # noqa: E402


# --------------------------------------------------------------------------
# State restore -- the analogue of A19's _restore_state across a process
# boundary
# --------------------------------------------------------------------------


def bind_state(data, state):
    """Pre-resolve ``(namespace object, field, harvested value)`` once."""
    out = []
    for (ns_name, fld), v in state.items():
        out.append((getattr(data, ns_name), fld, v))
    return out


def restore(bound) -> None:
    """Put the harvested entry state back, exactly.

    Arrays and lists are filled **in place** wherever shape and dtype allow,
    so any model object holding a direct reference to one still sees the
    restored values -- the same property A19's in-process restore relies on,
    and the reason it verified 0 mismatched fields across all 2 288 fields in
    2 447 replays.
    """
    for ns, fld, v in bound:
        cur = object.__getattribute__(ns, fld)
        if (
            type(cur) is np.ndarray
            and type(v) is np.ndarray
            and cur.shape == v.shape
            and cur.dtype == v.dtype
        ):
            cur[...] = v
        elif type(cur) is list and type(v) is list:
            cur[:] = copy.deepcopy(v)
        elif type(v) is np.ndarray:
            object.__setattr__(ns, fld, v.copy())
        elif type(v) is list:
            object.__setattr__(ns, fld, copy.deepcopy(v))
        else:
            object.__setattr__(ns, fld, v)


def verify_restore(bound) -> list:
    """Field-by-field verification.  Returns the names that do not match."""
    bad = []
    for ns, fld, v in bound:
        cur = object.__getattribute__(ns, fld)
        if not _same(cur, v):
            bad.append(f"{type(ns).__name__}.{fld}")
    return bad


# --------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------


def _check_ystate(scenario: str, spec: YSpec, harvest_path, harvest) -> dict:
    """Compare the live categorisation against the committed record.

    Three outcomes.  ``OK`` -- the committed record exists and agrees, on both
    the harvest identity and the categorisation hash.  ``MISSING`` -- no record
    is committed yet, which is not fatal (it is how the first run of a new
    scenario behaves) but is reported in every result file.  ``MISMATCH`` --
    the record exists and disagrees, which aborts the run.
    """
    path = YSTATE_DIR / f"ystate_{scenario}.json"
    live_sha = spec.components_sha256()
    if not path.exists():
        return {
            "status": "MISSING",
            "path": str(path),
            "live_components_sha256": live_sha,
            "detail": "no committed ystate record for this scenario",
        }
    rec = json.loads(path.read_text())
    # The spec is already built and the harvest already loaded; only the
    # identity needs recomputing, which is a hash rather than a re-measurement.
    fresh = {"harvest": harvest_identity(Path(harvest_path), harvest)}
    diffs = []
    if rec.get("components_sha256") != live_sha:
        diffs.append(
            f"components_sha256 committed={rec.get('components_sha256')} "
            f"live={live_sha}"
        )
    for k in ("content_sha256", "file_sha256"):
        a = (rec.get("harvest") or {}).get(k)
        b = (fresh.get("harvest") or {}).get(k)
        if a != b:
            diffs.append(f"harvest {k} committed={a} live={b}")
    return {
        "status": "MISMATCH" if diffs else "OK",
        "path": str(path.relative_to(YSTATE_DIR.parent.parent.parent)),
        "components_sha256": live_sha,
        "harvest_content_sha256": (fresh.get("harvest") or {}).get("content_sha256"),
        "scales_measured_over_n_design_points": rec.get(
            "scales_measured_over_n_design_points"
        ),
        "detail": "; ".join(diffs) if diffs else "committed record agrees",
    }


def y_index_by_node(spec: YSpec, writes_by_node: dict) -> dict:
    """node -> set of ``y`` component indices that node writes."""
    pos = {k: i for i, k in enumerate(spec.keys)}
    out = {}
    for node, fields in writes_by_node.items():
        idx = set()
        for f in fields:
            ns, _, fld = f.partition(".")
            i = pos.get((ns, fld))
            if i is not None:
                idx.add(i)
        out[node] = idx
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--harvest", required=True)
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--expect-tree", default=None)
    ap.add_argument("--tau", type=float, default=1e-6)
    ap.add_argument("--arms", nargs="*", default=list(A.ARMS))
    ap.add_argument("--hoist", type=int, default=0)
    ap.add_argument("--max-points", type=int, default=0)
    ap.add_argument(
        "--phases",
        nargs="*",
        default=None,
        help="restrict to these harvest phases (fn / grad / grad_reconcile)",
    )
    ap.add_argument("--label", default="")
    args = ap.parse_args()

    import process

    process_file = Path(process.__file__).resolve()
    if args.expect_tree:
        expect = Path(args.expect_tree).resolve()
        actual = process_file.parent.parent
        if actual != expect:
            raise SystemExit(
                f"WRONG TREE: imported {process_file} (tree {actual}), "
                f"expected exactly {expect}. Set PYTHONPATH={expect}."
            )
    if os.environ.get("PROCESS_IDF_PROBE"):
        raise SystemExit(
            "the replay must run with PROCESS_IDF_PROBE unset: an instrumented "
            "tree would wrap the very run() methods the engine calls"
        )

    import pickle

    with open(args.harvest, "rb") as fh:
        harvest = pickle.load(fh)
    assert harvest["format"] == "a18-harvest-1", harvest["format"]

    node_order = list(harvest["node_order"])
    node_module = dict(harvest["node_module"])

    # The category/scale spec is always built from the **whole** harvest, even
    # when only a subset is solved.  A scale measured from six points is not a
    # characteristic magnitude, and a component looks "constant" far too easily
    # in a small sample -- which would silently move components out of the test.
    all_points = harvest["points"]
    points = all_points
    if args.phases:
        points = [p for p in points if p.get("phase") in set(args.phases)]
    if args.max_points:
        points = points[: args.max_points]

    # ---- F4: the node map, and its one assertion ----------------------
    nmap = NodeMap.load()
    observed = set(node_order) | {
        n for n, v in harvest["writes_by_node"].items() if v
    }
    subset_check = nmap.assert_observed_subset(observed)

    from process.main import SingleRun

    sr = SingleRun(args.input, solver="vmcon", update_obsolete=True)
    models, data = sr.models, sr.data

    spec = YSpec.from_harvest(harvest["y_keys"], all_points)

    # The committed record of what every coupling quantity was decided to be
    # (arch_surgery/docs/data/ystate_<scenario>.json).  Re-derived here from
    # the harvest and compared, so that a scale set cannot be silently paired
    # with a harvest it was not measured from -- the scales decide which
    # quantities are excluded from the convergence test, and a wrong exclusion
    # would make every architecture declare a convergence that has not
    # happened, with no symptom.
    ystate_check = _check_ystate(args.scenario, spec, args.harvest, harvest)
    if ystate_check["status"] == "MISMATCH":
        raise SystemExit(
            "ystate MISMATCH for "
            f"{args.scenario}: the committed categorisation and scales do not "
            "match the ones this harvest produces "
            f"({ystate_check['detail']}). Regenerate with gen_ystate.py and "
            "commit, or point at the harvest the record was measured from."
        )
    ynode = y_index_by_node(spec, harvest["writes_by_node"])

    # C10: the DSM's feedback-edge set, resolved to y component indices.  It
    # never decides convergence -- it records the sweep at which it *would*
    # have, so a disagreement with the run-time set is visible as a number
    # rather than as an argument.
    pos = {k: i for i, k in enumerate(spec.keys)}
    cross_fields = nmap.feedback_fields()
    cross_subset = set()
    cross_missing = []
    cross_cat = {}
    for f in cross_fields:
        ns, _, fld = f.partition(".")
        i = pos.get((ns, fld))
        if i is None:
            cross_missing.append(f)
        else:
            cross_subset.add(i)
            cross_cat[f] = spec.category[i]

    hoist = bool(args.hoist)
    ln = A.loop_nodes(node_order, node_module, hoist=hoist)
    hn = A.hoisted_nodes(node_order, node_module, hoist=hoist)
    blocks = A.build_blocks(node_order, node_module, ynode, hoist=hoist)
    all_nodes = A.loop_nodes(node_order, node_module, hoist=False)

    result = {
        "scenario": args.scenario,
        "label": args.label,
        "tau": args.tau,
        "hoist": hoist,
        "arms": list(args.arms),
        "tree": str(process_file.parent.parent),
        "harvest": str(Path(args.harvest).resolve()),
        "n_points": len(points),
        "n_harvest_points": len(all_points),
        "node_map_check": subset_check,
        "node_map_counts": nmap.counts(observed),
        "topology": A.describe(node_order, node_module, hoist=hoist),
        "block_schedule": [
            {"label": lab, "nodes": nodes, "iterate": it, "n_y_subset": len(sub)}
            for lab, nodes, sub, it in blocks
        ],
        "y_census": spec.census(),
        "ystate_record": ystate_check,
        "dsm_cross_check": {
            "fields": cross_fields,
            "resolved_in_y": len(cross_subset),
            "not_in_y": cross_missing,
            "categories": cross_cat,
        },
        "y_scales_summary": _scale_summary(spec),
        "caps": {
            "inner": E.INNER_CAP,
            "outer": E.OUTER_CAP,
            "global_module_sweeps": E.GLOBAL_MODULE_SWEEP_CAP,
            "reference": E.REFERENCE_CAP,
        },
        "points": [],
        "restore_mismatch_total": 0,
        "restore_mismatch_fields": [],
        "errors": [],
    }

    t0 = time.perf_counter()
    for p in points:
        bound = bind_state(data, p["state"])
        row = {
            "call_index": p["call_index"],
            "phase": p.get("phase"),
            "m": p.get("m"),
            "s_global_live": p.get("s_global"),
            "loop_converged_live": p.get("loop_converged"),
            "arms": {},
        }
        for arm in args.arms:
            restore(bound)
            bad = verify_restore(bound)
            if bad:
                result["restore_mismatch_total"] += len(bad)
                result["restore_mismatch_fields"] = sorted(
                    set(result["restore_mismatch_fields"]) | set(bad)
                )[:40]
            sw = E.Sweeper(
                models, data, node_order, p["x"], p["nvars"], m=p.get("m")
            )
            try:
                if arm == "R":
                    out = E.solve_reference(sw, ln)
                elif arm == "A0":
                    out = E.solve_flat(
                        sw, spec, ln, args.tau, floor=1,
                        cross_subset=cross_subset or None,
                    )
                elif arm == "A0f":
                    out = E.solve_flat(sw, spec, ln, args.tau, floor=2)
                elif arm == "A1":
                    out = E.solve_block(sw, spec, blocks, args.tau, floor=1)
                else:
                    raise SystemExit(f"unknown arm {arm!r}")
                if hoist and hn and out["converged"]:
                    # the tail runs once, after the outer fixed point has
                    # converged -- not after each inner solve
                    b = E.Budget(0)
                    sw.run_nodes(hn, b)
                    out["hoist_tail_node_calls"] = b.node_calls
                out["audit"] = E.exit_audit(sw, spec, all_nodes, args.tau)
                out["restore_mismatch"] = len(bad)
            except Exception:
                out = {
                    "valid": False,
                    "converged": False,
                    "error": traceback.format_exc(limit=4),
                }
                result["errors"].append(
                    f"{arm}@{p['call_index']}: {out['error'].splitlines()[-1]}"
                )
            row["arms"][arm] = out
        result["points"].append(row)

    result["wall_s"] = time.perf_counter() - t0
    Path(args.out).write_text(json.dumps(result, indent=2, default=_default))
    print(
        json.dumps(
            {
                "scenario": args.scenario,
                "tau": args.tau,
                "hoist": hoist,
                "n_points": len(points),
        "n_harvest_points": len(all_points),
                "wall_s": result["wall_s"],
                "restore_mismatch_total": result["restore_mismatch_total"],
                "n_errors": len(result["errors"]),
                "y": result["y_census"],
            },
            indent=2,
        )
    )
    return 0


def _scale_summary(spec: YSpec) -> dict:
    s = np.array([spec.scale[i] for i in spec.idx_continuous], dtype=float)
    if not s.size:
        return {}
    return {
        "n": int(s.size),
        "min": float(s.min()),
        "p05": float(np.percentile(s, 5)),
        "median": float(np.median(s)),
        "p95": float(np.percentile(s, 95)),
        "max": float(s.max()),
        "n_below_1e-2": int((s < 1e-2).sum()),
        "n_below_1e-8": int((s < 1e-8).sum()),
    }


def _default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, set):
        return sorted(o)
    return str(o)


if __name__ == "__main__":
    raise SystemExit(main())
