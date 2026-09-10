#!/usr/bin/env python
"""The gate framework, and the two gates every driver change carries.

A **gate** is a check that must pass before a number is believed.  A gate's
**teeth** are deliberate breaks that the check must catch: a check whose failure
mode has never been exercised is an assertion, not a measurement (orchestration
protocol §12).  That rule is enforced here rather than reviewed: :class:`Gate`
refuses to exist without at least one :class:`Tooth`, so "we forgot the tooth"
is a ``TypeError`` at import and not an omission at review.

Two gates live here today, both of them bound on **every** commit that touches
the experiment's copy of PROCESS:

``G0'`` — *the physics stays frozen in the copy*
    Every file under ``PROCESS/process/models/`` is byte-identical to the frozen
    base commit, bar the one structural edit the user approved.  Implemented
    once, in ``PROCESS/copy_gates.py``; this module runs that implementation by
    path and records its verdict, so there is exactly one implementation of the
    criterion and exactly one place a reader has to look.

``G1`` — *switch neutrality*
    With every architecture switch unset, the copy **after** a driver change
    behaves byte-identically to the copy **before** it.  Two reference runs on
    each configuration — one optimisation and one evaluation, both with the
    whole switch vocabulary cleared — are recorded at the commit before the
    change and again after it, and every deterministic value of the two records
    is compared, plus PROCESS's own output file line by line.

The remaining gates of the experiment plan (G0, G2, G3/G3c, G4–G9, and the
registration of the reproduction gate GR) are **A52 (harness-gates)**'s; this
file starts the framework they land in.  *(One line for A52: give
``experiment_runner.py`` a ``--gate`` value per registered gate and dispatch to
:func:`registry`; nothing else here needs the runner.)*

Written by task **A56 (driver-renames)**.  It derives from no earlier file; the
``Check`` record it writes is shaped like ``harness/selfcheck.py``'s so that a
reader of one recognises the other.

Usage
-----
    python -m harness.gates g0prime
    python -m harness.gates switch-neutrality --capture before
    python -m harness.gates switch-neutrality --capture after
    python -m harness.gates switch-neutrality --compare
    python -m harness.gates all            # every gate that needs no capture

Exit status: 0 every gate passed with every tooth tripping, 1 otherwise.
"""

from __future__ import annotations

import argparse
import copy
import datetime as _dt
import importlib.util
import json
import math
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

_EXPERIMENT_DIR = Path(__file__).resolve().parent.parent
if str(_EXPERIMENT_DIR) not in sys.path:
    sys.path.insert(0, str(_EXPERIMENT_DIR))

from harness import pool as pool_mod  # noqa: E402
from harness import reference as reference_mod  # noqa: E402
from harness.config import Campaign, default_campaign  # noqa: E402

#: Where a gate's verdict goes, under the campaign's runs directory.  Bulk run
#: artifacts are untracked by design; the verdict is small and its numbers go
#: into the report.
GATES_SUBPATH = Path("gates")


class GateError(RuntimeError):
    """A refusal to run or to compare.  Never downgraded into a warning."""


# --------------------------------------------------------------------------
# the framework
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Tooth:
    """One deliberate break, and what the gate must do about it.

    ``check`` returns ``(caught, evidence)``: whether the gate noticed the
    break, and the sentence a reader needs to believe that it did.
    """

    name: str
    what: str
    must: str
    check: Callable[[], tuple[bool, str]] = field(compare=False, repr=False)

    def run(self) -> dict[str, Any]:
        try:
            caught, evidence = self.check()
        except Exception as exc:  # noqa: BLE001 - a tooth that raises is a failure
            caught, evidence = False, f"the tooth raised {type(exc).__name__}: {exc}"
        return {
            "tooth": self.name,
            "perturbation": self.what,
            "must": self.must,
            "caught": bool(caught),
            "tooth_result": "TRIPPED" if caught else "DID NOT TRIP",
            "evidence": evidence,
        }


