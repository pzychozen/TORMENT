"""B4A lane-preserving 7F motif projection qualification."""
from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from uuid import UUID

import numpy as np
import pytest

from torment_service.provenance_v1 import ProvenanceV1
from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.errors import SubstrateIdempotencyConflict
from torment_service.substrate.ids import generate_native_id, native_id_to_bytes
from torment_service.substrate.migration import (
    MigrationRehearsalConfig, MigrationRuntimeMotifProjectionRefused,
    MigrationRuntimeMotifProjectionRequest, MigrationRuntimeNormalizationRequest,
    MigrationRuntimeReadinessRequest, MigrationRuntimeRepresentationBootstrapRequest,
    MigrationRuntimeScopePlan, MotifRuntimeReadiness, NativeLegacyMigrationRehearsal,
    NativeMigrationRuntimeMotifProjectionService, NativeMigrationRuntimeNormalizationService,
    NativeMigrationRuntimeReadinessPreflight, NativeMigrationRuntimeRepresentationBootstrapService,
    create_snapshot_manifest,
)
from torment_service.substrate.motif_runtime_reader import NativeMotifRuntimeReader
from torment_service.substrate.motifs import NativeMotifService
from torment_service.substrate.objects import NativeObjectService, ObjectState
from torment_service.substrate.runtime_binding import NativeRepresentationLane
from torment_service.substrate.schema import create_schema


def _id(): return generate_native_id()


def _line(value: dict[str, object]) -> bytes:
    return json.dumps(value, separators=(",", ":")).encode() + b"\n"


def _payload() -> dict[str, object]:
    return {
        "summary": "B4A qualified legacy memory", "type": "memory", "memory_class": "core",
        "strength": .7, "confidence": .9, "seed_pos0": [1, 2, 3], "seed_v0": [.1, .2, .3],
        "governance": {"protected": False, "non_shareable": False, "collective_export_blocked": False, "collective_reingest_blocked": False, "decay_accelerated": False},
        "provenance": ProvenanceV1(source_type="role_output", source_role="tester", write_path="cognition_writeback", parent_eids=[], created_at_step=1, created_at_ts="2024-01-01T00:00:00Z").to_dict(),
        "lifecycle_status": {"state": "active", "is_authoritative_on_row": True, "requires_join": None, "set_by": {"actor": "user", "via": "api", "at": 1}, "history_ref": None},
    }


