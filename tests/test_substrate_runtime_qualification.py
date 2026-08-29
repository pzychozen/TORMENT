from __future__ import annotations

import sqlite3

import pytest

from torment_service.substrate.errors import SubstrateConfigurationError, SubstrateRuntimeIneligible
from torment_service.substrate.runtime_qualification import (
    KNOWN_INELIGIBLE_SQLITE_RUNTIME,
    QUALIFIED_SQLITE_RUNTIME,
    RuntimeQualificationPolicy,
    inspect_runtime,
    qualify_runtime,
)


def test_isolated_runtime_qualifies_against_exact_policy() -> None:
    result = qualify_runtime()

    assert result.runtime_admissible is True
    assert result.sqlite_runtime_version == QUALIFIED_SQLITE_RUNTIME
    assert result.json_available is True
    assert result.transaction_savepoint_available is True
    assert result.reason == "qualified"


def test_known_torment_runtime_is_rejected_by_policy() -> None:
    policy = RuntimeQualificationPolicy()
    result = inspect_runtime(
        policy=policy,
        sqlite_module=_SyntheticSQLiteModule(KNOWN_INELIGIBLE_SQLITE_RUNTIME),
    )

    assert result.runtime_admissible is False
    assert KNOWN_INELIGIBLE_SQLITE_RUNTIME in result.reason


def test_json_probe_failure_is_fail_closed() -> None:
    with pytest.raises(SubstrateRuntimeIneligible, match="JSON probe failed"):
        qualify_runtime(
            sqlite_module=_SyntheticSQLiteModule(QUALIFIED_SQLITE_RUNTIME),
            connection_factory=_NoJsonConnection,
        )


def test_runtime_policy_cannot_be_relaxed() -> None:
    with pytest.raises(SubstrateConfigurationError):
        RuntimeQualificationPolicy(admissible_sqlite_versions=frozenset({"3.99.0"}))


class _SyntheticSQLiteModule:
    version = sqlite3.version

    def __init__(self, sqlite_version: str) -> None:
        self.sqlite_version = sqlite_version

    @staticmethod
    def connect(_: str) -> sqlite3.Connection:
        return sqlite3.connect(":memory:")


class _NoJsonConnection:
    def __init__(self) -> None:
        self._connection = sqlite3.connect(":memory:")

    def execute(self, statement: str, *args: object) -> object:
        if "json_valid" in statement:
            raise sqlite3.OperationalError("json unavailable")
        return self._connection.execute(statement, *args)

    def close(self) -> None:
        self._connection.close()
