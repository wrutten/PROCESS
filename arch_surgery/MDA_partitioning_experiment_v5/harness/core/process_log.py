"""PROCESS's own log in a run folder: one file, gzip-compressed.

Task **A108 (v5-one-compressed-log)**.  PROCESS writes its log twice into
every run folder, and both copies come from PROCESS's ``process/main.py``,
not from the harness:

* ``process.log`` — the module-level ``logging.FileHandler("process.log",
  mode="a")``, opened relative to the working directory when ``process.main``
  is imported; the pool starts every child with the run folder as its
  working directory;
* ``<configuration>.process.log`` — the handler ``setup_loggers`` adds in
  ``SingleRun.initialise``, at the output prefix (``OUT.DAT`` replaced by
  ``process.log``), ``mode="w"``.

Both handlers carry the same level and formatter and are attached to the same
logger, so the two files are byte-identical whenever nothing is logged
between the import and ``initialise`` (task A108's report counts the
folders on disk that held the pair and how many pairs were identical).
Avoiding the second file would mean changing PROCESS's logging
set-up — a driver change — so the harness does not: the pool's close-out
(:func:`close_out`, called by ``pool.run`` after the record is assembled)
**verifies** the two are identical, writes ``process.log.gz`` from one,
verifies the round trip, and only then removes the plain files.  A pair that
differs is left as it is and said so: nothing is removed whose content the
kept file does not hold.

The forms a run folder may carry (:data:`FORMS`), all of them valid for a
complete record — the log is diagnostic text and no field of the record is
derived from it:

``compressed``
    one ``process.log.gz`` (every run made since this task);
``plain pair``
    ``process.log`` and ``<configuration>.process.log`` (every run made before
    it, until compacted by ``experiment_runner.py --compact-run-logs``);
``plain single``
    one of the two plain files (a run that ended before ``initialise``);
``none``
    no log (a run that never imported PROCESS).

:func:`open_text` is the one reader and reads every form.  The record's
``metrics.json`` is not touched by the close-out or the compaction, so a
record's job identity, digest and completeness — and with them the
``--resume`` decision (``pool.why_not_kept``) — are what they were.

The compressed file is deterministic: gzip level 6, no file name and a zero
time in its header, so the same log always compresses to the same bytes.
"""

from __future__ import annotations

import gzip
import hashlib
import io
import os
from pathlib import Path
from typing import IO, Any, Iterable

#: The plain log PROCESS's module-level handler writes into the working directory.
PLAIN_NAME = "process.log"

#: The suffix of the plain log PROCESS's ``setup_loggers`` writes at the output prefix.
PREFIXED_SUFFIX = ".process.log"

#: The one log a run folder keeps.
COMPRESSED_NAME = "process.log.gz"

#: The compressed file while it is being written; never a finished file.  An
#: interrupted compaction leaves at most this, which the next one removes.
PARTIAL_NAME = COMPRESSED_NAME + ".partial"

#: gzip level: ``gzip -6``, the command-line default.
LEVEL = 6

#: The forms of the log a run folder may carry, in the order a reader prefers them.
FORMS: tuple[str, ...] = ("compressed", "plain pair", "plain single", "none")

_BLOCK = 1 << 20


def plain_logs(directory: Path) -> list[Path]:
    """The plain PROCESS logs in *directory*: ``process.log`` first, then
    every ``<prefix>.process.log``."""
    directory = Path(directory)
    found = []
    if (directory / PLAIN_NAME).is_file():
        found.append(directory / PLAIN_NAME)
    found.extend(
        sorted(p for p in directory.glob("*" + PREFIXED_SUFFIX) if p.is_file() and p.name != PLAIN_NAME)
    )
    return found


def form_of(directory: Path) -> str:
    """Which of :data:`FORMS` *directory* carries.  A folder holding the
    compressed file and a plain one is a compaction not finished; it reads
    ``compressed`` (the compressed file is only ever renamed into place
    complete) and the next compaction finishes it."""
    directory = Path(directory)
    if (directory / COMPRESSED_NAME).is_file():
        return "compressed"
    plain = plain_logs(directory)
    if len(plain) >= 2:
        return "plain pair"
    if len(plain) == 1:
        return "plain single"
    return "none"


def open_text(directory: Path) -> IO[str] | None:
    """PROCESS's log of the run in *directory*, as text, in whichever form the
    folder carries it; None when it carries none.  The caller closes it."""
    directory = Path(directory)
    if (directory / COMPRESSED_NAME).is_file():
        return gzip.open(directory / COMPRESSED_NAME, "rt", encoding="utf-8", errors="replace")
    plain = plain_logs(directory)
    if plain:
        return open(plain[0], encoding="utf-8", errors="replace")
    return None


def _sha256_of_stream(stream: IO[bytes]) -> tuple[str, int]:
    digest = hashlib.sha256()
    n = 0
    for block in iter(lambda: stream.read(_BLOCK), b""):
        digest.update(block)
        n += len(block)
    return digest.hexdigest(), n


def sha256_of(path: Path) -> tuple[str, int]:
    """SHA-256 and length of a file's bytes."""
    with open(path, "rb") as handle:
        return _sha256_of_stream(handle)


def sha256_decompressed(path: Path) -> tuple[str, int]:
    """SHA-256 and length of what a gzip file decompresses to."""
    with gzip.open(path, "rb") as handle:
        return _sha256_of_stream(handle)


