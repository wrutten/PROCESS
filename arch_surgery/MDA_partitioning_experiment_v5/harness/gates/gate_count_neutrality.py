#!/usr/bin/env python
"""Gate GC — count neutrality across a driver change.

A driver change that is *meant* to change no count — resolving the block
schedule once per run instead of once per evaluation (DR9), moving the prime
from the head of every sweep to the head of every evaluation (DR10) — has to be
shown to change none.  Gate G1 shows that with **every switch unset** the copy
behaves as it did; it says nothing about the arms that compose the switches,
which are exactly the arms these changes touch.  This gate is the other half:
**every arm the matrix composes, on every configuration, before and after the
change, identical to the digit on every count and bit-identical on every exit
state.**

The job set
-----------
Both phases, every arm active on each configuration, one seed per
configuration: the evaluation phase from the displaced entry at the first
displaced seed (gate G6's pairing seed, δ the campaign's), the optimisation
phase from seed 0.  Twenty-two runs on V4's three configurations (`A1` and
`B1` are inactive on `st_regression`).  The jobs are composed through the
campaign and run through the shared pool like every other run-making gate's:
no directory is named.

Two sides at two commits, under one pool
-----------------------------------------
The pool keeps one directory per job identity, and the two sides of a straddle
are one job at two commits.  Gate G1 solves that by naming two directories;
this gate keeps the pool's rule and puts the **side into the identity**: every
job carries ``override_env[HARNESS_COUNT_NEUTRALITY_LABEL] = <label>`` — a
variable the driver never reads — so the "before" and "after" sides are two
identities, two digests, two pool directories, and neither can be resolved to
the other or to the campaign's own run of the same arm (issue I-29's hazard: a
job with a pool record's identity and its own directory re-makes the pool
record in place; a job with its own *identity* cannot).

:data:`STRADDLE` names the two labels this commit's press compares.  It is a
declaration committed **with** the driver change, so the record of which
change a verdict straddles is in the tree and not in whoever pressed the
button.  The "before" side is **read and never made** by the body: a side that
can only be made at a commit already behind us must never be handed to the
pool with ``--resume`` — the resume consults the *current* record contract and
would re-make an older record at this commit, collapsing the straddle into a
self-comparison with a passing verdict (trap T13; gate G1's docstring measures
the same failure).  Where the before side is absent the gate **refuses**; the
one exception is a press whose two labels are the same — the first press at
the copy commit, which makes the one side, compares it with itself and says
out loud that this is a determinism result and not a driver-change one.

What is compared
----------------
Every leaf under the declared count paths (:data:`COUNT_PATHS`: node calls,
sweeps, the sweep histogram, the block loop's totals, the two predicates'
counts, the block visits, the per-node census, the per-run deferral's own
counts, the output path's counts, the optimiser's iterations and attempts), the
optimum's hex floats, and **every coupling-state file the run wrote**
(``y_entry.json``, ``y_exit.json``, the output path's two snapshots) component
by component, floats as hex literals — bit equality, no tolerance.  A leaf or a
file present on one side only is a mismatch, never a smaller population.

One count is allowed to change, and only in the way the change declares
(:data:`PRIME_CALLS_DECLARATION`): ``n_arrangement_method_calls``.  Before DR10
the prime ran at the head of every sweep; after it, once per evaluation, so
under DR10 the after side must equal the **evaluation count** — 1 in the
evaluation phase, ``sweeps_per_eval.n_evaluations`` in the optimisation phase —
on every arm that composes the prime, and 0 on every arm that does not.  Under
every other declaration it is compared like any other count.

Teeth: one added to a count on a copy of an after-side record; one unit in the
last place on one float of a copy of an exit state; one added to the prime
count under the declared rule.  Each must be the one and only thing the
comparison reports.

Written by task **A99 (v5-schedule-and-prime)** for V5 experiment plan §7
(gate GC) and §11 (items 7 and 8, DR9 and DR10).
"""

from __future__ import annotations

import dataclasses
import json
import math
from pathlib import Path
from typing import Any, Mapping

from ..core import framework
from ..core import pool as pool_mod
from ..core import records as records_mod
from ..core.config import Campaign, Config
from ..core.framework import Gate, GateError, Tooth
from ..experiment import arms as arms_mod
from . import gate_neutrality as neutrality_mod
from . import gates as gates_mod

GATE_NAME = "count_neutrality"
PLAN_NAME = "GC"

#: The environment variable that carries the side's label into the job
#: identity.  The driver never reads it; the pool digests it.
LABEL_VARIABLE = "HARNESS_COUNT_NEUTRALITY_LABEL"