def _context(tmp_path: Path, *, workspace_lane=("synthetic", "synthetic", 3), include_workspace_meta=True, malformed_workspace_meta=False):
    qualified = open_temporary_test_connection(tmp_path / "b4a.db")
    connection = qualified.connection; metadata = create_schema(connection)
    object_ns, relationship_ns, motif_ns, target_alias_ns = _id(), _id(), _id(), _id()
    unknown_scope, target_scope, idempotency = _id(), _id(), _id()
    for value, key in ((object_ns, "b4a-objects"), (relationship_ns, "b4a-relationships"), (motif_ns, "b4a-motifs")):
        connection.execute("INSERT INTO identity_namespaces VALUES (?,?,0)", (native_id_to_bytes(value), key))
    for value, key in ((unknown_scope, "b4a-unknown"), (target_scope, "b4a-target")):
        connection.execute("INSERT INTO semantic_scopes VALUES (?,?,0)", (native_id_to_bytes(value), key))
    connection.execute("INSERT INTO idempotency_namespaces VALUES (?,?)", (native_id_to_bytes(idempotency), "b4a-idempotency"))
    connection.execute("INSERT INTO legacy_source_namespaces VALUES (?,?,0)", (native_id_to_bytes(target_alias_ns), "b4a-runtime-aliases"))
    root = tmp_path / "frozen" / "legacy"; root.mkdir(parents=True)
    vectors = np.asarray(((2.0, .6, 0.0),), dtype=np.float32)
    (root / "nodes.jsonl").write_bytes(_line({"eid": 7, "born_step": 1, "channel": 1, "payload": _payload(), "embedding_ref": {"map": "embeddings/shard.map.jsonl", "shard": "embeddings/shard.npy", "row": 0, "dimension": 3, "dtype": "float32"}}))
    embeddings = root / "embeddings"; embeddings.mkdir(); np.save(embeddings / "shard.npy", vectors)
    (embeddings / "manifest.json").write_bytes(_line({"encoding_id": "NUMPY_NPY", "dtype": "float32", "dimension": 3, "derivation_contract_version": "synthetic-captured-v1", "provider": "synthetic", "model": "synthetic", "shards": [{"path": "embeddings/shard.npy", "map": "embeddings/shard.map.jsonl"}]}))
    (embeddings / "shard.map.jsonl").write_bytes(_line({"eid": 7, "shard": "embeddings/shard.npy", "row": 0, "dimension": 3}))
    workspace = root / "workspaces" / "orchard"; workspace.mkdir(parents=True)
    if include_workspace_meta:
        (workspace / "workspace_meta.json").write_text(
            "{" if malformed_workspace_meta else json.dumps({"embed_provider": workspace_lane[0], "embed_model": workspace_lane[1], "embed_dim": workspace_lane[2]}), encoding="utf-8")
    motifs = workspace / "domains" / "reflection"; motifs.mkdir(parents=True)
    (motifs / "motifs.json").write_text(json.dumps({"motifs": {"motif-b4a": {"motif_id": "motif-b4a", "domain_id": "reflection", "label": "B4A", "centroid": [0.25, -0.5, .75], "strength": .7, "stability_score": .8, "contributing_agents": ["aria"], "created_ts": 1, "last_active_ts": 2, "members": [7]}}}), encoding="utf-8")
    source_ns = _id(); manifest_path = root.parent / "manifest.json"
    manifest = create_snapshot_manifest(snapshot_root=root, manifest_path=manifest_path, legacy_source_namespace_id=source_ns, legacy_source_namespace_key="b4a-source", capture_label="B4A fixture")
    NativeLegacyMigrationRehearsal(connection).run(snapshot_root=root, manifest_path=manifest_path, config=MigrationRehearsalConfig(native_core_id=_id(), idempotency_namespace_id=idempotency, object_identity_namespace_id=object_ns, relationship_identity_namespace_id=relationship_ns, unknown_semantic_scope_id=unknown_scope))
    plan = MigrationRuntimeScopePlan(legacy_source_namespace_id=source_ns, workspace_id="orchard", scope_kind="PRIVATE_AGENT", agent_id="aria", target_identity_namespace_id=object_ns, target_semantic_scope_id=target_scope, motif_alias_namespace_id=target_alias_ns, motif_identity_namespace_id=motif_ns, membership_identity_namespace_id=relationship_ns, idempotency_namespace_id=idempotency, motif_domain_id="reflection")
    lane = NativeRepresentationLane("synthetic", "synthetic", 3, "COMPAT_EMBEDDING", 1, "compat-embedding-v1", "RAW_VECTOR", "float32")
    source_object, r1 = connection.execute("SELECT object_id,current_revision_id FROM objects WHERE object_id=(SELECT object_id FROM legacy_object_aliases WHERE legacy_source_namespace_id=? AND alias_kind='EID' AND alias_value='7')", (native_id_to_bytes(source_ns),)).fetchone()
    normalized = NativeMigrationRuntimeNormalizationService(connection).normalize_legacy_core_memory(MigrationRuntimeNormalizationRequest(snapshot_root=root, manifest_path=manifest_path, legacy_snapshot_id=manifest.legacy_snapshot_id, legacy_source_namespace_id=source_ns, expected_native_core_id=UUID(bytes=metadata.core_id), eid=7, expected_revision_id=UUID(bytes=r1), scope_plans=(plan,), idempotency_namespace_id=idempotency, idempotency_key="b4a-b2"))
    NativeMigrationRuntimeRepresentationBootstrapService(connection).bootstrap_from_legacy_capture(MigrationRuntimeRepresentationBootstrapRequest(snapshot_root=root, manifest_path=manifest_path, legacy_snapshot_id=manifest.legacy_snapshot_id, legacy_source_namespace_id=source_ns, expected_native_core_id=UUID(bytes=metadata.core_id), eid=7, expected_r1_revision_id=UUID(bytes=r1), expected_r2_revision_id=normalized.revision_id, target_lane=lane, idempotency_namespace_id=idempotency, idempotency_key="b4a-b3"))
    motif_object, motif_r1 = connection.execute("SELECT object_id,current_revision_id FROM objects WHERE object_id=(SELECT object_id FROM legacy_object_aliases WHERE legacy_source_namespace_id=? AND alias_kind='MOTIF_ID' AND alias_value='motif-b4a')", (native_id_to_bytes(source_ns),)).fetchone()
    request = MigrationRuntimeMotifProjectionRequest(root, manifest_path, manifest.legacy_snapshot_id, source_ns, UUID(bytes=metadata.core_id), "motif-b4a", UUID(bytes=motif_object), UUID(bytes=motif_r1), (plan,), lane, idempotency, "b4a-project")
    return qualified, {"connection": connection, "root": root, "manifest": manifest, "plan": plan, "lane": lane, "request": request, "source": UUID(bytes=motif_object), "source_r1": UUID(bytes=motif_r1), "normalized": normalized}


