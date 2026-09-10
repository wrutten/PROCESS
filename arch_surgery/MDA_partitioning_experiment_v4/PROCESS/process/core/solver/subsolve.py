"""VP5 (framework hook F9) -- how a model's inner unknown is solved is a
driver choice.

Several PROCESS models determine an unknown *inside* the model, by an
expression or by an inner root-find, and then write the answer into the data
structure.  The optimiser never sees the unknown, never sees the residual it
satisfies, and cannot trade it off against anything else.  Variant point VP5
makes that a **driver** decision rather than a model one: the same residual is
either solved where it has always been solved, or handed to the optimiser as a
design variable with the residual registered as an equality constraint.

The pattern at every site is the one the experiment framework specifies
(``arch_surgery/docs/plans/EXPERIMENT_FRAMEWORK.md`` section 2.5):

1. The residual is extracted into a module-level ``f(unknown, *inputs) ->
   float`` in the model.  **The expression is unchanged** -- this is a pure
   refactor, which is what keeps decisions D5 and D11 satisfied.  Nothing about
   *what* the model computes moves.
2. The inline solve is replaced by :func:`subsolve`, whose default path
   performs *exactly* the original call, with the original tolerances and the
   original failure policy.
3. When the site is lifted, :func:`subsolve` returns the value the optimiser
   put in the data structure, and the residual extracted in step 1 becomes the
   body of the matching constraint equation.

**The default path is upstream's.**  With ``PROCESS_ARCH_LIFT`` unset,
:data:`LIFTED_SITES` is empty, :data:`LIFT_ENABLED` is ``False``, and
:func:`subsolve` calls straight through to the original solve.  The selection
is resolved **once at import**, never per call -- the framework's design rule
for a variant point.  Nothing here touches a float on the default path.

Selection
---------
``PROCESS_ARCH_LIFT`` is a comma-separated list of site names::

    PROCESS_ARCH_LIFT=burn_time

An unrecognised site name is an import-time error, not a silent no-op: a
misspelled arm that quietly runs the baseline is the failure mode that makes a
whole measurement worthless.

Sites
-----
``burn_time``
    ``process.models.pulse`` -- the flat-top burn time
    ``times.t_plant_pulse_burn``, determined by the volt-seconds the CS and PF
    coils have available for burn.  Registry allocation: iteration variable
    178, constraint 93 (``arch_surgery/docs/plans/REGISTRY_ALLOCATIONS.md``).
"""

from __future__ import annotations

import os

__all__ = [
    "BURN_TIME_IXC",
    "LIFTED_SITES",
    "LIFT_ENABLED",
    "PIN_BURN_TIME",
    "PIN_ENABLED",
    "SITES",
    "SITE_BURN_TIME",
    "assert_burn_time_pinned",
    "is_lifted",
    "subsolve",
]

#: The burn-time site: ``times.t_plant_pulse_burn`` in ``process.models.pulse``.
SITE_BURN_TIME = "burn_time"

#: Every site name this build knows about.  A site appears here as soon as its
#: model routes its solve through :func:`subsolve`, whether or not any queued
#: task lifts it.
SITES: tuple[str, ...] = (SITE_BURN_TIME,)

_raw = os.environ.get("PROCESS_ARCH_LIFT", "").strip()

#: Sites this run takes from the design vector instead of solving in the model.
LIFTED_SITES: frozenset[str] = frozenset(
    part for part in (token.strip() for token in _raw.split(",")) if part
)

_unknown = tuple(sorted(LIFTED_SITES.difference(SITES)))
if _unknown:
    raise RuntimeError(
        f"PROCESS_ARCH_LIFT={_raw!r} names {list(_unknown)}, which are not "
        f"recognised VP5 sites; expected a comma-separated subset of {SITES} "
        f"(or unset to leave every site solved in its model)."
    )

#: True when any site is lifted.  With the lift off this guards the only branch
#: the variant point adds, so the default path is upstream's.
LIFT_ENABLED: bool = bool(LIFTED_SITES)


def is_lifted(site: str) -> bool:
    """Whether *site*'s unknown comes from the design vector in this run."""
    return LIFT_ENABLED and site in LIFTED_SITES


