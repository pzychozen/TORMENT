"""
tests/test_governance.py — Memory governance resolution, enforcement, and audit tests

Phase D1 tests covering:
    - Governance resolver (normalize from any payload state)
    - Emission blocking (non_shareable / collective_export_blocked)
    - Compression protection (governance 'protected' flag)
    - Decay acceleration (with protected override)
    - Partial flag updates with audit trail
    - Audit log persistence
    - Invariant tests:
        1. Protected memories are never weakened automatically.
        2. Non-shareable or export-blocked memories never emit packets.
        3. Collective echoes are terminal by default.
        4. Collective echoes are influences, not autobiography.
        5. Collective provenance cannot outrank seed/canon identity by default.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.governance import (
    resolve_governance,
    should_emit_packet,
    is_compression_protected,
    is_decay_accelerated,
    allows_collective_reingest,
    update_governance,
    GovernanceAuditLog,
)
from torment_service.collective_models import MemoryGovernanceFlags


# ---------------------------------------------------------------------------
# Resolver tests
# ---------------------------------------------------------------------------

class TestResolveGovernance(unittest.TestCase):
    """resolve_governance normalizes governance from any payload state."""

    def test_none_payload(self):
        gov = resolve_governance(None)
        self.assertIsInstance(gov, MemoryGovernanceFlags)
        self.assertFalse(gov.protected)
        self.assertFalse(gov.non_shareable)

    def test_empty_payload(self):
        gov = resolve_governance({})
        self.assertFalse(gov.protected)

    def test_no_governance_key(self):
        gov = resolve_governance({"summary": "hello", "strength": 0.5})
        self.assertFalse(gov.protected)

    def test_governance_not_dict(self):
        gov = resolve_governance({"governance": "broken"})
        self.assertFalse(gov.protected)

    def test_partial_governance(self):
        """Missing fields get defaults."""
        gov = resolve_governance({"governance": {"protected": True}})
        self.assertTrue(gov.protected)
        self.assertFalse(gov.non_shareable)  # default
        self.assertFalse(gov.decay_accelerated)  # default

    def test_complete_governance(self):
        gov = resolve_governance({"governance": {
            "protected": True,
            "non_shareable": True,
            "decay_accelerated": False,
            "collective_export_blocked": True,
            "collective_reingest_blocked": True,
        }})
        self.assertTrue(gov.protected)
        self.assertTrue(gov.non_shareable)
        self.assertFalse(gov.decay_accelerated)
        self.assertTrue(gov.collective_export_blocked)
        self.assertTrue(gov.collective_reingest_blocked)

    def test_unknown_fields_ignored(self):
        """Extra fields in governance dict don't crash."""
        gov = resolve_governance({"governance": {"protected": True, "future_flag": True}})
        self.assertTrue(gov.protected)


# ---------------------------------------------------------------------------
# Emission blocking tests
# ---------------------------------------------------------------------------

class TestShouldEmitPacket(unittest.TestCase):
    """Invariant 2: Non-shareable or export-blocked memories never emit packets."""

    def test_default_allows_emission(self):
        self.assertTrue(should_emit_packet({}))

    def test_none_payload_allows_emission(self):
        self.assertTrue(should_emit_packet(None))

    def test_non_shareable_blocks(self):
        payload = {"governance": {"non_shareable": True}}
        self.assertFalse(should_emit_packet(payload))

    def test_export_blocked_blocks(self):
        payload = {"governance": {"collective_export_blocked": True}}
        self.assertFalse(should_emit_packet(payload))

    def test_both_block(self):
        payload = {"governance": {"non_shareable": True, "collective_export_blocked": True}}
        self.assertFalse(should_emit_packet(payload))

    def test_other_flags_dont_block_emission(self):
        """protected, decay_accelerated, reingest_blocked don't affect emission."""
        payload = {"governance": {
            "protected": True,
            "decay_accelerated": True,
            "collective_reingest_blocked": True,
        }}
        self.assertTrue(should_emit_packet(payload))


