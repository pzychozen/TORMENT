"""D1-S1 parity: the attribution helper layer does not alter scoring inputs.

Bounded S1 scope (no producer/consumer wiring): prove at the helper level that
(a) the affect scoring surfaces are live and deterministic, and (b) adding a
valid ``affect_attribution`` envelope to a hit does NOT change the values
produced by ``compute_continuity_bonuses`` — attribution is recorded, never a
scoring input (Ledger Observational-Boundary Doctrine §3). Full live query/trace
and identity-anchor parity become binding as stamping lands in S2/S3 and
cross-surface conformance closes in S5.

Deterministic inputs mirror tests/test_trace_continuity_parity.py and
tests/test_affect_state_mood_drift.py (keyword-classifier tags, neg set, spiral
gates), kept at the compute_continuity_bonuses() unit level.
"""

import os
import unittest

from torment_service.affect_attribution import SCHEMA_VERSION, read_affect_attribution
from torment_service.scoring import ContinuityContext, compute_continuity_bonuses

# Pin the scoring env so the captured baseline is deterministic regardless of
# ambient overrides; restored in tearDown to avoid cross-test leakage.
_PINNED_ENV = {
    "TORMENT_AFFECT_MATCH_BONUS": "0.05",
    "TORMENT_AFFECT_MIN_CONF": "0.40",
    "TORMENT_MOOD_DRIFT_QUERY_BONUS": "0.04",
    "TORMENT_MOOD_SPIRAL_ENABLE": "1",
    "TORMENT_MOOD_SPIRAL_MIN_NEG_DRIFTS": "2",
    "TORMENT_MOOD_SPIRAL_OLDER_THAN_STEPS": "250",
    "TORMENT_MOOD_SPIRAL_WINDOW_STEPS": "800",
    "TORMENT_MOOD_SPIRAL_PENALTY_MAX": "0.08",
}

_VALID_ENVELOPE = {
    "schema_version": SCHEMA_VERSION,
    "value_state": "set",
    "origin_kind": "inferred",
    "actor": "system",
    "actor_reference": None,
    "subject": "unknown",
    "confirmation": "unconfirmed",
    "confirmation_actor": None,
    "confirmation_actor_reference": None,
    "via": "ingest_affect_classifier",
}


class TestAffectAttributionParity(unittest.TestCase):
    def setUp(self):
        self._saved = {}
        for k, v in _PINNED_ENV.items():
            self._saved[k] = os.environ.get(k)
            os.environ[k] = v

    def tearDown(self):
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def _ctx(self):
        # Personal, negative-affect query; spiral_neg_recent >= min_drifts;
        # canonical_step high enough for an old hit to clear the age gate.
        return ContinuityContext.from_env(
            agent_id="agent",
            canonical_step=800,
            affect_personal=True,
            q_affect_tag="sad",
            q_affect_conf=0.8,
            spiral_neg_recent=3,
        )

    def _hit(self):
        # Negative-toned mood_drift hit, older than spiral_older_than. Foreign
        # agent_id isolates the affect surfaces from self-thread/self-anchor.
        return {
            "eid": 1,
            "scope": "private",
            "agent_id": "other",
            "type": "mood_drift",
            "affect_tag": "sad",
            "affect_conf": 0.8,
            "step": 10,
        }

    def test_affect_surfaces_are_live(self):
        r = compute_continuity_bonuses(self._hit(), self._ctx(), is_tool_result=False)
        self.assertGreater(r.affect_match_bonus, 0.0)
        self.assertGreater(r.mood_drift_bonus, 0.0)
        self.assertGreater(r.mood_spiral_penalty, 0.0)

    def test_envelope_presence_does_not_change_scoring(self):
        ctx = self._ctx()
        hit = self._hit()
        hit_env = {**hit, "affect_attribution": dict(_VALID_ENVELOPE)}
        r0 = compute_continuity_bonuses(hit, ctx, is_tool_result=False)
        r1 = compute_continuity_bonuses(hit_env, ctx, is_tool_result=False)
        self.assertEqual(r1.affect_match_bonus, r0.affect_match_bonus)
        self.assertEqual(r1.mood_drift_bonus, r0.mood_drift_bonus)
        self.assertEqual(r1.mood_spiral_penalty, r0.mood_spiral_penalty)
        self.assertEqual(r1.total, r0.total)

    def test_scoring_is_deterministic(self):
        ctx = self._ctx()
        hit = self._hit()
        a = compute_continuity_bonuses(hit, ctx, is_tool_result=False)
        b = compute_continuity_bonuses(hit, ctx, is_tool_result=False)
        self.assertEqual(
            (a.affect_match_bonus, a.mood_drift_bonus, a.mood_spiral_penalty, a.total),
            (b.affect_match_bonus, b.mood_drift_bonus, b.mood_spiral_penalty, b.total),
        )

    def test_read_shim_preserves_tag_conf(self):
        hit = self._hit()
        env_fallback = read_affect_attribution(hit)  # no envelope -> fallback
        self.assertEqual(env_fallback["origin_kind"], "recovered")
        self.assertEqual(env_fallback["value_state"], "set")
        # shim must not mutate the row's affect value
        self.assertEqual(hit["affect_tag"], "sad")
        self.assertEqual(hit["affect_conf"], 0.8)
        self.assertNotIn("affect_attribution", hit)

        hit_env = {**hit, "affect_attribution": dict(_VALID_ENVELOPE)}
        env_explicit = read_affect_attribution(hit_env)
        self.assertEqual(env_explicit["origin_kind"], "inferred")
        self.assertEqual(hit_env["affect_tag"], "sad")


if __name__ == "__main__":
    unittest.main()
