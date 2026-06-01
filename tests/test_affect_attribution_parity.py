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
import shutil
import tempfile
import unittest

from torment_service.affect_attribution import SCHEMA_VERSION, read_affect_attribution
from torment_service.fabric import TormentFabric
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


# --- Deterministic ingest fixtures (mirroring test_affect_state_mood_drift.py) ---
SAD_TEXT = "I feel so sad, depressed and hopeless today"
ANGRY_TEXT = "I am so angry, furious and full of rage"
SAD_TEXT_2 = "I feel sad, lonely and empty inside"
SPIRAL_QUERY = "I feel sad and hopeless about how things went"

_INGEST_ENV = {
    "TORMENT_AFFECT_ENABLE": "1",
    "TORMENT_MOOD_DRIFT_ENABLE": "1",
    "TORMENT_MOOD_SPIRAL_ENABLE": "1",
    # disable dedup so repeated affect ingests each spawn a fresh row
    "TORMENT_REINFORCE_SIM_THRESHOLD": "0",
}


class TestBaselineFullSurfaceParity(unittest.TestCase):
    """Characterization guards for the remaining tracked §10 surfaces.

    An injected (still-unwired) affect_attribution envelope must not change the
    full trace scoring path — final retrieval score, the continuity breakdown —
    nor the identity-anchor affect-sensitivity input (which keys solely on
    affect_tag). This locks the S1 baseline so D1-S2 stamping cannot drift these
    silently. No production wiring: the envelope is injected into payloads and
    proven inert.
    """

    def setUp(self):
        self._saved = {}
        for k, v in {**_PINNED_ENV, **_INGEST_ENV}.items():
            self._saved[k] = os.environ.get(k)
            os.environ[k] = v
        self.tmpdir = tempfile.mkdtemp(prefix="torment_d1s1_full_parity_")
        self.fabric = TormentFabric(data_dir=self.tmpdir)
        self.fabric.get_workspace("ws")
        self.fabric.create_agent("ws", "agent")
        self.ak = self.fabric._agent_key("ws", "agent")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def _ingest_old_negative_with_drifts(self):
        r = self.fabric.ingest(workspace_id="ws", agent_id="agent", text=SAD_TEXT, step=10)
        eid = r["eid"]
        self.fabric.ingest(workspace_id="ws", agent_id="agent", text=ANGRY_TEXT, step=200)
        self.fabric.ingest(workspace_id="ws", agent_id="agent", text=SAD_TEXT_2, step=400)
        # canonical clock drives the spiral age gate; ingest(step=) does not.
        self.fabric.agent_states[self.ak].step = 800
        return eid

    def _inject_envelopes(self):
        for ent in self.fabric.private_graphs[self.ak].entities.values():
            p = getattr(ent, "payload", None)
            if not isinstance(p, dict):
                continue
            env = dict(_VALID_ENVELOPE)
            env["value_state"] = "set" if p.get("affect_tag") is not None else "unset"
            p["affect_attribution"] = env

    def _trace_one(self, eid):
        res = self.fabric.trace(
            workspace_id="ws", agent_id="agent", query_text=SPIRAL_QUERY, eids=[eid]
        )
        items = res.get("items", [])
        self.assertTrue(items, "trace should return the requested eid")
        return items[0]

    def test_final_score_and_continuity_breakdown_invariant_to_envelope(self):
        eid = self._ingest_old_negative_with_drifts()
        before = self._trace_one(eid)
        # surfaces must be live (non-vacuous) before asserting invariance
        self.assertGreater(before["explain"]["mood_spiral_penalty"], 0.0)

        self._inject_envelopes()
        after = self._trace_one(eid)

        self.assertEqual(after["final_score"], before["final_score"])
        for key in (
            "affect_match_bonus",
            "mood_drift_bonus",
            "mood_spiral_penalty",
            "continuity_total_adjustment",
        ):
            self.assertEqual(
                after["explain"][key], before["explain"][key],
                f"{key} drifted under envelope presence",
            )

    def test_identity_anchor_affect_sensitivity_input_invariant(self):
        self._ingest_old_negative_with_drifts()
        ents = self.fabric.private_graphs[self.ak].entities
        tags_before = {e: (ent.payload or {}).get("affect_tag") for e, ent in ents.items()}
        self._inject_envelopes()
        tags_after = {e: (ent.payload or {}).get("affect_tag") for e, ent in ents.items()}
        # identity-anchor affect-sensitivity keys solely on affect_tag; an
        # attribution envelope must never shadow or alter it.
        self.assertEqual(tags_after, tags_before)


if __name__ == "__main__":
    unittest.main()