@dataclass(frozen=True)
class Gate:
    """One gate: what it binds, what it proves, how it runs, and its teeth.

    **A gate with no tooth cannot be constructed.**  That is the whole reason
    this class exists rather than a function per gate: the protocol's rule that
    every gate must be shown capable of failing is a ``TypeError`` here, not a
    checklist item somebody has to remember at review.
    """

    name: str
    binds: str
    what_it_proves: str
    body: Callable[[], dict[str, Any]] = field(compare=False, repr=False)
    teeth: tuple[Tooth, ...] = ()

    def __post_init__(self) -> None:
        if not self.teeth:
            raise TypeError(
                f"gate {self.name!r} was constructed with no tooth.  A check "
                f"that has never been shown to fail is an assertion, not a "
                f"measurement (protocol §12): give it at least one Tooth."
            )

    def run(self, *, records_dir: Path, teeth: bool = True) -> dict[str, Any]:
        """Run the gate, run its teeth, write the verdict, return it."""
        outcome = self.body()
        tooth_records = [t.run() for t in self.teeth] if teeth else []
        all_tripped = all(t["caught"] for t in tooth_records)
        verdict = {
            "gate": self.name,
            "binds": self.binds,
            "what_it_proves": self.what_it_proves,
            "verdict": (
                "PASS" if (outcome.get("passed") and (all_tripped or not teeth)) else "FAIL"
            ),
            "criterion_passed": bool(outcome.get("passed")),
            "teeth_all_tripped": all_tripped if teeth else None,
            "teeth_run": teeth,
            "generated": _dt.datetime.now().isoformat(timespec="seconds"),
            "tree_git_head": _git_head(),
            **{k: v for k, v in outcome.items() if k != "passed"},
            "teeth": tooth_records,
        }
        out = Path(records_dir) / self.name / "gate.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(verdict, indent=2, default=str) + "\n")
        verdict["record"] = str(out)
        return verdict


def _git_head() -> str | None:
    try:
        return subprocess.run(
            ["git", "-C", str(_EXPERIMENT_DIR), "rev-parse", "HEAD"],
            check=True,
            stdout=subprocess.PIPE,
            text=True,
        ).stdout.strip()
    except Exception:  # noqa: BLE001 - context only
        return None


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


# --------------------------------------------------------------------------
# G1 -- switch neutrality
# --------------------------------------------------------------------------
#
# What G1 compares, and what it deliberately does not.
#
# The claim is about **behaviour**: with every architecture switch unset, the
# driver after a change does what it did before it.  So the comparison is over
# every deterministic leaf of the run record and every line of PROCESS's own
# output file -- not over a curated list of interesting fields, because a
# curated list cannot notice a field nobody thought of.  The exclusions are
# therefore named one by one below, each with its reason, and their count is
# published beside the count of compared values: a zero over an unstated
# population is exactly the shape this project has published before (trap T11).

#: Record leaves that cannot be equal between two runs of the same code, with
#: the reason each cannot.  Matched as exact dotted paths or as prefixes.
VOLATILE_RECORD_PATHS: dict[str, str] = {
    # where the run happened
    "outdir": "the two runs are in different directories, by construction",
    "campaign_input_file": "the input file is copied into the run's own directory",
    "entry_state": "a path into the run's own directory",
    "exit_audit.coupling_state": "an absolute path; the file is the same file",
    "exit_audit.restricted.artifact": "an absolute path; the file is the same file",
    "exit_audit.restricted.census": "an absolute path; the file is the same file",
    "pythonpath": "an absolute path; the tree is the same tree",
    "tree": "an absolute path; the tree is the same tree",
    "repository": "an absolute path",
    "process_file": "an absolute path; equality of the tree is asserted per run",
    # when it happened, and how long it took
    "wall_s": "wall clock is context, never evidence (I-10)",
    "cpu_user_s": "cpu time is a contention diagnostic",
    "cpu_sys_s": "cpu time is a contention diagnostic",
    "cpu_s": "cpu time is a contention diagnostic",
    "maxrss_kb": "peak memory varies with the machine's state",
    "loadavg": "machine load while it ran",
    "mfile.process_runtime": "PROCESS's own timing of itself",
    # the commit, which differs by construction: the change is between them
    "tree_git_head": "the two runs are at different commits -- that is the point",
    "tree_git_describe": "derived from the commit",
    "tree_modified_tracked": "the working tree's state, not the driver's behaviour",
    "tree_untracked_paths": "the working tree's state, not the driver's behaviour",
    "tree_git_dirty": "derived from the two above",
    "process_copy_provenance.copy_date": "the copy's provenance file is regenerated by the change",
    # the names being renamed: comparing them would compare the change to itself
    "env_architecture": (
        "the switch vocabulary is what the change renames; every value in it is "
        "null on both sides because the arm sets nothing, but the *keys* are the "
        "rename itself"
    ),
    "resolved_switches": (
        "the driver's module-level readbacks are what the change renames; their "
        "values are the off-state on both sides"
    ),
}