# ---------------------------------------------------------------------------
# Compression protection tests
# ---------------------------------------------------------------------------

class TestIsCompressionProtected(unittest.TestCase):
    """Invariant 1: Protected memories are never weakened automatically."""

    def test_default_not_protected(self):
        self.assertFalse(is_compression_protected({}))

    def test_none_not_protected(self):
        self.assertFalse(is_compression_protected(None))

    def test_protected_flag(self):
        payload = {"governance": {"protected": True}}
        self.assertTrue(is_compression_protected(payload))

    def test_other_flags_dont_protect(self):
        payload = {"governance": {"non_shareable": True, "decay_accelerated": True}}
        self.assertFalse(is_compression_protected(payload))


class TestCompressionScorerGovernanceIntegration(unittest.TestCase):
    """Test that the CompressionScorer respects governance 'protected' flag."""

    def test_governance_protected_memory_not_scored(self):
        """A memory with governance.protected=True should return None from score()."""
        from torment_service.compression import CompressionScorer

        scorer = CompressionScorer(min_age_steps=0)
        node = {
            "eid": 42,
            "born_step": 0,
            "payload": {
                "summary": "Important memory",
                "strength": 0.5,
                "governance": {"protected": True},
            },
        }
        result = scorer.score(node, current_step=100, coherence_field=None)
        self.assertIsNone(result)

    def test_governance_unprotected_memory_scored(self):
        """A memory without governance protection should be scored normally."""
        from torment_service.compression import CompressionScorer

        scorer = CompressionScorer(min_age_steps=0)
        node = {
            "eid": 43,
            "born_step": 0,
            "payload": {
                "summary": "Normal memory",
                "strength": 0.3,
                "governance": {"protected": False},
            },
        }
        result = scorer.score(node, current_step=100, coherence_field=None)
        self.assertIsNotNone(result)
        self.assertEqual(result.eid, 43)

    def test_no_governance_memory_scored(self):
        """Older memories without governance key should be scored normally."""
        from torment_service.compression import CompressionScorer

        scorer = CompressionScorer(min_age_steps=0)
        node = {
            "eid": 44,
            "born_step": 0,
            "payload": {
                "summary": "Old memory without governance",
                "strength": 0.3,
            },
        }
        result = scorer.score(node, current_step=100, coherence_field=None)
        self.assertIsNotNone(result)


# ---------------------------------------------------------------------------
# Decay acceleration tests
# ---------------------------------------------------------------------------

class TestIsDecayAccelerated(unittest.TestCase):
    """Invariant 1 extension: protected always overrides decay_accelerated."""

    def test_default_no_acceleration(self):
        self.assertFalse(is_decay_accelerated({}))

    def test_accelerated_flag(self):
        payload = {"governance": {"decay_accelerated": True}}
        self.assertTrue(is_decay_accelerated(payload))

    def test_protected_overrides_accelerated(self):
        """Even if decay_accelerated=True, protected=True blocks it."""
        payload = {"governance": {"protected": True, "decay_accelerated": True}}
        self.assertFalse(is_decay_accelerated(payload))

    def test_protected_without_accelerated(self):
        payload = {"governance": {"protected": True}}
        self.assertFalse(is_decay_accelerated(payload))


# ---------------------------------------------------------------------------
# Reingest eligibility tests
# ---------------------------------------------------------------------------

class TestAllowsCollectiveReingest(unittest.TestCase):

    def test_default_allows(self):
        self.assertTrue(allows_collective_reingest({}))

    def test_blocked(self):
        payload = {"governance": {"collective_reingest_blocked": True}}
        self.assertFalse(allows_collective_reingest(payload))


# ---------------------------------------------------------------------------
# Partial update + audit tests
# ---------------------------------------------------------------------------

