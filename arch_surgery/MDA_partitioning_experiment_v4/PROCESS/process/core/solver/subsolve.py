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
3. When the site is out of the loop, :func:`subsolve` returns the value its new
   owner put in the data structure, and the residual extracted in step 1
   becomes the body of the matching constraint equation.

**The default path is upstream's.**  With ``PROCESS_ARCH_BURN_TIME_OWNER``
unset the loop owns the burn time, :data:`SITES_OUT_OF_LOOP` is empty,
:data:`BURN_TIME_OUT_OF_LOOP` is ``False``, and :func:`subsolve` calls straight
through to the original solve.  The selection is resolved **once at import**,
never per call -- the framework's design rule for a variant point.  Nothing
here touches a float on the default path.

Selection
---------
``PROCESS_ARCH_BURN_TIME_OWNER`` names **who owns the burn time**, and there are
exactly three answers::

    (unset), or  loop        the model solves for it, every sweep: upstream
    optimiser                it is a design variable; the residual below is
                             registered as an equality constraint and the
                             optimiser trades it off like any other unknown
    constant:0x1.f4p+12      a fixed value owns it, supplied as a C99 hex float

An unrecognised value is an import-time error, not a silent no-op: a misspelled
arm that quietly runs the baseline is the failure mode that makes a whole
measurement worthless.

**Why one switch and not two.**  The two non-default answers are the same
mechanism seen twice.  Both take the burn time out of the model -- the
mechanism this file calls the *lift* -- and they differ only in what holds it
while the analysis runs: the optimiser, or a number.  Expressed as two switches
they could be set inconsistently, and the pair "a constant owns it, but the
model still solves for it" had to be refused explicitly, because the model
would overwrite the constant on the first sweep and the constant would be a
wish.  As one switch that combination cannot be written down.  The refusal it
replaces is recorded in the change log of the task that folded them.

**One quantity, not a list.**  The earlier form took a comma-separated list of
sites, because the seam is general: any model unknown can be routed through
:func:`subsolve`.  Exactly one is, and this experiment lifts exactly one, so
the switch names the quantity rather than enumerating it.  **If a second
quantity is ever taken out of the loop, the general list form has to come back**
-- a second single-quantity switch would multiply, and the arms would stop being
one column of a matrix each.

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

from process.core.solver import ArchitectureRefusal

__all__ = [
    "BURN_TIME_CONSTANT",
    "BURN_TIME_IXC",
    "BURN_TIME_OUT_OF_LOOP",
    "BURN_TIME_OWNER",
    "CONSTANT_OWNS_BURN_TIME",
    "OWNERS",
    "SITES",
    "SITES_OUT_OF_LOOP",
    "SITE_BURN_TIME",
    "assert_burn_time_constant",
    "is_out_of_loop",
    "subsolve",
]

#: The burn-time site: ``times.t_plant_pulse_burn`` in ``process.models.pulse``.
SITE_BURN_TIME = "burn_time"

#: Every site name this build knows about.  A site appears here as soon as its
#: model routes its solve through :func:`subsolve`, whether or not any queued
#: task takes it out of the loop.
SITES: tuple[str, ...] = (SITE_BURN_TIME,)

#: The three owners the burn time can have.  ``constant`` is spelt
#: ``constant:<hex float>`` in the environment; the value is the constant.
OWNERS: tuple[str, ...] = ("loop", "optimiser", "constant")

_CONSTANT_PREFIX = "constant:"

_raw = os.environ.get("PROCESS_ARCH_BURN_TIME_OWNER", "").strip()


def _parse_owner(raw: str) -> tuple[str, float | None]:
    """``(owner, constant)`` from the environment's spelling of it."""
    if not raw or raw == "loop":
        return "loop", None
    if raw == "optimiser":
        return "optimiser", None
    if raw.startswith(_CONSTANT_PREFIX):
        literal = raw[len(_CONSTANT_PREFIX):].strip()
        if not literal.lower().lstrip("+-").startswith("0x"):
            raise ArchitectureRefusal(
                f"PROCESS_ARCH_BURN_TIME_OWNER={raw!r} names a constant owner "
                f"but {literal!r} is not a C99 hex float.  The constant is "
                f"passed as float.hex() output so that a measured value "
                f"survives the round trip exactly; a decimal literal would "
                f"quietly change the value being held."
            )
        try:
            return "constant", float.fromhex(literal)
        except ValueError as exc:
            raise ArchitectureRefusal(
                f"PROCESS_ARCH_BURN_TIME_OWNER={raw!r} does not parse as a hex "
                f"float: {exc}"
            ) from exc
    raise ArchitectureRefusal(
        f"PROCESS_ARCH_BURN_TIME_OWNER={raw!r} is not a recognised owner of "
        f"the burn time; expected 'loop' (or unset -- the model solves for it), "
        f"'optimiser' (a design variable), or 'constant:<hex float>' (a fixed "
        f"value owns it)."
    )


