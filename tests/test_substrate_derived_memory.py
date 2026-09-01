"""Focused A3D9 qualification for closed derived-memory mutation services."""
from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import inspect
import json
from pathlib import Path
import sqlite3

import numpy as np
import pytest

from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.compat import NativeMemoryCompatibilityFacade
from torment_service.substrate.derived_memory import (
    DerivedMemoryCreateKind,
    IdentityAnchorLifecyclePatch,
    NativeDerivedMemoryCreationRequest,
    NativeDerivedMemoryCreationService,
    NativeTypedMemorySuccessorRequest,
    NativeTypedMemorySuccessorService,
    derived_child_operation_key,
)
from torment_service.substrate.errors import SubstrateIdempotencyConflict
from torment_service.substrate.ids import generate_native_id, native_id_from_bytes, native_id_to_bytes
from torment_service.substrate.native_srg_runtime import SRGSuccessorMaterialization
from torment_service.substrate.native_world_runtime import WorldDiagnosticSuccessorMaterialization
from torment_service.substrate.object_revision_governance import NativeMemoryGovernanceFacts
from torment_service.substrate.provenance import NativeProvenanceRecord
from torment_service.substrate.representations import NativeRepresentationService
from torment_service.substrate.schema import create_schema
from torment_service.derived_memory_runtime import DerivedMemoryRuntimeContext
from torment_service.collective_models import MemoryGovernanceFlags
from torment_service.provenance_v1 import ProvenanceV1
from torment_service.substrate.fabric_native_routing import (
    NativeFabricMemoryRouter,
    NativeFabricRouteRequest,
    NativeFabricRoutingScope,
    prepare_native_fabric_routing_capability,
)
from torment_service.substrate.native_derived_memory_runtime import (
    NativeDerivedMemoryRuntime,
    NativeDerivedMemoryRuntimeConfiguration,
)
from torment_service.substrate.native_srg_runtime import NativeSRGProcessState
from torment_service.substrate.native_world_runtime import NativeWorldProcessState
from torment_service.substrate.runtime_binding import (
    NativeMemoryRuntimeScope,
    NativeRepresentationLane,
    prepare_native_memory_runtime_binding,
)


def _id():
    return generate_native_id()


def _database(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "a3d9.db")
    create_schema(qualified.connection)
    connection = qualified.connection
    values = {
        "qualified": qualified,
        "connection": connection,
        "identity": _id(),
        "scope": _id(),
        "idempotency": _id(),
        "alias": _id(),
    }
    connection.execute(
        "INSERT INTO identity_namespaces VALUES (?,?,0)",
        (native_id_to_bytes(values["identity"]), "a3d9-memory-identity"),
    )
    connection.execute(
        "INSERT INTO semantic_scopes VALUES (?,?,0)",
        (native_id_to_bytes(values["scope"]), "a3d9-private-scope"),
    )
    connection.execute(
        "INSERT INTO idempotency_namespaces VALUES (?,?)",
        (native_id_to_bytes(values["idempotency"]), "a3d9-idempotency"),
    )
    connection.execute(
        "INSERT INTO legacy_source_namespaces VALUES (?,?,0)",
        (native_id_to_bytes(values["alias"]), "a3d9-eid-alias"),
    )
    return values


