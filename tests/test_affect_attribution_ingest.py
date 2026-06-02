"""D1-S2 producer tests: TormentFabric.ingest() affect-attribution stamping.

The ingest fresh-spawn branch stamps an ``affect_attribution`` envelope iff affect
classification COMPLETED SUCCESSFULLY:

    set      = classifier completed and produced an affect value
    unset    = classifier completed and produced no affect value
    disabled = classifier intentionally did not run        -> NO stamp
    failed   = classifier raised under fail-soft           -> NO stamp

unset != not evaluated.

Scope is mechanism-defined, not caller-defined: every fresh row written through
the ingest spawn branch is covered. The tool-result / collective-echo /
cognition-writeback cases below are examples that prove affect-value lineage
(affect_attribution) coexists with row lineage (ProvenanceV1), not an allowlist.
Adjacent producers (mood_drift, reinforce-in-place) stay unstamped.
"""

import os
import shutil
import tempfile
import unittest
from unittest import mock

from torment_service.affect_attribution import read_affect_attribution
from torment_service.fabric import TormentFabric
from torment_service.provenance_v1 import ProvenanceV1

# Strong, keyword-rich affect text (mirrors test_affect_state_mood_drift.py).
SAD_TEXT = "I feel so sad, depressed and hopeless today"
ANGRY_TEXT = "I am so angry, furious and full of rage"
SAD_TEXT_2 = "I feel sad, lonely and empty inside"
# Substantive but affect-neutral content: classifier completes, finds nothing.
NEUTRAL_TEXT = "The quarterly report lists the inventory counts for each warehouse region."

_BASE_ENV = {
    "TORMENT_AFFECT_ENABLE": "1",
    "TORMENT_MOOD_DRIFT_ENABLE": "1",
    "TORMENT_REINFORCE_SIM_THRESHOLD": "0",  # default: fresh spawn, no dedup
}


class _IngestBase(unittest.TestCase):
    ENV = _BASE_ENV

    def setUp(self):
        self._saved = {}
        for k, v in self.ENV.items():
            self._saved[k] = os.environ.get(k)
            os.environ[k] = v
        self.tmp = tempfile.mkdtemp(prefix="torment_d1s2_ingest_")
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

    def _payload(self, eid):
        return self.fabric.private_graphs[self.ak].entities[int(eid)].payload


# --- T1 / T2: producer happy path -----------------------------------------

class TestProducerHappyPath(_IngestBase):
    def test_T1_affect_present_stamps_set_envelope(self):
        eid = self._ingest(SAD_TEXT, step=1)["eid"]
        self.assertIsNotNone(eid, "affect ingest should store a row")
        p = self._payload(eid)
        self.assertIsNotNone(p.get("affect_tag"))
        env = p["affect_attribution"]
        self.assertEqual(env["value_state"], "set")
        self.assertEqual(env["origin_kind"], "inferred")
        self.assertEqual(env["actor"], "system")
        self.assertIsNone(env["actor_reference"])
        self.assertEqual(env["subject"], "unknown")
        self.assertEqual(env["confirmation"], "unconfirmed")
        self.assertIsNone(env["confirmation_actor"])
        self.assertEqual(env["via"], "ingest_affect_classifier")

    def test_T2_completed_no_signal_stamps_unset_envelope(self):
        eid = self._ingest(NEUTRAL_TEXT, step=1)["eid"]
        self.assertIsNotNone(eid, "neutral ingest should still store a row")
        p = self._payload(eid)
        self.assertIsNone(p.get("affect_tag"))
        env = p["affect_attribution"]
        self.assertEqual(env["value_state"], "unset")
        self.assertEqual(env["origin_kind"], "inferred")
        self.assertEqual(env["via"], "ingest_affect_classifier")


# --- T3 / T4 / T5: affect lineage coexists with row lineage ----------------

