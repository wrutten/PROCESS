"""Phase A of the MDA partition experiment: fixed-point architectures, no optimiser.

Nothing in this package imports PROCESS at module scope, so it can be imported
by an analysis script that never builds a data structure.  The one module that
does need PROCESS -- :mod:`replay` -- imports it inside functions.
"""
