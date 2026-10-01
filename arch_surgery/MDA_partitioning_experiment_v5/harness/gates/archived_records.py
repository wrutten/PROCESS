"""The records every run ID reads and no run ID re-makes, copied into a new one.

Task **A107 (v5-campaign-settings-keys)**.  Under the run-ID layout
(``core/run_layout.py``) a press reads nothing outside its run ID's folder, so
a second campaign's folder starts without the records that are **read-only by
design** — made once, at a commit that is gone, and never re-made:

* the reproduction gate's verdict at the copy commit ``d6c246a1`` and the pool
  records it compared (``registry.RUN_ONCE``: GR is read, never pressed; the
  tally's contract gate reproduces V4's published cells on those twenty runs);
* gate GC's straddle records (one file per driver change; G2 part (ii) reads
  the DR9 -> DR10 one) and its job set's pool records — made under GC's
  **declared** straddle test set whatever campaign the button was pressed
  under, so the same jobs under every run ID;
* gate G1's ``before`` capture and its archived straddles, each made at the
  commit before a driver change;
* gate ``evaluation_warmup``'s archived verdict, its manifest and both sides
  it compared (A101's cold child, gone from the tree, and A102's warmed child
  under the default settings): the gate is read, never pressed (D44, A110);
* the derived (lifted) input files, whose bytes are gated on a committed
  digest and so are the same under every setting.

**The choice: an explicit, committed initialisation step that copies them
from an existing run ID's folder** (``experiment_runner.py
--copy-archived-records <from run ID>``, a dry run with a listing unless
``--apply``), not a shared read-only area.  The reason is the job identity:
it renders every path relative to the run ID's folder (``Campaign.runs_dir``),
and the pool resolves a job by that identity's digest inside the folder.  A
record in a shared area outside the folder would carry its entry-state paths
rendered against another root, so the gates' own job sets would never
resolve to it and the gates would make it again — the press this step exists
to avoid.  Copied to the **same relative path** in the new folder, every
record is the same job by construction, and the folder stays
self-contained: it can be moved, relocated or deleted without breaking
another.  The cost is disk (about a quarter of a gigabyte, most of it G1's
captures) and one command per new run ID.  Copies, never hard links: a
verdict file is rewritten in place by a re-press, and a hard link would
carry that write into the other run ID's folder.

Each file is copied with its modification time (``shutil.copy2``) and its
SHA-256 is compared with the source's after the copy; a file already present
with the same bytes is left alone, one with other bytes refuses the whole
step before anything is copied.  Nothing under the source folder is written.
Afterwards the step composes the gates' own job sets **under the destination
campaign** and states how many of them the pool resolves to a copied record
and keeps — the proof that the copies are the records those presses read.
Whether a gate whose archive was made under the source's settings (G1)
passes under the destination's is that gate's verdict to give, not this
step's; the warm-up gate's verdict is the source's by construction (D44).

**One archive at a time** (``--archive <gate>``, A110): a run ID that already
holds the other archives can be given one archive that is new or changed
without the whole step refusing on the files a re-press has since rewritten
in place (a verdict file such as ``gates/reproduction/gate.json`` is
rewritten by every read).  The conflict rule is unchanged within the archives
selected.
"""

from __future__ import annotations

import dataclasses
import datetime as _dt
import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from ..core import framework
from ..core import pool as pool_mod
from ..core import records as records_mod
from ..core import run_layout
from ..core.config import Campaign

#: The record the step writes into the destination folder.
COPY_RECORD = "archived_records_copied.json"

#: The record of the freeze that made the reproduction gate's archive in a run
#: ID's folder from its own shared pool (:func:`freeze_reproduction_records`).
FREEZE_RECORD = Path("gates") / "reproduction" / "pool_records_frozen.json"


@dataclass(frozen=True)
class Archive:
    """One gate's read-only records: where they are and why they are never re-made."""

    gate: str
    what: str
    why_read_only: str
    #: Glob patterns relative to the run ID's folder: files, or directories
    #: copied whole.
    paths: tuple[str, ...] = ()
    #: The gate's pool records, as its own job set composed under a campaign
    #: (the campaign it composes them under, and the jobs).
    jobs: Callable[[Campaign], tuple[Campaign, list[pool_mod.Job]]] | None = None


def _reproduction_jobs(campaign: Campaign) -> tuple[Campaign, list[pool_mod.Job]]:
    from . import reproduction as reproduction_mod  # noqa: PLC0415

    return campaign, reproduction_mod.jobs_read(campaign)


