# tests/test_hardening.py — Phase 2.7 real-host hardening tests
#
# Simulates the kinds of things that go wrong in practice:
#
#   A. Weird inputs — empty strings, huge payloads, unicode/special chars,
#      null-ish values, wrong types, negative numbers
#   B. Missing/incorrect context — no workspace, no agent, workspace that
#      doesn't exist, agent that doesn't exist, trust edge cases
#   C. Tier 2 intentionally blocked — guarded operations rejected when
#      exposure is "open" only, internal ops always rejected
#   D. Status surface verification — after a barrage of weird requests,
#      does /spine/status accurately answer "what just happened?"
#
# All tests use real Fabric instances with hash embeddings.
# ---------------------------------------------------------------------------
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("TORMENT_EMBED_PROVIDER", "hash")

from torment_service.spine import (
    SpineRequest,
    SpineResponse,
    submit_task,
    OPERATION_REGISTRY,
    get_exposed_operations,
    EXPOSURE_OPEN,
    EXPOSURE_GUARDED,
    DECISION_FAST_ALLOWED,
    DECISION_BLOCKED_UNKNOWN_OP,
    DECISION_BLOCKED_TRUST,
    DECISION_BLOCKED_NO_HANDLER,
    DECISION_ERROR_DISPATCH,
)
from torment_service.request_context import (
    RequestContext,
    TRUST_INGEST,
    TRUST_OPERATOR,
)
from torment_service.fabric import TormentFabric
from torment_service.incident_log import IncidentLog, get_incident_log
incident_mod = sys.modules["torment_service.incident_log"]


# ---------------------------------------------------------------------------
# Shared test fixtures
# ---------------------------------------------------------------------------

_fabric = None
_ws = "ws_hardening"
_agent = "atlas_hard"


def _get_fabric():
    global _fabric
    if _fabric is None:
        _fabric = TormentFabric(data_dir=":memory:")
        # get_workspace creates lazily; create_agent ensures agent state exists
        _fabric.get_workspace(_ws)
        _fabric.create_agent(_ws, _agent)
    return _fabric


def _submit(operation, payload, trust=0.6, mode="auto",
            workspace_id=None, agent_id=None):
    """Helper: submit a SpineRequest and return the SpineResponse."""
    fab = _get_fabric()
    ws = workspace_id if workspace_id is not None else _ws
    ag = agent_id if agent_id is not None else _agent
    ctx = RequestContext(
        client_id="hardening_test",
        trust_tier=trust,
        workspace_id=ws,
        agent_id=ag,
    )
    req = SpineRequest(
        workspace_id=ws,
        agent_id=ag,
        operation=operation,
        payload=payload,
        mode=mode,
    )
    return submit_task(req, fab, ctx)


def _reset_incident_log():
    incident_mod._incident_log = IncidentLog(max_size=500)
    return incident_mod._incident_log


# ===========================================================================
# A. Weird inputs
# ===========================================================================

