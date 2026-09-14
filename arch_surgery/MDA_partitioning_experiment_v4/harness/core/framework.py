#!/usr/bin/env python
"""The shapes every verification in this package takes: gate, tooth, check.

Three words, defined once, because the package uses them everywhere.

A **gate** is a check that must pass before a number is believed.  A gate's
**teeth** are deliberate breaks that the check must catch: a check whose failure
mode has never been exercised is an assertion, not a measurement (orchestration
protocol §12).  A **measurement** is the third thing in this file and is
deliberately *not* a gate — it publishes what the experiment plan asks for by
name and has nothing to pass or fail, so calling it a gate would put a verdict
where there is none.

The rule that makes this a module rather than a convention: :class:`Gate`
refuses to exist without at least one :class:`Tooth`, so "we forgot the tooth"
is a ``TypeError`` at import and not an omission at review.

:class:`Check` is the record shape the harness's own self-check and the artifact
stages already wrote before there was a framework.  It lived twice — once as
``selfcheck.Check`` and once as ``artifacts.StageCheck``, field for field
identical — and it lives here once instead.  The two names survive as aliases so
that nothing reading them has to change, and :func:`gate_from_check` promotes
one into a :class:`Gate` **without touching its criterion**: the criterion runs
exactly the code it ran before, and what the promotion adds is the verdict
record, the registry entry and the declared tooth list.

Why the declared tooth list is not decoration.  A ``Check`` runs its own teeth
inside its body and records what they did, so a promotion that simply copied
that list would give a gate whose teeth are whatever the body happened to
exercise — which is the same as having no declaration at all.  Instead each
promoted check **names** the teeth it must run; a declared tooth the body never
ran is a tooth that DID NOT TRIP, and the gate fails.  That turns "the six
self-checks still run the teeth they claim" into a comparison rather than a
belief.

This module imports nothing from the rest of the package, on purpose: every
other module may import it, and a framework that depends on what it frames
cannot be imported by all of it.

:func:`survey_records` and :func:`assert_records_read_are_current` are the same
idea one level up from :func:`survey_heads`: a stage that reads other records
declares them, the framework stamps what it found, and a consumer refuses the
stage record when those files have moved under it.

Written by task **A52 (harness-gates)**; the stage-provenance block and its
refusal by task **A63 (stage-provenance)**.  :class:`Gate` and :class:`Tooth` are
moved verbatim from ``harness/gates/gates.py``, where task **A56 (driver-renames)**
wrote them; :class:`Check` is moved verbatim from ``harness/gates/selfcheck.py``
(task **A47 (harness-skeleton)**), which ``harness/experiment/artifacts.py`` (task **A51
(harness-artifacts)**) had duplicated as ``StageCheck``.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

#: Where a gate's verdict goes, under the campaign's runs directory.  Bulk run
#: artifacts are untracked by design; the verdict is small and its numbers go
#: into the report.
GATES_SUBPATH = Path("gates")


class GateError(RuntimeError):
    """A refusal to run or to compare.  Never downgraded into a warning."""


class StaleRecordError(GateError):
    """What a stage record says it read is not what is on disk any more."""


# --------------------------------------------------------------------------
# a tooth, and a gate
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

    ``plan_name`` is the label the experiment plan's §3.9 table uses (``G4``,
    ``GR``, …) where the gate is one of the plan's; the promoted harness checks
    carry ``None`` and are listed under their own names.  ``needs_runs`` says
    whether running the gate starts PROCESS, so a caller can say what a button
    press is about to cost.
    """

    name: str
    binds: str
    what_it_proves: str
    body: Callable[..., dict[str, Any]] = field(compare=False, repr=False)
    teeth: tuple[Tooth, ...] = ()
    plan_name: str | None = None
    needs_runs: bool = False
    kind: str = "gate"
    #: Where this gate's own runs live, relative to the records directory.  The
    #: default is a directory named for the gate; a gate that also reads a
    #: shared set of runs names that too.  :meth:`run` surveys the commit every
    #: record under these paths was made at, so that a verdict says **which
    #: runs it read** rather than leaving a reader to assume they are current.
    runs_under: tuple[str, ...] = ()
    #: Gates whose runs or whose verdict this gate reads.  A **declared**
    #: dependency, because the order ``--gate all`` uses is derived from it
    #: rather than hand-sorted: cheapest-first is a preference, and a gate that
    #: reads another's runs has to follow it whatever either costs.
    reads_from: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.teeth:
            raise TypeError(
                f"gate {self.name!r} was constructed with no tooth.  A check "
                f"that has never been shown to fail is an assertion, not a "
                f"measurement (protocol §12): give it at least one Tooth."
            )

    def run(
        self, *, records_dir: Path, teeth: bool = True, resume: bool = False
    ) -> dict[str, Any]:
        """Run the gate, run its teeth, write the verdict, return it.

        ``resume`` reaches the gate's **runs**, not only its comparison.  That
        distinction was a defect: every body hard-coded ``resume=True``, so a
        verdict computed after a change silently read runs made before it while
        the option that was supposed to control that reached nothing.  A gate
        that compares fresh records to stale runs is a zero over a population
        that is not the one named, one level up.
        """
        outcome = self.body(resume=resume)
        provenance = survey_heads(
            [Path(records_dir) / sub for sub in (self.runs_under or (self.name,))]
        )
        stale = provenance["n_records"] > 0 and provenance["heads"] != [git_head()]
        outcome.setdefault("runs_provenance", provenance)
        if stale and not resume:
            outcome["passed"] = False
            outcome["runs_are_not_this_commit's"] = (
                f"the gate read {provenance['n_records']} run record(s) made at "
                f"{provenance['heads']} while this verdict is at {git_head()}, "
                f"and --resume was not asked for.  Without it every run is "
                f"re-made, so a record from another commit means one was kept "
                f"that should not have been"
            )
        elif stale:
            outcome["runs_are_not_this_commit's"] = (
                f"the gate read {provenance['n_records']} run record(s) made at "
                f"{provenance['heads']}, not all at this verdict's "
                f"{git_head()} — which is what --resume asks for, and is "
                f"stated here rather than left to be assumed"
            )
        tooth_records = [t.run() for t in self.teeth] if teeth else []
        all_tripped = all(t["caught"] for t in tooth_records)
        verdict = {
            "gate": self.name,
            "plan_name": self.plan_name,
            "binds": self.binds,
            "what_it_proves": self.what_it_proves,
            "verdict": (
                "PASS" if (outcome.get("passed") and (all_tripped or not teeth)) else "FAIL"
            ),
            "criterion_passed": bool(outcome.get("passed")),
            "resumed": bool(resume),
            "teeth_all_tripped": all_tripped if teeth else None,
            "teeth_run": teeth,
            "generated": _dt.datetime.now().isoformat(timespec="seconds"),
            "tree_git_head": git_head(),
            **{k: v for k, v in outcome.items() if k != "passed"},
            "teeth": tooth_records,
        }
        out = Path(records_dir) / self.name / "gate.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(verdict, indent=2, default=str) + "\n")
        verdict["record"] = str(out)
        return verdict


