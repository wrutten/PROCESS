"""Module containing solver routines

**This experiment's copy only.**  Everything below the first section divider is
an addition made by the architecture experiment (task A56 (driver-renames)) and
is not in upstream PROCESS.  It is here, in the package's own ``__init__``,
because it is the one module every architecture-switched file in this package
already imports through, and because a guard that runs late is a guard a stale
caller can get past.
"""

import os

# ---------------------------------------------------------------------------
# The typed refusal
# ---------------------------------------------------------------------------


class ArchitectureRefusal(RuntimeError):
    """The driver declining an architecture setting rather than failing at one.

    Every refusal this experiment's driver makes about *how the models are
    arranged* -- an unrecognised switch name, an illegal value, two owners for
    one quantity, a missing committed artifact, a retired name still set -- is
    this class.  Nothing about the physics raises it, and neither does a solve
    that simply did not converge: those are a different kind of event and are
    counted in a different row of the run taxonomy.

    **Why a class and not a message.**  The measurement harness has to tell a
    refused run (the guards working) from a crashed one (something broken).
    Until this class existed it did so by matching fragments of the sentences
    the driver writes, which works and was checked, but puts a reworded message
    in the wrong row of the failure table.  A reader of the harness's
    ``failure.py`` will find the text match still there, marked as the fallback
    it now is.
    """


# ---------------------------------------------------------------------------
# Retired switch names
# ---------------------------------------------------------------------------
#
# A stale caller is the hazard this guards.  Before the rename an unrecognised
# ``PROCESS_ARCH_*`` name was simply ignored, so a script still setting the old
# name would produce a *successful* run of a *different* arrangement under the
# right name, with no error anywhere -- the same shape as the two standing
# traps of this project (a working tree that does not redirect the editable
# install; a version string that agrees with the wrong commit).  The names
# below therefore raise, and the message names the switch that replaced each.
#
# The check runs at **package import**, which is as early as it can run: every
# module of this package that reads an architecture switch is inside it, and
# the one model that reaches for a driver seam imports through it too.

#: Name a caller may still be setting -> what to set instead.
RETIRED_SWITCHES: dict[str, str] = {
    "PROCESS_ARCH_MODULE_SOLVE": (
        "PROCESS_ARCH_MDA=flat|partitioned (unset for upstream's own loop)"
    ),
    "PROCESS_ARCH_OUTER": (
        "nothing: the partitioned schedule runs exactly once, which is what "
        "PROCESS_ARCH_MDA=partitioned now means.  The repeated schedule "
        "('verify') is gone -- its verification pass triggered a further pass "
        "zero times in 91 888 measured evaluations"
    ),
    "PROCESS_ARCH_INNER_TAU": (
        "PROCESS_ARCH_TAU: there is one tolerance for every converger, the "
        "flat loop and each block loop alike"
    ),
    "PROCESS_ARCH_SEQUENCE": "PROCESS_ARCH_ARRANGEMENT_NODE",
    "PROCESS_ARCH_PRIME": "PROCESS_ARCH_ARRANGEMENT_METHOD",
    "PROCESS_ARCH_HOIST": "PROCESS_ARCH_DEFER_PER_CALL",
    "PROCESS_ARCH_POST_SOLVE": "PROCESS_ARCH_DEFER_PER_RUN",
    "PROCESS_ARCH_LIFT": (
        "PROCESS_ARCH_BURN_TIME_OWNER=optimiser (the burn time as a design "
        "variable), or =constant:<hex float> (a fixed value owning it)"
    ),
    "PROCESS_ARCH_PIN_BURN_TIME": (
        "PROCESS_ARCH_BURN_TIME_OWNER=constant:<hex float>, which takes the "
        "burn time out of the model and hands it to that constant in one "
        "setting"
    ),
    "PROCESS_ARCH_YSTATE": "PROCESS_ARCH_COUPLING_STATE",
    "PROCESS_ARCH_WRITESET": "PROCESS_ARCH_WRITE_SETS",
}


def assert_no_retired_switches(environ=None) -> None:
    """Raise if a retired switch name is set, naming what replaced it.

    Idempotent and cheap: eleven dictionary lookups, and nothing is allocated
    on the path that finds nothing.  Called at the import of this package, so
    it binds every entry point into the driver.
    """
    environ = os.environ if environ is None else environ
    present = [name for name in RETIRED_SWITCHES if name in environ]
    if not present:
        return
    lines = "\n".join(
        f"  {name}={environ[name]!r}  ->  set {RETIRED_SWITCHES[name]}"
        for name in sorted(present)
    )
    raise ArchitectureRefusal(
        "the environment sets architecture switch name(s) this driver has "
        "retired:\n"
        f"{lines}\n"
        "They are refused rather than ignored: an ignored switch produces a "
        "successful run of a different arrangement under the right name, "
        "which is a wrong answer with no symptom."
    )


assert_no_retired_switches()
