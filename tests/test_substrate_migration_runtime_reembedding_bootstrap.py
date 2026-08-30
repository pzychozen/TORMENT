"""Phase 7G5B3B caller-owned re-embedding bootstrap qualification."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from uuid import UUID

import numpy as np
import pytest

from torment_service.substrate.compat_embedding_reader import NativeCompatEmbeddingReader
from torment_service.substrate.errors import SubstrateIdempotencyConflict
from torment_service.substrate.ids import generate_native_id, native_id_to_bytes
from torment_service.substrate.migration import (
    LegacyVectorStrategy,
    MigrationRuntimeReadinessRequest,
    MigrationRuntimeReembeddingBootstrapRefused,
    MigrationRuntimeReembeddingBootstrapRequest,
    NativeMigrationRuntimeReadinessPreflight,
    NativeMigrationRuntimeReembeddingBootstrapService,
    ObjectRuntimeReadiness,
)
from torment_service.substrate.representations import (
    INTEGRITY_ALGORITHM_SHA256,
    INTEGRITY_VALUE_ENCODING_RAW,
    NativeRepresentationService,
    RepresentationIntegrityExpectationRequest,
    RepresentationReadyRequest,
    RepresentationRequest,
)

from test_substrate_migration_runtime_representation_bootstrap import (
    _b1_request,
    _fixture,
    _normalize,
    _payload,
)


class _CountingEmbedder:
    def __init__(self, values, *, provider: str = "synthetic", model: str = "synthetic", dim: int = 3) -> None:
        self.provider = provider
        self.model = model
        self.dim = dim
        self._values = list(values)
        self.calls: list[str] = []

    def embed(self, text: str):
        self.calls.append(text)
        value = self._values[min(len(self.calls) - 1, len(self._values) - 1)]
        if isinstance(value, BaseException):
            raise value
        return value


def _context(tmp_path: Path, **fixture_kwargs):
    tmp_path.mkdir(parents=True, exist_ok=True)
    qualified, facts = _fixture(tmp_path, **fixture_kwargs)
    facts["connection"] = qualified.connection
    r2 = _normalize(facts)
    return qualified, facts, r2.revision_id


def _request(facts: dict[str, object], r2: UUID, *, key: str = "b3b-bootstrap", lane=None):
    return MigrationRuntimeReembeddingBootstrapRequest(
        snapshot_root=facts["root"], manifest_path=facts["manifest_path"],
        legacy_snapshot_id=facts["manifest"].legacy_snapshot_id,
        legacy_source_namespace_id=facts["source_namespace"],
        expected_native_core_id=UUID(bytes=facts["metadata"].core_id), eid=7,
        expected_r1_revision_id=facts["r1"], expected_r2_revision_id=r2,
        scope_plans=(facts["plan"],), target_lane=lane or facts["lane"],
        idempotency_namespace_id=facts["idempotency"], idempotency_key=key,
    )


def _item(connection, facts):
    report = NativeMigrationRuntimeReadinessPreflight(connection).run(_b1_request(facts))
    assert len(report.object_items) == 1
    return report.object_items[0]


def _compat_count(connection) -> int:
    return connection.execute(
        "SELECT count(*) FROM representations WHERE representation_class='COMPAT_EMBEDDING'"
    ).fetchone()[0]


def _legacy_capture(connection):
    return connection.execute(
        """
        SELECT r.representation_id,r.source_object_revision_id,r.representation_class,
               r.expected_payload_byte_length,s.readiness,s.operational_disposition,p.payload_bytes
          FROM representations r
          JOIN representation_current_state s USING(representation_id)
          JOIN representation_payloads p USING(representation_id)
         WHERE r.representation_class='LEGACY_EMBEDDING_CAPTURE'
        """
    ).fetchone()


@pytest.mark.parametrize(
    ("label", "fixture_kwargs", "strategy"),
    (
        ("reembed", {"provider": "different-provider"}, LegacyVectorStrategy.REEMBED_REQUIRED),
        ("no-vector", {"include_vector": False}, LegacyVectorStrategy.NO_VECTOR_PRESENT),
        ("unusable", {"vector": np.asarray((np.nan, 0.0, 0.0), dtype=np.float32)}, LegacyVectorStrategy.UNUSABLE_VECTOR_EVIDENCE),
    ),
)
def test_b3b_positive_b1_b2_progressions_and_evidence_retention(
    tmp_path: Path, label: str, fixture_kwargs: dict[str, object], strategy: LegacyVectorStrategy,
):
    qualified, facts, r2 = _context(tmp_path, **fixture_kwargs)
    try:
        connection = qualified.connection
        before_item = _item(connection, facts)
        assert before_item.readiness is ObjectRuntimeReadiness.REPRESENTATION_BOOTSTRAP_REQUIRED
        assert before_item.legacy_vector_strategy is strategy
        capture_before = _legacy_capture(connection)
        effect_tables = (
            "objects", "object_revisions", "legacy_object_aliases", "memory_runtime_enumeration_orders",
            "object_revision_governance", "provenance_records",
        )
        effects_before = {
            table: connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in effect_tables
        }
        embedder = _CountingEmbedder([np.asarray((2.0, 0.6, 0.0), dtype=np.float32)])
        result = NativeMigrationRuntimeReembeddingBootstrapService(connection).bootstrap_from_qualified_text(
            _request(facts, r2, key=f"positive-{label}"), embedder=embedder,
        )
        assert embedder.calls == ["evidence-complete legacy memory"]
        assert result.r2_revision_id == r2
        assert result.payload_sha256 == hashlib.sha256(
            np.asarray((2.0, 0.6, 0.0), dtype=np.float32).tobytes()
        ).hexdigest()
        assert _item(connection, facts).readiness is ObjectRuntimeReadiness.RUNTIME_READY_AS_IS
        assert connection.execute("SELECT count(*) FROM object_revisions WHERE object_id=?", (
            native_id_to_bytes(result.object_id),
        )).fetchone()[0] == 2
        assert effects_before == {
            table: connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in effect_tables
        }
        if capture_before is None:
            assert _legacy_capture(connection) is None
        else:
            assert _legacy_capture(connection) == capture_before
            assert result.retained_legacy_capture_ids == (UUID(bytes=capture_before[0]),)
        assert _compat_count(connection) == 1
    finally:
        qualified.close()


def test_b3b_refuses_b3a_byte_derivation_before_embedder_contact(tmp_path: Path):
    qualified, facts, r2 = _context(tmp_path)
    try:
        embedder = _CountingEmbedder([np.zeros(3, dtype=np.float32)])
        with pytest.raises(MigrationRuntimeReembeddingBootstrapRefused, match="B3A_DETERMINISTIC_CAPTURE"):
            NativeMigrationRuntimeReembeddingBootstrapService(qualified.connection).bootstrap_from_qualified_text(
                _request(facts, r2), embedder=embedder,
            )
        assert not embedder.calls
        assert _compat_count(qualified.connection) == 0
    finally:
        qualified.close()


def test_b3b_refuses_unresolved_or_non_b2_current_before_embedder_contact(tmp_path: Path):
    qualified, facts = _fixture(tmp_path, provider="different-provider")
    facts["connection"] = qualified.connection
    try:
        embedder = _CountingEmbedder([np.zeros(3, dtype=np.float32)])
        with pytest.raises(MigrationRuntimeReembeddingBootstrapRefused):
            NativeMigrationRuntimeReembeddingBootstrapService(qualified.connection).bootstrap_from_qualified_text(
                _request(facts, facts["r1"]), embedder=embedder,
            )
        assert not embedder.calls
        assert _compat_count(qualified.connection) == 0
    finally:
        qualified.close()


@pytest.mark.parametrize(
    ("provider", "model", "dim", "code"),
    (
        ("wrong", "synthetic", 3, "PROVIDER"),
        ("synthetic", "wrong", 3, "MODEL"),
        ("synthetic", "synthetic", 4, "DIMENSION"),
    ),
)
def test_b3b_refuses_embedder_identity_mismatch_before_contact(
    tmp_path: Path, provider: str, model: str, dim: int, code: str,
):
    qualified, facts, r2 = _context(tmp_path, provider="different-provider")
    try:
        embedder = _CountingEmbedder([np.zeros(3, dtype=np.float32)], provider=provider, model=model, dim=dim)
        with pytest.raises(MigrationRuntimeReembeddingBootstrapRefused, match=code):
            NativeMigrationRuntimeReembeddingBootstrapService(qualified.connection).bootstrap_from_qualified_text(
                _request(facts, r2), embedder=embedder,
            )
        assert not embedder.calls
        assert _compat_count(qualified.connection) == 0
    finally:
        qualified.close()


@pytest.mark.parametrize(
    ("value", "code"),
    (
        (RuntimeError("provider unavailable"), "TARGET_EMBEDDER_FAILED"),
        ("not an embedding", "TARGET_EMBEDDER_OUTPUT_INVALID"),
        (np.zeros(2, dtype=np.float32), "TARGET_EMBEDDER_DIMENSION_INVALID"),
        (np.asarray((0.0, np.nan, 0.0), dtype=np.float32), "TARGET_EMBEDDER_NONFINITE"),
        (np.asarray((0.0, np.inf, 0.0), dtype=np.float32), "TARGET_EMBEDDER_NONFINITE"),
    ),
)
def test_b3b_model_failures_publish_no_representation(tmp_path: Path, value, code: str):
    qualified, facts, r2 = _context(tmp_path, provider="different-provider")
    try:
        embedder = _CountingEmbedder([value])
        with pytest.raises(MigrationRuntimeReembeddingBootstrapRefused, match=code):
            NativeMigrationRuntimeReembeddingBootstrapService(qualified.connection).bootstrap_from_qualified_text(
                _request(facts, r2), embedder=embedder,
            )
        assert len(embedder.calls) == 1
        assert _compat_count(qualified.connection) == 0
    finally:
        qualified.close()


def test_b3b_fresh_success_and_ready_retry_use_exact_one_model_call(tmp_path: Path):
    qualified, facts, r2 = _context(tmp_path, provider="different-provider")
    try:
        embedder = _CountingEmbedder([np.asarray((1.5, -2.0, 0.0), dtype=np.float64)])
        service = NativeMigrationRuntimeReembeddingBootstrapService(qualified.connection)
        request = _request(facts, r2)
        first = service.bootstrap_from_qualified_text(request, embedder=embedder)
        second = service.bootstrap_from_qualified_text(request, embedder=embedder)
        assert first == second
        assert embedder.calls == ["evidence-complete legacy memory"]
        witness = NativeCompatEmbeddingReader(qualified.connection).read_current(
            first.object_id, expected_dimension=3,
        )
        assert witness is not None
        assert witness.payload_bytes == np.asarray((1.5, -2.0, 0.0), dtype=np.float32).tobytes()
    finally:
        qualified.close()


def test_b3b_pending_interruption_reembeds_then_establishes_fresh_expectation(tmp_path: Path):
    qualified, facts, r2 = _context(tmp_path, provider="different-provider")
    try:
        embedder = _CountingEmbedder([
            np.asarray((1.0, 0.0, 0.0), dtype=np.float32),
            np.asarray((2.0, 0.0, 0.0), dtype=np.float32),
        ])
        service = NativeMigrationRuntimeReembeddingBootstrapService(qualified.connection)
        request = _request(facts, r2)
        with pytest.raises(RuntimeError, match="pending"):
            service.bootstrap_from_qualified_text(request, embedder=embedder, _test_stop_after="PENDING")
        assert _compat_count(qualified.connection) == 1
        row = qualified.connection.execute(
            "SELECT count(*) FROM integrity_expectations"
        ).fetchone()[0]
        assert row == 0
        result = service.bootstrap_from_qualified_text(request, embedder=embedder)
        assert len(embedder.calls) == 2
        assert result.payload_sha256 == hashlib.sha256(
            np.asarray((2.0, 0.0, 0.0), dtype=np.float32).tobytes()
        ).hexdigest()
    finally:
        qualified.close()


def test_b3b_expectation_interruption_requires_byte_stable_retry(tmp_path: Path):
    qualified, facts, r2 = _context(tmp_path, provider="different-provider")
    try:
        vector = np.asarray((1.0, 2.0, 3.0), dtype=np.float32)
        embedder = _CountingEmbedder([vector, vector.copy()])
        service = NativeMigrationRuntimeReembeddingBootstrapService(qualified.connection)
        request = _request(facts, r2)
        with pytest.raises(RuntimeError, match="expectation"):
            service.bootstrap_from_qualified_text(request, embedder=embedder, _test_stop_after="EXPECTATION")
        result = service.bootstrap_from_qualified_text(request, embedder=embedder)
        assert len(embedder.calls) == 2
        assert result.payload_sha256 == hashlib.sha256(vector.tobytes()).hexdigest()
    finally:
        qualified.close()


def test_b3b_nondeterministic_post_expectation_output_fails_closed(tmp_path: Path):
    qualified, facts, r2 = _context(tmp_path, provider="different-provider")
    try:
        first = np.asarray((1.0, 0.0, 0.0), dtype=np.float32)
        second = np.asarray((0.0, 1.0, 0.0), dtype=np.float32)
        embedder = _CountingEmbedder([first, second])
        service = NativeMigrationRuntimeReembeddingBootstrapService(qualified.connection)
        request = _request(facts, r2)
        with pytest.raises(RuntimeError, match="expectation"):
            service.bootstrap_from_qualified_text(request, embedder=embedder, _test_stop_after="EXPECTATION")
        expectation = qualified.connection.execute(
            "SELECT expected_value FROM integrity_expectations"
        ).fetchone()[0]
        with pytest.raises(MigrationRuntimeReembeddingBootstrapRefused, match="NOT_BYTE_STABLE"):
            service.bootstrap_from_qualified_text(request, embedder=embedder)
        assert expectation == qualified.connection.execute(
            "SELECT expected_value FROM integrity_expectations"
        ).fetchone()[0]
        assert len(embedder.calls) == 2
        assert qualified.connection.execute(
            """SELECT readiness,operational_disposition FROM representation_current_state
                 WHERE representation_id=(SELECT representation_id FROM representations
                                           WHERE representation_class='COMPAT_EMBEDDING')"""
        ).fetchone() == ("PENDING", "WITHHELD")
        assert _compat_count(qualified.connection) == 1
    finally:
        qualified.close()


def test_b3b_ready_response_loss_recovers_without_another_model_call(tmp_path: Path):
    qualified, facts, r2 = _context(tmp_path, provider="different-provider")
    try:
        embedder = _CountingEmbedder([np.asarray((0.0, 0.0, 0.0), dtype=np.float32)])
        service = NativeMigrationRuntimeReembeddingBootstrapService(qualified.connection)
        request = _request(facts, r2)
        with pytest.raises(RuntimeError, match="response loss"):
            service.bootstrap_from_qualified_text(request, embedder=embedder, _test_lose_response_after_ready=True)
        recovered = service.bootstrap_from_qualified_text(request, embedder=embedder)
        assert len(embedder.calls) == 1
        assert recovered.payload_byte_length == 12
        assert _item(qualified.connection, facts).readiness is ObjectRuntimeReadiness.RUNTIME_READY_AS_IS
    finally:
        qualified.close()


def test_b3b_refuses_competing_current_compat_before_contact(tmp_path: Path):
    qualified, facts, r2 = _context(tmp_path, provider="different-provider")
    try:
        connection = qualified.connection
        representations = NativeRepresentationService(connection)
        pending = representations.create_representation_pending(
            idempotency_namespace_id=facts["idempotency"], idempotency_key="competing-b3b",
            request=RepresentationRequest(
                source_kind="OBJECT_REVISION", object_id=facts["object_id"], object_revision_id=r2,
                relationship_id=None, relationship_revision_id=None, representation_class="COMPAT_EMBEDDING",
                generation=1, derivation_contract_version="compat-embedding-v1", encoding_id="RAW_VECTOR",
                dtype="float32", dimension=3, representation_id=generate_native_id(),
                expected_payload_byte_length=12,
            ),
        )
        payload = np.asarray((3.0, 2.0, 1.0), dtype=np.float32).tobytes()
        representations.establish_representation_integrity_expectation(
            idempotency_namespace_id=facts["idempotency"], idempotency_key="competing-b3b-expectation",
            request=RepresentationIntegrityExpectationRequest(
                representation_id=pending.representation_id, algorithm_id=INTEGRITY_ALGORITHM_SHA256,
                expected_value=hashlib.sha256(payload).digest(), value_encoding=INTEGRITY_VALUE_ENCODING_RAW,
            ),
        )
        representations.publish_representation_ready(
            idempotency_namespace_id=facts["idempotency"], idempotency_key="competing-b3b-ready",
            request=RepresentationReadyRequest(
                representation_id=pending.representation_id, representation_class="COMPAT_EMBEDDING",
                generation=1, derivation_contract_version="compat-embedding-v1", encoding_id="RAW_VECTOR",
                payload_bytes=payload,
            ),
        )
        assert _item(connection, facts).readiness is ObjectRuntimeReadiness.RUNTIME_READY_AS_IS
        embedder = _CountingEmbedder([np.zeros(3, dtype=np.float32)])
        with pytest.raises(MigrationRuntimeReembeddingBootstrapRefused, match="COMPETING"):
            NativeMigrationRuntimeReembeddingBootstrapService(connection).bootstrap_from_qualified_text(
                _request(facts, r2), embedder=embedder,
            )
        assert not embedder.calls
    finally:
        qualified.close()


def test_b3b_canonical_input_preference_fallback_and_stale_payload_metadata(tmp_path: Path):
    summary_payload = _payload(summary="summary is preferred")
    summary_payload.update({
        "text": "text must not be embedded", "embedding_provider": "stale",
        "embedding_model": "old", "embedding_dim": 999, "embedding_checksum": "old-hash",
    })
    qualified, facts, r2 = _context(
        tmp_path / "summary", provider="different-provider", payload=summary_payload,
    )
    try:
        connection = qualified.connection
        payload_before = connection.execute(
            "SELECT payload_text FROM object_revisions WHERE object_revision_id=?", (native_id_to_bytes(r2),)
        ).fetchone()[0]
        summary_embedder = _CountingEmbedder([np.asarray((1.0, 1.0, 1.0), dtype=np.float32)])
        result = NativeMigrationRuntimeReembeddingBootstrapService(connection).bootstrap_from_qualified_text(
            _request(facts, r2), embedder=summary_embedder,
        )
        assert summary_embedder.calls == ["summary is preferred"]
        assert connection.execute(
            "SELECT payload_text FROM object_revisions WHERE object_revision_id=?", (native_id_to_bytes(r2),)
        ).fetchone()[0] == payload_before
        witness = NativeCompatEmbeddingReader(connection).read_current(result.object_id, expected_dimension=3)
        assert witness is not None and witness.representation_id == result.representation_id
    finally:
        qualified.close()

    text_payload = _payload()
    text_payload.pop("summary")
    text_payload["text"] = "text fallback exactly"
    qualified, facts, r2 = _context(tmp_path / "text", provider="different-provider", payload=text_payload)
    try:
        embedder = _CountingEmbedder([np.asarray((1.0, 1.0, 1.0), dtype=np.float32)])
        NativeMigrationRuntimeReembeddingBootstrapService(qualified.connection).bootstrap_from_qualified_text(
            _request(facts, r2), embedder=embedder,
        )
        assert embedder.calls == ["text fallback exactly"]
    finally:
        qualified.close()


def test_b3b_stale_r2_retry_is_idempotency_conflict_before_embedder_contact(tmp_path: Path):
    qualified, facts, r2 = _context(tmp_path, provider="different-provider")
    try:
        service = NativeMigrationRuntimeReembeddingBootstrapService(qualified.connection)
        original = _request(facts, r2)
        first_embedder = _CountingEmbedder([np.ones(3, dtype=np.float32)])
        service.bootstrap_from_qualified_text(original, embedder=first_embedder)
        changed = _request(facts, generate_native_id())
        retry_embedder = _CountingEmbedder([np.zeros(3, dtype=np.float32)])
        with pytest.raises(SubstrateIdempotencyConflict):
            service.bootstrap_from_qualified_text(changed, embedder=retry_embedder)
        assert not retry_embedder.calls
    finally:
        qualified.close()