class TestLineageOrthogonality(_IngestBase):
    def _assert_classifier_envelope(self, p):
        env = p["affect_attribution"]
        self.assertEqual(env["origin_kind"], "inferred")
        self.assertEqual(env["actor"], "system")
        self.assertEqual(env["via"], "ingest_affect_classifier")

    def test_T3_tool_result_lineage_coexists(self):
        d = ProvenanceV1.for_tool_result(tool_name="web_search", step=1).to_dict()
        eid = self._ingest(SAD_TEXT, provenance=d, supplied_summary=SAD_TEXT)["eid"]
        self.assertIsNotNone(eid)
        p = self._payload(eid)
        self.assertEqual(p["provenance"]["source_type"], d["source_type"])
        self._assert_classifier_envelope(p)

    def test_T4_collective_echo_lineage_coexists(self):
        d = ProvenanceV1.for_collective_echo(step=0).to_dict()
        text = "[collective echo] convergence about feeling sad and hopeless"
        eid = self._ingest(text, provenance=d, supplied_summary=text)["eid"]
        self.assertIsNotNone(eid)
        p = self._payload(eid)
        self.assertEqual(p["provenance"]["source_type"], d["source_type"])
        self._assert_classifier_envelope(p)

    def test_T5_cognition_writeback_lineage_coexists(self):
        d = ProvenanceV1.for_cognition_writeback(
            source_role="archivist_writeback", parent_eids=[], step=1
        ).to_dict()
        eid = self._ingest(SAD_TEXT, provenance=d, supplied_summary=SAD_TEXT)["eid"]
        self.assertIsNotNone(eid)
        p = self._payload(eid)
        self.assertEqual(p["provenance"]["write_path"], d["write_path"])
        self._assert_classifier_envelope(p)


# --- T6: reinforce-in-place must not re-stamp ------------------------------

class TestReinforceNoRestamp(_IngestBase):
    ENV = {**_BASE_ENV, "TORMENT_REINFORCE_SIM_THRESHOLD": "0.92"}

    def test_T6_reinforce_does_not_mutate_or_add_stamp(self):
        eid = self._ingest(SAD_TEXT, step=1)["eid"]
        self.assertIsNotNone(eid)
        env_before = dict(self._payload(eid)["affect_attribution"])

        # Identical text -> identical embedding -> reinforce-in-place, not a new spawn.
        self._ingest(SAD_TEXT, step=2)

        p = self._payload(eid)
        # reinforcement_count proves the reinforce branch ran (not a second spawn).
        self.assertGreaterEqual(
            int(p.get("reinforcement_count", 0)), 1,
            "expected reinforce-in-place to have triggered",
        )
        # The reinforce branch never builds _internal_ep, so the envelope is the
        # single one produced at first write — unchanged, not re-stamped.
        self.assertEqual(p["affect_attribution"], env_before)


# --- T7: internal-wins integrity -------------------------------------------

class TestInternalWins(_IngestBase):
    def test_T7_forged_caller_envelope_loses_to_internal_stamp(self):
        forged = {
            "schema_version": "1.0",
            "value_state": "set",
            "origin_kind": "asserted",
            "actor": "user",
            "actor_reference": "user:attacker",
            "subject": "user",
            "confirmation": "confirmed",
            "confirmation_actor": "user",
            "confirmation_actor_reference": "user:attacker",
            "via": "ingest_affect_classifier",
        }
        eid = self._ingest(
            SAD_TEXT, step=1, extra_payload={"affect_attribution": forged}
        )["eid"]
        self.assertIsNotNone(eid)
        env = self._payload(eid)["affect_attribution"]
        # Internal stamp wins: the forged confirmed/asserted claim is gone.
        self.assertEqual(env["origin_kind"], "inferred")
        self.assertEqual(env["confirmation"], "unconfirmed")
        self.assertIsNone(env["confirmation_actor"])
        self.assertIsNone(env["confirmation_actor_reference"])


# --- T8: a stamped row reads as inferred, not legacy fallback ---------------

