#!/usr/bin/env python
"""Gate ``evaluation_warmup`` — the warmed evaluation child changes no count.

V5 plan §6 (ruled by the orchestrator under D37 at A101's merge; built by task
**A102 (v5-campaign)**): the evaluation child runs a **discarded warm-up
evaluation** on the same entry, puts the whole data structure back to the
entry snapshot and re-enters the coupling state bit-exact (ruling D25's restore
mechanism), resets every driver counter and the timers, builds a fresh Caller
and runs the **measured** evaluation — so that a phase A record's module
timings carry no numba cache load (A101 §13: 259–351 ms per cold evaluation
against 21–32 ms warmed).  A harness change to the child, not a driver change:
no gate G1 press.  Its neutrality is shown the way gate GC shows a driver
change's — **the gate job set's evaluation records before and after, every
declared count identical to the digit and every coupling-state file
bit-identical.**

The two sides
-------------
**Before**: A101 (v5-timers-and-once)'s seeded records of the evaluation phase
made by the *cold* child — the repeatability stage's first repetition
(``runs/timing/repeatability/<configuration>/A_<arm>/rep1``: the gate job set
at gate GC's seed, under the campaign's declared setting, the census set at
τ = 1e-8, timers on, W = 1; the three repetitions were count-identical, which
is that stage's own refusal rule).  Those records are **archived** under this
gate's own directory on the first press and **never overwritten** (gate G1's
rule for a side that can only be made at a commit behind us): the record
contract now owes ``evaluation_warmup``, so the source directories are
re-made by the warmed child the next time the repeatability stage is pressed,
and the archive is what this gate reads from then on.  A source that already
carries the warm-up block is not a before side and is refused.

**After**: the same eleven jobs made by the warmed child at this commit, in
this gate's own directories, with the side in the job identity
(``override_env[HARNESS_EVALUATION_WARMUP_LABEL]``, GC's label mechanism) so
that nothing resolves them to the pool's or the campaign's records.

What is compared
----------------
Gate GC's own comparison functions: every leaf under GC's declared count
paths (rule ``identical``), the prime count (rule ``identical``), and every
coupling-state file the before side wrote (``y_entry.json``, ``y_exit.json``)
component by component as hex literals.  Beside them, the gate **re-derives**
each after record's own determinism check from its stamped counts — the
warm-up's and the measured evaluation's count leaves and exit-state digests
must agree — rather than trusting the child's ``agrees`` flag, and reports
the module time of the cold and the warmed evaluation as context.

Teeth: one added to a count on a copy of an after-side record must be the one
and only differing leaf; one added to a warm-up count on a copy of an
after-side record must read as disagreement in the re-derived check.
"""

from __future__ import annotations

import datetime as _dt
import json
import shutil
from pathlib import Path
from typing import Any, Mapping

from ..core import framework
from ..core import pool as pool_mod
from ..core import records as records_mod
from ..core.config import Campaign
from ..core.framework import Gate, GateError, Tooth
from ..experiment import arms as arms_mod
from . import gate_count_neutrality as gc_mod
from . import gates as gates_mod

GATE_NAME = "evaluation_warmup"

#: The environment variable that carries the side's label into the job
#: identity; the driver never reads it, the pool digests it.
LABEL_VARIABLE = "HARNESS_EVALUATION_WARMUP_LABEL"
AFTER_LABEL = "warmed"

#: Where the before side is read from: the repeatability stage's first
#: repetition of the evaluation phase (``harness/measurement/timing.py``).
BEFORE_STAGE = "repeatability"
BEFORE_REPETITION = 1

#: The record block the warmed child stamps; a before-side record lacks it.
WARMUP_BLOCK = "evaluation_warmup"

_HELD: dict[str, Any] = {}


# --------------------------------------------------------------------------
# where things are
# --------------------------------------------------------------------------


def root(campaign: Campaign) -> Path:
    return Path(campaign.runs_dir) / framework.GATES_SUBPATH / GATE_NAME


