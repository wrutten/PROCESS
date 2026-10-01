"""Where a press's records live: one self-contained folder per run ID.

Task **A107 (v5-campaign-settings-keys)**.  The user wanted to run the V5
campaign a second time under other settings and keep both: *"one
self-contained folder per run ID directly under the V5 folder's runs/"*.  The
layout::

    runs/
      _numba_cache/  _mplconfig/       shared caches (config.SHARED_CACHES)
      <run ID>/                         one folder per campaign settings
        run_settings.json               the settings the folder is of (this module)
        campaign/  supplementary/  gates/  timing/  single/  census/ …
        _press_logs/                    the presses' terminal output
      <another run ID>/ …

The **run ID** is ``config.run_id_for`` of the campaign's test set and its
tolerance or tolerance rule (``census_tau1e-08``, ``write_set_tau1e-06``,
``census_rule_epsvmc_times_epsfcn``).  ``Campaign.runs_dir`` *is* the run ID's
folder, so every path the harness derives from it — the chain's roots, the
shared pool, the gates' verdicts, the tallies, the timing stages, the derived
input files — lands inside it without a second construction, and every path a
job identity renders relative to it renders as it did before the layout: a
folder moved whole keeps every digest.

What this module holds:

* :func:`open_run` — the guard every press passes: refuses a ``runs/`` still in
  the layout before run IDs (pointing at the adoption), refuses a folder whose
  ``run_settings.json`` names other settings, and writes that file on the
  first press of a new run ID;
* :func:`stamp` and :func:`stamp_of_directory` — the run ID and settings every
  stage record carries, and the reading of them back;
* :func:`assert_stage_record_is_of_this_run` — the refusal of a stage record
  stamped with another run ID;
* :func:`adoption_plan` and :func:`adopt` — moving a tree in the old layout
  under the run ID its campaign records were made under;
* :func:`listing` — the run IDs on disk, with what each holds.

The settings-independent records every run ID needs without pressing them
again (the reproduction gate's verdict and pool records, the neutrality gates'
archived straddles) are copied into a new run ID's folder by an explicit
initialisation step, ``harness/gates/archived_records.py``.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from . import framework
from . import records as records_mod
from .config import (
    DEFAULT_RUN_ID,
    EXPERIMENT_DIR,
    SHARED_CACHES,
    TAU_BY_TEST_SET,
    Campaign,
    run_id_for,
)

#: The file that makes a folder under ``runs/`` a run ID's folder, and says
#: which settings it is of.
SETTINGS_FILE = "run_settings.json"

#: The settings a run ID is a key of, as stamped and compared.
SETTINGS_FIELDS: tuple[str, ...] = ("run_id", "test_set", "tau", "tau_rule")

#: The chain's run roots under a run ID's folder whose records are the
#: campaign's (``chain.campaign_plan``'s ``root_name`` and its stages).
CAMPAIGN_ROOT = "campaign"
CAMPAIGN_PHASE_DIRECTORIES: tuple[str, ...] = ("entry_references", "evaluation", "optimisation")

#: The tables document's name for the declared default campaign: the
#: committed ``paper_tables.md``.
DEFAULT_TABLES_DOCUMENT = "paper_tables.md"


class RunLayoutError(framework.GateError):
    """A press refused because of where its records would go or come from.

    A gate error, so every stage of the button that reports a refused gate
    reports this one the same way rather than dying past it."""


# --------------------------------------------------------------------------
# the settings of a run ID
# --------------------------------------------------------------------------


def settings_of(campaign: Campaign) -> dict[str, Any]:
    """The run ID's settings: what its name is a key of, and each τ."""
    return {
        "run_id": campaign.run_id,
        "test_set": campaign.test_set,
        "tau": None if campaign.tau_rule else float(campaign.tau),
        "tau_rule": campaign.tau_rule,
        "tau_by_configuration": {c.name: campaign.tau_for(c) for c in campaign.configurations},
    }


def stamp(campaign: Campaign) -> dict[str, Any] | None:
    """What a stage record carries to say which run ID it is of."""
    if campaign.run_id is None:
        return None
    settings = settings_of(campaign)
    return {name: settings[name] for name in SETTINGS_FIELDS}


