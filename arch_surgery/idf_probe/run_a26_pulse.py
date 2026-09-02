#!/usr/bin/env python
"""Run plan §4.1d's gate: ``pulse`` in the pre-predicate slot, under the lift.

Two arms per pulsed deck, differing in **one** setting::

    A  PROCESS_ARCH_LIFT=burn_time  PROCESS_ARCH_HOIST=feedforward
    B  PROCESS_ARCH_LIFT=burn_time  PROCESS_ARCH_HOIST=feedforward_lifted

Both run the derived ``ixc = 178`` / ``icc = 93`` deck (A25's
``a25_variant_deck.py``), so the lift is on in both and only ``pulse``'s
placement differs.

Every run is a **fresh subprocess in its own working directory**, serial (trap
T8), ``PYTHONPATH`` pinned to this worktree and the **exact** tree asserted
inside (trap T6).  The first run in a fresh environment is discarded --- numba
JIT dominates it.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TREE = HERE.parent.parent
RUNS = HERE / "runs" / "a26_pulse"

#: Decks with a burn-time coupler.  ``st_regression`` has ``i_pulsed_plant = 0``
#: so ``Pulse`` writes nothing and there is nothing to lift or to hoist.
PULSED = ["large_tokamak_nof", "low_aspect_ratio_DEMO"]

VOLATILE = (
    "(date)", "(time)", "(username)", "(computer)", "(directory)",
    "(fileprefix)", "(tagno)", "(branch_name)", "(commsg)", "(process_runtime)",
)


def _env(extra=None) -> dict:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(TREE)
    env["MPLCONFIGDIR"] = str(RUNS / "_mplconfig")
    env.pop("PROCESS_IDF_PROBE", None)
    env.pop("PROCESS_ARCH_HOIST", None)
    env.pop("PROCESS_ARCH_LIFT", None)
    if extra:
        env.update({k: str(v) for k, v in extra.items()})
    return env


def _sh(cmd, cwd, env, log: Path) -> int:
    t0 = time.perf_counter()
    p = subprocess.run(cmd, cwd=str(cwd), env=env, capture_output=True, text=True)
    log.with_suffix(".stdout.log").write_text(p.stdout)
    log.with_suffix(".stderr.log").write_text(p.stderr)
    print(f"      rc={p.returncode} {time.perf_counter() - t0:6.1f}s", flush=True)
    if p.returncode:
        print(p.stderr[-1500:], flush=True)
    return p.returncode


def mfile_lines(d: Path):
    c = sorted(d.glob("*MFILE.DAT"))
    if not c:
        return None
    return [ln for ln in c[0].read_text(errors="replace").splitlines()
            if not any(k in ln for k in VOLATILE)]


def mfile_floats(d: Path):
    """Every numeric MFILE value as an exact hex float, keyed by its label.

    A13's comparator anchored on the first ``(...)`` and silently dropped about
    a thousand floats per scenario (protocol §12's worked example).  This one
    takes the **last** parenthesised group as the key and parses every field
    that parses as a float, and reports how many it found so the denominator is
    visible.
    """
    c = sorted(d.glob("*MFILE.DAT"))
    if not c:
        return None
    out = {}
    for ln in c[0].read_text(errors="replace").splitlines():
        if any(k in ln for k in VOLATILE):
            continue
        parts = ln.split()
        if not parts:
            continue
        try:
            v = float(parts[-1])
        except ValueError:
            continue
        out[ln[: ln.rfind("_") if "_" in ln else 40][:80] + parts[0]] = v.hex()
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenarios", nargs="*", default=PULSED)
    args = ap.parse_args()
    RUNS.mkdir(parents=True, exist_ok=True)
    (RUNS / "_mplconfig").mkdir(exist_ok=True)
    sys.path.insert(0, str(HERE))
    from a26_pulse_gate import compare, sensitivity  # noqa: PLC0415

    report = {}
    warm = [True]
    for s in args.scenarios:
        base = RUNS / s
        if base.exists():
            shutil.rmtree(base)
        base.mkdir(parents=True)
        print(f"  {s}: deriving the lifted deck", flush=True)
        rc = _sh(
            [sys.executable, str(HERE / "a25_variant_deck.py"),
             "--scenario", s, "--outdir", str(base / "deck"),
             "--expect-tree", str(TREE)],
            base, _env(), base / "deck_derive",
        )
        deck = base / "deck" / f"{s}_lifted.IN.DAT"
        if rc or not deck.exists():
            report[s] = {"status": "INCOMPLETE -- variant deck not derived"}
            continue

        arms = {}
        plan = [("feedforward", "A"), ("feedforward_lifted", "B")]
        if warm[0]:
            plan.insert(0, ("feedforward", "warmup_discarded"))
            warm[0] = False
        for hoist, tag in plan:
            d = base / tag
            d.mkdir(parents=True, exist_ok=True)
            shutil.copy(deck, d / deck.name)
            print(f"  {s}: arm {tag} (HOIST={hoist}, LIFT=burn_time)", flush=True)
            rc = _sh(
                [sys.executable, str(HERE / "a26_pulse_gate.py"),
                 "--deck", str(d / deck.name), "--outdir", str(d),
                 "--expect-tree", str(TREE), "--label", tag],
                d, _env({"PROCESS_ARCH_HOIST": hoist,
                         "PROCESS_ARCH_LIFT": "burn_time"}),
                d / "run",
            )
            if tag == "warmup_discarded":
                continue
            p = d / "predicate_stream.json"
            arms[tag] = json.loads(p.read_text()) if p.exists() else {
                "status": "missing", "n_call_models": 0, "calls": []
            }

        if len(arms) != 2 or any(a.get("status") != "ok" for a in arms.values()):
            report[s] = {"status": "INCOMPLETE -- an arm did not run",
                         "arm_status": {k: v.get("status") for k, v in arms.items()}}
            continue

        la, lb = mfile_lines(base / "A"), mfile_lines(base / "B")
        fa, fb = mfile_floats(base / "A"), mfile_floats(base / "B")
        keys = sorted(set(fa or {}) | set(fb or {}))
        report[s] = {
            "arms": {
                "A": {k: arms["A"][k] for k in
                      ("hoist_name", "hoist_nodes", "pre_predicate_tail",
                       "post_predicate_tail", "n_call_models")},
                "B": {k: arms["B"][k] for k in
                      ("hoist_name", "hoist_nodes", "pre_predicate_tail",
                       "post_predicate_tail", "n_call_models")},
            },
            "predicate_stream": compare(arms["A"], arms["B"]),
            "sensitivity": sensitivity(arms["A"], arms["B"]),
            "mfile": {
                "lines_compared": len(la or []),
                "lines_differing": (
                    sum(1 for x, y in zip(la or [], lb or [], strict=False)
                        if x != y) + abs(len(la or []) - len(lb or []))
                ),
                "floats_compared": len(keys),
                "floats_differing": sum(
                    1 for k in keys if (fa or {}).get(k) != (fb or {}).get(k)
                ),
            },
            "note_constraint_41": (
                "constraints.t_current_ramp_up_min is read by constraint "
                "equation 41 alone, and no deck in this study activates "
                "icc = 41.  A zero difference in conf is therefore expected "
                "regardless of where pulse runs, and is NOT evidence that the "
                "placement is right.  The non-vacuous quantity is the field "
                "itself, compared above as an exact hex float at every "
                "call_models return."
            ),
        }
        r = report[s]
        r["status"] = (
            "PASS" if r["predicate_stream"]["status"] == "PASS"
            and r["sensitivity"]["status"] == "PASS"
            and r["mfile"]["lines_differing"] == 0
            and r["mfile"]["floats_differing"] == 0 else "FAIL"
        )
        print(f"    {s}: {r['status']}  field diffs "
              f"{r['predicate_stream']['differing_t_current_ramp_up_min_calls']}"
              f"/{r['predicate_stream']['n_calls_compared']} calls; conf diffs "
              f"{r['predicate_stream']['differing_conf_calls']} "
              f"({r['predicate_stream']['n_conf_entries_compared']} entries); "
              f"MFILE {r['mfile']['lines_differing']}/{r['mfile']['lines_compared']} "
              f"lines, {r['mfile']['floats_differing']}/{r['mfile']['floats_compared']} "
              f"floats; sensitivity {r['sensitivity']['n_caught']}/"
              f"{r['sensitivity']['n_applied']}", flush=True)

    (RUNS / "_pulse_gate.json").write_text(json.dumps(report, indent=2))
    return 0 if report and all(
        v.get("status") == "PASS" for v in report.values()
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
