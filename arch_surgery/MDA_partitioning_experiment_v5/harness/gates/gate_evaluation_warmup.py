#!/usr/bin/env python
"""Gate ``evaluation_warmup`` — the warmed evaluation child changes no count.

**A read-once gate (decision D44, the user, 2026-10-01; built by task A110
(v5-warmup-verdict-once)).**  The gate gives its verdict once, at the commit
that introduced the warmed evaluation child, and from then on every press,
under every run ID, **reads** that verdict and the records behind it.  It is
treated as the reproduction gate GR is (``registry._run_once``): it makes no
run, composes no job under the pressing run ID's settings, and returns the
recorded verdict once the record and the files it names are verified.

What the verdict says
---------------------
V5 plan §6 (ruled by the orchestrator under D37 at A101's merge; built by task
**A102 (v5-campaign)** at ``ff9e73a2``): the evaluation child runs a
**discarded warm-up evaluation** on the same entry, puts the whole data
structure back to the entry snapshot, re-enters the coupling state bit-exact
(D25), resets every driver counter and the timers, builds a fresh Caller and
runs the **measured** evaluation.  The gate compared the gate job set's
evaluation half — eleven ``(configuration, arm)`` pairs at seed 1, δ = 0.1,
the census set at τ = 1e-8, timers on — made by the *cold* child (A101's
repeatability stage, first repetition, at ``24b78e2d``; archived under
``before/``) against the same jobs made by the warmed child at ``ff9e73a2``
(``after/``): every count leaf under gate GC's declared paths identical, the
prime count identical, every coupling-state component of ``y_entry.json`` /
``y_exit.json`` bit-identical, and on every after record the warm-up and the
measured evaluation agreeing (re-derived from the stamped counts and digests).
**PASS: 1 426 count leaves, 0 differing; 18 450 components, 0 differing; 11 of
11 re-derived agreements.**

Which record is read, and why that one
--------------------------------------
The press at ``ff9e73a2`` wrote ``runs/gates/evaluation_warmup/gate.json``; the
next press of the gate, A103 (v5-tally-and-tables)'s ``--resume`` at
:data:`VERDICT_COMMIT` (``c2295511``), overwrote that file with a verdict over
the **same eleven after records** (made at ``ff9e73a2``, which it states in its
``runs_are_not_this_commit's``) and the same archived before side; the gate's
code and GC's comparison functions are unchanged between the two commits.  The
``c2295511`` record is the only verdict of the gate under the default settings
that survives, so it is the one read.  Its stamp is checked exactly as GR checks
its copy-commit stamp, and the first read archives it beside the live file as
``verdict_at_c2295511.json`` (GR's rule: the framework rewrites ``gate.json``
at every press, so a read of a read must still find the original).

Why it is not re-pressed
------------------------
The question is about one commit — did introducing the warmed child change a
count? — and its before side cannot be made again: the cold child is gone from
the tree.  Pressed under a run ID with other settings (``write_set_tau1e-06``,
A106) the old body composed its after side under those settings and compared it
with the census-made archive, so the two loops stopped on different tests and
the gate failed **by construction** (254 of 1 430 count leaves; I-40).  What
guards every campaign under every setting is the per-record check the record
contract owes, ``evaluation_warmup.agrees`` (``core/records.py``,
``child/evaluate.py``: the record is refused where the warm-up and the measured
evaluation differ on any count leaf or the exit-state digest) — untouched here.

How the read verifies what it reads
-----------------------------------
1. **The verdict record** — ``verdict_at_c2295511.json`` (or, on the first read
   only, the live ``gate.json``) — must be stamped :data:`VERDICT_COMMIT`, be
   this gate's, name the **default** settings (the census set at τ = 1e-8:
   ``config.default_campaign``), and carry one row per pair of the gate job
   set's evaluation half, in order.  Anything else is refused.
2. **The records it names** must be on disk under ``before/`` and ``after/``,
   the before records stamped :data:`COLD_CHILD_COMMIT` and carrying no warm-up
   block, the after records stamped :data:`WARMED_CHILD_COMMIT` and made under
   the verdict's settings, and every file the comparison reads (``metrics.json``
   and the coupling-state files) **byte-identical** to the SHA-256 the archive
   manifest :data:`MANIFEST` holds.  The manifest is written by the first read,
   beside the verdict archive, as GR's archive is: it attests that the files
   have not changed since, not what they were at ``c2295511`` (no digest of them
   was recorded then).
3. **The comparison is re-derived** from those files with the functions the
   verdict was made with (GC's ``compare_counts``, ``compare_prime_calls``,
   ``compare_state_files`` and :func:`rederive_agreement`), and every pair's
   numbers — count leaves compared and differing, prime checks and failures,
   components compared and differing, the re-derived agreement, the pair's
   PASS — must equal the recorded row's.  So a verdict whose numbers do not
   follow from its records is caught, whichever of the two was changed.

The gate's verdict is the recorded verdict, and FAIL wherever a check above
finds a discrepancy; a missing record or a wrong stamp is a refusal.

A fresh run ID gets the verdict archive, the manifest and both sides by
``--copy-archived-records <from run ID> --apply`` (``archived_records.ARCHIVES``).

The teeth (all run live, on every read)
---------------------------------------
* **a doctored count on one record** (kept from the pressed form): one added to
  ``node_calls_single_eval`` in a copy of an archived after record must be the
  one and only differing count leaf of the re-derived comparison.
* **a doctored warm-up count** (kept): one added to the warm-up's
  ``node_calls_single_eval`` in a copy of an archived after record must read as
  disagreement in the re-derived warm-up check, naming that leaf.
* **a doctored archived record** (new): one byte changed in a copy of an
  archived after record's ``metrics.json`` must be caught by the manifest.
* **a doctored recorded verdict** (new): one added to a row's count of
  differing leaves in a copy of the verdict record must be caught by the
  reconciliation with the re-derived comparison, naming the pair and the field.
* **a verdict stamped at another commit** (new): a copy of the verdict record
  with another ``tree_git_head`` must be refused.

No tooth of the pressed form was removed: both compared copies of real records
and still have real archived records to bite on.  Under ``write_set_tau1e-06``
the first could not trip in the pressed form (the pair already differed, A106);
in the read form both sides are the census-made archive, so it bites there too.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from ..core import framework
from ..core import records as records_mod
from ..core.config import Campaign, default_campaign
from ..core.framework import Gate, GateError, Tooth
from ..experiment import arms as arms_mod
from . import gate_count_neutrality as gc_mod

GATE_NAME = "evaluation_warmup"

#: The commit the verdict that is read was recorded at (A103's ``--resume``
#: press over the after records made at :data:`WARMED_CHILD_COMMIT`).
VERDICT_COMMIT = "c2295511298249638e0c2e9a1bb3620dfc1bbe11"

#: The commit that introduced the warmed evaluation child (A102): every after
#: record the verdict compared was made there.
WARMED_CHILD_COMMIT = "ff9e73a2f798058d401ec5e3aa60a2b05e172f1e"

#: The commit the cold child's before records were made at (A101's
#: repeatability stage, first repetition).
COLD_CHILD_COMMIT = "24b78e2d373dd8f6d0767ab762880d62e12c92db"

#: The archived copy of the verdict, beside the live ``gate.json``.
VERDICT_ARCHIVE = f"verdict_at_{VERDICT_COMMIT[:8]}.json"

#: The SHA-256 of every file the comparison reads, written by the first read.
MANIFEST = "archive_manifest.json"

#: The record block the warmed child stamps; a before-side record lacks it.
WARMUP_BLOCK = "evaluation_warmup"

#: The files of one record the comparison reads.
RECORD_FILE = "metrics.json"

_HELD: dict[str, Any] = {}


# --------------------------------------------------------------------------
# where things are
# --------------------------------------------------------------------------


def root(campaign: Campaign) -> Path:
    return Path(campaign.runs_dir) / framework.GATES_SUBPATH / GATE_NAME


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


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compared_files(campaign: Campaign) -> list[str]:
    """Every file the comparison reads, relative to the gate's directory:
    each side's record and the coupling-state files present on either side."""
    out: list[str] = []
    base = root(campaign)
    for configuration, arm in pairs(campaign):
        for directory in (before_archive(campaign, configuration, arm), after_directory(campaign, configuration, arm)):
            for name in (RECORD_FILE, *gc_mod.STATE_FILES):
                if name == RECORD_FILE or (directory / name).exists():
                    out.append((directory / name).relative_to(base).as_posix())
    return out