def settings_path(folder: Path) -> Path:
    return Path(folder) / SETTINGS_FILE


def read_settings(folder: Path) -> dict[str, Any] | None:
    path = settings_path(folder)
    if not path.exists():
        return None
    return json.loads(path.read_text())


def stamp_of_directory(directory: Path) -> dict[str, Any] | None:
    """The run ID stamp of the folder *directory* lies in, read from the
    nearest ``run_settings.json`` above it; None outside every run ID's folder
    (a ``--outdir`` elsewhere, a fixture)."""
    here = Path(directory).resolve()
    for folder in (here, *here.parents):
        settings = read_settings(folder)
        if settings is not None:
            return {name: settings.get(name) for name in SETTINGS_FIELDS}
    return None


def tables_document_name(run_id: str | None) -> str:
    """The tables document of a run ID: the committed ``paper_tables.md`` for
    the declared default campaign, ``paper_tables_<run ID>.md`` for any other."""
    if run_id is None or run_id == DEFAULT_RUN_ID:
        return DEFAULT_TABLES_DOCUMENT
    return f"paper_tables_{run_id}.md"


# --------------------------------------------------------------------------
# the guard every press passes
# --------------------------------------------------------------------------


def run_folders(root: Path) -> list[Path]:
    """Every run ID's folder under *root*: a directory holding the settings file."""
    root = Path(root)
    if not root.exists():
        return []
    return sorted(p for p in root.iterdir() if p.is_dir() and settings_path(p).exists())


def legacy_entries(root: Path) -> list[Path]:
    """Entries of ``runs/`` in the layout before run IDs: everything at the
    top level that is neither a shared cache nor a run ID's folder."""
    root = Path(root)
    if not root.exists():
        return []
    return sorted(
        p
        for p in root.iterdir()
        if p.name not in SHARED_CACHES and not (p.is_dir() and settings_path(p).exists())
    )


def open_run(campaign: Campaign, *, create: bool) -> dict[str, Any] | None:
    """Refuse a press whose records would not be this run ID's alone; return
    the folder's settings (written here on a new run ID's first press when
    *create*).

    Three refusals: ``runs/`` still holds records in the layout before run
    IDs (a press would start a second, empty campaign beside them — adopt
    first); the run ID's folder says it is of other settings (a folder
    renamed or a settings file edited by hand — its records are not this
    run ID's); and the settings file is unreadable.
    """
    if campaign.runs_root is None or campaign.run_id is None:
        return None
    legacy = legacy_entries(campaign.runs_root)
    if legacy:
        raise RunLayoutError(
            f"runs/ ({campaign.runs_root}) holds {len(legacy)} entr"
            f"{'y' if len(legacy) == 1 else 'ies'} in the layout before run IDs "
            f"({', '.join(p.name for p in legacy[:8])}{' …' if len(legacy) > 8 else ''}).  "
            f"A press now writes under runs/<run ID>/ and would start beside "
            f"them as if they did not exist.  Re-lay them first: "
            f"`experiment_runner.py --adopt-records-layout` lists the move, "
            f"`--adopt-records-layout --apply` makes it."
        )
    folder = Path(campaign.runs_dir)
    try:
        recorded = read_settings(folder)
    except json.JSONDecodeError as exc:
        raise RunLayoutError(f"{settings_path(folder)} is not readable JSON: {exc}") from exc
    wanted = stamp(campaign) or {}
    if recorded is not None:
        differing = {
            name: (recorded.get(name), wanted.get(name))
            for name in SETTINGS_FIELDS
            if recorded.get(name) != wanted.get(name)
        }
        if differing:
            raise RunLayoutError(
                f"{settings_path(folder)} says the folder is of other settings than "
                f"the run ID {campaign.run_id!r} asked for: "
                + ", ".join(f"{k} recorded {a!r}, asked {b!r}" for k, (a, b) in differing.items())
                + ".  Its records are not this run ID's; refused rather than read "
                f"or added to."
            )
        return recorded
    if not create:
        return None
    folder.mkdir(parents=True, exist_ok=True)
    settings = {
        **settings_of(campaign),
        "how": "first press under these settings",
        "created": _dt.datetime.now().isoformat(timespec="seconds"),
        "created_at_git_head": framework.git_head(),
    }
    settings_path(folder).write_text(json.dumps(settings, indent=2) + "\n")
    return settings


