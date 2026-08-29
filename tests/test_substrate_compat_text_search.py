"""Focused Phase 7G3C injected-embedder text-search compatibility tests."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace
import urllib.request

import numpy as np
import pytest

from torment_service import embeddings as embeddings_module
from torment_service.substrate import representations as representations_module
from torment_service.substrate.compat import NativeMemoryCompatibilityFacade
from torment_service.substrate.compat_query import CompatibilityQueryLane, search_text
from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.migration import create_snapshot_manifest
from torment_service.substrate.migration.admission import NativeLegacyObjectAdmissionService
from torment_service.substrate.migration.representation_admission import NativeLegacyRepresentationAdmissionService
from torment_service.substrate.ids import generate_native_id, native_id_to_bytes
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


class FakeEmbedder:
    """Offline deterministic Embedder-compatible test double."""

    def __init__(self, vector, *, provider="synthetic", model="synthetic-v1", dim=3, error=None):
        self.provider = provider
        self.model = model
        self.dim = dim
        self.vector = vector
        self.error = error
        self.calls: list[str] = []

    def embed(self, text: str):
        self.calls.append(text)
        if self.error is not None:
            raise self.error
        return self.vector.copy() if isinstance(self.vector, np.ndarray) else self.vector


def _lane(**overrides):
    values = {
        "provider": "synthetic", "model": "synthetic-v1", "dimension": 3,
        "representation_class": "COMPAT_EMBEDDING", "generation": 1,
        "derivation_contract_version": "compat-embedding-v1",
        "encoding_id": "RAW_VECTOR", "dtype": "float32",
    }
    values.update(overrides)
    return CompatibilityQueryLane(**values)


def _database(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "compat-text-search.db")
    create_schema(qualified.connection)
    connection = qualified.connection
    identity, scope, idem, source = (_id() for _ in range(4))
    connection.execute("INSERT INTO identity_namespaces VALUES (?,?,0)", (native_id_to_bytes(identity), "compat-text-identities"))
    connection.execute("INSERT INTO semantic_scopes VALUES (?,?,0)", (native_id_to_bytes(scope), "compat-text-scope"))
    connection.execute("INSERT INTO idempotency_namespaces VALUES (?,?)", (native_id_to_bytes(idem), "compat-text-idempotency"))
    connection.execute("INSERT INTO legacy_source_namespaces VALUES (?,?,0)", (native_id_to_bytes(source), "compat-text-source"))
    return qualified, identity, scope, idem, source


def _memory(facade, identity, scope, idem, source, key, **overrides):
    values = {
        "summary": f"memory {key}", "memory_type": "episodic", "memory_class": "core",
        "strength": 0.7, "confidence": 0.8, "half_life_days": 0.0,
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


def _pending_vector(connection, source, idem, key, vector):
    payload = _vector_bytes(vector)
    return NativeRepresentationService(connection).create_representation_pending(
        idempotency_namespace_id=idem,
        idempotency_key=f"pending:{key}",
        request=RepresentationRequest(
            "OBJECT_REVISION", source.object_id, source.revision_id, None, None,
            "COMPAT_EMBEDDING", 1, "compat-embedding-v1", "RAW_VECTOR",
            dtype="float32", dimension=3, expected_payload_byte_length=len(payload),
        ),
    )


def _ready_vector(connection, source, idem, key, vector):
    payload = _vector_bytes(vector)
    service = NativeRepresentationService(connection)
    pending = _pending_vector(connection, source, idem, key, vector)
    service.establish_representation_integrity_expectation(
        idempotency_namespace_id=idem,
        idempotency_key=f"expect:{key}",
        request=RepresentationIntegrityExpectationRequest(
            pending.representation_id, INTEGRITY_ALGORITHM_SHA256,
            sha256(payload).digest(), INTEGRITY_VALUE_ENCODING_RAW,
        ),
    )
    return service.publish_representation_ready(
        idempotency_namespace_id=idem,
        idempotency_key=f"ready:{key}",
        request=RepresentationReadyRequest(
            pending.representation_id, "COMPAT_EMBEDDING", 1,
            "compat-embedding-v1", "RAW_VECTOR", payload,
        ),
    )


def _counts(connection):
    tables = (
        "objects", "object_revisions", "relationships", "relationship_revisions",
        "representations", "representation_payloads", "operations",
        "semantic_transitions", "integrity_expectations", "integrity_measurements",
        "reconciliation_cases", "representation_state_effects",
        "integrity_measurement_effects", "operation_outputs",
    )
    return tuple(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in tables)


def _text_search(facade, source, embedder, query_text="alpha beta", **kwargs):
    return search_text(
        facade=facade,
        legacy_source_namespace_id=source,
        query_text=query_text,
        embedder=embedder,
        lane=kwargs.pop("lane", _lane()),
        **kwargs,
    )


def test_text_search_is_single_embed_direct_vector_equivalent_and_read_only(tmp_path: Path, monkeypatch):
    qualified, identity, scope, idem, source = _database(tmp_path)
    try:
        connection = qualified.connection
        assert open_schema(connection).core_role == CORE_ROLE_STAGING
        facade = NativeMemoryCompatibilityFacade(connection)
        a = _memory(facade, identity, scope, idem, source, "a", user_id="alice")
        b = _memory(facade, identity, scope, idem, source, "b", user_id="alice")
        _memory(facade, identity, scope, idem, source, "other", memory_type="other", user_id="bob")
        _ready_vector(connection, a, idem, "a", (1.0, 0.0, 0.0))
        _ready_vector(connection, b, idem, "b", (0.8, 0.6, 0.0))
        other = facade.get_memory_by_eid(legacy_source_namespace_id=source, eid=2)
        _ready_vector(connection, other, idem, "other", (0.95, np.sqrt(1.0 - 0.95 ** 2), 0.0))
        fake = FakeEmbedder(np.array((1.0, 0.0, 0.0), dtype=np.float32))
        before = _counts(connection)
        monkeypatch.setattr(embeddings_module, "build_embedder_from_env", lambda: (_ for _ in ()).throw(AssertionError("provider factory was called")))
        monkeypatch.setattr(urllib.request, "urlopen", lambda *_a, **_kw: (_ for _ in ()).throw(AssertionError("network was called")))
        monkeypatch.setattr(Path, "open", lambda *_a, **_kw: (_ for _ in ()).throw(AssertionError("text search opened a legacy file")))
        text_hits = _text_search(
            facade, source, fake, top_k=3, user_id="alice",
            min_score=0.75, type_filter=["episodic"],
        )
        direct_hits = facade.search_by_embedding(
            legacy_source_namespace_id=source, embedding=(1.0, 0.0, 0.0), dimension=3,
            representation_class="COMPAT_EMBEDDING", generation=1,
            derivation_contract_version="compat-embedding-v1", encoding_id="RAW_VECTOR",
            dtype="float32", top_k=3, user_id="alice", min_score=0.75,
            type_filter=["episodic"],
        )
        assert text_hits == direct_hits
        assert [hit.eid for hit in text_hits] == [a.eid, b.eid]
        assert fake.calls == ["alpha beta"]
        assert _counts(connection) == before
    finally:
        qualified.close()


def test_empty_and_invalid_embedder_contracts_are_read_only(tmp_path: Path):
    qualified, identity, scope, idem, source = _database(tmp_path)
    try:
        connection = qualified.connection
        facade = NativeMemoryCompatibilityFacade(connection)
        memory = _memory(facade, identity, scope, idem, source, "shape")
        _ready_vector(connection, memory, idem, "shape", (1.0, 0.0, 0.0))
        before = _counts(connection)

        assert search_text(
            facade=object(), legacy_source_namespace_id=source, query_text="  ",
            embedder=None, lane=_lane(),
        ) == ()
        wrong_provider = FakeEmbedder((1.0, 0.0, 0.0), provider="other")
        wrong_model = FakeEmbedder((1.0, 0.0, 0.0), model="other-v1")
        wrong_declared_dimension = FakeEmbedder((1.0, 0.0, 0.0), dim=4)
        for candidate, lane in (
            (None, _lane()),
            (wrong_provider, _lane()),
            (wrong_model, _lane()),
            (wrong_declared_dimension, _lane()),
            (FakeEmbedder((1.0, 0.0, 0.0)), _lane(representation_class="OTHER")),
        ):
            with pytest.raises(ValueError):
                _text_search(facade, source, candidate, lane=lane)
        assert wrong_provider.calls == []
        assert wrong_model.calls == []
        assert wrong_declared_dimension.calls == []

        wrong_returned_dimension = FakeEmbedder((1.0, 0.0))
        with pytest.raises(ValueError, match="wrong dimension"):
            _text_search(facade, source, wrong_returned_dimension)
        assert wrong_returned_dimension.calls == ["alpha beta"]

        for vector in ((np.nan, 0.0, 0.0), (np.inf, 0.0, 0.0), (0.0, 0.0, 0.0)):
            invalid = FakeEmbedder(vector)
            with pytest.raises(ValueError):
                _text_search(facade, source, invalid)
            assert invalid.calls == ["alpha beta"]

        exploding = FakeEmbedder((1.0, 0.0, 0.0), error=RuntimeError("synthetic embedder failure"))
        with pytest.raises(RuntimeError, match="synthetic embedder failure"):
            _text_search(facade, source, exploding)
        assert exploding.calls == ["alpha beta"]
        assert _counts(connection) == before
    finally:
        qualified.close()


def test_text_search_preserves_pending_failed_revision_and_integrity_gates(tmp_path: Path, monkeypatch):
    qualified, identity, scope, idem, source = _database(tmp_path)
    try:
        connection = qualified.connection
        facade = NativeMemoryCompatibilityFacade(connection)
        ready_source = _memory(facade, identity, scope, idem, source, "ready")
        pending_source = _memory(facade, identity, scope, idem, source, "pending")
        failed_source = _memory(facade, identity, scope, idem, source, "failed")
        e1 = _ready_vector(connection, ready_source, idem, "e1", (1.0, 0.0, 0.0))
        pending = _pending_vector(connection, pending_source, idem, "pending", (1.0, 0.0, 0.0))
        failed = _pending_vector(connection, failed_source, idem, "failed", (1.0, 0.0, 0.0))
        NativeRepresentationService(connection).fail_representation(
            idempotency_namespace_id=idem, idempotency_key="failed:state",
            request=RepresentationFailureRequest(failed.representation_id, "SYNTHETIC_FAILURE"),
        )
        state = NativeRepresentationService(connection)
        assert (state.get_representation_metadata(pending.representation_id).readiness, state.get_representation_metadata(pending.representation_id).disposition) == ("PENDING", "WITHHELD")
        assert (state.get_representation_metadata(failed.representation_id).readiness, state.get_representation_metadata(failed.representation_id).disposition) == ("FAILED", "WITHHELD")
        fake = FakeEmbedder((1.0, 0.0, 0.0))

        before = _counts(connection)
        assert [hit.representation_id for hit in _text_search(facade, source, fake)] == [e1.representation_id]
        assert _counts(connection) == before

        r2 = facade.patch_memory_state(
            legacy_source_namespace_id=source, eid=ready_source.eid, patch={"strength": 0.9},
            idempotency_namespace_id=idem, idempotency_key="ready:r2",
            expected_revision_id=ready_source.revision_id,
        )
        before = _counts(connection)
        assert _text_search(facade, source, fake) == ()
        assert _counts(connection) == before

        e2 = _ready_vector(connection, r2, idem, "e2", (1.0, 0.0, 0.0))
        before = _counts(connection)
        assert [hit.representation_id for hit in _text_search(facade, source, fake)] == [e2.representation_id]
        assert _counts(connection) == before

        monkeypatch.setattr(representations_module, "_measure_payload", lambda *_args: b"x" * 32)
        verification = state.verify_published_representation_integrity(
            idempotency_namespace_id=idem, idempotency_key="e2:mismatch",
            request=RepresentationIntegrityVerificationRequest(e2.representation_id, "synthetic later mismatch"),
        )
        assert verification.result == "MISMATCH"
        before = _counts(connection)
        assert _text_search(facade, source, fake) == ()
        assert _counts(connection) == before
    finally:
        qualified.close()


def _json_line(value):
    return json.dumps(value, separators=(",", ":")).encode("utf-8") + b"\n"


def test_unknown_migrated_vector_is_excluded_until_native_ready_rederivation(tmp_path: Path, monkeypatch):
    qualified, identity, scope, idem, _source = _database(tmp_path)
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
            legacy_source_namespace_id=source_namespace, legacy_source_namespace_key="compat-text-migration",
        )
        NativeLegacyObjectAdmissionService(connection).admit_nodes_current_state(
            snapshot_root=root, manifest_path=tmp_path / "migration-manifest.json",
            idempotency_namespace_id=idem, object_identity_namespace_id=identity,
            unknown_semantic_scope_id=scope,
        )
        legacy = NativeLegacyRepresentationAdmissionService(connection).admit_embedding_evidence(
            snapshot_root=root, manifest_path=tmp_path / "migration-manifest.json",
            idempotency_namespace_id=idem,
        ).results[0]
        assert legacy.admission_status == "ADMITTED" and legacy.representation_id is not None
        assert connection.execute(
            "SELECT readiness,operational_disposition FROM representation_current_state WHERE representation_id=?",
            (native_id_to_bytes(legacy.representation_id),),
        ).fetchone() == ("UNKNOWN", "RECONCILIATION_REQUIRED")
        facade = NativeMemoryCompatibilityFacade(connection)
        fake = FakeEmbedder((1.0, 0.0, 0.0))
        monkeypatch.setattr(Path, "open", lambda *_a, **_kw: (_ for _ in ()).throw(AssertionError("text search opened a legacy file")))
        assert _text_search(facade, manifest.legacy_source_namespace_id, fake) == ()
        current = facade.get_memory_by_eid(legacy_source_namespace_id=manifest.legacy_source_namespace_id, eid=1)
        native_source = SimpleNamespace(object_id=current.object_id, revision_id=current.revision_id)
        _ready_vector(connection, native_source, idem, "rederived", (1.0, 0.0, 0.0))
        assert [hit.eid for hit in _text_search(facade, manifest.legacy_source_namespace_id, fake)] == [1]
    finally:
        qualified.close()
