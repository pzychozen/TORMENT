# tests/test_incident_log.py — Unit tests for the Spine incident log
#
# Validates:
#   1. SpineIncident dataclass and is_failure() logic
#   2. IncidentLog.record() — basic recording and counter tracking
#   3. IncidentLog.query() — all filter parameters
#   4. IncidentLog.summary() — aggregate stats and block list
#   5. Ring buffer eviction when max_size exceeded
#   6. Thread-safety under concurrent writes
#   7. JSONL file persistence (file_path mode)
#   8. Module-level singleton and log_spine_decision() helper
# ---------------------------------------------------------------------------
from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
import time
import unittest

# Ensure project root is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.incident_log import (
    SpineIncident,
    IncidentLog,
    get_incident_log,
    log_spine_decision,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_incident(
    operation: str = "ingest",
    decision_code: str = "fast_allowed",
    result_code: str = "stored",
    ok: bool = True,
    workspace_id: str = "ws1",
    agent_id: str = "a1",
    trust_tier: float = 0.6,
    drift_status: str = "green",
    path: str = "fast",
    elapsed_ms: float = 1.5,
    escalated: bool = False,
    escalation_reasons: list = None,
    reason: str = "",
    timestamp: float = None,
    client_id: str = "",
    session_id: str = "",
    task_id: str = "",
) -> SpineIncident:
    return SpineIncident(
        timestamp=timestamp or time.time(),
        operation=operation,
        decision_code=decision_code,
        result_code=result_code,
        ok=ok,
        workspace_id=workspace_id,
        agent_id=agent_id,
        trust_tier=trust_tier,
        drift_status=drift_status,
        path=path,
        elapsed_ms=elapsed_ms,
        escalated=escalated,
        escalation_reasons=escalation_reasons or [],
        reason=reason,
        client_id=client_id,
        session_id=session_id,
        task_id=task_id,
    )


# ---------------------------------------------------------------------------
# Tests: SpineIncident dataclass
# ---------------------------------------------------------------------------

class TestSpineIncident(unittest.TestCase):
    """Test SpineIncident dataclass behaviour."""

    def test_successful_incident_not_failure(self):
        inc = _make_incident(ok=True, decision_code="fast_allowed")
        self.assertFalse(inc.is_failure())

    def test_blocked_trust_is_failure(self):
        inc = _make_incident(ok=False, decision_code="blocked_insufficient_trust")
        self.assertTrue(inc.is_failure())

    def test_blocked_unknown_op_is_failure(self):
        inc = _make_incident(ok=False, decision_code="blocked_unknown_operation")
        self.assertTrue(inc.is_failure())

    def test_error_dispatch_is_failure(self):
        inc = _make_incident(ok=False, decision_code="error_dispatch")
        self.assertTrue(inc.is_failure())

    def test_ok_false_always_failure(self):
        """Even with a non-block decision code, ok=False means failure."""
        inc = _make_incident(ok=False, decision_code="fast_allowed")
        self.assertTrue(inc.is_failure())

    def test_to_dict_roundtrip(self):
        inc = _make_incident(
            operation="query_memory",
            escalated=True,
            escalation_reasons=["identity_sensitive"],
            reason="test",
        )
        d = inc.to_dict()
        self.assertIsInstance(d, dict)
        self.assertEqual(d["operation"], "query_memory")
        self.assertTrue(d["escalated"])
        self.assertEqual(d["escalation_reasons"], ["identity_sensitive"])
        self.assertEqual(d["reason"], "test")

    def test_default_fields(self):
        inc = _make_incident()
        self.assertEqual(inc.escalated, False)
        self.assertEqual(inc.escalation_reasons, [])
        self.assertEqual(inc.reason, "")
        self.assertEqual(inc.client_id, "")
        self.assertEqual(inc.session_id, "")


# ---------------------------------------------------------------------------
# Tests: IncidentLog core operations
# ---------------------------------------------------------------------------

class TestIncidentLogRecord(unittest.TestCase):
    """Test IncidentLog.record() and counter tracking."""

    def test_record_single(self):
        log = IncidentLog(max_size=100)
        inc = _make_incident()
        log.record(inc)
        self.assertEqual(log._total_logged, 1)
        self.assertEqual(log._total_failures, 0)

    def test_record_failure_counted(self):
        log = IncidentLog(max_size=100)
        log.record(_make_incident(ok=True))
        log.record(_make_incident(ok=False, decision_code="blocked_insufficient_trust"))
        log.record(_make_incident(ok=False, decision_code="error_dispatch"))
        self.assertEqual(log._total_logged, 3)
        self.assertEqual(log._total_failures, 2)

    def test_record_multiple(self):
        log = IncidentLog(max_size=100)
        for i in range(50):
            log.record(_make_incident(timestamp=1000.0 + i))
        self.assertEqual(log._total_logged, 50)

    def test_clear_empties_buffer(self):
        log = IncidentLog(max_size=100)
        for _ in range(10):
            log.record(_make_incident())
        log.clear()
        self.assertEqual(len(log._buffer), 0)
        # Counters remain (they track lifetime, not current buffer)
        self.assertEqual(log._total_logged, 10)