def header(campaign: Campaign) -> str:
    """The line every stage prints first: which run ID, which settings, where."""
    if campaign.run_id is None:
        return f"records under {campaign.runs_dir} (no run ID: a fixture)"
    if campaign.tau_rule is not None:
        tolerance = f"tolerance rule {campaign.tau_rule} (" + ", ".join(
            f"{c.name} {campaign.tau_for(c)!r}" for c in campaign.configurations
        ) + ")"
    else:
        tolerance = f"tau {campaign.tau!r}" + (" (overridden)" if campaign.tau_overridden else "")
    return (
        f"run ID {campaign.run_id}: test set {campaign.test_set}, {tolerance}; "
        f"records under runs/{campaign.run_id}/"
    )


def assert_stage_record_is_of_this_run(
    record: Mapping[str, Any], *, run_id: str | None, what: str
) -> str:
    """Refuse a stage record stamped with another run ID.

    A record with no stamp was made before the run-ID layout; in a folder the
    adoption attributed to a run ID (its ``run_settings.json`` says so, with
    the campaign records that decided it) it is that run ID's, and the
    sentence says so rather than leaving it to be assumed.
    """
    stamped = (record.get("run") or {}).get("run_id") if isinstance(record.get("run"), Mapping) else None
    if stamped is None:
        return f"{what} carries no run ID stamp (made before the run-ID layout); read as {run_id}'s, the folder it is in"
    if run_id is not None and stamped != run_id:
        raise RunLayoutError(
            f"{what} is stamped with run ID {stamped!r}, not {run_id!r}, the run "
            f"ID this press was asked for.  A stage record of other settings is "
            f"never read as this run's; refused."
        )
    return f"{what} is stamped {stamped}"


# --------------------------------------------------------------------------
# the manifest: what is on disk, to the byte for the run records
# --------------------------------------------------------------------------


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def manifest(root: Path) -> dict[str, dict[str, Any]]:
    """Every file under *root* but the shared caches: relative path -> size,
    modification time (ns) and, for a run record (``metrics.json``), its
    SHA-256.  The adoption compares one before and after its renames; the
    isolation check one before and after a press."""
    root = Path(root)
    rows: dict[str, dict[str, Any]] = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if relative.parts and relative.parts[0] in SHARED_CACHES:
            continue
        if path.is_symlink() or not path.is_file():
            continue
        stat = path.stat()
        row: dict[str, Any] = {"size": stat.st_size, "mtime_ns": stat.st_mtime_ns}
        if path.name == "metrics.json":
            row["sha256"] = _sha256(path)
        rows[relative.as_posix()] = row
    return rows


# --------------------------------------------------------------------------
# adoption: the old layout re-laid under its run ID
# --------------------------------------------------------------------------


def _identity_settings(record: Mapping[str, Any]) -> tuple[str, float | None, str | None]:
    """A record's (test set, τ, rule) as its job identity states them."""
    identity = record.get("job_identity") or {}
    defaults = records_mod.IDENTITY_DEFAULTS_WHEN_ABSENT
    rule = identity.get("tau_rule", defaults["tau_rule"])
    tau = identity.get("tau", defaults["tau"])
    return (
        str(identity.get("test_set", defaults["test_set"])),
        None if rule else float(tau),
        rule,
    )


def _survey_settings(entries: list[Path]) -> dict[str, Any]:
    """Every run record under *entries*: by kind and by settings."""
    campaign_settings: Counter = Counter()
    campaign_example: dict[tuple, str] = {}
    other: Counter = Counter()
    n_records = 0
    for entry in entries:
        paths = [entry] if entry.name == "metrics.json" else (sorted(entry.rglob("metrics.json")) if entry.is_dir() else [])
        for path in paths:
            n_records += 1
            try:
                record = json.loads(path.read_text())
            except Exception:  # noqa: BLE001 - a half-written record is listed, not guessed
                other[("unreadable", None, None, None)] += 1
                continue
            settings = _identity_settings(record)
            kind = str(record.get("campaign_run_kind"))
            if kind == "campaign":
                campaign_settings[settings] += 1
                campaign_example.setdefault(settings, str(path))
            else:
                other[(kind, *settings)] += 1
    return {
        "n_records": n_records,
        "campaign": campaign_settings,
        "campaign_example": campaign_example,
        "other": other,
    }