class TestReadRoundTrip(_IngestBase):
    def test_T8_stamped_row_read_avoids_legacy_fallback(self):
        eid = self._ingest(SAD_TEXT, step=1)["eid"]
        self.assertIsNotNone(eid)
        env = read_affect_attribution(self._payload(eid))
        self.assertEqual(env["origin_kind"], "inferred")
        self.assertEqual(env["via"], "ingest_affect_classifier")


# --- T10: mood_drift stays unstamped (scope boundary; D1-S3 territory) ------

class TestScopeBoundaryMoodDrift(_IngestBase):
    ENV = {
        **_BASE_ENV,
        "TORMENT_MOOD_DRIFT_ENABLE": "1",
        "TORMENT_MOOD_DRIFT_MIN_CONF": "0.0",
        "TORMENT_MOOD_DRIFT_MIN_GAP_STEPS": "1",
    }

    def test_T10_mood_drift_rows_are_not_stamped(self):
        # Alternating tags with a step gap drive mood_drift emission.
        self._ingest(SAD_TEXT, step=10)
        self._ingest(ANGRY_TEXT, step=200)
        self._ingest(SAD_TEXT_2, step=400)
        ents = self.fabric.private_graphs[self.ak].entities
        mood = [
            e for e in ents.values()
            if (getattr(e, "payload", {}) or {}).get("type") == "mood_drift"
        ]
        self.assertTrue(mood, "expected at least one mood_drift row to be emitted")
        for e in mood:
            self.assertNotIn(
                "affect_attribution", e.payload,
                "mood_drift is D1-S3 scope and must remain unstamped in S2",
            )


# --- T12a / T12b / T12c: NOT-EVALUATED states earn no stamp -----------------

class TestNotEvaluatedDisabled(_IngestBase):
    ENV = {**_BASE_ENV, "TORMENT_AFFECT_ENABLE": "0"}

    def test_T12a_disabled_classifier_emits_no_stamp(self):
        eid = self._ingest(SAD_TEXT, step=1)["eid"]
        self.assertIsNotNone(eid)
        p = self._payload(eid)
        # Classifier intentionally did not run -> not evaluated -> no stamp.
        self.assertNotIn("affect_attribution", p)
        self.assertIsNone(p.get("affect_tag"))

    def test_T12b_disabled_row_reads_as_recovered_KNOWN_GAP(self):
        # CHARACTERIZATION of current behavior, NOT approved semantics:
        # an unstamped fresh row currently reads back through the legacy fallback
        # as recovered/migration/legacy_read_fallback. This is inaccurate for a
        # freshly created modern row and is the named deferred-vocabulary gap
        # ("not evaluated" has no posture yet). Locked here so a future slice that
        # resolves it must consciously update this expectation.
        eid = self._ingest(SAD_TEXT, step=1)["eid"]
        env = read_affect_attribution(self._payload(eid))
        self.assertEqual(env["origin_kind"], "recovered")   # KNOWN-GAP, not endorsed
        self.assertEqual(env["actor"], "migration")          # KNOWN-GAP, not endorsed
        self.assertEqual(env["via"], "legacy_read_fallback")  # KNOWN-GAP, not endorsed


class TestNotEvaluatedFailed(_IngestBase):
    def test_T12c_classifier_exception_emits_no_stamp(self):
        # Affect stays ENABLED, but classify_affect raises. Fail-soft swallows it;
        # this is the `failed` (not `unset`) state and must NOT be stamped — without
        # this guard we could "fix" the disabled flag yet still emit a false unset.
        def _boom(_text):
            raise RuntimeError("classifier blew up")

        with mock.patch("torment_service.fabric.classify_affect", side_effect=_boom):
            eid = self._ingest(SAD_TEXT, step=1)["eid"]
        self.assertIsNotNone(eid)
        p = self._payload(eid)
        self.assertNotIn("affect_attribution", p)
        self.assertIsNone(p.get("affect_tag"))


if __name__ == "__main__":
    unittest.main()