# --------------------------------------------------------------------------
# the re-derived determinism check (unchanged from the pressed form)
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


# --------------------------------------------------------------------------
# the checks of the read, each a pure function so a tooth can feed it a copy
# --------------------------------------------------------------------------


def check_verdict_record(recorded: Mapping[str, Any], expected_pairs: Sequence[tuple[str, str]]) -> list[str]:
    """Why *recorded* is not the verdict this gate reads; empty when it is."""
    problems: list[str] = []
    head = str(recorded.get("tree_git_head") or "")
    if head != VERDICT_COMMIT:
        problems.append(f"stamped {head[:8] or '(no stamp)'}, not {VERDICT_COMMIT[:8]}")
    if recorded.get("gate") != GATE_NAME:
        problems.append(f"the record is gate {recorded.get('gate')!r}'s, not {GATE_NAME!r}'s")
    default = default_campaign()
    if (recorded.get("test_set"), recorded.get("tau")) != (default.test_set, default.tau):
        problems.append(
            f"made under {recorded.get('test_set')}/{recorded.get('tau')}, not the default "
            f"settings {default.test_set}/{default.tau:g}"
        )
    keys = [str(row.get("key")) for row in recorded.get("rows") or []]
    wanted = [f"A/{arm}/{configuration}" for configuration, arm in expected_pairs]
    if keys != wanted:
        problems.append(f"its rows are {keys}, not the gate job set's evaluation half {wanted}")
    return problems


