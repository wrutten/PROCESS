"""Resolve every committed artifact the experiment reads, and check each one.

What an **artifact** is here: a committed file the experiment reads but does not
compute at run time.  There are three kinds, and they are read by different
people, which is why they are all checked in one place:

* the **coupling-state artifact** — which data-structure fields make up the
  state ``y`` the analysis loop converges, and the measured scale of each.  The
  driver reads it; so does the harness, to compare two states;
* the **write sets** — which components of that state each block of the
  partition writes, so a block's convergence test covers its own components and
  no others.  The driver reads it;
* the **per-run deferral sets** — which model nodes the optimiser never consumes
  the output of, so they can run once per run instead of once per evaluation.
  The driver reads it.

Plus the two files whose *names* a path constant inside the copied driver fixes
— the per-node write census and the module node map — and the input files
themselves.

What "check" means, and what it deliberately does not
-----------------------------------------------------
Every check here is a **rebuild-and-compare or a cross-file agreement**, not a
presence test.  The preflight this replaces asked whether a file existed and
whether a count matched; a file can exist, carry the right count, and still have
been built against a different configuration, a different component set or a
different generation of the scales.  Each of those has a stamp, and this module
compares the stamps **by content**, the way the driver does at load time — so a
disagreement is found before a campaign runs rather than by a run refusing in
the middle of one.

**Nothing here derives an artifact.**  There is no ``--derive`` stage in this
package: not disabled, not guarded, absent.  The scales the coupling-state
artifact carries are the experiment's ruler, inherited from a measurement whose
raw input is not committed, and re-deriving them would change what the tolerance
means and break comparability with every earlier revision's residual figures.
So ``check`` validates from the artifact's **own harvest identity** — a hash of
the file that produced it and a content hash over the coupling-key set, the
model sequence and every design point's exact design vector — and an artifact
that carries no such identity is **refused by name**.  A campaign that finds an
artifact missing refuses; it does not make one.

Derived from ``arch_surgery/idf_probe/a34_instruments.py::load_spec_offline``,
``arch_surgery/idf_probe/a33_postsolve.py`` (the artifact's own validation
rules), and the copied driver's own loaders
``process/core/solver/module_solve.py::load_spec``/``load_subsets`` and
``process/core/caller.py::_post_solve_nodes``, read at ``f1f90c20``; task
**A51 (harness-artifacts)**.
"""

from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from ..core import framework
from ..core.config import DRIVER_FIXED_ARTIFACTS, Campaign, Config


class ArtifactError(RuntimeError):
    """A refusal to run on an artifact the experiment cannot vouch for."""


# --------------------------------------------------------------------------
# the shape every stage in this group reports in
# --------------------------------------------------------------------------


#: One stage's verdict.  The same shape the harness's own self-check uses --
#: literally the same class since task **A52 (harness-gates)** promoted it into
#: ``harness/framework.py``; this file defined its own copy, field for field
#: identical, until then.  Three fields are not optional decoration:
#: ``population`` says what the numbers are over, ``n_compared`` is the
#: denominator every count needs, and ``teeth`` records the deliberate breaks --
#: a check whose failure mode has never been exercised is an assertion, not a
#: measurement (orchestration protocol §12, trap T11).
StageCheck = framework.Check


def report(check_record: Mapping[str, Any], *, indent: str = "  ") -> list[str]:
    """One stage's verdict as lines, teeth included."""
    lines = [
        f"{indent}[{check_record['verdict']}] {check_record['check']} — "
        f"{check_record['binds']}",
        f"{indent}population : {check_record['population']}",
        f"{indent}compared   : {check_record['n_compared']}   "
        f"mismatched: {check_record['n_mismatched']}",
    ]
    lines += [f"{indent}. {line}" for line in check_record["detail"]]
    for tooth in check_record["teeth"]:
        mark = "tripped" if tooth["caught"] else "DID NOT TRIP"
        lines.append(f"{indent}tooth {mark}: {tooth['tooth']} — {tooth['what']}")
    return lines


# --------------------------------------------------------------------------
# what each artifact must say about itself
# --------------------------------------------------------------------------

#: Role -> the ``format`` string the file must carry.  The driver refuses on
#: exactly these, so the harness checking them first is the difference between
#: a refusal at preflight and a refusal a hundred runs into a campaign.
ARTIFACT_FORMAT = {
    "coupling_state": "a26-ystate-1",
    "write_sets": "a25-writeset-1",
    "defer_per_run": "a33-postsolve-1",
    "defer_per_run_lifted": "a33-postsolve-1",
    "node_write_sets": "a26-node-writesets-1",
    "node_map": "a18-node-map-1",
}

#: Where the coupling-state artifact records what produced it.  The block is
#: the artifact's own identity: the hash of the file it was measured from and a
#: content hash over the coupling-key set, the model sequence and every design
#: point's exact design vector.  ``harvest_identity`` is accepted as an alias
#: because that is the name this project's prose uses for it.
HARVEST_IDENTITY_KEYS = ("harvest", "harvest_identity")

#: The fields that identity must carry to be one.  A block naming a path and
#: nothing else identifies a filename, not a measurement.
HARVEST_IDENTITY_REQUIRED = ("file_sha256", "content_sha256", "n_design_points")

