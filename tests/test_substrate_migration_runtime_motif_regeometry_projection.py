"""B4B cross-lane motif re-geometry projection qualification."""
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
    MigrationRehearsalConfig, MigrationRuntimeMotifRegeometryProjectionRefused,
    MigrationRuntimeMotifRegeometryProjectionRequest, MigrationRuntimeNormalizationRequest,
    MigrationRuntimeReadinessRequest, MigrationRuntimeReembeddingBootstrapRequest,
    MigrationRuntimeRepresentationBootstrapRequest, MigrationRuntimeScopePlan, MotifRuntimeReadiness,
    NativeLegacyMigrationRehearsal, NativeMigrationRuntimeMotifRegeometryProjectionService,
    NativeMigrationRuntimeNormalizationService, NativeMigrationRuntimeReadinessPreflight,
    NativeMigrationRuntimeReembeddingBootstrapService, NativeMigrationRuntimeRepresentationBootstrapService,
    create_snapshot_manifest,
)
from torment_service.substrate.motif_runtime_reader import NativeMotifRuntimeReader
from torment_service.substrate.motifs import NativeMotifService
from torment_service.substrate.objects import NativeObjectService, ObjectState
from torment_service.substrate.runtime_binding import NativeRepresentationLane
from torment_service.substrate.schema import create_schema


def _id(): return generate_native_id()
def _line(value): return json.dumps(value, separators=(",", ":")).encode() + b"\n"


def _payload(eid: int):
    return {"summary": f"cross lane member {eid}", "type": "memory", "memory_class": "core", "strength": .7, "confidence": .9,
            "seed_pos0": [1, 2, 3], "seed_v0": [.1, .2, .3],
            "governance": {"protected": False, "non_shareable": False, "collective_export_blocked": False, "collective_reingest_blocked": False, "decay_accelerated": False},
            "provenance": ProvenanceV1(source_type="role_output", source_role="tester", write_path="cognition_writeback", parent_eids=[], created_at_step=eid, created_at_ts="2024-01-01T00:00:00Z").to_dict(),
            "lifecycle_status": {"state": "active", "is_authoritative_on_row": True, "requires_join": None, "set_by": {"actor": "user", "via": "api", "at": eid}, "history_ref": None}}


class _Embedder:
    provider = "new-provider"; model = "new-model"; dim = 3
    def __init__(self, vector): self.vector = np.asarray(vector, dtype=np.float32); self.calls = []
    def embed(self, text): self.calls.append(text); return self.vector


