"""Gate G8 -- the convergence predicate's trial: two rulers, one implementation.

The experiment plan's section 3.6 declares the trial and its three parts, and
section 3.9 names the gate G8: the default ruler moves nothing (gate GR's own
check, read here); a pair of runs no evaluation decided differently is
bit-identical under the two rulers; and the components on which the two rulers
do disagree are named with |y| / s there, or their absence is stated with its
population.  :data:`PREDICATE_PAIR_EXCLUSIONS` is read by ``exclusion_review``.

Moved verbatim out of ``harness/gates/gates.py`` (its ``G8`` section, with
``print_predicate_mode``) by the code-move task of the simplification survey;
written by task **A59 (driver-predicate)**.  Gate name, record path, teeth and
``reads_from`` are unchanged; the gate is constructed by :func:`gate` and
registered in ``harness/gates/registry.py``.
"""

from __future__ import annotations

import copy
import datetime as _dt
import json
import math
import sys
from pathlib import Path
from typing import Any, Mapping

_EXPERIMENT_DIR = Path(__file__).resolve().parents[2]
if str(_EXPERIMENT_DIR) not in sys.path:
    sys.path.insert(0, str(_EXPERIMENT_DIR))

from harness.experiment import arms as arms_mod  # noqa: E402
from harness.core import framework  # noqa: E402
from harness.child import child as child_mod  # noqa: E402
from harness.core import pool as pool_mod  # noqa: E402
from harness.core import records as records_mod  # noqa: E402
from harness.core.config import Campaign, Config  # noqa: E402
from harness.gates.gate_neutrality import (  # noqa: E402
    _mfile_for,
    _read_record,
    compare_mfiles,
    compare_records,
)
from harness.gates import gates as gates_mod  # noqa: E402
from harness.gates.gates import _with_capture  # noqa: E402

GATES_SUBPATH = framework.GATES_SUBPATH
Gate = framework.Gate
Tooth = framework.Tooth
GateError = framework.GateError
_git_head = framework.git_head


# --------------------------------------------------------------------------
# G8 -- the convergence predicate's trial: two rulers, one implementation
# --------------------------------------------------------------------------
#
# The experiment plan's section 3.6 declares the trial and its three parts, and
# section 3.9 names the gate G8.  In one paragraph:
#
# The convergence test divides a step by a *ruler*.  The `frozen` ruler is a
# scale measured once over a harvest of design points; the `mixed` ruler keeps
# that scale as a floor and divides by the state's current magnitude where that
# is larger.  Wherever the current magnitude is at or below the scale the two
# are bit-identical, and `mixed` is never tighter, so no count can go up.  A
# pass is **decisive** when some component is at or above the tolerance on
# `frozen` and below it on `mixed` -- the only way the two can disagree at all.
#
# The three parts:
#
#   (1) neutrality -- under the default `frozen`, the runs reproduce the
#       previous revision bit for bit.  This is gate GR's own check and is not
#       re-implemented here: GR compares twenty of the previous revision's
#       records value for value, the evaluation-phase arms among them, and
#       every run it makes is composed under the default ruler.  G8 reads GR's
#       committed verdict and states what it covers.  A missing GR verdict is a
#       FAIL, not a skip: a criterion whose evidence is not there is not a
#       criterion (trap T11).
#
#   (2) the identity -- a pair of runs with no decisive pass must be
#       bit-identical.  This holds by construction, so a pair where it does not
#       is an implementation defect and the gate FAILS.
#
#   (3) the binding set -- for every pair that does have a decisive pass: where
#       it happened, which components, `|y| / s` there, and whether the
#       component was the one holding the pass open under `frozen`.  If none
#       occurs at these seeds that is a **result**, stated with its population,
#       not a gap.
#
# **Why the gate does not infer (2) from the records alone.**  "No decisive
# pass" cannot be read off two run records: a decisive pass is an event inside
# a loop, and a record carries counters.  Inferring "there was no decisive
# pass" from "the two runs agree" and then checking that they agree is
# circular, and a circular gate passes on a defect.  So the gate's runs carry
# the ruler observer (``child.install_ruler_observer``), which watches every
# predicate evaluation on both rulers and writes what it saw to its own file.
# The observer returns the run's own residual unchanged, so the runs it watches
# are exactly the runs the gate compares.
#
# **Two events, not one, and the difference matters.**  The plan's *decisive
# pass* is componentwise: some component crosses the tolerance between the
# rulers.  That is the binding set of part (3).  Whether the pair's runs may
# then *differ* is a narrower question -- it needs the crossing component to
# have been the one holding the evaluation open, so that the evaluation's
# verdict changes.  A component can cross while another still holds the loop
# open, and then the two runs stay bit-identical with a non-empty binding set.
# Both counts are recorded, and part (2)'s criterion binds on the narrower one:
# reporting the wider event as the narrower would let a defect hide behind a
# crossing that could not have caused it.

