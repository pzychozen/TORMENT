# tests/test_baton_requires_lifecycle_fields.py
"""
T1 — AC-1 proof: baton memory class requires lifecycle metadata at ingest.

Covers the acceptance criterion from BLOCK_A_DESIGN.md §4 AC-1:

    fabric.ingest(..., memory_class="baton",
                  provenance=ProvenanceV1.for_baton_ingest(...).to_dict(),
                  extra_payload={"baton_lifecycle": {...}}) succeeds when
    extra_payload["baton_lifecycle"] carries owner, expires_when, and
    resolution_condition. Missing any required field → ingest rejected
    with a specific error, no EID returned, no node written.

Scope per BLOCK_A_DESIGN.md §5.1–5.2:
    - Origin goes in provenance (source_type="baton_intent") via the new
      ProvenanceV1.for_baton_ingest factory.
    - Lifecycle state lives in extra_payload["baton_lifecycle"] and mutates
      over the baton's life. Provenance stays origin/lineage only.
    - Owner vocabulary: {"user", "next_ai", "system"}. Any other value at
      write is rejected.

These tests FAIL against current code (pre-implementation). They pass
once:
    - provenance_v1.SOURCE_BATON_INTENT is added
    - provenance_v1.ProvenanceV1.for_baton_ingest factory lands
    - fabric.ingest validates baton lifecycle fields
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.fabric import TormentFabric
from torment_service.provenance_v1 import (
    ProvenanceV1,
    VALID_SOURCE_TYPES,
    WRITE_DIRECT_INGEST,
)


class TestBatonSourceTypeRegistered(unittest.TestCase):
    """The new source_type must be a first-class vocabulary member."""

    def test_source_baton_intent_constant_exists(self) -> None:
        from torment_service.provenance_v1 import SOURCE_BATON_INTENT
        self.assertEqual(SOURCE_BATON_INTENT, "baton_intent")

    def test_source_baton_intent_in_valid_source_types(self) -> None:
        from torment_service.provenance_v1 import SOURCE_BATON_INTENT
        self.assertIn(SOURCE_BATON_INTENT, VALID_SOURCE_TYPES)


class TestForBatonIngestFactory(unittest.TestCase):
    """The factory must produce a minimal origin-only provenance record.

    Lifecycle fields (owner, expires_when, resolution_condition, status)
    do NOT live on ProvenanceV1 — they live on the memory entity's
    extra_payload. The factory concerns itself with origin/lineage only.
    """

    def test_factory_exists(self) -> None:
        self.assertTrue(
            hasattr(ProvenanceV1, "for_baton_ingest"),
            "ProvenanceV1.for_baton_ingest factory must exist per §5.1"
        )

    def test_factory_sets_source_type(self) -> None:
        from torment_service.provenance_v1 import SOURCE_BATON_INTENT
        p = ProvenanceV1.for_baton_ingest()
        self.assertEqual(p.source_type, SOURCE_BATON_INTENT)

    def test_factory_uses_direct_ingest_write_path(self) -> None:
        # Baton is WHAT it is (source_type), not a new write path.
        # Baton ingest is a direct user/agent ingest carrying lifecycle
        # metadata — the writer path is direct_ingest.
        p = ProvenanceV1.for_baton_ingest()
        self.assertEqual(p.write_path, WRITE_DIRECT_INGEST)

    def test_factory_accepts_step_and_session_id(self) -> None:
        p = ProvenanceV1.for_baton_ingest(step=7, session_id="s1")
        self.assertEqual(p.created_at_step, 7)
        self.assertEqual(p.session_id, "s1")

    def test_factory_does_not_carry_lifecycle_fields_on_provenance(self) -> None:
        """§5.1 separation: lifecycle fields must NOT live on provenance."""
        p = ProvenanceV1.for_baton_ingest()
        d = p.to_dict()
        for field in ("owner", "expires_when", "resolution_condition",
                      "baton_owner", "baton_expires_when"):
            self.assertNotIn(
                field, d,
                f"Provenance must not carry '{field}' — it is lifecycle state, not origin"
            )


class TestBatonIngestValidation(unittest.TestCase):
    """fabric.ingest must reject memory_class='baton' without the required
    lifecycle metadata in extra_payload['baton_lifecycle']."""

    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        self.fabric = TormentFabric(data_dir=self.tmp)
        self.fabric.get_workspace("ws1")
        self.fabric.create_agent("ws1", "atlas")

    def _baton_prov(self) -> dict:
        return ProvenanceV1.for_baton_ingest().to_dict()

    def _complete_lifecycle(self) -> dict:
        return {
            "owner": "user",
            "expires_when": "after_migration_verified",
            "resolution_condition": "user confirms migration ran clean",
        }

    def test_complete_baton_write_succeeds(self) -> None:
        result = self.fabric.ingest(
            workspace_id="ws1",
            agent_id="atlas",
            text="Remember to verify migration output tomorrow morning.",
            step=1,
            scope="private",
            provenance=self._baton_prov(),
            memory_class="baton",
            extra_payload={"baton_lifecycle": self._complete_lifecycle()},
        )
        # Baton ingest must return a successful envelope with an eid.
        self.assertTrue(result.get("stored") or result.get("eid") is not None,
                        f"Baton ingest should have stored; got: {result}")

    def test_missing_owner_is_rejected(self) -> None:
        bad = dict(self._complete_lifecycle())
        bad.pop("owner")
        with self.assertRaises((ValueError, Exception)) as ctx:
            self.fabric.ingest(
                workspace_id="ws1", agent_id="atlas",
                text="Missing owner test.",
                step=1, scope="private",
                provenance=self._baton_prov(),
                memory_class="baton",
                extra_payload={"baton_lifecycle": bad},
            )
        self.assertIn("owner", str(ctx.exception).lower())

    def test_missing_expires_when_is_rejected(self) -> None:
        bad = dict(self._complete_lifecycle())
        bad.pop("expires_when")
        with self.assertRaises((ValueError, Exception)) as ctx:
            self.fabric.ingest(
                workspace_id="ws1", agent_id="atlas",
                text="Missing expires_when test.",
                step=1, scope="private",
                provenance=self._baton_prov(),
                memory_class="baton",
                extra_payload={"baton_lifecycle": bad},
            )
        self.assertIn("expires_when", str(ctx.exception).lower())

    def test_missing_resolution_condition_is_rejected(self) -> None:
        bad = dict(self._complete_lifecycle())
        bad.pop("resolution_condition")
        with self.assertRaises((ValueError, Exception)) as ctx:
            self.fabric.ingest(
                workspace_id="ws1", agent_id="atlas",
                text="Missing resolution_condition test.",
                step=1, scope="private",
                provenance=self._baton_prov(),
                memory_class="baton",
                extra_payload={"baton_lifecycle": bad},
            )
        self.assertIn("resolution_condition", str(ctx.exception).lower())

    def test_invalid_owner_value_is_rejected(self) -> None:
        bad = dict(self._complete_lifecycle())
        bad["owner"] = "stranger"
        with self.assertRaises((ValueError, Exception)) as ctx:
            self.fabric.ingest(
                workspace_id="ws1", agent_id="atlas",
                text="Invalid owner test.",
                step=1, scope="private",
                provenance=self._baton_prov(),
                memory_class="baton",
                extra_payload={"baton_lifecycle": bad},
            )
        msg = str(ctx.exception).lower()
        # Error should reference owner or the valid vocabulary
        self.assertTrue(
            "owner" in msg or "user" in msg or "next_ai" in msg or "system" in msg,
            f"Error should mention owner vocabulary: {ctx.exception}"
        )

    def test_missing_baton_lifecycle_entirely_is_rejected(self) -> None:
        """memory_class='baton' without any baton_lifecycle dict → reject."""
        with self.assertRaises((ValueError, Exception)) as ctx:
            self.fabric.ingest(
                workspace_id="ws1", agent_id="atlas",
                text="No lifecycle at all.",
                step=1, scope="private",
                provenance=self._baton_prov(),
                memory_class="baton",
                # extra_payload omitted → no baton_lifecycle anywhere
            )
        self.assertIn("baton_lifecycle", str(ctx.exception).lower())

    def test_default_status_is_active(self) -> None:
        """When status is not provided at write, it defaults to 'active'
        per §5.2. Verified by inspecting the stored payload."""
        result = self.fabric.ingest(
            workspace_id="ws1", agent_id="atlas",
            text="Status default check.",
            step=1, scope="private",
            provenance=self._baton_prov(),
            memory_class="baton",
            extra_payload={"baton_lifecycle": self._complete_lifecycle()},
        )
        eid = int(result["eid"])
        ak = self.fabric._agent_key("ws1", "atlas")
        g = self.fabric.private_graphs[ak]
        ent = g.entities[eid]
        lifecycle = (ent.payload or {}).get("baton_lifecycle", {})
        self.assertEqual(lifecycle.get("status"), "active")


if __name__ == "__main__":
    unittest.main()