def _request(values, *, kind=DerivedMemoryCreateKind.IDENTITY_ANCHOR_CREATE, key="anchor", vector=(2.0, 0.6, 0.0), **changes):
    values_map = {
        "operation_kind": kind,
        "legacy_source_namespace_id": values["alias"],
        "memory_identity_namespace_id": values["identity"],
        "semantic_scope_id": values["scope"],
        "idempotency_namespace_id": values["idempotency"],
        "idempotency_key": key,
        "summary": "Identity anchor: recurring theme 'qualification'. Examples: one | two",
        "strength": 0.87,
        "confidence": 0.85,
        "half_life_days": 3650.0,
        "user_id": "aria",
        "logical_step": 1000,
        "created_ts": 100,
        "payload_fields": {
            "workspace_id": "ws",
            "domain_id": "personal",
            "scope": "private",
            "agent_id": "aria",
            "anchor_for_motif": "motif_personal_0001",
            "anchor_member_count": 4,
            "anchor_label": "qualification",
            "anchor_affect_sensitive": False,
            "anchor_origin": "derived",
            "anchor_source": "motif_cluster",
            "seed_overlap_count": 2,
            "seed_aligned": True,
            "source_member_eids": [1, 2, 3, 4],
            "embedding_provider": "synthetic",
            "embedding_model": "synthetic-v1",
            "embedding_dim": 3,
            "embedding_checksum": "a" * 64,
            "seed_pos0": [1.0, 2.0, 3.0],
            "seed_v0": [0.1, 0.2, 0.3],
        },
        "provenance": NativeProvenanceRecord(
            "DERIVED_MEMORY", "derived", "system", "DERIVED", "KNOWN", 1, 2,
            "DERIVED_MEMORY", "a3d9 fixture",
        ),
        "governance": NativeMemoryGovernanceFacts(
            protected=False, non_shareable=True, collective_export_blocked=True,
            collective_reingest_blocked=True, decay_accelerated=False,
        ),
        "embedding": vector,
        "expected_dimension": 3,
    }
    values_map.update(changes)
    return NativeDerivedMemoryCreationRequest(**values_map)


def _counts(connection):
    tables = (
        "objects", "object_revisions", "legacy_object_aliases", "memory_runtime_enumeration_orders",
        "provenance_records", "object_revision_governance", "relationships", "relationship_revisions",
        "representations", "representation_payloads", "operations", "semantic_transitions",
        "object_revision_effects", "relationship_revision_effects",
    )
    return {
        table: connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
        for table in tables
    }


def _payload(connection, revision_id):
    row = connection.execute(
        "SELECT payload_text FROM object_revisions WHERE object_revision_id=?",
        (native_id_to_bytes(revision_id),),
    ).fetchone()
    return json.loads(row[0])


def test_derived_anchor_creation_is_one_no_motif_r1_with_qualified_representation(tmp_path: Path):
    values = _database(tmp_path)
    try:
        connection = values["connection"]
        request = _request(values)
        result = NativeDerivedMemoryCreationService(connection).create(request)
        payload = _payload(connection, result.source.memory_revision_id)
        assert result.source.memory_revision_ordinal == 1
        assert result.source.eid == 0
        assert payload["type"] == "identity_anchor"
        assert payload["memory_class"] == "core"
        assert payload["canon"] is False
        assert payload["half_life"] == 3650.0
        assert payload["pos"] == [1.0, 2.0, 3.0]
        assert payload["vel"] == [0.1, 0.2, 0.3]
        assert payload["vel0"] == [0.1, 0.2, 0.3]
        assert connection.execute("SELECT count(*) FROM objects WHERE object_kind='DERIVED_MOTIF'").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM relationships").fetchone()[0] == 0
        assert _counts(connection) == {
            "objects": 1, "object_revisions": 1, "legacy_object_aliases": 1,
            "memory_runtime_enumeration_orders": 1, "provenance_records": 1,
            "object_revision_governance": 1, "relationships": 0, "relationship_revisions": 0,
            "representations": 1, "representation_payloads": 1, "operations": 4,
            "semantic_transitions": 3, "object_revision_effects": 1,
            "relationship_revision_effects": 0,
        }
        raw = np.asarray(request.embedding, dtype=np.float32).tobytes(order="C")
        assert NativeRepresentationService(connection).read_representation_payload(result.representation_id) == raw
        assert connection.execute(
            "SELECT authority_category,lifecycle_state,lifecycle_authoritative,governance_state FROM object_revisions"
        ).fetchone() == ("NOT_APPLICABLE", "ORDINARY", 0, "DERIVED")
    finally:
        values["qualified"].close()


