#!/usr/bin/env python
"""A31 (drift-diagnostic): name the components and mechanism behind the
recurring above-tau cross-pass movement on ``st_regression`` (DSM register
V14; revision-list item R1a).

The question, exactly
---------------------
Under A28's perturbed multi-start campaign, the block arm ``A1'`` on
``st_regression`` needed a 3rd-7th outer pass on 2 802 of 54 480 MDA calls
(5.14 %, all 25 starts; heavy tail at start010 with 858 and start005 with
621) -- the joint test caught some coupling-state component still moving by
more than tau = 1e-6 across outer pass 2 of an already-converged block
schedule.  Which component(s), and by what mechanism?  Two hypotheses:

(A) a **live cross-block feedback edge** that static analysis cannot see
    (the per-deck static export's full pairwise census found exactly one
    cross-block loop-carried pathway, FirstWall -> Build, and proved it
    frozen -- so A requires an edge invisible to the export);
(B) a **non-idempotent model**: some model returns different output at
    identical inputs because it reads its own previous execution's state
    (stale read across sweeps, warm-started internal solver, accumulator).
    The dependency instrument declares 498 variables written-and-read by
    one and the same model with same-sweep-vs-last-sweep timing unmeasured.

The instrument
--------------
``PROCESS_ARCH_PASS_TRACE=<path>`` (new, A31) makes the driver append every
joint-test residual evaluation to a JSONL file: per ``call_models`` index,
per outer-pass index, the residual max/argmax with before/after hex floats,
and from pass 2 on every component at or above tau with the same detail.
Unset, every hook is a no-op -- **gated** (protocol 12) by the neutrality
stage below, never asserted.  Driver files only: ``process/core/caller.py``
and ``process/core/solver/module_solve.py``; nothing under
``process/models/`` is touched.

Stages (protocol 15: every published number comes from executing this
committed script; failure paths are reachable from the same entry point)
------------------------------------------------------------------------
``neutrality``
    One **untraced** ``st_regression`` ``A1'`` run at start000, compared
    against the main checkout's recorded A28 metrics on three exact fields:
    ``node_calls_solve_phase``, ``outer_pass_hist``, and ``norm_objf`` as a
    hex float.  The gate's teeth are shown: a deliberate one-component
    perturbation of the comparator's own input must trip it, per field.
``trace``
    Traced ``A1'`` runs at start010 and start005 -- the two heaviest tails
    -- with the exact A28 perturbation machinery (delta = 0.10, hashed
    per-ixc factors, seed = start index) reproduced by importing
    ``run_a28.env_for`` / mirroring its ``run_one`` invocation.
``a0p``
    Optional: one traced ``A0'`` (flat, predicate-matched control) run at
    start010, for the cross-arm comparison of the same movers.  In that arm
    the single-block guard makes the FLAT block's inner test the joint
    test, and that is what the trace records there.
``analyze``
    Every pass >= 2 exceedance, aggregated per component and joined against
    (i) the committed run-time write census (``node_writesets.json``,
    per-scenario), (ii) the committed per-module write subsets
    (``writeset_st_regression.json`` -- block attribution in y-space),
    (iii) the frozen per-deck static dependency export (readers/writers at
    variable level), and (iv) the run's own recorded block schedule.  Also
    reconciles the traced runs' pass histograms against A28's recorded
    ones -- a mismatch is a finding, not a calibration to fix.

Isolation: every PROCESS run is a fresh subprocess in its own working
directory, ``PYTHONPATH`` pinned to this worktree and the exact tree
asserted inside the subprocess (traps T6/T10).  ``--jobs`` does not exist:
this task runs beside A29's heavy slot and everything here is serial.

No conclusion rests on a timing; every quantity this script emits is a
count, a name, or a bit-exact float.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
TREE = HERE.parent.parent
DATA = TREE / "arch_surgery" / "docs" / "data"
RUNS = HERE / "runs" / "a31"

sys.path.insert(0, str(HERE))
from run_a28 import TAU, deck_for, env_for  # noqa: E402

#: The main checkout: comparator inputs and the frozen static export live
#: there and are read, never written.
MAIN = Path("/home/wrutten/projects/PROCESS_surgery")
A28_REF_DIR = MAIN / "arch_surgery/idf_probe/runs/a28/h5/st_regression/A1p"
DSM_EXPORT = (
    MAIN
    / "arch_surgery/idf_probe/runs/dsm_exports/st_regression"
    / "process_dependencies.json"
)

SCENARIO = "st_regression"
#: D15's calibrated perturbation size, exactly as the A28 campaign ran it.
DELTA = 0.10

#: The A1' block order (module_solve.BLOCK_ORDER) -- used to decide whether
#: a reader runs before its writer within one outer pass, which is what
#: makes an edge loop-carried under the block schedule.
BLOCK_ORDER = ("M1", "M2", "PULSE", "M3", "FF")

#: Driver node for each supermodel execution-order index of the static
#: export (deck-specific: st_regression, i_tf_sup = 1, turn type 2 -> the
#: CROCO superconducting TF chain).  Orders 3-26 are Physics and its
#: physics-side submodel chains; 27-32 the TF-coil chain and the function
#: collections it calls (superconductors.py, materials.py, tfcoil/base.py);
#: 33-35 PFCoil (+ pfcoil function collection, CSCoil); 38-39 FirstWall and
#: the IVC function collection.  Verified against each node's file_path
#: when the map is built -- a mismatch raises rather than mislabels.
SUPERMODEL_ORDER_TO_NODE = (
    (1, 1, "plasma_geom"),
    (2, 2, "build"),
    (3, 26, "physics"),
    (27, 32, "croco_sctfcoil"),
    (33, 35, "pfcoil"),
    (36, 36, "pulse"),
    (37, 37, "divertor"),
    (38, 39, "fw"),
    (40, 40, "shield"),
    (41, 41, "vacuum_vessel"),
    (42, 42, "ccfe_hcpb"),
    (43, 43, "cryostat"),
    (44, 44, "structure"),
    (45, 45, "power"),
    (46, 46, "vacuum"),
    (47, 47, "buildings"),
    (48, 48, "availability"),
    (49, 49, "water_use"),
    (50, 50, "costs"),
)

#: What file a supermodel in each range is allowed to live in -- the sanity
#: check on the order table above (trap T2's lesson: check the extraction
#: against the source, never trust a mapping by eye).
_ORDER_FILE_HINTS = {
    "plasma_geom": ("plasma_geometry.py",),
    "build": ("build.py",),
    "physics": ("physics/",),
    "croco_sctfcoil": (
        "tfcoil/", "superconductors.py", "engineering/materials.py",
    ),
    "pfcoil": ("pfcoil.py",),
    "pulse": ("pulse.py",),
    "divertor": ("divertor.py",),
    "fw": ("fw.py", "engineering/ivc_functions.py"),
    "shield": ("shield.py",),
    # VacuumVessel (order 41) and Vacuum (order 46) both live in vacuum.py
    # at this pin; the order ranges keep them apart.
    "vacuum_vessel": ("vacuum.py",),
    "ccfe_hcpb": ("hcpb.py",),
    "cryostat": ("cryostat.py",),
    "structure": ("structure.py",),
    "power": ("power.py",),
    "vacuum": ("vacuum.py",),
    "buildings": ("buildings.py",),
    "availability": ("availability.py",),
    "water_use": ("water_use.py",),
    "costs": ("costs",),
}


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


# --------------------------------------------------------------------------
# running one PROCESS start (mirrors run_a28.run_one, plus the trace switch)
# --------------------------------------------------------------------------


def run_one_a31(
    arm: str,
    outdir: Path,
    *,
    seed: int,
    delta: float | None,
    trace: bool,
    timeout: int = 5400,
) -> dict:
    """One isolated run, the A28 way, with the pass trace opt-in.

    The invocation mirrors ``run_a28.run_one`` for the campaign
    configuration exactly -- same deck resolution, same perturbation flags,
    same exit audit and entry census, no per-node census (a campaign-count
    instrument only) -- and the environment is ``run_a28.env_for``'s with
    precisely one addition when ``trace`` is set.  The trace variable is
    popped first either way, so an inherited value can never leak into the
    neutrality run.
    """
    if outdir.exists():
        shutil.rmtree(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(HERE / "run_one.py"),
        "--scenario", SCENARIO,
        "--mode", "control",
        "--outdir", str(outdir),
        "--expect-tree", str(TREE),
        "--input", str(deck_for(SCENARIO, arm, RUNS / "_decks")),
        "--exit-audit", str(DATA / f"ystate_{SCENARIO}.json"),
        "--entry-census",
    ]
    if delta is not None:
        cmd += ["--perturb-delta", repr(delta), "--perturb-seed", str(seed)]
    env = env_for(SCENARIO, arm, RUNS, TAU, None)
    env.pop("PROCESS_ARCH_PASS_TRACE", None)
    env.pop("PROCESS_ARCH_PASS_TRACE_FULL_FROM", None)
    if trace:
        env["PROCESS_ARCH_PASS_TRACE"] = str(outdir / "pass_trace.jsonl")
    t0 = time.perf_counter()
    try:
        proc = subprocess.run(
            cmd, env=env, capture_output=True, text=True, cwd=str(outdir),
            timeout=timeout,
        )
        rc, out, err = proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        rc, out, err = 124, exc.stdout or "", (exc.stderr or "") + "\nTIMEOUT"
    (outdir / "stdout.log").write_text(out)
    (outdir / "stderr.log").write_text(err)
    mpath = outdir / "metrics.json"
    if not mpath.exists():
        mpath.write_text(json.dumps({
            "scenario": SCENARIO, "mode": "control",
            "status": "timeout" if rc == 124 else "no_metrics",
            "perturb_delta": delta, "perturb_seed": seed, "returncode": rc,
        }, indent=2))
    rec = json.loads(mpath.read_text())
    rec["a31_arm"] = arm
    rec["a31_traced"] = trace
    rec["a31_tau"] = TAU
    rec["a31_delta"] = delta
    rec["a31_seed"] = seed
    mpath.write_text(json.dumps(rec, indent=2))
    wall = time.perf_counter() - t0
    print(f"  {arm} seed={seed} trace={trace} rc={rc} {wall:6.1f}s "
          f"(wall clock is progress information, not a measurement)",
          flush=True)
    return {"arm": arm, "seed": seed, "trace": trace, "rc": rc,
            "outdir": str(outdir), "wall_s": wall}


# --------------------------------------------------------------------------
# stage: neutrality (the protocol-12 gate, teeth first)
# --------------------------------------------------------------------------

#: The three exact fields the gate compares.  Counts and a bit-comparison
#: -- never a timing (trap T5).
GATE_FIELDS = ("node_calls_solve_phase", "outer_pass_hist", "norm_objf_hex")


def gate_extract(metrics: dict) -> dict:
    return {
        "node_calls_solve_phase": metrics.get("node_calls_solve_phase"),
        "outer_pass_hist": dict(
            metrics.get("module_solve_totals", {}).get("outer_pass_hist", {})
        ),
        "norm_objf_hex": metrics.get("exact", {}).get("norm_objf"),
    }


def gate_compare(ref: dict, got: dict) -> dict:
    """Field-by-field exact comparison; the denominator is len(GATE_FIELDS)."""
    per_field = {}
    for f in GATE_FIELDS:
        per_field[f] = {
            "ref": ref[f],
            "got": got[f],
            "match": ref[f] == got[f],
        }
    return {
        "fields_compared": len(GATE_FIELDS),
        "fields_matching": sum(1 for v in per_field.values() if v["match"]),
        "pass": all(v["match"] for v in per_field.values()),
        "per_field": per_field,
    }


def gate_teeth(ref: dict, got: dict) -> dict:
    """Perturb the comparator's own input, one field at a time; each must trip.

    Protocol 12: a gate must be shown capable of failing before its zeros
    are accepted.  The perturbations are the smallest that should register:
    +1 on a count, +1 on one histogram bucket, one ULP on the float.
    """
    trials = {}
    p = json.loads(json.dumps(ref))
    p["node_calls_solve_phase"] = (p["node_calls_solve_phase"] or 0) + 1
    trials["node_calls_solve_phase+1"] = not gate_compare(p, got)["pass"]

    p = json.loads(json.dumps(ref))
    hist = p["outer_pass_hist"]
    k = sorted(hist)[0]
    hist[k] += 1
    trials[f"outer_pass_hist[{k}]+1"] = not gate_compare(p, got)["pass"]

    p = json.loads(json.dumps(ref))
    v = float.fromhex(p["norm_objf_hex"])
    p["norm_objf_hex"] = math.nextafter(v, math.inf).hex()
    trials["norm_objf+1ulp"] = not gate_compare(p, got)["pass"]

    return {
        "n_perturbations": len(trials),
        "n_tripped": sum(1 for v in trials.values() if v),
        "all_tripped": all(trials.values()),
        "per_perturbation": trials,
    }


def stage_neutrality() -> int:
    """The switch-neutrality gate: trace env unset must reproduce A28 exactly."""
    outdir = RUNS / "neutrality" / "A1p_start000"
    r = run_one_a31("A1p", outdir, seed=0, delta=DELTA, trace=False)
    ref_path = A28_REF_DIR / "start000" / "metrics.json"
    ref = gate_extract(json.loads(ref_path.read_text()))
    got = gate_extract(json.loads((outdir / "metrics.json").read_text()))
    verdict = gate_compare(ref, got)
    teeth = gate_teeth(ref, got)
    record = {
        "gate": "A31 switch-neutrality (protocol 12)",
        "reference": {"path": str(ref_path), "sha256": sha256_of(ref_path)},
        "run": {"outdir": str(outdir), "rc": r["rc"]},
        "comparison": verdict,
        "teeth": teeth,
        "verdict": (
            "PASS" if (verdict["pass"] and teeth["all_tripped"] and r["rc"] == 0)
            else "FAIL"
        ),
    }
    (RUNS / "neutrality" / "gate.json").write_text(json.dumps(record, indent=2))
    print(json.dumps(record, indent=2))
    return 0 if record["verdict"] == "PASS" else 1


# --------------------------------------------------------------------------
# stage: trace / a0p
# --------------------------------------------------------------------------


def stage_trace(starts=(10, 5)) -> int:
    rc = 0
    for k in starts:
        r = run_one_a31("A1p", RUNS / "trace" / f"A1p_start{k:03d}",
                        seed=k, delta=DELTA, trace=True)
        rc = rc or r["rc"]
    return rc


def stage_retrace(starts=(10,)) -> int:
    """Re-run with the upgraded trace (moved-constant before/after detail).

    The first traced runs established the mover class — the joint test is
    tripped by **moved constants**, which the first trace format recorded by
    name only.  The exact-equality assertion has no tolerance, so *how far*
    the constant moves per pass is the mechanism quantity; this stage
    repeats start010 with the upgraded instrument into ``trace2/``, leaving
    the first runs in place as the count record.
    """
    rc = 0
    for k in starts:
        r = run_one_a31("A1p", RUNS / "trace2" / f"A1p_start{k:03d}",
                        seed=k, delta=DELTA, trace=True)
        rc = rc or r["rc"]
    return rc


def stage_a0p(starts=(10,)) -> int:
    rc = 0
    for k in starts:
        r = run_one_a31("A0p", RUNS / "trace2" / f"A0p_start{k:03d}",
                        seed=k, delta=DELTA, trace=True)
        rc = rc or r["rc"]
    return rc


# --------------------------------------------------------------------------
# stage: analyze
# --------------------------------------------------------------------------


def _load_static_maps() -> dict:
    """Writer/reader maps per variable from the frozen per-deck export.

    Model nodes are mapped to driver nodes through their supermodel's
    execution order (``SUPERMODEL_ORDER_TO_NODE``), each assignment checked
    against the supermodel's source file.  Workflow drivers (COOR_SingleRun,
    MDA pseudo-nodes, the embedded sub-solvers) are kept, labelled
    ``driver:<name>`` -- an input-loader write must stay distinguishable
    from a model write.
    """
    d = json.loads(DSM_EXPORT.read_text())
    nodes, edges = d["nodes"], d["edges"]

    # supermodel uuid -> driver node
    order_node: dict[str, str] = {}
    for uuid, v in nodes.items():
        ai = v.get("annotations", {}).get("PROCESS_ast_info", {})
        if ai.get("level") != "supermodel":
            continue
        o = ai.get("supermodel_execution_order")
        if o is None:
            # the Constraints collection: the predicate layer, not a model
            order_node[uuid] = "objective_constraints"
            continue
        for lo, hi, name in SUPERMODEL_ORDER_TO_NODE:
            if lo <= o <= hi:
                fp = ai.get("file_path", "") or ""
                hints = _ORDER_FILE_HINTS.get(name, ())
                if fp and hints and not any(h in fp for h in hints):
                    raise RuntimeError(
                        f"supermodel order {o} ({fp}) does not look like "
                        f"driver node {name!r}; the order map is wrong for "
                        f"this export and must not be guessed"
                    )
                order_node[uuid] = name
                break
        else:
            raise RuntimeError(f"supermodel order {o} not covered by the map")

    # every model node -> driver node, via the parent chain
    def to_driver(uuid: str) -> str:
        v = nodes[uuid]
        if v.get("kind") == "workflow_driver":
            return f"driver:{v.get('name')}"
        seen = set()
        u = uuid
        while u is not None and u not in seen:
            seen.add(u)
            if u in order_node:
                return order_node[u]
            u = nodes[u].get("parent")
        return f"unmapped:{nodes[uuid].get('name')}"

    writers: dict[str, set] = defaultdict(set)
    readers: dict[str, set] = defaultdict(set)
    for v in edges.values():
        if v["kind"] != "data_interface":
            continue
        at = v["annotations"].get("PROCESS_ast_info", {}).get("access_type")
        if at not in ("read", "write", "read_write"):
            continue
        s, t = nodes[v["source"]], nodes[v["target"]]
        if at in ("write", "read_write") and t.get("kind") == "variable":
            writers[t["name"]].add(to_driver(v["source"]))
        if at in ("read", "read_write") and s.get("kind") == "variable":
            readers[s["name"]].add(to_driver(v["target"]))
    return {
        "writers": {k: sorted(v) for k, v in writers.items()},
        "readers": {k: sorted(v) for k, v in readers.items()},
        "export_sha256": sha256_of(DSM_EXPORT),
        "export_path": str(DSM_EXPORT),
    }


def _component_module(subsets: dict) -> dict:
    """y-component key -> block label(s), from the committed write subsets."""
    mod_of: dict[str, list] = defaultdict(list)
    for mod, keys in subsets.items():
        for k in keys:
            mod_of[k].append(mod)
    return {k: sorted(v) for k, v in mod_of.items()}


def _iter_trace(path: Path):
    with path.open() as fh:
        for line in fh:
            yield json.loads(line)


def _node_block(schedule: list, tails: list) -> dict:
    """driver node -> block label, from a run's own recorded schedule."""
    nb = {}
    for label, node_list, _it in schedule:
        for n in node_list:
            nb[n] = label
    for n in (tails or [[], []])[1]:
        nb[n] = "FF-tail"
    for n in (tails or [[], []])[0]:
        nb[n] = "FF-tail-pre"
    return nb