class TestUpdateGovernance(unittest.TestCase):
    """Partial governance updates with audit trail."""

    def test_partial_update_single_flag(self):
        payload = {"summary": "test"}
        audit = update_governance(payload, {"protected": True})
        self.assertTrue(payload["governance"]["protected"])
        self.assertFalse(payload["governance"]["non_shareable"])  # unchanged default
        self.assertIn("changed", audit)
        self.assertIn("protected", audit["changed"])

    def test_partial_update_preserves_existing(self):
        payload = {"governance": {"non_shareable": True}}
        update_governance(payload, {"protected": True})
        self.assertTrue(payload["governance"]["protected"])
        self.assertTrue(payload["governance"]["non_shareable"])  # preserved

    def test_no_change_when_same_value(self):
        payload = {"governance": {"protected": True}}
        audit = update_governance(payload, {"protected": True})
        self.assertEqual(audit["changed"], {})  # no actual change

    def test_multiple_flags_at_once(self):
        payload = {}
        audit = update_governance(payload, {
            "protected": True,
            "non_shareable": True,
            "decay_accelerated": True,
        })
        self.assertTrue(payload["governance"]["protected"])
        self.assertTrue(payload["governance"]["non_shareable"])
        self.assertTrue(payload["governance"]["decay_accelerated"])
        self.assertEqual(len(audit["changed"]), 3)

    def test_invalid_flag_raises(self):
        payload = {}
        with self.assertRaises(ValueError):
            update_governance(payload, {"nonexistent_flag": True})

    def test_audit_trail_appended(self):
        payload = {}
        update_governance(payload, {"protected": True}, actor="admin", source="cli")
        update_governance(payload, {"non_shareable": True}, actor="user", source="ui")

        trail = payload["governance_audit"]
        self.assertEqual(len(trail), 2)
        self.assertEqual(trail[0]["actor"], "admin")
        self.assertEqual(trail[0]["source"], "cli")
        self.assertEqual(trail[1]["actor"], "user")

    def test_audit_records_old_and_new(self):
        payload = {"governance": {"protected": False}}
        audit = update_governance(payload, {"protected": True})
        changed = audit["changed"]["protected"]
        self.assertFalse(changed["old"])
        self.assertTrue(changed["new"])

    def test_payload_not_corrupted(self):
        """Governance update should not destroy other payload fields."""
        payload = {"summary": "hello", "strength": 0.8, "srg": {"R": 0.1}}
        update_governance(payload, {"protected": True})
        self.assertEqual(payload["summary"], "hello")
        self.assertEqual(payload["strength"], 0.8)
        self.assertEqual(payload["srg"]["R"], 0.1)
        self.assertIn("governance", payload)


# ---------------------------------------------------------------------------
# Audit log persistence tests
# ---------------------------------------------------------------------------

class TestGovernanceAuditLog(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_log_and_read(self):
        log = GovernanceAuditLog(self.tmp, "ws1")
        record = log.log(eid=42, agent_id="ryuki", changes={"protected": {"old": False, "new": True}})
        self.assertEqual(record["eid"], 42)
        self.assertEqual(record["agent_id"], "ryuki")

        records = log.recent()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["eid"], 42)

    def test_multiple_records(self):
        log = GovernanceAuditLog(self.tmp, "ws1")
        log.log(eid=1, agent_id="a1", changes={"protected": True})
        log.log(eid=2, agent_id="a2", changes={"non_shareable": True})
        log.log(eid=3, agent_id="a1", changes={"decay_accelerated": True})

        records = log.recent()
        self.assertEqual(len(records), 3)

    def test_limit(self):
        log = GovernanceAuditLog(self.tmp, "ws1")
        for i in range(10):
            log.log(eid=i, agent_id="a1", changes={"x": True})
        records = log.recent(limit=3)
        self.assertEqual(len(records), 3)
        self.assertEqual(records[0]["eid"], 7)  # last 3

    def test_empty_log(self):
        log = GovernanceAuditLog(self.tmp, "ws1")
        self.assertEqual(log.recent(), [])

    def test_workspace_isolation(self):
        log1 = GovernanceAuditLog(self.tmp, "ws1")
        log2 = GovernanceAuditLog(self.tmp, "ws2")
        log1.log(eid=1, agent_id="a1", changes={"x": True})
        self.assertEqual(len(log1.recent()), 1)
        self.assertEqual(len(log2.recent()), 0)

    def test_persistence(self):
        log1 = GovernanceAuditLog(self.tmp, "ws1")
        log1.log(eid=42, agent_id="a1", changes={"protected": True})

        # New instance reads same file
        log2 = GovernanceAuditLog(self.tmp, "ws1")
        records = log2.recent()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["eid"], 42)


