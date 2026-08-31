"""7G5E2 Character seed witness, native planting, and recovered-reader locks."""
from __future__ import annotations

from dataclasses import replace
import hashlib
import json
import logging
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from types import SimpleNamespace
from uuid import UUID
from urllib.request import Request, urlopen

import numpy as np
import pytest

from torment_service.character import CharacterSeed, CharacterState, CharacterStore, _split_seed_text, measure_drift
from torment_service.character_drift_runtime import CharacterDriftPostWriteRequest
from torment_service.character_gravity_runtime import CharacterGravityCorrectionRequest, CharacterGravityCorrectionStatus
from torment_service.memory_graph import MemoryGraph
from torment_service.motifs import MotifRegistry
from torment_service.provenance_v1 import ProvenanceV1
from torment_service.substrate.character_seed_witness import (
    CharacterSeedWitnessRefused, read_legacy_character_seed_witness,
)
from torment_service.substrate.connection import open_existing_native_core_connection, open_temporary_test_connection
from torment_service.substrate.fabric_native_routing import NativeFabricRoutingScope, NativeMotifProcessOrder
from torment_service.substrate.ids import generate_native_id, native_id_to_bytes
from torment_service.substrate.motif_runtime_reader import NativeMotifRuntimeReader
from torment_service.substrate.native_character_drift_runtime import (
    NativeCharacterDriftRuntime, NativeCharacterDriftRuntimeConfiguration,
)
from torment_service.substrate.native_character_gravity_runtime import (
    NativeCharacterGravityCorrectionRuntime, NativeCharacterGravityCorrectionRuntimeConfiguration,
)
from torment_service.substrate.native_character_seed_plant import (
    NativeCharacterSeedPlantRequest, NativeCharacterSeedPlantRuntime,
    NativeCharacterSeedPlantRuntimeConfiguration,
)
from torment_service.substrate.native_memory_runtime_access import NativePostWriteMemoryAccess
from torment_service.substrate.native_derived_memory_runtime import NativeDerivedMemoryRuntimeConfiguration
from torment_service.substrate.native_post_write_runtime import (
    NativePostWriteExternalDependencies, NativePostWriteQualificationConfiguration,
    NativePostWriteQualificationProfile,
)
from torment_service.substrate.native_world_runtime import NativeWorldProcessState
from torment_service.substrate.runtime_binding import NativeMemoryRuntimeScope, NativeRepresentationLane
from torment_service.substrate.schema import create_schema
from torment_service.substrate.migration import (
    ExistingWorkspaceAdmissionRefused, ExistingWorkspaceNativeAdmissionRequest, ExistingWorkspaceNativeAdmissionService,
    RetainedSideStoreEIDObservation, RetainedSideStoreEIDObservationState,
    WorkspaceNativeEmbedderIdentity, WorkspaceNativeFeaturePosture,
    recover_existing_workspace_native_runtime,
)


def _id():
    return generate_native_id()


class _Embedder:
    provider = "synthetic"; model = "synthetic-v1"; dim = 3

    def __init__(self, vector=(1.0, 0.0, 0.0)):
        self.vector = vector; self.calls: list[str] = []

    def embed(self, text: str):
        self.calls.append(text)
        return np.asarray(self.vector, dtype=np.float32)


def _lane():
    return NativeRepresentationLane("synthetic", "synthetic-v1", 3, "COMPAT_EMBEDDING", 1, "compat-embedding-v1", "RAW_VECTOR", "float32")


def _database(tmp_path: Path):
    path = tmp_path / "character.db"
    qualified = open_temporary_test_connection(path); create_schema(qualified.connection)
    connection = qualified.connection
    values = {name: _id() for name in ("memory_identity", "motif_identity", "membership_identity", "scope", "idempotency", "memory_alias", "motif_alias")}
    for name in ("memory_identity", "motif_identity", "membership_identity"):
        connection.execute("INSERT INTO identity_namespaces VALUES (?,?,0)", (native_id_to_bytes(values[name]), name))
    connection.execute("INSERT INTO semantic_scopes VALUES (?,?,0)", (native_id_to_bytes(values["scope"]), "private"))
    connection.execute("INSERT INTO idempotency_namespaces VALUES (?,?)", (native_id_to_bytes(values["idempotency"]), "character"))
    for name in ("memory_alias", "motif_alias"):
        connection.execute("INSERT INTO legacy_source_namespaces VALUES (?,?,0)", (native_id_to_bytes(values[name]), name))
    scope = NativeMemoryRuntimeScope("ws", "PRIVATE_AGENT", values["memory_alias"], values["memory_identity"], values["scope"], "aria")
    values.update(path=path, qualified=qualified, connection=connection, routing=NativeFabricRoutingScope(scope, values["motif_alias"], values["motif_identity"], values["membership_identity"], values["idempotency"]))
    return values


def _seed():
    return CharacterSeed("aria-seed-v1", "Aria", "A patient and enduring first concept. A second resilient concept.", owner_agent_id="aria")