def _count_neutrality_jobs(campaign: Campaign) -> tuple[Campaign, list[pool_mod.Job]]:
    """GC's references and **both** labelled sides, composed as its body
    composes them: under the declared straddle test set."""
    from . import gate_count_neutrality as gc_mod  # noqa: PLC0415
    from . import gates as gates_mod  # noqa: PLC0415

    declared = gc_mod.STRADDLE_TEST_SET.get(gc_mod.STRADDLE[1])
    composed = (
        dataclasses.replace(campaign, test_set=declared, tau=None)
        if declared is not None and campaign.test_set != declared
        else campaign
    )
    references = gates_mod.entry_references_from_records(composed)
    jobs = list(gates_mod.entry_reference_jobs(composed))
    for label in dict.fromkeys(gc_mod.STRADDLE):
        jobs += [job for *_rest, job in gc_mod.count_neutrality_jobs(composed, references, label)]
    return composed, jobs


#: The declared archives, in the order they are copied.
ARCHIVES: tuple[Archive, ...] = (
    Archive(
        gate="reproduction",
        what="GR's verdict at the copy commit and its teeth record; its read-only archive of the records of its job set (references, the twenty planned runs, the substitutes, the composition tooth's run) and the record of the freeze that made it",
        why_read_only="registry.RUN_ONCE: pressed once at d6c246a1 and read under --resume, never re-made; tally_contracts reproduces V4's published cells on its twenty runs, read from the archive (I-41, A112); pool.run refuses any job resolving into it",
        # Not the whole gate folder: its gate.json is rewritten by every read,
        # so a copy of one archive into a run ID that holds the others would
        # refuse on it (A110).  The verdict the read takes is verdict_at_*.
        paths=(
            "gates/reproduction/verdict_at_*.json",
            "gates/reproduction/_teeth",
            "gates/reproduction/pool_records",
            "gates/reproduction/pool_records_frozen.json",
        ),
        jobs=_reproduction_jobs,
    ),
    Archive(
        gate="count_neutrality",
        what="GC's straddle records, one per driver change, and the pool records of its references and both labelled sides",
        why_read_only="each side is made at the commit of its label and never re-made; its test set is GC's declared straddle set whatever the campaign, so the same jobs under every run ID; G2 part (ii) reads the DR9 -> DR10 straddle",
        paths=("gates/count_neutrality/straddles",),
        jobs=_count_neutrality_jobs,
    ),
    Archive(
        gate="switch_neutrality",
        what="G1's before capture and its archived straddles (each pair of captures at the two commits of a driver change)",
        why_read_only="the before side is taken at the commit before the change and is never re-taken (harness plan amendment 13, rule (ii))",
        paths=("gates/switch_neutrality/before", "gates/switch_neutrality/straddles"),
    ),
    Archive(
        gate="evaluation_warmup",
        what=(
            "the gate's verdict at c2295511 and its manifest, archived by its first read, and both sides "
            "the verdict compared: the cold evaluation child's records of the gate job set's evaluation "
            "half and the warmed child's at ff9e73a2, all under the default settings"
        ),
        why_read_only=(
            "D44: the verdict is given once, at the commit that introduced the warmed child, and read "
            "under every run ID; A101's cold child is gone from the tree, so its side cannot be made again"
        ),
        paths=(
            "gates/evaluation_warmup/before",
            "gates/evaluation_warmup/after",
            "gates/evaluation_warmup/verdict_at_*.json",
            "gates/evaluation_warmup/archive_manifest.json",
        ),
    ),
    Archive(
        gate="artifacts_derive_inputs",
        what="the derived (lifted) input files of the pulsed configurations",
        why_read_only="their bytes are gated on the committed digest, so they are the same file under every setting; the lifted arms read them",
        paths=("input_files/*/*_lifted.IN.DAT",),
    ),
)


