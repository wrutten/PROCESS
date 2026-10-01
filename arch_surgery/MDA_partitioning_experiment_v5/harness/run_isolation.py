"""The run-ID layout's acceptance check: a press under one run ID changes
nothing outside its own folder.

Task **A107 (v5-campaign-settings-keys)**.  ``experiment_runner.py
--run-isolation smoke`` presses the harness's own smoke chain (one seed, the
cheapest configuration, both phases, every arm, the tallies and the tally's
contract gate) under the run ID the settings name, and around it:

(a) every file the press created or changed under ``runs/`` (the shared caches
    aside) is under ``runs/<run ID>/``, and the smoke's own records, stage
    records and press record are among them;
(b) **nothing under any other run ID's folder changed**: a manifest of every
    file's path, size and modification time, and the SHA-256 of every
    ``metrics.json``, taken before and after the press, identical;
(c) the reproduction gate was **not pressed**: its verdict files and the pool
    records of its job set in this folder are byte- and time-identical
    before and after, and its verdict is read (``registry``'s run-once gate,
    a read of the copy commit's record) from this run ID's folder;
(d) the listing (``run_layout.listing``) shows this run ID and the others.

Two teeth: the pool's refusal of a job resolving into another run ID's folder
(``gate_resume_identity.a_job_never_resolves_into_another_run_ids_folder``),
and the manifest comparison reporting a ``metrics.json`` whose digest was
changed in a doctored copy of the after-manifest.  A check with no other run
ID on disk proves nothing about isolation and refuses.

The shared caches (``config.SHARED_CACHES``) are outside the manifest: numba
may add compiled functions to its cache during any press, and that is the
cache being shared, not a record moving.  The record of this check goes under
``runs/<run ID>/run_isolation/``, written after the after-manifest is taken.
"""

from __future__ import annotations

import copy
import datetime as _dt
import json
from pathlib import Path
from typing import Any, Callable, Mapping

from .core import framework
from .core import pool as pool_mod
from .core import run_layout
from .core.config import SHARED_CACHES, Campaign
from .core.framework import GateError
from .core.run_layout import manifest

STAGE_NAME = "run_isolation"


def differences(before: Mapping[str, Any], after: Mapping[str, Any], *, prefix: str = "") -> dict[str, list[str]]:
    """Files added, removed or changed (size, time or digest) under *prefix*."""
    b = {k: v for k, v in before.items() if k.startswith(prefix)}
    a = {k: v for k, v in after.items() if k.startswith(prefix)}
    return {
        "added": sorted(set(a) - set(b)),
        "removed": sorted(set(b) - set(a)),
        "changed": sorted(k for k in set(a) & set(b) if a[k] != b[k]),
    }


def _n(diff: Mapping[str, list[str]]) -> int:
    return sum(len(v) for v in diff.values())


def _reproduction_paths(campaign: Campaign) -> list[str]:
    """This folder's reproduction-gate files: its verdict directory and the
    pool records its job set resolves to, relative to ``runs/``."""
    from .gates import reproduction as reproduction_mod  # noqa: PLC0415

    root = Path(campaign.runs_root)
    paths = [Path(campaign.runs_dir) / reproduction_mod.RUNS_SUBPATH]
    try:
        paths += pool_mod.directories_for(reproduction_mod.jobs_read(campaign), campaign)
    except Exception:  # noqa: BLE001 - no record of the job set: the verdict files alone
        pass
    return [Path(p).resolve().relative_to(root.resolve()).as_posix() + "/" for p in paths]