class TestWeirdInputs(unittest.TestCase):
    """Test Spine resilience to unusual/malformed inputs."""

    def setUp(self):
        _reset_incident_log()

    # --- Empty / minimal inputs ---

    def test_ingest_empty_text(self):
        """Empty text should not crash; Fabric may store an empty memory."""
        resp = _submit("ingest", {"text": "", "step": 0})
        # Should not crash. Whether it succeeds or fails gracefully is OK.
        self.assertIsInstance(resp, SpineResponse)
        self.assertIn(resp.decision_code, (
            DECISION_FAST_ALLOWED, DECISION_ERROR_DISPATCH,
        ))

    def test_ingest_whitespace_only(self):
        resp = _submit("ingest", {"text": "   \n\t  ", "step": 0})
        self.assertIsInstance(resp, SpineResponse)

    def test_ingest_missing_text_key(self):
        """Payload with no 'text' key — should degrade gracefully."""
        resp = _submit("ingest", {"step": 1})
        self.assertIsInstance(resp, SpineResponse)

    def test_query_memory_empty_query(self):
        resp = _submit("query_memory", {"query": ""})
        self.assertIsInstance(resp, SpineResponse)

    def test_query_memory_missing_query_key(self):
        resp = _submit("query_memory", {})
        self.assertIsInstance(resp, SpineResponse)

    def test_feedback_empty_arrays(self):
        resp = _submit("feedback", {
            "retrieved_ids": [],
            "used_successfully": [],
            "user_confirmed": [],
            "contradiction_detected": [],
        })
        self.assertIsInstance(resp, SpineResponse)

    def test_query_state_empty_payload(self):
        resp = _submit("query_state", {})
        self.assertTrue(resp.ok)

    # --- Large / extreme inputs ---

    def test_ingest_large_text(self):
        """10KB text — should succeed without issues."""
        big_text = "The quick brown fox jumps over the lazy dog. " * 250
        resp = _submit("ingest", {"text": big_text, "step": 1})
        self.assertIsInstance(resp, SpineResponse)
        # Should succeed on the fast path
        if resp.ok:
            self.assertEqual(resp.decision_code, DECISION_FAST_ALLOWED)

    def test_ingest_very_large_step(self):
        resp = _submit("ingest", {"text": "big step", "step": 999999999})
        self.assertIsInstance(resp, SpineResponse)

    def test_ingest_negative_step(self):
        resp = _submit("ingest", {"text": "negative step", "step": -1})
        self.assertIsInstance(resp, SpineResponse)

    def test_query_memory_large_top_k(self):
        resp = _submit("query_memory", {"query": "test", "top_k": 10000})
        self.assertIsInstance(resp, SpineResponse)

    def test_query_memory_zero_top_k(self):
        resp = _submit("query_memory", {"query": "test", "top_k": 0})
        self.assertIsInstance(resp, SpineResponse)

    # --- Unicode / special characters ---

    def test_ingest_unicode(self):
        resp = _submit("ingest", {
            "text": "Héllo wörld 你好世界 مرحبا 🌍✨",
            "step": 1,
        })
        self.assertIsInstance(resp, SpineResponse)

    def test_ingest_emoji_heavy(self):
        resp = _submit("ingest", {
            "text": "🔥💀👻🎃🦇🕸️🧛‍♂️🧟‍♀️" * 50,
            "step": 1,
        })
        self.assertIsInstance(resp, SpineResponse)

    def test_ingest_newlines_and_tabs(self):
        resp = _submit("ingest", {
            "text": "line1\nline2\n\nline4\ttabbed\r\nwindows",
            "step": 1,
        })
        self.assertIsInstance(resp, SpineResponse)

    def test_ingest_json_in_text(self):
        """Text containing JSON — should be treated as literal text."""
        resp = _submit("ingest", {
            "text": '{"key": "value", "nested": {"a": 1}}',
            "step": 1,
        })
        self.assertIsInstance(resp, SpineResponse)

    def test_ingest_html_in_text(self):
        resp = _submit("ingest", {
            "text": '<script>alert("xss")</script><b>bold</b>',
            "step": 1,
        })
        self.assertIsInstance(resp, SpineResponse)

    # --- Wrong types in payload ---

    def test_ingest_step_as_string(self):
        """Step passed as string — should be coerced or handled."""
        resp = _submit("ingest", {"text": "type test", "step": "5"})
        self.assertIsInstance(resp, SpineResponse)

    def test_ingest_step_as_float(self):
        resp = _submit("ingest", {"text": "float step", "step": 3.14})
        self.assertIsInstance(resp, SpineResponse)

    def test_query_memory_top_k_as_string(self):
        resp = _submit("query_memory", {"query": "test", "top_k": "5"})
        self.assertIsInstance(resp, SpineResponse)

    # --- Null-ish values ---

    def test_ingest_none_text(self):
        resp = _submit("ingest", {"text": None, "step": 0})
        self.assertIsInstance(resp, SpineResponse)

    def test_empty_payload(self):
        """Completely empty payload for every fast-path operation."""
        for op in ("ingest", "feedback", "reinforce", "query_state", "query_memory"):
            with self.subTest(operation=op):
                resp = _submit(op, {})
                self.assertIsInstance(resp, SpineResponse)


# ===========================================================================
# B. Missing / incorrect context
# ===========================================================================