def _plant(values, *, parent="seed-parent", embedder=None):
    return NativeCharacterSeedPlantRuntime(
        values["connection"], configuration=NativeCharacterSeedPlantRuntimeConfiguration(
            "ws", "aria", "personal", parent, values["routing"], _lane(), embedder or _Embedder(), now_ts=lambda: 100,
        ),
    )


class _InertB5SideStore:
    def load_anchor_state(self, **_kwargs):
        return {}

    def save_anchor_state(self, **_kwargs):
        raise AssertionError("B5 must not write Character state")

    def load_affect_state(self, **_kwargs):
        return {}

    def save_affect_state(self, **_kwargs):
        raise AssertionError("B5 must not write Character state")


def _character_admission_request(tmp_path: Path, root: Path, plan: dict[str, UUID], seed: CharacterSeed, *, lane: NativeRepresentationLane | None = None):
    lane = lane or _lane()
    runtime = NativeMemoryRuntimeScope(
        "orchard", "PRIVATE_AGENT", plan["source"], plan["target_identity"], plan["target_scope"], "aria",
    )
    routing = NativeFabricRoutingScope(runtime, plan["motif_alias"], plan["motif_identity"], plan["membership_identity"], plan["idempotency"])
    template = NativeDerivedMemoryRuntimeConfiguration(
        workspace_id="orchard", agent_id="aria", domain_id="personal", legacy_source_namespace_id=plan["source"],
        motif_alias_namespace_id=plan["motif_alias"], memory_identity_namespace_id=plan["target_identity"],
        semantic_scope_id=plan["target_scope"], idempotency_namespace_id=plan["idempotency"],
        parent_native_operation_key="7G5E2-B5-INERT", expected_dimension=lane.dimension,
        embed=lambda _text: (_ for _ in ()).throw(AssertionError("B5 must not embed")),
        embedder_provider=lane.provider, embedder_model=lane.model, side_store=_InertB5SideStore(),
    )
    post_write = NativePostWriteQualificationConfiguration(
        routing_scope=routing, profile=NativePostWriteQualificationProfile.core_staging(),
        external=NativePostWriteExternalDependencies(
            owner=SimpleNamespace(), workspace=SimpleNamespace(), identity=SimpleNamespace(), agent_key="aria",
            detect_canon_conflict=lambda *_args: (_ for _ in ()).throw(AssertionError("B5 must not post-write")),
            proposal_allowed=lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("B5 must not post-write")),
            hivemind_log=logging.getLogger("7g5e2.inert"),
        ),
        derived_runtime_template=template, motif_suggestion_maintenance_required=False,
        persistent_trajectory_evidence_required=False, checkpoint_snapshots_required=False,
        bridge_suggestions_required=False, deep_memory_required=False,
    )
    observations = tuple(
        RetainedSideStoreEIDObservation(name, RetainedSideStoreEIDObservationState.COMPLETE_ABSENT)
        for name in ("conflicts", "anchors", "affect_history", "character_store", "hivemind_collective", "bridges", "trajectory_evidence", "deep_memory")
    )
    return ExistingWorkspaceNativeAdmissionRequest(
        legacy_workspace_root=root, workspace_id="orchard", agent_id="aria",
        native_core_database_path=tmp_path / "native" / "core.db", admission_descriptor_path=tmp_path / "native" / "admission.json",
        snapshot_root=tmp_path / "snapshot" / "evidence", snapshot_manifest_path=tmp_path / "snapshot" / "manifest.json",
        admission_key="orchard-private-character-001", legacy_source_namespace_id=plan["source"], legacy_source_namespace_key="orchard-private-source",
        target_identity_namespace_id=plan["target_identity"], target_semantic_scope_id=plan["target_scope"], unknown_semantic_scope_id=plan["unknown_scope"],
        motif_alias_namespace_id=plan["motif_alias"], motif_identity_namespace_id=plan["motif_identity"], membership_identity_namespace_id=plan["membership_identity"], idempotency_namespace_id=plan["idempotency"],
        qualified_representation_lane=lane, motif_domain_id="personal", staging_feature_posture=WorkspaceNativeFeaturePosture.a3d10_core_staging(),
        production_feature_posture=WorkspaceNativeFeaturePosture.a3d10_core_staging(), qualification_embedder_identity=WorkspaceNativeEmbedderIdentity(lane.provider, lane.model, lane.dimension),
        post_write_configuration=post_write, retained_side_store_eid_observations=observations,
        character_seed_id=seed.seed_id,
    )


def _legacy_seed_payload(seed: CharacterSeed, *, index: int, concept: str) -> dict:
    return {
        "summary": concept, "type": "seed_canon", "memory_class": "core", "strength": .95,
        "confidence": .95, "half_life": seed.core_half_life, "canon": True, "user_id": "aria",
        "created_at": 0, "created_ts": 0, "last_reinforced": 0, "seed_id": seed.seed_id,
        "character_name": seed.character_name, "tier": "core_identity", "seed_concept_index": index,
        "lifecycle_status": {"state": "protected", "is_authoritative_on_row": True, "requires_join": None,
                             "set_by": {"actor": "system", "via": "canon_set", "at": 0}, "history_ref": None},
        "pos": [0.0, 0.0, 0.0], "vel": [0.0, 0.0, 0.0], "vel0": [0.0, 0.0, 0.0],
    }


