"""Phase 7G5B1 read-only admission-to-runtime readiness qualification."""
from __future__ import annotations

import json
import hashlib
from pathlib import Path
from uuid import UUID

import numpy as np

from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.ids import generate_native_id, native_id_to_bytes
from torment_service.substrate.migration import (
    CoreRuntimeReadiness,
    LegacyVectorStrategy,
    MigrationRehearsalConfig,
    MigrationRuntimeReadinessRequest,
    MigrationRuntimeScopePlan,
    MotifRuntimeReadiness,
    NativeLegacyMigrationRehearsal,
    NativeMigrationRuntimeReadinessPreflight,
    ObjectRuntimeReadiness,
    create_snapshot_manifest,
)
from torment_service.substrate.runtime_binding import NativeRepresentationLane
from torment_service.substrate.objects import NativeObjectService, ObjectState
from torment_service.substrate.representations import (
    INTEGRITY_ALGORITHM_SHA256,
    INTEGRITY_VALUE_ENCODING_RAW,
    NativeRepresentationService,
    RepresentationIntegrityExpectationRequest,
    RepresentationReadyRequest,
    RepresentationRequest,
)
from torment_service.substrate.schema import create_schema, create_schema_v1


def _id():
    return generate_native_id()


def _json_line(value: dict[str, object]) -> bytes:
    return json.dumps(value, separators=(",", ":")).encode("utf-8") + b"\n"


def _fixture(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "b1-readiness.db")
    metadata = create_schema(qualified.connection)
    connection = qualified.connection
    object_namespace, relationship_namespace = _id(), _id()
    unknown_scope, target_scope, idempotency = _id(), _id(), _id()
    for value, key in ((object_namespace, "b1-objects"), (relationship_namespace, "b1-relationships")):
        connection.execute("INSERT INTO identity_namespaces VALUES (?,?,0)", (native_id_to_bytes(value), key))
    for value, key in ((unknown_scope, "b1-legacy-unknown"), (target_scope, "b1-target-private")):
        connection.execute("INSERT INTO semantic_scopes VALUES (?,?,0)", (native_id_to_bytes(value), key))
    connection.execute("INSERT INTO idempotency_namespaces VALUES (?,?)", (native_id_to_bytes(idempotency), "b1-idempotency"))

    root = tmp_path / "snapshot" / "legacy"
    root.mkdir(parents=True)
    nodes = [
        {"eid": 1, "text": "captured core one", "embedding_ref": {
            "map": "embeddings/shard.map.jsonl", "shard": "embeddings/shard.npy", "row": 0,
            "dimension": 3, "dtype": "float32",
        }},
        {"eid": 2, "text": "captured core two"},
    ]
    (root / "nodes.jsonl").write_bytes(b"".join(_json_line(item) for item in nodes))
    embeddings = root / "embeddings"
    embeddings.mkdir()
    np.save(embeddings / "shard.npy", np.array([[2.0, 0.6, 0.0]], dtype=np.float32))
    (embeddings / "manifest.json").write_bytes(_json_line({
        "encoding_id": "NUMPY_NPY", "dtype": "float32", "dimension": 3,
        "derivation_contract_version": "synthetic-captured-v1", "provider": "synthetic",
        "model": "synthetic", "shards": [{"path": "embeddings/shard.npy", "map": "embeddings/shard.map.jsonl"}],
    }))
    (embeddings / "shard.map.jsonl").write_bytes(_json_line({
        "eid": 1, "shard": "embeddings/shard.npy", "row": 0, "dimension": 3,
    }))
    motif = root / "workspaces" / "orchard" / "domains" / "reflection" / "motifs.json"
    motif.parent.mkdir(parents=True)
    motif.write_text(json.dumps({"motifs": {"motif-b1": {
        "motif_id": "motif-b1", "domain_id": "reflection", "label": "B1 motif",
        "centroid": [0.25, -0.5, 0.75], "strength": 0.7, "members": [1, 2],
        "contributing_agents": ["aria"], "stability_score": 0.8, "created_ts": 1,
        "last_active_ts": 2,
    }}}, sort_keys=True), encoding="utf-8")
    source_namespace = _id()
    manifest_path = root.parent / "snapshot-manifest.json"
    manifest = create_snapshot_manifest(
        snapshot_root=root,
        manifest_path=manifest_path,
        legacy_source_namespace_id=source_namespace,
        legacy_source_namespace_key="b1-source",
        capture_label="synthetic B1 read-only preflight fixture",
    )
    config = MigrationRehearsalConfig(
        native_core_id=_id(), idempotency_namespace_id=idempotency,
        object_identity_namespace_id=object_namespace,
        relationship_identity_namespace_id=relationship_namespace,
        unknown_semantic_scope_id=unknown_scope,
    )
    NativeLegacyMigrationRehearsal(connection).run(
        snapshot_root=root, manifest_path=manifest_path, config=config,
    )
    plan = MigrationRuntimeScopePlan(
        legacy_source_namespace_id=source_namespace,
        workspace_id="orchard", scope_kind="PRIVATE_AGENT", agent_id="aria",
        target_identity_namespace_id=object_namespace,
        target_semantic_scope_id=target_scope,
        motif_alias_namespace_id=source_namespace,
        motif_identity_namespace_id=object_namespace,
        membership_identity_namespace_id=relationship_namespace,
        idempotency_namespace_id=idempotency, motif_domain_id="reflection",
    )
    lane = NativeRepresentationLane(
        provider="synthetic", model="synthetic", dimension=3,
        representation_class="COMPAT_EMBEDDING", generation=1,
        derivation_contract_version="compat-embedding-v1", encoding_id="RAW_VECTOR", dtype="float32",
    )
    request = MigrationRuntimeReadinessRequest(
        legacy_snapshot_id=manifest.legacy_snapshot_id,
        expected_native_core_id=UUID(bytes=metadata.core_id),
        scope_plans=(plan,), target_lane=lane,
    )
    return qualified, request, plan