@dataclass(frozen=True)
class Measurement:
    """A stage that publishes numbers and has nothing to pass.

    Registered beside the gates so that ``registry`` is the one place a reader
    finds every stage, and kept a different type so that nothing can quietly
    read a measurement as a verdict.  It has no teeth **because it has no
    criterion**: a tooth exists to show that a criterion can fail, and there is
    no criterion here.  What guards a measurement is the gate over the same
    records, which is named in ``guarded_by``.
    """

    name: str
    reports: str
    body: Callable[..., dict[str, Any]] = field(compare=False, repr=False)
    guarded_by: str = ""
    needs_runs: bool = False
    printer: Callable[[Mapping[str, Any]], None] | None = field(
        default=None, compare=False, repr=False
    )
    kind: str = "measurement"
    #: Glob patterns, relative to ``records_dir``, naming the **records this
    #: stage reads** — another stage's record, or a gate's verdict.  Declared
    #: here rather than left to the body, because what the stamp is for is a
    #: consumer re-reading those same paths later and refusing when they have
    #: moved: a declaration the framework can re-survey is the whole mechanism,
    #: and a body that stamped its own sources would have to be trusted about
    #: what it left out.  Run records are **not** named here; a stage over runs
    #: carries ``runs_provenance`` instead, which compares populations
    #: (commits and count) rather than files.
    reads_records: tuple[str, ...] = ()

    def run(self, *, records_dir: Path, resume: bool = False) -> dict[str, Any]:
        block = self.body(resume=resume)
        if self.reads_records:
            block = dict(block)
            block["records_read"] = survey_records(
                Path(records_dir), self.reads_records
            )
        out = Path(records_dir) / self.name / "measurements.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(block, indent=2, default=str) + "\n")
        if self.printer is not None:
            self.printer(block)
        print(f"\n  record: {out}")
        block = dict(block)
        block["record"] = str(out)
        return block