def _discover_runs(with_a0p: bool) -> list:
    """Every traced run present, as ``(generation, arm, seed, dir)``.

    ``trace/`` holds the first-format runs (moved constants by name only);
    ``trace2/`` the upgraded-format ones (before/after hex for every
    equality-tested component).  Both are analysed; the summary keys carry
    the generation so a figure can be traced to the run that produced it.
    """
    out = []
    for gen in ("trace", "trace2"):
        d = RUNS / gen
        if not d.exists():
            continue
        for p in sorted(d.iterdir()):
            if not (p / "metrics.json").exists():
                continue
            arm, _, s = p.name.partition("_start")
            if arm == "A0p" and not with_a0p:
                continue
            out.append((gen, arm, int(s), p))
    return out


def stage_analyze(with_a0p: bool) -> int:
    static = _load_static_maps()
    ws = json.loads((DATA / f"writeset_{SCENARIO}.json").read_text())
    comp_module = _component_module(ws["subsets"])
    nw = json.loads((DATA / "node_writesets.json").read_text())
    per_scn = nw["per_scenario"][SCENARIO]["writes_by_node"]
    runtime_writers: dict[str, list] = defaultdict(list)
    for node, keys in per_scn.items():
        for k in keys:
            runtime_writers[k].append(node)

    runs = _discover_runs(with_a0p)
    if not runs:
        print("no traced runs found -- run the trace stage first")
        return 1

    summary: dict = {
        "tau": TAU,
        "static_export": {
            "path": static["export_path"], "sha256": static["export_sha256"],
        },
        "runs": {},
        "components": {},
    }
    block_index = {b: i for i, b in enumerate(BLOCK_ORDER)}

    agg: dict[str, dict] = {}
    #: node -> block under the A1' schedule, taken from the first A1' run's
    #: own recorded schedule.  The A0' run's schedule is one FLAT block and
    #: must not overwrite the attribution the verdict is stated in.
    a1p_node_block: dict = {}
    for gen, arm, k, outdir in runs:
        label = f"{gen}/{arm}_start{k:03d}"
        mpath = outdir / "metrics.json"
        tpath = outdir / "pass_trace.jsonl"
        if not tpath.exists():
            print(f"  {label}: metrics but no pass_trace.jsonl -- skipped")
            continue
        m = json.loads(mpath.read_text())
        schedule = m.get("arch_block_schedule") or []
        node_block = _node_block(schedule, m.get("arch_hoist_tails_resolved"))
        if arm == "A1p" and not a1p_node_block:
            a1p_node_block = node_block

        # per-run roll-up of the trace
        n_records = 0
        n_exceed_records = 0
        n_const_only_records = 0
        exceed_calls: set = set()
        per_pass_movers: list = []
        for rec in _iter_trace(tpath):
            if rec.get("kind") == "header":
                summary["runs"].setdefault(label, {})["trace_header"] = rec
                continue
            n_records += 1
            call = rec["call"]
            if rec["pass"] < 2:
                continue
            movers = rec.get("above") or []
            n_disc = rec.get("n_discrete_mismatch", 0)
            n_const = rec.get("n_constant_moved", 0)
            if not movers and not n_disc and not n_const:
                continue
            n_exceed_records += 1
            if not movers and not n_disc:
                n_const_only_records += 1
            exceed_calls.add(call)
            mover_keys = [mv["key"] for mv in movers]
            mover_blocks = sorted({
                b for key in mover_keys for b in comp_module.get(key, ["?"])
            })
            per_pass_movers.append({
                "call": call, "pass": rec["pass"],
                "n_above": rec.get("n_above"),
                "max": rec.get("max"),
                "argmax": (rec.get("argmax") or {}).get("key"),
                "argmax_detail": rec.get("argmax"),
                "movers": mover_keys, "mover_blocks": mover_blocks,
                "discrete_mismatch": rec.get("discrete_mismatch", []),
                "moved_constant": rec.get("moved_constant", []),
                "moved_constant_detail": rec.get("moved_constant_detail"),
            })

            def _tally(key, kind, scaled=None, detail=None):
                a = agg.setdefault(key, {
                    "kind": kind, "n_exceedances": 0, "n_calls": set(),
                    "runs": set(), "max_scaled": 0.0,
                    "by_pass": defaultdict(int), "scaled_by_call_pass": {},
                    "max_abs_delta": 0.0, "max_rel_delta": 0.0,
                })
                a["n_exceedances"] += 1
                a["n_calls"].add((arm, k, call))
                a["runs"].add(label)
                a["by_pass"][str(rec["pass"])] += 1
                if scaled is not None:
                    a["max_scaled"] = max(a["max_scaled"], scaled)
                    a["scaled_by_call_pass"][
                        f"{arm}|{k}|{call}|{rec['pass']}"] = scaled
                if detail and "before" in detail and "after" in detail:
                    d = abs(detail["after"] - detail["before"])
                    a["max_abs_delta"] = max(a["max_abs_delta"], d)
                    ref = max(abs(detail["before"]), abs(detail["after"]))
                    if ref > 0:
                        a["max_rel_delta"] = max(a["max_rel_delta"], d / ref)

            for mv in movers:
                _tally(mv["key"], "continuous_above_tau",
                       scaled=mv.get("scaled"), detail=mv)
            const_detail = {d["key"]: d
                            for d in rec.get("moved_constant_detail") or []}
            for nm in rec.get("moved_constant", []):
                _tally(nm, "moved_constant", detail=const_detail.get(nm))
            disc_detail = {d["key"]: d
                           for d in rec.get("discrete_mismatch_detail") or []}
            for nm in rec.get("discrete_mismatch", []):
                _tally(nm, "discrete_mismatch", detail=disc_detail.get(nm))

        # the count reconciliation against A28's recorded run of the same
        # arm and start
        ref = None
        ref_path = (MAIN / "arch_surgery/idf_probe/runs/a28/h5"
                    / SCENARIO / arm / f"start{k:03d}" / "metrics.json")
        if ref_path.exists():
            ref = json.loads(ref_path.read_text())
        own_tot = m.get("module_solve_totals") or {}
        own_hist = own_tot.get("outer_pass_hist")
        a28_tot = (ref or {}).get("module_solve_totals") or {}
        run_summary = summary["runs"].setdefault(label, {})
        run_summary.update({
            "rc_status": m.get("status"),
            "n_trace_records": n_records,
            "n_pass_ge2_exceedance_records": n_exceed_records,
            "n_constant_only_exceedance_records": n_const_only_records,
            "n_calls_with_exceedance": len(exceed_calls),
            "own_outer_pass_hist": own_hist,
            "a28_recorded_outer_pass_hist": a28_tot.get("outer_pass_hist"),
            "hist_matches_a28": (
                (own_hist == a28_tot.get("outer_pass_hist"))
                if ref else None
            ),
            "own_inner_sweeps_by_block": own_tot.get("inner_sweeps_by_block"),
            "a28_inner_sweeps_by_block": a28_tot.get("inner_sweeps_by_block"),
            "own_n_call_models": own_tot.get("n_call_models"),
            "a28_n_call_models": a28_tot.get("n_call_models"),
            "norm_objf_hex": m.get("exact", {}).get("norm_objf"),
            "a28_norm_objf_hex": (ref or {}).get("exact", {}).get("norm_objf"),
            "node_calls_solve_phase": m.get("node_calls_solve_phase"),
            "a28_node_calls_solve_phase": (ref or {}).get(
                "node_calls_solve_phase"),
        })
        (RUNS / "analysis").mkdir(parents=True, exist_ok=True)
        (RUNS / "analysis" / f"per_pass_movers_{gen}_{arm}_start{k:03d}.json"
         ).write_text(json.dumps(per_pass_movers, indent=2))

    # component verdicts, stated in the A1' schedule's block attribution
    node_block = a1p_node_block
    for key, a in sorted(agg.items()):
        blocks = comp_module.get(key, [])
        rt_writers = runtime_writers.get(key, [])
        st_writers = static["writers"].get(key, [])
        st_readers = static["readers"].get(key, [])
        writer_blocks = sorted({
            b for n in rt_writers for b in [node_block.get(n)] if b
        })
        model_readers = [r for r in st_readers
                         if not r.startswith(("driver:", "unmapped:"))
                         and r != "objective_constraints"]
        reader_blocks = sorted({
            node_block.get(r) for r in model_readers if node_block.get(r)
        })
        # loop-carried: a model reader whose block runs strictly earlier in
        # the outer pass than the (runtime) writer's block
        loop_carried_pairs = []
        for wnode in rt_writers:
            wb = node_block.get(wnode)
            if wb not in block_index:
                continue
            for rnode in model_readers:
                rb = node_block.get(rnode)
                if rb in block_index and block_index[rb] < block_index[wb]:
                    loop_carried_pairs.append(
                        {"writer": wnode, "writer_block": wb,
                         "reader": rnode, "reader_block": rb}
                    )
        self_coupled = sorted(set(rt_writers) & set(model_readers))
        summary["components"][key] = {
            "kind": a["kind"],
            "n_exceedances": a["n_exceedances"],
            "n_distinct_calls": len(a["n_calls"]),
            "runs": sorted(a["runs"]),
            "max_scaled": a["max_scaled"],
            "max_abs_delta": a["max_abs_delta"],
            "max_rel_delta": a["max_rel_delta"],
            "by_pass": dict(a["by_pass"]),
            "block_writeset_membership": blocks,
            "runtime_writer_nodes": rt_writers,
            "static_writer_models": st_writers,
            "static_reader_models": st_readers,
            "writer_blocks": writer_blocks,
            "reader_blocks_models_only": reader_blocks,
            "cross_block_loop_carried_pairs": loop_carried_pairs,
            "self_coupled_writer_reader": self_coupled,
            "scaled_by_call_pass": a["scaled_by_call_pass"],
        }

    # A28 campaign-wide census (read-only, main checkout): on how many of
    # the 25 recorded A1' starts does the run-level moved-constant union
    # name pf_power.srcktpm, and how do the calls-with-moved-constant
    # counts sit against the 3+-pass tail.  The traced evidence covers two
    # starts; this states how far the named mechanism's *fingerprint*
    # extends across the campaign without re-running it.
    census = {"n_starts_read": 0, "n_with_srcktpm_in_union": 0,
              "per_start": {}}
    for p in sorted(A28_REF_DIR.glob("start*/metrics.json")):
        rec = json.loads(p.read_text())
        tot = rec.get("module_solve_totals") or {}
        hist = tot.get("outer_pass_hist") or {}
        n3plus = sum(v for kk, v in hist.items() if int(kk) >= 3)
        has = "pf_power.srcktpm" in (tot.get("moved_constants") or [])
        census["n_starts_read"] += 1
        census["n_with_srcktpm_in_union"] += bool(has)
        census["per_start"][p.parent.name] = {
            "srcktpm_in_moved_constant_union": has,
            "calls_at_3plus_passes": n3plus,
            "n_call_models_with_moved_constant": tot.get(
                "n_call_models_with_moved_constant"),
        }
    summary["a28_campaign_census"] = census

    out = RUNS / "analysis" / "summary.json"
    out.write_text(json.dumps(summary, indent=2))
    print(f"analysis written to {out}")
    print(f"\nA28 campaign census: srcktpm in the moved-constant union of "
          f"{census['n_with_srcktpm_in_union']} of "
          f"{census['n_starts_read']} recorded A1' starts")

    # console digest: the verdict table
    print("\ncomponents failing the pass>=2 joint test "
          f"({len(summary['components'])} distinct):")
    rows = sorted(summary["components"].items(),
                  key=lambda kv: -kv[1]["n_exceedances"])
    for key, c in rows:
        lc = len(c["cross_block_loop_carried_pairs"])
        print(f"  {key:50s} {c['kind']:20s} n={c['n_exceedances']:5d} "
              f"calls={c['n_distinct_calls']:4d} "
              f"max_scaled={c['max_scaled']:.3e} "
              f"max_rel_delta={c['max_rel_delta']:.3e} "
              f"blocks={','.join(c['block_writeset_membership']) or '?'} "
              f"writers={','.join(c['runtime_writer_nodes']) or '?'} "
              f"loop_carried_pairs={lc} "
              f"self_coupled={','.join(c['self_coupled_writer_reader']) or '-'}")
    for name, r in summary["runs"].items():
        print(f"\n{name}: hist_matches_a28={r.get('hist_matches_a28')} "
              f"own={r.get('own_outer_pass_hist')} "
              f"a28={r.get('a28_recorded_outer_pass_hist')} "
              f"exceed_records={r.get('n_pass_ge2_exceedance_records')} "
              f"(constant-only {r.get('n_constant_only_exceedance_records')}) "
              f"over calls={r.get('n_calls_with_exceedance')}")
    return 0


# --------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("stage",
                    choices=["neutrality", "trace", "retrace", "a0p",
                             "analyze", "all"])
    ap.add_argument("--with-a0p", action="store_true",
                    help="analyze: include the traced A0p run")
    args = ap.parse_args()
    RUNS.mkdir(parents=True, exist_ok=True)
    (RUNS / "_mplconfig").mkdir(exist_ok=True)

    if args.stage == "neutrality":
        return stage_neutrality()
    if args.stage == "trace":
        return stage_trace()
    if args.stage == "retrace":
        return stage_retrace()
    if args.stage == "a0p":
        return stage_a0p()
    if args.stage == "analyze":
        return stage_analyze(args.with_a0p)
    rc = stage_neutrality()
    rc = stage_trace() or rc
    rc = stage_retrace() or rc
    return stage_analyze(False) or rc


if __name__ == "__main__":
    raise SystemExit(main())