# ---------------------------------------------------------------------------
# Invariant tests (design contract verification)
# ---------------------------------------------------------------------------

class TestInvariant_ProtectedNeverWeakened(unittest.TestCase):
    """Invariant 1: Protected memories are never weakened automatically.

    This means:
        - Compression scorer returns None for governance-protected memories
        - decay_accelerated is ignored when protected=True
    """

    def test_scorer_rejects_protected(self):
        from torment_service.compression import CompressionScorer
        scorer = CompressionScorer(min_age_steps=0)
        node = {
            "eid": 1, "born_step": 0,
            "payload": {"strength": 0.1, "governance": {"protected": True}},
        }
        self.assertIsNone(scorer.score(node, 1000, None))

    def test_decay_blocked_when_protected(self):
        payload = {"governance": {"protected": True, "decay_accelerated": True}}
        self.assertFalse(is_decay_accelerated(payload))


class TestInvariant_NonShareableNeverEmits(unittest.TestCase):
    """Invariant 2: Non-shareable or export-blocked memories never emit packets."""

    def test_non_shareable(self):
        self.assertFalse(should_emit_packet({"governance": {"non_shareable": True}}))

    def test_export_blocked(self):
        self.assertFalse(should_emit_packet({"governance": {"collective_export_blocked": True}}))

    def test_both_blocked(self):
        self.assertFalse(should_emit_packet({"governance": {
            "non_shareable": True, "collective_export_blocked": True,
        }}))


class TestInvariant_CollectiveEchoesTerminal(unittest.TestCase):
    """Invariant 3: Collective echoes are terminal by default.

    A memory with provenance='collective' should have both:
        - collective_reingest_blocked = True
        - collective_export_blocked = True
    This test verifies the governance shape that Phase D3 will enforce.
    """

    def test_terminal_echo_shape(self):
        """Verify the governance flags that make an echo terminal."""
        # This is the governance state that reingest will apply
        echo_governance = MemoryGovernanceFlags(
            collective_reingest_blocked=True,
            collective_export_blocked=True,
        )
        # Cannot be re-echoed
        payload = {"governance": echo_governance.to_dict()}
        self.assertFalse(allows_collective_reingest(payload))
        # Cannot leave private memory
        self.assertFalse(should_emit_packet(payload))


class TestInvariant_SourceVsDerivedSplit(unittest.TestCase):
    """Verify source protection flags don't bleed into derived handling and vice versa."""

    def test_source_flags_dont_affect_reingest(self):
        """non_shareable and export_blocked are source flags — don't block reingest."""
        payload = {"governance": {
            "non_shareable": True,
            "collective_export_blocked": True,
        }}
        # Reingest is a derived concern — source flags don't block it
        self.assertTrue(allows_collective_reingest(payload))

    def test_derived_flags_dont_affect_emission(self):
        """reingest_blocked and decay_accelerated are derived flags — don't block emission."""
        payload = {"governance": {
            "collective_reingest_blocked": True,
            "decay_accelerated": True,
        }}
        # Emission is a source concern — derived flags don't block it
        self.assertTrue(should_emit_packet(payload))


if __name__ == "__main__":
    unittest.main()