def adoption_plan(root: Path, *, fallback: Campaign) -> dict[str, Any]:
    """What ``--adopt-records-layout`` would do to *root*, without doing it.

    The run ID is the one the tree's **campaign records** were made under,
    read from each record's job identity (the identity is what a run ID is a
    key of).  Gate, smoke, timing and supplementary records do not decide it:
    they carry settings of their own by design (the reproduction gate's are
    V4's, gate GC's its declared straddle set, a supplementary stage its own
    τ, a ``--run`` smoke whatever it was asked for) and belong to the press
    that made them; they are counted and listed.  A tree whose campaign
    records carry **more than one** setting is refused with the list: it is
    two campaigns, and re-laying both under one run ID would be the mixing
    the layout exists to end.  A tree with no campaign record is adopted
    under *fallback*'s run ID (the settings the command was given) and says
    so.
    """
    root = Path(root)
    legacy = legacy_entries(root)
    survey = _survey_settings(legacy)
    plan: dict[str, Any] = {
        "root": str(root),
        "legacy_entries": [p.name for p in legacy],
        "shared_caches_staying": [name for name in SHARED_CACHES if (root / name).exists()],
        "run_folders_present": [p.name for p in run_folders(root)],
        "n_records": survey["n_records"],
        "campaign_records_by_settings": [
            {"test_set": s[0], "tau": s[1], "tau_rule": s[2], "n": n, "example": survey["campaign_example"][s]}
            for s, n in sorted(survey["campaign"].items(), key=str)
        ],
        "other_records_by_kind_and_settings": [
            {"run_kind": k[0], "test_set": k[1], "tau": k[2], "tau_rule": k[3], "n": n}
            for k, n in sorted(survey["other"].items(), key=str)
        ],
        "refused": None,
    }
    if not legacy:
        plan["refused"] = "nothing to adopt: runs/ holds no entry in the layout before run IDs"
        return plan
    if len(survey["campaign"]) > 1:
        plan["refused"] = (
            f"the campaign records carry {len(survey['campaign'])} different settings "
            f"({'; '.join(f'{r['test_set']} tau {r['tau']!r} rule {r['tau_rule']!r}: {r['n']}' for r in plan['campaign_records_by_settings'])}): "
            f"two campaigns cannot be re-laid under one run ID.  Separate them by hand "
            f"first; nothing was moved."
        )
        return plan
    if survey["campaign"]:
        (test_set, tau, rule), = survey["campaign"].keys()
        run_id = run_id_for(test_set, tau if rule is None else TAU_BY_TEST_SET[test_set], rule)
        decided_by = f"the {sum(survey['campaign'].values())} campaign record(s), all of one setting"
        settings = {"run_id": run_id, "test_set": test_set, "tau": tau, "tau_rule": rule}
    else:
        run_id = fallback.run_id
        decided_by = "no campaign record names the settings; adopted under the settings the command was given"
        settings = {name: (stamp(fallback) or {}).get(name) for name in SETTINGS_FIELDS}
    destination = root / run_id
    clashes = [p.name for p in legacy if (destination / p.name).exists()] if destination.exists() else []
    if destination.exists() and not settings_path(destination).exists() and destination in legacy:
        clashes.append(f"{run_id} itself is a directory in the old layout")
    if clashes:
        plan["refused"] = f"runs/{run_id}/ already holds {clashes}; nothing was moved"
    plan.update(
        run_id=run_id,
        settings=settings,
        decided_by=decided_by,
        moves=[{"from": p.name, "to": f"{run_id}/{p.name}"} for p in legacy],
    )
    return plan


