"""Which model nodes the optimiser never consumes, derived rather than asserted.

The **per-run deferral set** is the list of model nodes whose outputs nothing the
optimiser decides on ever reads: not the objective, not an active constraint,
and not any model that runs while the optimiser is working.  Such a node cannot
change anything the optimiser does, so running it once per evaluation is pure
cost, and it is run **once per run** instead, at the accepted optimum.  Membership
is not a judgement call: it is derived, and the derivation is this module.

The derivation, in four steps
-----------------------------
1. **Seeds** — what the optimiser's own layer reads: the active figure of
   merit's branch of the objective function, plus every *active* constraint's
   read set, taken by parsing the source rather than by searching its text.
2. **Backward closure** — a node is *needed* if anything it writes is in the
   consumed set; when a node becomes needed, everything it reads joins that set.
   Repeat until nothing changes.  What each node writes is the runtime write
   census — measured, because what a node writes cannot be read off its source
   with any confidence.  What each node reads is a source scan of the tree under
   test.
3. **Candidates** — every node that never became needed.
4. **Confirmation** — for every field a candidate writes, every read site of that
   field anywhere in the tree is found and classified.  A site that cannot be
   classified, or that is classified live, is a **finding**: the closure and the
   confirmation disagree, and the derivation says so rather than preferring one.

Reads are attributed by enclosing class, not by file
-----------------------------------------------------
This is the correction the improvement list asks for, and it is not cosmetic.
The previous derivation decided whether a read site was "internal to the
candidate" by testing the file path against a prefix.  One file holds two
classes — the vacuum pumping model, which is a deferral candidate, and the
vacuum vessel, which is a live plant node — so a read of a pumping output made
inside the vessel class would have been classified *internal to the candidate*
and the node marked dead.  Nothing would have warned.  Here every site is
attributed to the class that encloses it, and the class-to-node map is derived
from the driver's own model container rather than transcribed.

Where a site has no enclosing class — a module-level helper — or its class maps
to no node, the site is attributed to **every node whose class is defined in that
file**.  That is the old file rule, applied only where class-level attribution
has nothing to say, and it errs towards keeping a node in the loop: attributing a
read too widely can only add needed nodes, never hide a reader.

Derived from ``arch_surgery/idf_probe/a33_postsolve.py`` (``classify``) at
``f1f90c20``, with three changes: the class-level attribution above; the
reachability layer is a source scan of the tree under test rather than a live
read of a sibling repository's generated exports, which this project's own trap
register forbids and which are not committed here; and a disagreement is
reported rather than raised.  Task **A51 (harness-artifacts)**.
"""

from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .artifacts import StageCheck, figures_of_merit, load, rebuild_nodes_sha256
from .config import Campaign, Config

#: Where this stage's records go.  Untracked, like every run artifact.
RUNS_SUBPATH = "per_run"

#: The constraint number the burn-time lift adds.
LIFT_CONSTRAINT = 93

#: Nodes that are not model calls and never candidates: the injection of the
#: design vector, and the objective/constraint block, which *is* the predicate.
NOT_A_MODEL_NODE = ("<x_inject>", "objective_constraints")

#: The three call sites that share one model object.  They are one unit for the
#: closure — they read and write through the same class — and are reported
#: individually, because the deferral artifact names call sites.
POWER_GROUP = ("power", "power.acpow", "power.plant_electric_production")

#: Directories of the tree whose reads are not model reads: the data structure
#: itself, and the input/output layer.
SKIPPED_TREE_PARTS = ("data_structure", "io")

#: Functions of the availability model reachable only from its non-default
#: plant-availability branches.  With the configuration on the default branch
#: they are dead code, and a read inside one is not a live read.  Derived by
#: reading the model's own dispatch; transcribed from the previous derivation at
#: ``f1f90c20`` and re-checked against the source by :func:`availability_branches`.
AVAILABILITY_NONDEFAULT_FUNCTIONS = {
    "avail_2",
    "avail_st",
    "calc_u_unplanned_vacuum",
    "calc_u_planned",
    "calc_u_unplanned_magnets",
    "calc_u_unplanned_divertor",
    "calc_u_unplanned_fwbs",
    "calc_u_unplanned_bop",
    "calc_u_unplanned_hcd",
    "avail_st_divertor",
    "avail_st_centrepost",
}


class PostSolveError(RuntimeError):
    """A refusal to derive, or to compare, a per-run deferral set."""


# ==========================================================================
# node <-> class, derived from the driver's own model container
# ==========================================================================

_INVOCATION_RE = re.compile(r"models\.(\w+)")


def node_attributes(node_map: Mapping[str, Any]) -> dict[str, str]:
    """Node name -> the attribute of the model container it invokes.

    Read from the committed node map's own ``invocation`` field, so the mapping
    is the one the map records rather than a second transcription of it.
    """
    out: dict[str, str] = {}
    for name, entry in node_map["nodes"].items():
        if name in NOT_A_MODEL_NODE:
            continue
        match = _INVOCATION_RE.search(entry.get("invocation") or "")
        if match:
            out[name] = match.group(1)
    return out


