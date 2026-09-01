"""D6 qualification for the disabled shared compression/deep-memory boundary."""
from __future__ import annotations

from dataclasses import replace
import logging
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from torment_service.collective_models import MemoryGovernanceFlags
from torment_service.post_write_runtime import FabricPostWriteContext, PostWriteStorageOutcome
from torment_service.provenance_v1 import ProvenanceV1
from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.errors import SubstrateConfigurationError
from torment_service.substrate.fabric_native_routing import (
    NativeFabricMemoryRouter,
    NativeFabricRouteRequest,
    NativeFabricRoutingScope,
    prepare_native_fabric_routing_capability,
)
from torment_service.substrate.ids import generate_native_id, native_id_from_bytes, native_id_to_bytes
from torment_service.substrate.native_post_write_runtime import (
    NativePostWriteExternalDependencies,
    NativePostWriteQualificationConfiguration,
    NativePostWriteQualificationProfile,
    NativePostWriteRouteWitness,
    prepare_native_fabric_post_write_adapter,
)
from torment_service.substrate.runtime_binding import (
    NativeMemoryRuntimeScope,
    NativeRepresentationLane,
    prepare_native_memory_runtime_binding,
)
from torment_service.substrate.schema import create_schema


def _id():
    return generate_native_id()


def _lane() -> NativeRepresentationLane:
    return NativeRepresentationLane(
        "synthetic", "synthetic-v1", 3, "COMPAT_EMBEDDING", 1,
        "compat-embedding-v1", "RAW_VECTOR", "float32",
    )


def _shared_scope(connection) -> NativeFabricRoutingScope:
    memory_identity, semantic_scope, memory_alias = _id(), _id(), _id()
    motif_identity, membership_identity, motif_alias, idempotency = (_id() for _ in range(4))
    for value, label in (
        (memory_identity, "memory"), (motif_identity, "motif"), (membership_identity, "membership"),
    ):
        connection.execute(
            "INSERT INTO identity_namespaces VALUES (?,?,0)",
            (native_id_to_bytes(value), f"d6:{label}"),
        )
    connection.execute(
        "INSERT INTO semantic_scopes VALUES (?,?,0)",
        (native_id_to_bytes(semantic_scope), "d6:semantic"),
    )
    for value, label in ((memory_alias, "memory-alias"), (motif_alias, "motif-alias")):
        connection.execute(
            "INSERT INTO legacy_source_namespaces VALUES (?,?,0)",
            (native_id_to_bytes(value), f"d6:{label}"),
        )
    connection.execute(
        "INSERT INTO idempotency_namespaces VALUES (?,?)", (native_id_to_bytes(idempotency), "d6"))
    runtime_scope = NativeMemoryRuntimeScope(
        workspace_id="ws", scope_kind="SHARED_DOMAIN", legacy_source_namespace_id=memory_alias,
        identity_namespace_id=memory_identity, semantic_scope_id=semantic_scope, domain_id="research",
    )
    return NativeFabricRoutingScope(
        runtime_scope=runtime_scope, motif_alias_namespace_id=motif_alias,
        motif_identity_namespace_id=motif_identity, membership_identity_namespace_id=membership_identity,
        idempotency_namespace_id=idempotency,
    )


def _prepared(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "d6.db")
    metadata = create_schema(qualified.connection)
    scope = _shared_scope(qualified.connection)
    binding = prepare_native_memory_runtime_binding(
        connection=qualified.connection, core_database_path=qualified.database_path,
        expected_core_id=native_id_from_bytes(metadata.core_id), scope_bindings=(scope.runtime_scope,),
        representation_lane=_lane(),
    )
    capability = prepare_native_fabric_routing_capability(
        binding=binding, connection=qualified.connection, routing_scopes=(scope,),
        expected_core_id=native_id_from_bytes(metadata.core_id),
    )
    return qualified, qualified.connection, capability, scope


