# torment_service/tool_executors/subprocess_python.py
"""
SubprocessPythonExecutor — best-effort bounded subprocess execution
for the `code_exec` tool family.

Provides timeout, env stripping, output bounds, and a light network-
block preamble. **Not a hostile-code containment boundary.** A
malicious script can bypass the network block via ctypes, direct
syscalls, module-system tricks, or raw subprocess re-entry. The
guarantees are appropriate to accidental/benign misuse, not hostile
inputs.

Designed and validated Windows-first. Linux hardening/parity is
future work; a real hostile-code boundary requires seccomp /
namespaces / AppContainer / containers, out of scope for v0.1.0b.

Return shape (matches the `ToolExecutor` protocol in agent_loop.py):

    {
        "output":       str,           # stdout, possibly truncated
        "stderr":       str,           # stderr, possibly truncated
        "exit_code":    int | None,    # None if execution didn't start
        "timed_out":    bool,
        "truncated":    bool,
        "error":        str | None,    # executor/system failure;
                                       # NOT set for user-code runtime errors
    }

Error split (deliberate doctrinal distinction, GPT-approved):
    * Executor/system failure → `error` is set, `exit_code` is None.
      Examples: interpreter not found, missing required argument,
      subprocess crash before exec, unknown family, timeout.
    * User-code failure → `error` is None, `exit_code` is nonzero,
      stderr contains the traceback. The sandbox ran; the code
      failed. These are very different conditions and should be
      observable separately.

References:
    - docs/TORMENT_AGENT_RUNTIME_SLICE_v0.1_PLAN.md v0.1.0b
    - torment_service.tool_registry.CODE_EXEC (signature + defaults)
    - torment_service.agent_loop.ToolExecutor (protocol)
"""
from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, Tuple


# Output size bounds — character-wise, not byte-wise.
_STDOUT_MAX_CHARS = 10_000
_STDERR_MAX_CHARS = 2_000
_TRUNCATION_MARKER = "\n...<truncated>"


# Best-effort network-block preamble, prepended to user code.
# HONEST LABEL: this is NOT a security boundary. Bypassable via
# ctypes, direct syscalls, re-import under a different alias,
# os.system, subprocess re-entry, /dev/* on Linux, etc. The purpose
# is to stop accidental network use and make the best-effort story
# less flimsy — not to contain a malicious actor.
#
# Implementation note: `socket.socket` is a CLASS that other stdlib
# modules (notably `ssl`) subclass at import time (`class SSLSocket(socket):`).
# If we replace it with a plain function, Python's class-definition
# machinery fails with "function() argument 'code' must be code, not str"
# the moment ssl or anything downstream imports. So we use a CLASS as
# the blocker for class-valued attributes — class definition still
# works (the class body runs), only instantiation raises. Function-
# valued attributes like socket.create_connection and
# urllib.request.urlopen are replaced with a plain function, since
# nothing subclasses them.
_NETWORK_BLOCK_PREAMBLE = '''\
class _TormentBlockedClass:
    """Class-valued network blocker. Subclassable (so `ssl` etc. can
    define their own classes at import time) but raises on actual
    instantiation or call. Best-effort; not a security boundary.
    """
    def __init__(self, *args, **kwargs):
        raise RuntimeError(
            "network access blocked by code_exec sandbox (best-effort)"
        )
    def __call__(self, *args, **kwargs):
        raise RuntimeError(
            "network access blocked by code_exec sandbox (best-effort)"
        )
def _torment_blk_fn(*args, **kwargs):
    raise RuntimeError(
        "network access blocked by code_exec sandbox (best-effort)"
    )
import socket as _torment_socket
# socket.socket is a class and is subclassed by ssl.SSLSocket at
# stdlib import time. Use the class-based blocker.
_torment_socket.socket = _TormentBlockedClass
# socket.create_connection and socket.getaddrinfo are functions;
# safe to replace with a plain function.
_torment_socket.create_connection = _torment_blk_fn
_torment_socket.getaddrinfo = _torment_blk_fn
try:
    import urllib.request as _torment_urlreq
    _torment_urlreq.urlopen = _torment_blk_fn
except ImportError:
    pass
try:
    import http.client as _torment_httpc
    # HTTPConnection / HTTPSConnection are classes, potentially
    # subclassable, so use the class-based blocker.
    _torment_httpc.HTTPConnection = _TormentBlockedClass
    _torment_httpc.HTTPSConnection = _TormentBlockedClass
except ImportError:
    pass
del _torment_blk_fn

# ----- user code begins below -----
'''