def _context(tmp_path: Path, *, source_lane=("old-provider", "old-model", 2), include_meta=True, malformed_meta=False, bootstrap_all=True):
    qualified = open_temporary_test_connection(tmp_path / "b4b.db"); connection = qualified.connection; metadata = create_schema(connection)
    object_ns, relationship_ns, motif_ns, target_alias_ns = _id(), _id(), _id(), _id()
    unknown_scope, target_scope, idempotency = _id(), _id(), _id()
    for value, key in ((object_ns, "b4b-memory"), (relationship_ns, "b4b-memberships"), (motif_ns, "b4b-motifs")):
        connection.execute("INSERT INTO identity_namespaces VALUES (?,?,0)", (native_id_to_bytes(value), key))
    for value, key in ((unknown_scope, "b4b-unknown"), (target_scope, "b4b-target")):
        connection.execute("INSERT INTO semantic_scopes VALUES (?,?,0)", (native_id_to_bytes(value), key))
    connection.execute("INSERT INTO idempotency_namespaces VALUES (?,?)", (native_id_to_bytes(idempotency), "b4b-idempotency"))
    connection.execute("INSERT INTO legacy_source_namespaces VALUES (?,?,0)", (native_id_to_bytes(target_alias_ns), "b4b-target-aliases"))
    root = tmp_path / "frozen" / "legacy"; root.mkdir(parents=True)
    nodes = []
    for eid in (7, 8, 9):
        node = {"eid": eid, "born_step": eid, "channel": 1, "payload": _payload(eid)}
        if eid == 7:
            node["embedding_ref"] = {"map": "embeddings/shard.map.jsonl", "shard": "embeddings/shard.npy", "row": 0, "dimension": 3, "dtype": "float32"}
        nodes.append(node)
    (root / "nodes.jsonl").write_bytes(b"".join(_line(node) for node in nodes))
    embeddings = root / "embeddings"; embeddings.mkdir(); np.save(embeddings / "shard.npy", np.asarray(((2.0, .6, 0.0),), dtype=np.float32))
    (embeddings / "manifest.json").write_bytes(_line({"encoding_id": "NUMPY_NPY", "dtype": "float32", "dimension": 3, "derivation_contract_version": "synthetic-captured-v1", "provider": "new-provider", "model": "new-model", "shards": [{"path": "embeddings/shard.npy", "map": "embeddings/shard.map.jsonl"}]}))
    (embeddings / "shard.map.jsonl").write_bytes(_line({"eid": 7, "shard": "embeddings/shard.npy", "row": 0, "dimension": 3}))
    workspace = root / "workspaces" / "orchard"; workspace.mkdir(parents=True)
    if include_meta:
        (workspace / "workspace_meta.json").write_text("{" if malformed_meta else json.dumps({"embed_provider": source_lane[0], "embed_model": source_lane[1], "embed_dim": source_lane[2]}), encoding="utf-8")
    motifs = workspace / "domains" / "reflection"; motifs.mkdir(parents=True)
    raw_motif = {"motif_id": "motif-b4b", "domain_id": "reflection", "label": "cross lane", "centroid": [.25, -.5], "strength": .73, "stability_score": .88, "contributing_agents": ["aria"], "created_ts": 4, "last_active_ts": 9, "members": [7, 8, 9]}
    (motifs / "motifs.json").write_text(json.dumps({"motifs": {"motif-b4b": raw_motif}}), encoding="utf-8")
    source_ns = _id(); manifest_path = root.parent / "manifest.json"; manifest = create_snapshot_manifest(snapshot_root=root, manifest_path=manifest_path, legacy_source_namespace_id=source_ns, legacy_source_namespace_key="b4b-source", capture_label="B4B cross-lane fixture")
    NativeLegacyMigrationRehearsal(connection).run(snapshot_root=root, manifest_path=manifest_path, config=MigrationRehearsalConfig(native_core_id=_id(), idempotency_namespace_id=idempotency, object_identity_namespace_id=object_ns, relationship_identity_namespace_id=relationship_ns, unknown_semantic_scope_id=unknown_scope))
    plan = MigrationRuntimeScopePlan(legacy_source_namespace_id=source_ns, workspace_id="orchard", scope_kind="PRIVATE_AGENT", agent_id="aria", target_identity_namespace_id=object_ns, target_semantic_scope_id=target_scope, motif_alias_namespace_id=target_alias_ns, motif_identity_namespace_id=motif_ns, membership_identity_namespace_id=relationship_ns, idempotency_namespace_id=idempotency, motif_domain_id="reflection")
    lane = NativeRepresentationLane("new-provider", "new-model", 3, "COMPAT_EMBEDDING", 1, "compat-embedding-v1", "RAW_VECTOR", "float32")
    r1s = {}
    r2s = {}
    for eid in (7, 8, 9):
        obj, r1 = connection.execute("SELECT object_id,current_revision_id FROM objects WHERE object_id=(SELECT object_id FROM legacy_object_aliases WHERE legacy_source_namespace_id=? AND alias_kind='EID' AND alias_value=?)", (native_id_to_bytes(source_ns), str(eid))).fetchone()
        r1s[eid] = (UUID(bytes=obj), UUID(bytes=r1))
        r2s[eid] = NativeMigrationRuntimeNormalizationService(connection).normalize_legacy_core_memory(MigrationRuntimeNormalizationRequest(root, manifest_path, manifest.legacy_snapshot_id, source_ns, UUID(bytes=metadata.core_id), eid, UUID(bytes=r1), (plan,), idempotency, f"b4b-b2-{eid}")).revision_id
    NativeMigrationRuntimeRepresentationBootstrapService(connection).bootstrap_from_legacy_capture(MigrationRuntimeRepresentationBootstrapRequest(root, manifest_path, manifest.legacy_snapshot_id, source_ns, UUID(bytes=metadata.core_id), 7, r1s[7][1], r2s[7], lane, idempotency, "b4b-b3a"))
    embedders = {}
    for eid, vector in ((8, (.1, 1.0, 0.0)), (9, (0.0, 0.0, 1.0))):
        if not bootstrap_all and eid == 9:
            continue
        embedder = _Embedder(vector); embedders[eid] = embedder
        NativeMigrationRuntimeReembeddingBootstrapService(connection).bootstrap_from_qualified_text(MigrationRuntimeReembeddingBootstrapRequest(root, manifest_path, manifest.legacy_snapshot_id, source_ns, UUID(bytes=metadata.core_id), eid, r1s[eid][1], r2s[eid], (plan,), lane, idempotency, f"b4b-b3b-{eid}"), embedder=embedder)
    motif_object, motif_r1 = connection.execute("SELECT object_id,current_revision_id FROM objects WHERE object_id=(SELECT object_id FROM legacy_object_aliases WHERE legacy_source_namespace_id=? AND alias_kind='MOTIF_ID' AND alias_value='motif-b4b')", (native_id_to_bytes(source_ns),)).fetchone()
    request = MigrationRuntimeMotifRegeometryProjectionRequest(root, manifest_path, manifest.legacy_snapshot_id, source_ns, UUID(bytes=metadata.core_id), "motif-b4b", UUID(bytes=motif_object), UUID(bytes=motif_r1), (plan,), lane, idempotency, "b4b-project")
    return qualified, {"connection": connection, "metadata": metadata, "manifest": manifest, "plan": plan, "lane": lane, "request": request, "source": UUID(bytes=motif_object), "r1s": r1s, "r2s": r2s, "embedders": embedders, "vectors": (np.asarray((2., .6, 0.), dtype=np.float32), np.asarray((.1, 1., 0.), dtype=np.float32), np.asarray((0., 0., 1.), dtype=np.float32))}


