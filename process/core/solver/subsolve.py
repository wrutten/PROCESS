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
    "LIFTED_SITES",
    "LIFT_ENABLED",
    "SITES",
    "SITE_BURN_TIME",
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
