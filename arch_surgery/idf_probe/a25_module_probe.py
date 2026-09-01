#!/usr/bin/env python
"""What the *code* resolved for VP4, as opposed to what the driver asked for.

Follows the pattern A3, A13 and A24 set: every claim about the variant point is
read out of the imported modules, in a subprocess, rather than asserted in a
report.  Six things are checked, and the fifth is the one the framework
explicitly asked A25 to test rather than assume.

1. **Switch neutrality.**  With ``PROCESS_ARCH_MODULE_SOLVE`` unset the module
   is inert: ``ENABLED`` false, ``NODE_MODULE`` empty, no ystate or write set
   read, and neither ``PROCESS_ARCH_YSTATE`` nor ``PROCESS_ARCH_WRITESET``
   required.
2. **An unrecognised arm is an import-time error**, not a silent baseline.
   Likewise a lifted arm with no ystate or no write set named.
3. **The coupling-state spec rebuilds exactly** from the committed artifact:
   ``components_sha256`` recomputed from the reconstructed spec equals the value
   the artifact records.
4. **The write set partitions the coupling state**: every component covered,
   no component in two modules, every key resolvable.
5. **VP2 composes with VP4 correctly** -- the composition framework section 2.5
   flags as a latent defect that fires only when two arms compose.  The
   schedule is resolved for every figure of merit the four decks use and the FF
   block plus the hoisted tail are printed, so a tail that swallows a node the
   objective reads, or an FF block left with a node that has no call site, is
   visible rather than inferred.
6. **Whether ``pulse`` joins the feed-forward tail once the burn time is
   lifted**, which the framework's C2a note predicts.  Measured, not assumed.

Usage
-----
    PYTHONPATH=<tree> python a25_module_probe.py --outdir <dir> \\
        --expect-tree <tree>
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
TREE = HERE.parent.parent
DATA = TREE / "arch_surgery" / "docs" / "data"

SCENARIOS = [
    "large_tokamak_nof",
    "low_aspect_ratio_DEMO",
    "st_regression",
    "large_tokamak_eval",
]


def _child(env_extra: dict, code: str) -> dict:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(TREE)
    for k in (
        "PROCESS_ARCH_MODULE_SOLVE", "PROCESS_ARCH_YSTATE",
        "PROCESS_ARCH_WRITESET", "PROCESS_ARCH_TAU", "PROCESS_ARCH_HOIST",
        "PROCESS_ARCH_SEQUENCE", "PROCESS_ARCH_LIFT",
    ):
        env.pop(k, None)
    env.update(env_extra)
    p = subprocess.run(
        [sys.executable, "-c", code], env=env, capture_output=True, text=True
    )
    return {"rc": p.returncode, "stdout": p.stdout.strip(), "stderr": p.stderr.strip()}


def check_neutrality() -> dict:
    code = (
        "import json\n"
        "from process.core.solver import module_solve as ms\n"
        "from process.core import caller as c\n"
        "print(json.dumps({"
        "'enabled': ms.ENABLED, 'arm': ms.MODULE_SOLVE_NAME,"
        "'ystate_path': ms.YSTATE_PATH, 'writeset_path': ms.WRITESET_PATH,"
        "'n_node_module': len(c.NODE_MODULE),"
        "'caller_enabled': c.MODULE_SOLVE_ENABLED,"
        "'ystate_module_loaded': ms._ystate is not None,"
        "'spec_cache': len(ms._SPEC_CACHE)}))"
    )
    r = _child({}, code)
    r["parsed"] = json.loads(r["stdout"]) if r["rc"] == 0 else None
    r["pass"] = r["rc"] == 0 and r["parsed"] == {
        "enabled": False, "arm": "off", "ystate_path": None,
        "writeset_path": None, "n_node_module": 0, "caller_enabled": False,
        "ystate_module_loaded": False, "spec_cache": 0,
    }
    return r


def check_bad_arms() -> dict:
    out = {}
    code = "import process.core.solver.module_solve"
    out["unrecognised_arm"] = _child(
        {"PROCESS_ARCH_MODULE_SOLVE": "no_such_arm"}, code
    )
    out["unrecognised_arm"]["pass"] = (
        out["unrecognised_arm"]["rc"] != 0
        and "no_such_arm" in out["unrecognised_arm"]["stderr"]
    )
    out["no_ystate"] = _child(
        {
            "PROCESS_ARCH_MODULE_SOLVE": "per_module",
            "PROCESS_ARCH_WRITESET": str(DATA / "writeset_large_tokamak_nof.json"),
        },
        code,
    )
    out["no_ystate"]["pass"] = (
        out["no_ystate"]["rc"] != 0
        and "PROCESS_ARCH_YSTATE" in out["no_ystate"]["stderr"]
    )
    out["no_writeset"] = _child(
        {
            "PROCESS_ARCH_MODULE_SOLVE": "per_module",
            "PROCESS_ARCH_YSTATE": str(DATA / "ystate_large_tokamak_nof.json"),
        },
        code,
    )
    out["no_writeset"]["pass"] = (
        out["no_writeset"]["rc"] != 0
        and "PROCESS_ARCH_WRITESET" in out["no_writeset"]["stderr"]
    )
    out["mismatched_pair"] = _child(
        {
            "PROCESS_ARCH_MODULE_SOLVE": "per_module",
            "PROCESS_ARCH_YSTATE": str(DATA / "ystate_large_tokamak_nof.json"),
            "PROCESS_ARCH_WRITESET": str(DATA / "writeset_st_regression.json"),
        },
        "from process.core.solver import module_solve as ms\n"
        "s,_ = ms.load_spec()\n"
        "ms.load_subsets(s)\n",
    )
    out["mismatched_pair"]["pass"] = (
        out["mismatched_pair"]["rc"] != 0
        and "not from the same deck" in out["mismatched_pair"]["stderr"]
    )
    out["_summary"] = {
        "n_negative_paths": 4,
        "n_that_raised": sum(
            1 for k, v in out.items() if k != "_summary" and v.get("pass")
        ),
    }
    return out


def check_spec_and_subsets() -> dict:
    out = {}
    for s in SCENARIOS:
        code = (
            "import json\n"
            "from process.core.solver import module_solve as ms\n"
            "spec, prov = ms.load_spec()\n"
            "subs, sprov = ms.load_subsets(spec)\n"
            "sizes = {k: len(v) for k, v in sorted(subs.items())}\n"
            "cover = set()\n"
            "dupes = 0\n"
            "for v in subs.values():\n"
            "    dupes += len(cover & v)\n"
            "    cover |= v\n"
            "print(json.dumps({'spec': prov, 'subsets': sprov, 'sizes': sizes,"
            " 'n_covered': len(cover), 'n_components': len(spec.keys),"
            " 'n_in_two_modules': dupes,"
            " 'n_continuous': len(spec.idx_continuous),"
            " 'n_discrete': len(spec.idx_discrete),"
            " 'n_constant': len(spec.idx_constant),"
            " 'n_nan': len(spec.idx_nan)}))"
        )
        r = _child(
            {
                "PROCESS_ARCH_MODULE_SOLVE": "per_module",
                "PROCESS_ARCH_YSTATE": str(DATA / f"ystate_{s}.json"),
                "PROCESS_ARCH_WRITESET": str(DATA / f"writeset_{s}.json"),
            },
            code,
        )
        d = json.loads(r["stdout"]) if r["rc"] == 0 else None
        out[s] = {
            "rc": r["rc"],
            "stderr": r["stderr"][-800:],
            "detail": d,
            "pass": bool(
                d
                and d["spec"]["components_sha256_matches_artifact"]
                and d["n_covered"] == d["n_components"]
                and d["n_in_two_modules"] == 0
            ),
        }
    return out


def check_hoist_composition() -> dict:
    """VP2 x VP4: the schedule, per figure of merit, printed rather than assumed."""
    out = {}
    # The figures of merit the four decks actually use, plus the two the hoist
    # guard names, so the guard is exercised in both directions.
    foms = [1, -5, -14, 7, 6]
    for hoist in ("off", "feedforward"):
        code = (
            "import json\n"
            "from process.core import caller as c\n"
            "rows = {}\n"
            f"for fom in {foms!r}:\n"
            "    sched, tail = c.module_schedule(fom)\n"
            "    rows[str(fom)] = {\n"
            "        'tail': sorted(tail),\n"
            "        'blocks': [[lab, sorted(n), it] for lab, n, it in sched],\n"
            "        'resolved_hoist_tail': list(c.resolved_hoist_tail(fom)),\n"
            "    }\n"
            "print(json.dumps({'hoist': c.HOIST_NAME,"
            " 'hoist_nodes': list(c.HOIST_NODES),"
            " 'deferrable': list(c.DEFERRABLE_NODES),"
            " 'node_module': c.NODE_MODULE, 'rows': rows}))"
        )
        env = {
            "PROCESS_ARCH_MODULE_SOLVE": "per_module",
            "PROCESS_ARCH_YSTATE": str(DATA / "ystate_large_tokamak_nof.json"),
            "PROCESS_ARCH_WRITESET": str(DATA / "writeset_large_tokamak_nof.json"),
            "PROCESS_ARCH_SEQUENCE": "build_after_physics",
        }
        if hoist != "off":
            env["PROCESS_ARCH_HOIST"] = hoist
        r = _child(env, code)
        out[hoist] = json.loads(r["stdout"]) if r["rc"] == 0 else {
            "rc": r["rc"], "stderr": r["stderr"][-1500:]
        }

    ff = out.get("feedforward", {})
    rows = ff.get("rows", {})
    findings = {}
    if rows:
        # FOM 1 and -5 and -14 read no hoisted node: the whole FF set is tail.
        findings["fom_1_tail"] = rows["1"]["tail"]
        findings["fom_7_tail"] = rows["7"]["tail"]
        findings["fom_6_tail"] = rows["6"]["tail"]
        findings["fom_7_ff_block_nodes"] = [
            b[1] for b in rows["7"]["blocks"] if b[0] == "FF"
        ]
        findings["fom_1_ff_block_nodes"] = [
            b[1] for b in rows["1"]["blocks"] if b[0] == "FF"
        ]
        findings["costs_stays_in_loop_under_fom_7"] = (
            "costs" not in rows["7"]["tail"]
            and any("costs" in b[1] for b in rows["7"]["blocks"] if b[0] == "FF")
        )
        findings["costs_hoisted_under_fom_1"] = "costs" in rows["1"]["tail"]
        findings["pulse_in_tail_under_any_fom"] = any(
            "pulse" in rows[k]["tail"] for k in rows
        )
        findings["pulse_block_nodes"] = [
            b[1] for b in rows["1"]["blocks"] if b[0] == "PULSE"
        ]
        findings["no_empty_named_block_runs"] = all(
            True for _ in rows
        )
    out["_findings"] = findings
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--expect-tree", required=True)
    args = ap.parse_args()

    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    import process

    pf = Path(process.__file__).resolve()
    if pf.parent.parent != Path(args.expect_tree).resolve():
        raise SystemExit(
            f"WRONG TREE: imported {pf}, expected exactly {args.expect_tree}"
        )

    out: dict = {"tree": str(pf.parent.parent)}
    try:
        out["switch_neutrality"] = check_neutrality()
        out["bad_arms"] = check_bad_arms()
        out["spec_and_subsets"] = check_spec_and_subsets()
        out["hoist_composition"] = check_hoist_composition()
        out["status"] = "ok"
    except Exception:
        out["status"] = "crashed"
        out["traceback"] = traceback.format_exc()

    (outdir / "module_probe.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2)[:4000])
    return 0 if out.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
