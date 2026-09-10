"""Opt-in, request-local aggregate timings for POST /agent/query.

No payloads, SQL text, identifiers, or row values are recorded. Inclusive spans
overlap; self_seconds excludes measured children. The ASGI envelope includes
dispatch/validation and response handling, not proof of delivery to a client.
"""
from __future__ import annotations

from contextvars import ContextVar
from functools import wraps
import inspect
import json
import logging
import os
import sqlite3
from time import perf_counter
from uuid import uuid4


GATE = "TORMENT_DIAGNOSTIC_QUERY_TIMING"
_current = ContextVar("query_timing", default=None)
_stack = ContextVar("query_timing_stack", default=())
_log = logging.getLogger("uvicorn.error")


class QueryTiming:
    def __init__(self):
        self.request_id = uuid4().hex
        self.started = perf_counter()
        self.stages = {}
        self.endpoint_started = None
        self.endpoint_finished = None
        self.endpoint_result = "NOT_ENTERED"
        self.status = None
        self.response_body_complete = False
        self.sqlite_busy_or_locked = 0

    def emit(self, event):
        _log.info("TORMENT_QUERY_TIMING %s", json.dumps({
            "event": event, "request_id": self.request_id,
            "elapsed_seconds": perf_counter() - self.started,
            "endpoint_result": self.endpoint_result,
            "http_status": self.status,
            "response_body_complete": self.response_body_complete,
            "validation_dispatch_seconds": None if self.endpoint_started is None
                else self.endpoint_started - self.started,
            "after_endpoint_seconds": None if self.endpoint_finished is None
                else perf_counter() - self.endpoint_finished,
            "sqlite_busy_or_locked": self.sqlite_busy_or_locked,
            "stages": self.stages,
        }, sort_keys=True))


class span:
    """Measure a synchronous nested boundary; never handle business exceptions."""
    def __init__(self, name):
        self.name = name
        self.collector = _current.get()

    def __enter__(self):
        if self.collector is not None:
            self.parents = _stack.get()
            self.children = 0.0
            self.started = perf_counter()
            self.token = _stack.set(self.parents + (self,))
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.collector is None:
            return False
        elapsed = perf_counter() - self.started
        _stack.reset(self.token)
        if self.parents:
            self.parents[-1].children += elapsed
        metric = self.collector.stages.setdefault(self.name, {
            "calls": 0, "seconds": 0.0, "self_seconds": 0.0,
            "errors": 0, "samples": [],
        })
        metric["calls"] += 1
        metric["seconds"] += elapsed
        metric["self_seconds"] += elapsed - self.children
        # Exception exits, including normal cursor-iteration StopIteration;
        # this field is not a count of SQLite failures or lock waits.
        metric["errors"] += int(exc_type is not None)
        # Only a bounded sample of coarse calls, never per-SQL/row logs.
        if not self.name.startswith("sqlite.") and len(metric["samples"]) < 8:
            metric["samples"].append({
                "start_seconds": self.started - self.collector.started,
                "seconds": elapsed,
                "parent": self.parents[-1].name if self.parents else None,
            })
        if isinstance(exc, sqlite3.Error) and self.name.startswith("sqlite."):
            code = getattr(exc, "sqlite_errorcode", 0) & 255
            self.collector.sqlite_busy_or_locked += int(code in (5, 6))
        return False


def timed(name, *, endpoint=False):
    def decorate(function):
        @wraps(function)
        def measured(*args, **kwargs):
            collector = _current.get()
            if collector is None:
                return function(*args, **kwargs)
            if endpoint:
                collector.endpoint_started = perf_counter()
                collector.endpoint_result = "EXCEPTION"
            try:
                with span(name):
                    result = function(*args, **kwargs)
                if endpoint:
                    collector.endpoint_result = "RETURNED"
                return result
            finally:
                if endpoint:
                    collector.endpoint_finished = perf_counter()
                    collector.emit("endpoint_complete")
        if endpoint:
            # FastAPI must resolve postponed annotations in the original module.
            measured.__signature__ = inspect.signature(function, eval_str=True)
        return measured
    return decorate


class QueryTimingMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if not (scope["type"] == "http" and scope.get("method") == "POST"
                and scope.get("path") == "/agent/query"
                and os.environ.get(GATE) == "1"):
            return await self.app(scope, receive, send)
        collector = QueryTiming()
        token = _current.set(collector)
        stack_token = _stack.set(())

        async def measured_send(message):
            if message["type"] == "http.response.start":
                collector.status = message["status"]
            await send(message)
            if message["type"] == "http.response.body" and not message.get("more_body", False):
                collector.response_body_complete = True

        try:
            collector.emit("request_start")
            with span("http.request"):
                await self.app(scope, receive, measured_send)
        finally:
            try:
                collector.emit("request_complete")
            finally:
                _stack.reset(stack_token)
                _current.reset(token)


class _TimingCursor(sqlite3.Cursor):
    @timed("sqlite.execute")
    def execute(self, *args, **kwargs):
        return super().execute(*args, **kwargs)

    @timed("sqlite.executemany")
    def executemany(self, *args, **kwargs):
        return super().executemany(*args, **kwargs)

    @timed("sqlite.executescript")
    def executescript(self, *args, **kwargs):
        return super().executescript(*args, **kwargs)

    @timed("sqlite.fetch")
    def fetchone(self, *args, **kwargs):
        return super().fetchone(*args, **kwargs)

    @timed("sqlite.fetch")
    def fetchmany(self, *args, **kwargs):
        return super().fetchmany(*args, **kwargs)

    @timed("sqlite.fetch")
    def fetchall(self, *args, **kwargs):
        return super().fetchall(*args, **kwargs)

    @timed("sqlite.fetch")
    def __next__(self):
        return super().__next__()


class _TimingConnection(sqlite3.Connection):
    def cursor(self, factory=_TimingCursor):
        return super().cursor(factory)

    def execute(self, *args, **kwargs):
        return self.cursor().execute(*args, **kwargs)

    def executemany(self, *args, **kwargs):
        return self.cursor().executemany(*args, **kwargs)

    def executescript(self, *args, **kwargs):
        return self.cursor().executescript(*args, **kwargs)

    @timed("sqlite.close")
    def close(self):
        return super().close()


def sqlite_connect(*args, **kwargs):
    """Use native sqlite3 types unchanged unless an opted-in request is active.

    Respect explicitly supplied factories (including the positional factory).
    No statements, connection parameters, pragmas, or transactions are added.
    """
    if _current.get() is None:
        return sqlite3.connect(*args, **kwargs)
    if len(args) < 6 and "factory" not in kwargs:
        kwargs["factory"] = _TimingConnection
    with span("sqlite.connect"):
        return sqlite3.connect(*args, **kwargs)