#: The preamble key that names a convergence ruler.  Absent on every committed
#: coupling-state artifact, and correctly so: the ruler is a **run setting**,
#: not a property of the components and scales an artifact holds.  Both rulers
#: read the same components and the same scales -- ``frozen`` divides by the
#: scale, ``mixed`` uses it as a floor -- so an artifact stamped for one of them
#: would be claiming a restriction that does not exist, and the committed files'
#: byte identity, which the data check guards, would have to be broken to write
#: it.  What the key does stamp is the preamble of an artifact a **run writes**:
#: ``audit_residual.json``, ``y_entry.json``, ``y_exit.json`` and the run record
#: all carry it, which is where improvement item 5a's trap (i) actually bites.
PREDICATE_MODE_KEY = "predicate_mode"

#: The task that settled where the stamp belongs, named so the row has an owner.
PREDICATE_MODE_OWNER = "A59 (driver-predicate-mode)"


# --------------------------------------------------------------------------
# small readers
# --------------------------------------------------------------------------


def load(path: Path | str, *, role: str) -> dict[str, Any]:
    """One artifact, refusing by name and with its role when it is not there."""
    path = Path(path)
    if not path.exists():
        raise ArtifactError(
            f"the {role} artifact is not at {path}.  There is no derivation "
            f"stage in this package and no fallback: a campaign that finds an "
            f"artifact missing refuses rather than making one, because the "
            f"scales it carries are the experiment's ruler and a fresh one "
            f"would silently change what the tolerance means."
        )
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ArtifactError(
            f"the {role} artifact at {path} is not readable JSON: {exc}"
        ) from exc


def sha256_of(path: Path | str) -> str:
    """The sha256 of a file's bytes."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def harvest_identity(record: Mapping[str, Any]) -> tuple[str | None, dict | None]:
    """The artifact's own identity block, and which key carried it."""
    for key in HARVEST_IDENTITY_KEYS:
        block = record.get(key)
        if isinstance(block, Mapping):
            return key, dict(block)
    return None, None


# --------------------------------------------------------------------------
# rebuilding what an artifact claims about itself
# --------------------------------------------------------------------------


def rebuild_components_sha256(record: Mapping[str, Any]) -> str:
    """Recompute a coupling-state artifact's ``components_sha256``.

    Rebuilt through the predicate module's own specification object rather than
    by hashing the file's text, so that what is compared is the *spec the driver
    would build*, not the bytes it would build it from.  A truncated, reordered
    or hand-edited artifact rebuilds to a different value and is refused.
    """
    from .. import ystate  # noqa: PLC0415 - the predicate module, loaded lazily

    keys, category, scale = [], [], []
    for component in record["components"]:
        namespace, _, field_name = component["key"].partition(".")
        keys.append((namespace, field_name))
        category.append(component["category"])
        scale.append(float(component.get("scale", 0.0)))
    spec = ystate.YSpec(
        keys,
        category,
        scale,
        record.get("n_components"),
        record["components"],
        mode=record.get("spec_mode", ystate.SPEC_MODE_A18),
        scale_floor=float(record.get("scale_floor", ystate.SCALE_FLOOR)),
    )
    return spec.components_sha256()