class TestMissingContext(unittest.TestCase):
    """Test behaviour with missing, incorrect, or edge-case context."""

    def setUp(self):
        _reset_incident_log()

    def test_nonexistent_workspace(self):
        """Operations on a workspace that doesn't exist."""
        resp = _submit("query_state", {}, workspace_id="ws_does_not_exist")
        self.assertIsInstance(resp, SpineResponse)
        # Should succeed but return empty/minimal state
        if resp.ok:
            result = resp.result
            self.assertEqual(result.get("memory_count", 0), 0)

    def test_nonexistent_agent(self):
        """Operations on an agent that doesn't exist in an existing workspace."""
        resp = _submit("query_state", {}, agent_id="agent_ghost")
        self.assertIsInstance(resp, SpineResponse)

    def test_ingest_nonexistent_workspace(self):
        """Ingest into a workspace that doesn't exist — should handle gracefully."""
        resp = _submit("ingest", {"text": "orphan memory", "step": 1},
                       workspace_id="ws_phantom")
        self.assertIsInstance(resp, SpineResponse)

    def test_ingest_nonexistent_agent(self):
        resp = _submit("ingest", {"text": "orphan agent", "step": 1},
                       agent_id="agent_phantom")
        self.assertIsInstance(resp, SpineResponse)

    # --- Trust edge cases ---

    def test_trust_exactly_at_minimum(self):
        """Trust exactly at the required level should be allowed."""
        # ingest requires TRUST_INGEST (0.4)
        resp = _submit("ingest", {"text": "exact trust", "step": 1},
                       trust=TRUST_INGEST)
        self.assertTrue(resp.ok)

    def test_trust_just_below_minimum(self):
        """Trust 0.01 below required should be blocked."""
        resp = _submit("ingest", {"text": "blocked", "step": 1},
                       trust=TRUST_INGEST - 0.01)
        self.assertFalse(resp.ok)
        self.assertEqual(resp.decision_code, DECISION_BLOCKED_TRUST)

    def test_trust_zero(self):
        """Trust 0.0 should block all write operations."""
        resp = _submit("ingest", {"text": "zero trust", "step": 1}, trust=0.0)
        self.assertFalse(resp.ok)
        self.assertEqual(resp.decision_code, DECISION_BLOCKED_TRUST)

    def test_trust_zero_allows_reads(self):
        """Trust 0.0 should still allow read-only ops (query_state min=0.0)."""
        resp = _submit("query_state", {}, trust=0.0)
        # query_state requires TRUST_READ_ONLY which is 0.0
        self.assertTrue(resp.ok)

    def test_trust_negative(self):
        """Negative trust should block everything except TRUST_READ_ONLY=0.0."""
        resp = _submit("ingest", {"text": "negative", "step": 1}, trust=-1.0)
        self.assertFalse(resp.ok)

    def test_trust_very_high(self):
        """Absurdly high trust should be fine."""
        resp = _submit("ingest", {"text": "super trusted", "step": 1}, trust=999.0)
        self.assertTrue(resp.ok)

    # --- Invalid operation names ---

    def test_empty_operation_name(self):
        """Empty string operation should be rejected as unknown."""
        resp = _submit("", {})
        self.assertFalse(resp.ok)
        self.assertEqual(resp.decision_code, DECISION_BLOCKED_UNKNOWN_OP)

    def test_operation_with_spaces(self):
        resp = _submit("ingest memory", {"text": "test"})
        self.assertFalse(resp.ok)
        self.assertEqual(resp.decision_code, DECISION_BLOCKED_UNKNOWN_OP)

    def test_operation_sql_injection(self):
        resp = _submit("ingest'; DROP TABLE memories; --", {})
        self.assertFalse(resp.ok)
        self.assertEqual(resp.decision_code, DECISION_BLOCKED_UNKNOWN_OP)

    def test_operation_case_sensitive(self):
        """Operation names are case-sensitive: 'Ingest' != 'ingest'."""
        resp = _submit("Ingest", {"text": "case test"})
        self.assertFalse(resp.ok)
        self.assertEqual(resp.decision_code, DECISION_BLOCKED_UNKNOWN_OP)

    # --- Invalid mode ---

    def test_invalid_mode_raises(self):
        """Invalid mode should raise ValueError during SpineRequest creation."""
        with self.assertRaises(ValueError):
            SpineRequest(
                workspace_id=_ws, agent_id=_agent,
                operation="ingest", mode="turbo",
            )

    # --- Domain that doesn't exist ---

    def test_ingest_unknown_domain(self):
        """Ingest with a domain_id that doesn't exist."""
        resp = _submit("ingest", {
            "text": "unknown domain", "step": 1,
            "domain_id": "nonexistent_domain_xyz",
        })
        self.assertIsInstance(resp, SpineResponse)

    def test_query_memory_unknown_domain(self):
        resp = _submit("query_memory", {
            "query": "test", "domain_id": "nonexistent_domain_xyz",
        })
        self.assertIsInstance(resp, SpineResponse)