def test_b4a_projects_exact_state_order_and_b1_progression(tmp_path: Path):
    qualified, facts = _context(tmp_path)
    try:
        connection = facts["connection"]; request = facts["request"]
        before = NativeMigrationRuntimeReadinessPreflight(connection).run(MigrationRuntimeReadinessRequest(facts["manifest"].legacy_snapshot_id, request.expected_native_core_id, (facts["plan"],), facts["lane"]))
        assert before.motif_items[0].readiness is MotifRuntimeReadiness.DETERMINISTIC_NORMALIZATION_REQUIRED
        source_before = connection.execute("SELECT current_revision_id,current_revision_ordinal FROM objects WHERE object_id=?", (native_id_to_bytes(facts["source"]),)).fetchone()
        source_aliases_before = connection.execute("SELECT legacy_source_namespace_id,alias_kind,alias_value,object_id FROM legacy_object_aliases WHERE object_id=?", (native_id_to_bytes(facts["source"]),)).fetchall()
        source_members_before = connection.execute("SELECT relationship_id,current_revision_id,current_revision_ordinal FROM relationships WHERE creating_transition_id=(SELECT creating_transition_id FROM objects WHERE object_id=?) ORDER BY relationship_id", (native_id_to_bytes(facts["source"]),)).fetchall()
        representations_before = connection.execute("SELECT count(*) FROM representations").fetchone()[0]
        result = NativeMigrationRuntimeMotifProjectionService(connection).project_lane_preserving_legacy_motif(request)
        assert NativeMigrationRuntimeMotifProjectionService(connection).project_lane_preserving_legacy_motif(request) == result
        reader = NativeMotifRuntimeReader(connection)
        motifs = reader.list_runtime_motifs(motif_alias_namespace_id=facts["plan"].motif_alias_namespace_id, domain_id="reflection", semantic_scope_id=facts["plan"].target_semantic_scope_id)
        assert len(motifs) == 1 and motifs[0].motif_object_id == result.motif_object_id
        assert motifs[0].read_model.centroid == (.25, -.5, .75)
        assert [member.member_object_id for member in reader.list_ordered_current_motif_members(result.motif_object_id)] == [facts["normalized"].object_id]
        assert reader.motif_radius(result.motif_object_id, expected_dimension=3) >= 0
        assert reader.domain_centroid(motif_alias_namespace_id=facts["plan"].motif_alias_namespace_id, domain_id="reflection", dimension=3, semantic_scope_id=facts["plan"].target_semantic_scope_id).shape == (3,)
        assert reader.project_coherence_field_rows(motif_alias_namespace_id=facts["plan"].motif_alias_namespace_id, domain_id="reflection", expected_dimension=3, semantic_scope_id=facts["plan"].target_semantic_scope_id)[0]["members"] == 1
        assert connection.execute("SELECT current_revision_id,current_revision_ordinal FROM objects WHERE object_id=?", (native_id_to_bytes(facts["source"]),)).fetchone() == source_before
        assert connection.execute("SELECT legacy_source_namespace_id,alias_kind,alias_value,object_id FROM legacy_object_aliases WHERE object_id=?", (native_id_to_bytes(facts["source"]),)).fetchall() == source_aliases_before
        assert connection.execute("SELECT relationship_id,current_revision_id,current_revision_ordinal FROM relationships WHERE creating_transition_id=(SELECT creating_transition_id FROM objects WHERE object_id=?) ORDER BY relationship_id", (native_id_to_bytes(facts["source"]),)).fetchall() == source_members_before
        assert connection.execute("SELECT count(*) FROM representations").fetchone()[0] == representations_before
        after = NativeMigrationRuntimeReadinessPreflight(connection).run(MigrationRuntimeReadinessRequest(facts["manifest"].legacy_snapshot_id, request.expected_native_core_id, (facts["plan"],), facts["lane"]))
        assert after.motif_items[0].readiness is MotifRuntimeReadiness.RUNTIME_READY_AS_IS
    finally: qualified.close()


@pytest.mark.parametrize("lane", [("wrong", "synthetic", 3), ("synthetic", "wrong", 3), ("synthetic", "synthetic", 4)])
def test_b4a_refuses_workspace_lane_mismatch_without_projection(tmp_path: Path, lane):
    qualified, facts = _context(tmp_path, workspace_lane=lane)
    try:
        with pytest.raises(MigrationRuntimeMotifProjectionRefused, match="B4A_MOTIF_GEOMETRY_LANE_UNQUALIFIED"):
            NativeMigrationRuntimeMotifProjectionService(facts["connection"]).project_lane_preserving_legacy_motif(facts["request"])
        assert facts["connection"].execute("SELECT count(*) FROM objects WHERE object_kind='DERIVED_MOTIF'").fetchone()[0] == 0
    finally: qualified.close()