#: Keys of PROCESS's own output file that record when and where a run happened
#: rather than what it computed.  Matched as ``(key)`` anywhere in the line.
VOLATILE_MFILE_KEYS: dict[str, str] = {
    "date": "the calendar date the run started",
    "time": "the clock time the run started",
    "username": "who ran it",
    "fileprefix": "the absolute path of the run's own input file",
    "procver": "the version string written when the tree was packaged",
    "tagno": "git describe of the commit -- different commits by construction",
    "branch_name": "the branch the tree is on",
    "process_runtime": "PROCESS's own timing of itself",
}

#: The two runs G1 makes on every configuration.  Both are reference arms: they
#: compose to an environment with the whole switch vocabulary cleared, which is
#: precisely the condition G1 is about.
NEUTRAL_ARMS: tuple[tuple[str, str], ...] = (("B", "BR"), ("A", "AR"))


def neutrality_root(campaign: Campaign) -> Path:
    return Path(campaign.runs_dir) / GATES_SUBPATH / "switch_neutrality"


def neutrality_run_dir(campaign: Campaign, label: str, configuration: str, arm: str) -> Path:
    return neutrality_root(campaign) / label / configuration / arm


def capture_neutrality(
    campaign: Campaign, label: str, *, resume: bool = False
) -> dict[str, Any]:
    """Run the neutral arms on every configuration and record where they went.

    *label* is ``before`` or ``after``: the copy immediately before the driver
    change, and the copy after it.  Nothing is compared here; capturing and
    comparing are separate so that the "before" side is taken at the commit it
    claims to be taken at and cannot be re-taken later to make a comparison
    agree.
    """
    if label not in ("before", "after"):
        raise GateError(
            f"{label!r} is neither 'before' nor 'after'; G1 compares exactly "
            f"those two captures"
        )
    jobs = []
    for config in campaign.configurations:
        for phase, arm in NEUTRAL_ARMS:
            jobs.append(
                pool_mod.Job(
                    phase=phase,
                    arm=arm,
                    config=config,
                    seed=0,
                    outdir=neutrality_run_dir(campaign, label, config.name, arm),
                    regime="unperturbed",
                    delta=campaign.delta if phase == "B" else None,
                    run_kind="gate",
                )
            )
    results = pool_mod.run_all(jobs, campaign, resume=resume)
    manifest = {
        "label": label,
        "captured": _dt.datetime.now().isoformat(timespec="seconds"),
        "tree_git_head": _git_head(),
        "tree": str(campaign.tree),
        "n_runs": len(jobs),
        "runs": [
            {
                "configuration": job.config.name,
                "arm": job.arm,
                "phase": job.phase,
                "outdir": str(job.outdir),
                "status": (results[i] or {}).get("status") if isinstance(results, list) else None,
            }
            for i, job in enumerate(jobs)
        ],
    }
    path = neutrality_root(campaign) / label / "manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, default=str) + "\n")
    manifest["manifest"] = str(path)
    return manifest


# --- the comparison itself -------------------------------------------------