#: ``(before, after)``: the two labelled sides this commit's press compares.
#: Committed with the driver change it straddles.  ``("copy", "copy")`` is the
#: first press, at the copy commit before any change: one side, compared with
#: itself, a determinism result.
STRADDLE: tuple[str, str] = ("DR10", "DR11")

#: The test set a labelled side is made under, where a change declares one.
#: DR11 (A100 (v5-test-set)) made the test set a switch and V4's whole write
#: set its fallback value (decision D39): the DR11 side of GC is made under
#: ``write_set`` **by declaration**, so that every count and every exit state
#: must be identical to the digit to the DR10 side's -- which is the proof
#: that the fallback is V4's predicate exactly.  The census value is another
#: campaign and is not GC's business; a press under it is refused.
STRADDLE_TEST_SET: dict[str, str] = {"DR11": "write_set"}

#: What each labelled side declares about ``n_arrangement_method_calls``,
#: keyed by the **after** label.  ``identical``: compared like every other
#: count.  ``once_per_evaluation``: the after side equals the evaluation count
#: on every arm that composes the prime and 0 on every arm that does not —
#: driver change DR10's declaration (V5 list item 8).
PRIME_CALLS_DECLARATION: dict[str, str] = {
    "copy": "identical",
    # DR9 (the schedule and the deferral sets resolved once per run) declares
    # no change to any count.
    "DR9": "identical",
    # DR10 (the prime once per evaluation, before M1) declares that the prime
    # count becomes the evaluation count; every other count is unchanged.
    "DR10": "once_per_evaluation",
    # DR11 (the loop's test set a switch; the mixed ruler removed) declares
    # no change to any count under the fallback: the prime count is compared
    # like every other count, and must be identical.
    "DR11": "identical",
}

#: The evaluation phase's seed: the first displaced one, as gate G6 pairs the
#: entries on.  An undisplaced entry is the reference snapshot itself.
EVALUATION_SEED = 1

#: The optimisation phase's seed: the undisplaced start.
OPTIMISATION_SEED = 0

#: Record paths whose every leaf is a count the change may not move.  Each
#: with the one line saying what it is; subtrees are expanded leaf by leaf.
COUNT_PATHS: dict[str, str] = {
    "status": "how the run ended; both sides must have finished",
    "failure_class": "the taxonomy row",
    "node_calls_total": "model executions, the whole run",
    "node_calls_single_eval": "the evaluation phase's one measured evaluation",
    "node_calls_solve_phase": "the optimisation phase's cost unit",
    "n_model_calls_sweeps": "sweeps the one evaluation took",
    "n_model_calls": "sweeps of the dispatch body over the whole optimisation",
    "dispatch_sweeps": "sweeps of the dispatch body, every path included",
    "dispatch_sweeps_solve_phase": "the same, frozen at the output path",
    "sweeps_per_eval": "the per-evaluation sweep histogram and the evaluation count",
    "block_loop_totals": "the block loop's own totals: sweeps and solves per block, evaluations, schedule passes",
    "predicate_evaluations": "coupling-state convergence tests",
    "components_compared": "components those tests walked",
    "predicate_counters": "the two predicates' counts split out, per block",
    "block_visits": "visits to each block",
    "empty_block_visits": "the visits that executed no node",
    "empty_block_sweeps": "what those visits cost",
    "upstream_predicate_evaluations": "upstream's own stopping tests",
    "upstream_components_compared": "values those tests compared",
    "node_census": "model executions per node name, and the flat tail's uncounted calls",
    "defer_per_run_totals": "the per-run deferral's own counts and node set",
    "output_path": "which output path ran",
    "output_loop_sweeps": "sweeps the output-time loop ran",
    "output_path_entries": "entries to the output path",
    "n_solver_iterations": "the optimiser's iterations on its final attempt",
    "exit_forensics.n_attempts": "attempts of the retry ladder",
    "exit_forensics.n_solver_iterations_summed_over_attempts": "iterations over every attempt",
    "exit_forensics.ifail": "the optimiser's exit code",
    "exit_forensics.ladder_stage": "which rung the ladder ended on",
    "attempts": "every per-attempt count: node calls, sweeps, sweeps per block, the sweep histogram, iterations, exit code",
    "attempt_accounting": "how the per-attempt costs decompose the totals",
    "first_call_models.node_calls": "the first evaluation's node calls",
    "first_call_models.sweeps": "the first evaluation's sweeps",
    "first_call_models.objf_hex": "the first evaluation's objective, as a hex float",
    "first_call_models.conf_l2_hex": "the first evaluation's constraint norm, as a hex float",
    "mfile.ifail": "the exit code PROCESS wrote to its own output file",
    "exact": "the optimum (or the evaluation's objective) as hex floats: what a bit-comparison compares",
    "exit_audit.frozen.residual_max_hex": "the audit's maximum scaled residual on the measured-scale ruler (the second ruler's leaf went with the mixed ruler, DR11)",
    "exit_audit.audit_node_calls": "the audit sweep's own node calls (never charged; the same instrument both sides)",
    "t_plant_pulse_burn_hex": "the burn time at exit, as a hex float",
    "lift_residual": "the lifted component's inconsistency at exit",
}