def compressed_size(path: Path) -> int:
    """The size *path* compresses to under :func:`_write_compressed`, measured
    by compressing into nothing: no byte is written to disk."""
    sink = _CountingSink()
    with gzip.GzipFile(filename="", mode="wb", fileobj=sink, compresslevel=LEVEL, mtime=0) as out:
        with open(path, "rb") as handle:
            for block in iter(lambda: handle.read(_BLOCK), b""):
                out.write(block)
    return sink.n


class _CountingSink(io.RawIOBase):
    def __init__(self) -> None:
        self.n = 0

    def writable(self) -> bool:
        return True

    def write(self, b) -> int:  # noqa: ANN001
        self.n += len(b)
        return len(b)


def _write_compressed(source: Path, destination: Path) -> None:
    with open(destination, "wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, compresslevel=LEVEL, mtime=0) as out:
            with open(source, "rb") as handle:
                for block in iter(lambda: handle.read(_BLOCK), b""):
                    out.write(block)
        raw.flush()
        os.fsync(raw.fileno())


def _bytes(paths: Iterable[Path]) -> int:
    return sum(p.stat().st_size for p in paths if p.exists())


def compact(directory: Path, *, apply: bool) -> dict[str, Any]:
    """Leave *directory* with one compressed PROCESS log — a plan unless *apply*.

    Touches nothing but :func:`plain_logs`, :data:`COMPRESSED_NAME` and
    :data:`PARTIAL_NAME`.  The outcome's ``action`` is one of:

    ``compacted``
        the plain log(s) verified identical to each other, compressed, the
        compressed file verified to decompress to the same SHA-256, and only
        then the plain file(s) removed (with *apply*; ``would compact``
        without);
    ``finished``
        a compaction interrupted after the compressed file was in place: it
        decompresses to each remaining plain file's SHA-256, so they are
        removed (``would finish``);
    ``already compacted``
        the compressed file alone; nothing to do;
    ``no log``
        no PROCESS log in the folder;
    ``left: …``
        refused, nothing changed: the plain files differ from each other, or
        an existing compressed file does not hold what a plain file holds, or
        the round trip of a new one failed (its partial file is removed).

    Restartable: the compressed file is written as :data:`PARTIAL_NAME`,
    synced, verified and renamed into place, so a finished
    :data:`COMPRESSED_NAME` is always whole; a leftover partial file is
    removed before anything else; the plain files go last.
    """
    directory = Path(directory)
    out: dict[str, Any] = {"directory": str(directory)}
    partial = directory / PARTIAL_NAME
    compressed = directory / COMPRESSED_NAME
    plain = plain_logs(directory)
    out["bytes_before"] = _bytes([*plain, compressed, partial])
    out["plain"] = [p.name for p in plain]
    if partial.exists():
        out["partial_removed"] = True
        if apply:
            partial.unlink()

    if compressed.is_file():
        if not plain:
            out.update(action="already compacted", bytes_after=compressed.stat().st_size)
            return out
        held, _ = sha256_decompressed(compressed)
        differing = [p.name for p in plain if sha256_of(p)[0] != held]
        if differing:
            out.update(
                action="left: an existing process.log.gz does not hold what " + ", ".join(differing) + " holds",
                bytes_after=out["bytes_before"],
            )
            return out
        out.update(action="finished" if apply else "would finish", bytes_after=compressed.stat().st_size)
        if apply:
            for path in plain:
                path.unlink()
        return out

    if not plain:
        out.update(action="no log", bytes_after=0)
        return out
    digests = {p.name: sha256_of(p) for p in plain}
    if len({d for d, _ in digests.values()}) != 1:
        out.update(
            action="left: the plain logs differ (" + ", ".join(f"{n} {d[:12]} {k} B" for n, (d, k) in digests.items()) + ")",
            bytes_after=out["bytes_before"],
        )
        return out
    source = plain[0]
    want, length = digests[source.name]
    out["sha256"] = want
    out["plain_bytes_each"] = length
    if not apply:
        out.update(action="would compact", bytes_after=compressed_size(source))
        return out
    _write_compressed(source, partial)
    got, got_length = sha256_decompressed(partial)
    if (got, got_length) != (want, length):
        partial.unlink()
        out.update(
            action=f"left: the round trip read {got[:12]} ({got_length} B) for {want[:12]} ({length} B)",
            bytes_after=out["bytes_before"],
        )
        return out
    os.replace(partial, compressed)
    for path in plain:
        path.unlink()
    out.update(action="compacted", bytes_after=compressed.stat().st_size)
    return out


def close_out(directory: Path) -> dict[str, Any]:
    """The pool's close-out of a run it has just made: :func:`compact` with
    *apply*.  Called after the record is assembled and stamped; reads and
    writes no field of the record."""
    return compact(directory, apply=True)


def log_folders(root: Path) -> list[Path]:
    """Every folder under *root* that holds a PROCESS log in any form, or a
    partial compressed file."""
    found: list[Path] = []
    for here, dirs, files in os.walk(root):
        dirs.sort()
        names = set(files)
        if (
            PLAIN_NAME in names
            or COMPRESSED_NAME in names
            or PARTIAL_NAME in names
            or any(n.endswith(PREFIXED_SUFFIX) for n in names)
        ):
            found.append(Path(here))
    return found