class _Owner:
    def __init__(self, enabled: bool = False) -> None:
        self._compress_enable = enabled
        self._log = logging.getLogger("d6.shared.owner")
        self.forbidden_reads: list[str] = []

    def __getattr__(self, name: str):
        self.forbidden_reads.append(name)
        raise AssertionError(f"D6 disabled shared profile accessed compression owner {name}")


def _configuration(scope: NativeFabricRoutingScope, owner: _Owner):
    return NativePostWriteQualificationConfiguration(
        routing_scope=scope,
        profile=NativePostWriteQualificationProfile.core_staging_with_shared_compression_disabled_noop(),
        external=NativePostWriteExternalDependencies(
            owner=owner, workspace=SimpleNamespace(domain_policies={"research": {}}),
            identity=SimpleNamespace(seed={}), agent_key="ws/aria",
            detect_canon_conflict=lambda *_args: (False, 0.0, "unused"),
            proposal_allowed=lambda *_args, **_kwargs: False,
            hivemind_log=logging.getLogger("d6.shared.hivemind"),
        ),
        derived_runtime_template=None, motif_suggestion_maintenance_required=False,
        persistent_trajectory_evidence_required=False, checkpoint_snapshots_required=False,
        bridge_suggestions_required=False, deep_memory_required=False,
        shared_compression_disabled_noop_required=True,
    )


def _request(key: str = "D6:SOURCE") -> NativeFabricRouteRequest:
    return NativeFabricRouteRequest(
        workspace_id="ws", scope="shared", agent_id="aria", domain_id="research",
        native_operation_key=key, embedder_lane=_lane(), summary="compression boundary source",
        memory_type="reflection", memory_class="core", strength=.8, confidence=.9,
        half_life_days=20., logical_step=1, created_ts=1, last_active_ts=1, last_reinforced_ts=1,
        incoming_embedding=(.2, .8, .1), provenance=ProvenanceV1.for_user_ingest(step=1),
        governance=MemoryGovernanceFlags(), flexible_payload={},
    )


def _context(result, request: NativeFabricRouteRequest) -> FabricPostWriteContext:
    return FabricPostWriteContext.make(
        workspace_id="ws", agent_id="aria", scope="shared", chosen_domain="research", step=1,
        storage_outcome=PostWriteStorageOutcome.CREATED_NEW, stored=result.stored, eid=result.eid,
        created_motif=result.motifs[0], motif_ids=result.motifs, half_life_days=request.half_life_days,
        summary=request.summary, embedding=np.asarray(request.incoming_embedding, dtype=np.float32),
        memory_class=request.memory_class, memory_type=request.memory_type, strength=request.strength,
        confidence=request.confidence, promotion_score=0., stability_delta=0., tri_mod={}, debug={},
        srg_state=None, phase_durations={}, state_symbol=None, affect_tag=None, affect_conf=None,
        skip_packet_emission=True,
    )


def _no_write_context() -> FabricPostWriteContext:
    return FabricPostWriteContext.make(
        workspace_id="ws", agent_id="aria", scope="shared", chosen_domain="research", step=2,
        storage_outcome=PostWriteStorageOutcome.NO_WRITE, stored=False, eid=None, created_motif=None,
        motif_ids=(), half_life_days=None, summary="no write", embedding=np.zeros(3, dtype=np.float32),
        memory_class="core", memory_type="reflection", strength=0., confidence=0.,
        promotion_score=0., stability_delta=0., tri_mod={}, debug={}, srg_state=None,
        phase_durations={}, state_symbol=None, affect_tag=None, affect_conf=None, skip_packet_emission=True,
    )


def _counts(connection) -> tuple[int, ...]:
    tables = (
        "objects", "object_revisions", "relationships", "relationship_revisions", "representations",
        "representation_payloads", "operations", "semantic_transitions", "provenance_records",
        "object_revision_governance", "memory_runtime_enumeration_orders",
    )
    return tuple(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in tables)


