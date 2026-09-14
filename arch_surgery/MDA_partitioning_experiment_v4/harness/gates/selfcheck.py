#!/usr/bin/env python
"""The harness's own gates, each shown able to fail.  No PROCESS run.

Five things are checked, and each carries a *tooth*: a deliberate break that
the check must catch before its zeros are believed (orchestration protocol
§12).  A count without the number of things compared is not reported.

1. **composition** — every arm composes on every configuration, a skipped arm
   refuses by name, and the arms the previous revision also ran ask the driver
   for the **same thing** it asked for.  Same thing, not same spelling: the
   switches have been renamed since, so the comparison is made **by role**,
   through the registry's map from each revision's variable names to the term
   for what the switch does.
2. **rungs** — the plan's matrix regenerates cell for cell from the arm
   records, and the difference between two arms equals the difference the plan
   declares for that step.
3. **capability** — the tree resolves every switch an arm asks for, and an arm
   asking for a switch the tree does not implement is refused, never run.
4. **provenance** — a modified tracked file and an untracked file are recorded
   separately, and only the first marks the tree dirty.
5. **data** — every committed file the experiment reads is byte-identical to
   its source at the recorded commit, the file set matches, and the moved
   predicate module differs from its own source in nothing but the heritage
   paragraph the record names.

Run it directly, or through ``experiment_runner.py --selfcheck``.  Both check
the experiment's own copy of PROCESS, which is the tree every run uses;
``--tree repository`` checks the repository-root package instead, and since the
switch rename its capability check **fails by design** — that tree belongs to
the previous revision and does not implement the new names, which is exactly
what the probe exists to notice.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as _dt
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
# dataclasses are no longer used here: the check record moved to harness/core/framework.py
from pathlib import Path
from typing import Any

_EXPERIMENT_DIR = Path(__file__).resolve().parents[2]
if str(_EXPERIMENT_DIR) not in sys.path:
    sys.path.insert(0, str(_EXPERIMENT_DIR))

from harness.experiment import arms as arms_mod  # noqa: E402
from harness.experiment import data_provenance as data_mod  # noqa: E402
from harness.core import framework  # noqa: E402
from harness.experiment import input_files as input_files_mod  # noqa: E402
from harness.child import perturb as perturb_mod  # noqa: E402
from harness.core import pool as pool_mod  # noqa: E402
from harness.core import records as records_mod  # noqa: E402
from harness.core import provenance as prov  # noqa: E402
from harness.experiment import switches as sw  # noqa: E402
from harness.core.config import (  # noqa: E402
    ARTIFACT_NAMES,
    DRIVER_FIXED_ARTIFACTS,
    Campaign,
    artifact_file_names,
    default_campaign,
    repository_tree_campaign,
)

# --------------------------------------------------------------------------
# results
# --------------------------------------------------------------------------


#: The check record's shape, defined once in ``harness/core/framework.py`` and named
#: here because this module's six checks are written against it.  It was defined
#: in this file until task **A52 (harness-gates)** promoted it: the class moved,
#: field for field, and nothing about what a check computes changed.
Check = framework.Check


# --------------------------------------------------------------------------
# 1. composition
# --------------------------------------------------------------------------
#
# The previous revision's composition, transcribed from
# MDA_partitioning_experiment_v3/v3_runner.py::env_for (lines 85-147) and
# phase_a.py::env_for_phase_a (lines 139-193) at f2dc9243.  It is transcribed
# rather than imported: every verification the experiment runs is implemented
# inside this package, and importing the earlier revision would pull five
# modules of superseded task machinery onto the import path to obtain six
# dictionaries.  `--crosscheck-previous` executes those two functions in a
# subprocess and compares, so the transcription itself is measured rather
# than trusted.

# The comparison below is **by role**, and that is the whole reason it still
# means something after the rename.  The previous revision's environments carry
# the names it used; this revision's carry the names it uses.  Comparing them
# literally would report every arm as different and prove nothing.  Comparing
# them by role -- through `switches.canonical_roles`, which maps each
# revision's variable names onto the term for what the switch *does* -- asks
# the question that matters: does this arm ask the driver for the same thing?
# Two foldings are part of that map and both can fail loudly rather than
# absorb a difference: `OUTER=trust` alongside the partitioned loop is dropped
# because the partitioned loop now means exactly that, and any other
# combination becomes an explicit role that makes the comparison fail; and the
# two burn-time settings become one owner, with a constant that lacks the lift
# refused rather than read as some other owner.

#: Arm names as the previous revision spelled them, for the comparison only.
_PREVIOUS_NAME = {"BR": "R", "A0": "A0", "A1": "A1", "B0": "B0", "B1": "B1", "B3": "B3"}


def _previous_environment(arm: str, config, campaign: Campaign) -> dict[str, str]:
    """What the previous revision set for *arm* on *config*, by transcription.

    Artifact values are the artifact's **role**, not its path: the previous
    revision read the files from the repository's shared data directory under
    the old spellings, and V4 reads its own copy under names that say what each
    file is for.  What must be equal is which artifact each switch is handed,
    and that is what a role compares.
    """
    name = config.name
    pulsed = config.pulsed
    tau = repr(campaign.tau)
    if arm == "BR":
        return {}
    base = {
        "PROCESS_ARCH_TAU": tau,
        "PROCESS_ARCH_YSTATE": "<coupling_state>",
        "PROCESS_ARCH_WRITESET": "<write_sets>",
    }
    if arm in ("A0", "B0"):
        return {**base, "PROCESS_ARCH_MODULE_SOLVE": "flat_state"}
    if arm == "B1":
        env = {**base, "PROCESS_ARCH_MODULE_SOLVE": "flat_state"}
        if pulsed:
            env["PROCESS_ARCH_LIFT"] = "burn_time"
        return env
    if arm in ("A1", "B3"):
        env = {
            **base,
            "PROCESS_ARCH_SEQUENCE": "build_after_physics",
            "PROCESS_ARCH_MODULE_SOLVE": "per_module",
            "PROCESS_ARCH_OUTER": "trust",
            "PROCESS_ARCH_PRIME": "fw_geometry",
            "PROCESS_ARCH_HOIST": (
                "feedforward_lifted" if pulsed else "feedforward"
            ),
        }
        # Phase A's block arm runs the committed input file, so its per-run
        # artifact is the one stamped for the base constraint set; Phase B's
        # runs the lifted input file and takes the other.  A steady-state
        # configuration has one artifact and both roles resolve to it.
        env["PROCESS_ARCH_POST_SOLVE"] = (
            "<defer_per_run_lifted>" if (arm == "B3" and pulsed) else "<defer_per_run>"
        )
        if pulsed:
            env["PROCESS_ARCH_LIFT"] = "burn_time"
            if arm == "A1":
                env["PROCESS_ARCH_PIN_BURN_TIME"] = "<pin>"
        return env
    raise KeyError(arm)


#: Role order for the reverse lookup.  A steady-state configuration has one
#: per-run artifact that both roles name, and the unmarked role wins, so the
#: two naming schemes agree on it even though they mark opposite members of
#: the pair.
_ROLE_ORDER = ("coupling_state", "write_sets", "defer_per_run", "defer_per_run_lifted")


def _artifact_role(file_name: str, config) -> str | None:
    """Which artifact *file_name* is, under any naming scheme this repo uses."""
    for naming in ARTIFACT_NAMES:
        files = artifact_file_names(
            config.name, pulsed=config.pulsed, naming=naming
        )
        for role in _ROLE_ORDER:
            if files[role] == file_name:
                return role
    for role, fixed in DRIVER_FIXED_ARTIFACTS.items():
        if fixed == file_name:
            return role
    return None


def _architecture_only(env: dict[str, str], config) -> dict[str, str]:
    """The architecture switches of *env*, artifact paths reduced to roles.

    A path is replaced by what the file is *for*, so that two revisions
    reading the same artifact under different names still compare equal, and
    two revisions reading *different* artifacts still compare unequal.
    """
    out = {}
    for name in sw.all_names():
        if name not in env:
            continue
        value = env[name]
        if value.startswith("/"):
            role = _artifact_role(Path(value).name, config)
            value = f"<{role}>" if role else Path(value).name
        out[name] = value
    return out


def _roles(env: dict[str, str], config, *, revision: str) -> dict[str, str]:
    """*env* as ``what the switch does -> the value it is given``.

    Artifact paths are reduced to the file's role first, so that the two
    revisions' different directory layouts do not read as different requests;
    then the variable names are mapped onto the terms, which is what makes a
    renamed switch comparable with its old name.
    """
    reduced = _architecture_only(env, config)
    roles = sw.canonical_roles(reduced, revision=revision)
    constant = roles.get("burn_time_owner", "")
    if constant.startswith("constant:"):
        # The constant itself rides a per-seed displacement stream and is not
        # the thing under comparison; that a constant owns the quantity is.
        roles["burn_time_owner"] = "constant:<a constant>"
    return roles


_PIN_HEX = float(1234.5).hex()


def check_composition(campaign: Campaign) -> Check:
    check = Check(
        name="composition",
        binds="every arm composes on every configuration, and the arms the "
        "previous revision also ran ask the driver for the same thing — "
        "compared by role, through the registry's name map, because the "
        "switches have been renamed since",
        population=(
            f"{len(arms_mod.ARMS)} arms x {len(campaign.configurations)} "
            f"configurations = "
            f"{len(arms_mod.ARMS) * len(campaign.configurations)} pairs"
        ),
    )
    composed: dict[tuple[str, str], dict[str, str]] = {}
    skipped = 0
    for config in campaign.configurations:
        for name, arm in arms_mod.ARMS.items():
            check.n_compared += 1
            if name in config.skips:
                skipped += 1
                try:
                    arms_mod.env_for(name, config, campaign=campaign, pending_ok=True)
                except sw.SwitchError as exc:
                    if config.skips[name] not in str(exc):
                        check.fail(
                            f"{name} on {config.name}: the refusal does not "
                            f"quote the recorded reason ({exc})"
                        )
                    continue
                check.fail(
                    f"{name} on {config.name} is recorded as skipped "
                    f"({config.skips[name]}) but composed anyway"
                )
                continue
            try:
                env = arms_mod.env_for(
                    name,
                    config,
                    seed=0,
                    pin_hex=_PIN_HEX,
                    campaign=campaign,
                    pending_ok=True,
                )
            except Exception as exc:  # noqa: BLE001 - reported, not raised
                check.fail(f"{name} on {config.name} did not compose: {exc}")
                continue
            composed[(name, config.name)] = env
            if arms_mod.ARMS[name].is_reference:
                set_here = _architecture_only(env, config)
                if set_here:
                    check.fail(
                        f"{name} on {config.name} is the reference arm and "
                        f"must compose to every switch cleared, but set "
                        f"{sorted(set_here)}"
                    )
    check.note(
        f"{skipped} recorded skip(s) refused by name; "
        f"{len(composed)} environment(s) composed"
    )

    # --- the pin is required where a constant owns the burn time -----------
    for config in campaign.configurations:
        for name in ("A0p", "A1"):
            if name in config.skips or not config.pulsed:
                continue
            try:
                arms_mod.env_for(
                    name, config, seed=7, campaign=campaign, pending_ok=True
                )
            except sw.SwitchError:
                continue
            check.fail(
                f"{name} on {config.name} composed without the constant that "
                f"owns the burn time"
            )

    # --- the same request as the previous revision, role for role ----------
    #
    # Comparable only over the roles **both** revisions can express.  A role
    # this revision has and the previous one had no switch for is not a
    # disagreement -- it is a capability the driver gained -- and it is
    # **derived** from the registry's own name map rather than listed here: a
    # term the map does not carry is a term the previous revision could not
    # say.  Listing it by hand is how such an exception becomes a place to hide
    # a real difference.  The roles set aside are named, with their values, and
    # counted beside the roles compared: a comparison whose population is
    # quietly smaller than the one stated is this project's trap T11.
    could_say = sw.previous_revision_roles()
    new_roles = sorted(term for term in sw.REGISTRY if term not in could_say)
    previous_compared = 0
    roles_compared = 0
    roles_set_aside = 0
    set_aside_seen: dict[str, set[str]] = {}
    for config in campaign.configurations:
        for name in _PREVIOUS_NAME:
            if name in config.skips or (name, config.name) not in composed:
                continue
            mine = _roles(composed[(name, config.name)], config, revision="current")
            theirs = _roles(
                _previous_environment(name, config, campaign),
                config,
                revision="previous",
            )
            for term in new_roles:
                if term in mine:
                    set_aside_seen.setdefault(term, set()).add(
                        f"{name}={mine[term]}"
                    )
                    roles_set_aside += 1
                    mine.pop(term)
            previous_compared += 1
            roles_compared += len(set(mine) | set(theirs))
            if mine != theirs:
                check.fail(
                    f"{name} on {config.name}: asks the driver for {mine}, the "
                    f"previous revision asked for {theirs}"
                )
    check.n_compared += previous_compared
    check.note(
        f"{previous_compared} arm/configuration pair(s) compared against the "
        f"previous revision's composition **by role**, {roles_compared} role "
        f"value(s) in total; the switch names differ on the two sides and the "
        f"registry's name map is what makes them comparable"
    )
    if set_aside_seen:
        check.note(
            f"{roles_set_aside} role value(s) set aside as capabilities the "
            f"previous revision could not express, measured from its own "
            f"composer and never listed: "
            + "; ".join(
                f"{term} ({', '.join(sorted(values))})"
                for term, values in sorted(set_aside_seen.items())
            )
        )
    else:
        check.note(
            "no role this revision composes is one the previous revision "
            "could not express, so nothing was set aside"
        )

    # A role BOTH revisions can express must never be set aside.  The tooth
    # takes the one the previous revision spelled differently and does exactly
    # that: if the derivation ever widened to cover it, the comparison would
    # stop noticing a real difference in the analysis loop.
    check.tooth(
        "a role both revisions can express treated as a new capability",
        "mda" not in new_roles and "burn_time_owner" not in new_roles,
        "the roles set aside are measured from the previous revision's own "
        "composer, so a role it *did* have a switch for -- the analysis loop, "
        "and the burn time's owner, which two of its switches folded into -- "
        "can never be among them; if one were, a real difference in it would "
        f"be silently dropped from the comparison (it could say "
        f"{sorted(could_say)}; set aside: {new_roles})",
    )

    # --- the arms whose declared switches no tree implements ---------------
    pending_report: list[str] = []
    for config in campaign.configurations:
        for name, arm in arms_mod.ARMS.items():
            if name in config.skips:
                continue
            terms = arm.terms(
                config, pin_hex=_PIN_HEX, campaign=campaign, seed=0
            )
            pending = sw.unimplemented(terms)
            if not pending:
                continue
            pending_report.append(f"{name}/{config.name}: {', '.join(pending)}")
            try:
                arms_mod.env_for(
                    name, config, seed=0, pin_hex=_PIN_HEX, campaign=campaign
                )
            except sw.SwitchError:
                continue
            check.fail(
                f"{name} on {config.name} composed although {pending} is not "
                f"implemented by any tree — that is a silent degrade"
            )
    if pending_report:
        check.note(
            "declared but not yet implemented by any tree (refused on a run "
            "path): " + "; ".join(pending_report)
        )
    else:
        check.note(
            "every switch every arm composes is implemented by the tree under "
            "test: no arm on any configuration is refused for a capability "
            "the driver does not have.  The convergence-predicate mode is the "
            "one declared switch still waiting on its driver change, and no "
            "arm composes it — only the trial does"
        )

    # --- a configuration can leave the experiment by a recorded decision ---
    victim = campaign.configurations[-1]
    before = sum(
        len(arms_mod.active_arms(c, "B")) * campaign.n_seeds
        for c in campaign.configurations
    )
    smaller = campaign.without_configuration(
        victim.name,
        decision="self-check",
        reason="exercising the removal mechanism; not a real removal",
        date="1970-01-01",
    )
    after = sum(
        len(arms_mod.active_arms(c, "B")) * campaign.n_seeds
        for c in smaller.configurations
    )
    expected_after = before - len(arms_mod.active_arms(victim, "B")) * campaign.n_seeds
    check.n_compared += 1
    if (
        victim.name in smaller.population
        or after != expected_after
        or not smaller.removed_configurations
    ):
        check.fail(
            f"removing {victim.name} by a recorded decision left the "
            f"population at {smaller.population} and the count at {after} "
            f"(expected {expected_after})"
        )
    removal_raised = False
    try:
        smaller.configuration(victim.name)
    except KeyError:
        removal_raised = True
    if not removal_raised:
        check.fail(
            f"{victim.name} was removed but is still reachable by name; a "
            f"lookup that misses must raise, never return an empty population"
        )
    check.note(
        f"removal mechanism: dropping {victim.name} moves the Phase B run "
        f"count from {before} to {after}, re-derived from the configuration "
        f"list rather than patched"
    )

    # --- teeth -------------------------------------------------------------
    #
    # Every break below is made on the **role** dictionary, because that is
    # what the comparison above compares.  A tooth that broke a variable name
    # would only prove that the two revisions spell things differently, which
    # is true and uninteresting.
    config = campaign.configurations[0]

    def previous_roles(name: str, cfg) -> dict[str, str]:
        return _roles(
            _previous_environment(name, cfg, campaign), cfg, revision="previous"
        )

    def comparable(name: str, cfg) -> dict[str, str]:
        """This revision's roles for one arm, on the footing the check compares.

        The same set-aside the comparison applies: a role the previous revision
        could not express is not part of a comparison against it, so a tooth
        that broke something else would otherwise be reported as tripping on a
        difference that is there anyway.
        """
        roles = _roles(composed[(name, cfg.name)], cfg, revision="current")
        for term in new_roles:
            roles.pop(term, None)
        return roles

    broken = comparable("B0", config)
    broken["mda"] = "partitioned"
    check.tooth(
        "wrong switch value in one arm",
        broken != previous_roles("B0", config),
        "B0's analysis-loop switch set to the partitioned value must not "
        "match the previous revision's B0",
    )
    missing = comparable("B3", config)
    missing.pop("arrangement_method", None)
    check.tooth(
        "one switch dropped from an arm",
        missing != previous_roles("B3", config),
        "B3 without the method-arrangement switch must not match the "
        "previous revision's B3",
    )
    pulsed = [c for c in campaign.configurations if c.pulsed]
    if pulsed:
        swapped = comparable("A1", pulsed[0])
        swapped["defer_per_run"] = "<defer_per_run_lifted>"
        check.tooth(
            "the wrong per-run artifact handed to an arm",
            swapped != previous_roles("A1", pulsed[0]),
            "the evaluation phase's block arm runs the committed input file, "
            "so it takes the artifact stamped for the base constraint set; "
            "handing it the lifted input file's artifact must not match",
        )
        folded = comparable("B3", pulsed[0])
        theirs = dict(_previous_environment("B3", pulsed[0], campaign))
        theirs.pop("PROCESS_ARCH_OUTER", None)
        check.tooth(
            "the fold read as a difference",
            folded == _roles(theirs, pulsed[0], revision="previous"),
            "the previous revision needed a second switch to say that the "
            "block schedule runs once; the partitioned loop now means that by "
            "itself.  Dropping that switch from the previous revision's side "
            "must leave the two asking for the same thing -- if it did not, "
            "the comparison above would be treating a rename as a change",
        )
        unfolded = dict(_previous_environment("B3", pulsed[0], campaign))
        unfolded["PROCESS_ARCH_OUTER"] = "verify"
        check.tooth(
            "a schedule policy the fold does not cover",
            folded != _roles(unfolded, pulsed[0], revision="previous"),
            "the fold drops the previous revision's schedule switch only where "
            "its value is the one the partitioned loop now implies; the other "
            "value must survive as a role of its own and make the comparison "
            "fail",
        )

    steady = [c for c in campaign.configurations if not c.pulsed]
    if steady:
        caught = False
        try:
            arms_mod.env_for("A0p", steady[0], campaign=campaign, pending_ok=True)
        except sw.SwitchError:
            caught = True
        check.tooth(
            "a skipped arm asked to compose",
            caught,
            f"A0p on {steady[0].name} is recorded as skipped and must refuse",
        )
    return check


# --------------------------------------------------------------------------
# 2. rungs and the matrix
# --------------------------------------------------------------------------


def check_rungs() -> Check:
    check = Check(
        name="rungs",
        binds="the plan's switch matrix and rung table are reproduced by the "
        "arm records",
        population=(
            f"{len(arms_mod.PLAN_MATRIX)} matrix rows x 8 arms = "
            f"{len(arms_mod.PLAN_MATRIX) * 8} cells; "
            f"{2 * len(arms_mod.RUNGS)} rung steps"
        ),
    )
    regenerated = arms_mod.matrix()
    for row, cells in arms_mod.PLAN_MATRIX.items():
        for index, expected in enumerate(cells):
            check.n_compared += 1
            got = regenerated[row][index]
            if got != expected:
                check.fail(
                    f"matrix row {row!r}, column {arms_mod.MATRIX_ORDER[index]}: "
                    f"regenerated {got!r}, the plan prints {expected!r}"
                )

    for rung_row in arms_mod.RUNGS:
        for step, declared in (
            (rung_row.phase_a, rung_row.changes_a),
            (rung_row.phase_b, rung_row.changes_b),
        ):
            check.n_compared += 1
            computed = tuple(arms_mod.rung(*step))
            if computed != tuple(declared):
                check.fail(
                    f"rung {step[0]} -> {step[1]}: the arms differ in "
                    f"{computed}, the plan declares {tuple(declared)}"
                )
        check.n_compared += 1
        twins = tuple(arms_mod.rung(*rung_row.phase_a)) == tuple(
            arms_mod.rung(*rung_row.phase_b)
        )
        if twins != rung_row.same_in_both_phases:
            check.fail(
                f"rung {rung_row.phase_a} / {rung_row.phase_b}: the two "
                f"phases' steps "
                f"{'do' if twins else 'do not'} move the same fields, but the "
                f"plan declares they "
                f"{'do' if rung_row.same_in_both_phases else 'do not'}"
            )

    # No arm, rung or column may name the removed arm.
    check.n_compared += 1
    for retired in sw.RETIRED_ARM_NAMES:
        if retired in arms_mod.ARMS:
            check.fail(f"{retired} was removed from the arm set but is present")

    # --- teeth -------------------------------------------------------------
    ladder = arms_mod.RUNGS[2]
    wrong = tuple(f for f in ladder.changes_b if f != "defer_per_run")
    check.tooth(
        "a wrong expected difference in the rung table",
        tuple(arms_mod.rung(*ladder.phase_b)) != wrong,
        "the partitioning rung with one deferral removed from its declared "
        "difference must not match the computed difference",
    )
    row = "burn-time owner"
    wrong_cells = list(arms_mod.PLAN_MATRIX[row])
    wrong_cells[6] = "loop"
    check.tooth(
        "a wrong cell in the transcribed matrix",
        tuple(wrong_cells) != regenerated[row],
        "the burn-time owner of B1 written as the loop must not match the "
        "regenerated row",
    )
    check.tooth(
        "an arm compared with itself",
        arms_mod.rung("B3", "B3") == {},
        "an arm differs from itself in nothing, so an empty difference is "
        "reachable and a non-empty one means something",
    )
    return check


# --------------------------------------------------------------------------
# 3. capability
# --------------------------------------------------------------------------


def check_capability(campaign: Campaign, *, timeout: int = 600) -> Check:
    check = Check(
        name="capability",
        binds="the tree resolves every switch an arm asks for, and an arm "
        "asking for a switch the tree does not implement is refused",
        population="every arm/configuration pair whose arms are active",
    )
    if not (campaign.tree / "process" / "__init__.py").exists():
        check.fail(
            f"no PROCESS package at {campaign.tree}; the capability of a tree "
            f"that is not there cannot be measured, and a fallback to another "
            f"tree would measure code nobody asked for"
        )
        return check

    jobs: list[tuple[str, Any, dict[str, str], dict[str, str]]] = []
    refused_expected = 0
    for config in campaign.configurations:
        for name, arm in arms_mod.ARMS.items():
            if name in config.skips:
                continue
            terms = arm.terms(config, pin_hex=_PIN_HEX, campaign=campaign, seed=0)
            pending = sw.unimplemented(terms)
            check.n_compared += 1
            if pending:
                refused_expected += 1
                caught = False
                try:
                    arms_mod.env_for(
                        name, config, seed=0, pin_hex=_PIN_HEX, campaign=campaign
                    )
                except sw.SwitchError as exc:
                    caught = all(term in str(exc) for term in pending)
                if not caught:
                    check.fail(
                        f"{name} on {config.name} asks for {pending}, which no "
                        f"tree implements, and was not refused by name"
                    )
                continue
            env = arms_mod.env_for(
                name, config, seed=0, pin_hex=_PIN_HEX, campaign=campaign
            )
            jobs.append((f"{name}/{config.name}", terms, env, {}))

    def run(job):
        label, terms, env, _ = job
        try:
            cap = sw.assert_capable(
                campaign.tree, terms, env, label=label, timeout=timeout
            )
            return label, None, cap
        except sw.SwitchError as exc:
            return label, str(exc), None

    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=max(1, campaign.workers)) as pool:
        for label, error, cap in pool.map(run, jobs):
            if error is not None:
                check.fail(f"{label}: {error}")
                continue
            tree_of_child = str(Path(cap.process_file or "").resolve().parent.parent)
            if tree_of_child != str(Path(campaign.tree).resolve()):
                check.fail(
                    f"{label}: the probe imported {cap.process_file}, which is "
                    f"not the tree under test {campaign.tree}"
                )
    check.note(
        f"{len(jobs)} arm/configuration pair(s) probed in "
        f"{time.perf_counter() - started:.1f} s at {campaign.workers} workers; "
        f"{refused_expected} pair(s) refused before probing because a declared "
        f"switch is not implemented by any tree"
    )

    # --- teeth -------------------------------------------------------------
    reference_env = sw.base_environment(campaign.tree, runs_dir=campaign.runs_dir)
    bogus = sw.Switch(
        term="tooth_absent_switch",
        driver_name="PROCESS_ARCH_A_SWITCH_THAT_DOES_NOT_EXIST",
        intended_name=None,
        value_kind="enum",
        values=("on",),
        composed=True,
        readbacks=((sw.CALLER, "A_NAME_THAT_DOES_NOT_EXIST"),),
        resolved_as_asked=lambda r, v: True,
    )
    sw.REGISTRY["tooth_absent_switch"] = bogus
    try:
        env = dict(reference_env)
        env[bogus.driver_name] = "on"
        caught = False
        try:
            sw.assert_capable(
                campaign.tree,
                {"tooth_absent_switch": "on"},
                env,
                label="tooth",
                timeout=timeout,
            )
        except sw.SwitchError as exc:
            caught = "A_NAME_THAT_DOES_NOT_EXIST" in str(exc)
        check.tooth(
            "an arm asks for a switch the tree does not implement",
            caught,
            "a switch name no tree defines must be refused, never ignored",
        )

        wrong_value = sw.Switch(
            term="tooth_wrong_value",
            driver_name="PROCESS_ARCH_MDA",
            intended_name=None,
            value_kind="enum",
            values=("partitioned",),
            composed=True,
            readbacks=((sw.MODULE_SOLVE, "MDA_MODE"),),
            resolved_as_asked=lambda r, v: r.get(f"{sw.MODULE_SOLVE}.MDA_MODE")
            == v,
        )
        sw.REGISTRY["tooth_wrong_value"] = wrong_value
        env = dict(reference_env)  # the switch deliberately NOT set
        caught = False
        try:
            sw.assert_capable(
                campaign.tree,
                {"tooth_wrong_value": "partitioned"},
                env,
                label="tooth",
                timeout=timeout,
            )
        except sw.SwitchError as exc:
            caught = "resolved" in str(exc)
        check.tooth(
            "the driver resolves a switch differently from what was asked",
            caught,
            "asking for the partitioned loop while the environment does not "
            "carry it must be refused",
        )
    finally:
        sw.REGISTRY.pop("tooth_absent_switch", None)
        sw.REGISTRY.pop("tooth_wrong_value", None)

    # --- every intended name resolves, and every retired one refuses -------
    #
    # Measured, not declared.  The registry says which names this revision
    # uses and which it retired; the tree says the same thing in its own
    # source.  If the two ever disagree the harness is describing a driver it
    # is not running -- which is the failure this whole module exists for.
    probe = sw.probe(
        campaign.tree,
        reference_env,
        readbacks=(*sw.counter_readbacks(), (sw.SOLVER, "RETIRED_SWITCHES")),
        timeout=timeout,
    )
    if not probe.ok:
        check.fail(f"the capability probe could not import the tree: {probe.error}")
    else:
        composed_terms = [
            term
            for term, entry in sw.REGISTRY.items()
            if entry.composed and entry.implemented
        ]
        unresolved = [
            f"{term} ({sw.REGISTRY[term].driver_name}) -> {module}.{attribute}"
            for term in composed_terms
            for module, attribute in sw.REGISTRY[term].readbacks
            if f"{module}.{attribute}" not in probe.resolved
        ]
        check.n_compared += len(composed_terms)
        if unresolved:
            check.fail(
                "the tree resolves no readback for "
                + "; ".join(unresolved)
                + " -- a switch the tree does not implement runs a different "
                "arrangement under this arm's name"
            )
        check.note(
            f"{len(composed_terms)} composed switch term(s) resolve every "
            f"readback the registry names, on the tree under test"
        )

        in_driver = probe.value(sw.SOLVER, "RETIRED_SWITCHES")
        in_registry = sorted(sw.retired_names())
        check.n_compared += 1
        if not isinstance(in_driver, dict):
            check.fail(
                f"the tree has no {sw.SOLVER}.RETIRED_SWITCHES, so the driver "
                f"refuses no stale switch name and the harness's list is a "
                f"claim about a tree that cannot keep it"
            )
        elif sorted(in_driver) != in_registry:
            check.fail(
                f"the driver retires {sorted(in_driver)} but the registry "
                f"retires {in_registry}; a name on one list and not the other "
                f"is either a switch the harness clears while the driver still "
                f"honours it, or one the harness refuses that the driver has "
                f"never heard of"
            )
        else:
            check.note(
                f"{len(in_registry)} retired switch name(s), identical in the "
                f"registry and in the driver's own list: "
                f"{', '.join(in_registry)}"
            )

        # --- the counters the harness is about to record ------------------
        #
        # A counter is not a switch: nothing composes it and no arm refuses on
        # it.  But every one of them becomes a field of every run record, and a
        # tree that does not expose one would fill that field with a null that
        # a reader could not tell from "this run did not get that far".  Said
        # here, in the probe's own report, rather than discovered afterwards.
        absent = [
            f"{module}.{attribute}"
            for module, attribute in sw.DIAGNOSTIC_READBACKS
            if f"{module}.{attribute}" not in probe.resolved
        ]
        check.n_compared += len(sw.DIAGNOSTIC_READBACKS)
        if absent:
            check.fail(
                "the tree exposes no counter for "
                + "; ".join(absent)
                + " -- every one of them is a declared field of every run "
                "record, and a tree that has none writes a null a reader "
                "cannot tell from a run that stopped early"
            )
        else:
            check.note(
                f"{len(sw.DIAGNOSTIC_READBACKS)} driver counter(s) resolve on "
                f"the tree under test, each a declared record field"
            )

    for retired in sorted(sw.retired_names()):
        caught = False
        try:
            sw.assert_no_retired({retired: "anything", **reference_env})
        except sw.SwitchError:
            caught = True
        check.tooth(
            f"the retired name {retired} present in the environment",
            caught,
            "a retired switch name must be refused, not cleared and forgotten: "
            "an ignored one runs a different arrangement under the right name",
        )

    refused_by_driver = sw.probe(
        campaign.tree,
        {**reference_env, "PROCESS_ARCH_OUTER": "trust"},
        timeout=timeout,
    )
    check.tooth(
        "the driver's own refusal of a retired name",
        (not refused_by_driver.ok)
        and "ArchitectureRefusal" in (refused_by_driver.error or ""),
        "the guard is in the driver as well as in the harness, so a caller "
        "that bypasses the harness is refused too: the tree must fail to "
        f"import with a retired name set ({refused_by_driver.error})",
    )

    # The probe must import the tree PYTHONPATH names, whatever directory the
    # button was pressed from.  This is a *measured* property, not a claim:
    # the child is started with its working directory inside a scratch tree
    # that contains a decoy `process/` package, which is exactly the shape the
    # repository root has.  Without the safe-path flag Python puts the cwd at
    # the head of sys.path and the decoy wins; with it, the copy does.
    #
    # The defect this tooth exists for was live: pressing the button from the
    # repository root made this check fail with 25 of 54 mismatched, because
    # the probe imported the repository's own `process/` while the environment
    # named the experiment's copy.  A verdict that depends on where the button
    # is pressed is not a verdict.
    decoy = Path(tempfile.mkdtemp(prefix="capability_decoy_"))
    try:
        package = decoy / "process"
        package.mkdir()
        (package / "__init__.py").write_text(
            '__file__ = "a decoy that must never be imported"\n'
            'raise ImportError("the decoy process package was imported: the '
            'working directory shadowed PYTHONPATH")\n'
        )
        here = Path.cwd()
        try:
            os.chdir(decoy)
            from_decoy = sw.probe(campaign.tree, reference_env, timeout=timeout)
        finally:
            os.chdir(here)
        imported = Path(from_decoy.process_file or "").resolve()
        expected = (Path(campaign.tree) / "process" / "__init__.py").resolve()
        check.n_compared += 1
        if not (from_decoy.ok and imported == expected):
            check.fail(
                f"the probe started from a directory holding a decoy process "
                f"package imported {from_decoy.process_file!r}, not "
                f"{expected}: the working directory shadows PYTHONPATH and the "
                f"check's verdict depends on where the button was pressed"
            )
        check.tooth(
            "the working directory holds a package that shadows the tree",
            from_decoy.ok and imported == expected,
            f"the probe run with its working directory inside a scratch tree "
            f"containing a decoy process/__init__.py still imported "
            f"{imported}, the tree under test — so the button's verdict does "
            f"not depend on where it is pressed",
        )
    finally:
        shutil.rmtree(decoy, ignore_errors=True)
    return check


# --------------------------------------------------------------------------
# 4. provenance
# --------------------------------------------------------------------------


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def check_provenance(campaign: Campaign) -> Check:
    check = Check(
        name="provenance",
        binds="a modified tracked file and an untracked file are recorded "
        "separately, and only the first marks the tree dirty",
        population="one scratch repository, three states",
    )
    scratch = Path(tempfile.mkdtemp(prefix="harness_provenance_"))
    try:
        repo = scratch / "tree"
        repo.mkdir()
        _git(repo.parent, "init", "-q", "-b", "main", str(repo))
        _git(repo, "config", "user.email", "selfcheck@example.invalid")
        _git(repo, "config", "user.name", "harness selfcheck")
        tracked = repo / "tracked.txt"
        tracked.write_text("one\n")
        _git(repo, "add", "tracked.txt")
        _git(repo, "commit", "-q", "-m", "initial")

        clean = prov.git_stamp(repo)
        check.n_compared += 1
        if (
            clean["tree_modified_tracked_n"],
            clean["tree_untracked_paths_n"],
            clean["tree_git_dirty"],
        ) != (0, 0, False):
            check.fail(f"a clean scratch tree stamped {clean}")

        tracked.write_text("two\n")
        modified = prov.git_stamp(repo)
        check.n_compared += 1
        if modified["tree_modified_tracked_n"] != 1:
            check.fail(
                f"a modified tracked file was not recorded: {modified}"
            )
        if modified["tree_untracked_paths_n"] != 0:
            check.fail(
                f"a modified tracked file was counted as untracked: {modified}"
            )
        if not modified["tree_git_dirty"]:
            check.fail("a modified tracked file did not mark the tree dirty")
        check.tooth(
            "a tracked file modified",
            modified["tree_modified_tracked_n"] == 1
            and modified["tree_untracked_paths_n"] == 0
            and modified["tree_git_dirty"] is True,
            "the one kind of change that can move a measurement must be "
            "counted, and must mark the tree dirty",
        )

        tracked.write_text("one\n")
        (repo / "draft_beside_the_runner.md").write_text("notes\n")
        untracked = prov.git_stamp(repo)
        check.n_compared += 1
        if untracked["tree_untracked_paths_n"] != 1:
            check.fail(f"an untracked file was not recorded: {untracked}")
        if untracked["tree_modified_tracked_n"] != 0:
            check.fail(
                f"an untracked file was counted as a tracked modification: "
                f"{untracked}"
            )
        if untracked["tree_git_dirty"]:
            check.fail("an untracked file marked the tree dirty")
        check.tooth(
            "an untracked file beside the runner",
            untracked["tree_untracked_paths_n"] == 1
            and untracked["tree_modified_tracked_n"] == 0
            and untracked["tree_git_dirty"] is False,
            "a draft file must be recorded as context and must not mark the "
            "tree dirty — the false alarm that stamped a whole set of records",
        )
        check.note(
            f"untracked path recorded as "
            f"{untracked['tree_untracked_paths']}"
        )
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    # The exact-tree assertion (trap T6) refuses a prefix match.
    check.n_compared += 1
    if repository_tree_campaign().is_experiment_copy:
        check.fail(
            "a campaign pointed at the repository's own tree reports itself "
            "as the experiment's copy; records would be made against a tree "
            "nobody asked for"
        )
    check.tooth(
        "a campaign pointed at a tree that is not the experiment's copy",
        (not repository_tree_campaign().is_experiment_copy)
        and default_campaign().is_experiment_copy,
        "the checking campaign must not pass for the production one; the "
        "runner refuses every campaign stage on that ground, so a record "
        "cannot be made against the wrong tree by forgetting a flag",
    )

    caught = False
    try:
        prov.assert_tree(Path(campaign.tree).parent)
    except (prov.ProvenanceError, ImportError, ModuleNotFoundError):
        caught = True
    check.tooth(
        "the tree asserted by a prefix instead of exactly",
        caught,
        "the parent of the tree under test must be refused: a prefix match "
        "passes on the main checkout even when the run is meant to measure a "
        "worktree",
    )
    return check


# --------------------------------------------------------------------------
# 5. data
# --------------------------------------------------------------------------


def _stage_data(source: Path, destination: Path) -> Path:
    """A throwaway copy of the data directory.  The real one is never touched."""
    shutil.copytree(source, destination)
    return destination


#: The scratch fixture's own verdict records: three gates, since one is enough
#: for a break but three make "1 of 3 disagree" a count rather than a tautology.
_SCRATCH_GATES: tuple[str, ...] = ("a_first_gate", "a_second_gate", "a_third_gate")


def _scratch_records(destination: Path) -> tuple[int, int]:
    """Write a records directory this check owns: verdicts and stage records.

    **Synthesised, never copied.**  A self-check builds its own fixtures: one
    that read the tree's real records would report FAIL on a tree that has not
    been pressed yet — a fresh worktree, or a trial merge — which is a
    statement about the directory and not about the mechanism this check
    binds.  (It did exactly that, and this is the fix.)  The real records are
    still read, further down, where their freshness is *noted*.

    The four stage records are the four the plan's §4 is rendered from, each
    with the least content the renderer accepts, so that the breaks below run
    through the renderer itself rather than through a function beside it.
    """
    destination = Path(destination)
    now = _dt.datetime.now().isoformat(timespec="seconds")
    for index, name in enumerate(_SCRATCH_GATES):
        path = destination / name / "gate.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "gate": name,
                    "plan_name": None,
                    "binds": "a scratch fixture, owned by the self-check",
                    "verdict": "PASS",
                    "population": f"{index + 1} scratch thing(s)",
                    "n_compared": index + 1,
                    "n_mismatched": 0,
                    "generated": now,
                    "tree_git_head": "0" * 40,
                    "teeth": [{"tooth": "a scratch tooth", "caught": True}],
                },
                indent=2,
            )
            + "\n"
        )
    rows = [
        {
            "gate": name,
            "plan_name": None,
            "binds": "a scratch fixture",
            "verdict": "PASS",
            "population": "scratch",
            "n_compared": index + 1,
            "n_mismatched": 0,
            "n_teeth": 1,
            "n_teeth_tripped": 1,
            "record": f"{name}/gate.json",
        }
        for index, name in enumerate(_SCRATCH_GATES)
    ]
    stage_records = {
        "gate_table": {
            "what_this_is": "a scratch gate table, owned by the self-check",
            "caption": "One row per scratch gate.",
            "population": f"{len(rows)} scratch gate(s)",
            "n_gates": len(rows),
            "n_pass": len(rows),
            "n_fail": 0,
            "n_not_run": 0,
            "n_teeth": len(rows),
            "n_teeth_tripped": len(rows),
            "rows": rows,
            "markdown": "| gate | verdict |\n|---|---|\n"
            + "\n".join(f"| `{row['gate']}` | **PASS** |" for row in rows),
        }
    }
    for stage in ("tally_evaluation", "tally_optimisation", "recomputed_tables"):
        stage_records[stage] = {
            "population": "a scratch population of 1",
            "runs_provenance": {"n_records": 0, "heads": []},
            "tables": [
                {
                    "table": f"a_scratch_table_of_{stage}",
                    "caption": "a scratch table, owned by the self-check.",
                    "denominator": 1,
                    "denominator_is": "one scratch row",
                    "columns": ["a"],
                    "rows": [{"a": 1}],
                    "markdown": "| a |\n|---|\n| 1 |",
                }
            ],
        }
    for stage, record in stage_records.items():
        path = destination / stage / "measurements.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        if stage == "gate_table":
            record["records_read"] = framework.survey_records(
                destination, ("*/gate.json",)
            )
        path.write_text(json.dumps(record, indent=2) + "\n")
    return len(_SCRATCH_GATES), len(stage_records)


def check_stage_provenance(campaign: Campaign) -> Check:
    """What a stage read, and whether a consumer can still trust it.

    The plan's results section is rendered from the ``gate_table`` **stage**
    record rather than from the verdicts themselves, so a gate re-run after
    that stage would be published as it was, not as it is — silently, with the
    same table and the same PASS or FAIL.  It happened: a re-render reproduced
    a failing row byte for byte after the gate had passed.

    So the stage stamps the records it read — path, bytes, commit, time,
    verdict — and the renderer refuses when they have moved.  The four breaks
    below are the four ways they can move, each made on a **copy** of this
    tree's own records in a scratch directory; nothing on disk is written.

    The census records are **surveyed** here rather than broken: what refuses
    an unstamped one is the stage that reads it (gate ``artifacts_census``,
    whose teeth do the breaking), and re-taking a census is a PROCESS run this
    check may not start.  What this check does is name them, so that a record
    a stamp survey cannot place is never merely absent from the survey.
    """
    from harness.child import census as census_mod  # noqa: PLC0415 - one direction
    from harness.measurement import plan_tables as plan_tables_mod  # noqa: PLC0415

    check = Check(
        name="stage provenance",
        binds=(
            "a stage record says which records it read, and a consumer of it "
            "refuses when those records have moved; a census record says "
            "which tree took it"
        ),
    )
    section = plan_tables_mod.SECTIONS[0]
    with tempfile.TemporaryDirectory(prefix="stage_provenance_") as scratch:
        root = Path(scratch)
        n_verdicts, n_stages = _scratch_records(root)
        check.n_compared += n_verdicts + n_stages
        check.population = (
            f"a scratch records directory this check writes itself — "
            f"{n_verdicts} verdict record(s) and {n_stages} stage record(s) — "
            f"broken 4 ways; a scratch census record, stamped and unstamped; "
            f"the census stamping path, run; and whatever live records this "
            f"tree holds, surveyed and named"
        )
        stage_path = root / section.stage / "measurements.json"
        original = json.loads(stage_path.read_text())
        block = original["records_read"]
        check.note(
            f"the scratch {section.stage} record names {block['n_records']} "
            f"verdict record(s) it read, matched by {block['patterns']}"
        )

        def renders() -> tuple[bool, str]:
            """Whether the renderer accepts the scratch records, and why not."""
            try:
                plan_tables_mod.render(campaign, root)
            except plan_tables_mod.PlanTablesError as exc:
                # Two lines, not one: the first says a stage record is stale
                # and the second is the row that names the gate, both commits
                # and both times — which is the half a reader acts on.
                said = " | ".join(str(exc).splitlines()[:2])
                return False, f"PlanTablesError: {said[:320]}"
            return True, "it rendered"

        agreed, why_agreed = renders()
        if not agreed:
            check.fail(
                f"the renderer refuses this tree's own unmodified records: "
                f"{why_agreed}"
            )

        # 1. a verdict re-made after the stage record was written: the case
        #    that was reproduced byte for byte in the plan.
        doctored = sorted(root.glob("*/gate.json"))[0]
        keep = doctored.read_bytes()
        verdict = json.loads(keep)
        was_commit, was_time = verdict.get("tree_git_head"), verdict.get("generated")
        verdict["tree_git_head"] = "e" * 40
        verdict["generated"] = "2099-01-01T00:00:00"
        verdict["verdict"] = "PASS" if verdict.get("verdict") != "PASS" else "FAIL"
        doctored.write_text(json.dumps(verdict, indent=2) + "\n")
        rendered, why = renders()
        check.tooth(
            "a verdict re-made at a later commit after the stage record was "
            "written",
            not rendered and agreed,
            f"{doctored.parent.name}'s verdict moved from "
            f"{str(was_commit)[:8]} at {was_time} to e2099 in the scratch "
            f"copy: "
            + (f"refused — {why}" if not rendered else "NOT refused")
            + "; the same records unmodified: "
            + (why_agreed if agreed else f"REFUSED TOO — {why_agreed}"),
        )
        doctored.write_bytes(keep)

        # 2. a gate run *after* the stage: a verdict nobody read.  Only the
        #    declared pattern can find this one, which is why the block
        #    carries the pattern and not just the files it matched.
        appeared = root / "a_gate_run_since" / "gate.json"
        appeared.parent.mkdir(parents=True, exist_ok=True)
        appeared.write_text(
            json.dumps(
                {
                    "gate": "a_gate_run_since",
                    "verdict": "FAIL",
                    "generated": "2099-01-01T00:00:00",
                    "tree_git_head": "f" * 40,
                },
                indent=2,
            )
            + "\n"
        )
        rendered, why = renders()
        check.tooth(
            "a verdict record written after the stage record",
            not rendered,
            "a gate.json that no stage ever read, added to the scratch copy: "
            + (f"refused — {why}" if not rendered else "NOT refused"),
        )
        shutil.rmtree(appeared.parent)

        # 3. a verdict the stage read that is no longer there.
        removed = sorted(root.glob("*/gate.json"))[0]
        keep = removed.read_bytes()
        removed.unlink()
        rendered, why = renders()
        check.tooth(
            "a verdict record the stage read and that is gone",
            not rendered,
            f"{removed.parent.name}'s verdict deleted from the scratch copy: "
            + (f"refused — {why}" if not rendered else "NOT refused"),
        )
        removed.write_bytes(keep)

        # 4. the shape every stage record had before this contract: numbers,
        #    and nothing saying what they were computed from.
        without = dict(original)
        without.pop("records_read", None)
        stage_path.write_text(json.dumps(without, indent=2) + "\n")
        rendered, why = renders()
        check.tooth(
            "a stage record that does not say what it read",
            not rendered,
            "the records_read block removed from the scratch copy of the "
            f"{section.stage} record: "
            + (f"refused — {why}" if not rendered else "NOT refused"),
        )
        stage_path.write_text(json.dumps(original, indent=2) + "\n")

    # --- a census record the check writes itself, stamped and unstamped ---
    # The census contract, exercised without a census on disk and without
    # starting PROCESS: the reader refuses an unstamped record, --resume does
    # not keep one (it is re-taken, as pool.run re-runs an incomplete run
    # record), and both accept the same record once the fields are there.
    with tempfile.TemporaryDirectory(prefix="scratch_census_") as scratch:
        directory = Path(scratch)
        (directory / "census.json").write_text(
            json.dumps(
                {
                    "configuration": "a_scratch_configuration",
                    "entry": "evaluation",
                    "read_census": True,
                    "writes_by_node": {},
                }
            )
        )
        bare = {"record_format": "census-1", "campaign_phase": "census"}
        (directory / "metrics.json").write_text(json.dumps(bare))
        reader_refused, reader_said = _must_refuse_here(
            lambda: census_mod.assert_stamped(
                json.loads((directory / "metrics.json").read_text()),
                where="the self-check's scratch census",
            )
        )
        kept_unstamped, why_unstamped = census_mod.resume_keeps(
            directory,
            configuration="a_scratch_configuration",
            entry="evaluation",
            read_census=True,
        )
        stamped = dict(bare)
        stamped["record_format"] = census_mod.RECORD_FORMAT
        stamped.update({name: None for name in census_mod.STAMP_FIELDS})
        (directory / "metrics.json").write_text(json.dumps(stamped))
        reader_accepted, _ = _must_refuse_here(
            lambda: census_mod.assert_stamped(
                json.loads((directory / "metrics.json").read_text()),
                where="the self-check's scratch census",
            )
        )
        kept_stamped, why_stamped = census_mod.resume_keeps(
            directory,
            configuration="a_scratch_configuration",
            entry="evaluation",
            read_census=True,
        )
    check.n_compared += 2
    check.tooth(
        "a scratch census record with no tree stamp",
        reader_refused
        and not reader_accepted
        and not kept_unstamped
        and kept_stamped,
        "a census record this check wrote, without the stamp: the reader "
        + (f"refused ({reader_said})" if reader_refused else "DID NOT refuse")
        + " and --resume "
        + (
            f"did not keep it, so it is re-taken — {why_unstamped[:110]}"
            if not kept_unstamped
            else "KEPT it"
        )
        + "; with the stamp: the reader "
        + ("accepted" if not reader_accepted else "REFUSED it too")
        + " and --resume "
        + ("kept it" if kept_stamped else f"did NOT keep it — {why_stamped[:110]}"),
    )

    # --- and the state of the real records, read rather than failed on ---
    live = Path(campaign.runs_dir) / framework.GATES_SUBPATH / section.stage
    live_record = live / "measurements.json"
    if live_record.exists():
        check.n_compared += 1
        try:
            check.note(
                "the records on disk now: "
                + plan_tables_mod.assert_stage_read_what_is_there(
                    json.loads(live_record.read_text()),
                    live.parent,
                    section,
                )
            )
        except plan_tables_mod.PlanTablesError as exc:
            check.note(
                "the records on disk now: the renderer would REFUSE — "
                + " | ".join(str(exc).splitlines()[:2])[:320]
                + f".  That is the order rule working ({section.stage} is "
                f"pressed after the gates, not before), not a failure of this "
                f"check."
            )

    # --- the stamping path a census child runs ---------------------------
    # The code itself, not a restatement of it: a check that rebuilt the stamp
    # beside the child would pass while the child stamped nothing.  It is the
    # only thing that can be said about a census record here without starting
    # PROCESS, which this check may not do.
    check.n_compared += 1
    fresh_stamp = census_mod.tree_stamp(
        campaign.tree,
        process_file=str(Path(campaign.tree) / "process" / "__init__.py"),
        pythonpath=None,
    )
    still_missing = census_mod.missing_stamp_fields(fresh_stamp)
    if still_missing:
        check.fail(
            f"the stamping path a census child runs leaves "
            f"{len(still_missing)} declared field(s) unset: "
            f"{', '.join(still_missing)} — a census taken now would be as "
            f"unplaceable as the ones taken before the contract"
        )
    else:
        check.note(
            f"the stamping path a census child runs produces all "
            f"{len(census_mod.STAMP_FIELDS)} declared field(s); a census taken "
            f"now would be stamped at "
            f"{str(fresh_stamp.get('tree_git_head'))[:8]}"
        )

    # --- the census records, surveyed and named --------------------------
    census_root = Path(campaign.runs_dir) / census_mod.RUNS_SUBPATH
    stamped: list[str] = []
    unstamped: list[str] = []
    for path in sorted(census_root.glob("*/*/metrics.json")):
        check.n_compared += 1
        try:
            record = json.loads(path.read_text())
        except Exception as exc:  # noqa: BLE001
            check.fail(f"{path} is not readable JSON: {exc}")
            continue
        missing = census_mod.missing_stamp_fields(record)
        where = str(path.relative_to(census_root))
        if missing:
            unstamped.append(
                f"{where} ({record.get('record_format')}, "
                f"{len(missing)} of {len(census_mod.STAMP_FIELDS)} field(s) "
                f"missing, commit reachable only as "
                f"provenance.tree_git_head = "
                f"{str((record.get('provenance') or {}).get('tree_git_head'))[:8]})"
            )
        else:
            stamped.append(f"{where} at {str(record.get('tree_git_head'))[:8]}")
    if not stamped and not unstamped and not live_record.exists():
        check.note(
            "this tree holds no verdict record, no stage record and no census "
            "record — a fresh worktree, or a trial merge, before its first "
            "press.  The scratch fixture above is the whole population of the "
            "breaks, which is why it is written here rather than read: a "
            "self-check that needed a press to pass would fail on every tree "
            "that has not had one."
        )
    else:
        check.note(
            f"census records: {len(stamped)} carry the tree stamp "
            f"({', '.join(stamped) or 'none'}); {len(unstamped)} do not "
            f"({'; '.join(unstamped) or 'none'})"
        )
    if unstamped:
        check.note(
            f"the {len(unstamped)} unstamped record(s) are named rather than "
            f"failed here: a stamp survey cannot place them, the stage that "
            f"reads a census refuses one by name (gate artifacts_census), and "
            f"re-taking a census is a PROCESS run this check may not start"
        )
    return check


def check_data(campaign: Campaign) -> Check:
    """The committed data is the source's, and the record says whose.

    ``harness/data/`` holds the files the copied driver and the harness read.
    Each was copied from the repository at a recorded commit and must still be
    byte-identical to it.  Two comparisons, not one: the file's sha256 against
    the one the record carries, **and** the record's sha256 against the source
    read back from the commit -- so regenerating the record cannot be the way a
    changed file becomes blessed.

    The moved predicate module ``harness/ystate.py`` is checked on the criterion
    the copied driver carries: its whole diff against its source at the recorded
    commit must be exactly the hunks the record holds, **and** its post-edit
    sha256 must be the recorded one.  Both directions are exercised below --- an
    edit with stale hunks is caught by the digest, an edit whose digest was
    updated to match is caught by the hunks.  Where the recorded hunks are a
    *pure addition* the older and stronger claim still applies and is still
    required: remove them again and the remainder is byte-identical to the
    source.  That was the whole of the criterion until task A59
    (driver-predicate-mode) implemented driver change DR5 in this module; the
    re-basing, and why the reconstruction test cannot apply to a module that is
    changed rather than only added to, is recorded in
    ``harness/experiment/data_provenance.py``'s docstring and in the record itself
    (``module.criterion_rebased_by``).

    The *campaign* argument selects the tree the rest of the self-check runs
    against and does not apply here: ``harness/data/`` is the experiment's own
    directory under its own naming scheme whichever tree is being checked, so
    the declared counts are compared against the production campaign's
    configurations in both cases.
    """
    production = default_campaign()
    declared = data_mod.declared_files(production)
    check = Check(
        name="data",
        binds="every committed file the experiment reads is byte-identical to "
        "its source at the recorded commit, the file set matches exactly, and "
        "the predicate module differs from its source by exactly the recorded "
        "hunks and carries the recorded post-edit digest",
        population=(
            f"{len(declared)} committed file(s) in harness/data/ + the moved "
            f"predicate module = {len(declared) + 1} comparisons; and "
            f"{3 * len(production.configurations)} declared counts "
            f"({len(production.configurations)} configurations x "
            f"coupling-state components, iteration variables, constraints)"
        ),
    )
    if not data_mod.PROVENANCE.exists():
        check.fail(
            f"{data_mod.PROVENANCE} is not present; the committed data has no "
            f"provenance record, so there is nothing to check it against and "
            f"an empty comparison would report a zero over nothing"
        )
        return check
    prov = data_mod.load_provenance()

    result = data_mod.verify(
        prov,
        data_mod.DATA_DIR,
        ystate_path=data_mod.YSTATE,
        campaign=production,
    )
    check.n_compared = result.n_declared
    for failure in result.failures:
        check.fail(failure)
    for note in result.notes:
        check.note(note)
    check.note(
        f"{result.n_identical}/{result.n_declared} identical; sources read "
        f"from {', '.join(sorted(result.read_from)) or '(nothing)'}"
    )
    check.note(
        f"the mapping from a role to a file name is config.artifact_file_names() "
        f"under both naming schemes, compared against the list "
        f"data_provenance.py declares; a disagreement raises rather than "
        f"picking a side"
    )

    # --- teeth -------------------------------------------------------------
    # Each perturbation is made on a throwaway copy of harness/data/ and the
    # same verification is re-run against it.  The real directory is never
    # modified.
    victim = declared[1].name  # a copied artifact, not an input file
    teeth: list[tuple[str, str]] = [
        ("one byte changed in a copied file", victim),
        ("a copied file missing", victim),
        ("a file added that the record does not name", "_a_file_nobody_recorded.json"),
        ("a changed file whose recorded sha256 was updated to match", victim),
    ]
    for name, target in teeth:
        with tempfile.TemporaryDirectory() as td:
            staged = _stage_data(data_mod.DATA_DIR, Path(td) / "data")
            path = staged / target
            if name == "a copied file missing":
                path.unlink()
                what = f"removed {target}"
            elif name.startswith("a file added"):
                path.write_text("{}\n")
                what = f"added {target}"
            else:
                raw = bytearray(path.read_bytes())
                raw[0] = raw[0] ^ 0x20 if raw[0] != 0x20 else 0x09
                path.write_bytes(bytes(raw))
                what = f"one byte of {target} changed"
            staged_prov = prov
            if name.startswith("a changed file whose recorded"):
                staged_prov = json.loads(json.dumps(prov))
                staged_prov["files"][target]["sha256"] = data_mod.sha256(
                    path.read_bytes()
                )
                what += ", and the record's sha256 updated to match it"
            broken = data_mod.verify(staged_prov, staged, campaign=None)
            check.tooth(name, not broken.passed, what)

    # --- the predicate module's own two teeth ------------------------------
    #
    # The module is allowed to differ from its source by the recorded hunks, so
    # both halves of that permission have to be shown biting: an edit nobody
    # recorded, and an edit whose recorded digest was updated to match it.  The
    # second is the one that matters after A59 re-based the criterion --- it is
    # exactly the move that would make an unrecorded change look blessed --- and
    # it is caught by the hunks, which the digest cannot be updated to satisfy.
    module_teeth: list[tuple[str, bool]] = [
        ("an unrecorded edit to the predicate module", False),
        (
            "an edited predicate module whose recorded sha256 was updated to "
            "match",
            True,
        ),
    ]
    for name, bless in module_teeth:
        with tempfile.TemporaryDirectory() as td:
            staged_module = Path(td) / "ystate.py"
            raw = bytearray(data_mod.YSTATE.read_bytes())
            # A comment character deep inside the file: a one-byte change that
            # cannot alter what the module computes, so what the tooth proves
            # is that the *check* is sensitive, not that the edit was harmful.
            raw[3] = raw[3] ^ 0x20 if raw[3] != 0x20 else 0x09
            staged_module.write_bytes(bytes(raw))
            staged_prov = json.loads(json.dumps(prov))
            what = "one byte of harness/ystate.py changed"
            if bless:
                staged_prov["module"]["sha256_in_copy"] = data_mod.sha256(
                    staged_module.read_bytes()
                )
                what += ", and the record's sha256 updated to match it"
            broken = data_mod.verify(
                staged_prov,
                data_mod.DATA_DIR,
                ystate_path=staged_module,
                campaign=None,
            )
            check.tooth(name, not broken.passed, what)
    return check


# --------------------------------------------------------------------------
# the previous revision's own composition, executed
# --------------------------------------------------------------------------

_CROSSCHECK_SOURCE = r"""
import json, os, sys
v3 = sys.argv[1]
sys.path.insert(0, v3)
import v3_config as cfg
import v3_runner
import phase_a
out = {}
for configuration in cfg.DECKS:
    for arm in ("R", "B0", "B1", "B3"):
        out["B:%s:%s" % (arm, configuration)] = {
            k: v for k, v in v3_runner.env_for(configuration, arm).items()
            if k.startswith("PROCESS_ARCH") or k == "PROCESS_IDF_PROBE"
        }
    for arm in ("A0", "A1"):
        pin = "0x1.34a0000000000p+10" if configuration in cfg.PULSED else None
        out["A:%s:%s" % (arm, configuration)] = {
            k: v
            for k, v in phase_a.env_for_phase_a(
                configuration, arm, pin_hex=pin
            ).items()
            if k.startswith("PROCESS_ARCH") or k == "PROCESS_IDF_PROBE"
        }