def container_classes(tree: Path) -> tuple[dict[str, set[str]], dict[str, Any]]:
    """Model-container attribute -> the classes that attribute can be.

    Parsed from the container's own constructor: ``self.<attribute> =
    <Class>(...)``.  Two shapes need more than the assignment itself:

    * an attribute built from other attributes — the plasma model is
      constructed from a dozen of them — **owns their classes too**, because a
      read inside one of those objects happens while that node is executing;
    * an attribute that is a property rather than an assignment — the cost model
      is chosen at run time between two implementations — owns the classes of
      every private attribute the property can return.

    Both are read from the source; neither is a table here.
    """
    source = Path(tree) / "process" / "main.py"
    module = ast.parse(source.read_text())
    container = None
    for node in ast.walk(module):
        if isinstance(node, ast.ClassDef) and node.name == "Models":
            container = node
    if container is None:
        raise PostSolveError(
            f"{source} has no model container class: the class-to-node map "
            f"would have to be transcribed, which is the drift this "
            f"derivation exists to remove"
        )

    direct: dict[str, str] = {}
    arguments: dict[str, set[str]] = {}
    for node in ast.walk(container):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not (
            isinstance(target, ast.Attribute)
            and isinstance(target.value, ast.Name)
            and target.value.id == "self"
        ):
            continue
        value = node.value
        if not (isinstance(value, ast.Call) and isinstance(value.func, ast.Name)):
            continue
        direct[target.attr] = value.func.id
        referenced: set[str] = set()
        for argument in list(value.args) + [kw.value for kw in value.keywords]:
            if (
                isinstance(argument, ast.Attribute)
                and isinstance(argument.value, ast.Name)
                and argument.value.id == "self"
            ):
                referenced.add(argument.attr)
        arguments[target.attr] = referenced

    properties: dict[str, set[str]] = {}
    for node in container.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        if not any(
            isinstance(d, ast.Name) and d.id == "property" for d in node.decorator_list
        ):
            continue
        referenced = set()
        for inner in ast.walk(node):
            if (
                isinstance(inner, ast.Attribute)
                and isinstance(inner.value, ast.Name)
                and inner.value.id == "self"
                and inner.attr in direct
            ):
                referenced.add(inner.attr)
        if referenced:
            properties[node.name] = referenced

    def closure(attribute: str, seen: set[str]) -> set[str]:
        if attribute in seen:
            return set()
        seen.add(attribute)
        out: set[str] = set()
        if attribute in direct:
            out.add(direct[attribute])
        for other in arguments.get(attribute, set()) | properties.get(attribute, set()):
            out |= closure(other, seen)
        return out

    owned = {
        attribute: closure(attribute, set())
        for attribute in set(direct) | set(properties)
    }
    diagnostics = {
        "source": str(source),
        "n_attributes_assigned": len(direct),
        "n_attributes_from_properties": len(properties),
        "properties": {k: sorted(v) for k, v in sorted(properties.items())},
        "note": (
            "an attribute owns the classes of the objects it is constructed "
            "from, because a read inside one of those objects happens while "
            "this node is executing"
        ),
    }
    return owned, diagnostics


def class_to_nodes(tree: Path, node_map: Mapping[str, Any]) -> tuple[dict, dict]:
    """Class name -> the node(s) whose execution can reach it."""
    attributes = node_attributes(node_map)
    owned, diagnostics = container_classes(tree)
    mapping: dict[str, set[str]] = {}
    unresolved: list[str] = []
    for node, attribute in attributes.items():
        classes = owned.get(attribute)
        if not classes:
            unresolved.append(f"{node} -> models.{attribute}")
            continue
        for name in classes:
            mapping.setdefault(name, set()).add(node)
    diagnostics = {
        **diagnostics,
        "n_nodes": len(attributes),
        "n_classes_mapped": len(mapping),
        "nodes_with_no_class": sorted(unresolved),
    }
    return mapping, diagnostics


# ==========================================================================
# the source scan: every read site, with the class that encloses it
# ==========================================================================


@dataclass(frozen=True)
class Site:
    """One read of one data-structure field, and where it is."""

    file: str
    line: int
    enclosing_class: str | None
    function: str
    field: str
    #: Reachable from a reporting entry point and from no node entry point:
    #: the read happens after the analysis loop, not inside it (traps T1/T7).
    output_only: bool = False
    #: In a file no configuration here executes.
    dead_path: bool = False


class _Reads(ast.NodeVisitor):
    """``data.<namespace>.<field>`` attribute loads.

    A parser, never a text search: ``= `` matches ``==``, and a pattern over
    these files reports comparisons as accesses (trap T2).
    """

    def __init__(self) -> None:
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


