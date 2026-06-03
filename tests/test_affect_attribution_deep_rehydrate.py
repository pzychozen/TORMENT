"""D1-S4 conformance: deep-rehydrate preserves the affect-attribution snapshot.

The deep-export metadata whitelist (DeepMemoryStore.export) now preserves the
source row's ``affect_attribution`` verbatim, so a deep-memory record (the
durable retrieval echo) carries the original producer envelope instead of
losing it and synthesizing a recovered/migration/legacy_read_fallback on read.

Axes kept separate (contract §4/§7/§10/§11):

    ProvenanceV1       = row lineage          (WHERE the row came from)
    affect_attribution = affect-value lineage (HOW the affect value was produced)
    authority_status   = retrieval-echo authority posture
                         (authoritative=false / requires_rehydration=true /
                          role=retrieval_echo)

Scope note: this slice preserves the snapshot at both required D1-S4 layers:
the DURABLE deep-memory record and the internal runtime ``_query_deep_lane``
retrieval echo. The live echo surfaces ``affect_tag`` beside
``affect_attribution`` so ``read_affect_attribution`` can validate and return
the original producer envelope without synthesizing a recovered fallback.
External/API cross-surface presentation remains deferred to D1-S5.
"""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np

from torment_service.affect_attribution import (
    build_ingest_classifier_attribution,
    build_mood_drift_attribution,
    read_affect_attribution,
)
from torment_service.deep_hits import DeepRetrievalHit, OrphanedAtRehydrateError
from torment_service.deep_memory import DeepMemory, DeepMemoryStore
from torment_service.fabric import TormentFabric


def _candidate(eid=42, born_step=10, summary="deep source", score=0.75):
    c = MagicMock()
    c.eid = eid
    c.born_step = born_step
    c.summary = summary
    c.score = score
    c.motif_id = None
    c.memory_class = "core"
    return c