#: Who owns the burn time in this run: ``loop`` (the default, upstream's),
#: ``optimiser`` or ``constant``.
BURN_TIME_OWNER: str

#: The constant that owns it, in seconds, or ``None`` when something else does.
BURN_TIME_CONSTANT: float | None

BURN_TIME_OWNER, BURN_TIME_CONSTANT = _parse_owner(_raw)

#: Sites this run takes out of the model's own solve.  A set, because the seam
#: is general even though this experiment uses one member of it; see the
#: module docstring on what a second member would cost.
SITES_OUT_OF_LOOP: frozenset[str] = (
    frozenset({SITE_BURN_TIME}) if BURN_TIME_OWNER != "loop" else frozenset()
)

#: True when the burn time is out of the loop -- the *lift*, in the mechanism's
#: own vocabulary.  With the loop owning it this guards the only branch the
#: variant point adds, so the default path is upstream's.
BURN_TIME_OUT_OF_LOOP: bool = bool(SITES_OUT_OF_LOOP)


def is_out_of_loop(site: str) -> bool:
    """Whether *site*'s unknown comes from outside the model in this run."""
    return site in SITES_OUT_OF_LOOP


# --------------------------------------------------------------------------
# A constant owning the burn time (the *pin*, in the mechanism's own word).
#
# The evaluation phase of this experiment measures the per-evaluation cost of
# the arrangement in which the burn time is out of the loop, **without an
# optimiser** (EXPERIMENT_PLAN.md section 3).  With the burn time out of the
# loop the optimiser holds it fixed within any single evaluation; with no
# optimiser present, something else has to own it.
# ``PROCESS_ARCH_BURN_TIME_OWNER=constant:<hex float>`` is that owner: the
# value is written into ``times.t_plant_pulse_burn`` at ``Caller``
# initialisation (caller.py), and nothing in the solve phase may overwrite it.
#
# The guarantee is structural, and it rests on the model no longer solving for
# the quantity: with the burn time out of the loop, ``subsolve`` returns the
# data-structure value instead of running the model's own solve, so
# ``Pulse.run``'s write is the identity.  If the model still solved for it the
# constant would be overwritten on the first sweep and would be a wish -- which
# is why the two settings that used to express this separately are now one
# switch, whose ``constant`` value takes the quantity out of the loop by
# construction.  **The refusal that combination needed is therefore gone**, and
# with it the class of run that could ask for it.  The second possible writer
# -- the design-vector injection at the head of every sweep -- exists only on
# an input file that names ``ixc = 178``, and ``Caller`` refuses that
# combination (the constant replaces the optimiser as the owner; two owners is
# a fight the sweep head would win silently).
#
# The guarantee is also **checked, not trusted**: ``assert_burn_time_constant``
# runs at the end of every model sweep and raises on any bit-level change.
# A tripwire rather than a rewrite, deliberately -- re-forcing the value each
# sweep would mask an unknown writer instead of naming it.
#
# With the loop owning the burn time -- the default --
# ``CONSTANT_OWNS_BURN_TIME`` is False, every call site's guard is dead, and
# behaviour is byte-identical (gated, protocol 12; never asserted).
# --------------------------------------------------------------------------

#: Iteration-variable number of the burn time when the optimiser owns it
#: (``arch_surgery/docs/plans/REGISTRY_ALLOCATIONS.md``).
BURN_TIME_IXC = 178

#: True when a constant owns the burn time.  Guards every branch the
#: instrument adds, so the default path is upstream's.
CONSTANT_OWNS_BURN_TIME: bool = BURN_TIME_OWNER == "constant"


def assert_burn_time_constant(data) -> None:
    """Raise if the constant-owned burn time has moved.  Bits, no tolerance.

    Called (guarded on :data:`CONSTANT_OWNS_BURN_TIME`) at the end of every
    model sweep, so an overwrite is named at the sweep that made it rather than
    surfacing as a quietly wrong measurement.

    This is a tripwire on a guarantee, not a refusal of a setting, so it is a
    plain ``RuntimeError``: the run crashed on a finding, and the failure
    taxonomy should say so rather than filing it with the guards that worked.
    """
    v = float(data.times.t_plant_pulse_burn)
    if v != BURN_TIME_CONSTANT:
        raise RuntimeError(
            f"the constant-owned burn time was overwritten during the solve "
            f"phase: PROCESS_ARCH_BURN_TIME_OWNER named "
            f"{BURN_TIME_CONSTANT!r} ({BURN_TIME_CONSTANT.hex()}) but "
            f"times.t_plant_pulse_burn now holds {v!r} ({v.hex()}).  Some "
            f"writer other than that constant owns this variable; that is a "
            f"finding, not a condition to write the value back over."
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
        out of the loop this is what its owner put there, and it is what is
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
        ``direct(*args)`` on the default path; ``x0`` when *site* is out of the
        loop.
    """
    if site in SITES_OUT_OF_LOOP:
        return x0
    return direct(*args)
