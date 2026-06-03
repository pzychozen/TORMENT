"""D1-S5a: cross-surface affect-attribution characterization (test-only).

Locks the current truthful boundaries across read/presentation surfaces:

    preserve where already carried   (ordinary query, governance retain, deep echo)
    omit where deliberately projected (character_context, prompt blocks)
    never relabel / never widen influence

Contract reading (CLUSTER_5_PATH_C_Q3_D1 §10, Codex/trio-resolved): attribution
is recorded / audit-visible only; no public/API/MCP or character_context exposure
is required. These tests are characterization locks — they assert the EXISTING
production behavior so a future refactor cannot silently drop preservation or
widen exposure. No production code is changed by this slice.

Surfaces locked by direct-seam characterization rather than end-to-end (stated
explicitly): the prompt-assembly block builder (`_hit_to_block`), the
character_context producer (`assemble_character_context`), the governance filter
(`filter_llm_facing`), and the deep runtime echo (`_query_deep_lane` via the
fake-fabric harness). MCP `query_memory` (pass-through `_spine_call("query")`,
references no affect field) and full scoring-invariance (covered by
`tests/test_affect_attribution_parity.py`) are intentionally not re-exercised
here to avoid widening the test footprint.
"""
import os
import shutil
import tempfile
import unittest
from types import SimpleNamespace

import numpy as np

from torment_service.affect_attribution import (
    build_ingest_classifier_attribution,
    build_mood_drift_attribution,
    read_affect_attribution,
)
from torment_service.character import assemble_character_context
from torment_service.deep_memory import DeepMemory
from torment_service.fabric import TormentFabric
from torment_service.governance import SURFACE_LLM_CONTEXT, filter_llm_facing
from torment_service.retrieval_assembler import BLOCK_RELATIONAL, _hit_to_block

SAD_TEXT = "I feel so sad, depressed and hopeless today"

_ENV = {
    "TORMENT_AFFECT_ENABLE": "1",
    "TORMENT_MOOD_DRIFT_ENABLE": "1",
    "TORMENT_REINFORCE_SIM_THRESHOLD": "0",
}


# === Surfaces 1-3: source row + ordinary query pass-through =================

class TestSourceAndQueryPreserve(unittest.TestCase):
    def setUp(self):
        self._saved = {k: os.environ.get(k) for k in _ENV}
        os.environ.update(_ENV)
        self.tmp = tempfile.mkdtemp(prefix="torment_d1s5a_")
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

    def _payload(self, eid):
        return self.fabric.private_graphs[self.ak].entities[int(eid)].payload

    def test_S1_source_row_carries_producer_lineage(self):
        eid = self.fabric.ingest(workspace_id="ws", agent_id="agent", text=SAD_TEXT, step=1)["eid"]
        p = self._payload(eid)
        self.assertIn("affect_attribution", p)
        self.assertIsNotNone(p.get("affect_tag"))
        env = read_affect_attribution(p)
        self.assertEqual(env["origin_kind"], "inferred")
        self.assertEqual(env["via"], "ingest_affect_classifier")

    def test_S2_ordinary_query_hit_preserves_attribution(self):
        eid = self.fabric.ingest(workspace_id="ws", agent_id="agent", text=SAD_TEXT, step=1)["eid"]
        res = self.fabric.query(workspace_id="ws", agent_id="agent", query_text=SAD_TEXT, top_k=8)
        hits = res.get("results") or []
        self.assertTrue(hits, "query should return the stamped row")
        target = next((h for h in hits if int(h.get("eid", -1)) == int(eid)), None)
        self.assertIsNotNone(target, "stamped row should appear in query results")
        # Production reads payload fields via (h.get("payload") or h); mirror it.
        pl = target.get("payload") or target
        self.assertIn("affect_attribution", pl)
        self.assertIsNotNone(pl.get("affect_tag"))
        env = read_affect_attribution(pl)
        self.assertEqual(env["via"], "ingest_affect_classifier")
        self.assertNotEqual(env["via"], "legacy_read_fallback")
        self.assertNotEqual(env["actor"], "migration")


# === Surface 4: governance filter preserves attribution on retained hits ====

class TestGovernanceFilterPreserves(unittest.TestCase):
    def test_S4_filter_llm_facing_does_not_strip_attribution(self):
        env = build_ingest_classifier_attribution(affect_tag="sad")
        hit = {
            "eid": 1,
            "summary": "x",
            "payload": {"affect_tag": "sad", "affect_attribution": dict(env)},
        }
        out = filter_llm_facing([hit], surface=SURFACE_LLM_CONTEXT)
        results = out["results"]
        self.assertEqual(len(results), 1, "shareable hit must be retained")
        pl = results[0].get("payload") or results[0]
        self.assertEqual(pl["affect_attribution"], env)  # unchanged verbatim
        self.assertEqual(pl.get("affect_tag"), "sad")
        self.assertEqual(read_affect_attribution(pl)["via"], "ingest_affect_classifier")


