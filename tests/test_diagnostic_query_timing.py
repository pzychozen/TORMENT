"""Bounded observability checks; all databases and requests are test fixtures."""
import asyncio
from contextlib import contextmanager
import json
import logging
import sqlite3

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel
import pytest

from torment_service import diagnostic_query_timing as timing


@contextmanager
def collecting():
    collector = timing.QueryTiming()
    token = timing._current.set(collector)
    stack_token = timing._stack.set(())
    try:
        yield collector
    finally:
        timing._stack.reset(stack_token)
        timing._current.reset(token)


def events(caplog):
    return [json.loads(r.message.split("TORMENT_QUERY_TIMING ", 1)[1])
            for r in caplog.records if "TORMENT_QUERY_TIMING " in r.message]


def test_wrapper_preserves_result_identity_exceptions_and_nested_accounting(caplog):
    result = object()
    error = ValueError("original")

    @timing.timed("child")
    def child(fail=False):
        if fail:
            raise error
        return result

    @timing.timed("parent")
    def parent(fail=False):
        return child(fail)

    assert parent() is result
    with pytest.raises(ValueError) as caught:
        parent(True)
    assert caught.value is error
    assert events(caplog) == []
    with collecting() as collector:
        assert parent() is result
        with pytest.raises(ValueError) as caught:
            parent(True)
        assert caught.value is error
        assert collector.stages["parent"]["calls"] == 2
        assert collector.stages["child"]["errors"] == 1
        assert collector.stages["parent"]["self_seconds"] >= 0
        assert collector.stages["parent"]["seconds"] == pytest.approx(
            sum(m["self_seconds"] for m in collector.stages.values()))
    assert timing._current.get() is None and timing._stack.get() == ()


class RequestBody(BaseModel):
    value: int


def test_http_gate_validation_and_exact_response_parity(monkeypatch, caplog):
    caplog.set_level(logging.INFO, logger="uvicorn.error")
    app = FastAPI()
    app.add_middleware(timing.QueryTimingMiddleware)

    @app.post("/agent/query")
    @timing.timed("http.endpoint", endpoint=True)
    def endpoint(req: RequestBody):
        return {"value": req.value, "unchanged": [1, None, "text"]}

    with TestClient(app) as client:
        monkeypatch.delenv(timing.GATE, raising=False)
        off = client.post("/agent/query", json={"value": 3})
        invalid_off = client.post("/agent/query", json={})
        assert events(caplog) == []
        monkeypatch.setenv(timing.GATE, "1")
        on = client.post("/agent/query", json={"value": 3})
        good = events(caplog)
        assert [e["event"] for e in good] == ["request_start", "endpoint_complete", "request_complete"]
        assert good[-1]["endpoint_result"] == "RETURNED"
        assert good[-1]["response_body_complete"] is True
        assert good[-1]["stages"]["http.endpoint"]["calls"] == 1
        assert good[-1]["stages"]["http.request"]["seconds"] == pytest.approx(
            sum(s["self_seconds"] for s in good[-1]["stages"].values()))
        invalid_on = client.post("/agent/query", json={})
        assert invalid_on.status_code == invalid_off.status_code == 422
        assert invalid_on.content == invalid_off.content
        assert events(caplog)[-1]["endpoint_result"] == "NOT_ENTERED"
        assert on.status_code == off.status_code == 200
        assert on.content == off.content and on.headers == off.headers
        caplog.clear()
        client.get("/missing")
        monkeypatch.setenv(timing.GATE, "true")
        client.post("/agent/query", json={"value": 3})
        assert events(caplog) == []


