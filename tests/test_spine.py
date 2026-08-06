# tests/test_spine.py — End-to-end tests for the governed Spine layer
#
# Validates:
#   1. SpineRequest/SpineResponse models
#   2. Fast governance path for ingest, collective_reingest, query_state
#   3. Trust enforcement (rejection on insufficient trust)
#   4. Auto-escalation triggers
#   5. Operation registry completeness
#   6. Response envelope shape
# ---------------------------------------------------------------------------
from __future__ import annotations

import os
import sys
import tempfile
import unittest

# Ensure project root is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.request_context import (
    RequestContext,
    TRUST_READ_ONLY,
    TRUST_QUERY_REINFORCE,
    TRUST_INGEST,
    TRUST_COLLECTIVE,
    TRUST_OPERATOR,
)
from torment_service.spine import (
    SpineRequest,
    SpineResponse,
    submit_task,
    preview_route_decision,
    should_escalate,
    escalation_reasons,
    ESCALATION_IDENTITY_SENSITIVE,
    ESCALATION_HIGH_DRIFT,
    ESCALATION_PROTECTED_MEMORY,
    OPERATION_REGISTRY,
    PATH_FAST,
    PATH_FULL,
    OP_CLASS_READ,
    OP_CLASS_WRITE,
    OP_CLASS_COLLECTIVE,
    OP_CLASS_IDENTITY,
    OP_CLASS_COGNITIVE,
    VALID_OP_CLASSES,
    DECISION_FAST_ALLOWED,
    DECISION_BLOCKED_TRUST,
    DECISION_BLOCKED_UNKNOWN_OP,
    RESULT_STORED,
    RESULT_REINFORCED,
    RESULT_QUERIED,
    RESULT_STATE_READ,
    RESULT_NONE,
    EXPOSURE_OPEN,
    EXPOSURE_GUARDED,
    EXPOSURE_INTERNAL,
    VALID_EXPOSURE_TIERS,
    get_exposed_operations,
)
from torment_service.fabric import TormentFabric
from torment_service.character import CharacterState


class TestSpineModels(unittest.TestCase):
    """Test SpineRequest and SpineResponse dataclasses."""

    def test_request_auto_id(self):
        req = SpineRequest(workspace_id="ws1", agent_id="a1", operation="ingest")
        self.assertTrue(req.task_id.startswith("spine_"))
        self.assertGreater(req.timestamp, 0)

    def test_request_invalid_mode(self):
        with self.assertRaises(ValueError):
            SpineRequest(workspace_id="ws1", agent_id="a1", operation="ingest", mode="invalid")

    def test_response_to_dict(self):
        resp = SpineResponse(
            ok=True, path="fast", operation="ingest",
            allowed=True, workspace_id="ws1", agent_id="a1",
        )
        d = resp.to_dict()
        self.assertTrue(d["ok"])
        self.assertEqual(d["path"], "fast")
        self.assertEqual(d["operation"], "ingest")


class TestOperationRegistry(unittest.TestCase):
    """Test the operation registry is complete and consistent."""

    def test_all_fast_ops_registered(self):
        for name in ("ingest", "feedback", "reinforce", "collective_reingest",
                      "memory_governance_set", "query_state", "query_memory",
                      "compression_run"):
            self.assertIn(name, OPERATION_REGISTRY, f"{name} not in registry")
            self.assertEqual(OPERATION_REGISTRY[name].default_path, PATH_FAST)

    def test_all_full_ops_registered(self):
        for name in ("cognition_run", "identity_rewrite", "seed_change"):
            self.assertIn(name, OPERATION_REGISTRY, f"{name} not in registry")
            self.assertEqual(OPERATION_REGISTRY[name].default_path, PATH_FULL)

    def test_trust_levels_ascending(self):
        """Verify trust hierarchy makes sense."""
        self.assertEqual(OPERATION_REGISTRY["query_state"].min_trust, TRUST_READ_ONLY)
        self.assertEqual(OPERATION_REGISTRY["feedback"].min_trust, TRUST_QUERY_REINFORCE)
        self.assertEqual(OPERATION_REGISTRY["ingest"].min_trust, TRUST_INGEST)
        self.assertEqual(OPERATION_REGISTRY["collective_reingest"].min_trust, TRUST_COLLECTIVE)
        self.assertEqual(OPERATION_REGISTRY["memory_governance_set"].min_trust, TRUST_OPERATOR)