def _manual_geometry(vectors):
    def unit(value):
        value = np.asarray(value, dtype=np.float32); return (value / float(np.linalg.norm(value) + 1e-12)).astype(np.float32)
    def cosine(a, b): return float(np.dot(a, b) / ((float(np.linalg.norm(a)) + 1e-12) * (float(np.linalg.norm(b)) + 1e-12)))
    centroid = unit(vectors[0]); stability = .5
    for prior_count, vector in enumerate(vectors[1:], 1):
        candidate = unit(vector); similarity = cosine(candidate, centroid)
        rate = float(np.clip(.12 / np.sqrt(1. + prior_count / 8.), .025, .08))
        centroid = unit((1. - rate) * centroid + rate * candidate)
        stability = float(np.clip(.9 * stability + .1 * max(0., similarity), 0., 1.))
    return centroid, stability


def test_b4b_mixed_bootstrap_cross_lane_geometry_b1_and_reader(tmp_path: Path):
    qualified, facts = _context(tmp_path)
    try:
        connection = facts["connection"]; request = facts["request"]
        before = NativeMigrationRuntimeReadinessPreflight(connection).run(MigrationRuntimeReadinessRequest(facts["manifest"].legacy_snapshot_id, request.expected_native_core_id, (facts["plan"],), facts["lane"]))
        assert before.motif_items[0].readiness is not MotifRuntimeReadiness.RUNTIME_READY_AS_IS
        source = connection.execute("SELECT current_revision_id,current_revision_ordinal FROM objects WHERE object_id=?", (native_id_to_bytes(facts["source"]),)).fetchone()
        result = NativeMigrationRuntimeMotifRegeometryProjectionService(connection).project_target_lane_regeometry(request)
        assert NativeMigrationRuntimeMotifRegeometryProjectionService(connection).project_target_lane_regeometry(request) == result
        expected_centroid, expected_stability = _manual_geometry(facts["vectors"])
        reader = NativeMotifRuntimeReader(connection); motifs = reader.list_runtime_motifs(motif_alias_namespace_id=facts["plan"].motif_alias_namespace_id, domain_id="reflection", semantic_scope_id=facts["plan"].target_semantic_scope_id)
        assert len(motifs) == 1 and motifs[0].motif_object_id == result.motif_object_id
        assert np.allclose(motifs[0].read_model.centroid, expected_centroid, rtol=0, atol=1e-7)
        assert motifs[0].read_model.stability_score == pytest.approx(expected_stability, abs=1e-7)
        assert motifs[0].read_model.stability_score != .88
        assert motifs[0].read_model.strength == .73
        assert [item.member_object_id for item in reader.list_ordered_current_motif_members(result.motif_object_id)] == [facts["r1s"][eid][0] for eid in (7, 8, 9)]
        assert reader.motif_radius(result.motif_object_id, expected_dimension=3) >= 0
        assert reader.domain_centroid(motif_alias_namespace_id=facts["plan"].motif_alias_namespace_id, domain_id="reflection", dimension=3, semantic_scope_id=facts["plan"].target_semantic_scope_id).shape == (3,)
        assert reader.project_coherence_field_rows(motif_alias_namespace_id=facts["plan"].motif_alias_namespace_id, domain_id="reflection", expected_dimension=3, semantic_scope_id=facts["plan"].target_semantic_scope_id)[0]["members"] == 3
        assert connection.execute("SELECT current_revision_id,current_revision_ordinal FROM objects WHERE object_id=?", (native_id_to_bytes(facts["source"]),)).fetchone() == source
        assert all(embedder.calls for embedder in facts["embedders"].values())
        after = NativeMigrationRuntimeReadinessPreflight(connection).run(MigrationRuntimeReadinessRequest(facts["manifest"].legacy_snapshot_id, request.expected_native_core_id, (facts["plan"],), facts["lane"]))
        assert after.motif_items[0].readiness is MotifRuntimeReadiness.RUNTIME_READY_AS_IS
    finally: qualified.close()


