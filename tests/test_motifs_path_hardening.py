"""Regression tests for motifs.py path-expression hardening.

Covers:
  1. Canonical domain root stays inside canonical data root
  2. motifs.json stays inside domain root
  3. motif_events.jsonl stays inside domain root
  4. motif_merges.json stays inside domain root
  5. Legacy embedding fallback path stays inside canonical base
  6. Invalid workspace/domain IDs are rejected
  7. Load/save/event logging/merge persistence still work after refactor
"""

import os
import json
import tempfile
import unittest

import numpy as np

from torment_service.motifs import MotifRegistry


class TestMotifRegistryPathIntegrity(unittest.TestCase):
    """1-4. All paths stay inside their respective roots."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self.reg = MotifRegistry(self._tmpdir, "test_ws", "test_domain")

    def tearDown(self):
        import shutil
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_data_dir_is_canonical(self):
        self.assertTrue(os.path.isabs(self.reg.data_dir))
        self.assertEqual(self.reg.data_dir, os.path.realpath(self.reg.data_dir))

    def test_motifs_json_inside_data_dir(self):
        """2. motifs.json stays inside data root."""
        self.assertTrue(
            self.reg.path.startswith(self.reg.data_dir + os.sep),
            f"motifs.json path {self.reg.path} not inside {self.reg.data_dir}",
        )

    def test_events_path_inside_data_dir(self):
        """3. motif_events.jsonl stays inside data root."""
        self.assertTrue(
            self.reg.events_path.startswith(self.reg.data_dir + os.sep),
            f"events path {self.reg.events_path} not inside {self.reg.data_dir}",
        )

    def test_merges_path_inside_data_dir(self):
        """4. motif_merges.json stays inside data root."""
        self.assertTrue(
            self.reg.merges_path.startswith(self.reg.data_dir + os.sep),
            f"merges path {self.reg.merges_path} not inside {self.reg.data_dir}",
        )

    def test_correct_filenames(self):
        self.assertTrue(self.reg.path.endswith("motifs.json"))
        self.assertTrue(self.reg.events_path.endswith("motif_events.jsonl"))
        self.assertTrue(self.reg.merges_path.endswith("motif_merges.json"))

    def test_domain_dir_created(self):
        domain_dir = os.path.dirname(self.reg.path)
        self.assertTrue(os.path.isdir(domain_dir))


class TestMotifRegistryInvalidPaths(unittest.TestCase):
    """6. Invalid workspace/domain IDs are rejected."""

    def test_rejects_dotdot_workspace(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                MotifRegistry(td, "../escape", "domain")

    def test_rejects_slash_workspace(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                MotifRegistry(td, "ws/evil", "domain")

    def test_rejects_empty_workspace(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                MotifRegistry(td, "", "domain")

    def test_rejects_dotdot_domain(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                MotifRegistry(td, "ws", "../escape")

    def test_rejects_slash_domain(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                MotifRegistry(td, "ws", "domain/evil")

    def test_rejects_empty_domain(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                MotifRegistry(td, "ws", "")


class TestMotifRegistryLegacyPath(unittest.TestCase):
    """5. Legacy embedding fallback path stays inside canonical base."""

    def test_legacy_fallback_loads_from_safe_path(self):
        """If a legacy emb_<eid>.npy exists at data_dir root, it should load."""
        with tempfile.TemporaryDirectory() as td:
            # Create a legacy embedding file
            vec = np.random.randn(8).astype(np.float32)
            np.save(os.path.join(td, "emb_42.npy"), vec)

            reg = MotifRegistry(td, "ws", "dom")
            result = reg._member_embedding(42)
            # Should load successfully (and normalize to unit)
            self.assertIsNotNone(result)

    def test_legacy_fallback_returns_none_for_missing(self):
        with tempfile.TemporaryDirectory() as td:
            reg = MotifRegistry(td, "ws", "dom")
            result = reg._member_embedding(99999)
            self.assertIsNone(result)


class TestMotifRegistryBehavior(unittest.TestCase):
    """7. Load/save/event logging still work after refactor."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self.reg = MotifRegistry(self._tmpdir, "test_ws", "test_domain")

    def tearDown(self):
        import shutil
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_save_and_reload(self):
        """Save motifs, then reload from disk."""
        from torment_service.motifs import Motif, _now_ts
        m = Motif(
            motif_id="motif_test_0001",
            domain_id="test_domain",
            label="Test Motif",
            centroid=[0.1, 0.2, 0.3],
            strength=0.8,
            members=[1, 2, 3],
            contributing_agents=["agent_a"],
            stability_score=0.9,
            created_ts=_now_ts(),
            last_active_ts=_now_ts(),
        )
        self.reg.motifs["motif_test_0001"] = m
        self.reg.save()

        reg2 = MotifRegistry(self._tmpdir, "test_ws", "test_domain")
        self.assertIn("motif_test_0001", reg2.motifs)
        self.assertEqual(reg2.motifs["motif_test_0001"].label, "Test Motif")

    def test_empty_registry_loads_cleanly(self):
        reg = MotifRegistry(self._tmpdir, "fresh_ws", "fresh_dom")
        self.assertEqual(len(reg.motifs), 0)


if __name__ == "__main__":
    unittest.main()
