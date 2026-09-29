"""The framework every other subpackage stands on.

What a gate, a tooth, a check and a measurement *are* (``framework``); every
declared setting (``config``); the failure taxonomy (``failure``); the
interpreter, tree and git stamps (``provenance``); the run-record schema and
its completeness contract (``records``); and the process pool that makes a run
in its own directory and decides whether an existing record may be kept
(``pool``).

Nothing here knows what the experiment measures.  The grouping is by *who
imports it and when it runs*, not by subject: every other subpackage imports
this one, and this one imports none of them.
"""
