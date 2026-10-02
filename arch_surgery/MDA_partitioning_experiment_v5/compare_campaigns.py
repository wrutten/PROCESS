#!/usr/bin/env python
"""Several V5 campaigns side by side, per configuration: outcomes, phase A, phase B, rules.

Each campaign is one run ID's folder under ``runs/`` (README §12).  **No PROCESS
run; nothing is written under ``runs/``.**  Per configuration (``tok``, ``lad``,
``st``) and per campaign it prints:

* **run outcomes per arm**, phase B (25 starts per arm) and phase A (25
  displaced-entry evaluations per arm), read from each record's ``metrics.json``:
  ``accepted`` (``status == ok`` and ``mfile.ifail == 1``), ``ok, ifail = k``
  (finished, not accepted), ``RuntimeError`` (a crash whose traceback's last line
  is a ``RuntimeError``), ``loop cap`` (``ModuleSolveFailure``: the coupling loop's
  sweep cap; the block, the cap, τ and the residual component the message names
  are listed), ``other`` (any other status or crash, with its last line);
* **phase A** module sweeps per evaluation, the four arm means and the declared
  pair's ratio of means (``A2/A1`` pulsed, ``A2/A0`` on ``st``, D34), recounted by
  :mod:`paper_cells_recount` (which reads the raw records and imports nothing of
  the harness);
* **phase B** over each campaign's own seed set (every arm accepted), from the
  campaign press's tally stage record (``gates/tally_optimisation``, table *the
  optimiser's path over the configurations*): per arm the mean iterations
  (summed over attempts), evaluations ε, node calls per evaluation ρ and node
  calls per run R = ρ × ε, and the ratios of means ``B2/B0``, ``B1/B0`` (where B1
  exists) and ``B2/BR``; and the ratios of *cost against both anchors*;
* **the rules**: A1 (matched accuracy; the declared pair's verdict, table
  *matched accuracy by configuration* of ``gates/tally_evaluation``) and B1 (same
  optimum; each judged pair's verdict, hops and hop seeds, table *same optimum by
  rung*).

Every number is read, none is derived beyond a ratio of two printed means.  A
stage record stamped with a run ID other than its folder's is refused; one with
no stamp (made before the run-ID layout) is read as its folder's and said so.
Records are read through :func:`paper_cells_recount.read_record`, which applies
the arm-name translation for records made before 2026-09-15 (trap T16) to the
record's own arm field, never to a directory name.

Usage::

    python compare_campaigns.py census_tau1e-08 write_set_tau1e-06 write_set_tau1e-08 \
        [--output campaign_comparison.md]

Written for the V5 campaign under the whole write set at τ = 1e-8 (2026-10-02),
to put it beside the two campaigns already on disk.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import paper_cells_recount as recount

HERE = Path(__file__).resolve().parent
RUNS = HERE / "runs"

CONFIGURATIONS = recount.CONFIGURATIONS
SHORT = recount.SHORT
PHASE_A_ARMS = recount.PHASE_A_ARMS
PHASE_B_ARMS = recount.PHASE_B_ARMS
CAP = re.compile(
    r"block (?P<block>\S+) did not converge in (?P<cap>\d+) sweeps at tau=(?P<tau>\S+); "
    r"max scaled residual (?P<residual>\S+) on (?P<component>\S+), (?P<n>\d+) components above tau"
)


class ComparisonError(RuntimeError):
    pass


# --------------------------------------------------------------------------
# reading
# --------------------------------------------------------------------------


def last_line(record: dict[str, Any]) -> str:
    tb = record.get("traceback") or ""
    if isinstance(tb, list):
        tb = "\n".join(str(x) for x in tb)
    lines = [ln for ln in str(tb).splitlines() if ln.strip()]
    return lines[-1].strip() if lines else ""


def outcome(record: dict[str, Any], phase: str) -> tuple[str, str]:
    """``(class, detail)`` of one record."""
    status = record.get("status")
    if status == "ok":
        if phase == "evaluation":
            return "ok", ""
        ifail = (record.get("mfile") or {}).get("ifail")
        if ifail == 1.0:
            return "accepted", ""
        return f"ok, ifail = {ifail if ifail is None else int(ifail)}", ""
    line = last_line(record)
    if "ModuleSolveFailure" in line:
        m = CAP.search(line)
        detail = (
            f"block {m['block']}, {m['cap']} sweeps at tau={m['tau']}, residual {m['residual']} on {m['component']} "
            f"({m['n']} above tau)"
            if m
            else line
        )
        return "loop cap", detail
    if line.startswith("RuntimeError"):
        return "RuntimeError", line
    return "other", f"status {status}, failure_class {record.get('failure_class')}: {line}"


def stage_record(folder: Path, stage: str) -> tuple[dict[str, Any], str]:
    path = folder / "gates" / stage / "measurements.json"
    if not path.exists():
        raise ComparisonError(f"{path} does not exist: press the campaign's reading stages first")
    data = json.loads(path.read_text())
    run = (data.get("run") or {}).get("run_id")
    if run is not None and run != folder.name:
        raise ComparisonError(f"{path} is stamped with run ID {run!r}, not its folder's {folder.name!r}")
    note = f"stamped {run}" if run else "no run-ID stamp (made before the run-ID layout); read as the folder's"
    return data, note


def table(data: dict[str, Any], name: str) -> dict[str, Any]:
    for t in data["tables"]:
        if t["table"] == name:
            return t
    raise ComparisonError(f"no table {name!r} in the stage record")


def fmt(value: Any, spec: str = ".4f") -> str:
    if value is None or value == "—":
        return "—"
    if isinstance(value, (int, float)):
        return format(float(value), spec)
    return str(value)


def ratio(num: Any, den: Any) -> float | None:
    if not isinstance(num, (int, float)) or not isinstance(den, (int, float)) or not den:
        return None
    return float(num) / float(den)


# --------------------------------------------------------------------------
# one campaign
# --------------------------------------------------------------------------


def read_campaign(run_id: str) -> dict[str, Any]:
    folder = RUNS / run_id
    if not (folder / "campaign").exists():
        raise ComparisonError(f"no campaign records under {folder}")
    out: dict[str, Any] = {"run_id": run_id, "configurations": {}}
    opt, out["tally_optimisation"] = stage_record(folder, "tally_optimisation")
    ev, out["tally_evaluation"] = stage_record(folder, "tally_evaluation")
    out["heads_optimisation"] = sorted(h[:8] for h in opt["runs_provenance"].get("heads") or [])
    path_rows = table(opt, "the optimiser's path over the configurations — campaign_optimisation")["rows"]
    anchors = table(opt, "cost against both anchors — campaign_optimisation")["rows"]
    rungs = table(opt, "same optimum by rung — campaign_optimisation")["rows"]
    accuracy = table(ev, "matched accuracy by configuration — campaign_displaced")["rows"]
    heads: set[str] = set()
    for configuration in CONFIGURATIONS:
        c: dict[str, Any] = {}
        for phase in ("optimisation", "evaluation"):
            by_arm = recount.records_of(folder, phase, configuration)
            classes: dict[str, dict[str, list[int]]] = {}
            details: dict[str, dict[str, list[int]]] = {}
            for arm, rows in sorted(by_arm.items()):
                for seed, rec in sorted(rows.items()):
                    heads.add(str(rec.get("tree_git_head"))[:8])
                    cls, detail = outcome(rec, phase)
                    classes.setdefault(arm, {}).setdefault(cls, []).append(seed)
                    if detail:
                        details.setdefault(arm, {}).setdefault(f"{cls}: {detail}", []).append(seed)
            c[f"{phase}_outcomes"] = classes
            c[f"{phase}_details"] = details
        c["phase_a"] = recount.recount_phase_a(folder, configuration)
        c["path"] = {r["quantity"].split(",")[0].split(" (")[0]: r for r in path_rows if r["configuration"] == configuration}
        c["anchors"] = [r for r in anchors if r["configuration"] == configuration]
        c["rungs"] = [r for r in rungs if r["configuration"] == configuration and r["role"] == "judged"]
        c["accuracy"] = next(r for r in accuracy if r["configuration"] == configuration)
        ref = c["accuracy"]["reference"]
        c["above_tau"] = next(
            (v.get("n_arm_runs_with_a_component_above_tau") for v in ev.get("similarity_verdicts") or []
             if v.get("source") == "campaign_displaced" and v.get("configuration") == configuration and v.get("pair") == f"A2/{ref}"),
            None,
        )
        out["configurations"][configuration] = c
    out["record_heads"] = sorted(heads)
    return out


# --------------------------------------------------------------------------
# rendering
# --------------------------------------------------------------------------


def seeds(values: list[int]) -> str:
    return ", ".join(str(s) for s in values)


def render(campaigns: list[dict[str, Any]], commit: str) -> str:
    out: list[str] = []
    w = out.append
    w("# Campaigns side by side")
    w("")
    w(f"Generated by `compare_campaigns.py` at `{commit}` from the run-ID folders under `runs/`, read-only.")
    w("Phase B over each campaign's own seed set (every arm accepted); a ratio is a ratio of the two arms' means")
    w("over that set (equal to the ratio of sums).  Phase A over 25 displaced-entry evaluations per arm (seeds 1-25).")
    w("")
    w("| run ID | campaign records' commits | tally_optimisation | tally_evaluation |")
    w("|---|---|---|---|")
    for c in campaigns:
        w(f"| `{c['run_id']}` | {', '.join(c['record_heads'])} | {c['tally_optimisation']} | {c['tally_evaluation']} |")
    w("")
    for configuration in CONFIGURATIONS:
        short = SHORT[configuration]
        w(f"## `{short}` ({configuration})")
        w("")
        # outcomes, phase B
        w("**Phase B run outcomes per arm** (25 starts per arm; seeds in brackets for the classes other than accepted):")
        w("")
        w("| run ID | arm | accepted | ok, ifail ≠ 1 | RuntimeError | loop cap | other |")
        w("|---|---|---:|---|---|---|---|")
        for c in campaigns:
            oc = c["configurations"][configuration]["optimisation_outcomes"]
            for arm in PHASE_B_ARMS:
                if arm not in oc:
                    continue
                cls = oc[arm]
                notok = {k: v for k, v in cls.items() if k.startswith("ok, ifail")}
                notok_s = "; ".join(f"{len(v)} ({k[4:]}: {seeds(v)})" for k, v in sorted(notok.items())) or "0"

                def cell(k: str) -> str:
                    v = cls.get(k, [])
                    return f"{len(v)} ({seeds(v)})" if v else "0"

                w(f"| `{c['run_id']}` | {arm} | {len(cls.get('accepted', []))} | {notok_s} | {cell('RuntimeError')} | {cell('loop cap')} | {cell('other')} |")
        w("")
        for c in campaigns:
            det = c["configurations"][configuration]["optimisation_details"]
            caps = [(arm, k, v) for arm, d in sorted(det.items()) for k, v in d.items() if not k.startswith("RuntimeError")]
            for arm, k, v in caps:
                w(f"- `{c['run_id']}` {arm}: {k} — seeds {seeds(v)}")
        w("")
        # outcomes, phase A
        w("**Phase A outcomes** (25 per arm):")
        w("")
        for c in campaigns:
            oc = c["configurations"][configuration]["evaluation_outcomes"]
            w(f"- `{c['run_id']}`: " + "; ".join(
                f"{arm} " + ", ".join(f"{k} {len(v)}" for k, v in sorted(oc[arm].items())) for arm in PHASE_A_ARMS if arm in oc))
        w("")
        # phase A
        pair = campaigns[0]["configurations"][configuration]["phase_a"]["pair"]
        w(f"**Phase A, module sweeps per evaluation: AR / A0 / A1 / A2 means, and {pair[1]}/{pair[0]} ratio of means**:")
        w("")
        w("| module | " + " | ".join(f"`{c['run_id']}`" for c in campaigns) + " |")
        w("|---|" + "---|" * len(campaigns))
        for label, _ in recount.ROWS:
            cells = []
            for c in campaigns:
                row = c["configurations"][configuration]["phase_a"]["rows"][label]
                means = " / ".join(fmt(row[a], ".2f") for a in PHASE_A_ARMS)
                r = row["ratio"]["pooled"] if row["ratio"] else None
                cells.append(f"{means} · {fmt(r, '.2f')}")
            w(f"| {label} | " + " | ".join(cells) + " |")
        w("")
        # phase B
        w("**Phase B, per run over the seed set: BR / B0 / B1 / B2 means; ratios of means.**")
        w("")
        w("| run ID | quantity | n | BR | B0 | B1 | B2 | B2/B0 | B1/B0 | B2/BR |")
        w("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|")
        for c in campaigns:
            path = c["configurations"][configuration]["path"]
            for q, label in (("iterations", "iterations"), ("evaluations of the model set", "evaluations ε"),
                             ("node calls per evaluation", "node calls / evaluation ρ"), ("node calls per run", "node calls / run R")):
                r = path[q]
                spec = ".3f" if q in ("iterations", "node calls per evaluation") else ".1f"
                w(f"| `{c['run_id']}` | {label} | {r['n']} | " + " | ".join(fmt(r[a], spec) for a in PHASE_B_ARMS)
                  + f" | {fmt(ratio(r['B2'], r['B0']))} | {fmt(ratio(r['B1'], r['B0']))} | {fmt(ratio(r['B2'], r['BR']))} |")
        w("")
        w("*Cost against both anchors* (solve-phase node calls summed over the set; the tally's table):")
        w("")
        w("| run ID | set | n | BR→B0 | B2/B0 | B2/BR |")
        w("|---|---|---:|---:|---:|---:|")
        for c in campaigns:
            for r in c["configurations"][configuration]["anchors"]:
                w(f"| `{c['run_id']}` | {r['set']} | {r['n']} | {fmt(r['reference_to_base'])} | {fmt(r['partition_to_base'])} | {fmt(r['partition_to_reference'])} |")
        w("")
        # rules
        w("**Rules.**")
        w("")
        w("| run ID | A1 (declared pair: median / p90 ratio, verdict) | A2 runs with a component ≥ τ | A1 note | B1 judged pair: n, objf median / p90, verdict, hops (seeds) |")
        w("|---|---|---:|---|---|")
        for c in campaigns:
            cc = c["configurations"][configuration]
            acc = cc["accuracy"]
            ref = acc["reference"]
            key = f"A2_over_{ref}"
            a1 = f"A2/{ref}: {fmt(acc.get(key + '_median'))} / {fmt(acc.get(key + '_p90'))}, {acc.get(key + '_verdict')}"
            b1 = "; ".join(
                f"{r['pair'].split(' (')[0]}: n {r['n']}, {fmt(r['r_median'], '.3e')} / {fmt(r['r_p90'], '.3e')}, "
                f"**{r['verdict']}**, {r['hops']} hops ({r['hop_seeds']})"
                for r in cc["rungs"]
            )
            w(f"| `{c['run_id']}` | {a1} | {cc['above_tau'] if cc['above_tau'] is not None else '—'} | {acc.get('note', '')} | {b1} |")
        w("")
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("run_ids", nargs="+", help="run IDs (folders under runs/), in column order")
    parser.add_argument("--output", type=Path, default=None, help="also write the rendering here")
    args = parser.parse_args(argv)
    commit = subprocess.run(["git", "rev-parse", "--short=8", "HEAD"], cwd=HERE, capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain", "--", "."], cwd=HERE, capture_output=True, text=True).stdout.strip()
    try:
        campaigns = [read_campaign(r) for r in args.run_ids]
    except (ComparisonError, recount.RecountError) as e:
        print(f"refused: {e}")
        return 1
    text = render(campaigns, commit + (" (dirty)" if dirty else ""))
    print(text, end="")
    if args.output:
        args.output.write_text(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
