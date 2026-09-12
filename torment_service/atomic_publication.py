"""Small byte publication primitives for externally owned files.

Containment and semantic verification belong to callers. Complete temporary
files are flushed before publication. Create uses the selector's no-overwrite
hard-link pattern; replacement compares an exact predecessor under a file-local
OS lock. The lock is a rendezvous file only, never owner state or a root lock.
It stays in place so competing processes cannot lock different inodes after
cleanup. OS locks release on process death.

Replacement serializes users of this helper. Ordinary writers that do not use
it must be quiescent, as later Genesis preparation requires. This module does
not stop writers or implement that preparation policy.
"""

from contextlib import contextmanager
from enum import Enum
import os
from pathlib import Path
import re
import tempfile
import time


class PublicationConflict(ValueError):
    """The target does not contain the exact allowed predecessor/successor."""


class PublicationResult(str, Enum):
    CREATED = "CREATED"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    REPLACED = "REPLACED"
    ALREADY_EXACT = "ALREADY_EXACT"


def is_publication_temporary(path: Path, targets) -> bool:
    """Recognize only this publisher's mkstemp names beside explicit targets.

    A recognized name is nonsemantic residue, never proof of target ownership
    or permission to read/adopt the temporary contents.
    """
    return any(path.parent == target.parent and re.fullmatch(
        r"\." + re.escape(target.name) + r"\.[a-z0-9_]{8}\.tmp", path.name)
        for target in map(Path, targets))


def _bytes(value: bytes) -> None:
    if type(value) is not bytes:
        raise TypeError("publication content must be bytes")


@contextmanager
def _prepared_file(target: Path, content: bytes):
    fd, name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        yield temporary
    finally:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass


def _sync_publication(target: Path) -> None:
    if os.name == "nt":
        # Windows requires a writable descriptor for FlushFileBuffers; it has
        # no portable directory-fsync equivalent. No contents are rewritten.
        with target.open("r+b") as handle:
            os.fsync(handle.fileno())
    else:
        fd = os.open(target.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


def publish_if_absent(path: str | Path, content: bytes) -> PublicationResult:
    """Publish complete bytes, or report existence for owner-side verification.

    Parent directories must already exist. A failure after publication can
    leave the complete target present; callers must verify it on retry.
    """
    _bytes(content)
    target = Path(path)
    with _prepared_file(target, content) as temporary:
        try:
            os.link(temporary, target)
        except FileExistsError:
            return PublicationResult.ALREADY_EXISTS
        _sync_publication(target)
    return PublicationResult.CREATED


@contextmanager
def _replacement_lock(target: Path):
    lock = target.with_name(f".{target.name}.publication.lock")
    # Refuse symlink rendezvous names; this lock never follows another owner.
    if lock.is_symlink():
        raise PublicationConflict("publication lock must not be a symlink")
    with lock.open("a+b") as handle:
        deadline = time.monotonic() + 10.0
        while True:
            try:
                if os.name == "nt":
                    import msvcrt
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError as exc:
                if time.monotonic() >= deadline:
                    raise PublicationConflict("publication lock is busy") from exc
                time.sleep(0.01)
        try:
            # Locking a byte beyond EOF is supported on Windows. Initialize
            # only after acquisition: another holder can deny even a read of
            # the locked byte, and the lock file may be empty after a crash.
            handle.seek(0)
            if handle.read(1) == b"":
                handle.write(b"0")
                handle.flush()
            yield
        finally:
            if os.name == "nt":
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def replace_if_exact_predecessor(
    path: str | Path, expected_bytes: bytes, replacement_bytes: bytes,
) -> PublicationResult:
    """Replace an exact predecessor once; exact successor replay does no write."""
    _bytes(expected_bytes)
    _bytes(replacement_bytes)
    target = Path(path)
    with _replacement_lock(target):
        if target.is_symlink() or not target.is_file():
            raise PublicationConflict("replacement requires a regular existing target")
        existing = target.read_bytes()
        if existing == replacement_bytes:
            return PublicationResult.ALREADY_EXACT
        if existing != expected_bytes:
            raise PublicationConflict("publication predecessor does not match")
        with _prepared_file(target, replacement_bytes) as temporary:
            # Detect a change during temporary-file preparation as well. The
            # file-local lock excludes other calls to this replacement helper.
            if target.is_symlink() or target.read_bytes() != expected_bytes:
                raise PublicationConflict("publication predecessor changed")
            os.replace(temporary, target)
            _sync_publication(target)
    return PublicationResult.REPLACED
