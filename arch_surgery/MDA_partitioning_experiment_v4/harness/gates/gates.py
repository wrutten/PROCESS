"""The gates with no module of their own, and what the gate modules share.

Here: gate ``G0'`` (the physics stays frozen in the copy) with the copy's two
sibling gates ``copy_identity`` and ``edit_behaviour``, all three loading their
one implementation from ``PROCESS/copy_gates.py`` by path; the shared cold-flat
entry references every warm gate is anchored on, and :func:`_with_capture`; gate
GR wrapped into the framework; the harness's own checks, promoted; and the
``self_containment`` measurement.

The gates that outgrew this file have their own modules beside it --
``gate_neutrality`` (G1), ``gate_output_path`` (G9), ``gate_predicate_mode``
(G8), ``exclusion_review`` -- and the registry that collects every gate and
stage is ``harness/gates/registry.py``.  The framework itself
(:class:`Gate`, :class:`Tooth`, :class:`Check`, :class:`Measurement`) lives in
``harness/core/framework.py``; the aliases below are kept because the plan
names ``gates.Gate`` and ``gates.Tooth`` and a reader who looks them up should
find them.

Written by task **A56 (driver-renames)** as the whole gate module; split along
its own section markers by the code-move task of the simplification survey.
The module's own command line is ``python -m harness.gates.registry``.
"""

from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path
from typing import Any, Mapping

_EXPERIMENT_DIR = Path(__file__).resolve().parents[2]
if str(_EXPERIMENT_DIR) not in sys.path:
    sys.path.insert(0, str(_EXPERIMENT_DIR))

from harness.core import framework  # noqa: E402
from harness.experiment import input_files as input_files_mod  # noqa: E402
from harness.core import pool as pool_mod  # noqa: E402
from harness.core import records as records_mod  # noqa: E402
from harness.experiment import switches as switches_mod  # noqa: E402
from harness.core.config import Campaign  # noqa: E402

#: Where a gate's verdict goes, under the campaign's runs directory.  Bulk run
#: artifacts are untracked by design; the verdict is small and its numbers go
#: into the report.
GATES_SUBPATH = framework.GATES_SUBPATH

#: The framework lives in ``harness/core/framework.py`` so that the self-check and
#: the artifact stages can import ``Check`` without importing this module -- the
#: promotion task **A52 (harness-gates)** moved the three shapes there and left
#: these names here, because the plan names ``gates.Gate`` and ``gates.Tooth``
#: and a reader who looks them up should find them.
Gate = framework.Gate
Tooth = framework.Tooth
Check = framework.Check
Measurement = framework.Measurement
GateError = framework.GateError
_git_head = framework.git_head


# --------------------------------------------------------------------------
# G0' -- the physics stays frozen in the copy
# --------------------------------------------------------------------------
#
# The criterion has exactly one implementation, in PROCESS/copy_gates.py, and it
# is loaded here **by path** rather than restated.  Two implementations of one
# criterion is how they drift, and a gate that drifts from the thing it gates is
# worse than no gate.


def _copy_gates(campaign: Campaign):
    """``PROCESS/copy_gates.py`` as a module, loaded by path."""
    path = Path(campaign.tree) / "copy_gates.py"
    if not path.exists():
        raise GateError(
            f"{path} is not present; G0' has no implementation to run and must "
            f"refuse rather than report a physics freeze it never checked."
        )
    spec = importlib.util.spec_from_file_location("_a56_copy_gates", path)
    if spec is None or spec.loader is None:  # pragma: no cover - import plumbing
        raise GateError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def g0prime_body(campaign: Campaign) -> dict[str, Any]:
    gates = _copy_gates(campaign)
    prov = gates.load_provenance()
    res = gates.check_frozen_physics(prov, Path(campaign.tree))
    return {
        "passed": res.passed,
        "population": (
            f"{res.compared} files under PROCESS/process/models/ compared "
            f"byte for byte against "
            f"{prov['frozen_physics']['base_commit']} (git cat-file, never a "
            f"working tree), plus the file set"
        ),
        "n_compared": res.compared,
        "n_identical": res.identical,
        "n_mismatched": res.compared - res.identical,
        "base_commit": prov["frozen_physics"]["base_commit_full"],
        "approved_differences": {
            a["path"]: a["decision"] for a in prov["frozen_physics"]["approved_differences"]
        },
        "unapproved_differences": res.detail["unapproved_differences"],
        "model_files_differing_from_base": res.detail["model_files_differing_from_base"],
        "failures": res.failures,
        "implementation": str(Path(campaign.tree) / "copy_gates.py"),
    }