class TestEscalationPolicy(unittest.TestCase):
    """Test auto-escalation triggers."""

    def _ctx(self, trust=TRUST_INGEST):
        return RequestContext(client_id="test", trust_tier=trust,
                              workspace_id="ws1", agent_id="a1")

    def test_identity_content_observed_for_ingest_but_does_not_redirect(self):
        payload = {"text": "rewrite my identity seed"}
        self.assertFalse(should_escalate("ingest", payload, self._ctx()))
        self.assertIn(ESCALATION_IDENTITY_SENSITIVE, escalation_reasons("ingest", payload, self._ctx()))

    def test_negative_high_drift_escalates_general_operations(self):
        self.assertTrue(should_escalate(
            "query_memory", {"query": "hello"}, self._ctx(trust=TRUST_OPERATOR), drift_score=-0.25))

    def test_large_positive_aligned_drift_does_not_escalate(self):
        self.assertFalse(should_escalate(
            "query_memory", {"query": "hello"}, self._ctx(trust=TRUST_OPERATOR), drift_score=0.915931224822998))

    def test_near_zero_drift_has_no_high_drift_reason(self):
        reasons = escalation_reasons(
            "query_memory", {"query": "hello"}, self._ctx(trust=TRUST_OPERATOR), drift_score=0.0
        )
        self.assertNotIn(ESCALATION_HIGH_DRIFT, reasons)

    def test_moderate_negative_drift_has_no_high_drift_reason(self):
        reasons = escalation_reasons(
            "query_memory", {"query": "hello"}, self._ctx(trust=TRUST_OPERATOR), drift_score=-0.15
        )
        self.assertNotIn(ESCALATION_HIGH_DRIFT, reasons)

    def test_negative_drift_beyond_threshold_has_high_drift_reason(self):
        reasons = escalation_reasons(
            "query_memory", {"query": "hello"}, self._ctx(trust=TRUST_OPERATOR), drift_score=-0.25
        )
        self.assertIn(ESCALATION_HIGH_DRIFT, reasons)

    def test_protected_memory_escalates(self):
        self.assertTrue(should_escalate(
            "query_memory", {"query": "x", "protected": True}, self._ctx(trust=TRUST_OPERATOR)))

    def test_normal_text_no_escalation(self):
        # Use trust well above minimum to avoid borderline trigger
        self.assertFalse(should_escalate(
            "ingest", {"text": "the weather is nice today"}, self._ctx(trust=TRUST_OPERATOR)))

    def test_non_escalatable_never_escalates(self):
        """Operations without can_escalate=True never escalate."""
        self.assertFalse(should_escalate(
            "feedback", {"text": "rewrite identity"}, self._ctx()))