def survey_heads(paths: Sequence[Path]) -> dict[str, Any]:
    """Which commit every run record under *paths* was made at.

    A gate's verdict is about the runs it read, and a reader cannot tell from a
    count whether those runs are the ones this commit would produce.  So the
    verdict carries the distinct ``tree_git_head`` values of the records under
    the gate's own run directories, with how many records sit at each.
    """
    by_head: dict[str, int] = {}
    total = 0
    for root in paths:
        for record in sorted(Path(root).rglob("metrics.json")):
            try:
                head = json.loads(record.read_text()).get("tree_git_head")
            except Exception:  # noqa: BLE001 - a half-written record is not a row
                continue
            total += 1
            key = str(head)
            by_head[key] = by_head.get(key, 0) + 1
    return {
        "paths": [str(path) for path in paths],
        "n_records": total,
        "heads": sorted(by_head),
        "records_by_head": by_head,
    }


# --------------------------------------------------------------------------
# what a stage read, and whether it is still what is on disk
# --------------------------------------------------------------------------
#
# :func:`survey_heads` above answers "which commit were the **runs** made at".
# The three functions below answer a different question about a different kind
# of record: a stage that reads **other records** — a gate's verdict, another
# stage's own record — publishes numbers that are only as current as the files
# it read, and nothing in a stage record said which files those were.  The
# failure is silent by construction: the plan's results section is rendered
# from the ``gate_table`` stage record, so a gate re-run after that stage
# leaves the section reproducing the older verdict, byte for byte, with no
# mark anywhere that it is doing so (issue I-22 (a); it happened).
#
# This is the same shape ``analysis.assert_the_tally_read_these_runs`` closed
# for the tally, one level down: there a stage record declares the **run
# population** it summarised and the consumer compares it with its own survey;
# here a stage record declares the **files** it read and the consumer compares
# digests.  It lives in the framework rather than beside either consumer so
# that it is one mechanism and not two — a stage inherits it by declaring
# ``reads_records``, and any reader of any stage record can call the assertion.


def describe_record(path: Path, root: Path) -> dict[str, Any]:
    """One record as a stage read it: which file, which bytes, whose verdict.

    The digest is what the comparison actually turns on — it moves for any
    change, including one a clock and a commit would both miss.  The commit
    and the time are what a refusal *names*, because "this verdict was made at
    another commit" is a sentence a reader can act on and a changed hash is
    not.
    """
    path = Path(path)
    raw = path.read_bytes()
    try:
        record = json.loads(raw)
    except Exception:  # noqa: BLE001 - a half-written record still has bytes
        record = {}
    try:
        relative = str(path.relative_to(Path(root)))
    except ValueError:
        relative = str(path)
    return {
        "path": relative,
        "name": path.parent.name,
        "digest_sha256": hashlib.sha256(raw).hexdigest(),
        "generated": record.get("generated"),
        "tree_git_head": record.get("tree_git_head"),
        "verdict": record.get("verdict"),
    }


def survey_records(root: Path, patterns: Sequence[str]) -> dict[str, Any]:
    """Every record under *root* matching *patterns*, as a stampable block.

    The **patterns** travel with the block, not only the files they matched.
    A survey that carried its matches alone could not tell a consumer that a
    gate has been run *since* — the new verdict would simply be a file nobody
    had ever mentioned.
    """
    root = Path(root)
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for pattern in patterns:
        for path in sorted(root.glob(pattern)):
            if str(path) in seen or not path.is_file():
                continue
            seen.add(str(path))
            records.append(describe_record(path, root))
    return {
        "what_this_is": (
            "the records this stage read: one entry per file, with the bytes "
            "it had, the commit it was made at and its verdict.  A consumer "
            "re-surveys these same patterns and refuses when they have moved"
        ),
        "under": str(root),
        "patterns": list(patterns),
        "n_records": len(records),
        "heads": sorted({str(entry["tree_git_head"]) for entry in records}),
        "records": sorted(records, key=lambda entry: entry["path"]),
    }