@pytest.mark.parametrize("stop", ("source", "pending", "expectation", "ready"))
def test_derived_creation_recovers_same_r1_and_representation_after_each_response_loss(tmp_path: Path, stop: str):
    values = _database(tmp_path)
    try:
        service = NativeDerivedMemoryCreationService(values["connection"])
        request = _request(values, key=f"loss-{stop}")
        with pytest.raises(RuntimeError, match="forced interruption"):
            service.create(request, _test_stop_after=stop)
        result = service.create(request)
        assert result.source.eid == 0
        assert _counts(values["connection"])["objects"] == 1
        assert _counts(values["connection"])["object_revisions"] == 1
        assert _counts(values["connection"])["memory_runtime_enumeration_orders"] == 1
        assert _counts(values["connection"])["representations"] == 1
        with pytest.raises(SubstrateIdempotencyConflict):
            service.create(replace(request, summary="different semantic input"))
    finally:
        values["qualified"].close()


def test_mood_drift_creation_is_closed_no_motif_and_uses_its_actual_raw_vector(tmp_path: Path):
    values = _database(tmp_path)
    try:
        request = _request(
            values, kind=DerivedMemoryCreateKind.MOOD_DRIFT_CREATE, key="mood",
            summary="Mood drift: from sad to angry.", strength=0.65, confidence=0.8625,
            half_life_days=60.0, vector=(1e-12, 3e-13, 0.0),
            payload_fields={
                "workspace_id": "ws", "domain_id": "personal", "scope": "private", "agent_id": "aria",
                "affect_tag": "angry", "affect_conf": 0.75, "mood_from": "sad", "mood_to": "angry",
                "affect_attribution": {"producer": "mood_drift_transition"},
                "embedding_provider": "synthetic", "embedding_model": "synthetic-v1",
                "embedding_dim": 3, "embedding_checksum": "b" * 64,
            },
        )
        result = NativeDerivedMemoryCreationService(values["connection"]).create(request)
        payload = _payload(values["connection"], result.source.memory_revision_id)
        assert payload["type"] == "mood_drift"
        assert payload["mood_from"] == "sad" and payload["mood_to"] == "angry"
        assert payload["affect_attribution"] == {"producer": "mood_drift_transition"}
        actual = NativeRepresentationService(values["connection"]).read_representation_payload(result.representation_id)
        assert actual == np.asarray((1e-12, 3e-13, 0.0), dtype=np.float32).tobytes(order="C")
        assert _counts(values["connection"])["relationships"] == 0
    finally:
        values["qualified"].close()