class ArchiveError(framework.GateError):
    """The copy was refused; nothing was copied."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _files_under(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(p for p in path.rglob("*") if p.is_file())


def selected(only: Sequence[str] | None) -> tuple[Archive, ...]:
    """The declared archives, or those of the gates *only* names; refuses a name no archive has."""
    if not only:
        return ARCHIVES
    unknown = sorted(set(only) - {archive.gate for archive in ARCHIVES})
    if unknown:
        raise ArchiveError(f"no archive is declared for {unknown}; the archives are {[a.gate for a in ARCHIVES]}")
    return tuple(archive for archive in ARCHIVES if archive.gate in set(only))


def plan(source: Campaign, destination: Campaign, *, only: Sequence[str] | None = None) -> dict[str, Any]:
    """What the copy would do, archive by archive, reading the source only."""
    if source.run_id is None or destination.run_id is None:
        raise ArchiveError("both campaigns must be run IDs' campaigns")
    if source.run_id == destination.run_id:
        raise ArchiveError(f"the source and the destination are the same run ID {source.run_id!r}")
    source_dir, destination_dir = Path(source.runs_dir), Path(destination.runs_dir)
    if run_layout.read_settings(source_dir) is None:
        raise ArchiveError(f"runs/{source.run_id}/ is not a run ID's folder (no {run_layout.SETTINGS_FILE})")
    rows: list[dict[str, Any]] = []
    files: dict[str, Path] = {}
    for archive in selected(only):
        row: dict[str, Any] = {
            "gate": archive.gate,
            "what": archive.what,
            "why_read_only": archive.why_read_only,
            "paths": [],
            "pool_records": [],
            "absent_at_source": [],
        }
        for pattern in archive.paths:
            matches = sorted(source_dir.glob(pattern))
            if not matches:
                row["absent_at_source"].append(pattern)
            for match in matches:
                found = _files_under(match)
                row["paths"].append({"path": match.relative_to(source_dir).as_posix(), "n_files": len(found)})
                for path in found:
                    files.setdefault(path.relative_to(source_dir).as_posix(), path)
        if archive.jobs is not None:
            composed, jobs = archive.jobs(source)
            for directory in pool_mod.directories_for(jobs, composed):
                relative = Path(directory).resolve().relative_to(source_dir.resolve()).as_posix()
                if not (Path(directory) / "metrics.json").exists():
                    row["absent_at_source"].append(relative)
                    continue
                found = _files_under(Path(directory))
                row["pool_records"].append({"path": relative, "n_files": len(found)})
                for path in found:
                    files.setdefault(path.relative_to(source_dir).as_posix(), path)
        rows.append(row)
    present = {rel: (destination_dir / rel) for rel in files if (destination_dir / rel).exists()}
    return {
        "source": source.run_id,
        "destination": destination.run_id,
        "archives": rows,
        "n_files": len(files),
        "n_bytes": sum(p.stat().st_size for p in files.values()),
        "n_already_present": len(present),
        "only": list(only) if only else None,
        "files": files,
    }


def copy(source: Campaign, destination: Campaign, *, apply: bool, only: Sequence[str] | None = None) -> dict[str, Any]:
    """The copy: a listing unless *apply*; refuses before copying anything
    where a file is already in the destination with other bytes.  With
    *only*, the archives of those gates alone, and the record of the copy is
    written under its own name so the whole copy's record is left as made."""
    block = plan(source, destination, only=only)
    block["applied"] = False
    if not apply:
        return block
    destination_dir = Path(destination.runs_dir)
    conflicts = [
        rel
        for rel, path in block["files"].items()
        if (destination_dir / rel).exists() and _sha256(destination_dir / rel) != _sha256(path)
    ]
    if conflicts:
        raise ArchiveError(
            f"{len(conflicts)} file(s) are already in runs/{destination.run_id}/ with other "
            f"bytes than runs/{source.run_id}/'s (first: {conflicts[:3]}); nothing was copied"
        )
    copied: list[dict[str, Any]] = []
    skipped = 0
    for rel, path in block["files"].items():
        target = destination_dir / rel
        source_sha = _sha256(path)
        if target.exists():
            skipped += 1
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        copied_sha = _sha256(target)
        if copied_sha != source_sha:
            raise ArchiveError(f"{rel}: the copy's SHA-256 {copied_sha[:16]} is not the source's {source_sha[:16]}")
        copied.append({"path": rel, "bytes": target.stat().st_size, "sha256": source_sha})
    record = {
        "what_this_is": (
            "the read-only records copied into this run ID's folder from another's "
            "(harness/gates/archived_records.py): every file's path, size and SHA-256, "
            "the same as the source's after the copy"
        ),
        "source_run_id": source.run_id,
        "destination_run_id": destination.run_id,
        "generated": _dt.datetime.now().isoformat(timespec="seconds"),
        "tree_git_head": framework.git_head(),
        "run": run_layout.stamp(destination),
        "archives": block["archives"],
        "only": list(only) if only else None,
        "n_copied": len(copied),
        "n_already_present_with_the_same_bytes": skipped,
        "copied": copied,
    }
    out = destination_dir / (
        COPY_RECORD if not only else COPY_RECORD.replace(".json", "_" + "_".join(sorted(only)) + ".json")
    )
    if copied or not out.exists():
        # A repeated copy that found every file already there leaves the
        # record of the copy that made them.
        out.write_text(json.dumps(record, indent=2) + "\n")
    block.update(applied=True, n_copied=len(copied), n_skipped_same_bytes=skipped, record=str(out))
    return block


