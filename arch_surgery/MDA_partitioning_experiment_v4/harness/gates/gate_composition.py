#!/usr/bin/env python
"""Gate G5 — the arm composed from the matrix is the arm composed switch by switch.

What the gate is about
----------------------
``harness/experiment/arms.py`` transcribes the experiment plan's switch matrix into a table
of frozen dataclasses, and ``env_for`` walks that table to build one arm's
environment.  That is one program reading one table.  If the table were
mis-transcribed, or ``env_for`` combined two fields wrongly, the campaign would
run an arm that is not the arm the plan describes — successfully, with the right
name on every record.  Nothing in the run path could notice: the driver would
resolve whatever it was given, and the arm's *name* is what the tables carry.

So the gate composes the same arm a **second, independent way** — from a
hand-written transcription of the plan's §3.2 column, set switch by switch in
the plan's own order, starting from a cleared environment — and then does two
things with it:

1. compares the two environments **name by name and value by value**, which is
   the cheap half and catches a transcription error outright;
2. **runs both**, on every configuration where the arm is active, and compares
   what came out: the normalised objective as a hex float, the optimiser's exit
   code, its iteration count, the block-sweep histogram and the exit audit's
   maximum as a hex float.  No tolerance is applied to any of them.

The second half is not redundant with the first.  Two environments that agree as
dictionaries still have to reach the driver through ``pool``, and the run is
where the composition becomes a *measurement* rather than a string.

The arm is ``B3`` — the full intervention, the arm with the most switches set
and therefore the one a composition error is most likely to reach.

Criterion inherited, and its source
-----------------------------------
Experiment plan §3.9's G5 row: *"the arm composed from the matrix equals the arm
composed switch by switch: ``norm_objf`` hex, ``ifail``, iterations, outer-pass
histogram, exit audit hex"*, with teeth *"``norm_objf`` hex and
``n_call_models`` teeth"*.  The two teeth are the previous revision's exactly:
append one character to the objective's hex literal, and add one to the model-call
count — each must make the comparison disagree, or the comparison's agreement
means nothing.

The hand-written column, and why it is written out
---------------------------------------------------
:data:`PLAN_COLUMN` is the plan's ``B3`` column, transcribed by hand.  Writing it
out is the point: a table derived from ``arms.py`` would be ``arms.py`` checking
itself.  What is *not* written out is anything that is not a matrix cell — the
tolerance, and the two committed artifact paths — because those are declared
settings rather than matrix cells, and hard-coding a path would make this gate
fail when a file is renamed rather than when a composition is wrong.

Written by task **A52 (harness-gates)**.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from ..experiment import arms as arms_mod
from . import gates as gates_mod
from ..core import pool as pool_mod
from ..core import records as records_mod
from ..experiment import switches as switches_mod
from ..core.config import Campaign, Config
from ..core.framework import Gate, GateError, Tooth

#: The arm this gate composes two ways.
G5_ARM = "B3"

#: The experiment plan's §3.2 column for that arm, transcribed by hand, in the
#: plan's own row order.  ``None`` means the switch is not set at all; a callable
#: means the value is a declared setting or an artifact path rather than a matrix
#: cell, and is resolved from the configuration and the campaign.
#:
#: The rows marked ⁺ in the plan apply on the pulsed configurations only, and
#: the entry says so by taking the configuration.
PLAN_COLUMN: tuple[tuple[str, Any], ...] = (
    # "MDA solve | partitioned"; the block schedule runs one pass, which is
    # what this value means since the repeated schedule was removed.
    ("mda", lambda config, campaign: "partitioned"),
    # "stopping rule | y @ tau" -- the one tolerance of every converger (D23).
    ("tolerance", lambda config, campaign: repr(campaign.tau)),
    # The two committed artifacts that define y and the per-block write sets.
    ("coupling_state", lambda config, campaign: str(config.coupling_state_path)),
    ("write_sets", lambda config, campaign: str(config.write_sets_path)),
    # "arrangement . node (build after physics) | checked".
    ("arrangement_node", lambda config, campaign: "build_after_physics"),
    # "arrangement . method (prime) | checked".
    ("arrangement_method", lambda config, campaign: "fw_geometry"),
    # "deferral per_call | checked".  The value names which read set the
    # deferral is computed against, and the arm reads the lifted input file on
    # a pulsed configuration, so the lifted one.
    (
        "defer_per_call",
        lambda config, campaign: (
            "feedforward_lifted" if config.pulsed else "feedforward"
        ),
    ),
    # "deferral per_run | checked" -- the artifact stamped for the input file
    # this arm actually reads.
    (
        "defer_per_run",
        lambda config, campaign: str(
            config.per_run_artifact(lifted_input_file=config.pulsed)
        ),
    ),
    # "burn-time owner | optimiser", a row the plan marks as applying on the
    # pulsed configurations **only**: where the plant is steady state there is
    # no burn-time coupling and the row does not apply, so the switch is left
    # unset rather than set to the loop.  (Found by this gate failing: writing
    # "loop" there composes a different environment for the same arm, and the
    # plan's own footnote is what settles which is right.)
    (
        "burn_time_owner",
        lambda config, campaign: "optimiser" if config.pulsed else None,
    ),
    # "output-time loop | none".
    ("output_loop", lambda config, campaign: "none"),
    # The convergence ruler.  The plan's row for this arm is the campaign's
    # **default**, and a default is composed by leaving the switch unset: the
    # driver resolves an absent `PROCESS_ARCH_PREDICATE` to the frozen ruler.
    # That is not taken on trust here — the run comparison below includes what
    # the driver *resolved*, read back from the imported modules, so "unset"
    # and "frozen" have to reach the same place or the gate fails.  (Found by
    # this gate failing: the hand-written column set the value explicitly and
    # the matrix left it unset, which is the same arm and a different
    # environment.)
    ("predicate_mode", lambda config, campaign: None),
)

#: What the two runs must agree on, and the path each is read from.  Every one
#: is a count or a bit-comparison; no tolerance is applied or available.
COMPARED: tuple[tuple[str, str], ...] = (
    ("norm_objf_hex", "exact.norm_objf"),
    ("ifail", "mfile.ifail"),
    ("n_solver_iterations", "n_solver_iterations"),
    ("n_call_models", "block_loop_totals.n_call_models"),
    ("block_sweeps", "block_loop_totals.block_sweeps"),
    ("pass_histogram", "block_loop_totals.schedule_passes_per_evaluation"),
    ("sweeps_by_block", "block_loop_totals.sweeps_by_block"),
    ("exit_audit_hex", "exit_audit.residual_max_hex"),
    ("node_calls_solve_phase", "node_calls_solve_phase"),
    # What the driver **resolved**, read back from the imported modules rather
    # than as the harness asked.  This is what makes a switch left unset and a
    # switch set to its default comparable: they compose different environments
    # and must resolve to the same thing.
    ("resolved_switches", "resolved_switches"),
)

_HELD: dict[str, Any] = {}


def switch_by_switch(config: Config, campaign: Campaign) -> dict[str, str | None]:
    """The arm's environment, built one switch at a time from the plan's column.

    Starts from **nothing**: every switch this harness knows about is cleared,
    and then the plan's rows are applied in the plan's order.  That is the same
    discipline ``env_for`` follows and the same discipline the plan states —
    *"every switch cleared first, then set"* — arrived at independently.
    """
    composed: dict[str, str | None] = {
        name: None for name in switches_mod.all_names()
    }
    for term, resolve in PLAN_COLUMN:
        switch = switches_mod.REGISTRY.get(term)
        if switch is None:
            raise GateError(
                f"the plan's column names switch term {term!r}, which the "
                f"switch registry does not know.  A gate composing a term "
                f"nobody implements would compare a typo with itself."
            )
        if switch.driver_name is None:
            raise GateError(
                f"the switch registry gives {term!r} no driver name; this tree "
                f"cannot compose the plan's column"
            )
        value = resolve(config, campaign)
        composed[switch.driver_name] = value  # None means "left unset"
    return composed


def _architecture_only(env: Mapping[str, str]) -> dict[str, str | None]:
    """Just the architecture switches of a composed environment.

    ``env_for`` returns a whole process environment — the interpreter's own
    variables, the tree, the thread pinning.  The comparison is about the
    switches, and comparing the rest would compare the machine.
    """
    return {name: env.get(name) for name in switches_mod.all_names()}


def composition_root(campaign: Campaign) -> Path:
    """Where G5's verdict goes.  Its runs are shared-pool jobs."""
    return Path(campaign.runs_dir) / gates_mod.GATES_SUBPATH / "switch_composition"