def check_manifest(manifest: Mapping[str, str], files: Sequence[str], read: Callable[[str], bytes | None]) -> dict[str, Any]:
    """Every file the comparison reads against the manifest's SHA-256."""
    missing = [rel for rel in files if read(rel) is None]
    unlisted = [rel for rel in files if rel not in manifest]
    spare = sorted(set(manifest) - set(files))
    changed = [
        rel
        for rel in files
        if rel in manifest and (data := read(rel)) is not None and _sha256(data) != manifest[rel]
    ]
    return {
        "n_files": len(files),
        "n_missing": len(missing),
        "missing": missing[:10],
        "n_not_in_the_manifest": len(unlisted),
        "not_in_the_manifest": unlisted[:10],
        "n_in_the_manifest_only": len(spare),
        "in_the_manifest_only": spare[:10],
        "n_changed": len(changed),
        "changed": changed[:10],
        "unchanged": not (missing or unlisted or spare or changed),
    }


def rederive_pair(before: Mapping[str, Any], after: Mapping[str, Any], before_dir: Path, after_dir: Path) -> dict[str, Any]:
    """The pressed form's comparison of one pair, from the archived files."""
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
    return {
        "counts": counts,
        "prime_calls": prime,
        "states": states,
        "warmup_rederived": rederived,
        "checks": checks,
        "passed": all(checks.values()),
    }


#: The numbers of a pair the recorded row and the re-derivation must agree on.
RECONCILED: tuple[tuple[str, ...], ...] = (
    ("counts", "n_compared"),
    ("counts", "n_mismatched"),
    ("prime_calls", "n_compared"),
    ("prime_calls", "n_mismatched"),
    ("states", "n_components_compared"),
    ("states", "n_components_differing"),
    ("warmup_rederived", "agrees"),
    ("passed",),
)


def _at(block: Mapping[str, Any], path: Sequence[str]) -> Any:
    value: Any = block
    for key in path:
        value = value.get(key) if isinstance(value, Mapping) else None
    return value