def test_anchor_lifecycle_successor_preserves_identity_order_embedding_and_typed_materializations(tmp_path: Path):
    values = _database(tmp_path)
    try:
        connection = values["connection"]
        created = NativeDerivedMemoryCreationService(connection).create(_request(values))
        srg = SRGSuccessorMaterialization.create(
            predecessor_revision_id=created.source.memory_revision_id,
            predecessor_revision_ordinal=1,
            effective_srg_state={"R": 0.42, "band": 1},
            effective_collision_report={"collision": True, "step": 1000},
        )
        world = WorldDiagnosticSuccessorMaterialization.create(
            predecessor_revision_id=created.source.memory_revision_id,
            predecessor_revision_ordinal=1,
            traj_label="orbital",
            traj_last_classify_step=1000,
        )
        request = NativeTypedMemorySuccessorRequest(
            legacy_source_namespace_id=values["alias"], eid=created.source.eid,
            expected_revision_id=created.source.memory_revision_id,
            expected_representation_id=created.representation_id,
            idempotency_namespace_id=values["idempotency"], idempotency_key="retire-anchor",
            expected_dimension=3,
            patch=IdentityAnchorLifecyclePatch.superseded(
                anchor_superseded_by=99, anchor_merged_into=99, last_reinforced=1001,
            ),
            srg_materialization=srg, world_diagnostic_materialization=world,
        )
        result = NativeTypedMemorySuccessorService(connection).publish_identity_anchor_lifecycle(request)
        old_payload = _payload(connection, created.source.memory_revision_id)
        new_payload = _payload(connection, result.source.revision_id)
        assert result.source.memory_object_id == created.source.memory_object_id
        assert result.source.eid == created.source.eid
        assert result.source.revision_ordinal == 2
        assert new_payload["anchor_retired"] is True
        assert new_payload["anchor_retired_reason"] == "superseded"
        assert new_payload["anchor_superseded_by"] == 99
        assert new_payload["anchor_merged_into"] == 99
        assert new_payload["last_reinforced"] == 1001
        assert new_payload["srg"] == {"R": 0.42, "band": 1}
        assert new_payload["traj_label"] == "orbital"
        assert old_payload["anchor_retired"] if "anchor_retired" in old_payload else False is False
        assert connection.execute("SELECT count(*) FROM memory_runtime_enumeration_orders").fetchone()[0] == 1
        e1 = NativeRepresentationService(connection).read_representation_payload(created.representation_id)
        e2 = NativeRepresentationService(connection).read_representation_payload(result.e2_representation_id)
        assert e2 == e1 and sha256(e2).digest() == sha256(e1).digest()
        assert connection.execute("SELECT count(*) FROM relationships").fetchone()[0] == 0
        # Same key recovers R2 rather than creating R3.
        recovered = NativeTypedMemorySuccessorService(connection).publish_identity_anchor_lifecycle(request)
        assert recovered.source.revision_id == result.source.revision_id
        assert connection.execute("SELECT count(*) FROM object_revisions").fetchone()[0] == 2
    finally:
        values["qualified"].close()


@pytest.mark.parametrize("stop", ("source", "pending", "expectation", "ready"))
def test_anchor_lifecycle_response_loss_never_creates_r3(tmp_path: Path, stop: str):
    values = _database(tmp_path)
    try:
        connection = values["connection"]
        created = NativeDerivedMemoryCreationService(connection).create(_request(values))
        request = NativeTypedMemorySuccessorRequest(
            legacy_source_namespace_id=values["alias"], eid=0,
            expected_revision_id=created.source.memory_revision_id,
            expected_representation_id=created.representation_id,
            idempotency_namespace_id=values["idempotency"], idempotency_key=f"loss-{stop}",
            expected_dimension=3,
            patch=IdentityAnchorLifecyclePatch.weak_old(anchor_superseded_by=9, last_reinforced=1200),
        )
        service = NativeTypedMemorySuccessorService(connection)
        with pytest.raises(RuntimeError, match="forced interruption"):
            service.publish_identity_anchor_lifecycle(request, _test_stop_after=stop)
        recovered = service.publish_identity_anchor_lifecycle(request)
        assert recovered.source.revision_ordinal == 2
        assert connection.execute("SELECT count(*) FROM object_revisions").fetchone()[0] == 2
        assert connection.execute("SELECT count(*) FROM memory_runtime_enumeration_orders").fetchone()[0] == 1
    finally:
        values["qualified"].close()


def test_typed_successor_does_not_expose_generic_payload_mutation_and_child_keys_are_stable():
    methods = inspect.signature(NativeTypedMemorySuccessorService.publish_identity_anchor_lifecycle).parameters
    assert "patch_payload" not in methods and "payload" not in methods and "update_payload" not in methods
    first = derived_child_operation_key(
        parent_native_operation_key="parent", operation_kind="IDENTITY_ANCHOR_CREATE",
        semantic_discriminator="motif_personal_0001:1000",
    )
    assert first == derived_child_operation_key(
        parent_native_operation_key="parent", operation_kind="IDENTITY_ANCHOR_CREATE",
        semantic_discriminator="motif_personal_0001:1000",
    )
    assert first != derived_child_operation_key(
        parent_native_operation_key="parent", operation_kind="MOOD_DRIFT_CREATE",
        semantic_discriminator="motif_personal_0001:1000",
    )
    with pytest.raises(ValueError):
        IdentityAnchorLifecyclePatch("arbitrary", 1, 1)


