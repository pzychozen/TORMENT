"""D1-S5b: generic user_confirmed feedback is isolated from affect confirmation.

Ratified contract falsifier (CLUSTER_5_PATH_C_Q3_D1_AFFECT_ATTRIBUTION_CONTRACT
§3 / §9 / §12):

    generic user_confirmed feedback must NEVER silently confirm affect
    generic user_confirmed  !=  affect confirmation

Production already satisfies this: ``TormentFabric.feedback`` consumes
``user_confirmed`` only as a generic memory-usefulness signal (``E_success``
-> identity-overlay / bridge-confidence nudges + a FEEDBACK log) and never
touches ``affect_tag`` / ``affect_conf`` / ``affect_attribution`` or sets
``confirmation``. These tests LOCK that boundary so a future refactor cannot
blur it. Test-only slice; no production change unless a violation is proven.

A genuine affect-confirmation event would be a separate, explicitly-authored
writer (none exists; the contract builds none). ``confirmation=confirmed`` also
requires BOTH confirmation_actor (class) and confirmation_actor_reference
(stable id); generic feedback supplies neither.
"""
import copy
import os
import shutil
import tempfile
import unittest

from torment_service.fabric import TormentFabric

SAD_TEXT = "I feel so sad, depressed and hopeless today"
ANGRY_TEXT = "I am so angry, furious and full of rage"
SAD_TEXT_2 = "I feel sad, lonely and empty inside"

_ENV = {
    "TORMENT_AFFECT_ENABLE": "1",
    "TORMENT_MOOD_DRIFT_ENABLE": "1",
    "TORMENT_MOOD_DRIFT_MIN_CONF": "0.0",
    "TORMENT_MOOD_DRIFT_MIN_GAP_STEPS": "1",
    "TORMENT_REINFORCE_SIM_THRESHOLD": "0",  # fresh spawns, no dedup
}


class _FeedbackBase(unittest.TestCase):
    def setUp(self):
        self._saved = {}
        for k, v in _ENV.items():
            self._saved[k] = os.environ.get(k)
            os.environ[k] = v
        self.tmp = tempfile.mkdtemp(prefix="torment_d1s5b_")
        self.fabric = TormentFabric(data_dir=self.tmp)
        self.fabric.get_workspace("ws")
        self.fabric.create_agent("ws", "agent")
        self.ak = self.fabric._agent_key("ws", "agent")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def _ingest(self, text, **kw):
        return self.fabric.ingest(workspace_id="ws", agent_id="agent", text=text, **kw)

    def _entities(self):
        return self.fabric.private_graphs[self.ak].entities

    def _payload(self, eid):
        return self._entities()[int(eid)].payload

    def _feedback(self, retrieved_ids, *, used_successfully=True, user_confirmed=True):
        return self.fabric.feedback(
            workspace_id="ws",
            agent_id="agent",
            retrieved_ids=list(retrieved_ids),
            used_successfully=used_successfully,
            user_confirmed=user_confirmed,
        )

    def _stamped_rows(self):
        """All private rows that carry an affect_attribution envelope."""
        return [
            (eid, e.payload)
            for eid, e in self._entities().items()
            if isinstance((e.payload or {}).get("affect_attribution"), dict)
        ]