# ---------------------------------------------------------------------------
# Tests: Ring buffer eviction
# ---------------------------------------------------------------------------

class TestRingBuffer(unittest.TestCase):
    """Test that the ring buffer evicts oldest entries when full."""

    def test_eviction_at_max_size(self):
        log = IncidentLog(max_size=5)
        for i in range(10):
            log.record(_make_incident(timestamp=1000.0 + i))
        # Only 5 most recent should remain
        self.assertEqual(len(log._buffer), 5)
        self.assertEqual(log._buffer[0].timestamp, 1005.0)
        self.assertEqual(log._buffer[-1].timestamp, 1009.0)

    def test_total_logged_counts_all(self):
        """total_logged counts ALL records, even evicted ones."""
        log = IncidentLog(max_size=3)
        for i in range(10):
            log.record(_make_incident())
        self.assertEqual(log._total_logged, 10)
        self.assertEqual(len(log._buffer), 3)


# ---------------------------------------------------------------------------
# Tests: IncidentLog.query() with filters
# ---------------------------------------------------------------------------

class TestIncidentLogQuery(unittest.TestCase):
    """Test the query() method with various filters."""

    def setUp(self):
        self.log = IncidentLog(max_size=500)
        # Record a variety of incidents
        self.log.record(_make_incident(
            timestamp=1000.0, operation="ingest", ok=True,
            decision_code="fast_allowed", workspace_id="ws1", agent_id="a1",
        ))
        self.log.record(_make_incident(
            timestamp=1001.0, operation="query_memory", ok=True,
            decision_code="fast_allowed", workspace_id="ws1", agent_id="a2",
        ))
        self.log.record(_make_incident(
            timestamp=1002.0, operation="ingest", ok=False,
            decision_code="blocked_insufficient_trust",
            workspace_id="ws2", agent_id="a1", reason="trust too low",
        ))
        self.log.record(_make_incident(
            timestamp=1003.0, operation="query_memory", ok=True,
            decision_code="escalated_full", workspace_id="ws1", agent_id="a1",
            escalated=True, escalation_reasons=["identity_sensitive"],
        ))
        self.log.record(_make_incident(
            timestamp=1004.0, operation="feedback", ok=True,
            decision_code="fast_allowed", workspace_id="ws1", agent_id="a1",
        ))

    def test_query_all(self):
        results = self.log.query(limit=100)
        self.assertEqual(len(results), 5)
        # Most recent first
        self.assertEqual(results[0].timestamp, 1004.0)
        self.assertEqual(results[-1].timestamp, 1000.0)

    def test_query_limit(self):
        results = self.log.query(limit=2)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].timestamp, 1004.0)

    def test_query_by_operation(self):
        results = self.log.query(operation="ingest")
        self.assertEqual(len(results), 2)
        for r in results:
            self.assertEqual(r.operation, "ingest")

    def test_query_by_decision_code(self):
        results = self.log.query(decision_code="blocked_insufficient_trust")
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0].ok)

    def test_query_by_ok(self):
        results = self.log.query(ok=False)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].decision_code, "blocked_insufficient_trust")

    def test_query_by_workspace(self):
        results = self.log.query(workspace_id="ws2")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].workspace_id, "ws2")

    def test_query_by_agent(self):
        results = self.log.query(agent_id="a2")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].agent_id, "a2")

    def test_query_since(self):
        results = self.log.query(since=1002.5)
        self.assertEqual(len(results), 2)
        for r in results:
            self.assertGreaterEqual(r.timestamp, 1002.5)

    def test_query_failures_only(self):
        results = self.log.query(failures_only=True)
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].is_failure())

    def test_query_combined_filters(self):
        results = self.log.query(operation="ingest", workspace_id="ws1")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].workspace_id, "ws1")
        self.assertEqual(results[0].operation, "ingest")

    def test_query_no_matches(self):
        results = self.log.query(operation="nonexistent")
        self.assertEqual(len(results), 0)

    def test_query_empty_log(self):
        empty_log = IncidentLog(max_size=100)
        results = empty_log.query()
        self.assertEqual(len(results), 0)


# ---------------------------------------------------------------------------
# Tests: IncidentLog.summary()
# ---------------------------------------------------------------------------