def reconcile(recorded_row: Mapping[str, Any], rederived: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Each number the recorded row and the re-derivation disagree on."""
    return [
        {"field": ".".join(path), "recorded": _at(recorded_row, path), "rederived": _at(rederived, path)}
        for path in RECONCILED
        if _at(recorded_row, path) != _at(rederived, path)
    ]


# --------------------------------------------------------------------------
# the body: a read
# --------------------------------------------------------------------------


def _load_verdict(campaign: Campaign) -> tuple[dict[str, Any], Path, bool]:
    """The recorded verdict, archived on its first read; refuses where there is none."""
    directory = root(campaign)
    archive = directory / VERDICT_ARCHIVE
    live = directory / "gate.json"
    source = archive if archive.exists() else live
    if not source.exists():
        raise GateError(
            f"gate {GATE_NAME} is read, never re-made (D44), and there is no recorded "
            f"verdict at {archive} (nor a live one at {live}).  A run ID made after "
            f"the gate gets it with --copy-archived-records <from run ID> --apply."
        )
    recorded = json.loads(source.read_text())
    head = str(recorded.get("tree_git_head") or "")
    if head != VERDICT_COMMIT:
        raise GateError(
            f"gate {GATE_NAME}'s recorded verdict at {source} is stamped "
            f"{head[:8] or '(no stamp)'}, not {VERDICT_COMMIT[:8]}: it is not the "
            f"record this gate reads.  Refused."
            + (
                f"  (No archive {VERDICT_ARCHIVE} is here; under a run ID made "
                f"after the gate, copy it with --copy-archived-records.)"
                if source == live
                else ""
            )
        )
    first_read = not archive.exists()
    return recorded, source, first_read


def body(campaign: Campaign, *, resume: bool = False) -> dict[str, Any]:  # noqa: ARG001 - a read; --resume changes nothing
    expected = pairs(campaign)
    recorded, source, first_read = _load_verdict(campaign)
    problems = check_verdict_record(recorded, expected)
    if problems:
        raise GateError(f"gate {GATE_NAME}'s recorded verdict at {source} is refused: {'; '.join(problems)}")

    base = root(campaign)
    files = compared_files(campaign)
    absent = [rel for rel in files if not (base / rel).exists()]
    if absent:
        raise GateError(
            f"gate {GATE_NAME}: {len(absent)} file(s) the recorded verdict compared are "
            f"not on disk under {base} (first: {absent[:3]}).  The read refuses rather "
            f"than reads a verdict whose records are gone."
        )
    archive = base / VERDICT_ARCHIVE
    manifest_path = base / MANIFEST
    if first_read:
        if manifest_path.exists():
            raise GateError(f"{manifest_path} exists without {archive}: refused")
        manifest = {rel: _sha256((base / rel).read_bytes()) for rel in files}
        archive.write_text(source.read_text())
        manifest_path.write_text(
            json.dumps(
                {
                    "what_this_is": (
                        f"the SHA-256 of every file gate {GATE_NAME}'s recorded verdict at "
                        f"{VERDICT_COMMIT[:8]} compared, taken by the gate's first read "
                        f"(D44, A110) beside {VERDICT_ARCHIVE}: every later read refuses a "
                        f"file that is missing or whose bytes differ"
                    ),
                    "taken_at_commit": framework.git_head(),
                    "verdict_commit": VERDICT_COMMIT,
                    "files": manifest,
                },
                indent=2,
            )
            + "\n"
        )
    if not manifest_path.exists():
        raise GateError(
            f"gate {GATE_NAME}: {archive} is here but its manifest {manifest_path} is not; "
            f"the read cannot show the records are unchanged.  Refused."
        )
    manifest = json.loads(manifest_path.read_text()).get("files") or {}

    def read(rel: str) -> bytes | None:
        path = base / rel
        return path.read_bytes() if path.exists() else None

    integrity = check_manifest(manifest, files, read)

    rows: list[dict[str, Any]] = []
    passed = recorded.get("verdict") == "PASS" and integrity["unchanged"]
    n_compared = n_mismatched = n_components = n_components_differing = 0
    n_prime = n_prime_failing = n_disagreeing = 0
    for (configuration, arm), recorded_row in zip(expected, recorded["rows"]):
        key = f"A/{arm}/{configuration}"
        before_dir = before_archive(campaign, configuration, arm)
        after_dir = after_directory(campaign, configuration, arm)
        before = gc_mod._read(before_dir, side="before", key=key)
        after = gc_mod._read(after_dir, side="after", key=key)
        rederived = rederive_pair(before, after, before_dir, after_dir)
        disagreements = reconcile(recorded_row, rederived)
        stamps = {
            "before_at_the_cold_child's_commit": before.get("tree_git_head") == COLD_CHILD_COMMIT,
            "after_at_the_warmed_child's_commit": after.get("tree_git_head") == WARMED_CHILD_COMMIT,
            "after_made_under_the_verdict's_settings": (
                (after.get("campaign_test_set"), after.get("campaign_tau"))
                == (recorded.get("test_set"), recorded.get("tau"))
            ),
        }
        row = {
            "configuration": configuration,
            "arm": arm,
            "key": key,
            "before": {"path": framework._relative(before_dir, Path(campaign.runs_dir)), "tree_git_head": before.get("tree_git_head")},
            "after": {"path": framework._relative(after_dir, Path(campaign.runs_dir)), "tree_git_head": after.get("tree_git_head")},
            "recorded_passed": recorded_row.get("passed"),
            "rederived": {
                "counts": {k: rederived["counts"][k] for k in ("n_compared", "n_mismatched")},
                "prime_calls": {k: rederived["prime_calls"][k] for k in ("n_compared", "n_mismatched")},
                "states": {k: rederived["states"][k] for k in ("n_components_compared", "n_components_differing")},
                "warmup_rederived": {k: rederived["warmup_rederived"][k] for k in ("agrees", "n_compared", "n_differing")},
                "checks": rederived["checks"],
                "passed": rederived["passed"],
            },
            "disagreements_with_the_recorded_row": disagreements,
            "stamps": stamps,
        }
        row["consistent"] = not disagreements and all(stamps.values())
        passed = passed and row["consistent"] and bool(recorded_row.get("passed"))
        n_disagreeing += int(not row["consistent"])
        n_compared += rederived["counts"]["n_compared"]
        n_mismatched += rederived["counts"]["n_mismatched"]
        n_components += rederived["states"]["n_components_compared"]
        n_components_differing += rederived["states"]["n_components_differing"]
        n_prime += rederived["prime_calls"]["n_compared"]
        n_prime_failing += rederived["prime_calls"]["n_mismatched"]
        rows.append(row)
    _HELD.update(rows=rows, recorded=recorded, manifest=manifest, campaign=campaign)
    survey = framework.survey_heads(
        [base / "before", base / "after"], relative_to=Path(campaign.runs_dir) / framework.GATES_SUBPATH
    )
    return {
        "passed": passed,
        "criterion": (
            f"READ, NOT PRESSED (D44): the verdict gate {GATE_NAME} recorded at "
            f"{VERDICT_COMMIT[:8]} over the after records made at {WARMED_CHILD_COMMIT[:8]} "
            f"(the commit that introduced the warmed child), under the default settings "
            f"— returned as recorded once (1) its stamp, its settings and its pairs are "
            f"verified, (2) every file it compared is on disk and byte-identical to the "
            f"archive manifest, and (3) the comparison re-derived from those files gives "
            f"the recorded numbers on every pair.  Recorded criterion: "
            f"{recorded.get('criterion')}"
        ),
        "criterion_source": "D44 (the user, 2026-10-01); V5 experiment plan §6; A101 §15",
        "read_of_the_recorded_verdict": {
            "what": (
                f"a READ of the verdict recorded at {VERDICT_COMMIT[:8]}, not a press: no "
                f"run was made, no job was composed under this run ID's settings "
                f"({campaign.test_set}/{campaign.tau}), and the verdict is the default "
                f"settings' ({recorded.get('test_set')}/{recorded.get('tau')}) whatever "
                f"run ID reads it.  What guards each campaign's own records is the "
                f"per-record check evaluation_warmup.agrees, owed by the record contract"
            ),
            "path": framework._relative(source, Path(campaign.runs_dir)),
            "archived_copy": framework._relative(archive, Path(campaign.runs_dir)),
            "archived_by_this_read": first_read,
            "tree_git_head": recorded.get("tree_git_head"),
            "generated": recorded.get("generated"),
            "recorded_verdict": recorded.get("verdict"),
            "recorded_teeth": [
                {"tooth": t.get("tooth"), "tooth_result": t.get("tooth_result")}
                for t in recorded.get("teeth") or []
            ],
            "recorded_straddles": recorded.get("straddles"),
            "recorded_population": recorded.get("population"),
        },
        "archive_integrity": {
            "manifest": framework._relative(manifest_path, Path(campaign.runs_dir)),
            **integrity,
        },
        "straddles": (
            f"cold child at {COLD_CHILD_COMMIT[:8]} -> warmed child at {WARMED_CHILD_COMMIT[:8]} "
            f"(read; verdict recorded at {VERDICT_COMMIT[:8]})"
        ),
        "population": (
            f"READ, not pressed (D44): the verdict recorded at {VERDICT_COMMIT[:8]} under the "
            f"default settings ({recorded.get('test_set')}/{recorded.get('tau')}), "
            f"{recorded.get('verdict')}; re-derived here from its {len(rows)} archived "
            f"evaluation pair(s): {n_compared} count leaves compared under "
            f"{len(gc_mod.COUNT_PATHS)} declared paths, {n_mismatched} differing; {n_prime} "
            f"prime-count check(s), {n_prime_failing} failing; {n_components} coupling-state "
            f"components compared bit for bit, {n_components_differing} differing; "
            f"{len(rows) - n_disagreeing} of {len(rows)} pairs agree with the recorded row and "
            f"their stamps; {integrity['n_files'] - integrity['n_changed'] - integrity['n_missing']} "
            f"of {integrity['n_files']} compared files byte-identical to the manifest"
        ),
        "n_pairs": len(rows),
        "n_compared": n_compared,
        "n_mismatched": n_mismatched,
        "n_prime_checks": n_prime,
        "n_prime_checks_failing": n_prime_failing,
        "n_components_compared": n_components,
        "n_components_differing": n_components_differing,
        "n_pairs_disagreeing_with_the_record": n_disagreeing,
        "count_paths": dict(gc_mod.COUNT_PATHS),
        "state_files": list(gc_mod.STATE_FILES),
        "test_set": recorded.get("test_set"),
        "tau": recorded.get("tau"),
        "pressed_under": {"run_id": campaign.run_id, "test_set": campaign.test_set, "tau": campaign.tau},
        "runs_provenance": {
            **survey,
            "what": (
                "the archived records the read verified, surveyed by commit; none was "
                "made by this read (the framework's own survey has nothing to survey: "
                "the gate declares no job set)"
            ),
        },
        "rows": rows,
    }


# --------------------------------------------------------------------------
# the teeth
# --------------------------------------------------------------------------


def _teeth(campaign: Campaign) -> tuple[Tooth, ...]:
    def _last_row() -> dict[str, Any] | None:
        rows = _HELD.get("rows") or []
        return rows[-1] if rows else None

    def _record(row: Mapping[str, Any], side: str) -> dict[str, Any]:
        return json.loads(json.dumps(records_mod.read(Path(campaign.runs_dir) / row[side]["path"])))

    def a_doctored_count() -> tuple[bool, str]:
        row = _last_row()
        if row is None:
            return False, "the gate read nothing, so nothing can be doctored"
        before, after = _record(row, "before"), _record(row, "after")
        field = "node_calls_single_eval"
        was = after.get(field)
        if not isinstance(was, int):
            return False, f"{field} is {was!r} on the after side; nothing to add one to"
        after[field] = was + 1
        result = gc_mod.compare_counts(before, after)
        named = [m["field"] for m in result["mismatches"]]
        return result["n_mismatched"] == 1 and named == [field], (
            f"one added to {field} ({was} -> {was + 1}) in a copy of {row['key']}'s "
            f"archived after record: the re-derived comparison reports "
            f"{result['n_mismatched']} differing leaf/leaves of {result['n_compared']} ({named})"
        )

    def a_doctored_warmup_count() -> tuple[bool, str]:
        row = _last_row()
        if row is None:
            return False, "the gate read nothing"
        after = _record(row, "after")
        counts = ((after.get(WARMUP_BLOCK) or {}).get("warmup") or {}).get("counts")
        if not isinstance(counts, dict) or "node_calls_single_eval" not in counts:
            return False, "the archived after record carries no warm-up count leaves to doctor"
        was = counts["node_calls_single_eval"]
        counts["node_calls_single_eval"] = int(was) + 1
        result = rederive_agreement(after)
        named = [d["leaf"] for d in result["differing"]]
        return (not result["agrees"]) and named == ["node_calls_single_eval"], (
            f"one added to the warm-up's node_calls_single_eval ({was} -> {int(was) + 1}) in a "
            f"copy of {row['key']}'s archived after record: the re-derived check reads agrees = "
            f"{result['agrees']} with {result['n_differing']} differing leaf/leaves ({named})"
        )

    def a_doctored_archived_record() -> tuple[bool, str]:
        row, manifest = _last_row(), _HELD.get("manifest")
        if row is None or not manifest:
            return False, "the gate read nothing, so there is no archive to doctor"
        base = root(campaign)
        target = (Path(campaign.runs_dir) / row["after"]["path"] / RECORD_FILE).relative_to(base).as_posix()
        files = compared_files(campaign)
        original = (base / target).read_bytes()
        doctored = original.replace(b'"status": "ok"', b'"status": "OK"', 1)
        if doctored == original:
            doctored = original + b" "

        def read(rel: str) -> bytes | None:
            if rel == target:
                return doctored
            path = base / rel
            return path.read_bytes() if path.exists() else None

        result = check_manifest(manifest, files, read)
        return (not result["unchanged"]) and result["changed"] == [target], (
            f"one byte changed in a copy of {target}: the manifest check reads unchanged = "
            f"{result['unchanged']}, changed = {result['changed']} (of {result['n_files']} files)"
        )

    def a_doctored_recorded_verdict() -> tuple[bool, str]:
        row, recorded = _last_row(), _HELD.get("recorded")
        if row is None or recorded is None:
            return False, "the gate read nothing"
        copy = json.loads(json.dumps(recorded))
        index = len(copy["rows"]) - 1
        recorded_row = copy["rows"][index]
        was = int(recorded_row["counts"]["n_mismatched"])
        recorded_row["counts"]["n_mismatched"] = was + 1
        rederived = row["rederived"]
        found = reconcile(recorded_row, rederived)
        named = [d["field"] for d in found]
        return named == ["counts.n_mismatched"], (
            f"one added to {row['key']}'s recorded counts.n_mismatched ({was} -> {was + 1}) in a "
            f"copy of the verdict record: the reconciliation with the re-derived comparison "
            f"names {named}"
        )

    def a_verdict_at_another_commit() -> tuple[bool, str]:
        recorded = _HELD.get("recorded")
        if recorded is None:
            return False, "the gate read nothing"
        copy = json.loads(json.dumps(recorded))
        copy["tree_git_head"] = WARMED_CHILD_COMMIT
        problems = check_verdict_record(copy, pairs(campaign))
        return bool(problems) and problems[0].startswith("stamped"), (
            f"a copy of the verdict record stamped {WARMED_CHILD_COMMIT[:8]} instead of "
            f"{VERDICT_COMMIT[:8]}: refused — {problems}"
        )

    return (
        Tooth(
            name="a doctored count on one record",
            what="one added to node_calls_single_eval in a copy of an archived after record",
            must="be the one and only differing count leaf of the re-derived comparison",
            check=a_doctored_count,
        ),
        Tooth(
            name="a doctored warm-up count",
            what="one added to the warm-up's node_calls_single_eval in a copy of an archived after record",
            must="read as disagreement in the re-derived warm-up check, naming that leaf",
            check=a_doctored_warmup_count,
        ),
        Tooth(
            name="a doctored archived record",
            what="one byte changed in a copy of an archived after record's metrics.json",
            must="be caught by the archive manifest, naming that file and no other",
            check=a_doctored_archived_record,
        ),
        Tooth(
            name="a doctored recorded verdict",
            what="one added to a row's recorded count of differing leaves in a copy of the verdict record",
            must="be caught by the reconciliation with the re-derived comparison, naming that field alone",
            check=a_doctored_recorded_verdict,
        ),
        Tooth(
            name="a verdict stamped at another commit",
            what=f"a copy of the verdict record with tree_git_head set to {WARMED_CHILD_COMMIT[:8]}",
            must=f"be refused: the record read is the one stamped {VERDICT_COMMIT[:8]}",
            check=a_verdict_at_another_commit,
        ),
    )


def gate(campaign: Campaign) -> Gate:
    return Gate(
        name=GATE_NAME,
        plan_name=None,
        # A read (D44): no PROCESS run, no job composed under the run ID's settings.
        needs_runs=False,
        binds=(
            "the warmed evaluation child (V5 plan §6): a harness change, not a "
            "driver change — its verdict made once, at the commit that "
            "introduced it, and read under every run ID (D44)"
        ),
        what_it_proves=(
            "the warm-up, the bit-exact re-entry and the counter reset changed "
            "no count and no bit of any exit state on the gate job set's "
            "evaluation half under the default settings, and every warmed "
            "record's own determinism check re-derives as agreeing; read from "
            "the archived verdict and its records, verified unchanged and "
            "re-derived"
        ),
        body=lambda *, resume=False: body(campaign, resume=resume),
        teeth=_teeth(campaign),
    )