def _durable_counts(connection) -> tuple[int, ...]:
    return tuple(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in (
        "objects", "object_revisions", "relationships", "relationship_revisions", "representations",
        "representation_current_state", "representation_payloads", "integrity_expectations",
        "integrity_measurements", "reconciliation_cases", "semantic_transitions", "operations",
        "legacy_admission_records", "memory_runtime_enumeration_orders", "maintenance_events",
    ))


def _append_test_only_capture(connection, *, generation: int, dtype: str, payload: bytes, expected_length: int) -> None:
    """Create a schema-valid captured-evidence row for negative B1 classification."""
    source = connection.execute(
        """SELECT r.source_object_id,r.source_object_revision_id,r.source_object_revision_ordinal,
                   state_effect.transition_id
              FROM representations r
              JOIN representation_state_effects state_effect USING(representation_id)
             WHERE r.representation_class='LEGACY_EMBEDDING_CAPTURE'
             ORDER BY r.representation_id LIMIT 1"""
    ).fetchone()
    object_id, revision_id, ordinal, transition_id = source
    representation_id = native_id_to_bytes(_id())
    connection.execute(
        """INSERT INTO representations(
               representation_id,source_kind,source_object_id,source_object_revision_id,
               source_object_revision_ordinal,representation_class,generation,
               derivation_contract_version,encoding_id,dtype,dimension,
               expected_payload_byte_length,created_at_ns
           ) VALUES (?,'OBJECT_REVISION',?,?,?,?,?,?,?,?,?,?,?)""",
        (
            representation_id, object_id, revision_id, ordinal, "LEGACY_EMBEDDING_CAPTURE", generation,
            "synthetic-captured-v1", "NUMPY_NPY", dtype, 3, expected_length, 0,
        ),
    )
    connection.execute(
        "INSERT INTO representation_current_state VALUES (?,'UNKNOWN','RECONCILIATION_REQUIRED',NULL)",
        (representation_id,),
    )
    connection.execute(
        "INSERT INTO representation_payloads VALUES (?,?,?,0)",
        (representation_id, payload, len(payload)),
    )
    connection.execute(
        "INSERT INTO representation_state_effects VALUES (? ,?,'UNKNOWN','RECONCILIATION_REQUIRED',NULL)",
        (transition_id, representation_id),
    )