class TestSpineEndToEnd(unittest.TestCase):
    """End-to-end tests through submit_task with a real TormentFabric."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        self.fabric = TormentFabric(data_dir=self.tmp)
        self.fabric.get_workspace("ws1")
        self.fabric.create_agent("ws1", "atlas")

    def _save_character_state(self, *, drift_score=0.0, drift_direction="stable", relational_count=0):
        self.fabric.character_store.save_state(
            "ws1",
            CharacterState(
                workspace_id="ws1",
                agent_id="atlas",
                seed_id="seed-test",
                drift_score=drift_score,
                drift_direction=drift_direction,
                relational_count=relational_count,
            ),
        )

    # --- Trust enforcement ---

    def test_insufficient_trust_rejected(self):
        """Read-only trust can't ingest."""
        ctx = RequestContext(client_id="guest", trust_tier=TRUST_READ_ONLY,
                             workspace_id="ws1", agent_id="atlas")
        req = SpineRequest(workspace_id="ws1", agent_id="atlas",
                           operation="ingest", payload={"text": "hello"})
        resp = submit_task(req, self.fabric, ctx)
        self.assertFalse(resp.ok)
        self.assertFalse(resp.allowed)
        self.assertIn("Insufficient trust", resp.reason)

    def test_unknown_operation_rejected(self):
        ctx = RequestContext(client_id="op", trust_tier=TRUST_OPERATOR,
                             workspace_id="ws1", agent_id="atlas")
        req = SpineRequest(workspace_id="ws1", agent_id="atlas",
                           operation="delete_everything")
        resp = submit_task(req, self.fabric, ctx)
        self.assertFalse(resp.ok)
        self.assertIn("Unknown operation", resp.reason)

    # --- Ingest (fast path) ---

    def test_ingest_fast_path(self):
        ctx = RequestContext(client_id="claude", trust_tier=TRUST_INGEST,
                             workspace_id="ws1", agent_id="atlas")
        req = SpineRequest(
            workspace_id="ws1", agent_id="atlas",
            operation="ingest",
            payload={"text": "The Spine governs all writes now."},
            mode="fast",
        )
        resp = submit_task(req, self.fabric, ctx)
        self.assertTrue(resp.ok)
        self.assertTrue(resp.allowed)
        self.assertEqual(resp.path, "fast")
        self.assertEqual(resp.operation, "ingest")
        self.assertEqual(resp.workspace_id, "ws1")
        self.assertEqual(resp.agent_id, "atlas")
        self.assertGreater(resp.elapsed_ms, 0)
        # Result should contain an eid
        self.assertIn("eid", resp.result)

    def test_ingest_auto_mode(self):
        """Auto mode should choose fast for normal text."""
        ctx = RequestContext(client_id="claude", trust_tier=TRUST_INGEST,
                             workspace_id="ws1", agent_id="atlas")
        req = SpineRequest(
            workspace_id="ws1", agent_id="atlas",
            operation="ingest",
            payload={"text": "Normal memory content."},
            mode="auto",
        )
        resp = submit_task(req, self.fabric, ctx)
        self.assertTrue(resp.ok)
        self.assertEqual(resp.path, "fast")
        self.assertFalse(resp.escalated)

    def test_explicit_ingest_positive_aligned_drift_stays_write_capable(self):
        self._save_character_state(
            drift_score=0.915931224822998,
            drift_direction="stable",
            relational_count=22,
        )
        ctx = RequestContext(client_id="claude", trust_tier=TRUST_INGEST,
                             workspace_id="ws1", agent_id="atlas")
        req = SpineRequest(
            workspace_id="ws1", agent_id="atlas",
            operation="ingest",
            payload={"text": "Companion summary about a stable aligned turn.", "step": 9},
            mode="auto",
        )

        route = preview_route_decision(req, self.fabric, ctx)
        resp = submit_task(req, self.fabric, ctx)

        self.assertTrue(route.write_capable)
        self.assertEqual(route.predicted_path, PATH_FAST)
        self.assertFalse(route.would_escalate)
        self.assertTrue(resp.ok)
        self.assertEqual(resp.path, PATH_FAST)
        self.assertFalse(resp.escalated)
        self.assertEqual(resp.result_code, RESULT_STORED)
        self.assertIn("eid", resp.result)

    def test_explicit_ingest_identity_words_do_not_become_read_only_success(self):
        ctx = RequestContext(client_id="claude", trust_tier=TRUST_INGEST,
                             workspace_id="ws1", agent_id="atlas")
        req = SpineRequest(
            workspace_id="ws1", agent_id="atlas",
            operation="ingest",
            payload={"text": "Hilmir asked who am i and Eira answered from character identity seed.", "step": 10},
            mode="auto",
        )

        resp = submit_task(req, self.fabric, ctx)

        self.assertTrue(resp.ok)
        self.assertEqual(resp.path, PATH_FAST)
        self.assertFalse(resp.escalated)
        self.assertEqual(resp.decision_code, DECISION_FAST_ALLOWED)
        self.assertEqual(resp.result_code, RESULT_STORED)
        self.assertIn(ESCALATION_IDENTITY_SENSITIVE, resp.escalation_reasons)
        self.assertNotEqual(resp.result_code, "cognition")

    def test_ingest_route_decision_exposes_suppressed_negative_drift_reason(self):
        self._save_character_state(drift_score=-0.25, drift_direction="away_seed")
        ctx = RequestContext(client_id="claude", trust_tier=TRUST_INGEST,
                             workspace_id="ws1", agent_id="atlas")
        req = SpineRequest(
            workspace_id="ws1", agent_id="atlas",
            operation="ingest",
            payload={"text": "memory under temporary away drift", "step": 11},
            mode="auto",
        )

        route = preview_route_decision(req, self.fabric, ctx)

        self.assertEqual(route.predicted_path, PATH_FAST)
        self.assertTrue(route.write_capable)
        self.assertFalse(route.would_escalate)
        self.assertTrue(route.escalation_suppressed)
        self.assertIn(ESCALATION_HIGH_DRIFT, route.escalation_reasons)

    def test_query_memory_negative_drift_still_predicts_full_escalation(self):
        self._save_character_state(drift_score=-0.25, drift_direction="away_seed")
        ctx = RequestContext(client_id="viewer", trust_tier=TRUST_OPERATOR,
                             workspace_id="ws1", agent_id="atlas")
        req = SpineRequest(
            workspace_id="ws1", agent_id="atlas",
            operation="query_memory",
            payload={"query": "ordinary recall"},
            mode="auto",
        )

        route = preview_route_decision(req, self.fabric, ctx)

        self.assertEqual(route.predicted_path, PATH_FULL)
        self.assertTrue(route.would_escalate)
        self.assertFalse(route.write_capable)
        self.assertIn(ESCALATION_HIGH_DRIFT, route.escalation_reasons)

    def test_ingest_route_decision_hard_refusal_is_visible(self):
        ctx = RequestContext(client_id="guest", trust_tier=TRUST_READ_ONLY,
                             workspace_id="ws1", agent_id="atlas")
        req = SpineRequest(
            workspace_id="ws1", agent_id="atlas",
            operation="ingest",
            payload={"text": "unauthorized"},
            mode="auto",
        )

        route = preview_route_decision(req, self.fabric, ctx)

        self.assertFalse(route.ok)
        self.assertTrue(route.would_refuse)
        self.assertFalse(route.write_capable)
        self.assertIn("Insufficient trust", route.refusal_reason)

    # --- Query State (fast path, read-only) ---

    def test_query_state_fast_path(self):
        ctx = RequestContext(client_id="viewer", trust_tier=TRUST_READ_ONLY,
                             workspace_id="ws1", agent_id="atlas")
        req = SpineRequest(
            workspace_id="ws1", agent_id="atlas",
            operation="query_state",
            mode="fast",
        )
        resp = submit_task(req, self.fabric, ctx)
        self.assertTrue(resp.ok)
        self.assertEqual(resp.path, "fast")
        self.assertEqual(resp.trust_tier, TRUST_READ_ONLY)
        # Result should contain agent info
        self.assertIn("workspace_id", resp.result)
        self.assertIn("agent_id", resp.result)
        self.assertIn("memory_count", resp.result)

    # --- Response envelope shape ---

    def test_response_envelope_has_audit(self):
        ctx = RequestContext(client_id="claude", trust_tier=TRUST_INGEST,
                             workspace_id="ws1", agent_id="atlas",
                             session_id="sess_001")
        req = SpineRequest(
            workspace_id="ws1", agent_id="atlas",
            operation="ingest",
            payload={"text": "Audit trail test."},
        )
        resp = submit_task(req, self.fabric, ctx)
        self.assertTrue(resp.ok)
        self.assertIn("client_id", resp.audit)
        self.assertEqual(resp.audit["client_id"], "claude")
        self.assertIn("session_id", resp.audit)
        self.assertEqual(resp.audit["session_id"], "sess_001")

    def test_response_has_drift_status(self):
        ctx = RequestContext(client_id="claude", trust_tier=TRUST_INGEST,
                             workspace_id="ws1", agent_id="atlas")
        req = SpineRequest(
            workspace_id="ws1", agent_id="atlas",
            operation="ingest",
            payload={"text": "Drift status test."},
        )
        resp = submit_task(req, self.fabric, ctx)
        self.assertIn(resp.drift_status, ("green", "yellow", "red", "unknown"))

    # --- Multiple ingests through Spine ---

    def test_multiple_ingests_sequential(self):
        """Multiple ingests through the Spine should all succeed."""
        ctx = RequestContext(client_id="claude", trust_tier=TRUST_INGEST,
                             workspace_id="ws1", agent_id="atlas")
        eids = []
        for i in range(5):
            req = SpineRequest(
                workspace_id="ws1", agent_id="atlas",
                operation="ingest",
                payload={"text": f"Memory {i}: governed ingest test."},
            )
            resp = submit_task(req, self.fabric, ctx)
            self.assertTrue(resp.ok, f"Ingest {i} failed: {resp.reason}")
            eids.append(resp.result.get("eid"))
        # All eids should be unique
        self.assertEqual(len(set(eids)), 5)