def _lane():
    return NativeRepresentationLane(
        provider="synthetic", model="synthetic-v1", dimension=3,
        representation_class="COMPAT_EMBEDDING", generation=1,
        derivation_contract_version="compat-embedding-v1", encoding_id="RAW_VECTOR", dtype="float32",
    )


def _qualified_runtime(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "a3d9-runtime.db")
    metadata = create_schema(qualified.connection)
    connection = qualified.connection
    memory_identity, semantic_scope, memory_alias = _id(), _id(), _id()
    motif_identity, membership_identity, motif_alias, idem = (_id() for _ in range(4))
    for value, label in (
        (memory_identity, "memory"), (motif_identity, "motif"), (membership_identity, "membership"),
    ):
        connection.execute("INSERT INTO identity_namespaces VALUES (?,?,0)", (native_id_to_bytes(value), label))
    connection.execute("INSERT INTO semantic_scopes VALUES (?,?,0)", (native_id_to_bytes(semantic_scope), "private"))
    for value, label in ((memory_alias, "memory-alias"), (motif_alias, "motif-alias")):
        connection.execute("INSERT INTO legacy_source_namespaces VALUES (?,?,0)", (native_id_to_bytes(value), label))
    connection.execute("INSERT INTO idempotency_namespaces VALUES (?,?)", (native_id_to_bytes(idem), "idem"))
    runtime_scope = NativeMemoryRuntimeScope(
        workspace_id="ws", scope_kind="PRIVATE_AGENT", legacy_source_namespace_id=memory_alias,
        identity_namespace_id=memory_identity, semantic_scope_id=semantic_scope, agent_id="aria",
    )
    routing_scope = NativeFabricRoutingScope(
        runtime_scope=runtime_scope, motif_alias_namespace_id=motif_alias,
        motif_identity_namespace_id=motif_identity, membership_identity_namespace_id=membership_identity,
        idempotency_namespace_id=idem,
    )
    binding = prepare_native_memory_runtime_binding(
        connection=connection, core_database_path=qualified.database_path,
        expected_core_id=native_id_from_bytes(metadata.core_id),
        scope_bindings=(runtime_scope,), representation_lane=_lane(),
    )
    capability = prepare_native_fabric_routing_capability(
        binding=binding, connection=connection, routing_scopes=(routing_scope,),
        expected_core_id=native_id_from_bytes(metadata.core_id),
    )
    return qualified, connection, capability, routing_scope


class _SideStore:
    def __init__(self):
        self.anchor = {"motifs": {}}
        self.affect = {"last_tag": None, "last_conf": 0.0, "last_step": -10**9, "drift_hist": []}
        self.events: list[tuple[str, int]] = []
        self.connection = None

    def _objects(self):
        return self.connection.execute("SELECT count(*) FROM objects").fetchone()[0]

    def load_anchor_state(self, **_kwargs):
        return json.loads(json.dumps(self.anchor))

    def save_anchor_state(self, *, state, **_kwargs):
        self.anchor = json.loads(json.dumps(state))
        self.events.append(("anchor-save", self._objects()))

    def load_affect_state(self, **_kwargs):
        return json.loads(json.dumps(self.affect))

    def save_affect_state(self, *, state, **_kwargs):
        self.affect = json.loads(json.dumps(state))
        self.events.append(("affect-save", self._objects()))


