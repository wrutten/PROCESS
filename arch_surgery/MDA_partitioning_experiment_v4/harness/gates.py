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
    python -m harness.gates predicate-counters   # a measurement, not a gate

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

from harness import arms as arms_mod  # noqa: E402
from harness import input_files as input_files_mod  # noqa: E402
from harness import pool as pool_mod  # noqa: E402
from harness import records as records_mod  # noqa: E402
from harness import reference as reference_mod  # noqa: E402
from harness import switches as switches_mod  # noqa: E402
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
    # The counts of the two lists above.  Excluded on the same reason, and
    # named here because leaving them out was a defect: the lists were excluded
    # and their counts were not, so a single scratch file beside the runner --
    # a draft report, a log -- made G1 FAIL on a field that cannot change what
    # the driver does.  That is the false alarm the record schema was amended
    # to prevent when it split "modified tracked" from "untracked" (A44
    # (transfer-gap) stamped a whole set of records dirty on untracked files
    # alone).  What can move a measurement is a modified *tracked* file, and
    # that is not hidden by this: it would move the behaviour, which is what
    # the other 2 300 values compare.
    "tree_modified_tracked_n": "the count of the list above, on the same reason",
    "tree_untracked_paths_n": "the count of the list above, on the same reason",
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
    # fields a harness change adds or rewords between the two captures.  G1
    # binds the *driver*, and the two captures are made by the harness at each
    # commit, so a field the harness itself adds is excluded by name -- and
    # only ever by name, with the reason, because a zero over a population
    # quietly smaller than the one stated is this project's own trap T11.
    "output_loop_sweeps": (
        "the count is what the output-path change adds: null on the side that "
        "had no counter, measured on the side that has one.  What the two "
        "sides' output paths *did* is compared in full through the output file "
        "and through node_calls_total"
    ),
    "output_loop_null_because": (
        "the sentence explaining the absent counter, present only on the side "
        "that had no counter"
    ),
    "output_path_entries": (
        "a counter the output-path change adds; absent on the earlier side"
    ),
    "audit_snapshot": (
        "the snapshot block the audit-position change adds; absent on the "
        "earlier side.  Both captures audit at the same position, which is "
        "checked before the comparison runs and is what makes exit_audit "
        "comparable"
    ),
    "reproduction_overrides": (
        "a field the record gains so that a run made under the reproduction "
        "gate's overrides says so; null on both sides here, absent on the "
        "earlier one"
    ),
    "audit_position_note": (
        "the sentence saying how the audit position is reached, which is what "
        "the change rewrites.  audit_position itself is compared, and the two "
        "captures are refused if it differs"
    ),
    # The predicate counters (DR4).  Each is a field whose value is *null on
    # the earlier side because no counter existed* and a number on the later
    # one -- which is the change itself, not a behavioural difference, and is
    # the only reason each is here.  Two of them, the upstream pair, are not
    # zero on the later side: the reference arms the gate runs stop on
    # upstream's own test, so those two count a loop upstream was already
    # running.  That is precisely why they cannot be compared across the two
    # captures, and precisely why the rest of the record -- the node counts,
    # the sweep histogram, the exit audit, every output-file line -- is what
    # carries the neutrality claim instead.
    "predicate_evaluations": (
        "null before the counter existed, a number after: the count is the "
        "change.  It is 0 in these runs, because the reference arms never "
        "enter the block path, and 0 is still not null"
    ),
    "components_compared": (
        "null before, a number after; 0 in these runs for the same reason as "
        "the line above"
    ),
    "block_visits": (
        "null before, a per-block mapping after.  Empty in these runs: the "
        "reference arms build no block schedule"
    ),
    "empty_block_visits": (
        "null before, a per-block mapping after; empty in these runs for the "
        "same reason"
    ),
    "empty_block_sweeps": (
        "null before, a per-block mapping after; empty in these runs for the "
        "same reason"
    ),
    "dispatch_sweeps": (
        "null before, the run's sweep total after.  The count itself is not "
        "new -- the driver has always incremented this cell, and the sweep "
        "histogram it feeds IS compared, value for value, on both sides -- "
        "what is new is the record field"
    ),
    "upstream_predicate_evaluations": (
        "null before, a number after, and **not** zero: these runs are the "
        "reference arms, which stop on upstream's own test.  What the test "
        "decided is compared in full through the sweep histogram, the node "
        "counts and the output file"
    ),
    "upstream_components_compared": (
        "null before, a number after; not zero, for the same reason as the "
        "line above"
    ),
    "predicate_counters": (
        "the block the counters are split out in, with their sentences: "
        "absent on the earlier side entirely"
    ),
    "predicate_counters_null_because": (
        "the sentence explaining the absent counters, present only on the "
        "side that had none"
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

#: Where G1's optimisation runs take their exit audit, on **both** sides.
#:
#: G1 binds the driver, and the two captures are made by the harness as it
#: stood at each commit.  Where a driver change also moves a harness-side
#: instrument, pinning that instrument to one position on both sides is what
#: keeps the comparison about the driver: the whole ``exit_audit`` block --
#: residual, argmax, brief, restricted statistic, the audit's own node count --
#: is then compared value for value instead of excluded.  The alternative,
#: letting each side audit wherever its own revision does and excluding the
#: block, would put the strongest thing G1 compares outside the comparison.
#: A capture whose records disagree about the position **refuses**.
NEUTRAL_AUDIT_POSITION = "after_run"


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
                    audit_position=NEUTRAL_AUDIT_POSITION,
                )
            )
    results = pool_mod.run_all(jobs, campaign, resume=resume)
    manifest = {
        "label": label,
        "captured": _dt.datetime.now().isoformat(timespec="seconds"),
        "tree_git_head": _git_head(),
        "tree": str(campaign.tree),
        "n_runs": len(jobs),
        "audit_position": NEUTRAL_AUDIT_POSITION,
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


def _assert_same_audit_position(
    before: Mapping[str, Any], after: Mapping[str, Any], *, key: str
) -> str | None:
    """Refuse unless both captures measured their accuracy at the same place.

    The ``exit_audit`` block is the most sensitive thing G1 compares, and it is
    only comparable if both sides took it at the same position.  A capture made
    at one position against a capture made at another would report the moved
    instrument as a driver difference -- or, worse, be "fixed" by excluding the
    block, which is how a gate quietly stops testing the thing it is for.
    """
    a, b = before.get("audit_position"), after.get("audit_position")
    if a != b:
        raise GateError(
            f"G1 cannot compare {key}: the 'before' capture audited at {a!r} "
            f"and the 'after' capture at {b!r}.  The exit audit is only "
            f"comparable at one position, and moving it between captures would "
            f"report the instrument as a driver difference.  Re-capture one "
            f"side at the other's position; do not exclude the block."
        )
    return a


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
            _assert_same_audit_position(before, after, key=key)
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
        "audit_position_on_both_sides": NEUTRAL_AUDIT_POSITION,
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

    def moved_audit_position() -> tuple[bool, str]:
        record, _name = sample_record()
        moved = copy.deepcopy(record)
        moved["audit_position"] = "entry_to_write_output_files"
        try:
            _assert_same_audit_position(record, moved, key="BR/tooth")
        except GateError as exc:
            return True, f"refused: {str(exc).splitlines()[0][:170]}"
        return False, "two captures audited at different positions and compared anyway"

    return (
        Tooth(
            "captures_audited_at_different_positions",
            "a throwaway copy of a captured record with its audit position "
            "moved to the other legal value",
            "REFUSE, not compare",
            moved_audit_position,
        ),
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
# G9 -- the output path writes the state the solve handed over
# --------------------------------------------------------------------------
#
# What G9 binds is the removal of upstream's output-time loop from the two
# intervention arms, and it binds it in the only way that means anything: not
# "the switch was set" but "the state that reached the output files is the
# state the optimiser accepted".
#
# Three criteria on an arm whose matrix cell turns the loop off:
#
#   (i)   the coupling state immediately before the file-writing call is
#         **bit-identical**, component by component in hex, to the snapshot
#         taken at the entry to the output path -- on every component the
#         per-run deferred nodes do not own.  Those nodes run between the two
#         snapshots by design (that is what "once per run, at the accepted
#         optimum" means), their write set is derived from the same two
#         committed artifacts the restricted audit derives it from, never
#         listed, and the components they move are reported by name rather
#         than waved past;
#   (ii)  the output-time loop ran **0** sweeps;
#   (iii) the objective in PROCESS's own output file is the accepted objective,
#         to the bit.
#
# And on the reference arms, which keep the loop: every field that describes
# the solve equals the reproduction gate's record for the same run.  "Nothing
# changes on BR/B0" is a comparison against a record made before this change,
# not an assertion.  The audit residual is deliberately **not** among those
# fields -- the audit moved to the declared position for every arm, which is
# the other half of this task -- and that exclusion is stated here rather than
# left to be noticed.

#: Fields that describe the solve and must be untouched by an output-path
#: change, compared against the reproduction gate's record run for run.
#: ``exit_audit.residual_max_hex`` is deliberately absent: the audit position
#: moved for every arm in this same change, so the residual is expected to
#: differ and comparing it would test the audit, not the output path.
UNCHANGED_ON_REFERENCE_ARMS: tuple[str, ...] = (
    "node_calls_solve_phase",
    "node_calls_total",
    "n_model_calls",
    "n_prime_calls",
    "exact.norm_objf",
    "n_solver_iterations",
    "mfile.ifail",
    "exit_forensics.n_attempts",
    "exit_forensics.n_solver_iterations_summed_over_attempts",
)


def output_path_root(campaign: Campaign) -> Path:
    return Path(campaign.runs_dir) / GATES_SUBPATH / "output_path"


def output_path_jobs(campaign: Campaign) -> list[pool_mod.Job]:
    """Every Phase B arm at seed 0 on every configuration where it is active.

    The intervention arms carry the criteria; the reference arms carry the
    "nothing changes" half.  A skipped arm is skipped **by the configuration's
    own recorded reason**, never by a condition written here.
    """
    root = output_path_root(campaign)
    jobs: list[pool_mod.Job] = []
    for config in campaign.configurations:
        for arm in arms_mod.active_arms(config, "B"):
            jobs.append(
                pool_mod.Job(
                    phase="B",
                    arm=arm,
                    config=config,
                    seed=0,
                    outdir=root / "runs" / config.name / arm,
                    regime="unperturbed",
                    delta=campaign.delta,
                    run_kind="gate",
                )
            )
    return jobs


def capture_output_path(campaign: Campaign, *, resume: bool = False) -> dict[str, Any]:
    """Run G9's runs and record where they went.  Nothing is compared here."""
    jobs = output_path_jobs(campaign)
    # The two arms whose matrix cell turns the loop off read the lifted input
    # file.  Checked here, before anything starts, so that "the derived input
    # file is not there" is a refusal at the gate's front door rather than a
    # failed run three jobs in.
    lifted = {}
    for config in campaign.configurations:
        if config.pulsed:
            lifted[config.name] = input_files_mod.assert_lifted(config, campaign)
    results = pool_mod.run_all(jobs, campaign, resume=resume)
    manifest = {
        "captured": _dt.datetime.now().isoformat(timespec="seconds"),
        "tree_git_head": _git_head(),
        "n_runs": len(jobs),
        "lifted_input_files": lifted,
        "runs": [
            {
                "configuration": job.config.name,
                "arm": job.arm,
                "outdir": str(job.outdir),
                "status": (results[i] or {}).get("status")
                if isinstance(results, list)
                else None,
            }
            for i, job in enumerate(jobs)
        ],
        "skipped": {
            config.name: dict(arms_mod.skipped_arms(config))
            for config in campaign.configurations
        },
    }
    path = output_path_root(campaign) / "manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, default=str) + "\n")
    manifest["manifest"] = str(path)
    return manifest


def _snapshot(directory: Path, where: str, *, key: str) -> dict[str, Any]:
    path = Path(directory) / f"y_{where}.json"
    if not path.exists():
        raise GateError(
            f"G9 has no {where!r} snapshot for {key}: {path} is not there.  A "
            f"gate that cannot find one of the two states it compares must "
            f"refuse, never pass over an empty comparison (trap T11)."
        )
    return json.loads(path.read_text())


def compare_snapshots(
    entry: Mapping[str, Any],
    written: Mapping[str, Any],
    *,
    excluded: set[str],
) -> dict[str, Any]:
    """Two snapshots of the coupling state, component by component, exactly.

    Floats travel as hex literals in a snapshot, so equality here is bit
    equality and no tolerance is applied or available.  ``excluded`` names the
    components the per-run deferred nodes own; they are compared too, and
    reported separately, so that "the difference is confined to the nodes that
    are *supposed* to run there" is a measurement rather than a premise.
    """
    if entry["components_sha256"] != written["components_sha256"]:
        raise GateError(
            "G9's two snapshots were taken against different component specs "
            f"({entry['components_sha256']} vs {written['components_sha256']}); "
            "comparing them would compare components nobody paired"
        )
    a, b = entry["state"], written["state"]
    names = sorted(set(a) | set(b))
    differing_kept, differing_excluded = [], []
    for name in names:
        if a.get(name) == b.get(name):
            continue
        (differing_excluded if name in excluded else differing_kept).append(name)
    return {
        "n_components": len(names),
        "n_excluded_as_per_run_owned": len(excluded & set(names)),
        "n_compared": len(names) - len(excluded & set(names)),
        "n_differing_outside_the_per_run_write_sets": len(differing_kept),
        "differing_outside_the_per_run_write_sets": differing_kept[:20],
        "n_differing_inside_the_per_run_write_sets": len(differing_excluded),
        "differing_inside_the_per_run_write_sets": differing_excluded[:20],
    }


def per_run_owned_components(
    campaign: Campaign, arm: str, config
) -> tuple[set[str], dict[str, Any]]:
    """Components the per-run deferred nodes write, derived from the artifacts.

    The same derivation the restricted audit uses -- the per-run artifact names
    nodes, the committed run-time write census maps each node to what it writes
    on this configuration -- so the two statistics cannot drift apart.  An arm
    that defers nothing owns nothing, and the whole state is compared.
    """
    entry = arms_mod.ARMS[arm]
    if not entry.defer_per_run:
        return set(), {"defers_per_run": False, "artifact": None}
    artifact = config.per_run_artifact(lifted_input_file=entry.input_file == "lifted")
    nodes = list(json.loads(Path(artifact).read_text())["post_solve_nodes"])
    census = json.loads(
        (Path(campaign.data_dir) / "node_writesets.json").read_text()
    )["per_scenario"]
    if config.name not in census:
        raise GateError(
            f"G9 has no write census for {config.name}; the per-run-owned set "
            f"would be guessed, so it is refused"
        )
    writes = census[config.name]["writes_by_node"]
    owned: set[str] = set()
    for node in nodes:
        owned |= set(writes.get(node, ()))
    return owned, {
        "defers_per_run": True,
        "artifact": str(artifact),
        "per_run_nodes": nodes,
        "n_owned_fields": len(owned),
    }


def output_path_body(campaign: Campaign) -> dict[str, Any]:
    """Compare each run against its criteria, and each reference against GR."""
    root = output_path_root(campaign)
    reference_root = Path(campaign.runs_dir) / "gates" / "reproduction" / "runs"
    rows: list[dict[str, Any]] = []
    passed = True
    n_components = n_component_diffs = 0
    n_reference_values = n_reference_diffs = 0
    for config in campaign.configurations:
        for arm in arms_mod.active_arms(config, "B"):
            key = f"{arm}/{config.name}"
            directory = root / "runs" / config.name / arm
            record = _read_record(directory, side="G9", key=key)
            entry = arms_mod.ARMS[arm]
            row: dict[str, Any] = {
                "arm": arm,
                "configuration": config.name,
                "matrix_cell": arms_mod.matrix_cell(entry, "output-time loop (MDA_Output)"),
                "status": record.get("status"),
                "output_path": record.get("output_path"),
                "output_loop_sweeps": record.get("output_loop_sweeps"),
                "output_path_entries": record.get("output_path_entries"),
                "audit_position": record.get("audit_position"),
                "audit_position_declared": record.get("audit_position_declared"),
                "exit_audit_residual_max_hex": (record.get("exit_audit") or {}).get(
                    "residual_max_hex"
                ),
                "exit_audit_n_above_tau": (
                    (record.get("exit_audit") or {}).get("restricted") or {}
                ).get("n_above"),
                "outdir": str(directory),
            }
            checks: list[dict[str, Any]] = []
            checks.append(
                {
                    "check": "the audit was taken where the plan declares",
                    "passed": record.get("audit_position")
                    == record.get("audit_position_declared")
                    == "entry_to_write_output_files",
                    "detail": f"{record.get('audit_position')!r}",
                }
            )
            if entry.output_loop == "none":
                row["expected_output_path"] = "finalise_once"
                owned, derivation = per_run_owned_components(campaign, arm, config)
                row["per_run_derivation"] = derivation
                comparison = compare_snapshots(
                    _snapshot(directory, "entry_to_write_output_files", key=key),
                    _snapshot(directory, "before_finalise", key=key),
                    excluded=owned,
                )
                row["state_written_vs_handed_over"] = comparison
                n_components += comparison["n_compared"]
                n_component_diffs += comparison[
                    "n_differing_outside_the_per_run_write_sets"
                ]
                checks += [
                    {
                        "check": (
                            "(i) the state written out is the state the solve "
                            "handed over, component by component in hex, "
                            "outside the per-run deferred nodes' own writes"
                        ),
                        "passed": comparison[
                            "n_differing_outside_the_per_run_write_sets"
                        ]
                        == 0,
                        "detail": (
                            f"{comparison['n_differing_outside_the_per_run_write_sets']}"
                            f" of {comparison['n_compared']} components differ"
                        ),
                    },
                    {
                        "check": "(ii) the output-time loop ran no sweep",
                        "passed": record.get("output_loop_sweeps") == 0,
                        "detail": f"output_loop_sweeps = {record.get('output_loop_sweeps')}",
                    },
                    {
                        "check": "(iii) the output file's objective is the accepted objective, to the bit",
                        "passed": _same_hex(
                            (record.get("mfile") or {}).get("norm_objf"),
                            (record.get("exact") or {}).get("norm_objf"),
                        ),
                        "detail": _hex_detail(
                            (record.get("mfile") or {}).get("norm_objf"),
                            (record.get("exact") or {}).get("norm_objf"),
                        ),
                    },
                    {
                        "check": "the driver resolved the finalise-once path",
                        "passed": record.get("output_path") == "finalise_once",
                        "detail": f"{record.get('output_path')!r}",
                    },
                ]
            else:
                row["expected_output_path"] = "mda_output"
                reference = reference_root / config.name / arm / pool_mod.seed_directory(0)
                previous = _read_record(
                    reference, side="reproduction gate", key=key
                )
                diffs = []
                for path in UNCHANGED_ON_REFERENCE_ARMS:
                    left = records_mod.resolve_path(previous, path)
                    right = records_mod.resolve_path(record, path)
                    n_reference_values += 1
                    if not _same(left, right):
                        diffs.append({"field": path, "gate_GR": left, "here": right})
                n_reference_diffs += len(diffs)
                row["unchanged_against_the_reproduction_gate"] = {
                    "reference_record": str(reference / "metrics.json"),
                    "n_compared": len(UNCHANGED_ON_REFERENCE_ARMS),
                    "n_differing": len(diffs),
                    "differing": diffs,
                    "fields": list(UNCHANGED_ON_REFERENCE_ARMS),
                    "audit_residual_excluded_because": (
                        "the audit position moved to the declared one for every "
                        "arm in this same change, so the residual is expected "
                        "to differ; the audit is gated by its own criterion "
                        "above and the two residuals are published side by side"
                    ),
                    "audit_residual_here": row["exit_audit_residual_max_hex"],
                    "audit_residual_at_the_previous_position": (
                        previous.get("exit_audit") or {}
                    ).get("residual_max_hex"),
                }
                checks += [
                    {
                        "check": "nothing about the solve changed on the reference arm",
                        "passed": not diffs,
                        "detail": (
                            f"{len(diffs)} of {len(UNCHANGED_ON_REFERENCE_ARMS)} "
                            f"fields differ from the reproduction gate's record"
                        ),
                    },
                    {
                        "check": "the driver resolved upstream's output path",
                        "passed": record.get("output_path") == "mda_output",
                        "detail": f"{record.get('output_path')!r}",
                    },
                    {
                        "check": "the output-time loop actually ran",
                        "passed": (record.get("output_loop_sweeps") or 0) >= 1,
                        "detail": f"output_loop_sweeps = {record.get('output_loop_sweeps')}",
                    },
                ]
            row["checks"] = checks
            row["passed"] = record.get("status") == "ok" and all(
                c["passed"] for c in checks
            )
            passed = passed and row["passed"]
            rows.append(row)
    return {
        "passed": passed,
        "population": (
            f"{len(rows)} run(s) at seed 0 = every optimisation-phase arm on "
            f"every configuration where it is active, each composed from the "
            f"experiment's matrix; {n_components} coupling-state components "
            f"compared in hex on the arms whose matrix cell turns the "
            f"output-time loop off, and {n_reference_values} solve-describing "
            f"values compared against the reproduction gate's records on the "
            f"arms that keep it.  No tolerance is applied to any of them"
        ),
        "n_runs": len(rows),
        "n_components_compared": n_components,
        "n_components_differing": n_component_diffs,
        "n_reference_values_compared": n_reference_values,
        "n_reference_values_differing": n_reference_diffs,
        "unchanged_fields": list(UNCHANGED_ON_REFERENCE_ARMS),
        "runs": rows,
    }


def _same_hex(mfile_value, accepted_hex) -> bool:
    if mfile_value is None or accepted_hex is None:
        return False
    try:
        return float(mfile_value).hex() == accepted_hex
    except (TypeError, ValueError):
        return False


def _hex_detail(mfile_value, accepted_hex) -> str:
    try:
        got = float(mfile_value).hex()
    except (TypeError, ValueError):
        got = repr(mfile_value)
    return f"output file {got}, accepted {accepted_hex}"


def _output_path_teeth(campaign: Campaign) -> tuple[Tooth, ...]:
    """Four breaks, every one on a throwaway copy; no run is ever touched."""

    def an_intervention_run() -> tuple[Path, str, Any]:
        for config in campaign.configurations:
            for arm in arms_mod.active_arms(config, "B"):
                if arms_mod.ARMS[arm].output_loop == "none":
                    directory = output_path_root(campaign) / "runs" / config.name / arm
                    if (directory / "metrics.json").exists():
                        return directory, f"{arm}/{config.name}", config
        raise GateError("G9 has no intervention run to bite on")

    def one_ulp_before_finalise() -> tuple[bool, str]:
        directory, key, config = an_intervention_run()
        entry = _snapshot(directory, "entry_to_write_output_files", key=key)
        written = copy.deepcopy(entry)
        arm = key.split("/")[0]
        owned, _ = per_run_owned_components(campaign, arm, config)
        target = next(
            (
                name
                for name, value in sorted(written["state"].items())
                if value.get("k") == "f" and name not in owned
            ),
            None,
        )
        if target is None:
            return False, "the snapshot carries no float component outside the per-run write sets"
        before = float.fromhex(written["state"][target]["hex"])
        after = math.nextafter(before, math.inf)
        written["state"][target]["hex"] = after.hex()
        result = compare_snapshots(entry, written, excluded=owned)
        return (
            result["n_differing_outside_the_per_run_write_sets"] == 1
            and result["differing_outside_the_per_run_write_sets"] == [target],
            f"{target} moved by one unit in the last place between the snapshot "
            f"and the file-writing call ({before.hex()} -> {after.hex()}) -> "
            f"{result['n_differing_outside_the_per_run_write_sets']} of "
            f"{result['n_compared']} components differ",
        )

    def missing_snapshot() -> tuple[bool, str]:
        import tempfile  # noqa: PLC0415 - tooth path only

        with tempfile.TemporaryDirectory() as td:
            try:
                _snapshot(Path(td), "before_finalise", key="B3/tooth")
            except GateError as exc:
                return True, f"refused: {str(exc).splitlines()[0][:160]}"
        return False, "a missing snapshot did not refuse"

    def a_sweep_that_should_not_be() -> tuple[bool, str]:
        directory, key, _config = an_intervention_run()
        record = copy.deepcopy(_read_record(directory, side="G9", key=key))
        record["output_loop_sweeps"] = 1
        return (
            record["output_loop_sweeps"] != 0,
            f"a throwaway copy of {key}'s record with output_loop_sweeps = 1 "
            f"fails criterion (ii), which reads the field the driver stamped "
            f"(the run itself recorded 0)",
        )

    def a_moved_objective() -> tuple[bool, str]:
        directory, key, _config = an_intervention_run()
        record = _read_record(directory, side="G9", key=key)
        accepted = (record.get("exact") or {}).get("norm_objf")
        written = (record.get("mfile") or {}).get("norm_objf")
        if accepted is None or written is None:
            return False, f"{key} carries no objective to move"
        nudged = math.nextafter(float(written), math.inf)
        return (
            _same_hex(written, accepted) and not _same_hex(nudged, accepted),
            f"the output file's objective moved by one unit in the last place "
            f"({float(written).hex()} -> {nudged.hex()}) no longer equals the "
            f"accepted {accepted}",
        )

    return (
        Tooth(
            "one_component_moved_by_one_ulp_before_finalise",
            "one float of a throwaway copy of the entry snapshot moved by one "
            "unit in the last place, standing in for the state being touched "
            "between the snapshot and the file-writing call",
            "FAIL, naming the component",
            one_ulp_before_finalise,
        ),
        Tooth(
            "missing_snapshot",
            "one of the two snapshots asked for at a directory that has none",
            "REFUSE, not skip",
            missing_snapshot,
        ),
        Tooth(
            "an_output_time_sweep_under_the_finalise_once_path",
            "a throwaway copy of an intervention run's record with "
            "output_loop_sweeps = 1",
            "FAIL",
            a_sweep_that_should_not_be,
        ),
        Tooth(
            "the_written_objective_moved",
            "the output file's objective moved by one unit in the last place",
            "FAIL",
            a_moved_objective,
        ),
    )


# --------------------------------------------------------------------------
# the output path, measured -- not a gate
# --------------------------------------------------------------------------
#
# Two quantities the experiment plan asks for by name, published as
# measurements with their populations and never as acceptance criteria.
#
# **What the output-time loop costs.**  Section 3.3 of the plan commits the
# sweep count of that loop, per run, by arm and configuration.  It is read from
# the driver's own counter on the reproduction gate's runs -- the only set of
# runs in which every arm, including the two whose matrix cell turns the loop
# off, executes it (that gate runs them with it on, because the records it
# reproduces were made that way).
#
# **What the accepted state's residual is, at the declared position.**  The
# same section says the one signal the output-time loop found by accident in
# the previous revision -- a handed-over state that was not output-idempotent
# -- is to be "looked for on purpose": the exit audit at the accepted point,
# per run, with the count of components above the tolerance.  That count is
# read from the gate's own runs at the declared position.
#
# It is published **twice**, and the reason is not caution.  The audit sweep
# runs every node, including the ones an arm defers to once per run; measured
# from the handed-over state -- which is *before* those nodes have run -- their
# own outputs necessarily move, and a whole-state count on such an arm would
# report that as non-convergence.  The restricted count excludes exactly the
# components those nodes write, derived here from the same two committed
# artifacts the audit's own restricted statistic derives from: the per-run
# deferral artifact names the nodes, the run-time write census says what each
# writes on this configuration.  One excluded set per configuration, from the
# committed input file's artifact, so that the count is on the same ruler in
# every arm of that configuration.
#
# (The restricted count is computed here, from the run's own committed residual
# vector, rather than carried in the record: wiring it into the optimisation
# record belongs with gate G4, which is task A52 (harness-gates)'s.  Both
# constructions are stated in the table's caption.)


def _residual_vector(directory: Path, *, key: str) -> dict[str, Any]:
    path = Path(directory) / "audit_residual.json"
    if not path.exists():
        raise GateError(
            f"no residual vector for {key}: {path} is not there.  A count of "
            f"components above the tolerance with no vector behind it is a "
            f"number over an unstated population (trap T11)."
        )
    return json.loads(path.read_text())


def excluded_by_the_per_run_nodes(campaign: Campaign, config) -> tuple[set[str], dict]:
    """Components the per-run deferrable nodes write on this configuration.

    One set per configuration, from the **committed** input file's artifact, so
    that every arm of that configuration is restricted by the same set — which
    is the whole point of a restricted statistic.  The derivation is the audit's
    own: the artifact names nodes, the census maps each node to what it writes.
    """
    artifact = config.per_run_artifact(lifted_input_file=False)
    nodes = list(json.loads(Path(artifact).read_text())["post_solve_nodes"])
    census = json.loads(
        (Path(campaign.data_dir) / "node_writesets.json").read_text()
    )["per_scenario"]
    if config.name not in census:
        raise GateError(
            f"no write census for {config.name}; the excluded set would be "
            f"guessed, so it is refused"
        )
    writes = census[config.name]["writes_by_node"]
    owned: set[str] = set()
    for node in nodes:
        owned |= set(writes.get(node, ()))
    return owned, {
        "artifact": str(artifact),
        "per_run_nodes": nodes,
        "census": str(Path(campaign.data_dir) / "node_writesets.json"),
        "n_fields_named": len(owned),
    }


#: The two runs the contrast makes on each configuration: the reference arm,
#: identical in everything, written out through each of the two output paths.
CONTRAST_LABELS: dict[str, str | None] = {"with_loop": None, "without_loop": "none"}


def contrast_root(campaign: Campaign) -> Path:
    return output_path_root(campaign) / "contrast"


def contrast_jobs(campaign: Campaign) -> list[pool_mod.Job]:
    """The reference arm, run twice per configuration, once down each path.

    Deliberately **not** a matrix composition: no arm of the experiment writes
    upstream's own solve out through the one-call path.  That is the point —
    holding the solve fixed and varying only the output path is the only way to
    say what the output-time loop does to the numbers a reader of the output
    file gets, and the arm whose numbers a reader actually gets is the reference
    one.  It runs as a gate, never as a campaign record, and the environment
    override is stamped in each record.
    """
    jobs: list[pool_mod.Job] = []
    for config in campaign.configurations:
        for label, value in CONTRAST_LABELS.items():
            jobs.append(
                pool_mod.Job(
                    phase="B",
                    arm="BR",
                    config=config,
                    seed=0,
                    outdir=contrast_root(campaign) / config.name / label,
                    regime="unperturbed",
                    delta=campaign.delta,
                    run_kind="gate",
                    override_env=(
                        {}
                        if value is None
                        else {switches_mod.REGISTRY["output_loop"].driver_name: value}
                    ),
                )
            )
    return jobs


def capture_contrast(campaign: Campaign, *, resume: bool = False) -> dict[str, Any]:
    """Run the contrast's two runs per configuration.  Nothing is compared here."""
    jobs = contrast_jobs(campaign)
    results = pool_mod.run_all(jobs, campaign, resume=resume)
    manifest = {
        "captured": _dt.datetime.now().isoformat(timespec="seconds"),
        "tree_git_head": _git_head(),
        "n_runs": len(jobs),
        "runs": [
            {
                "configuration": job.config.name,
                "label": sorted(CONTRAST_LABELS)[i % len(CONTRAST_LABELS)],
                "override_env": dict(job.override_env),
                "outdir": str(job.outdir),
                "status": (results[i] or {}).get("status")
                if isinstance(results, list)
                else None,
            }
            for i, job in enumerate(jobs)
        ],
    }
    path = contrast_root(campaign) / "manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, default=str) + "\n")
    manifest["manifest"] = str(path)
    return manifest


def contrast_rows(campaign: Campaign) -> list[dict[str, Any]]:
    """What the output-time loop moves, per configuration, in the output file.

    The solve is held fixed and is checked to be fixed: the accepted objective
    and the solve-phase node count must be identical on the two sides, and a
    row where they are not says so rather than attributing a solve difference
    to the output path.  What is then counted is output-file lines differing,
    with the same metadata keys excluded that gate G1 excludes -- date, time,
    user, paths, version strings and PROCESS's own timing of itself.
    """
    rows: list[dict[str, Any]] = []
    for config in campaign.configurations:
        key = f"BR/{config.name}"
        directory = {
            label: contrast_root(campaign) / config.name / label
            for label in CONTRAST_LABELS
        }
        record = {
            label: _read_record(d, side=f"contrast:{label}", key=key)
            for label, d in directory.items()
        }
        mfile = {}
        for label, d in directory.items():
            found = _mfile_for(d, config.name)
            if found is None:
                raise GateError(
                    f"the contrast has no output file for {key} on the "
                    f"{label!r} side ({d}); the line comparison would be over "
                    f"nothing"
                )
            mfile[label] = found
        lines = compare_mfiles(mfile["with_loop"], mfile["without_loop"])
        solve_identical = (
            record["with_loop"].get("node_calls_solve_phase")
            == record["without_loop"].get("node_calls_solve_phase")
            and (record["with_loop"].get("exact") or {}).get("norm_objf")
            == (record["without_loop"].get("exact") or {}).get("norm_objf")
        )
        rows.append(
            {
                "configuration": config.name,
                "arm": "BR",
                "solve_identical": solve_identical,
                "node_calls_solve_phase": record["with_loop"].get(
                    "node_calls_solve_phase"
                ),
                "node_calls_total_with_loop": record["with_loop"].get(
                    "node_calls_total"
                ),
                "node_calls_total_without_loop": record["without_loop"].get(
                    "node_calls_total"
                ),
                "accepted_objf_hex": (record["with_loop"].get("exact") or {}).get(
                    "norm_objf"
                ),
                "output_loop_sweeps_with_loop": record["with_loop"].get(
                    "output_loop_sweeps"
                ),
                "output_loop_sweeps_without_loop": record["without_loop"].get(
                    "output_loop_sweeps"
                ),
                "mfile_ifail_with_loop": (record["with_loop"].get("mfile") or {}).get(
                    "ifail"
                ),
                "mfile_ifail_without_loop": (
                    record["without_loop"].get("mfile") or {}
                ).get("ifail"),
                "n_lines_compared": lines["n_lines_compared"],
                "n_lines_excluded": lines["n_lines_excluded"],
                "n_lines_differing": lines["n_lines_differing"],
                "differing_first": [
                    row["before"].split()[0][:70] for row in lines["differing"][:12]
                ],
            }
        )
    return rows


def output_path_measurements(campaign: Campaign) -> dict[str, Any]:
    """The two measurements, over the run sets each is defined on."""
    reproduction_root = Path(campaign.runs_dir) / "gates" / "reproduction" / "runs"
    sweeps: list[dict[str, Any]] = []
    for run in reference_mod.reference_set(campaign):
        if run.phase != "B":
            continue
        key = f"{run.arm}/{run.configuration}/seed{run.seed:03d}"
        directory = (
            reproduction_root
            / run.configuration
            / run.arm
            / pool_mod.seed_directory(run.seed)
        )
        record = _read_record(directory, side="the reproduction gate", key=key)
        total = record.get("node_calls_total")
        solve = record.get("node_calls_solve_phase")
        sweeps.append(
            {
                "arm": run.arm,
                "configuration": run.configuration,
                "seed": run.seed,
                "output_path": record.get("output_path"),
                "output_loop_sweeps": record.get("output_loop_sweeps"),
                "output_path_entries": record.get("output_path_entries"),
                "reproduction_overrides": record.get("reproduction_overrides"),
                "node_calls_solve_phase": solve,
                "node_calls_total": total,
                "node_calls_after_the_solve": (
                    None if total is None or solve is None else total - solve
                ),
            }
        )

    above: list[dict[str, Any]] = []
    excluded_by_config: dict[str, dict] = {}
    for config in campaign.configurations:
        owned, derivation = excluded_by_the_per_run_nodes(campaign, config)
        excluded_by_config[config.name] = derivation
        for arm in arms_mod.active_arms(config, "B"):
            if arms_mod.ARMS[arm].output_loop != "none":
                continue
            key = f"{arm}/{config.name}"
            directory = output_path_root(campaign) / "runs" / config.name / arm
            record = _read_record(directory, side="G9", key=key)
            vector = _residual_vector(directory, key=key)
            tau = float(vector["tau"])
            scaled = vector["scaled"]
            kept = {k: v for k, v in scaled.items() if k not in owned}
            above.append(
                {
                    "arm": arm,
                    "configuration": config.name,
                    "audit_position": record.get("audit_position"),
                    "tau": tau,
                    "residual_max_hex": (record.get("exit_audit") or {}).get(
                        "residual_max_hex"
                    ),
                    "n_tested_whole_state": len(scaled),
                    "n_above_tau_whole_state": sum(
                        1 for v in scaled.values() if v >= tau
                    ),
                    "n_tested_restricted": len(kept),
                    "n_above_tau_restricted": sum(
                        1 for v in kept.values() if v >= tau
                    ),
                    "n_excluded_as_per_run_owned": len(scaled) - len(kept),
                    "residual_max_restricted": max(kept.values()) if kept else 0.0,
                    "residual_max_restricted_hex": float(
                        max(kept.values()) if kept else 0.0
                    ).hex(),
                    "residual_argmax_restricted": (
                        max(kept, key=kept.get) if kept else None
                    ),
                    "above_tau_restricted": sorted(
                        k for k, v in kept.items() if v >= tau
                    )[:20],
                }
            )
    contrast = contrast_rows(campaign)
    return {
        "what_the_output_time_loop_moves": {
            "population": (
                f"{len(contrast) * 2} run(s) = the reference arm at seed 0 on "
                f"each of {len(contrast)} configuration(s), written out once "
                f"through each output path with everything else identical.  "
                f"Not a matrix composition: no arm of the experiment writes "
                f"upstream's own solve through the one-call path, and holding "
                f"the solve fixed while varying only the output path is what "
                f"isolates the loop's effect on the numbers a reader gets"
            ),
            "rows": contrast,
        },
        "output_time_loop_sweeps": {
            "population": (
                f"{len(sweeps)} optimisation run(s) of the reproduction gate = "
                f"its whole optimisation-phase reference set.  Every one runs "
                f"upstream's output-time loop: the two arms whose matrix cell "
                f"turns it off carry the gate's recorded override, because the "
                f"records they reproduce were made before the switch existed"
            ),
            "rows": sweeps,
        },
        "above_tau_at_the_declared_position": {
            "population": (
                f"{len(above)} run(s) at seed 0 = the arms whose matrix cell "
                f"turns the output-time loop off, on every configuration where "
                f"they are active, from gate G9's own runs; the audit is taken "
                f"at the entry to the output path in every one"
            ),
            "excluded_set_per_configuration": excluded_by_config,
            "rows": above,
        },
        "generated": _dt.datetime.now().isoformat(timespec="seconds"),
        "tree_git_head": _git_head(),
    }


def print_measurements(block: Mapping[str, Any]) -> None:
    """The three tables, with their captions, as the report prints them."""
    contrast = block["what_the_output_time_loop_moves"]
    print()
    print(
        "*Caption: one row per configuration.  The reference arm is run at "
        "seed 0 and written out twice — once through upstream's output-time "
        "loop and once through the one-call path — with everything else "
        "identical.  The solve is held fixed and checked to be fixed: "
        '"solve identical" is the accepted objective hex and the solve-phase '
        "node count agreeing on the two sides, and a row where they do not "
        "agree is not a statement about the output path.  Lines differing are "
        "lines of PROCESS's own output file, with the same metadata keys "
        "excluded that the switch-neutrality gate excludes (date, time, user, "
        "paths, version strings and PROCESS's own timing of itself).  Counts, "
        "not timings.  Population: " + contrast["population"] + ".*"
    )
    print()
    print(
        "| configuration | solve identical | accepted objective (hex) | "
        "solve-phase node calls | total node calls, loop on / off | sweeps, "
        "on / off | output-file lines differing / compared |"
    )
    print("|---|---|---|---:|---:|---:|---:|")
    for row in contrast["rows"]:
        print(
            f"| `{row['configuration']}` | "
            f"{'yes' if row['solve_identical'] else '**NO**'} | "
            f"`{row['accepted_objf_hex']}` | {row['node_calls_solve_phase']} | "
            f"{row['node_calls_total_with_loop']} / "
            f"{row['node_calls_total_without_loop']} | "
            f"{row['output_loop_sweeps_with_loop']} / "
            f"{row['output_loop_sweeps_without_loop']} | "
            f"**{row['n_lines_differing']}** / {row['n_lines_compared']} |"
        )
    print()
    for row in contrast["rows"]:
        if row["differing_first"]:
            print(f"  {row['configuration']}: {', '.join(row['differing_first'])}")
    sweeps = block["output_time_loop_sweeps"]
    print()
    print(
        "*Caption: one row per optimisation run of the reproduction gate.  "
        '"Sweeps" is how many times upstream\'s output-time loop evaluated the '
        "whole model set before writing the output files, read from the "
        'driver\'s own counter; "entries" is how many times the output path '
        'was entered (one per scan point).  "After the solve" is model node '
        "calls made after the solve-phase counter was frozen: the per-run "
        "deferred nodes where an arm has them, plus the output-time loop's own "
        "sweeps.  Counts, not timings.  Population: "
        + sweeps["population"]
        + ".*"
    )
    print()
    print("| arm | configuration | seed | path | sweeps | entries | solve-phase node calls | node calls after the solve |")
    print("|---|---|---:|---|---:|---:|---:|---:|")
    for row in sweeps["rows"]:
        print(
            f"| `{row['arm']}` | `{row['configuration']}` | {row['seed']} | "
            f"`{row['output_path']}` | {row['output_loop_sweeps']} | "
            f"{row['output_path_entries']} | {row['node_calls_solve_phase']} | "
            f"{row['node_calls_after_the_solve']} |"
        )
    above = block["above_tau_at_the_declared_position"]
    print()
    print(
        "*Caption: one row per run of gate G9 on an arm whose matrix cell "
        "turns the output-time loop off.  The exit audit is one further sweep "
        "of the whole model set from the state the solve handed over, and the "
        "columns count how many coupling-state components moved by at least "
        "the tolerance under it.  **Whole state** counts every tested "
        "component; **restricted** excludes the components the per-run "
        "deferrable nodes write, derived from the committed per-run artifact "
        "and the committed run-time write census, one set per configuration so "
        "every arm is on the same ruler.  The two differ because the audit "
        "sweep runs those nodes and the handed-over state is from before they "
        "ran, so their own outputs move by construction — which is why the "
        "whole-state maximum is not published here at all: on an arm that "
        "defers, it is a per-run node's own output and says nothing about "
        "convergence.  Population: "
        + above["population"]
        + ".*"
    )
    print()
    print(
        "| arm | configuration | tau | tested | above tau, whole state | "
        "tested, restricted | above tau, restricted | restricted max | "
        "restricted argmax |"
    )
    print("|---|---|---:|---:|---:|---:|---:|---:|---|")
    for row in above["rows"]:
        print(
            f"| `{row['arm']}` | `{row['configuration']}` | {row['tau']:g} | "
            f"{row['n_tested_whole_state']} | "
            f"{row['n_above_tau_whole_state']} | {row['n_tested_restricted']} | "
            f"{row['n_above_tau_restricted']} | "
            f"{row['residual_max_restricted']:.3g} | "
            f"`{row['residual_argmax_restricted']}` |"
        )
    print()
    for name, derivation in above["excluded_set_per_configuration"].items():
        print(
            f"  {name}: per-run nodes {derivation['per_run_nodes']} write "
            f"{derivation['n_fields_named']} field(s); artifact "
            f"{Path(derivation['artifact']).name}"
        )


# --------------------------------------------------------------------------
# The per-sweep overhead, counted -- a measurement, not a gate
# --------------------------------------------------------------------------
#
# EXPERIMENT_PLAN.md section 3.5, check 5, and improvement-list item 3.  The
# partitioned arrangement runs far more sweeps of the model sequence than the
# flat one while executing far fewer model nodes, and the previous revision
# measured it no faster.  Something a sweep costs is therefore not proportional
# to the nodes it runs, and the convergence test is the obvious suspect: a flat
# loop compares the whole coupling state on every sweep while a block loop
# compares only its own block's write set.
#
# Nothing here is evidence about speed.  These are counts, which reproduce bit
# for bit; no conclusion in this experiment rests on a clock (issue I-10).  What
# the counts settle is whether a non-node-proportional term of the hypothesised
# *size* exists at all.
#
# The population is the reproduction gate's own runs, because they already
# exist at this commit, they cover every arm the gate covers on all three
# configurations, and they are made by the committed run path.  They are one
# seed each -- seed 0 for most rows -- so no row here is a campaign statistic
# and none is quoted as one.

#: The order rows are printed in, so a reader can compare configurations down a
#: column.  Arms follow the experiment plan's matrix order.
MEASUREMENT_ARM_ORDER = arms_mod.MATRIX_ORDER


def predicate_counter_rows(campaign: Campaign, root: Path | None = None) -> list[dict[str, Any]]:
    """One row per run of the reproduction gate, with its counters.

    Reads records; runs nothing.  A run directory with no record is a row that
    says so, never a row silently dropped: a table over a population quietly
    smaller than the one named is this project's trap T11.
    """
    from harness import reproduction as reproduction_mod  # noqa: PLC0415

    base = Path(root or (Path(campaign.runs_dir) / reproduction_mod.RUNS_SUBPATH))
    rows: list[dict[str, Any]] = []
    for run in reference_mod.reference_set(campaign):
        directory = (
            base / "runs" / run.configuration / run.arm
            / pool_mod.seed_directory(run.seed)
        )
        record = records_mod.read(directory)
        rows.append(_counter_row(run.arm, run.configuration, run.seed, run.phase, record))
    rows.sort(
        key=lambda r: (
            r["configuration"],
            MEASUREMENT_ARM_ORDER.index(r["arm"])
            if r["arm"] in MEASUREMENT_ARM_ORDER
            else len(MEASUREMENT_ARM_ORDER),
            r["seed"],
        )
    )
    return rows


def _counter_row(
    arm: str, configuration: str, seed: int, phase: str, record: Mapping[str, Any]
) -> dict[str, Any]:
    """One run's counters, with the reconciliation of its sweep total."""
    block_visits = record.get("block_visits") or {}
    empty_visits = record.get("empty_block_visits") or {}
    empty_sweeps = record.get("empty_block_sweeps") or {}
    totals = record.get("module_solve_totals") or {}
    evaluations = record.get("predicate_evaluations")
    components = record.get("components_compared")
    upstream_evaluations = record.get("upstream_predicate_evaluations")
    upstream_components = record.get("upstream_components_compared")
    counters = record.get("predicate_counters") or {}
    coupling = counters.get("coupling_state_predicate") or {}
    row: dict[str, Any] = {
        "configuration": configuration,
        "arm": arm,
        "seed": seed,
        "phase": phase,
        "status": record.get("status"),
        "stops_on": (
            "coupling state"
            if evaluations
            else ("upstream's objective/constraint test" if upstream_evaluations else "—")
        ),
        "dispatch_sweeps": record.get("dispatch_sweeps"),
        "block_sweeps": totals.get("block_sweeps"),
        "output_loop_sweeps": record.get("output_loop_sweeps"),
        "predicate_evaluations": evaluations,
        "components_compared": components,
        "mean_test_width": coupling.get("mean_test_width"),
        "mean_test_width_by_block": coupling.get("mean_test_width_by_block") or {},
        "evaluations_by_block": coupling.get("evaluations_by_block") or {},
        "upstream_predicate_evaluations": upstream_evaluations,
        "upstream_components_compared": upstream_components,
        "upstream_mean_test_width": (
            (counters.get("upstream_predicate") or {}).get("mean_test_width")
        ),
        "block_visits": dict(sorted(block_visits.items())) if block_visits else {},
        "n_block_visits": sum(block_visits.values()) if block_visits else 0,
        "empty_block_visits": dict(sorted(empty_visits.items())) if empty_visits else {},
        "n_empty_block_visits": sum(empty_visits.values()) if empty_visits else 0,
        "empty_block_sweeps": dict(sorted(empty_sweeps.items())) if empty_sweeps else {},
        "n_empty_block_sweeps": sum(empty_sweeps.values()) if empty_sweeps else 0,
        "node_calls_solve_phase": record.get("node_calls_solve_phase"),
        "node_calls_single_eval": record.get("node_calls_single_eval"),
        "n_call_models": totals.get("n_call_models"),
    }
    row["empty_share_of_block_visits"] = (
        (row["n_empty_block_visits"] / row["n_block_visits"])
        if row["n_block_visits"]
        else None
    )
    row["reconciliation"] = _reconcile_sweeps(record, row)
    return row


def _reconcile_sweeps(record: Mapping[str, Any], row: Mapping[str, Any]) -> dict[str, Any]:
    """Does the run's sweep total decompose into the parts that claim it?

    The identity, for an arm that runs a block schedule::

        dispatch_sweeps = block_sweeps + output_loop_sweeps + per_run_sweep

    ``per_run_sweep`` is one sweep, spent in ``write_output_files`` running the
    nodes deferred to once per run; it is 1 when that set is non-empty and 0
    otherwise.  For an arm with no block schedule the first term is instead the
    sweeps the analysis loop took, which the per-evaluation histogram sums.

    A residual that is not 0 is reported, never absorbed: a sweep total nobody
    can decompose is a total nobody can attribute.
    """
    total = row["dispatch_sweeps"]
    if total is None:
        return {"checked": False, "why": "the record carries no sweep total"}
    per_run = record.get("post_solve_totals") or {}
    per_run_sweep = 1 if (per_run.get("executed_once") or []) else 0
    output = row["output_loop_sweeps"] or 0
    if row["block_sweeps"]:
        loop = row["block_sweeps"]
        loop_is = "block_sweeps (the block schedule's own charged sweeps)"
    else:
        loop = ((record.get("sweeps_per_eval") or {}).get("n_sweeps")) or 0
        loop_is = "sweeps_per_eval.n_sweeps (the analysis loop's own sweeps)"
    residual = total - (loop + output + per_run_sweep)
    return {
        "checked": True,
        "dispatch_sweeps": total,
        "loop_sweeps": loop,
        "loop_sweeps_is": loop_is,
        "output_loop_sweeps": output,
        "per_run_deferral_sweep": per_run_sweep,
        "residual": residual,
        "decomposes": residual == 0,
        "why": (
            "the exit audit's own sweep is not in this total: the counters are "
            "read before the audit runs, so the measurement is not charged to "
            "the thing it measures"
        ),
    }


def predicate_counter_measurements(
    campaign: Campaign, root: Path | None = None
) -> dict[str, Any]:
    """The per-sweep-overhead block the report publishes, with its population."""
    rows = predicate_counter_rows(campaign, root=root)
    finished = [r for r in rows if r["status"] == "ok"]
    undecomposed = [
        f"{r['arm']}/{r['configuration']}"
        for r in finished
        if r["reconciliation"].get("checked") and not r["reconciliation"]["decomposes"]
    ]
    empty_rows = [r for r in finished if r["n_empty_block_visits"]]
    return {
        "what": (
            "what each arm's convergence test cost, in counts.  Two predicates "
            "are reported and never pooled: an arm stops on exactly one of "
            "them.  'mean test width' is components compared divided by "
            "evaluations — the average number of components one test walked"
        ),
        "population": (
            f"{len(rows)} run(s) of the reproduction gate at this commit, "
            f"{len(finished)} of them finished; one seed per row (seed 0 "
            f"except where the row says otherwise), so no figure here is a "
            f"campaign statistic and none is quoted as one"
        ),
        "empty_visits_disclaimer": (
            "empty block visits are INCLUDED in every visit and sweep count "
            "here.  On st_regression the PULSE block is visited once per "
            "evaluation of the model set with its member skipped at the call "
            "site: a full sweep of the model sequence that executes no model.  "
            "The user ruled that this stays and is disclaimed rather than "
            "repaired (issue I-20a), because dropping the block would change "
            "the node weights the comparison rests on.  A block the per-call "
            "deferral has emptied of members is also an empty visit but costs "
            "no sweep at all, which is why the two are counted separately"
        ),
        "timing_note": (
            "no timing appears here and none is implied: these are counts, "
            "which reproduce bit for bit"
        ),
        "n_rows": len(rows),
        "n_finished": len(finished),
        "rows": rows,
        "sweep_decomposition": {
            "identity": (
                "dispatch_sweeps = loop sweeps + output-time loop sweeps + the "
                "one sweep the per-run deferral spends at the output path"
            ),
            "n_checked": len([r for r in finished if r["reconciliation"].get("checked")]),
            "n_that_do_not_decompose": len(undecomposed),
            "which": undecomposed,
        },
        "flat_against_partitioned": {
            "what": (
                "the flat control against the partitioned arm at the same "
                "configuration and the same seed: how much more often the "
                "convergence test is evaluated, how much narrower each "
                "evaluation is, and what the two multiply to.  A ratio below "
                "1 in the components column means the partitioned arm does "
                "LESS component comparison than the flat one, which is what "
                "decides the per-sweep-overhead hypothesis on counts"
            ),
            "population": (
                "one run against one run per cell, never a campaign mean, and "
                "only where both arms have a run at the same seed"
            ),
            "rows": predicate_pair_rows(rows),
        },
        "empty_visits": {
            "n_runs_with_any": len(empty_rows),
            "by_run": [
                {
                    "configuration": r["configuration"],
                    "arm": r["arm"],
                    "visits": r["n_block_visits"],
                    "empty_visits": r["n_empty_block_visits"],
                    "empty_visits_that_cost_a_sweep": r["n_empty_block_sweeps"],
                    "share_of_visits": r["empty_share_of_block_visits"],
                    "by_block": r["empty_block_visits"],
                    "sweeps_by_block": r["empty_block_sweeps"],
                }
                for r in empty_rows
            ],
        },
    }


#: The pairs check 5 is about: the flat control against the partitioned arm, at
#: the same configuration and the same seed.  ``B1`` is the flat arm carrying
#: the lift, so it is the one whose design vector matches ``B3``'s; ``B0`` is
#: the flat control the cost ratio is quoted against.  A pair is formed only
#: where both runs exist at the same seed — never across seeds, because the two
#: would then be different problems.
PREDICATE_PAIRS: tuple[tuple[str, str], ...] = (("B0", "B3"), ("B1", "B3"))


def predicate_pair_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Flat against partitioned, at matched configuration and seed.

    The hypothesis check 5 exists to settle is that the partitioned arm pays a
    per-sweep cost the flat one does not, with the convergence test the prime
    suspect: the flat loop compares the whole coupling state on every sweep and
    a block loop compares only its own block's write set.  The suspect predicts
    that the partitioned arm does **more** component comparison in total, since
    it runs far more sweeps.  These ratios are what decides that, and they
    decide it on counts alone.

    Each cell is a ratio of two single runs, not of two campaign means; the
    caption says so and nothing here is a campaign statistic.
    """
    by_key = {(r["configuration"], r["arm"], r["seed"]): r for r in rows}
    out: list[dict[str, Any]] = []
    for (configuration, arm, seed), row in sorted(by_key.items()):
        for flat, partitioned in PREDICATE_PAIRS:
            if arm != partitioned:
                continue
            control = by_key.get((configuration, flat, seed))
            if control is None or control["status"] != "ok" or row["status"] != "ok":
                continue
            out.append(
                {
                    "configuration": configuration,
                    "seed": seed,
                    "flat_arm": flat,
                    "partitioned_arm": partitioned,
                    "flat_evaluations": control["predicate_evaluations"],
                    "partitioned_evaluations": row["predicate_evaluations"],
                    "evaluations_ratio": _ratio(
                        row["predicate_evaluations"], control["predicate_evaluations"]
                    ),
                    "flat_width": control["mean_test_width"],
                    "partitioned_width": row["mean_test_width"],
                    "width_ratio": _ratio(
                        row["mean_test_width"], control["mean_test_width"]
                    ),
                    "flat_components": control["components_compared"],
                    "partitioned_components": row["components_compared"],
                    "components_ratio": _ratio(
                        row["components_compared"], control["components_compared"]
                    ),
                    "flat_sweeps": control["dispatch_sweeps"],
                    "partitioned_sweeps": row["dispatch_sweeps"],
                    "sweeps_ratio": _ratio(
                        row["dispatch_sweeps"], control["dispatch_sweeps"]
                    ),
                    "flat_node_calls": control["node_calls_solve_phase"],
                    "partitioned_node_calls": row["node_calls_solve_phase"],
                    "node_calls_ratio": _ratio(
                        row["node_calls_solve_phase"],
                        control["node_calls_solve_phase"],
                    ),
                }
            )
    return out


def _ratio(a, b):
    if a is None or not b:
        return None
    return a / b


def _n(value) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:,.1f}"
    return f"{value:,}"


def print_predicate_counters(block: Mapping[str, Any]) -> None:
    """The measurement, as the report prints it."""
    print("\n=== the per-sweep overhead, counted (experiment plan §3.5 check 5)")
    print(f"    {block['what']}")
    print(f"    population : {block['population']}")
    print(f"    empty visits: {block['empty_visits_disclaimer']}")
    print()
    head = (
        f"    {'configuration':<22} {'arm':<4} {'seed':>4} {'stops on':<34} "
        f"{'sweeps':>8} {'pred.ev':>8} {'comps':>12} {'width':>8} "
        f"{'visits':>7} {'empty':>7} {'e.sweeps':>9}"
    )
    print(head)
    print("    " + "-" * (len(head) - 4))
    for row in block["rows"]:
        if row["status"] != "ok":
            print(
                f"    {row['configuration']:<22} {row['arm']:<4} "
                f"{row['seed']:>4} NO RECORD ({row['status']})"
            )
            continue
        evaluations = row["predicate_evaluations"] or row["upstream_predicate_evaluations"]
        components = row["components_compared"] or row["upstream_components_compared"]
        width = row["mean_test_width"] or row["upstream_mean_test_width"]
        print(
            f"    {row['configuration']:<22} {row['arm']:<4} {row['seed']:>4} "
            f"{row['stops_on']:<34} "
            f"{_n(row['dispatch_sweeps']):>8} {_n(evaluations):>8} "
            f"{_n(components):>12} {_n(width):>8} "
            f"{_n(row['n_block_visits']):>7} {_n(row['n_empty_block_visits']):>7} "
            f"{_n(row['n_empty_block_sweeps']):>9}"
        )
    print()
    print("    per-block mean test width, one row per run:")
    for row in block["rows"]:
        if not row["mean_test_width_by_block"]:
            continue
        widths = ", ".join(
            f"{label} {width:.0f} ({row['evaluations_by_block'].get(label, 0):,} tests)"
            for label, width in row["mean_test_width_by_block"].items()
        )
        print(
            f"      {row['configuration']:<22} {row['arm']:<4} "
            f"{row['seed']:>4} {widths}"
        )
    print()
    pairs = block["flat_against_partitioned"]
    print("    flat against partitioned, matched configuration and seed:")
    print(f"      {pairs['what']}")
    print(f"      population : {pairs['population']}")
    pair_head = (
        f"      {'configuration':<22} {'pair':<9} {'seed':>4} "
        f"{'evals x':>9} {'width x':>9} {'comps x':>9} {'sweeps x':>9} "
        f"{'nodes x':>9}"
    )
    print(pair_head)
    print("      " + "-" * (len(pair_head) - 6))
    for pair in pairs["rows"]:
        def _r(value):
            return f"{value:.3f}" if value is not None else "—"
        print(
            f"      {pair['configuration']:<22} "
            f"{pair['flat_arm'] + '→' + pair['partitioned_arm']:<9} "
            f"{pair['seed']:>4} {_r(pair['evaluations_ratio']):>9} "
            f"{_r(pair['width_ratio']):>9} {_r(pair['components_ratio']):>9} "
            f"{_r(pair['sweeps_ratio']):>9} {_r(pair['node_calls_ratio']):>9}"
        )
    print()
    decomposition = block["sweep_decomposition"]
    print(f"    sweep decomposition: {decomposition['identity']}")
    print(
        f"      {decomposition['n_checked']} run(s) checked, "
        f"{decomposition['n_that_do_not_decompose']} that do not decompose"
        + (f": {decomposition['which']}" if decomposition["which"] else "")
    )
    print(f"    {block['timing_note']}")


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
        "output_path": Gate(
            name="output_path",
            binds=(
                "the removal of the output-time loop from the arms whose "
                "matrix cell turns it off, on every configuration where they "
                "are active"
            ),
            what_it_proves=(
                "the state those arms write to their output files is the "
                "state their solve handed over — bit for bit, outside the "
                "per-run deferred nodes' own writes — with no output-time "
                "sweep run and the accepted objective in the file; and that "
                "nothing about the solve changed on the arms that keep the "
                "loop"
            ),
            body=lambda: output_path_body(campaign),
            teeth=_output_path_teeth(campaign),
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
    for key in (
        "n_runs",
        "n_components_compared",
        "n_components_differing",
        "n_reference_values_compared",
        "n_reference_values_differing",
    ):
        if key in verdict:
            print(f"    {key:<28}: {verdict[key]}")
    for row in verdict.get("runs", []):
        if "checks" in row:
            print(
                f"      {row['arm']:<3} {row['configuration']:<22} "
                f"loop={row['matrix_cell']:<8} path={str(row['output_path']):<14} "
                f"sweeps={row['output_loop_sweeps']}  "
                f"{'PASS' if row['passed'] else 'FAIL'}"
            )
            for check in row["checks"]:
                print(f"        [{'ok ' if check['passed'] else 'FAIL'}] "
                      f"{check['check']} — {check['detail']}")
            continue
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
        choices=(
            "g0prime",
            "switch-neutrality",
            "output-path",
            "output-path-contrast",
            "output-path-measurements",
            "predicate-counters",
            "all",
        ),
        help="which gate to run; 'all' runs the gates that need no capture.  "
        "'output-path-contrast', 'output-path-measurements' and "
        "'predicate-counters' are not gates: they publish what the experiment "
        "plan asks for by name — what the output-time loop moves in the output "
        "files, what it costs, where the accepted state sits against the "
        "tolerance at the declared audit position, and (section 3.5 check 5) "
        "what each arm's convergence test cost in evaluations and components "
        "compared, with the empty block visits counted beside them",
    )
    parser.add_argument(
        "--capture",
        choices=("before", "after", "runs"),
        help="switch-neutrality: run the two reference arms on every "
        "configuration and record them under this label ('before' or "
        "'after'), then stop.  output-path: 'runs' makes the gate's own runs, "
        "then stops",
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

    if args.gate == "output-path-contrast":
        manifest = capture_contrast(campaign, resume=args.resume)
        print(f"captured {manifest['n_runs']} contrast run(s) at "
              f"{manifest['tree_git_head']}")
        for row in manifest["runs"]:
            print(f"  {row['configuration']:<22} {row['label']:<14} "
                  f"{row['status']} {row['override_env']}")
        print(f"  manifest: {manifest['manifest']}")
        return 0

    if args.gate == "predicate-counters":
        block = predicate_counter_measurements(campaign)
        out = records_dir / "predicate_counters" / "measurements.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(block, indent=2, default=str) + "\n")
        print_predicate_counters(block)
        print(f"\n  record: {out}")
        return 0

    if args.gate == "output-path-measurements":
        block = output_path_measurements(campaign)
        out = records_dir / "output_path" / "measurements.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(block, indent=2, default=str) + "\n")
        print_measurements(block)
        print(f"\n  record: {out}")
        return 0

    if args.gate == "output-path" and args.capture:
        manifest = capture_output_path(campaign, resume=args.resume)
        print(f"captured {manifest['n_runs']} run(s) at "
              f"{manifest['tree_git_head']}")
        for row in manifest["runs"]:
            print(f"  {row['arm']:<3} {row['configuration']:<22} "
                  f"{row['status']} {row['outdir']}")
        print(f"  manifest: {manifest['manifest']}")
        return 0

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
    elif args.gate == "output-path":
        names = ["output_path"]
    elif args.gate == "all":
        names.append("switch_neutrality")
        names.append("output_path")

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
