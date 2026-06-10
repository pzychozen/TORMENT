"""Security regression tests for spirit_return.py WarmupTracker.

Covers the four HIGH CodeQL py/path-injection findings (alerts #150/#151/
#840/#529) by asserting that WarmupTracker derives every stored path from a
containment sanitizer (pathing.ensure_within_base), exactly like the already-
hardened sibling SpiritReflectionStore (see test_spirit_reflection_security.py).

Scope: path-integrity only. No behavior/persistence-format tests beyond what is
needed to prove containment of the warmup_state.jsonl sinks and the compaction
temp file.
"""
from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

import pytest

from torment_service.spirit_return import WarmupTracker
from torment_service.pathing import ensure_within_base


@pytest.fixture
def base_dir():
    d = tempfile.mkdtemp(prefix="torment_warmup_sec_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


# -------------------------------------------------------------------
# 1. Path traversal / escape rejection
# -------------------------------------------------------------------


class TestPathSanitization:
    def test_traversal_rejected(self, base_dir):
        """Paths containing '../' that escape base_dir must be rejected."""
        evil_path = os.path.join(base_dir, "legit", "..", "..", "etc", "warmup")
        with pytest.raises(ValueError, match="escapes base directory"):
            WarmupTracker(Path(evil_path), base_dir=base_dir)

    def test_absolute_escape_rejected(self, base_dir):
        """An absolute path outside base_dir must be rejected."""
        with pytest.raises(ValueError, match="escapes base directory"):
            WarmupTracker(Path("/tmp/evil_warmup"), base_dir=base_dir)

    def test_symlink_escape_rejected(self, base_dir):
        """A symlink pointing outside base_dir must be rejected (POSIX).

        Skipped where symlink creation is not permitted (e.g. unprivileged
        Windows), since the escape is resolved by realpath at construction.
        """
        outside = tempfile.mkdtemp(prefix="torment_outside_")
        link = os.path.join(base_dir, "sneaky_link")
        try:
            try:
                os.symlink(outside, link)
            except (OSError, NotImplementedError):
                pytest.skip("symlink creation not permitted on this platform")
            with pytest.raises(ValueError, match="escapes base directory"):
                WarmupTracker(Path(link), base_dir=base_dir)
        finally:
            shutil.rmtree(outside, ignore_errors=True)

    def test_valid_path_accepted(self, base_dir):
        """A legitimate sub-path inside base_dir should work."""
        safe_path = os.path.join(base_dir, "workspaces", "ws1", "agents", "a1", "warmup")
        tracker = WarmupTracker(Path(safe_path), base_dir=base_dir)
        assert tracker.storage_path.exists()
        assert str(tracker.storage_path).startswith(os.path.realpath(base_dir))

    def test_warmup_file_validated_and_contained(self, base_dir):
        """The warmup_state.jsonl file path must be validated and within base."""
        safe_path = os.path.join(base_dir, "warmup")
        tracker = WarmupTracker(Path(safe_path), base_dir=base_dir)
        assert tracker._file.name == "warmup_state.jsonl"
        assert str(tracker._file).startswith(os.path.realpath(base_dir))

    def test_resolved_path_posture(self, base_dir):
        """Stored paths must be fully resolved (no '..' segments)."""
        sub = os.path.join(base_dir, "a", "b", "..", "b", "warmup")
        tracker = WarmupTracker(Path(sub), base_dir=base_dir)
        assert ".." not in str(tracker.storage_path)
        assert ".." not in str(tracker._file)
        # ensure_within_base must agree the resolved path is contained
        resolved = ensure_within_base(str(tracker.storage_path), base_dir)
        assert str(tracker.storage_path) == str(resolved)

    def test_windows_backslash_component_contained_or_rejected(self, base_dir):
        """A component containing a backslash must not escape base_dir.

        On Windows a backslash is a separator (may resolve to an escape →
        ValueError); on POSIX it is a literal filename character (stays
        contained). Either outcome is acceptable; a silent escape is not.
        """
        weird = os.path.join(base_dir, "warmup", "..\\..\\outside")
        try:
            tracker = WarmupTracker(Path(weird), base_dir=base_dir)
        except ValueError:
            return  # rejected — acceptable
        # accepted → must remain contained
        assert str(tracker.storage_path).startswith(os.path.realpath(base_dir))
        assert str(tracker._file).startswith(os.path.realpath(base_dir))


# -------------------------------------------------------------------
# 2. Compaction temp-file containment
# -------------------------------------------------------------------


class TestCompactionContainment:
    def test_compaction_tmpfile_contained(self, base_dir):
        """The compaction temp file path must remain inside base_dir, and
        compaction on a valid store must not raise or escape."""
        safe_path = os.path.join(base_dir, "warmup")
        tracker = WarmupTracker(Path(safe_path), base_dir=base_dir)

        # The temp path the compactor derives must be contained.
        tmp_expected = tracker._file.with_suffix(".jsonl.tmp")
        assert str(os.path.realpath(tmp_expected)).startswith(os.path.realpath(base_dir))

        # Exercise the real path: write a few states, then compact.
        for eid in range(5):
            tracker.get_or_create(eid, current_step=eid)
        summary = tracker.compact()
        assert isinstance(summary, dict)
        # File (if present) stays inside base.
        assert str(tracker._file).startswith(os.path.realpath(base_dir))
