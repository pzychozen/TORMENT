# -*- coding: utf-8 -*-
"""
Workspace Isolation Regression Tests
=====================================
Verifies that agents with identical agent_ids across different workspaces
do NOT leak state, retrieval results, or memory data between workspaces.

Root cause tested: in-memory dicts (private_graphs, agent_states,
_phase_timers, _deep_stores) were previously keyed by bare agent_id,
so "atlas" in workspace "wsA" and "atlas" in workspace "wsB" would
silently collide.  The fix uses composite keys via _agent_key().

Coverage:
  1. Same agent_id in two workspaces → separate identity.json
  2. Ingest in workspace A does not alter state in workspace B
  3. Query in workspace B never returns workspace A rows
  4. Seed persistence is workspace-scoped
"""

import os
import shutil
import sys
import tempfile
import types
import unittest


def _ensure_fastapi_stub():
    """Create a minimal fastapi stub if the real package is unavailable."""
    if "fastapi" not in sys.modules:
        mod = types.ModuleType("fastapi")

        class _HTTPException(Exception):
            def __init__(self, status_code=500, detail=""):
                self.status_code = status_code
                self.detail = detail
                super().__init__(detail)

        mod.HTTPException = _HTTPException
        sys.modules["fastapi"] = mod
        sys.modules["fastapi.responses"] = types.ModuleType("fastapi.responses")


def _setenv():
    os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
    os.environ["TORMENT_CHARACTER_ENABLE"] = "0"
    os.environ["TORMENT_CHECKPOINT_ENABLE"] = "0"
    os.environ["TORMENT_COMPRESS_ENABLE"] = "0"
    os.environ["TORMENT_SRG_ENABLE"] = "0"
    os.environ["TORMENT_HIVEMIND_ENABLE"] = "0"


_ensure_fastapi_stub()
_setenv()

from torment_service.fabric import TormentFabric


WS_A = "workspace_alpha"
WS_B = "workspace_beta"
AGENT_ID = "atlas"  # same agent_id in both workspaces