def leaves(document: Any, prefix: str = "") -> dict[str, Any]:
    """Every scalar of a record, keyed by its dotted path.

    Lists are expanded element by element (``xcs[3]``) rather than compared
    whole, so a mismatch names the element that moved instead of the list that
    contains it.  An empty list is itself a leaf, so that a list becoming empty
    is a difference and not an absence.
    """
    out: dict[str, Any] = {}
    if isinstance(document, dict):
        if not document:
            out[prefix or "<root>"] = "{}"
            return out
        for key, value in document.items():
            out.update(leaves(value, f"{prefix}.{key}" if prefix else str(key)))
    elif isinstance(document, list):
        if not document:
            out[f"{prefix}[]"] = "[]"
            return out
        for index, value in enumerate(document):
            out.update(leaves(value, f"{prefix}[{index}]"))
    else:
        out[prefix] = document
    return out


def is_volatile(path: str) -> str | None:
    """The reason *path* is excluded from the comparison, or None."""
    bare = path.split("[")[0]
    for name, reason in VOLATILE_RECORD_PATHS.items():
        if bare == name or bare.startswith(name + "."):
            return reason
    return None


def compare_records(before: Mapping[str, Any], after: Mapping[str, Any]) -> dict[str, Any]:
    """Every deterministic leaf of two records, compared without tolerance."""
    a, b = leaves(dict(before)), leaves(dict(after))
    every = sorted(set(a) | set(b))
    compared, excluded, mismatches = 0, [], []
    for path in every:
        reason = is_volatile(path)
        if reason is not None:
            excluded.append(path)
            continue
        compared += 1
        missing = object()
        va, vb = a.get(path, missing), b.get(path, missing)
        if va is missing or vb is missing:
            mismatches.append(
                {
                    "field": path,
                    "before": "<absent>" if va is missing else va,
                    "after": "<absent>" if vb is missing else vb,
                    "why": "the field is present on one side only",
                }
            )
            continue
        if not _same(va, vb):
            mismatches.append({"field": path, "before": va, "after": vb})
    return {
        "n_compared": compared,
        "n_excluded": len(excluded),
        "excluded": excluded,
        "n_mismatched": len(mismatches),
        "mismatches": mismatches,
    }


def _same(a: Any, b: Any) -> bool:
    """Bit equality for floats, plain equality otherwise.

    ``==`` says two NaNs differ and says ``-0.0 == 0.0``; neither is what a
    byte-identity gate means, so floats are compared through their hex form.
    """
    if isinstance(a, float) and isinstance(b, float):
        if math.isnan(a) or math.isnan(b):
            return math.isnan(a) and math.isnan(b)
        return a.hex() == b.hex()
    return a == b


def mfile_lines(path: Path) -> list[str]:
    return path.read_text(errors="replace").splitlines()


def mfile_volatile(line: str) -> str | None:
    for key, reason in VOLATILE_MFILE_KEYS.items():
        if f"({key})" in line:
            return reason
    return None


def compare_mfiles(before: Path, after: Path) -> dict[str, Any]:
    """PROCESS's own output file, line by line, with the metadata lines named."""
    a, b = mfile_lines(before), mfile_lines(after)
    n_excluded = 0
    differing: list[dict[str, Any]] = []
    for index in range(max(len(a), len(b))):
        la = a[index] if index < len(a) else None
        lb = b[index] if index < len(b) else None
        source = la if la is not None else lb
        if source is not None and mfile_volatile(source) is not None:
            n_excluded += 1
            continue
        if la != lb:
            differing.append({"line": index + 1, "before": la, "after": lb})
    return {
        "before": str(before),
        "after": str(after),
        "n_lines_before": len(a),
        "n_lines_after": len(b),
        "n_lines_compared": max(len(a), len(b)) - n_excluded,
        "n_lines_excluded": n_excluded,
        "n_lines_differing": len(differing),
        "differing": differing[:20],
    }


def _mfile_for(outdir: Path, configuration: str) -> Path | None:
    named = Path(outdir) / f"{configuration}.MFILE.DAT"
    if named.exists():
        return named
    candidates = sorted(Path(outdir).glob("*MFILE.DAT"))
    return candidates[0] if candidates else None


