"""Focused Phase 7G2B in-process draft/finalize/representation workflow tests."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import pytest

from torment_service.candidate_types import CandidateShapedValue
from torment_service.substrate.compat import (
    CompatibilityEmbeddingPublicationRequest,
    NativeMemoryCompatibilityFacade,
)
from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.errors import SubstrateIdempotencyConflict, SubstrateObjectNotFound, SubstrateRevisionConflict
from torment_service.substrate.ids import generate_native_id, native_id_to_bytes
from torment_service.substrate.representations import NativeRepresentationService, RepresentationFailureRequest, RepresentationRequest
from torment_service.substrate.schema import CORE_ROLE_STAGING, create_schema, open_schema


def _id(): return generate_native_id()


def _database(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "compat-drafts.db")
    create_schema(qualified.connection)
    connection = qualified.connection
    identities, scope, idem, source_a, source_b = _id(), _id(), _id(), _id(), _id()
    connection.execute("INSERT INTO identity_namespaces VALUES (?,?,0)", (native_id_to_bytes(identities), "compat-drafts-identities"))
    connection.execute("INSERT INTO semantic_scopes VALUES (?,?,0)", (native_id_to_bytes(scope), "compat-drafts-scope"))
    connection.execute("INSERT INTO idempotency_namespaces VALUES (?,?)", (native_id_to_bytes(idem), "compat-drafts-idempotency"))
    connection.execute("INSERT INTO legacy_source_namespaces VALUES (?,?,0)", (native_id_to_bytes(source_a), "compat-drafts-source-a"))
    connection.execute("INSERT INTO legacy_source_namespaces VALUES (?,?,0)", (native_id_to_bytes(source_b), "compat-drafts-source-b"))
    return qualified, identities, scope, idem, source_a, source_b


def _embedding(payload=b"derived-vector"):
    return CompatibilityEmbeddingPublicationRequest(
        payload_bytes=payload, representation_class="COMPAT_EMBEDDING", generation=1,
        derivation_contract_version="compat-embedding-v1", encoding_id="RAW_VECTOR",
        dtype="float32", dimension=3,
    )


def _draft(facade, identities, scope, idem, source, key="draft-1", **kwargs):
    values = {
        "summary": "draft memory", "memory_type": "episodic", "memory_class": "core",
        "strength": 0.7, "confidence": 0.8, "half_life_days": 5.0,
        "user_id": "user-a", "logical_step": 12, "extra_payload": {"tag": "draft"},
    }
    values.update(kwargs)
    return facade.begin_memory_draft(
        legacy_source_namespace_id=source, idempotency_namespace_id=idem, idempotency_key=key,
        identity_namespace_id=identities, semantic_scope_id=scope, **values,
    )


def _semantic_counts(connection):
    return tuple(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in ("objects", "legacy_object_aliases", "object_revisions", "operations", "semantic_transitions", "representations"))


def test_drafts_are_immutable_process_local_and_leave_no_precommit_residue(tmp_path: Path):
    qualified, identities, scope, idem, source_a, _source_b = _database(tmp_path)
    try:
        connection = qualified.connection
        assert open_schema(connection).core_role == CORE_ROLE_STAGING
        facade = NativeMemoryCompatibilityFacade(connection)
        before = _semantic_counts(connection)
        draft = _draft(facade, identities, scope, idem, source_a, extra_payload={"symbols": ["a"], "pos": [1, 2, 3]})
        assert not hasattr(draft, "eid") and _semantic_counts(connection) == before == (0, 0, 0, 0, 0, 0)
        with pytest.raises(TypeError):
            draft.extra_payload["new"] = "not mutable"
        with pytest.raises(SubstrateObjectNotFound):
            facade.resolve_memory_eid(legacy_source_namespace_id=source_a, eid=0)
        with pytest.raises(SubstrateObjectNotFound):
            from torment_service.substrate.objects import NativeObjectService
            NativeObjectService(connection).get_current_object(draft.draft_token)
        enriched = facade.enrich_memory_draft(draft, {"symbols": ["a", "b"], "resonance_score": 0.8, "vel": [0, 1, 0]})
        assert enriched is not draft and draft.extra_payload["symbols"] == ("a",) and enriched.extra_payload["symbols"] == ("a", "b")
        for key in ("scope", "lifecycle_state", "governance", "authority_category", "authorization", "provenance_id", "revision_id", "representation_readiness", "integrity", "reconciliation", "operation_id"):
            with pytest.raises(ValueError):
                facade.enrich_memory_draft(draft, {key: "blocked"})
        facade.abandon_memory_draft(enriched)
        assert _semantic_counts(connection) == before
        with pytest.raises(TypeError):
            _draft(facade, identities, scope, idem, source_a, key="candidate-summary", summary=CandidateShapedValue("sealed"))
        with pytest.raises(TypeError):
            _draft(facade, identities, scope, idem, source_a, key="candidate-extra-object", extra_payload=CandidateShapedValue("sealed"))
        with pytest.raises(TypeError):
            _draft(facade, identities, scope, idem, source_a, key="candidate-extra", extra_payload={"ordinary": CandidateShapedValue("sealed")})
        with pytest.raises(ValueError):
            _draft(facade, identities, scope, idem, source_a, key="invalid-embedding", embedding_request=CompatibilityEmbeddingPublicationRequest(bytearray(b"not-immutable"), "COMPAT_EMBEDDING", 1, "v1", "RAW"))
        assert _semantic_counts(connection) == before
    finally:
        qualified.close()


def test_finalize_allocates_eid_only_at_source_commit_and_is_reconstructibly_idempotent(tmp_path: Path):
    qualified, identities, scope, idem, source_a, source_b = _database(tmp_path)
    try:
        connection = qualified.connection
        facade = NativeMemoryCompatibilityFacade(connection)
        original = _draft(
            facade, identities, scope, idem, source_a, key="source-lost-response",
            extra_payload={"authority": "approved", "permission": "allow", "canon": True},
        )
        assert _semantic_counts(connection) == (0, 0, 0, 0, 0, 0)
        first = facade.finalize_memory_draft(original, publish_embedding=False)
        assert first.eid == 0 and first.representation is None
        assert facade.get_memory_by_eid(legacy_source_namespace_id=source_a, eid=first.eid).object_id == first.object_id
        assert connection.execute("SELECT lineage_kind,lifecycle_state,authority_category FROM object_revisions WHERE object_revision_id=?", (native_id_to_bytes(first.revision_id),)).fetchone() == ("NATIVE_CREATION", "PROTECTED", "NOT_APPLICABLE")
        reconstructed = _draft(
            facade, identities, scope, idem, source_a, key="source-lost-response",
            extra_payload={"authority": "approved", "permission": "allow", "canon": True},
        )
        assert reconstructed.draft_token != original.draft_token
        assert facade.finalize_memory_draft(reconstructed, publish_embedding=False).source == first.source
        with pytest.raises(SubstrateIdempotencyConflict):
            facade.finalize_memory_draft(_draft(facade, identities, scope, idem, source_a, key="source-lost-response", summary="changed"), publish_embedding=False)
        other = facade.finalize_memory_draft(_draft(facade, identities, scope, idem, source_b, key="source-b"), publish_embedding=False)
        assert other.eid == 0 and other.object_id != first.object_id
    finally:
        qualified.close()


def test_embedding_preestablishes_then_publishes_ready_and_stays_bound_to_r1(tmp_path: Path):
    qualified, identities, scope, idem, source_a, _source_b = _database(tmp_path)
    try:
        connection = qualified.connection
        facade = NativeMemoryCompatibilityFacade(connection)
        draft = _draft(facade, identities, scope, idem, source_a, key="embedding-ready", embedding_request=_embedding())
        prepared = facade.prepare_memory_draft_embedding(draft)
        assert prepared.representation.readiness == "PENDING" and prepared.expectation.expected_value == sha256(b"derived-vector").digest()
        assert connection.execute("SELECT count(*) FROM representation_payloads WHERE representation_id=?", (native_id_to_bytes(prepared.representation.representation_id),)).fetchone()[0] == 0
        result = facade.finalize_memory_draft(draft)
        assert result.source == prepared.source and result.representation is not None
        assert (result.representation.readiness, result.representation.disposition) == ("READY", "USABLE")
        assert connection.execute("SELECT source_object_id,source_object_revision_id,source_object_revision_ordinal FROM representations WHERE representation_id=?", (native_id_to_bytes(result.representation.representation_id),)).fetchone() == (native_id_to_bytes(result.object_id), native_id_to_bytes(result.revision_id), 1)
        service = NativeRepresentationService(connection)
        traced: list[str] = []
        connection.set_trace_callback(traced.append)
        assert service.get_representation_metadata(result.representation.representation_id).readiness == "READY"
        connection.set_trace_callback(None)
        assert not any("representation_payloads" in statement.lower() for statement in traced)
        assert service.read_representation_payload(result.representation.representation_id) == b"derived-vector"
        r2 = facade.patch_memory_state(legacy_source_namespace_id=source_a, eid=result.eid, patch={"strength": 0.9}, idempotency_namespace_id=idem, idempotency_key="r2")
        assert r2.revision_id != result.revision_id
        assert connection.execute("SELECT source_object_revision_id FROM representations WHERE representation_id=?", (native_id_to_bytes(result.representation.representation_id),)).fetchone()[0] == native_id_to_bytes(result.revision_id)
        retry = facade.finalize_memory_draft(_draft(facade, identities, scope, idem, source_a, key="embedding-ready", embedding_request=_embedding()))
        assert retry == result
        with pytest.raises(SubstrateIdempotencyConflict):
            facade.finalize_memory_draft(_draft(facade, identities, scope, idem, source_a, key="embedding-ready", embedding_request=_embedding(b"changed")))
    finally:
        qualified.close()


def test_embedding_failure_is_local_to_pending_representation_and_source_survives(tmp_path: Path):
    qualified, identities, scope, idem, source_a, _source_b = _database(tmp_path)
    try:
        connection = qualified.connection
        facade = NativeMemoryCompatibilityFacade(connection)
        dependency_source = facade.finalize_memory_draft(_draft(facade, identities, scope, idem, source_a, key="dependency-source"), publish_embedding=False).source
        dependency = NativeRepresentationService(connection).create_representation_pending(
            idempotency_namespace_id=idem, idempotency_key="dependency-pending",
            request=RepresentationRequest("OBJECT_REVISION", dependency_source.object_id, dependency_source.revision_id, None, None, "DEPENDENCY", 1, "v1", "RAW", expected_payload_byte_length=1),
        )
        blocked_draft = _draft(facade, identities, scope, idem, source_a, key="blocked-embedding", embedding_request=CompatibilityEmbeddingPublicationRequest(b"blocked", "COMPAT_EMBEDDING", 1, "compat-embedding-v1", "RAW_VECTOR", dependencies=(dependency.representation_id,)))
        with pytest.raises(SubstrateRevisionConflict, match="dependencies are not ready"):
            facade.finalize_memory_draft(blocked_draft)
        source = facade.finalize_memory_draft(blocked_draft, publish_embedding=False).source
        pending = facade.prepare_memory_draft_embedding(blocked_draft).representation
        assert facade.get_memory_by_eid(legacy_source_namespace_id=source_a, eid=source.eid).revision_id == source.revision_id
        assert (pending.readiness, pending.disposition) == ("PENDING", "WITHHELD")
        assert connection.execute("SELECT count(*) FROM representation_payloads WHERE representation_id=?", (native_id_to_bytes(pending.representation_id),)).fetchone()[0] == 0
        failed = NativeRepresentationService(connection).fail_representation(
            idempotency_namespace_id=idem, idempotency_key="blocked-explicit-failure",
            request=RepresentationFailureRequest(pending.representation_id, "DEPENDENCY_UNAVAILABLE"),
        )
        assert (failed.readiness, failed.disposition) == ("FAILED", "WITHHELD")
        assert facade.get_memory_by_eid(legacy_source_namespace_id=source_a, eid=source.eid).object_id == source.object_id
    finally:
        qualified.close()
