"""Gate ``resume_identity`` — what ``--resume`` calls the same job, and what it must not.

Two things are bound here, both without a PROCESS run.

**The identity covers every field the pool composes.**  ``pool.Job`` is a
dataclass; :data:`harness.core.pool.JOB_IDENTITY_FIELDS` and
:data:`harness.core.pool.JOB_NON_IDENTITY_FIELDS` must between them name every
field of it, so that a field added to a job cannot be a field ``--resume``
ignores.  Before task **A72 (resume-identity-and-shared-pool)** the resume
comparison was six fields and everything else — δ, the ruler, the pin, the
stencil point, the entry state, the overrides, the audit position — was kept
apart by the directory layout alone (issue I-23).

**Every deliberate second run keeps its own identity.**  The shared pool
(survey item B1) gives one directory to one job identity, so a gate that runs
the same arm at the same seed *on purpose a second way* has to differ from the
first run in an identity field, or the pool hands it the first run's record
and the comparison the gate exists for compares a record with itself.  The
survey names the classes: G5's hand-composed second run, G7's smoke runs, G4's
doctored entries, G1's two captures, GR's overrides and its composition tooth,
G8's two rulers and its observer, G2's prime on and off, the written-file gate's
after-run audit.  :func:`by_design_pairs` composes one pair per class **from
the gate modules' own job constructors** and requires the two digests to
differ — and the one pair that must *agree* (the three gates' entry reference,
one construction) to agree.

Teeth: a record whose digest matches but whose child-stamped δ differs is
refused; a record with no digest is incomplete; a digest that does not
re-derive from the stamped identity is refused; an unclassified job field
refuses the module; a by-design pair doctored to collide is reported.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Any

from ..core import pool as pool_mod
from ..core import records as records_mod
from ..core.config import Campaign, Config
from ..core.framework import Gate, Tooth

GATE_NAME = "resume_identity"

_HELD: dict[str, Any] = {}


# --------------------------------------------------------------------------
# the by-design pairs
# --------------------------------------------------------------------------


def _synthetic_reference(campaign: Campaign, config: Config) -> dict[str, Any]:
    """A reference block shaped like ``gates.entry_references`` returns, with a
    stand-in snapshot path: identities need the *path*, not the file."""
    from . import reproduction as reproduction_mod

    snapshot = pool_mod.pool_root(campaign) / "_identity_stand_in" / config.name / "y_exit.json"
    return {
        "outdir": str(snapshot.parent),
        "snapshot": str(snapshot),
        "t_plant_pulse_burn_hex": float(3000.0).hex(),
        "pin_for": reproduction_mod.pin_for,
    }


def by_design_pairs(campaign: Campaign) -> list[dict[str, Any]]:
    """One pair per class of deliberate second run, composed by the gate modules.

    Each row: the class, the two jobs, and ``must`` — ``"differ"`` for a
    second run that must keep its own directory, ``"agree"`` for the one job
    three gates must share.  Composed on the first configuration where the
    arms are active, with stand-in entry states where a real one would be
    read from a record: the identity is over the path, so no run is needed.
    """
    from . import gate_composition, gate_entry, gate_predicate_mode, gate_prime
    from . import gate_audit, gate_output_path, gate_records, gate_written_file
    from . import reproduction as reproduction_mod
    from .gate_neutrality import NEUTRAL_AUDIT_POSITION, NEUTRAL_GATE_NAME, neutrality_run_dir

    pairs: list[dict[str, Any]] = []
    configs = list(campaign.configurations)
    pulsed = [c for c in configs if c.pulsed] or configs
    config = pulsed[0]
    reference = _synthetic_reference(campaign, config)
    references = {c.name: _synthetic_reference(campaign, c) for c in configs}

    # G5: the matrix's composition against the hand-built one.
    from_matrix, by_switch = gate_composition.composition_jobs(campaign, config)
    pairs.append({"class": "G5 switch_by_switch second composition", "a": from_matrix, "b": by_switch, "must": "differ"})

    # G7: the smoke evaluation against the gates' shared reference of the same arm.
    pairs.append({
        "class": "G7 smoke evaluation vs the gates' entry reference (run kind)",
        "a": gate_records.evaluation_job(campaign),
        "b": reproduction_mod.entry_reference_job(gate_records.fewest_variables_configuration(campaign)),
        "must": "differ",
    })
    # G7: the forced-unconverged optimisation against G4's optimisation of the same arm.
    forced = gate_records.forced_job(campaign)
    g4_same = next(
        (j for j in gate_audit.optimisation_jobs(campaign) if j.config.name == forced.config.name),
        None,
    )
    if g4_same is not None and forced.arm == g4_same.arm:
        pairs.append({"class": "G7 forced-unconverged optimisation vs G4's optimisation (force_maxcal, run kind)", "a": forced, "b": g4_same, "must": "differ"})

    # G4: two doctored entries are two jobs (the entry state path).
    entries = pool_mod.pool_root(campaign).parent / "audit_restriction" / config.name / "_entries"
    doctored_a = gate_audit._job(campaign, config, "in_loop", entries / "in_loop.json", None)
    doctored_b = gate_audit._job(campaign, config, "per_run_x", entries / "per_run_x.json", None)
    baseline = gate_audit._job(campaign, config, "baseline", Path(reference["snapshot"]), None)
    pairs.append({"class": "G4 two doctored entries (entry state)", "a": doctored_a, "b": doctored_b, "must": "differ"})
    pairs.append({"class": "G4 doctored entry vs the undoctored baseline (entry state)", "a": doctored_a, "b": baseline, "must": "differ"})

    # G4 baseline vs G6 warm of the same arm, both entered from the reference snapshot
    # with the same pin: the SAME job, so the pool shares it (the saving).
    g6_pairing, g6_warm = gate_entry.entry_and_warm_jobs(campaign, references)
    warm_same = next((j for _c, a, j in g6_warm if _c == config.name and a == baseline.arm), None)
    if warm_same is not None:
        baseline_pinned = gate_audit._job(
            campaign, config, "baseline", Path(reference["snapshot"]), gate_audit._pin(config, reference)
        )
        pairs.append({"class": "G4 baseline vs G6 warm of the same arm from the same snapshot (shared)", "a": baseline_pinned, "b": warm_same, "must": "agree"})

    # G1: before and after are one identity; the layout keeps them apart.
    g1 = pool_mod.Job(
        phase="B", arm="BR", config=config, seed=0, regime="unperturbed",
        delta=campaign.delta, run_kind="gate",
        audit_position=NEUTRAL_AUDIT_POSITION, audit_position_caller=NEUTRAL_GATE_NAME,
        outdir=neutrality_run_dir(campaign, "before", config.name, "BR"),
    )
    g1_after = dataclasses.replace(g1, outdir=neutrality_run_dir(campaign, "after", config.name, "BR"))
    pairs.append({"class": "G1 before vs after capture (same identity; explicit directories)", "a": g1, "b": g1_after, "must": "agree", "directories_must": "differ"})

    # GR: its B3 at seed 0 against G5's B3 at seed 0 (audit position, overrides, δ).
    root = Path(campaign.runs_dir) / reproduction_mod.RUNS_SUBPATH
    planned, _prereq = reproduction_mod.plan(campaign, root)
    gr_b3 = next((i.job for i in planned if i.run.arm == "B3" and i.run.seed == 0 and i.run.configuration == config.name), None)
    if gr_b3 is not None:
        pairs.append({"class": "GR's B3 seed 0 vs G5's B3 seed 0 (audit position, reproduction overrides)", "a": gr_b3, "b": from_matrix, "must": "differ"})
        _chosen, tooth_job = reproduction_mod.composition_tooth_job(planned, campaign)
        if tooth_job is not None:
            gr_same = next(i.job for i in planned if i.run.arm == "B3" and i.run.seed == 0 and i.run.configuration == tooth_job.config.name)
            pairs.append({"class": "GR composition tooth vs GR's planned B3 (override_env)", "a": tooth_job, "b": gr_same, "must": "differ"})

    # G8: the two rulers; and the frozen trial run against G6's pairing run of the same arm and seed.
    entries8 = {c.name: _synthetic_reference(campaign, c) for c in configs}
    pair8 = gate_predicate_mode.predicate_mode_pairs(campaign)
    if pair8 and len(campaign.predicate_modes) > 1:
        p8 = pair8[0]
        frozen = gate_predicate_mode.predicate_mode_job(campaign, entries8, p8["config"], p8["arm"], p8["seed"], campaign.predicate_modes[0])
        mixed = gate_predicate_mode.predicate_mode_job(campaign, entries8, p8["config"], p8["arm"], p8["seed"], campaign.predicate_modes[1])
        pairs.append({"class": "G8 the two rulers (predicate mode)", "a": frozen, "b": mixed, "must": "differ"})
        g6_same = next((j for c, a, j in g6_pairing if c == p8["config"].name and a == p8["arm"] and j.seed == p8["seed"]), None)
        if g6_same is not None:
            pairs.append({"class": "G8 frozen trial run vs G6 pairing run of the same arm and seed (observer variable)", "a": frozen, "b": g6_same, "must": "differ"})

    # G2: the prime on and off.
    g2 = gate_prime.prime_map_jobs(campaign, references)
    offs = [j for _c, _arr, on, j in g2 if not on and _c == config.name]
    ons = [j for _c, _arr, on, j in g2 if on and _c == config.name]
    if offs and ons:
        pairs.append({"class": "G2 prime off vs prime on (override_env)", "a": offs[0], "b": ons[0], "must": "differ"})

    # The written-file gate's BR against G9's BR (audit position and caller).
    wf = gate_written_file.written_file_job(campaign, config, "BR")
    g9 = gate_output_path.output_path_job(campaign, config, "BR")
    pairs.append({"class": "written_file_gap's BR vs G9's BR (audit position, caller)", "a": wf, "b": g9, "must": "differ"})

    # The one construction three gates share: the entry reference.
    pairs.append({
        "class": "entry reference: gates.entry_reference_jobs vs GR's prerequisite vs G8's reference (shared)",
        "a": reproduction_mod.entry_reference_job(config),
        "b": gate_predicate_mode.predicate_mode_reference_jobs(campaign)[configs.index(config)],
        "must": "agree",
    })
    return pairs


def check_pairs(pairs: list[dict[str, Any]], campaign: Campaign) -> list[dict[str, Any]]:
    """Each pair's two digests and directories, and whether it holds."""
    rows: list[dict[str, Any]] = []
    for pair in pairs:
        a, b = pair["a"], pair["b"]
        da, db = pool_mod.digest_for(a, campaign), pool_mod.digest_for(b, campaign)
        dira, dirb = pool_mod.directory_for(a, campaign), pool_mod.directory_for(b, campaign)
        differing = [
            name
            for name in pool_mod.JOB_IDENTITY_FIELDS
            if a.identity(Path(campaign.runs_dir)).get(name) != b.identity(Path(campaign.runs_dir)).get(name)
        ]
        holds = (da != db) if pair["must"] == "differ" else (da == db)
        if pair.get("directories_must") == "differ":
            holds = holds and dira != dirb
        rows.append(
            {
                "class": pair["class"],
                "must": pair["must"],
                "a": a.key,
                "b": b.key,
                "digest_a": da[:16],
                "digest_b": db[:16],
                "identity_fields_differing": differing,
                "directories_differ": dira != dirb,
                "holds": holds,
            }
        )
    return rows