def adopt(root: Path, *, fallback: Campaign, apply: bool) -> dict[str, Any]:
    """Re-lay *root* under its run ID — a dry run unless *apply*.

    Each old top-level entry is **renamed** into ``runs/<run ID>/`` on the
    same filesystem: one ``os.rename`` per entry, so no file is opened, no
    byte and no modification time inside changes, and a record's path
    relative to the run ID's folder is its old path relative to ``runs/`` —
    which is what every job identity renders, so every digest holds.  The
    settings file is written **first**, marking the folder as a run ID's,
    so an interrupted adoption leaves a folder the next one completes.  The
    record count of the whole tree is taken before and after.
    """
    root = Path(root)
    plan = adoption_plan(root, fallback=fallback)
    plan["applied"] = False
    if plan["refused"] or not apply:
        return plan
    before_manifest = manifest(root)
    before = sum(1 for _ in root.rglob("metrics.json"))
    destination = root / plan["run_id"]
    destination.mkdir(exist_ok=True)
    settings = {
        **plan["settings"],
        "how": "adopted from the layout before run IDs (experiment_runner.py --adopt-records-layout --apply)",
        "decided_by": plan["decided_by"],
        "campaign_records_by_settings": plan["campaign_records_by_settings"],
        "other_records_by_kind_and_settings": plan["other_records_by_kind_and_settings"],
        "moved": [m["from"] for m in plan["moves"]],
        "created": _dt.datetime.now().isoformat(timespec="seconds"),
        "created_at_git_head": framework.git_head(),
    }
    settings_path(destination).write_text(json.dumps(settings, indent=2, default=str) + "\n")
    for move in plan["moves"]:
        os.rename(root / move["from"], root / move["to"])
    after = sum(1 for _ in root.rglob("metrics.json"))
    inside = sum(1 for _ in destination.rglob("metrics.json"))
    # Every file of the moved entries, compared by its path relative to the
    # entry: the same size, the same modification time, and for every run
    # record the same SHA-256 — the adoption opened no file.
    prefix = f"{plan['run_id']}/"
    after_manifest = {
        k[len(prefix):]: v
        for k, v in manifest(root).items()
        if k.startswith(prefix) and k != prefix + SETTINGS_FILE
    }
    moved_before = {k: v for k, v in before_manifest.items() if k.split("/")[0] in {m["from"] for m in plan["moves"]}}
    differing = sorted(
        k for k in set(moved_before) | set(after_manifest) if moved_before.get(k) != after_manifest.get(k)
    )
    plan.update(
        applied=True,
        n_records_before=before,
        n_records_after=after,
        n_records_in_folder=inside,
        manifest_comparison={
            "n_files_compared": len(moved_before),
            "n_run_records_digested": sum(1 for v in moved_before.values() if "sha256" in v),
            "n_differing": len(differing),
            "differing": differing[:20],
        },
    )
    settings["manifest_comparison"] = plan["manifest_comparison"]
    settings_path(destination).write_text(json.dumps(settings, indent=2, default=str) + "\n")
    if before != after or differing:
        raise RunLayoutError(
            f"the adoption changed runs/: {before} run records before, {after} after; "
            f"{len(differing)} file(s) differ by path, size, time or digest (first: {differing[:3]})"
        )
    return plan


# --------------------------------------------------------------------------
# the listing
# --------------------------------------------------------------------------


def _campaign_records(folder: Path) -> dict[str, Any]:
    by_phase: dict[str, Counter] = {}
    heads: Counter = Counter()
    for phase in CAMPAIGN_PHASE_DIRECTORIES:
        counter: Counter = Counter()
        for path in sorted((folder / CAMPAIGN_ROOT / phase).rglob("metrics.json")):
            try:
                record = json.loads(path.read_text())
            except Exception:  # noqa: BLE001
                counter["unreadable"] += 1
                continue
            counter[str(record.get("status"))] += 1
            heads[str(record.get("tree_git_head"))[:8]] += 1
        by_phase[phase] = counter
    return {
        "by_phase_and_status": {phase: dict(sorted(c.items())) for phase, c in by_phase.items()},
        "n": sum(sum(c.values()) for c in by_phase.values()),
        "commits": dict(sorted(heads.items())),
    }


