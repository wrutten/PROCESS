"""Which taxonomy row an exception belongs in, decided once.

A run that ends badly ends badly in one of a small number of distinguishable
ways, and the distinctions are the point.  The two that have already been
confused in this project:

* **upstream's own analysis loop raising after ten passes** is a *finding about
  the shipped code*, not a broken run.  A displaced entry may reach that cap by
  design.  It has its own row, ``unconverged-at-cap``;
* **a machinery failure** — a wrong interpreter, a missing file, a subprocess
  that never started — is not a physics result.  On 2026-09-04 one was published
  as "the reference arm did not converge", which is a machinery failure wearing
  a physics result's clothes.  It has its own row, ``machinery``.

A **refusal** is a third thing again: the driver declining to run a combination
that would measure something other than the arm it is named after — a constant
owning the burn time while the model still solves for it, an input file that
names the same variable twice, a deferral asked for without the artifact that
says which nodes.  Those are the guards working, and a campaign that counted
them as crashes would report the guards as failures.

**How a refusal is recognised, and how it used to be.**  The driver raises a
typed refusal — ``process.core.solver.ArchitectureRefusal`` — for every refusal
of an architecture setting, and that **type** is what classifies a run here.
Before it existed the only evidence was the text of the message, matched on
distinctive fragments; that worked, and was checked, but it puts a *reworded*
refusal in the wrong row of the failure table.  The text match was kept as a
fallback for records made by a tree that predates the typed refusal; every run
asserts the copy, no such record exists, and the fallback was removed once a
grep of the copy's ``process/core/`` showed every architecture refusal typed
(37 ``raise ArchitectureRefusal`` sites; the ``RuntimeError`` sites that remain
are upstream's pass cap, a tripwire that is a crash by design, and the
superseded probe's own mode guard, which no arm sets).

The type is matched **by name over the exception's inheritance chain**, not by
``isinstance``.  The harness must be able to classify a run without importing
the driver — it runs in the parent process, and the driver is only importable
in the child with the right ``PYTHONPATH`` — and a name walk over
``type(exc).__mro__`` needs neither the import nor the tree.

Written by task **A50 (harness-run)**; the typed classification is
**A56 (driver-renames)**'s.  The taxonomy is the harness plan's §4.4 and
EXPERIMENT_REPORT.md §3.4.
"""

from __future__ import annotations

#: The text upstream's analysis loop raises with when it runs out of passes.
#: Matched on a distinctive fragment rather than the whole sentence, so a
#: reworded message still lands in the right row; if the sentence changes so
#: much that this stops matching, the run lands in ``crashed`` and is visible.
UPSTREAM_PASS_CAP_MARKERS: tuple[str, ...] = (
    "After 10 model evaluations",
    "don't produce idempotent values",
)

#: The driver's typed refusal, by name.  Matched over the exception's whole
#: inheritance chain, so a future subclass of it lands in the same row.
REFUSAL_TYPES: tuple[str, ...] = ("ArchitectureRefusal",)


def classify(exception: BaseException | None, *, status: str) -> str:
    """The taxonomy row for how a run ended.

    *status* is the run's own word for it; *exception* is what it raised, if
    anything.  The order below is the order of specificity: a pass-cap raise is
    an unconverged-at-cap before it is a crash, and a refusal is a refusal
    before it is either.
    """
    if status == "ok":
        return "ok"
    if status == "timeout":
        return "timeout"
    if status == "no_record":
        return "machinery"
    if exception is None:
        return "crashed" if status == "crashed" else status
    chain = type_names(exception)
    text = str(exception)
    if "ModuleSolveFailure" in chain:
        return "unconverged"
    # The type first: a refusal is a refusal whatever it says.
    if any(name in chain for name in REFUSAL_TYPES):
        return "refused"
    if all(marker in text for marker in UPSTREAM_PASS_CAP_MARKERS):
        return "unconverged-at-cap"
    return "crashed"


def type_names(exception: BaseException) -> tuple[str, ...]:
    """The exception's class and every class it inherits from, by name.

    Names rather than classes, because the harness classifies a run in the
    parent process where the driver is not importable.
    """
    return tuple(cls.__name__ for cls in type(exception).__mro__)
