"""The experiment harness: what to run, and whether the tree can run it.

Everything the experiment needs to decide *what* to run lives in this
package, and nothing here imports the earlier revisions' machinery.  Read
``README.md`` beside this file first — it explains the experiment, the
vocabulary and the gates in plain language.

The public surface is this module.  Import from it, not from the submodules,
so that a module split later is not a change to every caller::

    from harness import ARMS, default_campaign, env_for, rung
"""

from __future__ import annotations

#: Harness version.  Bumped when the public surface or the record schema
#: changes; stamped into every record so a record says which harness wrote it.
__version__ = "0.5.0"

from .experiment.arms import (  # noqa: F401
    ARMS,
    MATRIX_FIELDS,
    MATRIX_ORDER,
    PHASE_A_ARMS,
    PHASE_B_ARMS,
    PLAN_MATRIX,
    RUNGS,
    Arm,
    Rung,
    active_arms,
    input_file_for,
    env_for,
    matrix,
    matrix_cell,
    rung,
    skipped_arms,
)
from .core.config import (  # noqa: F401
    ARTIFACT_NAMES,
    DRIVER_FIXED_ARTIFACTS,
    EXECUTION_APPROVED,
    Campaign,
    Config,
    Removal,
    artifact_file_names,
    default_campaign,
    default_configurations,
)
from .child.perturb import (  # noqa: F401
    coupling_state_factor,
    design_vector_factor,
    is_perturbed,
)
from .core.pool import (  # noqa: F401
    Job,
    PoolError,
    run_all,
    seed_directory,
)
from .core.provenance import (  # noqa: F401
    BASE_COMMIT,
    ProvenanceError,
    assert_interpreter,
    assert_tree,
    banner,
    git_stamp,
    stamp,
)
from .core.records import (  # noqa: F401
    FAILURE_CLASSES,
    REGIMES,
    RUN_KINDS,
    RecordError,
    assert_usable,
    resolve_path,
)
from .experiment.switches import (  # noqa: F401
    PREVIOUS_ARM_NAMES,
    PROBE_VARIABLES,
    REGISTRY,
    RETIRED_ARM_NAMES,
    Capability,
    Switch,
    SwitchError,
    assert_capable,
    assert_no_retired,
    base_environment,
    clear_all,
    probe,
    retired_names,
    unimplemented,
)

__all__ = [
    "__version__",
    "seed_directory",
    "run_all",
    "resolve_path",
    "is_perturbed",
    "design_vector_factor",
    "coupling_state_factor",
    "assert_usable",
    "RecordError",
    "RUN_KINDS",
    "REGIMES",
    "PoolError",
    "Job",
    "FAILURE_CLASSES",
    "ARMS",
    "ARTIFACT_NAMES",
    "Arm",
    "BASE_COMMIT",
    "Campaign",
    "Capability",
    "Config",
    "DRIVER_FIXED_ARTIFACTS",
    "EXECUTION_APPROVED",
    "MATRIX_FIELDS",
    "MATRIX_ORDER",
    "PHASE_A_ARMS",
    "PHASE_B_ARMS",
    "PLAN_MATRIX",
    "PREVIOUS_ARM_NAMES",
    "PROBE_VARIABLES",
    "REGISTRY",
    "RETIRED_ARM_NAMES",
    "RUNGS",
    "Removal",
    "ProvenanceError",
    "Rung",
    "Switch",
    "SwitchError",
    "active_arms",
    "artifact_file_names",
    "assert_capable",
    "assert_interpreter",
    "assert_no_retired",
    "assert_tree",
    "banner",
    "base_environment",
    "clear_all",
    "input_file_for",
    "default_campaign",
    "default_configurations",
    "env_for",
    "git_stamp",
    "matrix",
    "matrix_cell",
    "probe",
    "retired_names",
    "rung",
    "skipped_arms",
    "stamp",
    "unimplemented",
]