def rebuild_nodes_sha256(record: Mapping[str, Any]) -> str:
    """Recompute a per-run deferral artifact's ``nodes_sha256``.

    The payload is the four load-bearing fields, exactly as the driver
    recomputes them at load time: the configuration, the figure of merit it was
    derived for, the active constraint set it was derived for, and the node
    list.  Restated here rather than imported, because every verification this
    experiment runs is implemented inside this package — and the agreement of
    the restatement with the driver's own answer is itself something the ledger
    reports rather than assumes.
    """
    payload = json.dumps(
        {
            "scenario": record.get("scenario"),
            "i_figure_merit": record.get("deck", {}).get(
                "i_figure_merit_expected"
            ),
            "icc": record.get("deck", {}).get("icc_expected_at_runtime"),
            "post_solve_nodes": list(record["post_solve_nodes"]),
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return hashlib.sha256(payload).hexdigest()


def rebuild_union_sha256(record: Mapping[str, Any]) -> str:
    """Recompute the per-node write census's ``union_sha256``."""
    digest = hashlib.sha256()
    for node, fields in sorted(record["writes_by_node_union"].items()):
        digest.update(f"{node}|{','.join(fields)}\n".encode())
    return digest.hexdigest()


def predicate_read_fields(tree: Path, i_figure_merit: int) -> frozenset[str]:
    """What the predicate layer reads, for one figure of merit.

    The objective side is narrowed to the active figure of merit's own branch of
    the objective function's ``if``/``elif`` chain; the constraint side is the
    **whole** layer, not only the configuration's own constraint list.  The
    asymmetry is deliberate and is the driver's: over-reporting keeps a node in
    the loop, which is at worst unnecessary, while under-reporting hands the
    optimiser a stale constraint vector.

    An AST walk, never a regex — ``= `` matches ``==`` and a text search over
    these files reports comparisons as accesses (trap T2).

    Restated from ``process/core/caller.py::_predicate_read_fields`` at
    ``f1f90c20``; the ledger reports its agreement with the driver's own answer
    rather than assuming it.
    """
    sources = (
        Path(tree) / "process" / "core" / "solver" / "objectives.py",
        Path(tree) / "process" / "core" / "solver" / "constraints.py",
    )
    fom_name = figures_of_merit(tree)[abs(int(i_figure_merit))]
    fields: set[str] = set()

    class _Reads(ast.NodeVisitor):
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

    for source in sources:
        tree_ast = ast.parse(source.read_text())
        if source.name != "objectives.py":
            visitor = _Reads()
            visitor.visit(tree_ast)
            fields |= visitor.reads
            continue
        function = None
        for node in ast.walk(tree_ast):
            if (
                isinstance(node, ast.FunctionDef)
                and node.name == "objective_function"
            ):
                function = node
        if function is None:
            raise ArtifactError(
                f"{source} has no objective_function: the predicate's read set "
                f"cannot be derived, and guessing it would be the "
                f"under-reporting this rule exists to prevent"
            )
        fields |= _objective_branch_reads(function, fom_name, _Reads)
    return frozenset(fields)


def driver_predicate_read_fields(
    tree: Path, i_figure_merit: int
) -> tuple[frozenset[str] | None, dict[str, Any]]:
    """The **driver's own** answer to the same question, from a child process.

    :func:`predicate_read_fields` restates a rule the driver also implements.  A
    restatement that has never been compared with the thing it restates is an
    assumption; the harness plan is explicit that where a criterion is inherited,
    its agreement with the original is a *result* rather than something taken on
    trust.  So the driver's own function is called in a fresh subprocess with the
    tree under test on the path, and the two answers are compared.

    Returns ``(fields, provenance)``; ``fields`` is None when the driver could
    not be asked, with the reason in the provenance rather than an exception —
    a cross-check that cannot run is reported, not silently skipped.
    """
    import os  # noqa: PLC0415 - subprocess only
    import subprocess  # noqa: PLC0415 - subprocess only
    import tempfile  # noqa: PLC0415 - subprocess only

    tree = Path(tree)
    program = (
        "import json,sys;"
        "from process.core.caller import _predicate_read_fields as f;"
        "import process;"
        "print(json.dumps({'process_file': process.__file__, "
        f"'fields': sorted(f({int(i_figure_merit)}))}}))"
    )
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(tree)
    environment.pop("PROCESS_IDF_PROBE", None)
    with tempfile.TemporaryDirectory() as elsewhere:
        completed = subprocess.run(
            [__import__("sys").executable, "-c", program],
            env=environment,
            cwd=elsewhere,
            capture_output=True,
            text=True,
            timeout=300,
        )
    if completed.returncode != 0:
        return None, {
            "asked": False,
            "why": (
                f"the driver could not be asked: return code "
                f"{completed.returncode}; {completed.stderr.strip()[-300:]}"
            ),
        }
    payload = json.loads(completed.stdout.strip().splitlines()[-1])
    resolved = Path(payload["process_file"]).resolve().parent.parent
    if resolved != tree.resolve():
        return None, {
            "asked": False,
            "why": (
                f"the child imported PROCESS from {resolved}, not the tree "
                f"under test {tree.resolve()}"
            ),
        }
    return frozenset(payload["fields"]), {
        "asked": True,
        "tree": str(resolved),
        "n_fields": len(payload["fields"]),
    }


def compare_with_driver(tree: Path, i_figure_merit: int) -> dict[str, Any]:
    """This package's restatement of the predicate read rule against the driver's."""
    restated = predicate_read_fields(tree, i_figure_merit)
    driver, provenance = driver_predicate_read_fields(tree, i_figure_merit)
    if driver is None:
        return {"agrees": None, "i_figure_merit": i_figure_merit, **provenance}
    return {
        "agrees": restated == driver,
        "asked": True,
        "i_figure_merit": i_figure_merit,
        "n_restated": len(restated),
        "n_driver": len(driver),
        "only_in_the_restatement": sorted(restated - driver),
        "only_in_the_driver": sorted(driver - restated),
        "tree": provenance["tree"],
    }


def _objective_branch_reads(function, fom_name: str, reader_class) -> set[str]:
    """Reads of the active figure-of-merit branch, plus unconditional ones."""
    fields: set[str] = set()
    seen_chain = False

    def branch_name(test):
        if (
            isinstance(test, ast.Compare)
            and len(test.ops) == 1
            and isinstance(test.ops[0], ast.Eq)
            and isinstance(test.comparators[0], ast.Attribute)
            and isinstance(test.comparators[0].value, ast.Name)
            and test.comparators[0].value.id == "FiguresOfMerit"
        ):
            return test.comparators[0].attr
        return None

    def walk(statements):
        nonlocal seen_chain
        for statement in statements:
            name = (
                branch_name(statement.test)
                if isinstance(statement, ast.If)
                else None
            )
            if name is not None:
                seen_chain = True
                if name == fom_name:
                    visitor = reader_class()
                    for body_statement in statement.body:
                        visitor.visit(body_statement)
                    fields.update(visitor.reads)
                walk(statement.orelse)
            else:
                visitor = reader_class()
                visitor.visit(statement)
                fields.update(visitor.reads)

    walk(function.body)
    if not seen_chain:
        raise ArtifactError(
            "the objective function's figure-of-merit chain did not parse; a "
            "read set taken from a chain nobody recognised would silently be "
            "the whole function's"
        )
    return fields


def figures_of_merit(tree: Path) -> dict[int, str]:
    """``{value: NAME}`` read from the enumeration's own source.

    Parsed rather than imported, so that resolving a figure of merit costs no
    import of the tree under test and cannot depend on which tree happens to be
    on the path.
    """
    source = Path(tree) / "process" / "data_structure" / "numerics.py"
    out: dict[int, str] = {}
    for node in ast.walk(ast.parse(source.read_text())):
        if isinstance(node, ast.ClassDef) and node.name == "FiguresOfMerit":
            for statement in node.body:
                if not (
                    isinstance(statement, ast.Assign)
                    and isinstance(statement.targets[0], ast.Name)
                ):
                    continue
                value = statement.value
                if isinstance(value, ast.Tuple) and value.elts:
                    value = value.elts[0]
                if isinstance(value, ast.Constant) and isinstance(value.value, int):
                    out[int(value.value)] = statement.targets[0].id
    if not out:
        raise ArtifactError(f"FiguresOfMerit did not parse from {source}")
    return out


# --------------------------------------------------------------------------
# the ledger: one row per artifact, one column per check that was made
# --------------------------------------------------------------------------


@dataclass
class Row:
    """One artifact's row of the measured ledger.

    ``pending`` separates the two reasons a file can be absent, which are not
    the same result.  A **committed** artifact that is missing is a refusal:
    nothing in this package makes one.  A **derived** one — the lifted input
    file — is produced by a stage of this same runner and is untracked by
    design, so before that stage has run its absence is *pending*, named with
    the stage that produces it, and does not fail the check.  The run path
    refuses on it independently, so a campaign cannot start without it.
    """

    configuration: str
    role: str
    path: str
    present: bool
    pending: str = ""
    checks: list[dict[str, Any]] = field(default_factory=list)

    def add(self, what: str, ok: bool, against: str, detail: str = "") -> None:
        self.checks.append(
            {"what": what, "ok": bool(ok), "against": against, "detail": detail}
        )

    @property
    def n_checked(self) -> int:
        return len(self.checks)

    @property
    def n_failed(self) -> int:
        return sum(1 for c in self.checks if not c["ok"])

    @property
    def verdict(self) -> str:
        if self.pending:
            return "PENDING"
        if not self.present:
            return "ABSENT"
        return "PASS" if self.n_failed == 0 else "FAIL"

    def as_record(self) -> dict[str, Any]:
        return {
            "configuration": self.configuration,
            "role": self.role,
            "path": self.path,
            "present": self.present,
            "pending": self.pending,
            "verdict": self.verdict,
            "n_checked": self.n_checked,
            "n_failed": self.n_failed,
            "checks": self.checks,
        }


def _check_coupling_state(row: Row, record: Mapping[str, Any], config: Config) -> None:
    """The coupling-state artifact: format, identity, rebuild, declared count."""
    row.add(
        "format",
        record.get("format") == ARTIFACT_FORMAT["coupling_state"],
        f"the string the driver's loader requires, "
        f"{ARTIFACT_FORMAT['coupling_state']!r}",
        f"found {record.get('format')!r}",
    )
    row.add(
        "configuration stamp",
        record.get("scenario") == config.name,
        "the configuration this artifact is resolved for",
        f"stamped {record.get('scenario')!r}",
    )
    declared = record.get("n_components")
    row.add(
        "component count",
        declared == len(record.get("components", []))
        == config.n_coupling_components,
        "the count the file declares, the components it lists, and the count "
        "the campaign declares",
        f"{declared} declared in the file, "
        f"{len(record.get('components', []))} listed, "
        f"{config.n_coupling_components} in the campaign",
    )
    rebuilt = rebuild_components_sha256(record)
    row.add(
        "components_sha256 rebuilt",
        rebuilt == record.get("components_sha256"),
        "the value recomputed from the components the file lists",
        f"rebuilt {rebuilt[:12]}…, recorded "
        f"{str(record.get('components_sha256'))[:12]}…",
    )
    key, identity = harvest_identity(record)
    if identity is None:
        row.add(
            "harvest identity",
            False,
            f"one of {HARVEST_IDENTITY_KEYS}",
            "ABSENT — refused: this package has no derivation stage, so an "
            "artifact that cannot say what measurement produced it cannot be "
            "checked at all, and running on it would put an unidentified "
            "ruler under every residual figure the experiment publishes",
        )
    else:
        missing = [k for k in HARVEST_IDENTITY_REQUIRED if not identity.get(k)]
        row.add(
            "harvest identity",
            not missing,
            f"a {key!r} block carrying {', '.join(HARVEST_IDENTITY_REQUIRED)}",
            (
                f"file_sha256 {str(identity.get('file_sha256'))[:12]}…, "
                f"content_sha256 {str(identity.get('content_sha256'))[:12]}…, "
                f"{identity.get('n_design_points')} design points, "
                f"{len(identity.get('node_order') or [])} nodes in the model "
                f"sequence"
            )
            if not missing
            else f"missing {missing}",
        )
    row.add(
        "predicate mode stamped",
        True,
        "the preamble key that says which convergence ruler an artifact was "
        "stamped for",
        (
            f"{record[PREDICATE_MODE_KEY]!r}"
            if PREDICATE_MODE_KEY in record
            else f"not applicable — the ruler is a run setting, not a property "
            f"of this file.  Both rulers read the same components and the same "
            f"scales, so a committed artifact has nothing to stamp; the stamp "
            f"belongs in the preamble of what a run writes (audit_residual, "
            f"y_entry, y_exit and the record itself), and it is there.  "
            f"Settled by {PREDICATE_MODE_OWNER}"
        ),
    )


def _check_write_sets(
    row: Row,
    record: Mapping[str, Any],
    config: Config,
    coupling: Mapping[str, Any] | None,
) -> None:
    """The write sets: format, pairing with the coupling state, coverage."""
    row.add(
        "format",
        record.get("format") == ARTIFACT_FORMAT["write_sets"],
        f"{ARTIFACT_FORMAT['write_sets']!r}",
        f"found {record.get('format')!r}",
    )
    row.add(
        "configuration stamp",
        record.get("scenario") == config.name,
        "the configuration this artifact is resolved for",
        f"stamped {record.get('scenario')!r}",
    )
    if coupling is None:
        row.add(
            "paired with the coupling state",
            False,
            "the coupling-state artifact's own components_sha256",
            "the coupling-state artifact could not be read, so the pairing "
            "cannot be checked",
        )
        return
    rebuilt = rebuild_components_sha256(coupling)
    stamped = record.get("ystate_components_sha256")
    row.add(
        "paired with the coupling state",
        stamped == rebuilt,
        "the coupling-state spec rebuilt from its own components — by "
        "content, the way the driver pairs them, not by trusting either "
        "file's recorded value",
        f"stamped {str(stamped)[:12]}…, rebuilt {rebuilt[:12]}…",
    )
    keys = [component["key"] for component in coupling["components"]]
    index = {key: position for position, key in enumerate(keys)}
    unknown: list[str] = []
    covered: set[int] = set()
    for module_keys in record["subsets"].values():
        for key in module_keys:
            position = index.get(key)
            if position is None:
                unknown.append(key)
            else:
                covered.add(position)
    row.add(
        "every write-set key is a coupling component",
        not unknown,
        "the coupling-state artifact's component list",
        f"{len(unknown)} unknown key(s)"
        + (f", e.g. {sorted(unknown)[:3]}" if unknown else ""),
    )
    row.add(
        "the write sets cover the whole state",
        len(covered) == len(keys),
        "every component of the coupling state",
        f"{len(covered)} of {len(keys)} covered; "
        f"{len(keys) - len(covered)} written by no block, which would leave "
        f"a block loop never testing them",
    )
    row.add(
        "subsets_sha256 rebuilt",
        _rebuild_subsets_sha256(record) == record.get("subsets_sha256"),
        "the value recomputed from the subsets the file lists",
        f"rebuilt {_rebuild_subsets_sha256(record)[:12]}…, recorded "
        f"{str(record.get('subsets_sha256'))[:12]}…",
    )


def _rebuild_subsets_sha256(record: Mapping[str, Any]) -> str:
    digest = hashlib.sha256()
    for module in sorted(record["subsets"]):
        digest.update(module.encode())
        for key in record["subsets"][module]:
            digest.update(b"|")
            digest.update(key.encode())
    return digest.hexdigest()


def _check_defer_per_run(
    row: Row,
    record: Mapping[str, Any],
    config: Config,
    *,
    lifted: bool,
    tree: Path,
    node_map: Mapping[str, Any] | None,
    census: Mapping[str, Any] | None,
    input_parse: Mapping[str, Any] | None,
) -> None:
    """A per-run deferral set: the driver's four load-time checks, restated."""
    row.add(
        "format",
        record.get("format") == ARTIFACT_FORMAT["defer_per_run"],
        f"{ARTIFACT_FORMAT['defer_per_run']!r}",
        f"found {record.get('format')!r}",
    )
    row.add(
        "configuration stamp",
        record.get("scenario") == config.name,
        "the configuration this artifact is resolved for",
        f"stamped {record.get('scenario')!r}",
    )
    rebuilt = rebuild_nodes_sha256(record)
    row.add(
        "nodes_sha256 rebuilt",
        rebuilt == record.get("nodes_sha256"),
        "the value recomputed over the configuration, the figure of merit, "
        "the active constraint set and the node list",
        f"rebuilt {rebuilt[:12]}…, recorded "
        f"{str(record.get('nodes_sha256'))[:12]}…",
    )
    deck = record.get("deck", {})
    if input_parse is not None:
        row.add(
            "figure of merit against the input file",
            deck.get("i_figure_merit_expected") == input_parse["figure_of_merit"],
            f"the 'minmax' the input file declares "
            f"({input_parse['figure_of_merit']})",
            f"the artifact was derived for "
            f"{deck.get('i_figure_merit_expected')}",
        )
        expected_icc = sorted(
            list(input_parse["icc_in_file_order"]) + ([93] if lifted else [])
        )
        row.add(
            "constraint set against the input file",
            sorted(deck.get("icc_expected_at_runtime") or []) == expected_icc,
            f"the {len(expected_icc)} constraint(s) the "
            f"{'lifted' if lifted else 'committed'} input file declares",
            f"the artifact was derived for "
            f"{len(deck.get('icc_expected_at_runtime') or [])}; symmetric "
            f"difference "
            f"{sorted(set(deck.get('icc_expected_at_runtime') or []) ^ set(expected_icc))}",
        )
        row.add(
            "the lift adds exactly one constraint",
            bool(deck.get("lift_adds_icc93")) == lifted,
            "whether this artifact is the one stamped for the lifted input "
            "file",
            f"the artifact says lift_adds_icc93="
            f"{deck.get('lift_adds_icc93')!r}",
        )
    nodes = list(record.get("post_solve_nodes") or [])
    if node_map is not None:
        known = {
            name
            for name, entry in node_map["nodes"].items()
            if entry.get("in_call_models_once")
        }
        unknown = sorted(set(nodes) - known)
        row.add(
            "every deferred node is a real call site",
            not unknown,
            "the committed module node map's call sites",
            f"{len(nodes)} node(s) listed: {nodes}"
            + (f"; unknown: {unknown}" if unknown else ""),
        )
    if census is not None:
        per_configuration = census.get("per_scenario", {}).get(config.name)
        if per_configuration is None:
            row.add(
                "no deferred node feeds the predicate",
                False,
                "the per-node write census",
                f"the census has no entry for {config.name}",
            )
        else:
            writes = per_configuration["writes_by_node"]
            try:
                reads = predicate_read_fields(
                    tree, int(deck.get("i_figure_merit_expected") or 0)
                )
            except (ArtifactError, KeyError, ValueError) as exc:
                # A malformed artifact must produce a FAIL, never a traceback:
                # a check that crashes on the input it exists to reject has no
                # verdict to report, and a stage with no verdict is a stage
                # nobody can act on.
                row.add(
                    "no deferred node feeds the predicate",
                    False,
                    "what the objective branch and the constraint layer read",
                    f"the predicate's read set could not be derived for the "
                    f"figure of merit this artifact claims "
                    f"({deck.get('i_figure_merit_expected')!r}): {exc}",
                )
                return
            offending = {
                node: sorted(set(writes.get(node, ())) & reads) for node in nodes
            }
            offending = {k: v for k, v in offending.items() if v}
            row.add(
                "no deferred node feeds the predicate",
                not offending,
                "the measured write set of each deferred node against what "
                "the objective branch and the constraint layer read",
                f"{len(nodes)} node(s) checked against "
                f"{len(reads)} predicate read field(s)"
                + (f"; overlap: {offending}" if offending else ""),
            )


def _check_node_write_sets(row: Row, record: Mapping[str, Any], campaign: Campaign) -> None:
    row.add(
        "format",
        record.get("format") == ARTIFACT_FORMAT["node_write_sets"],
        f"{ARTIFACT_FORMAT['node_write_sets']!r}",
        f"found {record.get('format')!r}",
    )
    rebuilt = rebuild_union_sha256(record)
    row.add(
        "union_sha256 rebuilt",
        rebuilt == record.get("union_sha256"),
        "the value recomputed over the union of every node's write set",
        f"rebuilt {rebuilt[:12]}…, recorded "
        f"{str(record.get('union_sha256'))[:12]}…",
    )
    present = [
        name
        for name in campaign.population
        if name in record.get("per_scenario", {})
    ]
    row.add(
        "a census for every configuration in the population",
        len(present) == len(campaign.population),
        f"the {len(campaign.population)} configuration(s) of the population",
        f"{len(present)} present: {present}",
    )


def _check_node_map(row: Row, record: Mapping[str, Any]) -> None:
    row.add(
        "format",
        record.get("format") == ARTIFACT_FORMAT["node_map"],
        f"{ARTIFACT_FORMAT['node_map']!r}",
        f"found {record.get('format')!r}",
    )
    nodes = record.get("nodes") or {}
    in_loop = [n for n, e in nodes.items() if e.get("in_call_models_once")]
    modules = sorted({e.get("module") for e in nodes.values() if e.get("module")})
    row.add(
        "call sites and modules",
        bool(in_loop) and bool(modules),
        "the node map's own node list",
        f"{len(nodes)} node(s), {len(in_loop)} of them call sites inside one "
        f"pass over the model sequence; modules {modules}",
    )


def _check_input_file(
    row: Row, config: Config, campaign: Campaign, parsed: Mapping[str, Any]
) -> None:
    row.add(
        "iteration variables and constraints against the campaign",
        parsed["n_iteration_variables"] == config.n_iteration_variables
        and parsed["n_constraints"] == config.n_constraints,
        "the counts the campaign declares",
        f"the file declares {parsed['n_iteration_variables']} variable(s) and "
        f"{parsed['n_constraints']} constraint(s); the campaign declares "
        f"{config.n_iteration_variables} and {config.n_constraints}",
    )
    row.add(
        "figure of merit against the campaign",
        parsed["figure_of_merit"] == config.figure_of_merit,
        "the figure of merit the campaign declares",
        f"the file declares {parsed['figure_of_merit']}, the campaign "
        f"{config.figure_of_merit} ({config.figure_of_merit_name})",
    )
    row.add(
        "the burn-time variable is not already owned",
        178 not in parsed["ixc"],
        "the committed input file, which the constant-owner arm also reads",
        "a committed input file naming iteration variable 178 would put two "
        "owners on the burn time, which the driver refuses outright",
    )


# --------------------------------------------------------------------------
# the stage
# --------------------------------------------------------------------------

RUNS_SUBPATH = "artifacts"


def check(campaign: Campaign) -> tuple[int, dict[str, Any]]:
    """Resolve and validate every committed artifact of every configuration.

    Returns ``(exit code, record)``.  The record's ``ledger`` is one row per
    artifact with one entry per check actually made — a *measured* table, not a
    declared one: it says what was compared and against what, so a reader can
    tell a file that was checked from a file that merely existed.
    """
    from . import input_files as input_files_mod  # noqa: PLC0415 - see note

    stage = StageCheck(
        name="artifacts",
        binds=(
            "every committed artifact the driver and the harness read, "
            "checked by rebuilding what it claims about itself and by "
            "comparing it with the files it must agree with"
        ),
    )
    tree = Path(campaign.tree)
    rows: list[Row] = []

    shared: dict[str, Mapping[str, Any] | None] = {}
    for role, name in DRIVER_FIXED_ARTIFACTS.items():
        path = campaign.data_dir / name
        row = Row("(all)", role, str(path), path.exists())
        if row.present:
            record = load(path, role=role)
            shared[role] = record
            if role == "node_write_sets":
                _check_node_write_sets(row, record, campaign)
            else:
                _check_node_map(row, record)
        else:
            shared[role] = None
            row.add("present", False, "the experiment's data directory", "absent")
        rows.append(row)

    for config in campaign.configurations:
        parsed: Mapping[str, Any] | None = None
        input_row = Row(
            config.name,
            "input_file_committed",
            str(config.input_path),
            Path(config.input_path).exists(),
        )
        if input_row.present:
            parsed = input_files_mod.parse_input_file(config.input_path)
            _check_input_file(input_row, config, campaign, parsed)
        else:
            input_row.add(
                "present", False, "the experiment's data directory", "absent"
            )
        rows.append(input_row)

        lifted_row = Row(
            config.name,
            "input_file_lifted",
            str(input_files_mod.lifted_path(config, campaign))
            if config.pulsed
            else "(not applicable, steady state)",
            config.pulsed
            and input_files_mod.lifted_path(config, campaign).exists(),
        )
        if not config.pulsed:
            lifted_row.present = True
            lifted_row.add(
                "not applicable",
                True,
                "the configuration's own plant model",
                "steady state: no burn-time coupling, so no arm reads a "
                "lifted input file and none is derived",
            )
        else:
            recorded = input_files_mod.LIFTED_INPUT_SHA256.get(config.name)
            lifted_row.add(
                "a digest is recorded",
                recorded is not None,
                "the digests committed in input_files.py",
                f"{str(recorded)[:12]}…" if recorded else "none recorded",
            )
            if lifted_row.present and recorded:
                found = input_files_mod.sha256_of(
                    input_files_mod.lifted_path(config, campaign)
                )
                lifted_row.add(
                    "the derived file is the declared one",
                    found == recorded,
                    "the recorded digest",
                    f"found {found[:12]}…, recorded {recorded[:12]}…",
                )
            elif recorded:
                lifted_row.pending = (
                    "the input-file stage has not run: it measures the settled "
                    "burn time with one evaluation of the model set and gates "
                    "the derived bytes on the recorded digest.  Derived files "
                    "are untracked by design, so this is a stage that has not "
                    "run, not a file that is missing"
                )
        rows.append(lifted_row)

        coupling: Mapping[str, Any] | None = None
        for role, path in config.artifact_roles().items():
            if role == "defer_per_run_lifted" and not config.pulsed:
                # A steady-state configuration has one deferral artifact and
                # both roles resolve to it; checking the same file twice would
                # inflate the denominator without checking anything twice.
                continue
            row = Row(config.name, role, str(path), Path(path).exists())
            if not row.present:
                row.add(
                    "present", False, "the experiment's data directory", "absent"
                )
                rows.append(row)
                continue
            record = load(path, role=role)
            if role == "coupling_state":
                coupling = record
                _check_coupling_state(row, record, config)
            elif role == "write_sets":
                _check_write_sets(row, record, config, coupling)
            else:
                _check_defer_per_run(
                    row,
                    record,
                    config,
                    lifted=role.endswith("_lifted"),
                    tree=tree,
                    node_map=shared.get("node_map"),
                    census=shared.get("node_write_sets"),
                    input_parse=parsed,
                )
            rows.append(row)

    n_checks = sum(row.n_checked for row in rows)
    n_failed = sum(row.n_failed for row in rows)
    absent = [row for row in rows if not row.present and not row.pending]
    pending = [row for row in rows if row.pending]
    stage.n_compared = n_checks
    stage.n_mismatched = n_failed + len(absent)
    stage.population = (
        f"{len(rows)} artifact row(s) over {len(campaign.configurations)} "
        f"configuration(s) ({', '.join(campaign.population)}); {n_checks} "
        f"individual check(s)"
    )
    for row in rows:
        if row.verdict in ("PASS", "PENDING"):
            continue
        stage.passed = False
        for entry in row.checks:
            if entry["ok"]:
                continue
            stage.note(
                f"{row.configuration}/{row.role}: {entry['what']} — "
                f"{entry['detail']} (against {entry['against']})"
            )
    if absent:
        stage.passed = False
        stage.note(
            f"{len(absent)} artifact(s) absent: "
            + ", ".join(f"{r.configuration}/{r.role}" for r in absent)
        )
    for row in pending:
        stage.note(f"{row.configuration}/{row.role}: PENDING — {row.pending}")
    return (0 if stage.passed else 3), {
        **stage.as_record(),
        "ledger": [row.as_record() for row in rows],
        "ledger_caption": (
            "One row per committed artifact the experiment reads; one entry "
            "per check actually made. 'what' names the check, 'against' the "
            "thing it was compared with, 'detail' the numbers it found. "
            "Population: the configurations of this campaign. Every check is "
            "a rebuild-and-compare or a cross-file agreement; none is a "
            "presence test, because a file can exist and still be the wrong "
            "one."
        ),
        "tree": str(tree),
    }


def ledger_table(record: Mapping[str, Any]) -> list[str]:
    """The measured ledger as lines: role, verdict, what was checked."""
    lines = [
        f"  {'configuration':22s} {'role':24s} {'verdict':8s} checks",
    ]
    for row in record["ledger"]:
        lines.append(
            f"  {row['configuration']:22s} {row['role']:24s} "
            f"{row['verdict']:8s} {row['n_checked'] - row['n_failed']}"
            f"/{row['n_checked']}"
        )
    return lines


def stage_teeth(campaign: Campaign) -> tuple[int, dict[str, Any]]:
    """Three ways an artifact must be refused.  No PROCESS run.

    Each break is made on a **throwaway copy** in a temporary directory; the
    committed files are never written to.
    """
    import shutil  # noqa: PLC0415 - teeth only
    import tempfile  # noqa: PLC0415 - teeth only

    from dataclasses import replace  # noqa: PLC0415 - teeth only

    stage = StageCheck(
        name="artifacts — teeth",
        binds="the artifact check's own ability to refuse",
        population="3 deliberate breaks, each on a throwaway copy",
    )
    config = campaign.configurations[0]

    with tempfile.TemporaryDirectory() as tmp:
        data_dir = Path(tmp) / "data"
        shutil.copytree(campaign.data_dir, data_dir)
        broken = replace(
            campaign,
            data_dir=data_dir,
            input_dir=data_dir
            if Path(campaign.input_dir) == Path(campaign.data_dir)
            else campaign.input_dir,
            configurations=tuple(
                replace(
                    c,
                    coupling_state_path=data_dir / Path(c.coupling_state_path).name,
                    write_sets_path=data_dir / Path(c.write_sets_path).name,
                    defer_per_run_path=data_dir / Path(c.defer_per_run_path).name,
                    defer_per_run_lifted_path=data_dir
                    / Path(c.defer_per_run_lifted_path).name,
                    input_path=(
                        data_dir / Path(c.input_path).name
                        if Path(campaign.input_dir) == Path(campaign.data_dir)
                        else c.input_path
                    ),
                )
                for c in campaign.configurations
            ),
        )
        target = data_dir / Path(config.coupling_state_path).name

        # 1. a corrupted stamp: the recorded components digest no longer
        #    describes the components the file lists.
        record = json.loads(target.read_text())
        record["components_sha256"] = "0" * 64
        target.write_text(json.dumps(record))
        code, result = check(broken)
        stage.tooth(
            "a corrupted components digest",
            code != 0
            and any(
                not entry["ok"]
                for row in result["ledger"]
                if row["role"] == "coupling_state"
                and row["configuration"] == config.name
                for entry in row["checks"]
                if entry["what"] == "components_sha256 rebuilt"
            ),
            f"components_sha256 of a throwaway copy of {config.name}'s "
            f"coupling-state artifact set to zeros; the rebuild must catch it",
        )

        # 2. an artifact with no harvest identity: refused by name.
        record = json.loads(target.read_text())
        record["components_sha256"] = rebuild_components_sha256(record)
        for key in HARVEST_IDENTITY_KEYS:
            record.pop(key, None)
        target.write_text(json.dumps(record))
        code, result = check(broken)
        stage.tooth(
            "an artifact with no harvest identity",
            code != 0
            and any(
                not entry["ok"]
                for row in result["ledger"]
                if row["role"] == "coupling_state"
                and row["configuration"] == config.name
                for entry in row["checks"]
                if entry["what"] == "harvest identity"
            ),
            "the identity block removed from a throwaway copy; this package "
            "has no derivation stage, so an artifact that cannot say what "
            "produced it must be refused rather than used",
        )
        target.write_text(Path(config.coupling_state_path).read_text())

        # 3. a per-run deferral artifact derived for a different figure of
        #    merit: the same node list, the wrong problem.
        deferral = data_dir / Path(config.defer_per_run_path).name
        record = json.loads(deferral.read_text())
        record["deck"]["i_figure_merit_expected"] = (
            int(record["deck"]["i_figure_merit_expected"]) + 1
        )
        record["nodes_sha256"] = rebuild_nodes_sha256(record)
        deferral.write_text(json.dumps(record))
        code, result = check(broken)
        stage.tooth(
            "a deferral set derived for a different figure of merit",
            code != 0
            and any(
                not entry["ok"]
                for row in result["ledger"]
                if row["role"] == "defer_per_run"
                and row["configuration"] == config.name
                for entry in row["checks"]
                if entry["what"] == "figure of merit against the input file"
            ),
            "the figure of merit changed on a throwaway copy and its "
            "nodes_sha256 recomputed to match, so only the comparison with "
            "the input file can catch it — which is the point: an artifact "
            "that rebuilds its own hash can still be the wrong problem's",
        )
    return (0 if stage.passed else 3), stage.as_record()
