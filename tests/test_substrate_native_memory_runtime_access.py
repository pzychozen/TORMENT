"""Focused native qualification for the post-write memory read adapter."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import numpy as np
import pytest

from torment_service.memory_runtime_access import LegacyPostWriteMemoryAccess
from torment_service.kernel.seed_entities import SeedEntity
from torment_service.memory_graph import MemoryGraph
from torment_service.fabric import _detect_canon_conflict
from torment_service.substrate.compat import NativeMemoryCompatibilityFacade
from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.errors import SubstrateInvariantViolation
from torment_service.substrate.ids import generate_native_id, native_id_to_bytes
from torment_service.substrate.native_memory_runtime_access import NativePostWriteMemoryAccess
from torment_service.substrate.representations import (
    INTEGRITY_ALGORITHM_SHA256,
    INTEGRITY_VALUE_ENCODING_RAW,
    NativeRepresentationService,
    RepresentationIntegrityExpectationRequest,
    RepresentationReadyRequest,
    RepresentationRequest,
)
from torment_service.substrate.schema import create_schema


def _id():
    return generate_native_id()


def _database(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "a3d2.db")
    create_schema(qualified.connection)
    connection = qualified.connection
    identity, scope, idem, namespace = (_id() for _ in range(4))
    for table, identifier, label in (
        ("identity_namespaces", identity, "a3d2-identities"),
        ("semantic_scopes", scope, "a3d2-scope"),
        ("idempotency_namespaces", idem, "a3d2-idempotency"),
        ("legacy_source_namespaces", namespace, "a3d2-legacy-source"),
    ):
        connection.execute(
            f"INSERT INTO {table} VALUES ({'?,?,0' if table != 'idempotency_namespaces' else '?,?'})",
            (native_id_to_bytes(identifier), label),
        )
    return qualified, connection, identity, scope, idem, namespace


def _provenance(connection, *, source_type="user_input", write_path="direct_ingest"):
    provenance_id = _id()
    connection.execute(
        "INSERT INTO provenance_records VALUES (?,?,?,?,?,?,?,?,?,?)",
        (native_id_to_bytes(provenance_id), "RUNTIME_PROVENANCE_V1", source_type, "user", write_path,
         "KNOWN", None, None, None, None),
    )
    return provenance_id


def _memory(connection, identity, scope, idem, namespace, key, *, governance=None, provenance=True, **overrides):
    provenance_id = _provenance(connection) if provenance else None
    values = {
        "summary": f"memory {key}", "memory_type": "reflection", "memory_class": "core",
        "strength": 0.7, "confidence": 0.8, "half_life_days": 0.0, "user_id": "aria", "logical_step": 2,
        "extra_payload": {"resonance_score": 0.61, "loop_type": "spiral", "srg": {"band": 2}, "ordinary": key},
        "governance_state": "DERIVED", "provenance_id": provenance_id,
    }
    values.update(overrides)
    source = NativeMemoryCompatibilityFacade(connection).create_memory_state(
        legacy_source_namespace_id=namespace, idempotency_namespace_id=idem, idempotency_key=f"memory:{key}",
        identity_namespace_id=identity, semantic_scope_id=scope, **values,
    )
    if governance is not None:
        connection.execute(
            """INSERT INTO object_revision_governance(
                object_id,object_revision_id,object_revision_ordinal,protected,non_shareable,
                collective_export_blocked,collective_reingest_blocked,decay_accelerated
            ) VALUES (?,?,?,?,?,?,?,?)""",
            (native_id_to_bytes(source.object_id), native_id_to_bytes(source.revision_id), 1,
             int(governance.get("protected", False)), int(governance.get("non_shareable", False)),
             int(governance.get("collective_export_blocked", False)),
             int(governance.get("collective_reingest_blocked", False)), int(governance.get("decay_accelerated", False))),
        )
    return source


def _ready(connection, idem, source, key, vector):
    payload = np.asarray(vector, dtype=np.float32).reshape(-1).tobytes(order="C")
    representations = NativeRepresentationService(connection)
    pending = representations.create_representation_pending(
        idempotency_namespace_id=idem, idempotency_key=f"pending:{key}",
        request=RepresentationRequest(
            "OBJECT_REVISION", source.object_id, source.revision_id, None, None,
            "COMPAT_EMBEDDING", 1, "compat-embedding-v1", "RAW_VECTOR",
            "float32", 3, (), None, len(payload),
        ),
    )
    representations.establish_representation_integrity_expectation(
        idempotency_namespace_id=idem, idempotency_key=f"expect:{key}",
        request=RepresentationIntegrityExpectationRequest(
            pending.representation_id, INTEGRITY_ALGORITHM_SHA256, sha256(payload).digest(), INTEGRITY_VALUE_ENCODING_RAW,
        ),
    )
    return representations.publish_representation_ready(
        idempotency_namespace_id=idem, idempotency_key=f"ready:{key}",
        request=RepresentationReadyRequest(
            pending.representation_id, "COMPAT_EMBEDDING", 1, "compat-embedding-v1", "RAW_VECTOR", payload,
        ),
    )


class _ThreeDimensionalEmbedder:
    dim = 3

    def embed(self, _text):
        return np.zeros(3, dtype=np.float32)


def _legacy_equivalent(tmp_path: Path, connection, namespace, sources_and_vectors):
    graph = MemoryGraph(str(tmp_path), embedder=_ThreeDimensionalEmbedder())
    facade = NativeMemoryCompatibilityFacade(connection)
    for source, vector, governance in sources_and_vectors:
        native = facade.get_memory_by_eid(legacy_source_namespace_id=namespace, eid=source.eid)
        payload = dict(native.payload)
        payload["governance"] = dict(governance)
        payload["provenance"] = {"source_type": "user_input", "write_path": "direct_ingest"}
        graph.entities[source.eid] = SeedEntity(
            eid=source.eid, born_step=0, channel=0,
            pos=np.zeros(3), vel=np.zeros(3), vel0=np.zeros(3), payload=payload,
        )
        np.save(graph._emb_path(source.eid), np.asarray(vector, dtype=np.float32))
    return LegacyPostWriteMemoryAccess(graph, expected_dimension=3)


def _counts(connection):
    tables = (
        "objects", "object_revisions", "relationships", "relationship_revisions", "representations",
        "operations", "semantic_transitions", "object_revision_governance", "provenance_records",
        "integrity_expectations", "integrity_measurements", "reconciliation_cases", "reconciliation_case_states",
    )
    return tuple(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in tables)


def test_current_view_embedding_and_nonzero_search_parity_are_read_only(tmp_path: Path):
    qualified, connection, identity, scope, idem, namespace = _database(tmp_path)
    try:
        governance = {"protected": True, "non_shareable": True, "collective_reingest_blocked": True}
        first = _memory(connection, identity, scope, idem, namespace, "first", governance=governance)
        second = _memory(connection, identity, scope, idem, namespace, "second", governance=governance)
        other = _memory(connection, identity, scope, idem, namespace, "other", governance=governance, user_id="other")
        _ready(connection, idem, first, "first", (1.0, 0.0, 0.0))
        _ready(connection, idem, second, "second", (0.8, 0.6, 0.0))
        _ready(connection, idem, other, "other", (0.8, 0.6, 0.0))
        native = NativePostWriteMemoryAccess(connection, legacy_source_namespace_id=namespace, expected_dimension=3)
        legacy = _legacy_equivalent(tmp_path / "legacy", connection, namespace, (
            (first, (1.0, 0.0, 0.0), governance),
            (second, (0.8, 0.6, 0.0), governance),
            (other, (0.8, 0.6, 0.0), governance),
        ))
        before = _counts(connection)

        assert native.get_current(first.eid) == legacy.get_current(first.eid)
        with pytest.raises(TypeError):
            native.get_current(first.eid).payload["ordinary"] = "changed"  # type: ignore[union-attr,index]
        native_embedding = native.read_current_embedding(first.eid, expected_dimension=3)
        legacy_embedding = legacy.read_current_embedding(first.eid, expected_dimension=3)
        assert native_embedding is not None and native_embedding == legacy_embedding
        assert native_embedding.as_float32().flags.writeable is False

        native_outcome = native.search_by_embedding((1.0, 0.0, 0.0), top_k=3, user_id="aria")
        legacy_outcome = legacy.search_by_embedding((1.0, 0.0, 0.0), top_k=3, user_id="aria")
        assert (native_outcome.status, legacy_outcome.status) == ("SEARCHABLE", "SEARCHABLE")
        native_hits, legacy_hits = native_outcome.hits, legacy_outcome.hits
        assert [hit.eid for hit in native_hits] == [hit.eid for hit in legacy_hits] == [first.eid, second.eid]
        assert [hit.raw_score for hit in native_hits] == pytest.approx([hit.raw_score for hit in legacy_hits], rel=1e-6)
        assert [hit.score for hit in native_hits] == pytest.approx([hit.score for hit in legacy_hits], rel=1e-6)
        assert _counts(connection) == before
    finally:
        qualified.close()


def test_representation_gap_and_structural_provenance_refusal(tmp_path: Path):
    qualified, connection, identity, scope, idem, namespace = _database(tmp_path)
    try:
        gap = _memory(connection, identity, scope, idem, namespace, "gap")
        missing_provenance = _memory(connection, identity, scope, idem, namespace, "missing", governance={}, provenance=False)
        native = NativePostWriteMemoryAccess(connection, legacy_source_namespace_id=namespace, expected_dimension=3)
        assert native.get_current(gap.eid) is not None
        assert native.read_current_embedding(gap.eid, expected_dimension=3) is None
        assert native.search_by_embedding((1.0, 0.0, 0.0), top_k=3).hits == ()
        missing_governance = native.get_current(gap.eid).governance  # type: ignore[union-attr]
        assert missing_governance.structurally_explicit is False
        assert missing_governance == type(missing_governance)(False, False, False, False, False, False)
        with pytest.raises(SubstrateInvariantViolation, match="structural provenance"):
            native.get_current(missing_provenance.eid)
    finally:
        qualified.close()


def test_zero_query_contract_preserves_reinforcement_and_conflict_decisions(tmp_path: Path, monkeypatch):
    """The port classifies zero-norm queries without invoking either backend."""
    qualified, connection, identity, scope, idem, namespace = _database(tmp_path)
    try:
        zero = _memory(connection, identity, scope, idem, namespace, "zero", governance={})
        _ready(connection, idem, zero, "zero", (0.0, 0.0, 0.0))
        native = NativePostWriteMemoryAccess(connection, legacy_source_namespace_id=namespace, expected_dimension=3)
        legacy = _legacy_equivalent(tmp_path / "legacy", connection, namespace, ((zero, (0.0, 0.0, 0.0), {}),))
        assert native.read_current_embedding(zero.eid, expected_dimension=3).as_float32().tolist() == [0.0, 0.0, 0.0]  # type: ignore[union-attr]

        raw_legacy_hits = legacy._graph.search_by_embedding((0.0, 0.0, 0.0), top_k=3)
        assert raw_legacy_hits and all(hit["raw_score"] == 0.0 for hit in raw_legacy_hits)
        assert not any(hit["raw_score"] >= 0.92 for hit in raw_legacy_hits)
        assert not any(_detect_canon_conflict("new", hit["summary"], hit["raw_score"])[0] for hit in raw_legacy_hits)
        with pytest.raises(ValueError, match="positive finite norm"):
            NativeMemoryCompatibilityFacade(connection).search_by_embedding(
                legacy_source_namespace_id=namespace, embedding=(0.0, 0.0, 0.0), dimension=3,
            )

        monkeypatch.setattr(legacy._graph, "search_by_embedding", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("legacy search called")))
        monkeypatch.setattr(native._compatibility_reads, "search_by_embedding", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("native search called")))
        legacy_outcome = legacy.search_by_embedding((0.0, 0.0, 0.0), top_k=3)
        native_outcome = native.search_by_embedding((0.0, 0.0, 0.0), top_k=3)
        assert (legacy_outcome.status, legacy_outcome.hits) == ("ZERO_NORM", ())
        assert (native_outcome.status, native_outcome.hits) == ("ZERO_NORM", ())
        for invalid in ((), (1.0, 0.0), (float("nan"), 0.0, 0.0), (float("inf"), 0.0, 0.0)):
            with pytest.raises(ValueError):
                legacy.search_by_embedding(invalid, top_k=3)
            with pytest.raises(ValueError):
                native.search_by_embedding(invalid, top_k=3)
    finally:
        qualified.close()