def _route_request(key: str, step: int):
    return NativeFabricRouteRequest(
        workspace_id="ws", scope="private", agent_id="aria", domain_id="personal",
        native_operation_key=key, embedder_lane=_lane(), summary=f"member {key}",
        memory_type="reflection", memory_class="core", strength=0.7, confidence=0.8,
        half_life_days=10.0, logical_step=step, created_ts=step, last_active_ts=step,
        last_reinforced_ts=step, incoming_embedding=(2.0, 0.6, 0.0),
        provenance=ProvenanceV1.for_user_ingest(step=step), governance=MemoryGovernanceFlags(),
        flexible_payload={"qualification": "a3d9"},
    )


def test_native_derived_runtime_uses_native_motifs_side_stores_and_fresh_world_state(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TORMENT_ID_ANCHOR_MIN_COUNT", "3")
    monkeypatch.setenv("TORMENT_ID_ANCHOR_MIN_GAP_STEPS", "50")
    monkeypatch.setenv("TORMENT_REINFORCE_SIM_THRESHOLD", "1.1")
    qualified, connection, capability, scope = _qualified_runtime(tmp_path)
    try:
        router = NativeFabricMemoryRouter(capability)
        for number in range(3):
            attempt = router.route(_route_request(f"ordinary-{number}", number + 1))
            assert attempt.result is not None and attempt.result.motifs == ("motif_personal_0001",)
        side = _SideStore()
        side.connection = connection
        configuration = NativeDerivedMemoryRuntimeConfiguration(
            workspace_id="ws", agent_id="aria", domain_id="personal",
            legacy_source_namespace_id=scope.runtime_scope.legacy_source_namespace_id,
            motif_alias_namespace_id=scope.motif_alias_namespace_id,
            memory_identity_namespace_id=scope.runtime_scope.identity_namespace_id,
            semantic_scope_id=scope.runtime_scope.semantic_scope_id,
            idempotency_namespace_id=scope.idempotency_namespace_id,
            parent_native_operation_key="derived-pass", expected_dimension=3,
            embed=lambda _text: np.asarray((2.0, 0.6, 0.0), dtype=np.float32),
            embedder_provider="synthetic", embedder_model="synthetic-v1", side_store=side,
            seed_eids=(0, 1), now_ts=lambda: 500,
        )
        runtime = router.bind_derived_memory_runtime(connection, configuration=configuration)
        context = DerivedMemoryRuntimeContext(
            "ws", "aria", "personal", "private", 1000, ("motif_personal_0001",), None, None,
        )
        anchor_eid = runtime.maybe_emit_identity_anchor(context)
        assert anchor_eid == 3
        anchor = NativeMemoryCompatibilityFacade(connection).get_memory_by_eid(
            legacy_source_namespace_id=scope.runtime_scope.legacy_source_namespace_id, eid=anchor_eid,
        )
        assert anchor.payload["source_member_eids"] == [0, 1, 2]
        assert anchor.payload["seed_overlap_count"] == 2
        assert connection.execute("SELECT count(*) FROM relationships").fetchone()[0] == 3
        assert side.events[-1] == ("anchor-save", 5)
        world = runtime._world.snapshot_for_testing()
        assert world.eids == (0, 1, 2, 3) and world.born_steps[-1] == 1000

        # A fourth native member qualifies a second anchor. The original
        # anchor becomes an R2 lifecycle successor without EID/order movement
        # and the A3D8 world entry retains its history carrier.
        assert router.route(_route_request("ordinary-3", 4)).result is not None
        first_anchor_history = runtime._world.snapshot_for_testing().history_lengths[3]
        second_anchor = runtime.maybe_emit_identity_anchor(
            DerivedMemoryRuntimeContext(
                "ws", "aria", "personal", "private", 1100, ("motif_personal_0001",), None, None,
            )
        )
        assert second_anchor == 5
        retired = NativeMemoryCompatibilityFacade(connection).get_memory_by_eid(
            legacy_source_namespace_id=scope.runtime_scope.legacy_source_namespace_id, eid=anchor_eid,
        )
        assert retired.revision_ordinal == 2
        assert retired.payload["anchor_retired_reason"] == "superseded"
        assert connection.execute("SELECT count(*) FROM memory_runtime_enumeration_orders").fetchone()[0] == 6
        world_successor = runtime._world.snapshot_for_testing()
        assert world_successor.eids == (0, 1, 2, 3, 4, 5)
        assert world_successor.history_lengths[3] == first_anchor_history

        # First affect writes side state with no row; the separated transition
        # writes it before source creation and then again with drift history.
        assert runtime.maybe_emit_mood_drift(
            DerivedMemoryRuntimeContext("ws", "aria", "personal", "private", 1010, (), "sad", 0.75)
        ) is None
        assert side.events[-1] == ("affect-save", 7)
        mood_eid = runtime.maybe_emit_mood_drift(
            DerivedMemoryRuntimeContext("ws", "aria", "personal", "private", 1140, (), "angry", 0.75)
        )
        assert mood_eid == 6
        assert side.events[-2:] == [("affect-save", 7), ("affect-save", 8)]
        mood = NativeMemoryCompatibilityFacade(connection).get_memory_by_eid(
            legacy_source_namespace_id=scope.runtime_scope.legacy_source_namespace_id, eid=mood_eid,
        )
        assert (mood.payload["mood_from"], mood.payload["mood_to"]) == ("sad", "angry")
        assert side.affect["drift_hist"] == [{"from": "sad", "to": "angry", "step": 1140, "conf": 0.75}]
        world_after = runtime._world.snapshot_for_testing()
        assert world_after.eids == (0, 1, 2, 3, 4, 5, 6) and world_after.born_steps[-1] == 1140
    finally:
        qualified.close()


def test_native_derived_runtime_shared_trigger_skips_anchor_sql_and_side_stores(tmp_path: Path):
    """D0: shared triggers cannot fabricate private anchor provenance."""
    qualified, connection, capability, scope = _qualified_runtime(tmp_path)
    try:
        runtime = NativeFabricMemoryRouter(capability).bind_derived_memory_runtime(
            connection,
            configuration=NativeDerivedMemoryRuntimeConfiguration(
                workspace_id="ws", agent_id="aria", domain_id="personal",
                legacy_source_namespace_id=scope.runtime_scope.legacy_source_namespace_id,
                motif_alias_namespace_id=scope.motif_alias_namespace_id,
                memory_identity_namespace_id=scope.runtime_scope.identity_namespace_id,
                semantic_scope_id=scope.runtime_scope.semantic_scope_id,
                idempotency_namespace_id=scope.idempotency_namespace_id,
                parent_native_operation_key="d0-shared-trigger", expected_dimension=3,
                embed=lambda _text: np.asarray((2.0, 0.6, 0.0), dtype=np.float32),
                embedder_provider="synthetic", embedder_model="synthetic-v1", side_store=_SideStore(),
                now_ts=lambda: 500,
            ),
        )
        context = DerivedMemoryRuntimeContext(
            "ws", "aria", "personal", "shared", 1000, ("motif_personal_0001",), None, None,
        )
        before_changes = connection.total_changes
        forbidden_actions = {
            sqlite3.SQLITE_READ, sqlite3.SQLITE_INSERT, sqlite3.SQLITE_UPDATE, sqlite3.SQLITE_DELETE,
        }

        def reject_anchor_sql(action, _arg1, _arg2, _database, _trigger):
            if action in forbidden_actions:
                raise AssertionError("shared anchor no-op touched SQLite")
            return sqlite3.SQLITE_OK

        connection.set_authorizer(reject_anchor_sql)
        try:
            assert runtime.maybe_emit_identity_anchor(context) is None
            assert runtime.refine_identity_anchors(context) is None
        finally:
            connection.set_authorizer(None)
        assert connection.total_changes == before_changes
    finally:
        qualified.close()