def test_endpoint_completion_survives_failed_send_and_exception_is_unchanged(monkeypatch, caplog):
    caplog.set_level(logging.INFO, logger="uvicorn.error")
    monkeypatch.setenv(timing.GATE, "1")
    error = OSError("disconnected")

    @timing.timed("http.endpoint", endpoint=True)
    def endpoint():
        return {"ok": True}

    async def app(scope, receive, send):
        assert await asyncio.to_thread(endpoint) == {"ok": True}
        await send({"type": "http.response.start", "status": 200, "headers": []})

    async def send(message):
        raise error

    async def receive():
        return {"type": "http.disconnect"}

    with pytest.raises(OSError) as caught:
        asyncio.run(timing.QueryTimingMiddleware(app)(
            {"type": "http", "method": "POST", "path": "/agent/query"}, receive, send))
    assert caught.value is error
    recorded = events(caplog)
    assert recorded[1]["endpoint_result"] == "RETURNED"
    assert recorded[-1]["response_body_complete"] is False
    assert recorded[-1]["stages"]["http.request"]["errors"] == 1


def sqlite_scenario(connect):
    connection = connect(":memory:")
    statements = []
    connection.set_trace_callback(statements.append)
    connection.row_factory = sqlite3.Row
    connection.executescript("CREATE TABLE sample (v INTEGER UNIQUE); INSERT INTO sample VALUES (0);")
    connection.executemany("INSERT INTO sample VALUES (?)", [(1,), (2,), (3,)])
    first = tuple(connection.execute("SELECT v FROM sample ORDER BY v").fetchone())
    cursor = connection.cursor().execute("SELECT v FROM sample ORDER BY v")
    cursor.arraysize = 2
    batch = [tuple(row) for row in cursor.fetchmany()]
    remaining = [tuple(row) for row in cursor]
    all_rows = [tuple(row) for row in connection.execute("SELECT v FROM sample ORDER BY v").fetchall()]
    errors = []
    for sql in ("INVALID SQL", "INSERT INTO sample VALUES (1)"):
        try:
            connection.execute(sql)
        except sqlite3.Error as exc:
            errors.append((type(exc), str(exc), exc.sqlite_errorcode))
    connection.rollback()
    with connection:
        connection.execute("INSERT INTO sample VALUES (5)")
    rows = [tuple(row) for row in connection.execute("SELECT v FROM sample ORDER BY v")]
    connection.close()
    return statements, first, batch, remaining, all_rows, errors, rows


def test_sqlite_exact_statements_results_factories_transactions_and_errors():
    expected = sqlite_scenario(sqlite3.connect)
    with timing.sqlite_connect(":memory:") as connection:
        assert type(connection) is sqlite3.Connection
    connection.close()
    assert sqlite_scenario(timing.sqlite_connect) == expected
    with collecting() as collector:
        assert sqlite_scenario(timing.sqlite_connect) == expected
        explicit = timing.sqlite_connect(":memory:", factory=sqlite3.Connection)
        assert type(explicit) is sqlite3.Connection
        explicit.close()
        assert collector.stages["sqlite.connect"]["calls"] == 2
        assert collector.stages["sqlite.execute"]["errors"] == 2
        assert collector.stages["sqlite.fetch"]["calls"] > 0
        assert collector.sqlite_busy_or_locked == 0


def test_aggregate_volume_is_bounded():
    @timing.timed("repeat")
    def operation():
        return 1

    with collecting() as collector:
        for _ in range(100):
            assert operation() == 1
        assert collector.stages["repeat"]["calls"] == 100
        assert len(collector.stages["repeat"]["samples"]) == 8


def test_existing_native_rest_contract_with_diagnostics_enabled(tmp_path, monkeypatch, caplog):
    from test_b5_a4r3_public_backend_selection import test_rest_native_transport_uses_one_configured_runtime

    monkeypatch.setenv(timing.GATE, "1")
    caplog.set_level(logging.INFO, logger="uvicorn.error")
    test_rest_native_transport_uses_one_configured_runtime(tmp_path, monkeypatch)
    completed = [e for e in events(caplog) if e["event"] == "request_complete"]
    assert len(completed) == 1
    assert completed[0]["endpoint_result"] == "RETURNED"
    stages = completed[0]["stages"]
    assert stages["native.owner_recovery"]["calls"] == 3
    assert stages["sqlite.execute"]["calls"] > 0
    assert stages["query.fabric"]["calls"] == 1