#: The one count the change may move, and its companion on the first
#: evaluation of an optimisation.  Compared under :data:`PRIME_CALLS_DECLARATION`.
PRIME_PATHS: tuple[str, ...] = (
    "n_arrangement_method_calls",
    "first_call_models.n_arrangement_method_calls",
)

#: The switch readback that says whether the run composed the prime.
PRIME_READBACK = "process.core.caller.ARRANGEMENT_METHOD_FW_GEOMETRY"

#: Every coupling-state file a run may write.  Those present on the before
#: side must be present and bit-identical on the after side.
STATE_FILES: tuple[str, ...] = (
    "y_entry.json",
    "y_exit.json",
    "y_entry_to_write_output_files.json",
    "y_before_finalise.json",
)

_HELD: dict[str, Any] = {}


# --------------------------------------------------------------------------
# the job set
# --------------------------------------------------------------------------


def arms_of_phase(phase: str) -> tuple[str, ...]:
    """Every arm of the matrix in *phase*, in the matrix's order."""
    return tuple(name for name, arm in arms_mod.ARMS.items() if arm.phase == phase)


def labelled(label: str) -> dict[str, str]:
    """The identity field that makes one side's jobs their own."""
    return {LABEL_VARIABLE: label}


def count_neutrality_jobs(
    campaign: Campaign, references: Mapping[str, Any], label: str
) -> list[tuple[str, str, str, pool_mod.Job]]:
    """One side's job set: ``(phase, configuration, arm, job)`` per active arm."""
    from . import reproduction as reproduction_mod

    plan: list[tuple[str, str, str, pool_mod.Job]] = []
    for config in campaign.configurations:
        reference = references[config.name]
        snapshot = Path(reference["snapshot"])
        for arm in arms_of_phase("A"):
            if arm in config.skips:
                continue
            plan.append(
                (
                    "A",
                    config.name,
                    arm,
                    pool_mod.Job(
                        phase="A",
                        arm=arm,
                        config=config,
                        seed=EVALUATION_SEED,
                        regime="perturbed",
                        delta=campaign.delta,
                        pin_hex=reproduction_mod.entry_pin(
                            config,
                            arm,
                            reference,
                            seed=EVALUATION_SEED,
                            delta=campaign.delta,
                        ),
                        entry_state=snapshot,
                        run_kind="gate",
                        override_env=labelled(label),
                    ),
                )
            )
        for arm in arms_of_phase("B"):
            if arm in config.skips:
                continue
            plan.append(
                (
                    "B",
                    config.name,
                    arm,
                    pool_mod.Job(
                        phase="B",
                        arm=arm,
                        config=config,
                        seed=OPTIMISATION_SEED,
                        regime="unperturbed",
                        delta=None,
                        run_kind="gate",
                        override_env=labelled(label),
                    ),
                )
            )
    return plan


def jobs_read(campaign: Campaign) -> list[pool_mod.Job]:
    """The jobs this gate **makes** at this commit: the references and the after side.

    The before side is at another commit by construction and is listed in the
    verdict's ``straddle`` block with each record's own commit, not here: the
    framework's survey of ``jobs`` is the check that a gate's own runs are
    this commit's, and the before side is meant not to be.
    """
    references = gates_mod.entry_references_from_records(campaign)
    return gates_mod.entry_reference_jobs(campaign) + [
        job for *_rest, job in count_neutrality_jobs(campaign, references, STRADDLE[1])
    ]


# --------------------------------------------------------------------------
# the comparisons
# --------------------------------------------------------------------------


def _subtree(record: Mapping[str, Any], path: str) -> Any:
    """The value at dotted *path*, or the sentinel when it is not there."""
    return records_mod.resolve_path(record, path) if records_mod.has_path(record, path) else _MISSING


_MISSING = object()