#: The arms and seeds the trial runs.  Evaluation-phase arms only: the plan
#: licenses the optimisation phase under `mixed` **only if** the evaluation
#: phase shows a decisive pass on an in-loop component, so running it here
#: would be spending the licence before it is granted.
PREDICATE_MODE_ARMS: tuple[str, ...] = ("A0", "A2")
PREDICATE_MODE_SEEDS: tuple[int, ...] = (1, 2)

#: Record leaves that differ between the two runs of a pair **by construction**,
#: each with the reason.  A much shorter list than G1's, and deliberately: G1's
#: two sides are at different commits and made by different revisions of the
#: harness, while these two sides are the same code at the same commit run twice
#: with one setting changed, so almost nothing is licensed to differ.  In
#: particular ``exit_audit.mixed`` is **not** here.  The plan allows it to be
#: excluded; it is compared instead, because a pair with no decisive pass
#: reaches the same exit state and both audits of one exit state are the same
#: numbers -- so comparing it costs nothing and is strictly stronger.
PREDICATE_PAIR_EXCLUSIONS: dict[str, str] = {
    # where the run happened
    "outdir": "the two runs are in different directories, by construction",
    # how long it took, and what the machine was doing
    "wall_s": "wall clock is context, never evidence (I-10)",
    "cpu_user_s": "cpu time is a contention diagnostic",
    "cpu_sys_s": "cpu time is a contention diagnostic",
    "cpu_s": "cpu time is a contention diagnostic",
    "maxrss_kb": "peak memory varies with the machine's state",
    "loadavg": "machine load while it ran",
    "mfile.process_runtime": "PROCESS's own timing of itself",
    "tree_untracked_paths": "the working tree's state, not the driver's behaviour",
    "tree_untracked_paths_n": "the count of the list above, on the same reason",
    # the mode stamps -- the thing being varied.  Every one of these is the
    # setting itself or the driver's readback of it; comparing them would be
    # comparing the change to itself.
    "campaign_predicate_mode": (
        "the setting being varied: 'frozen' on one side, 'mixed' on the other"
    ),
    "switches_asked.predicate_mode": (
        "the term the arm composes under 'mixed' and does not under 'frozen'"
    ),
    "env_architecture.env_PROCESS_ARCH_PREDICATE": (
        "the environment variable being varied, as the record spells it "
        "(the block prefixes every name with 'env_')"
    ),
    "resolved_switches.process.core.solver.module_solve.PREDICATE_MODE": (
        "the driver's readback of the setting being varied.  It is what proves "
        "each run was the arm it says it was, and is checked as such, per run, "
        "before anything is concluded from the pair"
    ),
    "coupling_state_provenance.predicate_mode": (
        "the loaded spec's stamp of the same setting"
    ),
    "exit_audit.predicate_mode": "the audit's stamp of the same setting",
    "job_identity.predicate_mode": (
        "the pool's stamp of the setting being varied (rule (xiv): predicate_mode "
        "is a Job field, so it is in the identity)"
    ),
    "job_digest": (
        "sha256 of the identity, which changes whenever any identity field does "
        "-- here exactly because job_identity.predicate_mode does.  Excluded on "
        "the condition this gate's pairs differ in that one field and no other, "
        "which the identity block's other leaves, all compared, hold; that two "
        "distinct jobs carry distinct digests is gate resume_identity's claim, "
        "not this one's (a fix of the same class as A62's instrument stamp: a "
        "field the pair varies by construction; A73, the D27 press)"
    ),
    "exit_audit.rulers_note": (
        "prose, identical on both sides, excluded beside the stamps it explains"
    ),
}


def predicate_mode_root(campaign: Campaign) -> Path:
    return Path(campaign.runs_dir) / GATES_SUBPATH / "predicate_mode"


def predicate_mode_run_dir(
    campaign: Campaign, mode: str, configuration: str, arm: str, seed: int
) -> Path:
    """Where one trial run's record is: the shared pool's directory for its job.

    Resolved through the job's identity — which carries the ruler, the
    observer variable, the entry state and the constant — so two runs of one
    pair are two directories by construction, and the reference record must
    exist for the directory to be known (``GateError`` otherwise).
    """
    config = campaign.configuration(configuration)
    entries = predicate_mode_entries(campaign)
    return pool_mod.directory_for(
        predicate_mode_job(campaign, entries, config, arm, seed, mode), campaign
    )


def predicate_mode_pairs(campaign: Campaign) -> list[dict[str, Any]]:
    """Every (configuration, arm, seed) the trial runs under both rulers."""
    pairs: list[dict[str, Any]] = []
    for config in campaign.configurations:
        for arm in PREDICATE_MODE_ARMS:
            if arm in config.skips:
                continue
            for seed in PREDICATE_MODE_SEEDS:
                pairs.append({"config": config, "arm": arm, "seed": seed})
    return pairs


