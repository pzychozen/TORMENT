"""Qualified SQLite connection boundaries for the native substrate."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3

from .errors import SubstrateConfigurationError, SubstrateConnectionError
from .runtime_qualification import RuntimeQualificationPolicy, RuntimeQualificationResult, qualify_runtime
from .schema import require_current_schema


DEFAULT_TEST_BUSY_TIMEOUT_MS = 1_000
DEFAULT_EXISTING_CORE_BUSY_TIMEOUT_MS = 1_000


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


@dataclass
class QualifiedExistingCoreConnection:
    """One same-thread, existing-v1.1-core connection owned by its caller.

    This deliberately differs from :class:`QualifiedTemporaryConnection`:
    it opens only a pre-existing database with SQLite's ``mode=rw`` and then
    requires the current schema.  It never bootstraps, migrates, upgrades, or
    otherwise creates durable state.
    """

    connection: sqlite3.Connection
    qualification: RuntimeQualificationResult
    database_path: Path

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "QualifiedExistingCoreConnection":
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


def open_existing_native_core_connection(
    database_path: str | Path,
    *,
    busy_timeout_ms: int = DEFAULT_EXISTING_CORE_BUSY_TIMEOUT_MS,
    runtime_policy: RuntimeQualificationPolicy | None = None,
) -> QualifiedExistingCoreConnection:
    """Open one already-existing, current native core without creating it.

    A3D routes own these connections per bounded operation.  The URI uses
    ``mode=rw`` in addition to the pre-open existence check so a raced-away
    path is refused by SQLite instead of being recreated.
    """
    path = _validate_existing_core_database_path(database_path)
    if not isinstance(busy_timeout_ms, int) or busy_timeout_ms < 0:
        raise SubstrateConfigurationError("busy_timeout_ms must be a non-negative integer")
    qualification = qualify_runtime(policy=runtime_policy)
    try:
        connection = sqlite3.connect(
            f"{path.as_uri()}?mode=rw",
            uri=True,
            isolation_level=None,
            check_same_thread=True,
        )
    except sqlite3.Error as exc:
        raise SubstrateConnectionError("unable to open the existing native core") from exc
    try:
        _configure_connection(connection, busy_timeout_ms=busy_timeout_ms)
        require_current_schema(connection)
    except Exception:
        connection.close()
        raise
    return QualifiedExistingCoreConnection(connection, qualification, path)


def _validate_test_database_path(database_path: str | Path) -> Path:
    if not isinstance(database_path, (str, Path)):
        raise SubstrateConfigurationError("a file-backed temporary database path is required")
    if str(database_path).strip() in {"", ":memory:"}:
        raise SubstrateConfigurationError("temporary substrate connection requires a file-backed database")
    path = Path(database_path).expanduser().resolve()
    if path.suffix.lower() != ".db":
        raise SubstrateConfigurationError("temporary substrate database path must use a .db suffix")
    return path


def _validate_existing_core_database_path(database_path: str | Path) -> Path:
    if not isinstance(database_path, (str, Path)):
        raise SubstrateConfigurationError("an existing native core database path is required")
    if str(database_path).strip() in {"", ":memory:"}:
        raise SubstrateConfigurationError("existing native core connection requires a file-backed database")
    path = Path(database_path).expanduser().resolve()
    if path.suffix.lower() != ".db":
        raise SubstrateConfigurationError("existing native core database path must use a .db suffix")
    if not path.is_file():
        raise SubstrateConfigurationError("native core database must already exist")
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