def _truncate(text: str, limit: int) -> Tuple[str, bool]:
    """Truncate `text` to `limit` chars; return (possibly-truncated, was_truncated)."""
    if text is None:
        return "", False
    if len(text) <= limit:
        return text, False
    return text[:limit] + _TRUNCATION_MARKER, True


def _empty_result_with_error(error: str) -> Dict[str, Any]:
    """Shape a result dict for an executor-level failure."""
    return {
        "output": "",
        "stderr": "",
        "exit_code": None,
        "timed_out": False,
        "truncated": False,
        "error": error,
    }


@dataclass
class SubprocessPythonExecutor:
    """Bounded subprocess executor for `code_exec`.

    Instantiated by AgentRunner owners who want real execution
    instead of the stub path. Provides best-effort sandboxing as
    documented at module scope. NOT suitable for hostile-code
    containment; pair with OS-level isolation if that's the goal.

    Parameters:
        python_path: path to the Python interpreter to use.
            Defaults to `sys.executable` (same interpreter as parent).
    """
    python_path: str = field(default_factory=lambda: sys.executable)

    def execute(
        self,
        family: str,
        arguments: Dict[str, Any],
        defaults: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Run a narrowed tool invocation.

        Contract (per the ToolExecutor protocol):
            family: the narrowed family name. v0.1.0b accepts only
                "code_exec"; anything else → error="unknown_family".
            arguments: LLM-filled arguments. Must contain "code" (a
                Python source string). Absence → error="missing_required_argument".
            defaults: controller-side constraints from the
                ToolSignature (language, scope, timeout_seconds).
                Not LLM-fillable.
        """
        # Strict family check — we don't dispatch anything else.
        if family != "code_exec":
            return _empty_result_with_error(f"unknown_family: {family!r}")

        # Required argument check.
        if "code" not in arguments:
            return _empty_result_with_error("missing_required_argument: code")

        code = arguments.get("code")
        if not isinstance(code, str):
            return _empty_result_with_error(
                f"invalid_argument_type: code (expected str, got {type(code).__name__})"
            )

        # Build the full subprocess source: preamble + user code.
        full_code = _NETWORK_BLOCK_PREAMBLE + code

        # Pull bounded defaults; fall back to safe values if absent.
        timeout_seconds = float(defaults.get("timeout_seconds", 10))

        # Invoke subprocess.
        try:
            result = subprocess.run(
                [self.python_path, "-E", "-S", "-c", full_code],
                timeout=timeout_seconds,
                env={},                 # no inherited env vars
                capture_output=True,
                text=True,
                errors="replace",       # tolerate weird decoded bytes
                shell=False,            # no shell injection surface
                check=False,            # we read returncode ourselves
            )
        except subprocess.TimeoutExpired as e:
            # Include any partial output captured before the kill.
            # Note: TimeoutExpired.stdout/stderr can be bytes even when
            # subprocess.run was called with text=True, because the kill
            # pre-empts the text-decoding pipeline. Normalize to str.
            partial_stdout_raw = e.stdout
            partial_stderr_raw = e.stderr
            if isinstance(partial_stdout_raw, bytes):
                partial_stdout_raw = partial_stdout_raw.decode("utf-8", errors="replace")
            if isinstance(partial_stderr_raw, bytes):
                partial_stderr_raw = partial_stderr_raw.decode("utf-8", errors="replace")
            partial_out, out_trunc = _truncate(partial_stdout_raw or "", _STDOUT_MAX_CHARS)
            partial_err, err_trunc = _truncate(partial_stderr_raw or "", _STDERR_MAX_CHARS)
            return {
                "output": partial_out,
                "stderr": partial_err,
                "exit_code": None,
                "timed_out": True,
                "truncated": out_trunc or err_trunc,
                "error": "timeout",
            }
        except FileNotFoundError:
            return _empty_result_with_error("interpreter_not_found")
        except Exception as e:
            return _empty_result_with_error(
                f"subprocess_error: {type(e).__name__}: {e}"
            )

        # Successful or user-code-failed run. Either way: bound output.
        stdout_out, out_trunc = _truncate(result.stdout, _STDOUT_MAX_CHARS)
        stderr_out, err_trunc = _truncate(result.stderr, _STDERR_MAX_CHARS)

        return {
            "output": stdout_out,
            "stderr": stderr_out,
            "exit_code": result.returncode,
            "timed_out": False,
            "truncated": out_trunc or err_trunc,
            "error": None,  # user-code failures live in exit_code + stderr, not here
        }