class TestSpineQueryMemory(unittest.TestCase):
    """Test query_memory through the Spine."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        self.fabric = TormentFabric(data_dir=self.tmp)
        self.fabric.get_workspace("ws1")
        self.fabric.create_agent("ws1", "atlas")
        # Ingest some memories via Spine
        ctx = RequestContext(client_id="test", trust_tier=TRUST_INGEST,
                             workspace_id="ws1", agent_id="atlas")
        for text in ["The quantum field resonates", "Memory dynamics are stable",
                     "Identity preserved through drift"]:
            req = SpineRequest(workspace_id="ws1", agent_id="atlas",
                               operation="ingest", payload={"text": text})
            submit_task(req, self.fabric, ctx)

    def test_query_returns_results(self):
        ctx = RequestContext(client_id="viewer", trust_tier=TRUST_READ_ONLY,
                             workspace_id="ws1", agent_id="atlas")
        req = SpineRequest(
            workspace_id="ws1", agent_id="atlas",
            operation="query_memory",
            payload={"query": "quantum", "top_k": 3},
        )
        resp = submit_task(req, self.fabric, ctx)
        self.assertTrue(resp.ok)
        self.assertEqual(resp.path, "fast")
        # Should have results
        self.assertIn("results", resp.result)


class TestEscalationReasonCodes(unittest.TestCase):
    """Test structured escalation reason codes (Patch 1G)."""

    def _ctx(self, trust=TRUST_INGEST):
        return RequestContext(client_id="test", trust_tier=trust,
                              workspace_id="ws1", agent_id="a1")

    def test_identity_reason_code(self):
        reasons = escalation_reasons(
            "ingest", {"text": "rewrite my identity seed"}, self._ctx())
        self.assertIn(ESCALATION_IDENTITY_SENSITIVE, reasons)

    def test_high_drift_reason_code(self):
        reasons = escalation_reasons(
            "ingest", {"text": "hello"}, self._ctx(), drift_score=-0.25)
        self.assertIn(ESCALATION_HIGH_DRIFT, reasons)

    def test_protected_memory_reason_code(self):
        reasons = escalation_reasons(
            "ingest", {"text": "x", "protected": True}, self._ctx())
        self.assertIn(ESCALATION_PROTECTED_MEMORY, reasons)

    def test_no_reasons_for_normal_text(self):
        reasons = escalation_reasons(
            "ingest", {"text": "the weather is nice today"}, self._ctx(trust=TRUST_OPERATOR))
        self.assertEqual(reasons, [])

    def test_multiple_reasons_can_fire(self):
        """Multiple triggers can fire simultaneously."""
        reasons = escalation_reasons(
            "ingest",
            {"text": "rewrite my identity seed", "protected": True},
            self._ctx(),
            drift_score=-0.30,
        )
        self.assertIn(ESCALATION_IDENTITY_SENSITIVE, reasons)
        self.assertIn(ESCALATION_HIGH_DRIFT, reasons)
        self.assertIn(ESCALATION_PROTECTED_MEMORY, reasons)
        self.assertGreaterEqual(len(reasons), 3)

    def test_query_memory_now_escalatable(self):
        """query_memory should now support escalation (Patch 1F)."""
        spec = OPERATION_REGISTRY["query_memory"]
        self.assertTrue(spec.can_escalate)
        reasons = escalation_reasons(
            "query_memory", {"query": "who am i and what is my identity"},
            self._ctx(trust=TRUST_READ_ONLY))
        self.assertIn(ESCALATION_IDENTITY_SENSITIVE, reasons)


class TestSpineBlockedActions(unittest.TestCase):
    """Test blocked-action audit integration (Patch 1H)."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        self.fabric = TormentFabric(data_dir=self.tmp)
        self.fabric.get_workspace("ws1")
        self.fabric.create_agent("ws1", "atlas")

    def test_blocked_response_has_reason(self):
        """Trust rejection should have a structured reason string."""
        ctx = RequestContext(client_id="guest", trust_tier=TRUST_READ_ONLY,
                             workspace_id="ws1", agent_id="atlas")
        req = SpineRequest(workspace_id="ws1", agent_id="atlas",
                           operation="ingest", payload={"text": "hello"})
        resp = submit_task(req, self.fabric, ctx)
        self.assertFalse(resp.ok)
        self.assertIn("Insufficient trust", resp.reason)

    def test_suppressed_ingest_escalation_reasons_in_response(self):
        """Explicit ingest should carry observed reasons without route escalation."""
        ctx = RequestContext(client_id="claude", trust_tier=TRUST_INGEST,
                             workspace_id="ws1", agent_id="atlas")
        req = SpineRequest(
            workspace_id="ws1", agent_id="atlas",
            operation="ingest",
            payload={"text": "rewrite my identity seed"},
            mode="auto",
        )
        resp = submit_task(req, self.fabric, ctx)
        self.assertTrue(resp.ok)
        self.assertEqual(resp.path, PATH_FAST)
        self.assertFalse(resp.escalated)
        self.assertIn(ESCALATION_IDENTITY_SENSITIVE, resp.escalation_reasons)

    def test_non_escalated_has_empty_reasons(self):
        """Normal fast-path response should have empty escalation_reasons."""
        ctx = RequestContext(client_id="claude", trust_tier=TRUST_INGEST,
                             workspace_id="ws1", agent_id="atlas")
        req = SpineRequest(
            workspace_id="ws1", agent_id="atlas",
            operation="ingest",
            payload={"text": "Normal memory content."},
            mode="fast",
        )
        resp = submit_task(req, self.fabric, ctx)
        self.assertTrue(resp.ok)
        self.assertEqual(resp.escalation_reasons, [])