def before_source(campaign: Campaign, configuration: str, arm: str) -> Path:
    from ..measurement import timing as timing_mod  # noqa: PLC0415

    return timing_mod.timing_root(campaign, BEFORE_STAGE) / configuration / f"A_{arm}" / f"rep{BEFORE_REPETITION}"


def before_archive(campaign: Campaign, configuration: str, arm: str) -> Path:
    return root(campaign) / "before" / configuration / f"A_{arm}"


def after_directory(campaign: Campaign, configuration: str, arm: str) -> Path:
    return root(campaign) / "after" / configuration / f"A_{arm}"


def pairs(campaign: Campaign) -> list[tuple[str, str]]:
    """``(configuration, arm)`` per active evaluation arm: the gate job set's evaluation half."""
    return [
        (config.name, arm)
        for config in campaign.configurations
        for arm in arms_mod.active_arms(config, "A")
    ]


# --------------------------------------------------------------------------
# the two sides
# --------------------------------------------------------------------------


def archive_before(campaign: Campaign) -> dict[str, Any]:
    """Copy each before record into the gate's own directory, once; refuse a
    missing side or a source the warmed child already re-made."""
    rows: list[dict[str, Any]] = []
    n_copied = n_kept = 0
    for configuration, arm in pairs(campaign):
        archive = before_archive(campaign, configuration, arm)
        source = before_source(campaign, configuration, arm)
        if (archive / "metrics.json").exists():
            record = records_mod.read(archive)
            n_kept += 1
            rows.append({"key": f"A/{arm}/{configuration}", "archive": str(archive), "kept": True, "tree_git_head": record.get("tree_git_head")})
            continue
        if not (source / "metrics.json").exists():
            raise GateError(
                f"{GATE_NAME} has no before side for A/{arm}/{configuration}: "
                f"neither the archive {archive} nor the source {source} holds a "
                f"record.  The before side is A101's cold-child record of the "
                f"repeatability stage and is never made here (a side made by the "
                f"warmed child would compare the child with itself)."
            )
        record = records_mod.read(source)
        if WARMUP_BLOCK in record:
            raise GateError(
                f"{GATE_NAME}: the source {source} for A/{arm}/{configuration} "
                f"already carries {WARMUP_BLOCK!r} — it was made by the warmed "
                f"child and is not a before side.  Refused: the archive under "
                f"{root(campaign) / 'before'} is what this gate reads, and it "
                f"is absent."
            )
        archive.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, archive)
        (archive / "ARCHIVED_FROM.json").write_text(
            json.dumps(
                {
                    "source": str(source),
                    "archived_at": _dt.datetime.now().isoformat(timespec="seconds"),
                    "archived_by": GATE_NAME,
                    "source_tree_git_head": record.get("tree_git_head"),
                    "why": (
                        "the before side of the warmed-child neutrality gate: a "
                        "record the cold evaluation child made; the source "
                        "directory is re-made by the warmed child at the next "
                        "repeatability press, this copy is never overwritten"
                    ),
                },
                indent=2,
            )
        )
        n_copied += 1
        rows.append({"key": f"A/{arm}/{configuration}", "archive": str(archive), "kept": False, "source": str(source), "tree_git_head": record.get("tree_git_head")})
    return {"n_copied_this_press": n_copied, "n_kept": n_kept, "rows": rows}


def after_jobs(campaign: Campaign, references: Mapping[str, Any]) -> list[tuple[str, str, pool_mod.Job]]:
    """The after side: the gate job set's evaluation jobs by the warmed child."""
    from . import reproduction as reproduction_mod  # noqa: PLC0415

    plan: list[tuple[str, str, pool_mod.Job]] = []
    for configuration, arm in pairs(campaign):
        config = campaign.configuration(configuration)
        reference = references[configuration]
        plan.append(
            (
                configuration,
                arm,
                pool_mod.Job(
                    phase="A",
                    arm=arm,
                    config=config,
                    seed=gc_mod.EVALUATION_SEED,
                    outdir=after_directory(campaign, configuration, arm),
                    regime="perturbed",
                    delta=campaign.delta,
                    pin_hex=reproduction_mod.entry_pin(
                        config, arm, reference, seed=gc_mod.EVALUATION_SEED, delta=campaign.delta
                    ),
                    entry_state=Path(reference["snapshot"]),
                    run_kind="gate",
                    timers=True,
                    override_env={LABEL_VARIABLE: AFTER_LABEL},
                ),
            )
        )
    return plan