def _stage_record_summary(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        record = json.loads(path.read_text())
    except Exception:  # noqa: BLE001
        return {"readable": False}
    summary: dict[str, Any] = {
        "written": _dt.datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds"),
        "tree_git_head": record.get("tree_git_head"),
    }
    if "n_pass" in record:
        summary.update(n_pass=record.get("n_pass"), n_gates=record.get("n_gates"), n_fail=record.get("n_fail"), n_not_run=record.get("n_not_run"))
    run = record.get("run") if isinstance(record.get("run"), Mapping) else None
    summary["run_id_stamp"] = (run or {}).get("run_id")
    return summary


def listing(root: Path) -> dict[str, Any]:
    """The run IDs on disk, each with what it holds.  No comparison between
    them: the user compares from the folders."""
    root = Path(root)
    rows = []
    for folder in run_folders(root):
        settings = read_settings(folder) or {}
        gates = folder / "gates"
        rows.append(
            {
                "run_id": folder.name,
                "settings": {name: settings.get(name) for name in SETTINGS_FIELDS},
                "tau_by_configuration": settings.get("tau_by_configuration"),
                "how": settings.get("how"),
                "name_matches_settings": settings.get("run_id") == folder.name,
                "campaign_records": _campaign_records(folder),
                "n_run_records": sum(1 for _ in folder.rglob("metrics.json")),
                "gate_table": _stage_record_summary(gates / "gate_table" / "measurements.json"),
                "tallies": {
                    name: _stage_record_summary(gates / name / "measurements.json")
                    for name in ("tally_evaluation", "tally_optimisation", "tally_supplementary")
                },
                "tables_document": {
                    "name": tables_document_name(folder.name),
                    "exists": (EXPERIMENT_DIR / tables_document_name(folder.name)).exists(),
                },
            }
        )
    return {
        "root": str(root),
        "run_ids": rows,
        "shared_caches": [name for name in SHARED_CACHES if (root / name).exists()],
        "legacy_entries": [p.name for p in legacy_entries(root)],
    }


def print_listing(block: Mapping[str, Any]) -> None:
    print(f"  runs/ = {block['root']}")
    print(f"  shared caches: {', '.join(block['shared_caches']) or '(none)'}")
    if block["legacy_entries"]:
        print(
            f"  ENTRIES IN THE LAYOUT BEFORE RUN IDS: {', '.join(block['legacy_entries'])} "
            f"(--adopt-records-layout)"
        )
    if not block["run_ids"]:
        print("  no run ID's folder on disk")
    for row in block["run_ids"]:
        s = row["settings"]
        tolerance = f"rule {s['tau_rule']}" if s["tau_rule"] else f"tau {s['tau']!r}"
        print(f"\n  {row['run_id']}" + ("" if row["name_matches_settings"] else "   (FOLDER NAME DOES NOT MATCH ITS SETTINGS)"))
        print(f"    settings: test set {s['test_set']}, {tolerance}; {row['how']}")
        if s["tau_rule"]:
            print(f"    tau by configuration: {row['tau_by_configuration']}")
        c = row["campaign_records"]
        print(f"    campaign records: {c['n']}" + (f" at {', '.join(f'{h} ({n})' for h, n in c['commits'].items())}" if c["commits"] else ""))
        for phase, statuses in c["by_phase_and_status"].items():
            if statuses:
                print(f"      {phase:<18} " + ", ".join(f"{k} {v}" for k, v in statuses.items()))
        print(f"    run records in the folder: {row['n_run_records']}")
        table = row["gate_table"]
        if table is None:
            print("    gate table: none")
        else:
            print(
                f"    gate table: {table.get('n_pass')} PASS of {table.get('n_gates')} "
                f"({table.get('n_fail')} FAIL, {table.get('n_not_run')} not run), written {table.get('written')}"
            )
        for name, tally in row["tallies"].items():
            print(f"    {name}: " + ("none" if tally is None else f"record written {tally.get('written')}"))
        doc = row["tables_document"]
        print(f"    tables document {doc['name']}: {'present' if doc['exists'] else 'none'}")