class TestIncidentLogSummary(unittest.TestCase):
    """Test the summary() aggregate stats."""

    def test_empty_summary(self):
        log = IncidentLog(max_size=100)
        s = log.summary()
        self.assertEqual(s["total_logged"], 0)
        self.assertEqual(s["total_failures"], 0)
        self.assertEqual(s["buffer_size"], 0)
        self.assertEqual(s["recent_decisions"], {})
        self.assertEqual(s["recent_blocks"], [])

    def test_summary_counts_decisions(self):
        log = IncidentLog(max_size=100)
        log.record(_make_incident(decision_code="fast_allowed"))
        log.record(_make_incident(decision_code="fast_allowed"))
        log.record(_make_incident(decision_code="escalated_full"))
        s = log.summary()
        self.assertEqual(s["total_logged"], 3)
        self.assertEqual(s["buffer_size"], 3)
        self.assertEqual(s["recent_decisions"]["fast_allowed"], 2)
        self.assertEqual(s["recent_decisions"]["escalated_full"], 1)

    def test_summary_captures_blocks(self):
        log = IncidentLog(max_size=100)
        log.record(_make_incident(ok=True, decision_code="fast_allowed"))
        log.record(_make_incident(
            ok=False, decision_code="blocked_insufficient_trust",
            reason="trust 0.1 < 0.4", workspace_id="ws_test", agent_id="atlas",
            trust_tier=0.1,
        ))
        s = log.summary()
        self.assertEqual(s["total_failures"], 1)
        self.assertEqual(len(s["recent_blocks"]), 1)
        block = s["recent_blocks"][0]
        self.assertEqual(block["decision_code"], "blocked_insufficient_trust")
        self.assertEqual(block["workspace_id"], "ws_test")
        self.assertEqual(block["agent_id"], "atlas")

    def test_summary_limits_blocks_to_10(self):
        log = IncidentLog(max_size=500)
        for i in range(20):
            log.record(_make_incident(
                ok=False, decision_code="blocked_insufficient_trust",
                timestamp=1000.0 + i,
            ))
        s = log.summary()
        self.assertLessEqual(len(s["recent_blocks"]), 10)

    def test_summary_has_timestamps(self):
        log = IncidentLog(max_size=100)
        log.record(_make_incident(timestamp=1000.0))
        log.record(_make_incident(timestamp=2000.0))
        s = log.summary()
        self.assertEqual(s["oldest_timestamp"], 1000.0)
        self.assertEqual(s["newest_timestamp"], 2000.0)


# ---------------------------------------------------------------------------
# Tests: JSONL file persistence
# ---------------------------------------------------------------------------