def test_7f_rehearsal_is_classified_without_creating_any_durable_effect(tmp_path: Path):
    qualified, request, _plan = _fixture(tmp_path)
    try:
        before = _durable_counts(qualified.connection)
        report = NativeMigrationRuntimeReadinessPreflight(qualified.connection).run(request)
        assert _durable_counts(qualified.connection) == before
        assert report.durable_effect_count == report.authority_expansion_count == 0
        assert report.schema_version == (1, 2)
        assert report.deploy_gate_ready is True
        assert report.legacy_source_namespace_id == request.scope_plans[0].legacy_source_namespace_id
        assert len(report.scope_plan_digest) == 64
        assert len(report.object_items) == 3
        assert {item.readiness for item in report.object_items} == {
            ObjectRuntimeReadiness.SEMANTIC_FACTS_UNRESOLVED,
            ObjectRuntimeReadiness.EVIDENCE_ONLY_NOT_RUNTIME_OBJECT,
        }
        capture = next(item for item in report.object_items if item.legacy_captures).legacy_captures[0]
        assert capture.strategy is LegacyVectorStrategy.BYTE_DERIVATION_POSSIBLE
        assert "FUTURE_BYTE_DERIVATION_REQUIRES_FROZEN_B2_RULE" in capture.reason_codes
        assert next(item for item in report.object_items if not item.legacy_captures).legacy_vector_strategy is LegacyVectorStrategy.NO_VECTOR_PRESENT
        assert report.motif_items[0].readiness is MotifRuntimeReadiness.DETERMINISTIC_NORMALIZATION_REQUIRED
        assert "MOTIF_OBJECT_KIND_NORMALIZATION_REQUIRED" in report.motif_items[0].reason_codes
        assert report.b2_recommendation == "B2_SCOPE_GOVERNANCE_PROVENANCE_LIFECYCLE_NORMALIZATION_FIRST"
        assert {item.side_store for item in report.side_stores} >= {
            "conflicts", "deep_memory", "proposals", "trajectory_evidence",
        }
    finally:
        qualified.close()


def test_scope_ambiguity_is_reported_not_resolved_by_the_preflight(tmp_path: Path):
    qualified, request, plan = _fixture(tmp_path)
    try:
        ambiguous = MigrationRuntimeScopePlan(
            legacy_source_namespace_id=plan.legacy_source_namespace_id,
            workspace_id=plan.workspace_id, scope_kind="PRIVATE_AGENT", agent_id="second-agent",
            target_identity_namespace_id=plan.target_identity_namespace_id,
            target_semantic_scope_id=plan.target_semantic_scope_id,
            motif_alias_namespace_id=plan.motif_alias_namespace_id,
            motif_identity_namespace_id=plan.motif_identity_namespace_id,
            membership_identity_namespace_id=plan.membership_identity_namespace_id,
            idempotency_namespace_id=plan.idempotency_namespace_id, motif_domain_id=plan.motif_domain_id,
        )
        report = NativeMigrationRuntimeReadinessPreflight(qualified.connection).run(
            MigrationRuntimeReadinessRequest(
                legacy_snapshot_id=request.legacy_snapshot_id,
                expected_native_core_id=request.expected_native_core_id,
                scope_plans=(plan, ambiguous), target_lane=request.target_lane,
            )
        )
        assert "RUNTIME_SCOPE_PLAN_AMBIGUOUS" in report.blocking_reasons
        core_items = [item for item in report.object_items if item.eid is not None]
        assert all(item.readiness is ObjectRuntimeReadiness.SEMANTIC_FACTS_UNRESOLVED for item in core_items)
        assert all("RUNTIME_SCOPE_PLAN_AMBIGUOUS" in item.reason_codes for item in core_items)
    finally:
        qualified.close()


