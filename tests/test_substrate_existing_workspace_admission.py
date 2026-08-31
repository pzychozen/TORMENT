"""7G5E1 existing-workspace private-core admission and recovery qualification."""
from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from urllib.request import Request, urlopen
from types import SimpleNamespace
from uuid import UUID

import numpy as np
import pytest

from torment_service.provenance_v1 import ProvenanceV1
from torment_service.substrate.fabric_native_routing import NativeFabricRoutingScope
from torment_service.substrate.connection import open_new_native_core_connection
from torment_service.substrate.ids import generate_native_id
from torment_service.substrate.migration import (
    ExistingWorkspaceAdmissionRefused,
    ExistingWorkspaceNativeAdmissionRequest,
    ExistingWorkspaceNativeAdmissionService,
    RetainedSideStoreEIDObservation,
    RetainedSideStoreEIDObservationState,
    WorkspaceNativeEmbedderIdentity,
    WorkspaceNativeFeaturePosture,
    load_existing_workspace_admission_descriptor,
    recover_existing_workspace_native_runtime,
)
from torment_service.substrate.native_derived_memory_runtime import NativeDerivedMemoryRuntimeConfiguration
from torment_service.substrate.native_post_write_runtime import (
    NativePostWriteExternalDependencies,
    NativePostWriteQualificationConfiguration,
    NativePostWriteQualificationProfile,
)
from torment_service.substrate.runtime_binding import NativeMemoryRuntimeScope, NativeRepresentationLane
from torment_service.substrate.schema import create_schema


def _id():
    return generate_native_id()


def _lane() -> NativeRepresentationLane:
    return NativeRepresentationLane("synthetic", "synthetic", 3, "COMPAT_EMBEDDING", 1, "compat-embedding-v1", "RAW_VECTOR", "float32")


class _InertSideStore:
    def load_anchor_state(self, **_kwargs):
        return {}

    def save_anchor_state(self, **_kwargs):
        raise AssertionError("B5 must not call side stores")

    def load_affect_state(self, **_kwargs):
        return {}

    def save_affect_state(self, **_kwargs):
        raise AssertionError("B5 must not call side stores")


def _post_write(plan, lane):
    runtime = NativeMemoryRuntimeScope(
        workspace_id=plan["workspace_id"], scope_kind="PRIVATE_AGENT", agent_id=plan["agent_id"],
        legacy_source_namespace_id=plan["source"], identity_namespace_id=plan["target_identity"],
        semantic_scope_id=plan["target_scope"],
    )
    routing = NativeFabricRoutingScope(runtime, plan["motif_alias"], plan["motif_identity"], plan["membership_identity"], plan["idempotency"])
    template = NativeDerivedMemoryRuntimeConfiguration(
        workspace_id=plan["workspace_id"], agent_id=plan["agent_id"], domain_id=plan["domain"],
        legacy_source_namespace_id=plan["source"], motif_alias_namespace_id=plan["motif_alias"],
        memory_identity_namespace_id=plan["target_identity"], semantic_scope_id=plan["target_scope"],
        idempotency_namespace_id=plan["idempotency"], parent_native_operation_key="7G5E1-B5-INERT",
        expected_dimension=lane.dimension, embed=lambda _text: (_ for _ in ()).throw(AssertionError("B5 must not embed")),
        embedder_provider=lane.provider, embedder_model=lane.model, side_store=_InertSideStore(),
    )
    return NativePostWriteQualificationConfiguration(
        routing_scope=routing, profile=NativePostWriteQualificationProfile.core_staging(),
        external=NativePostWriteExternalDependencies(
            owner=SimpleNamespace(), workspace=SimpleNamespace(), identity=SimpleNamespace(), agent_key=plan["agent_id"],
            detect_canon_conflict=lambda *_args: (_ for _ in ()).throw(AssertionError("B5 must not post-write")),
            proposal_allowed=lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("B5 must not post-write")),
            hivemind_log=logging.getLogger("7g5e1.inert"),
        ),
        derived_runtime_template=template, motif_suggestion_maintenance_required=False,
        persistent_trajectory_evidence_required=False, checkpoint_snapshots_required=False,
        bridge_suggestions_required=False, deep_memory_required=False,
    )