class TestJSONLPersistence(unittest.TestCase):
    """Test optional JSONL file append mode."""

    def test_file_append_on_record(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            path = f.name

        try:
            log = IncidentLog(max_size=100, file_path=path)
            log.record(_make_incident(operation="ingest", workspace_id="ws_file"))
            log.record(_make_incident(operation="query_memory", workspace_id="ws_file"))

            with open(path, "r") as f:
                lines = f.readlines()

            self.assertEqual(len(lines), 2)

            # Each line is valid JSON
            for line in lines:
                data = json.loads(line)
                self.assertIn("operation", data)
                self.assertIn("workspace_id", data)
                self.assertEqual(data["workspace_id"], "ws_file")
        finally:
            os.unlink(path)

    def test_file_append_contains_all_fields(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            path = f.name

        try:
            log = IncidentLog(max_size=100, file_path=path)
            log.record(_make_incident(
                operation="ingest",
                decision_code="fast_allowed",
                result_code="stored",
                ok=True,
                escalated=True,
                escalation_reasons=["identity_sensitive"],
                reason="test reason",
                client_id="cl1",
                session_id="sess1",
                task_id="t1",
            ))

            with open(path, "r") as f:
                data = json.loads(f.readline())

            self.assertEqual(data["operation"], "ingest")
            self.assertEqual(data["decision_code"], "fast_allowed")
            self.assertTrue(data["escalated"])
            self.assertEqual(data["escalation_reasons"], ["identity_sensitive"])
            self.assertEqual(data["client_id"], "cl1")
            self.assertEqual(data["task_id"], "t1")
        finally:
            os.unlink(path)

    def test_file_path_none_no_file_created(self):
        """With no file_path, no file is created."""
        log = IncidentLog(max_size=100, file_path=None)
        log.record(_make_incident())
        self.assertEqual(log._total_logged, 1)

    def test_bad_file_path_does_not_crash(self):
        """Bad file path should be silently ignored (observability must never crash)."""
        log = IncidentLog(max_size=100, file_path="/nonexistent/dir/incidents.jsonl")
        # Should not raise
        log.record(_make_incident())
        self.assertEqual(log._total_logged, 1)


# ---------------------------------------------------------------------------
# Tests: Thread safety
# ---------------------------------------------------------------------------

class TestThreadSafety(unittest.TestCase):
    """Basic thread-safety validation for concurrent writes."""

    def test_concurrent_writes(self):
        log = IncidentLog(max_size=1000)
        barrier = threading.Barrier(10)

        def writer(thread_id):
            barrier.wait()
            for i in range(100):
                log.record(_make_incident(
                    agent_id=f"agent_{thread_id}",
                    timestamp=1000.0 + thread_id * 100 + i,
                ))

        threads = [threading.Thread(target=writer, args=(t,)) for t in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(log._total_logged, 1000)
        self.assertEqual(len(log._buffer), 1000)

    def test_concurrent_writes_with_eviction(self):
        """Ensure no corruption when buffer wraps under contention."""
        log = IncidentLog(max_size=50)
        barrier = threading.Barrier(5)

        def writer(thread_id):
            barrier.wait()
            for i in range(100):
                log.record(_make_incident(agent_id=f"agent_{thread_id}"))

        threads = [threading.Thread(target=writer, args=(t,)) for t in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(log._total_logged, 500)
        self.assertEqual(len(log._buffer), 50)


# ---------------------------------------------------------------------------
# Tests: Module-level singleton (get_incident_log)
# ---------------------------------------------------------------------------

class TestModuleSingleton(unittest.TestCase):
    """Test the module-level singleton accessor."""

    def test_get_incident_log_returns_same_instance(self):
        # Reset the module-level singleton for clean test
        mod = sys.modules["torment_service.incident_log"]
        old = mod._incident_log
        mod._incident_log = None
        try:
            log1 = get_incident_log()
            log2 = get_incident_log()
            self.assertIs(log1, log2)
        finally:
            mod._incident_log = old

    def test_env_var_enables_file_persistence(self):
        """TORMENT_MCP_INCIDENT_LOG env var wires up JSONL persistence."""
        mod = sys.modules["torment_service.incident_log"]
        old = mod._incident_log
        mod._incident_log = None

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            path = f.name

        try:
            os.environ["TORMENT_MCP_INCIDENT_LOG"] = path
            log = get_incident_log()
            log.record(_make_incident(operation="env_var_test"))

            with open(path, "r") as f:
                lines = f.readlines()
            self.assertEqual(len(lines), 1)
            data = json.loads(lines[0])
            self.assertEqual(data["operation"], "env_var_test")
        finally:
            os.environ.pop("TORMENT_MCP_INCIDENT_LOG", None)
            mod._incident_log = old
            os.unlink(path)

    def test_no_env_var_no_file(self):
        """Without the env var, no file persistence."""
        mod = sys.modules["torment_service.incident_log"]
        old = mod._incident_log
        mod._incident_log = None
        os.environ.pop("TORMENT_MCP_INCIDENT_LOG", None)
        try:
            log = get_incident_log()
            self.assertIsNone(log._file_path)
        finally:
            mod._incident_log = old


# ---------------------------------------------------------------------------
# Tests: log_spine_decision() helper
# ---------------------------------------------------------------------------

class TestLogSpineDecision(unittest.TestCase):
    """Test the log_spine_decision() convenience function."""

    def test_log_spine_decision_records_incident(self):
        mod = sys.modules["torment_service.incident_log"]
        old = mod._incident_log
        mod._incident_log = IncidentLog(max_size=100)
        try:
            # Build mock-like response, request, context objects
            class MockResp:
                operation = "ingest"
                decision_code = "fast_allowed"
                result_code = "stored"
                ok = True
                workspace_id = "ws_test"
                agent_id = "a_test"
                trust_tier = 0.6
                drift_status = "green"
                path = "fast"
                elapsed_ms = 2.3
                escalated = False
                escalation_reasons = []
                reason = ""
                task_id = "t123"

            class MockReq:
                pass

            class MockCtx:
                client_id = "test_client"
                session_id = "sess_test"

            log_spine_decision(MockResp(), MockReq(), MockCtx())

            log = get_incident_log()
            results = log.query(limit=1)
            self.assertEqual(len(results), 1)
            inc = results[0]
            self.assertEqual(inc.operation, "ingest")
            self.assertEqual(inc.decision_code, "fast_allowed")
            self.assertEqual(inc.workspace_id, "ws_test")
            self.assertEqual(inc.client_id, "test_client")
        finally:
            mod._incident_log = old


if __name__ == "__main__":
    unittest.main()