def _g0prime_teeth(campaign: Campaign) -> tuple[Tooth, ...]:
    """The four perturbations ``copy_gates.run_teeth`` already builds.

    They are run **once** and shared: each perturbation stages a throwaway copy
    of the whole package, so running the set four times over would copy 22 MB
    to say the same four things.
    """
    cache: dict[str, dict] = {}

    def one(kind: str):
        def check() -> tuple[bool, str]:
            if not cache:
                gates = _copy_gates(campaign)
                prov = gates.load_provenance()
                for record in gates.run_teeth(
                    prov, Path(campaign.tree), "frozen-physics"
                ):
                    cache[record["tooth"]] = record
            record = cache.get(kind)
            if record is None:
                return False, f"copy_gates.run_teeth produced no {kind!r} tooth"
            return (
                record["tooth_result"] == "TRIPPED",
                f"{record['perturbation']} -> gate {record['gate_verdict']}"
                f" ({record['first_failure']})",
            )

        return check

    return (
        Tooth(
            "one_byte_changed",
            "one byte of one model file changed in a throwaway copy of the tree",
            "FAIL",
            one("one_byte_changed"),
        ),
        Tooth(
            "file_removed",
            "one model file removed from a throwaway copy of the tree",
            "FAIL",
            one("file_removed"),
        ),
        Tooth(
            "file_added",
            "one model file added to a throwaway copy of the tree",
            "FAIL",
            one("file_added"),
        ),
        Tooth(
            "approved_file_changed_further",
            "the one model file with an approved edit changed again",
            "FAIL",
            one("approved_file_changed_further"),
        ),
    )



def g0prime_gate(campaign: Campaign) -> Gate:
    """G0 / G0', as the registry holds it.  The literal is the one ``_plan_gates`` held."""
    return Gate(
        name="g0prime",
        plan_name="G0 / G0'",
        binds="every V4 commit, every arm, both phases",
        what_it_proves=(
            "the physics and engineering models in the experiment's own "
            "copy of PROCESS are byte-identical to the frozen base commit, "
            "bar the one structural edit the user approved"
        ),
        body=lambda *, resume=False: g0prime_body(campaign),
        teeth=_g0prime_teeth(campaign),
    )


# --------------------------------------------------------------------------
# the copy's two other gates -- copy identity, and the one edit's behaviour
# --------------------------------------------------------------------------
#
# ``PROCESS/copy_gates.py`` implements three criteria about the copy.  G0' has
# been registered here since A56; the other two were run by that script's own
# command line only, which wrote verdicts under ``runs/gates/`` with no commit
# stamp and no place in the registry, the ordering or the gate table (A63 §5
# d3; survey item A9).  They are registered here the way G0' is -- the
# criterion loaded by path, never restated -- so that one gate runner covers
# the copy and ``--gate all`` reaches them.  ``copy_gates.py all`` remains a
# thin second entry to the same functions and writes no record of its own.


def copy_identity_body(campaign: Campaign) -> dict[str, Any]:
    gates = _copy_gates(campaign)
    prov = gates.load_provenance()
    res = gates.check_copy_identity(prov, Path(campaign.tree))
    detail = res.detail
    return {
        "passed": res.passed,
        "population": (
            f"{res.compared} files under PROCESS/process/ compared byte for "
            f"byte against the source commit {prov['source']['commit']} (git "
            f"cat-file, never a working tree), plus the file set; "
            f"{len(detail['permitted_edit_files'])} permitted-edit file(s) "
            f"compared on their recorded post-edit digest and hunks"
        ),
        "n_compared": res.compared,
        "n_identical": res.identical,
        "n_mismatched": res.compared - res.identical,
        "source_commit": detail["source_commit_full"],
        "files_at_source_commit": detail["files_at_source_commit"],
        "files_in_copy": detail["files_in_copy"],
        "files_missing_from_copy": detail["files_missing_from_copy"],
        "files_added_to_copy": detail["files_added_to_copy"],
        "permitted_edit_files": detail["permitted_edit_files"],
        "unexplained_differences": detail["unexplained_differences"],
        "failures": res.failures,
        "implementation": str(Path(campaign.tree) / "copy_gates.py"),
        "note": (
            "n_mismatched counts the files that differ from the source commit; "
            "the gate passes when every one of them is a recorded permitted "
            "edit with the recorded digest and hunks, and fails on any other"
        ),
    }


def _copy_identity_teeth(campaign: Campaign) -> tuple[Tooth, ...]:
    """The four perturbations ``copy_gates.run_teeth`` builds for copy-identity.

    Run once and shared, as G0''s are: each stages a throwaway copy of the
    whole package.
    """
    cache: dict[str, dict] = {}

    def one(kind: str):
        def check() -> tuple[bool, str]:
            if not cache:
                gates = _copy_gates(campaign)
                prov = gates.load_provenance()
                for record in gates.run_teeth(prov, Path(campaign.tree), "copy-identity"):
                    cache[record["tooth"]] = record
            record = cache.get(kind)
            if record is None:
                return False, f"copy_gates.run_teeth produced no {kind!r} tooth"
            return (
                record["tooth_result"] == "TRIPPED",
                f"{record['perturbation']} -> gate {record['gate_verdict']}"
                f" ({record['first_failure']})",
            )

        return check

    return (
        Tooth(
            "one_byte_changed",
            "one byte of one copied driver file changed in a throwaway copy of the tree",
            "FAIL",
            one("one_byte_changed"),
        ),
        Tooth(
            "file_removed",
            "one copied file removed from a throwaway copy of the tree",
            "FAIL",
            one("file_removed"),
        ),
        Tooth(
            "file_added",
            "one file added to a throwaway copy of the tree",
            "FAIL",
            one("file_added"),
        ),
        Tooth(
            "permitted_file_changed_elsewhere",
            "a file that is allowed to differ, changed somewhere other than its recorded hunks",
            "FAIL",
            one("permitted_file_changed_elsewhere"),
        ),
    )


