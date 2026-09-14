"""Everything a measurement subprocess imports.

The three child entry points (``evaluate``, ``optimise``, ``census``) and what
they load: the in-child machinery (``child``), the coupling-state predicate
layer (``predicate``), the seeded delta stream (``perturb``), the data-structure
snapshot (``data_structure``) and the post-solve derivation (``postsolve``).

**This subpackage is exactly the set the harness implementation plan's
amendment 13, rule (vi) forbids editing while any measurement run executes** —
the child imports these modules, so an edit here corrupts a population that is
half-measured, and rule (v) already forbids the commit.  One module of that set
is *not* here: ``harness/ystate.py`` stays at the top of the package because the
copied driver reaches it by the literal path
``parents[4] / "harness" / "ystate.py"`` (``PROCESS/process/core/solver/
module_solve.py``), and that literal is itself asserted by
``PROCESS/copy_gates.py``.  It belongs to this set for the purpose of rule (vi).
"""