class TestOperationClasses(unittest.TestCase):
    """Test operation class assignments (Priority C)."""

    def test_all_operations_have_valid_class(self):
        for name, spec in OPERATION_REGISTRY.items():
            self.assertIn(spec.op_class, VALID_OP_CLASSES,
                          f"Operation '{name}' has invalid op_class '{spec.op_class}'")

    def test_read_ops_are_read_class(self):
        for name in ("query_state", "query_memory"):
            self.assertEqual(OPERATION_REGISTRY[name].op_class, OP_CLASS_READ)

    def test_write_ops_are_write_class(self):
        for name in ("ingest", "feedback", "reinforce", "memory_governance_set", "compression_run"):
            self.assertEqual(OPERATION_REGISTRY[name].op_class, OP_CLASS_WRITE)

    def test_collective_ops_are_collective_class(self):
        for name in ("collective_reingest", "collective_policy_change", "proposal_review"):
            self.assertEqual(OPERATION_REGISTRY[name].op_class, OP_CLASS_COLLECTIVE)

    def test_identity_ops_are_identity_class(self):
        for name in ("identity_rewrite", "seed_change"):
            self.assertEqual(OPERATION_REGISTRY[name].op_class, OP_CLASS_IDENTITY)

    def test_cognitive_ops_are_cognitive_class(self):
        for name in ("cognition_run", "role_conflict_resolution", "architecture_review"):
            self.assertEqual(OPERATION_REGISTRY[name].op_class, OP_CLASS_COGNITIVE)