def copy_identity_gate(campaign: Campaign) -> Gate:
    return Gate(
        name="copy_identity",
        binds="every V4 commit that touches the experiment's copy of PROCESS",
        what_it_proves=(
            "every file under the copy's process/ is byte-identical to the "
            "source commit named in PROVENANCE.json, except the recorded "
            "permitted edits -- whose post-edit digest and exact hunks match "
            "-- and the file set is the source commit's"
        ),
        body=lambda *, resume=False: copy_identity_body(campaign),
        teeth=_copy_identity_teeth(campaign),
    )


def edit_behaviour_body(campaign: Campaign) -> dict[str, Any]:
    gates = _copy_gates(campaign)
    prov = gates.load_provenance()
    passed, result = gates.check_edit_behaviour(prov, root=Path(campaign.tree))
    return {
        "passed": passed,
        "population": (
            "three arms of one probe, no PROCESS run: the copy with the "
            "per-run write-set artifact absent, the source commit "
            f"{prov['source']['commit']} (git archive) with it absent, and the "
            "copy with it present"
        ),
        "n_compared": 3,
        "n_mismatched": len(result.get("failures") or []),
        "copy_artifact_absent": result.get("copy_artifact_absent"),
        "source_commit_artifact_absent": result.get("source_commit_artifact_absent"),
        "copy_artifact_present": result.get("tooth_copy_artifact_present"),
        "artifact_used": result.get("artifact_used"),
        "failures": result.get("failures") or [],
        "implementation": str(Path(campaign.tree) / "copy_gates.py"),
    }


def _edit_behaviour_teeth(campaign: Campaign) -> tuple[Tooth, ...]:
    def doctored() -> tuple[bool, str]:
        gates = _copy_gates(campaign)
        prov = gates.load_provenance()
        record = gates.run_edit_behaviour_tooth(prov, Path(campaign.tree))
        return (
            record["tooth_result"] == "TRIPPED",
            f"{record['perturbation']} -> gate {record['gate_verdict']} "
            f"(the doctored copy raised {record.get('copy_artifact_absent_raised')}; "
            f"{record['first_failure']})",
        )

    return (
        Tooth(
            "permitted_edit_doctored",
            "the permitted edit's existence check made unreachable in a "
            "throwaway copy of the tree, so the copy behaves as the source "
            "commit did",
            "FAIL",
            doctored,
        ),
    )


def edit_behaviour_gate(campaign: Campaign) -> Gate:
    return Gate(
        name="edit_behaviour",
        binds="the one permitted edit in the copy that is not a rename or a comment",
        what_it_proves=(
            "the existence check A48 added on the per-run deferral path "
            "refuses by name where the source commit raised a bare "
            "FileNotFoundError, and refuses nothing when the artifact is "
            "present -- a guard on absence, not a new refusal on the path "
            "every run takes"
        ),
        body=lambda *, resume=False: edit_behaviour_body(campaign),
        teeth=_edit_behaviour_teeth(campaign),
    )


def copy_gates(campaign: Campaign) -> dict[str, Gate]:
    """The copy's two gates beside G0', for the registry."""
    return {
        "copy_identity": copy_identity_gate(campaign),
        "edit_behaviour": edit_behaviour_gate(campaign),
    }


# --------------------------------------------------------------------------
# the entry reference every warm gate is anchored on
# --------------------------------------------------------------------------
#
# Three gates -- G2 (the prime's fixed-point map), G4 (the audit restriction)
# and G6 (entry and warm equivalence) -- all start from the same thing: one
# undisplaced evaluation of the flat control per configuration, entered cold
# from the input file's own design point.  Its exit state is the fixed point
# every warm run is entered from and its converged burn time is what a constant
# owns.  It is made once, here, and shared, because three gates making their own
# would be three fixed points that have to be argued to be the same one.
#
# The directory shape is `reproduction.phase_a_reference_directory`'s, imported
# rather than restated, so the reproduction gate's references and these are the
# same construction and can be read side by side.


def entry_reference_root(campaign: Campaign) -> Path:
    return Path(campaign.runs_dir) / GATES_SUBPATH / "entry_references"


#: Which run roots this process has already made its shared cold-flat
#: references under.  Three gates are anchored on them, and without this the
#: second and third gate of one ``--gate all`` would re-make what the first just
#: made — so the references are made **once per invocation** and shared, which
#: is what they were for.  The memo is per process: a new invocation makes them
#: again unless ``--resume`` says otherwise.
_ENTRY_REFERENCES_MADE: set[str] = set()


