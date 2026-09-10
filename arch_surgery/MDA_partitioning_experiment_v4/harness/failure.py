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

Written by task **A50 (harness-run)**; the taxonomy is the harness plan's §4.4
and EXPERIMENT_PLAN.md §3.4.
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

#: Fragments that mark a driver refusal — the driver declining a combination
#: rather than failing at one.  Each is a sentence the driver itself writes.
REFUSAL_MARKERS: tuple[str, ...] = (
    "is not a recognised",
    "must refuse rather than",
    "refuse rather than",
    "two owners",
    "which is only correct once",
    "does not exist.  There",
    "which is not present",
    "must not be guessed",
    "does not rebuild",
)


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
    name = type(exception).__name__
    text = str(exception)
    if name == "ModuleSolveFailure":
        return "unconverged"
    if all(marker in text for marker in UPSTREAM_PASS_CAP_MARKERS):
        return "unconverged-at-cap"
    if any(marker in text for marker in REFUSAL_MARKERS):
        return "refused"
    return "crashed"