def records_read_disagreements(
    block: Mapping[str, Any], root: Path
) -> list[dict[str, Any]]:
    """Where the block's account of what it read differs from what is there.

    Three ways, each named rather than merged into one count: a record that
    exists now and was never read (a gate run since the stage), a record the
    stage read that is gone, and a record whose bytes have changed — the last
    reported with both commits and both times, because *why* it changed is the
    thing a reader needs.
    """
    now = survey_records(Path(root), tuple(block.get("patterns") or ()))
    then = {entry["path"]: entry for entry in (block.get("records") or ())}
    current = {entry["path"]: entry for entry in now["records"]}
    rows: list[dict[str, Any]] = []
    for path in sorted(set(then) | set(current)):
        was, is_now = then.get(path), current.get(path)
        if was is None:
            rows.append(
                {
                    "path": path,
                    "name": is_now["name"],
                    "how": "written after the stage record",
                    "read_commit": None,
                    "read_generated": None,
                    "disk_commit": is_now["tree_git_head"],
                    "disk_generated": is_now["generated"],
                    "disk_verdict": is_now["verdict"],
                }
            )
            continue
        if is_now is None:
            rows.append(
                {
                    "path": path,
                    "name": was["name"],
                    "how": "read by the stage and no longer on disk",
                    "read_commit": was["tree_git_head"],
                    "read_generated": was["generated"],
                    "disk_commit": None,
                    "disk_generated": None,
                    "disk_verdict": None,
                }
            )
            continue
        if was["digest_sha256"] == is_now["digest_sha256"]:
            continue
        how: list[str] = []
        if str(was["tree_git_head"]) != str(is_now["tree_git_head"]):
            how.append("at a different commit from the one the stage read")
        if str(is_now["generated"] or "") > str(was["generated"] or ""):
            how.append("newer than the one the stage read")
        rows.append(
            {
                "path": path,
                "name": is_now["name"],
                "how": " and ".join(how) or "different bytes at the same commit and time",
                "read_commit": was["tree_git_head"],
                "read_generated": was["generated"],
                "read_verdict": was["verdict"],
                "disk_commit": is_now["tree_git_head"],
                "disk_generated": is_now["generated"],
                "disk_verdict": is_now["verdict"],
            }
        )
    return rows


def assert_records_read_are_current(
    stage_record: Mapping[str, Any],
    root: Path,
    *,
    stage: str,
    remedy: str = "",
) -> str:
    """Refuse to use a stage record whose sources have moved under it.

    Returns the sentence a caller prints when they agree, so that the agreeing
    case is stated rather than left to be assumed — the same convention
    ``Gate.run`` follows for its runs.
    """
    block = stage_record.get("records_read")
    if not block:
        raise StaleRecordError(
            f"the {stage} stage record does not say which records it read, so "
            f"nothing can tell whether they are the ones on disk now.  It was "
            f"written before the stage declared its sources: re-run "
            f"`experiment_runner.py --measure {stage}`."
        )
    rows = records_read_disagreements(block, Path(root))
    if rows:
        lines = [
            f"  {row['name']}: {row['how']} — the stage read "
            f"{str(row['read_commit'])[:8] or 'nothing'} generated "
            f"{row['read_generated']}, disk has "
            f"{str(row['disk_commit'])[:8] or 'nothing'} generated "
            f"{row['disk_generated']}"
            + (
                f" (verdict {row.get('read_verdict')} → {row.get('disk_verdict')})"
                if row.get("read_verdict") != row.get("disk_verdict")
                else ""
            )
            for row in rows
        ]
        raise StaleRecordError(
            f"the {stage} stage record does not describe the records on disk: "
            f"{len(rows)} disagreement(s) against the {block['n_records']} "
            f"record(s) it read.\n"
            + "\n".join(lines)
            + "\n  Using it would publish the older record without saying so.  "
            + (remedy or f"Re-run `experiment_runner.py --measure {stage}`.")
        )
    return (
        f"the {stage} stage record read {block['n_records']} record(s) at "
        f"{block['heads']}, and every one of them is byte-identical to what is "
        f"on disk now"
    )


def git_head() -> str | None:
    """The commit of the tree this package lives in, or None."""
    here = Path(__file__).resolve().parents[2]
    try:
        return subprocess.run(
            ["git", "-C", str(here), "rev-parse", "HEAD"],
            check=True,
            stdout=subprocess.PIPE,
            text=True,
        ).stdout.strip()
    except Exception:  # noqa: BLE001 - context only
        return None


# --------------------------------------------------------------------------
# a check, and its promotion into a gate
# --------------------------------------------------------------------------