#: Leaves under the declared paths that are **paths on disk**, not counts,
#: each with its reason: excluded by name, never compared.  Found by the
#: first press of the DR10 -> DR11 straddle (A100 (v5-test-set)): the before
#: side had been made in A99's worktree and the after side in A100's, and the
#: one differing leaf of 3 963 on every deferring arm was this absolute path
#: — the first GC straddle whose two sides were made in two working trees
#: (A99's three presses were all one tree, where the path agrees by accident
#: of location; the same class as gate G1's cross-tree paths).  What still
#: carries the artifact's identity is compared beside it: ``nodes_sha256``,
#: ``nodes``, ``executed_once`` and the per-node suppression counts.
PATH_LEAVES_NOT_COMPARED: dict[str, str] = {
    "defer_per_run_totals.artifact": (
        "an absolute path to the per-run deferral artifact, different between "
        "two working trees by construction; its content is compared through "
        "defer_per_run_totals.nodes_sha256 and the node lists beside it"
    ),
}


def count_leaves(record: Mapping[str, Any], paths: Mapping[str, str] | tuple[str, ...]) -> dict[str, Any]:
    """Every leaf under every declared path, keyed by its full dotted path,
    less the path leaves :data:`PATH_LEAVES_NOT_COMPARED` names."""
    out: dict[str, Any] = {}
    for path in paths:
        value = _subtree(record, path)
        if value is _MISSING:
            continue
        if isinstance(value, (dict, list)):
            for leaf, leaf_value in neutrality_mod.leaves(value, prefix=path).items():
                if leaf in PATH_LEAVES_NOT_COMPARED:
                    continue
                out[leaf] = leaf_value
        else:
            out[path] = value
    return out


def compare_counts(
    before: Mapping[str, Any], after: Mapping[str, Any], *, paths: Mapping[str, str] | tuple[str, ...] = COUNT_PATHS
) -> dict[str, Any]:
    """Every count leaf of two records, exactly.

    A leaf present on one side only is a mismatch, so a change that drops a
    count or adds one is reported rather than quietly shrinking or growing the
    population.
    """
    a = count_leaves(before, paths)
    b = count_leaves(after, paths)
    every = sorted(set(a) | set(b))
    mismatches: list[dict[str, Any]] = []
    for path in every:
        if path not in a or path not in b:
            mismatches.append(
                {
                    "field": path,
                    "before": a.get(path, "<absent>"),
                    "after": b.get(path, "<absent>"),
                    "why": "the leaf is present on one side only",
                }
            )
            continue
        if not neutrality_mod._same(a[path], b[path]):
            mismatches.append({"field": path, "before": a[path], "after": b[path]})
    return {
        "n_compared": len(every),
        "n_mismatched": len(mismatches),
        "mismatches": mismatches[:40],
    }


def _primed(record: Mapping[str, Any]) -> bool | None:
    """Whether the run composed the prime, read back from the driver."""
    value = (record.get("resolved_switches") or {}).get(PRIME_READBACK)
    return None if value is None else bool(value)


def _evaluations(record: Mapping[str, Any]) -> int | None:
    """The evaluation count of the run: 1 for an evaluation, the histogram's total for an optimisation."""
    if record.get("campaign_phase") == "A":
        return 1
    return ((record.get("sweeps_per_eval") or {}).get("n_evaluations"))


def compare_prime_calls(
    before: Mapping[str, Any], after: Mapping[str, Any], *, rule: str
) -> dict[str, Any]:
    """The prime count under the declared rule.

    ``identical``: both prime paths compared as counts.  ``once_per_evaluation``:
    the after side's whole-run count equals the evaluation count where the
    prime is composed and 0 where it is not, and the first evaluation's own
    count is 1 or 0 likewise; the before side is reported beside and not
    compared, because the change is the point.
    """
    if rule == "identical":
        result = compare_counts(before, after, paths=PRIME_PATHS)
        result["rule"] = rule
        result["passed"] = result["n_mismatched"] == 0
        return result
    if rule != "once_per_evaluation":
        raise GateError(
            f"PRIME_CALLS_DECLARATION names the rule {rule!r}, which this gate "
            f"does not implement; a rule nobody implements would pass by "
            f"never being applied"
        )
    primed = _primed(after)
    if primed is None:
        raise GateError(
            f"the after-side record does not read back {PRIME_READBACK}, so "
            f"whether the prime was composed cannot be known"
        )
    evaluations = _evaluations(after)
    expected_total = (evaluations if primed else 0)
    got_total = after.get("n_arrangement_method_calls")
    checks: dict[str, Any] = {
        "whole_run": {
            "expected": expected_total,
            "got": got_total,
            "before": before.get("n_arrangement_method_calls"),
            "passed": got_total is not None and evaluations is not None and got_total == expected_total,
        }
    }
    if records_mod.has_path(after, "first_call_models.n_arrangement_method_calls"):
        got_first = records_mod.resolve_path(after, "first_call_models.n_arrangement_method_calls")
        expected_first = 1 if primed else 0
        checks["first_evaluation"] = {
            "expected": expected_first,
            "got": got_first,
            "before": (
                records_mod.resolve_path(before, "first_call_models.n_arrangement_method_calls")
                if records_mod.has_path(before, "first_call_models.n_arrangement_method_calls")
                else "<absent>"
            ),
            "passed": got_first == expected_first,
        }
    n_mismatched = sum(1 for c in checks.values() if not c["passed"])
    return {
        "rule": rule,
        "primed": primed,
        "evaluations": evaluations,
        "n_compared": len(checks),
        "n_mismatched": n_mismatched,
        "checks": checks,
        "passed": n_mismatched == 0,
    }


