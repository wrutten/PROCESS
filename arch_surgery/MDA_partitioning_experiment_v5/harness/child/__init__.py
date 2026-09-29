"""Everything a measurement subprocess imports.

The three child entry points (``evaluate``, ``optimise``, ``census``) and what
they load: the in-child machinery (``child``), the coupling-state predicate
layer (``predicate``), the seeded delta stream (``perturb``), the data-structure
snapshot (``data_structure``) and the post-solve derivation (``postsolve``).

**This subpackage is exactly the set the harness implementation plan's
amendment 13, rule (vi) forbids editing while any measurement run executes** —
the child imports these modules, so an edit here corrupts a population that is
half-measured, and rule (v) already forbids the commit.  The coupling-state
module ``ystate`` is here too: the copied driver reaches it by the literal path
``parents[4] / "harness" / "child" / "ystate.py"`` (``PROCESS/process/core/
solver/module_solve.py``), a permitted edit ``PROCESS/copy_gates.py`` asserts
and ``PROCESS/PROVENANCE.json`` records (task A66, carried by A73 under D27).
"""