def _read_record(directory: Path, *, side: str, key: str) -> dict[str, Any]:
    path = Path(directory) / "metrics.json"
    if not path.exists():
        raise GateError(
            f"G1 has no {side} record for {key}: {path} is not there.  A gate "
            f"that cannot find one of its two sides must refuse, never skip -- "
            f"a check with no population is not a check (trap T11)."
        )
    return json.loads(path.read_text())


def neutrality_body(campaign: Campaign) -> dict[str, Any]:
    """Compare the two captures, run by run, value by value and line by line."""
    rows: list[dict[str, Any]] = []
    n_values = n_excluded_values = n_value_mismatches = 0
    n_lines = n_excluded_lines = n_line_mismatches = 0
    passed = True
    for config in campaign.configurations:
        for phase, arm in NEUTRAL_ARMS:
            key = f"{arm}/{config.name}"
            before_dir = neutrality_run_dir(campaign, "before", config.name, arm)
            after_dir = neutrality_run_dir(campaign, "after", config.name, arm)
            before = _read_record(before_dir, side="before", key=key)
            after = _read_record(after_dir, side="after", key=key)
            values = compare_records(before, after)
            mfile_before = _mfile_for(before_dir, config.name)
            mfile_after = _mfile_for(after_dir, config.name)
            if mfile_before is None or mfile_after is None:
                raise GateError(
                    f"G1 has no output file for {key} on one side "
                    f"({mfile_before} / {mfile_after}); the line comparison "
                    f"would be over nothing"
                )
            mfile = compare_mfiles(mfile_before, mfile_after)
            row = {
                "arm": arm,
                "phase": phase,
                "configuration": config.name,
                "status_before": before.get("status"),
                "status_after": after.get("status"),
                "record": values,
                "mfile": mfile,
                "passed": (
                    before.get("status") == "ok"
                    and after.get("status") == "ok"
                    and values["n_mismatched"] == 0
                    and mfile["n_lines_differing"] == 0
                ),
            }
            rows.append(row)
            passed = passed and row["passed"]
            n_values += values["n_compared"]
            n_excluded_values += values["n_excluded"]
            n_value_mismatches += values["n_mismatched"]
            n_lines += mfile["n_lines_compared"]
            n_excluded_lines += mfile["n_lines_excluded"]
            n_line_mismatches += mfile["n_lines_differing"]
    before_manifest = neutrality_root(campaign) / "before" / "manifest.json"
    after_manifest = neutrality_root(campaign) / "after" / "manifest.json"
    return {
        "passed": passed,
        "population": (
            f"{len(rows)} run pair(s) = {len(campaign.configurations)} "
            f"configuration(s) x {len(NEUTRAL_ARMS)} reference arm(s); "
            f"{n_values} deterministic record values and {n_lines} output-file "
            f"lines compared without tolerance, {n_excluded_values} record "
            f"values and {n_excluded_lines} lines excluded as run metadata "
            f"(each named, with its reason, in this record)"
        ),
        "n_pairs": len(rows),
        "n_values_compared": n_values,
        "n_values_excluded": n_excluded_values,
        "n_values_differing": n_value_mismatches,
        "n_mfile_lines_compared": n_lines,
        "n_mfile_lines_excluded": n_excluded_lines,
        "n_mfile_lines_differing": n_line_mismatches,
        "excluded_record_paths": VOLATILE_RECORD_PATHS,
        "excluded_mfile_keys": VOLATILE_MFILE_KEYS,
        "reference_fields_for_context": {
            phase: list(fields) for phase, fields in reference_mod.REFERENCE_FIELDS.items()
        },
        "before_manifest": json.loads(before_manifest.read_text())
        if before_manifest.exists()
        else None,
        "after_manifest": json.loads(after_manifest.read_text())
        if after_manifest.exists()
        else None,
        "runs": rows,
    }


