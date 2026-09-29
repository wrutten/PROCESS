#!/usr/bin/env python
"""The committed data this experiment reads, copied here and provably unchanged.

The experiment runs its own copy of the PROCESS package (decision D20 in the
master queue's register), and that copy resolves three artifacts by a path
constant pointing at ``harness/data/``.  The harness resolves five more per
configuration.  All of them already existed in the repository, produced by
earlier tasks; this module **copies them into the experiment's own directory**
and records, per file, where it came from and what its bytes are.

Two claims are made and both are checked rather than asserted:

* every file in ``harness/data/`` is **byte-identical** (sha256) to its source
  at the recorded source commit -- read with ``git cat-file``, never from a
  working tree, so an uncommitted edit beside the source cannot ride along;
* the **file set** matches exactly, because a per-file hash loop that never
  compares the set passes on a removed file and on an added one.

``harness/child/ystate.py`` is recorded here too.  It is code, not data, but it was
moved by the same task and under the same rule, and the claim about it has the
same shape as the one ``PROCESS/copy_gates.py`` makes about the copied driver:
**the file's whole diff against its source at the source commit is exactly the
recorded hunks, and its post-edit sha256 is the recorded one.**

That criterion is a **re-basing**, made by task A59 (driver-predicate-mode) and
recorded here rather than in a commit message.  A48 (harness-data) moved the
module whole and added one paragraph, so the check it could make was the
strongest available: remove the recorded paragraph and the remainder is
byte-identical to the source.  A59 implements driver change DR5 in this module
--- the convergence predicate's second ruler --- so the module is no longer the
source plus a paragraph, and that reconstruction test is no longer available.
Two ways out were possible and only one of them is honest: drop the check, or
re-base it on the model the copied driver already uses, where an edit is legal
because it is **recorded and reviewable** rather than because it is absent.  The
second is what is done.  Concretely:

* every hunk of the diff is recorded in ``harness/data/PROVENANCE.json``, and a
  file whose diff is not exactly those hunks **fails** --- so an edit nobody
  recorded is refused as before;
* the post-edit sha256 is recorded too, so an edit that updated the hunks and
  not the digest fails, and one that updated the digest and not the hunks fails;
* each recorded edit carries what it is, what it does and which task made it
  (:data:`MODULE_EDITS`), so the hunks can be read against a claim instead of
  merely being present;
* where the recorded hunks *are* a pure addition, the old reconstruction test
  still runs and is still required.  It is not weakened where it applies; it is
  only unavailable where it cannot apply, and the record says which of the two
  held.

What is **not** weakened is the thing the check exists for: this revision of the
experiment has exactly one implementation of the predicate (decision D14(c)),
the copied driver loads *this* file by a fixed path, and an unrecorded edit to
it still fails the gate.

The mapping from a role to a file name is **not** decided here.  It is
:func:`harness.core.config.artifact_file_names`, the same function the arms use to
hand a switch its artifact, read under both naming schemes: the experiment's
own names on one side, the repository's older spellings on the other.  If the
two disagree with the declared source list below, this module refuses rather
than choosing.

What is deliberately absent
---------------------------

There is no *derivation* stage.  The scales inside the coupling-state artifacts
are the experiment's frozen ruler; re-deriving them from a new harvest would
change what the tolerance means and break comparability with every earlier
revision that quoted a residual on that ruler.  A campaign that finds an
artifact missing refuses; it never makes one.  (Harness implementation plan
section 5.4, ruled 2026-09-10.)

Heritage: new in task A48 (harness-data); it derives from no earlier file.  The
copy rule is the harness implementation plan's section 5.2 as ruled under D20.
Standard library only, no PROCESS run, runs in a second.

Usage
-----
    python harness/experiment/data_provenance.py verify      # compare, print, exit 0/1
    python harness/experiment/data_provenance.py plan        # the declared mapping only
    python harness/experiment/data_provenance.py copy --force --source-commit <sha>
    python harness/experiment/data_provenance.py record --force   # re-record, copy nothing

Exit status: 0 everything matches, 1 a comparison failed, 2 setup error.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import difflib
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

_EXPERIMENT_DIR = Path(__file__).resolve().parents[2]
if str(_EXPERIMENT_DIR) not in sys.path:
    sys.path.insert(0, str(_EXPERIMENT_DIR))

from harness.core.config import (  # noqa: E402
    DRIVER_FIXED_ARTIFACTS,
    MEASUREMENT_ARTIFACTS,
    Campaign,
    artifact_file_names,
    default_campaign,
)

HERE = Path(__file__).resolve().parent.parent
DATA_DIR = HERE / "data"
PROVENANCE = DATA_DIR / "PROVENANCE.json"

#: The predicate module, moved whole from the repository's research tree.
YSTATE = HERE / "child" / "ystate.py"

#: Where in the repository each class of source lives.  Relative to the
#: repository root, because that is how ``git cat-file`` addresses a blob.
ARTIFACT_SOURCE_DIR = "arch_surgery/docs/data"
INPUT_FILE_SOURCE_DIR = "arch_surgery/idf_probe/scenarios"
YSTATE_SOURCE = "arch_surgery/fixedpoint/ystate.py"

#: Files in ``harness/data/`` that are the record rather than a copied file.
NOT_A_COPIED_FILE = frozenset({"PROVENANCE.json"})


# ---------------------------------------------------------------------------
# what each copied file is
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DataFile:
    """One copied file: its role, its name here, and where it came from."""

    #: What the file is for.  ``input_file`` for the committed input file; the
    #: artifact roles of :meth:`harness.core.config.Config.artifact_roles`; and the
    #: two roles whose file name a path constant in the copied driver fixes.
    role: str
    #: The configuration it belongs to, or ``None`` for the two shared files.
    configuration: str | None
    #: The file name inside ``harness/data/``.
    name: str
    #: The source path, relative to the repository root.
    source: str
    #: Why the name changed, or why it did not.
    note: str
    #: The commit the copy was taken from, where it is **not** the record's
    #: one source commit: a file added to ``harness/data/`` after the copy of
    #: 2026-09-14 has a source that did not exist at that commit, and it
    #: carries its own (``PROVENANCE.json``'s ``files[<name>].source_commit``).
    #: ``None`` means the record's ``source.commit_full``.
    source_commit: str | None = None

    @property
    def source_name(self) -> str:
        return self.source.rsplit("/", 1)[-1]


def declared_files(campaign: Campaign) -> list[DataFile]:
    """Every file ``harness/data/`` holds, derived from the naming schemes.

    The role-to-name mapping comes from :func:`artifact_file_names` under both
    schemes -- ``harness`` for the name here, ``repository`` for the source --
    so this list cannot drift from the mapping the arms actually compose with.
    A steady-state configuration has no lifted input file, so its two per-run
    deferral roles resolve to one file and it is copied once.
    """
    files: list[DataFile] = []
    for config in campaign.configurations:
        files.append(
            DataFile(
                role="input_file",
                configuration=config.name,
                name=f"{config.name}.IN.DAT",
                source=f"{INPUT_FILE_SOURCE_DIR}/{config.name}.IN.DAT",
                note=(
                    "the committed input file, never edited (decision D9: the "
                    "committed input files are the experiment's fixed input); "
                    "the name is unchanged"
                ),
            )
        )
        here = artifact_file_names(
            config.name, pulsed=config.pulsed, naming="harness"
        )
        there = artifact_file_names(
            config.name, pulsed=config.pulsed, naming="repository"
        )
        seen: set[str] = set()
        for role in ("coupling_state", "write_sets", "defer_per_run",
                     "defer_per_run_lifted"):
            if here[role] in seen:
                continue
            seen.add(here[role])
            if role == "defer_per_run" and not config.pulsed:
                note = (
                    "steady state: there is no lifted input file, so one file "
                    "serves both per-run deferral roles and is copied once"
                )
            else:
                note = (
                    "renamed for the role it plays: no task token and no "
                    "revision token in the name"
                )
            files.append(
                DataFile(
                    role=role,
                    configuration=config.name,
                    name=here[role],
                    source=f"{ARTIFACT_SOURCE_DIR}/{there[role]}",
                    note=note,
                )
            )
    for role, fixed in DRIVER_FIXED_ARTIFACTS.items():
        files.append(
            DataFile(
                role=role,
                configuration=None,
                name=fixed,
                source=f"{ARTIFACT_SOURCE_DIR}/{fixed}",
                note=(
                    "the name is fixed by a path constant inside the copied "
                    "driver; renaming it would be a driver edit"
                ),
            )
        )
    for role, fixed in MEASUREMENT_ARTIFACTS.items():
        # Read by the measurement layer only; its source commit is its own
        # (``files[<name>].source_commit`` in the record), because the file
        # was generated and committed after the one copy of 2026-09-14.
        files.append(
            DataFile(
                role=role,
                configuration=None,
                name=fixed,
                source=f"{ARTIFACT_SOURCE_DIR}/{fixed}",
                note=(
                    "read by the measurement layer, never by the driver; "
                    "generated once from the dependency analysis's exports at "
                    "the named pin by arch_surgery/fixedpoint/gen_function_counts.py "
                    "and committed as data (trap T9); the name is unchanged"
                ),
                source_commit=None,
            )
        )
    return files


#: The mapping this task was dispatched with, written out so that the code's
#: mapping and the brief's are compared rather than one of them being trusted.
#: ``{harness name: source name}``, in the order of :func:`declared_files`.
EXPECTED_MAPPING: dict[str, str] = {
    "large_tokamak_nof.IN.DAT": "large_tokamak_nof.IN.DAT",
    "coupling_state_large_tokamak_nof.json": "ystate_a26_large_tokamak_nof.json",
    "write_sets_large_tokamak_nof.json": "writeset_a26_large_tokamak_nof.json",
    "defer_per_run_large_tokamak_nof.json": "postsolve_nolift_large_tokamak_nof.json",
    "defer_per_run_lifted_large_tokamak_nof.json": "postsolve_large_tokamak_nof.json",
    "low_aspect_ratio_DEMO.IN.DAT": "low_aspect_ratio_DEMO.IN.DAT",
    "coupling_state_low_aspect_ratio_DEMO.json": "ystate_a26_low_aspect_ratio_DEMO.json",
    "write_sets_low_aspect_ratio_DEMO.json": "writeset_a26_low_aspect_ratio_DEMO.json",
    "defer_per_run_low_aspect_ratio_DEMO.json": "postsolve_nolift_low_aspect_ratio_DEMO.json",
    "defer_per_run_lifted_low_aspect_ratio_DEMO.json": "postsolve_low_aspect_ratio_DEMO.json",
    "st_regression.IN.DAT": "st_regression.IN.DAT",
    "coupling_state_st_regression.json": "ystate_a26_st_regression.json",
    "write_sets_st_regression.json": "writeset_a26_st_regression.json",
    "defer_per_run_st_regression.json": "postsolve_st_regression.json",
    "node_writesets.json": "node_writesets.json",
    "dsm_node_map.json": "dsm_node_map.json",
    "dsm_function_counts.json": "dsm_function_counts.json",
}


def assert_mapping_agrees(files: list[DataFile]) -> None:
    """Refuse if the code's mapping and the declared one disagree.

    Two independent statements of the same mapping, compared instead of one of
    them being believed.  A disagreement is a finding to report, never
    something to resolve by picking a side, so this raises.
    """
    got = {f.name: f.source_name for f in files}
    if got != EXPECTED_MAPPING:
        only_code = {k: v for k, v in got.items() if EXPECTED_MAPPING.get(k) != v}
        only_declared = {
            k: v for k, v in EXPECTED_MAPPING.items() if got.get(k) != v
        }
        raise SystemExit(
            "the artifact mapping in harness/core/config.py and the mapping this "
            "module declares disagree, so neither is used.  From the code: "
            f"{only_code}.  Declared here: {only_declared}."
        )


# ---------------------------------------------------------------------------
# git access -- always the commit, never a working tree
# ---------------------------------------------------------------------------


def _git(*args: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(HERE), *args], check=True, stdout=subprocess.PIPE
    ).stdout


def repo_root() -> Path:
    return Path(_git("rev-parse", "--show-toplevel").decode().strip())


def blob_at(commit: str, path: str) -> bytes | None:
    """The bytes of ``path`` at ``commit``, or ``None`` if it is not there."""
    proc = subprocess.run(
        ["git", "-C", str(HERE), "cat-file", "blob", f"{commit}:{path}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    return proc.stdout if proc.returncode == 0 else None


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class SourceBytes:
    """The source of one file, and how it was obtained."""

    data: bytes
    read_from: str  # "commit <sha>" or "working tree <path>"


def source_bytes(item_source: str, commit: str | None) -> SourceBytes:
    """The source file's bytes, from the commit where one is available.

    The commit is the stronger source and is used whenever the blob is there.
    Falling back to the working tree is recorded in the verdict rather than
    hidden, because "compared against a working tree" is a weaker claim than
    "compared against the commit" and a reader must be able to tell which was
    made.
    """
    if commit:
        data = blob_at(commit, item_source)
        if data is not None:
            return SourceBytes(data, f"commit {commit[:8]}")
    path = repo_root() / item_source
    if not path.exists():
        raise SystemExit(
            f"{item_source} is neither at commit {commit} nor in the working "
            f"tree at {path}; there is nothing to compare against."
        )
    return SourceBytes(path.read_bytes(), f"working tree {path}")


# ---------------------------------------------------------------------------
# the moved predicate module
# ---------------------------------------------------------------------------


#: Every recorded change ``harness/child/ystate.py`` carries against its source, in
#: the order the tasks made them.  This is documentation *of* the hunks, not a
#: substitute for them: the check compares the hunks and the digest, and this
#: list is what lets a reviewer read one against a claim.  Same model, same
#: fields and the same purpose as ``PROCESS/copy_gates.py``'s ``PermittedEdit``.
MODULE_EDITS: tuple[dict[str, str], ...] = (
    {
        "kind": "heritage paragraph",
        "name": "the module docstring's Heritage section",
        "description": (
            "the module was moved whole out of the repository's research tree "
            "into the experiment's own harness, and says so, with the reason "
            "it was moved rather than imported"
        ),
        "task": "A48 (harness-data)",
    },
    {
        "kind": "second ruler",
        "name": "RULER_FROZEN / RULER_MIXED / RULERS, and the ruler argument",
        "description": (
            "the convergence predicate's denominator becomes an argument.  "
            "'frozen' is max|dy_i| / s_i -- the measured scale alone, every "
            "earlier revision's ruler, the default here, and bit-for-bit "
            "unchanged.  'mixed' is max|dy_i| / max(|y_i|, s_i), the "
            "conventional scaled step with that scale kept as a floor under "
            "the current magnitude, where |y_i| is the current value's "
            "characteristic magnitude taken exactly as the scale was.  The two "
            "are bit-identical wherever |y_i| <= s_i and 'mixed' is never "
            "tighter, so no count can go up; discrete components, moved "
            "constants, a new NaN, a changed non-finite pattern and an "
            "unwritten component all behave identically under both.  A ruler "
            "that is neither is refused, never defaulted around"
        ),
        "task": "A59 (driver-predicate-mode)",
    },
    {
        "kind": "per-component reporting",
        "name": "Residual.denominator / .magnitude / .bound_by / "
                ".value_over_scale / .binding_components / .ruler_detail",
        "description": (
            "the residual says which term bound each component's denominator "
            "and what |y_i| / s_i was there, so the set of components on which "
            "the two rulers can disagree is read from the residual rather than "
            "inferred.  brief()'s six keys are deliberately untouched: they are "
            "compared value for value by the switch-neutrality gate, so the new "
            "reporting is a separate method"
        ),
        "task": "A59 (driver-predicate-mode)",
    },
)


def module_hunks(source: bytes, copy: bytes, label: str) -> list[str]:
    """The unified diff of the moved module, zero context, as a line list.

    Zero context so the record shows the added lines and their position and
    nothing else.  The same construction ``PROCESS/copy_gates.py`` uses for the
    copied driver's permitted edits, so one reading habit covers both.
    """
    return [
        line.rstrip("\n")
        for line in difflib.unified_diff(
            source.decode().splitlines(keepends=True),
            copy.decode().splitlines(keepends=True),
            fromfile=f"source commit:{label}",
            tofile=f"copy:{label}",
            n=0,
        )
    ]


def is_pure_addition(hunks: list[str]) -> bool:
    """Whether the recorded diff is one hunk that only adds lines.

    The reconstruction test below is available only then.  It is *not* the
    identity criterion -- that is the hunks and the digest, as it is for the
    copied driver -- but where it applies it is a second, independent way of
    saying the same thing, and it is kept for exactly that reason.
    """
    headers = [line for line in hunks if line.startswith("@@")]
    removals = [
        line
        for line in hunks
        if line.startswith("-") and not line.startswith("---")
    ]
    return len(headers) == 1 and not removals


def strip_recorded_hunk(copy_text: str, hunks: list[str]) -> str | None:
    """``copy_text`` with the recorded addition removed, or ``None``.

    Applies only where :func:`is_pure_addition` holds: the recorded hunk is a
    single pure addition -- a heritage paragraph and nothing else -- so removing
    it is well defined.  Anything else and this returns ``None``; the caller
    checks :func:`is_pure_addition` first and reports which of the two
    criteria it was able to apply, rather than treating "cannot reconstruct" as
    a failure of a file that never claimed to be reconstructible.
    """
    added: list[str] = []
    header: str | None = None
    for line in hunks:
        if line.startswith("@@"):
            if header is not None:
                return None  # more than one hunk: not a single paragraph
            header = line
        elif line.startswith("+++") or line.startswith("---"):
            continue
        elif line.startswith("+"):
            added.append(line[1:])
        elif line.startswith("-"):
            return None  # a removal: not a pure addition
    if header is None:
        return "" if not copy_text else copy_text
    match = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", header)
    if match is None:
        return None
    start = int(match.group(3)) - 1
    count = int(match.group(4) or 1)
    lines = copy_text.splitlines(keepends=True)
    if [line.rstrip("\n") for line in lines[start : start + count]] != [
        a.rstrip("\n") for a in added
    ]:
        return None
    return "".join(lines[:start] + lines[start + count :])


# ---------------------------------------------------------------------------
# the declarations the artifacts have to agree with
# ---------------------------------------------------------------------------

_IXC = re.compile(rb"^[ \t]*ixc[ \t]*=", re.MULTILINE)
_ICC = re.compile(rb"^[ \t]*icc[ \t]*=", re.MULTILINE)


def declaration_checks(campaign: Campaign, root: Path) -> list[dict]:
    """Three numbers per configuration, compared against the files themselves.

    ``harness/core/config.py`` states each configuration's coupling-state component
    count, its iteration-variable count and its constraint count.  All three
    are properties of committed files, so all three are read back from the
    files rather than trusted: the component count from the coupling-state
    artifact's own ``n_components``, and the other two by counting the input
    file's ``ixc =`` and ``icc =`` statements, one entry per statement.
    """
    rows: list[dict] = []
    for config in campaign.configurations:
        coupling = root / config.coupling_state_path.name
        n_components: object = "absent"
        if coupling.exists():
            try:
                n_components = json.loads(coupling.read_text()).get("n_components")
            except Exception as exc:  # noqa: BLE001 - reported, not raised
                n_components = f"unreadable: {exc}"
        input_file = root / config.input_path.name
        n_ixc: object = "absent"
        n_icc: object = "absent"
        if input_file.exists():
            raw = input_file.read_bytes()
            n_ixc = len(_IXC.findall(raw))
            n_icc = len(_ICC.findall(raw))
        rows.extend(
            [
                {
                    "configuration": config.name,
                    "quantity": "coupling-state components",
                    "declared": config.n_coupling_components,
                    "in_the_file": n_components,
                    "read_from": coupling.name,
                    "agrees": n_components == config.n_coupling_components,
                },
                {
                    "configuration": config.name,
                    "quantity": "iteration variables",
                    "declared": config.n_iteration_variables,
                    "in_the_file": n_ixc,
                    "read_from": input_file.name,
                    "agrees": n_ixc == config.n_iteration_variables,
                },
                {
                    "configuration": config.name,
                    "quantity": "constraints",
                    "declared": config.n_constraints,
                    "in_the_file": n_icc,
                    "read_from": input_file.name,
                    "agrees": n_icc == config.n_constraints,
                },
            ]
        )
    return rows


# ---------------------------------------------------------------------------
# verification
# ---------------------------------------------------------------------------


@dataclass
class Verdict:
    """The result of comparing one directory against one provenance record."""

    n_declared: int = 0
    n_identical: int = 0
    failures: list[str] = None  # type: ignore[assignment]
    notes: list[str] = None  # type: ignore[assignment]
    read_from: set = None  # type: ignore[assignment]
    missing: list[str] = None  # type: ignore[assignment]
    added: list[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        self.failures = []
        self.notes = []
        self.read_from = set()
        self.missing = []
        self.added = []

    @property
    def passed(self) -> bool:
        return not self.failures


def verify(
    prov: dict,
    data_dir: Path,
    *,
    ystate_path: Path | None = None,
    campaign: Campaign | None = None,
) -> Verdict:
    """Compare ``data_dir`` against the provenance record, file by file.

    Everything the check binds is here, so the self-check's teeth can run this
    against a throwaway copy of the directory and the real one is never
    touched.
    """
    res = Verdict()
    commit = prov["source"]["commit_full"]
    recorded = prov["files"]

    on_disk = {
        p.name
        for p in sorted(data_dir.iterdir())
        if p.is_file() and p.name not in NOT_A_COPIED_FILE
    }
    res.missing = sorted(set(recorded) - on_disk)
    res.added = sorted(on_disk - set(recorded))
    for name in res.missing:
        res.failures.append(f"file missing from harness/data/: {name}")
    for name in res.added:
        res.failures.append(
            f"file in harness/data/ that the provenance record does not "
            f"name: {name}"
        )

    for name in sorted(recorded):
        entry = recorded[name]
        res.n_declared += 1
        path = data_dir / name
        if not path.exists():
            continue
        got = sha256(path.read_bytes())
        if got != entry["sha256"]:
            res.failures.append(
                f"{name}: sha256 {got}, the provenance record says "
                f"{entry['sha256']}"
            )
            continue
        # A file added after the one copy carries its own source commit; the
        # rest are read at the record's.
        src = source_bytes(entry["source"], entry.get("source_commit") or commit)
        res.read_from.add(src.read_from)
        if sha256(src.data) != entry["sha256"]:
            res.failures.append(
                f"{name}: differs from its source {entry['source']} "
                f"(source sha256 {sha256(src.data)}, copy {got})"
            )
            continue
        res.n_identical += 1

    if ystate_path is not None:
        res.n_declared += 1
        module = prov["module"]
        if not ystate_path.exists():
            res.failures.append(f"{module['name']} is not present at {ystate_path}")
        else:
            copy = ystate_path.read_bytes()
            if sha256(copy) != module["sha256_in_copy"]:
                res.failures.append(
                    f"{module['name']}: sha256 {sha256(copy)}, the provenance "
                    f"record says {module['sha256_in_copy']}"
                )
            src = source_bytes(module["source"], commit)
            res.read_from.add(src.read_from)
            got_hunks = module_hunks(src.data, copy, module["source"])
            if got_hunks != module["expected_hunks"]:
                res.failures.append(
                    f"{module['name']}: its difference from "
                    f"{module['source']} is not the recorded set of hunks "
                    f"({len(got_hunks)} diff line(s) against "
                    f"{len(module['expected_hunks'])} recorded).  An edit that "
                    f"is not recorded is refused, whatever the digest says"
                )
            elif is_pure_addition(module["expected_hunks"]):
                # The recorded edit adds lines and removes none, so the
                # stronger reconstruction claim is available and is required.
                stripped = strip_recorded_hunk(copy.decode(), module["expected_hunks"])
                if stripped is None or stripped.encode() != src.data:
                    res.failures.append(
                        f"{module['name']}: with the recorded addition removed "
                        f"it is not byte-identical to {module['source']}"
                    )
                else:
                    res.n_identical += 1
                    res.notes.append(
                        f"{module['name']}: {len(module['expected_hunks'])} "
                        f"recorded diff line(s), a pure addition; with them "
                        f"removed the file is byte-identical to "
                        f"{module['source']} (sha256 {sha256(src.data)[:12]})"
                    )
            else:
                # The recorded edits change the module rather than only add to
                # it, so the criterion is the copied driver's: the whole diff
                # is exactly the recorded hunks and the post-edit digest is the
                # recorded one.  Both were checked above; what is stated here
                # is which criterion held and what the recorded edits claim to
                # be, so a reader is not left to infer either.
                res.n_identical += 1
                res.notes.append(
                    f"{module['name']}: {len(module['expected_hunks'])} "
                    f"recorded diff line(s) in "
                    f"{sum(1 for h in module['expected_hunks'] if h.startswith('@@'))} "
                    f"hunk(s) against {module['source']} at the source commit, "
                    f"and the post-edit sha256 is the recorded one.  The "
                    f"recorded edits are not a pure addition, so the identity "
                    f"criterion is the copied driver's -- exactly these hunks, "
                    f"exactly this digest -- and not reconstruction of the "
                    f"source: "
                    + "; ".join(
                        f"{e['kind']} ({e['task']})"
                        for e in module.get("recorded_edits", ())
                    )
                )

    if campaign is not None:
        rows = declaration_checks(campaign, data_dir)
        disagree = [r for r in rows if not r["agrees"]]
        for row in disagree:
            res.failures.append(
                f"{row['configuration']}: harness/core/config.py declares "
                f"{row['declared']} {row['quantity']}, {row['read_from']} has "
                f"{row['in_the_file']}"
            )
        res.notes.append(
            f"{len(rows) - len(disagree)}/{len(rows)} declared counts agree "
            f"with the files (3 configurations x coupling-state components, "
            f"iteration variables, constraints)"
        )
    return res


# ---------------------------------------------------------------------------
# building the record
# ---------------------------------------------------------------------------


def file_entry(item: DataFile, commit: str) -> dict:
    """One file's record entry: its copy compared byte for byte with its
    source at *commit*, and refused if they differ."""
    src = source_bytes(item.source, commit)
    copy = DATA_DIR / item.name
    if not copy.exists():
        raise SystemExit(f"{copy} is not present; copy the files first.")
    data = copy.read_bytes()
    if data != src.data:
        raise SystemExit(
            f"refusing to write PROVENANCE.json: {item.name} is not "
            f"byte-identical to {item.source}.  Regenerating provenance "
            "must never be the way a changed file becomes blessed."
        )
    record = json.loads(data) if item.name.endswith(".json") else {}
    entry = {
        "role": item.role,
        "configuration": item.configuration,
        "source": item.source,
        "source_name": item.source_name,
        "sha256": sha256(data),
        "bytes": len(data),
        "note": item.note,
        "artifact_fields": {
            key: record[key]
            for key in ("format", "scenario", "generated_by", "tree_git_head")
            if key in record
        },
    }
    if "ystate_artifact" in record:
        entry["artifact_fields"]["ystate_artifact"] = record["ystate_artifact"]
    return entry


def add_file(name: str, commit: str, campaign: Campaign) -> dict:
    """Add **one** measurement artifact to the record, copying it from its
    source at *commit* and recording that commit on the entry.

    The record's other entries are not touched and nothing is re-blessed:
    the one file is written into ``harness/data/`` from the commit (never from
    a working tree), compared, and entered with ``source_commit``.  A name that
    is not a declared measurement artifact, or that already has an entry, is
    refused.
    """
    files = declared_files(campaign)
    assert_mapping_agrees(files)
    item = next((f for f in files if f.name == name), None)
    if item is None or item.role not in MEASUREMENT_ARTIFACTS:
        raise SystemExit(
            f"{name} is not a declared measurement artifact "
            f"({sorted(MEASUREMENT_ARTIFACTS.values())}); `add` enters those "
            f"only -- every other file is the one copy's"
        )
    prov = load_provenance()
    if name in (prov.get("files") or {}):
        raise SystemExit(
            f"{name} already has an entry in {PROVENANCE}; re-adding would "
            f"re-bless whatever the source holds now"
        )
    full = _git("rev-parse", commit).decode().strip()
    src = source_bytes(item.source, full)
    if not src.read_from.startswith("commit "):
        raise SystemExit(
            f"{item.source} is not at commit {full}; a measurement artifact is "
            f"copied from a commit, never from a working tree"
        )
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / name).write_bytes(src.data)
    entry = file_entry(item, full)
    entry["source_commit"] = full
    entry["added_by"] = (
        "harness/experiment/data_provenance.py add -- one measurement artifact "
        "entered after the copy of 2026-09-14, from its own source commit"
    )
    prov["files"][name] = entry
    return prov


def build_provenance(commit: str, campaign: Campaign) -> dict:
    """Assemble the provenance record from the commit and the files on disk."""
    full = _git("rev-parse", commit).decode().strip()
    files = declared_files(campaign)
    assert_mapping_agrees(files)

    entries: dict[str, dict] = {}
    for item in files:
        if item.role in MEASUREMENT_ARTIFACTS:
            # Not blessed by a rebuild: a measurement artifact enters the
            # record through ``add``, with its own source commit, and a rebuild
            # keeps the entry it already has rather than re-reading it at the
            # record's commit, where its source does not exist.
            existing = (load_provenance().get("files") or {}).get(item.name) if PROVENANCE.exists() else None
            if existing is None:
                raise SystemExit(
                    f"{item.name} is a measurement artifact with no entry in "
                    f"{PROVENANCE}; add it with `data_provenance.py add "
                    f"{item.name} --source-commit <commit>` first"
                )
            entries[item.name] = existing
            continue
        entries[item.name] = file_entry(item, full)

    ystate_src = source_bytes(YSTATE_SOURCE, full)
    ystate_copy = YSTATE.read_bytes()
    ystate_hunks = module_hunks(ystate_src.data, ystate_copy, YSTATE_SOURCE)
    module = {
        "what": (
            "The coupling-state predicate: which fields make up y, their "
            "categories and scales, the residual, and the convergence test in "
            "both of its rulers.  It is code, not data, and the copied driver "
            "loads it by path (module_solve.YSTATE_MODULE_PATH).  Moved whole "
            "out of the research tree, then changed by the approved driver "
            "change DR5, which added the second ruler.  The identity claim is "
            "the one the copied driver carries: the whole diff against the "
            "source at the source commit is exactly the hunks recorded below, "
            "and the post-edit sha256 is the one recorded below.  An edit "
            "nobody recorded fails either way round -- stale hunks are caught "
            "by the digest, a digest updated to match is caught by the hunks."
        ),
        "identity_criterion": (
            "the recorded hunks and the post-edit sha256"
            if not is_pure_addition(ystate_hunks)
            else "the recorded hunks, the post-edit sha256, and reconstruction "
                 "of the source by removing the recorded addition"
        ),
        "criterion_rebased_by": (
            "A59 (driver-predicate-mode).  A48 (harness-data) moved the module "
            "whole and added one paragraph, so it could require that removing "
            "the paragraph reproduced the source byte for byte.  DR5 changes "
            "the module, so that reconstruction is no longer available; the "
            "criterion is re-based on the model PROCESS/copy_gates.py already "
            "uses for the copied driver -- an edit is legal because it is "
            "recorded and reviewable, not because it is absent -- and the "
            "reconstruction test still runs wherever the recorded hunks are a "
            "pure addition."
        ),
        "name": "harness/child/ystate.py",
        "source": YSTATE_SOURCE,
        "sha256_at_source_commit": sha256(ystate_src.data),
        "sha256_in_copy": sha256(ystate_copy),
        "lines_at_source_commit": ystate_src.data.decode().count("\n"),
        "lines_in_copy": ystate_copy.decode().count("\n"),
        "recorded_edits": [dict(edit) for edit in MODULE_EDITS],
        "expected_hunks": ystate_hunks,
    }

    return {
        "what": (
            "Provenance of the committed data this experiment reads.  Every "
            "file in harness/data/ was copied from the source below at the "
            "source commit, not from a working tree, and is byte-identical to "
            "it.  harness/gates/selfcheck.py's data check verifies both claims and "
            "is runnable at any later commit."
        ),
        "task": "A48 (harness-data)",
        "decision": (
            "D20, 2026-09-10 -- the experiment runs its own copy of PROCESS "
            "and owns its own inputs; harness implementation plan sections 5.2 "
            "and 5.3, ruled the same day"
        ),
        "generated_by": "harness/data_provenance.py copy",
        "copy_date": _dt.date.today().isoformat(),
        "source": {
            "repository": (
                "PROCESS_surgery (this repository), branch architecture_surgery"
            ),
            "artifact_path": f"{ARTIFACT_SOURCE_DIR}/",
            "input_file_path": f"{INPUT_FILE_SOURCE_DIR}/",
            "predicate_module_path": YSTATE_SOURCE,
            "commit": full[:8],
            "commit_full": full,
            "read_with": "git cat-file blob <commit>:<path>",
        },
        "stale_internal_names": {
            "what": (
                "Each write_sets_<configuration>.json carries an internal "
                "field ystate_artifact naming the file it was built against "
                "under the repository's older spelling "
                "(ystate_a26_<configuration>.json), which is the name the "
                "coupling-state artifact no longer has here.  The field is "
                "left as it stands: the copy is byte-identical to its source, "
                "and editing it would forfeit that."
            ),
            "why_it_is_harmless": (
                "The driver never pairs the two files by name.  "
                "process/core/solver/module_solve.py's load_subsets (the "
                "docstring at lines 631-635, the check at lines 642-649) "
                "requires the write set's ystate_components_sha256 to equal "
                "the loaded coupling-state spec's own components_sha256 and "
                "raises otherwise -- a content hash over the component list, "
                "not a file name.  A wrong pairing is caught by the bytes; a "
                "renamed file is not noticed at all."
            ),
            "fields": {
                name: entry["artifact_fields"]["ystate_artifact"]
                for name, entry in sorted(entries.items())
                if "ystate_artifact" in entry["artifact_fields"]
            },
        },
        "not_derivable_here": (
            "The scales inside the coupling-state artifacts come from a "
            "harvest that is untracked by policy.  This experiment uses the "
            "committed artifacts as its frozen ruler and never regenerates "
            "them: a campaign that finds one missing refuses.  Harness "
            "implementation plan section 5.4."
        ),
        "module": module,
        "files": entries,
    }


def copy_files(campaign: Campaign, commit: str) -> list[tuple[str, str]]:
    """Write every declared file into ``harness/data/`` from the commit."""
    files = declared_files(campaign)
    assert_mapping_agrees(files)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    written = []
    for item in files:
        if item.role in MEASUREMENT_ARTIFACTS:
            # entered by `add` from its own source commit, never by the copy
            continue
        src = source_bytes(item.source, commit)
        (DATA_DIR / item.name).write_bytes(src.data)
        written.append((item.name, src.read_from))
    return written


# ---------------------------------------------------------------------------
# entry point
# ---------------------------------------------------------------------------


def load_provenance() -> dict:
    if not PROVENANCE.exists():
        raise SystemExit(
            f"{PROVENANCE} is not present; harness/data/ has no provenance and "
            "nothing can be checked against it."
        )
    return json.loads(PROVENANCE.read_text())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=["verify", "plan", "copy", "record", "add"])
    parser.add_argument(
        "name",
        nargs="?",
        default=None,
        help="add: the one measurement artifact to enter (its name in harness/data/)",
    )
    parser.add_argument("--force", action="store_true", help="copy: overwrite")
    parser.add_argument(
        "--source-commit",
        default=None,
        help="the commit the files are copied from (defaults to the one "
        "already recorded, which never changes for a given copy)",
    )
    args = parser.parse_args(argv)
    campaign = default_campaign()

    if args.command == "plan":
        files = declared_files(campaign)
        assert_mapping_agrees(files)
        print(f"{len(files)} declared file(s):\n")
        for item in files:
            print(f"  {item.name:<46s} <- {item.source}")
            print(f"      role {item.role}   configuration {item.configuration}")
        return 0

    if args.command == "copy":
        if PROVENANCE.exists() and not args.force:
            raise SystemExit(
                f"{PROVENANCE} already exists.  Re-copying re-blesses whatever "
                "the sources currently hold, so it needs --force and a "
                "reviewer who reads the resulting diff."
            )
        commit = args.source_commit
        if commit is None:
            if not PROVENANCE.exists():
                raise SystemExit(
                    "no PROVENANCE.json to take the source commit from; pass "
                    "--source-commit explicitly."
                )
            commit = load_provenance()["source"]["commit_full"]
        full = _git("rev-parse", commit).decode().strip()
        for name, read_from in copy_files(campaign, full):
            print(f"  wrote {name}  (from {read_from})")
        prov = build_provenance(full, campaign)
        PROVENANCE.write_text(json.dumps(prov, indent=2) + "\n")
        print(f"\nwrote {PROVENANCE}")
        print(f"  source commit {prov['source']['commit_full']}")
        print(f"  {len(prov['files'])} files + {prov['module']['name']}")
        return 0

    if args.command == "add":
        if not args.name or not args.source_commit:
            raise SystemExit("add needs the file name and --source-commit <commit>")
        prov = add_file(args.name, args.source_commit, campaign)
        PROVENANCE.write_text(json.dumps(prov, indent=2) + "\n")
        entry = prov["files"][args.name]
        print(f"added {args.name} to {PROVENANCE}")
        print(f"  source        {entry['source']} at {entry['source_commit']}")
        print(f"  sha256        {entry['sha256']}  ({entry['bytes']} bytes)")
        print(f"  {len(prov['files'])} files + {prov['module']['name']}")
        return 0

    if args.command == "record":
        # Rebuild the record from the files as they stand, copying nothing.
        # This is what a task that *edits* the predicate module runs: re-copying
        # the data would re-bless whatever the sources hold, which is a far
        # larger claim than the one being made.  The symmetry is deliberate --
        # PROCESS/copy_gates.py's "provenance --force" does exactly this for the
        # copied driver, and for the same reason.
        if PROVENANCE.exists() and not args.force:
            raise SystemExit(
                f"{PROVENANCE} already exists.  Re-recording blesses whatever "
                "harness/data/ and the predicate module currently hold, so it "
                "needs --force and a reviewer who reads the resulting diff."
            )
        commit = args.source_commit
        if commit is None:
            commit = load_provenance()["source"]["commit_full"]
        full = _git("rev-parse", commit).decode().strip()
        prov = build_provenance(full, campaign)
        PROVENANCE.write_text(json.dumps(prov, indent=2) + "\n")
        print(f"wrote {PROVENANCE} (nothing copied)")
        print(f"  source commit {prov['source']['commit_full']}")
        print(f"  {len(prov['files'])} files + {prov['module']['name']}")
        print(f"  module criterion: {prov['module']['identity_criterion']}")
        print(f"  module hunks    : {len(prov['module']['expected_hunks'])} "
              f"diff line(s), "
              f"{sum(1 for h in prov['module']['expected_hunks'] if h.startswith('@@'))} "
              f"hunk(s)")
        return 0

    prov = load_provenance()
    res = verify(prov, DATA_DIR, ystate_path=YSTATE, campaign=campaign)
    print(f"source commit : {prov['source']['commit_full']}")
    print(f"compared      : {res.n_declared}  identical: {res.n_identical}")
    print(f"read from     : {', '.join(sorted(res.read_from)) or '(nothing)'}")
    for note in res.notes:
        print(f"  . {note}")
    for failure in res.failures:
        print(f"  FAILURE: {failure}")
    print("verdict: " + ("PASS" if res.passed else "FAIL"))
    return 0 if res.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