# --------------------------------------------------------------------------
# A34 (pin instrument): the burn-time coupling held at a supplied value.
#
# Phase A of the V2 experiment measures the per-call MDA cost of the lifted
# architecture **without an optimiser** (EXPERIMENT_PLAN.md section 3).  In
# the lifted architecture the optimiser holds the burn time fixed within any
# single evaluation; with no optimiser present, something else has to own the
# variable.  ``PROCESS_ARCH_PIN_BURN_TIME=<float>`` is that owner: the value
# is written into ``times.t_plant_pulse_burn`` at ``Caller`` initialisation
# (caller.py), and nothing in the solve phase may overwrite it.
#
# The guarantee is structural, and it rests on the lift: with
# ``PROCESS_ARCH_LIFT=burn_time``, ``subsolve`` returns the data-structure
# value instead of running the model's own solve, so ``Pulse.run``'s write is
# the identity.  Without the lift the model would overwrite the pin on the
# first sweep and the pin would be a wish, which is why pin-without-lift is
# an import-time error rather than a value that quietly loses.  The second
# possible writer -- the design-vector injection at the head of every sweep
# -- exists only on a deck that names ``ixc = 178``, and ``Caller`` refuses
# that combination (the pin replaces the optimiser as the variable's owner;
# two owners is a fight the sweep head would win silently).
#
# The guarantee is also **checked, not trusted**: ``assert_burn_time_pinned``
# runs at the end of every model sweep and raises on any bit-level change.
# A tripwire rather than a re-pin, deliberately -- re-forcing the value each
# sweep would mask an unknown writer instead of naming it.
#
# Unset -- the default -- ``PIN_ENABLED`` is False, every call site's guard
# is dead, and behaviour is byte-identical (gated, protocol 12; never
# asserted).
# --------------------------------------------------------------------------

#: Iteration-variable number of the lifted burn time
#: (``arch_surgery/docs/plans/REGISTRY_ALLOCATIONS.md``).
BURN_TIME_IXC = 178

_pin_raw = os.environ.get("PROCESS_ARCH_PIN_BURN_TIME", "").strip()

#: The pinned burn time in seconds, or ``None`` (the default: no pin).
#: Accepts a decimal literal or -- so a measured value can be passed with no
#: round-trip loss -- a C99 hex float literal (``float.hex()`` output).
PIN_BURN_TIME: float | None = (
    None
    if not _pin_raw
    else float.fromhex(_pin_raw)
    if _pin_raw.lower().lstrip("+-").startswith("0x")
    else float(_pin_raw)
)

#: True when the burn time is pinned.  Guards every branch the instrument
#: adds, so the default path is upstream's.
PIN_ENABLED: bool = PIN_BURN_TIME is not None

if PIN_ENABLED and not is_lifted(SITE_BURN_TIME):
    raise RuntimeError(
        f"PROCESS_ARCH_PIN_BURN_TIME={_pin_raw!r} is set without "
        f"PROCESS_ARCH_LIFT={SITE_BURN_TIME}.  The pin's guarantee that the "
        f"solve phase never overwrites the value rests on the lift making "
        f"Pulse's burn-time write the identity; without it the model would "
        f"overwrite the pin on the first sweep.  Set "
        f"PROCESS_ARCH_LIFT={SITE_BURN_TIME}, or unset the pin."
    )


def assert_burn_time_pinned(data) -> None:
    """Raise if the pinned burn time has moved.  Bit comparison, no tolerance.

    Called (guarded on :data:`PIN_ENABLED`) at the end of every model sweep,
    so an overwrite is named at the sweep that made it rather than surfacing
    as a quietly wrong measurement.
    """
    v = float(data.times.t_plant_pulse_burn)
    if v != PIN_BURN_TIME:
        raise RuntimeError(
            f"the pinned burn time was overwritten during the solve phase: "
            f"PROCESS_ARCH_PIN_BURN_TIME={PIN_BURN_TIME!r} "
            f"({PIN_BURN_TIME.hex()}) but times.t_plant_pulse_burn now holds "
            f"{v!r} ({v.hex()}).  Some writer other than the pin owns this "
            f"variable; that is a finding, not a condition to re-pin over."
        )


def subsolve(residual, x0, args, *, site: str, direct):
    """Resolve one model unknown, either in the model or from the design vector.

    Parameters
    ----------
    residual :
        The site's residual, ``f(unknown, *args) -> float``, zero exactly when
        *unknown* is the value the model would have computed.  It is the
        function the matching constraint equation evaluates, and the function
        an iterative arm would root-find.  It is **not** called on either path
        below; it is part of the seam's contract, so that the residual and the
        solve can never drift apart unnoticed.
    x0 :
        The unknown's current value in the data structure.  When the site is
        lifted this is what the optimiser put there, and it is what is
        returned.  For a site whose original solve was iterative it is also the
        initial guess ``direct`` would use.
    args :
        The residual's remaining arguments -- the model inputs the unknown is
        determined by -- and the positional arguments passed to *direct*.
    site :
        One of :data:`SITES`.
    direct :
        The model's own solve, called as ``direct(*args)``.  This is the
        original call, unchanged: same expression or same root-finder, same
        tolerances, same failure policy.

    Returns
    -------
    float
        ``direct(*args)`` on the default path; ``x0`` when *site* is lifted.
    """
    if LIFT_ENABLED and site in LIFTED_SITES:
        return x0
    return direct(*args)