@dataclass
class Check:
    """One check: what it binds, over how many things, and its teeth.

    Three fields are not optional decoration: ``population`` says what the
    numbers are over, ``n_compared`` is the denominator every count needs, and
    ``teeth`` records the deliberate breaks — a check whose failure mode has
    never been exercised is an assertion, not a measurement (orchestration
    protocol §12, trap T11).
    """

    name: str
    binds: str
    passed: bool = True
    population: str = ""
    n_compared: int = 0
    n_mismatched: int = 0
    detail: list[str] = field(default_factory=list)
    teeth: list[dict[str, Any]] = field(default_factory=list)

    def fail(self, message: str) -> None:
        self.passed = False
        self.n_mismatched += 1
        self.detail.append(message)

    def note(self, message: str) -> None:
        self.detail.append(message)

    def tooth(self, name: str, caught: bool, message: str) -> None:
        """Record a deliberate break and whether the check caught it."""
        self.teeth.append({"tooth": name, "caught": bool(caught), "what": message})
        if not caught:
            self.passed = False
            self.detail.append(f"TOOTH DID NOT TRIP: {name} — {message}")

    def as_record(self) -> dict[str, Any]:
        return {
            "check": self.name,
            "binds": self.binds,
            "verdict": "PASS" if self.passed else "FAIL",
            "population": self.population,
            "n_compared": self.n_compared,
            "n_mismatched": self.n_mismatched,
            "detail": self.detail,
            "teeth": self.teeth,
        }


def report_lines(check_record: Mapping[str, Any], *, indent: str = "  ") -> list[str]:
    """One check's verdict as lines, teeth included."""
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


def gate_from_check(
    *,
    name: str,
    binds: str,
    what_it_proves: str,
    run: Callable[..., Check],
    teeth: Sequence[str],
    needs_runs: bool = False,
    runs_under: tuple[str, ...] = (),
) -> Gate:
    """Promote a ``Check``-shaped criterion into the gate framework, unchanged.

    The criterion is **not** restated: ``run`` is the same function that
    produced the check before the promotion, so the numbers a promoted gate
    reports are the numbers the check reported.  What the promotion adds is a
    verdict record on disk, a place in :func:`harness.gates.gates.registry`, and a
    *declared* tooth list.

    ``teeth`` names the deliberate breaks the criterion must exercise.  Each
    becomes a :class:`Tooth` that reads its own result out of the check the body
    just ran — so a declared tooth the criterion no longer runs is a tooth that
    DID NOT TRIP, and the gate fails rather than quietly losing it.  Any tooth
    the criterion runs that is **not** declared is reported too, under
    ``undeclared_teeth``, and fails the criterion: a check that grew a tooth
    nobody declared is a check whose declaration has stopped describing it.
    """
    if not teeth:
        raise TypeError(
            f"promoted check {name!r} declares no tooth.  A check that has "
            f"never been shown to fail is an assertion, not a measurement "
            f"(protocol §12)."
        )
    held: dict[str, Check] = {}
    declared = tuple(teeth)

    def body(*, resume: bool = False) -> dict[str, Any]:
        check = run(resume=resume)
        held["check"] = check
        ran = {t["tooth"] for t in check.teeth}
        undeclared = sorted(ran - set(declared))
        return {
            "passed": bool(check.passed) and not undeclared,
            "criterion": "promoted unchanged from the harness's own check",
            "population": check.population,
            "n_compared": check.n_compared,
            "n_mismatched": check.n_mismatched,
            "detail": list(check.detail),
            "declared_teeth": list(declared),
            "n_teeth_run_by_the_criterion": len(check.teeth),
            "undeclared_teeth": undeclared,
            "undeclared_teeth_note": (
                "a tooth the criterion runs that this gate does not declare: "
                "the declaration has stopped describing the check, so the "
                "gate fails rather than losing the difference"
                if undeclared
                else "none"
            ),
        }

    def reader(tooth_name: str) -> Callable[[], tuple[bool, str]]:
        def look() -> tuple[bool, str]:
            check = held.get("check")
            if check is None:
                return False, (
                    "the criterion did not run, so its teeth were never "
                    "exercised"
                )
            for entry in check.teeth:
                if entry["tooth"] == tooth_name:
                    return bool(entry["caught"]), str(entry["what"])
            return False, (
                f"the criterion ran no tooth named {tooth_name!r}; a declared "
                f"tooth that the check no longer exercises is a tooth that did "
                f"not trip, not one fewer tooth"
            )

        return look

    return Gate(
        name=name,
        binds=binds,
        what_it_proves=what_it_proves,
        body=body,
        needs_runs=needs_runs,
        runs_under=runs_under,
        teeth=tuple(
            Tooth(
                name=tooth_name,
                what="the criterion's own deliberate break, by name",
                must="TRIP",
                check=reader(tooth_name),
            )
            for tooth_name in declared
        ),
    )