def predicate_mode_reference_dir(campaign: Campaign, configuration: str) -> Path:
    """Where a configuration's undisplaced evaluation reference lives.

    The evaluation phase displaces a *converged* state, not the input file's
    cold values, so each configuration needs one undisplaced evaluation first:
    its exit state is what every displaced entry is built from, and its
    converged burn time is what the constant owns on the arm that takes the
    quantity out of the loop.  The job is ``reproduction.entry_reference_job``
    — the same identity GR, G2, G4, G6 and the cold chain enter from — so under
    the shared pool it is one record, where before A72 this gate made its own
    "so that no two gates share a run directory".
    """
    from harness.gates import reproduction as reproduction_mod  # noqa: PLC0415

    return reproduction_mod.phase_a_reference_directory(
        campaign, campaign.configuration(configuration)
    )


def predicate_mode_reference_jobs(campaign: Campaign) -> list[pool_mod.Job]:
    from harness.gates import reproduction as reproduction_mod  # noqa: PLC0415

    return [
        reproduction_mod.entry_reference_job(config)
        for config in campaign.configurations
    ]


def predicate_mode_entries(campaign: Campaign) -> dict[str, dict[str, Any]]:
    """Each configuration's reference exit state and converged burn time."""
    from harness.gates import reproduction as reproduction_mod  # noqa: PLC0415

    entries: dict[str, dict[str, Any]] = {}
    for config in campaign.configurations:
        directory = predicate_mode_reference_dir(campaign, config.name)
        record = records_mod.read(directory)
        if record.get("status") != "ok":
            raise GateError(
                f"G8's evaluation reference for {config.name} did not finish "
                f"(status {record.get('status')!r}, taxonomy row "
                f"{record.get('failure_class')!r}).  Every displaced entry is "
                f"built from its exit state, so there is nothing to displace: "
                f"the gate stops here rather than entering the runs from "
                f"somewhere else."
            )
        entries[config.name] = {
            "outdir": str(directory),
            "snapshot": str(directory / "y_exit.json"),
            "t_plant_pulse_burn_hex": record.get("t_plant_pulse_burn_hex"),
            "pin_for": reproduction_mod.pin_for,
        }
    return entries


def predicate_mode_job(
    campaign: Campaign,
    entries: Mapping[str, dict[str, Any]] | None,
    config: Config,
    arm_name: str,
    seed: int,
    mode: str,
) -> pool_mod.Job:
    """One trial run: this arm at this seed under this ruler, observer installed."""
    arm = arms_mod.ARMS[arm_name]
    entry_state = None
    pin_hex = None
    if entries is not None:
        entry = entries[config.name]
        entry_state = Path(entry["snapshot"])
        if config.pulsed and arm.burn_time_owner == "constant":
            pin_hex = entry["pin_for"](
                entry["t_plant_pulse_burn_hex"], seed, campaign.delta
            )
    return pool_mod.Job(
        phase="A",
        arm=arm_name,
        config=config,
        seed=seed,
        regime="perturbed",
        delta=campaign.delta,
        run_kind="gate",
        predicate_mode=mode,
        entry_state=entry_state,
        pin_hex=pin_hex,
        # The gate's detector.  Not a switch: the driver has never heard of
        # this name, so it cannot be mistaken for one, and the child refuses
        # it outright on a campaign run.  It is in the job's identity, so a
        # trial run and a pairing run of the same arm at the same seed are two
        # jobs: the record G6 reads has no observation file, and this gate's
        # must.
        override_env={child_mod.RULER_OBSERVER_VARIABLE: "1"},
    )


def predicate_mode_jobs(
    campaign: Campaign, entries: Mapping[str, dict[str, Any]] | None = None
) -> list[pool_mod.Job]:
    """The trial's runs.  Both rulers, entered from the same state per pair.

    The two runs of a pair are entered from the **same** snapshot with the
    **same** constant, which is what makes their difference attributable to the
    ruler and nothing else.
    """
    jobs: list[pool_mod.Job] = []
    for pair in predicate_mode_pairs(campaign):
        config, arm_name, seed = pair["config"], pair["arm"], pair["seed"]
        for mode in campaign.predicate_modes:
            jobs.append(
                predicate_mode_job(campaign, entries, config, arm_name, seed, mode)
            )
    return jobs


def jobs_read(campaign: Campaign) -> list[pool_mod.Job]:
    """Every job G8 reads: the references and every pair under both rulers."""
    return predicate_mode_reference_jobs(campaign) + predicate_mode_jobs(
        campaign, predicate_mode_entries(campaign)
    )