def jobs_read(campaign: Campaign) -> list[pool_mod.Job]:
    references = gates_mod.entry_references_from_records(campaign)
    return gates_mod.entry_reference_jobs(campaign) + [job for *_r, job in after_jobs(campaign, references)]


# --------------------------------------------------------------------------
# the re-derived determinism check
# --------------------------------------------------------------------------


def rederive_agreement(record: Mapping[str, Any]) -> dict[str, Any]:
    """The child's per-record determinism check, computed again from the
    stamped count leaves and exit-state digests of the two evaluations."""
    block = record.get(WARMUP_BLOCK)
    if not isinstance(block, Mapping):
        return {"agrees": False, "why": f"the record carries no {WARMUP_BLOCK!r} block", "n_compared": 0, "n_differing": 0, "differing": []}
    warm = block.get("warmup") or {}
    measured = block.get("measured") or {}
    a, b = warm.get("counts") or {}, measured.get("counts") or {}
    every = sorted(set(a) | set(b))
    differing = [
        {"leaf": k, "warmup": a.get(k, "<absent>"), "measured": b.get(k, "<absent>")}
        for k in every
        if k not in a or k not in b or a[k] != b[k]
    ]
    same_state = (
        warm.get("exit_state_sha256") is not None
        and warm.get("exit_state_sha256") == measured.get("exit_state_sha256")
    )
    return {
        "agrees": bool(every) and not differing and same_state,
        "stamped_agrees": block.get("agrees"),
        "n_compared": len(every),
        "n_differing": len(differing),
        "differing": differing[:10],
        "exit_state_digests_identical": same_state,
    }


def _module_time_ms(record: Mapping[str, Any], campaign: Campaign) -> dict[str, Any] | None:
    """The module rows and Total of one timed record, in ms: context only."""
    from ..measurement import timing as timing_mod  # noqa: PLC0415

    try:
        groups = timing_mod._grouping(campaign, str(record["campaign_configuration"]), [record], "A")
        rows = timing_mod.rows_of(record, groups)
    except Exception as exc:  # noqa: BLE001 - context, never a verdict
        return {"error": f"{type(exc).__name__}: {exc}"}
    return {
        "modules_ms": 1000.0 * sum(float(rows["rows"].get(m) or 0.0) for m in timing_mod.MODULE_ROWS),
        "total_ms": 1000.0 * float(rows["rows"].get("Total") or 0.0),
        "fixed_per_run_s": rows.get("fixed_per_run_s"),
    }


# --------------------------------------------------------------------------
# the body
# --------------------------------------------------------------------------


