"""Focused Phase 7G3B native compatibility embedding-search tests."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

import numpy as np
import pytest

from torment_service.substrate import representations as representations_module
from torment_service.substrate.compat import NativeMemoryCompatibilityFacade
from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.errors import SubstrateInvariantViolation, SubstrateObjectNotFound
from torment_service.substrate.ids import generate_native_id, native_id_to_bytes
from torment_service.substrate.migration import create_snapshot_manifest
from torment_service.substrate.migration.admission import NativeLegacyObjectAdmissionService
from torment_service.substrate.migration.representation_admission import NativeLegacyRepresentationAdmissionService
from torment_service.substrate.representations import (
    INTEGRITY_ALGORITHM_SHA256,
    INTEGRITY_VALUE_ENCODING_RAW,
    NativeRepresentationService,
    RepresentationFailureRequest,
    RepresentationIntegrityExpectationRequest,
    RepresentationIntegrityVerificationRequest,
    RepresentationReadyRequest,
    RepresentationRequest,
)
from torment_service.substrate.schema import CORE_ROLE_STAGING, create_schema, open_schema


def _id(): return generate_native_id()


def _database(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "compat-embedding-search.db")
    create_schema(qualified.connection)
    connection = qualified.connection
    identity, scope_a, scope_b, idem, source_a, source_b = (_id() for _ in range(6))
    connection.execute("INSERT INTO identity_namespaces VALUES (?,?,0)", (native_id_to_bytes(identity), "compat-search-identities"))
    connection.execute("INSERT INTO semantic_scopes VALUES (?,?,0)", (native_id_to_bytes(scope_a), "compat-search-scope-a"))
    connection.execute("INSERT INTO semantic_scopes VALUES (?,?,0)", (native_id_to_bytes(scope_b), "compat-search-scope-b"))
    connection.execute("INSERT INTO idempotency_namespaces VALUES (?,?)", (native_id_to_bytes(idem), "compat-search-idempotency"))
    connection.execute("INSERT INTO legacy_source_namespaces VALUES (?,?,0)", (native_id_to_bytes(source_a), "compat-search-source-a"))
    connection.execute("INSERT INTO legacy_source_namespaces VALUES (?,?,0)", (native_id_to_bytes(source_b), "compat-search-source-b"))
    return qualified, identity, scope_a, scope_b, idem, source_a, source_b


def _memory(facade, identity, scope, idem, source, key, **overrides):
    values = {
        "summary": f"memory {key}", "memory_type": "episodic", "memory_class": "core",
        "strength": 0.7, "confidence": 0.8, "half_life_days": 5.0,
        "user_id": "owner", "logical_step": 12, "extra_payload": {"tag": key},
        "governance_state": "STAGING",
    }
    values.update(overrides)
    return facade.create_memory_state(
        legacy_source_namespace_id=source, idempotency_namespace_id=idem,
        idempotency_key=f"memory:{key}", identity_namespace_id=identity,
        semantic_scope_id=scope, **values,
    )


def _vector_bytes(vector):
    return np.asarray(vector, dtype=np.float32).reshape(-1).tobytes(order="C")


def _pending_vector(connection, source, idem, key, vector, *, encoding_id="RAW_VECTOR"):
    payload = _vector_bytes(vector)
    return NativeRepresentationService(connection).create_representation_pending(
        idempotency_namespace_id=idem,
        idempotency_key=f"pending:{key}",
        request=RepresentationRequest(
            "OBJECT_REVISION", source.object_id, source.revision_id, None, None,
            "COMPAT_EMBEDDING", 1, "compat-embedding-v1", encoding_id,
            dtype="float32", dimension=3, expected_payload_byte_length=len(payload),
        ),
    )


def _ready_vector(connection, source, idem, key, vector, *, encoding_id="RAW_VECTOR"):
    payload = _vector_bytes(vector)
    service = NativeRepresentationService(connection)
    pending = _pending_vector(connection, source, idem, key, vector, encoding_id=encoding_id)
    service.establish_representation_integrity_expectation(
        idempotency_namespace_id=idem,
        idempotency_key=f"expect:{key}",
        request=RepresentationIntegrityExpectationRequest(
            pending.representation_id, INTEGRITY_ALGORITHM_SHA256, sha256(payload).digest(), INTEGRITY_VALUE_ENCODING_RAW,
        ),
    )
    return service.publish_representation_ready(
        idempotency_namespace_id=idem,
        idempotency_key=f"ready:{key}",
        request=RepresentationReadyRequest(
            pending.representation_id, "COMPAT_EMBEDDING", 1, "compat-embedding-v1", encoding_id, payload,
        ),
    )


def _search(facade, source, embedding=(1.0, 0.0, 0.0), dimension=3, **kwargs):
    return facade.search_by_embedding(
        legacy_source_namespace_id=source, embedding=embedding, dimension=dimension, **kwargs,
    )


def _read_only_counts(connection):
    return tuple(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in (
        "objects", "object_revisions", "relationships", "relationship_revisions", "representations",
        "operations", "semantic_transitions", "integrity_measurements", "reconciliation_cases",
    ))


def test_exact_cosine_ranking_filters_decay_projection_and_read_only(tmp_path: Path, monkeypatch):
    qualified, identity, scope_a, _scope_b, idem, source_a, _source_b = _database(tmp_path)
    try:
        connection = qualified.connection
        assert open_schema(connection).core_role == CORE_ROLE_STAGING
        facade = NativeMemoryCompatibilityFacade(connection)
        a = _memory(facade, identity, scope_a, idem, source_a, "a", extra_payload={
            "canon": True, "user_id": "a", "created_ts": 100, "half_life": 1.0, "authority": "payload-only",
        })
        c = _memory(facade, identity, scope_a, idem, source_a, "c", memory_type="other", extra_payload={"user_id": "b"})
        b = _memory(facade, identity, scope_a, idem, source_a, "b", extra_payload={"user_id": "b"})
        d = _memory(facade, identity, scope_a, idem, source_a, "d", memory_type="other", extra_payload={"user_id": "b"})
        _ready_vector(connection, a, idem, "a", (1.0, 0.0, 0.0))
        _ready_vector(connection, c, idem, "c", (0.95, np.sqrt(1.0 - 0.95 ** 2), 0.0))
        _ready_vector(connection, b, idem, "b", (0.8, 0.6, 0.0))
        _ready_vector(connection, d, idem, "d", (0.95, np.sqrt(1.0 - 0.95 ** 2), 0.0))
        before = _read_only_counts(connection)
        monkeypatch.setattr(Path, "open", lambda *_a, **_kw: (_ for _ in ()).throw(AssertionError("native search opened a legacy file")))
        hits = _search(facade, source_a, top_k=4, now_ts=100 + 86400)
        assert [hit.eid for hit in hits] == [c.eid, d.eid, b.eid, a.eid]
        assert hits[-1].raw_score == pytest.approx(1.0) and hits[-1].decay_factor == pytest.approx(0.5)
        assert hits[2].raw_score == pytest.approx(0.8) and hits[2].score == pytest.approx(0.8)
        assert [hit.eid for hit in _search(facade, source_a, top_k=2, user_id="b", type_filter=["episodic"], now_ts=100 + 86400)] == []
        assert [hit.eid for hit in _search(facade, source_a, top_k=4, user_id="b", type_filter=["other"], now_ts=100 + 86400)] == [c.eid, d.eid]
        assert [hit.eid for hit in _search(facade, source_a, top_k=4, canon_only=True, now_ts=100 + 86400)] == [a.eid]
        assert [hit.eid for hit in _search(facade, source_a, top_k=4, min_score=0.97, now_ts=100 + 86400)] == [a.eid]
        assert [hit.eid for hit in _search(facade, source_a, top_k=0, now_ts=100 + 86400)] == [a.eid]
        legacy = hits[-1].to_legacy_dict()
        assert {"eid", "score", "raw_score", "decay_factor", "summary", "type", "strength", "confidence", "step", "ts"}.issubset(legacy)
        assert legacy["authority_category"] == "NOT_APPLICABLE" and legacy["eid"] == a.eid
        with pytest.raises(TypeError):
            hits[0].payload["new"] = "immutable"
        assert _read_only_counts(connection) == before
    finally:
        qualified.close()


def test_state_eligibility_stale_revision_restoration_and_later_mismatch(tmp_path: Path, monkeypatch):
    qualified, identity, scope_a, _scope_b, idem, source_a, _source_b = _database(tmp_path)
    try:
        connection = qualified.connection
        facade = NativeMemoryCompatibilityFacade(connection)
        source = _memory(facade, identity, scope_a, idem, source_a, "source")
        pending_source = _memory(facade, identity, scope_a, idem, source_a, "pending")
        failed_source = _memory(facade, identity, scope_a, idem, source_a, "failed")
        zero_source = _memory(facade, identity, scope_a, idem, source_a, "zero")
        unsupported_source = _memory(facade, identity, scope_a, idem, source_a, "unsupported")
        e1 = _ready_vector(connection, source, idem, "e1", (1.0, 0.0, 0.0))
        pending = _pending_vector(connection, pending_source, idem, "pending", (1.0, 0.0, 0.0))
        failed = _pending_vector(connection, failed_source, idem, "failed", (1.0, 0.0, 0.0))
        NativeRepresentationService(connection).fail_representation(
            idempotency_namespace_id=idem, idempotency_key="failed:state",
            request=RepresentationFailureRequest(failed.representation_id, "SYNTHETIC_FAILURE"),
        )
        _ready_vector(connection, zero_source, idem, "zero", (0.0, 0.0, 0.0))
        _ready_vector(connection, unsupported_source, idem, "unsupported", (1.0, 0.0, 0.0), encoding_id="UNSUPPORTED")
        states = NativeRepresentationService(connection)
        assert (states.get_representation_metadata(pending.representation_id).readiness, states.get_representation_metadata(pending.representation_id).disposition) == ("PENDING", "WITHHELD")
        assert (states.get_representation_metadata(failed.representation_id).readiness, states.get_representation_metadata(failed.representation_id).disposition) == ("FAILED", "WITHHELD")
        assert [hit.eid for hit in _search(facade, source_a)] == [source.eid]
        assert facade.get_memory_by_eid(legacy_source_namespace_id=source_a, eid=pending_source.eid).object_id == pending_source.object_id
        assert facade.get_memory_by_eid(legacy_source_namespace_id=source_a, eid=failed_source.eid).object_id == failed_source.object_id
        r2 = facade.patch_memory_state(
            legacy_source_namespace_id=source_a, eid=source.eid, patch={"strength": 0.9},
            idempotency_namespace_id=idem, idempotency_key="source:r2", expected_revision_id=source.revision_id,
        )
        assert _search(facade, source_a) == ()
        assert NativeRepresentationService(connection).read_representation_payload(e1.representation_id) == _vector_bytes((1.0, 0.0, 0.0))
        e2 = _ready_vector(connection, r2, idem, "e2", (1.0, 0.0, 0.0))
        assert [hit.representation_id for hit in _search(facade, source_a)] == [e2.representation_id]
        monkeypatch.setattr(representations_module, "_measure_payload", lambda *_args: b"x" * 32)
        verification = NativeRepresentationService(connection).verify_published_representation_integrity(
            idempotency_namespace_id=idem, idempotency_key="e2:mismatch",
            request=RepresentationIntegrityVerificationRequest(e2.representation_id, "synthetic later mismatch"),
        )
        assert verification.result == "MISMATCH"
        assert _search(facade, source_a) == ()
        assert facade.get_memory_by_eid(legacy_source_namespace_id=source_a, eid=source.eid).revision_id == r2.revision_id
        assert pending.representation_id != failed.representation_id
    finally:
        qualified.close()


def test_query_validation_and_payload_shape_refusal(tmp_path: Path, monkeypatch):
    qualified, identity, scope_a, _scope_b, idem, source_a, _source_b = _database(tmp_path)
    try:
        connection = qualified.connection
        facade = NativeMemoryCompatibilityFacade(connection)
        source = _memory(facade, identity, scope_a, idem, source_a, "shape")
        _ready_vector(connection, source, idem, "shape", (1.0, 0.0, 0.0))
        for embedding, dimension in (((), 3), ((1.0, 0.0), 3), ((np.nan, 0.0, 0.0), 3), ((np.inf, 0.0, 0.0), 3), ((0.0, 0.0, 0.0), 3)):
            with pytest.raises(ValueError):
                _search(facade, source_a, embedding=embedding, dimension=dimension)
        with pytest.raises(ValueError):
            _search(facade, source_a, representation_class="OTHER")
        with pytest.raises(ValueError):
            _search(facade, source_a, type_filter="episodic")
        monkeypatch.setattr(NativeRepresentationService, "read_representation_payload", lambda *_args: b"short")
        with pytest.raises(SubstrateInvariantViolation, match="payload length"):
            _search(facade, source_a)
    finally:
        qualified.close()


def test_search_namespace_isolation_and_read_only_counts(tmp_path: Path):
    qualified, identity, scope_a, scope_b, idem, source_a, source_b = _database(tmp_path)
    try:
        connection = qualified.connection
        facade = NativeMemoryCompatibilityFacade(connection)
        a = _memory(facade, identity, scope_a, idem, source_a, "a")
        b = _memory(facade, identity, scope_b, idem, source_b, "b")
        _ready_vector(connection, a, idem, "a", (1.0, 0.0, 0.0))
        _ready_vector(connection, b, idem, "b", (1.0, 0.0, 0.0))
        before = _read_only_counts(connection)
        a_hits = _search(facade, source_a)
        b_hits = _search(facade, source_b)
        assert (a.eid, b.eid) == (0, 0)
        assert a_hits[0].object_id == a.object_id and b_hits[0].object_id == b.object_id
        assert a_hits[0].object_id != b_hits[0].object_id
        assert _read_only_counts(connection) == before
    finally:
        qualified.close()


def _json_line(value):
    return json.dumps(value, separators=(",", ":")).encode("utf-8") + b"\n"


def test_migrated_unknown_vector_is_excluded_until_native_ready_rederivation(tmp_path: Path, monkeypatch):
    qualified, identity, scope_a, _scope_b, idem, _source_a, _source_b = _database(tmp_path)
    try:
        connection = qualified.connection
        root = tmp_path / "legacy-snapshot"
        embeddings = root / "embeddings"
        embeddings.mkdir(parents=True)
        (root / "nodes.jsonl").write_bytes(_json_line({"eid": 1, "summary": "migrated", "embedding_ref": {"map": "embeddings/shard_000000.map.jsonl", "shard": "embeddings/shard_000000.npy", "row": 0, "dimension": 3, "dtype": "float32"}}))
        np.save(embeddings / "shard_000000.npy", np.array([[1.0, 0.0, 0.0]], dtype=np.float32))
        (embeddings / "shard_000000.map.jsonl").write_bytes(_json_line({"eid": 1, "shard": "embeddings/shard_000000.npy", "row": 0, "dimension": 3}))
        (embeddings / "manifest.json").write_bytes(_json_line({"encoding_id": "NUMPY_NPY", "dtype": "float32", "dimension": 3, "derivation_contract_version": "legacy-v1", "shards": [{"path": "embeddings/shard_000000.npy", "map": "embeddings/shard_000000.map.jsonl"}]}))
        source_namespace = _id()
        manifest = create_snapshot_manifest(
            snapshot_root=root, manifest_path=tmp_path / "migration-manifest.json",
            legacy_source_namespace_id=source_namespace, legacy_source_namespace_key="compat-search-migration",
        )
        admitted = NativeLegacyObjectAdmissionService(connection).admit_nodes_current_state(
            snapshot_root=root, manifest_path=tmp_path / "migration-manifest.json",
            idempotency_namespace_id=idem, object_identity_namespace_id=identity, unknown_semantic_scope_id=scope_a,
        ).results[0]
        legacy = NativeLegacyRepresentationAdmissionService(connection).admit_embedding_evidence(
            snapshot_root=root, manifest_path=tmp_path / "migration-manifest.json", idempotency_namespace_id=idem,
        ).results[0]
        facade = NativeMemoryCompatibilityFacade(connection)
        assert (legacy.admission_status, legacy.representation_id is not None) == ("ADMITTED", True)
        assert connection.execute("SELECT readiness,operational_disposition FROM representation_current_state WHERE representation_id=?", (native_id_to_bytes(legacy.representation_id),)).fetchone() == ("UNKNOWN", "RECONCILIATION_REQUIRED")
        with pytest.raises(SubstrateObjectNotFound):
            NativeRepresentationService(connection).read_representation_payload(legacy.representation_id)
        monkeypatch.setattr(Path, "open", lambda *_a, **_kw: (_ for _ in ()).throw(AssertionError("native search opened a legacy file")))
        assert _search(facade, manifest.legacy_source_namespace_id) == ()
        source = facade.get_memory_by_eid(legacy_source_namespace_id=manifest.legacy_source_namespace_id, eid=1)
        current = type("Source", (), {"object_id": source.object_id, "revision_id": source.revision_id})()
        _ready_vector(connection, current, idem, "rederived", (1.0, 0.0, 0.0))
        assert [hit.eid for hit in _search(facade, manifest.legacy_source_namespace_id)] == [1]
        assert admitted.object_id == source.object_id
    finally:
        qualified.close()
