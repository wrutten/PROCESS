#!/usr/bin/env python
"""A33 (postsolve-hoist): classification artifacts, driver capability gates.

The intervention component this task builds (V2 plan section 1, Appendix A
item 3a): model nodes whose outputs the optimiser never consumes -- no
objective read, no active-constraint read, no solve-phase model read -- leave
the per-call path entirely and run **once per run at the accepted optimum**.

Three deliverables, all produced or gated by this one entry point
(protocol section 15: every published number comes from executing a committed
script; failure paths are reachable from the same entry point):

``classify``
    Derives, per deck, the committed artifact
    ``arch_surgery/docs/data/postsolve_<scenario>.json``:

    * **Seeds** -- the objective's read set (the deck's ``minmax`` branch of
      ``objective_function``, by AST) plus every active constraint's read set
      (per ``icc``, by AST over ``constraints.py`` with local-call closure).
      The deck's ``icc`` list is parsed from the frozen scenario deck; the
      count is cross-checked against A28's recorded ``n_constraints``
      (lifted decks carry ``icc = 93`` in addition, exactly one, which is the
      lift's own constraint) and the stage refuses on any disagreement.
    * **Backward crawl** -- writer authority is the committed run-time write
      census (``node_writesets.json``, per scenario); transitive reachability
      comes from the sibling repository's per-deck dependency exports
      (``PROCESS_code_analysis/output/<config>/process_dependencies.json``,
      read-only, sha256 and git head recorded at read time -- trap T9 is
      accepted here on the task brief's explicit instruction, and the
      recorded hash makes any later regeneration visible rather than
      silent).  A node is a post-solve candidate iff nothing it writes is
      (transitively) consumed by the seeds within the solve phase.
    * **Confirmation in source** -- an AST scan of ``process/`` for readers
      of every candidate-written field; every external read site must be
      classified (candidate-internal, inactive objective branch, inactive
      constraint, branch dead under this deck's switches, unreachable model,
      driver debug logging).  An unclassifiable site fails the stage.
    * **V6 / branch-liveness** -- the availability-model reads of
      ``vacuum.n_vac_pumps_high`` sit in the ``i_plant_availability`` 2/3
      branches; each deck's switch value is parsed from the deck and the
      liveness verdict recorded per site.
    * The artifact carries ``nodes_sha256`` over its load-bearing fields so
      the driver's loader refuses a hand-edited file.

``writesets``
    a26-generation write sets for the two pulsed decks (V2 Appendix A item
    1), which do not exist yet and which the full-run gates need.  The
    A18-default **control** runs first: from the same probe census
    (A18 harvest, read-only in the main checkout), the default invocation of
    ``a25_writeset.py`` must regenerate every committed
    ``writeset_<scenario>.json`` exactly -- every field but ``tree_git_head``
    -- and the committed ``writeset_a26_st_regression.json`` likewise.  Any
    control failure stops the stage before anything is generated.

``validation``
    The loader's teeth: four refusal probes in fresh subprocesses (a
    hand-edited artifact, a wrong-deck artifact, an artifact listing a node
    the deck keeps per-call, an artifact naming an unknown node).  Each must
    REFUSE before any model runs; a probe that runs anyway fails the stage.

``gate``
    Protocol-12 switch-neutrality: with ``PROCESS_ARCH_POST_SOLVE`` unset,
    one ``A1'`` ``st_regression`` start000 run under the a26-mode spec on
    the edited driver must reproduce A32's recorded start000 **bit-for-bit**
    (``node_calls_solve_phase``, ``outer_pass_hist``, ``norm_objf`` hex),
    teeth included (A31's gate machinery, reused not reimplemented).

``fullrun``
    The strong equivalence gate, per deck: one full optimisation WITH the
    exclusion against one WITHOUT, everything else identical (``A1'``
    configuration, a26-mode spec, tau = 1e-6, the deck's own baseline start).
    If the classification is right, nothing the solve phase computes reads a
    skipped output, so the two solve phases are **bit-identical**: same
    ``norm_objf``/``sqsumsq``/``xcm``/``rcm`` as exact hex, same ``ifail``,
    same pass histograms and sweep counts -- and the node-call ledger differs
    by exactly the suppressed call sites (checked per node against the
    driver's own suppression counts).  A mismatch in any field means the
    classification is wrong for that deck; that is the failure path and it is
    reported, never tuned.

``tally``
    Re-derives the fullrun comparison tables from the run records on disk.

Isolation: every PROCESS run is a fresh subprocess in its own working
directory, ``PYTHONPATH`` pinned to this worktree, the exact tree asserted
inside the subprocess (traps T6/T10).  No conclusion rests on a timing; every
quantity emitted is a count, a name, a hash or a bit-exact float.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
TREE = HERE.parent.parent
DATA = TREE / "arch_surgery" / "docs" / "data"
RUNS = HERE / "runs" / "a33"

sys.path.insert(0, str(HERE))
from run_a28 import TAU, deck_for, env_for, stage_decks  # noqa: E402
from a31_drift_probe import gate_compare, gate_extract, gate_teeth  # noqa: E402

#: The main checkout: reference records live there and are read, never
#: written.
MAIN = Path("/home/wrutten/projects/PROCESS_surgery")
A32_REF = MAIN / "arch_surgery/idf_probe/runs/a32/campaign/A1p/start000/metrics.json"
A28_H5 = MAIN / "arch_surgery/idf_probe/runs/a28/h5"
A18_HARVEST = MAIN / "arch_surgery/idf_probe/runs/a18"

#: The sibling dependency-analysis repository (read-only; never written,
#: never messaged).  Its per-deck exports are the crawl's reachability
#: source; ``ANALYSIS_PIN`` is read from its config at run time rather than
#: copied into a document (CLAUDE.md).
SIBLING = Path("/home/wrutten/projects/PROCESS_code_analysis")
SIBLING_CONFIG = SIBLING / "src/PROCESS_DSM/inputs/config.py"

SCENARIOS = ["large_tokamak_nof", "low_aspect_ratio_DEMO", "st_regression"]
PULSED = {"large_tokamak_nof", "low_aspect_ratio_DEMO"}
#: Which sibling export configuration serves each deck.  ``tokamak`` is the
#: analysis preset, which matches ``large_tokamak_nof`` exactly (node map
#: caveat V6, resolved 2026-09-01 by per-scenario regeneration M100); the
#: other two decks have their own per-deck exports.
DSM_EXPORT = {
    "large_tokamak_nof": "tokamak",
    "low_aspect_ratio_DEMO": "low_aspect_ratio_DEMO",
    "st_regression": "st_regression",
}
#: A28's recorded constraint counts (the cross-check the task brief demands).
#: Pulsed decks ran the LIFTED deck in A28's A1', which carries exactly one
#: extra constraint -- the lift's own ``icc = 93``.
A28_N_CONSTRAINTS = {
    "st_regression": 18,
    "large_tokamak_nof": 27,
    "low_aspect_ratio_DEMO": 26,
}

#: D15's calibrated perturbation size -- used ONLY by the neutrality gate,
#: which must reproduce A32's start000 configuration exactly (seed 0 leaves
#: the deck's own point unperturbed).  The fullrun gate runs delta = None.
DELTA_GATE = 0.10

ICC_RE = re.compile(r"^icc\s*=\s*(\d+)\s*(?:\*.*)?$")
MM_RE = re.compile(r"^minmax\s*=\s*(-?\d+)\s*(?:\*.*)?$")
SWITCH_RE = re.compile(r"^(\w+)\s*=\s*(-?\d+)\s*(?:\*.*)?$")

#: Sequence order of the deferrable-in-principle call sites, as
#: ``_call_models_once`` issues them.  Used only to order the artifact's
#: node list the way the one-shot sweep will execute it.
SEQUENCE_ORDER = [
    "plasma_geom", "build", "physics", "copper_tf_coil", "cicc_sctfcoil",
    "croco_sctfcoil", "aluminium_tf_coil", "pfcoil", "pulse", "divertor",
    "fw", "shield", "vacuum_vessel", "ccfe_hcpb", "dcll", "cryostat",
    "structure", "tfcoil", "power", "vacuum", "buildings", "power.acpow",
    "power.plant_electric_production", "availability", "water_use", "costs",
]


def _git_head() -> str | None:
    try:
        return subprocess.run(
            ["git", "-C", str(TREE), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=False,
        ).stdout.strip() or None
    except Exception:
        return None


def _git_dirty() -> bool:
    """Tracked-file dirtiness only (``-uno``): the artifacts this script is
    in the middle of generating are necessarily untracked at generation time
    and must not mark their own provenance dirty; a MODIFIED tracked file is
    the hazard the stamp exists for."""
    out = subprocess.run(
        ["git", "-C", str(TREE), "status", "--porcelain",
         "--untracked-files=no"],
        capture_output=True, text=True, check=False,
    ).stdout
    return bool(out.strip())


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ==========================================================================
# stage: classify
# ==========================================================================


def parse_deck(scenario: str) -> tuple[list[int], int, dict]:
    """(icc list, minmax, integer switches) from the frozen scenario deck.

    Comment lines start with ``*``; a value line may carry a trailing ``*``
    comment.  A naive regex over-matches the DESCRIPTION comments, which is
    why the parsed count is cross-checked against A28's record before
    anything downstream trusts it.
    """
    iccs, minmax, switches = [], None, {}
    for line in (HERE / "scenarios" / f"{scenario}.IN.DAT").read_text().splitlines():
        t = line.strip()
        if t.startswith("*"):
            continue
        m = ICC_RE.match(t)
        if m:
            iccs.append(int(m.group(1)))
            continue
        m = MM_RE.match(t)
        if m:
            minmax = int(m.group(1))
            continue
        m = SWITCH_RE.match(t)
        if m:
            switches[m.group(1)] = int(m.group(2))
    if minmax is None:
        raise SystemExit(f"{scenario}: no minmax parsed from the deck")
    return iccs, minmax, switches


class _Reads(ast.NodeVisitor):
    """``data.<ns>.<field>`` attribute loads (trap T2: the parser, not a
    regex, so ``==`` and comments cannot produce phantom accesses)."""

    def __init__(self):
        self.reads: set[str] = set()

    def visit_Attribute(self, node):  # noqa: N802
        inner = node.value
        if (
            isinstance(inner, ast.Attribute)
            and isinstance(inner.value, ast.Name)
            and inner.value.id == "data"
            and isinstance(node.ctx, ast.Load)
        ):
            self.reads.add(f"{inner.attr}.{node.attr}")
        self.generic_visit(node)


def _figures_of_merit() -> dict[int, str]:
    """``{value: NAME}`` parsed from the enum's own source (no import).

    A member is either ``NAME = 1`` or ``NAME = (1, "description")``.
    """
    src = (TREE / "process/data_structure/numerics.py").read_text()
    out = {}
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.ClassDef) and node.name == "FiguresOfMerit":
            for st in node.body:
                if not (isinstance(st, ast.Assign)
                        and isinstance(st.targets[0], ast.Name)):
                    continue
                val = st.value
                if isinstance(val, ast.Tuple) and val.elts:
                    val = val.elts[0]
                if isinstance(val, ast.Constant) and isinstance(val.value, int):
                    out[int(val.value)] = st.targets[0].id
    if not out:
        raise SystemExit("FiguresOfMerit did not parse from numerics.py")
    return out


def objective_reads(minmax: int) -> set[str]:
    """Reads of the active figure-of-merit branch, plus any unconditional
    reads of ``objective_function`` (same walk as the driver's own
    ``_predicate_read_fields``, narrowed to one branch)."""
    fom_name = _figures_of_merit()[abs(minmax)]
    src = (TREE / "process/core/solver/objectives.py").read_text()
    fn = None
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.FunctionDef) and node.name == "objective_function":
            fn = node
    if fn is None:
        raise SystemExit("objectives.py has no objective_function")
    fields: set[str] = set()
    seen_chain = False

    def fom_of(test):
        if (isinstance(test, ast.Compare) and len(test.ops) == 1
                and isinstance(test.ops[0], ast.Eq)
                and isinstance(test.comparators[0], ast.Attribute)
                and isinstance(test.comparators[0].value, ast.Name)
                and test.comparators[0].value.id == "FiguresOfMerit"):
            return test.comparators[0].attr
        return None

    def walk(stmts):
        nonlocal seen_chain
        for st in stmts:
            name = fom_of(st.test) if isinstance(st, ast.If) else None
            if name is not None:
                seen_chain = True
                if name == fom_name:
                    v = _Reads()
                    for b in st.body:
                        v.visit(b)
                    fields.update(v.reads)
                walk(st.orelse)
            else:
                v = _Reads()
                v.visit(st)
                fields.update(v.reads)

    walk(fn.body)
    if not seen_chain:
        raise SystemExit("objective_function's FoM chain did not parse")
    return fields


def constraint_reads_by_icc() -> tuple[dict[int, set[str]], dict[int, str]]:
    """``{icc: data reads}`` with closure over local calls inside
    ``constraints.py`` (a constraint that delegates to a local helper owns
    the helper's reads too).  Also returns ``{icc: function name}``."""
    src = (TREE / "process/core/solver/constraints.py").read_text()
    tree = ast.parse(src)
    fns, icc_fn = {}, {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            fns[node.name] = node
            for dec in node.decorator_list:
                if (isinstance(dec, ast.Call)
                        and isinstance(dec.func, ast.Attribute)
                        and dec.func.attr == "register_constraint"
                        and dec.args and isinstance(dec.args[0], ast.Constant)):
                    icc_fn[int(dec.args[0].value)] = node.name
    direct, calls = {}, {}
    for name, fn in fns.items():
        v = _Reads()
        v.visit(fn)
        direct[name] = v.reads
        cs = set()
        for n in ast.walk(fn):
            if (isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                    and n.func.id in fns):
                cs.add(n.func.id)
        calls[name] = cs

    def closure(name, seen):
        if name in seen:
            return set()
        seen.add(name)
        out = set(direct[name])
        for c in calls[name]:
            out |= closure(c, seen)
        return out

    return ({i: closure(f, set()) for i, f in icc_fn.items()},
            icc_fn)


#: DSM supermodel class -> driver node.  Helper ``file_model`` supermodels
#: are attributed through their (transitive) callers instead, so a shared
#: helper's reads land on every node that can invoke it -- over-attribution
#: is conservative (it can only ADD needed nodes, never hide a reader).
CLASS_TO_NODE = {
    "PlasmaGeom": "plasma_geom", "Build": "build",
    "Physics": "physics", "PlasmaCurrent": "physics",
    "PlasmaFields": "physics", "PlasmaInductance": "physics",
    "NeProfile": "physics", "PlasmaDensityLimit": "physics",
    "PlasmaProfile": "physics", "TeProfile": "physics",
    "PlasmaBeta": "physics", "PlasmaDiamagneticCurrent": "physics",
    "PlasmaBootstrapCurrent": "physics", "SauterBootstrapCurrent": "physics",
    "CurrentDrive": "physics", "ElectronCyclotron": "physics",
    "FusionReactionRate": "physics", "PlasmaConfinementTime": "physics",
    "PlasmaConfinementTransition": "physics", "PlasmaExhaust": "physics",
    "ScrapeOffLayer": "physics", "ImpurityRadiation": "physics",
    "CROCOSuperconductingTFCoil": "croco_sctfcoil",
    "CICCSuperconductingTFCoil": "cicc_sctfcoil",
    "PFCoil": "pfcoil", "CSCoil": "pfcoil", "CsFatigue": "pfcoil",
    "Pulse": "pulse", "Divertor": "divertor", "FirstWall": "fw",
    "Shield": "shield", "VacuumVessel": "vacuum_vessel",
    "CCFE_HCPB": "ccfe_hcpb", "Cryostat": "cryostat",
    "Structure": "structure", "Power": "power+", "Vacuum": "vacuum",
    "Buildings": "buildings", "Availability": "availability",
    "WaterUse": "water_use", "Costs": "costs",
}
#: The three ``Power``-class call sites share one DSM supermodel; the crawl
#: treats them as one unit and the artifact reports them together.
POWER_GROUP = ("power", "power.acpow", "power.plant_electric_production")


def dsm_reads(scenario: str) -> tuple[dict, dict, dict]:
    """Per-driver-unit read sets from the sibling's per-deck export.

    Returns ``(reads, provenance, t1_probe)``.  ``reads`` maps driver unit
    -> set of datastructure fields read anywhere under that unit's
    supermodels (helpers attributed to all transitive callers).  The export
    is rooted at each model's ``run()`` entry (trap T1: ``output()`` paths
    are not in it), which ``t1_probe`` spot-checks on the edge that bit
    first: ``physics.b_plasma_vertical_required`` must have no read edge
    into any M1 unit.
    """
    export = SIBLING / "output" / DSM_EXPORT[scenario] / "process_dependencies.json"
    sha = _sha256(export)
    d = json.loads(export.read_text())
    nodes, edges = d["nodes"], d["edges"]

    def top(uid):
        while nodes[uid].get("parent"):
            uid = nodes[uid]["parent"]
        return uid

    sm = {k: v for k, v in nodes.items()
          if v["kind"] == "model"
          and v.get("annotations", {}).get("PROCESS_ast_info", {})
                .get("level") == "supermodel"}
    helpers = {k for k, v in sm.items()
               if v["annotations"]["PROCESS_ast_info"].get("model_type")
               == "file_model"}
    call_from = defaultdict(set)
    for e in edges.values():
        if e["kind"] != "call_interface":
            continue
        ss, ts = top(e["source"]), top(e["target"])
        if ts in helpers and ss != ts:
            call_from[ts].add(ss)

    def owners(h, seen):
        out = set()
        for c in call_from.get(h, ()):
            if c in seen:
                continue
            seen.add(c)
            if c in helpers:
                out |= owners(c, seen)
            else:
                out.add(c)
        return out

    unmapped = set()

    def units_of(smid):
        if smid not in sm:
            return set()
        name = sm[smid]["name"]
        if smid in helpers:
            us = set()
            for o in owners(smid, set()):
                oname = sm[o]["name"]
                if oname in CLASS_TO_NODE:
                    us.add(CLASS_TO_NODE[oname])
                elif oname != "Constraints":
                    unmapped.add(oname)
            return us
        if name == "Constraints":
            # the predicate layer: its reads are the SEEDS, taken from the
            # driver's own source per active icc, not from here.
            return set()
        if name in CLASS_TO_NODE:
            return {CLASS_TO_NODE[name]}
        unmapped.add(name)
        return set()

    def is_ds_var(v):
        ai = v.get("annotations", {}).get("PROCESS_ast_info", {})
        return v["kind"] == "variable" and "scope" not in ai and "." in v["name"]

    reads = defaultdict(set)
    n_read_edges = 0
    for e in edges.values():
        if e["kind"] != "data_interface":
            continue
        ai = e["annotations"].get("PROCESS_ast_info", {})
        if ai.get("family") != "access":
            continue
        if ai.get("access_type") not in ("read", "read_write"):
            continue
        var = nodes[e["source"]]
        if var["kind"] != "variable" or not is_ds_var(var):
            continue
        n_read_edges += 1
        for u in units_of(top(e["target"])):
            reads[u].add(var["name"])
    if unmapped:
        raise SystemExit(
            f"{scenario}: DSM supermodels {sorted(unmapped)} have no driver "
            f"mapping; the crawl must not guess"
        )

    # T1 probe: the output-path edge that bit three times must be absent.
    t1_readers = sorted(
        u for u, flds in reads.items() if "physics.b_plasma_vertical_required" in flds
    )
    t1 = {
        "field": "physics.b_plasma_vertical_required",
        "read_by_units_in_export": t1_readers,
        "read_by_physics": "physics" in t1_readers,
        "verdict": ("PASS: no run-path read into M1 -- the export excludes "
                    "output() paths on the edge that bit first (trap T1)"
                    if "physics" not in t1_readers else
                    "FAIL: the export attributes an output()-path read to "
                    "the run path"),
    }
    prov = {
        "export": str(export),
        "sha256_at_read": sha,
        "sibling_git_head": subprocess.run(
            ["git", "-C", str(SIBLING), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=False).stdout.strip(),
        "n_access_read_edges": n_read_edges,
        "n_supermodels": len(sm),
    }
    return reads, prov, t1


def _analysis_pin() -> str:
    """The sibling's pin name, read from its config (never copied)."""
    m = re.search(r'ANALYSIS_PIN_NAME\s*=\s*"([^"]+)"',
                  SIBLING_CONFIG.read_text())
    if not m:
        raise SystemExit(f"ANALYSIS_PIN_NAME not found in {SIBLING_CONFIG}")
    return m.group(1)


def source_reader_scan(fields: set[str]) -> dict[str, list[dict]]:
    """Every Load-context ``<x>.<ns>.<field>`` site in ``process/`` for the
    given ``ns.field`` set, with file, line and enclosing function.

    Deliberately over-matches (any attribute chain ending ``.ns.field``, not
    only ``data.``-rooted ones): a missed reader is the dangerous direction,
    a spurious one just gets classified.
    """
    targets = defaultdict(set)
    for f in fields:
        ns, _, fl = f.partition(".")
        targets[fl].add(ns)
    hits = defaultdict(list)
    for py in (TREE / "process").rglob("*.py"):
        parts = py.relative_to(TREE).parts
        if "data_structure" in parts or "io" in parts:
            continue
        try:
            tree = ast.parse(py.read_text())
        except SyntaxError:
            continue
        funcs = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                funcs.append((node.lineno, node.end_lineno, node.name))

        def enc(line):
            e = [f for f in funcs if f[0] <= line <= f[1]]
            e.sort(key=lambda f: f[1] - f[0])
            return e[0][2] if e else "<module>"

        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
                if node.attr not in targets:
                    continue
                inner = node.value
                if isinstance(inner, ast.Attribute) and inner.attr in targets[node.attr]:
                    hits[f"{inner.attr}.{node.attr}"].append({
                        "file": str(py.relative_to(TREE)),
                        "line": node.lineno,
                        "function": enc(node.lineno),
                    })
    return dict(hits)


#: Model files owned by each candidate node -- reads inside them are the
#: candidate's own.
CANDIDATE_FILES = {
    "costs": ("process/models/costs",),
    "water_use": ("process/models/water_use",),
    "vacuum": ("process/models/vacuum",),
    "pulse": ("process/models/pulse",),
}

#: ``availability.py`` functions reachable ONLY from the non-default
#: ``i_plant_availability`` branches (2 = Morris, 3 = ST); with the deck at
#: 0 they are dead.  Derived by reading ``Availability.run``'s dispatch.
AVAILABILITY_NONDEFAULT_FUNCS = {
    "avail_2", "avail_st", "calc_u_unplanned_vacuum", "calc_u_planned",
    "calc_u_unplanned_magnets", "calc_u_unplanned_divertor",
    "calc_u_unplanned_fwbs", "calc_u_unplanned_bop", "calc_u_unplanned_hcd",
    "avail_st_divertor", "avail_st_centrepost",
}


def classify_site(site: dict, candidate: str, active_icc: list[int],
                  icc_fn: dict[int, str], switches: dict) -> tuple[str, bool]:
    """(classification, is_live_solve_phase_reader) for one read site."""
    f, fn = site["file"], site["function"]
    for c, prefixes in CANDIDATE_FILES.items():
        if any(f.startswith(p) for p in prefixes):
            return (f"internal to candidate '{c}'"
                    + ("" if c == candidate else " (post-solve peer)"), False)
    if f == "process/core/solver/objectives.py":
        return ("objective_function branch not active on this deck "
                "(active branch has no overlap -- enforced by the loader's "
                "predicate check)", False)
    if f == "process/core/solver/constraints.py":
        icc = next((i for i, n in icc_fn.items() if n == fn), None)
        if icc in active_icc:
            return (f"ACTIVE constraint icc={icc} reads this field", True)
        return (f"constraint icc={icc} ({fn}) not active on this deck", False)
    if f == "process/core/solver/evaluators.py" and fn == "fcnvmc1":
        return ("driver debug logging (logger.debug f-string): the value is "
                "formatted into a string, never fed to a computation", False)
    if f.startswith("process/models/stellarator"):
        return ("stellarator path (istell = 0 on every deck; the block "
                "driver refuses istell != 0 outright)", False)
    if f.startswith("process/models/ife"):
        return ("IFE path (ife = 0 on every deck)", False)
    if f == "process/models/availability.py":
        if fn in AVAILABILITY_NONDEFAULT_FUNCS:
            ipa = switches.get("i_plant_availability")
            if ipa == 0:
                return (f"availability branch '{fn}' dead: deck sets "
                        f"i_plant_availability = 0 (Taylor/Ward), this "
                        f"function is reachable only from models 2/3 "
                        f"(V6 branch-liveness check)", False)
            return (f"availability branch '{fn}' LIVE: deck sets "
                    f"i_plant_availability = {ipa}", True)
        return (f"availability read in '{fn}' -- UNCLASSIFIED", True)
    return ("UNCLASSIFIED external read", True)


def classify_scenario(scenario: str) -> dict:
    iccs, minmax, switches = parse_deck(scenario)
    lifted = scenario in PULSED
    icc_eff = sorted(iccs + ([93] if lifted else []))
    n_a28 = A28_N_CONSTRAINTS[scenario]
    a28_path = A28_H5 / scenario / "A1p" / "start000" / "metrics.json"
    a28 = json.loads(a28_path.read_text())
    checks = {
        "parsed_base_icc_count": len(iccs),
        "lift_adds_icc93": lifted,
        "effective_icc_count": len(icc_eff),
        "a28_recorded_n_constraints": a28["n_constraints"],
        "a28_expected_table": n_a28,
        "a28_i_figure_merit": a28["i_figure_merit"],
        "match": (len(icc_eff) == n_a28 == a28["n_constraints"]
                  and a28["i_figure_merit"] == minmax),
        "a28_source": str(a28_path),
    }
    if not checks["match"]:
        raise SystemExit(
            f"{scenario}: parsed icc/minmax disagree with A28's record "
            f"({json.dumps(checks)}).  STOP -- the task brief forbids "
            f"proceeding on a seed-count disagreement."
        )

    creads, icc_fn = constraint_reads_by_icc()
    obj_reads = objective_reads(minmax)
    seeds = set(obj_reads)
    seed_detail = {"objective": sorted(obj_reads)}
    for i in icc_eff:
        if i not in creads:
            raise SystemExit(f"{scenario}: icc {i} has no registered "
                             f"constraint function")
        seeds |= creads[i]
        seed_detail[f"icc_{i}"] = sorted(creads[i])

    nw = json.loads((DATA / "node_writesets.json").read_text())
    per = nw["per_scenario"][scenario]
    census = {n: set(f) for n, f in per["writes_by_node"].items()
              if n not in ("<x_inject>", "objective_constraints")}
    probe = json.loads(
        (A18_HARVEST / scenario / "harvest" / "probe_modules.json").read_text())
    executed = sorted(set(probe["writes_by_node"])
                      - {"<x_inject>", "objective_constraints"})

    reads, dsm_prov, t1 = dsm_reads(scenario)

    def unit_of(n):
        return "power+" if n in POWER_GROUP else n

    def unit_writes(u):
        if u == "power+":
            out = set()
            for n in POWER_GROUP:
                out |= census.get(n, set())
            return out
        return census.get(u, set())

    units = sorted({unit_of(n) for n in executed})
    needed_fields = set(seeds)
    field_consumers = {f: ["seed"] for f in seeds}
    needed: dict[str, dict] = {}
    changed = True
    while changed:
        changed = False
        for u in units:
            if u in needed:
                continue
            hit = sorted(unit_writes(u) & needed_fields)
            if hit:
                needed[u] = {
                    "consumed_writes": hit,
                    "consumed_by": {f: field_consumers.get(f, []) for f in hit},
                }
                for f in reads.get(u, set()):
                    field_consumers.setdefault(f, []).append(u)
                needed_fields |= reads.get(u, set())
                changed = True
    candidate_units = [u for u in units if u not in needed]
    # back to driver-node names, in sequence order
    candidates = []
    for u in candidate_units:
        candidates.extend(POWER_GROUP if u == "power+" else [u])
    candidates = [n for n in SEQUENCE_ORDER if n in candidates]

    # ---- evidence per candidate --------------------------------------
    cand_fields = set()
    for u in candidate_units:
        cand_fields |= unit_writes(u)
    sites_by_field = source_reader_scan(cand_fields) if cand_fields else {}
    evidence = {}
    hard_failures = []
    for u in candidate_units:
        wf = sorted(unit_writes(u))
        ext = {}
        for f in wf:
            rows = []
            for s in sites_by_field.get(f, []):
                cls, live = classify_site(s, u, icc_eff, icc_fn, switches)
                rows.append({**s, "classification": cls, "live": live})
                if live:
                    hard_failures.append((u, f, s, cls))
            if rows:
                ext[f] = rows
        # DSM in-loop readers of this candidate's writes (needed units only:
        # a read by a fellow candidate runs post-solve too)
        dsm_readers = {}
        for f in wf:
            rd = sorted(nu for nu in needed if f in reads.get(nu, set()))
            if rd:
                dsm_readers[f] = rd
                hard_failures.append((u, f, {"file": "DSM"}, f"read by needed unit(s) {rd}"))
        # order within the post-solve sweep: a candidate that READS another
        # candidate's writes must come after it in sequence order
        order_notes = []
        for v in candidate_units:
            if v == u:
                continue
            shared = sorted(reads.get(u, set()) & unit_writes(v))
            if shared:
                iu = min(SEQUENCE_ORDER.index(n) for n in
                         (POWER_GROUP if u == "power+" else [u]))
                iv = min(SEQUENCE_ORDER.index(n) for n in
                         (POWER_GROUP if v == "power+" else [v]))
                order_notes.append({
                    "reads_from_candidate": v,
                    "fields": shared[:8],
                    "writer_precedes_reader_in_sequence": iv < iu,
                })
        evidence[u] = {
            "census_writes": wf,
            "n_census_writes": len(wf),
            "external_source_read_sites": ext,
            "dsm_readers_among_needed_units": dsm_readers,
            "reads_from_other_candidates": order_notes,
            "predicate_read_overlap": sorted(
                set(wf) & (obj_reads | set().union(*(creads[i] for i in icc_eff)))
            ),
        }
    if hard_failures:
        raise SystemExit(
            f"{scenario}: classification found live solve-phase readers of "
            f"candidate outputs -- the crawl and the confirmation disagree, "
            f"which is a finding, not something to paper over: "
            f"{hard_failures[:5]}"
        )

    art_nodes = candidates
    payload = json.dumps(
        {"scenario": scenario, "i_figure_merit": minmax, "icc": icc_eff,
         "post_solve_nodes": art_nodes},
        sort_keys=True, separators=(",", ":"),
    ).encode()
    artifact = {
        "format": "a33-postsolve-1",
        "scenario": scenario,
        "generated_by": "arch_surgery/idf_probe/a33_postsolve.py classify",
        "tree_git_head": _git_head(),
        "tree_git_dirty": _git_dirty(),
        "deck": {
            "path": f"arch_surgery/idf_probe/scenarios/{scenario}.IN.DAT",
            "minmax": minmax,
            "icc_parsed_from_deck": iccs,
            "lift_adds_icc93": lifted,
            "icc_expected_at_runtime": icc_eff,
            "i_figure_merit_expected": minmax,
            "n_constraints_crosscheck": checks,
            "switches_bearing_on_liveness": {
                k: switches.get(k) for k in ("i_plant_availability",
                                             "i_pulsed_plant", "itart")
            },
        },
        "seeds": {
            "n_fields": len(seeds),
            "detail": seed_detail,
        },
        "writer_authority": {
            "path": "arch_surgery/docs/data/node_writesets.json",
            "union_sha256": nw.get("union_sha256"),
            "note": ("run-time write census (PROCESS_IDF_PROBE=modules), "
                     "closed at the _call_models_once boundary -- no "
                     "output()-path write is in it (traps T1/T7)"),
        },
        "dsm": {
            **dsm_prov,
            "analysis_pin": _analysis_pin(),
            "config_used": DSM_EXPORT[scenario],
            "v6_note": (
                "per-deck export" if DSM_EXPORT[scenario] == scenario else
                "the analysis 'tokamak' preset, which matches this deck "
                "exactly (dsm_node_map.json caveat V6, resolved by M100 "
                "per-scenario regeneration)"
            ),
            "t1_probe": t1,
            "t9_note": (
                "read live from the sibling's output/ on the task brief's "
                "explicit instruction; sha256 recorded at read time so any "
                "later regeneration is visible, not silent"
            ),
        },
        "crawl": {
            "rule": ("backward fixpoint from the seeds: a unit is NEEDED "
                     "iff its measured writes intersect the consumed field "
                     "set; a needed unit's DSM reads join that set; every "
                     "unit never needed is a post-solve candidate"),
            "units": units,
            "needed": needed,
            "candidates": candidates,
        },
        "evidence": evidence,
        "post_solve_nodes": art_nodes,
        "nodes_sha256": hashlib.sha256(payload).hexdigest(),
    }
    out = DATA / f"postsolve_{scenario}.json"
    out.write_text(json.dumps(artifact, indent=2))
    print(f"{scenario:24s} minmax {minmax:>3d}  icc_eff {len(icc_eff):2d} "
          f"(A28 cross-check PASS)  seeds {len(seeds):3d} fields  "
          f"post-solve: {art_nodes}")
    return artifact


def stage_classify() -> int:
    print("classify: deriving postsolve_<scenario>.json for", SCENARIOS)
    firstcut = {"costs", "water_use"}
    beyond = {}
    for s in SCENARIOS:
        art = classify_scenario(s)
        extra = sorted(set(art["post_solve_nodes"]) - firstcut)
        missing = sorted(firstcut - set(art["post_solve_nodes"]))
        beyond[s] = {"beyond_first_cut": extra, "first_cut_missing": missing}
        if missing:
            print(f"  !! {s}: the crawl DROPPED a first-cut member "
                  f"{missing} -- the crawl wins; report it")
    print("\nfirst-cut comparison (costs + water_use expected everywhere):")
    for s, r in beyond.items():
        print(f"  {s:24s} beyond first cut: {r['beyond_first_cut']}, "
              f"missing: {r['first_cut_missing']}")
    return 0


# ==========================================================================
# stage: writesets
# ==========================================================================


def _compare_writesets(generated: Path, committed: Path) -> dict:
    g = json.loads(generated.read_text())
    c = json.loads(committed.read_text())
    diff = sorted(
        k for k in set(g) | set(c)
        if k != "tree_git_head" and g.get(k) != c.get(k)
    )
    return {
        "generated": str(generated),
        "committed": str(committed),
        "fields_differing_besides_tree_git_head": diff,
        "match": not diff,
    }


def stage_writesets() -> int:
    """a26-generation write sets for the pulsed decks, control first."""
    work = RUNS / "writesets"
    probe_runs = work / "probe_census"
    control_out = work / "control_out"
    for d in (probe_runs, control_out):
        d.mkdir(parents=True, exist_ok=True)
    record: dict = {"stage": "writesets", "tree_git_head": _git_head(),
                    "controls": [], "generated": []}

    # the probe censuses, copied read-only from the main checkout's A18
    # harvest (their provenance: A18's write census, validated by A32's
    # control for st_regression)
    for s in SCENARIOS:
        src = A18_HARVEST / s / "harvest" / "probe_modules.json"
        dst = probe_runs / s
        dst.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, dst / "probe_modules.json")
        record.setdefault("census_sources", {})[s] = {
            "path": str(src), "sha256": _sha256(src),
        }

    def run_gen(outdir: Path, scenarios, variant=None) -> int:
        cmd = [sys.executable, str(HERE / "a25_writeset.py"),
               "--probe-runs", str(probe_runs), "--out", str(outdir),
               "--scenarios", *scenarios]
        if variant:
            cmd += ["--spec-variant", variant]
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              cwd=str(work))
        (work / f"gen_{variant or 'default'}.log").write_text(
            proc.stdout + proc.stderr)
        print(proc.stdout, end="")
        if proc.returncode:
            print(proc.stderr, end="")
        return proc.returncode

    # (1) CONTROL: the default invocation must regenerate every committed
    # A18-generation write set exactly (every field but tree_git_head).
    rc = run_gen(control_out, SCENARIOS)
    if rc:
        print("control generation failed to run; STOP")
        return 3
    ok = True
    for s in SCENARIOS:
        cmp_ = _compare_writesets(control_out / f"writeset_{s}.json",
                                  DATA / f"writeset_{s}.json")
        cmp_["control"] = f"A18-default regeneration, {s}"
        record["controls"].append(cmp_)
        ok = ok and cmp_["match"]
        print(f"  control {s:24s} "
              f"{'PASS' if cmp_['match'] else 'FAIL: ' + str(cmp_['fields_differing_besides_tree_git_head'])}")
    # (2) CONTROL: the a26 generation for st must regenerate A32's committed
    # artifact exactly (same rule).
    rc = run_gen(control_out, ["st_regression"], variant="a26")
    if rc:
        print("a26 st control generation failed to run; STOP")
        return 3
    cmp_ = _compare_writesets(control_out / "writeset_a26_st_regression.json",
                              DATA / "writeset_a26_st_regression.json")
    cmp_["control"] = "a26 regeneration, st_regression (A32's artifact)"
    record["controls"].append(cmp_)
    ok = ok and cmp_["match"]
    print(f"  control st_regression a26      "
          f"{'PASS' if cmp_['match'] else 'FAIL: ' + str(cmp_['fields_differing_besides_tree_git_head'])}")
    if not ok:
        (work / "writesets_record.json").write_text(json.dumps(record, indent=2))
        print("\nA CONTROL FAILED.  STOP: the a26 generation is not trusted "
              "and nothing was written to docs/data (a failed gate is a "
              "result, not an obstacle).")
        return 3

    # (3) the deliverable: a26-generation write sets for the pulsed decks,
    # straight into docs/data (provenance disclosed inside each artifact by
    # a25_writeset.py itself: spec_variant + ystate_artifact fields).
    rc = run_gen(DATA, sorted(PULSED), variant="a26")
    if rc:
        print("a26 pulsed generation failed; STOP")
        return 3
    for s in sorted(PULSED):
        gen = DATA / f"writeset_a26_{s}.json"
        g = json.loads(gen.read_text())
        ys = json.loads((DATA / f"ystate_a26_{s}.json").read_text())
        a18 = json.loads((DATA / f"writeset_{s}.json").read_text())
        row = {
            "artifact": str(gen),
            "pairs_with_a26_spec": (g.get("ystate_components_sha256")
                                    == ys.get("components_sha256")),
            "subsets_identical_to_a18_generation": (g.get("subsets")
                                                    == a18.get("subsets")),
            "subsets_sha256": g.get("subsets_sha256"),
        }
        record["generated"].append(row)
        print(f"  generated {s:24s} pairs_with_a26_spec="
              f"{row['pairs_with_a26_spec']} subsets_identical_to_a18="
              f"{row['subsets_identical_to_a18_generation']}")
        if not (row["pairs_with_a26_spec"]
                and row["subsets_identical_to_a18_generation"]):
            print("  generated artifact failed its own pairing checks; STOP")
            return 3
    (work / "writesets_record.json").write_text(json.dumps(record, indent=2))
    return 0


# ==========================================================================
# running one PROCESS start (A32's recipe, parameterised on the exclusion)
# ==========================================================================


def run_one_a33(
    scenario: str,
    arm: str,
    outdir: Path,
    *,
    seed: int = 0,
    delta: float | None = None,
    post_solve: Path | None = None,
    node_census: bool = False,
    exit_audit: Path | None = None,
    timeout: int = 5400,
) -> dict:
    """One isolated run, the A28/A32 way, on the a26-mode spec generation.

    The one experimental variable is ``post_solve``: when given,
    ``PROCESS_ARCH_POST_SOLVE`` names the deck's committed classification
    artifact; when ``None`` the variable is absent (env_for clears it).
    ``exit_audit`` defaults to the deck's a26 artifact; the neutrality gate
    passes the A18 one to mirror A32's configuration exactly.
    """
    if outdir.exists():
        shutil.rmtree(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(HERE / "run_one.py"),
        "--scenario", scenario,
        "--mode", "control",
        "--outdir", str(outdir),
        "--expect-tree", str(TREE),
        "--input", str(deck_for(scenario, arm, RUNS / "_decks")),
        "--exit-audit",
        str(exit_audit or DATA / f"ystate_a26_{scenario}.json"),
        "--entry-census",
    ]
    if node_census:
        cmd += ["--node-census"]
    if delta is not None:
        cmd += ["--perturb-delta", repr(delta), "--perturb-seed", str(seed)]
    env = env_for(scenario, arm, RUNS, TAU, None)
    env["PROCESS_ARCH_YSTATE"] = str(DATA / f"ystate_a26_{scenario}.json")
    env["PROCESS_ARCH_WRITESET"] = str(DATA / f"writeset_a26_{scenario}.json")
    if post_solve is not None:
        env["PROCESS_ARCH_POST_SOLVE"] = str(post_solve)
    t0 = time.perf_counter()
    try:
        proc = subprocess.run(cmd, env=env, capture_output=True, text=True,
                              cwd=str(outdir), timeout=timeout)
        rc, out, err = proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        rc, out, err = 124, exc.stdout or "", (exc.stderr or "") + "\nTIMEOUT"
    (outdir / "stdout.log").write_text(out)
    (outdir / "stderr.log").write_text(err)
    mpath = outdir / "metrics.json"
    if not mpath.exists():
        mpath.write_text(json.dumps({
            "scenario": scenario, "mode": "control",
            "status": "no_metrics", "returncode": rc,
            "perturb_delta": delta, "perturb_seed": seed,
        }, indent=2))
    rec = json.loads(mpath.read_text())
    rec["a33_arm"] = arm
    rec["a33_tau"] = TAU
    rec["a33_delta"] = delta
    rec["a33_seed"] = seed
    rec["a33_post_solve"] = str(post_solve) if post_solve else None
    mpath.write_text(json.dumps(rec, indent=2))
    wall = time.perf_counter() - t0
    print(f"  {scenario} {arm} seed={seed} post_solve="
          f"{'ON' if post_solve else 'off'} rc={rc} {wall:6.1f}s "
          f"(wall clock is progress information, not a measurement)",
          flush=True)
    return {"scenario": scenario, "arm": arm, "rc": rc,
            "outdir": str(outdir), "wall_s": wall}


def _ensure_decks() -> int:
    """Derive the pulsed decks' lifted variants (never editing the frozen
    scenarios), exactly as run_a28's decks stage does."""
    decks = RUNS / "_decks"
    have = all((decks / s / f"{s}_lifted.IN.DAT").exists() for s in PULSED)
    if have:
        return 0
    print("deriving lifted decks for the pulsed scenarios:")
    return stage_decks(RUNS, sorted(PULSED), decks)


# ==========================================================================
# stage: validation (the loader's teeth)
# ==========================================================================

_PROBE_SRC = r"""
import json, sys
import process
tree = sys.argv[1]
actual = process.__file__
assert actual.startswith(tree + "/"), "wrong tree: " + actual
from process.main import SingleRun
try:
    sr = SingleRun(sys.argv[2], solver="vmcon", update_obsolete=True)
    sr.run()
    print(json.dumps({"refused": False, "note": "run completed"}))
except Exception as exc:
    print(json.dumps({
        "refused": True,
        "error_type": type(exc).__name__,
        "error": str(exc)[:600],
    }))
"""


def _refusal_probe(scenario: str, arm: str, artifact: dict, outdir: Path,
                   expect_fragment: str) -> dict:
    """Run PROCESS with a deliberately bad artifact; it must refuse."""
    if outdir.exists():
        shutil.rmtree(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    art = outdir / "artifact.json"
    art.write_text(json.dumps(artifact, indent=2))
    deck_src = deck_for(scenario, arm, RUNS / "_decks")
    deck = outdir / deck_src.name
    shutil.copy(deck_src, deck)
    env = env_for(scenario, arm, RUNS, TAU, None)
    env["PROCESS_ARCH_YSTATE"] = str(DATA / f"ystate_a26_{scenario}.json")
    env["PROCESS_ARCH_WRITESET"] = str(DATA / f"writeset_a26_{scenario}.json")
    env["PROCESS_ARCH_POST_SOLVE"] = str(art)
    proc = subprocess.run(
        [sys.executable, "-c", _PROBE_SRC, str(TREE), str(deck)],
        env=env, capture_output=True, text=True, cwd=str(outdir),
        timeout=1800,
    )
    try:
        rec = json.loads(proc.stdout.strip().splitlines()[-1])
    except Exception:
        rec = {"refused": None,
               "error": (proc.stderr or proc.stdout)[-1500:]}
    rec["expect_fragment"] = expect_fragment
    rec["fragment_found"] = expect_fragment in (rec.get("error") or "")
    rec["pass"] = bool(rec.get("refused")) and rec["fragment_found"]
    return rec


def stage_validation() -> int:
    rc = _ensure_decks()
    if rc:
        return rc
    outroot = RUNS / "validation"
    art_st = json.loads((DATA / "postsolve_st_regression.json").read_text())
    art_ltn = json.loads(
        (DATA / "postsolve_large_tokamak_nof.json").read_text())
    probes = {}

    # (a) hand-edited artifact: add a node without regenerating the sha
    bad = json.loads(json.dumps(art_st))
    bad["post_solve_nodes"] = [*bad["post_solve_nodes"], "divertor"]
    probes["hand_edited_sha_mismatch"] = _refusal_probe(
        "st_regression", "A1p", bad, outroot / "hand_edited",
        "does not rebuild")

    # (b) wrong deck: the large_tokamak_nof artifact run on st_regression
    probes["wrong_deck"] = _refusal_probe(
        "st_regression", "A1p", art_ltn, outroot / "wrong_deck",
        "wrong deck")

    # (c) a node the deck keeps per-call: pulse on a pulsed deck, sha
    # regenerated so ONLY the per-call check can refuse it
    bad = json.loads(json.dumps(art_ltn))
    bad["post_solve_nodes"] = ["pulse", *bad["post_solve_nodes"]]
    payload = json.dumps(
        {"scenario": bad["scenario"],
         "i_figure_merit": bad["deck"]["i_figure_merit_expected"],
         "icc": bad["deck"]["icc_expected_at_runtime"],
         "post_solve_nodes": bad["post_solve_nodes"]},
        sort_keys=True, separators=(",", ":")).encode()
    bad["nodes_sha256"] = hashlib.sha256(payload).hexdigest()
    probes["per_call_node_refused"] = _refusal_probe(
        "large_tokamak_nof", "A1p", bad, outroot / "per_call",
        "keeps 'pulse' per-call")

    # (d) unknown node, sha regenerated so only the node-map check can refuse
    bad = json.loads(json.dumps(art_st))
    bad["post_solve_nodes"] = [*bad["post_solve_nodes"], "not_a_node"]
    payload = json.dumps(
        {"scenario": bad["scenario"],
         "i_figure_merit": bad["deck"]["i_figure_merit_expected"],
         "icc": bad["deck"]["icc_expected_at_runtime"],
         "post_solve_nodes": bad["post_solve_nodes"]},
        sort_keys=True, separators=(",", ":")).encode()
    bad["nodes_sha256"] = hashlib.sha256(payload).hexdigest()
    probes["unknown_node_refused"] = _refusal_probe(
        "st_regression", "A1p", bad, outroot / "unknown_node",
        "not _call_models_once call sites")

    n_pass = sum(1 for p in probes.values() if p["pass"])
    record = {
        "stage": "validation (loader refusal teeth)",
        "tree_git_head": _git_head(),
        "probes": probes,
        "n_probes": len(probes),
        "n_refused_as_required": n_pass,
        "verdict": "PASS" if n_pass == len(probes) else "FAIL",
    }
    outroot.mkdir(parents=True, exist_ok=True)
    (outroot / "validation.json").write_text(json.dumps(record, indent=2))
    for k, p in probes.items():
        print(f"  {k:28s} refused={p.get('refused')} "
              f"fragment_found={p.get('fragment_found')} -> "
              f"{'PASS' if p['pass'] else 'FAIL'}")
    print(f"validation verdict: {record['verdict']} "
          f"({n_pass}/{len(probes)} probes refused as required)")
    return 0 if record["verdict"] == "PASS" else 1


# ==========================================================================
# stage: gate (protocol-12 switch-neutrality against A32's record)
# ==========================================================================


def stage_gate() -> int:
    """Env unset, A1' st_regression start000 under the a26 spec must
    reproduce A32's recorded start000 bit-for-bit, teeth included."""
    outdir = RUNS / "gate" / "A1p_start000"
    r = run_one_a33("st_regression", "A1p", outdir, seed=0, delta=DELTA_GATE,
                    post_solve=None,
                    exit_audit=DATA / "ystate_st_regression.json")
    ref = gate_extract(json.loads(A32_REF.read_text()))
    got = gate_extract(json.loads((outdir / "metrics.json").read_text()))
    verdict = gate_compare(ref, got)
    teeth = gate_teeth(ref, got)
    record = {
        "gate": "A33 switch-neutrality against A32's a26-spec record "
                "(protocol 12)",
        "reference": {"path": str(A32_REF), "sha256": _sha256(A32_REF)},
        "run": {"outdir": str(outdir), "rc": r["rc"]},
        "comparison": verdict,
        "teeth": teeth,
        "verdict": ("PASS" if (verdict["pass"] and teeth["all_tripped"]
                               and r["rc"] == 0) else "FAIL"),
    }
    (RUNS / "gate").mkdir(parents=True, exist_ok=True)
    (RUNS / "gate" / "gate.json").write_text(json.dumps(record, indent=2))
    print(json.dumps(record, indent=2))
    return 0 if record["verdict"] == "PASS" else 1


# ==========================================================================
# stage: fullrun (the strong equivalence gate) and its tally
# ==========================================================================

#: Fields that must be EXACTLY equal between the WITH and WITHOUT runs.
#: Counts and hex floats only -- never a timing (trap T5).
FULLRUN_EQUAL_FIELDS = (
    "status",
    "norm_objf_hex",
    "sqsumsq_hex",
    "xcm_hex",
    "rcm_hex",
    "ifail",
    "n_solver_iterations",
    "n_call_models",
    "outer_pass_hist",
    "block_sweeps",
    "inner_sweeps_by_block",
    "exit_audit_residual_max_hex",
)


def _fullrun_extract(metrics: dict) -> dict:
    t = metrics.get("module_solve_totals") or {}
    ex = metrics.get("exact") or {}
    nc = metrics.get("node_census") or {}
    return {
        "status": metrics.get("status"),
        "norm_objf_hex": ex.get("norm_objf"),
        "sqsumsq_hex": ex.get("sqsumsq"),
        "xcm_hex": ex.get("xcm"),
        "rcm_hex": ex.get("rcm"),
        "ifail": (metrics.get("mfile") or {}).get("ifail"),
        "n_solver_iterations": metrics.get("n_solver_iterations"),
        "n_call_models": t.get("n_call_models"),
        "outer_pass_hist": t.get("outer_pass_hist"),
        "block_sweeps": t.get("block_sweeps"),
        "inner_sweeps_by_block": t.get("inner_sweeps_by_block"),
        "exit_audit_residual_max_hex": (
            (metrics.get("exit_audit") or {}).get("residual_max_hex")),
        "node_calls_solve_phase": metrics.get("node_calls_solve_phase"),
        "node_calls_total": metrics.get("node_calls_total"),
        "per_node": nc.get("per_node_counted_through_Caller_node"),
        "post_solve_totals": metrics.get("post_solve_totals"),
        "arch_hoist_tails_resolved": metrics.get("arch_hoist_tails_resolved"),
    }


def _fullrun_compare(scenario: str, ref: dict, got: dict,
                     excluded: list[str]) -> dict:
    """WITHOUT (ref) against WITH (got), per field, with the node-call
    ledger reconciled against the driver's own suppression counts."""
    per_field = {}
    for f in FULLRUN_EQUAL_FIELDS:
        per_field[f] = {"without": ref[f], "with": got[f],
                        "match": ref[f] == got[f]}
        if f in ("xcm_hex", "rcm_hex") and per_field[f]["match"]:
            per_field[f] = {"without": f"[{len(ref[f] or [])} hex]",
                            "with": "identical", "match": True}
    pst = got.get("post_solve_totals") or {}
    suppressed = pst.get("n_call_sites_suppressed")
    by_node = pst.get("suppressed_by_node") or {}
    ledger = {
        "node_calls_solve_phase_without": ref["node_calls_solve_phase"],
        "node_calls_solve_phase_with": got["node_calls_solve_phase"],
        "difference": (ref["node_calls_solve_phase"] or 0)
        - (got["node_calls_solve_phase"] or 0),
        "driver_reported_suppressed_call_sites": suppressed,
        "suppressed_by_node": by_node,
        "match": ((ref["node_calls_solve_phase"] or 0)
                  - (got["node_calls_solve_phase"] or 0)) == suppressed,
    }
    per_node = {}
    per_node_ok = True
    if ref.get("per_node") and got.get("per_node"):
        for n in sorted(set(ref["per_node"]) | set(got["per_node"])):
            a = ref["per_node"].get(n, 0)
            b = got["per_node"].get(n, 0)
            want = (by_node.get(n, 0) - 1) if n in excluded else 0
            row_ok = (a - b) == want
            per_node_ok = per_node_ok and row_ok
            per_node[n] = {"without": a, "with": b, "delta": a - b,
                           "expected_delta": want, "match": row_ok,
                           "excluded": n in excluded}
    all_equal = all(v["match"] for v in per_field.values())
    return {
        "scenario": scenario,
        "excluded_nodes": excluded,
        "fields_compared": len(per_field),
        "fields_matching": sum(1 for v in per_field.values() if v["match"]),
        "per_field": per_field,
        "node_call_ledger": ledger,
        "per_node_census": per_node,
        "per_node_census_reconciles": per_node_ok,
        "pass": bool(all_equal and ledger["match"] and per_node_ok),
    }


def _fullrun_teeth(scenario: str, ref: dict, got: dict,
                   excluded: list[str]) -> dict:
    """Perturb the comparator's own inputs, one field at a time; each must
    trip (protocol 12: shown able to fail before its zeros are accepted)."""
    import math
    trials = {}

    p = json.loads(json.dumps(ref))
    p["norm_objf_hex"] = math.nextafter(
        float.fromhex(p["norm_objf_hex"]), math.inf).hex()
    trials["norm_objf+1ulp"] = not _fullrun_compare(
        scenario, p, got, excluded)["pass"]

    p = json.loads(json.dumps(ref))
    p["n_call_models"] = (p["n_call_models"] or 0) + 1
    trials["n_call_models+1"] = not _fullrun_compare(
        scenario, p, got, excluded)["pass"]

    p = json.loads(json.dumps(ref))
    if p["rcm_hex"]:
        p["rcm_hex"] = list(p["rcm_hex"])
        p["rcm_hex"][0] = math.nextafter(
            float.fromhex(p["rcm_hex"][0]), math.inf).hex()
    trials["rcm[0]+1ulp"] = not _fullrun_compare(
        scenario, p, got, excluded)["pass"]

    p = json.loads(json.dumps(ref))
    p["node_calls_solve_phase"] = (p["node_calls_solve_phase"] or 0) + 1
    trials["node_calls_solve_phase+1"] = not _fullrun_compare(
        scenario, p, got, excluded)["pass"]

    return {
        "n_perturbations": len(trials),
        "n_tripped": sum(1 for v in trials.values() if v),
        "all_tripped": all(trials.values()),
        "per_perturbation": trials,
    }


def stage_fullrun(scenarios=None) -> int:
    rc = _ensure_decks()
    if rc:
        return rc
    scenarios = scenarios or SCENARIOS
    results = {}
    worst = 0
    for s in scenarios:
        art = DATA / f"postsolve_{s}.json"
        excluded = json.loads(art.read_text())["post_solve_nodes"]
        root = RUNS / "fullrun" / s
        r_without = run_one_a33(s, "A1p", root / "without", delta=None,
                                post_solve=None, node_census=True)
        r_with = run_one_a33(s, "A1p", root / "with", delta=None,
                             post_solve=art, node_census=True)
        ref = _fullrun_extract(json.loads(
            (root / "without" / "metrics.json").read_text()))
        got = _fullrun_extract(json.loads(
            (root / "with" / "metrics.json").read_text()))
        cmp_ = _fullrun_compare(s, ref, got, excluded)
        teeth = _fullrun_teeth(s, ref, got, excluded)
        verdict = ("PASS" if (cmp_["pass"] and teeth["all_tripped"]
                              and r_without["rc"] == 0 and r_with["rc"] == 0)
                   else "FAIL")
        results[s] = {"comparison": cmp_, "teeth": teeth,
                      "rc_without": r_without["rc"], "rc_with": r_with["rc"],
                      "verdict": verdict}
        if verdict != "PASS":
            worst = 1
            bad = [f for f, v in cmp_["per_field"].items() if not v["match"]]
            print(f"  {s}: FULL-RUN GATE FAILED -- diverging fields: {bad}; "
                  f"ledger match={cmp_['node_call_ledger']['match']}; "
                  f"per-node reconciles={cmp_['per_node_census_reconciles']}."
                  f"  The classification is wrong for this deck; that is the "
                  f"result, not something to tune.")
        else:
            led = cmp_["node_call_ledger"]
            print(f"  {s}: PASS -- {cmp_['fields_matching']}/"
                  f"{cmp_['fields_compared']} fields bit-identical; solve "
                  f"phase {led['node_calls_solve_phase_without']} -> "
                  f"{led['node_calls_solve_phase_with']} node calls "
                  f"(-{led['difference']}, = suppressed sites); teeth "
                  f"{teeth['n_tripped']}/{teeth['n_perturbations']}")
    (RUNS / "fullrun").mkdir(parents=True, exist_ok=True)
    (RUNS / "fullrun" / "fullrun_summary.json").write_text(
        json.dumps({"tau": TAU, "delta": None, "results": results}, indent=2))
    return worst


def stage_tally() -> int:
    """Re-derive the fullrun comparison from the run records on disk."""
    worst = 0
    for s in SCENARIOS:
        root = RUNS / "fullrun" / s
        if not (root / "without" / "metrics.json").exists():
            print(f"  {s}: no fullrun records")
            continue
        excluded = json.loads(
            (DATA / f"postsolve_{s}.json").read_text())["post_solve_nodes"]
        ref = _fullrun_extract(json.loads(
            (root / "without" / "metrics.json").read_text()))
        got = _fullrun_extract(json.loads(
            (root / "with" / "metrics.json").read_text()))
        cmp_ = _fullrun_compare(s, ref, got, excluded)
        print(f"  {s:24s} fields {cmp_['fields_matching']}/"
              f"{cmp_['fields_compared']} ledger "
              f"{cmp_['node_call_ledger']['match']} per-node "
              f"{cmp_['per_node_census_reconciles']} -> "
              f"{'PASS' if cmp_['pass'] else 'FAIL'}")
        worst = worst or (0 if cmp_["pass"] else 1)
    return worst


# ==========================================================================


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["classify", "writesets", "validation",
                                      "gate", "fullrun", "tally", "all"])
    ap.add_argument("--scenarios", nargs="*", default=None,
                    help="fullrun only: restrict the decks")
    args = ap.parse_args()
    RUNS.mkdir(parents=True, exist_ok=True)
    (RUNS / "_mplconfig").mkdir(exist_ok=True)
    if _git_dirty():
        print("NOTE: tree is dirty; campaign-class stages should run from "
              "the clean committed tree (metrics stamp tree_git_dirty).")

    if args.stage == "classify":
        return stage_classify()
    if args.stage == "writesets":
        return stage_writesets()
    if args.stage == "validation":
        return stage_validation()
    if args.stage == "gate":
        return stage_gate()
    if args.stage == "fullrun":
        return stage_fullrun(args.scenarios)
    if args.stage == "tally":
        return stage_tally()
    for fn in (stage_classify, stage_writesets, stage_validation, stage_gate,
               stage_fullrun):
        rc = fn()
        if rc != 0:
            return rc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