# --------------------------------------------------------------------------
# the body
# --------------------------------------------------------------------------


def body(campaign: Campaign, *, resume: bool = False) -> dict[str, Any]:
    declared = sorted(f.name for f in dataclasses.fields(pool_mod.Job))
    classified = sorted(
        (set(pool_mod.JOB_IDENTITY_FIELDS) - {"configuration"}) | set(pool_mod.JOB_NON_IDENTITY_FIELDS)
    )
    fields_ok = declared == classified
    rows = check_pairs(by_design_pairs(campaign), campaign)
    _HELD["rows"] = rows
    n_compared = len(declared) + len(rows)
    n_mismatched = (0 if fields_ok else len(set(declared) ^ set(classified))) + sum(
        1 for r in rows if not r["holds"]
    )
    return {
        "passed": fields_ok and all(r["holds"] for r in rows),
        "criterion": (
            "every field of pool.Job is classified as identity or non-identity; "
            "every class of deliberate second run composes to a job digest "
            "different from the run it is compared against, and the one job "
            "three gates share composes to one digest"
        ),
        "population": (
            f"{len(declared)} Job field(s); {len(rows)} by-design pair(s) "
            f"({sum(1 for r in rows if r['must'] == 'differ')} must differ, "
            f"{sum(1 for r in rows if r['must'] == 'agree')} must agree)"
        ),
        "n_compared": n_compared,
        "n_mismatched": n_mismatched,
        "identity_fields": list(pool_mod.JOB_IDENTITY_FIELDS),
        "non_identity_fields": list(pool_mod.JOB_NON_IDENTITY_FIELDS),
        "job_fields": declared,
        "pool_root": str(pool_mod.POOL_SUBPATH),
        "pairs": rows,
    }