def _ordinary_payload() -> dict:
    return {
        "summary": "A later ordinary private memory.", "type": "memory", "memory_class": "core", "strength": .7,
        "confidence": .9, "half_life_days": 365.0, "seed_pos0": [1, 2, 3], "seed_v0": [.1, .2, .3],
        "governance": {"protected": False, "non_shareable": False, "collective_export_blocked": False,
                       "collective_reingest_blocked": False, "decay_accelerated": False},
        "provenance": ProvenanceV1(source_type="role_output", source_role="tester", write_path="cognition_writeback", parent_eids=[], created_at_step=4, created_at_ts="2024-01-01T00:00:00Z").to_dict(),
        "lifecycle_status": {"state": "active", "is_authoritative_on_row": True, "requires_join": None,
                             "set_by": {"actor": "user", "via": "api", "at": 4}, "history_ref": None},
    }


def _legacy_character_workspace(tmp_path: Path):
    data = tmp_path / "data"; root = data / "workspaces" / "orchard"; private = root / "agents" / "aria" / "private"
    private.mkdir(parents=True); (tmp_path / "native").mkdir(); (tmp_path / "snapshot").mkdir()
    seed = CharacterSeed("aria-seed-v1", "Aria", "A patient and enduring first concept. A second resilient concept.", owner_agent_id="aria")
    concepts = _split_seed_text(seed.seed_text); seed.seed_eids = [7, 8]; seed.seed_motif_id = "motif-seed"; seed.created_ts = 0
    CharacterStore(str(data)).save_seed("orchard", seed)
    (root / "workspace_meta.json").write_text(json.dumps({"workspace_id": "orchard", "embed_provider": "synthetic", "embed_model": "synthetic-v1", "embed_dim": 3}), encoding="utf-8")
    (root / "agents" / "aria" / "identity.json").write_text(json.dumps({"workspace_id": "orchard", "agent_id": "aria", "seed": seed.to_dict()}), encoding="utf-8")
    payloads = [_legacy_seed_payload(seed, index=index, concept=concept) for index, concept in enumerate(concepts)] + [_ordinary_payload()]
    eids = [7, 8, 9]; vectors = np.asarray(((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (-1.0, 0.0, 0.0)), dtype=np.float32)
    rows = [json.dumps({"eid": eid, "born_step": index, "channel": 1, "payload": payload,
                        "embedding_ref": {"map": "embeddings/shard.map.jsonl", "shard": "embeddings/shard.npy", "row": index, "dimension": 3, "dtype": "float32"}}, separators=(",", ":"))
            for index, (eid, payload) in enumerate(zip(eids, payloads, strict=True))]
    (private / "nodes.jsonl").write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
    embeddings = private / "embeddings"; embeddings.mkdir(); np.save(embeddings / "shard.npy", vectors)
    (embeddings / "manifest.json").write_text(json.dumps({"encoding_id": "NUMPY_NPY", "dtype": "float32", "dimension": 3, "derivation_contract_version": "synthetic-captured-v1", "provider": "synthetic", "model": "synthetic-v1", "shards": [{"path": "embeddings/shard.npy", "map": "embeddings/shard.map.jsonl"}]}), encoding="utf-8")
    (embeddings / "shard.map.jsonl").write_text("\n".join(json.dumps({"eid": eid, "shard": "embeddings/shard.npy", "row": index, "dimension": 3}) for index, eid in enumerate(eids)) + "\n", encoding="utf-8", newline="\n")
    motifs = root / "domains" / "personal"; motifs.mkdir(parents=True)
    def motif(runtime_id, members):
        return {"motif_id": runtime_id, "domain_id": "personal", "label": runtime_id, "centroid": [1.0, 0.0, 0.0], "strength": .7, "stability_score": .8, "contributing_agents": ["aria"], "created_ts": 0, "last_active_ts": 0, "members": members}
    (motifs / "motifs.json").write_text(json.dumps({"motifs": {"motif-seed": motif("motif-seed", [7, 8]), "motif-ordinary": motif("motif-ordinary", [9])}}), encoding="utf-8")
    plan = {name: _id() for name in ("source", "target_identity", "target_scope", "unknown_scope", "motif_alias", "motif_identity", "membership_identity", "idempotency")}
    return data, root, seed, plan


def _rewrite_seed_json(root: Path, seed_id: str, mutate) -> None:
    path = root / "seeds" / seed_id / "seed.json"
    value = json.loads(path.read_text(encoding="utf-8")); mutate(value)
    path.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")


def _rewrite_node_payload(root: Path, eid: int, mutate) -> None:
    path = root / "agents" / "aria" / "private" / "nodes.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    for row in rows:
        if row["eid"] == eid:
            mutate(row["payload"]); break
    else:
        raise AssertionError("fixture EID is missing")
    path.write_text("\n".join(json.dumps(row, separators=(",", ":")) for row in rows) + "\n", encoding="utf-8", newline="\n")


@pytest.mark.parametrize("kind", (
    "seed_eids", "seed_id", "character_name", "missing_concept", "duplicate_index",
    "summary", "foreign_seed_canon", "seed_motif_members",
))
def test_legacy_character_seed_witness_refuses_incomplete_or_mismatching_evidence(tmp_path: Path, kind: str):
    case = tmp_path / kind; case.mkdir()
    _data, root, seed, _plan = _legacy_character_workspace(case)
    if kind == "seed_eids":
        _rewrite_seed_json(root, seed.seed_id, lambda value: value.__setitem__("seed_eids", [7, 9]))
    elif kind == "seed_id":
        _rewrite_seed_json(root, seed.seed_id, lambda value: value.__setitem__("seed_id", "not-aria"))
    elif kind == "character_name":
        _rewrite_node_payload(root, 7, lambda value: value.__setitem__("character_name", "Not Aria"))
    elif kind == "missing_concept":
        _rewrite_seed_json(root, seed.seed_id, lambda value: value.__setitem__("seed_eids", [7]))
    elif kind == "duplicate_index":
        _rewrite_node_payload(root, 8, lambda value: value.__setitem__("seed_concept_index", 0))
    elif kind == "summary":
        _rewrite_node_payload(root, 8, lambda value: value.__setitem__("summary", "not the frozen concept"))
    elif kind == "foreign_seed_canon":
        _rewrite_node_payload(root, 9, lambda value: value.__setitem__("type", "seed_canon"))
    elif kind == "seed_motif_members":
        path = root / "domains" / "personal" / "motifs.json"; value = json.loads(path.read_text(encoding="utf-8"))
        value["motifs"][seed.seed_motif_id]["members"] = [9]
        path.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(CharacterSeedWitnessRefused):
        read_legacy_character_seed_witness(
            workspace_root=root, workspace_id="orchard", agent_id="aria", domain_id="personal", requested_seed_id=seed.seed_id,
        )


def test_existing_character_seed_admission_normalizes_only_witnessed_seed_rows(tmp_path: Path):
    data, root, seed, plan = _legacy_character_workspace(tmp_path)
    witness = read_legacy_character_seed_witness(
        workspace_root=root, workspace_id="orchard", agent_id="aria", domain_id="personal", requested_seed_id=seed.seed_id,
    )
    assert witness.seed_eids == (7, 8) and witness.seed_motif_seed_eids == (7, 8)
    request = _character_admission_request(tmp_path, root, plan, seed)
    result = ExistingWorkspaceNativeAdmissionService().admit(request)
    assert result.descriptor.payload["profile"] == "EXISTING_WORKSPACE_PRIVATE_CHARACTER"
    assert result.descriptor.character_seed_witness == witness
    assert result.memory_count == 3 and result.motif_count == 2
    with open_existing_native_core_connection(request.native_core_database_path) as qualified:
        rows = qualified.connection.execute(
            """SELECT a.alias_value,r.revision_ordinal,p.origin_kind,p.source_channel,p.source_role,
                      p.derivation_status,p.uncertainty_state,p.memory_role,r.payload_text
                   FROM legacy_object_aliases a JOIN objects o ON o.object_id=a.object_id
                   JOIN object_revisions r ON r.object_id=o.object_id AND r.object_revision_id=o.current_revision_id
                   LEFT JOIN provenance_records p ON p.provenance_id=r.provenance_id
                  WHERE a.legacy_source_namespace_id=? AND o.object_kind='LEGACY_CORE_NODE'
                  ORDER BY CAST(a.alias_value AS INTEGER)""",
            (native_id_to_bytes(plan["source"]),),
        ).fetchall()
    assert [(row[0], row[1]) for row in rows] == [("7", 2), ("8", 2), ("9", 2)]
    assert [row[2:8] for row in rows[:2]] == [
        ("CHARACTER_SEED_PLANT", "character_runtime", "seed_canon", "seed_plant", "KNOWN", "seed_canon"),
        ("CHARACTER_SEED_PLANT", "character_runtime", "seed_canon", "seed_plant", "KNOWN", "seed_canon"),
    ]
    assert json.loads(rows[0][8])["summary"] == _split_seed_text(seed.seed_text)[0]
    # The non-seed memory still uses ordinary B2 and its existing provenance translation.
    assert rows[2][2] != "CHARACTER_SEED_PLANT"
    recovered = recover_existing_workspace_native_runtime(
        native_core_database_path=request.native_core_database_path,
        admission_descriptor_path=request.admission_descriptor_path,
        character_store=CharacterStore(str(data)),
    )
    with recovered.open_readers() as readers:
        assert [readers.memory.get_memory_by_eid(legacy_source_namespace_id=plan["source"], eid=eid).payload["type"] for eid in seed.seed_eids] == ["seed_canon", "seed_canon"]
        motifs = readers.motifs.list_runtime_motifs(motif_alias_namespace_id=plan["motif_alias"], domain_id="personal", semantic_scope_id=plan["target_scope"])
        seed_motif = next(item for item in motifs if item.read_model.runtime_motif_id == seed.seed_motif_id)
        members = readers.motifs.list_ordered_current_motif_members(seed_motif.motif_object_id)
        seed_object_ids = {
            readers.memory.resolve_memory_eid(legacy_source_namespace_id=plan["source"], eid=eid)
            for eid in seed.seed_eids
        }
        assert {member.member_object_id for member in members} == seed_object_ids


def test_existing_character_cold_recovery_preserves_native_c1a_and_c1b_without_graph(tmp_path: Path):
    data, root, seed, plan = _legacy_character_workspace(tmp_path)
    store = CharacterStore(str(data))
    graph = MemoryGraph(str(root / "agents" / "aria" / "private"), embedder=_Embedder())
    registry = MotifRegistry(
        str(data), "orchard", "personal", shard_reader=graph._shard_reader,
        entity_payload_fn=lambda eid: graph.entities[eid].payload if eid in graph.entities else None,
    )
    prior = CharacterState("orchard", "aria", seed.seed_id, distance_to_seed=0.0)
    legacy_drift = measure_drift(
        graph=graph, motif_registry=registry, coherence_field=None, seed=seed, agent_id="aria",
        current_step=10, previous_state=prior,
    )
    store.save_state("orchard", prior)
    request = _character_admission_request(tmp_path, root, plan, seed)
    ExistingWorkspaceNativeAdmissionService().admit(request)

    # CharacterStore remains in place, while all legacy native-storage inputs
    # used by MemoryGraph and MotifRegistry become unavailable.
    (root / "agents" / "aria" / "private").rename(root / "legacy-private-unavailable")
    (root / "domains").rename(root / "legacy-domains-unavailable")
    recovered = recover_existing_workspace_native_runtime(
        native_core_database_path=request.native_core_database_path,
        admission_descriptor_path=request.admission_descriptor_path,
        character_store=store,
    )
    with recovered.open_readers() as readers:
        drift = NativeCharacterDriftRuntime(
            configuration=NativeCharacterDriftRuntimeConfiguration(
                "orchard", "aria", seed.seed_id, "personal", plan["motif_alias"], plan["target_scope"], 3, True, 1,
            ),
            store=store, memory_read=readers.memory_enumeration, memory_enumeration=readers.memory_enumeration,
            motif_reader=readers.motifs,
        ).measure_for_post_write(CharacterDriftPostWriteRequest("orchard", "aria", 10, True, "CREATED_NEW"))
        assert drift.drift is not None
        for field in ("drift_score", "distance_to_seed", "drift_direction", "core_count", "relational_count", "situational_count", "seed_basin_role"):
            assert drift.drift[field] == pytest.approx(legacy_drift[field]) if isinstance(legacy_drift[field], float) else drift.drift[field] == legacy_drift[field]

    # C1B deliberately receives a frozen correction trigger after the cold
    # read; it writes only to the native core and retains the external seed.
    with open_existing_native_core_connection(request.native_core_database_path) as qualified:
        correction = NativeCharacterGravityCorrectionRuntime(
            qualified.connection,
            configuration=NativeCharacterGravityCorrectionRuntimeConfiguration(
                "orchard", "aria", "personal", "existing-seed-c1b", recovered.fabric_routing_scope,
                _lane(), _Embedder((1.0, 0.0, 0.0)), now_ts=lambda: 101,
                choose_concept=lambda concepts: concepts[0],
            ),
            world_process_state=NativeWorldProcessState(), motif_process_order=NativeMotifProcessOrder(),
        ).correct_for_post_write(CharacterGravityCorrectionRequest(
            "orchard", "aria", 10, seed, {"drift_score": -.5, "drift_direction": "away_seed"},
        ))
        assert correction.status is CharacterGravityCorrectionStatus.APPLIED
        assert correction.correction_identity is not None
        correction_retry = NativeCharacterGravityCorrectionRuntime(
            qualified.connection,
            configuration=NativeCharacterGravityCorrectionRuntimeConfiguration(
                "orchard", "aria", "personal", "existing-seed-c1b", recovered.fabric_routing_scope,
                _lane(), _Embedder((1.0, 0.0, 0.0)), now_ts=lambda: 101,
                choose_concept=lambda concepts: concepts[0],
            ),
            world_process_state=NativeWorldProcessState(), motif_process_order=NativeMotifProcessOrder(),
        ).correct_for_post_write(CharacterGravityCorrectionRequest(
            "orchard", "aria", 10, seed, {"drift_score": -.5, "drift_direction": "away_seed"},
        ))
        assert correction_retry.correction_identity is not None
        assert correction_retry.correction_identity.source.eid == correction.correction_identity.source.eid
        assert correction_retry.correction_identity.source.memory_object_id == correction.correction_identity.source.memory_object_id
        assert correction_retry.correction_identity.representation_id == correction.correction_identity.representation_id
        assert correction_retry.motif_status == correction.motif_status

    with open_existing_native_core_connection(request.native_core_database_path) as reopened:
        access = NativePostWriteMemoryAccess(reopened.connection, legacy_source_namespace_id=plan["source"], expected_dimension=3)
        correction_view = access.get_current(correction.correction_identity.source.eid)
        assert correction_view is not None and correction_view.memory_type == "drift_correction"
        assert correction_view.payload["tier"] == "core_identity" and correction_view.payload["canon"] is True
        assert access.read_current_embedding(correction.correction_identity.source.eid, expected_dimension=3) is not None
    stored_seed = store.load_seed("orchard", seed.seed_id)
    assert stored_seed is not None and stored_seed.seed_eids == seed.seed_eids and stored_seed.seed_motif_id == seed.seed_motif_id


def test_existing_character_admission_response_loss_descriptor_tamper_and_namespace_changes_refuse(tmp_path: Path):
    data, root, seed, plan = _legacy_character_workspace(tmp_path)
    request = _character_admission_request(tmp_path, root, plan, seed)
    service = ExistingWorkspaceNativeAdmissionService()
    with pytest.raises(RuntimeError, match="response loss"):
        service.admit(request, _test_lose_response_after_stage="B2")
    completed = service.admit(request)
    assert service.admit(request).descriptor.digest == completed.descriptor.digest
    with pytest.raises(ExistingWorkspaceAdmissionRefused, match="REQUEST_MISMATCH"):
        service.admit(replace(request, legacy_source_namespace_id=_id()))
    with pytest.raises(ExistingWorkspaceAdmissionRefused, match="REQUEST_MISMATCH"):
        service.admit(replace(request, motif_alias_namespace_id=_id()))
    # A post-completion seed-definition change is source evidence drift, not a
    # new immutable CharacterStore claim.  The descriptor refuses it.
    _rewrite_seed_json(root, seed.seed_id, lambda value: value.__setitem__("character_name", "Changed Aria"))
    with pytest.raises(ExistingWorkspaceAdmissionRefused, match="SOURCE_EVIDENCE_MISMATCH"):
        service.admit(request)
    descriptor = json.loads(request.admission_descriptor_path.read_text(encoding="utf-8"))
    descriptor["payload"]["character_seed"]["seed_definition_digest"] = "0" * 64
    request.admission_descriptor_path.write_text(json.dumps(descriptor), encoding="utf-8")
    with pytest.raises(ExistingWorkspaceAdmissionRefused, match="DESCRIPTOR_TAMPERED"):
        recover_existing_workspace_native_runtime(
            native_core_database_path=request.native_core_database_path,
            admission_descriptor_path=request.admission_descriptor_path,
            character_store=CharacterStore(str(data)),
        )


def test_fresh_native_seed_plant_is_idempotent_and_cold_readable(tmp_path: Path):
    values = _database(tmp_path)
    try:
        seed, embedder = _seed(), _Embedder()
        runtime = _plant(values, embedder=embedder)
        result = runtime.plant_seed(NativeCharacterSeedPlantRequest(seed, step=0))
        assert result.state == "COMPLETE" and result.seed_eids == (0, 1)
        assert [source.concept for source in result.sources] == _split_seed_text(seed.seed_text)
        assert len(embedder.calls) == 2
        access = NativePostWriteMemoryAccess(values["connection"], legacy_source_namespace_id=values["memory_alias"], expected_dimension=3)
        assert [item.eid for item in access.list_current()] == [0, 1]
        for index, source in enumerate(result.sources):
            current = access.get_current(source.eid)
            assert current is not None and current.summary == source.concept
            assert current.memory_type == "seed_canon" and current.memory_class == "core"
            assert current.strength == current.confidence == .95
            assert current.payload["half_life"] == 3650.0 and current.payload["tier"] == "core_identity"
            assert current.payload["seed_concept_index"] == index
            assert access.read_current_embedding(source.eid, expected_dimension=3).payload_bytes == np.asarray((1., 0., 0.), dtype=np.float32).tobytes()
            provenance = values["connection"].execute("SELECT origin_kind,source_channel,source_role,derivation_status,uncertainty_state,memory_role FROM provenance_records WHERE provenance_id=?", (native_id_to_bytes(source.provenance_id),)).fetchone()
            assert provenance == ("CHARACTER_SEED_PLANT", "character_runtime", "seed_canon", "seed_plant", "KNOWN", "seed_canon")
        motifs = NativeMotifRuntimeReader(values["connection"]).list_runtime_motifs(motif_alias_namespace_id=values["motif_alias"], domain_id="personal", semantic_scope_id=values["scope"])
        assert [(item.read_model.runtime_motif_id, item.read_model.member_count) for item in motifs] == [(result.seed_motif_id, 2)]
        counts = tuple(values["connection"].execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in ("objects", "object_revisions", "representations", "relationships", "operations"))
        retry = runtime.plant_seed(NativeCharacterSeedPlantRequest(seed, step=0))
        assert retry.seed_eids == result.seed_eids and retry.seed_motif_id == result.seed_motif_id
        assert tuple(values["connection"].execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in ("objects", "object_revisions", "representations", "relationships", "operations")) == counts
        with pytest.raises(Exception, match="idempotency"):
            runtime.plant_seed(NativeCharacterSeedPlantRequest(replace(seed, seed_text="A different enduring concept."), step=0))
        values["qualified"].close()
        with open_existing_native_core_connection(values["path"]) as reopened:
            access = NativePostWriteMemoryAccess(reopened.connection, legacy_source_namespace_id=values["memory_alias"], expected_dimension=3)
            assert [item.eid for item in access.list_current()] == list(result.seed_eids)
            motif = NativeMotifRuntimeReader(reopened.connection).list_runtime_motifs(motif_alias_namespace_id=values["motif_alias"], domain_id="personal", semantic_scope_id=values["scope"])
            assert motif[0].read_model.runtime_motif_id == result.seed_motif_id
    finally:
        try: values["qualified"].close()
        except Exception: pass


def test_fresh_seed_partial_resume_and_cold_native_c1a_c1b(tmp_path: Path):
    values = _database(tmp_path)
    try:
        seed, runtime = _seed(), _plant(values)
        with pytest.raises(RuntimeError, match="interruption"):
            runtime.plant_seed(NativeCharacterSeedPlantRequest(seed), _test_interrupt_after_concept=0)
        result = runtime.plant_seed(NativeCharacterSeedPlantRequest(seed))
        assert result.seed_eids == (0, 1)
        store = CharacterStore(str(tmp_path / "external-character-store"))
        persisted = replace(seed, seed_eids=list(result.seed_eids), seed_motif_id=result.seed_motif_id, created_ts=100)
        store.save_seed("ws", persisted)
        values["qualified"].close()
        with open_existing_native_core_connection(values["path"]) as reopened:
            access = NativePostWriteMemoryAccess(reopened.connection, legacy_source_namespace_id=values["memory_alias"], expected_dimension=3)
            drift = NativeCharacterDriftRuntime(
                configuration=NativeCharacterDriftRuntimeConfiguration("ws", "aria", seed.seed_id, "personal", values["motif_alias"], values["scope"], 3, True, 1),
                store=store, memory_read=access, memory_enumeration=access, motif_reader=NativeMotifRuntimeReader(reopened.connection),
            )
            drift_result = drift.measure_for_post_write(CharacterDriftPostWriteRequest("ws", "aria", 10, True, "CREATED_NEW"))
            assert drift_result.drift is not None and drift_result.drift["core_count"] == 0
            correction = NativeCharacterGravityCorrectionRuntime(
                reopened.connection, configuration=NativeCharacterGravityCorrectionRuntimeConfiguration(
                    "ws", "aria", "personal", "seed-c1b", values["routing"], _lane(), _Embedder(), now_ts=lambda: 101,
                    choose_concept=lambda concepts: concepts[0],
                ), world_process_state=NativeWorldProcessState(), motif_process_order=NativeMotifProcessOrder(),
            )
            corrected = correction.correct_for_post_write(CharacterGravityCorrectionRequest("ws", "aria", 10, persisted, {"drift_score": -.5, "drift_direction": "away_seed"}))
            assert corrected.status is CharacterGravityCorrectionStatus.APPLIED
            assert corrected.correction_identity is not None
            assert NativeMotifRuntimeReader(reopened.connection).list_runtime_motifs(motif_alias_namespace_id=values["motif_alias"], domain_id="personal", semantic_scope_id=values["scope"])[0].read_model.runtime_motif_id == result.seed_motif_id
    finally:
        values["qualified"].close()


def test_fresh_seed_without_real_split_geometry_remains_admissible(tmp_path: Path):
    values = _database(tmp_path)
    try:
        first = _plant(values, parent="first").plant_seed(NativeCharacterSeedPlantRequest(_seed()))
        existing = NativeMotifRuntimeReader(values["connection"]).list_runtime_motifs(
            motif_alias_namespace_id=values["motif_alias"], domain_id="personal", semantic_scope_id=values["scope"],
        )[0]
        # Catalog cardinality alone is not a split decision.  The actual
        # qualified current geometry remains below the split input size.
        inflated_model = replace(existing.read_model, member_count=95)
        values["connection"]  # keep the qualified core explicit in the fixture
        runtime = _plant(values, parent="split")
        runtime._motif_reader.list_runtime_motifs = lambda **_kwargs: (replace(existing, read_model=inflated_model),)  # type: ignore[method-assign]
        result = runtime.plant_seed(NativeCharacterSeedPlantRequest(replace(_seed(), seed_id="aria-seed-split")))
        assert result.seed_motif_id == existing.read_model.runtime_motif_id
        assert first.seed_motif_id == NativeMotifRuntimeReader(values["connection"]).list_runtime_motifs(
            motif_alias_namespace_id=values["motif_alias"], domain_id="personal", semantic_scope_id=values["scope"],
        )[0].read_model.runtime_motif_id
    finally:
        values["qualified"].close()


def _http_json(path: str, payload: dict):
    request = Request(
        f"http://127.0.0.1:8787{path}", data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def test_normal_service_character_workspace_admits_and_cold_recovers(tmp_path: Path):
    """The only legacy writer in this test is normal ``python -m torment_service``."""
    data = tmp_path / "normal-service-data"; native = tmp_path / "native"; snapshot = tmp_path / "snapshot"
    native.mkdir(); snapshot.mkdir()
    environment = os.environ.copy()
    environment.update({
        "TORMENT_DATA_DIR": str(data), "TORMENT_EMBED_PROVIDER": "hash", "TORMENT_HASH_DIM": "384",
        "TORMENT_CHARACTER_ENABLE": "1", "TORMENT_AUTH_ENABLE": "0", "TORMENT_CHECKPOINT_ENABLE": "0",
        "TORMENT_HIVEMIND_ENABLE": "0", "TORMENT_THINKING_ADVISORY": "0", "TORMENT_SRG_COGNITION": "0",
    })
    server = subprocess.Popen(
        [sys.executable, "-m", "torment_service"], cwd=Path.cwd(), env=environment,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
    )
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
        assert _http_json("/workspace/create", {"workspace_id": "orchard", "domains": ["personal"]})["workspace_id"] == "orchard"
        seed_input = {
            "seed_id": "aria-production-v1", "character_name": "Aria",
            "seed_text": "A patient and enduring first concept. A second resilient concept.",
        }
        _http_json("/agent/create", {"workspace_id": "orchard", "agent_id": "aria", "seed": seed_input})
        for step, index in enumerate(range(3), start=1):
            vector = [0.0] * 384; vector[index] = .8; vector[index + 8] = .6
            assert _http_json("/agent/ingest", {
                "workspace_id": "orchard", "agent_id": "aria", "text": f"ordinary character memory {step}",
                "step": step, "domain_id": "personal", "scope": "private",
                "supplied_summary": f"ordinary character memory {step}", "supplied_embedding": vector,
            }).get("ok") is True
    finally:
        if server.poll() is None:
            try:
                server.send_signal(signal.CTRL_BREAK_EVENT); server.wait(timeout=10)
            except (AttributeError, subprocess.TimeoutExpired):
                server.terminate(); server.wait(timeout=10)

    root = data / "workspaces" / "orchard"; store = CharacterStore(str(data))
    seed = store.load_seed("orchard", "aria-production-v1")
    assert seed is not None and seed.seed_eids and seed.seed_motif_id
    metadata = json.loads((root / "workspace_meta.json").read_text(encoding="utf-8"))
    lane = NativeRepresentationLane(metadata["embed_provider"], metadata["embed_model"], metadata["embed_dim"], "COMPAT_EMBEDDING", 1, "compat-embedding-v1", "RAW_VECTOR", "float32")
    plan = {name: _id() for name in ("source", "target_identity", "target_scope", "unknown_scope", "motif_alias", "motif_identity", "membership_identity", "idempotency")}
    request = _character_admission_request(tmp_path, root, plan, seed, lane=lane)
    admitted = ExistingWorkspaceNativeAdmissionService().admit(request)
    assert admitted.descriptor.character_seed_witness is not None
    # Retain only CharacterStore files from the legacy workspace and prove the
    # seed references resolve from the native core after a cold reconstruction.
    (root / "agents" / "aria" / "private").rename(root / "legacy-private-unavailable")
    (root / "domains").rename(root / "legacy-domains-unavailable")
    recovered = recover_existing_workspace_native_runtime(
        native_core_database_path=request.native_core_database_path,
        admission_descriptor_path=request.admission_descriptor_path, character_store=store,
    )
    with recovered.open_readers() as readers:
        for eid in seed.seed_eids:
            memory = readers.memory.get_memory_by_eid(legacy_source_namespace_id=plan["source"], eid=eid)
            assert memory.payload["type"] == "seed_canon"
            assert readers.embeddings.read_current(memory.object_id, expected_dimension=lane.dimension) is not None
        motifs = readers.motifs.list_runtime_motifs(
            motif_alias_namespace_id=plan["motif_alias"], domain_id="personal", semantic_scope_id=plan["target_scope"],
        )
        assert any(item.read_model.runtime_motif_id == seed.seed_motif_id for item in motifs)
    fresh_code = (
        "from pathlib import Path; import json, sys; "
        "from torment_service.character import CharacterStore; "
        "from torment_service.substrate.migration import recover_existing_workspace_native_runtime as recover; "
        "runtime=recover(native_core_database_path=Path(sys.argv[1]), admission_descriptor_path=Path(sys.argv[2]), character_store=CharacterStore(sys.argv[3])); "
        "seed=runtime.require_external_character_seed(CharacterStore(sys.argv[3])); readers=runtime.open_readers(); "
        "eids=[view.eid for view in readers.memory_enumeration.list_current() if view.memory_type == 'seed_canon']; "
        "motifs=readers.motifs.list_runtime_motifs(motif_alias_namespace_id=runtime.fabric_routing_scope.motif_alias_namespace_id, domain_id='personal', semantic_scope_id=runtime.memory_runtime_scope.semantic_scope_id); "
        "print(json.dumps({'seed_eids':eids, 'motif_ids':[item.read_model.runtime_motif_id for item in motifs], 'external_seed':seed.seed_id})); readers.close()"
    )
    fresh = subprocess.run(
        [sys.executable, "-c", fresh_code, str(request.native_core_database_path), str(request.admission_descriptor_path), str(data)],
        cwd=Path.cwd(), check=True, text=True, capture_output=True,
    )
    fresh_result = json.loads(fresh.stdout)
    assert fresh_result["external_seed"] == seed.seed_id
    assert fresh_result["seed_eids"] == seed.seed_eids and seed.seed_motif_id in fresh_result["motif_ids"]
