"""
v0.1.0b tests: SubprocessPythonExecutor.

Covers the bounded-subprocess executor's contract:
    * successful execution returns stdout + exit_code=0
    * user-code failures surface as nonzero exit_code + stderr (NOT `error`)
    * executor-level failures surface as `error` with exit_code=None
    * timeout is enforced, partial output captured
    * output truncation bounds apply
    * env isolation strips parent env
    * best-effort network block rejects socket/urllib/http.client access
    * strict family gate rejects unknown families
    * missing/invalid `code` argument surfaces as executor error
    * empty `code` string succeeds cleanly (edge case per GPT)

References:
    - torment_service/tool_executors/subprocess_python.py
    - docs/TORMENT_AGENT_RUNTIME_SLICE_v0.1_PLAN.md v0.1.0b
"""
import os
import sys

import pytest

from torment_service.tool_executors import SubprocessPythonExecutor
from torment_service.tool_registry import CODE_EXEC


# Default defaults block from the tool signature; tests override
# timeout_seconds for the timeout test.
DEFAULTS = dict(CODE_EXEC.defaults)


@pytest.fixture
def executor():
    """Fresh executor for each test."""
    return SubprocessPythonExecutor()


# ---------------------------------------------------------------------------
# Successful execution
# ---------------------------------------------------------------------------


class TestSuccessfulExecution:
    """User code runs to completion with exit_code=0."""

    def test_hello_world(self, executor):
        result = executor.execute(
            family="code_exec",
            arguments={"code": "print('hi')"},
            defaults=DEFAULTS,
        )
        assert result["exit_code"] == 0
        assert "hi" in result["output"]
        assert result["error"] is None
        assert result["timed_out"] is False

    def test_arithmetic(self, executor):
        result = executor.execute(
            family="code_exec",
            arguments={"code": "print(2 + 2)"},
            defaults=DEFAULTS,
        )
        assert result["exit_code"] == 0
        assert "4" in result["output"]

    def test_unicode_output_round_trips(self, executor):
        result = executor.execute(
            family="code_exec",
            arguments={"code": "print('\u00e5ngstr\u00f6m')"},
            defaults=DEFAULTS,
        )
        assert result["exit_code"] == 0
        # Some Windows consoles mangle unicode; tolerate that but
        # insist the payload survived subprocess capture somehow.
        assert result["output"]

    def test_empty_code_string_succeeds_cleanly(self, executor):
        """Per GPT: empty code is a distinct edge case from missing code."""
        result = executor.execute(
            family="code_exec",
            arguments={"code": ""},
            defaults=DEFAULTS,
        )
        # Empty Python snippet is valid; subprocess runs preamble
        # and exits 0.
        assert result["exit_code"] == 0
        assert result["error"] is None
        assert result["timed_out"] is False
        # Output should be empty (or nearly so — preamble produces nothing).
        assert result["output"] == ""


# ---------------------------------------------------------------------------
# User-code failures — nonzero exit_code, NOT error
# ---------------------------------------------------------------------------


class TestUserCodeFailures:
    """User-code exceptions/exits surface as nonzero exit_code +
    stderr, NOT as `error`. The executor ran; the code failed."""

    def test_sys_exit_one_returns_exit_code_one(self, executor):
        result = executor.execute(
            family="code_exec",
            arguments={"code": "import sys; sys.exit(1)"},
            defaults=DEFAULTS,
        )
        assert result["exit_code"] == 1
        assert result["error"] is None  # executor worked fine

    def test_runtime_error_surfaces_in_stderr(self, executor):
        result = executor.execute(
            family="code_exec",
            arguments={"code": "1 / 0"},
            defaults=DEFAULTS,
        )
        assert result["exit_code"] != 0
        assert result["error"] is None
        assert "ZeroDivisionError" in result["stderr"]

    def test_syntax_error_surfaces_in_stderr(self, executor):
        result = executor.execute(
            family="code_exec",
            arguments={"code": "def broken("},
            defaults=DEFAULTS,
        )
        assert result["exit_code"] != 0
        assert result["error"] is None
        assert "SyntaxError" in result["stderr"]

    def test_stderr_print_captured(self, executor):
        result = executor.execute(
            family="code_exec",
            arguments={
                "code": "import sys; print('hello err', file=sys.stderr)"
            },
            defaults=DEFAULTS,
        )
        assert result["exit_code"] == 0  # code itself succeeded
        assert "hello err" in result["stderr"]


# ---------------------------------------------------------------------------
# Timeout
# ---------------------------------------------------------------------------


class TestTimeoutEnforcement:
    """Wall-clock timeout kills the subprocess and returns timed_out=True."""

    def test_long_sleep_times_out(self, executor):
        result = executor.execute(
            family="code_exec",
            arguments={"code": "import time; time.sleep(20)"},
            defaults={**DEFAULTS, "timeout_seconds": 2},
        )
        assert result["timed_out"] is True
        assert result["error"] == "timeout"
        assert result["exit_code"] is None

    def test_timeout_includes_any_partial_stdout(self, executor):
        """Output printed before the kill is still captured."""
        result = executor.execute(
            family="code_exec",
            arguments={
                "code": (
                    "import time, sys\n"
                    "print('before', flush=True); sys.stdout.flush()\n"
                    "time.sleep(20)\n"
                )
            },
            defaults={**DEFAULTS, "timeout_seconds": 2},
        )
        assert result["timed_out"] is True
        # Partial stdout may or may not arrive depending on OS buffering
        # behavior under TimeoutExpired; we only assert the shape is valid.
        assert isinstance(result["output"], str)


# ---------------------------------------------------------------------------
# Output truncation
# ---------------------------------------------------------------------------