def _enclosures(module: ast.Module) -> tuple[list[tuple], list[tuple]]:
    classes = [
        (node.lineno, node.end_lineno, node.name)
        for node in ast.walk(module)
        if isinstance(node, ast.ClassDef)
    ]
    functions = [
        (node.lineno, node.end_lineno, node.name)
        for node in ast.walk(module)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    return classes, functions


def _innermost(spans: Sequence[tuple], line: int) -> str | None:
    hits = [span for span in spans if span[0] <= line <= span[1]]
    if not hits:
        return None
    hits.sort(key=lambda span: span[1] - span[0])
    return hits[0][2]


#: Method names a model node is entered through.  Derived from the committed
#: node map's own ``invocation`` strings, plus the first-wall geometry prime,
#: which the driver calls at the head of every sweep and is therefore on the
#: solve path even though it is not a node.
PRIME_METHOD = "set_fw_geometry"


def entry_methods(node_map: Mapping[str, Any]) -> set[str]:
    """The method names one pass over the model sequence calls."""
    methods = {PRIME_METHOD}
    for name, entry in node_map["nodes"].items():
        if name in NOT_A_MODEL_NODE:
            continue
        match = re.search(r"models\.\w+\.(\w+)", entry.get("invocation") or "")
        if match:
            methods.add(match.group(1))
    return methods


def _call_closure(
    methods: Mapping[str, ast.AST], roots: Iterable[str], *, on_self: bool
) -> set[str]:
    """Which of *methods* are reachable from *roots* through local calls."""
    edges: dict[str, set[str]] = {}
    for name, node in methods.items():
        called: set[str] = set()
        for inner in ast.walk(node):
            if not isinstance(inner, ast.Call):
                continue
            function = inner.func
            if on_self:
                if (
                    isinstance(function, ast.Attribute)
                    and isinstance(function.value, ast.Name)
                    and function.value.id == "self"
                    and function.attr in methods
                ):
                    called.add(function.attr)
            elif isinstance(function, ast.Name) and function.id in methods:
                called.add(function.id)
        edges[name] = called
    reached: set[str] = set()
    stack = [r for r in roots if r in methods]
    while stack:
        name = stack.pop()
        if name in reached:
            continue
        reached.add(name)
        stack.extend(edges.get(name, ()))
    return reached


def output_only_functions(
    module: ast.Module, roots: set[str]
) -> set[tuple[str | None, str]]:
    """``(class, function)`` pairs reachable only from a reporting method.

    Ten model objects call their own ``run()`` from inside their ``output()``
    method, so "was this read taken during the analysis loop?" cannot be
    answered by asking whether the enclosing function is called at all.  It is
    answered here the way the driver's own instrument answers it: a function
    reachable from a reporting entry point and **not** from any node entry point
    is off the solve path, and a read inside it is not a dependency.  The three
    times this project has invented an edge, this is the rule that was missing
    (traps T1 and T7).
    """
    excluded: set[tuple[str | None, str]] = set()
    for node in ast.walk(module):
        if not isinstance(node, ast.ClassDef):
            continue
        methods = {
            child.name: child
            for child in node.body
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        reporting = {
            name
            for name in methods
            if name == "output" or name.startswith("output_")
        }
        if not reporting:
            continue
        from_run = _call_closure(methods, roots, on_self=True)
        from_output = _call_closure(methods, reporting, on_self=True)
        for name in from_output - from_run:
            excluded.add((node.name, name))
    return excluded


def dead_branch_functions(settings: Mapping[str, int]) -> set[str]:
    """Function names this configuration's own switches make unreachable.

    One family today: the plant-availability model has three implementations and
    each configuration selects one.  Every configuration here selects the
    default, so the two others' functions are dead code, and a read inside one
    is not a live read of the field it names.  The list is checked against the
    source by :func:`availability_branches`, so a renamed function shows up as a
    disagreement rather than as a silently empty exclusion.
    """
    if settings.get("i_plant_availability") in (2, 3):
        return set()
    return set(AVAILABILITY_NONDEFAULT_FUNCTIONS)


#: Files no configuration in this experiment executes: a different confinement
#: concept and a different fusion approach.  The block driver refuses the first
#: outright.
DEAD_PATH_FILE_MARKERS = ("stellarator", "models/ife.py", "neoclassics")


def scan_reads(
    tree: Path, roots: set[str]
) -> tuple[list[Site], dict[str, set[str]], dict[str, Any]]:
    """Every ``<x>.<namespace>.<field>`` read in the tree, with its enclosure.

    Deliberately wider than ``data.``-rooted accesses: any attribute chain
    ending in a two-level ``namespace.field`` counts.  A missed reader is the
    dangerous direction — it would let a live node be marked dead — and a
    spurious one only gets classified.

    Each site is flagged with the two things that decide whether it is a read on
    the solve path at all: whether its function is reachable only from a
    reporting entry point, and whether its file is one no configuration here
    executes.

    Also returns, per file, the set of classes defined in it, which is what the
    fallback attribution needs where a site has no class of its own.
    """
    sites: list[Site] = []
    classes_by_file: dict[str, set[str]] = {}
    root = Path(tree)
    n_output_only = n_dead_path = 0
    output_only_pairs: set[tuple[str | None, str]] = set()
    for path in sorted((root / "process").rglob("*.py")):
        parts = path.relative_to(root).parts
        if any(part in SKIPPED_TREE_PARTS for part in parts):
            continue
        try:
            module = ast.parse(path.read_text())
        except SyntaxError:
            continue
        relative = str(path.relative_to(root))
        dead_path = any(marker in relative for marker in DEAD_PATH_FILE_MARKERS)
        class_spans, function_spans = _enclosures(module)
        classes_by_file[relative] = {name for _, _, name in class_spans}
        reporting_only = output_only_functions(module, roots)
        output_only_pairs |= reporting_only
        for node in ast.walk(module):
            if not (
                isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load)
            ):
                continue
            inner = node.value
            if not isinstance(inner, ast.Attribute):
                continue
            enclosing_class = _innermost(class_spans, node.lineno)
            function = _innermost(function_spans, node.lineno) or "<module>"
            output_only = (enclosing_class, function) in reporting_only
            n_output_only += int(output_only)
            n_dead_path += int(dead_path)
            sites.append(
                Site(
                    file=relative,
                    line=node.lineno,
                    enclosing_class=enclosing_class,
                    function=function,
                    field=f"{inner.attr}.{node.attr}",
                    output_only=output_only,
                    dead_path=dead_path,
                )
            )
    diagnostics = {
        "n_sites": len(sites),
        "n_sites_on_a_reporting_path_only": n_output_only,
        "n_sites_in_a_path_no_configuration_executes": n_dead_path,
        "n_functions_reachable_only_from_a_reporting_entry_point": len(
            output_only_pairs
        ),
        "node_entry_methods": sorted(roots),
        "dead_path_markers": list(DEAD_PATH_FILE_MARKERS),
    }
    return sites, classes_by_file, diagnostics


def reads_by_node(
    sites: Iterable[Site],
    class_map: Mapping[str, set[str]],
    classes_by_file: Mapping[str, set[str]],
    *,
    fields: set[str] | None = None,
    dead_functions: set[str] | None = None,
) -> tuple[dict[str, set[str]], dict[str, Any]]:
    """Per node, every field a read site attributable to it touches.

    *fields* restricts the result to a known field set — the union of what the
    census saw written plus the seeds — so that attribute chains that merely
    look like a data-structure access do not enter the closure.

    Three kinds of site are excluded, each counted: a read on a reporting path
    only, a read in a file no configuration here executes, and a read inside a
    function this configuration's own switches make unreachable.  All three are
    *branch liveness*, and leaving them in would make every node needed and the
    derivation vacuous — but each is also the direction in which a mistake marks
    a live node dead, so each is counted and named rather than applied quietly.
    """
    dead_functions = dead_functions or set()
    per_node: dict[str, set[str]] = {}
    n_attributed_by_class = n_attributed_by_file = n_unattributed = 0
    n_excluded_reporting = n_excluded_dead_path = n_excluded_dead_branch = 0
    unattributed_files: dict[str, int] = {}
    for site in sites:
        if fields is not None and site.field not in fields:
            continue
        if site.output_only:
            n_excluded_reporting += 1
            continue
        if site.dead_path:
            n_excluded_dead_path += 1
            continue
        if site.function in dead_functions:
            n_excluded_dead_branch += 1
            continue
        owners = class_map.get(site.enclosing_class or "", set())
        if owners:
            n_attributed_by_class += 1
        else:
            owners = set()
            for name in classes_by_file.get(site.file, set()):
                owners |= class_map.get(name, set())
            if owners:
                n_attributed_by_file += 1
            else:
                n_unattributed += 1
                unattributed_files[site.file] = (
                    unattributed_files.get(site.file, 0) + 1
                )
                continue
        for node in owners:
            per_node.setdefault(node, set()).add(site.field)
    diagnostics = {
        "n_sites_attributed_by_enclosing_class": n_attributed_by_class,
        "n_sites_attributed_by_file_fallback": n_attributed_by_file,
        "n_sites_attributed_to_no_node": n_unattributed,
        "n_sites_excluded_reporting_path_only": n_excluded_reporting,
        "n_sites_excluded_path_not_executed": n_excluded_dead_path,
        "n_sites_excluded_dead_branch": n_excluded_dead_branch,
        "dead_branch_functions": sorted(dead_functions),
        "files_with_no_mapped_class": dict(
            sorted(unattributed_files.items(), key=lambda kv: -kv[1])[:20]
        ),
        "rule": (
            "a read site belongs to the node(s) its enclosing class maps to; "
            "a site with no class, or a class that maps to no node, belongs to "
            "every node whose class is defined in the same file"
        ),
    }
    return per_node, diagnostics


# ==========================================================================
# the seeds: what the optimiser's own layer reads
# ==========================================================================


def constraint_reads_by_number(tree: Path) -> tuple[dict[int, set[str]], dict[int, str]]:
    """``{constraint number: fields read}``, closed over local helper calls.

    A constraint that delegates to a helper in the same file owns the helper's
    reads: the read happens because that constraint was evaluated.
    """
    source = Path(tree) / "process" / "core" / "solver" / "constraints.py"
    module = ast.parse(source.read_text())
    functions: dict[str, ast.FunctionDef] = {}
    by_number: dict[int, str] = {}
    for node in module.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        functions[node.name] = node
        for decorator in node.decorator_list:
            if (
                isinstance(decorator, ast.Call)
                and isinstance(decorator.func, ast.Attribute)
                and decorator.func.attr == "register_constraint"
                and decorator.args
                and isinstance(decorator.args[0], ast.Constant)
            ):
                by_number[int(decorator.args[0].value)] = node.name
    direct: dict[str, set[str]] = {}
    calls: dict[str, set[str]] = {}
    for name, function in functions.items():
        visitor = _Reads()
        visitor.visit(function)
        direct[name] = visitor.reads
        called = set()
        for node in ast.walk(function):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in functions
            ):
                called.add(node.func.id)
        calls[name] = called

    def closure(name: str, seen: set[str]) -> set[str]:
        if name in seen:
            return set()
        seen.add(name)
        out = set(direct[name])
        for other in calls[name]:
            out |= closure(other, seen)
        return out

    return (
        {number: closure(name, set()) for number, name in by_number.items()},
        by_number,
    )