# --------------------------------------------------------------------------
# the teeth
# --------------------------------------------------------------------------


def _complete_record_of(job: pool_mod.Job, campaign: Campaign) -> dict[str, Any]:
    """A record that ``is_complete_for`` accepts for *job*: every declared
    field present (null where the value does not matter), stamps consistent."""
    identity = job.identity(Path(campaign.runs_dir))
    record: dict[str, Any] = {name: None for name in records_mod.declared_field_names(job.phase)}
    for path in records_mod.CONTRACT[job.phase]:
        cursor = record
        parts = path.split(".")
        for part in parts[:-1]:
            if not isinstance(cursor.get(part), dict):
                cursor[part] = {}
            cursor = cursor[part]
        cursor[parts[-1]] = 0
    for name, child_name in records_mod.IDENTITY_FIELDS_STAMPED_BY_THE_CHILD.items():
        record[child_name] = identity[name]
    record["status"] = "ok"
    record["failure_class"] = "ok"
    record["exit_audit"] = {
        ruler: {"residual_max_hex": "0x0.0p+0"} for ruler in records_mod.AUDIT_RULERS
    }
    record["exit_audit"]["instrument"] = {"restores": "x", "n_restored": 0, "n_not_restorable": 0}
    record["exit_audit"]["predicate_mode"] = identity["predicate_mode"]
    record["job_identity"] = identity
    record["job_digest"] = records_mod.job_digest(identity)
    return record


