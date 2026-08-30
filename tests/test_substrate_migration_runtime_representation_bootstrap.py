"""Phase 7G5B3A captured-vector bootstrap qualification."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from uuid import UUID

import numpy as np
import pytest

from torment_service.provenance_v1 import ProvenanceV1
from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.errors import SubstrateIdempotencyConflict
from torment_service.substrate.ids import generate_native_id, native_id_to_bytes
from torment_service.substrate.migration import (
    MigrationRehearsalConfig,
    MigrationRuntimeNormalizationRequest,
    MigrationRuntimeReadinessRequest,
    MigrationRuntimeRepresentationBootstrapRefused,
    MigrationRuntimeRepresentationBootstrapRequest,
    MigrationRuntimeScopePlan,
    NativeLegacyMigrationRehearsal,
    NativeMigrationRuntimeNormalizationService,
    NativeMigrationRuntimeReadinessPreflight,
    NativeMigrationRuntimeRepresentationBootstrapService,
    ObjectRuntimeReadiness,
    create_snapshot_manifest,
)
from torment_service.substrate.representations import (
    INTEGRITY_ALGORITHM_SHA256,
    INTEGRITY_VALUE_ENCODING_RAW,
    NativeRepresentationService,
    RepresentationIntegrityExpectationRequest,
    RepresentationReadyRequest,
    RepresentationRequest,
)
from torment_service.substrate.runtime_binding import NativeRepresentationLane
from torment_service.substrate.schema import create_schema


def _id():
    return generate_native_id()


def _line(value: dict[str, object]) -> bytes:
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False).encode("utf-8") + b"\n"


def _payload(*, summary: str = "evidence-complete legacy memory") -> dict[str, object]:
    return {
        "summary": summary, "type": "memory", "memory_class": "core", "strength": 0.75,
        "confidence": 0.9, "seed_pos0": [1, 2, 3], "seed_v0": [0.1, 0.2, 0.3],
        "governance": {
            "protected": False, "non_shareable": True, "collective_export_blocked": True,
            "collective_reingest_blocked": False, "decay_accelerated": False,
        },
        "provenance": ProvenanceV1(
            source_type="role_output", source_role="archivist", write_path="cognition_writeback",
            parent_eids=[], created_at_step=4, created_at_ts="2024-01-02T03:04:05Z",
        ).to_dict(),
        "lifecycle_status": {
            "state": "active", "is_authoritative_on_row": True, "requires_join": None,
            "set_by": {"actor": "user", "via": "api", "at": 7}, "history_ref": None,
        },
    }


def _fixture(
    tmp_path: Path,
    *,
    vector: np.ndarray | None = None,
    provider: str = "synthetic",
    model: str = "synthetic",
    dtype: str = "float32",
    include_vector: bool = True,
):
    qualified = open_temporary_test_connection(tmp_path / "b3a.db")
    connection = qualified.connection
    metadata = create_schema(connection)
    object_namespace, relationship_namespace = _id(), _id()
    unknown_scope, target_scope, idempotency = _id(), _id(), _id()
    for value, key in ((object_namespace, "b3a-objects"), (relationship_namespace, "b3a-relationships")):
        connection.execute("INSERT INTO identity_namespaces VALUES (?,?,0)", (native_id_to_bytes(value), key))
    for value, key in ((unknown_scope, "b3a-unknown"), (target_scope, "b3a-target")):
        connection.execute("INSERT INTO semantic_scopes VALUES (?,?,0)", (native_id_to_bytes(value), key))
    connection.execute("INSERT INTO idempotency_namespaces VALUES (?,?)", (native_id_to_bytes(idempotency), "b3a-idempotency"))

    root = tmp_path / "frozen" / "legacy"
    root.mkdir(parents=True)
    node: dict[str, object] = {"eid": 7, "born_step": 12, "channel": 4, "payload": _payload()}
    actual = vector if vector is not None else np.asarray((2.0, 0.6, 0.0), dtype=np.float32)
    if include_vector:
        node["embedding_ref"] = {
            "map": "embeddings/shard.map.jsonl", "shard": "embeddings/shard.npy", "row": 0,
            "dimension": int(actual.size), "dtype": dtype,
        }
        embeddings = root / "embeddings"
        embeddings.mkdir()
        np.save(embeddings / "shard.npy", actual.reshape(1, -1))
        (embeddings / "manifest.json").write_bytes(_line({
            "encoding_id": "NUMPY_NPY", "dtype": dtype, "dimension": int(actual.size),
            "derivation_contract_version": "synthetic-captured-v1", "provider": provider, "model": model,
            "shards": [{"path": "embeddings/shard.npy", "map": "embeddings/shard.map.jsonl"}],
        }))
        (embeddings / "shard.map.jsonl").write_bytes(_line({
            "eid": 7, "shard": "embeddings/shard.npy", "row": 0, "dimension": int(actual.size),
        }))
    (root / "nodes.jsonl").write_bytes(_line(node))
    source_namespace = _id()
    manifest_path = root.parent / "manifest.json"
    manifest = create_snapshot_manifest(
        snapshot_root=root, manifest_path=manifest_path, legacy_source_namespace_id=source_namespace,
        legacy_source_namespace_key="b3a-source", capture_label="B3A evidence-complete fixture",
    )
    NativeLegacyMigrationRehearsal(connection).run(
        snapshot_root=root, manifest_path=manifest_path,
        config=MigrationRehearsalConfig(
            native_core_id=_id(), idempotency_namespace_id=idempotency,
            object_identity_namespace_id=object_namespace,
            relationship_identity_namespace_id=relationship_namespace,
            unknown_semantic_scope_id=unknown_scope,
        ),
    )
    plan = MigrationRuntimeScopePlan(
        legacy_source_namespace_id=source_namespace, workspace_id="orchard", scope_kind="PRIVATE_AGENT",
        agent_id="aria", target_identity_namespace_id=object_namespace, target_semantic_scope_id=target_scope,
        motif_alias_namespace_id=source_namespace, motif_identity_namespace_id=object_namespace,
        membership_identity_namespace_id=relationship_namespace, idempotency_namespace_id=idempotency,
    )
    lane = NativeRepresentationLane(
        provider="synthetic", model="synthetic", dimension=3, representation_class="COMPAT_EMBEDDING",
        generation=1, derivation_contract_version="compat-embedding-v1", encoding_id="RAW_VECTOR", dtype="float32",
    )
    object_id, r1 = connection.execute(
        """SELECT object_id,current_revision_id FROM objects
             WHERE object_id=(SELECT object_id FROM legacy_object_aliases WHERE legacy_source_namespace_id=? AND alias_value='7')""",
        (native_id_to_bytes(source_namespace),),
    ).fetchone()
    facts = {
        "metadata": metadata, "root": root, "manifest_path": manifest_path, "manifest": manifest,
        "source_namespace": source_namespace, "idempotency": idempotency, "plan": plan, "lane": lane,
        "object_id": UUID(bytes=object_id), "r1": UUID(bytes=r1), "vector": actual.astype(np.float32).tobytes(),
    }
    return qualified, facts


def _b1_request(facts: dict[str, object]) -> MigrationRuntimeReadinessRequest:
    return MigrationRuntimeReadinessRequest(
        legacy_snapshot_id=facts["manifest"].legacy_snapshot_id,
        expected_native_core_id=UUID(bytes=facts["metadata"].core_id),
        scope_plans=(facts["plan"],), target_lane=facts["lane"],
    )


def _normalize(facts: dict[str, object]):
    return NativeMigrationRuntimeNormalizationService(facts["connection"]).normalize_legacy_core_memory(
        MigrationRuntimeNormalizationRequest(
            snapshot_root=facts["root"], manifest_path=facts["manifest_path"],
            legacy_snapshot_id=facts["manifest"].legacy_snapshot_id,
            legacy_source_namespace_id=facts["source_namespace"],
            expected_native_core_id=UUID(bytes=facts["metadata"].core_id), eid=7,
            expected_revision_id=facts["r1"], scope_plans=(facts["plan"],),
            idempotency_namespace_id=facts["idempotency"], idempotency_key="b3a-normalize",
        )
    )


def _bootstrap_request(facts: dict[str, object], r2: UUID, *, key: str = "b3a-bootstrap", lane=None):
    return MigrationRuntimeRepresentationBootstrapRequest(
        snapshot_root=facts["root"], manifest_path=facts["manifest_path"],
        legacy_snapshot_id=facts["manifest"].legacy_snapshot_id,
        legacy_source_namespace_id=facts["source_namespace"],
        expected_native_core_id=UUID(bytes=facts["metadata"].core_id), eid=7,
        expected_r1_revision_id=facts["r1"], expected_r2_revision_id=r2,
        target_lane=lane or facts["lane"], idempotency_namespace_id=facts["idempotency"], idempotency_key=key,
    )


def _representation_counts(connection) -> tuple[int, int, int, int]:
    return tuple(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in (
        "representations", "representation_payloads", "integrity_expectations", "integrity_measurements",
    ))


def test_b3a_exact_bytes_complete_b1_b2_b3a_chain(tmp_path: Path):
    qualified, facts = _fixture(tmp_path)
    facts["connection"] = qualified.connection
    try:
        connection = qualified.connection
        initial = NativeMigrationRuntimeReadinessPreflight(connection).run(_b1_request(facts))
        assert initial.object_items[0].readiness is ObjectRuntimeReadiness.DETERMINISTIC_NORMALIZATION_REQUIRED
        r2 = _normalize(facts)
        normalized = NativeMigrationRuntimeReadinessPreflight(connection).run(_b1_request(facts))
        assert normalized.object_items[0].readiness is ObjectRuntimeReadiness.REPRESENTATION_BOOTSTRAP_REQUIRED
        capture_before = connection.execute(
            """SELECT r.representation_id,r.source_object_revision_id,s.readiness,s.operational_disposition,p.payload_bytes
                 FROM representations r JOIN representation_current_state s USING(representation_id)
                 JOIN representation_payloads p USING(representation_id)
                 WHERE r.representation_class='LEGACY_EMBEDDING_CAPTURE'"""
        ).fetchone()
        result = NativeMigrationRuntimeRepresentationBootstrapService(connection).bootstrap_from_legacy_capture(
            _bootstrap_request(facts, r2.revision_id)
        )
        assert result.payload_sha256 == hashlib.sha256(facts["vector"]).hexdigest()
        assert result.payload_byte_length == len(facts["vector"])
        witness = connection.execute(
            """SELECT r.source_object_revision_id,r.source_object_revision_ordinal,r.representation_class,
                      r.generation,r.derivation_contract_version,r.encoding_id,r.dtype,r.dimension,
                      s.readiness,s.operational_disposition,p.payload_bytes
                 FROM representations r JOIN representation_current_state s USING(representation_id)
                 JOIN representation_payloads p USING(representation_id) WHERE r.representation_id=?""",
            (native_id_to_bytes(result.representation_id),),
        ).fetchone()
        assert witness == (
            native_id_to_bytes(r2.revision_id), 2, "COMPAT_EMBEDDING", 1, "compat-embedding-v1", "RAW_VECTOR",
            "float32", 3, "READY", "USABLE", facts["vector"],
        )
        assert connection.execute(
            "SELECT result,observed_value FROM integrity_measurements WHERE measurement_id=?",
            (native_id_to_bytes(result.selected_measurement_id),),
        ).fetchone() == ("MATCH", hashlib.sha256(facts["vector"]).digest())
        assert connection.execute(
            "SELECT current_revision_id,current_revision_ordinal FROM objects WHERE object_id=?",
            (native_id_to_bytes(facts["object_id"]),),
        ).fetchone() == (native_id_to_bytes(r2.revision_id), 2)
        assert connection.execute(
            """SELECT r.representation_id,r.source_object_revision_id,s.readiness,s.operational_disposition,p.payload_bytes
                 FROM representations r JOIN representation_current_state s USING(representation_id)
                 JOIN representation_payloads p USING(representation_id)
                 WHERE r.representation_class='LEGACY_EMBEDDING_CAPTURE'"""
        ).fetchone() == capture_before
        after = NativeMigrationRuntimeReadinessPreflight(connection).run(_b1_request(facts))
        assert after.object_items[0].readiness is ObjectRuntimeReadiness.RUNTIME_READY_AS_IS
        assert connection.execute("SELECT count(*) FROM object_revisions").fetchone()[0] == 2
    finally:
        qualified.close()


@pytest.mark.parametrize("stop", ["PENDING", "EXPECTATION", "READY"])
def test_b3a_phase_response_loss_recovers_without_duplicate_representation(tmp_path: Path, stop: str):
    qualified, facts = _fixture(tmp_path)
    facts["connection"] = qualified.connection
    try:
        r2 = _normalize(facts)
        service = NativeMigrationRuntimeRepresentationBootstrapService(qualified.connection)
        request = _bootstrap_request(facts, r2.revision_id, key=f"lost-{stop}")
        with pytest.raises(RuntimeError):
            service.bootstrap_from_legacy_capture(
                request,
                _test_stop_after=None if stop == "READY" else stop,
                _test_lose_response_after_ready=stop == "READY",
            )
        recovered = service.bootstrap_from_legacy_capture(request)
        assert recovered.payload_sha256 == hashlib.sha256(facts["vector"]).hexdigest()
        assert _representation_counts(qualified.connection)[0:4] == (2, 2, 1, 1)
    finally:
        qualified.close()


def test_b3a_changed_capture_or_lane_same_key_conflicts(tmp_path: Path):
    qualified, facts = _fixture(tmp_path)
    facts["connection"] = qualified.connection
    try:
        r2 = _normalize(facts)
        service = NativeMigrationRuntimeRepresentationBootstrapService(qualified.connection)
        request = _bootstrap_request(facts, r2.revision_id, key="same-key")
        with pytest.raises(RuntimeError):
            service.bootstrap_from_legacy_capture(request, _test_stop_after="PENDING")
        lane = NativeRepresentationLane(**{**facts["lane"].__dict__, "model": "different"})
        with pytest.raises(SubstrateIdempotencyConflict):
            service.bootstrap_from_legacy_capture(_bootstrap_request(facts, r2.revision_id, key="same-key", lane=lane))
        with pytest.raises(SubstrateIdempotencyConflict):
            service.bootstrap_from_legacy_capture(_bootstrap_request(facts, facts["r1"], key="same-key"))
        capture = qualified.connection.execute(
            "SELECT representation_id,payload_bytes FROM representation_payloads WHERE representation_id=(SELECT representation_id FROM representations WHERE representation_class='LEGACY_EMBEDDING_CAPTURE')"
        ).fetchone()
        mutated = np.asarray((0.2, 0.4, 0.8), dtype=np.float32).tobytes()
        # Capture bytes are immutable evidence, so a changed-capture retry is
        # rejected even before the bootstrap idempotency path can be reached.
        with pytest.raises(Exception, match="immutable representation payload"):
            qualified.connection.execute(
                "UPDATE representation_payloads SET payload_bytes=? WHERE representation_id=?", (mutated, capture[0])
            )
        assert service.bootstrap_from_legacy_capture(request).payload_sha256 == hashlib.sha256(facts["vector"]).hexdigest()
    finally:
        qualified.close()


def test_b3a_refuses_unresolved_r1_and_no_vector_r2_without_effects(tmp_path: Path):
    from test_substrate_migration_runtime_readiness import _fixture as b1_fixture

    qualified, b1_request, plan = b1_fixture(tmp_path)
    try:
        connection = qualified.connection
        r1 = UUID(bytes=connection.execute(
            "SELECT current_revision_id FROM objects WHERE object_id=(SELECT object_id FROM legacy_object_aliases WHERE legacy_source_namespace_id=? AND alias_value='1')",
            (native_id_to_bytes(plan.legacy_source_namespace_id),),
        ).fetchone()[0])
        before = connection.execute("SELECT count(*) FROM representations WHERE representation_class='COMPAT_EMBEDDING'").fetchone()[0]
        with pytest.raises(MigrationRuntimeRepresentationBootstrapRefused):
            NativeMigrationRuntimeRepresentationBootstrapService(connection).bootstrap_from_legacy_capture(
                MigrationRuntimeRepresentationBootstrapRequest(
                    snapshot_root=tmp_path / "snapshot" / "legacy", manifest_path=tmp_path / "snapshot" / "snapshot-manifest.json",
                    legacy_snapshot_id=b1_request.legacy_snapshot_id, legacy_source_namespace_id=plan.legacy_source_namespace_id,
                    expected_native_core_id=b1_request.expected_native_core_id, eid=1,
                    expected_r1_revision_id=r1, expected_r2_revision_id=r1, target_lane=b1_request.target_lane,
                    idempotency_namespace_id=plan.idempotency_namespace_id, idempotency_key="unresolved",
                )
            )
        assert connection.execute("SELECT count(*) FROM representations WHERE representation_class='COMPAT_EMBEDDING'").fetchone()[0] == before
    finally:
        qualified.close()

    no_vector_root = tmp_path / "no-vector"
    no_vector_root.mkdir()
    qualified, facts = _fixture(no_vector_root, include_vector=False)
    facts["connection"] = qualified.connection
    try:
        r2 = _normalize(facts)
        with pytest.raises(MigrationRuntimeRepresentationBootstrapRefused, match="CAPTURE_SELECTION"):
            NativeMigrationRuntimeRepresentationBootstrapService(qualified.connection).bootstrap_from_legacy_capture(
                _bootstrap_request(facts, r2.revision_id)
            )
        assert qualified.connection.execute("SELECT count(*) FROM representations WHERE representation_class='COMPAT_EMBEDDING'").fetchone()[0] == 0
    finally:
        qualified.close()


def test_b3a_refuses_dimension_mismatch_core_mismatch_and_nonlegacy_deployment(tmp_path: Path):
    qualified, facts = _fixture(tmp_path, vector=np.asarray((2.0, 0.6, 0.0, 0.1), dtype=np.float32))
    facts["connection"] = qualified.connection
    try:
        r2 = _normalize(facts)
        service = NativeMigrationRuntimeRepresentationBootstrapService(qualified.connection)
        with pytest.raises(MigrationRuntimeRepresentationBootstrapRefused, match="REEMBED_REQUIRED"):
            service.bootstrap_from_legacy_capture(_bootstrap_request(facts, r2.revision_id))
        wrong_core = MigrationRuntimeRepresentationBootstrapRequest(
            **{**_bootstrap_request(facts, r2.revision_id).__dict__, "expected_native_core_id": _id()}
        )
        with pytest.raises(MigrationRuntimeRepresentationBootstrapRefused, match="NATIVE_CORE_ID_MISMATCH"):
            service.bootstrap_from_legacy_capture(wrong_core)
        qualified.connection.execute(
            "UPDATE deployment_metadata SET deployment_state='CUTOVER_PENDING',referenced_core_id=?",
            (facts["metadata"].core_id,),
        )
        with pytest.raises(MigrationRuntimeRepresentationBootstrapRefused, match="DEPLOYMENT_NOT_LEGACY_ACTIVE"):
            service.bootstrap_from_legacy_capture(_bootstrap_request(facts, r2.revision_id))
        assert qualified.connection.execute("SELECT count(*) FROM representations WHERE representation_class='COMPAT_EMBEDDING'").fetchone()[0] == 0
    finally:
        qualified.close()


@pytest.mark.parametrize("provider,model,dtype,code", [
    ("other", "synthetic", "float32", "REEMBED_REQUIRED"),
    ("synthetic", "other", "float32", "REEMBED_REQUIRED"),
    ("synthetic", "synthetic", "float64", "REEMBED_REQUIRED"),
])
def test_b3a_refuses_reembed_required_capture_without_conversion(
    tmp_path: Path, provider: str, model: str, dtype: str, code: str,
):
    vector = np.asarray((2.0, 0.6, 0.0), dtype=np.float64 if dtype == "float64" else np.float32)
    qualified, facts = _fixture(tmp_path, vector=vector, provider=provider, model=model, dtype=dtype)
    facts["connection"] = qualified.connection
    try:
        r2 = _normalize(facts)
        with pytest.raises(MigrationRuntimeRepresentationBootstrapRefused, match=code):
            NativeMigrationRuntimeRepresentationBootstrapService(qualified.connection).bootstrap_from_legacy_capture(
                _bootstrap_request(facts, r2.revision_id)
            )
        assert qualified.connection.execute("SELECT count(*) FROM representations WHERE representation_class='COMPAT_EMBEDDING'").fetchone()[0] == 0
    finally:
        qualified.close()


def test_b3a_refuses_competing_current_qualified_embedding(tmp_path: Path):
    qualified, facts = _fixture(tmp_path)
    facts["connection"] = qualified.connection
    try:
        r2 = _normalize(facts)
        payload = np.asarray((0.1, 0.2, 0.3), dtype=np.float32).tobytes()
        representations = NativeRepresentationService(qualified.connection)
        pending = representations.create_representation_pending(
            idempotency_namespace_id=facts["idempotency"], idempotency_key="competing-pending",
            request=RepresentationRequest(
                source_kind="OBJECT_REVISION", object_id=facts["object_id"], object_revision_id=r2.revision_id,
                relationship_id=None, relationship_revision_id=None, representation_class="COMPAT_EMBEDDING",
                generation=1, derivation_contract_version="compat-embedding-v1", encoding_id="RAW_VECTOR",
                dtype="float32", dimension=3, expected_payload_byte_length=len(payload),
            ),
        )
        representations.establish_representation_integrity_expectation(
            idempotency_namespace_id=facts["idempotency"], idempotency_key="competing-expectation",
            request=RepresentationIntegrityExpectationRequest(
                representation_id=pending.representation_id, algorithm_id=INTEGRITY_ALGORITHM_SHA256,
                expected_value=hashlib.sha256(payload).digest(), value_encoding=INTEGRITY_VALUE_ENCODING_RAW,
            ),
        )
        representations.publish_representation_ready(
            idempotency_namespace_id=facts["idempotency"], idempotency_key="competing-ready",
            request=RepresentationReadyRequest(
                representation_id=pending.representation_id, representation_class="COMPAT_EMBEDDING", generation=1,
                derivation_contract_version="compat-embedding-v1", encoding_id="RAW_VECTOR", payload_bytes=payload,
            ),
        )
        with pytest.raises(MigrationRuntimeRepresentationBootstrapRefused, match="COMPETING"):
            NativeMigrationRuntimeRepresentationBootstrapService(qualified.connection).bootstrap_from_legacy_capture(
                _bootstrap_request(facts, r2.revision_id)
            )
    finally:
        qualified.close()


def test_b3a_refuses_mutated_snapshot_before_representation_publication(tmp_path: Path):
    qualified, facts = _fixture(tmp_path)
    facts["connection"] = qualified.connection
    try:
        r2 = _normalize(facts)
        (facts["root"] / "nodes.jsonl").write_bytes(b"{}\n")
        with pytest.raises(Exception):
            NativeMigrationRuntimeRepresentationBootstrapService(qualified.connection).bootstrap_from_legacy_capture(
                _bootstrap_request(facts, r2.revision_id)
            )
        assert qualified.connection.execute("SELECT count(*) FROM representations WHERE representation_class='COMPAT_EMBEDDING'").fetchone()[0] == 0
    finally:
        qualified.close()