def test_d6_disabled_shared_route_is_a_real_noop_without_native_or_external_reads(tmp_path: Path, monkeypatch):
    qualified, connection, capability, scope = _prepared(tmp_path)
    try:
        request = _request()
        result = NativeFabricMemoryRouter(capability).route(request).result
        assert result is not None
        owner = _Owner(enabled=False)
        adapter = prepare_native_fabric_post_write_adapter(
            capability=capability, configuration=_configuration(scope, owner),
        )
        before = _counts(connection)
        import torment_service.substrate.native_post_write_runtime as post_write_runtime

        monkeypatch.setattr(
            post_write_runtime,
            "open_existing_native_core_connection",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("D6 opened native core")),
        )
        adapter.run(
            _context(result, request),
            route_witness=NativePostWriteRouteWitness(result, request.native_operation_key),
        )
        adapter.run(_no_write_context())
        assert _counts(connection) == before
        assert owner.forbidden_reads == []
    finally:
        qualified.close()


def test_d6_refuses_enabled_compression_during_preparation_before_any_effect(tmp_path: Path):
    qualified, connection, capability, scope = _prepared(tmp_path)
    try:
        owner = _Owner(enabled=True)
        before = _counts(connection)
        with pytest.raises(SubstrateConfigurationError, match="TORMENT_COMPRESS_ENABLE=false"):
            prepare_native_fabric_post_write_adapter(
                capability=capability, configuration=_configuration(scope, owner),
            )
        assert _counts(connection) == before
        assert owner.forbidden_reads == []
    finally:
        qualified.close()


def test_d6_rechecks_live_disable_flag_before_the_noop(tmp_path: Path, monkeypatch):
    qualified, connection, capability, scope = _prepared(tmp_path)
    try:
        request = _request("D6:DRIFT")
        result = NativeFabricMemoryRouter(capability).route(request).result
        assert result is not None
        owner = _Owner(enabled=False)
        adapter = prepare_native_fabric_post_write_adapter(
            capability=capability, configuration=_configuration(scope, owner),
        )
        owner._compress_enable = True
        before = _counts(connection)
        import torment_service.substrate.native_post_write_runtime as post_write_runtime

        monkeypatch.setattr(
            post_write_runtime,
            "open_existing_native_core_connection",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("D6 opened native core")),
        )
        with pytest.raises(SubstrateConfigurationError, match="TORMENT_COMPRESS_ENABLE=false"):
            adapter.run(_context(result, request))
        assert _counts(connection) == before
        assert owner.forbidden_reads == []
    finally:
        qualified.close()


def test_d6_requires_its_explicit_profile_and_isolated_consumer_slot(tmp_path: Path):
    qualified, _connection, capability, scope = _prepared(tmp_path)
    try:
        owner = _Owner()
        configuration = _configuration(scope, owner)
        with pytest.raises(SubstrateConfigurationError, match="does not qualify shared compression disabled no-op"):
            prepare_native_fabric_post_write_adapter(
                capability=capability,
                configuration=replace(
                    configuration, profile=NativePostWriteQualificationProfile.core_staging(),
                ),
            )
        with pytest.raises(SubstrateConfigurationError, match="prepared separately"):
            prepare_native_fabric_post_write_adapter(
                capability=capability,
                configuration=replace(configuration, shared_checkpoint_snapshot_required=True),
            )
    finally:
        qualified.close()


def test_d6_never_claims_enabled_compression_or_deep_memory(tmp_path: Path):
    qualified, _connection, capability, scope = _prepared(tmp_path)
    try:
        configuration = _configuration(scope, _Owner())
        with pytest.raises(SubstrateConfigurationError, match="enabled compression"):
            prepare_native_fabric_post_write_adapter(
                capability=capability,
                configuration=replace(
                    configuration,
                    profile=replace(configuration.profile, compression=configuration.profile.shared_compression_disabled_noop),
                ),
            )
        with pytest.raises(SubstrateConfigurationError, match="deep-memory export"):
            prepare_native_fabric_post_write_adapter(
                capability=capability,
                configuration=replace(
                    configuration,
                    profile=replace(configuration.profile, deep_memory=configuration.profile.shared_compression_disabled_noop),
                ),
            )
    finally:
        qualified.close()