def test_b4b_refuses_same_lane_missing_or_malformed_source_witness(tmp_path: Path):
    qualified, facts = _context(tmp_path, source_lane=("new-provider", "new-model", 3))
    try:
        with pytest.raises(MigrationRuntimeMotifRegeometryProjectionRefused, match="B4A_LANE_PRESERVING_PROJECTION_AVAILABLE"):
            NativeMigrationRuntimeMotifRegeometryProjectionService(facts["connection"]).project_target_lane_regeometry(facts["request"])
    finally: qualified.close()
    for suffix, kwargs in (("missing", {"include_meta": False}), ("malformed", {"malformed_meta": True})):
        child = tmp_path / suffix; child.mkdir()
        qualified, facts = _context(child, **kwargs)
        try:
            with pytest.raises(MigrationRuntimeMotifRegeometryProjectionRefused, match="B4B_SOURCE_LANE_UNQUALIFIED"):
                NativeMigrationRuntimeMotifRegeometryProjectionService(facts["connection"]).project_target_lane_regeometry(facts["request"])
        finally: qualified.close()


def test_b4b_atomic_response_loss_idempotency_and_future_append(tmp_path: Path):
    qualified, facts = _context(tmp_path)
    try:
        service = NativeMigrationRuntimeMotifRegeometryProjectionService(facts["connection"])
        with pytest.raises(RuntimeError, match="before B4B"):
            service.project_target_lane_regeometry(facts["request"], _test_fail_before_commit=True)
        assert facts["connection"].execute("SELECT count(*) FROM objects WHERE object_kind='DERIVED_MOTIF'").fetchone()[0] == 0
        with pytest.raises(RuntimeError, match="response loss"):
            service.project_target_lane_regeometry(facts["request"], _test_lose_response_after_commit=True)
        result = service.project_target_lane_regeometry(facts["request"])
        with pytest.raises(SubstrateIdempotencyConflict):
            service.project_target_lane_regeometry(replace(facts["request"], runtime_motif_id="different"))
        extra = NativeObjectService(facts["connection"]).create_object(idempotency_namespace_id=facts["request"].idempotency_namespace_id, idempotency_key="b4b-extra-object", state=ObjectState(facts["plan"].target_identity_namespace_id, facts["plan"].target_semantic_scope_id, "LEGACY_CORE_NODE", "EXISTS", "EXPLICIT", True, "DERIVED", "NOT_APPLICABLE", {"summary": "extra"}, "JSON"))
        motifs = NativeMotifService(facts["connection"]); current = motifs.get_current_motif(result.motif_object_id)
        motifs.add_motif_member(idempotency_namespace_id=facts["request"].idempotency_namespace_id, idempotency_key="b4b-extra-member", motif_alias_namespace_id=facts["plan"].motif_alias_namespace_id, membership_identity_namespace_id=facts["plan"].membership_identity_namespace_id, motif_object_id=result.motif_object_id, expected_motif_revision_id=current.motif_revision_id, state=current.state, member_object_id=extra.object_id)
        assert [item.member_object_id for item in NativeMotifRuntimeReader(facts["connection"]).list_ordered_current_motif_members(result.motif_object_id)] == [facts["r1s"][eid][0] for eid in (7, 8, 9)] + [extra.object_id]
    finally: qualified.close()


def test_b4b_refuses_an_incomplete_target_member_vector_without_partial_projection(tmp_path: Path):
    qualified, facts = _context(tmp_path, bootstrap_all=False)
    try:
        with pytest.raises(MigrationRuntimeMotifRegeometryProjectionRefused, match="B4B_MEMBER_TARGET_GEOMETRY_INCOMPLETE"):
            NativeMigrationRuntimeMotifRegeometryProjectionService(facts["connection"]).project_target_lane_regeometry(facts["request"])
        assert facts["connection"].execute("SELECT count(*) FROM objects WHERE object_kind='DERIVED_MOTIF'").fetchone()[0] == 0
    finally: qualified.close()