def capture_predicate_mode(
    campaign: Campaign, *, resume: bool = False
) -> dict[str, Any]:
    """Run every pair under both rulers, with the observer installed.

    The undisplaced references run first and the displaced pairs follow,
    because the pairs are entered from the references' exit states.
    """
    references = predicate_mode_reference_jobs(campaign)
    pool_mod.run_all(references, campaign, resume=resume)
    jobs = predicate_mode_jobs(campaign, predicate_mode_entries(campaign))
    results = pool_mod.run_all(jobs, campaign, resume=resume)
    manifest = {
        "captured": _dt.datetime.now().isoformat(timespec="seconds"),
        "tree_git_head": _git_head(),
        "n_runs": len(jobs),
        "arms": list(PREDICATE_MODE_ARMS),
        "seeds": list(PREDICATE_MODE_SEEDS),
        "rulers": list(campaign.predicate_modes),
        "delta": campaign.delta,
        "observer": child_mod.RULER_OBSERVER_VARIABLE,
        "runs": [
            {
                "configuration": job.config.name,
                "arm": job.arm,
                "seed": job.seed,
                "ruler": job.predicate_mode,
                "outdir": str(job.outdir),
                "status": (results[i] or {}).get("status")
                if isinstance(results, list)
                else None,
            }
            for i, job in enumerate(jobs)
        ],
    }
    path = predicate_mode_root(campaign) / "manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, default=str) + "\n")
    manifest["manifest"] = str(path)
    return manifest


def _observation(directory: Path, *, key: str) -> dict[str, Any]:
    path = Path(directory) / child_mod.RULER_OBSERVATION_FILE
    if not path.exists():
        raise GateError(
            f"G8 has no ruler observation for {key}: {path} is not there.  "
            f"Without it the gate would have to infer 'there was no decisive "
            f"pass' from 'the two runs agree', which is the thing it is "
            f"checking; a check that assumes its own conclusion is not a check."
        )
    return json.loads(path.read_text())


def _neutrality_from_reproduction(campaign: Campaign) -> dict[str, Any]:
    """Part (1): what gate GR already proves about the default ruler.

    Not re-implemented here.  GR reproduces twenty of the previous revision's
    records value for value, its evaluation-phase arms among them, and every
    run it makes is composed under the default ruler -- so "the default ruler
    moves nothing" is GR's verdict, read rather than re-measured.  What this
    adds is a statement of *what* GR covers, because a gate silent about its
    own coverage boundary is trap T11's shape.
    """
    # Imported here rather than at the top: reproduction imports selfcheck,
    # which imports this module, so a module-level import back would be a cycle.
    from harness.gates import reproduction as reproduction_mod  # noqa: PLC0415

    path = Path(campaign.runs_dir) / reproduction_mod.RUNS_SUBPATH / "gate.json"
    if not path.exists():
        return {
            "passed": False,
            "verdict": "NO EVIDENCE",
            "record": str(path),
            "why": (
                "gate GR has not been run at this commit, so G8's neutrality "
                "part has no evidence.  It is neither skipped nor assumed: run "
                "'experiment_runner.py --gate reproduction' and re-run this "
                "gate."
            ),
        }
    verdict = json.loads(path.read_text())
    # The file holds the framework's verdict for the gate, which carries the
    # stage's own verdict inside it under 'reproduction'; older files are the
    # stage's verdict alone.  Both shapes are read, because a gate that could
    # not read its own evidence would report NO EVIDENCE over a file that has
    # it.
    inner = verdict.get("reproduction") or verdict
    comparison = inner.get("comparison") or {}
    return {
        "passed": verdict.get("verdict") == "PASS",
        "verdict": verdict.get("verdict"),
        "record": str(path),
        "tree": inner.get("tree"),
        "n_runs_reproduced": comparison.get("n_runs_reproduced"),
        "n_runs": comparison.get("n_runs"),
        "n_values_compared": comparison.get("n_values_compared"),
        "n_values_differing": comparison.get("n_values_mismatched"),
        "gr_population": comparison.get("population"),
        "covers": (
            "every run gate GR makes is composed under the default ruler, so "
            "GR's bit-for-bit reproduction of the previous revision's records "
            "-- the evaluation-phase arms among them -- is the neutrality "
            "criterion.  It is read here, never re-measured: a second "
            "implementation of one comparison is the drift decision D14(c) "
            "exists to prevent."
        ),
    }