def _teeth(campaign: Campaign) -> tuple[Tooth, ...]:
    def _job() -> pool_mod.Job:
        config = campaign.configurations[0]
        return pool_mod.Job(
            phase="A", arm="A0", config=config, seed=1, regime="perturbed",
            delta=campaign.delta, run_kind="gate",
        )

    def _why(record: dict[str, Any], job: pool_mod.Job) -> str | None:
        identity = job.identity(Path(campaign.runs_dir))
        return records_mod.why_not_complete_for(
            record, identity=identity, digest=records_mod.job_digest(identity)
        )

    def a_matching_digest_with_a_different_delta() -> tuple[bool, str]:
        job = _job()
        record = _complete_record_of(job, campaign)
        clean = _why(record, job)
        if clean is not None:
            return False, f"the undoctored record is itself refused: {clean}"
        record["campaign_delta"] = float(campaign.delta) * 2.0
        why = _why(record, job)
        return (why is not None and "campaign_delta" in why), (
            f"a record whose job_digest equals the job's but whose child-stamped "
            f"campaign_delta is {record['campaign_delta']} against the job's "
            f"{job.delta}: {why!r}"
        )

    def a_record_with_no_digest() -> tuple[bool, str]:
        job = _job()
        record = _complete_record_of(job, campaign)
        record.pop("job_digest")
        record.pop("job_identity")
        why = _why(record, job)
        return (why is not None and "job_identity" in why), (
            f"the same record with job_identity and job_digest removed — every "
            f"record made before A72 — is incomplete: {why!r}"
        )

    def a_digest_that_does_not_rederive() -> tuple[bool, str]:
        job = _job()
        record = _complete_record_of(job, campaign)
        # The identity is doctored on a field the child does not stamp, so
        # only the re-derivation of the digest from the stamped identity can
        # see it; the digest itself is left equal to the job's.
        forged = dict(record["job_identity"])
        forged["node_census"] = not forged["node_census"]
        record["job_identity"] = forged
        why = _why(record, job)
        return (why is not None and "node_census" in why), (
            f"job_identity.node_census flipped while job_digest kept: {why!r}"
        )

    def an_unclassified_job_field() -> tuple[bool, str]:
        original = pool_mod.JOB_IDENTITY_FIELDS
        try:
            pool_mod.JOB_IDENTITY_FIELDS = tuple(f for f in original if f != "delta")
            try:
                pool_mod._assert_every_job_field_is_classified()
            except TypeError as exc:
                return True, f"with 'delta' dropped from JOB_IDENTITY_FIELDS: {str(exc)[:160]}"
            return False, "a Job field neither list names was accepted"
        finally:
            pool_mod.JOB_IDENTITY_FIELDS = original

    def a_by_design_pair_made_to_collide() -> tuple[bool, str]:
        from . import gate_composition

        config = campaign.configurations[0]
        from_matrix, by_switch = gate_composition.composition_jobs(campaign, config)
        collided = dataclasses.replace(by_switch, override_env={})
        rows = check_pairs(
            [{"class": "G5 doctored: override_env cleared", "a": from_matrix, "b": collided, "must": "differ"}],
            campaign,
        )
        return (not rows[0]["holds"]), (
            f"G5's second composition with its override_env cleared composes to "
            f"digest {rows[0]['digest_b']} against the first's {rows[0]['digest_a']}; "
            f"the pair check reports holds={rows[0]['holds']}"
        )

    return (
        Tooth(
            name="a matching digest with a different stamped delta",
            what="the child-stamped campaign_delta doubled in a record whose job_digest equals the job's",
            must="be refused by name",
            check=a_matching_digest_with_a_different_delta,
        ),
        Tooth(
            name="a record with no digest",
            what="job_identity and job_digest removed from a complete record",
            must="be incomplete for the job (every pre-A72 record re-runs)",
            check=a_record_with_no_digest,
        ),
        Tooth(
            name="a digest that does not re-derive from the stamped identity",
            what="job_identity.node_census flipped while job_digest is kept equal to the job's",
            must="be refused by the re-derivation",
            check=a_digest_that_does_not_rederive,
        ),
        Tooth(
            name="an unclassified job field",
            what="'delta' dropped from JOB_IDENTITY_FIELDS",
            must="refuse the classification (TypeError)",
            check=an_unclassified_job_field,
        ),
        Tooth(
            name="a by-design pair made to collide",
            what="G5's hand-composed run with its override_env cleared",
            must="be reported as a pair that does not hold",
            check=a_by_design_pair_made_to_collide,
        ),
    )


def gate(campaign: Campaign) -> Gate:
    return Gate(
        name=GATE_NAME,
        needs_runs=False,
        binds="every --resume decision and every directory of the shared run pool",
        what_it_proves=(
            "that 'the same job' is decided by every field the pool composes "
            "into a run, that a record's stamps must agree with each other "
            "and with the job, and that every deliberate second run keeps a "
            "directory of its own under the shared pool"
        ),
        body=lambda *, resume=False: body(campaign, resume=resume),
        teeth=_teeth(campaign),
    )
