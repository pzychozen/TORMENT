"""Security regression tests for spirit_reflection.py.

Covers CodeQL findings:
  - Path traversal / escape in SpiritReflectionStore
  - Log injection via newline characters in guard reasons
  - Unused import / variable cleanup verification
"""
from __future__ import annotations

import logging
import os
import shutil
import tempfile
from pathlib import Path

import pytest

from torment_service.spirit_reflection import (
    SpiritReflectionStore,
    _ensure_within_base,
    _safe_log_value,
)


@pytest.fixture
def base_dir():
    d = tempfile.mkdtemp(prefix="torment_sr_sec_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


# -------------------------------------------------------------------
# 1. Path traversal / escape rejection
# -------------------------------------------------------------------


class TestPathSanitization:
    def test_traversal_rejected(self, base_dir):
        """Paths containing '../' that escape base_dir must be rejected."""
        evil_path = os.path.join(base_dir, "legit", "..", "..", "etc", "passwd")
        with pytest.raises(ValueError, match="escapes base directory"):
            SpiritReflectionStore(Path(evil_path), base_dir=base_dir)

    def test_absolute_escape_rejected(self, base_dir):
        """An absolute path outside base_dir must be rejected."""
        with pytest.raises(ValueError, match="escapes base directory"):
            SpiritReflectionStore(Path("/tmp/evil_reflections"), base_dir=base_dir)

    def test_symlink_escape_rejected(self, base_dir):
        """A symlink pointing outside base_dir must be rejected."""
        outside = tempfile.mkdtemp(prefix="torment_outside_")
        try:
            link = os.path.join(base_dir, "sneaky_link")
            os.symlink(outside, link)
            with pytest.raises(ValueError, match="escapes base directory"):
                SpiritReflectionStore(Path(link), base_dir=base_dir)
        finally:
            shutil.rmtree(outside, ignore_errors=True)

    def test_valid_path_accepted(self, base_dir):
        """A legitimate sub-path inside base_dir should work."""
        safe_path = os.path.join(base_dir, "agents", "a1", "spirit_reflections")
        store = SpiritReflectionStore(Path(safe_path), base_dir=base_dir)
        # Verify the directory was created
        assert store._dir.exists()
        assert str(store._dir).startswith(os.path.realpath(base_dir))

    def test_ensure_within_base_returns_resolved_path(self, base_dir):
        """_ensure_within_base should return a fully resolved Path."""
        sub = os.path.join(base_dir, "a", "b", "..", "b")
        result = _ensure_within_base(sub, base_dir)
        # Should be resolved (no '..')
        assert ".." not in str(result)
        assert isinstance(result, Path)

    def test_reflections_file_also_validated(self, base_dir):
        """The reflections.jsonl file path should also be within base_dir."""
        safe_path = os.path.join(base_dir, "reflections")
        store = SpiritReflectionStore(Path(safe_path), base_dir=base_dir)
        assert str(store._file).startswith(os.path.realpath(base_dir))


# -------------------------------------------------------------------
# 2. Log injection sanitization
# -------------------------------------------------------------------


class TestLogSanitization:
    def test_newline_stripped(self):
        """Newline characters must be escaped to prevent log injection."""
        malicious = "benign reason\nINFO injected log line"
        sanitized = _safe_log_value(malicious)
        assert "\n" not in sanitized
        assert "\\n" in sanitized

    def test_carriage_return_stripped(self):
        """Carriage returns must be escaped."""
        malicious = "benign\rINFO injected"
        sanitized = _safe_log_value(malicious)
        assert "\r" not in sanitized
        assert "\\r" in sanitized

    def test_combined_crlf(self):
        """CRLF sequence must be fully escaped."""
        malicious = "ok\r\nERROR fake"
        sanitized = _safe_log_value(malicious)
        assert "\r" not in sanitized
        assert "\n" not in sanitized

    def test_safe_values_unchanged(self):
        """Normal strings pass through unchanged."""
        assert _safe_log_value("cooldown_active (gap=5, need=50)") == \
            "cooldown_active (gap=5, need=50)"
        assert _safe_log_value(42) == "42"

    def test_log_output_sanitized(self, base_dir, caplog):
        """Verify that process_spirit_reflections actually uses sanitized
        log output when rejecting a candidate."""
        from torment_service.spirit_reflection import (
            process_spirit_reflections,
        )
        safe_path = os.path.join(base_dir, "reflections")
        store = SpiritReflectionStore(Path(safe_path), base_dir=base_dir)

        # Build a candidate that will be rejected (influence too low)
        block = {
            "from_spirit_return": True,
            "eid": 999,
            "summary": "x",
            "spirit_return_mode": "recollection",
            "spirit_return_flavor": "",
            "warmth_score": 0.0,
            "symbol_interaction": "neutral",
        }

        with caplog.at_level(logging.DEBUG, logger="torment_service.spirit_reflection"):
            process_spirit_reflections(
                blocks=[block],
                response_text="completely unrelated response",
                query_text="test query",
                current_step=1,
                store=store,
                influence_threshold=0.99,  # force rejection
            )

        # The rejection log line should not contain raw newlines
        for record in caplog.records:
            assert "\n" not in record.getMessage(), (
                f"Raw newline in log: {record.getMessage()!r}"
            )


# -------------------------------------------------------------------
# 3. Cleanup verification — unused import removed
# -------------------------------------------------------------------


class TestCleanup:
    def test_no_unused_field_import(self):
        """The unused 'field' import from dataclasses should be removed."""
        import torment_service.spirit_reflection as mod
        import inspect
        source = inspect.getsource(mod)
        # 'field' should not appear in a dataclass import line
        import re
        imports = [l for l in source.splitlines()
                   if l.startswith("from dataclasses")]
        for line in imports:
            assert "field" not in line, (
                f"Unused 'field' import still present: {line}"
            )
