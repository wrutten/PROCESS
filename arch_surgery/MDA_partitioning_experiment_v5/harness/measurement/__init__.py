"""What the records mean: the declared constructions, the tally, the paper's document.

The constructions of the experiment plan in one place (``stats``), the tables
that cannot be emitted without a caption (``tables``), the tally's source
declarations and its two stages (``tally``, ``tally_evaluation``,
``tally_optimisation``) and the one document generator for the paper
(``paper_tables``).

The second implementation (``analysis``) and the report renderer
(``plan_tables``) of V4 were removed under V5 list item 10; the independent
check of the paper's cells is the short script ``paper_cells_recount.py``
beside the runner, which imports nothing from this package.
"""
