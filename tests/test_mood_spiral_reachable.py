"""Regression test: mood-spiral logic must be reachable in non-default workspaces.

The bug: fabric.query() checked `str(agent_id) in self.private_graphs`
but private_graphs is keyed by 'workspace/agent', so the check always
failed for any agent, silently disabling mood-spiral dampening.

Fix: use `ak in self.private_graphs` where ak = self._agent_key(ws, agent).
"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestMoodSpiralReachable(unittest.TestCase):
    """Verify that mood-spiral gate uses canonical agent keys.

    The bug: ``str(agent_id) in self.private_graphs`` always returned
    False because private_graphs is keyed by 'workspace/agent'.
    Fix: use ``ak in self.private_graphs`` where ak = _agent_key(ws, ag).

    We verify via source inspection to avoid query() timeouts in CI
    with the hash embedding provider.
    """

    def test_spiral_gate_source_uses_ak(self):
        """The mood-spiral membership check must use 'ak', not bare agent_id."""
        import inspect
        from torment_service.fabric import TormentFabric
        source = inspect.getsource(TormentFabric.query)
        # The old buggy pattern
        self.assertNotIn("str(agent_id) in self.private_graphs", source,
                         "Mood-spiral gate must not use bare agent_id for "
                         "private_graphs membership check")
        # The fix: should check 'ak in self.private_graphs'
        self.assertIn("ak in self.private_graphs", source,
                      "Mood-spiral gate should use canonical 'ak' key")

    def test_canonical_key_in_private_graphs(self):
        """After ingest, canonical key exists but bare agent_id does not."""
        from torment_service.fabric import TormentFabric
        tmpdir = tempfile.mkdtemp()
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        fabric = TormentFabric(data_dir=tmpdir)

        ws, agent = "custom_workspace", "test_agent"
        fabric.ingest(workspace_id=ws, agent_id=agent,
                      text="test memory", step=1)

        ak = fabric._agent_key(ws, agent)
        self.assertIn(ak, fabric.private_graphs,
                      "Canonical agent key must be present in private_graphs")
        self.assertNotIn(agent, fabric.private_graphs,
                         "Bare agent_id must NOT be a key in private_graphs")


class TestDriftKeyConstruction(unittest.TestCase):
    """Verify cognition/drift.py uses _agent_key, not manual f-string."""

    def test_drift_uses_agent_key_helper(self):
        """drift.py should call fabric._agent_key, not build the key manually."""
        import inspect
        from cognition.drift import make_live_drift_check
        source = inspect.getsource(make_live_drift_check)
        self.assertIn("_agent_key", source,
                      "drift.py should use _agent_key helper, not manual key construction")
        self.assertNotIn('f"{workspace_id}/{agent_id}"', source,
                         "drift.py should not use manual f-string key construction")


if __name__ == "__main__":
    unittest.main()