def _neutrality_teeth(campaign: Campaign) -> tuple[Tooth, ...]:
    """Three breaks, on throwaway copies; neither capture is ever touched."""

    def sample_record() -> tuple[dict[str, Any], str]:
        config = campaign.configurations[0]
        directory = neutrality_run_dir(campaign, "before", config.name, "BR")
        return _read_record(directory, side="before", key=f"BR/{config.name}"), config.name

    def one_ulp() -> tuple[bool, str]:
        record, _name = sample_record()
        moved = copy.deepcopy(record)
        target = "values.norm_objf"
        value = (moved.get("values") or {}).get("norm_objf")
        if not isinstance(value, float):
            return False, "the sample record carries no values.norm_objf to move"
        nudged = math.nextafter(value, math.inf)
        moved["values"]["norm_objf"] = nudged
        result = compare_records(record, moved)
        return (
            result["n_mismatched"] == 1
            and result["mismatches"][0]["field"] == target,
            f"{target} moved by one unit in the last place "
            f"({value.hex()} -> {nudged.hex()}) -> "
            f"{result['n_mismatched']} of {result['n_compared']} values differ",
        )

    def one_line() -> tuple[bool, str]:
        config = campaign.configurations[0]
        directory = neutrality_run_dir(campaign, "before", config.name, "BR")
        mfile = _mfile_for(directory, config.name)
        if mfile is None:
            return False, f"no output file under {directory}"
        import tempfile  # noqa: PLC0415 - tooth path only

        with tempfile.TemporaryDirectory() as td:
            twin = Path(td) / mfile.name
            lines = mfile_lines(mfile)
            index = next(
                (
                    i
                    for i, line in enumerate(lines)
                    if mfile_volatile(line) is None and "(ifail)" in line
                ),
                None,
            )
            if index is None:
                return False, "the output file has no (ifail) line to change"
            broken = list(lines)
            broken[index] = broken[index].replace("1 ", "2 ", 1)
            twin.write_text("\n".join(broken) + "\n")
            result = compare_mfiles(mfile, twin)
        return (
            result["n_lines_differing"] >= 1,
            f"line {index + 1} of {mfile.name} (the exit code) changed -> "
            f"{result['n_lines_differing']} of {result['n_lines_compared']} "
            f"compared lines differ",
        )

    def missing_before() -> tuple[bool, str]:
        import tempfile  # noqa: PLC0415 - tooth path only

        with tempfile.TemporaryDirectory() as td:
            try:
                _read_record(Path(td) / "not_there", side="before", key="BR/tooth")
            except GateError as exc:
                return True, f"refused: {str(exc).splitlines()[0][:160]}"
        return False, "a missing 'before' record did not refuse"

    return (
        Tooth(
            "one_value_moved_by_one_ulp",
            "one float of a throwaway copy of a captured record moved by one "
            "unit in the last place",
            "FAIL",
            one_ulp,
        ),
        Tooth(
            "one_output_file_line_changed",
            "one line of a throwaway copy of a captured output file changed",
            "FAIL",
            one_line,
        ),
        Tooth(
            "missing_before_record",
            "the 'before' capture asked for at a directory that does not exist",
            "REFUSE, not skip",
            missing_before,
        ),
    )


# --------------------------------------------------------------------------
# the registry
# --------------------------------------------------------------------------


def registry(campaign: Campaign) -> dict[str, Gate]:
    """Every gate this module implements, by name.

    A52 (harness-gates) adds the rest of the experiment plan's gates here and
    wires the names into ``experiment_runner.py``'s ``--gate`` option.
    """
    return {
        "g0prime": Gate(
            name="g0prime",
            binds="every V4 commit, every arm, both phases",
            what_it_proves=(
                "the physics and engineering models in the experiment's own "
                "copy of PROCESS are byte-identical to the frozen base commit, "
                "bar the one structural edit the user approved"
            ),
            body=lambda: g0prime_body(campaign),
            teeth=_g0prime_teeth(campaign),
        ),
        "switch_neutrality": Gate(
            name="switch_neutrality",
            binds="each driver change, run per change and never batched",
            what_it_proves=(
                "with every architecture switch unset, the copy after the "
                "change behaves byte-identically to the copy before it"
            ),
            body=lambda: neutrality_body(campaign),
            teeth=_neutrality_teeth(campaign),
        ),
    }


