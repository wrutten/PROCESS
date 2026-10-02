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

Every number above is read, none is derived beyond a ratio of two printed means.

**Three tables on where the arms end** (added 2026-10-02 for the four-campaign
comparison, test set {census, whole write set} × τ {1e-6, 1e-8}).  They are
derived from the records' stored state, not read from a stage record, and every
statistic is declared here before its output was read:

* **The relative difference** of two numbers ``a``, ``b`` is ``0`` when ``a == b``
  and otherwise ``|a - b| / max(|a|, |b|)`` (the definition of
  ``arch_surgery/st_stall_mechanism/optimiser_path_split.py``'s ``rel``); a NaN
  on either side, or a non-numeric component (``none``, ``b``) that differs, or an
  array whose shape differs, gives ``inf``.  A component's relative difference is
  the largest over its elements (``af``, ``a``, ``l``).  A state's *largest
  relative difference* is the largest over its components, and the component
  that attains it is its *worst component* (first in sorted name order on a tie).
* **Bit-identical** means every component of ``y_exit.json``'s ``state`` equal as
  stored (the JSON values compared, hex strings included), and the same set of
  component names.  A component present on one side only counts as differing,
  with relative difference ``inf``.
* **Phase A, same fixed point** (per configuration and run ID): the pairs
  partitioned against flat (``A2``/``A1`` on ``tok`` and ``lad``, ``A2``/``A0`` on
  ``st``) and flat against reference (``A0``/``AR``), seed by seed over the 25
  displaced entries (seeds 1-25), records with ``status == ok`` on both sides
  only (the denominator is printed).  Printed: the starts whose exit states are
  bit-identical; over the rest, the number of differing components (median,
  max), the largest relative difference (median, max), and the worst component
  that occurs most often over those starts (with its count; ties broken by name).
* **Phase A, same arm across settings** (per configuration, arm and unordered
  pair of run IDs, in the order given): seed by seed, the arm's exit state under
  one run ID against the other's; printed: the starts whose entries
  (``y_entry.json``'s ``state``) are bit-identical, the starts whose exit states
  are bit-identical, and the largest relative difference of the exit state
  (median, max over the starts).
* **Phase B, where the partitioned arm ends** (per configuration and run ID):
  ``B2`` against ``B1`` on ``tok`` and ``lad``, ``B2`` against ``B0`` on ``st``,
  over the starts (seeds 0-24) both arms accepted (``status == ok`` and
  ``mfile.ifail == 1``).  Printed: n; the largest relative difference over the
  iteration variables of the final design (``exact.xcs``, hex), median and max,
  the number of starts above 10 % (strictly), and the variable most often the
  worst (per start the first in ``ixc`` order on a tie); the relative difference of the objective (``exact.norm_objf``), median
  and max, and the starts on which it is exactly 0.

Medians are ``statistics.median`` (the mean of the two middle values for an even
count).  A stage record stamped with a run ID other than its folder's is refused; one with
no stamp (made before the run-ID layout) is read as its folder's and said so.
Records are read through :func:`paper_cells_recount.read_record`, which applies
the arm-name translation for records made before 2026-09-15 (trap T16) to the
record's own arm field, never to a directory name.

Usage::

    python compare_campaigns.py census_tau1e-08 write_set_tau1e-06 write_set_tau1e-08 census_tau1e-06 \
        [--output campaign_comparison.md]

Written for the V5 campaign under the whole write set at τ = 1e-8 (2026-10-02),
to put it beside the two campaigns already on disk; the three end-state tables
added for the campaign under the census set at τ = 1e-6 (the same day).
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
import re
import statistics
import subprocess
import sys
from collections import Counter
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
# end states (the three tables declared in the module docstring)
# --------------------------------------------------------------------------

INF = math.inf
SAME_FIXED_POINT_PAIRS = {  # (arm, against)
    "large_tokamak_nof": (("A2", "A1"), ("A0", "AR")),
    "low_aspect_ratio_DEMO": (("A2", "A1"), ("A0", "AR")),
    "st_regression": (("A2", "A0"), ("A0", "AR")),
}
PARTITIONED_AGAINST = {"large_tokamak_nof": "B1", "low_aspect_ratio_DEMO": "B1", "st_regression": "B0"}


def rel(a: float, b: float) -> float:
    """The declared relative difference: 0 if equal, else |a-b|/max(|a|,|b|); NaN gives inf."""
    if a == b:
        return 0.0
    if math.isnan(a) or math.isnan(b):
        return INF
    d = max(abs(a), abs(b))
    return abs(a - b) / d if d else INF


def numbers_of(value: dict[str, Any]) -> tuple[tuple[int, ...], list[float]] | None:
    """``(shape, elements)`` of one stored component, or ``None`` when it is not numeric."""
    k = value.get("k")
    if k == "f":
        return (), [float.fromhex(value["hex"])]
    if k == "i":
        return (), [float(value["v"])]
    if k == "af":
        return tuple(value["shape"]), [float.fromhex(h) for h in value["hex"]]
    if k == "a":
        v = value["v"]
        flat = list(itertools.chain.from_iterable(v)) if v and isinstance(v[0], list) else list(v)
        if not all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in flat):
            return None
        return tuple(value["shape"]), [float(x) for x in flat]
    if k == "l":
        parts = [numbers_of(x) for x in value["v"]]
        if any(p is None or p[0] != () for p in parts):
            return None
        return (len(parts),), [p[1][0] for p in parts]  # type: ignore[index]
    return None


def component_rel(a: dict[str, Any], b: dict[str, Any]) -> float:
    if a == b:
        return 0.0
    na, nb = numbers_of(a), numbers_of(b)
    if na is None or nb is None or na[0] != nb[0] or len(na[1]) != len(nb[1]):
        return INF
    return max((rel(x, y) for x, y in zip(na[1], nb[1], strict=True)), default=0.0)


def compare_states(a: dict[str, Any], b: dict[str, Any]) -> tuple[int, float, str | None]:
    """``(components differing, largest relative difference, worst component)``; ``(0, 0, None)`` if bit-identical."""
    n = 0
    worst, worst_name = 0.0, None
    for name in sorted(set(a) | set(b)):
        if name in a and name in b and a[name] == b[name]:
            continue
        n += 1
        r = component_rel(a[name], b[name]) if name in a and name in b else INF
        if worst_name is None or r > worst:
            worst, worst_name = r, name
    return n, worst, worst_name


def state_of(directory: Path, name: str) -> dict[str, Any]:
    return json.loads((directory / name).read_text())["state"]


def directories_of(folder: Path, phase: str, configuration: str) -> dict[str, dict[int, tuple[Path, dict[str, Any]]]]:
    """``{arm: {seed: (directory, record)}}``, arm from the record (T16)."""
    out: dict[str, dict[int, tuple[Path, dict[str, Any]]]] = {}
    for path in sorted((folder / "campaign" / phase / configuration).glob("*/seed*/metrics.json")):
        record = recount.read_record(path)
        out.setdefault(record["campaign_arm"], {})[int(record["campaign_seed"])] = (path.parent, record)
    return out


def accepted(record: dict[str, Any]) -> bool:
    return record.get("status") == "ok" and (record.get("mfile") or {}).get("ifail") == 1.0


def med(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def most_common(names: list[str]) -> str:
    if not names:
        return "—"
    counts = Counter(names)
    top = max(counts.values())
    name = sorted(n for n, k in counts.items() if k == top)[0]
    return f"`{name}` ({top})"


def same_fixed_point(evaluation: dict[str, dict[int, tuple[Path, dict[str, Any]]]], arm: str, against: str) -> dict[str, Any]:
    seeds_ = sorted(s for s in set(evaluation.get(arm, {})) & set(evaluation.get(against, {}))
                    if evaluation[arm][s][1].get("status") == "ok" and evaluation[against][s][1].get("status") == "ok")
    identical, ndiff, worst, names = 0, [], [], []
    for s in seeds_:
        n, r, name = compare_states(state_of(evaluation[arm][s][0], "y_exit.json"), state_of(evaluation[against][s][0], "y_exit.json"))
        if n == 0:
            identical += 1
            continue
        ndiff.append(n)
        worst.append(r)
        names.append(name)
    return {"n": len(seeds_), "identical": identical, "ndiff": ndiff, "worst": worst, "worst_component": most_common(names)}


def across_settings(a: dict[int, tuple[Path, dict[str, Any]]], b: dict[int, tuple[Path, dict[str, Any]]]) -> dict[str, Any]:
    seeds_ = sorted(s for s in set(a) & set(b) if a[s][1].get("status") == "ok" and b[s][1].get("status") == "ok")
    entries, identical, worst = 0, 0, []
    for s in seeds_:
        if state_of(a[s][0], "y_entry.json") == state_of(b[s][0], "y_entry.json"):
            entries += 1
        n, r, _ = compare_states(state_of(a[s][0], "y_exit.json"), state_of(b[s][0], "y_exit.json"))
        identical += n == 0
        worst.append(r)
    return {"n": len(seeds_), "entries": entries, "identical": identical, "worst": worst}


def final_design(record: dict[str, Any]) -> tuple[list[float], float]:
    exact = record["exact"]
    return [float.fromhex(h) for h in exact["xcs"]], float.fromhex(exact["norm_objf"])


def where_partitioned_ends(optimisation: dict[str, dict[int, tuple[Path, dict[str, Any]]]], against: str) -> dict[str, Any]:
    b2, base = optimisation.get("B2", {}), optimisation.get(against, {})
    seeds_ = sorted(s for s in set(b2) & set(base) if accepted(b2[s][1]) and accepted(base[s][1]))
    x_worst, x_names, objf = [], [], []
    for s in seeds_:
        xa, fa = final_design(b2[s][1])
        xb, fb = final_design(base[s][1])
        names = b2[s][1].get("itvar_names") or []
        if len(xa) != len(xb):
            x_worst.append(INF)
            x_names.append("(design vectors of different length)")
        else:
            diffs = [rel(x, y) for x, y in zip(xa, xb, strict=True)]
            i = max(range(len(diffs)), key=lambda j: (diffs[j], -j))
            x_worst.append(diffs[i])
            x_names.append(names[i] if i < len(names) else str(i))
        objf.append(rel(fa, fb))
    return {
        "n": len(seeds_),
        "x_worst": x_worst,
        "above_10pc": sum(1 for v in x_worst if v > 0.1),
        "x_worst_variable": most_common(x_names),
        "objf": objf,
        "objf_zero": sum(1 for v in objf if v == 0.0),
    }


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
        evaluation = directories_of(folder, "evaluation", configuration)
        optimisation = directories_of(folder, "optimisation", configuration)
        c["evaluation_directories"] = evaluation
        c["same_fixed_point"] = {pair: same_fixed_point(evaluation, *pair) for pair in SAME_FIXED_POINT_PAIRS[configuration]}
        c["where_partitioned_ends"] = where_partitioned_ends(optimisation, PARTITIONED_AGAINST[configuration])
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
        render_end_states(campaigns, configuration, w)
    return "\n".join(out) + "\n"


def e(value: float | None) -> str:
    if value is None:
        return "—"
    return "inf" if value == INF else format(value, ".2e")


def render_end_states(campaigns: list[dict[str, Any]], configuration: str, w: Any) -> None:
    """The three end-state tables of one configuration (declared in the module docstring)."""
    w("**Phase A, same fixed point** (seed by seed over the 25 displaced entries; exit states, `y_exit.json`):")
    w("")
    w("| run ID | pair | n | bit-identical | differing components: median / max | largest relative difference: median / max | most often the worst component |")
    w("|---|---|---:|---:|---|---|---|")
    for c in campaigns:
        for (arm, against), r in c["configurations"][configuration]["same_fixed_point"].items():
            nd = f"{fmt(med(r['ndiff']), '.1f')} / {max(r['ndiff'])}" if r["ndiff"] else "—"
            wr = f"{e(med(r['worst']))} / {e(max(r['worst']))}" if r["worst"] else "—"
            w(f"| `{c['run_id']}` | {arm}/{against} | {r['n']} | {r['identical']} | {nd} | {wr} | {r['worst_component']} |")
    w("")
    w("**Phase A, same arm across settings** (seed by seed; entries `y_entry.json`, exit states `y_exit.json`):")
    w("")
    w("| arm | run ID | against run ID | n | entries bit-identical | exits bit-identical | largest relative difference of the exit: median / max |")
    w("|---|---|---|---:|---:|---:|---|")
    for arm in PHASE_A_ARMS:
        for ca, cb in itertools.combinations(campaigns, 2):
            da = ca["configurations"][configuration]["evaluation_directories"].get(arm)
            db = cb["configurations"][configuration]["evaluation_directories"].get(arm)
            if not da or not db:
                continue
            r = across_settings(da, db)
            wr = f"{e(med(r['worst']))} / {e(max(r['worst']))}" if r["worst"] else "—"
            w(f"| {arm} | `{ca['run_id']}` | `{cb['run_id']}` | {r['n']} | {r['entries']} | {r['identical']} | {wr} |")
    w("")
    against = PARTITIONED_AGAINST[configuration]
    w(f"**Phase B, where the partitioned arm ends: B2 against {against}** (the starts both arms accepted; final design `exact.xcs`, objective `exact.norm_objf`):")
    w("")
    w("| run ID | n | design: largest relative difference, median / max | starts above 10 % | most often the worst variable | objective: relative difference, median / max | objective identical |")
    w("|---|---:|---|---:|---|---|---:|")
    for c in campaigns:
        r = c["configurations"][configuration]["where_partitioned_ends"]
        xw = f"{e(med(r['x_worst']))} / {e(max(r['x_worst']))}" if r["x_worst"] else "—"
        ob = f"{e(med(r['objf']))} / {e(max(r['objf']))}" if r["objf"] else "—"
        w(f"| `{c['run_id']}` | {r['n']} | {xw} | {r['above_10pc']} | {r['x_worst_variable']} | {ob} | {r['objf_zero']} |")
    w("")


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