def predicate_mode_body(campaign: Campaign) -> dict[str, Any]:
    """Parts (1), (2) and (3), over every pair the trial runs."""
    neutrality = _neutrality_from_reproduction(campaign)
    frozen_name = campaign.predicate_modes[0]
    mixed_name = campaign.predicate_modes[1]
    rows: list[dict[str, Any]] = []
    binding: list[dict[str, Any]] = []
    n_values = n_excluded = n_differing = 0
    n_lines = n_line_differing = 0
    n_identical_pairs = n_changed_verdict_pairs = 0
    n_evaluations = 0

    for pair in predicate_mode_pairs(campaign):
        config, arm, seed = pair["config"], pair["arm"], pair["seed"]
        key = f"{arm}/{config.name}/seed{seed:03d}"
        by_mode: dict[str, dict[str, Any]] = {}
        observed: dict[str, dict[str, Any]] = {}
        for mode in campaign.predicate_modes:
            directory = predicate_mode_run_dir(
                campaign, mode, config.name, arm, seed
            )
            by_mode[mode] = _read_record(directory, side=mode, key=key)
            observed[mode] = _observation(directory, key=f"{key} under {mode}")

        # Each run really was the arm it says it was: the driver's own readback,
        # checked before anything is concluded from the pair.  This is the
        # failure the switch registry exists for -- a setting the tree ignores
        # produces a successful run of a different arm under the right name.
        resolved_wrong = [
            mode
            for mode in campaign.predicate_modes
            if (by_mode[mode].get("resolved_switches") or {}).get(
                "process.core.solver.module_solve.PREDICATE_MODE"
            )
            != mode
        ]

        # The decisive-pass question, answered by the observer on the FROZEN
        # run: it is that run's trajectory a mixed run would depart from.
        frozen_obs = observed[frozen_name]
        decisive_evaluations = frozen_obs[
            "n_evaluations_with_a_decisive_component"
        ]
        verdict_changes = frozen_obs["n_evaluations_where_the_verdict_changed"]
        n_evaluations += frozen_obs["n_predicate_evaluations_observed"]

        comparison = compare_records(
            by_mode[frozen_name],
            by_mode[mixed_name],
            excluded=PREDICATE_PAIR_EXCLUSIONS,
        )
        n_values += comparison["n_compared"]
        n_excluded += comparison["n_excluded"]
        n_differing += comparison["n_mismatched"]

        mfiles = {
            mode: _mfile_for(
                predicate_mode_run_dir(campaign, mode, config.name, arm, seed),
                config.name,
            )
            for mode in campaign.predicate_modes
        }
        if any(path is None for path in mfiles.values()):
            raise GateError(
                f"G8 has no output file for {key} on one side ({mfiles}); the "
                f"line comparison would be over nothing"
            )
        mfile = compare_mfiles(mfiles[frozen_name], mfiles[mixed_name])
        n_lines += mfile["n_lines_compared"]
        n_line_differing += mfile["n_lines_differing"]

        pair_identical = (
            comparison["n_mismatched"] == 0 and mfile["n_lines_differing"] == 0
        )
        if pair_identical:
            n_identical_pairs += 1
        if verdict_changes:
            n_changed_verdict_pairs += 1

        # Part (2)'s criterion, and it binds only where no evaluation changed
        # its verdict.  Where one did, the pair is *allowed* to differ and part
        # (3) says what made it.
        passed = not resolved_wrong and (
            pair_identical or verdict_changes > 0
        )

        for event in frozen_obs["decisive"]:
            for component in event["components"]:
                binding.append(
                    {
                        "configuration": config.name,
                        "arm": arm,
                        "seed": seed,
                        "evaluation": event["evaluation"],
                        "component": component["component"],
                        "value_over_scale": component["value_over_scale"],
                        "frozen_scaled_hex": component["frozen_scaled_hex"],
                        "mixed_scaled_hex": component["other_scaled_hex"],
                        "held_the_pass_under_frozen": component[
                            "held_the_pass_under_frozen"
                        ],
                        "changed_the_evaluation_verdict": event[
                            "verdict_changed"
                        ],
                    }
                )

        rows.append(
            {
                "configuration": config.name,
                "arm": arm,
                "seed": seed,
                "status": {m: by_mode[m].get("status") for m in by_mode},
                "resolved_wrong": resolved_wrong,
                "n_predicate_evaluations": frozen_obs[
                    "n_predicate_evaluations_observed"
                ],
                "n_evaluations_with_a_decisive_component": decisive_evaluations,
                "n_evaluations_where_the_verdict_changed": verdict_changes,
                "components_compared": {
                    m: by_mode[m].get("components_compared") for m in by_mode
                },
                "components_compared_identical": (
                    by_mode[frozen_name].get("components_compared")
                    == by_mode[mixed_name].get("components_compared")
                ),
                "record": comparison,
                "mfile": mfile,
                "identical": pair_identical,
                "criterion": (
                    "bit-identical (no evaluation changed its verdict)"
                    if verdict_changes == 0
                    else "may differ (an evaluation changed its verdict)"
                ),
                "audit": {
                    run_ruler: {
                        audit_ruler: (
                            (by_mode[run_ruler].get("exit_audit") or {})
                            .get(audit_ruler, {})
                            .get("residual_max_hex")
                        )
                        for audit_ruler in campaign.predicate_modes
                    }
                    for run_ruler in by_mode
                },
                "passed": passed,
            }
        )

    passed = (
        neutrality["passed"]
        and bool(rows)
        and all(row["passed"] for row in rows)
    )
    return {
        "passed": passed,
        "population": (
            f"{len(rows)} pair(s) = {len(campaign.configurations)} "
            f"configuration(s) x the evaluation-phase arms active on each "
            f"({', '.join(PREDICATE_MODE_ARMS)}) x "
            f"{len(PREDICATE_MODE_SEEDS)} seed(s), each run under both rulers "
            f"= {2 * len(rows)} runs at delta = {campaign.delta}; "
            f"{n_values} deterministic record values and {n_lines} output-file "
            f"lines compared without tolerance, {n_excluded} record values "
            f"excluded as the setting being varied or as run metadata (each "
            f"named, with its reason, in this record); {n_evaluations} "
            f"predicate evaluations observed on both rulers"
        ),
        "neutrality_is_gate_GR": neutrality,
        "n_pairs": len(rows),
        "n_pairs_bit_identical": n_identical_pairs,
        "n_pairs_with_a_changed_verdict": n_changed_verdict_pairs,
        "n_values_compared": n_values,
        "n_values_excluded": n_excluded,
        "n_values_differing": n_differing,
        "n_mfile_lines_compared": n_lines,
        "n_mfile_lines_differing": n_line_differing,
        "n_predicate_evaluations_observed": n_evaluations,
        "n_binding_component_events": len(binding),
        "binding_set": binding,
        "binding_set_empty_because": (
            None
            if binding
            else (
                "no component was at or above the tolerance on the frozen "
                "ruler and below it on the mixed one at any of the "
                f"{n_evaluations} predicate evaluations these {2 * len(rows)} "
                f"runs made.  That is a result about these arms and these "
                f"seeds, stated with its population, not a gap: the observer "
                f"that would have seen one is the same one the teeth below "
                f"exercise."
            )
        ),
        "excluded_record_paths": PREDICATE_PAIR_EXCLUSIONS,
        "runs": rows,
    }


