"""Regression tests for app.py security hardening (Bug Fix 10).

Covers:
  1. _safe_join_data_dir rejects traversal / escaped paths
  2. _safe_join_data_dir keeps paths inside DATA_DIR
  3. Endpoints no longer return raw exception text to callers
  4. _safe_log_value escapes CR/LF on logged user-derived values
"""

import os
import sys
import unittest
import json
from types import SimpleNamespace

import pytest

# We import the helpers directly from the app module.
# _safe_join_data_dir and _safe_log_value are module-level functions.
import torment_service.app as appmod
from torment_service.app import (
    _validate_path_component,
    _safe_join_data_dir,
    _safe_log_value,
    DATA_DIR,
)
from fastapi import HTTPException


class TestSafeJoinDataDir(unittest.TestCase):
    """1 & 2: _safe_join_data_dir rejects traversal and keeps paths inside DATA_DIR."""

    # --- Traversal rejection ---

    def test_rejects_dotdot(self):
        """Path component containing '..' should be rejected."""
        with self.assertRaises(HTTPException) as ctx:
            _safe_join_data_dir("workspaces", "..", "..", "etc", "passwd")
        self.assertEqual(ctx.exception.status_code, 400)

    def test_rejects_slash_in_component(self):
        """Path component with embedded '/' should be rejected."""
        with self.assertRaises(HTTPException) as ctx:
            _safe_join_data_dir("workspaces", "ws/../../etc")
        self.assertEqual(ctx.exception.status_code, 400)

    def test_rejects_backslash_in_component(self):
        """Path component with embedded backslash should be rejected."""
        with self.assertRaises(HTTPException) as ctx:
            _safe_join_data_dir("workspaces", "ws\\..\\..\\etc")
        self.assertEqual(ctx.exception.status_code, 400)

    def test_rejects_empty_component(self):
        """Empty path component should be rejected."""
        with self.assertRaises(HTTPException) as ctx:
            _safe_join_data_dir("workspaces", "")
        self.assertEqual(ctx.exception.status_code, 400)

    # --- Stays inside DATA_DIR ---

    def test_valid_path_stays_inside_data_dir(self):
        """A normal path should stay under DATA_DIR."""
        result = _safe_join_data_dir("workspaces", "myws", "agents", "myagent")
        self.assertTrue(
            result.startswith(DATA_DIR + os.sep) or result == DATA_DIR,
            f"Path {result} does not start with DATA_DIR {DATA_DIR}",
        )

    def test_normpath_traversal_caught(self):
        """Even with validate_parts=False, path-escape is caught by normpath check."""
        # Construct a path that normpath would resolve outside DATA_DIR
        # This tests the second safety layer (the normpath check)
        with self.assertRaises(HTTPException) as ctx:
            _safe_join_data_dir("..", "..", "etc", "passwd", validate_parts=False)
        self.assertEqual(ctx.exception.status_code, 400)


class TestValidatePathComponent(unittest.TestCase):
    """Additional tests for _validate_path_component."""

    def test_normal_name_passes(self):
        """A simple alphanumeric name should pass validation."""
        result = _validate_path_component("my_workspace_123", "workspace_id")
        self.assertEqual(result, "my_workspace_123")

    def test_dotdot_rejected(self):
        with self.assertRaises(HTTPException):
            _validate_path_component("foo..bar", "test")

    def test_slash_rejected(self):
        with self.assertRaises(HTTPException):
            _validate_path_component("foo/bar", "test")


class TestNoRawExceptionInResponses(unittest.TestCase):
    """3: Endpoints no longer return raw exception text to callers.

    We verify that the known exception-catching patterns in app.py use
    generic messages rather than str(exc).
    """

    def test_no_str_exc_in_http_responses(self):
        """Scan app.py source for str(exc) or str(e) in HTTPException detail or error fields.

        This is a source-level assertion: any str(exc) usage in an HTTPException
        detail= parameter or an 'error' dict value is a regression.
        """
        import inspect
        import re

        source = inspect.getsource(sys.modules['torment_service.app'])

        # Find lines that have both 'HTTPException' and 'str(exc)' or 'str(e)'
        # Pattern: detail=str(exc) or detail=str(e) in raise HTTPException
        http_exc_pattern = re.compile(r'raise\s+HTTPException\(.*detail\s*=\s*str\(')
        matches = http_exc_pattern.findall(source)
        self.assertEqual(
            len(matches), 0,
            f"Found {len(matches)} HTTPException(detail=str(...)) patterns — "
            f"raw exception text should not be exposed to callers",
        )

        # Also check for "error": str(exc) in return dicts
        error_dict_pattern = re.compile(r'"error"\s*:\s*str\(exc\)')
        error_matches = error_dict_pattern.findall(source)
        self.assertEqual(
            len(error_matches), 0,
            f"Found {len(error_matches)} 'error': str(exc) patterns — "
            f"raw exception text should not be exposed in JSON responses",
        )

    def test_cognition_run_returns_generic_pipeline_failure(self):
        """The cognition endpoint must not pass pipeline error text to clients."""
        import inspect

        source = inspect.getsource(sys.modules['torment_service.app'])
        self.assertNotIn('detail=result.get("error"', source)
        self.assertIn('detail="Cognition pipeline failed"', source)

    def test_no_f_string_exc_in_http_detail(self):
        """Check that f-string interpolation of {exc} is not used in HTTPException detail."""
        import inspect
        import re

        source = inspect.getsource(sys.modules['torment_service.app'])
        # Pattern: detail=f"...{exc}..." or detail=f"...{e}..."
        fstring_pattern = re.compile(r'detail\s*=\s*f["\'].*\{exc\}')
        matches = fstring_pattern.findall(source)
        self.assertEqual(
            len(matches), 0,
            f"Found {len(matches)} detail=f'...{{exc}}...' patterns — "
            f"exception text should not be interpolated into HTTP details",
        )


