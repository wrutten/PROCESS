"""The lifted input file: where it comes from, and how it is checked.

A **configuration** is one optimisation problem and its **input file** is the
file that problem is read from.  Two arms read a *lifted* input file — one in
which the burn time has become an optimiser variable — and that file is
**derived** from the committed one by an edit of exactly three lines: the burn
time becomes iteration variable 178, its consistency residual becomes equality
constraint 93 inserted inside the input file's equality block with the count
raised in the same edit, and the variable's initial value is set to the burn
time the incumbent's own loop settles on at the configuration's starting design
vector.

This module has two halves.  The first — *resolve the file, and refuse anything
that is not the one the experiment declares* — is what the run path needs, and
rests on the two digests committed below.  The second is the **derivation**
itself: :func:`stage_derive` measures the settled burn time with one evaluation
of the model set and rebuilds the file from the committed one, and its gate is
those same two digests.

Why the digests are committed rather than trusted.  Gate GR — the check that
rewriting the harness did not move the measurement — runs the two lifted arms,
and it must run them on **the same bytes the previous revision ran**.  Deriving
the file afresh with nothing to check it against would put a second variable
into a comparison whose whole argument is that only the harness changed.  So the
derivation is gated on the bytes, not merely reviewed.

A note on the derived file's own text.  Its header and its three edit comments
are reproduced **verbatim** from the script that first produced it, task tokens
and all, because the digest is the gate: a tidier comment is a different file
and would fail it.  The harness-plan rule against version and task tokens
(§11.1) binds identifiers in this package; it cannot bind the bytes of a file
whose byte-identity with the previous revision's is the thing being proved.

Derived from ``arch_surgery/idf_probe/a25_variant_deck.py`` (the three-line edit
and the settled-burn-time rule) and
``arch_surgery/MDA_partitioning_experiment_v3/v3_runner.py::deck_for``, read at
``9a8defa6``; task **A50 (harness-run)** wrote the resolution half, task
**A51 (harness-artifacts)** the derivation, at ``f1f90c20``.
"""

from __future__ import annotations

import hashlib
import re
import shutil
from pathlib import Path
from typing import Any, Mapping, Sequence

from ..core.config import Campaign, Config


class InputFileError(RuntimeError):
    """A refusal to run on an input file the experiment does not declare."""


#: sha256 of each configuration's lifted input file.  Measured, not chosen: the
#: three revisions that have derived it — the two earlier experiment revisions
#: and the task that first built the derivation — produced byte-identical files,
#: read from the main checkout on 2026-09-10 at all three paths.  A steady-state
#: configuration has no lifted input file and is absent from this map, which is
#: what makes asking for one a refusal rather than a missing file.
LIFTED_INPUT_SHA256: dict[str, str] = {
    "large_tokamak_nof":
        "8902a6a58bb3ce07223fbc774b84c4cc7082b95d6c40b5b0c88d7c99fe6f4aab",
    "low_aspect_ratio_DEMO":
        "189c5e1e99c21f1f6a35d471380923d7d26f43cbf84ca2063c6efcf072dd0aaa",
}

#: Where the digests came from, quoted in the record so a reader does not have
#: to take them on trust.
LIFTED_INPUT_PROVENANCE = {
    "what": (
        "the lifted input file derived from the committed one by the "
        "three-line edit described in this module's docstring"
    ),
    "measured_from": [
        "arch_surgery/MDA_partitioning_experiment_v3/runs/_decks/<name>/<name>_lifted.IN.DAT",
        "arch_surgery/MDA_partitioning_experiment_v2/runs/_decks/<name>/<name>_lifted.IN.DAT",
        "arch_surgery/idf_probe/runs/a28/_decks/<name>/<name>_lifted.IN.DAT",
    ],
    "read_on": "2026-09-10, in the main checkout; all three byte-identical",
    "derivation_owner": "task A51 (harness-artifacts); its gate is these digests",
}


