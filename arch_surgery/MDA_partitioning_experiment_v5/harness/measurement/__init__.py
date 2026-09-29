"""What the records mean: the declared constructions, the tally, the analysis.

The constructions of the experiment plan in one place (``stats``), the tables
that cannot be emitted without a caption (``tables``), the tally's source
declarations and its two stages (``tally``, ``tally_evaluation``,
``tally_optimisation``), the independent recomputation (``analysis``) and the
renderer for the plan's own results section (``plan_tables``).

``analysis`` deliberately imports no part of the tally: it is the second
implementation, and a shared helper would make the agreement between them
vacuous.
"""