class TestDecisionResultCodes(unittest.TestCase):
    """Test decision_code and result_code in SpineResponse (Priority B)."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        self.fabric = TormentFabric(data_dir=self.tmp)
        self.fabric.get_workspace("ws1")
        self.fabric.create_agent("ws1", "atlas")

    def test_fast_ingest_codes(self):
        ctx = RequestContext(client_id="claude", trust_tier=TRUST_INGEST,
                             workspace_id="ws1", agent_id="atlas")
        req = SpineRequest(workspace_id="ws1", agent_id="atlas",
                           operation="ingest", payload={"text": "hello"},
                           mode="fast")
        resp = submit_task(req, self.fabric, ctx)
        self.assertTrue(resp.ok)
        self.assertEqual(resp.decision_code, DECISION_FAST_ALLOWED)
        self.assertEqual(resp.result_code, RESULT_STORED)

    def test_query_state_codes(self):
        ctx = RequestContext(client_id="claude", trust_tier=TRUST_INGEST,
                             workspace_id="ws1", agent_id="atlas")
        req = SpineRequest(workspace_id="ws1", agent_id="atlas",
                           operation="query_state", mode="fast")
        resp = submit_task(req, self.fabric, ctx)
        self.assertTrue(resp.ok)
        self.assertEqual(resp.decision_code, DECISION_FAST_ALLOWED)
        self.assertEqual(resp.result_code, RESULT_STATE_READ)

    def test_query_memory_codes(self):
        ctx = RequestContext(client_id="claude", trust_tier=TRUST_INGEST,
                             workspace_id="ws1", agent_id="atlas")
        req = SpineRequest(workspace_id="ws1", agent_id="atlas",
                           operation="query_memory",
                           payload={"query": "test"}, mode="fast")
        resp = submit_task(req, self.fabric, ctx)
        self.assertTrue(resp.ok)
        self.assertEqual(resp.decision_code, DECISION_FAST_ALLOWED)
        self.assertEqual(resp.result_code, RESULT_QUERIED)

    def test_feedback_codes(self):
        ctx = RequestContext(client_id="claude", trust_tier=TRUST_INGEST,
                             workspace_id="ws1", agent_id="atlas")
        req = SpineRequest(workspace_id="ws1", agent_id="atlas",
                           operation="feedback",
                           payload={"retrieved_ids": [], "used_successfully": []},
                           mode="fast")
        resp = submit_task(req, self.fabric, ctx)
        self.assertTrue(resp.ok)
        self.assertEqual(resp.decision_code, DECISION_FAST_ALLOWED)
        self.assertEqual(resp.result_code, RESULT_REINFORCED)

    def test_blocked_trust_codes(self):
        ctx = RequestContext(client_id="guest", trust_tier=TRUST_READ_ONLY,
                             workspace_id="ws1", agent_id="atlas")
        req = SpineRequest(workspace_id="ws1", agent_id="atlas",
                           operation="ingest", payload={"text": "hello"})
        resp = submit_task(req, self.fabric, ctx)
        self.assertFalse(resp.ok)
        self.assertEqual(resp.decision_code, DECISION_BLOCKED_TRUST)
        self.assertEqual(resp.result_code, RESULT_NONE)

    def test_blocked_unknown_op_codes(self):
        ctx = RequestContext(client_id="claude", trust_tier=TRUST_OPERATOR,
                             workspace_id="ws1", agent_id="atlas")
        req = SpineRequest(workspace_id="ws1", agent_id="atlas",
                           operation="nonexistent_op")
        resp = submit_task(req, self.fabric, ctx)
        self.assertFalse(resp.ok)
        self.assertEqual(resp.decision_code, DECISION_BLOCKED_UNKNOWN_OP)
        self.assertEqual(resp.result_code, RESULT_NONE)

    def test_tool_result_ingest_codes(self):
        """Regression for 2026-04-11 bug: successful tool_result_ingest
        stamped result_code='none' because the operation was registered
        in _ALWAYS_FAST without a matching _OPERATION_RESULT_CODES entry.
        A successful write must stamp RESULT_STORED.
        """
        ctx = RequestContext(client_id="claude", trust_tier=TRUST_INGEST,
                             workspace_id="ws1", agent_id="atlas")
        req = SpineRequest(
            workspace_id="ws1", agent_id="atlas",
            operation="tool_result_ingest",
            payload={
                "tool_name": "test_tool",
                "content": "tool returned this payload",
                "summary": "test summary",
            },
            mode="fast",
        )
        resp = submit_task(req, self.fabric, ctx)
        self.assertTrue(resp.ok, f"tool_result_ingest should succeed, got: {resp.to_dict()}")
        self.assertEqual(resp.decision_code, DECISION_FAST_ALLOWED)
        self.assertEqual(
            resp.result_code, RESULT_STORED,
            "tool_result_ingest must stamp RESULT_STORED on success — "
            "result_code='none' on a successful write is the exact "
            "regression this test exists to prevent.",
        )


class TestResultCodeMappingInvariant(unittest.TestCase):
    """Guardrail for the 2026-04-11 tool_result_ingest result_code bug.

    The spine has a startup-time consistency check that raises if any
    fast-path OperationSpec is missing from _OPERATION_RESULT_CODES.
    These tests run the same invariant at test time so a regression is
    caught in CI before it ever reaches MCP runtime.
    """

    def test_every_fast_path_op_has_result_code(self):
        """Every OperationSpec.name in _ALWAYS_FAST must have a
        corresponding entry in _OPERATION_RESULT_CODES. Missing entries
        cause successful writes to silently stamp result_code='none'."""
        from torment_service.spine import _ALWAYS_FAST, _OPERATION_RESULT_CODES
        fast_names = {spec.name for spec in _ALWAYS_FAST}
        mapped_names = set(_OPERATION_RESULT_CODES.keys())
        missing = fast_names - mapped_names
        self.assertEqual(
            missing, set(),
            f"Fast-path operations missing from _OPERATION_RESULT_CODES: "
            f"{sorted(missing)}. Every fast-path op must have a "
            f"result_code mapping or successful writes will stamp "
            f"result_code='none' (see 2026-04-11 tool_result_ingest bug).",
        )

    def test_result_code_mapping_has_no_orphan_entries(self):
        """_OPERATION_RESULT_CODES should not carry entries for
        operations that are not registered as fast-path. Orphan entries
        are not a live bug but indicate drift between the two tables."""
        from torment_service.spine import _ALWAYS_FAST, _OPERATION_RESULT_CODES
        fast_names = {spec.name for spec in _ALWAYS_FAST}
        mapped_names = set(_OPERATION_RESULT_CODES.keys())
        orphans = mapped_names - fast_names
        self.assertEqual(
            orphans, set(),
            f"_OPERATION_RESULT_CODES has orphan entries not in "
            f"_ALWAYS_FAST: {sorted(orphans)}",
        )


class TestExposureTiers(unittest.TestCase):
    """Test exposure_tier assignments and get_exposed_operations helper."""

    def test_all_operations_have_valid_exposure_tier(self):
        for name, spec in OPERATION_REGISTRY.items():
            self.assertIn(spec.exposure_tier, VALID_EXPOSURE_TIERS,
                          f"Operation '{name}' has invalid exposure_tier '{spec.exposure_tier}'")

    def test_tier1_open_operations(self):
        """Tier 1 should include core read/write ops."""
        exposed = get_exposed_operations(EXPOSURE_OPEN)
        expected_open = {"query_state", "query_memory", "ingest", "feedback", "reinforce"}
        for name in expected_open:
            self.assertIn(name, exposed, f"'{name}' should be Tier 1 (open)")

    def test_tier1_excludes_guarded_and_internal(self):
        exposed = get_exposed_operations(EXPOSURE_OPEN)
        for name, spec in OPERATION_REGISTRY.items():
            if spec.exposure_tier != EXPOSURE_OPEN:
                self.assertNotIn(name, exposed,
                                 f"'{name}' (tier={spec.exposure_tier}) should not be in Tier 1")

    def test_tier2_guarded_includes_tier1(self):
        exposed = get_exposed_operations(EXPOSURE_GUARDED)
        tier1 = get_exposed_operations(EXPOSURE_OPEN)
        for name in tier1:
            self.assertIn(name, exposed, f"Tier 1 op '{name}' should also be in Tier 2")

    def test_tier2_guarded_operations(self):
        exposed = get_exposed_operations(EXPOSURE_GUARDED)
        expected_guarded = {"collective_reingest", "memory_governance_set",
                            "compression_run", "cognition_run"}
        for name in expected_guarded:
            self.assertIn(name, exposed, f"'{name}' should be in Tier 2 (guarded)")

    def test_tier3_internal_never_in_tier2(self):
        exposed = get_exposed_operations(EXPOSURE_GUARDED)
        internal_ops = {"identity_rewrite", "seed_change", "collective_policy_change",
                        "proposal_review", "role_conflict_resolution", "architecture_review"}
        for name in internal_ops:
            self.assertNotIn(name, exposed,
                             f"'{name}' (internal) should not be in Tier 2")

    def test_identity_ops_are_internal(self):
        for name in ("identity_rewrite", "seed_change"):
            self.assertEqual(OPERATION_REGISTRY[name].exposure_tier, EXPOSURE_INTERNAL)

    def test_get_exposed_count(self):
        tier1 = get_exposed_operations(EXPOSURE_OPEN)
        tier2 = get_exposed_operations(EXPOSURE_GUARDED)
        self.assertGreater(len(tier2), len(tier1))
        self.assertEqual(len(tier1), 5)  # query_state, query_memory, ingest, feedback, reinforce
        self.assertEqual(len(tier2), 10)  # tier1 + 5 guarded (incl. tool_result_ingest)


if __name__ == "__main__":
    unittest.main()