def _state(directory: Path, name: str) -> dict[str, Any] | None:
    path = Path(directory) / name
    if not path.exists():
        return None
    return json.loads(path.read_text())


def compare_state_files(before_dir: Path, after_dir: Path) -> dict[str, Any]:
    """Every coupling-state file the before side wrote, against the after side's.

    Component by component, every kind of component, floats as hex literals:
    bit equality (gate G2's construction, :func:`gate_prime.full_state_compare`).
    A file on one side only is a mismatch of its whole component count.
    """
    from . import gate_prime as prime_mod

    files: dict[str, Any] = {}
    n_components = n_differing = 0
    for name in STATE_FILES:
        a = _state(before_dir, name)
        b = _state(after_dir, name)
        if a is None and b is None:
            continue
        if a is None or b is None:
            n = len((a or b)["state"])
            files[name] = {
                "n_components": n,
                "n_differing": n,
                "why": "the file is present on one side only",
            }
            n_components += n
            n_differing += n
            continue
        if a.get("components_sha256") != b.get("components_sha256"):
            n = max(len(a["state"]), len(b["state"]))
            files[name] = {
                "n_components": n,
                "n_differing": n,
                "why": "the two states were taken against different component specs",
            }
            n_components += n
            n_differing += n
            continue
        comparison = prime_mod.full_state_compare(a["state"], b["state"])
        files[name] = comparison
        n_components += comparison["n_components"]
        n_differing += comparison["n_differing"]
    return {
        "n_components_compared": n_components,
        "n_components_differing": n_differing,
        "files": files,
    }


# --------------------------------------------------------------------------
# the body
# --------------------------------------------------------------------------


def _read(directory: Path, *, side: str, key: str) -> dict[str, Any]:
    record = records_mod.read(directory)
    if record.get("status") == "no_record":
        raise GateError(
            f"GC has no {side} record for {key} at {directory}: "
            f"{record.get('why')}.  A gate that cannot find one of the two "
            f"records it compares refuses, never passes over an empty "
            f"comparison (trap T11)."
        )
    return record


def _side_provenance(campaign: Campaign, plan: list) -> dict[str, Any]:
    paths = [pool_mod.directory_for(job, campaign) for *_r, job in plan]
    survey = framework.survey_heads(paths, relative_to=Path(campaign.runs_dir) / framework.GATES_SUBPATH)
    survey["records"] = [
        {
            "key": job.key,
            "path": framework._relative(pool_mod.directory_for(job, campaign), Path(campaign.runs_dir) / framework.GATES_SUBPATH),
            "tree_git_head": records_mod.read(pool_mod.directory_for(job, campaign)).get("tree_git_head"),
        }
        for *_r, job in plan
    ]
    return survey


def _straddle(before: Mapping[str, Any], after: Mapping[str, Any]) -> dict[str, Any]:
    """What this press straddles, said out loud (gate G1's construction)."""
    before_label, after_label = STRADDLE
    b_heads, a_heads = list(before.get("heads") or []), list(after.get("heads") or [])
    if before_label == after_label:
        return {
            "before_label": before_label,
            "after_label": after_label,
            "before_commits": b_heads,
            "after_commits": a_heads,
            "straddles_a_change": False,
            "says": (
                f"ONE SIDE, labelled {after_label!r}, at {a_heads}: compared "
                f"with itself — determinism and coverage of the declared "
                f"paths, NOT a driver-change result."
            ),
        }
    if b_heads and a_heads and set(b_heads) != set(a_heads):
        return {
            "before_label": before_label,
            "after_label": after_label,
            "before_commits": b_heads,
            "after_commits": a_heads,
            "straddles_a_change": True,
            "says": (
                f"straddles {before_label!r} at {[h[:8] for h in b_heads]} -> "
                f"{after_label!r} at {[h[:8] for h in a_heads]}: a count-neutrality result."
            ),
        }
    return {
        "before_label": before_label,
        "after_label": after_label,
        "before_commits": b_heads,
        "after_commits": a_heads,
        "straddles_a_change": None,
        "says": (
            f"the two sides are labelled {before_label!r} and {after_label!r} "
            f"but their records' commits do not differ ({b_heads} / {a_heads}): "
            f"what this press straddles cannot be stated."
        ),
    }


