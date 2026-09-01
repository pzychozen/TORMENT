"""7G5E4C multi-scope existing-workspace admission qualification."""
from __future__ import annotations

import hashlib
import json
import logging
import os
import gc
from dataclasses import replace
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace
from urllib.request import Request, urlopen

import numpy as np
import pytest

from torment_service.bridges import Bridge, BridgeRegistry
from torment_service.memory_graph import MemoryGraph
from torment_service.motifs import MotifRegistry
from torment_service.substrate.connection import open_new_native_core_connection
from torment_service.substrate.errors import SubstrateInvariantViolation
from torment_service.substrate.fabric_native_routing import NativeFabricRoutingScope
from torment_service.substrate.ids import generate_native_id
from torment_service.substrate.migration import (
    ExistingWorkspaceMultiScopeAdmissionRefused,
    ExistingWorkspaceNativeLanePlan,
    ExistingWorkspaceNativeMultiScopeAdmissionRequest,
    ExistingWorkspaceNativeMultiScopeAdmissionService,
    RetainedSideStoreEIDObservation,
    RetainedSideStoreEIDObservationState,
    WorkspaceNativeEmbedderIdentity,
    WorkspaceNativeFeaturePosture,
    load_existing_workspace_multi_scope_admission_descriptor,
    recover_existing_workspace_native_multi_scope_runtime,
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


class _InertSideStore:
    def load_anchor_state(self, **_kwargs):
        return {}

    def save_anchor_state(self, **_kwargs):
        raise AssertionError("admission B5 must not write side stores")

    def load_affect_state(self, **_kwargs):
        return {}

    def save_affect_state(self, **_kwargs):
        raise AssertionError("admission B5 must not write side stores")


class _Embedder:
    provider = "hash"
    model = "hash:3:torment"
    dim = 3

    def embed(self, _text):
        return np.asarray((1.0, 0.0, 0.0), dtype=np.float32)


def _lane() -> NativeRepresentationLane:
    return NativeRepresentationLane("hash", "hash:3:torment", 3, "COMPAT_EMBEDDING", 1, "compat-embedding-v1", "RAW_VECTOR", "float32")


def _observations():
    return tuple(RetainedSideStoreEIDObservation(name, RetainedSideStoreEIDObservationState.COMPLETE_ABSENT) for name in (
        "conflicts", "anchors", "affect_history", "character_store", "hivemind_collective", "bridges", "trajectory_evidence", "deep_memory",
    ))


def _post_write_private(plan: ExistingWorkspaceNativeLanePlan, lane: NativeRepresentationLane):
    runtime = NativeMemoryRuntimeScope(plan.workspace_id, plan.scope_kind, plan.legacy_source_namespace_id, plan.target_identity_namespace_id, plan.target_semantic_scope_id, plan.agent_id, plan.domain_id)
    routing = NativeFabricRoutingScope(runtime, plan.motif_alias_namespace_id, plan.motif_identity_namespace_id, plan.membership_identity_namespace_id, plan.idempotency_namespace_id)
    template = NativeDerivedMemoryRuntimeConfiguration(
        workspace_id=plan.workspace_id, agent_id=plan.agent_id or "", domain_id=plan.motif_domain_id,
        legacy_source_namespace_id=plan.legacy_source_namespace_id, motif_alias_namespace_id=plan.motif_alias_namespace_id,
        memory_identity_namespace_id=plan.target_identity_namespace_id, semantic_scope_id=plan.target_semantic_scope_id,
        idempotency_namespace_id=plan.idempotency_namespace_id, parent_native_operation_key="7G5E4C-B5-INERT",
        expected_dimension=lane.dimension, embed=lambda _text: (_ for _ in ()).throw(AssertionError("B5 must not embed")),
        embedder_provider=lane.provider, embedder_model=lane.model, side_store=_InertSideStore(),
    )
    return NativePostWriteQualificationConfiguration(
        routing_scope=routing, profile=NativePostWriteQualificationProfile.core_staging(),
        external=NativePostWriteExternalDependencies(
            owner=SimpleNamespace(), workspace=SimpleNamespace(), identity=SimpleNamespace(), agent_key=plan.agent_id or "",
            detect_canon_conflict=lambda *_args: (_ for _ in ()).throw(AssertionError("B5 must not post-write")),
            proposal_allowed=lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("B5 must not post-write")),
            hivemind_log=logging.getLogger("7g5e4c.inert"),
        ),
        derived_runtime_template=template, motif_suggestion_maintenance_required=False,
        persistent_trajectory_evidence_required=False, checkpoint_snapshots_required=False,
        bridge_suggestions_required=False, deep_memory_required=False,
    )


