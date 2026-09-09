"""Focused Phase 7G3B native compatibility embedding-search tests."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from uuid import UUID

import numpy as np
import pytest

from torment_service.substrate import representations as representations_module
from torment_service.substrate.compat import NativeMemoryCompatibilityFacade
from torment_service.substrate.compat_embedding_reader import NativeCompatEmbeddingReader
from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.errors import SubstrateInvariantViolation
from torment_service.substrate.ids import generate_native_id, native_id_to_bytes
from torment_service.substrate.migration import (
    MigrationRuntimeReembeddingBootstrapRequest,
    NativeMigrationRuntimeReembeddingBootstrapService,
)
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

from test_substrate_migration_runtime_representation_bootstrap import (
    _fixture as _qualified_migration_fixture,
    _normalize as _normalize_legacy_memory,
)


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


class _DeterministicReembeddingEmbedder:
    """B3B test embedder with a qualified target-lane identity."""

    provider = "synthetic"
    model = "synthetic"
    dim = 3

    def __init__(self) -> None:
        self.calls: list[str] = []

    def embed(self, text: str) -> np.ndarray:
        self.calls.append(text)
        return np.asarray((1.0, 0.0, 0.0), dtype=np.float32)


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


def test_migrated_unknown_vector_is_excluded_until_native_ready_rederivation(tmp_path: Path, monkeypatch):
    qualified, facts = _qualified_migration_fixture(tmp_path, provider="different-provider")
    facts["connection"] = qualified.connection
    try:
        connection = qualified.connection
        facade = NativeMemoryCompatibilityFacade(connection)
        object_id = facts["object_id"]
        r1 = facts["r1"]
        source_namespace = facts["source_namespace"]
        legacy_capture = connection.execute(
            """SELECT r.representation_id,r.source_object_revision_id,s.readiness,s.operational_disposition
                 FROM representations r JOIN representation_current_state s USING(representation_id)
                WHERE r.representation_class='LEGACY_EMBEDDING_CAPTURE'"""
        ).fetchone()

        # Stage A: R1 and its captured vector are retained historical evidence,
        # not a runtime-semantic memory or usable runtime representation.
        assert connection.execute(
            "SELECT lineage_kind FROM object_revisions WHERE object_revision_id=?",
            (native_id_to_bytes(r1),),
        ).fetchone() == ("LEGACY_PREDECESSOR_UNKNOWN",)
        assert legacy_capture == (
            legacy_capture[0], native_id_to_bytes(r1), "UNKNOWN", "RECONCILIATION_REQUIRED",
        )
        with monkeypatch.context() as no_legacy_files:
            no_legacy_files.setattr(
                Path, "open",
                lambda *_a, **_kw: (_ for _ in ()).throw(AssertionError("native search opened a legacy file")),
            )
            assert _search(facade, source_namespace) == ()
        with pytest.raises(
            SubstrateInvariantViolation,
            match="RUNTIME_SEMANTIC_ADMISSION_REFUSED_LEGACY_PREDECESSOR_UNKNOWN",
        ):
            facade.get_memory_by_eid(legacy_source_namespace_id=source_namespace, eid=7)

        # Stage B: the qualified B2 normalizer creates the sole R2 runtime
        # successor while preserving R1 and its captured representation.
        r2 = _normalize_legacy_memory(facts).revision_id
        assert connection.execute(
            """SELECT lineage_kind,predecessor_revision_id,predecessor_revision_ordinal
                 FROM object_revisions WHERE object_revision_id=?""",
            (native_id_to_bytes(r2),),
        ).fetchone() == ("NATIVE_ORDINARY", native_id_to_bytes(r1), 1)
        assert connection.execute(
            "SELECT current_revision_id,current_revision_ordinal FROM objects WHERE object_id=?",
            (native_id_to_bytes(object_id),),
        ).fetchone() == (native_id_to_bytes(r2), 2)
        assert connection.execute(
            """SELECT r.representation_id,r.source_object_revision_id,s.readiness,s.operational_disposition
                 FROM representations r JOIN representation_current_state s USING(representation_id)
                WHERE r.representation_class='LEGACY_EMBEDDING_CAPTURE'"""
        ).fetchone() == legacy_capture

        # Stage C: B3B re-derives the ready usable target against R2, never R1.
        request = MigrationRuntimeReembeddingBootstrapRequest(
            snapshot_root=facts["root"], manifest_path=facts["manifest_path"],
            legacy_snapshot_id=facts["manifest"].legacy_snapshot_id,
            legacy_source_namespace_id=source_namespace,
            expected_native_core_id=UUID(bytes=facts["metadata"].core_id), eid=7,
            expected_r1_revision_id=r1, expected_r2_revision_id=r2,
            scope_plans=(facts["plan"],), target_lane=facts["lane"],
            idempotency_namespace_id=facts["idempotency"], idempotency_key="compat-search-b3b-rederived",
        )
        embedder = _DeterministicReembeddingEmbedder()
        rederived = NativeMigrationRuntimeReembeddingBootstrapService(connection).bootstrap_from_qualified_text(
            request, embedder=embedder,
        )
        assert rederived.r2_revision_id == r2
        assert embedder.calls == ["evidence-complete legacy memory"]
        source = facade.get_memory_by_eid(legacy_source_namespace_id=source_namespace, eid=7)
        assert (source.object_id, source.revision_id) == (object_id, r2)
        witness = NativeCompatEmbeddingReader(connection).read_current(object_id, expected_dimension=3)
        assert witness is not None
        assert (
            witness.source_revision_id, witness.representation_class, witness.readiness, witness.disposition,
        ) == (r2, "COMPAT_EMBEDDING", "READY", "USABLE")
        assert [hit.eid for hit in _search(facade, source_namespace)] == [7]
    finally:
        qualified.close()