def count_neutrality_body(campaign: Campaign, *, resume: bool = False) -> dict[str, Any]:
    """GC: before and after the change, every count and every exit state agree."""
    before_label, after_label = STRADDLE
    rule = PRIME_CALLS_DECLARATION.get(after_label)
    if rule is None:
        raise GateError(
            f"PRIME_CALLS_DECLARATION declares nothing for the after label "
            f"{after_label!r}; a change that does not say what it does to the "
            f"prime count is not declared, and an undeclared change cannot pass"
        )
    declared_set = STRADDLE_TEST_SET.get(after_label)
    if declared_set is not None and campaign.test_set != declared_set:
        raise GateError(
            f"GC's after side {after_label!r} is declared under the "
            f"{declared_set!r} test set and this press composes "
            f"{campaign.test_set!r}: the count-neutrality claim of DR11 is that "
            f"the fallback is V4's predicate exactly, and a side made under "
            f"another test set would be another campaign, not a straddle.  "
            f"Press it with --test-set {declared_set}."
        )
    references = gates_mod.entry_references(campaign, resume=resume)
    before_plan = count_neutrality_jobs(campaign, references, before_label)
    after_plan = count_neutrality_jobs(campaign, references, after_label)

    if before_label != after_label:
        # The before side is read, never made: see the module docstring.
        absent = [
            job.key
            for *_r, job in before_plan
            if not (pool_mod.directory_for(job, campaign) / "metrics.json").exists()
        ]
        if absent:
            raise GateError(
                f"GC's before side ({before_label!r}) has no record for "
                f"{len(absent)} of {len(before_plan)} job(s) — first: "
                f"{absent[:3]}.  The before side is made at the commit "
                f"before the change and is never made here; press this gate "
                f"at that commit with STRADDLE = ({before_label!r}, "
                f"{before_label!r}) first."
            )
    pool_mod.run_all([job for *_r, job in after_plan], campaign, resume=resume)

    rows: list[dict[str, Any]] = []
    passed = True
    n_compared = n_mismatched = 0
    n_components = n_components_differing = 0
    n_prime_compared = n_prime_mismatched = 0
    by_key = {(p, c, a): job for p, c, a, job in before_plan}
    for phase, config_name, arm, after_job in after_plan:
        before_job = by_key[(phase, config_name, arm)]
        before_dir = pool_mod.directory_for(before_job, campaign)
        after_dir = pool_mod.directory_for(after_job, campaign)
        key = f"{phase}/{arm}/{config_name}"
        before = _read(before_dir, side="before", key=key)
        after = _read(after_dir, side="after", key=key)
        counts = compare_counts(before, after)
        prime = compare_prime_calls(before, after, rule=rule)
        states = compare_state_files(before_dir, after_dir)
        unlabelled = pool_mod.Job(
            **{
                f.name: getattr(after_job, f.name)
                for f in dataclasses.fields(pool_mod.Job)
                if f.name not in ("override_env", "outdir")
            }
        )
        row = {
            "phase": phase,
            "configuration": config_name,
            "arm": arm,
            "key": key,
            "before": {
                "path": str(before_dir),
                "tree_git_head": before.get("tree_git_head"),
                "status": before.get("status"),
            },
            "after": {
                "path": str(after_dir),
                "tree_git_head": after.get("tree_git_head"),
                "status": after.get("status"),
            },
            "counts": counts,
            "prime_calls": prime,
            "states": states,
            "label_is_an_identity_field": {
                "before_digest": pool_mod.digest_for(before_job, campaign)[:16],
                "after_digest": pool_mod.digest_for(after_job, campaign)[:16],
                "unlabelled_digest": pool_mod.digest_for(unlabelled, campaign)[:16],
            },
        }
        distinct = len(
            {
                row["label_is_an_identity_field"]["before_digest"],
                row["label_is_an_identity_field"]["after_digest"],
                row["label_is_an_identity_field"]["unlabelled_digest"],
            }
        ) == (2 if before_label == after_label else 3)
        checks = {
            "both_runs_finished": before.get("status") == "ok" and after.get("status") == "ok",
            "every_count_identical": counts["n_mismatched"] == 0,
            "prime_count_as_declared": prime["passed"],
            "every_exit_state_bit_identical": states["n_components_differing"] == 0,
            "at_least_one_state_file_compared": states["n_components_compared"] > 0,
            "labels_are_distinct_identities": distinct,
        }
        row["checks"] = checks
        row["passed"] = all(checks.values())
        passed = passed and row["passed"]
        n_compared += counts["n_compared"]
        n_mismatched += counts["n_mismatched"]
        n_prime_compared += prime["n_compared"]
        n_prime_mismatched += prime["n_mismatched"]
        n_components += states["n_components_compared"]
        n_components_differing += states["n_components_differing"]
        rows.append(row)

    before_prov = _side_provenance(campaign, before_plan)
    after_prov = _side_provenance(campaign, after_plan)
    straddle = _straddle(before_prov, after_prov)
    _HELD["rows"] = rows
    _HELD["rule"] = rule
    outcome = {
        "passed": passed,
        "criterion": (
            "on a job set of both phases, every arm active on each "
            "configuration at one seed per configuration (the evaluation "
            "phase from the displaced entry, the optimisation phase from seed "
            "0), every declared count identical to the digit and every "
            "coupling-state file bit-identical between the before and after "
            "sides of the change; n_arrangement_method_calls compared under "
            "the rule the change declares"
        ),
        "criterion_source": "V5 experiment plan §7 (gate GC) and §11 (DR9, DR10)",
        "straddle": straddle,
        "prime_calls_rule": rule,
        "prime_calls_declaration": dict(PRIME_CALLS_DECLARATION),
        "test_set": campaign.test_set,
        "tau": campaign.tau,
        "straddle_test_set_declaration": dict(STRADDLE_TEST_SET),
        "population": (
            f"{straddle['says']}  {len(rows)} run pair(s) = "
            f"{sum(1 for r in rows if r['phase'] == 'A')} evaluation(s) + "
            f"{sum(1 for r in rows if r['phase'] == 'B')} optimisation(s); "
            f"{n_compared} count leaves compared under {len(COUNT_PATHS)} "
            f"declared paths, {n_mismatched} differing; {n_prime_compared} "
            f"prime-count check(s) under the rule {rule!r}, "
            f"{n_prime_mismatched} failing; {n_components} coupling-state "
            f"components compared bit for bit over the state files, "
            f"{n_components_differing} differing"
        ),
        "n_pairs": len(rows),
        "n_compared": n_compared,
        "n_mismatched": n_mismatched,
        "n_prime_checks": n_prime_compared,
        "n_prime_checks_failing": n_prime_mismatched,
        "n_components_compared": n_components,
        "n_components_differing": n_components_differing,
        "count_paths": dict(COUNT_PATHS),
        "path_leaves_not_compared": dict(PATH_LEAVES_NOT_COMPARED),
        "prime_paths": list(PRIME_PATHS),
        "state_files": list(STATE_FILES),
        "label_variable": LABEL_VARIABLE,
        "evaluation_seed": EVALUATION_SEED,
        "optimisation_seed": OPTIMISATION_SEED,
        "delta": campaign.delta,
        "before_side": before_prov,
        "after_side": after_prov,
        "rows": rows,
    }
    # One file per straddle, never overwritten by a later change's press: the
    # framework writes the *latest* verdict to ``count_neutrality/gate.json``,
    # and a gate that reads this gate's result for one particular change (G2
    # reads the per-sweep -> once-per-evaluation straddle) needs that change's
    # record whatever was pressed since.  Under the verdict directory, not the
    # pool: it is a comparison record, not a run.
    path = straddle_record_path(campaign, before_label, after_label)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "gate": GATE_NAME,
                "plan_name": PLAN_NAME,
                "tree_git_head": framework.git_head(),
                **outcome,
            },
            indent=2,
            default=str,
        )
        + "\n"
    )
    outcome["straddle_record"] = str(path)
    return outcome