class _DeepStoreBase(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.mkdtemp(prefix="torment_d1s4_")
        self.store = DeepMemoryStore(Path(self._tmpdir), dim=8)
        self.vec = np.zeros(8, dtype=np.float32)

    def tearDown(self):
        import shutil
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def _export(self, original_payload, eid=42):
        return self.store.export(_candidate(eid=eid), self.vec, original_payload)


# --- 1 / 2: export preserves the producer snapshot verbatim -----------------

class TestExportPreservesSnapshot(_DeepStoreBase):
    def test_ingest_attribution_snapshot_preserved(self):
        env = build_ingest_classifier_attribution(affect_tag="sad")
        mem = self._export({"affect_tag": "sad", "affect_attribution": env})
        self.assertIn("affect_attribution", mem.metadata)
        self.assertEqual(mem.metadata["affect_attribution"], env)
        self.assertEqual(mem.metadata["affect_attribution"]["origin_kind"], "inferred")
        self.assertEqual(
            mem.metadata["affect_attribution"]["via"], "ingest_affect_classifier"
        )

    def test_mood_drift_attribution_snapshot_preserved(self):
        env = build_mood_drift_attribution(affect_tag="sad")
        mem = self._export({"affect_tag": "sad", "affect_attribution": env})
        self.assertEqual(mem.metadata["affect_attribution"], env)
        self.assertEqual(mem.metadata["affect_attribution"]["origin_kind"], "derived")
        self.assertEqual(
            mem.metadata["affect_attribution"]["via"], "mood_drift_transition"
        )


# --- 3: snapshot survives the durable JSONL round-trip (the echo record) ----

class TestSnapshotRoundTrip(_DeepStoreBase):
    def test_snapshot_survives_recall_round_trip(self):
        env = build_ingest_classifier_attribution(affect_tag="angry")
        self._export({"affect_tag": "angry", "affect_attribution": env}, eid=7)
        # recall() reloads from disk via DeepMemory.from_dict.
        recalled = self.store.recall(7)
        self.assertIsNotNone(recalled)
        self.assertEqual(recalled.metadata.get("affect_attribution"), env)


# --- 4: reading the snapshot returns the producer envelope, not a fallback --

class TestReadReturnsProducerNotFallback(_DeepStoreBase):
    def test_read_snapshot_returns_producer_envelope(self):
        env = build_ingest_classifier_attribution(affect_tag="sad")
        mem = self._export({"affect_tag": "sad", "affect_attribution": env})
        out = read_affect_attribution(mem.metadata)
        # Producer lineage preserved — NOT relabeled recovered/migration/legacy.
        self.assertEqual(out["origin_kind"], "inferred")
        self.assertEqual(out["via"], "ingest_affect_classifier")
        self.assertNotEqual(out["via"], "legacy_read_fallback")
        self.assertNotEqual(out["actor"], "migration")


# --- 5: affect-value lineage is orthogonal to echo authority posture --------

class TestSnapshotOrthogonalToAuthority(_DeepStoreBase):
    def test_snapshot_and_authority_status_are_separate_axes(self):
        env = build_mood_drift_attribution(affect_tag="sad")
        mem = self._export({"affect_tag": "sad", "affect_attribution": env}, eid=9)

        # affect-value lineage lives in the snapshot, carries no echo/authority keys.
        snap = mem.metadata["affect_attribution"]
        for forbidden in ("authoritative", "requires_rehydration", "role"):
            self.assertNotIn(forbidden, snap)

        # echo/authority lineage lives in authority_status, carries no affect keys.
        wrapper = DeepRetrievalHit(
            source_eid=9,
            workspace_id="ws",
            agent_id="agent",
            compressed_step=int(mem.compressed_step),
            similarity_score=float(mem.compression_score),
        )
        auth = wrapper.to_dict()["authority_status"]
        self.assertEqual(auth["authoritative"], False)
        self.assertEqual(auth["requires_rehydration"], True)
        self.assertEqual(auth["role"], "retrieval_echo")
        self.assertNotIn("affect_attribution", auth)


# --- 6: rehydrate returns the authoritative source row, envelope unchanged --

class TestRehydratePreservesSourceEnvelope(unittest.TestCase):
    def test_rehydrate_returns_source_with_unchanged_envelope(self):
        env = build_ingest_classifier_attribution(affect_tag="sad")
        source_payload = {"affect_tag": "sad", "affect_attribution": env}

        class _Entity:
            def __init__(self, payload):
                self.payload = payload

        class _Graph:
            def __init__(self, entities):
                self.entities = entities

        graph = _Graph({5: _Entity(dict(source_payload))})
        hit = DeepRetrievalHit(
            source_eid=5, workspace_id="ws", agent_id="agent",
            compressed_step=100, similarity_score=0.5,
        )
        entity = hit.rehydrate(graph)
        self.assertEqual(entity.payload["affect_attribution"], env)

    def test_rehydrate_missing_source_raises_orphan(self):
        class _Graph:
            entities = {}

        hit = DeepRetrievalHit(
            source_eid=404, workspace_id="ws", agent_id="agent",
            compressed_step=100, similarity_score=0.5,
        )
        with self.assertRaises(OrphanedAtRehydrateError):
            hit.rehydrate(_Graph())


# --- 7: genuinely unstamped legacy source -> no snapshot, legacy unchanged --

class TestUnstampedLegacySource(_DeepStoreBase):
    def test_legacy_source_has_no_snapshot_and_keeps_fallback(self):
        # Source row predates stamping: affect present, but no envelope.
        mem = self._export({"affect_tag": "sad"}, eid=11)
        self.assertNotIn("affect_attribution", mem.metadata)
        # Read shim characterization is unchanged (parked vocabulary, not S4).
        out = read_affect_attribution(mem.metadata)
        self.assertEqual(out["via"], "legacy_read_fallback")
        self.assertEqual(out["origin_kind"], "recovered")
        self.assertEqual(out["actor"], "migration")
        # Echo row-lineage is still correctly retrieval_echo — not conflated.
        wrapper = DeepRetrievalHit(
            source_eid=11, workspace_id="ws", agent_id="agent",
            compressed_step=100, similarity_score=0.5,
        )
        self.assertEqual(
            wrapper.to_dict()["authority_status"]["role"], "retrieval_echo"
        )


# --- 8: scoring inputs unchanged by adding the audit-only snapshot ----------

class TestScoringInputsUnchanged(_DeepStoreBase):
    def test_snapshot_does_not_alter_scoring_relevant_metadata(self):
        # affect_attribution is audit-only (contract §10); scoring reads
        # affect_tag / type. Adding the snapshot must not change those.
        payload = {
            "type": "memory",
            "affect_tag": "sad",
            "affect_conf": 0.8,
            "affect_attribution": build_ingest_classifier_attribution(affect_tag="sad"),
        }
        mem = self._export(payload, eid=13)
        self.assertEqual(mem.metadata.get("type"), "memory")
        self.assertEqual(mem.metadata.get("affect_tag"), "sad")
        self.assertEqual(mem.metadata.get("affect_conf"), 0.8)


# --- D1-S4b: live _query_deep_lane echo surfaces the preserved snapshot -----
# The runtime retrieval echo is the same object that carries the Q1 authority
# markers. D1-S4b copies affect_tag + affect_attribution verbatim onto that hit
# when a snapshot exists, so read_affect_attribution returns the producer
# envelope instead of synthesizing recovered/migration/legacy_read_fallback.

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


class TestLiveEchoSurfacesSnapshot(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.mkdtemp(prefix="torment_d1s4b_")

    def tearDown(self):
        import shutil
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def _lane(self, metadata, eid=21, source_present=True):
        store = _FakeDeepStore([_deep_record(eid, metadata)])
        entities = {eid: _FakeEntity({})} if source_present else {}
        graph = _FakeGraph(entities)
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

    def test_live_echo_exposes_tag_and_snapshot(self):
        env = build_ingest_classifier_attribution(affect_tag="sad")
        hits = self._lane(
            {"type": "memory", "affect_tag": "sad", "affect_attribution": env}
        )
        self.assertEqual(len(hits), 1)
        hit = hits[0]
        self.assertEqual(hit.get("affect_tag"), "sad")
        self.assertEqual(hit.get("affect_attribution"), env)

    def test_read_on_live_echo_returns_producer_not_fallback(self):
        env = build_mood_drift_attribution(affect_tag="sad")
        hit = self._lane({"affect_tag": "sad", "affect_attribution": env})[0]
        out = read_affect_attribution(hit)  # must not raise
        self.assertEqual(out["origin_kind"], "derived")
        self.assertEqual(out["via"], "mood_drift_transition")
        self.assertNotEqual(out["via"], "legacy_read_fallback")
        self.assertNotEqual(out["actor"], "migration")

    def test_live_echo_preserves_q1_markers_orthogonally(self):
        env = build_ingest_classifier_attribution(affect_tag="sad")
        hit = self._lane({"affect_tag": "sad", "affect_attribution": env})[0]
        auth = hit["authority_status"]
        self.assertEqual(auth["authoritative"], False)
        self.assertEqual(auth["requires_rehydration"], True)
        self.assertEqual(auth["role"], "retrieval_echo")
        # affect-value lineage carries no authority keys (axes stay separate).
        for forbidden in ("authoritative", "requires_rehydration", "role"):
            self.assertNotIn(forbidden, hit["affect_attribution"])

    def test_live_echo_does_not_surface_affect_conf(self):
        env = build_ingest_classifier_attribution(affect_tag="sad")
        hit = self._lane(
            {"affect_tag": "sad", "affect_conf": 0.9, "affect_attribution": env}
        )[0]
        self.assertIn("affect_attribution", hit)
        self.assertNotIn("affect_conf", hit)

    def test_legacy_echo_no_snapshot_keeps_fallback(self):
        # Unstamped legacy source: no envelope -> nothing surfaced -> read shim
        # returns the parked legacy characterization; role stays retrieval_echo.
        hit = self._lane({"affect_tag": "sad"})[0]
        self.assertNotIn("affect_attribution", hit)
        out = read_affect_attribution(hit)
        self.assertEqual(out["via"], "legacy_read_fallback")
        self.assertEqual(hit["authority_status"]["role"], "retrieval_echo")

    def test_orphan_source_still_filtered(self):
        env = build_ingest_classifier_attribution(affect_tag="sad")
        hits = self._lane(
            {"affect_tag": "sad", "affect_attribution": env},
            eid=99, source_present=False,
        )
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