def body(campaign: Campaign, *, resume: bool = False) -> dict[str, Any]:
    archive = archive_before(campaign)
    references = gates_mod.entry_references(campaign, resume=resume)
    plan = after_jobs(campaign, references)
    pool_mod.run_all([job for *_r, job in plan], campaign, resume=resume)

    rows: list[dict[str, Any]] = []
    passed = True
    n_compared = n_mismatched = n_components = n_components_differing = 0
    n_prime = n_prime_failing = 0
    for configuration, arm, job in plan:
        key = f"A/{arm}/{configuration}"
        before_dir = before_archive(campaign, configuration, arm)
        after_dir = pool_mod.directory_for(job, campaign)
        before = gc_mod._read(before_dir, side="before", key=key)
        after = gc_mod._read(after_dir, side="after", key=key)
        counts = gc_mod.compare_counts(before, after)
        prime = gc_mod.compare_prime_calls(before, after, rule="identical")
        states = gc_mod.compare_state_files(before_dir, after_dir)
        rederived = rederive_agreement(after)
        checks = {
            "both_runs_finished": before.get("status") == "ok" and after.get("status") == "ok",
            "before_is_the_cold_child's": WARMUP_BLOCK not in before,
            "after_carries_the_warmup_block": isinstance(after.get(WARMUP_BLOCK), Mapping),
            "every_count_identical": counts["n_mismatched"] == 0,
            "prime_count_identical": prime["passed"],
            "every_exit_state_bit_identical": states["n_components_differing"] == 0,
            "at_least_one_state_file_compared": states["n_components_compared"] > 0,
            "warmup_and_measured_agree_rederived": rederived["agrees"],
            "child_stamped_agreement": (after.get(WARMUP_BLOCK) or {}).get("agrees") is True,
        }
        row = {
            "configuration": configuration,
            "arm": arm,
            "key": key,
            "before": {"path": str(before_dir), "tree_git_head": before.get("tree_git_head"), "status": before.get("status"), "run_kind": before.get("campaign_run_kind")},
            "after": {"path": str(after_dir), "tree_git_head": after.get("tree_git_head"), "status": after.get("status")},
            "counts": counts,
            "prime_calls": prime,
            "states": states,
            "warmup_rederived": rederived,
            "restore": {
                k: (after.get(WARMUP_BLOCK) or {}).get("restore", {}).get(k)
                for k in ("n_fields_moved_by_the_warmup", "n_restored", "n_not_restorable", "not_restorable", "n_still_differing_from_the_entry", "restored_bitexact")
            } if isinstance((after.get(WARMUP_BLOCK) or {}).get("restore"), Mapping) else None,
            "timing_context_ms": {"before_cold": _module_time_ms(before, campaign), "after_warmed": _module_time_ms(after, campaign)},
            "checks": checks,
        }
        row["passed"] = all(checks.values())
        passed = passed and row["passed"]
        n_compared += counts["n_compared"]
        n_mismatched += counts["n_mismatched"]
        n_components += states["n_components_compared"]
        n_components_differing += states["n_components_differing"]
        n_prime += prime["n_compared"]
        n_prime_failing += prime["n_mismatched"]
        rows.append(row)
    _HELD["rows"] = rows
    before_heads = sorted({str(r["before"]["tree_git_head"]) for r in rows})
    after_heads = sorted({str(r["after"]["tree_git_head"]) for r in rows})
    return {
        "passed": passed,
        "criterion": (
            "the gate job set's evaluation records made by the cold child "
            "(A101's repeatability stage, archived) against the same jobs made "
            "by the warmed child at this commit: every declared count identical "
            "to the digit (gate GC's paths, rule identical), the prime count "
            "identical, every coupling-state file bit-identical; and on every "
            "after record the warm-up and the measured evaluation agree on "
            "every count leaf and the exit-state digest, re-derived here"
        ),
        "criterion_source": "V5 experiment plan §6 (the warmed phase A evaluation); A101 §15 (the ruling)",
        "before_side": {"stage": BEFORE_STAGE, "repetition": BEFORE_REPETITION, "commits": before_heads, "archive": archive},
        "after_side": {"label": AFTER_LABEL, "label_variable": LABEL_VARIABLE, "commits": after_heads},
        "straddles": (
            f"cold child at {[h[:8] for h in before_heads]} -> warmed child at "
            f"{[h[:8] for h in after_heads]}"
        ),
        "population": (
            f"{len(rows)} evaluation pair(s) (the gate job set's evaluation half: every "
            f"arm active on each configuration at seed {gc_mod.EVALUATION_SEED}, δ = {campaign.delta}, "
            f"{campaign.test_set}/{campaign.tau:g}, timers on); {n_compared} count leaves compared under "
            f"{len(gc_mod.COUNT_PATHS)} declared paths, {n_mismatched} differing; {n_prime} prime-count "
            f"check(s), {n_prime_failing} failing; {n_components} coupling-state components compared bit "
            f"for bit, {n_components_differing} differing; the re-derived warm-up agreement holds on "
            f"{sum(1 for r in rows if r['warmup_rederived']['agrees'])} of {len(rows)} after records"
        ),
        "n_pairs": len(rows),
        "n_compared": n_compared,
        "n_mismatched": n_mismatched,
        "n_prime_checks": n_prime,
        "n_prime_checks_failing": n_prime_failing,
        "n_components_compared": n_components,
        "n_components_differing": n_components_differing,
        "count_paths": dict(gc_mod.COUNT_PATHS),
        "state_files": list(gc_mod.STATE_FILES),
        "test_set": campaign.test_set,
        "tau": campaign.tau,
        "timing_context": "the module time and Total of the cold and the warmed evaluation per pair are in each row (ms); context, never evidence (D33)",
        "rows": rows,
    }