def entry_references(
    campaign: Campaign, *, resume: bool = False
) -> dict[str, dict[str, Any]]:
    """One cold flat evaluation per configuration, and what it left behind.

    Returns, per configuration: the exit snapshot's path, the converged burn
    time as a hex literal, the run's own exit-audit maximum, and the cold-start
    cost.  A configuration whose reference did not finish **refuses** -- every
    warm run is entered from its exit state, so there is nothing to enter from,
    and that is a result rather than a reason to enter from somewhere else.
    """
    from . import reproduction as reproduction_mod

    root = entry_reference_root(campaign)
    jobs = [
        pool_mod.Job(
            phase="A",
            arm="A0",
            config=config,
            seed=0,
            outdir=reproduction_mod.phase_a_reference_directory(root, config.name),
            regime="unperturbed",
            delta=None,
            run_kind="gate",
        )
        for config in campaign.configurations
    ]
    already = str(root) in _ENTRY_REFERENCES_MADE
    pool_mod.run_all(jobs, campaign, resume=resume or already)
    _ENTRY_REFERENCES_MADE.add(str(root))
    references: dict[str, dict[str, Any]] = {}
    for job in jobs:
        record = records_mod.read(job.outdir)
        if record.get("status") != "ok":
            raise GateError(
                f"the entry reference for {job.config.name} did not finish "
                f"(status {record.get('status')!r}, taxonomy row "
                f"{record.get('failure_class')!r}).  Every warm run of every "
                f"gate is entered from its exit state, so the gates that need "
                f"it stop here rather than entering from somewhere else."
            )
        references[job.config.name] = {
            "outdir": str(job.outdir),
            "snapshot": str(Path(job.outdir) / "y_exit.json"),
            "t_plant_pulse_burn_hex": record.get("t_plant_pulse_burn_hex"),
            "audit_residual_max_hex": (record.get("exit_audit") or {}).get(
                "residual_max_hex"
            ),
            "cold_start_node_calls": record.get("node_calls_single_eval"),
            "cold_start_sweeps": record.get("n_model_calls_sweeps"),
        }
    return references


def _with_capture(
    capture, body, campaign: Campaign, *, resume: bool = False
) -> dict[str, Any]:
    """Make the gate's own runs, then compare them.

    Two gates were built as two shell steps — capture, then compare — because
    the driver task that wrote them was straddling a commit.  Nothing about
    **these** two needs two commits: both sides are the same code at the same
    commit, so the gate makes its runs itself and the button really is one
    button (protocol §15: no stage exists only as a shell invocation).  The
    capture resumes, so a complete record of the same job is kept rather than
    re-made; that is not a retry, and ``pool.run`` checks the job matches
    before it keeps anything.

    Gate G1 is deliberately **not** wrapped this way: its two sides are at
    different commits by construction, and a gate that made its own "before"
    would be comparing the tree with itself.
    """
    manifest = capture(campaign, resume=resume)
    outcome = body(campaign)
    outcome["capture"] = {
        "n_runs": manifest.get("n_runs"),
        "manifest": manifest.get("manifest"),
        "tree_git_head": manifest.get("tree_git_head"),
    }
    return outcome


# --------------------------------------------------------------------------
# gate GR, wrapped into the framework
# --------------------------------------------------------------------------
#
# GR is implemented in ``harness/gates/reproduction.py`` and was reachable only from
# ``experiment_runner.py --gate reproduction``.  It is registered here so that
# ``registry`` really is *every* gate, and so that ``--gate all`` runs it with
# the rest.  The criterion is not restated: the body calls the same stage, and
# the teeth read the same seven results out of its verdict.

#: GR's own deliberate breaks, by the names ``reproduction.teeth`` records them
#: under.  Declared here rather than counted, so that a tooth the gate stops
#: running is a tooth that DID NOT TRIP rather than one fewer tooth.
REPRODUCTION_TEETH: tuple[str, ...] = (
    "count",
    "hex",
    # The one tooth here that must **not** end in a refusal: a reference value
    # the gate no longer compares, doctored, has to be reported as excluded by
    # name — neither as a mismatch (the exclusion would not be in force) nor as
    # a match (a doctored value would have passed).
    "excluded field",
    "missing reference",
    "missing key",
    "bad name map",
    "composition",
    "attempt summation",
)

_REPRODUCTION_HELD: dict[str, Any] = {}

#: Where GR's runs and verdict go when the gate is run from the registry.  It
#: is settable so that ``--outdir`` redirects the gate, which it did not before
#: (task A57 (driver-output-path) recorded the quirk: ``--gate reproduction``
#: wrote to the campaign's records directory whatever ``--outdir`` said).
REPRODUCTION_ROOT: dict[str, Any] = {"root": None}

def _reproduction_body(campaign: Campaign, *, resume: bool = False) -> dict[str, Any]:
    from . import reproduction as reproduction_mod

    code, verdict = reproduction_mod.stage(
        campaign=campaign,
        root=REPRODUCTION_ROOT["root"],
        resume=resume,
    )
    _REPRODUCTION_HELD["verdict"] = verdict
    comparison = verdict.get("comparison") or {}
    # The gate writes its verdict to the same path the stage writes its own, so
    # the stage's whole verdict is carried inside this one rather than
    # overwritten: a reader who opens the file must find everything, not the
    # framework's summary where the detail used to be.
    return {
        "passed": code == 0,
        "criterion": (
            "twenty runs against the previous revision's committed numbers, "
            "every compared value exact — counts and hex floats, no tolerance"
        ),
        "population": comparison.get("population")
        or f"{verdict.get('n_planned')} reference runs",
        "n_compared": comparison.get("n_values_compared"),
        "n_mismatched": comparison.get("n_values_mismatched"),
        "n_runs": comparison.get("n_runs"),
        "n_runs_reproduced": comparison.get("n_runs_reproduced"),
        "refused": verdict.get("refused"),
        "coverage_boundary": verdict.get("coverage_boundary"),
        "substitutes": {
            name: block.get("passed")
            for name, block in (verdict.get("substitutes") or {}).items()
        },
        "record_contract_passed": (verdict.get("record_contract") or {}).get("passed"),
        "reproduction": verdict,
    }


