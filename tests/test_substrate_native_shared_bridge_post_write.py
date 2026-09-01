"""B1 qualification for the bridge-only shared native post-write consumer."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import replace
import logging
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from torment_service.bridges import Bridge, BridgeRegistry
from torment_service.collective_models import MemoryGovernanceFlags
from torment_service.motif_geometry_port import NativeMotifGeometryAdapter
from torment_service.post_write_runtime import (
    FabricPostWriteContext,
    PostWriteStorageOutcome,
    run_bridge_suggestions,
)
from torment_service.provenance_v1 import ProvenanceV1
from torment_service.substrate.connection import open_existing_native_core_connection, open_temporary_test_connection
from torment_service.substrate.errors import SubstrateConfigurationError, SubstrateInvariantViolation
from torment_service.substrate.fabric_native_routing import (
    NativeFabricMemoryRouter,
    NativeFabricRouteRequest,
    NativeFabricRoutingScope,
    prepare_native_fabric_routing_capability,
)
from torment_service.substrate.ids import generate_native_id, native_id_from_bytes, native_id_to_bytes
from torment_service.substrate.motif_runtime_reader import NativeMotifRuntimeReader
from torment_service.substrate.native_motif_merge_runtime import NativeMotifMergeRuntime
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


def _scope_rows(connection, domain_id: str) -> NativeFabricRoutingScope:
    memory_identity, semantic_scope, memory_alias = _id(), _id(), _id()
    motif_identity, membership_identity, motif_alias, idempotency = (_id() for _ in range(4))
    for value, label in (
        (memory_identity, "memory-identity"), (motif_identity, "motif-identity"),
        (membership_identity, "membership-identity"),
    ):
        connection.execute(
            "INSERT INTO identity_namespaces VALUES (?,?,0)",
            (native_id_to_bytes(value), f"b1:{domain_id}:{label}"),
        )
    connection.execute(
        "INSERT INTO semantic_scopes VALUES (?,?,0)",
        (native_id_to_bytes(semantic_scope), f"b1:{domain_id}:semantic"),
    )
    for value, label in ((memory_alias, "memory-alias"), (motif_alias, "motif-alias")):
        connection.execute(
            "INSERT INTO legacy_source_namespaces VALUES (?,?,0)",
            (native_id_to_bytes(value), f"b1:{domain_id}:{label}"),
        )
    connection.execute(
        "INSERT INTO idempotency_namespaces VALUES (?,?)",
        (native_id_to_bytes(idempotency), f"b1:{domain_id}:idempotency"),
    )
    runtime_scope = NativeMemoryRuntimeScope(
        workspace_id="b1-workspace", scope_kind="SHARED_DOMAIN",
        legacy_source_namespace_id=memory_alias, identity_namespace_id=memory_identity,
        semantic_scope_id=semantic_scope, domain_id=domain_id,
    )
    return NativeFabricRoutingScope(
        runtime_scope=runtime_scope, motif_alias_namespace_id=motif_alias,
        motif_identity_namespace_id=motif_identity, membership_identity_namespace_id=membership_identity,
        idempotency_namespace_id=idempotency,
    )


class _RecoveredSharedScope:
    """Test-only façade exposing existing native readers through the E4C port shape."""

    def __init__(self, core_path: Path, scope: NativeFabricRoutingScope) -> None:
        self.memory_runtime_scope = scope.runtime_scope
        self.fabric_routing_scope = scope
        self._core_path = core_path

    @contextmanager
    def open_readers(self):
        with open_existing_native_core_connection(self._core_path) as qualified:
            yield SimpleNamespace(motifs=NativeMotifRuntimeReader(qualified.connection))


class _RecoveredSharedRuntime:
    def __init__(self, core_path: Path, scopes: dict[str, NativeFabricRoutingScope]) -> None:
        self._scopes = {
            domain: _RecoveredSharedScope(core_path, scope)
            for domain, scope in scopes.items()
        }

    def lookup_shared(self, domain_id: str) -> _RecoveredSharedScope:
        try:
            return self._scopes[domain_id]
        except KeyError as exc:
            raise KeyError(f"unadmitted native shared domain {domain_id!r}") from exc


class _ForbiddenLegacyMotifs:
    def __getattr__(self, _name):
        raise AssertionError("B1 native bridge consulted stale legacy motif state")


def _prepared(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "b1-shared-bridge.db")
    metadata = create_schema(qualified.connection)
    connection = qualified.connection
    scopes = {domain: _scope_rows(connection, domain) for domain in ("research", "engineering", "creative", "archive")}
    binding = prepare_native_memory_runtime_binding(
        connection=connection, core_database_path=qualified.database_path,
        expected_core_id=native_id_from_bytes(metadata.core_id),
        scope_bindings=tuple(scope.runtime_scope for scope in scopes.values()),
        representation_lane=_lane(),
    )
    capability = prepare_native_fabric_routing_capability(
        binding=binding, connection=connection, routing_scopes=tuple(scopes.values()),
        expected_core_id=native_id_from_bytes(metadata.core_id),
    )
    router = NativeFabricMemoryRouter(capability)
    results = {}
    for ordinal, (domain, vector) in enumerate((
        ("research", (1.0, 0.0, 0.0)),
        ("engineering", (1.0, 0.0, 0.0)),
        ("creative", (0.96, 0.28, 0.0)),
        ("archive", (0.0, 1.0, 0.0)),
    ), start=1):
        request = _route_request(domain, f"B1:SEED:{domain}", ordinal, vector)
        result = router.route(request).result
        assert result is not None
        results[domain] = (request, result)
    retired_source = _route_request("research", "B1:SEED:research-drop", 5, (0.0, 1.0, 0.0))
    retired_result = router.route(retired_source).result
    assert retired_result is not None
    merged = NativeMotifMergeRuntime(
        connection, routing_scope=scopes["research"], domain_id="research",
        process_order=capability.process_order,
    ).merge_suggestion({
        "suggestion_id": "B1:RETIRED:research",
        "a": results["research"][1].motifs[0],
        "b": retired_result.motifs[0],
        "created_ts": 6,
    }, note="B1 retired-endpoint fixture")
    assert merged is not None
    recovered = _RecoveredSharedRuntime(qualified.database_path, scopes)
    geometry = NativeMotifGeometryAdapter(
        recovered, domain_ids=("research", "engineering", "creative", "archive"), expected_dimension=3,
    )
    return qualified, connection, capability, scopes, results, geometry, merged.drop_runtime_motif_id


def _route_request(domain_id: str, key: str, step: int, vector) -> NativeFabricRouteRequest:
    return NativeFabricRouteRequest(
        workspace_id="b1-workspace", scope="shared", agent_id="aria", domain_id=domain_id,
        native_operation_key=key, embedder_lane=_lane(), summary=f"B1 {domain_id} {key}",
        memory_type="reflection", memory_class="core", strength=.8, confidence=.9,
        half_life_days=20.0, logical_step=step, created_ts=step, last_active_ts=step,
        last_reinforced_ts=step, incoming_embedding=vector,
        provenance=ProvenanceV1.for_user_ingest(step=step), governance=MemoryGovernanceFlags(),
        flexible_payload={"b1": True},
    )


def _context(result, request: NativeFabricRouteRequest, *, tri_mod=None) -> FabricPostWriteContext:
    return FabricPostWriteContext.make(
        workspace_id=request.workspace_id, agent_id=request.agent_id, scope="shared",
        chosen_domain=request.domain_id, step=request.logical_step,
        storage_outcome=PostWriteStorageOutcome.CREATED_NEW, stored=result.stored, eid=result.eid,
        created_motif=result.motifs[0], motif_ids=result.motifs, half_life_days=request.half_life_days,
        summary=request.summary, embedding=np.asarray(request.incoming_embedding, dtype=np.float32),
        memory_class=request.memory_class, memory_type=request.memory_type, strength=request.strength,
        confidence=request.confidence, promotion_score=.5, stability_delta=.0,
        tri_mod=tri_mod or {}, debug={}, srg_state=None, phase_durations={}, state_symbol=None,
        affect_tag=None, affect_conf=None, skip_packet_emission=False,
    )


def _configuration(scope, *, workspace, geometry, random_chance, required=True, profile=None):
    return NativePostWriteQualificationConfiguration(
        routing_scope=scope,
        profile=profile or NativePostWriteQualificationProfile.core_staging_with_shared_bridge_suggestion(),
        external=NativePostWriteExternalDependencies(
            owner=SimpleNamespace(), workspace=workspace, identity=SimpleNamespace(), agent_key="aria",
            detect_canon_conflict=lambda *_args: (False, 0.0, "unused"),
            proposal_allowed=lambda *_args, **_kwargs: False,
            hivemind_log=logging.getLogger("b1.shared.bridge"),
            shared_bridge_geometry=geometry, random_chance=random_chance,
        ),
        derived_runtime_template=None, motif_suggestion_maintenance_required=False,
        persistent_trajectory_evidence_required=False, checkpoint_snapshots_required=False,
        bridge_suggestions_required=False, deep_memory_required=False,
        shared_bridge_suggestions_required=required,
    )


def _native_counts(connection):
    return tuple(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in (
        "objects", "object_revisions", "relationships", "relationship_revisions",
        "operations", "semantic_transitions", "representations", "representation_payloads",
    ))


def _bridge_rows(registry: BridgeRegistry):
    return [
        (bridge.from_domain, bridge.from_motif, bridge.to_domain, bridge.to_motif,
         bridge.confidence, bridge.status)
        for bridge in registry.bridges
    ]


def test_b1_shared_bridge_post_write_is_explicit_native_geometry_only_and_read_only(tmp_path: Path):
    qualified, connection, capability, scopes, results, geometry, retired_motif_id = _prepared(tmp_path)
    try:
        bridge_store = BridgeRegistry(str(tmp_path / "bridge-store"), "b1-workspace")
        research_id = geometry.list_motifs("research")[0].runtime_motif_id
        engineering_id = geometry.list_motifs("engineering")[0].runtime_motif_id
        bridge_store.bridges.append(Bridge(
            "research", research_id, "engineering", engineering_id, 1.0, 1,
        ))
        bridge_store.save()
        workspace = SimpleNamespace(bridges=bridge_store, motif_regs=_ForbiddenLegacyMotifs())
        attempts: list[tuple[object, float, int]] = []
        original_suggest = bridge_store.suggest

        def record_suggest(input_geometry, *, sim_threshold, max_new):
            attempts.append((input_geometry, sim_threshold, max_new))
            return original_suggest(input_geometry, sim_threshold=sim_threshold, max_new=max_new)

        bridge_store.suggest = record_suggest  # type: ignore[method-assign]
        request, result = results["research"]
        context = _context(result, request, tri_mod={"bridge_p": .08, "bridge_sim": .86, "tearing_risk": .0})
        probabilities: list[float] = []
        gate = lambda probability: probabilities.append(probability) or False
        configuration = _configuration(scopes["research"], workspace=workspace, geometry=geometry, random_chance=gate)
        adapter = prepare_native_fabric_post_write_adapter(capability=capability, configuration=configuration)
        before_native = _native_counts(connection)
        before_motifs = {domain: tuple(item.runtime_motif_id for item in geometry.list_motifs(domain)) for domain in geometry.domain_ids()}
        assert retired_motif_id not in before_motifs["research"]
        adapter.run(context, route_witness=NativePostWriteRouteWitness(result, request.native_operation_key))
        assert probabilities == [.08]
        assert attempts == []
        assert _native_counts(connection) == before_native

        configuration = replace(
            configuration,
            external=replace(configuration.external, random_chance=lambda _probability: True),
        )
        adapter = prepare_native_fabric_post_write_adapter(capability=capability, configuration=configuration)
        adapter.run(context, route_witness=NativePostWriteRouteWitness(result, request.native_operation_key))
        assert len(attempts) == 1
        assert attempts[0] == (geometry, pytest.approx(.86), 5)
        rows_after_first = _bridge_rows(bridge_store)
        assert ("research", research_id, "engineering", engineering_id, 1.0, "suggested") in rows_after_first
        assert len(rows_after_first) > 1  # at least one non-duplicate eligible pair was suggested.
        assert all("archive" not in (from_domain, to_domain) for from_domain, _, to_domain, _, _, _ in rows_after_first)
        assert all("motif" in from_motif and "motif" in to_motif for _, from_motif, _, to_motif, _, _ in rows_after_first)
        assert all(retired_motif_id not in endpoint for row in rows_after_first for endpoint in (row[1], row[3]))
        assert _native_counts(connection) == before_native
        assert {domain: tuple(item.runtime_motif_id for item in geometry.list_motifs(domain)) for domain in geometry.domain_ids()} == before_motifs

        adapter.run(context, route_witness=NativePostWriteRouteWitness(result, request.native_operation_key))
        assert len(attempts) == 2  # one decision invocation per post-write call
        assert _bridge_rows(bridge_store) == rows_after_first  # BridgeRegistry owns duplicate suppression.
        with pytest.raises(KeyError, match="unadmitted native domain"):
            geometry.list_motifs("unadmitted")
        assert not hasattr(adapter, "vector_runtime")

        with pytest.raises(SubstrateConfigurationError, match="no qualified consumer"):
            prepare_native_fabric_post_write_adapter(
                capability=capability,
                configuration=replace(configuration, shared_bridge_suggestions_required=False),
            )
        with pytest.raises(SubstrateConfigurationError, match="does not qualify"):
            prepare_native_fabric_post_write_adapter(
                capability=capability,
                configuration=replace(
                    configuration, profile=NativePostWriteQualificationProfile.core_staging(),
                ),
            )
        incomplete_geometry = NativeMotifGeometryAdapter(
            _RecoveredSharedRuntime(capability.core_database_path, scopes),
            domain_ids=("research", "engineering", "creative"), expected_dimension=3,
        )
        with pytest.raises(SubstrateConfigurationError, match="does not cover exactly"):
            prepare_native_fabric_post_write_adapter(
                capability=capability,
                configuration=replace(
                    configuration,
                    external=replace(configuration.external, shared_bridge_geometry=incomplete_geometry),
                ),
            )
        with pytest.raises(SubstrateInvariantViolation, match="does not match claimed native scope"):
            adapter.run(
                replace(context, scope="private"),
                route_witness=NativePostWriteRouteWitness(result, request.native_operation_key),
            )

        # The neutral geometry opens current SQLite readers itself.  After the
        # original core handle is closed, a cold B1 retry reads those same
        # current motifs and the external BridgeRegistry deduplicates the
        # existing endpoint pairs without any legacy motifs.json authority.
        qualified.close()
        cold_geometry = NativeMotifGeometryAdapter(
            _RecoveredSharedRuntime(
                capability.core_database_path, scopes,
            ),
            domain_ids=("research", "engineering", "creative", "archive"), expected_dimension=3,
        )
        cold_registry = BridgeRegistry(str(tmp_path / "bridge-store"), "b1-workspace")
        cold_rows_before = _bridge_rows(cold_registry)
        cold_workspace = SimpleNamespace(bridges=cold_registry, motif_regs=_ForbiddenLegacyMotifs())
        cold_adapter = prepare_native_fabric_post_write_adapter(
            capability=capability,
            configuration=_configuration(
                scopes["research"], workspace=cold_workspace, geometry=cold_geometry,
                random_chance=lambda _probability: True,
            ),
        )
        cold_adapter.run(context, route_witness=NativePostWriteRouteWitness(result, request.native_operation_key))
        assert _bridge_rows(cold_registry) == cold_rows_before
        assert cold_geometry.list_motifs("research")
        assert not list(tmp_path.rglob("motifs.json"))
    finally:
        qualified.close()


@pytest.mark.parametrize(
    ("tri_mod", "expected_probability", "expected_threshold"),
    (
        ({"bridge_p": -1.0, "bridge_sim": .1, "tearing_risk": .0}, .02, .84),
        ({"bridge_p": .08, "bridge_sim": .86, "tearing_risk": .5}, .064, .875),
        ({"bridge_p": 1.0, "bridge_sim": 1.0, "tearing_risk": .0}, .12, .92),
    ),
)
def test_b1_shared_bridge_probability_threshold_and_failure_topology_match_legacy(
    tmp_path: Path,
    tri_mod,
    expected_probability,
    expected_threshold,
):
    qualified, _connection, capability, scopes, results, geometry, retired_motif_id = _prepared(tmp_path)
    try:
        request, result = results["research"]
        context = _context(result, request, tri_mod=tri_mod)
        legacy_registry = BridgeRegistry(str(tmp_path / "legacy-bridge-store"), "b1-workspace")
        native_registry = BridgeRegistry(str(tmp_path / "native-bridge-store"), "b1-workspace")
        research_id = geometry.list_motifs("research")[0].runtime_motif_id
        engineering_id = geometry.list_motifs("engineering")[0].runtime_motif_id
        for registry in (legacy_registry, native_registry):
            registry.bridges.append(Bridge("research", research_id, "engineering", engineering_id, 1.0, 1))
            registry.save()
        legacy_workspace = SimpleNamespace(bridges=legacy_registry, motif_regs=_ForbiddenLegacyMotifs())
        native_workspace = SimpleNamespace(bridges=native_registry, motif_regs=_ForbiddenLegacyMotifs())
        legacy_probability: list[float] = []
        native_probability: list[float] = []
        run_bridge_suggestions(
            context, workspace=legacy_workspace,
            random_chance=lambda probability: legacy_probability.append(probability) or False,
            geometry=geometry,
        )
        configuration = _configuration(
            scopes["research"], workspace=native_workspace, geometry=geometry,
            random_chance=lambda probability: native_probability.append(probability) or False,
        )
        adapter = prepare_native_fabric_post_write_adapter(capability=capability, configuration=configuration)
        adapter.run(context, route_witness=NativePostWriteRouteWitness(result, request.native_operation_key))
        assert legacy_probability == native_probability == [pytest.approx(expected_probability)]

        legacy_attempts: list[tuple[float, int]] = []
        native_attempts: list[tuple[float, int]] = []
        legacy_suggest = legacy_registry.suggest
        native_suggest = native_registry.suggest
        legacy_registry.suggest = lambda _geometry, *, sim_threshold, max_new: (  # type: ignore[method-assign]
            legacy_attempts.append((sim_threshold, max_new))
            or legacy_suggest(_geometry, sim_threshold=sim_threshold, max_new=max_new)
        )
        native_registry.suggest = lambda _geometry, *, sim_threshold, max_new: (  # type: ignore[method-assign]
            native_attempts.append((sim_threshold, max_new))
            or native_suggest(_geometry, sim_threshold=sim_threshold, max_new=max_new)
        )
        run_bridge_suggestions(context, workspace=legacy_workspace, random_chance=lambda _probability: True, geometry=geometry)
        adapter = prepare_native_fabric_post_write_adapter(
            capability=capability,
            configuration=replace(
                configuration,
                external=replace(configuration.external, random_chance=lambda _probability: True),
            ),
        )
        adapter.run(context, route_witness=NativePostWriteRouteWitness(result, request.native_operation_key))
        assert legacy_attempts == native_attempts == [(pytest.approx(expected_threshold), 5)]
        assert _bridge_rows(native_registry) == _bridge_rows(legacy_registry)
        assert all("archive" not in (from_domain, to_domain) for from_domain, _, to_domain, _, _, _ in _bridge_rows(native_registry))
        assert all(retired_motif_id not in endpoint for row in _bridge_rows(native_registry) for endpoint in (row[1], row[3]))

        def boom(*_args, **_kwargs):
            raise RuntimeError("bridge side-store failure")

        native_workspace.bridges.suggest = boom
        adapter = prepare_native_fabric_post_write_adapter(
            capability=capability,
            configuration=replace(
                configuration,
                external=replace(configuration.external, random_chance=lambda _probability: True),
            ),
        )
        with pytest.raises(RuntimeError, match="bridge side-store failure"):
            adapter.run(context, route_witness=NativePostWriteRouteWitness(result, request.native_operation_key))
        legacy_workspace.bridges.suggest = boom
        with pytest.raises(RuntimeError, match="bridge side-store failure"):
            run_bridge_suggestions(context, workspace=legacy_workspace, random_chance=lambda _probability: True, geometry=geometry)
    finally:
        qualified.close()
