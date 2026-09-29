"""Every gate, every tooth, and the harness's own self-checks.

The gate registry and the gates that need no dedicated module (``gates``), the
gates that do (``gate_composition``, ``gate_entry``,
``gate_prime``, ``gate_records``, ``gate_tally``), the reproduction gate and its
committed reference (``reproduction``, ``reference``) and the self-check suite
(``selfcheck``).

A gate reads records; it never decides what a record means.  That is
``measurement``'s job, and this subpackage imports it rather than the other way
round.
"""
