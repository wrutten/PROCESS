#!/usr/bin/env python
"""A short, independent recount of exactly the paper's cells from the raw records.

V5 list item 10 replaces V4's second implementation (a 6 464-line recomputation
of every table) with **this**: the paper's cells — and only those — recounted
from the run records by code that shares nothing with the generator
(``harness/measurement/paper_tables.py``).  It imports no module of
``harness/``; it reads ``metrics.json`` files, the committed node map and the
per-run artifacts directly, and it parses the generator's rendered document
to put the two readings side by side with a mismatch count.

What is recounted, per configuration:

* **phase A** (``campaign/evaluation/<configuration>/<arm>/seedNNN``, seeds
  ≥ 1, ``status == "ok"``): each module row's mean sweeps per evaluation per
  arm — a module's sweeps are the census count every node of the module
  shares (``node_census.counted``; unequal counts refuse) — and, on the pair
  the plan publishes (``A1 → A2`` on a pulsed configuration, ``A0 → A2`` on a
  steady-state one, **D34**), the ratio of the means, the per-seed ratio's
  nearest-rank upper-middle median and its ``[min, max]``;
* **phase B** (``campaign/optimisation/…``): the one seed set (every arm
  ``status == "ok"`` and ``mfile.ifail == 1``), each arm's mean iterations
  summed over attempts and the ``B2/B0`` ratio statistics; each module row's
  mean sweeps per optimisation with the exit audit's one sweep per node
  subtracted (``node_census.per_node_counted`` − 1), and the same statistics;
* **per-arm success**: starts offered and accepted per arm.

**Arm names.**  A record made before the renaming of 2026-09-15 (no
``arm_naming`` stamp) spells its arm in the old scheme (trap T16); this
script carries its own three-entry translation, ``RECORDED_ARM_NAMES``, and
applies it to the record's ``campaign_arm`` field — never to the directory
name.  It is deliberately a copy of the harness's table, not an import.

Usage
-----
    python paper_cells_recount.py --runs <runs/run ID folder> --document <paper_tables.md>

Exit status 0 when every cell agrees, 1 otherwise; the mismatch count is the
last line printed.  Written by task **A98 (v5-reporting-trim)**, 2026-09-29.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
DATA = HERE / "harness" / "data"

#: The old spelling → today's, for records without an ``arm_naming`` stamp.
RECORDED_ARM_NAMES = {"A0p": "A1", "A1": "A2", "B3": "B2"}
ARM_NAMING_FIELD = "arm_naming"

CONFIGURATIONS = ("large_tokamak_nof", "low_aspect_ratio_DEMO", "st_regression")
SHORT = {"large_tokamak_nof": "tok", "low_aspect_ratio_DEMO": "lad", "st_regression": "st"}
PULSED = {"large_tokamak_nof": True, "low_aspect_ratio_DEMO": True, "st_regression": False}
PHASE_A_ARMS = ("AR", "A0", "A1", "A2")
PHASE_B_ARMS = ("BR", "B0", "B1", "B2")
ROWS = (("M1", ("M1",)), ("M2", ("M2",)), ("M3", ("M3",)), ("Feedforward", ("PULSE", "FF")), ("Post-processing", ("once per run",)))


class RecountError(RuntimeError):
    pass


# --------------------------------------------------------------------------
# reading
# --------------------------------------------------------------------------


def read_record(path: Path) -> dict[str, Any]:
    record = json.loads(path.read_text())
    if record.get(ARM_NAMING_FIELD) is None:
        record["campaign_arm"] = RECORDED_ARM_NAMES.get(record["campaign_arm"], record["campaign_arm"])
    return record


def records_of(runs: Path, stage: str, configuration: str) -> dict[str, dict[int, dict[str, Any]]]:
    """``{arm: {seed: record}}`` under ``campaign/<stage>/<configuration>/``, arm from the record."""
    out: dict[str, dict[int, dict[str, Any]]] = {}
    root = runs / "campaign" / stage / configuration
    for path in sorted(root.glob("*/seed*/metrics.json")):
        record = read_record(path)
        out.setdefault(record["campaign_arm"], {})[int(record["campaign_seed"])] = record
    return out


def grouping(configuration: str, records: list[dict[str, Any]], census_key: str) -> list[tuple[str, list[str]]]:
    node_map = json.loads((DATA / "dsm_node_map.json").read_text())["nodes"]
    artifacts = sorted({Path(str(r["per_run_artifact"])).name for r in records if r.get("per_run_artifact")})
    once: set[str] | None = None
    for name in artifacts:
        nodes = set(json.loads((DATA / name).read_text())["post_solve_nodes"])
        if once is not None and nodes != once:
            raise RecountError(f"{configuration}: per-run artifacts {artifacts} disagree on the once-per-run set")
        once = nodes
    once = once or set()
    seen: set[str] = set()
    for r in records:
        seen |= set((r.get("node_census") or {}).get(census_key) or {})
    groups: dict[str, list[str]] = {}
    for node in sorted(seen):
        module = "once per run" if node in once else node_map[node]["module"]
        groups.setdefault(module, []).append(node)
    return sorted(groups.items())


def sweeps_of(counts: dict[str, int], groups: list[tuple[str, list[str]]], where: str) -> dict[str, float]:
    out = {}
    for group, nodes in groups:
        values = {int(counts.get(n, 0)) for n in nodes}
        if len(values) != 1:
            raise RecountError(f"{where}: group {group} executed its nodes unequally: {values}")
        out[group] = float(values.pop())
    return out


def row_value(sweeps: dict[str, float], members: tuple[str, ...], where: str) -> float | None:
    present = sorted({sweeps[g] for g in members if g in sweeps})
    if not present:
        return None
    if len(present) != 1:
        raise RecountError(f"{where}: groups {members} swept {present} times")
    return present[0]


def mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def median(values: list[float]) -> float | None:
    if not values:
        return None
    return sorted(values)[len(values) // 2]


def ratio_stats(base: list[float], arm: list[float]) -> dict[str, float | None]:
    per_seed = [b / a for a, b in zip(base, arm) if a]
    return {
        "pooled": (sum(arm) / sum(base)) if sum(base) else None,
        "median": median(per_seed),
        "min": min(per_seed) if per_seed else None,
        "max": max(per_seed) if per_seed else None,
    }


# --------------------------------------------------------------------------
# the recount
# --------------------------------------------------------------------------


def recount_phase_a(runs: Path, configuration: str) -> dict[str, Any]:
    by_arm = records_of(runs, "evaluation", configuration)
    finished = {a: {s: r for s, r in rows.items() if s >= 1 and r.get("status") == "ok"} for a, rows in by_arm.items()}
    every = [r for rows in finished.values() for r in rows.values()]
    groups = grouping(configuration, every, "counted")
    sweeps = {
        a: {s: sweeps_of(r["node_census"]["counted"], groups, f"{configuration}/{a}/seed{s}") for s, r in rows.items()}
        for a, rows in finished.items()
    }
    base, arm = ("A1", "A2") if PULSED[configuration] else ("A0", "A2")
    paired = sorted(set(sweeps.get(base, {})) & set(sweeps.get(arm, {})))
    cells: dict[str, Any] = {"n": {a: len(rows) for a, rows in finished.items()}, "pair": (base, arm), "rows": {}}
    for label, members in ROWS:
        row: dict[str, Any] = {}
        for a in PHASE_A_ARMS:
            values = [v for s, sw in sorted(sweeps.get(a, {}).items()) if (v := row_value(sw, members, f"{a} seed {s}")) is not None]
            row[a] = mean(values)
        left = [row_value(sweeps[base][s], members, "pair") for s in paired]
        right = [row_value(sweeps[arm][s], members, "pair") for s in paired]
        row["ratio"] = None if any(v is None for v in left + right) or not paired else ratio_stats(left, right)
        cells["rows"][label] = row
    return cells


def recount_phase_b(runs: Path, configuration: str) -> dict[str, Any]:
    by_arm = records_of(runs, "optimisation", configuration)
    seeds = sorted(set().union(*(set(rows) for rows in by_arm.values())))

    def accepted(r: dict[str, Any]) -> bool:
        return r.get("status") == "ok" and (r.get("mfile") or {}).get("ifail") == 1.0

    converged = [s for s in seeds if all(accepted(by_arm[a].get(s, {})) for a in by_arm)]
    base, arm = "B0", "B2"

    def iterations(r: dict[str, Any]) -> float | None:
        values = [a.get("n_iterations") for a in r.get("attempts") or []]
        return None if not values or any(v is None for v in values) else float(sum(values))

    it_row: dict[str, Any] = {"n": len(converged)}
    for a in PHASE_B_ARMS:
        it_row[a] = mean([v for s in converged if a in by_arm and (v := iterations(by_arm[a][s])) is not None])
    it_row["ratio"] = ratio_stats([iterations(by_arm[base][s]) for s in converged], [iterations(by_arm[arm][s]) for s in converged])

    records = [by_arm[a][s] for a in by_arm for s in converged]
    groups = grouping(configuration, records, "per_node_counted")

    def minus_audit(r: dict[str, Any]) -> dict[str, int]:
        counted = r["node_census"]["per_node_counted"]
        if int(r["node_census"].get("audit_node_calls", -1)) != len(counted):
            raise RecountError(f"{configuration}: audit_node_calls is not one sweep of every counted node")
        return {n: int(v) - 1 for n, v in counted.items()}

    sweeps = {a: {s: sweeps_of(minus_audit(by_arm[a][s]), groups, f"{a} seed {s}") for s in converged} for a in by_arm}
    module_rows: dict[str, Any] = {}
    for label, members in ROWS:
        row: dict[str, Any] = {}
        for a in PHASE_B_ARMS:
            row[a] = mean([v for s in converged if a in sweeps and (v := row_value(sweeps[a][s], members, a)) is not None])
        left = [row_value(sweeps[base][s], members, "pair") for s in converged]
        right = [row_value(sweeps[arm][s], members, "pair") for s in converged]
        row["ratio"] = None if any(v is None for v in left + right) or not converged else ratio_stats(left, right)
        module_rows[label] = row
    success = {a: {"offered": len(rows), "accepted": sum(1 for r in rows.values() if accepted(r))} for a, rows in by_arm.items()}
    return {"iterations": it_row, "modules": module_rows, "success": success}


# --------------------------------------------------------------------------
# the rendered document, parsed
# --------------------------------------------------------------------------


def fmt(value: float | None, places: int) -> str:
    return "—" if value is None else f"{float(value):.{places}f}"


def fmt_ratio(stats: dict[str, Any] | None) -> tuple[str, str]:
    if not stats or stats.get("pooled") is None:
        return "—", "—"
    return fmt(stats["pooled"], 2), f"{fmt(stats['median'], 2)} [{fmt(stats['min'], 2)}, {fmt(stats['max'], 2)}]"


def parse_document(document: Path) -> dict[str, dict[str, list[str]]]:
    """``{section: {row label: cells}}`` for the four tables the recount covers."""
    text = document.read_text().splitlines()
    sections: dict[str, dict[str, list[str]]] = {}
    current: str | None = None
    block: str | None = None
    wanted = {
        "tab:phaseA_results": "phase_a",
        "tab:phaseB_iterations": "phase_b_iterations",
        "tab:phaseB_results": "phase_b_modules",
        "per-arm success": "success",
    }
    for line in text:
        if line.startswith("### "):
            current = next((v for k, v in wanted.items() if k in line), None)
            block = None
            continue
        if current is None:
            continue
        m = re.match(r"\*\*`(\w+)`\*\*", line)
        if m:
            block = m.group(1)
            continue
        if line.startswith("|") and not line.startswith("|---") and not line.startswith("| Module") and not line.startswith("| Configuration") and not line.startswith("| arm"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            key = f"{block}:{cells[0]}" if current != "phase_b_iterations" else cells[0].strip("`")
            sections.setdefault(current, {})[key] = cells[1:]
    return sections


# --------------------------------------------------------------------------
# side by side
# --------------------------------------------------------------------------


def compare(runs: Path, document: Path) -> int:
    rendered = parse_document(document)
    rows: list[tuple[str, str, str]] = []
    for configuration in CONFIGURATIONS:
        short = SHORT[configuration]
        a = recount_phase_a(runs, configuration)
        for label, row in a["rows"].items():
            mine = [fmt(row[x], 1) if x != "A2" or label not in ("Feedforward", "Post-processing") or row[x] is None else str(int(row[x])) for x in PHASE_A_ARMS]
            mine += list(fmt_ratio(row["ratio"]))
            theirs = rendered.get("phase_a", {}).get(f"{short}:{label}", [])
            rows.append((f"A {short} {label}", " | ".join(mine), " | ".join(theirs)))
        b = recount_phase_b(runs, configuration)
        it = b["iterations"]
        mine = [str(it["n"])] + [fmt(it[x], 1) for x in PHASE_B_ARMS] + list(fmt_ratio(it["ratio"]))
        rows.append((f"B {short} iterations", " | ".join(mine), " | ".join(rendered.get("phase_b_iterations", {}).get(short, []))))
        for label, row in b["modules"].items():
            mine = [fmt(row[x], 0) for x in PHASE_B_ARMS] + list(fmt_ratio(row["ratio"]))
            rows.append((f"B {short} {label}", " | ".join(mine), " | ".join(rendered.get("phase_b_modules", {}).get(f"{short}:{label}", []))))
        for arm, counts in sorted(b["success"].items()):
            theirs = rendered.get("success", {}).get(f"{short}:{arm}", [])[:2]
            rows.append((f"success {short} {arm} offered|accepted", f"{counts['offered']} | {counts['accepted']}", " | ".join(theirs)))
    mismatched = 0
    width = max(len(r[0]) for r in rows)
    print(f"{'cell':<{width}}  {'recount':<48}  rendered")
    for key, mine, theirs in rows:
        ok = mine == theirs
        mismatched += not ok
        print(f"{key:<{width}}  {mine:<48}  {theirs}{'' if ok else '   <-- MISMATCH'}")
    print(f"\n{len(rows)} cell row(s) compared, {mismatched} mismatched")
    return 1 if mismatched else 0


#: The run ID of the declared default campaign, whose folder holds the
#: records ``paper_tables.md`` is of (``harness/core/config.DEFAULT_RUN_ID``,
#: task A107 (v5-campaign-settings-keys)).  Written here rather than imported,
#: as everything else in this script is: it imports no module of the harness.
DEFAULT_RUN_ID = "census_tau1e-08"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--runs",
        type=Path,
        default=HERE / "runs" / DEFAULT_RUN_ID,
        help="the run ID's folder (campaign/ under it); the declared default "
        "campaign's, runs/" + DEFAULT_RUN_ID + "/, unless named",
    )
    parser.add_argument("--document", type=Path, default=HERE / "paper_tables.md", help="the generator's rendered file")
    args = parser.parse_args(argv)
    if not (args.runs / "campaign").exists():
        print(f"no campaign records under {args.runs}; nothing to recount")
        return 1
    if not args.document.exists():
        print(f"{args.document} does not exist; render it first (--paper-tables write)")
        return 1
    return compare(args.runs, args.document)


if __name__ == "__main__":
    sys.exit(main())