def _predicate_mode_teeth(campaign: Campaign) -> tuple[Tooth, ...]:
    """Four breaks: two on the ruler itself, two on the gate's own comparisons."""

    def doctored_component() -> tuple[bool, str]:
        """The plan's tooth: a component at 100 s with dy = 50 tau s.

        Built on the :class:`Residual` directly, from a two-component synthetic
        spec, so that what is exercised is the arithmetic and not a run.  The
        magnitudes are the *current* values, which is what the mixed ruler
        divides by, so the first component's current value is exactly 100 s and
        the second's is exactly s.
        """
        ystate = _load_ystate()
        tau = campaign.tau
        scale = 2.0
        spec = ystate.YSpec(
            [("doctored", "far_above_its_scale"), ("doctored", "at_its_scale")],
            [ystate.CONTINUOUS, ystate.CONTINUOUS],
            [scale, scale],
            1,
            [
                {"key": "doctored.far_above_its_scale"},
                {"key": "doctored.at_its_scale"},
            ],
            mode=ystate.SPEC_MODE_A26,
        )
        step = 50.0 * tau * scale
        cur = [100.0 * scale, scale]
        prev = [cur[0] - step, cur[1] - step]
        frozen = spec.residual(prev, cur, ruler=ystate.RULER_FROZEN)
        mixed = spec.residual(prev, cur, ruler=ystate.RULER_MIXED)
        far_fails_frozen = float(frozen.scaled[0]) >= tau
        far_passes_mixed = float(mixed.scaled[0]) < tau
        at_fails_frozen = float(frozen.scaled[1]) >= tau
        at_fails_mixed = float(mixed.scaled[1]) >= tau
        caught = (
            far_fails_frozen
            and far_passes_mixed
            and at_fails_frozen
            and at_fails_mixed
        )
        return caught, (
            f"at y = 100 s the scaled step is {float(frozen.scaled[0]):.3e} "
            f"frozen (>= tau = {tau:g}) and {float(mixed.scaled[0]):.3e} mixed "
            f"(< tau); the same dy at y = s is "
            f"{float(frozen.scaled[1]):.3e} frozen and "
            f"{float(mixed.scaled[1]):.3e} mixed, above tau on both"
        )

    def bit_identity_below_the_scale() -> tuple[bool, str]:
        """Where |y| <= s the two rulers must agree to the last bit.

        Not decoration: it is the property the identity criterion rests on.  If
        the two rulers differed by an ULP on components where they are supposed
        to be the same expression, every pair would differ and part (2) would be
        vacuous.
        """
        ystate = _load_ystate()
        scale = 7.5
        spec = ystate.YSpec(
            [("doctored", "below_its_scale")],
            [ystate.CONTINUOUS],
            [scale],
            1,
            [{"key": "doctored.below_its_scale"}],
            mode=ystate.SPEC_MODE_A26,
        )
        prev = [scale * 0.25]
        cur = [scale * 0.25 + 1.0e-9]
        frozen = spec.residual(prev, cur, ruler=ystate.RULER_FROZEN)
        mixed = spec.residual(prev, cur, ruler=ystate.RULER_MIXED)
        same = float(frozen.scaled[0]).hex() == float(mixed.scaled[0]).hex()
        return same, (
            f"at |y| = {cur[0]:g} <= s = {scale:g} both rulers give "
            f"{float(frozen.scaled[0]).hex()}"
        )

    def one_ulp_between_two_identical_records() -> tuple[bool, str]:
        """The identity check must catch a 1-ULP difference.

        The gate's central claim is a zero over a population of record values.
        A zero from a comparator that cannot see the smallest possible
        difference is an assertion, so one is planted here: a copy of a record
        with one float moved by a single unit in the last place, compared with
        the original under the gate's own exclusion set.
        """
        pairs = predicate_mode_pairs(campaign)
        if not pairs:
            return False, "there are no pairs, so there is nothing to perturb"
        pair = pairs[0]
        directory = predicate_mode_run_dir(
            campaign,
            campaign.predicate_modes[0],
            pair["config"].name,
            pair["arm"],
            pair["seed"],
        )
        record = _read_record(
            directory, side=campaign.predicate_modes[0], key="a tooth"
        )
        audit = (record.get("exit_audit") or {}).get(
            campaign.predicate_modes[0]
        ) or {}
        original = audit.get("residual_max")
        if not isinstance(original, float):
            return False, (
                "the sample record carries no float exit-audit residual to "
                "perturb, so the tooth would be planted in nothing"
            )
        moved = copy.deepcopy(record)
        nudged = math.nextafter(original, math.inf)
        moved["exit_audit"][campaign.predicate_modes[0]]["residual_max"] = nudged
        result = compare_records(
            record, moved, excluded=PREDICATE_PAIR_EXCLUSIONS
        )
        return result["n_mismatched"] == 1, (
            f"exit_audit.{campaign.predicate_modes[0]}.residual_max moved from "
            f"{original.hex()} to {nudged.hex()} (1 ULP): "
            f"{result['n_mismatched']} of {result['n_compared']} compared "
            f"values differ"
        )

    def a_stamp_that_is_not_excluded() -> tuple[bool, str]:
        """The exclusion set must not be wider than it says.

        A gate's zero is only worth its exclusion list, so the list is checked
        for the one thing it must not cover: the exit audit's *mixed* block,
        which the plan permits excluding and which this gate compares.  A
        difference planted there must be caught.
        """
        pairs = predicate_mode_pairs(campaign)
        if not pairs:
            return False, "there are no pairs, so there is nothing to perturb"
        pair = pairs[0]
        directory = predicate_mode_run_dir(
            campaign,
            campaign.predicate_modes[0],
            pair["config"].name,
            pair["arm"],
            pair["seed"],
        )
        record = _read_record(
            directory, side=campaign.predicate_modes[0], key="a tooth"
        )
        moved = copy.deepcopy(record)
        block = moved["exit_audit"][campaign.predicate_modes[1]]
        block["residual_max_hex"] = str(block["residual_max_hex"]) + "0"
        result = compare_records(
            record, moved, excluded=PREDICATE_PAIR_EXCLUSIONS
        )
        return result["n_mismatched"] == 1, (
            f"a changed exit_audit.{campaign.predicate_modes[1]}."
            f"residual_max_hex gives {result['n_mismatched']} differing "
            f"value(s): the mixed audit is compared, not excluded"
        )

    return (
        Tooth(
            name="doctored_component",
            what="a component at y = 100 s with dy = 50 tau s, and the same dy at y = s",
            must="fail frozen and pass mixed; fail both",
            check=doctored_component,
        ),
        Tooth(
            name="bit_identity_below_the_scale",
            what="a component with |y| well below its scale",
            must="give the identical float on both rulers",
            check=bit_identity_below_the_scale,
        ),
        Tooth(
            name="one_ulp_between_identical_records",
            what="one float of a record moved by a single unit in the last place",
            must="be caught by the identity comparison",
            check=one_ulp_between_two_identical_records,
        ),
        Tooth(
            name="the_mixed_audit_is_compared",
            what="a changed exit_audit.mixed value",
            must="be caught -- the block the plan permits excluding is compared",
            check=a_stamp_that_is_not_excluded,
        ),
    )