def _observations():
    return tuple(
        RetainedSideStoreEIDObservation(name, RetainedSideStoreEIDObservationState.COMPLETE_ABSENT)
        for name in ("conflicts", "anchors", "affect_history", "character_store", "hivemind_collective", "bridges", "trajectory_evidence", "deep_memory")
    )


def _payload(eid: int):
    return {
        "summary": f"ordinary private core {eid}", "type": "memory", "memory_class": "core",
        "strength": .7 + (eid % 3) * .01, "confidence": .9, "half_life_days": 365.0,
        "seed_pos0": [1, 2, 3], "seed_v0": [.1, .2, .3],
        "governance": {"protected": False, "non_shareable": False, "collective_export_blocked": False, "collective_reingest_blocked": False, "decay_accelerated": False},
        "provenance": ProvenanceV1(source_type="role_output", source_role="tester", write_path="cognition_writeback", parent_eids=[], created_at_step=eid, created_at_ts="2024-01-01T00:00:00Z").to_dict(),
        "lifecycle_status": {"state": "active", "is_authoritative_on_row": True, "requires_join": None, "set_by": {"actor": "user", "via": "api", "at": eid}, "history_ref": None},
    }


def _tree_bytes_fingerprint(root: Path) -> str:
    """Detect a source-tree byte or pathname change without normalizing it."""
    digest = hashlib.sha256()
    for path in sorted((item for item in root.rglob("*") if item.is_file()), key=lambda item: item.as_posix()):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _source(tmp_path: Path, *, character=False, members=8) -> tuple[Path, dict, list[tuple[int, bytes]]]:
    root = tmp_path / "legacy-workspace"; private = root / "agents" / "aria" / "private"
    private.mkdir(parents=True)
    (root / "workspace_meta.json").write_text(json.dumps({"workspace_id": "orchard", "embed_provider": "synthetic", "embed_model": "synthetic", "embed_dim": 3}), encoding="utf-8")
    (root / "agents" / "aria" / "identity.json").write_text(json.dumps({"workspace_id": "orchard", "agent_id": "aria", "seed": {"seed_id": "blocked" if character else "", "seed_text": "blocked" if character else ""}}), encoding="utf-8")
    eids = list(range(7, 7 + members))
    vectors = np.asarray([(2.0 + index, .6 + index * .1, 0.0) for index in range(members)], dtype=np.float32)
    rows = []
    raw = []
    for index, eid in enumerate(eids):
        rows.append(json.dumps({"eid": eid, "born_step": index + 1, "channel": 1, "payload": _payload(eid), "embedding_ref": {"map": "embeddings/shard.map.jsonl", "shard": "embeddings/shard.npy", "row": index, "dimension": 3, "dtype": "float32"}}, separators=(",", ":")))
        raw.append((eid, vectors[index].tobytes()))
    (private / "nodes.jsonl").write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
    embeddings = private / "embeddings"; embeddings.mkdir()
    np.save(embeddings / "shard.npy", vectors)
    (embeddings / "manifest.json").write_text(json.dumps({"encoding_id": "NUMPY_NPY", "dtype": "float32", "dimension": 3, "derivation_contract_version": "synthetic-captured-v1", "provider": "synthetic", "model": "synthetic", "shards": [{"path": "embeddings/shard.npy", "map": "embeddings/shard.map.jsonl"}]}), encoding="utf-8")
    (embeddings / "shard.map.jsonl").write_text("\n".join(json.dumps({"eid": eid, "shard": "embeddings/shard.npy", "row": index, "dimension": 3}) for index, eid in enumerate(eids)) + "\n", encoding="utf-8", newline="\n")
    motifs = root / "domains" / "reflection"; motifs.mkdir(parents=True)
    midpoint = max(1, members // 2)
    groups = {"motif-a": eids[:midpoint], "motif-b": eids[midpoint:]}
    (motifs / "motifs.json").write_text(json.dumps({"motifs": {name: {"motif_id": name, "domain_id": "reflection", "label": name, "centroid": [1.0, 0.0, 0.0], "strength": .7, "stability_score": .8, "contributing_agents": ["aria"], "created_ts": 1, "last_active_ts": 2, "members": group} for name, group in groups.items()}}), encoding="utf-8")
    plan = {"workspace_id": "orchard", "agent_id": "aria", "domain": "reflection", "source": _id(), "target_identity": _id(), "target_scope": _id(), "unknown_scope": _id(), "motif_alias": _id(), "motif_identity": _id(), "membership_identity": _id(), "idempotency": _id()}
    return root, plan, raw


def _request(tmp_path: Path, root: Path, plan: dict, *, lane: NativeRepresentationLane | None = None):
    lane = lane or _lane()
    return ExistingWorkspaceNativeAdmissionRequest(
        legacy_workspace_root=root, workspace_id=plan["workspace_id"], agent_id=plan["agent_id"],
        native_core_database_path=tmp_path / "native" / "core.db", admission_descriptor_path=tmp_path / "native" / "admission.json",
        snapshot_root=tmp_path / "snapshot" / "evidence", snapshot_manifest_path=tmp_path / "snapshot" / "manifest.json",
        admission_key="orchard-private-core-001", legacy_source_namespace_id=plan["source"], legacy_source_namespace_key="orchard-private-source",
        target_identity_namespace_id=plan["target_identity"], target_semantic_scope_id=plan["target_scope"], unknown_semantic_scope_id=plan["unknown_scope"],
        motif_alias_namespace_id=plan["motif_alias"], motif_identity_namespace_id=plan["motif_identity"], membership_identity_namespace_id=plan["membership_identity"], idempotency_namespace_id=plan["idempotency"],
        qualified_representation_lane=lane, motif_domain_id=plan["domain"], staging_feature_posture=WorkspaceNativeFeaturePosture.a3d10_core_staging(),
        production_feature_posture=WorkspaceNativeFeaturePosture.a3d10_core_staging(), qualification_embedder_identity=WorkspaceNativeEmbedderIdentity(lane.provider, lane.model, lane.dimension),
        post_write_configuration=_post_write(plan, lane), retained_side_store_eid_observations=_observations(),
    )


def _table_counts(path: Path):
    from torment_service.substrate.connection import open_existing_native_core_connection
    with open_existing_native_core_connection(path) as qualified:
        return tuple(qualified.connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in ("objects", "object_revisions", "legacy_object_aliases", "representations", "relationships", "operations"))


def test_existing_workspace_private_core_admission_and_cold_native_reads(tmp_path: Path):
    (tmp_path / "native").mkdir(); (tmp_path / "snapshot").mkdir()
    root, plan, raw = _source(tmp_path)
    before = _tree_bytes_fingerprint(root)
    request = _request(tmp_path, root, plan)
    result = ExistingWorkspaceNativeAdmissionService().admit(request)
    assert result.readiness_report.core_staging_runtime_ready
    assert result.memory_count == result.readiness_report.b3a_ready_memory_count == 8
    assert result.motif_count == result.readiness_report.b4a_ready_motif_count == 2
    assert result.descriptor.state.value == "ADMISSION_COMPLETE"
    assert before == _tree_bytes_fingerprint(root)

    recovered = recover_existing_workspace_native_runtime(native_core_database_path=request.native_core_database_path, admission_descriptor_path=request.admission_descriptor_path)
    assert recovered.memory_runtime_scope.agent_id == "aria"
    assert recovered.representation_lane == request.qualified_representation_lane
    with recovered.open_readers() as readers:
        runtime_memories = readers.memory_enumeration.list_current()
        assert [item.eid for item in runtime_memories] == [eid for eid, _bytes in raw]
        assert len({item.eid for item in runtime_memories}) == len(raw)
        for eid, bytes_expected in raw:
            object_id = readers.memory.resolve_memory_eid(legacy_source_namespace_id=plan["source"], eid=eid)
            memory = readers.memory.get_memory_by_eid(legacy_source_namespace_id=plan["source"], eid=eid)
            qualified = readers.embeddings.read_current(object_id, expected_dimension=3)
            runtime = readers.memory_enumeration.get_current(eid)
            expected = _payload(eid)
            assert object_id == memory.object_id
            assert memory.revision_ordinal >= 2
            assert memory.summary == f"ordinary private core {eid}"
            assert memory.payload["type"] == expected["type"]
            assert memory.payload["memory_class"] == expected["memory_class"]
            assert memory.payload["strength"] == expected["strength"]
            assert memory.payload["confidence"] == expected["confidence"]
            assert memory.payload["half_life_days"] == expected["half_life_days"]
            assert runtime is not None
            assert runtime.memory_type == expected["type"] and runtime.memory_class == expected["memory_class"]
            assert runtime.strength == expected["strength"] and runtime.confidence == expected["confidence"]
            assert runtime.payload["half_life_days"] == expected["half_life_days"]
            assert runtime.governance.structurally_explicit
            assert not runtime.governance.protected and not runtime.governance.non_shareable
            assert runtime.provenance.structurally_explicit
            assert runtime.provenance.source_type == "role_output"
            assert runtime.provenance.write_path == "cognition_writeback"
            matching_references = [reference for reference in memory.representation_references if reference.representation_class == "COMPAT_EMBEDDING"]
            assert len(matching_references) == 1
            assert matching_references[0].readiness == "READY" and matching_references[0].usable
            assert qualified is not None and qualified.payload_bytes == bytes_expected
        search = readers.memory.search_by_embedding(legacy_source_namespace_id=plan["source"], embedding=np.frombuffer(raw[0][1], dtype=np.float32), dimension=3, top_k=8)
        assert {item.eid for item in search} == {eid for eid, _bytes in raw}
        legacy_scores = sorted(
            ((eid, float(np.dot(np.frombuffer(raw[0][1], dtype=np.float32), np.frombuffer(bytes_expected, dtype=np.float32)) /
                         (np.linalg.norm(np.frombuffer(raw[0][1], dtype=np.float32)) * np.linalg.norm(np.frombuffer(bytes_expected, dtype=np.float32)))))
             for eid, bytes_expected in raw), key=lambda item: (-item[1], item[0])
        )
        assert [item.eid for item in search] == [eid for eid, _score in legacy_scores]
        assert [item.raw_score for item in search] == pytest.approx([score for _eid, score in legacy_scores])
        motifs = readers.motifs.list_runtime_motifs(motif_alias_namespace_id=plan["motif_alias"], domain_id="reflection", semantic_scope_id=plan["target_scope"])
        assert [item.read_model.runtime_motif_id for item in motifs] == ["motif-a", "motif-b"]
        assert sum(item.read_model.member_count for item in motifs) == 8
        assert all(item.read_model.centroid == (1.0, 0.0, 0.0) for item in motifs)
        assert all(item.read_model.stability_score == .8 and item.read_model.strength == .7 for item in motifs)
        members = [readers.motifs.list_ordered_current_motif_members(item.motif_object_id) for item in motifs]
        assert sum(len(group) for group in members) == 8
        assert {member.member_object_id for group in members for member in group} == {
            readers.memory.resolve_memory_eid(legacy_source_namespace_id=plan["source"], eid=eid)
            for eid, _bytes in raw
        }
        assert all(readers.motifs.motif_radius(item.motif_object_id, expected_dimension=3) >= 0 for item in motifs)

    renamed = root.with_name("legacy-source-unavailable")
    root.rename(renamed)
    code = (
        "from pathlib import Path; import json, sys; "
        "from torment_service.substrate.migration import recover_existing_workspace_native_runtime as f; "
        "r=f(native_core_database_path=Path(sys.argv[1]), admission_descriptor_path=Path(sys.argv[2])); "
        "x=r.open_readers(); m=x.memory_enumeration.list_current(); first=m[0]; e=x.memory_enumeration.read_current_embedding(first.eid, expected_dimension=r.representation_lane.dimension); s=x.memory.search_by_embedding(legacy_source_namespace_id=r.memory_runtime_scope.legacy_source_namespace_id, embedding=__import__('numpy').frombuffer(e.payload_bytes, dtype='float32'), dimension=r.representation_lane.dimension, top_k=len(m)); motifs=x.motifs.list_runtime_motifs(motif_alias_namespace_id=r.fabric_routing_scope.motif_alias_namespace_id, domain_id='reflection', semantic_scope_id=r.memory_runtime_scope.semantic_scope_id); print(json.dumps({'workspace': r.memory_runtime_scope.workspace_id, 'eids': [v.eid for v in m], 'search': [v.eid for v in s], 'motifs': len(motifs)})); x.close()"
    )
    fresh = subprocess.run([sys.executable, "-c", code, str(request.native_core_database_path), str(request.admission_descriptor_path)], cwd=Path.cwd(), check=True, text=True, capture_output=True)
    fresh_result = json.loads(fresh.stdout)
    assert fresh_result["workspace"] == "orchard"
    assert fresh_result["eids"] == [eid for eid, _bytes in raw]
    assert set(fresh_result["search"]) == {eid for eid, _bytes in raw}
    assert fresh_result["motifs"] == 2


def test_resume_after_response_loss_and_stage_interruption_is_idempotent(tmp_path: Path):
    (tmp_path / "native").mkdir(); (tmp_path / "snapshot").mkdir()
    root, plan, _raw = _source(tmp_path)
    request = _request(tmp_path, root, plan); service = ExistingWorkspaceNativeAdmissionService()
    with pytest.raises(RuntimeError, match="response loss"):
        service.admit(request, _test_lose_response_after_stage="B3A")
    completed = service.admit(request)
    assert completed.resumed and completed.descriptor.state.value == "ADMISSION_COMPLETE"
    after_resume = _table_counts(Path(request.native_core_database_path))
    assert service.admit(request).descriptor.digest == completed.descriptor.digest
    assert _table_counts(Path(request.native_core_database_path)) == after_resume

    stage_root = tmp_path / "between-stages"; (stage_root / "native").mkdir(parents=True); (stage_root / "snapshot").mkdir()
    source_root, stage_plan, _ = _source(stage_root)
    stage_request = _request(stage_root, source_root, stage_plan)
    with pytest.raises(RuntimeError, match="interruption"):
        ExistingWorkspaceNativeAdmissionService().admit(stage_request, _test_interrupt_after_stage="B4A")
    stage_completed = ExistingWorkspaceNativeAdmissionService().admit(stage_request)
    assert stage_completed.resumed and stage_completed.descriptor.state.value == "ADMISSION_COMPLETE"
    stable = _table_counts(Path(stage_request.native_core_database_path))
    ExistingWorkspaceNativeAdmissionService().admit(stage_request)
    assert _table_counts(Path(stage_request.native_core_database_path)) == stable


@pytest.mark.parametrize("kind, code", (("character", "EXISTING_WORKSPACE_CHARACTER_PROVENANCE_BLOCKED"), ("shared", "SHARED_DOMAIN_ADMISSION_NOT_IN_7G5E1_PROFILE")))
def test_profile_boundaries_refuse_explicitly(tmp_path: Path, kind: str, code: str):
    (tmp_path / "native").mkdir(); (tmp_path / "snapshot").mkdir()
    root, plan, _raw = _source(tmp_path, character=kind == "character")
    request = _request(tmp_path, root, plan)
    if kind == "shared":
        request = ExistingWorkspaceNativeAdmissionRequest(**{**request.__dict__, "shared_domain_claimed": True})
    with pytest.raises(ExistingWorkspaceAdmissionRefused, match=code):
        ExistingWorkspaceNativeAdmissionService().admit(request)


def test_source_change_descriptor_tamper_wrong_core_and_wrong_lane_refuse(tmp_path: Path):
    (tmp_path / "native").mkdir(); (tmp_path / "snapshot").mkdir()
    root, plan, _raw = _source(tmp_path); request = _request(tmp_path, root, plan)
    ExistingWorkspaceNativeAdmissionService().admit(request)
    descriptor_path = Path(request.admission_descriptor_path)
    data = json.loads(descriptor_path.read_text(encoding="utf-8")); data["payload"]["workspace_id"] = "changed"
    descriptor_path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ExistingWorkspaceAdmissionRefused, match="DESCRIPTOR_TAMPERED"):
        load_existing_workspace_admission_descriptor(descriptor_path)