def _reproduction_teeth() -> tuple[Tooth, ...]:
    def read(name: str):
        def look() -> tuple[bool, str]:
            verdict = _REPRODUCTION_HELD.get("verdict")
            if verdict is None:
                return False, "the gate did not run, so its teeth never ran"
            for entry in (verdict.get("teeth") or {}).get("teeth", []):
                if entry["tooth"] == name:
                    return bool(entry["caught"]), str(entry["what"])
            return False, (
                f"gate GR ran no tooth named {name!r}; a declared tooth the "
                f"gate no longer exercises is a tooth that did not trip"
            )

        return look

    return tuple(
        Tooth(
            name=name,
            what="gate GR's own deliberate break, by name",
            must=(
                "FAIL, REFUSE or RAISE — never skip; the 'excluded field' "
                "tooth instead requires the doctored value to be reported as "
                "excluded by name"
            ),
            check=read(name),
        )
        for name in REPRODUCTION_TEETH
    )




def reproduction_gate(campaign: Campaign) -> Gate:
    """GR, as the registry holds it.  The literal is the one ``_plan_gates`` held."""
    return Gate(
        name="reproduction",
        plan_name="GR",
        needs_runs=True,
        binds=(
            "the harness rewrite and the experiment's copy of PROCESS, "
            "once, at the copy commit before any driver change"
        ),
        what_it_proves=(
            "the rewritten harness reproduces the previous revision's "
            "twenty runs bit for bit on every count field and hex float, "
            "so the rewrite changed the measurement in no respect this "
            "experiment compares on"
        ),
        body=lambda *, resume=False: _reproduction_body(campaign, resume=resume),
        teeth=_reproduction_teeth(),
    )


# --------------------------------------------------------------------------
# the harness's own checks, promoted
# --------------------------------------------------------------------------
#
# Six self-checks and four artifact stages existed before this framework did,
# each already carrying what a gate carries: what it binds, a population, a
# denominator, a mismatch count and its own teeth.  They are promoted rather
# than rewritten -- ``framework.gate_from_check`` runs the *same function* and
# adds the verdict record, the registry entry and a declared tooth list.  The
# numbers a promoted gate reports are the numbers the check reported; that is
# the point of promoting instead of restating.


def _selfcheck_gates(campaign: Campaign) -> dict[str, Gate]:
    """The six self-checks, each with the teeth it must run.

    The retired-name family is **derived** from the switch registry rather than
    listed, because the check generates one tooth per retired name from that
    same registry: a hand-copied list would drift the moment a name is retired.
    """
    from . import selfcheck as selfcheck_mod
    from ..experiment import switches as switches_mod

    retired = tuple(
        f"the retired name {name} present in the environment"
        for name in sorted(switches_mod.retired_names())
    )
    declared: dict[str, tuple[str, ...]] = {
        "composition": (
            "a role both revisions can express treated as a new capability",
            "wrong switch value in one arm",
            "one switch dropped from an arm",
            "the wrong per-run artifact handed to an arm",
            "the fold read as a difference",
            "a schedule policy the fold does not cover",
            "a skipped arm asked to compose",
        ),
        "rungs": (
            "a wrong expected difference in the rung table",
            "a wrong cell in the transcribed matrix",
            "an arm compared with itself",
        ),
        "capability": (
            "an arm asks for a switch the tree does not implement",
            "the driver resolves a switch differently from what was asked",
            *retired,
            "the driver's own refusal of a retired name",
            "the working directory holds a package that shadows the tree",
        ),
        "provenance": (
            "a tracked file modified",
            "an untracked file beside the runner",
            "a campaign pointed at a tree that is not the experiment's copy",
            "the tree asserted by a prefix instead of exactly",
        ),
        "data": (
            "one byte changed in a copied file",
            "a copied file missing",
            "a file added that the record does not name",
            "a changed file whose recorded sha256 was updated to match",
            "an unrecorded edit to the predicate module",
            "an edited predicate module whose recorded sha256 was updated to match",
        ),
        "stage_provenance": (
            "a verdict re-made at a later commit after the stage record was "
            "written",
            "a verdict record written after the stage record",
            "a verdict record the stage read and that is gone",
            "a stage record that does not say what it read",
            "a scratch census record with no tree stamp",
        ),
        "run_path": (
            "a declared field removed",
            "an exit audit carrying one convergence ruler and not both",
            "a record that does not say what kind of run made it",
            "per-attempt costs that do not sum to the run total",
            "per-attempt costs stamped at some attempts and not others",
            "the design-vector stream keyed on position instead of number",
            "the two streams sharing a namespace",
            "a run against a tree that is not the experiment's copy",
            "a run asking for a switch the tree does not implement",
            "an allowance naming a switch the tree does implement",
            "a campaign run carrying the reproduction gate's override",
            "a reproduction override that changes nothing",
            "a campaign run asking for the after_run audit position",
            "an undeclared caller asking for the after_run audit position",
        ),
    }
    # None of the six starts a PROCESS run through the pool -- the capability
    # check starts import-only probe children -- so ``resume`` reaches them and
    # has nothing to do, which is why each signature swallows it.
    bodies: dict[str, Any] = {
        "composition": lambda *, resume=False: selfcheck_mod.check_composition(campaign),
        "rungs": lambda *, resume=False: selfcheck_mod.check_rungs(),
        "capability": lambda *, resume=False: selfcheck_mod.check_capability(campaign),
        "provenance": lambda *, resume=False: selfcheck_mod.check_provenance(campaign),
        "data": lambda *, resume=False: selfcheck_mod.check_data(campaign),
        "run_path": lambda *, resume=False: selfcheck_mod.check_run_path(campaign),
        "stage_provenance": lambda *, resume=False: (
            selfcheck_mod.check_stage_provenance(campaign)
        ),
    }
    proves = {
        "composition": (
            "every arm composes on every configuration, a skipped arm refuses "
            "by name, and the arms the previous revision also ran ask the "
            "driver for the same thing"
        ),
        "rungs": (
            "the plan's switch matrix and rung table regenerate cell for cell "
            "from the arm records"
        ),
        "capability": (
            "the tree resolves every switch each arm asks for, exactly as "
            "asked, and refuses a retired name rather than ignoring it"
        ),
        "provenance": (
            "a modified tracked file and an untracked file are recorded "
            "separately, and only the first marks the tree dirty"
        ),
        "data": (
            "every committed file the experiment reads is byte-identical to "
            "its source at the recorded commit, and the predicate module "
            "differs from its source by exactly the recorded hunks"
        ),
        "run_path": (
            "a finished record carries every field it declares, both rulers "
            "included; the two displacement streams key on what they say they "
            "key on; and a run against the wrong tree is refused, not made"
        ),
        "stage_provenance": (
            "a stage record names the records it read, and the renderer of "
            "the plan's results section refuses one whose verdicts have since "
            "been re-made, removed or added to — so a section can no longer "
            "reproduce an older verdict without saying so; and every census "
            "record on disk is placed by its own commit or named as one a "
            "stamp survey cannot place"
        ),
    }
    return {
        name: framework.gate_from_check(
            name=name,
            binds="the harness itself, before any PROCESS run",
            what_it_proves=proves[name],
            run=bodies[name],
            teeth=declared[name],
            needs_runs=False,
        )
        for name in declared
    }