@pytest.mark.parametrize("kwargs", ({"include_workspace_meta": False}, {"malformed_workspace_meta": True}))
def test_b4a_refuses_missing_or_malformed_workspace_lane_witness(tmp_path: Path, kwargs):
    qualified, facts = _context(tmp_path, **kwargs)
    try:
        with pytest.raises(MigrationRuntimeMotifProjectionRefused, match="B4A_MOTIF_GEOMETRY_LANE_UNQUALIFIED"):
            NativeMigrationRuntimeMotifProjectionService(facts["connection"]).project_lane_preserving_legacy_motif(facts["request"])
    finally: qualified.close()


def test_b4a_refuses_source_alias_namespace_reuse_and_target_alias_collision(tmp_path: Path):
    qualified, facts = _context(tmp_path)
    try:
        request = facts["request"]
        shared_plan = replace(facts["plan"], motif_alias_namespace_id=request.legacy_source_namespace_id)
        shared = replace(request, scope_plans=(shared_plan,))
        service = NativeMigrationRuntimeMotifProjectionService(facts["connection"])
        with pytest.raises(MigrationRuntimeMotifProjectionRefused, match="B4A_ALIAS_SEPARATION_BLOCKED"):
            service.project_lane_preserving_legacy_motif(shared)
        facts["connection"].execute("INSERT INTO legacy_object_aliases VALUES (?,?,?,?)", (native_id_to_bytes(facts["plan"].motif_alias_namespace_id), "MOTIF_ID", "motif-b4a", native_id_to_bytes(facts["source"])))
        with pytest.raises(MigrationRuntimeMotifProjectionRefused, match="B4A_TARGET_MOTIF_ALIAS_COLLISION"):
            service.project_lane_preserving_legacy_motif(request)
    finally: qualified.close()


def test_b4a_response_loss_recovers_one_atomic_projection_and_changed_key_conflicts(tmp_path: Path):
    qualified, facts = _context(tmp_path)
    try:
        service = NativeMigrationRuntimeMotifProjectionService(facts["connection"])
        with pytest.raises(RuntimeError, match="response loss"):
            service.project_lane_preserving_legacy_motif(facts["request"], _test_lose_response_after_commit=True)
        recovered = service.project_lane_preserving_legacy_motif(facts["request"])
        assert facts["connection"].execute("SELECT count(*) FROM objects WHERE object_kind='DERIVED_MOTIF'").fetchone()[0] == 1
        changed = MigrationRuntimeMotifProjectionRequest(**{**facts["request"].__dict__, "runtime_motif_id": "changed"})
        with pytest.raises(SubstrateIdempotencyConflict): service.project_lane_preserving_legacy_motif(changed)
        assert recovered.membership_ids
    finally: qualified.close()


def test_b4a_baseline_order_precedes_an_ordinary_native_member_append(tmp_path: Path):
    qualified, facts = _context(tmp_path)
    try:
        connection = facts["connection"]; result = NativeMigrationRuntimeMotifProjectionService(connection).project_lane_preserving_legacy_motif(facts["request"])
        appended = NativeObjectService(connection).create_object(
            idempotency_namespace_id=facts["request"].idempotency_namespace_id, idempotency_key="b4a-extra-memory",
            state=ObjectState(facts["plan"].target_identity_namespace_id, facts["plan"].target_semantic_scope_id,
                              "LEGACY_CORE_NODE", "EXISTS", "EXPLICIT", True, "DERIVED", "NOT_APPLICABLE",
                              {"summary": "ordinary append"}, "JSON"),
        )
        motifs = NativeMotifService(connection); current = motifs.get_current_motif(result.motif_object_id)
        motifs.add_motif_member(
            idempotency_namespace_id=facts["request"].idempotency_namespace_id, idempotency_key="b4a-extra-member",
            motif_alias_namespace_id=facts["plan"].motif_alias_namespace_id,
            membership_identity_namespace_id=facts["plan"].membership_identity_namespace_id,
            motif_object_id=result.motif_object_id, expected_motif_revision_id=current.motif_revision_id,
            state=current.state, member_object_id=appended.object_id,
        )
        ordered = NativeMotifRuntimeReader(connection).list_ordered_current_motif_members(result.motif_object_id)
        assert [member.member_object_id for member in ordered] == [facts["normalized"].object_id, appended.object_id]
    finally: qualified.close()