class TestUserConfirmedDoesNotConfirmAffect(_FeedbackBase):
    def test_ingest_row_stays_unconfirmed_after_user_confirmed(self):
        eid = self._ingest(SAD_TEXT, step=1)["eid"]
        before = copy.deepcopy(self._payload(eid)["affect_attribution"])
        self.assertEqual(before["confirmation"], "unconfirmed")

        self._feedback([eid], used_successfully=True, user_confirmed=True)

        after = self._payload(eid)["affect_attribution"]
        self.assertEqual(after, before)  # envelope unchanged verbatim
        self.assertEqual(after["confirmation"], "unconfirmed")
        self.assertIsNone(after["confirmation_actor"])
        self.assertIsNone(after["confirmation_actor_reference"])

    def test_mood_drift_row_stays_unconfirmed_after_user_confirmed(self):
        # Drive a mood_drift transition row.
        self._ingest(SAD_TEXT, step=10)
        self._ingest(ANGRY_TEXT, step=200)
        self._ingest(SAD_TEXT_2, step=400)
        mood = [
            (eid, p) for eid, p in self._stamped_rows()
            if p.get("type") == "mood_drift"
        ]
        self.assertTrue(mood, "expected at least one stamped mood_drift row")
        ids = [eid for eid, _ in mood]
        before = {eid: copy.deepcopy(p["affect_attribution"]) for eid, p in mood}

        self._feedback(ids, used_successfully=True, user_confirmed=True)

        for eid in ids:
            env = self._payload(eid)["affect_attribution"]
            self.assertEqual(env, before[eid])
            self.assertEqual(env["confirmation"], "unconfirmed")
            self.assertIsNone(env["confirmation_actor"])
            self.assertIsNone(env["confirmation_actor_reference"])

    def test_no_row_anywhere_gains_confirmed_or_confirmer(self):
        eid = self._ingest(SAD_TEXT, step=1)["eid"]
        self._ingest("The quarterly report lists inventory counts.", step=2)
        self._feedback([eid], used_successfully=True, user_confirmed=True)
        for _eid, p in self._stamped_rows():
            env = p["affect_attribution"]
            self.assertNotEqual(env["confirmation"], "confirmed")
            self.assertIsNone(env["confirmation_actor"])
            self.assertIsNone(env["confirmation_actor_reference"])


class TestFeedbackDoesNotWriteAffectFields(_FeedbackBase):
    def test_affect_fields_unchanged_by_feedback(self):
        eid = self._ingest(SAD_TEXT, step=1)["eid"]
        p = self._payload(eid)
        before = {
            "affect_tag": copy.deepcopy(p.get("affect_tag")),
            "affect_conf": copy.deepcopy(p.get("affect_conf")),
            "affect_attribution": copy.deepcopy(p.get("affect_attribution")),
        }
        self._feedback([eid], used_successfully=True, user_confirmed=True)
        p2 = self._payload(eid)
        self.assertEqual(p2.get("affect_tag"), before["affect_tag"])
        self.assertEqual(p2.get("affect_conf"), before["affect_conf"])
        self.assertEqual(p2.get("affect_attribution"), before["affect_attribution"])


class TestGenericFeedbackPathStillWorks(_FeedbackBase):
    def test_E_success_path_is_exercised(self):
        # used_successfully + user_confirmed drives E_success, which nudges the
        # identity overlay (reinforcement_gain up). Proves the generic feedback
        # behavior remains intact — isolation is from affect, not a no-op.
        eid = self._ingest(SAD_TEXT, step=1)["eid"]
        before = float(
            self.fabric.create_agent("ws", "agent").overlay.get("reinforcement_gain", 0.0)
        )
        self._feedback([eid], used_successfully=True, user_confirmed=True)
        after = float(
            self.fabric.create_agent("ws", "agent").overlay.get("reinforcement_gain", 0.0)
        )
        self.assertGreater(after, before)


class TestRepeatedAndNegativeControl(_FeedbackBase):
    def test_repeated_user_confirmed_cannot_confirm_affect(self):
        eid = self._ingest(SAD_TEXT, step=1)["eid"]
        for _ in range(3):
            self._feedback([eid], used_successfully=True, user_confirmed=True)
        env = self._payload(eid)["affect_attribution"]
        self.assertEqual(env["confirmation"], "unconfirmed")
        self.assertIsNone(env["confirmation_actor"])

    def test_negative_control_user_confirmed_false_leaves_attribution_unchanged(self):
        eid = self._ingest(SAD_TEXT, step=1)["eid"]
        before = copy.deepcopy(self._payload(eid)["affect_attribution"])
        self._feedback([eid], used_successfully=True, user_confirmed=False)
        self.assertEqual(self._payload(eid)["affect_attribution"], before)
        self.assertEqual(
            self._payload(eid)["affect_attribution"]["confirmation"], "unconfirmed"
        )


if __name__ == "__main__":
    unittest.main()