def objective_reads(tree: Path, figure_of_merit: int) -> set[str]:
    """The active figure of merit's own branch of the objective function."""
    from .artifacts import _objective_branch_reads  # noqa: PLC0415 - one direction

    source = Path(tree) / "process" / "core" / "solver" / "objectives.py"
    module = ast.parse(source.read_text())
    function = None
    for node in ast.walk(module):
        if isinstance(node, ast.FunctionDef) and node.name == "objective_function":
            function = node
    if function is None:
        raise PostSolveError(f"{source} has no objective_function")
    name = figures_of_merit(tree)[abs(int(figure_of_merit))]
    return _objective_branch_reads(function, name, _Reads)


def availability_branches(tree: Path) -> dict[str, Any]:
    """Whether the transcribed non-default branch list still names real functions."""
    source = Path(tree) / "process" / "models" / "availability.py"
    module = ast.parse(source.read_text())
    defined = {
        node.name
        for node in ast.walk(module)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    missing = sorted(AVAILABILITY_NONDEFAULT_FUNCTIONS - defined)
    return {
        "n_declared": len(AVAILABILITY_NONDEFAULT_FUNCTIONS),
        "n_found_in_source": len(AVAILABILITY_NONDEFAULT_FUNCTIONS) - len(missing),
        "declared_but_absent": missing,
        "agrees": not missing,
    }


# ==========================================================================
# classifying one read site of a candidate's output
# ==========================================================================


def classify_site(
    site: Site,
    *,
    candidate: str,
    candidates: set[str],
    needed: set[str],
    class_map: Mapping[str, set[str]],
    active_constraints: Sequence[int],
    constraint_functions: Mapping[int, str],
    settings: Mapping[str, int],
) -> tuple[str, bool]:
    """``(classification, is a live read)`` for one read of a candidate output."""
    owners = class_map.get(site.enclosing_class or "", set())
    if owners and owners <= candidates:
        which = sorted(owners)
        if owners == {candidate}:
            return f"internal to the candidate {candidate!r}", False
        return (
            f"internal to deferred node(s) {which} — they run in the same "
            f"once-per-run sweep",
            False,
        )
    if site.file.endswith("core/solver/objectives.py"):
        return (
            "the objective function, in a branch this configuration does not "
            "take (the active branch's reads are seeds, so a candidate cannot "
            "write one)",
            False,
        )
    if site.file.endswith("core/solver/constraints.py"):
        number = next(
            (n for n, name in constraint_functions.items() if name == site.function),
            None,
        )
        if number in active_constraints:
            return f"ACTIVE constraint {number} reads this field", True
        return (
            f"constraint {number} ({site.function}) is not active on this "
            f"configuration",
            False,
        )
    if site.file.endswith("core/solver/evaluators.py") and site.function == "fcnvmc1":
        return (
            "driver logging: the value is formatted into a message, never fed "
            "to a computation",
            False,
        )
    if "stellarator" in site.file:
        return "the stellarator path, which no configuration here takes", False
    if site.file.endswith("models/ife.py"):
        return "the inertial-fusion path, which no configuration here takes", False
    if site.file.endswith("models/availability.py"):
        if site.function in AVAILABILITY_NONDEFAULT_FUNCTIONS:
            branch = settings.get("i_plant_availability")
            if branch in (None, 0):
                return (
                    f"the availability branch {site.function!r} is dead: this "
                    f"configuration selects plant-availability model "
                    f"{branch!r}, and that function is reachable only from the "
                    f"other two",
                    False,
                )
            return (
                f"the availability branch {site.function!r} is LIVE: this "
                f"configuration selects plant-availability model {branch}",
                True,
            )
    if owners & needed:
        return (
            f"read by needed node(s) {sorted(owners & needed)} — a node the "
            f"optimiser does consume",
            True,
        )
    if not owners:
        return (
            f"in {site.file}, which defines no class this experiment maps to a "
            f"model node — UNCLASSIFIED",
            True,
        )
    return (
        f"in class {site.enclosing_class!r}, mapped to node(s) "
        f"{sorted(owners)} — UNCLASSIFIED",
        True,
    )


# ==========================================================================
# the derivation
# ==========================================================================


def derive(
    config: Config,
    campaign: Campaign,
    *,
    lifted: bool,
    census: Mapping[str, Any],
    node_map: Mapping[str, Any],
) -> dict[str, Any]:
    """One configuration's per-run deferral set, derived from first principles."""
    from . import input_files as input_files_mod  # noqa: PLC0415 - one direction

    tree = Path(campaign.tree)
    parsed = input_files_mod.parse_input_file(config.input_path)
    figure_of_merit = parsed["figure_of_merit"]
    active = sorted(
        list(parsed["icc_in_file_order"]) + ([LIFT_CONSTRAINT] if lifted else [])
    )

    constraint_reads, constraint_functions = constraint_reads_by_number(tree)
    unknown = [n for n in active if n not in constraint_reads]
    if unknown:
        raise PostSolveError(
            f"{config.name}: constraint(s) {unknown} are active but no "
            f"registered constraint function claims them; the seed set would "
            f"be missing whatever they read"
        )
    objective = objective_reads(tree, figure_of_merit)
    seeds = set(objective)
    seed_detail = {"objective": sorted(objective)}
    for number in active:
        seeds |= constraint_reads[number]
        seed_detail[f"constraint_{number}"] = sorted(constraint_reads[number])

    writes_by_node = {
        node: set(fields)
        for node, fields in census["writes_by_node"].items()
        if fields and node not in NOT_A_MODEL_NODE
    }
    # Every node that *ran*, not only every node that wrote something.  A node
    # whose body is guarded off on this configuration writes nothing and is
    # still executed on every sweep — which is precisely a node worth deferring,
    # and a unit list taken from the writers alone would never propose it.
    executed = sorted(
        {
            node
            for node in (census.get("node_calls") or writes_by_node)
            if node not in NOT_A_MODEL_NODE
        }
        | set(writes_by_node)
    )
    class_map, class_diagnostics = class_to_nodes(tree, node_map)
    roots = entry_methods(node_map)
    sites, classes_by_file, scan_diagnostics = scan_reads(tree, roots)
    known_fields = set(seeds)
    for fields in writes_by_node.values():
        known_fields |= fields
    dead_functions = dead_branch_functions(parsed["integer_settings"])
    node_reads, read_diagnostics = reads_by_node(
        sites,
        class_map,
        classes_by_file,
        fields=known_fields,
        dead_functions=dead_functions,
    )

    def unit_of(node: str) -> str:
        return "power+" if node in POWER_GROUP else node

    def unit_writes(unit: str) -> set[str]:
        if unit == "power+":
            out: set[str] = set()
            for node in POWER_GROUP:
                out |= writes_by_node.get(node, set())
            return out
        return writes_by_node.get(unit, set())

    def unit_reads(unit: str) -> set[str]:
        if unit == "power+":
            out = set()
            for node in POWER_GROUP:
                out |= node_reads.get(node, set())
            return out
        return node_reads.get(unit, set())

    units = sorted({unit_of(node) for node in executed})
    consumed = set(seeds)
    consumers = {name: ["seed"] for name in seeds}
    needed: dict[str, dict[str, Any]] = {}
    changed = True
    while changed:
        changed = False
        for unit in units:
            if unit in needed:
                continue
            hit = sorted(unit_writes(unit) & consumed)
            if not hit:
                continue
            needed[unit] = {
                "consumed_writes": hit,
                "n_consumed_writes": len(hit),
                "first_consumers": {
                    name: consumers.get(name, []) for name in hit[:10]
                },
            }
            for name in unit_reads(unit):
                consumers.setdefault(name, []).append(unit)
            consumed |= unit_reads(unit)
            changed = True

    candidate_units = [unit for unit in units if unit not in needed]
    candidates: list[str] = []
    for unit in candidate_units:
        candidates.extend(POWER_GROUP if unit == "power+" else [unit])
    # In the order the models execute, taken from the census itself: the
    # instrument records nodes in first-seen order, which is the order the
    # once-per-run sweep will run them in.
    order = [node for node in census["node_calls"] if node not in NOT_A_MODEL_NODE]
    candidates = [node for node in order if node in candidates] + [
        node for node in candidates if node not in order
    ]

    candidate_set = set(candidates)
    needed_nodes: set[str] = set()
    for unit in needed:
        needed_nodes |= set(POWER_GROUP) if unit == "power+" else {unit}

    candidate_fields: set[str] = set()
    for unit in candidate_units:
        candidate_fields |= unit_writes(unit)
    sites_by_field: dict[str, list[Site]] = {}
    for site in sites:
        if site.field in candidate_fields:
            sites_by_field.setdefault(site.field, []).append(site)

    evidence: dict[str, Any] = {}
    live_reads: list[dict[str, Any]] = []
    for unit in candidate_units:
        rows: dict[str, list[dict[str, Any]]] = {}
        for name in sorted(unit_writes(unit)):
            classified = []
            for site in sites_by_field.get(name, []):
                text, live = classify_site(
                    site,
                    candidate=unit,
                    candidates=candidate_set | {"power+"} if unit == "power+" else candidate_set,
                    needed=needed_nodes,
                    class_map=class_map,
                    active_constraints=active,
                    constraint_functions=constraint_functions,
                    settings=parsed["integer_settings"],
                )
                classified.append(
                    {
                        "file": site.file,
                        "line": site.line,
                        "class": site.enclosing_class,
                        "function": site.function,
                        "classification": text,
                        "live": live,
                    }
                )
                if live:
                    live_reads.append(
                        {
                            "candidate": unit,
                            "field": name,
                            "file": site.file,
                            "line": site.line,
                            "class": site.enclosing_class,
                            "function": site.function,
                            "classification": text,
                        }
                    )
            if classified:
                rows[name] = classified
        evidence[unit] = {
            "n_written_fields": len(unit_writes(unit)),
            "n_fields_with_external_read_sites": len(rows),
            "read_sites": rows,
        }

    payload_nodes = list(candidates)
    derived = {
        "format": "a33-postsolve-1",
        "scenario": config.name,
        "generated_by": "harness/postsolve.py",
        "deck": {
            "path": str(config.input_path),
            "minmax": figure_of_merit,
            "icc_parsed_from_deck": parsed["icc_in_file_order"],
            "lift_adds_icc93": lifted,
            "icc_expected_at_runtime": active,
            "i_figure_merit_expected": figure_of_merit,
            "switches_bearing_on_liveness": {
                key: parsed["integer_settings"].get(key)
                for key in ("i_plant_availability", "i_pulsed_plant", "itart")
            },
        },
        "seeds": {"n_fields": len(seeds), "detail": seed_detail},
        "writer_authority": {
            "source": census.get("run", {}).get("outdir")
            or "the committed per-node write census",
            "entry": census.get("entry"),
            "n_nodes": len(writes_by_node),
            "n_fields": sum(len(v) for v in writes_by_node.values()),
        },
        "reachability": {
            "source": (
                "a source scan of the tree under test, attributed by enclosing "
                "class"
            ),
            "class_map": class_diagnostics,
            "scan": scan_diagnostics,
            "attribution": read_diagnostics,
            "n_nodes_with_reads": len(node_reads),
            "n_read_fields_total": sum(len(v) for v in node_reads.values()),
        },
        "availability_branches": availability_branches(tree),
        "crawl": {
            "rule": (
                "backward closure from the seeds: a unit is needed if its "
                "measured writes intersect the consumed field set; a needed "
                "unit's reads join that set; every unit never needed is a "
                "candidate"
            ),
            "units": units,
            "n_needed": len(needed),
            "needed": needed,
            "candidate_units": candidate_units,
        },
        "evidence": evidence,
        "live_reads_of_candidate_outputs": live_reads,
        "post_solve_nodes": payload_nodes,
    }
    derived["nodes_sha256"] = rebuild_nodes_sha256(derived)
    if lifted:
        derived["variant"] = "lifted"
    return derived


def compare(derived: Mapping[str, Any], committed: Mapping[str, Any]) -> dict[str, Any]:
    """The derived deferral set against the committed one, node by node."""
    derived_nodes = list(derived["post_solve_nodes"])
    committed_nodes = list(committed["post_solve_nodes"])
    only_derived = [n for n in derived_nodes if n not in committed_nodes]
    only_committed = [n for n in committed_nodes if n not in derived_nodes]
    return {
        "configuration": derived["scenario"],
        "lifted": bool(derived["deck"]["lift_adds_icc93"]),
        "derived": derived_nodes,
        "committed": committed_nodes,
        "n_derived": len(derived_nodes),
        "n_committed": len(committed_nodes),
        "n_in_both": len(set(derived_nodes) & set(committed_nodes)),
        "only_in_the_derivation": only_derived,
        "only_in_the_committed_artifact": only_committed,
        "same_set": set(derived_nodes) == set(committed_nodes),
        "same_order": derived_nodes == committed_nodes,
        "derived_nodes_sha256": derived["nodes_sha256"],
        "committed_nodes_sha256": committed.get("nodes_sha256"),
        "same_nodes_sha256": derived["nodes_sha256"] == committed.get("nodes_sha256"),
        "constraint_set_agrees": sorted(derived["deck"]["icc_expected_at_runtime"])
        == sorted(committed.get("deck", {}).get("icc_expected_at_runtime") or []),
        "figure_of_merit_agrees": derived["deck"]["i_figure_merit_expected"]
        == committed.get("deck", {}).get("i_figure_merit_expected"),
        "n_seed_fields_derived": derived["seeds"]["n_fields"],
        "n_seed_fields_committed": committed.get("seeds", {}).get("n_fields"),
        "caption": (
            "One comparison per configuration and input file. 'derived' is the "
            "set this stage computes from the seeds, the write census and the "
            "class-level read attribution; 'committed' is the artifact the "
            "driver loads. A node in one and not the other is a finding: "
            "either the derivation is wrong or the artifact is stale."
        ),
    }


# ==========================================================================
# the stage
# ==========================================================================


def stage(
    campaign: Campaign,
    *,
    configurations: Sequence[str] | None = None,
    census_entry: str = "optimisation",
    resume: bool = True,
    use_committed_census: bool = False,
) -> tuple[int, dict[str, Any]]:
    """Derive every per-run deferral set and compare it with the committed one."""
    from . import census as census_mod  # noqa: PLC0415 - one direction

    check = StageCheck(
        name="per-run deferral sets",
        binds=(
            "the committed per-run deferral artifacts, against a derivation "
            "from the seeds, the write census and class-level read attribution"
        ),
    )
    names = list(configurations) if configurations else list(campaign.population)
    node_map = load(campaign.data_dir / "dsm_node_map.json", role="node_map")
    committed_census = load(
        campaign.data_dir / "node_writesets.json", role="node_write_sets"
    )
    rows: list[dict[str, Any]] = []
    n_pairs = 0
    for name in names:
        config = campaign.configuration(name)
        if use_committed_census:
            census = {
                "writes_by_node": committed_census["per_scenario"][name][
                    "writes_by_node"
                ],
                "node_calls": {
                    node: None
                    for node in committed_census["per_scenario"][name][
                        "writes_by_node"
                    ]
                },
                "entry": "the committed per-node write census",
            }
        else:
            try:
                census = census_mod.take(
                    config,
                    campaign,
                    entry=census_entry,
                    read_census=False,
                    resume=resume,
                )
            except (census_mod.CensusError, RuntimeError) as exc:
                check.fail(f"{name}: REFUSED — {exc}")
                rows.append({"configuration": name, "verdict": "REFUSED", "error": str(exc)})
                continue
        for lifted in (False, True):
            if lifted and not config.pulsed:
                continue
            path = config.per_run_artifact(lifted_input_file=lifted)
            committed = load(path, role="defer_per_run")
            try:
                derived = derive(
                    config, campaign, lifted=lifted, census=census, node_map=node_map
                )
            except PostSolveError as exc:
                check.fail(f"{name} ({'lifted' if lifted else 'committed'}): {exc}")
                continue
            result = compare(derived, committed)
            result["committed_artifact"] = str(path)
            result["input_file"] = "lifted" if lifted else "committed"
            n_pairs += 1
            check.n_compared += max(result["n_derived"], result["n_committed"])
            rows.append(
                {
                    **result,
                    "live_reads_of_candidate_outputs": derived[
                        "live_reads_of_candidate_outputs"
                    ],
                    "reachability": derived["reachability"],
                    "crawl_units": derived["crawl"]["units"],
                    "n_needed_units": derived["crawl"]["n_needed"],
                    "availability_branches": derived["availability_branches"],
                }
            )
            label = f"{name} ({'lifted' if lifted else 'committed'} input file)"
            if result["same_set"]:
                check.note(
                    f"{label}: the derivation reproduces the committed set "
                    f"{result['committed']} "
                    f"({'same order, same digest' if result['same_nodes_sha256'] else 'same set, different order or digest'}); "
                    f"{derived['seeds']['n_fields']} seed field(s), "
                    f"{derived['crawl']['n_needed']} of "
                    f"{len(derived['crawl']['units'])} unit(s) needed"
                )
            else:
                check.fail(
                    f"{label}: the derivation does NOT reproduce the committed "
                    f"set — derived {result['derived']}, committed "
                    f"{result['committed']}; only in the derivation "
                    f"{result['only_in_the_derivation']}, only in the artifact "
                    f"{result['only_in_the_committed_artifact']}.  Reported, "
                    f"not absorbed."
                )
            if derived["live_reads_of_candidate_outputs"]:
                check.fail(
                    f"{label}: "
                    f"{len(derived['live_reads_of_candidate_outputs'])} live "
                    f"read site(s) of a deferred node's output — the closure "
                    f"and the confirmation disagree; first: "
                    f"{derived['live_reads_of_candidate_outputs'][0]}"
                )
    check.population = (
        f"{n_pairs} (configuration, input file) pair(s) over {len(names)} "
        f"configuration(s) ({', '.join(names)}); the write census is "
        f"{'the committed one' if use_committed_census else f'measured at one {census_entry}'}"
    )
    return (0 if check.passed else 3), {
        **check.as_record(),
        "pairs": rows,
    }


def stage_teeth(campaign: Campaign) -> tuple[int, dict[str, Any]]:
    """Two ways the deferral comparison must fail.  No PROCESS run.

    Both breaks are made on a throwaway copy of a committed artifact; the
    committed files are never written to.
    """
    check = StageCheck(
        name="per-run deferral sets — teeth",
        binds="the deferral comparison's own ability to fail",
        population="2 deliberate breaks, on throwaway copies of one artifact",
    )
    config = campaign.configurations[0]
    committed = load(
        config.per_run_artifact(lifted_input_file=False), role="defer_per_run"
    )
    derived = {
        "scenario": config.name,
        "deck": dict(committed["deck"]),
        "seeds": dict(committed.get("seeds", {})),
        "post_solve_nodes": list(committed["post_solve_nodes"]),
    }
    derived["nodes_sha256"] = rebuild_nodes_sha256(derived)
    baseline = compare(derived, committed)
    if not baseline["same_set"]:
        check.fail(
            "the control comparison does not agree with itself: the teeth "
            "below would then be measuring the wrong thing"
        )
        return 3, check.as_record()

    broken = json.loads(json.dumps(committed))
    dropped = broken["post_solve_nodes"].pop(0)
    result = compare(derived, broken)
    check.tooth(
        "a node removed from the committed set",
        not result["same_set"] and result["only_in_the_derivation"] == [dropped],
        f"{dropped!r} removed from a throwaway copy of {config.name}'s "
        f"artifact; the comparison must name it as derived-only",
    )

    broken = json.loads(json.dumps(committed))
    broken["post_solve_nodes"].append("physics")
    result = compare(derived, broken)
    check.tooth(
        "a node added to the committed set",
        not result["same_set"]
        and result["only_in_the_committed_artifact"] == ["physics"],
        "a live node added to a throwaway copy; the comparison must name it "
        "as artifact-only, which is the direction that would defer a node the "
        "optimiser consumes",
    )
    return (0 if check.passed else 3), check.as_record()