def composition_jobs(campaign: Campaign, config: Config) -> tuple[pool_mod.Job, pool_mod.Job]:
    """The two runs: from the matrix, and switch by switch.

    The second is composed by forcing **every** switch name to the hand-built
    value -- present ones set, absent ones removed -- so the run really is
    driven by that dictionary and not by the matrix's with a coincidence on
    top.  Its ``override_env`` is what makes it a **different job identity**
    from the first under the shared pool, although the two compose the same
    environment: the comparison *is* the second run (survey §5), and the
    identity is over what the pool was handed, not over what it produced.
    """
    from_matrix = pool_mod.Job(
        phase="B",
        arm=G5_ARM,
        config=config,
        seed=0,
        regime="unperturbed",
        delta=None,
        run_kind="gate",
    )
    by_switch = pool_mod.Job(
        phase="B",
        arm=G5_ARM,
        config=config,
        seed=0,
        regime="unperturbed",
        delta=None,
        run_kind="gate",
        override_env=switch_by_switch(config, campaign),
    )
    return from_matrix, by_switch


def jobs_read(campaign: Campaign) -> list[pool_mod.Job]:
    """Every job G5 reads: two per configuration where the arm is active."""
    jobs: list[pool_mod.Job] = []
    for config in campaign.configurations:
        if G5_ARM in config.skips:
            continue
        jobs.extend(composition_jobs(campaign, config))
    return jobs