class TestWorkspaceIsolation(unittest.TestCase):
    """Agents with the same agent_id across workspaces must be fully isolated."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="torment_ws_iso_")
        self.fabric = TormentFabric(data_dir=self.tmpdir)

        # Create both workspaces and agents
        self.fabric.get_workspace(WS_A, domains=["research"])
        self.fabric.get_workspace(WS_B, domains=["research"])

        seed_a = {
            "seed_text": "Alpha workspace agent — analytical researcher.",
            "seed_id": "atlas_alpha_v1",
            "core_traits": ["analytical"],
            "coupling_mode": "read_only",
            "coupling_strength": 0.25,
        }
        seed_b = {
            "seed_text": "Beta workspace agent — creative storyteller.",
            "seed_id": "atlas_beta_v1",
            "core_traits": ["creative"],
            "coupling_mode": "read_only",
            "coupling_strength": 0.25,
        }

        self.ident_a = self.fabric.create_agent(WS_A, AGENT_ID, seed=seed_a)
        self.ident_b = self.fabric.create_agent(WS_B, AGENT_ID, seed=seed_b)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # ── Test 1: Identity is workspace-scoped ──

    def test_identity_files_are_separate(self):
        """Each workspace stores its own identity.json for the same agent_id."""
        path_a = os.path.join(
            self.tmpdir, "workspaces", WS_A, "agents", AGENT_ID, "identity.json"
        )
        path_b = os.path.join(
            self.tmpdir, "workspaces", WS_B, "agents", AGENT_ID, "identity.json"
        )
        self.assertTrue(os.path.exists(path_a), "identity.json missing for workspace A")
        self.assertTrue(os.path.exists(path_b), "identity.json missing for workspace B")

    def test_seed_text_persisted_per_workspace(self):
        """Seed text from each workspace is stored independently."""
        self.assertIn("Alpha", self.ident_a.seed.get("seed_text", ""))
        self.assertIn("Beta", self.ident_b.seed.get("seed_text", ""))

    # ── Test 2: In-memory dicts use composite keys ──

    def test_private_graphs_use_composite_key(self):
        """private_graphs must have separate entries for each workspace."""
        key_a = self.fabric._agent_key(WS_A, AGENT_ID)
        key_b = self.fabric._agent_key(WS_B, AGENT_ID)
        self.assertIn(key_a, self.fabric.private_graphs)
        self.assertIn(key_b, self.fabric.private_graphs)
        self.assertIsNot(
            self.fabric.private_graphs[key_a],
            self.fabric.private_graphs[key_b],
            "Both workspaces share the same MemoryGraph instance — leakage!",
        )

    def test_agent_states_use_composite_key(self):
        """agent_states must have separate entries for each workspace."""
        key_a = self.fabric._agent_key(WS_A, AGENT_ID)
        key_b = self.fabric._agent_key(WS_B, AGENT_ID)
        self.assertIn(key_a, self.fabric.agent_states)
        self.assertIn(key_b, self.fabric.agent_states)

    # ── Test 3: Ingest isolation ──

    def test_ingest_does_not_leak_across_workspaces(self):
        """Ingesting into workspace A must not appear in workspace B queries."""
        # Ingest a distinctive memory into workspace A only
        self.fabric.ingest(
            workspace_id=WS_A,
            agent_id=AGENT_ID,
            text="Unique alpha memory: quantum entanglement research breakthrough XYZ-7742",
            step=1,
            domain_id="research",
        )

        # Query workspace B for the same text — should find nothing relevant
        result_b = self.fabric.query(
            workspace_id=WS_B,
            agent_id=AGENT_ID,
            query_text="quantum entanglement XYZ-7742",
            top_k=5,
        )

        # Check that no workspace-A content leaked into workspace-B results
        all_texts = []
        for hit in result_b.get("results", []):
            text = hit.get("text", "") or hit.get("summary", "")
            all_texts.append(text)

        leaked = any("XYZ-7742" in t for t in all_texts)
        self.assertFalse(
            leaked,
            f"Workspace A memory leaked into workspace B query results: {all_texts}",
        )

    def test_ingest_stays_in_own_workspace(self):
        """Memory ingested into workspace A is retrievable from workspace A."""
        self.fabric.ingest(
            workspace_id=WS_A,
            agent_id=AGENT_ID,
            text="Alpha-only marker: resonance-cascade-alpha-9999",
            step=1,
            domain_id="research",
        )

        result_a = self.fabric.query(
            workspace_id=WS_A,
            agent_id=AGENT_ID,
            query_text="resonance-cascade-alpha-9999",
            top_k=5,
        )

        all_texts = []
        for hit in result_a.get("results", []):
            text = hit.get("text", "") or hit.get("summary", "")
            all_texts.append(text)

        found = any("alpha-9999" in t.lower() for t in all_texts)
        self.assertTrue(
            found,
            f"Ingested memory not found in own workspace: {all_texts}",
        )

    # ── Test 4: Bidirectional isolation ──

    def test_bidirectional_isolation(self):
        """Ingest into both workspaces, verify each only sees its own data."""
        self.fabric.ingest(
            workspace_id=WS_A,
            agent_id=AGENT_ID,
            text="Alpha-signal: photon-lattice-alignment study",
            step=1,
            domain_id="research",
        )
        self.fabric.ingest(
            workspace_id=WS_B,
            agent_id=AGENT_ID,
            text="Beta-signal: narrative-arc-compression technique",
            step=1,
            domain_id="research",
        )

        result_a = self.fabric.query(
            workspace_id=WS_A,
            agent_id=AGENT_ID,
            query_text="photon lattice alignment",
            top_k=5,
        )
        result_b = self.fabric.query(
            workspace_id=WS_B,
            agent_id=AGENT_ID,
            query_text="narrative arc compression",
            top_k=5,
        )

        texts_a = [h.get("text", "") for h in result_a.get("results", [])]
        texts_b = [h.get("text", "") for h in result_b.get("results", [])]

        # A should not contain B's data
        a_has_beta = any("narrative-arc" in t for t in texts_a)
        self.assertFalse(a_has_beta, f"Beta data leaked into Alpha: {texts_a}")

        # B should not contain A's data
        b_has_alpha = any("photon-lattice" in t for t in texts_b)
        self.assertFalse(b_has_alpha, f"Alpha data leaked into Beta: {texts_b}")

    # ── Test 5: State isolation after kernel processing ──

    def test_kernel_state_isolation(self):
        """Kernel state (agent_states) must be independent per workspace."""
        key_a = self.fabric._agent_key(WS_A, AGENT_ID)
        key_b = self.fabric._agent_key(WS_B, AGENT_ID)

        # Ingest multiple steps into workspace A to evolve its kernel state
        for i in range(5):
            self.fabric.ingest(
                workspace_id=WS_A,
                agent_id=AGENT_ID,
                text=f"Alpha step {i}: evolving kernel state with distinct content",
                step=i + 1,
                domain_id="research",
            )

        state_a = self.fabric.agent_states[key_a]
        state_b = self.fabric.agent_states[key_b]

        # States should not be the same object
        self.assertIsNot(state_a, state_b, "Kernel states are the same object — leakage!")


class TestAgentKeyHelper(unittest.TestCase):
    """Verify the _agent_key helper produces correct composite keys."""

    def test_basic_key_format(self):
        key = TormentFabric._agent_key("my_workspace", "my_agent")
        self.assertEqual(key, "my_workspace/my_agent")

    def test_different_workspaces_different_keys(self):
        k1 = TormentFabric._agent_key("ws1", "atlas")
        k2 = TormentFabric._agent_key("ws2", "atlas")
        self.assertNotEqual(k1, k2)

    def test_same_workspace_different_agents(self):
        k1 = TormentFabric._agent_key("ws1", "atlas")
        k2 = TormentFabric._agent_key("ws1", "vanta")
        self.assertNotEqual(k1, k2)


if __name__ == "__main__":
    unittest.main()
