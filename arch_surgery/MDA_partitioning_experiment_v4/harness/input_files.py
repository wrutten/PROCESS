"""The lifted input file: where it comes from, and how it is checked.

A **configuration** is one optimisation problem and its **input file** is the
file that problem is read from.  Two arms read a *lifted* input file — one in
which the burn time has become an optimiser variable — and that file is
**derived** from the committed one by an edit of exactly three lines: the burn
time becomes iteration variable 178, its consistency residual becomes equality
constraint 93 inserted inside the input file's equality block with the count
raised in the same edit, and the variable's initial value is set to the burn
time the incumbent's own loop settles on at the configuration's starting design
vector.

**The derivation itself is task A51 (harness-artifacts)'s** — it needs a
PROCESS run to measure that settled burn time, and it is a committed stage of
the runner.  This module is the half the run path needs first: *resolve the
file, and refuse anything that is not the one the experiment declares*.

Why the run path needs it before the derivation exists.  Gate GR — the check
that rewriting the harness did not move the measurement — runs the two lifted
arms, and it must run them on **the same bytes the previous revision ran**.
Deriving the file afresh would put a second variable into a comparison whose
whole argument is that only the harness changed.  So the two digests below are
committed as data, the file is staged from a named directory, and a byte that
does not match is a refusal.  When A51's derivation lands, its gate is exactly
these two digests, which is what that task's queue row already asks for.

Derived from ``arch_surgery/idf_probe/a25_variant_deck.py`` and
``arch_surgery/MDA_partitioning_experiment_v3/v3_runner.py::deck_for``, read at
``9a8defa6``; task **A50 (harness-run)**.
"""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from typing import Any, Mapping

from .config import Campaign, Config


class InputFileError(RuntimeError):
    """A refusal to run on an input file the experiment does not declare."""


#: sha256 of each configuration's lifted input file.  Measured, not chosen: the
#: three revisions that have derived it — the two earlier experiment revisions
#: and the task that first built the derivation — produced byte-identical files,
#: read from the main checkout on 2026-09-10 at all three paths.  A steady-state
#: configuration has no lifted input file and is absent from this map, which is
#: what makes asking for one a refusal rather than a missing file.
LIFTED_INPUT_SHA256: dict[str, str] = {
    "large_tokamak_nof":
        "8902a6a58bb3ce07223fbc774b84c4cc7082b95d6c40b5b0c88d7c99fe6f4aab",
    "low_aspect_ratio_DEMO":
        "189c5e1e99c21f1f6a35d471380923d7d26f43cbf84ca2063c6efcf072dd0aaa",
}

#: Where the digests came from, quoted in the record so a reader does not have
#: to take them on trust.
LIFTED_INPUT_PROVENANCE = {
    "what": (
        "the lifted input file derived from the committed one by the "
        "three-line edit described in this module's docstring"
    ),
    "measured_from": [
        "arch_surgery/MDA_partitioning_experiment_v3/runs/_decks/<name>/<name>_lifted.IN.DAT",
        "arch_surgery/MDA_partitioning_experiment_v2/runs/_decks/<name>/<name>_lifted.IN.DAT",
        "arch_surgery/idf_probe/runs/a28/_decks/<name>/<name>_lifted.IN.DAT",
    ],
    "read_on": "2026-09-10, in the main checkout; all three byte-identical",
    "derivation_owner": "task A51 (harness-artifacts); its gate is these digests",
}


def sha256_of(path: Path) -> str:
    """The sha256 of a file's bytes."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def is_lifted_available(config: Config, campaign: Campaign) -> bool:
    """Whether the lifted input file this configuration needs is in place."""
    if not config.pulsed:
        return True
    return lifted_path(config, campaign).exists()


def lifted_path(config: Config, campaign: Campaign) -> Path:
    """Where the lifted input file lives once it has been produced."""
    return (
        Path(campaign.derived_input_dir)
        / config.name
        / f"{config.name}_lifted.IN.DAT"
    )


def assert_lifted(config: Config, campaign: Campaign) -> dict[str, Any]:
    """Refuse unless the lifted input file is present and is the declared one.

    Returns its identity for the record: an input file a run record does not
    name by digest is an input file nobody can check afterwards.
    """
    if not config.pulsed:
        raise InputFileError(
            f"{config.name} is a steady-state configuration: there is no "
            f"burn-time coupling, so no arm reads a lifted input file and none "
            f"is derived for it"
        )
    expected = LIFTED_INPUT_SHA256.get(config.name)
    if expected is None:
        raise InputFileError(
            f"no digest is recorded for {config.name}'s lifted input file; the "
            f"digests are {sorted(LIFTED_INPUT_SHA256)}.  A file nobody has "
            f"recorded is not staged on trust."
        )
    path = lifted_path(config, campaign)
    if not path.exists():
        raise InputFileError(
            f"the lifted input file for {config.name} is not at {path}.  It is "
            f"derived by the input-file stage (task A51 (harness-artifacts)); "
            f"until that exists, stage it from a directory holding the "
            f"previous revision's derived files — the runner's "
            f"--lifted-from option — which checks the bytes against the "
            f"recorded digest {expected[:12]}…"
        )
    found = sha256_of(path)
    if found != expected:
        raise InputFileError(
            f"the lifted input file for {config.name} at {path} is not the one "
            f"this experiment declares: sha256 {found} against {expected} "
            f"recorded.  Refused: an arm run on a different problem is not "
            f"that arm."
        )
    return {
        "path": str(path),
        "sha256": found,
        "kind": "lifted",
        "provenance": LIFTED_INPUT_PROVENANCE,
    }


def stage_lifted(
    config: Config, campaign: Campaign, source_dir: Path
) -> dict[str, Any]:
    """Put a previously derived lifted input file where the run path expects it.

    *source_dir* is a directory holding ``<name>/<name>_lifted.IN.DAT``.  The
    bytes are checked against the recorded digest **before** the copy, so a
    wrong file is refused rather than staged and then found.
    """
    if not config.pulsed:
        return {"skipped": f"{config.name} is steady state: no lifted input file"}
    expected = LIFTED_INPUT_SHA256[config.name]
    source = Path(source_dir) / config.name / f"{config.name}_lifted.IN.DAT"
    if not source.exists():
        raise InputFileError(
            f"no lifted input file for {config.name} under {source_dir}: "
            f"{source} does not exist"
        )
    found = sha256_of(source)
    if found != expected:
        raise InputFileError(
            f"{source} is not {config.name}'s lifted input file: sha256 "
            f"{found} against {expected} recorded"
        )
    destination = lifted_path(config, campaign)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    return {
        "configuration": config.name,
        "source": str(source),
        "destination": str(destination),
        "sha256": found,
        "matched_recorded_digest": True,
    }


def identity(path: Path, *, kind: str) -> Mapping[str, Any]:
    """What a record says about the input file it ran."""
    return {"path": str(path), "sha256": sha256_of(path), "kind": kind}
