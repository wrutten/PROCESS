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

from fixedpoint import accounting as ACC  # noqa: E402
from fixedpoint import arms as A  # noqa: E402
from fixedpoint import engine as E  # noqa: E402
from fixedpoint import manifest as MAN  # noqa: E402
from fixedpoint import predicate_reads as PR  # noqa: E402
from fixedpoint.gen_ystate import OUT_DIR as YSTATE_DIR  # noqa: E402
from fixedpoint.gen_ystate import harvest_identity  # noqa: E402
from fixedpoint.nodemap import NodeMap  # noqa: E402
from fixedpoint.ystate import (  # noqa: E402
    SCALE_FLOOR,
    SPEC_MODE_A18,
    SPEC_MODES,
    YSpec,
    _same,
)


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


def ystate_path(scenario: str, spec: YSpec):
    """Where this scenario's committed categorisation lives, per spec mode.

    A26's mode gets its own file rather than overwriting A18's, because A18,
    A22 and A23's recorded artifacts have to keep re-deriving.  A run at a
    **non-canonical scale floor** deliberately has no committed record: it is a
    sensitivity probe, its ``ystate_record`` comes back ``MISSING``, and that
    is reported in the result rather than passing silently.
    """
    if spec.mode == SPEC_MODE_A18:
        return YSTATE_DIR / f"ystate_{scenario}.json"
    if float(spec.scale_floor) == float(SCALE_FLOOR):
        return YSTATE_DIR / f"ystate_a26_{scenario}.json"
    return YSTATE_DIR / f"ystate_a26_{scenario}_floor{spec.scale_floor:g}.json"


