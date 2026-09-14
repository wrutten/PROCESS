"""The seeded displacement stream: one implementation, both phases.

Derived from ``arch_surgery/idf_probe/v2_eval_one.py::perturb_factor`` and the
design-vector hook of ``arch_surgery/idf_probe/run_one.py`` (the local
``_factor``), both read at ``9a8defa6``; task **A50 (harness-run)**.  The
previous revision had the same arithmetic written twice — once for each phase —
and reached the evaluation phase by importing a function out of the other
phase's run driver.  Here there is one function and two thin callers.

What a factor is
----------------
``1 + delta * u``, with ``u`` uniform in ``[-1, 1)`` taken from the first eight
bytes of a sha256 of ``"<namespace>|<seed>|<key>"``.  Deterministic, seedable,
and independent of iteration order — which is the property that matters: two
arms with *different-length* design vectors, or with different component
orderings, still give the identical factor to everything they share.

The two streams, and what each is keyed on
------------------------------------------
* the **coupling-state stream** is keyed on the component's **name**
  (``"times.t_plant_pulse_burn"``), so every arm displaces the identical
  component by the identical factor whatever its architecture switches;
* the **design-vector stream** is keyed on the iteration variable's **number**
  (PROCESS's ``ixc`` entry), *not* on its position in the vector, so the lifted
  input file — one variable longer, because the burn time becomes iteration
  variable 178 — gives bit-identical factors to every variable it shares with
  the committed one.

Seed 0 is the unperturbed point in both phases (the house convention: the
displacement is not applied at all, rather than applied with a factor of one).

The two namespace tokens
------------------------
``"a34"`` and ``"a25"`` are **frozen wire values**, not names: they are bytes
fed to a hash, and changing either changes every factor the experiment has ever
drawn and breaks comparability with every recorded run.  They are the task
labels of the tasks that first drew each stream, and they stay exactly as they
were.  The harness plan's §11.1 rule — no task token in a *name* — is about
identifiers; these are data, and the constants below say what they are for.
"""

from __future__ import annotations

import hashlib

#: Hash namespace of the coupling-state stream.  A frozen wire value; see the
#: module docstring.  Drawn first by the task labelled ``a34``.
COUPLING_STATE_NAMESPACE = "a34"

#: Hash namespace of the design-vector stream.  A frozen wire value; see the
#: module docstring.  Drawn first by the task labelled ``a25``.
DESIGN_VECTOR_NAMESPACE = "a25"


def factor(seed: int, key: str, delta: float, *, namespace: str) -> float:
    """``1 + delta * u``, ``u`` uniform in ``[-1, 1)`` from ``(namespace, seed, key)``.

    The one implementation.  *key* is a component name or an iteration-variable
    number rendered as text; *namespace* separates the two streams so that a
    component and a variable that happen to share a key never share a factor.
    """
    digest = hashlib.sha256(f"{namespace}|{seed}|{key}".encode()).digest()
    u = int.from_bytes(digest[:8], "big") / float(1 << 64)  # [0, 1)
    return 1.0 + delta * (2.0 * u - 1.0)


def coupling_state_factor(seed: int, component: str, delta: float) -> float:
    """The factor the coupling-state stream gives one component at one seed."""
    return factor(seed, component, delta, namespace=COUPLING_STATE_NAMESPACE)


def design_vector_factor(seed: int, iteration_variable: int, delta: float) -> float:
    """The factor the design-vector stream gives one iteration variable.

    Keyed on the variable's **number**, so the lifted design vector shares
    every factor with the committed one on the variables they have in common.
    """
    return factor(
        seed, str(int(iteration_variable)), delta,
        namespace=DESIGN_VECTOR_NAMESPACE,
    )


def is_perturbed(seed: int, delta: float | None) -> bool:
    """Whether a run at this ``(seed, delta)`` displaces anything at all.

    Seed 0 is the unperturbed point in both phases even when a displacement
    size is declared: the campaign's first run is the input file's own point,
    and saying so once here keeps the two entry points from disagreeing about
    it — which is exactly the shape of the defect the single composition
    function exists to prevent.
    """
    return bool(delta) and bool(seed)