def check(campaign: Campaign, press: Callable[[], int]) -> dict[str, Any]:
    """Press the smoke under *campaign*'s run ID and check (a)–(d); the record."""
    from .gates import gate_resume_identity as resume_identity_mod  # noqa: PLC0415
    from .gates import registry as registry_mod  # noqa: PLC0415

    if campaign.runs_root is None or campaign.run_id is None:
        raise GateError("the isolation check needs a run ID's campaign")
    root = Path(campaign.runs_root)
    mine = campaign.run_id
    others = [f.name for f in run_layout.run_folders(root) if f.name != mine]
    if not others:
        raise GateError(
            f"no run ID's folder under {root} besides {mine!r}: a press under one "
            f"run ID cannot be shown to leave another's alone when there is no other"
        )
    reproduction_paths = _reproduction_paths(campaign)
    started = _dt.datetime.now().isoformat(timespec="seconds")
    before = manifest(root)
    rc = press()
    after = manifest(root)
    finished = _dt.datetime.now().isoformat(timespec="seconds")

    whole = differences(before, after)
    touched = whole["added"] + whole["removed"] + whole["changed"]
    outside = [p for p in touched if not p.startswith(f"{mine}/")]
    inside_by_top: dict[str, int] = {}
    for p in touched:
        if p.startswith(f"{mine}/"):
            top = p.split("/")[1] if p.count("/") >= 1 else p
            inside_by_top[top] = inside_by_top.get(top, 0) + 1
    new_records = [p for p in whole["added"] + whole["changed"] if p.endswith("/metrics.json")]
    press_record = Path(campaign.runs_dir) / "smoke" / "press.json"
    smoke_records = [p for p in new_records if p.startswith(f"{mine}/smoke/")]
    part_a = {
        "n_files_added_or_changed": len(touched),
        "outside_this_run_ids_folder": outside,
        "inside_by_top_level": dict(sorted(inside_by_top.items())),
        "n_run_records_made_or_changed": len(new_records),
        "n_smoke_records_made": len(smoke_records),
        "run_records_outside": [p for p in new_records if not p.startswith(f"{mine}/")],
        "press_record": str(press_record) if press_record.exists() else None,
        "passed": not outside and press_record.exists() and bool(smoke_records),
    }

    part_b = {}
    for other in others:
        diff = differences(before, after, prefix=f"{other}/")
        part_b[other] = {
            "n_files": sum(1 for k in before if k.startswith(f"{other}/")),
            "n_run_records_digested": sum(1 for k, v in before.items() if k.startswith(f"{other}/") and "sha256" in v),
            "added": diff["added"],
            "removed": diff["removed"],
            "changed": diff["changed"],
            "identical": _n(diff) == 0,
        }

    changed_reproduction = [p for p in touched if any(p.startswith(r) for r in reproduction_paths)]
    try:
        read = registry_mod.gates_only(campaign)["reproduction"].body(resume=True)
        verdict_read = {
            "passed": bool(read.get("passed")),
            "path": (read.get("read_of_the_recorded_verdict") or {}).get("path"),
            "tree_git_head": (read.get("read_of_the_recorded_verdict") or {}).get("tree_git_head"),
            "n_runs_reproduced": read.get("n_runs_reproduced"),
            "n_runs": read.get("n_runs"),
        }
    except GateError as exc:
        verdict_read = {"passed": False, "refused": str(exc)}
    part_c = {
        "n_reproduction_paths_watched": len(reproduction_paths),
        "changed_by_the_press": changed_reproduction,
        "verdict_read": verdict_read,
        "verdict_is_in_this_run_ids_folder": str(verdict_read.get("path") or "").startswith(str(Path(campaign.runs_dir))),
    }
    part_c["passed"] = (
        not changed_reproduction and verdict_read.get("passed") and part_c["verdict_is_in_this_run_ids_folder"]
    )

    listed = run_layout.listing(root)
    listed_ids = [row["run_id"] for row in listed["run_ids"]]
    part_d = {"run_ids_listed": listed_ids, "passed": mine in listed_ids and all(o in listed_ids for o in others)}

    teeth = []
    caught, message = resume_identity_mod.a_job_never_resolves_into_another_run_ids_folder(campaign)
    teeth.append({"tooth": "a job resolving into another run ID's folder", "caught": caught, "message": message})
    doctored = copy.deepcopy(after)
    target = next((k for k, v in doctored.items() if k.startswith(f"{others[0]}/") and "sha256" in v), None)
    if target is None:
        teeth.append({"tooth": "a doctored after-manifest", "caught": False, "message": f"no run record in runs/{others[0]}/ to doctor"})
    else:
        doctored[target]["sha256"] = "0" * 64
        seen = differences(before, doctored, prefix=f"{others[0]}/")["changed"]
        teeth.append(
            {
                "tooth": "a doctored after-manifest",
                "caught": seen == [target],
                "message": f"one metrics.json digest of runs/{others[0]}/ zeroed in a copy of the after-manifest: the comparison reports {seen}",
            }
        )

    passed = (
        part_a["passed"]
        and all(row["identical"] for row in part_b.values())
        and part_c["passed"]
        and part_d["passed"]
        and all(t["caught"] for t in teeth)
    )
    record = {
        "stage": STAGE_NAME,
        "what_this_is": (
            "the run-ID layout's acceptance check: the smoke chain pressed under this "
            "run ID, with (a) everything it wrote inside this run ID's folder, (b) "
            "every other run ID's folder unchanged by path, size, modification time "
            "and run-record digest, (c) the reproduction gate not pressed and its "
            "verdict read from this folder, (d) the listing showing every run ID"
        ),
        "verdict": "PASS" if passed else "FAIL",
        "run": run_layout.stamp(campaign),
        "other_run_ids": others,
        "smoke_press_exit_code": rc,
        "started": started,
        "finished": finished,
        "tree_git_head": framework.git_head(),
        "manifest_scope": "every file under runs/ except the shared caches " + ", ".join(SHARED_CACHES),
        "n_files_before": len(before),
        "n_files_after": len(after),
        "a_written_inside": part_a,
        "b_others_unchanged": part_b,
        "c_reproduction_not_pressed": part_c,
        "d_listing": part_d,
        "teeth": teeth,
    }
    out = Path(campaign.runs_dir) / STAGE_NAME / "smoke.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record, indent=2, default=str) + "\n")
    record["record"] = str(out)
    return record