def _check_ystate(scenario: str, spec: YSpec, harvest_path, harvest) -> dict:
    """Compare the live categorisation against the committed record.

    Three outcomes.  ``OK`` -- the committed record exists and agrees, on both
    the harvest identity and the categorisation hash.  ``MISSING`` -- no record
    is committed yet, which is not fatal (it is how the first run of a new
    scenario behaves) but is reported in every result file.  ``MISMATCH`` --
    the record exists and disagrees, which aborts the run.
    """
    path = ystate_path(scenario, spec)
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
    # **The content hash is fatal; the file hash is reported.**  The two exist
    # precisely because they mean different things (``gen_ystate``'s own
    # docstring): the content hash covers the coupling-key set, the model
    # sequence and every design point's identity and design vector as exact hex
    # floats, and "changes if and only if the harvest is a different
    # measurement"; the file hash covers how ``pickle`` happened to lay bytes
    # out.  Treating both as fatal made a **from-scratch reproduction
    # impossible**: a freshly recorded harvest of the same run aborts the replay
    # on a byte-layout difference the instrument itself documents as
    # meaningless, while its content hash and the categorisation hash both
    # agree.  Found by running the entry point from scratch (A28).  A file-hash
    # difference is now recorded in every result file as a note, so nothing is
    # hidden -- it simply does not abort.
    note = None
    for k in ("content_sha256",):
        a = (rec.get("harvest") or {}).get(k)
        b = (fresh.get("harvest") or {}).get(k)
        if a != b:
            diffs.append(f"harvest {k} committed={a} live={b}")
    fa = (rec.get("harvest") or {}).get("file_sha256")
    fb = (fresh.get("harvest") or {}).get("file_sha256")
    if fa != fb:
        note = (
            f"harvest file_sha256 differs (committed={fa} live={fb}) but its "
            f"content_sha256 and the categorisation hash both agree, so this "
            f"is the same measurement in a different byte layout -- a "
            f"re-recorded harvest.  Reported, not fatal"
        )
    return {
        "status": "MISMATCH" if diffs else "OK",
        "harvest_file_sha256_note": note,
        "path": str(path.relative_to(YSTATE_DIR.parent.parent.parent)),
        "components_sha256": live_sha,
        "harvest_content_sha256": (fresh.get("harvest") or {}).get("content_sha256"),
        "scales_measured_over_n_design_points": rec.get(
            "scales_measured_over_n_design_points"
        ),
        "spec_mode": spec.mode,
        "scale_floor": spec.scale_floor,
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
    ap.add_argument(
        "--inner-tau",
        type=float,
        default=None,
        help="block arm's INNER tolerance; default = --tau, which is what A18 "
             "ran and is the handicap §6.1 names",
    )
    ap.add_argument("--arms", nargs="*", default=list(A.ARMS))
    ap.add_argument("--hoist", type=int, default=0)
    ap.add_argument(
        "--lift", type=int, default=0,
        help="post-lift topology: pulse leaves the MDA (plan §4.1d). Replay "
             "only -- it changes which nodes the loop runs, not the physics",
    )
    ap.add_argument(
        "--spec-mode", default=SPEC_MODE_A18, choices=list(SPEC_MODES),
        help="a18 = A18's categorisation, reproduced exactly; a26 = scale "
             "floor, nothing excluded for never having varied (§6.3(ii))",
    )
    ap.add_argument("--scale-floor", type=float, default=SCALE_FLOOR)
    ap.add_argument(
        "--predicate-guard", type=int, default=1,
        help="1 = route hoisted nodes by the measured predicate read set "
             "(A26); 0 = A18's unguarded behaviour, for reproduction only",
    )
    ap.add_argument(
        "--reps", type=int, default=1,
        help="repeat every arm this many times per design point and record "
             "each repetition's CPU and wall time.  Counts are unaffected and "
             "are asserted identical across repetitions; timings are context",
    )
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

    spec = YSpec.from_harvest(
        harvest["y_keys"], all_points,
        mode=args.spec_mode, scale_floor=args.scale_floor,
    )

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
    lift = bool(args.lift)

    # A26 / plan §4.1d: which slot a hoisted node goes in is decided by the
    # measured predicate read set, not by a static label.  The read set is
    # exact on the objective side (this deck's own figure of merit) and a
    # superset on the constraint side; over-reporting routes a node to the
    # pre-predicate slot, which is never wrong.
    i_fom = int(data.numerics.i_figure_merit)
    tree_root = Path(process_file).resolve().parents[1]
    pred = PR.predicate_read_set(tree_root, i_fom)
    routing = (
        A.Routing(pred["fields"], harvest["writes_by_node"])
        if args.predicate_guard else A.UNGUARDED
    )

    ln, pre_tail, post_tail = A.hoist_split(
        node_order, node_module, hoist=hoist, routing=routing, lift=lift
    )
    hn = pre_tail + post_tail
    blocks = A.build_blocks(node_order, node_module, ynode, hoist=hoist,
                            routing=routing, lift=lift)
    # The audit sweep is the **full** model set, identical for every arm at
    # every setting, so accuracy is compared on one map.
    all_nodes = A.loop_nodes(node_order, node_module, hoist=False,
                             routing=routing, lift=False)

    result = {
        "scenario": args.scenario,
        "label": args.label,
        "tau": args.tau,
        "inner_tau": args.tau if args.inner_tau is None else args.inner_tau,
        "inner_tau_explicit": args.inner_tau is not None,
        "hoist": hoist,
        "lift": lift,
        "spec_mode": spec.mode,
        "scale_floor": spec.scale_floor,
        "predicate_guard": bool(args.predicate_guard),
        "i_figure_merit": i_fom,
        "predicate_read_set": {
            k: v for k, v in pred.items() if k != "fields"
        },
        "predicate_read_fields_sha_n": len(pred["fields"]),
        "accounting": ACC.__doc__.split("\n")[0],
        "reps": args.reps,
        "arms": list(args.arms),
        "tree": str(process_file.parent.parent),
        "harvest": str(Path(args.harvest).resolve()),
        "n_points": len(points),
        "n_harvest_points": len(all_points),
        "node_map_check": subset_check,
        "node_map_counts": nmap.counts(observed),
        "topology": A.describe(node_order, node_module, hoist=hoist,
                               routing=routing, lift=lift),
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
        "arm_descriptors": {},
        "manifest_check": None,
        "timing": {},
        "count_reproducibility": {"compared": 0, "identical": 0, "mismatches": []},
        "restore_mismatch_total": 0,
        "restore_mismatch_fields": [],
        "errors": [],
    }

    # ---- arm descriptors and the comparison manifests -------------------
    # §6.3(iii): every arm-versus-arm comparison declares what it varies, and
    # is refused if it varies anything else.  The descriptors are built from
    # the objects the arms are actually run with, not from the CLI arguments,
    # so a mismatch between what was asked for and what was built shows up
    # here rather than in a table three tasks later.
    inner_tau_eff = args.tau if args.inner_tau is None else args.inner_tau
    spec_sha = spec.components_sha256()

    def _desc(name, predicate, sequence, schedule, floor, inner_tau):
        return MAN.arm_descriptor(
            name=name, predicate=predicate, node_sequence=sequence,
            block_schedule=schedule, floor=floor, tau=args.tau,
            inner_tau=inner_tau, hoist=hoist, lift=lift,
            pre_predicate_tail=pre_tail, post_predicate_tail=post_tail,
            loop_nodes=ln, spec_mode=spec.mode, scale_floor=spec.scale_floor,
            spec_sha256=spec_sha, inner_cap=E.INNER_CAP,
            outer_cap=E.OUTER_CAP, global_cap=E.GLOBAL_MODULE_SWEEP_CAP,
        )

    block_sequence = [n for _l, ns_, _s, _i in blocks for n in ns_]
    desc = {}
    if "R" in args.arms:
        desc["R"] = _desc("R", "objf/conf allclose(rtol=1e-6)", ln, None, 2, None)
    if "A0" in args.arms:
        desc["A0"] = _desc("A0", "scaled y residual", ln, None, 1, None)
    if "A0f" in args.arms:
        desc["A0f"] = _desc("A0f", "scaled y residual", ln, None, 2, None)
    if "A1" in args.arms:
        desc["A1"] = _desc("A1", "scaled y residual", block_sequence, blocks, 1,
                           inner_tau_eff)
    result["arm_descriptors"] = desc

    MANIFESTS = {
        "R -> A0f": MAN.Manifest(
            "R -> A0f", varies=["stopping_test"],
            rationale=(
                "the predicate alone: same nodes, same order, same two-sweep "
                "floor.  This is the isolator A18 built A0f for"
            ),
        ),
        "A0f -> A0": MAN.Manifest(
            "A0f -> A0", varies=["sweep_floor"],
            rationale=(
                "the two-sweep floor alone.  It and the predicate act in "
                "opposite directions, so R -> A0 can only report their sum"
            ),
        ),
        "R -> A0": MAN.Manifest(
            "R -> A0", varies=["stopping_test", "sweep_floor"],
            rationale=(
                "their sum, and only their sum.  The two act in opposite "
                "directions, so this pair can never separate them; it is "
                "reported alongside R -> A0f and A0f -> A0, never instead"
            ),
        ),
        "R -> A1": MAN.Manifest(
            "R -> A1", varies=["stopping_test", "sweep_floor",
                               "block_grouping", "inner_tau"],
            rationale=(
                "everything at once -- the user-facing figure, never the "
                "partition's benefit.  Quoting it as the architecture's cost "
                "would repeat the units error trap T11 records"
            ),
        ),
        "A0f -> A1": MAN.Manifest(
            "A0f -> A1", varies=["sweep_floor", "block_grouping", "inner_tau"],
            rationale=(
                "the grouping against the floored flat arm.  Reported for "
                "completeness; A0 -> A1 is the comparison the study quotes"
            ),
        ),
        "A0 -> A1": MAN.Manifest(
            "A0 -> A1", varies=["block_grouping", "inner_tau"],
            rationale=(
                "the module grouping, and the inner tolerance the grouping "
                "introduces -- the block arm has an inner solve and the flat "
                "arm has none, so an inner tolerance exists on one side only. "
                "The node-order transposition that comes with the grouping is "
                "licensed by block_grouping and controlled separately in "
                "§4.4.4; nothing else may differ"
            ),
        ),
    }
    # A comparison whose arms were not both run is skipped and named, never
    # silently absent: an empty check set reports EMPTY, not PASS.
    result["manifest_check"] = MAN.check_all(MANIFESTS, desc)

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
            # Repetitions exist for the **timing**, and for one gate: the
            # counts must be identical across them.  A count that moves between
            # repetitions of a deterministic replay is a defect in the
            # instrument, and it would otherwise hide inside a median.
            reps_out = []
            for rep in range(max(1, args.reps)):
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
                t_w0, t_c0 = time.perf_counter(), time.process_time()
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
                        out = E.solve_block(
                            sw, spec, blocks, args.tau,
                            inner_tau=args.inner_tau, floor=1,
                        )
                    else:
                        raise SystemExit(f"unknown arm {arm!r}")
                    # The two tails run once each, after the fixed point:
                    # pre-predicate first (its output is read by objf/conf),
                    # then post-predicate.  Counted together as tail work --
                    # see fixedpoint/accounting.py, which is the one place the
                    # accounting is defined.
                    if hoist and hn and out["converged"]:
                        b = E.Budget(0)
                        if pre_tail:
                            sw.run_nodes(pre_tail, b)
                        out["pre_predicate_tail_node_calls"] = b.node_calls
                        if post_tail:
                            sw.run_nodes(post_tail, b)
                        out["hoist_tail_node_calls"] = b.node_calls
                    out["audit"] = E.exit_audit(sw, spec, all_nodes, args.tau)
                    out["restore_mismatch"] = len(bad)
                except Exception:
                    out = {
                        "valid": False,
                        "converged": False,
                        "error": traceback.format_exc(limit=4),
                    }
                    if rep == 0:
                        result["errors"].append(
                            f"{arm}@{p['call_index']}: "
                            f"{out['error'].splitlines()[-1]}"
                        )
                out["rep"] = rep
                out["wall_s"] = time.perf_counter() - t_w0
                out["cpu_s"] = time.process_time() - t_c0
                reps_out.append(out)

            first = reps_out[0]
            if len(reps_out) > 1:
                # The gate: every repetition must produce the same counts.
                key = ("sweeps", "node_calls", "module_sweeps", "converged",
                       "cap_hit")
                sig = [tuple(r.get(k) for k in key) for r in reps_out]
                result["count_reproducibility"]["compared"] += len(reps_out) - 1
                if all(x == sig[0] for x in sig[1:]):
                    result["count_reproducibility"]["identical"] += (
                        len(reps_out) - 1
                    )
                elif len(result["count_reproducibility"]["mismatches"]) < 20:
                    result["count_reproducibility"]["mismatches"].append(
                        {"call_index": p["call_index"], "arm": arm,
                         "signatures": [list(x) for x in sig]}
                    )
                first["reps_wall_s"] = [r["wall_s"] for r in reps_out]
                first["reps_cpu_s"] = [r["cpu_s"] for r in reps_out]
            row["arms"][arm] = first
        result["points"].append(row)

    result["wall_s"] = time.perf_counter() - t0
    result["timing"] = _timing_rollup(result, args)
    result["accounting"] = ACC.accounting_record(
        [r for r in result["points"]
         if all(r["arms"][a].get("converged") for a in args.arms)],
        list(args.arms),
    )
    cr = result["count_reproducibility"]
    cr["status"] = (
        "N/A -- one repetition" if cr["compared"] == 0
        else ("PASS" if cr["identical"] == cr["compared"] else "FAIL")
    )
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


def _machine_context() -> dict:
    """What the machine was doing, recorded with every timing.

    I-10: identical work has varied by up to 35 % in CPU-seconds on this
    machine and **the cause is not known** --- not contention, on the evidence.
    So a timing here carries the load average, the run's position in the
    sequence (I-10's own recorded confound), and the repetition count, and it
    is reported as a median with an interval.  None of it makes a timing
    evidence; it makes a timing legible.
    """
    out: dict = {}
    try:
        out["loadavg_1_5_15"] = list(os.getloadavg())
    except OSError:
        out["loadavg_1_5_15"] = None
    try:
        import resource

        out["peak_rss_kb"] = resource.getrusage(
            resource.RUSAGE_SELF
        ).ru_maxrss
    except Exception:
        out["peak_rss_kb"] = None
    out["n_cpus"] = os.cpu_count()
    out["sequence_position_env"] = os.environ.get(
        "PROCESS_ARCH_SEQUENCE_POSITION"
    )
    return out


def _interval(vals):
    """Median and a stated interval, never a mean and never a bare number."""
    v = sorted(float(x) for x in vals if x is not None)
    if not v:
        return None
    n = len(v)

    def q(f):
        if n == 1:
            return v[0]
        i = f * (n - 1)
        lo, hi = int(i), min(int(i) + 1, n - 1)
        return v[lo] + (v[hi] - v[lo]) * (i - lo)

    med = q(0.5)
    return {
        "n": n,
        "median": med,
        "p10": q(0.10),
        "p90": q(0.90),
        "min": v[0],
        "max": v[-1],
        "spread_p10_p90_pct": (
            100.0 * (q(0.90) - q(0.10)) / med if med else None
        ),
        "spread_min_max_pct": 100.0 * (v[-1] - v[0]) / med if med else None,
    }


def _timing_rollup(result: dict, args) -> dict:
    """Per-arm CPU and wall time, as a median and an interval.  Context only.

    Two things this deliberately does **not** do.  It does not report a mean,
    because a mean of a distribution whose spread is unexplained invites being
    quoted as a value.  And it does not compare arms: the ratio of two of these
    numbers is exactly the quantity I-10 showed moving 6.4 % -> 4.4 % on
    identical code, and this study's acceptance quantities are counts and
    bit-comparisons.
    """
    per_arm = {}
    for a in result["arms"]:
        wall, cpu = [], []
        for row in result["points"]:
            r = row["arms"].get(a) or {}
            wall += r.get("reps_wall_s") or ([r["wall_s"]] if "wall_s" in r else [])
            cpu += r.get("reps_cpu_s") or ([r["cpu_s"]] if "cpu_s" in r else [])
        per_arm[a] = {
            "wall_s_per_design_point_solve": _interval(wall),
            "cpu_s_per_design_point_solve": _interval(cpu),
        }
    return {
        "status": "CONTEXT ONLY -- never evidence (CLAUDE.md working rules)",
        "reps_per_design_point": args.reps,
        "machine": _machine_context(),
        "caveat": (
            "I-10 is OPEN: identical work has varied by up to 35 % in "
            "CPU-seconds on this machine and the cause is not known.  Read "
            "the interval, not the median; where the interval is wider than "
            "the effect, the timing resolves nothing and says so."
        ),
        "per_arm": per_arm,
    }


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