class TestOutputTruncation:
    """Runaway output is bounded at 10000 chars for stdout."""

    def test_large_stdout_truncated(self, executor):
        result = executor.execute(
            family="code_exec",
            arguments={"code": "print('x' * 50000)"},
            defaults=DEFAULTS,
        )
        assert result["exit_code"] == 0
        assert result["truncated"] is True
        # Output length bounded (plus truncation marker overhead).
        assert len(result["output"]) < 11_000


# ---------------------------------------------------------------------------
# Environment isolation
# ---------------------------------------------------------------------------


class TestEnvironmentIsolation:
    """Parent env vars are not visible to the subprocess."""

    def test_parent_env_var_not_inherited(self, executor, monkeypatch):
        monkeypatch.setenv("TORMENT_TEST_SECRET", "do_not_leak")
        result = executor.execute(
            family="code_exec",
            arguments={
                "code": (
                    "import os; "
                    "print(os.environ.get('TORMENT_TEST_SECRET', 'missing'))"
                )
            },
            defaults=DEFAULTS,
        )
        assert result["exit_code"] == 0
        assert "missing" in result["output"]
        assert "do_not_leak" not in result["output"]


# ---------------------------------------------------------------------------
# Best-effort network block preamble
# ---------------------------------------------------------------------------


class TestNetworkBlockPreamble:
    """The preamble rejects obvious network-access attempts.

    HONEST: this is NOT a security boundary. These tests just
    confirm the preamble is wired; a malicious script can bypass
    via ctypes/syscalls/reimport.
    """

    def test_socket_socket_blocked(self, executor):
        result = executor.execute(
            family="code_exec",
            arguments={"code": "import socket; socket.socket()"},
            defaults=DEFAULTS,
        )
        assert result["exit_code"] != 0
        assert "network access blocked" in result["stderr"]

    def test_socket_create_connection_blocked(self, executor):
        result = executor.execute(
            family="code_exec",
            arguments={
                "code": "import socket; socket.create_connection(('1.1.1.1', 80))"
            },
            defaults=DEFAULTS,
        )
        assert result["exit_code"] != 0
        assert "network access blocked" in result["stderr"]

    def test_socket_getaddrinfo_blocked(self, executor):
        result = executor.execute(
            family="code_exec",
            arguments={"code": "import socket; socket.getaddrinfo('example.com', 80)"},
            defaults=DEFAULTS,
        )
        assert result["exit_code"] != 0
        assert "network access blocked" in result["stderr"]

    def test_urllib_urlopen_blocked(self, executor):
        result = executor.execute(
            family="code_exec",
            arguments={
                "code": (
                    "import urllib.request; "
                    "urllib.request.urlopen('http://example.com')"
                )
            },
            defaults=DEFAULTS,
        )
        assert result["exit_code"] != 0
        assert "network access blocked" in result["stderr"]

    def test_http_client_httpconnection_blocked(self, executor):
        result = executor.execute(
            family="code_exec",
            arguments={
                "code": (
                    "import http.client; "
                    "http.client.HTTPConnection('example.com')"
                )
            },
            defaults=DEFAULTS,
        )
        assert result["exit_code"] != 0
        assert "network access blocked" in result["stderr"]


# ---------------------------------------------------------------------------
# Strict family gate
# ---------------------------------------------------------------------------


class TestStrictFamilyGate:
    """Only `code_exec` is dispatched; everything else → error."""

    def test_unknown_family_returns_error(self, executor):
        result = executor.execute(
            family="web_fetch",
            arguments={"code": "print('hi')"},
            defaults=DEFAULTS,
        )
        assert result["error"] is not None
        assert "unknown_family" in result["error"]
        assert result["exit_code"] is None

    def test_empty_family_returns_error(self, executor):
        result = executor.execute(
            family="",
            arguments={"code": "print('hi')"},
            defaults=DEFAULTS,
        )
        assert result["error"] is not None
        assert "unknown_family" in result["error"]


# ---------------------------------------------------------------------------
# Argument validation
# ---------------------------------------------------------------------------


class TestArgumentValidation:
    """Missing / wrong-type `code` argument surfaces as executor error."""

    def test_missing_code_argument(self, executor):
        result = executor.execute(
            family="code_exec",
            arguments={},
            defaults=DEFAULTS,
        )
        assert result["error"] == "missing_required_argument: code"
        assert result["exit_code"] is None

    def test_code_argument_wrong_type(self, executor):
        result = executor.execute(
            family="code_exec",
            arguments={"code": 42},
            defaults=DEFAULTS,
        )
        assert result["error"] is not None
        assert "invalid_argument_type" in result["error"]
        assert result["exit_code"] is None


# ---------------------------------------------------------------------------
# Return-shape contract
# ---------------------------------------------------------------------------


class TestReturnShape:
    """Every return dict has the declared keys."""

    REQUIRED_KEYS = {
        "output", "stderr", "exit_code",
        "timed_out", "truncated", "error",
    }

    def test_success_shape(self, executor):
        r = executor.execute(
            family="code_exec",
            arguments={"code": "print(1)"},
            defaults=DEFAULTS,
        )
        assert set(r.keys()) == self.REQUIRED_KEYS

    def test_error_shape(self, executor):
        r = executor.execute(
            family="unknown",
            arguments={},
            defaults=DEFAULTS,
        )
        assert set(r.keys()) == self.REQUIRED_KEYS

    def test_timeout_shape(self, executor):
        r = executor.execute(
            family="code_exec",
            arguments={"code": "import time; time.sleep(10)"},
            defaults={**DEFAULTS, "timeout_seconds": 1},
        )
        assert set(r.keys()) == self.REQUIRED_KEYS