#: The four artifact stages, each promoted with **its own** teeth.  The stage
#: and its teeth are two functions in the artifact modules, so the promotion
#: runs both: the criterion is the stage, unchanged, and the teeth are the
#: stage's own deliberate breaks, declared by name here.
ARTIFACT_GATE_TEETH: dict[str, tuple[str, ...]] = {
    "artifacts_check": (
        "a corrupted components digest",
        "an artifact with no harvest identity",
        "a deferral set derived for a different figure of merit",
    ),
    "artifacts_derive_inputs": (
        "one byte changed in a derived file",
        "no measurement behind the third line: a baseline evaluation that crashed",
        "no measurement behind the third line: a record carrying no settled burn time",
        "the burn-time constraint appended at the end of the file",
    ),
    "artifacts_census": (
        "one node's write removed from the census",
        "a node writing a field the committed census does not have",
        "a census record carrying no tree stamp",
        "an unstamped census record offered to --resume",
        "a census with no run record beside it",
    ),
    "artifacts_per_run": (
        "a node removed from the committed set",
        "a node added to the committed set",
    ),
}

#: Which entry the census stages are taken at when they run from the registry.
#: ``evaluation`` is one design point and costs seconds; ``optimisation`` is the
#: population the committed census was measured over.  Settable so that the
#: runner's ``--census-entry`` reaches the promoted gates too.
CENSUS_ENTRY: dict[str, str] = {"entry": "evaluation"}


def _artifact_gates(campaign: Campaign) -> dict[str, Gate]:
    from ..experiment import artifacts as artifacts_mod
    from ..child import census as census_mod
    from ..experiment import input_files as input_files_mod
    from ..child import postsolve as postsolve_mod

    def promote(
        name: str,
        *,
        binds: str,
        proves: str,
        stage,
        stage_teeth,
        needs_runs: bool,
    ) -> Gate:
        def run(*, resume: bool = False) -> Check:
            _code, record = stage(resume)
            check = Check(
                name=name,
                binds=binds,
                passed=record.get("verdict") == "PASS",
                population=record.get("population", ""),
                n_compared=record.get("n_compared", 0),
                n_mismatched=record.get("n_mismatched", 0),
                detail=list(record.get("detail") or ()),
            )
            tooth_code, tooth_record = stage_teeth()
            check.teeth = list(tooth_record.get("teeth") or ())
            if tooth_code != 0:
                check.note(
                    "the stage's teeth stage returned a non-zero code; the "
                    "teeth below say which break was not caught"
                )
            return check

        return framework.gate_from_check(
            name=name,
            binds=binds,
            what_it_proves=proves,
            run=run,
            teeth=ARTIFACT_GATE_TEETH[name],
            needs_runs=needs_runs,
        )

    return {
        "artifacts_check": promote(
            "artifacts_check",
            binds="every committed artifact of every configuration",
            proves=(
                "each artifact's own stamps rebuild and agree with the files "
                "they must agree with, so an artifact built for a different "
                "configuration or component set is refused by name"
            ),
            stage=lambda resume: artifacts_mod.check(campaign),
            stage_teeth=lambda: artifacts_mod.stage_teeth(campaign),
            needs_runs=False,
        ),
        "artifacts_derive_inputs": promote(
            "artifacts_derive_inputs",
            binds="the lifted input file of each pulsed configuration",
            proves=(
                "the three-line derivation reproduces the recorded bytes, and "
                "a derivation with no measurement behind its third line "
                "refuses rather than falling back on a default"
            ),
            stage=lambda resume: input_files_mod.stage_derive(campaign, resume=resume),
            stage_teeth=lambda: input_files_mod.stage_teeth(campaign),
            needs_runs=True,
        ),
        "artifacts_census": promote(
            "artifacts_census",
            binds="the committed run-time write census, per configuration",
            proves=(
                "what the models write at run time is what the committed "
                "census says they write, node by node and field by field"
            ),
            stage=lambda resume: census_mod.stage(
                campaign, entry=CENSUS_ENTRY["entry"], resume=resume
            ),
            stage_teeth=lambda: census_mod.stage_teeth(campaign),
            needs_runs=True,
        ),
        "artifacts_per_run": promote(
            "artifacts_per_run",
            binds="each configuration's per-run deferral set",
            proves=(
                "the class-level classifier re-derives every committed "
                "deferral set from a source scan of the tree under test, node "
                "for node and in the same order"
            ),
            stage=lambda resume: postsolve_mod.stage(
                campaign, census_entry=CENSUS_ENTRY["entry"], resume=resume
            ),
            stage_teeth=lambda: postsolve_mod.stage_teeth(campaign),
            # It takes a write census of its own, so it starts PROCESS.
            needs_runs=True,
        ),
    }