# ===========================================================================
# C. Tier 2 / Tier 3 operations intentionally blocked
# ===========================================================================

class TestExposureTierBlocking(unittest.TestCase):
    """Verify that guarded and internal operations are correctly gated.

    This tests the POLICY level — the Spine doesn't block based on
    exposure tier (that's the MCP layer's job), but we verify that
    the exposure tier metadata is correct and consistent so the MCP
    layer can enforce it.
    """

    def test_tier1_open_ops_exist(self):
        """All Tier 1 operations should be in the open set."""
        open_ops = get_exposed_operations(EXPOSURE_OPEN)
        expected_open = {"ingest", "feedback", "reinforce",
                         "query_state", "query_memory"}
        for op in expected_open:
            self.assertIn(op, open_ops, f"{op} should be Tier 1 (open)")

    def test_tier2_guarded_ops_not_in_tier1(self):
        """Guarded operations should NOT appear in the Tier 1 set."""
        open_ops = get_exposed_operations(EXPOSURE_OPEN)
        guarded_expected = {"collective_reingest", "memory_governance_set",
                            "compression_run", "cognition_run"}
        for op in guarded_expected:
            self.assertNotIn(op, open_ops,
                             f"{op} is guarded and should not be in Tier 1")

    def test_tier3_internal_never_exposed(self):
        """Internal operations should not appear even in Tier 2."""
        guarded_ops = get_exposed_operations(EXPOSURE_GUARDED)
        internal_expected = {"identity_rewrite", "seed_change",
                             "collective_policy_change", "proposal_review",
                             "role_conflict_resolution", "architecture_review"}
        for op in internal_expected:
            self.assertNotIn(op, guarded_ops,
                             f"{op} is internal and should never be exposed via MCP")

    def test_guarded_ops_execute_with_sufficient_trust(self):
        """Guarded ops CAN execute through the Spine directly (not MCP).

        The Spine doesn't enforce exposure tiers — that's the MCP layer.
        The Spine only enforces trust. So a direct submit_task call with
        sufficient trust should work even for guarded ops.
        """
        # compression_run is guarded but requires TRUST_OPERATOR
        resp = _submit("compression_run", {"step": 1}, trust=TRUST_OPERATOR)
        self.assertIsInstance(resp, SpineResponse)
        # Should succeed or at least not be blocked by tier
        if not resp.ok:
            # Only acceptable failure is dispatch-level (e.g., no data to compress)
            self.assertNotEqual(resp.decision_code, DECISION_BLOCKED_TRUST)

    def test_internal_ops_execute_with_operator_trust(self):
        """Internal ops CAN execute through Spine with operator trust.

        Again, exposure tiers are MCP-layer policy, not Spine-layer.
        """
        # identity_rewrite requires full path + operator trust
        # It will likely fail on dispatch (no cognition pipeline configured
        # in test), but it should NOT be blocked by trust or unknown-op.
        resp = _submit("identity_rewrite", {"text": "test"}, trust=TRUST_OPERATOR,
                       mode="full")
        self.assertIsInstance(resp, SpineResponse)
        if not resp.ok:
            # Acceptable: dispatch error (no cognition pipeline in test env)
            self.assertIn(resp.decision_code,
                          (DECISION_ERROR_DISPATCH, DECISION_BLOCKED_NO_HANDLER))

    def test_every_registered_op_has_valid_tier(self):
        """Every operation in the registry has a valid exposure tier."""
        from torment_service.spine import VALID_EXPOSURE_TIERS
        for name, spec in OPERATION_REGISTRY.items():
            self.assertIn(spec.exposure_tier, VALID_EXPOSURE_TIERS,
                          f"{name} has invalid exposure tier: {spec.exposure_tier}")

    def test_every_registered_op_has_valid_op_class(self):
        from torment_service.spine import VALID_OP_CLASSES
        for name, spec in OPERATION_REGISTRY.items():
            if spec.op_class:
                self.assertIn(spec.op_class, VALID_OP_CLASSES,
                              f"{name} has invalid op_class: {spec.op_class}")