def _http(path: str, payload: dict):
    request = Request(f"http://127.0.0.1:8787{path}", data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def _tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted((item for item in root.rglob("*") if item.is_file()), key=lambda item: item.as_posix()):
        digest.update(path.relative_to(root).as_posix().encode("utf-8")); digest.update(b"\0")
        digest.update(path.read_bytes()); digest.update(b"\0")
    return digest.hexdigest()


def _create_real_workspace(data: Path) -> Path:
    """Use the ordinary executable service plus HTTP ingestion for every lane."""
    environment = os.environ.copy()
    environment.update({
        "TORMENT_DATA_DIR": str(data), "TORMENT_EMBED_PROVIDER": "hash", "TORMENT_HASH_DIM": "3",
        "TORMENT_CHARACTER_ENABLE": "0", "TORMENT_AUTH_ENABLE": "0", "TORMENT_CHECKPOINT_ENABLE": "0",
        "TORMENT_HIVEMIND_ENABLE": "0", "TORMENT_THINKING_ADVISORY": "0", "TORMENT_SRG_COGNITION": "0",
        "TORMENT_REINFORCE_SIM_THRESHOLD": "0", "TORMENT_ID_ANCHOR_MIN_COUNT": "1000",
    })
    server = subprocess.Popen(
        [sys.executable, "-m", "torment_service"], cwd=Path.cwd(), env=environment,
        stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, text=True,
        creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
    )
    try:
        deadline = time.monotonic() + 35
        while True:
            try:
                with urlopen("http://127.0.0.1:8787/health", timeout=1) as response:
                    if response.status == 200:
                        break
            except OSError:
                if time.monotonic() >= deadline:
                    raise AssertionError("normal torment_service did not start")
                time.sleep(.2)
        assert _http("/workspace/create", {"workspace_id": "orchard", "domains": ["personal", "research", "engineering", "creative"]})["workspace_id"] == "orchard"
        _http("/agent/create", {"workspace_id": "orchard", "agent_id": "aria", "seed": {"seed_id": "", "seed_text": ""}})
        lane_vectors = {
            "personal": ((.9, .3, .1), (.85, .35, .1), (.8, .4, .1)),
            "research": ((.7, .6, .1), (.68, .62, .1), (.66, .64, .1)),
            "engineering": ((.1, .8, .5), (.1, .78, .52), (.1, .76, .54)),
            "creative": ((.3, .1, .9), (.32, .1, .88), (.34, .1, .86)),
        }
        step = 0
        for domain, vectors in lane_vectors.items():
            for ordinal, vector in enumerate(vectors):
                step += 1
                scope = "private" if domain == "personal" else "shared"
                response = _http("/agent/ingest", {
                    "workspace_id": "orchard", "agent_id": "aria", "text": f"{domain} normal-service memory {ordinal}",
                    "step": step, "domain_id": domain, "scope": scope,
                    "supplied_summary": f"{domain} normal-service memory {ordinal}", "supplied_embedding": list(vector),
                })
                assert response.get("stored") is True
    finally:
        if server.poll() is None:
            server.terminate()
            server.wait(timeout=12)
    root = data / "workspaces" / "orchard"
    # BridgeRegistry is retained and external.  Use its normal owner API,
    # rather than hand-writing bridge JSON, to make one cross-domain endpoint
    # available for the admission observation.
    bridges = BridgeRegistry(str(data), "orchard")
    bridges.bridges.append(Bridge(
        from_domain="research", from_motif="motif_research_0001",
        to_domain="engineering", to_motif="motif_engineering_0001",
        confidence=.9, created_ts=1,
    ))
    bridges.bridges.append(Bridge(
        from_domain="research", from_motif="motif_research_0001",
        to_domain="archive", to_motif="motif_archive_0001",
        confidence=.4, created_ts=2,
    ))
    bridges.save()
    return root


def _plans(root: Path):
    values = []
    private = ExistingWorkspaceNativeLanePlan(
        workspace_id="orchard", scope_kind="PRIVATE_AGENT", agent_id="aria",
        legacy_graph_source_path=root / "agents" / "aria" / "private", legacy_source_namespace_id=_id(),
        legacy_source_namespace_key="orchard:private:aria", target_identity_namespace_id=_id(),
        target_semantic_scope_id=_id(), motif_alias_namespace_id=_id(), motif_identity_namespace_id=_id(),
        membership_identity_namespace_id=_id(), idempotency_namespace_id=_id(), motif_domain_id="personal",
        representation_lane=_lane(),
    )
    values.append(private)
    for domain in ("creative", "engineering", "research"):
        values.append(ExistingWorkspaceNativeLanePlan(
            workspace_id="orchard", scope_kind="SHARED_DOMAIN", domain_id=domain,
            legacy_graph_source_path=root / "domains" / domain / "shared", legacy_source_namespace_id=_id(),
            legacy_source_namespace_key=f"orchard:shared:{domain}", target_identity_namespace_id=_id(),
            target_semantic_scope_id=_id(), motif_alias_namespace_id=_id(), motif_identity_namespace_id=_id(),
            membership_identity_namespace_id=_id(), idempotency_namespace_id=_id(), motif_domain_id=domain,
            representation_lane=_lane(),
        ))
    return tuple(values)


def _freeze_zero_eid_overlap(root: Path, plans) -> None:
    """Characterize a pre-existing legacy EID=0 in every isolated graph.

    Normal current service creation is intentionally exercised first.  Its
    SeedWorld allocator begins at one, so this narrow frozen-source adjustment
    models the established legacy EID-zero case without fabricating the
    workspace, vectors, or motifs from JSON alone.
    """
    for plan in plans:
        graph = Path(plan.legacy_graph_source_path)
        nodes = []
        for line in (graph / "nodes.jsonl").read_text(encoding="utf-8").splitlines():
            value = json.loads(line)
            if value["eid"] == 1:
                value["eid"] = 0
            nodes.append(value)
        (graph / "nodes.jsonl").write_text("\n".join(json.dumps(value, separators=(",", ":")) for value in nodes) + "\n", encoding="utf-8", newline="\n")
        for mapping in (graph / "embeddings").glob("*.map.jsonl"):
            map_rows = []
            for line in mapping.read_text(encoding="utf-8").splitlines():
                value = json.loads(line)
                if value["eid"] == 1:
                    value["eid"] = 0
                map_rows.append(value)
            mapping.write_text("\n".join(json.dumps(value, separators=(",", ":")) for value in map_rows) + "\n", encoding="utf-8", newline="\n")
        motifs_path = root / "domains" / plan.motif_domain_id / "motifs.json"
        motifs = json.loads(motifs_path.read_text(encoding="utf-8"))
        for motif in motifs["motifs"].values():
            motif["members"] = [0 if value == 1 else value for value in motif["members"]]
        motifs_path.write_text(json.dumps(motifs, indent=2, sort_keys=True), encoding="utf-8", newline="\n")


def _request(tmp_path: Path, root: Path, plans):
    lane = _lane()
    return ExistingWorkspaceNativeMultiScopeAdmissionRequest(
        legacy_workspace_root=root, workspace_id="orchard", native_core_database_path=tmp_path / "native" / "core.db",
        admission_descriptor_path=tmp_path / "native" / "multi-scope-admission.json", snapshot_root=tmp_path / "snapshots" / "evidence",
        admission_key="orchard-multi-scope-001", lane_plans=plans, unknown_semantic_scope_id=_id(),
        qualified_representation_lane=lane, staging_feature_posture=WorkspaceNativeFeaturePosture.a3d10_core_staging(),
        production_feature_posture=WorkspaceNativeFeaturePosture.a3d10_core_staging(),
        qualification_embedder_identity=WorkspaceNativeEmbedderIdentity(lane.provider, lane.model, lane.dimension),
        private_post_write_configuration=_post_write_private(plans[0], lane),
        retained_side_store_eid_observations=_observations(),
    )


def test_real_multi_scope_admission_cold_recovery_vectors_and_resume(tmp_path: Path):
    (tmp_path / "native").mkdir(); (tmp_path / "snapshots").mkdir()
    root = _create_real_workspace(tmp_path / "service-data")
    plans = _plans(root); _freeze_zero_eid_overlap(root, plans); request = _request(tmp_path, root, plans)
    service = ExistingWorkspaceNativeMultiScopeAdmissionService()
    with pytest.raises(ExistingWorkspaceMultiScopeAdmissionRefused, match="LANE_PATH_MISMATCH"):
        service.admit(replace(request, lane_plans=(replace(plans[0], agent_id="wrong-agent"), *plans[1:])))
    with pytest.raises(ExistingWorkspaceMultiScopeAdmissionRefused, match="LANE_PATH_MISMATCH"):
        wrong_shared = replace(plans[-1], domain_id="wrong-domain", motif_domain_id="wrong-domain")
        service.admit(replace(request, lane_plans=(*plans[:-1], wrong_shared)))
    mismatched_lane = NativeRepresentationLane("hash", "wrong-model", 3, "COMPAT_EMBEDDING", 1, "compat-embedding-v1", "RAW_VECTOR", "float32")
    with pytest.raises(ExistingWorkspaceMultiScopeAdmissionRefused, match="EMBEDDING_LANE_MISMATCH"):
        service.admit(replace(
            request, lane_plans=tuple(replace(plan, representation_lane=mismatched_lane) for plan in plans),
            qualified_representation_lane=mismatched_lane,
            qualification_embedder_identity=WorkspaceNativeEmbedderIdentity("hash", "wrong-model", 3),
        ))
    legacy_matrices = {}
    for plan in plans:
        graph = MemoryGraph(str(plan.legacy_graph_source_path), embedder=_Embedder())
        graph._ensure_index()
        legacy_matrices[plan.qualifier] = (tuple(graph._eid_list), graph._emb_mat.copy())
    del graph
    gc.collect()
    legacy_centroids = {
        domain: MotifRegistry(str(root.parents[1]), "orchard", domain).domain_centroid(3)
        for domain in ("research", "engineering", "creative")
    }
    before = _tree_digest(root)
    with pytest.raises(RuntimeError, match="shared B3A"):
        service.admit(request, _test_interrupt_after="SHARED_B3A")
    with pytest.raises(ExistingWorkspaceMultiScopeAdmissionRefused, match="RECOVERY_NOT_COMPLETE"):
        recover_existing_workspace_native_multi_scope_runtime(
            native_core_database_path=request.native_core_database_path,
            admission_descriptor_path=request.admission_descriptor_path,
        )
    changed_path = root / "domains" / "creative" / "shared" / "nodes.jsonl"
    original = changed_path.read_bytes()
    changed_path.write_bytes(original + b"\n")
    with pytest.raises(ExistingWorkspaceMultiScopeAdmissionRefused, match="SOURCE_EVIDENCE_MISMATCH"):
        service.admit(request)
    changed_path.write_bytes(original)
    with pytest.raises(RuntimeError, match="response loss"):
        service.admit(request, _test_lose_response_after="B5")
    result = service.admit(request)
    assert result.resumed and result.multi_scope_b5
    assert result.descriptor.state.value == "ADMISSION_COMPLETE"
    assert [item.qualifier for item in result.lane_results] == ["aria", "creative", "engineering", "research"]
    assert all(item.memory_count and item.representation_count and item.motif_count for item in result.lane_results)
    assert before == _tree_digest(root)
    bridge_observation = result.descriptor.payload["bridge_compatibility_observation"]
    assert bridge_observation["owner"] == "EXTERNAL_BRIDGE_REGISTRY"
    admitted_bridge = next(item for item in bridge_observation["bridges"] if (
        item["from_domain"], item["to_domain"]
    ) == ("research", "engineering"))
    assert [item["status"] for item in admitted_bridge["endpoints"]] == ["RESOLVED", "RESOLVED"]
    unadmitted_bridge = next(item for item in bridge_observation["bridges"] if item["to_domain"] == "archive")
    assert [item["status"] for item in unadmitted_bridge["endpoints"]] == ["RESOLVED", "UNADMITTED_DOMAIN"]

    recovered = recover_existing_workspace_native_multi_scope_runtime(
        native_core_database_path=request.native_core_database_path,
        admission_descriptor_path=request.admission_descriptor_path,
    )
    with pytest.raises(ExistingWorkspaceMultiScopeAdmissionRefused, match="WRONG_LANE"):
        recover_existing_workspace_native_multi_scope_runtime(
            native_core_database_path=request.native_core_database_path,
            admission_descriptor_path=request.admission_descriptor_path,
            expected_representation_lane=NativeRepresentationLane("wrong", "wrong", 3, "COMPAT_EMBEDDING", 1, "compat-embedding-v1", "RAW_VECTOR", "float32"),
        )
    wrong_core = tmp_path / "wrong-core.db"
    with open_new_native_core_connection(wrong_core) as qualified:
        create_schema(qualified.connection)
    with pytest.raises(ExistingWorkspaceMultiScopeAdmissionRefused, match="WRONG_CORE"):
        recover_existing_workspace_native_multi_scope_runtime(
            native_core_database_path=wrong_core,
            admission_descriptor_path=request.admission_descriptor_path,
        )
    private = recovered.lookup_private("aria")
    shared = tuple(recovered.lookup_shared(domain) for domain in ("research", "engineering", "creative"))
    object_ids = []
    for scope in (private, *shared):
        with scope.open_readers() as readers:
            first = readers.memory_enumeration.get_current(0)
            assert first is not None and first.eid == 0
            object_ids.append(readers.memory.resolve_memory_eid(
                legacy_source_namespace_id=scope.memory_runtime_scope.legacy_source_namespace_id, eid=0,
            ))
            qualified = readers.memory_enumeration.read_current_embedding(0, expected_dimension=3)
            assert qualified is not None
            with scope.new_vector_runtime(embedder=_Embedder()) as vector_runtime:
                hits = vector_runtime.search_by_embedding(np.frombuffer(qualified.payload_bytes, dtype=np.float32), top_k=8)
                assert hits and {item["eid"] for item in hits}.issubset({item.eid for item in readers.memory_enumeration.list_current()})
                # A warm same-lane query reuses the lane-local B1 matrix.  The
                # fixture opens one runtime per lane, preventing accidental
                # reuse of a whole-core query cache.
                assert vector_runtime.search_by_embedding(np.frombuffer(qualified.payload_bytes, dtype=np.float32), top_k=8) == hits
                assert vector_runtime.rebuild_count == 1
                expected_eids, expected_matrix = legacy_matrices[scope.memory_runtime_scope.qualifier]
                assert tuple(row.eid for row in vector_runtime.snapshot.rows) == expected_eids
                assert vector_runtime.snapshot.matrix.tobytes() == expected_matrix.tobytes()
                marker = "personal" if scope.memory_runtime_scope.scope_kind == "PRIVATE_AGENT" else scope.memory_runtime_scope.domain_id
                assert all(marker in str(item["summary"]) for item in hits)
    assert len(set(object_ids)) == 4  # every legacy lane's numeric EID 0 is isolated.

    for scope in shared:
        with scope.open_readers() as readers:
            centroid = readers.motifs.domain_centroid(
                motif_alias_namespace_id=scope.fabric_routing_scope.motif_alias_namespace_id,
                domain_id=scope.memory_runtime_scope.domain_id or "", dimension=3,
                semantic_scope_id=scope.memory_runtime_scope.semantic_scope_id,
            )
            assert centroid == pytest.approx(tuple(legacy_centroids[scope.memory_runtime_scope.domain_id]))

    with recovered.lookup_shared("research").open_readers() as readers:
        research = recovered.lookup_shared("research")
        engineering = recovered.lookup_shared("engineering")
        with pytest.raises(SubstrateInvariantViolation):
            readers.motifs.list_runtime_motifs(
                motif_alias_namespace_id=engineering.fabric_routing_scope.motif_alias_namespace_id,
                domain_id="research", semantic_scope_id=research.memory_runtime_scope.semantic_scope_id,
            )

    gc.collect()
    root.rename(root.with_name("orchard-source-unavailable"))
    code = (
        "from pathlib import Path\nimport json,sys\n"
        "from torment_service.substrate.migration import recover_existing_workspace_native_multi_scope_runtime as f\n"
        "r=f(native_core_database_path=Path(sys.argv[1]),admission_descriptor_path=Path(sys.argv[2]))\n"
        "s=[r.lookup_private('aria'),r.lookup_shared('research'),r.lookup_shared('engineering'),r.lookup_shared('creative')]\n"
        "out=[]\nfor x in s:\n z=x.open_readers()\n out.append((x.memory_runtime_scope.scope_kind,x.memory_runtime_scope.qualifier,[m.eid for m in z.memory_enumeration.list_current()]))\n z.close()\n"
        "print(json.dumps(out))"
    )
    fresh = subprocess.run([sys.executable, "-c", code, str(request.native_core_database_path), str(request.admission_descriptor_path)], cwd=Path.cwd(), check=True, text=True, capture_output=True)
    fresh_result = json.loads(fresh.stdout)
    assert [item[1] for item in fresh_result] == ["aria", "research", "engineering", "creative"]
    assert all(item[2] for item in fresh_result)
    descriptor_path = Path(request.admission_descriptor_path)
    wrapped = json.loads(descriptor_path.read_text(encoding="utf-8"))
    wrapped["payload"]["lanes"].pop()
    tampered_descriptor_path = descriptor_path.with_name("multi-scope-admission-tampered.json")
    tampered_descriptor_path.write_text(json.dumps(wrapped), encoding="utf-8")
    with pytest.raises(ExistingWorkspaceMultiScopeAdmissionRefused, match="DESCRIPTOR_TAMPERED"):
        load_existing_workspace_multi_scope_admission_descriptor(tampered_descriptor_path)
    inserted = json.loads(descriptor_path.read_text(encoding="utf-8"))
    inserted["payload"]["lanes"].append(json.loads(json.dumps(inserted["payload"]["lanes"][0])))
    inserted["payload"]["declared_lane_count"] += 1
    inserted["descriptor_digest"] = hashlib.sha256(json.dumps(
        inserted["payload"], sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode("utf-8")).hexdigest()
    inserted_descriptor_path = descriptor_path.with_name("multi-scope-admission-inserted.json")
    inserted_descriptor_path.write_text(json.dumps(inserted), encoding="utf-8")
    with pytest.raises(ExistingWorkspaceMultiScopeAdmissionRefused, match="LANE_SET_MISMATCH"):
        load_existing_workspace_multi_scope_admission_descriptor(inserted_descriptor_path)


def test_multi_scope_request_refuses_colliding_or_mismatched_lane_plans(tmp_path: Path):
    root = tmp_path / "root"; (root / "agents" / "aria" / "private" / "embeddings").mkdir(parents=True)
    # Constructor checks are deliberately available before a source is touched.
    first = ExistingWorkspaceNativeLanePlan("workspace", "PRIVATE_AGENT", root / "agents" / "aria" / "private", _id(), "private", _id(), _id(), _id(), _id(), _id(), _id(), "personal", representation_lane=_lane(), agent_id="aria")
    second = ExistingWorkspaceNativeLanePlan("workspace", "SHARED_DOMAIN", root / "domains" / "research" / "shared", _id(), "research", _id(), _id(), _id(), _id(), _id(), _id(), "research", representation_lane=_lane(), domain_id="research")

    def request_with(second_plan):
        return ExistingWorkspaceNativeMultiScopeAdmissionRequest(
            legacy_workspace_root=root, workspace_id="workspace", native_core_database_path=tmp_path / "core.db",
            admission_descriptor_path=tmp_path / "descriptor.json", snapshot_root=tmp_path / "snapshots", admission_key="key",
            lane_plans=(first, second_plan), unknown_semantic_scope_id=_id(), qualified_representation_lane=_lane(),
            staging_feature_posture=WorkspaceNativeFeaturePosture.a3d10_core_staging(), production_feature_posture=WorkspaceNativeFeaturePosture.a3d10_core_staging(),
            qualification_embedder_identity=WorkspaceNativeEmbedderIdentity("hash", "hash:3:torment", 3), private_post_write_configuration=_post_write_private(first, _lane()),
        )

    with pytest.raises(ValueError, match="distinct legacy_source_namespace_id"):
        request_with(replace(second, legacy_source_namespace_id=first.legacy_source_namespace_id))
    with pytest.raises(ValueError, match="distinct target_semantic_scope_id"):
        request_with(replace(second, target_semantic_scope_id=first.target_semantic_scope_id))
    with pytest.raises(ValueError, match="distinct motif_alias_namespace_id"):
        request_with(replace(second, motif_alias_namespace_id=first.motif_alias_namespace_id))
    with pytest.raises(ValueError, match="motif_domain_id"):
        ExistingWorkspaceNativeLanePlan("workspace", "SHARED_DOMAIN", root / "domains" / "research" / "shared", _id(), "research", _id(), _id(), _id(), _id(), _id(), _id(), "wrong", representation_lane=_lane(), domain_id="research")
