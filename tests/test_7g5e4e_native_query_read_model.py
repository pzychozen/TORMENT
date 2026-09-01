"""7G5E4E-A2 differential qualification for the inert query read model."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest

from torment_service import memory_graph as memory_graph_module
from torment_service.memory_graph import MemoryGraph
from torment_service.motifs import Motif, MotifRegistry
from torment_service.query_read_model import (
    LegacyQualifiedQueryReadModel,
    NativeQualifiedQueryReadModel,
)
from torment_service.substrate import native_memory_vector_runtime as vector_runtime_module
from torment_service.substrate.compat import NativeMemoryCompatibilityFacade
from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.fabric_native_routing import NativeFabricRoutingScope
from torment_service.substrate.ids import generate_native_id, native_id_from_bytes, native_id_to_bytes
from torment_service.substrate.migration.existing_workspace_multi_scope_admission import (
    RecoveredExistingWorkspaceNativeMultiScopeScope,
)
from torment_service.substrate.motifs import MotifState, NativeMotifService
from torment_service.substrate.representations import (
    INTEGRITY_ALGORITHM_SHA256,
    INTEGRITY_VALUE_ENCODING_RAW,
    NativeRepresentationService,
    RepresentationIntegrityExpectationRequest,
    RepresentationReadyRequest,
    RepresentationRequest,
)
from torment_service.substrate.runtime_binding import NativeMemoryRuntimeScope, NativeRepresentationLane
from torment_service.substrate.schema import create_schema


def _id():
    return generate_native_id()


class _Embedder:
    provider = "7g5e4e-a2"
    model = "deterministic-3"
    dim = 3

    def __init__(self, vector: tuple[float, ...] = (1.0, 0.0, 0.0)) -> None:
        self.vector = np.asarray(vector, dtype=np.float32)
        self.calls: list[str] = []

    def embed(self, text: str) -> np.ndarray:
        self.calls.append(text)
        return self.vector.copy()


def _lane() -> NativeRepresentationLane:
    return NativeRepresentationLane(
        "7g5e4e-a2", "deterministic-3", 3,
        "COMPAT_EMBEDDING", 1, "compat-embedding-v1", "RAW_VECTOR", "float32",
    )


@dataclass(frozen=True)
class _RecoveredRuntime:
    workspace_id: str
    native_core_id: Any
    representation_lane: NativeRepresentationLane
    scopes: tuple[RecoveredExistingWorkspaceNativeMultiScopeScope, ...]
    descriptor: Any

    def lookup_private(self, agent_id: str):
        return self._lookup("PRIVATE_AGENT", agent_id)

    def lookup_shared(self, domain_id: str):
        return self._lookup("SHARED_DOMAIN", domain_id)

    def _lookup(self, kind: str, qualifier: str):
        matches = [
            scope for scope in self.scopes
            if scope.memory_runtime_scope.scope_kind == kind
            and scope.memory_runtime_scope.qualifier == qualifier
        ]
        if len(matches) != 1:
            raise KeyError((kind, qualifier))
        return matches[0]


def _namespace(connection, table: str, identifier, label: str) -> None:
    if table == "idempotency_namespaces":
        connection.execute(
            "INSERT INTO idempotency_namespaces VALUES (?,?)",
            (native_id_to_bytes(identifier), label),
        )
    else:
        connection.execute(
            f"INSERT INTO {table} VALUES (?,?,0)",
            (native_id_to_bytes(identifier), label),
        )


def _scope(connection, database_path: Path, core_id, *, kind: str, qualifier: str, idempotency):
    identity, semantic, source = _id(), _id(), _id()
    motif_alias, motif_identity, membership_identity = _id(), _id(), _id()
    for table, identifier, label in (
        ("identity_namespaces", identity, f"a2:memory:{kind}:{qualifier}"),
        ("semantic_scopes", semantic, f"a2:semantic:{kind}:{qualifier}"),
        ("legacy_source_namespaces", source, f"a2:source:{kind}:{qualifier}"),
        ("legacy_source_namespaces", motif_alias, f"a2:motif-alias:{kind}:{qualifier}"),
        ("identity_namespaces", motif_identity, f"a2:motif:{kind}:{qualifier}"),
        ("identity_namespaces", membership_identity, f"a2:membership:{kind}:{qualifier}"),
    ):
        _namespace(connection, table, identifier, label)
    memory = NativeMemoryRuntimeScope(
        workspace_id="orchard", scope_kind=kind,
        legacy_source_namespace_id=source, identity_namespace_id=identity,
        semantic_scope_id=semantic,
        agent_id=qualifier if kind == "PRIVATE_AGENT" else None,
        domain_id=qualifier if kind == "SHARED_DOMAIN" else None,
    )
    routing = NativeFabricRoutingScope(
        memory, motif_alias, motif_identity, membership_identity, idempotency,
    )
    return RecoveredExistingWorkspaceNativeMultiScopeScope(
        database_path, core_id, _lane(), memory, routing,
    )


def _provenance(connection):
    identifier = _id()
    connection.execute(
        "INSERT INTO provenance_records VALUES (?,?,?,?,?,?,?,?,?,?)",
        (native_id_to_bytes(identifier), "RUNTIME_PROVENANCE_V1", "user_input", "user",
         "direct_ingest", "KNOWN", None, None, None, None),
    )
    return identifier


def _memory(
    connection, scope, idempotency, key: str, vector: tuple[float, ...], *,
    memory_type: str = "episodic", user_id: str = "aria", half_life: float = 0.0,
    reinforced: bool = False, pending: bool = False,
):
    runtime_scope = scope.memory_runtime_scope
    payload = {
        "workspace_id": "orchard",
        "domain_id": "personal" if runtime_scope.scope_kind == "PRIVATE_AGENT" else runtime_scope.domain_id,
        "agent_id": "aria",
        "provenance_type": "user_input",
        "collective": False,
        "tool_result": False,
        "srg": {"intensity": .31, "phase": "fixture"},
        "created_ts": 100,
        "last_reinforced_ts": 100,
        "reinforcement_count": 4 if reinforced else 0,
        "fixture_tag": key,
    }
    source = NativeMemoryCompatibilityFacade(connection).create_memory_state(
        legacy_source_namespace_id=runtime_scope.legacy_source_namespace_id,
        idempotency_namespace_id=idempotency,
        idempotency_key=f"a2:memory:{runtime_scope.qualifier}:{key}",
        identity_namespace_id=runtime_scope.identity_namespace_id,
        semantic_scope_id=runtime_scope.semantic_scope_id,
        summary=f"{runtime_scope.qualifier} {key}", memory_type=memory_type,
        memory_class="core", strength=.7, confidence=.8, half_life_days=half_life,
        user_id=user_id, logical_step=12, extra_payload=payload,
        governance_state="EXPLICIT", provenance_id=_provenance(connection),
    )
    representation = _representation(
        connection, source, idempotency, f"{runtime_scope.qualifier}:{key}", vector,
        publish=not pending,
    )
    return source, representation


def _representation(connection, source, idempotency, key: str, vector, *, publish: bool):
    payload = np.asarray(vector, dtype=np.float32).reshape(-1).tobytes(order="C")
    service = NativeRepresentationService(connection)
    pending = service.create_representation_pending(
        idempotency_namespace_id=idempotency, idempotency_key=f"a2:pending:{key}",
        request=RepresentationRequest(
            "OBJECT_REVISION", source.object_id, source.revision_id, None, None,
            "COMPAT_EMBEDDING", 1, "compat-embedding-v1", "RAW_VECTOR", "float32", 3,
            (), None, len(payload),
        ),
    )
    if not publish:
        return pending
    service.establish_representation_integrity_expectation(
        idempotency_namespace_id=idempotency, idempotency_key=f"a2:expect:{key}",
        request=RepresentationIntegrityExpectationRequest(
            pending.representation_id, INTEGRITY_ALGORITHM_SHA256,
            sha256(payload).digest(), INTEGRITY_VALUE_ENCODING_RAW,
        ),
    )
    return service.publish_representation_ready(
        idempotency_namespace_id=idempotency, idempotency_key=f"a2:ready:{key}",
        request=RepresentationReadyRequest(
            pending.representation_id, "COMPAT_EMBEDDING", 1,
            "compat-embedding-v1", "RAW_VECTOR", payload,
        ),
    )


def _create_motif(connection, scope, idempotency, *, motif_id: str, domain_id: str, source, centroid, strength: float, last_active_ts: int):
    routing = scope.fabric_routing_scope
    state = MotifState(
        scope.memory_runtime_scope.semantic_scope_id, motif_id, domain_id,
        f"label {domain_id} {motif_id}", tuple(centroid), strength, .7, ("aria",),
        100, last_active_ts,
    )
    return NativeMotifService(connection).create_motif_with_member(
        idempotency_namespace_id=idempotency,
        idempotency_key=f"a2:motif:{scope.memory_runtime_scope.qualifier}:{motif_id}",
        motif_identity_namespace_id=routing.motif_identity_namespace_id,
        membership_identity_namespace_id=routing.membership_identity_namespace_id,
        motif_alias_namespace_id=routing.motif_alias_namespace_id,
        state=state, member_object_id=source.object_id,
    )


def _legacy_graph(tmp_path: Path, connection, scope, sources_and_vectors, embedder: _Embedder) -> MemoryGraph:
    graph = MemoryGraph(str(tmp_path / f"legacy-{scope.memory_runtime_scope.qualifier}"), embedder=embedder)
    graph.world._next_id = 0
    reader = NativeMemoryCompatibilityFacade(connection)
    runtime_scope = scope.memory_runtime_scope
    embedding_refs = {}
    for source, vector in sources_and_vectors:
        eid = graph.add_memory(
            summary=f"placeholder {source.eid}", embedding=np.asarray(vector, dtype=np.float32),
            mtype="episodic", strength=.7, confidence=.8, half_life_days=0.0,
            user_id="aria", step=12,
        )
        assert eid == source.eid
        embedding_refs[eid] = graph.entities[eid].payload["embedding_ref"]
        view = reader.get_memory_by_eid(
            legacy_source_namespace_id=runtime_scope.legacy_source_namespace_id, eid=eid,
        )
        payload = dict(view.payload)
        payload.update({
            "workspace_id": "orchard",
            "scope": "private" if runtime_scope.scope_kind == "PRIVATE_AGENT" else "shared",
            "agent_id": runtime_scope.agent_id or "aria",
            "domain_id": "personal" if runtime_scope.scope_kind == "PRIVATE_AGENT" else runtime_scope.domain_id,
        })
        graph.entities[eid].payload = payload
        graph._emb_by_eid[eid] = graph._normalize(np.asarray(vector, dtype=np.float32))
    graph._a3_fixture_embedding_refs = embedding_refs
    graph._rebuild_matrix()
    return graph


def _legacy_registry(graph: MemoryGraph, domain_id: str, motifs: list[tuple[str, int, tuple[float, ...], float, int]]) -> MotifRegistry:
    def entity_payload(eid: int):
        entity = graph.entities.get(eid)
        if entity is None:
            return None
        payload = dict(entity.payload)
        payload["embedding_ref"] = graph._a3_fixture_embedding_refs[eid]
        return payload

    registry = MotifRegistry(
        graph.data_dir, "orchard", domain_id, shard_reader=graph._shard_reader,
        entity_payload_fn=entity_payload,
    )
    registry.motifs = {
        motif_id: Motif(
            motif_id, domain_id, f"label {domain_id} {motif_id}", list(centroid), strength,
            [eid], ["aria"], .7, 100, last_active,
        )
        for motif_id, eid, centroid, strength, last_active in motifs
    }
    return registry


@pytest.fixture
def qualified_models(tmp_path: Path, monkeypatch):
    qualified = open_temporary_test_connection(tmp_path / "native-a2.db")
    connection = qualified.connection
    metadata = create_schema(connection)
    core_id = native_id_from_bytes(metadata.core_id)
    idempotency = _id()
    _namespace(connection, "idempotency_namespaces", idempotency, "a2:operations")
    private = _scope(connection, qualified.database_path, core_id, kind="PRIVATE_AGENT", qualifier="aria", idempotency=idempotency)
    research = _scope(connection, qualified.database_path, core_id, kind="SHARED_DOMAIN", qualifier="research", idempotency=idempotency)
    engineering = _scope(connection, qualified.database_path, core_id, kind="SHARED_DOMAIN", qualifier="engineering", idempotency=idempotency)
    archive = _scope(connection, qualified.database_path, core_id, kind="SHARED_DOMAIN", qualifier="archive", idempotency=idempotency)
    native_embedder = _Embedder()
    graphs: list[MemoryGraph] = []
    model = None
    try:
        private_rows = (
            _memory(connection, private, idempotency, "plain", (.2, .9, .0), memory_type="reference"),
            _memory(connection, private, idempotency, "reinforced", (1., .0, .0), half_life=1., reinforced=True),
            _memory(connection, private, idempotency, "pending", (.95, .05, .0), pending=True),
        )
        # Retain a real R1/READY predecessor, then make R2/READY current for
        # the same scoped EID.  The A2 lane must select only R2's vector and
        # payload; the differential graph below is built from that current R2.
        private_r2 = NativeMemoryCompatibilityFacade(connection).patch_memory_state(
            legacy_source_namespace_id=private.memory_runtime_scope.legacy_source_namespace_id,
            eid=private_rows[1][0].eid,
            patch={"reinforcement_count": 5, "fixture_tag": "reinforced-current"},
            idempotency_namespace_id=idempotency,
            idempotency_key="a2:private:reinforced:r2",
            expected_revision_id=private_rows[1][0].revision_id,
        )
        private_rows = (
            private_rows[0],
            (private_r2, _representation(connection, private_r2, idempotency, "aria:reinforced:r2", (1., .0, .0), publish=True)),
            private_rows[2],
        )
        research_rows = (
            _memory(connection, research, idempotency, "motifless", (.5, .5, .0)),
            _memory(connection, research, idempotency, "same", (1., .0, .0)),
            _memory(connection, research, idempotency, "hot", (.8, .2, .0), memory_type="reflection"),
        )
        engineering_rows = (
            _memory(connection, engineering, idempotency, "motifless", (.0, .7, .7), user_id="nox"),
            _memory(connection, engineering, idempotency, "same", (1., .0, .0)),
        )
        archive_rows = (
            _memory(connection, archive, idempotency, "bridge", (.0, .0, 1.)),
        )
        assert private_rows[1][0].eid == research_rows[1][0].eid == engineering_rows[1][0].eid == 1
        _create_motif(connection, private, idempotency, motif_id="private-anchor", domain_id="personal", source=private_rows[1][0], centroid=(1., 0., 0.), strength=.65, last_active_ts=110)
        _create_motif(connection, research, idempotency, motif_id="same-id", domain_id="research", source=research_rows[1][0], centroid=(1., 0., 0.), strength=.60, last_active_ts=100)
        _create_motif(connection, research, idempotency, motif_id="research-hot", domain_id="research", source=research_rows[2][0], centroid=(.8, .2, .0), strength=.60, last_active_ts=200)
        _create_motif(connection, engineering, idempotency, motif_id="same-id", domain_id="engineering", source=engineering_rows[1][0], centroid=(0., 1., 0.), strength=.60, last_active_ts=100)
        _create_motif(connection, archive, idempotency, motif_id="archive-id", domain_id="archive", source=archive_rows[0][0], centroid=(0., 0., 1.), strength=.55, last_active_ts=100)

        legacy_embedders = (_Embedder(), _Embedder(), _Embedder(), _Embedder())
        private_graph = _legacy_graph(tmp_path, connection, private, tuple((row[0], vector) for row, vector in zip(private_rows[:2], ((.2, .9, .0), (1., .0, .0)), strict=True)), legacy_embedders[0])
        research_graph = _legacy_graph(tmp_path, connection, research, tuple((row[0], vector) for row, vector in zip(research_rows, ((.5, .5, .0), (1., .0, .0), (.8, .2, .0)), strict=True)), legacy_embedders[1])
        engineering_graph = _legacy_graph(tmp_path, connection, engineering, tuple((row[0], vector) for row, vector in zip(engineering_rows, ((.0, .7, .7), (1., .0, .0)), strict=True)), legacy_embedders[2])
        archive_graph = _legacy_graph(tmp_path, connection, archive, tuple((row[0], vector) for row, vector in zip(archive_rows, ((.0, .0, 1.),), strict=True)), legacy_embedders[3])
        graphs.extend((private_graph, research_graph, engineering_graph, archive_graph))
        registries = {
            "personal": _legacy_registry(private_graph, "personal", [("private-anchor", 1, (1., 0., 0.), .65, 110)]),
            "research": _legacy_registry(research_graph, "research", [("same-id", 1, (1., 0., 0.), .60, 100), ("research-hot", 2, (.8, .2, .0), .60, 200)]),
            "engineering": _legacy_registry(engineering_graph, "engineering", [("same-id", 1, (0., 1., 0.), .60, 100)]),
            "archive": _legacy_registry(archive_graph, "archive", [("archive-id", 0, (0., 0., 1.), .55, 100)]),
        }
        legacy = LegacyQualifiedQueryReadModel(
            "orchard", private_graphs={"aria": private_graph},
            shared_graphs={"research": research_graph, "engineering": engineering_graph, "archive": archive_graph},
            motif_registries=registries, private_motif_domains={"aria": "personal"},
            shared_domain_order=("research", "engineering", "archive"),
        )
        descriptor = SimpleNamespace(payload={"lanes": [
            {"plan": {"scope_kind": "PRIVATE_AGENT", "agent_id": "aria", "motif_domain_id": "personal"}},
            {"plan": {"scope_kind": "SHARED_DOMAIN", "domain_id": "research", "motif_domain_id": "research"}},
            {"plan": {"scope_kind": "SHARED_DOMAIN", "domain_id": "engineering", "motif_domain_id": "engineering"}},
            {"plan": {"scope_kind": "SHARED_DOMAIN", "domain_id": "archive", "motif_domain_id": "archive"}},
        ]})
        recovered = _RecoveredRuntime("orchard", core_id, _lane(), (private, research, engineering, archive), descriptor)
        model = NativeQualifiedQueryReadModel(recovered, embedder=native_embedder)
        model._a3_fixture_runtime = recovered
        monkeypatch.setattr(memory_graph_module, "_now_ts", lambda: 100 + 86400)
        monkeypatch.setattr(vector_runtime_module.time, "time", lambda: float(100 + 86400))
        yield legacy, model, native_embedder, legacy_embedders
    finally:
        if model is not None:
            model.close()
        for graph in graphs:
            graph.close()
        qualified.close()


@pytest.mark.parametrize("kind,qualifier", (("private", "aria"), ("shared", "research"), ("shared", "engineering"), ("shared", "archive")))
def test_native_lane_search_is_legacy_shaped_and_qualified(qualified_models, kind: str, qualifier: str):
    legacy, native, native_embedder, legacy_embedders = qualified_models
    legacy_lane = legacy.private_lane("orchard", qualifier) if kind == "private" else legacy.shared_lane("orchard", qualifier)
    native_lane = native.private_lane("orchard", qualifier) if kind == "private" else native.shared_lane("orchard", qualifier)
    expected = legacy_lane.search("  query  ", top_k=8)
    actual = native_lane.search("  query  ", top_k=8)
    assert [item.as_legacy_hit() for item in actual] == [item.as_legacy_hit() for item in expected]
    assert native_embedder.calls == ["query"]
    assert legacy_embedders[("aria", "research", "engineering", "archive").index(qualifier)].calls == ["query"]
    assert all(item.memory_identity.scope == kind and item.memory_identity.qualifier == qualifier for item in actual)
    assert native_lane.search("   ") == ()
    assert native_embedder.calls == ["query"]


def test_filters_decay_namespaces_geometry_and_cold_rebuild(qualified_models):
    legacy, native, native_embedder, _legacy_embedders = qualified_models
    private_legacy = legacy.private_lane("orchard", "aria")
    private_native = native.private_lane("orchard", "aria")
    assert [item.as_legacy_hit() for item in private_native.search("q", top_k=1)] == [item.as_legacy_hit() for item in private_legacy.search("q", top_k=1)]
    assert [item.as_legacy_hit() for item in private_native.search("q", top_k=9, type_filter=["episodic"])] == [item.as_legacy_hit() for item in private_legacy.search("q", top_k=9, type_filter=["episodic"])]
    assert private_native.search("q", user_id="nox") == ()
    private_hits = private_native.search("q", min_score=.99)
    assert [item.memory_identity.eid for item in private_hits] == [1]
    assert private_hits[0].compatibility_hit["reinforcement_count"] == 5
    assert private_hits[0].compatibility_hit["srg"] == {"intensity": .31, "phase": "fixture"}
    assert private_hits[0].motif_ids == ("private-anchor",)

    research_hit = native.shared_lane("orchard", "research").search("q", top_k=9)[0]
    engineering_hit = native.shared_lane("orchard", "engineering").search("q", top_k=9)[0]
    assert research_hit.memory_identity.eid == engineering_hit.memory_identity.eid == 1
    assert research_hit.memory_identity != engineering_hit.memory_identity
    assert research_hit.motif_memberships[0].motif_id == engineering_hit.motif_memberships[0].motif_id == "same-id"
    assert research_hit.motif_memberships[0].domain_id == "research"
    assert engineering_hit.motif_memberships[0].domain_id == "engineering"
    assert research_hit.motif_memberships[0].semantic_scope_id != engineering_hit.motif_memberships[0].semantic_scope_id

    assert native.active_motifs("research", top_k=6) == legacy.active_motifs("research", top_k=6)
    assert native.domain_ids() == legacy.domain_ids() == ("research", "engineering", "archive")
    for domain in native.domain_ids():
        legacy_geometry = legacy.domain_geometry(domain)
        native_geometry = native.domain_geometry(domain)
        assert np.allclose(native_geometry.centroid, legacy_geometry.centroid)
        assert sorted((item.identity.domain_id, item.identity.motif_id) for item in native_geometry.motifs) == sorted((item.identity.domain_id, item.identity.motif_id) for item in legacy_geometry.motifs)

    before = [item.as_legacy_hit() for item in native.shared_lane("orchard", "research").search("q", top_k=9)]
    native.close()
    after = [item.as_legacy_hit() for item in native.shared_lane("orchard", "research").search("q", top_k=9)]
    assert after == before
    assert native_embedder.calls.count("q") >= 6