print("@@X@@" + json.dumps(out) + "@@X@@")
"""


def crosscheck_previous(campaign: Campaign) -> Check:
    """Execute the previous revision's composition and compare, once.

    Not one of the four gates and not run by default: it reaches outside this
    package deliberately, to measure the transcription in
    :func:`_previous_environment` instead of trusting it.
    """
    check = Check(
        name="crosscheck-previous",
        binds="the transcription of the previous revision's composition "
        "matches what its own code produces",
        population="6 arms x 3 configurations",
    )
    v3 = Path(campaign.tree) / "arch_surgery" / "MDA_partitioning_experiment_v3"
    if not v3.exists():
        check.note(f"no previous revision at {v3}; not run")
        return check
    # ``-P`` and PYTHONSAFEPATH for the same reason the capability probe
    # carries them: with ``-c``, Python puts the current working directory at
    # the head of ``sys.path``, ahead of everything PYTHONPATH names, so a
    # child started from a directory that happens to hold a ``process/``
    # package would import that one instead of the tree this check is about.
    proc = subprocess.run(
        [sys.executable, "-P", "-c", _CROSSCHECK_SOURCE, str(v3)],
        capture_output=True,
        text=True,
        env={
            **dict(__import__("os").environ),
            "PYTHONPATH": str(campaign.tree),
            "PYTHONSAFEPATH": "1",
        },
        timeout=600,
    )
    body = proc.stdout.split("@@X@@")
    if len(body) < 3:
        check.fail(
            f"the previous revision's composition could not be executed "
            f"(rc={proc.returncode}): {(proc.stderr or '').strip()[-400:]}"
        )
        return check
    theirs_all = json.loads(body[1])
    for config in campaign.configurations:
        for name in _PREVIOUS_NAME:
            if name in config.skips:
                continue
            phase = arms_mod.ARMS[name].phase
            key = f"{phase}:{_PREVIOUS_NAME[name]}:{config.name}"
            if key not in theirs_all:
                check.fail(f"no previous-revision environment for {key}")
                continue
            theirs = _architecture_only(theirs_all[key], config)
            if "PROCESS_ARCH_PIN_BURN_TIME" in theirs:
                theirs["PROCESS_ARCH_PIN_BURN_TIME"] = "<pin>"
            mine = _previous_environment(name, config, campaign)
            check.n_compared += 1
            if mine != theirs:
                check.fail(
                    f"{name} on {config.name}: transcribed {mine}, their code "
                    f"produced {theirs}"
                )

    first = campaign.configurations[0]
    key = f"B:B3:{first.name}"
    if key in theirs_all:
        theirs = _architecture_only(theirs_all[key], first)
        corrupted = dict(_previous_environment("B3", first, campaign))
        corrupted["PROCESS_ARCH_HOIST"] = "feedforward"
        check.tooth(
            "a wrong value in the transcription",
            corrupted != theirs,
            "the per-call deferral transcribed without the lifted variant "
            "must not match what their code produced on a pulsed "
            "configuration",
        )
    return check


# --------------------------------------------------------------------------
# entry point
# --------------------------------------------------------------------------


# --------------------------------------------------------------------------
# 6. the run path
# --------------------------------------------------------------------------
#
# No PROCESS run happens here: what is checked is the machinery around one —
# the record's own contract, the displacement streams' keying, and the
# refusals that stop a run being made against the wrong tree or without a
# switch its arm declares.  The runs themselves are gate GR's business
# (harness/gates/reproduction.py), which is a measurement and takes an hour and a
# half; these are the parts that can be shown to fail in a second.


def _synthetic_record(phase: str) -> dict:
    """A record carrying every declared field, so the contract has a baseline.

    Built from the schema rather than typed out: a field added to the schema
    and forgotten here would make this check fail, which is the point.
    """
    record: dict[str, Any] = {}
    for field in records_mod.fields_for(phase, finished=True):
        _set_path(record, field.name, 0)
    for path in records_mod.CONTRACT[phase]:
        _set_path(record, path, 0)
    record["campaign_phase"] = phase
    record["campaign_run_kind"] = "smoke"
    record["failure_class"] = "ok"
    record["status"] = "ok"
    record["attempts"] = []
    return record


def _set_path(record: dict, path: str, value) -> None:
    """Write *value* at a dotted path, making the intermediate levels dicts.

    A field of the schema and a path of the contract can name the same key at
    different depths (``mfile`` and ``mfile.ifail``); the deeper one wins,
    because it is the one with a shape.
    """
    cursor = record
    parts = path.split(".")
    for step in parts[:-1]:
        if not isinstance(cursor.get(step), dict):
            cursor[step] = {}
        cursor = cursor[step]
    if parts[-1] not in cursor or not isinstance(cursor[parts[-1]], dict):
        cursor[parts[-1]] = value


def check_run_path(campaign: Campaign) -> Check:
    """The record contract, the displacement streams, and the run refusals."""
    check = Check(
        name="run path",
        binds="a record that does not carry what it declares is refused; the "
        "two displacement streams key on what they say they key on; and a run "
        "against the wrong tree, or without a switch its arm declares, is "
        "refused rather than made",
        population=(
            "2 phases x the declared field list; 2 displacement streams; "
            "4 refusals"
        ),
    )

    # --- the record's own contract ---------------------------------------
    for phase in ("A", "B"):
        record = _synthetic_record(phase)
        check.n_compared += 1
        missing = records_mod.missing_fields(record)
        if missing:
            check.fail(
                f"phase {phase}: a record built from the schema itself is "
                f"reported as missing {missing}"
            )
    complete = _synthetic_record("B")

    stripped = json.loads(json.dumps(complete))
    stripped.pop("node_calls_solve_phase")
    caught, message = _must_refuse_here(
        lambda: records_mod.assert_complete(stripped, where="a tooth")
    )
    check.tooth(
        "a declared field removed",
        caught,
        f"a finished record without node_calls_solve_phase must be refused, "
        f"not summarised over ({message})",
    )

    # Half of the audit's ruler pair, which is what a table would read as an
    # accuracy gain rather than a change of ruler.
    half = json.loads(json.dumps(complete))
    half["exit_audit"].pop(records_mod.AUDIT_RULERS[1])
    caught, message = _must_refuse_here(
        lambda: records_mod.assert_complete(half, where="a tooth")
    )
    check.tooth(
        "an exit audit carrying one convergence ruler and not both",
        caught,
        f"the mixed ruler reads lower wherever its denominator binds, so a "
        f"residual table built from records with one column here and two "
        f"there reports a change of ruler as a change of accuracy ({message})",
    )

    unlabelled = json.loads(json.dumps(complete))
    unlabelled["campaign_run_kind"] = "measurement"
    caught, message = _must_refuse_here(
        lambda: records_mod.assert_run_kind(unlabelled)
    )
    check.tooth(
        "a record that does not say what kind of run made it",
        caught,
        f"a gate run and a campaign run are indistinguishable afterwards, and "
        f"one of them is not a measurement ({message})",
    )

    unsummed = json.loads(json.dumps(complete))
    unsummed["node_calls_solve_phase"] = 1000
    unsummed["attempts"] = [
        {"attempt": 1, "node_calls_solve_phase": 400},
        {"attempt": 2, "node_calls_solve_phase": 550},
    ]
    caught, message = _must_refuse_here(
        lambda: records_mod.assert_attempt_summation(unsummed, where="a tooth")
    )
    check.tooth(
        "per-attempt costs that do not sum to the run total",
        caught,
        f"400 + 550 against a total of 1000 must be refused: the cost ratio "
        f"published with and without retried seeds would otherwise be computed "
        f"over quantities that do not decompose the published one ({message})",
    )

    partial = json.loads(json.dumps(complete))
    partial["node_calls_solve_phase"] = 1000
    partial["attempts"] = [
        {"attempt": 1, "node_calls_solve_phase": 1000},
        {"attempt": 2, "node_calls_solve_phase": None},
    ]
    caught, message = _must_refuse_here(
        lambda: records_mod.assert_attempt_summation(partial, where="a tooth")
    )
    check.tooth(
        "per-attempt costs stamped at some attempts and not others",
        caught,
        f"a partial decomposition cannot be summed and must be refused "
        f"({message})",
    )

    # --- the two displacement streams ------------------------------------
    # The design-vector stream is keyed on the variable's NUMBER, which is what
    # lets a lifted design vector — one element longer — give bit-identical
    # factors to every variable it shares with the committed one.  Checked as a
    # computation over two vectors of different length, not asserted.
    committed = [2, 5, 9, 13]
    lifted = [2, 5, 9, 13, 178]
    check.n_compared += len(committed)
    for number in committed:
        a = perturb_mod.design_vector_factor(1, number, campaign.delta)
        b = perturb_mod.design_vector_factor(1, number, campaign.delta)
        if a != b:
            check.fail(f"the design-vector stream is not deterministic at {number}")
    shared_differ = [
        number
        for index, number in enumerate(committed)
        if perturb_mod.design_vector_factor(1, number, campaign.delta)
        != perturb_mod.design_vector_factor(
            1, lifted[index], campaign.delta
        )
    ]
    if shared_differ:
        check.fail(
            f"a design vector one element longer changes the factor of shared "
            f"variables {shared_differ}: the stream is keyed on position, not "
            f"on the variable's number"
        )
    check.note(
        f"the design-vector stream gives bit-identical factors to all "
        f"{len(committed)} shared variables across a {len(committed)}-element "
        f"and a {len(lifted)}-element vector"
    )
    by_position = [
        perturb_mod.design_vector_factor(1, index, campaign.delta)
        for index in range(len(committed))
    ]
    by_number = [
        perturb_mod.design_vector_factor(1, number, campaign.delta)
        for number in committed
    ]
    check.tooth(
        "the design-vector stream keyed on position instead of number",
        by_position != by_number,
        "keying on the position in the vector must give different factors "
        "from keying on the variable's number, or the invariance above is "
        "vacuous",
    )
    check.tooth(
        "the two streams sharing a namespace",
        perturb_mod.coupling_state_factor(1, "178", campaign.delta)
        != perturb_mod.design_vector_factor(1, 178, campaign.delta),
        "a coupling component and an iteration variable that happen to share a "
        "key must not share a factor",
    )

    # --- the refusals -----------------------------------------------------
    config = campaign.configurations[0]
    elsewhere = repository_tree_campaign()
    job = pool_mod.Job(
        phase="B",
        arm="BR",
        config=elsewhere.configurations[0],
        seed=0,
        outdir=Path(elsewhere.runs_dir) / "_never",
        run_kind="smoke",
    )
    caught, message = _must_refuse_here(lambda: pool_mod.run(job, elsewhere))
    check.tooth(
        "a run against a tree that is not the experiment's copy",
        caught,
        f"records are only ever made against the copy; a measurement of "
        f"another tree produced by forgetting a flag is what that separation "
        f"prevents ({message})",
    )

    # The two allowance teeth, **re-pointed** (task A59 (driver-predicate-mode)).
    #
    # The allowance is the one way a run may happen without a switch its arm
    # declares, and it exists for a switch no tree implements yet.  Both of its
    # refusals have to be shown biting.  Until DR5 landed the teeth could bite
    # on a real pending switch -- the predicate trial composed one whose driver
    # change had not been made -- and A57's report predicted that they would go
    # quiet the moment it did.  It has: every switch this harness can compose is
    # now implemented, and `switches.REGISTRY` has no entry left with no driver
    # name.
    #
    # Going quiet is the wrong answer.  A mechanism whose refusals are never
    # exercised is an assertion, not a measurement (protocol section 12), and
    # the mechanism is still live -- the next driver change to be approved and
    # not yet made will use it.  So the teeth are re-pointed onto a **doctored
    # registry**: for the duration of the two checks, the predicate-mode switch
    # is put back the way it stood before DR5 landed (its driver name removed),
    # which is exactly the state the allowance exists for.  The doctoring is the
    # perturbation, it is stated in the tooth's evidence, it is confined to
    # these two checks, and it is undone in a finally.  Nothing outside them
    # sees it: `environment_for` refuses before any subprocess starts.
    #
    # The alternative -- retiring the teeth and noting that nothing is pending
    # -- was rejected: it would leave `pool.environment_for`'s two refusals
    # untested for as long as the registry happens to be complete, and they
    # would be found broken by the task that next needed them.
    pending_mode = next(
        (m for m in campaign.predicate_modes if m != campaign.predicate_mode_default),
        "mixed",
    )
    real_switch = sw.REGISTRY["predicate_mode"]
    check.note(
        f"every switch this harness can compose — the matrix's and the "
        f"predicate trial's alike — is implemented by the tree under test "
        f"(0 registry entries with no driver name), so the two allowance "
        f"teeth bite on a registry doctored back to the state before "
        f"{real_switch.driver_name} landed rather than on a live gap"
    )
    sw.REGISTRY["predicate_mode"] = dataclasses.replace(
        real_switch,
        driver_name=None,
        pending_change="a driver change that has not been made (doctored here)",
    )
    try:
        pending_terms = sw.unimplemented(
            arms_mod.ARMS["B0"].terms(
                config, pin_hex=_PIN_HEX, campaign=campaign,
                predicate_mode=pending_mode,
            )
        )
        if not pending_terms:
            check.fail(
                "the doctored registry did not make the predicate mode look "
                "unimplemented, so the two allowance teeth would pass over an "
                "empty perturbation"
            )
        no_allowance = pool_mod.Job(
            phase="B",
            arm="B0",
            config=config,
            seed=0,
            outdir=Path(campaign.runs_dir) / "_never",
            pin_hex=_PIN_HEX,
            run_kind="smoke",
            predicate_mode=pending_mode,
        )
        caught, message = _must_refuse_here(
            lambda: pool_mod.environment_for(no_allowance, campaign)
        )
        check.tooth(
            "a run asking for a switch the tree does not implement",
            caught,
            f"with the registry doctored back to before "
            f"{real_switch.driver_name} landed, B0 under predicate mode "
            f"{pending_mode!r} declares {list(pending_terms)}, which that "
            f"registry says no tree implements; composing without it would be "
            f"a successful run of a different arm under this arm's name "
            f"({message})",
        )
        over_allowed = pool_mod.Job(
            phase="B",
            arm="B0",
            config=config,
            seed=0,
            outdir=Path(campaign.runs_dir) / "_never",
            pin_hex=_PIN_HEX,
            run_kind="smoke",
            predicate_mode=pending_mode,
            allow_pending=(*pending_terms, "mda"),
        )
        caught, message = _must_refuse_here(
            lambda: pool_mod.environment_for(over_allowed, campaign)
        )
        check.tooth(
            "an allowance naming a switch the tree does implement",
            caught,
            f"an allowance that covers a switch the tree has is an allowance "
            f"nobody checked ({message})",
        )
    finally:
        sw.REGISTRY["predicate_mode"] = real_switch

    # And the live state, checked rather than assumed: with the real registry
    # back, the arm that asks for the trial's ruler composes it and needs no
    # allowance at all.  This is the half the doctored teeth cannot say.
    live = pool_mod.Job(
        phase="B",
        arm="B0",
        config=config,
        seed=0,
        outdir=Path(campaign.runs_dir) / "_never",
        pin_hex=_PIN_HEX,
        run_kind="smoke",
        predicate_mode=pending_mode,
    )
    try:
        live_env, _asked = pool_mod.environment_for(live, campaign)
    except Exception as exc:  # noqa: BLE001 - reported as a failure
        check.fail(
            f"B0 under predicate mode {pending_mode!r} no longer composes: "
            f"{type(exc).__name__}: {exc}"
        )
    else:
        got = live_env.get(real_switch.driver_name)
        if got != pending_mode:
            check.fail(
                f"B0 under predicate mode {pending_mode!r} composed "
                f"{real_switch.driver_name}={got!r}"
            )
        else:
            check.note(
                f"B0 under predicate mode {pending_mode!r} composes "
                f"{real_switch.driver_name}={pending_mode} and needs no "
                f"allowance — the capability probe resolves it"
            )

    # --- the reproduction gate's overrides, and what refuses one ----------
    #
    # Imported here rather than at the top: the reproduction gate imports this
    # module's Check, so a module-level import back would be a cycle.
    from harness.gates import reproduction as reproduction_mod  # noqa: PLC0415

    #
    # The gate that reproduces the previous revision runs two arms with the
    # output-time loop on, because that is how the records it reproduces were
    # made.  That is a departure from the matrix, so it is not allowed to be
    # quiet: it is derived from the matrix rather than listed, refused for a
    # campaign run, refused when it changes nothing, and stamped into every
    # record it produces.
    overridden = {
        name
        for name in arms_mod.ARMS
        if reproduction_mod.reproduction_overrides(name)
    }
    from_matrix = {
        name
        for name, entry in arms_mod.ARMS.items()
        if entry.phase == "B" and entry.output_loop == "none"
    }
    check.n_compared += 1
    if overridden != from_matrix:
        check.fail(
            f"the reproduction gate overrides {sorted(overridden)} but the "
            f"matrix turns the output-time loop off for {sorted(from_matrix)}"
        )
    check.note(
        f"the reproduction gate's overrides are derived from the matrix and "
        f"cover exactly {sorted(overridden)}, the arm(s) whose matrix cell "
        f"turns the output-time loop off; every run it makes is stamped with "
        f"them and audits at the previous revision's position "
        f"({reproduction_mod.REPRODUCTION_AUDIT_POSITION})"
    )
    override_arm = sorted(overridden)[0] if overridden else None
    if override_arm is None:
        check.note("no arm carries a reproduction override, so its teeth bite on nothing")
    else:
        pulsed = next(c for c in campaign.configurations if c.pulsed)
        campaign_job = pool_mod.Job(
            phase="B",
            arm=override_arm,
            config=pulsed,
            seed=0,
            outdir=Path(campaign.runs_dir) / "_never",
            run_kind="campaign",
            reproduction_overrides=reproduction_mod.reproduction_overrides(
                override_arm
            ),
        )
        caught, message = _must_refuse_here(
            lambda: pool_mod.environment_for(campaign_job, campaign)
        )
        check.tooth(
            "a campaign run carrying the reproduction gate's override",
            caught,
            f"the campaign composes each arm from the matrix and nothing else; "
            f"an override that reached it would publish {override_arm} as the "
            f"matrix describes it while running something else ({message})",
        )
        inert_job = pool_mod.Job(
            phase="B",
            arm=override_arm,
            config=pulsed,
            seed=0,
            outdir=Path(campaign.runs_dir) / "_never",
            run_kind="gate",
            reproduction_overrides={"output_loop": "none"},
        )
        caught, message = _must_refuse_here(
            lambda: pool_mod.environment_for(inert_job, campaign)
        )
        check.tooth(
            "a reproduction override that changes nothing",
            caught,
            f"an override set to the value the arm composes anyway is an "
            f"override nobody checked, and would let the declared set drift "
            f"out of step with the matrix unnoticed ({message})",
        )

    # --- the after_run audit position's declared callers -------------------
    #
    # The third way a run may differ from the campaign: where its exit audit
    # is taken.  ``after_run`` has a table of declared callers
    # (records.AUDIT_POSITION_AFTER_RUN_CALLERS) with a reason per row; the
    # pool refuses the position for a campaign run and for any caller the
    # table does not name.  Both refusals are teeth, and the table's rows are
    # checked to be registered stages, so a caller nobody runs cannot be
    # declared.
    from harness.gates import gates as gates_mod  # noqa: PLC0415 - cycle otherwise

    declared_callers = records_mod.AUDIT_POSITION_AFTER_RUN_CALLERS
    registered = set(gates_mod.registry(campaign))
    for caller in declared_callers:
        check.n_compared += 1
        if caller not in registered:
            check.fail(
                f"records.AUDIT_POSITION_AFTER_RUN_CALLERS names {caller!r}, "
                f"which the registry does not hold; a declared caller nobody "
                f"runs is a declaration nobody checks"
            )
    check.note(
        f"the after_run audit position has {len(declared_callers)} declared "
        f"caller(s), every one a registered stage: "
        f"{', '.join(sorted(declared_callers))}"
    )
    pulsed = next(c for c in campaign.configurations if c.pulsed)
    campaign_after_run = pool_mod.Job(
        phase="B",
        arm="BR",
        config=pulsed,
        seed=0,
        outdir=Path(campaign.runs_dir) / "_never",
        run_kind="campaign",
        audit_position=records_mod.AUDIT_POSITION_AFTER_RUN,
        audit_position_caller="reproduction",
    )
    caught, message = _must_refuse_here(
        lambda: pool_mod.environment_for(campaign_after_run, campaign)
    )
    check.tooth(
        "a campaign run asking for the after_run audit position",
        caught,
        f"every campaign record audits at the declared position, whoever asks; "
        f"a campaign run audited after the output path would publish the "
        f"written-file gap as an arm's accuracy ({message})",
    )
    undeclared_after_run = pool_mod.Job(
        phase="B",
        arm="BR",
        config=pulsed,
        seed=0,
        outdir=Path(campaign.runs_dir) / "_never",
        run_kind="gate",
        audit_position=records_mod.AUDIT_POSITION_AFTER_RUN,
        audit_position_caller="a_stage_nobody_declared",
    )
    caught, message = _must_refuse_here(
        lambda: pool_mod.environment_for(undeclared_after_run, campaign)
    )
    check.tooth(
        "an undeclared caller asking for the after_run audit position",
        caught,
        f"the position has declared callers with a reason each; a stage that "
        f"needs it is added to the table, not waved through ({message})",
    )

    # --- the lifted input file's digests ----------------------------------
    for name in input_files_mod.LIFTED_INPUT_SHA256:
        check.n_compared += 1
        if name not in campaign.population:
            check.fail(
                f"a lifted-input digest is recorded for {name}, which is not "
                f"a configuration of this campaign"
            )
    check.note(
        f"lifted input digests recorded for "
        f"{', '.join(sorted(input_files_mod.LIFTED_INPUT_SHA256))}; the "
        f"derivation that must reproduce them is task A51 (harness-artifacts)"
    )
    return check


def _must_refuse_here(call) -> tuple[bool, str]:
    """Whether *call* refused, and what it said.  A success is a tooth failure."""
    try:
        call()
    except Exception as exc:  # noqa: BLE001 - the refusal is the result
        return True, f"{type(exc).__name__}: {str(exc).splitlines()[0][:140]}"
    return False, "it did not refuse"


def run_all(
    campaign: Campaign,
    *,
    include_capability: bool = True,
    include_crosscheck: bool = False,
) -> list[Check]:
    checks = [check_composition(campaign), check_rungs()]
    if include_capability:
        checks.append(check_capability(campaign))
    checks.append(check_provenance(campaign))
    checks.append(check_data(campaign))
    checks.append(check_run_path(campaign))
    checks.append(check_stage_provenance(campaign))
    if include_crosscheck:
        checks.append(crosscheck_previous(campaign))
    return checks


def report(checks: list[Check]) -> int:
    width = 74
    print("=" * width)
    print("harness self-check — gates and their teeth; no PROCESS run")
    print("=" * width)
    for check in checks:
        verdict = "PASS" if check.passed else "FAIL"
        print(f"\n[{verdict}] {check.name} — {check.binds}")
        print(f"  population : {check.population}")
        print(f"  compared   : {check.n_compared}   mismatched: {check.n_mismatched}")
        for line in check.detail:
            print(f"  . {line}")
        for tooth in check.teeth:
            mark = "tripped" if tooth["caught"] else "DID NOT TRIP"
            print(f"  tooth {mark}: {tooth['tooth']} — {tooth['what']}")
    failed = [c.name for c in checks if not c.passed]
    print("\n" + "=" * width)
    print("verdict: " + ("PASS" if not failed else f"FAIL ({', '.join(failed)})"))
    print("=" * width)
    return 0 if not failed else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--tree",
        choices=("copy", "repository"),
        default="copy",
        help="which tree to check against.  The default is the experiment's "
        "own copy, which is the tree every run uses.  'repository' checks "
        "against the repository-root package, which belongs to the previous "
        "revision: **its capability check now fails by design**, because that "
        "tree does not implement the renamed switches and the probe's whole "
        "job is to say so",
    )
    parser.add_argument(
        "--no-capability",
        action="store_true",
        help="skip the capability probe (it starts one child process per "
        "arm and configuration and takes tens of seconds)",
    )
    parser.add_argument(
        "--crosscheck-previous",
        action="store_true",
        help="also execute the previous revision's own composition and "
        "compare it with this package's transcription of it",
    )
    parser.add_argument("--json", type=Path, help="write the records here")
    args = parser.parse_args(argv)

    campaign = (
        repository_tree_campaign() if args.tree == "repository" else default_campaign()
    )
    print(f"tree under check: {campaign.tree}")
    print(f"artifacts       : {campaign.data_dir}")
    print(f"configurations  : {', '.join(campaign.population)}\n")
    checks = run_all(
        campaign,
        include_capability=not args.no_capability,
        include_crosscheck=args.crosscheck_previous,
    )
    rc = report(checks)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps(
                {
                    "tree": str(campaign.tree),
                    "data_dir": str(campaign.data_dir),
                    "configurations": list(campaign.population),
                    "provenance": prov.git_stamp(campaign.tree),
                    "checks": [c.as_record() for c in checks],
                },
                indent=2,
            )
        )
        print(f"records: {args.json}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
