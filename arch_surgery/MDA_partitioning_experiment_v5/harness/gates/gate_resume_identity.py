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

**A record's arm name is the name at the time of the run.**  The arm renaming
of 2026-09-15 (``records.RECORDED_ARM_NAMES``, task A78 (arm-renames)) left
the campaign's 949 records and every earlier gate record stamped with the old
names; the records were not re-made.  The one translation is applied by
``records.read``, and the pool resolves a job's directory by the translated
digest.  This gate binds that: the table's values are arms of the matrix and
distinct; every record under ``runs/`` reads under a name the matrix knows,
and the verdict counts how many were read under a translated name; and the
teeth show a pre-renaming record of a renamed arm is complete for today's job,
a post-renaming record (stamped ``arm_naming``) is not translated, an arm
nobody declared is refused by name, and a canonical directory occupied by
another job's record is not removed.

Teeth: a job never resolves into another run ID's folder (task A107
(v5-campaign-settings-keys)); a crash record is kept only when complete as a crash (issue I-38);
an unnamed job never resolves into another gate's root (issue I-36);
a record whose digest matches but whose child-stamped δ differs is
refused; a record with no digest is incomplete; a digest that does not
re-derive from the stamped identity is refused; an unclassified job field
refuses the module; a by-design pair doctored to collide is reported; and the
four arm-name teeth above.
"""

from __future__ import annotations

import dataclasses
import json
import tempfile
from pathlib import Path
from typing import Any

from ..experiment import arms as arms_mod

from ..core import pool as pool_mod
from ..core import records as records_mod
from ..core.config import V4_TEST_SET, Campaign, Config
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
    from . import gate_composition, gate_entry, gate_prime
    from . import gate_output_path, gate_records, gate_test_set, gate_written_file
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
    # G7: the forced-unconverged optimisation against G5's matrix-composed
    # optimisation of the same arm (gate G4, whose optimisation this pair
    # used to read, retired under decision D36 by A101 (v5-timers-and-once)).
    forced = gate_records.forced_job(campaign)
    g5_from_matrix, _by_switch = gate_composition.composition_jobs(campaign, forced.config)
    if forced.arm == g5_from_matrix.arm:
        pairs.append({"class": "G7 forced-unconverged optimisation vs G5's optimisation (force_maxcal, run kind)", "a": forced, "b": g5_from_matrix, "must": "differ"})

    # Two entries are two jobs (the entry state path): the class gate G4's
    # doctored entries used to show, kept on two named entry files so the
    # identity field is still checked after G4's retirement.
    entries = pool_mod.pool_root(campaign).parent / "resume_identity" / config.name / "_entries"

    def _entered_from(label: str, entry: Path) -> pool_mod.Job:
        return pool_mod.Job(
            phase="A", arm="A2", config=config, seed=0, regime="unperturbed",
            delta=None, pin_hex=None, entry_state=entry, run_kind="gate",
        )

    doctored_a = _entered_from("in_loop", entries / "in_loop.json")
    doctored_b = _entered_from("per_run_x", entries / "per_run_x.json")
    baseline = _entered_from("baseline", Path(reference["snapshot"]))
    pairs.append({"class": "two doctored entries (entry state)", "a": doctored_a, "b": doctored_b, "must": "differ"})
    pairs.append({"class": "a doctored entry vs the undoctored reference entry (entry state)", "a": doctored_a, "b": baseline, "must": "differ"})

    # GT's full-set run of an arm vs G6's pairing run of the same arm from the
    # same displaced entry: the SAME job, so the pool shares it (the saving).
    g6_pairing, _g6_warm = gate_entry.entry_and_warm_jobs(campaign, references)
    gt_full = gate_test_set.full_jobs(campaign, references)
    pairing_same = next((j for _c, a, j in g6_pairing if _c == config.name and a == "A2"), None)
    full_same = next((j for _c, a, j in gt_full if _c == config.name and a == "A2"), None)
    if pairing_same is not None and full_same is not None:
        pairs.append({"class": "GT full-set run vs G6 pairing run of the same arm from the same entry (shared)", "a": full_same, "b": pairing_same, "must": "agree"})

    # G1: before and after are one identity; the layout keeps them apart.
    g1 = pool_mod.Job(
        phase="B", arm="BR", config=config, seed=0, regime="unperturbed",
        delta=campaign.delta, run_kind="gate",
        audit_position=NEUTRAL_AUDIT_POSITION, audit_position_caller=NEUTRAL_GATE_NAME,
        outdir=neutrality_run_dir(campaign, "before", config.name, "BR"),
    )
    g1_after = dataclasses.replace(g1, outdir=neutrality_run_dir(campaign, "after", config.name, "BR"))
    pairs.append({"class": "G1 before vs after capture (same identity; explicit directories)", "a": g1, "b": g1_after, "must": "agree", "directories_must": "differ"})

    # GC: one side's labelled job against the unlabelled job of the same arm
    # (the label rides in override_env, an identity field; A99's proposal 4,
    # applied by A100 (v5-test-set)).
    from . import gate_count_neutrality  # noqa: PLC0415

    gc_plan = gate_count_neutrality.count_neutrality_jobs(
        campaign, references, gate_count_neutrality.STRADDLE[1]
    )
    gc_b = next((j for p, c, a, j in gc_plan if p == "B" and c == config.name and a == "B2"), None)
    if gc_b is not None:
        unlabelled = dataclasses.replace(gc_b, override_env={})
        pairs.append({"class": "GC labelled side vs the unlabelled job of the same arm (override_env)", "a": gc_b, "b": unlabelled, "must": "differ"})

    # GR: its B2 at seed 0 against G5's B2 at seed 0 (audit position, overrides, δ).
    root = Path(campaign.runs_dir) / reproduction_mod.RUNS_SUBPATH
    planned, _prereq = reproduction_mod.plan(campaign, root)
    gr_b2 = next((i.job for i in planned if i.run.arm == "B2" and i.run.seed == 0 and i.run.configuration == config.name), None)
    if gr_b2 is not None:
        pairs.append({"class": "GR's B2 seed 0 vs G5's B2 seed 0 (audit position, reproduction overrides)", "a": gr_b2, "b": from_matrix, "must": "differ"})
        _chosen, tooth_job = reproduction_mod.composition_tooth_job(planned, campaign)
        if tooth_job is not None:
            gr_same = next(i.job for i in planned if i.run.arm == "B2" and i.run.seed == 0 and i.run.configuration == tooth_job.config.name)
            pairs.append({"class": "GR composition tooth vs GR's planned B2 (override_env)", "a": tooth_job, "b": gr_same, "must": "differ"})

    # (G8's two pairs — the two rulers, and the frozen trial run against G6's
    # pairing run — went with the gate, V5 list item 10.)

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

    # The one construction the warm gates share: the entry reference.
    from . import gates as gates_mod  # noqa: PLC0415

    pairs.append({
        "class": "entry reference: gates.entry_reference_jobs vs GR's prerequisite (shared)",
        "a": reproduction_mod.entry_reference_job(config),
        "b": gates_mod.entry_reference_jobs(campaign)[configs.index(config)],
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
            if a.identity(Path(campaign.runs_dir), campaign=campaign).get(name) != b.identity(Path(campaign.runs_dir), campaign=campaign).get(name)
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


def tolerance_rule_identity_rows(campaign: Campaign) -> list[dict[str, Any]]:
    """A named tolerance rule moves no default identity and owns its own.

    Task A105 (v5-resume-fixes-and-tau-rule).  Per rule and configuration,
    the flat control's seed-1 evaluation is composed three ways — under this
    campaign with no rule, under the rule, and under ``--tau`` set to the
    rule's own value — and must give: no ``tau_rule`` in the identity
    without a rule (so no record made without one moves); the rule's name
    and its τ in the identity under it; three distinct digests (a rule's
    record never resolves into the plain campaign's, nor into a ``--tau``
    campaign's at the same value).
    """
    from ..core.config import TAU_RULES  # noqa: PLC0415

    plain = dataclasses.replace(campaign, tau=None, tau_rule=None)
    runs_dir = Path(campaign.runs_dir)
    rows: list[dict[str, Any]] = []
    for rule in TAU_RULES:
        ruled = dataclasses.replace(plain, tau_rule=rule.name)
        for config in campaign.configurations:
            def job() -> pool_mod.Job:
                return pool_mod.Job(
                    phase="A", arm="A0", config=config, seed=1, regime="perturbed",
                    delta=campaign.delta, run_kind="gate",
                )
            tau = ruled.tau_for(config)
            same_tau = dataclasses.replace(plain, tau=tau)
            identities = {
                "none": job().identity(runs_dir, campaign=plain),
                "rule": job().identity(runs_dir, campaign=ruled),
                "tau": job().identity(runs_dir, campaign=same_tau),
            }
            digests = {k: records_mod.job_digest(v) for k, v in identities.items()}
            holds = (
                "tau_rule" not in identities["none"]
                and identities["rule"].get("tau_rule") == rule.name
                and identities["rule"].get("tau") == tau
                and "tau_rule" not in identities["tau"]
                and len(set(digests.values())) == 3
            )
            rows.append({
                "rule": rule.name,
                "configuration": config.name,
                "tau": tau,
                "digests": {k: v[:16] for k, v in digests.items()},
                "holds": holds,
            })
    return rows


def arm_name_translation_survey(campaign: Campaign) -> dict[str, Any]:
    """Every record under ``runs/`` by how its arm name was read.

    Three classes, counted with the denominator beside them: *stamped* (made
    after the renaming, ``arm_naming`` on disk, read as written); *translated*
    (unstamped, its arm renamed by the table); *unchanged* (unstamped, its arm
    not in the table).  A record naming an arm nobody declared raises out of
    ``records.read`` and is listed as a refusal, not counted into a class.
    """
    root = Path(campaign.runs_dir)
    counts = {"stamped": 0, "translated": 0, "unchanged": 0, "no_arm": 0}
    by_translation: dict[str, int] = {}
    refusals: list[str] = []
    n = 0
    if root.exists():
        for path in sorted(root.rglob("metrics.json")):
            n += 1
            try:
                on_disk = json.loads(path.read_text())
            except Exception:  # noqa: BLE001 - an unreadable record is no arm
                counts["no_arm"] += 1
                continue
            if not isinstance(on_disk, dict) or on_disk.get("campaign_arm") is None:
                counts["no_arm"] += 1
                continue
            try:
                record = records_mod.read(path.parent)
            except records_mod.RecordError as exc:
                refusals.append(f"{path.relative_to(root)}: {exc}")
                continue
            if on_disk.get(records_mod.ARM_NAMING_FIELD) is not None:
                counts["stamped"] += 1
            elif records_mod.ARM_NAME_TRANSLATION_FIELD in record:
                counts["translated"] += 1
                key = (
                    f"{on_disk.get('campaign_arm')} -> {record.get('campaign_arm')}"
                )
                by_translation[key] = by_translation.get(key, 0) + 1
            else:
                counts["unchanged"] += 1
    return {
        "n_records": n,
        "by_class": counts,
        "translated_by_name": dict(sorted(by_translation.items())),
        "refusals": refusals,
        "table": dict(records_mod.RECORDED_ARM_NAMES),
        "naming_stamp": {records_mod.ARM_NAMING_FIELD: records_mod.ARM_NAMING},
    }


def check_translation_table() -> list[str]:
    """What is wrong with ``records.RECORDED_ARM_NAMES``, if anything."""
    problems: list[str] = []
    table = records_mod.RECORDED_ARM_NAMES
    for old, new in table.items():
        if new not in arms_mod.ARMS:
            problems.append(f"the table maps {old!r} to {new!r}, which is not an arm of the matrix")
    values = list(table.values())
    if len(set(values)) != len(values):
        problems.append(f"the table maps two recorded names to one arm: {values}")
    if not records_mod.ARM_NAMING:
        problems.append("the naming stamp records.ARM_NAMING is empty")
    return problems


def body(campaign: Campaign, *, resume: bool = False) -> dict[str, Any]:
    declared = sorted(f.name for f in dataclasses.fields(pool_mod.Job))
    classified = sorted(
        (set(pool_mod.JOB_IDENTITY_FIELDS) - {"configuration"}) | set(pool_mod.JOB_NON_IDENTITY_FIELDS)
    )
    fields_ok = declared == classified
    rows = check_pairs(by_design_pairs(campaign), campaign)
    _HELD["rows"] = rows
    rule_rows = tolerance_rule_identity_rows(campaign)
    table_problems = check_translation_table()
    survey = arm_name_translation_survey(campaign)
    n_compared = (
        len(declared) + len(rows) + len(rule_rows)
        + len(records_mod.RECORDED_ARM_NAMES) + survey["n_records"]
    )
    n_mismatched = (
        (0 if fields_ok else len(set(declared) ^ set(classified)))
        + sum(1 for r in rows if not r["holds"])
        + sum(1 for r in rule_rows if not r["holds"])
        + len(table_problems)
        + len(survey["refusals"])
    )
    return {
        "passed": (
            fields_ok
            and all(r["holds"] for r in rows)
            and all(r["holds"] for r in rule_rows)
            and not table_problems
            and not survey["refusals"]
        ),
        "criterion": (
            "every field of pool.Job is classified as identity or non-identity; "
            "every class of deliberate second run composes to a job digest "
            "different from the run it is compared against, and the one job "
            "three gates share composes to one digest; the recorded-arm-name "
            "table maps onto distinct arms of the matrix, and every record "
            "under runs/ reads under an arm the matrix knows"
        ),
        "population": (
            f"{len(declared)} Job field(s); {len(rows)} by-design pair(s) "
            f"({sum(1 for r in rows if r['must'] == 'differ')} must differ, "
            f"{sum(1 for r in rows if r['must'] == 'agree')} must agree); "
            f"{len(rule_rows)} tolerance-rule identity row(s) (rule x "
            f"configuration: no rule, the rule, --tau at the rule's value); "
            f"{len(records_mod.RECORDED_ARM_NAMES)} recorded-name row(s); "
            f"{survey['n_records']} record(s) under runs/ read by arm name"
        ),
        "n_compared": n_compared,
        "n_mismatched": n_mismatched,
        "identity_fields": list(pool_mod.JOB_IDENTITY_FIELDS),
        "non_identity_fields": list(pool_mod.JOB_NON_IDENTITY_FIELDS),
        "job_fields": declared,
        "pool_root": str(pool_mod.POOL_SUBPATH),
        "pairs": rows,
        "tolerance_rule_identity": rule_rows,
        "arm_names": {
            "table_problems": table_problems,
            "survey": survey,
            "note": (
                "a record's arm name is the name at the time of the run; the "
                "records were not re-made at the renaming of 2026-09-15, the "
                "table is applied once in records.read, and pool.directory_for "
                "resolves a job's directory by the translated digest"
            ),
        },
    }


# --------------------------------------------------------------------------
# the teeth
# --------------------------------------------------------------------------


def _complete_record_of(job: pool_mod.Job, campaign: Campaign) -> dict[str, Any]:
    """A record that ``is_complete_for`` accepts for *job*: every declared
    field present (null where the value does not matter), stamps consistent."""
    identity = job.identity(Path(campaign.runs_dir), campaign=campaign)
    record: dict[str, Any] = {}
    # Every declared field, a null leaf at its dotted path (null counts as
    # carried): a nested declared field (`exit_audit.instrument.restores`,
    # `evaluation_warmup.agrees`) needs its parents to be dictionaries, or
    # the contract reads it as missing from a record whose parent is null --
    # which is how A102 (v5-campaign)'s `evaluation_warmup.agrees` refused
    # this synthetic record and nine teeth could not trip (A101's §8.6 met
    # the same class on `timers`).
    for name in records_mod.declared_field_names(job.phase):
        cursor = record
        parts = name.split(".")
        for part in parts[:-1]:
            if not isinstance(cursor.get(part), dict):
                cursor[part] = {}
            cursor = cursor[part]
        if not isinstance(cursor.get(parts[-1]), dict):
            cursor[parts[-1]] = None
    for path in records_mod.CONTRACT[job.phase]:
        cursor = record
        parts = path.split(".")
        for part in parts[:-1]:
            if not isinstance(cursor.get(part), dict):
                cursor[part] = {}
            cursor = cursor[part]
        cursor[parts[-1]] = 0
    for name, child_name in records_mod.IDENTITY_FIELDS_STAMPED_BY_THE_CHILD.items():
        # an identity field rendered only where it differs from its default
        # (the test set, the tolerance, the timers) is absent from a job at
        # the default: the child stamps the default then
        record[child_name] = identity.get(name, records_mod.IDENTITY_DEFAULTS_WHEN_ABSENT.get(name))
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


def a_job_never_resolves_into_another_run_ids_folder(campaign: Campaign) -> tuple[bool, str]:
    """The run-ID layout's rule (task A107 (v5-campaign-settings-keys)): a job
    composed under one run ID never resolves into another run ID's folder.

    In a scratch ``runs/`` holding two run IDs' folders: a job that **names**
    its directory in the other folder is refused by the pool
    (``pool.refuse_another_runs_folder``); an unnamed job whose digest is on
    disk **only** in the other folder resolves to its canonical directory in
    this one (step 2's search is confined to the run ID's folder); and, as
    the control that keeps the second part from passing over a dead search,
    the same record put inside this folder is found by digest.
    """
    config = campaign.configurations[0]
    with tempfile.TemporaryDirectory(prefix="run_id_tooth_") as td:
        root = Path(td) / "runs"
        here = dataclasses.replace(
            campaign,
            run_id="this_run",
            runs_root=root,
            runs_dir=root / "this_run",
            derived_input_dir=root / "this_run" / "input_files",
        )
        other = root / "other_run"
        named = pool_mod.Job(
            phase="A", arm="AR", config=config, seed=0, run_kind="gate",
            outdir=other / "single" / config.name / "AR" / "seed000",
        )
        try:
            pool_mod.directory_for(named, here)
            named_refused, named_message = False, "resolved without a refusal"
        except pool_mod.PoolError as exc:
            named_refused, named_message = True, str(exc)[:160]
        unnamed = pool_mod.Job(phase="A", arm="AR", config=config, seed=0, run_kind="gate")
        text = json.dumps(_complete_record_of(dataclasses.replace(unnamed), here))
        canonical = pool_mod.canonical_directory_for(dataclasses.replace(unnamed), here)
        elsewhere = other / "gates" / "_runs" / "a_record_of_this_digest"
        inside = here.runs_dir / "single" / "a_record_of_this_digest"
        try:
            elsewhere.mkdir(parents=True)
            (elsewhere / "metrics.json").write_text(text)
            pool_mod.forget_record_index()
            confined = pool_mod.directory_for(dataclasses.replace(unnamed), here)
            inside.mkdir(parents=True)
            (inside / "metrics.json").write_text(text)
            pool_mod.forget_record_index()
            control = pool_mod.directory_for(dataclasses.replace(unnamed), here)
        finally:
            pool_mod.forget_record_index()
    stays = confined.resolve() == canonical.resolve()
    found = control.resolve() == inside.resolve()
    return (named_refused and stays and found), (
        f"a job naming a directory in another run ID's folder: "
        f"{'refused' if named_refused else 'NOT refused'} ({named_message}); an unnamed "
        f"job whose digest is only in the other folder resolves to "
        f"{'its canonical directory in this one' if stays else str(confined)}; the same "
        f"record inside this folder is {'found by digest' if found else 'NOT found: ' + str(control)}"
    )


def an_archived_reproduction_record_is_never_re_made(campaign: Campaign) -> tuple[bool, str]:
    """Issue I-41 (task A112 (v5-reproduction-records-read-only)), on a scratch copy.

    In a scratch run ID whose settings are V4's own (the whole write set at
    1e-6, where another gate's job carries the reproduction gate's identity):
    a reproduction job's record in the gate's archive, **incomplete** under
    today's contract as the copied records were at A109's press.  (a) The other
    gate's unnamed job of the same identity resolves to its canonical pool
    directory, not into the archive -- it is made as its own record; (b) a
    resumed press of a job naming the archived directory is refused by the
    pool before anything is removed, and the archived record's bytes are
    unchanged; and, so that (b) refuses something real, (c) the resume decision
    on that record says it would be re-made, and the pool directory is not
    refused.
    """
    from . import reproduction as reproduction_mod  # noqa: PLC0415

    config = campaign.configurations[0]
    with tempfile.TemporaryDirectory(prefix="reproduction_archive_tooth_") as td:
        root = Path(td) / "runs"
        here = dataclasses.replace(
            campaign,
            test_set=V4_TEST_SET,
            tau=None,
            tau_rule=None,
            run_id="this_run",
            runs_root=root,
            runs_dir=root / "this_run",
            derived_input_dir=root / "this_run" / "input_files",
        )
        archived_job = reproduction_mod.v4_criterion(
            pool_mod.Job(phase="A", arm="AR", config=config, seed=0, run_kind="gate")
        )
        archived = reproduction_mod.archived_directory_for(archived_job, here)
        record = _complete_record_of(dataclasses.replace(archived_job), here)
        dropped = next(n for n in records_mod.declared_field_names("A") if "." not in n and n in record)
        record.pop(dropped)
        archived.mkdir(parents=True)
        text = json.dumps(record)
        (archived / "metrics.json").write_text(text)
        try:
            pool_mod.forget_record_index()
            other = pool_mod.Job(phase="A", arm="AR", config=config, seed=0, run_kind="gate")
            same_identity = pool_mod.digest_for(other, here) == pool_mod.digest_for(dataclasses.replace(archived_job), here)
            canonical = pool_mod.canonical_directory_for(dataclasses.replace(other), here)
            redirected = pool_mod.directory_for(dataclasses.replace(other), here).resolve() == canonical.resolve()
            named = dataclasses.replace(archived_job, outdir=archived)
            try:
                pool_mod.run(named, here, resume=True)
                refused, message = False, "the press was NOT refused"
            except pool_mod.PoolError as exc:
                refused, message = True, str(exc)[:120]
            unchanged = (archived / "metrics.json").exists() and (archived / "metrics.json").read_text() == text
            identity = named.identity(Path(here.runs_dir))
            would_remake = pool_mod.why_not_kept(
                named, here, identity=identity, digest=records_mod.job_digest(identity), directory=archived
            )
            try:
                pool_mod.refuse_a_read_only_archive(canonical, here)
                pool_free = True
            except pool_mod.PoolError:
                pool_free = False
        finally:
            pool_mod.forget_record_index()
    caught = same_identity and redirected and refused and unchanged and would_remake is not None and pool_free
    return caught, (
        f"a reproduction record of {archived_job.key} in the archive lacking {dropped!r}: the other gate's "
        f"job {'has' if same_identity else 'does NOT have'} the same digest and resolves to "
        f"{'its canonical pool directory' if redirected else 'the ARCHIVE'}; a resumed press naming the "
        f"archived directory is {'refused (' + message + ')' if refused else 'NOT refused'}; the archived "
        f"bytes {'unchanged' if unchanged else 'CHANGED'}; the resume decision there: {would_remake!r}; "
        f"the pool directory {'is not refused' if pool_free else 'is refused too'}"
    )


def _teeth(campaign: Campaign) -> tuple[Tooth, ...]:
    def _job() -> pool_mod.Job:
        config = campaign.configurations[0]
        return pool_mod.Job(
            phase="A", arm="A0", config=config, seed=1, regime="perturbed",
            delta=campaign.delta, run_kind="gate",
        )

    def _why(record: dict[str, Any], job: pool_mod.Job) -> str | None:
        identity = job.identity(Path(campaign.runs_dir), campaign=campaign)
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

    def _renamed_job() -> pool_mod.Job:
        """Today's job of an arm the table renamed, on a configuration that runs it."""
        renamed = [new for new in records_mod.RECORDED_ARM_NAMES.values() if new in arms_mod.ARMS]
        for config in campaign.configurations:
            for arm in renamed:
                if arm not in config.skips and arms_mod.ARMS[arm].phase == "A":
                    return pool_mod.Job(
                        phase="A", arm=arm, config=config, seed=1, regime="perturbed",
                        delta=campaign.delta, run_kind="gate",
                    )
        raise RuntimeError("no renamed evaluation arm is active on any configuration")

    def _old_spelling(arm: str) -> str:
        for old, new in records_mod.RECORDED_ARM_NAMES.items():
            if new == arm:
                return old
        raise KeyError(arm)

    def _read_from_disk(record: dict[str, Any]) -> dict[str, Any]:
        """Write *record* to a scratch directory outside runs/ and read it back
        through the one reader.  The disk round trip is the point: the
        translation is applied by ``records.read``, nowhere else."""
        with tempfile.TemporaryDirectory(prefix="arm_names_tooth_") as td:
            (Path(td) / "metrics.json").write_text(json.dumps(record))
            return records_mod.read(td)

    def a_pre_renaming_record_of_a_renamed_arm_is_todays_job() -> tuple[bool, str]:
        job = _renamed_job()
        old = _old_spelling(job.arm)
        record = _complete_record_of(job, campaign)
        # As the run wrote it before the renaming: the old spelling in both
        # stamps, the digest over the old identity, no naming stamp.
        record["campaign_arm"] = old
        record["job_identity"] = dict(record["job_identity"], arm=old)
        record["job_digest"] = records_mod.job_digest(record["job_identity"])
        record.pop(records_mod.ARM_NAMING_FIELD, None)
        old_digest = record["job_digest"]
        read = _read_from_disk(record)
        why = _why(read, job)
        identity = job.identity(Path(campaign.runs_dir), campaign=campaign)
        trace = read.get(records_mod.ARM_NAME_TRANSLATION_FIELD) or {}
        return (
            why is None
            and read.get("campaign_arm") == job.arm
            and read.get("job_digest") == records_mod.job_digest(identity)
            and trace.get("job_digest_as_stamped") == old_digest
        ), (
            f"a complete record of {job.key} written as the run wrote it before "
            f"the renaming (campaign_arm={old!r}, digest {old_digest[:12]}…) reads "
            f"back as {read.get('campaign_arm')!r} with digest "
            f"{str(read.get('job_digest'))[:12]}… (stamped one kept as "
            f"{records_mod.ARM_NAME_TRANSLATION_FIELD}.job_digest_as_stamped "
            f"{str(trace.get('job_digest_as_stamped'))[:12]}…) "
            f"and is {'complete for' if why is None else 'NOT complete for'} today's job"
            + (f": {why}" if why else "")
        )

    def a_post_renaming_record_is_not_translated() -> tuple[bool, str]:
        job = _renamed_job()
        record = _complete_record_of(job, campaign)
        record[records_mod.ARM_NAMING_FIELD] = records_mod.ARM_NAMING
        stamped = _read_from_disk(record)
        unstamped_record = dict(record)
        unstamped_record.pop(records_mod.ARM_NAMING_FIELD)
        unstamped = _read_from_disk(unstamped_record)
        # The same bytes minus the stamp: the stamp alone decides.  Today's
        # name of the renamed arm is also a *key* of the table, so without
        # the stamp the record would be read as a different arm.
        would_be = records_mod.RECORDED_ARM_NAMES.get(job.arm, job.arm)
        return (
            _why(stamped, job) is None
            and stamped.get("campaign_arm") == job.arm
            and records_mod.ARM_NAME_TRANSLATION_FIELD not in stamped
            and unstamped.get("campaign_arm") == would_be
            and (would_be == job.arm or _why(unstamped, job) is not None)
        ), (
            f"a record of {job.key} stamped {records_mod.ARM_NAMING_FIELD}="
            f"{records_mod.ARM_NAMING!r} reads back as {stamped.get('campaign_arm')!r} "
            f"and is {'complete' if _why(stamped, job) is None else 'NOT complete'} "
            f"for the job; the same bytes without the stamp read back as "
            f"{unstamped.get('campaign_arm')!r}"
            + (
                f" and are {'NOT complete' if _why(unstamped, job) else 'complete'} for it"
                if would_be != job.arm
                else " (this arm's name is not a key of the table)"
            )
        )

    def an_arm_nobody_declared_is_refused_by_name() -> tuple[bool, str]:
        job = _job()
        record = _complete_record_of(job, campaign)
        record["campaign_arm"] = "ZZ"
        record["job_identity"] = dict(record["job_identity"], arm="ZZ")
        record["job_digest"] = records_mod.job_digest(record["job_identity"])
        record.pop(records_mod.ARM_NAMING_FIELD, None)
        try:
            _read_from_disk(record)
        except records_mod.RecordError as exc:
            unstamped_refused, unstamped_said = True, str(exc)
        else:
            unstamped_refused, unstamped_said = False, "ACCEPTED"
        record[records_mod.ARM_NAMING_FIELD] = records_mod.ARM_NAMING
        try:
            _read_from_disk(record)
        except records_mod.RecordError as exc:
            stamped_refused, stamped_said = True, str(exc)
        else:
            stamped_refused, stamped_said = False, "ACCEPTED"
        return (
            unstamped_refused and "'ZZ'" in unstamped_said
            and stamped_refused and "'ZZ'" in stamped_said
        ), (
            f"a record naming arm 'ZZ': unstamped, "
            f"{'refused' if unstamped_refused else 'ACCEPTED'} "
            f"({unstamped_said[:90]}…); stamped {records_mod.ARM_NAMING!r}, "
            f"{'refused' if stamped_refused else 'ACCEPTED'} ({stamped_said[:90]}…)"
        )

    def a_canonical_directory_taken_by_another_jobs_record() -> tuple[bool, str]:
        job = _renamed_job()
        # Another arm of the same phase at the same seed: the flat control,
        # which every configuration runs.
        other = pool_mod.Job(
            phase=job.phase, arm="A0", config=job.config, seed=job.seed,
            regime=job.regime, delta=job.delta, run_kind=job.run_kind,
        )
        record = _complete_record_of(other, campaign)
        record[records_mod.ARM_NAMING_FIELD] = records_mod.ARM_NAMING
        identity = job.identity(Path(campaign.runs_dir), campaign=campaign)
        with tempfile.TemporaryDirectory(prefix="arm_names_tooth_") as td:
            (Path(td) / "metrics.json").write_text(json.dumps(record))
            try:
                pool_mod.assert_not_another_jobs_record(job, identity, Path(td))
            except pool_mod.PoolError as exc:
                refused, said = True, str(exc)
            else:
                refused, said = False, "ACCEPTED"
            try:
                pool_mod.assert_not_another_jobs_record(
                    other, other.identity(Path(campaign.runs_dir), campaign=campaign), Path(td)
                )
            except pool_mod.PoolError as exc:
                own_refused, own_said = True, str(exc)
            else:
                own_refused, own_said = False, "accepted"
        return (refused and not own_refused), (
            f"{job.key}'s canonical directory holding a record of {other.key}: "
            f"removal {'refused' if refused else 'ALLOWED'} ({said[:100]}…); "
            f"the same directory asked for by {other.key} itself: "
            f"{'REFUSED' if own_refused else 'allowed'} ({own_said[:60]})"
        )

    def a_named_directory_is_the_jobs_whatever_holds_its_digest() -> tuple[bool, str]:
        """Issue I-29 in the form A99 (v5-schedule-and-prime) met it on gate G1."""
        config = campaign.configurations[0]
        with tempfile.TemporaryDirectory(prefix="named_directory_tooth_") as td:
            runs = Path(td) / "runs"
            local = dataclasses.replace(campaign, runs_dir=runs)
            unnamed = pool_mod.Job(
                phase="A", arm="AR", config=config, seed=0, run_kind="gate",
            )
            elsewhere = runs / "elsewhere"
            elsewhere.mkdir(parents=True)
            (elsewhere / "metrics.json").write_text(
                json.dumps(_complete_record_of(unnamed, local))
            )
            named = dataclasses.replace(unnamed, outdir=runs / "gates" / "named" / "AR")
            pool_mod.forget_record_index()
            try:
                resolved_named = pool_mod.directory_for(named, local)
                resolved_unnamed = pool_mod.directory_for(unnamed, local)
            finally:
                pool_mod.forget_record_index()
        named_ok = resolved_named.resolve() == Path(named.outdir).resolve()
        unnamed_ok = resolved_unnamed.resolve() == elsewhere.resolve()
        return (named_ok and unnamed_ok), (
            f"a record of {unnamed.key}'s digest under runs/elsewhere: the job "
            f"naming runs/gates/named/AR resolves to "
            f"{'its own directory' if named_ok else str(resolved_named)}; the same "
            f"job with no directory named resolves to "
            f"{'the record by digest' if unnamed_ok else str(resolved_unnamed)} "
            f"(the named one must never be re-made into another caller's record)"
        )

    def an_unnamed_job_never_resolves_into_another_gates_root() -> tuple[bool, str]:
        """Issue I-36: the reproduction gate's unnamed AR substitute resolved by
        digest to five of gate G1's named captures and the pool refused.

        A record of an unnamed job's digest under ``runs/gates/<gate>/`` (one
        copy, then two) must leave the job at its canonical pool directory;
        the same record under ``runs/elsewhere`` must still resolve by digest.
        """
        config = campaign.configurations[0]
        with tempfile.TemporaryDirectory(prefix="gate_root_tooth_") as td:
            runs = Path(td) / "runs"
            local = dataclasses.replace(campaign, runs_dir=runs)
            unnamed = pool_mod.Job(phase="A", arm="AR", config=config, seed=0, run_kind="gate")
            text = json.dumps(_complete_record_of(unnamed, local))
            canonical = pool_mod.canonical_directory_for(dataclasses.replace(unnamed), local)
            captures = [runs / "gates" / "switch_neutrality" / side / config.name / "AR" for side in ("before", "after")]
            resolved: list[Path] = []
            try:
                for n in (1, 2):
                    captures[n - 1].mkdir(parents=True)
                    (captures[n - 1] / "metrics.json").write_text(text)
                    pool_mod.forget_record_index()
                    resolved.append(pool_mod.directory_for(dataclasses.replace(unnamed), local))
                elsewhere = runs / "elsewhere"
                elsewhere.mkdir(parents=True)
                (elsewhere / "metrics.json").write_text(text)
                pool_mod.forget_record_index()
                resolved.append(pool_mod.directory_for(dataclasses.replace(unnamed), local))
            finally:
                pool_mod.forget_record_index()
        ok = (
            all(r.resolve() == canonical.resolve() for r in resolved[:2])
            and resolved[2].resolve() == elsewhere.resolve()
        )
        return ok, (
            f"a record of {unnamed.key}'s digest in one, then two, of G1's named "
            f"captures under runs/gates/switch_neutrality/: the unnamed job resolves to "
            f"{'its canonical pool directory both times' if all(r.resolve() == canonical.resolve() for r in resolved[:2]) else [str(r) for r in resolved[:2]]}; "
            f"with a third copy under runs/elsewhere it resolves to "
            f"{'that record by digest' if resolved[2].resolve() == elsewhere.resolve() else str(resolved[2])}"
        )

    def a_crash_is_kept_only_when_complete_as_a_crash() -> tuple[bool, str]:
        """Issue I-38: a crashed record complete as a crash is kept by --resume.

        Before task A105 (v5-resume-fixes-and-tau-rule) every record whose
        status was not ``ok`` was re-made, so each resumed campaign press
        re-ran the 20 crashing starts and re-stamped them.  A crash record
        with its identity, status, traceback and the pool's launcher stamps
        must now be kept; the same record without the traceback, without the
        launcher, or in the ``machinery`` row must still be re-made, each by
        name.
        """
        job = _job()
        record = _complete_record_of(job, campaign)
        record["status"] = "crashed"
        record["failure_class"] = "crashed"
        record["traceback"] = (
            "Traceback (most recent call last):\n  File \"x.py\", line 1, in run\n"
            "RuntimeError: Failed to converge after 50 iterations, value is nan.\n"
        )
        record["launcher"] = {"spawned_at": 1.0, "returned_at": 2.0, "wall_s": 1.0}
        kept = _why(record, job)
        doctored = {
            "traceback": dict(record, traceback=""),
            "launcher": {k: v for k, v in record.items() if k != "launcher"},
            "failure_class": dict(record, failure_class="machinery"),
        }
        whys = {name: _why(rec, job) for name, rec in doctored.items()}
        caught = kept is None and all(
            why is not None and name in why for name, why in whys.items()
        )
        return caught, (
            f"a crash record with its identity, traceback and launcher stamps: "
            f"{'kept' if kept is None else 'RE-MADE (' + kept + ')'}; "
            + "; ".join(f"without its {name} (or machinery): {why!r}" for name, why in whys.items())
        )

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

    def a_record_composed_with_one_term_fewer() -> tuple[bool, str]:
        """A kept record must have been composed from the terms the arm sets today.

        The identity names the arm and not its switches, so a driver change
        that makes an arm compose one more switch (V5 list item 5) leaves an
        earlier record of that arm with the same digest.  The pool compares
        the record's ``switches_asked`` with the arm's terms by name and
        re-makes on a difference; a record with one term dropped, and one
        with a term the arm never sets, must both be refused by name, and the
        undoctored record must be kept.
        """
        job = _job()
        _env, terms = pool_mod.environment_for(job, campaign)
        record = _complete_record_of(job, campaign)
        record["switches_asked"] = dict(terms)
        clean = pool_mod.why_not_composed_as_today(record, terms)
        if clean is not None:
            return False, f"the undoctored record is itself refused: {clean}"
        dropped = dict(terms)
        dropped.pop("mda")
        record["switches_asked"] = dropped
        fewer = pool_mod.why_not_composed_as_today(record, terms)
        record["switches_asked"] = {**terms, "a_term_nobody_composes": "x"}
        more = pool_mod.why_not_composed_as_today(record, terms)
        caught = (
            fewer is not None and "'mda'" in fewer
            and more is not None and "a_term_nobody_composes" in more
        )
        return caught, (
            f"the same record with 'mda' dropped from switches_asked: {fewer!r}; "
            f"with a term the arm never sets added: {more!r}; undoctored: kept"
        )

    return (
        Tooth(
            name="a job never resolves into another run ID's folder",
            what=(
                "in a scratch runs/ with two run IDs' folders: a job naming its "
                "directory in the other folder; an unnamed job whose digest is "
                "on disk only there; the same record inside this folder"
            ),
            must=(
                "refuse the first (PoolError), resolve the second to its "
                "canonical directory in this folder, and find the third by "
                "digest (task A107 (v5-campaign-settings-keys))"
            ),
            check=lambda: a_job_never_resolves_into_another_run_ids_folder(campaign),
        ),
        Tooth(
            name="an archived reproduction record is never re-made",
            what=(
                "in a scratch run ID at V4's settings: a reproduction record in the "
                "gate's archive, incomplete under today's contract; another gate's "
                "unnamed job of the same identity; a resumed press naming the "
                "archived directory"
            ),
            must=(
                "resolve the other gate's job to its canonical pool directory, "
                "refuse the press (PoolError) with the archived bytes unchanged, "
                "while the resume decision says the record would otherwise be "
                "re-made (issue I-41, task A112)"
            ),
            check=lambda: an_archived_reproduction_record_is_never_re_made(campaign),
        ),
        Tooth(
            name="a record composed with one term fewer, or one more",
            what=(
                "a complete record whose switches_asked lacks a term the arm "
                "composes today, and one that carries a term it never sets"
            ),
            must="be refused by name, while the undoctored record is kept",
            check=a_record_composed_with_one_term_fewer,
        ),
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
            name="an unnamed job never resolves into another gate's root",
            what=(
                "a complete record of an unnamed job's digest in one and then "
                "two of gate G1's named capture directories, then a third copy "
                "outside runs/gates/"
            ),
            must=(
                "leave the job at its canonical pool directory while the copies "
                "are under a gate's root, and resolve it to the copy outside by "
                "digest (issue I-36)"
            ),
            check=an_unnamed_job_never_resolves_into_another_gates_root,
        ),
        Tooth(
            name="a crash is kept only when complete as a crash",
            what=(
                "a complete crash record (status crashed, a result row, the "
                "traceback's last line, the launcher stamps), then the same "
                "record with its traceback emptied, its launcher removed, or "
                "its failure class machinery"
            ),
            must=(
                "keep the first under --resume and re-make each doctored "
                "copy, naming what it lacks (issue I-38)"
            ),
            check=a_crash_is_kept_only_when_complete_as_a_crash,
        ),
        Tooth(
            name="a by-design pair made to collide",
            what="G5's hand-composed run with its override_env cleared",
            must="be reported as a pair that does not hold",
            check=a_by_design_pair_made_to_collide,
        ),
        Tooth(
            name="a pre-renaming record of a renamed arm is today's job",
            what=(
                "a complete record written with the arm's old spelling in both "
                "stamps, the digest over the old identity and no naming stamp, "
                "read back through records.read"
            ),
            must=(
                "read under today's name with the digest re-derived, the stamped "
                "one kept beside it, and be complete for today's job"
            ),
            check=a_pre_renaming_record_of_a_renamed_arm_is_todays_job,
        ),
        Tooth(
            name="a post-renaming record is not translated",
            what=(
                "the same complete record of a renamed arm with and without the "
                "arm_naming stamp"
            ),
            must=(
                "read as written with the stamp, and as the table's translation "
                "without it -- the stamp alone tells today's A1 from yesterday's"
            ),
            check=a_post_renaming_record_is_not_translated,
        ),
        Tooth(
            name="an arm nobody declared is refused by name",
            what="a complete record naming arm 'ZZ', unstamped and stamped",
            must="raise RecordError naming the arm, both ways",
            check=an_arm_nobody_declared_is_refused_by_name,
        ),
        Tooth(
            name="a canonical directory taken by another job's record",
            what=(
                "a renamed arm's canonical directory holding a complete record "
                "of a different arm at the same seed"
            ),
            must="refuse removal (PoolError), and allow it for the record's own job",
            check=a_canonical_directory_taken_by_another_jobs_record,
        ),
        Tooth(
            name="a named directory is the job's whatever holds its digest",
            what=(
                "a job naming its own directory while another directory under "
                "runs/ holds a complete record of its digest"
            ),
            must=(
                "resolve to the named directory (and the unnamed job to the "
                "record by digest): gate G1's two captures are one identity in "
                "two named directories, and a press once wrote the second into "
                "the first (issue I-29)"
            ),
            check=a_named_directory_is_the_jobs_whatever_holds_its_digest,
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