class TestSafeLogValue(unittest.TestCase):
    """4: _safe_log_value escapes CR/LF on logged user-derived values."""

    def test_escapes_newline(self):
        result = _safe_log_value("hello\nworld")
        self.assertNotIn("\n", result)
        self.assertIn("\\n", result)

    def test_escapes_carriage_return(self):
        result = _safe_log_value("hello\rworld")
        self.assertNotIn("\r", result)
        self.assertIn("\\r", result)

    def test_escapes_crlf(self):
        result = _safe_log_value("line1\r\nline2")
        self.assertNotIn("\r", result)
        self.assertNotIn("\n", result)
        self.assertEqual(result, "line1\\r\\nline2")

    def test_passthrough_clean_string(self):
        result = _safe_log_value("clean_workspace_id_123")
        self.assertEqual(result, "clean_workspace_id_123")

    def test_handles_non_string_input(self):
        """_safe_log_value should handle non-string input via str() coercion."""
        result = _safe_log_value(12345)
        self.assertEqual(result, "12345")


class _CognitionDummyFabric:
    private_graphs = {}

    def get_workspace(self, workspace_id):
        return SimpleNamespace(domains=[])

    def create_agent(self, workspace_id, agent_id):
        return SimpleNamespace(seed={}, overlay={}, agent_id=agent_id)

    def ingest(self, *args, **kwargs):
        return {"ok": True}

    def _agent_key(self, workspace_id, agent_id):
        return f"{workspace_id}:{agent_id}"


def _run_cognition_with_result(monkeypatch, result):
    import cognition.pipeline as pipeline

    monkeypatch.setattr(appmod, "fabric", _CognitionDummyFabric())
    monkeypatch.setattr(pipeline, "run_cognition_pipeline", lambda **kwargs: result)
    req = appmod.CognitionRunReq(workspace_id="ws", agent_id="agent", user_input="hello")
    return appmod.cognition_run(req)


def test_cognition_status_error_returns_generic_pipeline_failure(monkeypatch):
    result = {"ok": False, "status": "error", "error": "SECRET\nTRACE"}

    with pytest.raises(HTTPException) as ctx:
        _run_cognition_with_result(monkeypatch, result)

    assert ctx.value.status_code == 500
    assert ctx.value.detail == "Cognition pipeline failed"
    assert "SECRET" not in str(ctx.value.detail)
    assert "TRACE" not in str(ctx.value.detail)


def test_cognition_success_scrubs_internal_error_field(monkeypatch):
    result = {
        "ok": True,
        "status": "partial",
        "final_answer": "normal answer",
        "error": "SECRET\nTRACE",
        "normal": {"kept": True},
    }

    response = _run_cognition_with_result(monkeypatch, result)

    assert response["final_answer"] == "normal answer"
    assert response["normal"] == {"kept": True}
    assert response["error"] == "Cognition pipeline failed"
    encoded = json.dumps(response)
    assert "SECRET" not in encoded
    assert "TRACE" not in encoded


def test_cognition_success_scrubs_traceback_stack_like_fields(monkeypatch):
    result = {
        "ok": True,
        "final_answer": "normal answer",
        "traceback": "LEAKME traceback",
        "stack": "LEAKME stack",
        "nested": {
            "stacktrace": "LEAKME stacktrace",
            "items": [{"exception": "LEAKME exception"}],
            "kept": "safe value",
        },
    }

    response = _run_cognition_with_result(monkeypatch, result)

    assert response["final_answer"] == "normal answer"
    assert response["traceback"] == "Cognition pipeline failed"
    assert response["stack"] == "Cognition pipeline failed"
    assert response["nested"]["stacktrace"] == "Cognition pipeline failed"
    assert response["nested"]["items"][0]["exception"] == "Cognition pipeline failed"
    assert response["nested"]["kept"] == "safe value"
    assert "LEAKME" not in json.dumps(response)


if __name__ == "__main__":
    unittest.main()