# --------------------------------------------------------------------------
# self-containment, measured rather than asserted
# --------------------------------------------------------------------------
#
# The user's binding requirement on this package (harness plan §6): **every
# verification gate V4 runs is implemented inside `harness/` — none is imported
# from `arch_surgery/idf_probe/` or `arch_surgery/fixedpoint/`, and none is
# invoked as a subprocess into them.**
#
# "grep finds no import" is a claim, and a claim about a package is worth what
# its measurement is worth, so this stage *is* the grep: it reads every Python
# file of the package and the runner beside it, finds every occurrence of either
# directory name, and classifies each one.  Anything it cannot classify is
# printed as a finding rather than passed over.
#
# One classification needs stating because it looks like a hit and is not.  The
# **driver's own** census probe is `process/core/_idf_probe*.py`, inside the
# copied PROCESS tree: same three letters, different thing entirely.  A name
# beginning with an underscore is that module; `arch_surgery/idf_probe` is the
# superseded task machinery.  The stage tells them apart by the underscore and
# says so, because a measurement that silently counted one as the other would be
# reporting the opposite of what it claims.

#: Lines of executable code that name one of the two directories and are
#: **allowed** to, each with what it is and why it cannot reach a measurement.
#: A line of code naming either directory that is not here is a finding.
DECLARED_OUTSIDE_REFERENCES: dict[str, str] = {
    "config.py": (
        "the preflight-only campaign's input directory.  "
        "`repository_tree_campaign()` points the preflight and the self-check "
        "at the repository's own tree and its committed input files, which is "
        "where the superseded revision kept them.  It answers 'does the "
        "harness still compose against the tree the earlier revisions "
        "measured?' and **no record is ever made against it**: "
        "`Campaign.is_experiment_copy` is False for it and `pool.run` refuses "
        "every run on that ground, with a tooth in the run-path check.  It is "
        "a path constant, not an import and not a subprocess"
    ),
    "data_provenance.py": (
        "the declared **source** of two committed files: where each came from "
        "when it was copied in.  It is read by the data check, which fetches "
        "the source from the recorded commit with `git cat-file` — the "
        "repository at a commit, never the live directory (trap T9: a sibling "
        "study's generated output read live catches a half-written state).  A "
        "provenance string, not an import and not a subprocess"
    ),
    "reference.py": (
        "the default root of the **previous revision's** untracked run "
        "records, under `MDA_partitioning_experiment_v3/runs` — not "
        "`idf_probe/` or `fixedpoint/` at all.  It is read by the reproduction "
        "reference's `extract` and `verify` stages only, never at run time, "
        "and what the gate compares against is the committed extract"
    ),
    "gates.py": (
        "this stage's own declaration: the two directory names it searches "
        "for, and the prose that explains each classification.  A measurement "
        "that looks for a string has to contain the string"
    ),
    "registry.py": (
        "the registry entry of this stage: the sentence in its `reports=` "
        "that says what the stage measures names the two directories.  Prose "
        "in a string the button prints; this package opens no such path.  "
        "Added when the registry moved out of gates.py into its own module -- "
        "the stage found the line there and reported it, which is the "
        "scanner biting on a move"
    ),
    "input_files.py": (
        "a sentence inside a **refusal message**, saying where the previous "
        "revision's derived input files were kept so that a reader knows what "
        "to point `--lifted-from` at.  Prose in a message; this package opens "
        "no such path"
    ),
    "ystate.py": (
        "a provenance stamp written **into** a generated artifact, naming the "
        "generator the artifact came from.  It is data written out, not a path "
        "read in"
    ),
    "selfcheck.py": (
        "the opt-in, labelled cross-check of the previous revision's "
        "composition — `--crosscheck-previous`, which executes that revision's "
        "own two composition functions in a subprocess and compares.  It names "
        "`MDA_partitioning_experiment_v3`, not `idf_probe/` or `fixedpoint/`; "
        "it is off by default, is not one of the package's gates, and exists "
        "so that the transcription in this package is *measured* rather than "
        "trusted"
    ),
}