# === Surface 5: deep runtime echo preserves snapshot + authority posture ====

class _FakeEntity:
    def __init__(self, payload):
        self.payload = payload


class _FakeGraph:
    def __init__(self, entities):
        self.entities = entities


class _FakeDeepStore:
    def __init__(self, hits):
        self._hits = hits

    def query(self, qv, top_k):
        return list(self._hits[: max(1, int(top_k))])


def _deep_record(eid, metadata):
    return DeepMemory(
        eid=eid, born_step=0, compressed_step=100,
        summary=f"deep_{eid}", compression_score=0.5,
        original_motif_id=None, memory_class="core",
        embedding_ref=None, metadata=metadata,
    )


class TestDeepEchoSurface(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.mkdtemp(prefix="torment_d1s5a_echo_")

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def _lane(self, metadata, eid=21):
        store = _FakeDeepStore([_deep_record(eid, metadata)])
        graph = _FakeGraph({eid: _FakeEntity({})})
        ws, ag = "ws1", "ag1"
        ak = TormentFabric._agent_key(ws, ag)

        class _F:
            pass

        f = _F()
        f._compress_enable = True
        f.data_dir = str(self._tmpdir)
        f._deep_stores = {ak: store}
        f.private_graphs = {ak: graph}
        qemb = np.zeros(384, dtype=np.float32)
        return TormentFabric._query_deep_lane(
            f, ak, ws, ag, qemb, top_k=5, canonical_step=100
        )

    def test_S5_deep_echo_preserves_snapshot_and_authority(self):
        env = build_mood_drift_attribution(affect_tag="sad")
        hits = self._lane({"affect_tag": "sad", "affect_attribution": env})
        self.assertEqual(len(hits), 1)
        hit = hits[0]
        self.assertEqual(hit.get("affect_tag"), "sad")
        self.assertEqual(hit.get("affect_attribution"), env)
        auth = hit["authority_status"]
        self.assertEqual(auth["role"], "retrieval_echo")
        self.assertEqual(auth["authoritative"], False)
        self.assertEqual(auth["requires_rehydration"], True)
        out = read_affect_attribution(hit)
        self.assertEqual(out["origin_kind"], "derived")
        self.assertEqual(out["via"], "mood_drift_transition")
        self.assertNotEqual(out["via"], "legacy_read_fallback")


# === Surface 6: character_context producer deliberately omits affect fields =

class TestCharacterContextOmitsAffect(unittest.TestCase):
    def test_S6_character_context_has_no_affect_fields(self):
        seed = SimpleNamespace(
            seed_text="A test character with a calm, careful voice.",
            seed_id="test_seed_v1",
            character_name="TestCharacter",
            relational_weight=0.35,
        )
        ctx = assemble_character_context(
            graph=None,
            seed=seed,
            agent_id="ag",
            hits=[],  # matches existing unit-test pattern; avoids graph branch
            drift_info={
                "drift_score": 0.0,
                "drift_direction": "stable",
                "explanation": "",
                "seed_basin_role": "anchor",
                "relational_count": 0,
            },
        )
        for k in ("affect_tag", "affect_conf", "affect_attribution"):
            self.assertNotIn(k, ctx, f"character_context must not surface {k}")


# === Surface 7: prompt-assembly block builder omits attribution =============

class TestPromptAssemblyOmitsAffect(unittest.TestCase):
    def test_S7_hit_to_block_does_not_carry_attribution(self):
        env = build_ingest_classifier_attribution(affect_tag="sad")
        hit = {
            "eid": 1,
            "summary": "I feel sad about the deadline",
            "type": "memory",
            "affect_tag": "sad",
            "affect_conf": 0.7,
            "affect_attribution": dict(env),
        }
        block = _hit_to_block(hit, BLOCK_RELATIONAL)
        # block text is summary-derived; attribution never reaches prompt text.
        self.assertIn("I feel sad about the deadline", block.text)
        self.assertNotIn("affect_attribution", block.text)
        # block metadata carries type/strength/etc., never affect lineage.
        self.assertNotIn("affect_attribution", block.metadata)
        self.assertNotIn("affect_tag", block.metadata)
        self.assertNotIn("affect_conf", block.metadata)


if __name__ == "__main__":
    unittest.main()