# ===========================================================================
# D. Status surface verification after a barrage of mixed requests
# ===========================================================================

class TestStatusSurfaceAfterBarrage(unittest.TestCase):
    """After a barrage of good, bad, and weird requests, verify that
    /spine/status and the incident log accurately answer:
    'What just happened?'
    """

    def test_barrage_and_verify(self):
        """Fire a mix of requests and check the status surface."""
        _reset_incident_log()

        # --- Fire a barrage ---
        results = []

        # Good requests
        results.append(_submit("ingest", {"text": "memory one", "step": 1}))
        results.append(_submit("ingest", {"text": "memory two", "step": 2}))
        results.append(_submit("query_state", {}))
        results.append(_submit("query_memory", {"query": "memory"}))

        # Bad trust
        results.append(_submit("ingest", {"text": "blocked", "step": 1}, trust=0.0))

        # Unknown operations
        results.append(_submit("explode", {}))
        results.append(_submit("", {}))

        # Weird inputs (should not crash)
        results.append(_submit("ingest", {"text": "", "step": 0}))
        results.append(_submit("ingest", {"text": None, "step": 0}))
        results.append(_submit("query_memory", {"query": "🔥" * 100}))

        # Identity-sensitive (may escalate)
        results.append(_submit("ingest", {
            "text": "who am i? what is my core identity?", "step": 3,
        }))

        # --- Verify the status surface ---
        log = get_incident_log()
        total = log._total_logged
        self.assertEqual(total, len(results),
                         "Every submit_task call should produce exactly one incident")

        # Count by category
        summary = log.summary()
        self.assertEqual(summary["total_logged"], total)
        self.assertEqual(summary["buffer_size"], total)

        # We should have at least 3 failures:
        #   - blocked trust
        #   - 2 unknown operations
        self.assertGreaterEqual(summary["total_failures"], 3)

        # Decision code distribution should include fast_allowed and blocked codes
        decisions = summary["recent_decisions"]
        self.assertIn("fast_allowed", decisions)
        self.assertGreaterEqual(decisions.get("fast_allowed", 0), 1)

        # Blocks should be in recent_blocks
        blocks = summary["recent_blocks"]
        self.assertGreaterEqual(len(blocks), 2)
        block_codes = {b["decision_code"] for b in blocks}
        self.assertIn("blocked_unknown_operation", block_codes)

        # Query should return filtered results correctly
        failures = log.query(failures_only=True)
        self.assertGreaterEqual(len(failures), 3)

        successes = log.query(ok=True)
        self.assertGreaterEqual(len(successes), 4)  # at least the 4 good requests

        # Operation filter
        ingests = log.query(operation="ingest")
        self.assertGreaterEqual(len(ingests), 2)

        # Timestamp ordering: most recent first
        all_incidents = log.query(limit=100)
        for i in range(len(all_incidents) - 1):
            self.assertGreaterEqual(all_incidents[i].timestamp,
                                    all_incidents[i + 1].timestamp)

    def test_escalation_appears_in_status(self):
        """If any auto-escalation fires, it shows up in the log."""
        _reset_incident_log()

        # This should trigger identity_sensitive escalation
        resp = _submit("query_memory", {
            "query": "who am i? what is my seed identity and character?",
        })

        log = get_incident_log()
        incidents = log.query(limit=1)
        self.assertEqual(len(incidents), 1)
        inc = incidents[0]

        if resp.escalated:
            self.assertTrue(inc.escalated)
            self.assertGreater(len(inc.escalation_reasons), 0)
            self.assertIn("identity_sensitive", inc.escalation_reasons)
            self.assertEqual(inc.decision_code, "escalated_full")


if __name__ == "__main__":
    unittest.main()
