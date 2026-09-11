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

Written by task **A52 (harness-gates)**.  :class:`Gate` and :class:`Tooth` are
moved verbatim from ``harness/gates.py``, where task **A56 (driver-renames)**
wrote them; :class:`Check` is moved verbatim from ``harness/selfcheck.py``
(task **A47 (harness-skeleton)**), which ``harness/artifacts.py`` (task **A51
(harness-artifacts)**) had duplicated as ``StageCheck``.
"""

from __future__ import annotations

import datetime as _dt
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
    body: Callable[[], dict[str, Any]] = field(compare=False, repr=False)
    teeth: tuple[Tooth, ...] = ()
    plan_name: str | None = None
    needs_runs: bool = False
    kind: str = "gate"

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
            "plan_name": self.plan_name,
            "binds": self.binds,
            "what_it_proves": self.what_it_proves,
            "verdict": (
                "PASS" if (outcome.get("passed") and (all_tripped or not teeth)) else "FAIL"
            ),
            "criterion_passed": bool(outcome.get("passed")),
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
    body: Callable[[], dict[str, Any]] = field(compare=False, repr=False)
    guarded_by: str = ""
    needs_runs: bool = False
    printer: Callable[[Mapping[str, Any]], None] | None = field(
        default=None, compare=False, repr=False
    )
    kind: str = "measurement"

    def run(self, *, records_dir: Path) -> dict[str, Any]:
        block = self.body()
        out = Path(records_dir) / self.name / "measurements.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(block, indent=2, default=str) + "\n")
        if self.printer is not None:
            self.printer(block)
        print(f"\n  record: {out}")
        block = dict(block)
        block["record"] = str(out)
        return block


def git_head() -> str | None:
    """The commit of the tree this package lives in, or None."""
    here = Path(__file__).resolve().parent.parent
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
    run: Callable[[], Check],
    teeth: Sequence[str],
    needs_runs: bool = False,
) -> Gate:
    """Promote a ``Check``-shaped criterion into the gate framework, unchanged.

    The criterion is **not** restated: ``run`` is the same function that
    produced the check before the promotion, so the numbers a promoted gate
    reports are the numbers the check reported.  What the promotion adds is a
    verdict record on disk, a place in :func:`harness.gates.registry`, and a
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

    def body() -> dict[str, Any]:
        check = run()
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