def test_first_destination_and_descriptor_request_identity_are_pinned(tmp_path: Path):
    (tmp_path / "native").mkdir(); (tmp_path / "snapshot").mkdir()
    root, plan, _raw = _source(tmp_path); request = _request(tmp_path, root, plan)
    Path(request.native_core_database_path).write_bytes(b"not a new destination")
    with pytest.raises(ExistingWorkspaceAdmissionRefused, match="FIRST_DESTINATION_MUST_BE_NEW"):
        ExistingWorkspaceNativeAdmissionService().admit(request)

    second = tmp_path / "second"; (second / "native").mkdir(parents=True); (second / "snapshot").mkdir()
    root, plan, _raw = _source(second); request = _request(second, root, plan)
    ExistingWorkspaceNativeAdmissionService().admit(request)
    changed = ExistingWorkspaceNativeAdmissionRequest(**{**request.__dict__, "admission_key": "different-operator-key"})
    with pytest.raises(ExistingWorkspaceAdmissionRefused, match="DESCRIPTOR_REQUEST_MISMATCH"):
        ExistingWorkspaceNativeAdmissionService().admit(changed)


def test_source_change_after_snapshot_and_wrong_recovery_inputs_refuse(tmp_path: Path):
    (tmp_path / "native").mkdir(); (tmp_path / "snapshot").mkdir()
    root, plan, _raw = _source(tmp_path); request = _request(tmp_path, root, plan)
    service = ExistingWorkspaceNativeAdmissionService()
    with pytest.raises(RuntimeError, match="interruption"):
        service.admit(request, _test_interrupt_after_stage="B2")
    with pytest.raises(ExistingWorkspaceAdmissionRefused, match="RECOVERY_NOT_COMPLETE"):
        recover_existing_workspace_native_runtime(
            native_core_database_path=request.native_core_database_path,
            admission_descriptor_path=request.admission_descriptor_path,
        )
    nodes = root / "agents" / "aria" / "private" / "nodes.jsonl"
    nodes.write_text(nodes.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(ExistingWorkspaceAdmissionRefused, match="SOURCE_EVIDENCE_MISMATCH"):
        service.admit(request)

    # A completed descriptor is pinned to its exact core and lane.
    (tmp_path / "complete-native").mkdir(); (tmp_path / "complete-snapshot").mkdir()
    complete_root, complete_plan, _ = _source(tmp_path / "complete")
    complete_request = _request(tmp_path / "complete", complete_root, complete_plan)
    (Path(complete_request.native_core_database_path).parent).mkdir(exist_ok=True)
    (Path(complete_request.snapshot_root).parent).mkdir(exist_ok=True)
    ExistingWorkspaceNativeAdmissionService().admit(complete_request)
    wrong_core = tmp_path / "other.db"
    with open_new_native_core_connection(wrong_core) as qualified:
        create_schema(qualified.connection)
    with pytest.raises(ExistingWorkspaceAdmissionRefused, match="WRONG_CORE"):
        recover_existing_workspace_native_runtime(native_core_database_path=wrong_core, admission_descriptor_path=complete_request.admission_descriptor_path)
    with pytest.raises(ExistingWorkspaceAdmissionRefused, match="WRONG_LANE"):
        recover_existing_workspace_native_runtime(native_core_database_path=complete_request.native_core_database_path, admission_descriptor_path=complete_request.admission_descriptor_path, expected_representation_lane=NativeRepresentationLane("synthetic", "synthetic", 4, "COMPAT_EMBEDDING", 1, "compat-embedding-v1", "RAW_VECTOR", "float32"))


def _http_json(path: str, payload: dict):
    request = Request(f"http://127.0.0.1:8787{path}", data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def test_normal_service_workspace_is_admitted_and_recovers_without_source(tmp_path: Path):
    """The legacy source is created only through normal HTTP service surfaces."""
    data = tmp_path / "normal-service-data"; native = tmp_path / "native"; snapshot = tmp_path / "snapshot"
    native.mkdir(); snapshot.mkdir()
    environment = os.environ.copy()
    environment.update({
        "TORMENT_DATA_DIR": str(data), "TORMENT_EMBED_PROVIDER": "hash", "TORMENT_HASH_DIM": "384",
        "TORMENT_CHARACTER_ENABLE": "0", "TORMENT_AUTH_ENABLE": "0", "TORMENT_CHECKPOINT_ENABLE": "0",
        "TORMENT_HIVEMIND_ENABLE": "0", "TORMENT_THINKING_ADVISORY": "0", "TORMENT_SRG_COGNITION": "0",
    })
    creation_flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    server = subprocess.Popen([sys.executable, "-m", "torment_service"], cwd=Path.cwd(), env=environment, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, creationflags=creation_flags)
    try:
        deadline = time.monotonic() + 30
        while True:
            try:
                with urlopen("http://127.0.0.1:8787/health", timeout=1) as response:
                    if response.status == 200:
                        break
            except OSError:
                if time.monotonic() >= deadline:
                    output = server.stdout.read() if server.stdout else ""
                    raise AssertionError(f"normal torment_service did not start: {output}")
                time.sleep(.2)
        assert _http_json("/workspace/create", {"workspace_id": "orchard", "domains": ["reflection"]})["workspace_id"] == "orchard"
        _http_json("/agent/create", {"workspace_id": "orchard", "agent_id": "aria", "seed": {"seed_id": "", "seed_text": ""}})
        # One exact repeat gives legacy reinforcement; two nearby clusters make
        # several ordinary memories and multiple motif memberships below split.
        vectors = []
        for group in range(2):
            for index in range(4):
                vector = [0.0] * 384; vector[group * 16] = .8; vector[group * 16 + index + 1] = .6
                vectors.append(vector)
        for step, vector in enumerate(vectors, start=1):
            body = {"workspace_id": "orchard", "agent_id": "aria", "text": f"ordinary production shaped private memory {step}", "step": step, "domain_id": "reflection", "scope": "private", "supplied_summary": f"ordinary production shaped private memory {step}", "supplied_embedding": vector}
            assert _http_json("/agent/ingest", body).get("ok") is True
        repeat = {"workspace_id": "orchard", "agent_id": "aria", "text": "ordinary production shaped private memory 1", "step": 9, "domain_id": "reflection", "scope": "private", "supplied_summary": "ordinary production shaped private memory 1", "supplied_embedding": vectors[0]}
        assert _http_json("/agent/ingest", repeat).get("ok") is True
    finally:
        if server.poll() is None:
            try:
                server.send_signal(signal.CTRL_BREAK_EVENT)
                server.wait(timeout=10)
            except (AttributeError, subprocess.TimeoutExpired):
                server.terminate(); server.wait(timeout=10)

    root = data / "workspaces" / "orchard"
    metadata = json.loads((root / "workspace_meta.json").read_text(encoding="utf-8"))
    lane = NativeRepresentationLane(metadata["embed_provider"], metadata["embed_model"], metadata["embed_dim"], "COMPAT_EMBEDDING", 1, "compat-embedding-v1", "RAW_VECTOR", "float32")
    plan = {"workspace_id": "orchard", "agent_id": "aria", "domain": "reflection", "source": _id(), "target_identity": _id(), "target_scope": _id(), "unknown_scope": _id(), "motif_alias": _id(), "motif_identity": _id(), "membership_identity": _id(), "idempotency": _id()}
    request = _request(tmp_path, root, plan, lane=lane)
    before = _tree_bytes_fingerprint(root)
    result = ExistingWorkspaceNativeAdmissionService().admit(request)
    assert result.memory_count >= 8 and result.motif_count >= 2 and result.readiness_report.core_staging_runtime_ready
    assert before == _tree_bytes_fingerprint(root)
    root.rename(root.with_name("orchard-source-unavailable"))
    code = (
        "from pathlib import Path; import json, sys; "
        "from torment_service.substrate.migration import recover_existing_workspace_native_runtime as f; "
        "r=f(native_core_database_path=Path(sys.argv[1]), admission_descriptor_path=Path(sys.argv[2])); "
        "x=r.open_readers(); m=x.memory_enumeration.list_current(); first=m[0]; e=x.memory_enumeration.read_current_embedding(first.eid, expected_dimension=r.representation_lane.dimension); s=x.memory.search_by_embedding(legacy_source_namespace_id=r.memory_runtime_scope.legacy_source_namespace_id, embedding=__import__('numpy').frombuffer(e.payload_bytes, dtype='float32'), dimension=r.representation_lane.dimension, top_k=len(m)); motifs=x.motifs.list_runtime_motifs(motif_alias_namespace_id=r.fabric_routing_scope.motif_alias_namespace_id, domain_id='reflection', semantic_scope_id=r.memory_runtime_scope.semantic_scope_id); print(json.dumps({'eids': [v.eid for v in m], 'search': [v.eid for v in s], 'motifs': len(motifs)})); x.close()"
    )
    fresh = subprocess.run([sys.executable, "-c", code, str(request.native_core_database_path), str(request.admission_descriptor_path)], cwd=Path.cwd(), check=True, text=True, capture_output=True)
    fresh_result = json.loads(fresh.stdout)
    assert len(fresh_result["eids"]) >= 8
    assert set(fresh_result["search"]) == set(fresh_result["eids"])
    assert fresh_result["motifs"] >= 2