#: The two directories the requirement names.
FORBIDDEN_DIRECTORIES: tuple[str, ...] = ("idf_probe", "fixedpoint")


def _docstring_and_comment_lines(source: str) -> set[int]:
    """Every line of *source* that is inside a docstring or a comment."""
    import io
    import tokenize

    lines: set[int] = set()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        tree = None
    if tree is not None:
        for node in ast.walk(tree):
            if not isinstance(
                node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
            ):
                continue
            body = getattr(node, "body", None)
            if not body:
                continue
            first = body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                if isinstance(first.value.value, str):
                    lines.update(range(first.lineno, (first.end_lineno or first.lineno) + 1))
    try:
        for token in tokenize.generate_tokens(io.StringIO(source).readline):
            if token.type == tokenize.COMMENT:
                lines.add(token.start[0])
            elif token.type == tokenize.STRING and "\n" in token.string:
                # a triple-quoted string used as prose anywhere else
                lines.update(range(token.start[0], token.end[0] + 1))
    except tokenize.TokenError:
        pass
    return lines


def self_containment(campaign: Campaign) -> dict[str, Any]:
    """Every mention of the two superseded directories, classified.

    The measurement behind the sentence *"grep finds no import of, and no
    subprocess into, `idf_probe/` or `fixedpoint/`"*.
    """
    here = Path(__file__).resolve().parent.parent
    runner = here.parent / "experiment_runner.py"
    files = sorted(here.rglob("*.py")) + [runner]
    hits: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    imports: list[dict[str, Any]] = []
    for path in files:
        source = path.read_text()
        prose = _docstring_and_comment_lines(source)
        try:
            tree = ast.parse(source)
        except SyntaxError:
            tree = None
        if tree is not None:
            for node in ast.walk(tree):
                names: list[str] = []
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    names = [node.module or ""]
                for name in names:
                    if any(d in name for d in FORBIDDEN_DIRECTORIES):
                        imports.append(
                            {"file": path.name, "line": node.lineno, "imports": name}
                        )
        for number, line in enumerate(source.splitlines(), start=1):
            for directory in FORBIDDEN_DIRECTORIES:
                if directory not in line:
                    continue
                driver_probe = "_idf_probe" in line and "arch_surgery" not in line
                if driver_probe:
                    kind = (
                        "the driver's own census probe, process/core/"
                        "_idf_probe*.py inside the copied PROCESS tree — the "
                        "same three letters, a different module"
                    )
                    classified = True
                elif number in prose:
                    kind = "heritage: a docstring or comment naming the file this one derives from"
                    classified = True
                elif path.name in DECLARED_OUTSIDE_REFERENCES:
                    kind = DECLARED_OUTSIDE_REFERENCES[path.name]
                    classified = True
                else:
                    kind = "UNCLASSIFIED — a finding"
                    classified = False
                row = {
                    "file": str(path.relative_to(here.parent)),
                    "line": number,
                    "text": line.strip()[:140],
                    "directory": directory,
                    "classification": kind,
                    "executable": number not in prose,
                }
                hits.append(row)
                if not classified:
                    findings.append(row)
                break
    by_kind: dict[str, int] = {}
    for row in hits:
        key = row["classification"].split(" — ")[0].split(".")[0][:60]
        by_kind[key] = by_kind.get(key, 0) + 1
    return {
        "what_this_is": (
            "the measurement behind 'grep finds no import of, and no "
            "subprocess into, the superseded directories': every occurrence "
            "of either name in this package and the runner beside it, "
            "classified"
        ),
        "caption": (
            "One row per line naming one of the two directories. 'executable' "
            "is False where the line is inside a docstring or a comment. "
            f"Population: {len(files)} Python file(s) — every module of the "
            "package plus the runner. A row classified as a finding is one "
            "this stage could not account for."
        ),
        "n_files_scanned": len(files),
        "n_hits": len(hits),
        "n_in_prose": sum(1 for row in hits if not row["executable"]),
        "n_executable": sum(1 for row in hits if row["executable"]),
        "n_findings": len(findings),
        "n_imports_of_either_directory": len(imports),
        "imports": imports,
        "by_classification": by_kind,
        "findings": findings,
        "passed": not findings and not imports,
        "hits": hits,
    }


def print_self_containment(block: Mapping[str, Any]) -> None:
    print(f"\n  {block['what_this_is']}")
    print(f"\n  {block['caption']}\n")
    print(
        f"    files scanned                 {block['n_files_scanned']}\n"
        f"    lines naming either directory {block['n_hits']}\n"
        f"      of which inside prose       {block['n_in_prose']}\n"
        f"      of which executable code    {block['n_executable']}\n"
        f"    imports of either directory   {block['n_imports_of_either_directory']}\n"
        f"    unclassified (findings)       {block['n_findings']}"
    )
    print("\n    by classification:")
    for kind, count in sorted(block["by_classification"].items(), key=lambda kv: -kv[1]):
        print(f"      {count:>3}  {kind}")
    print("\n    every executable line, with what it is:")
    for row in block["hits"]:
        if not row["executable"]:
            continue
        print(f"      {row['file']}:{row['line']}  {row['text']}")
        print(f"          {row['classification'][:150]}")
    if block["findings"]:
        print("\n    FINDINGS:")
        for row in block["findings"]:
            print(f"      {row['file']}:{row['line']}  {row['text']}")