def switch_composition_body(
    campaign: Campaign, *, resume: bool = False
) -> dict[str, Any]:
    """G5: the matrix and the plan's own column compose the same arm."""
    rows: list[dict[str, Any]] = []
    jobs: list[tuple[str, str, pool_mod.Job]] = []
    passed = True
    n_compared = 0
    n_mismatched = 0

    for config in campaign.configurations:
        if G5_ARM in config.skips:
            rows.append({"configuration": config.name, "skipped": config.skips[G5_ARM]})
            continue
        from_matrix = _architecture_only(
            arms_mod.env_for(G5_ARM, config, seed=0, campaign=campaign)
        )
        by_switch = switch_by_switch(config, campaign)
        names = sorted(set(from_matrix) | set(by_switch))
        differing = [n for n in names if from_matrix.get(n) != by_switch.get(n)]
        row: dict[str, Any] = {
            "configuration": config.name,
            "n_switch_names_compared": len(names),
            "n_switch_names_differing": len(differing),
            "differing_switches": {
                n: {"from_the_matrix": from_matrix.get(n), "switch_by_switch": by_switch.get(n)}
                for n in differing
            },
            "set_by_the_matrix": {
                n: v for n, v in sorted(from_matrix.items()) if v is not None
            },
        }
        n_compared += len(names)
        n_mismatched += len(differing)
        rows.append(row)
        if differing:
            row["passed"] = False
            passed = False
            continue
        from_matrix_job, by_switch_job = composition_jobs(campaign, config)
        jobs.append((config.name, "from_the_matrix", from_matrix_job))
        jobs.append((config.name, "switch_by_switch", by_switch_job))

    pool_mod.run_all([job for *_r, job in jobs], campaign, resume=resume)

    by_key = {(c, label): job for c, label, job in jobs}
    for row in rows:
        if "skipped" in row or row.get("passed") is False:
            continue
        name = row["configuration"]
        a = records_mod.read(by_key[(name, "from_the_matrix")].outdir)
        b = records_mod.read(by_key[(name, "switch_by_switch")].outdir)
        values: dict[str, Any] = {}
        differing_values: list[str] = []
        for label, path in COMPARED:
            left = records_mod.resolve_path(a, path)
            right = records_mod.resolve_path(b, path)
            values[label] = {"from_the_matrix": left, "switch_by_switch": right}
            if left != right:
                differing_values.append(label)
        row["statuses"] = [a.get("status"), b.get("status")]
        row["values"] = values
        row["n_values_compared"] = len(COMPARED)
        row["n_values_differing"] = len(differing_values)
        row["differing_values"] = differing_values
        n_compared += len(COMPARED)
        n_mismatched += len(differing_values)
        row["checks"] = {
            "both_runs_finished": row["statuses"] == ["ok", "ok"],
            "every_compared_value_identical": not differing_values,
        }
        row["passed"] = all(row["checks"].values())
        passed = passed and row["passed"]

    _HELD["rows"] = rows
    live = [r for r in rows if "skipped" not in r]
    return {
        "passed": passed,
        "criterion": (
            "the arm composed from the matrix equals the arm composed switch "
            "by switch — every switch name and value, and then the two runs' "
            "objective hex, exit code, iterations, block-sweep histogram, "
            "node calls and exit-audit hex, with no tolerance on any of them"
        ),
        "criterion_source": (
            "the experiment plan §3.9's G5 row, restated here; the second "
            "composition is a hand transcription of the plan's §3.2 column, "
            "not a second reading of arms.py"
        ),
        "population": (
            f"{len(live)} configuration(s) where {G5_ARM} is active; "
            f"{len(jobs)} optimisations; "
            f"{len(switches_mod.all_names())} switch names and "
            f"{len(COMPARED)} run values per configuration"
        ),
        "n_compared": n_compared,
        "n_mismatched": n_mismatched,
        "arm": G5_ARM,
        "plan_column": [term for term, _ in PLAN_COLUMN],
        "rows": rows,
    }