def _load_ystate():
    """The coupling-state module, the way everything else in the harness gets it."""
    from harness.child import ystate as ystate_mod  # noqa: PLC0415

    return ystate_mod



def gate(campaign: Campaign) -> Gate:
    """G8, as the registry holds it.  The literal is the one ``_plan_gates`` held."""
    return Gate(
        name="predicate_mode",
        plan_name="G8",
        needs_runs=True,
        binds=(
            "the convergence predicate's second ruler, on the "
            "evaluation-phase arms of every configuration"
        ),
        what_it_proves=(
            "the default ruler moves nothing (gate GR's own check, read "
            "here); a pair of runs no evaluation decided differently is "
            "bit-identical under the two rulers; and the components on "
            "which the two rulers do disagree are named with |y| / s "
            "there, or their absence is stated with its population"
        ),
        body=lambda *, resume=False: _with_capture(
            capture_predicate_mode, predicate_mode_body, campaign, resume=resume
        ),
        # Its neutrality part is the reproduction gate's verdict, read
        # rather than re-measured, so that verdict has to exist first.
        reads_from=("reproduction",),
        jobs=lambda: gates_mod.job_rows(jobs_read, campaign),
        teeth=_predicate_mode_teeth(campaign),
    )


def print_predicate_mode(verdict: Mapping[str, Any]) -> None:
    """G8's three parts, each with its population.

    Printed rather than left in the record because the gate's result is a
    *table*: the identity is a zero over a stated population, and the binding
    set is a list of components that either exists or does not.  A reader
    should not have to open a JSON file to learn which.
    """
    neutrality = verdict.get("neutrality_is_gate_GR") or {}
    print("\n  (1) neutrality of the default ruler — gate GR's own check")
    print(f"      GR verdict : {neutrality.get('verdict')}")
    if neutrality.get("why"):
        print(f"      {neutrality['why']}")
    else:
        print(
            f"      {neutrality.get('n_runs_reproduced')}/"
            f"{neutrality.get('n_runs')} run(s) reproduced; "
            f"{neutrality.get('n_values_differing')} of "
            f"{neutrality.get('n_values_compared')} compared value(s) differ"
        )
        print(f"      population : {neutrality.get('gr_population')}")
    print(f"      record     : {neutrality.get('record')}")

    print(
        "\n  (2) the identity — a pair no evaluation decided differently is "
        "bit-identical"
    )
    print(
        f"      {verdict.get('n_pairs_bit_identical')}/"
        f"{verdict.get('n_pairs')} pair(s) bit-identical; "
        f"{verdict.get('n_pairs_with_a_changed_verdict')} pair(s) had an "
        f"evaluation whose verdict changed and are therefore allowed to differ"
    )
    print(
        f"      {verdict.get('n_values_differing')} of "
        f"{verdict.get('n_values_compared')} record values and "
        f"{verdict.get('n_mfile_lines_differing')} of "
        f"{verdict.get('n_mfile_lines_compared')} output-file lines differ"
    )
    header = (
        f"      {'arm':<4}{'configuration':<23}{'seed':>5} "
        f"{'evals':>6}{'decisive':>9}{'verdict':>8} {'comps=':>7}  "
        f"{'values':>12} {'lines':>8}  result"
    )
    print(header)
    for row in verdict.get("runs", []):
        print(
            f"      {row['arm']:<4}{row['configuration']:<23}"
            f"{row['seed']:>5} {row['n_predicate_evaluations']:>6}"
            f"{row['n_evaluations_with_a_decisive_component']:>9}"
            f"{row['n_evaluations_where_the_verdict_changed']:>8} "
            f"{str(row['components_compared_identical']):>7}  "
            f"{row['record']['n_mismatched']:>5}/"
            f"{row['record']['n_compared']:<6} "
            f"{row['mfile']['n_lines_differing']:>3}/"
            f"{row['mfile']['n_lines_compared']:<4}  "
            f"{'PASS' if row['passed'] else 'FAIL'}"
        )
        for mismatch in row["record"]["mismatches"][:10]:
            print(
                f"        DIFFERS {mismatch['field']}: "
                f"{mismatch.get('before')!r} -> {mismatch.get('after')!r}"
            )

    print("\n  (3) the binding set — where the two rulers disagree at all")
    binding = verdict.get("binding_set") or []
    if not binding:
        print(f"      none.  {verdict.get('binding_set_empty_because')}")
    else:
        print(
            f"      {verdict.get('n_binding_component_events')} component "
            f"event(s) over "
            f"{verdict.get('n_predicate_evaluations_observed')} observed "
            f"predicate evaluations"
        )
        print(
            f"      {'configuration':<23}{'arm':<4}{'seed':>5}{'eval':>6}  "
            f"{'component':<44}{'|y|/s':>10}  held  changed"
        )
        for event in binding[:40]:
            ratio = event["value_over_scale"]
            print(
                f"      {event['configuration']:<23}{event['arm']:<4}"
                f"{event['seed']:>5}{event['evaluation']:>6}  "
                f"{event['component']:<44}"
                f"{'n/a' if ratio is None else format(ratio, '10.3f')}  "
                f"{str(event['held_the_pass_under_frozen']):<5} "
                f"{event['changed_the_evaluation_verdict']}"
            )
        if len(binding) > 40:
            print(f"      … and {len(binding) - 40} more, in the gate record")

    print("\n  the exit audit, both rulers, per run (hex maxima)")
    print(
        f"      {'arm':<4}{'configuration':<23}{'seed':>5}  "
        f"{'run ruler':<10}{'audit frozen':<24}{'audit mixed':<24}"
    )
    for row in verdict.get("runs", []):
        for run_ruler, block in row["audit"].items():
            print(
                f"      {row['arm']:<4}{row['configuration']:<23}"
                f"{row['seed']:>5}  {run_ruler:<10}"
                f"{str(block.get('frozen')):<24}{str(block.get('mixed')):<24}"
            )
    print(
        "      both columns are shown because one alone would report a change "
        "of ruler as a change of accuracy"
    )
    for tooth in verdict.get("teeth", []):
        print(
            f"    tooth {tooth['tooth']:<38} {tooth['tooth_result']:<13} "
            f"{tooth['evidence']}"
        )
    print(f"    record       : {verdict.get('record')}")