# --------------------------------------------------------------------------
# the teeth
# --------------------------------------------------------------------------


def _teeth(campaign: Campaign) -> tuple[Tooth, ...]:
    def _last_row() -> dict[str, Any] | None:
        rows = _HELD.get("rows") or []
        return rows[-1] if rows else None

    def a_doctored_count() -> tuple[bool, str]:
        row = _last_row()
        if row is None:
            return False, "the gate compared nothing, so nothing can be doctored"
        before = records_mod.read(Path(row["before"]["path"]))
        after = json.loads(json.dumps(records_mod.read(Path(row["after"]["path"]))))
        field = "node_calls_single_eval"
        was = after.get(field)
        if not isinstance(was, int):
            return False, f"{field} is {was!r} on the after side; nothing to add one to"
        after[field] = was + 1
        result = gc_mod.compare_counts(before, after)
        named = [m["field"] for m in result["mismatches"]]
        return result["n_mismatched"] == 1 and named == [field], (
            f"one added to {field} ({was} -> {was + 1}) in a copy of {row['key']}'s "
            f"after-side record: the comparison reports {result['n_mismatched']} "
            f"differing leaf/leaves of {result['n_compared']} ({named})"
        )

    def a_doctored_warmup_count() -> tuple[bool, str]:
        row = _last_row()
        if row is None:
            return False, "the gate compared nothing"
        after = json.loads(json.dumps(records_mod.read(Path(row["after"]["path"]))))
        counts = ((after.get(WARMUP_BLOCK) or {}).get("warmup") or {}).get("counts")
        if not isinstance(counts, dict) or "node_calls_single_eval" not in counts:
            return False, "the after-side record carries no warm-up count leaves to doctor"
        was = counts["node_calls_single_eval"]
        counts["node_calls_single_eval"] = int(was) + 1
        result = rederive_agreement(after)
        named = [d["leaf"] for d in result["differing"]]
        return (not result["agrees"]) and named == ["node_calls_single_eval"], (
            f"one added to the warm-up's node_calls_single_eval ({was} -> {int(was) + 1}) in a "
            f"copy of {row['key']}'s after-side record: the re-derived check reads agrees = "
            f"{result['agrees']} with {result['n_differing']} differing leaf/leaves ({named})"
        )

    return (
        Tooth(
            name="a doctored count on one record",
            what="one added to node_calls_single_eval in a copy of an after-side record",
            must="be the one and only differing count leaf",
            check=a_doctored_count,
        ),
        Tooth(
            name="a doctored warm-up count",
            what="one added to the warm-up's node_calls_single_eval in a copy of an after-side record",
            must="read as disagreement in the re-derived warm-up check, naming that leaf",
            check=a_doctored_warmup_count,
        ),
    )


def gate(campaign: Campaign) -> Gate:
    return Gate(
        name=GATE_NAME,
        plan_name=None,
        needs_runs=True,
        binds="the warmed evaluation child (V5 plan §6): a harness change, not a driver change",
        what_it_proves=(
            "the warm-up, the bit-exact re-entry and the counter reset change "
            "no count and no bit of any exit state on the gate job set's "
            "evaluation half, and every warmed record's own determinism check "
            "re-derives as agreeing"
        ),
        body=lambda *, resume=False: body(campaign, resume=resume),
        # The after side and the references are this gate's own runs at this
        # commit; the before side is A101's by construction and is reported
        # in the outcome's ``before_side`` with its commits, never surveyed
        # as this gate's runs (gate GC's rule for its before side).
        jobs=lambda: gates_mod.job_rows(jobs_read, campaign),
        teeth=_teeth(campaign),
    )
