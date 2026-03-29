"""
tests/test_character_selfstate.py — Character self-state assembly

Tests for:
    - build_self_state with seeded agent (full state)
    - build_self_state with non-seeded agent (minimal state)
    - build_self_state with phase timer data
    - build_self_state with SRG flag
    - CharacterSelfState populated from real CharacterState + Seed data
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.character import (
    CharacterSeed,
    CharacterState,
    CharacterStore,
    build_self_state,
)
from torment_service.collective_models import CharacterSelfState


class TestBuildSelfStateNoSeed(unittest.TestCase):
    """Agents without a character seed should get minimal state."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.store = CharacterStore(self.tmp)

    def test_no_seed_returns_minimal(self):
        result = build_self_state("ws1", "agent_noseed", self.store, seed_id=None)
        self.assertEqual(result["workspace_id"], "ws1")
        self.assertEqual(result["agent_id"], "agent_noseed")
        self.assertIsNone(result["seed_id"])
        self.assertEqual(result["drift_score"], 0.0)
        self.assertEqual(result["drift_direction"], "stable")
        self.assertEqual(result["core_count"], 0)

    def test_empty_seed_id(self):
        result = build_self_state("ws1", "agent_empty", self.store, seed_id="")
        self.assertIsNone(result["seed_id"])


class TestBuildSelfStateSeeded(unittest.TestCase):
    """Agents with a character seed should get full state."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.store = CharacterStore(self.tmp)

        # Create a seed
        self.seed = CharacterSeed(
            seed_id="ryuki_v1",
            character_name="Ryuki Nox",
            seed_text="Fierce guardian bonded across dimensions.",
            seed_motif_id="m_ryuki_core",
            seed_eids=[1, 2, 3],
            created_ts=int(time.time()),
        )
        self.store.save_seed("ws1", self.seed)

        # Create a character state
        self.state = CharacterState(
            workspace_id="ws1",
            agent_id="ryuki",
            seed_id="ryuki_v1",
            drift_score=-0.15,
            drift_direction="away_seed",
            distance_to_seed=0.28,
            seed_basin_role="basin",
            seed_basin_phi=0.82,
            seed_basin_kappa=0.45,
            seed_basin_tension=0.12,
            core_count=5,
            relational_count=42,
            situational_count=130,
        )
        self.store.save_state("ws1", self.state)

    def test_full_state(self):
        result = build_self_state("ws1", "ryuki", self.store, seed_id="ryuki_v1")
        self.assertEqual(result["seed_id"], "ryuki_v1")
        self.assertEqual(result["character_name"], "Ryuki Nox")
        self.assertEqual(result["seed_motif_id"], "m_ryuki_core")
        self.assertAlmostEqual(result["drift_score"], -0.15)
        self.assertEqual(result["drift_direction"], "away_seed")
        self.assertAlmostEqual(result["distance_to_seed"], 0.28)
        self.assertEqual(result["seed_basin_role"], "basin")
        self.assertEqual(result["core_count"], 5)
        self.assertEqual(result["relational_count"], 42)
        self.assertEqual(result["situational_count"], 130)

    def test_seed_exists_but_no_state(self):
        """Agent has a seed but no drift measurements yet."""
        result = build_self_state("ws1", "new_agent", self.store, seed_id="ryuki_v1")
        self.assertEqual(result["seed_id"], "ryuki_v1")
        self.assertEqual(result["character_name"], "Ryuki Nox")
        # Drift should be default zeros
        self.assertEqual(result["drift_score"], 0.0)
        self.assertEqual(result["drift_direction"], "stable")
        self.assertEqual(result["core_count"], 0)

    def test_with_phase_timers(self):
        timers = {
            "ryuki": {
                "phase_duration_steps": 85,
                "corridor_duration_steps": 12,
                "cycle_stage": "S3",
                "identity_state": "s5",
            }
        }
        result = build_self_state(
            "ws1", "ryuki", self.store,
            seed_id="ryuki_v1",
            phase_timers=timers,
        )
        self.assertEqual(result["phase_duration_steps"], 85)
        self.assertEqual(result["corridor_duration_steps"], 12)
        self.assertEqual(result["last_cycle_stage"], "S3")
        self.assertEqual(result["last_identity_state"], "s5")

    def test_without_phase_timers(self):
        result = build_self_state("ws1", "ryuki", self.store, seed_id="ryuki_v1")
        self.assertIsNone(result["phase_duration_steps"])
        self.assertIsNone(result["corridor_duration_steps"])
        self.assertIsNone(result["last_cycle_stage"])

    def test_phase_timers_missing_agent(self):
        """Phase timers exist but not for this agent."""
        timers = {"other_agent": {"phase_duration_steps": 50}}
        result = build_self_state(
            "ws1", "ryuki", self.store,
            seed_id="ryuki_v1",
            phase_timers=timers,
        )
        self.assertIsNone(result["phase_duration_steps"])

    def test_srg_flag(self):
        result_off = build_self_state("ws1", "ryuki", self.store, seed_id="ryuki_v1", srg_enable=False)
        result_on = build_self_state("ws1", "ryuki", self.store, seed_id="ryuki_v1", srg_enable=True)
        self.assertFalse(result_off["srg_enabled"])
        self.assertTrue(result_on["srg_enabled"])

    def test_result_is_serializable(self):
        """Result should be a plain dict that JSON-serializes cleanly."""
        result = build_self_state("ws1", "ryuki", self.store, seed_id="ryuki_v1")
        serialized = json.dumps(result)
        deserialized = json.loads(serialized)
        self.assertEqual(result["seed_id"], deserialized["seed_id"])
        self.assertEqual(result["drift_score"], deserialized["drift_score"])

    def test_updated_ts_is_recent(self):
        before = int(time.time())
        result = build_self_state("ws1", "ryuki", self.store, seed_id="ryuki_v1")
        after = int(time.time())
        self.assertGreaterEqual(result["updated_ts"], before)
        self.assertLessEqual(result["updated_ts"], after)


if __name__ == "__main__":
    unittest.main()