def test_lane_or_core_mismatch_is_classified_without_a_runtime_workaround(tmp_path: Path):
    qualified, request, _plan = _fixture(tmp_path)
    try:
        reembed_lane = NativeRepresentationLane(
            provider="synthetic", model="different-model", dimension=4,
            representation_class="COMPAT_EMBEDDING", generation=1,
            derivation_contract_version="compat-embedding-v1", encoding_id="RAW_VECTOR", dtype="float32",
        )
        report = NativeMigrationRuntimeReadinessPreflight(qualified.connection).run(
            MigrationRuntimeReadinessRequest(
                legacy_snapshot_id=request.legacy_snapshot_id,
                expected_native_core_id=_id(), scope_plans=request.scope_plans, target_lane=reembed_lane,
            )
        )
        assert report.deploy_gate_ready is False
        assert "CORE_ID_MISMATCH" in report.blocking_reasons
        capture = next(item for item in report.object_items if item.legacy_captures).legacy_captures[0]
        assert capture.strategy is LegacyVectorStrategy.REEMBED_REQUIRED
        assert "LEGACY_VECTOR_DIMENSION_DOES_NOT_MATCH_TARGET_LANE" in capture.reason_codes
        assert "LEGACY_VECTOR_PROVIDER_MODEL_NOT_PROVEN_FOR_TARGET_LANE" in capture.reason_codes
        assert report.reembed_required_count == 1
        assert report.durable_effect_count == 0
    finally:
        qualified.close()


def test_wrong_dtype_and_corrupt_capture_are_classified_without_promotion(tmp_path: Path):
    qualified, request, _plan = _fixture(tmp_path)
    try:
        connection = qualified.connection
        _append_test_only_capture(
            connection, generation=2, dtype="float64",
            payload=np.array([1.0, 2.0, 3.0], dtype=np.float64).tobytes(), expected_length=24,
        )
        _append_test_only_capture(
            connection, generation=3, dtype="float32", payload=b"too-short", expected_length=12,
        )
        before = _durable_counts(connection)
        report = NativeMigrationRuntimeReadinessPreflight(connection).run(request)
        assert _durable_counts(connection) == before
        vectorized = next(item for item in report.object_items if item.legacy_captures)
        assert vectorized.legacy_vector_strategy is LegacyVectorStrategy.UNUSABLE_VECTOR_EVIDENCE
        assert {capture.strategy for capture in vectorized.legacy_captures} >= {
            LegacyVectorStrategy.BYTE_DERIVATION_POSSIBLE,
            LegacyVectorStrategy.REEMBED_REQUIRED,
            LegacyVectorStrategy.UNUSABLE_VECTOR_EVIDENCE,
        }
        assert len(report.representation_items) == 3
        assert report.durable_effect_count == 0
    finally:
        qualified.close()


def test_cutover_posture_is_refused_without_mutating_the_snapshot(tmp_path: Path):
    qualified, request, _plan = _fixture(tmp_path)
    try:
        connection = qualified.connection
        connection.execute(
            "UPDATE deployment_metadata SET deployment_state='CUTOVER_PENDING', referenced_core_id=?",
            (native_id_to_bytes(request.expected_native_core_id),),
        )
        before = _durable_counts(connection)
        report = NativeMigrationRuntimeReadinessPreflight(connection).run(request)
        assert _durable_counts(connection) == before
        assert report.deploy_gate_ready is False
        assert CoreRuntimeReadiness.DEPLOYMENT_NOT_LEGACY_ACTIVE in report.core_readiness
        assert CoreRuntimeReadiness.DEPLOYMENT_REFERENCES_CORE in report.core_readiness
        assert report.durable_effect_count == 0
    finally:
        qualified.close()


def test_older_schema_is_reported_as_a_gate_failure_without_an_upgrade(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "b1-older-schema.db")
    try:
        metadata = create_schema_v1(qualified.connection)
        lane = NativeRepresentationLane(
            provider="synthetic", model="synthetic", dimension=3,
            representation_class="COMPAT_EMBEDDING", generation=1,
            derivation_contract_version="compat-embedding-v1", encoding_id="RAW_VECTOR", dtype="float32",
        )
        report = NativeMigrationRuntimeReadinessPreflight(qualified.connection).run(
            MigrationRuntimeReadinessRequest(
                legacy_snapshot_id=_id(), expected_native_core_id=UUID(bytes=metadata.core_id),
                scope_plans=(), target_lane=lane,
            )
        )
        assert report.schema_version == (1, 0)
        assert report.deploy_gate_ready is False
        assert CoreRuntimeReadiness.SCHEMA_VERSION_NOT_CURRENT in report.core_readiness
        assert report.durable_effect_count == 0
    finally:
        qualified.close()