def straddle_record_path(campaign: Campaign, before_label: str, after_label: str) -> Path:
    """Where one straddle's comparison record is kept, by its two labels."""
    return (
        Path(campaign.runs_dir)
        / framework.GATES_SUBPATH
        / GATE_NAME
        / "straddles"
        / f"{before_label}__{after_label}.json"
    )


# --------------------------------------------------------------------------
# the teeth
# --------------------------------------------------------------------------


def _last_live_row() -> dict[str, Any] | None:
    rows = _HELD.get("rows") or []
    return rows[-1] if rows else None


def _teeth(campaign: Campaign) -> tuple[Tooth, ...]:
    def a_doctored_count() -> tuple[bool, str]:
        row = _last_live_row()
        if row is None:
            return False, "the gate compared nothing, so nothing can be doctored"
        before = records_mod.read(Path(row["before"]["path"]))
        after = json.loads(json.dumps(records_mod.read(Path(row["after"]["path"]))))
        field = "node_calls_total"
        was = after.get(field)
        if not isinstance(was, int):
            return False, f"{field} is {was!r} on the after side; nothing to add one to"
        after[field] = was + 1
        result = compare_counts(before, after)
        named = [m["field"] for m in result["mismatches"]]
        return result["n_mismatched"] == 1 and named == [field], (
            f"one added to {field} ({was} → {was + 1}) in a copy of "
            f"{row['key']}'s after-side record: the comparison reports "
            f"{result['n_mismatched']} differing leaf/leaves of "
            f"{result['n_compared']} ({named})"
        )

    def a_doctored_exit_state_byte() -> tuple[bool, str]:
        from . import gate_prime as prime_mod

        row = _last_live_row()
        if row is None:
            return False, "the gate compared nothing"
        state = dict(json.loads((Path(row["after"]["path"]) / "y_exit.json").read_text())["state"])
        chosen = None
        for name in sorted(state):
            value = state[name]
            if not (isinstance(value, dict) and value.get("k") == "f"):
                continue
            number = float.fromhex(value["hex"])
            if math.isfinite(number) and number != 0.0:
                chosen = (name, value["hex"], math.nextafter(number, math.inf).hex())
                break
        if chosen is None:
            return False, "no finite non-zero float component to doctor: a finding, report it"
        name, before_hex, after_hex = chosen
        clean = dict(state)
        state[name] = {"k": "f", "hex": after_hex}
        result = prime_mod.full_state_compare(clean, state)
        return result["n_differing"] == 1 and result["differing"] == [name], (
            f"one unit in the last place on {name} ({before_hex} → {after_hex}) "
            f"in a copy of {row['key']}'s exit state: the comparison reports "
            f"{result['n_differing']} differing component(s) of "
            f"{result['n_components']}"
        )

    def a_doctored_prime_count() -> tuple[bool, str]:
        row = _last_live_row()
        if row is None:
            return False, "the gate compared nothing"
        rule = _HELD.get("rule")
        before = records_mod.read(Path(row["before"]["path"]))
        after = json.loads(json.dumps(records_mod.read(Path(row["after"]["path"]))))
        was = after.get("n_arrangement_method_calls")
        if not isinstance(was, int):
            return False, f"n_arrangement_method_calls is {was!r}; nothing to add one to"
        after["n_arrangement_method_calls"] = was + 1
        result = compare_prime_calls(before, after, rule=rule)
        return not result["passed"], (
            f"one added to n_arrangement_method_calls ({was} → {was + 1}) in a "
            f"copy of {row['key']}'s after-side record under the rule "
            f"{rule!r}: the check reports {result['n_mismatched']} of "
            f"{result['n_compared']} failing"
        )

    return (
        Tooth(
            name="a doctored count on one record",
            what="one added to node_calls_total in a copy of an after-side record",
            must="be the one and only differing count leaf",
            check=a_doctored_count,
        ),
        Tooth(
            name="a doctored exit-state byte",
            what="one unit in the last place on one float of a copy of an exit state",
            must="be the one and only differing component",
            check=a_doctored_exit_state_byte,
        ),
        Tooth(
            name="a doctored prime count",
            what="one added to n_arrangement_method_calls in a copy of an after-side record",
            must="fail the declared rule, whichever rule is declared",
            check=a_doctored_prime_count,
        ),
    )


def gate(campaign: Campaign) -> Gate:
    return Gate(
        name=GATE_NAME,
        plan_name=PLAN_NAME,
        needs_runs=True,
        binds=(
            "each count-neutral driver change (DR9, DR10): every arm the "
            "matrix composes, both phases, on every configuration"
        ),
        what_it_proves=(
            "before and after the change, every declared count is identical "
            "to the digit and every coupling-state file the run wrote is "
            "bit-identical, with the prime count moving only as the change "
            "declares"
        ),
        body=lambda *, resume=False: count_neutrality_body(campaign, resume=resume),
        jobs=lambda: gates_mod.job_rows(jobs_read, campaign),
        teeth=_teeth(campaign),
    )
