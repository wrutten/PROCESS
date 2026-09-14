#!/usr/bin/env python
"""Survey the harness package: size, structure, reach, and cost per press.

Read-only.  Starts no PROCESS run.  Written for the simplification survey
(task A68 (harness-simplification-survey), 2026-09-14) so that every number
that survey's report cites is produced by a committed script (protocol §15).

What it measures, in the order it prints:

1. **lines** — per module and per subpackage: total, blank, comment-only,
   docstring, code.  ``ast`` decides what is a docstring; a ``#`` line is a
   comment.
2. **imports** — the intra-package import graph, and which modules nothing in
   the package, the runner, ``chain.py`` or the copy's gates import.
3. **definitions** — every module-level function and class, with the count of
   *other* sites in the package (plus the top-level scripts and
   ``PROCESS/copy_gates.py``) that mention its name.  Zero mentions outside the
   definition is a candidate for a path nothing reaches; the report reads each
   candidate before calling it dead.
4. **duplicates** — function names defined in more than one module, and
   functions whose bodies are identical after normalising away their name.
5. **registry** — every gate and measurement stage: teeth, ``needs_runs``,
   ``runs_under``, ``reads_from``, ``reads_records``.  Imports the package;
   builds nothing.
6. **records** — the run-record schema against its readers: for every declared
   field, how many source sites outside ``records.py`` name it.
7. **runs per press** — from a directory of relocated gate records (the main
   checkout's ``idf_probe/runs/A65_runs/gates``, read-only): run records per
   gate directory, their ``tree_git_head`` values, their run kinds and the sum
   of ``wall_s`` (context only — I-10, T5).
8. **flags** — every ``--flag`` of ``experiment_runner.py`` against the
   documents that mention it (README, the two plans, the archived reports).
9. **prose** — docstring and comment share per module; paragraphs of the
   README that also appear in the harness plan.

Usage::

    python harness_survey.py [--records DIR] [--json OUT]
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import sys
import tokenize
from collections import Counter, defaultdict
from io import StringIO
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
HARNESS = HERE / "harness"
REPO = HERE.parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

TOP_LEVEL_SCRIPTS = (
    HERE / "experiment_runner.py",
    HERE / "PROCESS_diff.py",
    HERE / "run_stamp_survey.py",
    HERE / "PROCESS" / "copy_gates.py",
)

#: The relocated gate records of the latest merged task, in whichever checkout
#: this script runs in.  A task worktree holds none; point ``--records`` at the
#: main checkout's copy (read-only) instead.
DEFAULT_RECORDS = REPO / "arch_surgery" / "idf_probe" / "runs" / "A65_runs" / "gates"

DOCS = {
    "README": HARNESS / "README.md",
    "EXPERIMENT_PLAN": HERE / "EXPERIMENT_PLAN.md",
    "HARNESS_PLAN": REPO / "arch_surgery" / "docs" / "plans"
    / "V4_HARNESS_IMPLEMENTATION_PLAN.md",
    "IMPROVEMENT_LIST": REPO / "arch_surgery" / "docs" / "plans"
    / "V4_IMPROVEMENT_LIST.md",
    "ASSESSMENT": REPO / "arch_surgery" / "docs" / "reports"
    / "V4_IMPLEMENTATION_ASSESSMENT.md",
}
ARCHIVED_REPORTS = sorted(
    (REPO / "arch_surgery" / "docs" / "reports" / "deprecated").glob("A[4-6][0-9]_*.md")
)


# --------------------------------------------------------------------------
# 1. lines
# --------------------------------------------------------------------------


def harness_modules() -> list[Path]:
    return sorted(p for p in HARNESS.rglob("*.py"))


def module_label(path: Path) -> str:
    return str(path.relative_to(HERE))


def line_census(path: Path) -> dict[str, int]:
    source = path.read_text()
    lines = source.splitlines()
    tree = ast.parse(source)
    doc_lines: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.body and isinstance(node.body[0], ast.Expr) and isinstance(
                getattr(node.body[0], "value", None), ast.Constant
            ) and isinstance(node.body[0].value.value, str):
                d = node.body[0]
                doc_lines.update(range(d.lineno, (d.end_lineno or d.lineno) + 1))
    comment_lines: set[int] = set()
    try:
        for tok in tokenize.generate_tokens(StringIO(source).readline):
            if tok.type == tokenize.COMMENT:
                comment_lines.add(tok.start[0])
    except tokenize.TokenError:
        pass
    blank = sum(1 for i, l in enumerate(lines, 1) if not l.strip() and i not in doc_lines)
    comment_only = sum(
        1 for i, l in enumerate(lines, 1)
        if i in comment_lines and l.strip().startswith("#") and i not in doc_lines
    )
    doc = len(doc_lines)
    # lines that lie wholly inside a string literal other than a docstring:
    # the refusal messages, captions and printed sentences
    string_lines: set[int] = set()
    try:
        for tok in tokenize.generate_tokens(StringIO(source).readline):
            if tok.type == tokenize.STRING and tok.start[0] not in doc_lines:
                for i in range(tok.start[0], tok.end[0] + 1):
                    if lines[i - 1].strip().startswith(('"', "'", 'f"', "f'", 'r"', "r'")):
                        string_lines.add(i)
    except tokenize.TokenError:
        pass
    code = len(lines) - blank - comment_only - doc
    return {"total": len(lines), "blank": blank, "comment": comment_only,
            "docstring": doc, "code": code, "message": len(string_lines - doc_lines)}


def lines_section() -> dict[str, Any]:
    per_module = {}
    for p in harness_modules():
        per_module[module_label(p)] = line_census(p)
    for p in TOP_LEVEL_SCRIPTS:
        per_module[module_label(p)] = line_census(p)
    per_sub: dict[str, Counter] = defaultdict(Counter)
    for label, c in per_module.items():
        parts = Path(label).parts
        sub = parts[1] if parts[0] == "harness" and len(parts) > 2 else (
            "harness (top)" if parts[0] == "harness" else "top-level scripts"
        )
        per_sub[sub].update(c)
    total = Counter()
    for c in per_sub.values():
        total.update(c)
    return {"per_module": per_module, "per_subpackage": {k: dict(v) for k, v in per_sub.items()},
            "total": dict(total),
            "gates_py_sections": sections_of(HARNESS / "gates" / "gates.py")}


def sections_of(path: Path) -> list[dict[str, Any]]:
    """The blocks of a module separated by ``# ----`` rule comments.

    Each block is named by the first titled comment line after its rule, and
    sized in lines.  This is how ``gates.py`` marks its gates and stages.
    """
    lines = path.read_text().splitlines()
    rules = [i for i, l in enumerate(lines, 1) if l.startswith("# ----")]
    starts = []
    for i in rules:
        if starts and i - starts[-1][0] <= 2:
            continue
        starts.append((i, None))
    out = []
    for n, (start, _) in enumerate(starts):
        end = starts[n + 1][0] - 1 if n + 1 < len(starts) else len(lines)
        title = ""
        for l in lines[start:min(start + 6, end)]:
            body = l[1:].strip()
            if body and not body.startswith("---"):
                title = body
                break
        out.append({"start": start, "end": end, "lines": end - start + 1, "title": title[:90]})
    return out


# --------------------------------------------------------------------------
# 2. imports
# --------------------------------------------------------------------------


def _module_name(path: Path) -> str:
    rel = path.relative_to(HERE).with_suffix("")
    return ".".join(rel.parts)


def imports_of(path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name.startswith("harness"):
                    found.add(a.name)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if node.level:
                # relative import inside the package: resolve against the file
                base = _module_name(path).split(".")[: -node.level]
                mod = ".".join(base + ([mod] if mod else []))
            if mod.startswith("harness"):
                for a in node.names:
                    cand = f"{mod}.{a.name}"
                    if (HERE / Path(*cand.split("."))).with_suffix(".py").exists():
                        found.add(cand)
                    else:
                        found.add(mod)
    return found


def imports_section() -> dict[str, Any]:
    graph: dict[str, list[str]] = {}
    all_mods = {_module_name(p): p for p in harness_modules()}
    for name, p in all_mods.items():
        graph[name] = sorted(i for i in imports_of(p) if i in all_mods and i != name)
    for p in TOP_LEVEL_SCRIPTS:
        graph[module_label(p)] = sorted(i for i in imports_of(p) if i in all_mods)
    imported_by: dict[str, set[str]] = defaultdict(set)
    for src, targets in graph.items():
        for t in targets:
            imported_by[t].add(src)
    # a subpackage __init__ importing a module counts too
    never_imported = sorted(
        m for m in all_mods
        if not imported_by.get(m) and not m.endswith("__init__")
    )
    return {"graph": graph,
            "imported_by": {k: sorted(v) for k, v in imported_by.items()},
            "never_imported": never_imported}


# --------------------------------------------------------------------------
# 3. definitions and their reach
# --------------------------------------------------------------------------


def definitions_section() -> dict[str, Any]:
    sources: dict[str, str] = {}
    for p in list(harness_modules()) + list(TOP_LEVEL_SCRIPTS):
        sources[module_label(p)] = p.read_text()
    word = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
    tokens_per_file: dict[str, Counter] = {}
    for label, src in sources.items():
        # strip docstrings and comments so a mention in prose is not a reference
        try:
            tree = ast.parse(src)
        except SyntaxError:
            tokens_per_file[label] = Counter(word.findall(src))
            continue
        doc_spans = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.body and isinstance(node.body[0], ast.Expr) and isinstance(
                    getattr(node.body[0], "value", None), ast.Constant
                ) and isinstance(node.body[0].value.value, str):
                    d = node.body[0]
                    doc_spans.append((d.lineno, d.end_lineno or d.lineno))
        lines = src.splitlines()
        kept = []
        for i, l in enumerate(lines, 1):
            if any(a <= i <= b for a, b in doc_spans):
                continue
            kept.append(l.split("#", 1)[0] if "#" in l and not l.strip().startswith('"') else l)
        tokens_per_file[label] = Counter(word.findall("\n".join(kept)))
    defs: list[dict[str, Any]] = []
    for p in harness_modules():
        label = module_label(p)
        tree = ast.parse(sources[label])
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = node.name
                own = tokens_per_file[label][name]
                others = sum(c[name] for l, c in tokens_per_file.items() if l != label)
                # references inside its own module beyond the definition line itself
                own_refs = own - 1
                defs.append({
                    "module": label, "name": name,
                    "kind": "class" if isinstance(node, ast.ClassDef) else "function",
                    "lines": (node.end_lineno or node.lineno) - node.lineno + 1,
                    "refs_in_own_module": own_refs,
                    "refs_elsewhere": others,
                    "private": name.startswith("_"),
                    "lineno": node.lineno,
                })
    unreferenced = [d for d in defs if d["refs_elsewhere"] == 0 and d["refs_in_own_module"] == 0
                    and d["name"] not in ("main",) and not d["name"].startswith("__")]
    private_only_own = [d for d in defs if d["refs_elsewhere"] == 0 and not d["private"]
                        and d["name"] != "main"]
    return {
        "n_definitions": len(defs),
        "definitions": defs,
        "unreferenced": unreferenced,
        "public_but_module_local": private_only_own,
    }


# --------------------------------------------------------------------------
# 4. duplicates
# --------------------------------------------------------------------------


class _Normalise(ast.NodeTransformer):
    def visit_FunctionDef(self, node):
        node.name = "f"
        node.body = [b for b in node.body if not (
            isinstance(b, ast.Expr) and isinstance(getattr(b, "value", None), ast.Constant)
            and isinstance(b.value.value, str))]
        self.generic_visit(node)
        return node


def duplicates_section() -> dict[str, Any]:
    by_name: dict[str, list[str]] = defaultdict(list)
    by_body: dict[str, list[tuple[str, str, int]]] = defaultdict(list)
    for p in list(harness_modules()) + list(TOP_LEVEL_SCRIPTS):
        label = module_label(p)
        tree = ast.parse(p.read_text())
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                by_name[node.name].append(label)
                n = (node.end_lineno or node.lineno) - node.lineno + 1
                if n < 6:
                    continue
                clone = _Normalise().visit(ast.parse(ast.unparse(node)))
                key = hashlib.sha256(ast.dump(clone).encode()).hexdigest()[:12]
                by_body[key].append((label, node.name, n))
    same_name = {k: v for k, v in by_name.items() if len(v) > 1 and not k.startswith("__")}
    same_body = [v for v in by_body.values() if len(v) > 1]
    return {"same_name": same_name, "same_body": same_body}


# --------------------------------------------------------------------------
# 5. registry
# --------------------------------------------------------------------------


def registry_section() -> dict[str, Any]:
    from harness.core.config import default_campaign
    from harness.gates import registry as gates_mod

    campaign = default_campaign()
    reg = gates_mod.registry(campaign)
    rows = []
    for name, entry in reg.items():
        row = {
            "name": name,
            "kind": getattr(entry, "kind", "?"),
            "plan_name": getattr(entry, "plan_name", None),
            "needs_runs": getattr(entry, "needs_runs", None),
            "n_teeth": len(getattr(entry, "teeth", ()) or ()),
            "runs_under": list(getattr(entry, "runs_under", ()) or ()),
            "reads_from": list(getattr(entry, "reads_from", ()) or ()),
            "reads_records": list(getattr(entry, "reads_records", ()) or ()),
            "guarded_by": getattr(entry, "guarded_by", None),
            "binds": getattr(entry, "binds", getattr(entry, "reports", "")),
            "teeth": [t.name for t in getattr(entry, "teeth", ()) or ()],
        }
        rows.append(row)
    gates = [r for r in rows if r["kind"] == "gate"]
    measurements = [r for r in rows if r["kind"] != "gate"]
    order = gates_mod.ordered_gate_names(campaign)
    return {
        "n_gates": len(gates), "n_measurements": len(measurements),
        "n_teeth": sum(r["n_teeth"] for r in gates),
        "gates_needing_runs": sorted(r["name"] for r in gates if r["needs_runs"]),
        "gates_without_runs": sorted(r["name"] for r in gates if not r["needs_runs"]),
        "gate_all_order": order,
        "rows": rows,
    }


# --------------------------------------------------------------------------
# 6. records schema vs readers
# --------------------------------------------------------------------------


def records_section() -> dict[str, Any]:
    from harness.core import records

    readers: dict[str, str] = {}
    for p in list(harness_modules()) + list(TOP_LEVEL_SCRIPTS):
        if p.name == "records.py" and p.parent.name == "core":
            continue
        readers[module_label(p)] = p.read_text()
    rows = []
    for f in records.SCHEMA:
        name = f.name
        head = name.split(".")[0]
        leaf = name.split(".")[-1]
        pat_leaf = re.compile(r"(?<![A-Za-z0-9_])" + re.escape(leaf) + r"(?![A-Za-z0-9_])")
        pat_exact = re.compile(r"(?<![A-Za-z0-9_.])" + re.escape(name) + r"(?![A-Za-z0-9_])")
        pat_head = re.compile(r"(?<![A-Za-z0-9_])" + re.escape(head) + r"(?![A-Za-z0-9_])")
        exact_sites = {l: len(pat_exact.findall(s)) for l, s in readers.items()}
        head_sites = {l: len(pat_head.findall(s)) for l, s in readers.items()}
        leaf_sites = {l: len(pat_leaf.findall(s)) for l, s in readers.items()}
        rows.append({
            "leaf_mentions": sum(leaf_sites.values()),
            "leaf_modules": sorted(l for l, n in leaf_sites.items() if n),
            "field": name, "phases": "".join(f.phases), "when": f.when,
            "exact_mentions": sum(exact_sites.values()),
            "exact_modules": sorted(l for l, n in exact_sites.items() if n),
            "head_mentions": sum(head_sites.values()),
            "head_modules": sorted(l for l, n in head_sites.items() if n),
        })
    child_only = [r for r in rows if set(r["exact_modules"]) <= {
        "harness/child/child.py", "harness/child/optimise.py", "harness/child/evaluate.py"}]
    return {"n_fields": len(rows), "rows": rows,
            "fields_named_only_by_the_writer": [r["field"] for r in child_only],
            "fields_named_nowhere_else": [r["field"] for r in rows if r["exact_mentions"] == 0],
            "fields_whose_leaf_is_named_nowhere_else": [r["field"] for r in rows if r["leaf_mentions"] == 0]}


# --------------------------------------------------------------------------
# 7. runs per press
# --------------------------------------------------------------------------


def runs_section(records_dir: Path) -> dict[str, Any]:
    if not records_dir.exists():
        return {"records_dir": str(records_dir), "present": False}
    per_gate: dict[str, dict[str, Any]] = {}
    for gate_dir in sorted(p for p in records_dir.iterdir() if p.is_dir()):
        recs = sorted(gate_dir.rglob("metrics.json"))
        heads = Counter()
        kinds = Counter()
        runners = Counter()
        arms = Counter()
        wall = 0.0
        teeth_runs = 0
        for r in recs:
            try:
                d = json.loads(r.read_text())
            except Exception:
                continue
            heads[str(d.get("tree_git_head", "?"))[:8]] += 1
            kinds[d.get("campaign_run_kind", "?")] += 1
            runners[d.get("runner", "?")] += 1
            arms[f"{d.get('campaign_arm')}/{d.get('campaign_configuration')}/s{d.get('campaign_seed')}"] += 1
            wall += float(d.get("wall_s") or 0.0)
            if "_teeth" in r.parts or "teeth" in r.parts:
                teeth_runs += 1
        verdict = None
        for vf in ("gate.json", "measurements.json"):
            if (gate_dir / vf).exists():
                try:
                    v = json.loads((gate_dir / vf).read_text())
                    verdict = {
                        "file": vf,
                        "verdict": v.get("verdict"),
                        "tree_git_head": str(v.get("tree_git_head", ""))[:8],
                        "resumed": v.get("resumed"),
                        "n_teeth": len(v.get("teeth", []) or []),
                        "runs_provenance": v.get("runs_provenance"),
                    }
                except Exception:
                    verdict = {"file": vf, "unreadable": True}
        per_gate[gate_dir.name] = {
            "n_run_records": len(recs),
            "n_under_teeth_dirs": teeth_runs,
            "heads": dict(heads), "run_kinds": dict(kinds), "runners": dict(runners),
            "wall_s_sum": round(wall, 1),
            "distinct_jobs": len(arms),
            "verdict": verdict,
        }
    total_runs = sum(g["n_run_records"] for g in per_gate.values())
    total_wall = round(sum(g["wall_s_sum"] for g in per_gate.values()), 1)
    # the same (arm, configuration, seed, runner) made under more than one gate
    job_index: dict[str, list[str]] = defaultdict(list)
    for gate_dir in sorted(p for p in records_dir.iterdir() if p.is_dir()):
        for r in gate_dir.rglob("metrics.json"):
            try:
                d = json.loads(r.read_text())
            except Exception:
                continue
            key = (f"{d.get('runner')}:{d.get('campaign_arm')}/{d.get('campaign_configuration')}"
                   f"/s{d.get('campaign_seed')}/{d.get('regime')}/{d.get('campaign_delta')}"
                   f"/{d.get('campaign_predicate_mode')}")
            job_index[key].append(str(r.relative_to(records_dir)))
    shared = {k: v for k, v in job_index.items() if len(v) > 1}
    # the sharper question: records whose composed environment AND outputs are
    # bit-identical to another record's — the same run made twice in one press.
    # Outputs compared: node calls, dispatch sweeps and the objective's hex.
    identical: dict[str, list[str]] = defaultdict(list)
    for gate_dir in sorted(p for p in records_dir.iterdir() if p.is_dir()):
        for r in gate_dir.rglob("metrics.json"):
            try:
                d = json.loads(r.read_text())
            except Exception:
                continue
            if d.get("status") != "ok":
                continue
            exact = d.get("exact") or {}
            key = json.dumps({
                "runner": d.get("runner"), "arm": d.get("campaign_arm"),
                "configuration": d.get("campaign_configuration"),
                "seed": d.get("campaign_seed"), "regime": d.get("regime"),
                "env": d.get("env_architecture"),
                "node_calls_total": d.get("node_calls_total"),
                "dispatch_sweeps": d.get("dispatch_sweeps"),
                "objf": exact.get("norm_objf") or exact.get("objf"),
                "force_maxcal": d.get("force_maxcal"),
                "audit_position": d.get("audit_position"),
            }, sort_keys=True, default=str)
            identical[key].append(str(r.relative_to(records_dir)))
    dup_groups = {k: v for k, v in identical.items() if len(v) > 1}
    # Two runs that are the same job by design, and are not a saving: the
    # neutrality gate's before/after captures (two commits by construction,
    # amendment 13 rule ii) and the composition gate's matrix-vs-switch pair
    # (the comparison IS the second run).  Counted apart.
    # Also apart: the audit-restriction gate's doctored runs (the doctoring is
    # applied inside the child before the audit sweep, so the run must be made
    # again even though the solve is identical).
    def by_design(path: str) -> bool:
        return (path.startswith("switch_neutrality/before/")
                or path.startswith("switch_composition/") and "/switch_by_switch/" in path
                or path.startswith("audit_restriction/") and "/per_run_" in path
                or path.startswith("audit_restriction/") and "/in_loop/" in path)
    n_redundant = 0
    n_by_design = 0
    for v in dup_groups.values():
        design = [p for p in v if by_design(p)]
        n_by_design += len(design)
        n_redundant += max(len(v) - len(design) - 1, 0)
    wall_redundant = 0.0
    for k, v in dup_groups.items():
        rest = [p for p in v if not by_design(p)]
        for p in rest[1:]:
            try:
                wall_redundant += float(json.loads((records_dir / p).read_text()).get("wall_s") or 0)
            except Exception:
                pass
    return {"records_dir": str(records_dir), "present": True,
            "n_run_records": total_runs, "wall_s_sum": total_wall,
            "per_gate": per_gate,
            "n_distinct_jobs": len(job_index),
            "jobs_made_under_more_than_one_directory": shared,
            "n_ok_records_compared_for_identity": sum(len(v) for v in identical.values()),
            "identical_run_groups": [
                {"job": json.loads(k), "records": v} for k, v in dup_groups.items()
            ],
            "n_records_that_duplicate_another": n_redundant,
            "n_duplicates_by_design": n_by_design,
            "wall_s_of_the_redundant_records": round(wall_redundant, 1)}


# --------------------------------------------------------------------------
# 8. runner flags vs documents
# --------------------------------------------------------------------------


def flags_section() -> dict[str, Any]:
    src = (HERE / "experiment_runner.py").read_text()
    tree = ast.parse(src)
    flags: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "attr", "") == "add_argument":
            for a in node.args:
                if isinstance(a, ast.Constant) and str(a.value).startswith("--"):
                    flags.append(a.value)
    docs = {k: p.read_text() for k, p in DOCS.items() if p.exists()}
    reports = "\n".join(p.read_text() for p in ARCHIVED_REPORTS)
    rows = []
    for f in flags:
        pat = re.compile(re.escape(f) + r"(?![A-Za-z0-9-])")
        row = {"flag": f}
        for k, t in docs.items():
            row[k] = len(pat.findall(t))
        row["archived_reports"] = len(pat.findall(reports))
        row["harness_source"] = sum(
            len(pat.findall(p.read_text())) for p in harness_modules()
        )
        rows.append(row)
    undocumented = [r["flag"] for r in rows if r["README"] == 0]
    return {"flags": rows, "n_flags": len(flags), "not_in_README": undocumented}


# --------------------------------------------------------------------------
# 9. prose
# --------------------------------------------------------------------------


def prose_section(lines: dict[str, Any]) -> dict[str, Any]:
    per_module = lines["per_module"]
    shares = {
        m: round((c["docstring"] + c["comment"]) / max(c["total"], 1), 3)
        for m, c in per_module.items()
    }
    # paragraphs shared between README and the harness plan / experiment plan
    def paragraphs(text: str) -> list[str]:
        out = []
        for para in re.split(r"\n\s*\n", text):
            p = " ".join(para.split())
            if len(p) > 200 and not p.startswith("|"):
                out.append(p)
        return out
    readme = DOCS["README"].read_text()
    shared: dict[str, int] = {}
    readme_paras = paragraphs(readme)
    for k in ("HARNESS_PLAN", "EXPERIMENT_PLAN"):
        other = DOCS[k].read_text()
        other_norm = " ".join(other.split())
        n = 0
        for p in readme_paras:
            # a 120-character window of a README paragraph found verbatim elsewhere
            window = p[: 120]
            if window in other_norm:
                n += 1
        shared[k] = n
    doc_sizes = {k: len(p.read_text().splitlines()) for k, p in DOCS.items() if p.exists()}
    return {"docstring_and_comment_share": shares,
            "readme_paragraphs": len(readme_paras),
            "readme_paragraphs_found_verbatim_in": shared,
            "document_lines": doc_sizes}


# --------------------------------------------------------------------------
# printing
# --------------------------------------------------------------------------


def _print_lines(sec: dict[str, Any]) -> None:
    print("\n== 1. lines ==")
    print(f"{'subpackage':22s} {'total':>7s} {'code':>7s} {'docstr':>7s} {'comment':>7s} {'blank':>6s} {'msg':>6s}")
    print("  ('msg' = lines lying wholly inside a non-docstring string literal: refusal messages, captions, printed sentences; a subset of 'code')")
    for k, c in sorted(sec["per_subpackage"].items(), key=lambda kv: -kv[1]["total"]):
        print(f"{k:22s} {c['total']:7d} {c['code']:7d} {c['docstring']:7d} {c['comment']:7d} {c['blank']:6d} {c['message']:6d}")
    t = sec["total"]
    print(f"{'ALL':22s} {t['total']:7d} {t['code']:7d} {t['docstring']:7d} {t['comment']:7d} {t['blank']:6d} {t['message']:6d}")
    print("\ngates.py by section (blocks between its own `# ----` rules):")
    for sec_ in sec["gates_py_sections"]:
        print(f"  {sec_['start']:5d}-{sec_['end']:5d} {sec_['lines']:5d}  {sec_['title']}")
    print("\nlargest modules:")
    for m, c in sorted(sec["per_module"].items(), key=lambda kv: -kv[1]["total"])[:15]:
        print(f"  {m:50s} {c['total']:6d} code {c['code']:6d} doc {c['docstring']:5d} msg {c['message']:5d}")


def _print_imports(sec: dict[str, Any]) -> None:
    print("\n== 2. imports ==")
    print("never imported by anything in the package or the top-level scripts:")
    for m in sec["never_imported"]:
        print(f"  {m}")
    fan_in = sorted(sec["imported_by"].items(), key=lambda kv: -len(kv[1]))
    print("highest fan-in:")
    for m, by in fan_in[:8]:
        print(f"  {m:45s} imported by {len(by)}")


def _print_defs(sec: dict[str, Any]) -> None:
    print("\n== 3. definitions ==")
    print(f"{sec['n_definitions']} module-level functions/classes")
    print(f"{len(sec['unreferenced'])} referenced by name nowhere but their definition:")
    for d in sec["unreferenced"]:
        print(f"  {d['module']}:{d['lineno']:5d} {d['kind']:8s} {d['name']:45s} {d['lines']:4d} lines")
    pub = sec["public_but_module_local"]
    print(f"{len(pub)} public names referenced only inside their own module (candidates for an underscore, not deletion)")


def _print_dups(sec: dict[str, Any]) -> None:
    print("\n== 4. duplicates ==")
    print(f"{len(sec['same_name'])} function names defined in more than one module:")
    for k, v in sorted(sec["same_name"].items()):
        print(f"  {k:35s} {', '.join(v)}")
    print(f"{len(sec['same_body'])} groups of functions with identical bodies (>= 6 lines, name-normalised):")
    for group in sec["same_body"]:
        print("  " + " | ".join(f"{l}:{n} ({k})" for l, n, k in group))


def _print_registry(sec: dict[str, Any]) -> None:
    print("\n== 5. registry ==")
    print(f"{sec['n_gates']} gates, {sec['n_teeth']} teeth, {sec['n_measurements']} measurement stages")
    print(f"gates that start PROCESS ({len(sec['gates_needing_runs'])}): {', '.join(sec['gates_needing_runs'])}")
    print(f"gates that do not ({len(sec['gates_without_runs'])}): {', '.join(sec['gates_without_runs'])}")
    print(f"{'name':26s} {'kind':12s} {'plan':8s} {'teeth':>5s} {'runs':>5s} reads_from / reads_records")
    for r in sec["rows"]:
        print(f"{r['name']:26s} {r['kind']:12s} {str(r['plan_name'] or ''):8s} {r['n_teeth']:5d} "
              f"{str(r['needs_runs']):>5s} {r['reads_from']} {r['reads_records'] if r['reads_records'] else ''}")


def _print_records(sec: dict[str, Any]) -> None:
    print("\n== 6. records ==")
    print(f"{sec['n_fields']} declared fields")
    print(f"{len(sec['fields_named_nowhere_else'])} named (full path) by nothing outside records.py: {sec['fields_named_nowhere_else']}")
    print(f"{len(sec['fields_whose_leaf_is_named_nowhere_else'])} whose last path segment is named by nothing outside records.py: {sec['fields_whose_leaf_is_named_nowhere_else']}")
    print(f"{len(sec['fields_named_only_by_the_writer'])} named only by the child that writes them:")
    for f in sec["fields_named_only_by_the_writer"]:
        print(f"  {f}")
    low = [r for r in sec["rows"] if r["exact_mentions"] <= 2]
    print(f"{len(low)} fields with <= 2 exact mentions outside records.py:")
    for r in low:
        print(f"  {r['field']:45s} exact {r['exact_mentions']:3d} leaf {r['leaf_mentions']:3d} {sorted(set(r['exact_modules']) | set(r['leaf_modules']))}")


def _print_runs(sec: dict[str, Any]) -> None:
    print("\n== 7. runs per press ==")
    if not sec.get("present"):
        print(f"records directory absent: {sec['records_dir']}")
        return
    print(f"{sec['records_dir']}")
    print(f"{sec['n_run_records']} run records, wall_s summed {sec['wall_s_sum']} s (context only)")
    print(f"{'gate dir':26s} {'runs':>5s} {'teeth':>5s} {'wall_s':>8s} {'jobs':>5s} heads / kinds / runners")
    for g, d in sorted(sec["per_gate"].items(), key=lambda kv: -kv[1]["n_run_records"]):
        if d["n_run_records"] == 0:
            continue
        print(f"{g:26s} {d['n_run_records']:5d} {d['n_under_teeth_dirs']:5d} {d['wall_s_sum']:8.0f} {d['distinct_jobs']:5d} "
              f"{d['heads']} {d['run_kinds']} {d['runners']}")
    print(f"{sec['n_distinct_jobs']} distinct (runner, arm, configuration, seed, regime, delta, mode) jobs; "
          f"{len(sec['jobs_made_under_more_than_one_directory'])} of them made under more than one gate directory "
          f"(an upper bound: the key ignores composition overrides and entry states)")
    print(f"{sec['n_records_that_duplicate_another']} of {sec['n_ok_records_compared_for_identity']} ok records are "
          f"bit-identical to another record of the same press on (environment, audit position, node calls, sweeps, "
          f"objective hex) and are not one of the {sec['n_duplicates_by_design']} second runs a gate makes by design; "
          f"their wall_s sums to {sec['wall_s_of_the_redundant_records']} s (context only). Groups:")
    for g in sec["identical_run_groups"]:
        j = g["job"]
        print(f"  {j['runner']}:{j['arm']}/{j['configuration']}/s{j['seed']}/{j['regime']} "
              f"node_calls {j['node_calls_total']} objf {j['objf']}  x{len(g['records'])}")
        for p in g["records"]:
            print(f"      {p}")


def _print_flags(sec: dict[str, Any]) -> None:
    print("\n== 8. flags ==")
    print(f"{sec['n_flags']} flags on experiment_runner.py")
    keys = ["README", "EXPERIMENT_PLAN", "HARNESS_PLAN", "IMPROVEMENT_LIST", "ASSESSMENT", "archived_reports", "harness_source"]
    print(f"{'flag':20s} " + " ".join(f"{k[:9]:>9s}" for k in keys))
    for r in sec["flags"]:
        print(f"{r['flag']:20s} " + " ".join(f"{r.get(k, 0):9d}" for k in keys))
    print(f"not mentioned in the README: {sec['not_in_README']}")


def _print_prose(sec: dict[str, Any]) -> None:
    print("\n== 9. prose ==")
    print("document lines:", sec["document_lines"])
    print(f"README paragraphs > 200 chars: {sec['readme_paragraphs']}; found verbatim (120-char window) in: "
          f"{sec['readme_paragraphs_found_verbatim_in']}")
    top = sorted(sec["docstring_and_comment_share"].items(), key=lambda kv: -kv[1])[:12]
    print("highest docstring+comment share:")
    for m, s in top:
        print(f"  {m:50s} {s:.2f}")


def import_walk() -> dict[str, Any]:
    """Import every harness module and the top-level scripts, live, and say which fail.

    The static graph above says who imports whom; this says whether each
    module *imports at all* in this tree — the check a refactor task runs
    before and after (A71, A72).  Scripts are imported as modules by path,
    so their ``main`` is not run.
    """
    import importlib
    import importlib.util
    import traceback

    failures: dict[str, str] = {}
    names: list[str] = []
    for path in harness_modules():
        name = _module_name(path)
        names.append(name)
        try:
            importlib.import_module(name)
        except Exception:  # noqa: BLE001 - the failure is the finding
            failures[name] = traceback.format_exc().splitlines()[-1]
    for path in TOP_LEVEL_SCRIPTS:
        label = module_label(path)
        names.append(label)
        try:
            # Registered in sys.modules before executing: a dataclass in the
            # script looks its own module up there while being defined.
            spec_name = f"_import_walk_{path.stem}"
            spec = importlib.util.spec_from_file_location(spec_name, path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec_name] = module
            spec.loader.exec_module(module)  # type: ignore[union-attr]
        except Exception:  # noqa: BLE001
            failures[label] = traceback.format_exc().splitlines()[-1]
    return {"n_modules": len(names), "n_failures": len(failures), "failures": failures}


def _print_import_walk(sec: dict[str, Any]) -> None:
    print(f"\n== import walk: {sec['n_modules']} modules, {sec['n_failures']} failure(s)")
    for name, why in sorted(sec["failures"].items()):
        print(f"  FAIL {name}: {why}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--records", type=Path, default=DEFAULT_RECORDS,
                    help="a directory of relocated gate records (read-only)")
    ap.add_argument("--json", type=Path, default=None, help="write the whole survey here")
    ap.add_argument("--import-walk", action="store_true",
                    help="import every module live and report failures, then stop")
    args = ap.parse_args(argv)

    if args.import_walk:
        walk = import_walk()
        _print_import_walk(walk)
        if args.json:
            args.json.parent.mkdir(parents=True, exist_ok=True)
            args.json.write_text(json.dumps(walk, indent=1, default=str))
        return 0 if walk["n_failures"] == 0 else 1

    out: dict[str, Any] = {}
    out["lines"] = lines_section(); _print_lines(out["lines"])
    out["imports"] = imports_section(); _print_imports(out["imports"])
    out["definitions"] = definitions_section(); _print_defs(out["definitions"])
    out["duplicates"] = duplicates_section(); _print_dups(out["duplicates"])
    out["registry"] = registry_section(); _print_registry(out["registry"])
    out["records"] = records_section(); _print_records(out["records"])
    out["runs"] = runs_section(args.records); _print_runs(out["runs"])
    out["flags"] = flags_section(); _print_flags(out["flags"])
    out["prose"] = prose_section(out["lines"]); _print_prose(out["prose"])
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(out, indent=1, default=str))
        print(f"\nwritten: {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