def test_explicit_current_r2_and_ready_representation_are_recognized_as_is(tmp_path: Path):
    qualified, request, plan = _fixture(tmp_path)
    try:
        connection = qualified.connection
        object_blob, revision_blob = connection.execute(
            """SELECT o.object_id,o.current_revision_id FROM objects o
                 JOIN representations r ON r.source_object_id=o.object_id
                WHERE r.representation_class='LEGACY_EMBEDDING_CAPTURE'
                ORDER BY o.object_id LIMIT 1"""
        ).fetchone()
        object_id, legacy_revision_id = UUID(bytes=object_blob), UUID(bytes=revision_blob)
        provenance_id = _id()
        connection.execute(
            """INSERT INTO provenance_records(
                   provenance_id,origin_kind,source_channel,source_role,derivation_status,
                   uncertainty_state,source_time_ns,capture_time_ns,memory_role,descriptive_notes
               ) VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                native_id_to_bytes(provenance_id), "LEGACY_NORMALIZED", "synthetic", "memory",
                "DETERMINISTIC", "KNOWN", None, None, "memory", "test-only explicit provenance",
            ),
        )
        successor = NativeObjectService(connection).transition_object(
            idempotency_namespace_id=plan.idempotency_namespace_id,
            idempotency_key="b1-positive-r2",
            object_id=object_id,
            expected_revision_id=legacy_revision_id,
            state=ObjectState(
                identity_namespace_id=plan.target_identity_namespace_id,
                semantic_scope_id=plan.target_semantic_scope_id,
                object_kind="LEGACY_CORE_NODE", existence_state="EXISTS",
                lifecycle_state="ACTIVE", lifecycle_authoritative=True,
                governance_state="EXPLICIT", payload="normalized fixture memory", payload_format="TEXT",
                provenance_id=provenance_id,
            ),
        )
        connection.execute(
            """INSERT INTO object_revision_governance VALUES (?,?,?,?,?,?,?,?)""",
            (native_id_to_bytes(object_id), native_id_to_bytes(successor.revision_id), 2, 0, 0, 0, 0, 0),
        )
        payload = np.array([0.25, -0.5, 0.75], dtype=np.float32).tobytes()
        representations = NativeRepresentationService(connection)
        pending = representations.create_representation_pending(
            idempotency_namespace_id=plan.idempotency_namespace_id,
            idempotency_key="b1-positive-pending",
            request=RepresentationRequest(
                source_kind="OBJECT_REVISION", object_id=object_id,
                object_revision_id=successor.revision_id, relationship_id=None,
                relationship_revision_id=None, representation_class="COMPAT_EMBEDDING",
                generation=1, derivation_contract_version="compat-embedding-v1", encoding_id="RAW_VECTOR",
                dtype="float32", dimension=3, expected_payload_byte_length=len(payload),
            ),
        )
        representations.establish_representation_integrity_expectation(
            idempotency_namespace_id=plan.idempotency_namespace_id,
            idempotency_key="b1-positive-expectation",
            request=RepresentationIntegrityExpectationRequest(
                representation_id=pending.representation_id, algorithm_id=INTEGRITY_ALGORITHM_SHA256,
                expected_value=hashlib.sha256(payload).digest(), value_encoding=INTEGRITY_VALUE_ENCODING_RAW,
            ),
        )
        representations.publish_representation_ready(
            idempotency_namespace_id=plan.idempotency_namespace_id,
            idempotency_key="b1-positive-ready",
            request=RepresentationReadyRequest(
                representation_id=pending.representation_id, representation_class="COMPAT_EMBEDDING",
                generation=1, derivation_contract_version="compat-embedding-v1", encoding_id="RAW_VECTOR",
                payload_bytes=payload,
            ),
        )
        report = NativeMigrationRuntimeReadinessPreflight(connection).run(request)
        ready = next(item for item in report.object_items if item.object_id == object_id)
        assert ready.readiness is ObjectRuntimeReadiness.RUNTIME_READY_AS_IS
        assert ready.qualified_representation_id == pending.representation_id
        assert ready.legacy_vector_strategy is LegacyVectorStrategy.BYTE_DERIVATION_POSSIBLE
    finally:
        qualified.close()