def resolution(campaign: Campaign, *, only: Sequence[str] | None = None) -> list[dict[str, Any]]:
    """The archives' job sets composed **under** *campaign*: per job, the
    directory the pool resolves it to (relative to the run ID's folder) and
    the resume decision there.  Run on the source and on the destination,
    the two must agree job for job — the same relative directory, the same
    decision — which is the proof that the copies are the records the
    destination's presses read, and are read as the source's are."""
    rows = []
    for archive in selected(only):
        if archive.jobs is None:
            continue
        try:
            composed, jobs = archive.jobs(campaign)
            listing = pool_mod.job_listing(jobs, composed)
        except Exception as exc:  # noqa: BLE001 - a refusal is the row
            rows.append({"gate": archive.gate, "refused": f"{type(exc).__name__}: {exc}"})
            continue
        base = Path(campaign.runs_dir).resolve()
        rows.append(
            {
                "gate": archive.gate,
                "n_jobs": len(listing),
                "n_kept": sum(1 for r in listing if r["why_not_complete"] is None),
                "jobs": {
                    r["job_digest"]: {
                        "key": r["key"],
                        "path": framework._relative(Path(r["path"]), base),
                        "why_not_kept": r["why_not_complete"],
                    }
                    for r in listing
                },
            }
        )
    return rows