def print_verdict(verdict: Mapping[str, Any]) -> None:
    print(f"\n=== gate {verdict['gate']} — {verdict['what_it_proves']}")
    print(f"    binds        : {verdict['binds']}")
    print(f"    verdict      : {verdict['verdict']}")
    print(f"    population   : {verdict.get('population', '(none stated)')}")
    for key in (
        "n_compared",
        "n_identical",
        "n_mismatched",
        "n_pairs",
        "n_values_compared",
        "n_values_excluded",
        "n_values_differing",
        "n_mfile_lines_compared",
        "n_mfile_lines_excluded",
        "n_mfile_lines_differing",
    ):
        if key in verdict:
            print(f"    {key:<28}: {verdict[key]}")
    for row in verdict.get("runs", []):
        print(
            f"      {row['arm']:<3} {row['configuration']:<22} "
            f"values {row['record']['n_mismatched']}/{row['record']['n_compared']} "
            f"lines {row['mfile']['n_lines_differing']}/"
            f"{row['mfile']['n_lines_compared']}  "
            f"{'PASS' if row['passed'] else 'FAIL'}"
        )
        for mismatch in row["record"]["mismatches"][:10]:
            print(f"        DIFFERS {mismatch['field']}: {mismatch.get('before')!r} "
                  f"-> {mismatch.get('after')!r}")
        for line in row["mfile"]["differing"][:10]:
            print(f"        LINE {line['line']}: {line['before']!r} -> {line['after']!r}")
    for failure in verdict.get("failures", []) or []:
        print(f"    FAILURE: {failure}")
    for tooth in verdict.get("teeth", []):
        print(f"    tooth {tooth['tooth']:<32} {tooth['tooth_result']:<13} {tooth['evidence']}")
    print(f"    record       : {verdict.get('record')}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "gate",
        choices=("g0prime", "switch-neutrality", "all"),
        help="which gate to run; 'all' runs the gates that need no capture",
    )
    parser.add_argument(
        "--capture",
        choices=("before", "after"),
        help="switch-neutrality: run the two reference arms on every "
        "configuration and record them under this label, then stop",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="switch-neutrality: compare the two captures (the default)",
    )
    parser.add_argument("--resume", action="store_true", help="skip completed runs")
    parser.add_argument("--no-teeth", action="store_true", help="skip the teeth")
    parser.add_argument(
        "--records", default=None, help="where the verdict goes (default runs/gates)"
    )
    args = parser.parse_args(argv)

    campaign = default_campaign()
    records_dir = Path(args.records) if args.records else Path(campaign.runs_dir) / GATES_SUBPATH

    if args.gate == "switch-neutrality" and args.capture:
        manifest = capture_neutrality(campaign, args.capture, resume=args.resume)
        print(f"captured {manifest['n_runs']} run(s) as {args.capture!r} at "
              f"{manifest['tree_git_head']}")
        for row in manifest["runs"]:
            print(f"  {row['arm']:<3} {row['configuration']:<22} {row['outdir']}")
        print(f"  manifest: {manifest['manifest']}")
        return 0

    names = (
        ["g0prime"]
        if args.gate in ("g0prime", "all")
        else []
    )
    if args.gate == "switch-neutrality":
        names = ["switch_neutrality"]
    elif args.gate == "all":
        names.append("switch_neutrality")

    gates = registry(campaign)
    status = 0
    for name in names:
        try:
            verdict = gates[name].run(records_dir=records_dir, teeth=not args.no_teeth)
        except GateError as exc:
            print(f"\n=== gate {name} — REFUSED TO RUN\n    {exc}")
            status = 1
            continue
        print_verdict(verdict)
        if verdict["verdict"] != "PASS":
            status = 1
    return status


if __name__ == "__main__":
    sys.exit(main())
