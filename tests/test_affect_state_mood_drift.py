"""Regression tests for the affect-state side-store + mood-drift / mood-spiral.

Defect (b9f633a): the refactor "extract lane-specific retrieval helpers from
fabric.query" accidentally deleted the module-level helpers
``_affect_state_path`` / ``_load_affect_state`` / ``_save_affect_state`` while
their callers in ``_maybe_emit_mood_drift`` and the retrieval/trace mood-spiral
paths remained live. Every call sat inside a broad ``except Exception`` so the
resulting ``NameError`` failed *soft*: mood_drift memories were never emitted,
``drift_hist`` never persisted, and the mood-spiral penalty silently collapsed
to zero. The suite stayed green because no test asserted those behaviors as
*nonzero* (``test_trace_continuity_parity`` only asserts the penalty field is
present and ``>= 0.0``).

These tests pin the restored behavior so the silent failure cannot recur:
  1. first high-confidence affect ingest persists ``affect_state.json``
  2. a separated high-confidence transition emits a real ``mood_drift`` entity
  3. alternating transitions accumulate ``drift_hist`` and reload from disk
  4. tracing an old negative memory yields ``explain.mood_spiral_penalty > 0.0``
     (externally observable via the trace() explanation surface only).
"""

import os
import shutil
import tempfile
import unittest

from torment_service.fabric import (
    TormentFabric,
    _affect_state_path,
    _load_affect_state,
)

# Keyword-classifier inputs (deterministic, no LLM). Each has >= 3 keywords for
# one tag, giving conf = 3/(3+1) = 0.75, comfortably above the mood-drift
# min_conf gate (TORMENT_MOOD_DRIFT_MIN_CONF default 0.55) and the affect-match
# min_conf (0.40). The texts never share keywords across tags.
SAD_TEXT = "I feel so sad, depressed and hopeless today"
ANGRY_TEXT = "I am so angry, furious and full of rage"
SAD_TEXT_2 = "I feel sad, lonely and empty inside"
ANGRY_TEXT_2 = "I am mad, furious and seething with rage"

# Pinned for determinism; restored in tearDown to avoid cross-test env leakage.
_PINNED_ENV = {
    "TORMENT_AFFECT_ENABLE": "1",
    "TORMENT_MOOD_DRIFT_ENABLE": "1",
    "TORMENT_MOOD_SPIRAL_ENABLE": "1",
    # Disable duplicate suppression so repeated affect ingests each spawn a
    # fresh entity instead of reinforcing in place. Keeps this restoration
    # test decoupled from the parked reinforcement-policy question.
    "TORMENT_REINFORCE_SIM_THRESHOLD": "0",
}


class TestAffectStateMoodDrift(unittest.TestCase):
    def setUp(self):
        self._env_saved = {}
        for k, v in _PINNED_ENV.items():
            self._env_saved[k] = os.environ.get(k)
            os.environ[k] = v
        self.tmpdir = tempfile.mkdtemp(prefix="torment_affect_state_")
        self.fabric = TormentFabric(data_dir=self.tmpdir)
        self.fabric.get_workspace("ws")
        self.fabric.create_agent("ws", "agent")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        for k, v in self._env_saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def _ingest(self, text, step):
        return self.fabric.ingest(
            workspace_id="ws", agent_id="agent", text=text, step=step,
        )

    # 1. First high-confidence affect ingest persists affect_state.json.
    def test_first_affect_ingest_persists_side_state(self):
        self._ingest(SAD_TEXT, step=10)

        path = _affect_state_path(self.tmpdir, "ws", "agent")
        self.assertTrue(
            os.path.exists(path),
            "affect_state.json should be created on first affect ingest",
        )

        st = _load_affect_state(self.tmpdir, "ws", "agent")
        self.assertEqual(st.get("last_tag"), "sad")
        self.assertGreaterEqual(float(st.get("last_conf", 0.0)), 0.55)
        self.assertEqual(int(st.get("last_step", -1)), 10)
        self.assertIsInstance(st.get("drift_hist"), list)

    # 2. A separated high-confidence transition emits a real mood_drift entity.
    def test_separated_transition_emits_mood_drift_entity(self):
        self._ingest(SAD_TEXT, step=10)
        self._ingest(ANGRY_TEXT, step=140)  # gap 130 >= min_gap (120); sad -> angry

        ak = self.fabric._agent_key("ws", "agent")
        graph = self.fabric.private_graphs[ak]
        drifts = [
            (ent.payload or {})
            for ent in graph.entities.values()
            if (ent.payload or {}).get("mood_from") is not None
        ]
        self.assertTrue(drifts, "a mood_drift entity should have been emitted")
        p = drifts[0]
        self.assertEqual(p.get("mood_from"), "sad")
        self.assertEqual(p.get("mood_to"), "angry")
        self.assertEqual(p.get("affect_tag"), "angry")

    # 3. Alternating transitions accumulate drift_hist and reload from disk.
    def test_drift_hist_accumulates_and_reloads(self):
        self._ingest(SAD_TEXT, step=10)
        self._ingest(ANGRY_TEXT, step=140)   # sad -> angry
        self._ingest(SAD_TEXT_2, step=270)   # angry -> sad

        st = _load_affect_state(self.tmpdir, "ws", "agent")  # fresh read from disk
        dh = st.get("drift_hist")
        self.assertIsInstance(dh, list)
        self.assertGreaterEqual(
            len(dh), 2,
            "two separated transitions should record two drift entries",
        )
        tos = [str(e.get("to")) for e in dh]
        self.assertIn("angry", tos)
        self.assertIn("sad", tos)

    # 4. Tracing an old negative memory yields a nonzero mood_spiral_penalty.
    #    Externally observable via the trace() explanation surface only.
    def test_old_negative_memory_yields_nonzero_spiral_penalty(self):
        r_old = self._ingest(SAD_TEXT, step=10)  # old negative memory (born_step=10)
        eid_old = r_old["eid"]
        # >= 2 recent negative drift transitions so spiral_neg_recent >= 2.
        self._ingest(ANGRY_TEXT, step=200)    # sad -> angry  (to=angry, neg)
        self._ingest(SAD_TEXT_2, step=400)    # angry -> sad  (to=sad,   neg)
        self._ingest(ANGRY_TEXT_2, step=700)  # sad -> angry  (to=angry, neg)

        # ingest(step=N) advances born_step / world step but NOT the kernel
        # ModelState.step that trace() reads for canonical_step (it advances
        # ~+1 per kernel.process call). Advance the canonical clock explicitly
        # so the old memory clears the spiral_older_than age gate (default 250);
        # window=800 keeps the step>=200 drift entries in range, so
        # spiral_neg_recent stays >= 2.
        ak = self.fabric._agent_key("ws", "agent")
        self.fabric.agent_states[ak].step = 800

        result = self.fabric.trace(
            workspace_id="ws", agent_id="agent",
            query_text="I feel sad and hopeless about how things went",
            eids=[eid_old],
        )
        items = result.get("items", [])
        self.assertTrue(items, "trace should return the requested eid")
        explain = items[0]["explain"]
        self.assertIn("mood_spiral_penalty", explain)
        self.assertGreater(
            explain["mood_spiral_penalty"], 0.0,
            "a persisted recent negative drift must yield a nonzero mood-spiral penalty",
        )


if __name__ == "__main__":
    unittest.main()