def report(record: Mapping[str, Any]) -> list[str]:
    a, c, d = record["a_written_inside"], record["c_reproduction_not_pressed"], record["d_listing"]
    lines = [
        f"  run ID {record['run']['run_id']}; other run ID(s): {', '.join(record['other_run_ids'])}; "
        f"smoke press exit code {record['smoke_press_exit_code']}",
        f"  (a) {a['n_files_added_or_changed']} file(s) added or changed by the press, "
        f"{len(a['outside_this_run_ids_folder'])} outside runs/{record['run']['run_id']}/; "
        f"{a['n_run_records_made_or_changed']} run record(s) made or re-made ({a['n_smoke_records_made']} under smoke/); by folder: {a['inside_by_top_level']}"
        f" -> {'PASS' if a['passed'] else 'FAIL'}",
    ]
    for other, row in record["b_others_unchanged"].items():
        lines.append(
            f"  (b) runs/{other}/: {row['n_files']} file(s), {row['n_run_records_digested']} run record(s) "
            f"digested; added {len(row['added'])}, removed {len(row['removed'])}, changed {len(row['changed'])}"
            f" -> {'IDENTICAL' if row['identical'] else 'CHANGED'}"
        )
    lines.append(
        f"  (c) reproduction files watched {c['n_reproduction_paths_watched']}, changed by the press "
        f"{len(c['changed_by_the_press'])}; verdict read: {c['verdict_read']}"
        f" -> {'PASS' if c['passed'] else 'FAIL'}"
    )
    lines.append(f"  (d) listed: {d['run_ids_listed']} -> {'PASS' if d['passed'] else 'FAIL'}")
    for tooth in record["teeth"]:
        lines.append(f"  tooth {'tripped' if tooth['caught'] else 'DID NOT TRIP'}: {tooth['tooth']} — {tooth['message']}")
    lines.append(f"  verdict: {record['verdict']}; record {record.get('record')}")
    return lines
