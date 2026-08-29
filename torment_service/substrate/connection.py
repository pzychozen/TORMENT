"""Temporary/test-only SQLite connection boundary for Phase 7A."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3

from .errors import SubstrateConfigurationError, SubstrateConnectionError
from .runtime_qualification import RuntimeQualificationPolicy, RuntimeQualificationResult, qualify_runtime


DEFAULT_TEST_BUSY_TIMEOUT_MS = 1_000


@dataclass
class QualifiedTemporaryConnection:
    """A same-thread SQLite connection plus its qualification facts."""

    connection: sqlite3.Connection
    qualification: RuntimeQualificationResult
    database_path: Path

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "QualifiedTemporaryConnection":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()


def open_temporary_test_connection(
    database_path: str | Path,
    *,
    busy_timeout_ms: int = DEFAULT_TEST_BUSY_TIMEOUT_MS,
    runtime_policy: RuntimeQualificationPolicy | None = None,
) -> QualifiedTemporaryConnection:
    """Open a qualified file-backed test database; no production path exists here."""
    path = _validate_test_database_path(database_path)
    if not isinstance(busy_timeout_ms, int) or busy_timeout_ms < 0:
        raise SubstrateConfigurationError("busy_timeout_ms must be a non-negative integer")

    qualification = qualify_runtime(policy=runtime_policy)
    if not path.parent.is_dir():
        raise SubstrateConfigurationError(
            "temporary substrate database parent directory must already exist"
        )
    try:
        connection = sqlite3.connect(
            str(path),
            isolation_level=None,
            check_same_thread=True,
        )
    except sqlite3.Error as exc:
        raise SubstrateConnectionError("unable to open temporary substrate database") from exc

    try:
        _configure_connection(connection, busy_timeout_ms=busy_timeout_ms)
    except Exception:
        connection.close()
        raise
    return QualifiedTemporaryConnection(connection, qualification, path)


def _validate_test_database_path(database_path: str | Path) -> Path:
    if not isinstance(database_path, (str, Path)):
        raise SubstrateConfigurationError("a file-backed temporary database path is required")
    if str(database_path).strip() in {"", ":memory:"}:
        raise SubstrateConfigurationError("temporary substrate connection requires a file-backed database")
    path = Path(database_path).expanduser().resolve()
    if path.suffix.lower() != ".db":
        raise SubstrateConfigurationError("temporary substrate database path must use a .db suffix")
    return path


def _configure_connection(connection: sqlite3.Connection, *, busy_timeout_ms: int) -> None:
    try:
        # This must occur before any transaction or savepoint is active.
        connection.execute("PRAGMA foreign_keys = ON")
        if connection.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
            raise SubstrateConnectionError("SQLite foreign_keys did not read back as enabled")

        connection.execute(f"PRAGMA busy_timeout = {busy_timeout_ms}")
        if connection.execute("PRAGMA busy_timeout").fetchone()[0] != busy_timeout_ms:
            raise SubstrateConnectionError("SQLite busy_timeout did not read back as configured")

        connection.execute("PRAGMA synchronous = FULL")
        if connection.execute("PRAGMA synchronous").fetchone()[0] < 2:
            raise SubstrateConnectionError("SQLite synchronous did not meet FULL")

        journal_mode = str(connection.execute("PRAGMA journal_mode = WAL").fetchone()[0]).lower()
        if journal_mode != "wal":
            raise SubstrateConnectionError("SQLite journal_mode did not establish WAL")
        if str(connection.execute("PRAGMA journal_mode").fetchone()[0]).lower() != "wal":
            raise SubstrateConnectionError("SQLite journal_mode did not read back as WAL")
        if connection.execute("PRAGMA synchronous").fetchone()[0] < 2:
            raise SubstrateConnectionError("SQLite synchronous no longer met FULL after WAL setup")
    except SubstrateConnectionError:
        raise
    except sqlite3.Error as exc:
        raise SubstrateConnectionError("temporary connection qualification failed") from exc