def _teeth(campaign: Campaign) -> tuple[Tooth, ...]:
    def objective_hex() -> tuple[bool, str]:
        rows = [r for r in (_HELD.get("rows") or []) if "values" in r]
        if not rows:
            return False, "the gate compared no run, so nothing can be doctored"
        row = rows[0]
        left = row["values"]["norm_objf_hex"]["from_the_matrix"]
        right = row["values"]["norm_objf_hex"]["switch_by_switch"]
        doctored = (left or "") + "0"
        return doctored != right, (
            f"one character appended to {row['configuration']}'s objective hex "
            f"({left} → {doctored}): the comparison against {right} must "
            f"disagree"
        )

    def model_calls() -> tuple[bool, str]:
        rows = [r for r in (_HELD.get("rows") or []) if "values" in r]
        if not rows:
            return False, "the gate compared no run"
        row = rows[0]
        left = row["values"]["n_call_models"]["from_the_matrix"]
        right = row["values"]["n_call_models"]["switch_by_switch"]
        doctored = (left or 0) + 1
        return doctored != right, (
            f"one added to {row['configuration']}'s model-call count "
            f"({left} → {doctored}): the comparison against {right} must "
            f"disagree"
        )

    def a_dropped_switch() -> tuple[bool, str]:
        config = next(
            (c for c in campaign.configurations if G5_ARM not in c.skips), None
        )
        if config is None:
            return False, f"{G5_ARM} is active on no configuration"
        by_switch = switch_by_switch(config, campaign)
        from_matrix = _architecture_only(
            arms_mod.env_for(G5_ARM, config, seed=0, campaign=campaign)
        )
        name = switches_mod.REGISTRY["arrangement_method"].driver_name
        doctored = dict(by_switch)
        doctored[name] = None
        differing = [
            n
            for n in set(from_matrix) | set(doctored)
            if from_matrix.get(n) != doctored.get(n)
        ]
        return differing == [name], (
            f"{name} dropped from the hand-built column: the environment "
            f"comparison reports {differing} — a switch missing from one "
            f"composition must be one differing name, not none"
        )

    return (
        Tooth(
            name="norm_objf hex",
            what="one character appended to the objective's hex literal",
            must="make the comparison disagree",
            check=objective_hex,
        ),
        Tooth(
            name="n_call_models",
            what="one added to the model-call count",
            must="make the comparison disagree",
            check=model_calls,
        ),
        Tooth(
            name="a switch dropped from the hand-built column",
            what="the arrangement's method-level switch removed from one side",
            must="be reported as exactly one differing switch name",
            check=a_dropped_switch,
        ),
    )


def switch_composition_gate(campaign: Campaign) -> Gate:
    return Gate(
        name="switch_composition",
        plan_name="G5",
        needs_runs=True,
        binds=f"{G5_ARM}, on every configuration where it is active",
        what_it_proves=(
            "the arm the campaign runs is the arm the plan's matrix describes: "
            "composing it from the matrix and composing it switch by switch "
            "from the plan's own column give the same environment and the same "
            "run, to the bit"
        ),
        body=lambda *, resume=False: switch_composition_body(campaign, resume=resume),
        jobs=lambda: gates_mod.job_rows(jobs_read, campaign),
        teeth=_teeth(campaign),
    )