def agreement(source_rows: Sequence[Mapping[str, Any]], destination_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Job for job, do the destination's resolutions equal the source's?"""
    by_gate = {row["gate"]: row for row in source_rows}
    out = []
    for row in destination_rows:
        source = by_gate.get(row["gate"]) or {}
        mine, theirs = row.get("jobs") or {}, source.get("jobs") or {}
        differing = sorted(d for d in set(mine) | set(theirs) if mine.get(d) != theirs.get(d))
        out.append(
            {
                "gate": row["gate"],
                "n_jobs": row.get("n_jobs"),
                "n_kept": row.get("n_kept"),
                "source_n_jobs": source.get("n_jobs"),
                "source_n_kept": source.get("n_kept"),
                "n_differing": len(differing),
                "differing": [(mine.get(d) or theirs.get(d) or {}).get("key") for d in differing[:5]],
                "refused": row.get("refused") or source.get("refused"),
            }
        )
    return {"gates": out, "agree": all(r["n_differing"] == 0 and not r["refused"] for r in out)}


def report(block: Mapping[str, Any], resolved: Mapping[str, Any] | None = None) -> list[str]:
    lines = [
        f"  from runs/{block['source']}/ into runs/{block['destination']}/: "
        f"{block['n_files']} file(s), {block['n_bytes'] / 1e6:.1f} MB; "
        f"{block['n_already_present']} already present"
    ]
    for row in block["archives"]:
        lines.append(f"  {row['gate']}: {row['what']}")
        lines.append(f"    read-only because {row['why_read_only']}")
        for entry in row["paths"]:
            lines.append(f"    {entry['path']}  ({entry['n_files']} file(s))")
        if row["pool_records"]:
            lines.append(f"    {len(row['pool_records'])} pool record(s), {sum(e['n_files'] for e in row['pool_records'])} file(s)")
        for absent in row["absent_at_source"]:
            lines.append(f"    ABSENT at the source: {absent}")
    if block.get("applied"):
        lines.append(f"  copied {block['n_copied']} file(s); {block['n_skipped_same_bytes']} already present with the same bytes; record {block['record']}")
    else:
        lines.append("  dry run: nothing copied (--apply copies)")
    if block.get("only"):
        lines.append(f"  only the archive(s) of {block['only']} (--archive)")
    if resolved is not None:
        for row in resolved["gates"]:
            if row["refused"]:
                lines.append(f"  {row['gate']}'s job set: not composable — {row['refused']}")
                continue
            lines.append(
                f"  {row['gate']}'s job set: under runs/{block['destination']}/ {row['n_jobs']} job(s), "
                f"--resume keeps {row['n_kept']}; under runs/{block['source']}/ {row['source_n_jobs']} "
                f"job(s), keeps {row['source_n_kept']}; jobs resolving or deciding differently: {row['n_differing']}"
                + (f" (first: {row['differing']})" if row["differing"] else "")
            )
        lines.append(
            "  the destination's job sets resolve to the copies exactly as the source's to the originals: "
            + ("YES" if resolved["agree"] else "NO")
        )
    return lines


# --------------------------------------------------------------------------
# the reproduction gate's archive, frozen from a run ID's own pool (I-41)
# --------------------------------------------------------------------------


def _settings_are_v4s(campaign: Campaign) -> bool:
    """Whether *campaign*'s settings are V4's own -- the reproduction gate's
    criterion -- so that its campaign composition renders GR's identities."""
    from ..core.config import TAU_BY_TEST_SET, V4_TEST_SET  # noqa: PLC0415

    return (
        campaign.test_set == V4_TEST_SET
        and campaign.tau_rule is None
        and all(float(campaign.tau_for(c)) == float(TAU_BY_TEST_SET[V4_TEST_SET]) for c in campaign.configurations)
    )


def freeze_reproduction_records(campaign: Campaign, *, apply: bool) -> dict[str, Any]:
    """Make the reproduction gate's read-only archive from this run ID's own
    shared pool: a listing unless *apply* (issue I-41; task A112
    (v5-reproduction-records-read-only)).

    GR's job set is composed as before A112 -- every job resolved by the pool
    (``reproduction.jobs_read(from_the_pool=True)``) -- and every record found
    is copied, file by file with its modification time, into the archive
    directory GR's readers now name (``reproduction.archived_directory_for``:
    the pool's canonical name under ``gates/reproduction/pool_records/``); each
    file's SHA-256 is compared after the copy.  Nothing in the pool is moved,
    removed or written: the pool keeps its records, which are the records of
    whichever gate composes those identities.

    **Refused under a run ID whose settings are V4's own** (the whole write set
    at 1e-6): there the campaign's composition renders GR's identities, so the
    pool's records of them are other gates' too and may have been re-made by
    today's driver -- which is I-41.  Such a run ID takes the archive from
    another by ``--copy-archived-records <run ID> --archive reproduction``.
    Refused, before anything is copied, where a file is already in the archive
    with other bytes.
    """
    from . import reproduction as reproduction_mod  # noqa: PLC0415

    if _settings_are_v4s(campaign):
        raise ArchiveError(
            f"runs/{campaign.run_id}/'s settings are V4's own: its campaign composition renders the "
            f"reproduction gate's job identities, so the shared pool's records of them are other gates' "
            f"too and may have been re-made by today's driver (issue I-41).  Copy the archive from a run "
            f"ID whose settings differ: --copy-archived-records <run ID> --archive reproduction"
        )
    runs_dir = Path(campaign.runs_dir)
    pool_mod.forget_record_index()
    pool_jobs = reproduction_mod.jobs_read(campaign, from_the_pool=True)
    rows: list[dict[str, Any]] = []
    files: list[tuple[Path, Path]] = []
    seen: set[str] = set()
    for job in pool_jobs:
        digest = pool_mod.digest_for(job, campaign)
        if digest in seen:
            continue
        seen.add(digest)
        source = pool_mod.directory_for(job, campaign)
        target = reproduction_mod.archived_directory_for(job, campaign)
        row: dict[str, Any] = {
            "key": job.key,
            "job_digest": digest,
            "source": framework._relative(source, runs_dir),
            "archive": framework._relative(target, runs_dir),
        }
        if not (source / "metrics.json").exists():
            row["absent"] = True
            rows.append(row)
            continue
        record = json.loads((source / "metrics.json").read_text())
        row.update(
            tree_git_head=record.get("tree_git_head"),
            stamped_digest=record.get("job_digest"),
            n_files=len(_files_under(source)),
        )
        if record.get("job_digest") != digest:
            raise ArchiveError(
                f"{job.key}: the record the pool resolves to ({row['source']}) is stamped with digest "
                f"{str(record.get('job_digest'))[:16]}, not the job's {digest[:16]}; refused rather than archived"
            )
        rows.append(row)
        for path in _files_under(source):
            files.append((path, target / path.relative_to(source)))
    conflicts = [str(t) for s, t in files if t.exists() and _sha256(t) != _sha256(s)]
    block: dict[str, Any] = {
        "run_id": campaign.run_id,
        "n_jobs": len(rows),
        "n_records": sum(1 for r in rows if not r.get("absent")),
        "n_absent": sum(1 for r in rows if r.get("absent")),
        "n_files": len(files),
        "n_bytes": sum(s.stat().st_size for s, _t in files),
        "n_already_present": sum(1 for _s, t in files if t.exists()),
        "rows": rows,
        "applied": False,
    }
    if conflicts:
        raise ArchiveError(
            f"{len(conflicts)} file(s) are already in the archive with other bytes (first: {conflicts[:3]}); nothing was copied"
        )
    if not apply:
        return block
    copied = 0
    manifest: list[dict[str, Any]] = []
    for source, target in files:
        sha = _sha256(source)
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            copied += 1
        if _sha256(target) != sha:
            raise ArchiveError(f"{target}: the copy's SHA-256 is not the source's")
        manifest.append({"path": framework._relative(target, runs_dir), "bytes": target.stat().st_size, "sha256": sha})
    record = {
        "what_this_is": (
            "the reproduction gate's read-only archive, frozen from this run ID's own shared pool "
            "(harness/gates/archived_records.freeze_reproduction_records; issue I-41, task A112): per job "
            "the pool directory it was copied from, the archive directory GR's readers name, the record's "
            "stamp; every archived file's SHA-256, the same as the pool's after the copy.  The pool was not written."
        ),
        "run_id": campaign.run_id,
        "generated": _dt.datetime.now().isoformat(timespec="seconds"),
        "tree_git_head": framework.git_head(),
        "run": run_layout.stamp(campaign),
        "jobs": rows,
        "files": manifest,
    }
    out = runs_dir / FREEZE_RECORD
    if copied or not out.exists():
        out.write_text(json.dumps(record, indent=2) + "\n")
    block.update(applied=True, n_copied=copied, record=str(out))
    pool_mod.forget_record_index()
    return block


def freeze_report(block: Mapping[str, Any]) -> list[str]:
    lines = [
        f"  runs/{block['run_id']}/: the reproduction gate's job set, {block['n_jobs']} job(s): "
        f"{block['n_records']} record(s) in the shared pool, {block['n_absent']} with none; "
        f"{block['n_files']} file(s), {block['n_bytes'] / 1e6:.1f} MB; {block['n_already_present']} already in the archive"
    ]
    for row in block["rows"]:
        if row.get("absent"):
            lines.append(f"    {row['key']}: no record in the pool ({row['source']}); nothing archived")
        else:
            lines.append(f"    {row['key']}: {row['source']} -> {row['archive']} (stamped {str(row['tree_git_head'])[:8]}, {row['n_files']} file(s))")
    if block.get("applied"):
        lines.append(f"  copied {block['n_copied']} file(s); record {block['record']}")
    else:
        lines.append("  dry run: nothing copied (--apply copies)")
    return lines


# --------------------------------------------------------------------------
# which other gates' jobs carry an archived record's identity (I-41's class)
# --------------------------------------------------------------------------


def _archived_directories(campaign: Campaign, archive: Archive) -> tuple[set[Path], str | None]:
    runs_dir = Path(campaign.runs_dir)
    found: set[Path] = set()
    for pattern in archive.paths:
        for match in sorted(runs_dir.glob(pattern)):
            for path in _files_under(match):
                if path.name == "metrics.json":
                    found.add(path.parent.resolve())
    refused = None
    if archive.jobs is not None:
        try:
            composed, jobs = archive.jobs(campaign)
            for directory in pool_mod.directories_for(jobs, composed):
                if (Path(directory) / "metrics.json").exists():
                    found.add(Path(directory).resolve())
        except Exception as exc:  # noqa: BLE001 - a refusal is the row
            refused = f"{type(exc).__name__}: {str(exc).splitlines()[0][:200]}"
    return found, refused


def collisions(campaign: Campaign) -> dict[str, Any]:
    """Per declared archive: which **other** gates' jobs carry the identity of
    one of its records, and whether each resolves **into** the archived
    directory (so that a press of that gate keeps -- or re-makes -- the
    archive's record as its own: I-41's class) or elsewhere.

    The archived records are every ``metrics.json`` under the archive's paths
    and its job set's directories; the other jobs are every registered gate's
    ``jobs`` declaration composed under *campaign* (what ``--jobs all``
    composes).  Read-only: nothing runs, nothing is written.  Campaign, smoke,
    timing and supplementary jobs cannot carry a gate record's identity: the
    run kind is an identity field, and the survey counts the archived records'
    run kinds to show they are all ``gate``.
    """
    from . import registry as registry_mod  # noqa: PLC0415

    pool_mod.forget_record_index()
    gates = registry_mod.gates_only(campaign)
    rows_by_gate: dict[str, list[Mapping[str, Any]]] = {}
    not_composable: dict[str, str] = {}
    for name, gate in gates.items():
        if gate.jobs is None:
            continue
        try:
            rows_by_gate[name] = list(gate.jobs())
        except Exception as exc:  # noqa: BLE001 - a gate not composable is stated
            not_composable[name] = f"{type(exc).__name__}: {str(exc).splitlines()[0][:160]}"
    out: list[dict[str, Any]] = []
    for archive in ARCHIVES:
        directories, refused = _archived_directories(campaign, archive)
        digests: dict[str, set[Path]] = {}
        run_kinds: dict[str, int] = {}
        for directory in directories:
            record = records_mod.read(directory)
            digest = record.get("job_digest")
            if isinstance(digest, str):
                digests.setdefault(digest, set()).add(directory)
            kind = str(record.get("campaign_run_kind"))
            run_kinds[kind] = run_kinds.get(kind, 0) + 1
        protected = all(pool_mod.read_only_archive_of(d, campaign) is not None for d in directories) if directories else False
        hits: list[dict[str, Any]] = []
        for name, rows in rows_by_gate.items():
            if name == archive.gate:
                continue
            for row in rows:
                if row["job_digest"] not in digests:
                    continue
                resolved = Path(row["path"]).resolve()
                hits.append(
                    {
                        "gate": name,
                        "makes_runs": bool(gates[name].needs_runs),
                        "key": row["key"],
                        "job_digest": row["job_digest"],
                        "into_the_archive": resolved in digests[row["job_digest"]],
                        "path": framework._relative(resolved, Path(campaign.runs_dir)),
                    }
                )
        out.append(
            {
                "archive": archive.gate,
                "n_records": len(directories),
                "n_digests": len(digests),
                "run_kinds": run_kinds,
                "refused": refused,
                "protected_by_the_pool": protected,
                "n_other_jobs_sharing_an_identity": len(hits),
                "n_into_the_archive": sum(1 for h in hits if h["into_the_archive"]),
                "n_into_the_archive_by_a_gate_that_makes_runs": sum(
                    1 for h in hits if h["into_the_archive"] and h["makes_runs"]
                ),
                "hits": hits,
            }
        )
    return {"run_id": campaign.run_id, "archives": out, "gates_not_composable": not_composable}


def collisions_report(block: Mapping[str, Any]) -> list[str]:
    lines = [f"  runs/{block['run_id']}/"]
    for row in block["archives"]:
        lines.append(
            f"  {row['archive']}: {row['n_records']} archived record(s), {row['n_digests']} identit(y/ies), "
            f"run kinds {row['run_kinds']}; protected by pool.run: {'yes' if row['protected_by_the_pool'] else 'no'}"
            + (f"; job set not composable: {row['refused']}" if row["refused"] else "")
        )
        lines.append(
            f"    other gates' jobs carrying an archived identity: {row['n_other_jobs_sharing_an_identity']}; "
            f"resolving into the archived directory: {row['n_into_the_archive']} "
            f"({row['n_into_the_archive_by_a_gate_that_makes_runs']} of them by a gate that makes runs)"
        )
        by: dict[tuple[str, bool], list[str]] = {}
        for hit in row["hits"]:
            by.setdefault((hit["gate"], hit["into_the_archive"]), []).append(hit["key"])
        for (gate, into), keys in sorted(by.items()):
            lines.append(
                f"      {gate}{' (makes runs)' if any(h['makes_runs'] for h in row['hits'] if h['gate'] == gate) else ''}: "
                f"{len(keys)} job(s) {'INTO the archive' if into else 'resolved elsewhere'}: {', '.join(keys[:4])}"
                + (" …" if len(keys) > 4 else "")
            )
    for name, why in sorted(block["gates_not_composable"].items()):
        lines.append(f"  gate {name}'s jobs not composable: {why}")
    return lines
