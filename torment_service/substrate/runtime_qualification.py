"""Fail-closed qualification for Python's actually loaded SQLite runtime."""

from __future__ import annotations

from dataclasses import dataclass
import platform
import sqlite3
from collections.abc import Callable
from typing import Any, Final

from .errors import SubstrateConfigurationError, SubstrateRuntimeIneligible


QUALIFIED_SQLITE_RUNTIME: Final[str] = "3.53.4"
KNOWN_INELIGIBLE_SQLITE_RUNTIME: Final[str] = "3.51.2"


@dataclass(frozen=True)
class RuntimeQualificationPolicy:
    """Explicit runtime policy; it is deliberately not a minimum-version test."""

    admissible_sqlite_versions: frozenset[str] = frozenset({QUALIFIED_SQLITE_RUNTIME})

    def __post_init__(self) -> None:
        if self.admissible_sqlite_versions != frozenset({QUALIFIED_SQLITE_RUNTIME}):
            raise SubstrateConfigurationError(
                "Phase 7A accepts only the frozen SQLite runtime policy"
            )


@dataclass(frozen=True)
class RuntimeQualificationResult:
    """Redacted runtime facts suitable for diagnostics and startup reporting."""

    python_version: str
    sqlite3_module_version: str
    sqlite_runtime_version: str
    json_available: bool
    transaction_savepoint_available: bool
    runtime_admissible: bool
    reason: str


ConnectionFactory = Callable[[], Any]


def inspect_runtime(
    *,
    policy: RuntimeQualificationPolicy | None = None,
    sqlite_module: Any = sqlite3,
    connection_factory: ConnectionFactory | None = None,
    python_version: str | None = None,
) -> RuntimeQualificationResult:
    """Collect and evaluate runtime facts without opening a substrate database."""
    policy = policy or RuntimeQualificationPolicy()
    runtime_version = str(sqlite_module.sqlite_version)
    module_version = str(sqlite_module.version)
    json_available, transaction_savepoint_available, probe_reason = _probe_sqlite(
        sqlite_module=sqlite_module,
        connection_factory=connection_factory,
    )

    if runtime_version == KNOWN_INELIGIBLE_SQLITE_RUNTIME:
        reason = f"SQLite {runtime_version} is explicitly ineligible for the WAL semantic core"
        admissible = False
    elif runtime_version not in policy.admissible_sqlite_versions:
        reason = f"SQLite {runtime_version} is not in the explicit admissibility policy"
        admissible = False
    elif not json_available:
        reason = f"SQLite JSON probe failed: {probe_reason}"
        admissible = False
    elif not transaction_savepoint_available:
        reason = f"SQLite transaction/savepoint probe failed: {probe_reason}"
        admissible = False
    else:
        reason = "qualified"
        admissible = True

    return RuntimeQualificationResult(
        python_version=python_version or platform.python_version(),
        sqlite3_module_version=module_version,
        sqlite_runtime_version=runtime_version,
        json_available=json_available,
        transaction_savepoint_available=transaction_savepoint_available,
        runtime_admissible=admissible,
        reason=reason,
    )


def qualify_runtime(**kwargs: Any) -> RuntimeQualificationResult:
    """Return qualified runtime facts or fail closed with a substrate error."""
    result = inspect_runtime(**kwargs)
    if not result.runtime_admissible:
        raise SubstrateRuntimeIneligible(result.reason)
    return result


def _probe_sqlite(
    *, sqlite_module: Any, connection_factory: ConnectionFactory | None
) -> tuple[bool, bool, str]:
    factory = connection_factory or (lambda: sqlite_module.connect(":memory:"))
    connection: Any | None = None
    try:
        connection = factory()
        json_value = connection.execute("SELECT json_valid(?)", ('{"probe":true}',)).fetchone()[0]
        if json_value != 1:
            return False, False, "json_valid did not return 1"
        connection.execute("BEGIN")
        connection.execute("SAVEPOINT substrate_qualification")
        connection.execute("RELEASE SAVEPOINT substrate_qualification")
        connection.execute("ROLLBACK")
        return True, True, "qualified"
    except Exception:
        return False, False, "unavailable"
    finally:
        if connection is not None:
            try:
                connection.close()
            except Exception:
                pass