def sha256_of(path: Path) -> str:
    """The sha256 of a file's bytes."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def is_lifted_available(config: Config, campaign: Campaign) -> bool:
    """Whether the lifted input file this configuration needs is in place."""
    if not config.pulsed:
        return True
    return lifted_path(config, campaign).exists()


def lifted_path(config: Config, campaign: Campaign) -> Path:
    """Where the lifted input file lives once it has been produced."""
    return (
        Path(campaign.derived_input_dir)
        / config.name
        / f"{config.name}_lifted.IN.DAT"
    )


def assert_lifted(config: Config, campaign: Campaign) -> dict[str, Any]:
    """Refuse unless the lifted input file is present and is the declared one.

    Returns its identity for the record: an input file a run record does not
    name by digest is an input file nobody can check afterwards.
    """
    if not config.pulsed:
        raise InputFileError(
            f"{config.name} is a steady-state configuration: there is no "
            f"burn-time coupling, so no arm reads a lifted input file and none "
            f"is derived for it"
        )
    expected = LIFTED_INPUT_SHA256.get(config.name)
    if expected is None:
        raise InputFileError(
            f"no digest is recorded for {config.name}'s lifted input file; the "
            f"digests are {sorted(LIFTED_INPUT_SHA256)}.  A file nobody has "
            f"recorded is not staged on trust."
        )
    path = lifted_path(config, campaign)
    if not path.exists():
        raise InputFileError(
            f"the lifted input file for {config.name} is not at {path}.  It is "
            f"derived by the input-file stage (task A51 (harness-artifacts)); "
            f"until that exists, stage it from a directory holding the "
            f"previous revision's derived files — the runner's "
            f"--lifted-from option — which checks the bytes against the "
            f"recorded digest {expected[:12]}…"
        )
    found = sha256_of(path)
    if found != expected:
        raise InputFileError(
            f"the lifted input file for {config.name} at {path} is not the one "
            f"this experiment declares: sha256 {found} against {expected} "
            f"recorded.  Refused: an arm run on a different problem is not "
            f"that arm."
        )
    return {
        "path": str(path),
        "sha256": found,
        "kind": "lifted",
        "provenance": LIFTED_INPUT_PROVENANCE,
    }


def stage_lifted(
    config: Config, campaign: Campaign, source_dir: Path
) -> dict[str, Any]:
    """Put a previously derived lifted input file where the run path expects it.

    *source_dir* is a directory holding ``<name>/<name>_lifted.IN.DAT``.  The
    bytes are checked against the recorded digest **before** the copy, so a
    wrong file is refused rather than staged and then found.
    """
    if not config.pulsed:
        return {"skipped": f"{config.name} is steady state: no lifted input file"}
    expected = LIFTED_INPUT_SHA256[config.name]
    source = Path(source_dir) / config.name / f"{config.name}_lifted.IN.DAT"
    if not source.exists():
        raise InputFileError(
            f"no lifted input file for {config.name} under {source_dir}: "
            f"{source} does not exist"
        )
    found = sha256_of(source)
    if found != expected:
        raise InputFileError(
            f"{source} is not {config.name}'s lifted input file: sha256 "
            f"{found} against {expected} recorded"
        )
    destination = lifted_path(config, campaign)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    return {
        "configuration": config.name,
        "source": str(source),
        "destination": str(destination),
        "sha256": found,
        "matched_recorded_digest": True,
    }


def identity(path: Path, *, kind: str) -> Mapping[str, Any]:
    """What a record says about the input file it ran."""
    return {"path": str(path), "sha256": sha256_of(path), "kind": kind}


# ==========================================================================
# reading a committed input file
# ==========================================================================
#
# PROCESS's input files are a flat list of ``name = value`` lines; a line
# beginning with ``*`` is a comment and a value line may carry a trailing ``*``
# comment.  The parser below is anchored on that shape rather than on a loose
# search, because a loose search over these files matches the DESCRIPTION
# comments as well as the settings (trap T2 in its general form: a pattern that
# also matches something else reports it as data).

_ICC_RE = re.compile(r"^icc\s*=\s*(\d+)\s*(?:\*.*)?$")
_IXC_RE = re.compile(r"^ixc\s*=\s*(\d+)\s*(?:\*.*)?$")
_MINMAX_RE = re.compile(r"^minmax\s*=\s*(-?\d+)\s*(?:\*.*)?$")
_INT_SWITCH_RE = re.compile(r"^(\w+)\s*=\s*(-?\d+)\s*(?:\*.*)?$")
_EQUALITY_COUNT_RE = re.compile(
    r"^\s*(neqns|n_equality_constraints)\s*=\s*([0-9]+)"
)


def parse_input_file(path: Path | str) -> dict[str, Any]:
    """What an input file declares: the problem, not the physics.

    Returns the constraint list in file order, the iteration-variable list in
    file order, the figure of merit, the declared equality count and every
    integer-valued setting.  Three of those are what makes an artifact
    checkable against the file it was derived for: the figure of merit and the
    active constraint set are exactly what the driver compares an artifact's
    stamp against at load time, and the equality count is what decides which
    ``icc`` entries are equalities.

    Derived from ``arch_surgery/idf_probe/a33_postsolve.py::parse_deck`` at
    ``f1f90c20``; task **A51 (harness-artifacts)**.
    """
    path = Path(path)
    icc: list[int] = []
    ixc: list[int] = []
    minmax: int | None = None
    switches: dict[str, int] = {}
    equality_count: int | None = None
    equality_name: str | None = None
    equality_line: int | None = None
    for number, line in enumerate(path.read_text().splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("*"):
            continue
        match = _ICC_RE.match(stripped)
        if match:
            icc.append(int(match.group(1)))
            continue
        match = _IXC_RE.match(stripped)
        if match:
            ixc.append(int(match.group(1)))
            continue
        match = _MINMAX_RE.match(stripped)
        if match:
            minmax = int(match.group(1))
            continue
        match = _EQUALITY_COUNT_RE.match(stripped)
        if match:
            equality_name = match.group(1)
            equality_count = int(match.group(2))
            equality_line = number
            switches[match.group(1)] = equality_count
            continue
        match = _INT_SWITCH_RE.match(stripped)
        if match:
            switches[match.group(1)] = int(match.group(2))
    if minmax is None:
        raise InputFileError(
            f"{path} declares no figure of merit (no 'minmax =' line): the "
            f"artifacts that stamp themselves for a figure of merit cannot be "
            f"checked against it"
        )
    return {
        "path": str(path),
        "sha256": sha256_of(path),
        "icc_in_file_order": icc,
        "icc": sorted(icc),
        "n_constraints": len(icc),
        "ixc_in_file_order": ixc,
        "ixc": sorted(ixc),
        "n_iteration_variables": len(ixc),
        "figure_of_merit": minmax,
        "equality_count_declared": equality_count,
        "equality_count_name": equality_name,
        "equality_count_line": equality_line,
        "integer_settings": switches,
    }


def expected_constraint_set(
    path: Path | str, *, lifted: bool
) -> list[int]:
    """The active ``icc`` set a run of this input file will hold.

    The lifted input file carries exactly one constraint the committed one does
    not — the burn-time consistency residual — so the two artifacts differ in
    their stamp by that one entry and in nothing else.
    """
    parsed = parse_input_file(path)
    icc = list(parsed["icc_in_file_order"])
    if lifted:
        icc.append(ICC_BURN_TIME)
    return sorted(icc)


# ==========================================================================
# the derivation: three lines, and the measurement behind the third
# ==========================================================================

#: The registry number the burn time takes when the optimiser owns it.  Numbers
#: are appended, never fitted into a gap (decision D10).
IXC_BURN_TIME = 178

#: The constraint number the burn-time consistency residual takes.
ICC_BURN_TIME = 93

#: Which arm measures the settled burn time, and why it is this one.
#:
#: The rule is "the burn time the incumbent's own loop settles on at the
#: configuration's starting design vector".  The incumbent is PROCESS as
#: shipped, so the measuring run must have **every architecture switch unset** —
#: that is the reference arm, ``AR`` in the evaluation phase.  It is the
#: evaluation phase and not the optimisation phase because the rule asks for the
#: value at the *starting* design vector: one evaluation of the model set at the
#: input file's own point is exactly that, and an optimisation would move the
#: design vector before the loop settled anywhere.
#:
#: The alternative would have been to compose the flat control ``A0`` instead.
#: It is the wrong choice for a reason that matters: ``A0`` stops on the
#: coupling state at τ, and the value the lifted variable must start from is the
#: one the *incumbent's* stopping rule leaves behind, not the one a tighter rule
#: would.  Two arms would give two different starting points, and only one of
#: them makes the lifted arm's entry consistency residual what the previous
#: revision measured.
BASELINE_ARM = "AR"

#: The field the measurement reads back, on the record the evaluation writes.
BURN_TIME_FIELD = "t_plant_pulse_burn"


def derive_text(
    source_text: str, source_name: str, burn_time: float
) -> tuple[str, dict[str, Any]]:
    """The lifted input file's bytes, from the committed one's and one number.

    Exactly three lines change, and **where** the constraint line goes is not
    cosmetic.  PROCESS does not decide which constraints are equalities from the
    constraints themselves: it takes the first ``n_equality_constraints`` entries
    of ``icc`` **in the order the file lists them**.  Appending the burn-time
    constraint at the end of the file would therefore make an *equality* into
    the last *inequality* — a problem in which nothing forces the burn time onto
    its own consistency manifold, which still returns a converged run with an
    objective that looks right.  That happened once, and was found by reading
    the inequality count in a gate table rather than by inspection.  So the line
    is inserted immediately after the last existing equality entry and the count
    is raised in the same edit.

    A pure function of (bytes, name, number): no file is read and none is
    written, so the same three inputs give the same bytes on any machine, which
    is what makes the digest gate meaningful.

    Reproduced from ``arch_surgery/idf_probe/a25_variant_deck.py::
    write_variant_deck`` at ``f1f90c20``.  The comment text is verbatim,
    including its task token, because the previous revision's bytes are what
    this must reproduce.
    """
    lines = source_text.splitlines()

    icc_at = [
        i
        for i, line in enumerate(lines)
        if re.match(r"\s*icc\s*=", line) and not line.lstrip().startswith("*")
    ]
    equality_at = [
        i
        for i, line in enumerate(lines)
        if _EQUALITY_COUNT_RE.match(line) and not line.lstrip().startswith("*")
    ]
    if len(equality_at) != 1:
        raise InputFileError(
            f"{source_name}: expected exactly one equality-count line "
            f"('neqns' or 'n_equality_constraints'), found {len(equality_at)}. "
            f"Which entries of icc are equalities would be a guess, and the "
            f"whole point of this edit is where the new entry lands."
        )
    equality_line = lines[equality_at[0]]
    match = _EQUALITY_COUNT_RE.match(equality_line)
    n_equality = int(match.group(2))
    if n_equality < 1 or n_equality > len(icc_at):
        raise InputFileError(
            f"{source_name}: the file declares {n_equality} equality "
            f"constraint(s) but lists {len(icc_at)} icc entries"
        )

    insert_after = icc_at[n_equality - 1]
    lines[equality_at[0]] = (
        f"{match.group(1)} = {n_equality + 1}  * A25: was {n_equality}; "
        f"constraint 93 appended to the equality block"
    )
    lines.insert(
        insert_after + 1,
        f"icc = {ICC_BURN_TIME}  * A25: burn time consistency (EQUALITY -- "
        f"must sit inside the first neqns icc entries)",
    )

    header = [
        "*",
        "* ---------------------------------------------------------------",
        "* A25 (phase-b-variant): DERIVED deck -- do not edit by hand.",
        f"* Generated from {source_name} by a25_variant_deck.py.",
        "* Exactly three things change and nothing else:",
        f"*   icc = {ICC_BURN_TIME} inserted after icc line {n_equality} "
        f"(the last equality),",
        f"*       and {match.group(1)} raised {n_equality} -> "
        f"{n_equality + 1} in the same edit.",
        f"*   ixc = {IXC_BURN_TIME} appended -- the burn time becomes a "
        f"design variable.",
        "*   t_plant_pulse_burn set to the value the BASELINE's own idempotence",
        "*       loop settles on at this deck's own starting design vector:",
        f"*       {burn_time!r} s (measured, not chosen).",
        "* ---------------------------------------------------------------",
        "*",
    ]
    tail = [
        "*",
        "* --- A25 (phase-b-variant): the burn-time lift ------------------",
        f"t_plant_pulse_burn = {burn_time!r}  * A25: baseline entry value, "
        f"measured",
        f"ixc = {IXC_BURN_TIME}  * A25: t_plant_pulse_burn lifted to the "
        f"design vector",
    ]
    text = "\n".join(header + lines + tail) + "\n"
    edit = {
        "n_icc_lines_source": len(icc_at),
        "equality_count_name": match.group(1),
        "equality_count_source": n_equality,
        "equality_count_derived": n_equality + 1,
        "icc_93_inserted_after_source_line": insert_after + 1,
        "icc_93_position_in_icc_list": n_equality + 1,
        "equality_count_line_source": equality_line.strip(),
        "burn_time": burn_time,
        "burn_time_hex": float(burn_time).hex(),
        "lines_source": len(source_text.splitlines()),
        "lines_derived": len(text.splitlines()),
        "lines_changed": 3,
        "lines_of_header_and_marker_comments": len(header) + 2,
    }
    return text, edit


def changed_lines(source_text: str, derived_text: str) -> list[dict[str, Any]]:
    """The lines that differ between a committed file and a derived one.

    Reported rather than summarised: when the derived file's digest does not
    match the recorded one, the content of the difference is the finding, and a
    count of differing lines is not.
    """
    import difflib  # noqa: PLC0415 - reporting path only

    rows: list[dict[str, Any]] = []
    for line in difflib.unified_diff(
        source_text.splitlines(),
        derived_text.splitlines(),
        fromfile="committed",
        tofile="derived",
        lineterm="",
        n=0,
    ):
        if line.startswith(("---", "+++")):
            continue
        rows.append({"line": line})
    return rows


def burn_time_from_record(record: Mapping[str, Any], *, where: str) -> float:
    """The settled burn time a baseline evaluation left behind.

    Refuses on anything short of a finished evaluation that carries the field.
    The third of the three edited lines is a **measurement**, and a derivation
    that quietly substituted the input file's default for it would produce a
    file that looks right and starts the lifted arm at a design point the
    incumbent never visits — the confound the rule exists to remove.  The
    default is 1000 s and none of the pulsed configurations sets it, while their
    settled values are thousands of seconds, so the substitution would not even
    look wrong.
    """
    status = record.get("status")
    if status != "ok":
        raise InputFileError(
            f"{where}: the baseline evaluation did not finish (status "
            f"{status!r}, taxonomy {record.get('failure_class')!r}), so there "
            f"is no settled burn time to derive from.  Refused: the initial "
            f"value of the lifted variable is measured, and a derivation "
            f"without the measurement is a different file."
        )
    if BURN_TIME_FIELD not in record:
        raise InputFileError(
            f"{where}: the baseline evaluation's record carries no "
            f"{BURN_TIME_FIELD!r}.  Refused rather than defaulted: the input "
            f"file's own default is 1000 s and the settled values are "
            f"thousands of seconds, so a substituted default would produce a "
            f"file that looks right and starts the lifted arm somewhere the "
            f"incumbent never goes."
        )
    return float(record[BURN_TIME_FIELD])


def measure_settled_burn_time(
    config: Config, campaign: Campaign, *, outdir: Path, resume: bool = False
) -> tuple[float, dict[str, Any]]:
    """One evaluation of the model set, and the burn time it settles on.

    The run goes through the pool like every other PROCESS run this package
    starts: a fresh subprocess in its own directory, ``PYTHONPATH`` naming the
    tree under test, the exact tree asserted inside the child.  Its kind is
    ``gate``, never ``campaign``: this run derives an input, it does not measure
    an architecture.
    """
    from ..core import pool as pool_mod  # noqa: PLC0415 - pool imports this module
    from ..core import records as records_mod  # noqa: PLC0415 - symmetry with pool

    job = pool_mod.Job(
        phase="A",
        arm=BASELINE_ARM,
        config=config,
        seed=0,
        outdir=Path(outdir),
        regime="unperturbed",
        run_kind="gate",
    )
    result = pool_mod.run(job, campaign, resume=resume)
    record = records_mod.read(Path(outdir))
    burn_time = burn_time_from_record(
        record, where=f"{config.name} / {BASELINE_ARM}"
    )
    measurement = {
        "arm": BASELINE_ARM,
        "why_this_arm": (
            "the incumbent's own loop: every architecture switch unset, one "
            "evaluation of the model set at the input file's own design vector"
        ),
        "outdir": str(outdir),
        "status": record.get("status"),
        "resumed": result.get("resumed", False),
        "burn_time": burn_time,
        "burn_time_hex": float(burn_time).hex(),
        "burn_time_recorded_hex": record.get(f"{BURN_TIME_FIELD}_hex"),
        "n_model_calls_sweeps": record.get("n_model_calls_sweeps"),
        "architecture_environment": record.get("env_architecture")
        or record.get("resolved_switches_environment"),
        "wall_s": result.get("wall_s"),
    }
    return burn_time, measurement


def derive_one(
    config: Config,
    campaign: Campaign,
    *,
    runs_dir: Path,
    resume: bool = False,
) -> dict[str, Any]:
    """Derive one configuration's lifted input file, and gate it on its digest.

    A steady-state configuration is **not applicable**, and says so: it has no
    burn-time coupling, no arm on it reads a lifted input file, and there is no
    file to derive.  That is recorded as a stage outcome rather than as a
    skipped row, because "not applicable" and "not done" are different results.
    """
    if not config.pulsed:
        return {
            "configuration": config.name,
            "applicable": False,
            "verdict": "not applicable, steady state",
            "why": (
                "a steady-state configuration has no burn-time coupling: the "
                "arm in which the optimiser owns the burn time composes onto "
                "its predecessor there, no arm reads a lifted input file, and "
                "none is derived"
            ),
        }

    expected = LIFTED_INPUT_SHA256.get(config.name)
    if expected is None:
        raise InputFileError(
            f"no digest is recorded for {config.name}'s lifted input file, so "
            f"a derived one could not be gated.  The derivation is gated on "
            f"the bytes, never merely reviewed."
        )

    burn_time, measurement = measure_settled_burn_time(
        config,
        campaign,
        outdir=Path(runs_dir) / config.name / "baseline_evaluation",
        resume=resume,
    )
    source = Path(config.input_path)
    source_text = source.read_text()
    text, edit = derive_text(source_text, source.name, burn_time)

    destination = lifted_path(config, campaign)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text)
    found = sha256_of(destination)
    matched = found == expected

    derived_parsed = parse_input_file(destination)
    source_parsed = parse_input_file(source)

    row: dict[str, Any] = {
        "configuration": config.name,
        "applicable": True,
        "committed_input_file": str(source),
        "committed_sha256": source_parsed["sha256"],
        "derived_input_file": str(destination),
        "derived_sha256": found,
        "recorded_sha256": expected,
        "matched_recorded_digest": matched,
        "verdict": "PASS" if matched else "FAIL",
        "measurement": measurement,
        "edit": edit,
        "declared_by_the_file": {
            "committed": {
                "n_iteration_variables": source_parsed["n_iteration_variables"],
                "n_constraints": source_parsed["n_constraints"],
                "equality_count": source_parsed["equality_count_declared"],
                "figure_of_merit": source_parsed["figure_of_merit"],
            },
            "derived": {
                "n_iteration_variables": derived_parsed["n_iteration_variables"],
                "n_constraints": derived_parsed["n_constraints"],
                "equality_count": derived_parsed["equality_count_declared"],
                "figure_of_merit": derived_parsed["figure_of_merit"],
            },
        },
        "burn_time_variable_present": IXC_BURN_TIME in derived_parsed["ixc"],
        "burn_time_constraint_position_in_icc": (
            derived_parsed["icc_in_file_order"].index(ICC_BURN_TIME) + 1
            if ICC_BURN_TIME in derived_parsed["icc_in_file_order"]
            else None
        ),
        "burn_time_constraint_is_an_equality": (
            ICC_BURN_TIME in derived_parsed["icc_in_file_order"]
            and derived_parsed["icc_in_file_order"].index(ICC_BURN_TIME)
            < (derived_parsed["equality_count_declared"] or 0)
        ),
    }
    if not matched:
        row["difference"] = {
            "what": (
                "the derived file's bytes are not the ones the experiment "
                "declares.  This is a finding, not something to absorb: "
                "neither file is edited to make the other pass"
            ),
            "changed_lines_against_the_committed_input_file": changed_lines(
                source_text, text
            ),
            "measured_burn_time": burn_time,
            "measured_burn_time_hex": float(burn_time).hex(),
        }
    return row


# ==========================================================================
# the stage, and its teeth
# ==========================================================================

#: Where this stage's own records go.  Untracked, like every run artifact.
RUNS_SUBPATH = "input_files"


def stage_derive(
    campaign: Campaign,
    *,
    configurations: Sequence[str] | None = None,
    resume: bool = False,
) -> tuple[int, dict[str, Any]]:
    """Derive every pulsed configuration's lifted input file and gate it.

    Returns ``(exit code, record)``.  A digest that does not match is reported
    with the derived file's own differing lines and the stage **fails**; nothing
    is retried and neither file is edited to make the other pass.
    """
    from .artifacts import StageCheck  # noqa: PLC0415 - see module note

    check = StageCheck(
        name="input files",
        binds=(
            "the derivation of each pulsed configuration's lifted input file "
            "from its committed one"
        ),
        population=(
            f"{len(campaign.configurations)} configuration(s) "
            f"({', '.join(campaign.population)}); the digest gate applies to "
            f"the {len(campaign.pulsed)} pulsed one(s)"
        ),
    )
    names = list(configurations) if configurations else list(campaign.population)
    runs_dir = Path(campaign.runs_dir) / RUNS_SUBPATH
    rows: list[dict[str, Any]] = []
    for name in names:
        config = campaign.configuration(name)
        try:
            row = derive_one(config, campaign, runs_dir=runs_dir, resume=resume)
        except InputFileError as exc:
            check.fail(f"{name}: REFUSED — {exc}")
            rows.append(
                {"configuration": name, "verdict": "REFUSED", "error": str(exc)}
            )
            continue
        rows.append(row)
        if not row.get("applicable"):
            check.note(f"{name}: {row['verdict']} — {row['why']}")
            continue
        check.n_compared += 1
        if row["matched_recorded_digest"]:
            check.note(
                f"{name}: derived sha256 {row['derived_sha256'][:12]}… equals "
                f"the recorded digest; burn time "
                f"{row['measurement']['burn_time']!r} s "
                f"({row['measurement']['burn_time_hex']}) measured by one "
                f"{BASELINE_ARM} evaluation; constraint "
                f"{ICC_BURN_TIME} at position "
                f"{row['burn_time_constraint_position_in_icc']} of the icc "
                f"list, inside the equality block; iteration variable "
                f"{IXC_BURN_TIME} present"
            )
        else:
            check.fail(
                f"{name}: the derived file is not the declared one — sha256 "
                f"{row['derived_sha256']} against {row['recorded_sha256']} "
                f"recorded.  Reported, not absorbed; see the record's "
                f"'difference' block for the differing lines."
            )
    return (0 if check.passed else 3), {
        **check.as_record(),
        "configurations": rows,
        "constants": {
            "iteration_variable": IXC_BURN_TIME,
            "constraint": ICC_BURN_TIME,
            "measuring_arm": BASELINE_ARM,
        },
        "recorded_digests": dict(LIFTED_INPUT_SHA256),
        "digest_provenance": LIFTED_INPUT_PROVENANCE,
    }


def stage_teeth(campaign: Campaign) -> tuple[int, dict[str, Any]]:
    """The four ways this derivation is made to fail.  No PROCESS run.

    A gate whose failure mode has never been exercised is an assertion, not a
    measurement (orchestration protocol §12).
    """
    import tempfile  # noqa: PLC0415 - teeth only

    from .artifacts import StageCheck  # noqa: PLC0415 - see module note

    check = StageCheck(
        name="input files — teeth",
        binds="the derivation's own ability to fail",
        population="4 deliberate breaks",
    )
    pulsed = [c for c in campaign.configurations if c.pulsed]
    if not pulsed:
        check.fail(
            "no pulsed configuration in the population: the teeth would run "
            "over nothing, and a check with an empty population is how a zero "
            "gets published over nothing"
        )
        return 3, check.as_record()
    config = pulsed[0]
    source_text = Path(config.input_path).read_text()
    burn_time = 2568.1324076519313
    text, _ = derive_text(source_text, Path(config.input_path).name, burn_time)

    with tempfile.TemporaryDirectory() as tmp:
        # 1. one byte changed in a throwaway derived file.
        path = Path(tmp) / "one_byte.IN.DAT"
        path.write_text(text)
        good = sha256_of(path)
        raw = bytearray(path.read_bytes())
        raw[len(raw) // 2] = raw[len(raw) // 2] ^ 0x01
        path.write_bytes(bytes(raw))
        check.tooth(
            "one byte changed in a derived file",
            sha256_of(path) != good,
            f"one byte of a throwaway copy of {config.name}'s derived input "
            f"file flipped; the digest must change",
        )

    # 2. a derivation with no baseline evaluation behind it.
    for label, record in (
        ("a baseline evaluation that crashed", {"status": "crashed"}),
        ("a record carrying no settled burn time", {"status": "ok"}),
    ):
        try:
            burn_time_from_record(record, where="tooth")
            caught = False
        except InputFileError:
            caught = True
        check.tooth(
            f"no measurement behind the third line: {label}",
            caught,
            "the initial value of the lifted variable is measured; a "
            "derivation without the measurement must refuse rather than fall "
            "back on the input file's 1000 s default",
        )

    # 3. the constraint appended at the end instead of inside the equality
    #    block — the mistake that once produced a converged run of the wrong
    #    problem.  The digest must reject it.
    end_appended = "\n".join(
        source_text.splitlines() + [f"icc = {ICC_BURN_TIME}"]
    ) + "\n"
    check.tooth(
        "the burn-time constraint appended at the end of the file",
        hashlib.sha256(end_appended.encode()).hexdigest()
        != LIFTED_INPUT_SHA256[config.name],
        "appending the constraint outside the equality block makes an "
        "equality into the last inequality; the digest must reject that file",
    )
    return (0 if check.passed else 3), check.as_record()
