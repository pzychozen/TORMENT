from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

import pytest

from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.errors import SubstrateConfigurationError


def test_temporary_connection_qualifies_and_supports_commit_and_rollback(tmp_path: Path) -> None:
    database_path = tmp_path / "substrate-test.db"
    with open_temporary_test_connection(database_path) as qualified:
        connection = qualified.connection
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert str(connection.execute("PRAGMA journal_mode").fetchone()[0]).lower() == "wal"
        assert connection.execute("PRAGMA synchronous").fetchone()[0] >= 2

        connection.execute("CREATE TABLE test_rows (value INTEGER NOT NULL)")
        connection.execute("BEGIN IMMEDIATE")
        connection.execute("INSERT INTO test_rows(value) VALUES (1)")
        connection.execute("COMMIT")
        assert connection.execute("SELECT count(*) FROM test_rows").fetchone()[0] == 1

        connection.execute("BEGIN IMMEDIATE")
        connection.execute("INSERT INTO test_rows(value) VALUES (2)")
        connection.execute("ROLLBACK")
        assert connection.execute("SELECT count(*) FROM test_rows").fetchone()[0] == 1


def test_temporary_connection_remains_same_thread_only(tmp_path: Path) -> None:
    database_path = tmp_path / "same-thread.db"
    qualified = open_temporary_test_connection(database_path)
    failures: list[BaseException] = []

    def use_connection_from_other_thread() -> None:
        try:
            qualified.connection.execute("PRAGMA foreign_keys")
        except BaseException as exc:  # sqlite3 raises ProgrammingError here.
            failures.append(exc)

    worker = threading.Thread(target=use_connection_from_other_thread)
    worker.start()
    worker.join()
    qualified.close()

    assert len(failures) == 1
    assert isinstance(failures[0], sqlite3.ProgrammingError)


def test_closing_temporary_connection_releases_database_file(tmp_path: Path) -> None:
    database_path = tmp_path / "close-release.db"
    qualified = open_temporary_test_connection(database_path)
    qualified.connection.execute("CREATE TABLE test_rows (value INTEGER)")
    qualified.close()

    database_path.unlink()
    assert not database_path.exists()


@pytest.mark.parametrize("database_path", [":memory:", "", "not-a-database.txt"])
def test_temporary_connection_requires_explicit_file_backed_db(database_path: str) -> None:
    with pytest.raises(SubstrateConfigurationError):
        open_temporary_test_connection(database_path)


def test_temporary_connection_requires_existing_explicit_test_directory(tmp_path: Path) -> None:
    with pytest.raises(SubstrateConfigurationError):
        open_temporary_test_connection(tmp_path / "missing" / "substrate-test.db")
