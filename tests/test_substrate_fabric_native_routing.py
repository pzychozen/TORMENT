"""Focused A3D qualification tests for the explicit native route boundary."""
from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import sqlite3

import numpy as np
import pytest

from torment_service.collective_models import MemoryGovernanceFlags
from torment_service.provenance_v1 import ProvenanceV1
from torment_service.substrate.connection import (
    open_existing_native_core_connection,
    open_temporary_test_connection,
)
from torment_service.substrate.compat import NativeMemoryCompatibilityFacade
from torment_service.substrate.errors import (
    SubstrateConfigurationError,
    SubstrateIdempotencyConflict,
    SubstrateSchemaCompatibilityError,
)
from torment_service.substrate.fabric_native_routing import (
    NativeFabricMemoryRouter,
    NativeFabricRouteRequest,
    NativeFabricRoutingScope,
    prepare_native_fabric_routing_capability,
)
from torment_service.substrate.ids import generate_native_id, native_id_from_bytes, native_id_to_bytes
from torment_service.substrate.motif_runtime_reader import NativeMotifRuntimeReader
from torment_service.substrate.native_memory_runtime_access import NativePostWriteMemoryAccess
from torment_service.substrate.native_srg_runtime import (
    NativeSRGProcessState,
    NativeSRGTransientRuntime,
)
from torment_service.substrate.motifs import NativeMotifService
from torment_service.substrate.representations import NativeRepresentationService
from torment_service.substrate.runtime_binding import (
    NativeMemoryRuntimeScope,
    NativeRepresentationLane,
    prepare_native_memory_runtime_binding,
)
from torment_service.substrate.schema import create_schema, create_schema_v1


def _id():
    return generate_native_id()


def _lane(**changes):
    values = {
        "provider": "synthetic",
        "model": "synthetic-v1",
        "dimension": 3,
        "representation_class": "COMPAT_EMBEDDING",
        "generation": 1,
        "derivation_contract_version": "compat-embedding-v1",
        "encoding_id": "RAW_VECTOR",
        "dtype": "float32",
    }
    values.update(changes)
    return NativeRepresentationLane(**values)


def _scope_rows(connection, *, workspace: str, kind: str, qualifier: str):
    memory_identity, semantic_scope, memory_alias = _id(), _id(), _id()
    motif_identity, membership_identity, motif_alias, idem = (_id() for _ in range(4))
    for value, label in (
        (memory_identity, "memory-identity"),
        (motif_identity, "motif-identity"),
        (membership_identity, "membership-identity"),
    ):
        connection.execute(
            "INSERT INTO identity_namespaces VALUES (?,?,0)",
            (native_id_to_bytes(value), f"{workspace}:{kind}:{qualifier}:{label}"),
        )
    connection.execute(
        "INSERT INTO semantic_scopes VALUES (?,?,0)",
        (native_id_to_bytes(semantic_scope), f"{workspace}:{kind}:{qualifier}:semantic"),
    )
    for value, label in ((memory_alias, "memory-alias"), (motif_alias, "motif-alias")):
        connection.execute(
            "INSERT INTO legacy_source_namespaces VALUES (?,?,0)",
            (native_id_to_bytes(value), f"{workspace}:{kind}:{qualifier}:{label}"),
        )
    connection.execute(
        "INSERT INTO idempotency_namespaces VALUES (?,?)",
        (native_id_to_bytes(idem), f"{workspace}:{kind}:{qualifier}:idempotency"),
    )
    runtime = NativeMemoryRuntimeScope(
        workspace_id=workspace,
        scope_kind=kind,
        legacy_source_namespace_id=memory_alias,
        identity_namespace_id=memory_identity,
        semantic_scope_id=semantic_scope,
        agent_id=qualifier if kind == "PRIVATE_AGENT" else None,
        domain_id=qualifier if kind == "SHARED_DOMAIN" else None,
    )
    return NativeFabricRoutingScope(
        runtime_scope=runtime,
        motif_alias_namespace_id=motif_alias,
        motif_identity_namespace_id=motif_identity,
        membership_identity_namespace_id=membership_identity,
        idempotency_namespace_id=idem,
    )


def _prepared(tmp_path: Path, *, include_shared: bool = False):
    qualified = open_temporary_test_connection(tmp_path / "a3d-staging.db")
    metadata = create_schema(qualified.connection)
    connection = qualified.connection
    private = _scope_rows(
        connection, workspace="qualified-workspace", kind="PRIVATE_AGENT", qualifier="aria"
    )
    scopes = [private]
    shared = None
    if include_shared:
        shared = _scope_rows(
            connection, workspace="qualified-workspace", kind="SHARED_DOMAIN", qualifier="research"
        )
        scopes.append(shared)
    core_id = native_id_from_bytes(metadata.core_id)
    binding = prepare_native_memory_runtime_binding(
        connection=connection,
        core_database_path=qualified.database_path,
        expected_core_id=core_id,
        scope_bindings=tuple(item.runtime_scope for item in scopes),
        representation_lane=_lane(),
    )
    capability = prepare_native_fabric_routing_capability(
        binding=binding,
        connection=connection,
        routing_scopes=tuple(scopes),
        expected_core_id=core_id,
    )
    return qualified, connection, capability, private, shared


def _request(*, key: str | None, vector=(1.0, 0.0, 0.0), scope="private", domain="research", **changes):
    values = {
        "workspace_id": "qualified-workspace",
        "scope": scope,
        "agent_id": "aria",
        "domain_id": domain,
        "native_operation_key": key,
        "embedder_lane": _lane(),
        "summary": f"native route {key}",
        "memory_type": "reflection",
        "memory_class": "core",
        "strength": 0.7,
        "confidence": 0.8,
        "half_life_days": 5.0,
        "logical_step": 12,
        "created_ts": 100,
        "last_active_ts": 101,
        "last_reinforced_ts": 102,
        "incoming_embedding": vector,
        "provenance": ProvenanceV1.for_user_ingest(step=12),
        "governance": MemoryGovernanceFlags(),
        "flexible_payload": {"qualification_marker": "a3d"},
    }
    values.update(changes)
    return NativeFabricRouteRequest(**values)


def _counts(connection):
    tables = (
        "objects", "object_revisions", "relationships", "relationship_revisions",
        "representations", "representation_payloads", "operations", "semantic_transitions",
    )
    return tuple(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in tables)


def _apply_srg_overlay(connection, capability, private, *, eid, state, report):
    runtime = NativeSRGTransientRuntime(
        connection,
        legacy_source_namespace_id=private.runtime_scope.legacy_source_namespace_id,
        process_state=capability.srg_process_state,
    )
    reads = NativePostWriteMemoryAccess(
        connection,
        legacy_source_namespace_id=private.runtime_scope.legacy_source_namespace_id,
        expected_dimension=3,
    )
    view = reads.get_current(eid)
    runtime.apply_collision(
        existing=view, incoming=view, existing_state=state,
        incoming_state=state, incoming_report=report,
    )
    return runtime, view


def test_existing_core_opener_refuses_absent_path_without_creating_a_database(tmp_path: Path):
    missing = tmp_path / "missing-native-core.db"
    with pytest.raises(SubstrateConfigurationError, match="already exist"):
        open_existing_native_core_connection(missing)
    assert not missing.exists()


def test_existing_core_opener_refuses_v1_without_upgrading(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "historical-v1.db")
    try:
        create_schema_v1(qualified.connection)
        path = qualified.database_path
    finally:
        qualified.close()
    with pytest.raises(SubstrateSchemaCompatibilityError, match="read-only"):
        open_existing_native_core_connection(path)
    raw = sqlite3.connect(path)
    try:
        assert raw.execute("SELECT schema_major,schema_minor FROM core_metadata").fetchone() == (1, 0)
    finally:
        raw.close()


def test_capability_is_separate_immutable_and_revalidates_explicit_namespaces(tmp_path: Path):
    qualified, connection, capability, private, _shared = _prepared(tmp_path)
    try:
        before = _counts(connection)
        assert capability.binding is not None
        assert capability.production_activation_allowed is False
        assert capability.qualification_only is True
        assert capability.routing_scopes == (private,)
        assert private.runtime_scope.legacy_source_namespace_id != private.motif_alias_namespace_id
        with pytest.raises(Exception):
            capability.core_id = _id()  # type: ignore[misc]
        assert _counts(connection) == before
    finally:
        qualified.close()


def test_claimed_scope_requires_stable_operation_key_and_unclaimed_scope_stays_outside_native(tmp_path: Path):
    qualified, connection, capability, _private, _shared = _prepared(tmp_path)
    try:
        router = NativeFabricMemoryRouter(capability)
        before = _counts(connection)
        missing = router.route(_request(key=None))
        assert (missing.qualification.eligible, missing.qualification.reason_code, missing.result) == (
            False, "MISSING_NATIVE_OPERATION_KEY", None,
        )
        mismatch = router.route(_request(key="unclaimed", agent_id="other-agent"))
        assert (mismatch.qualification.eligible, mismatch.qualification.reason_code, mismatch.result) == (
            False, "SCOPE_NOT_CLAIMED", None,
        )
        assert _counts(connection) == before
    finally:
        qualified.close()


def test_new_memory_route_uses_a3c1_a3c2_and_exact_e1_publication_without_legacy_state(tmp_path: Path):
    qualified, connection, capability, private, _shared = _prepared(tmp_path)
    try:
        raw = np.asarray((2.0, 0.5, 0.0), dtype=np.float32)
        attempt = NativeFabricMemoryRouter(capability).route(
            _request(key="new-memory", vector=raw)
        )
        assert attempt.qualification.eligible is True
        result = attempt.result
        assert result is not None
        assert (result.stored, result.reinforced, result.eid, result.motifs) == (
            True, False, 0, ("motif_research_0001",),
        )
        assert NativeRepresentationService(connection).read_representation_payload(
            result.representation_id
        ) == raw.tobytes(order="C")
        assert connection.execute("SELECT readiness,operational_disposition FROM representation_current_state").fetchall() == [
            ("READY", "USABLE")
        ]
        assert connection.execute("SELECT count(*) FROM legacy_object_aliases WHERE legacy_source_namespace_id=? AND alias_kind='EID'", (
            native_id_to_bytes(private.runtime_scope.legacy_source_namespace_id),
        )).fetchone()[0] == 1
        # Only native carriers exist; the router does not create a MemoryGraph,
        # JSONL node, or legacy motif registry as a shadow substitute.
        assert not list(tmp_path.rglob("nodes.jsonl"))
        assert not list(tmp_path.rglob("motifs.json"))
    finally:
        qualified.close()


def test_new_memory_retry_after_source_commit_recovers_same_source_and_e1(tmp_path: Path):
    qualified, connection, capability, _private, _shared = _prepared(tmp_path)
    try:
        router = NativeFabricMemoryRouter(capability)
        request = _request(key="interrupted-source", vector=(1.0, 0.0, 0.0))
        with pytest.raises(RuntimeError, match="committed native new-memory source"):
            router.route(request, _test_stop_after="source")
        after_source = _counts(connection)
        complete = router.route(request).result
        assert complete is not None and complete.reinforced is False
        assert _counts(connection)[0] == after_source[0]
        assert _counts(connection)[2] == after_source[2]
        assert _counts(connection)[4] == 1
        assert NativeRepresentationService(connection).get_representation_metadata(
            complete.representation_id
        ).readiness == "READY"
    finally:
        qualified.close()


def test_e1_failure_after_native_source_leaves_no_legacy_fallback_and_retry_resumes(tmp_path: Path, monkeypatch):
    qualified, connection, capability, _private, _shared = _prepared(tmp_path)
    try:
        router = NativeFabricMemoryRouter(capability)
        request = _request(key="e1-failure", vector=(1.0, 0.0, 0.0))
        original = NativeRepresentationService.publish_representation_ready

        def fail_ready(*_args, **_kwargs):
            raise RuntimeError("forced E1 publication failure")

        with monkeypatch.context() as patcher:
            patcher.setattr(NativeRepresentationService, "publish_representation_ready", fail_ready)
            with pytest.raises(RuntimeError, match="forced E1 publication failure"):
                router.route(request)
        assert connection.execute("SELECT count(*) FROM objects").fetchone()[0] == 2
        assert connection.execute("SELECT count(*) FROM representation_payloads").fetchone()[0] == 0
        resumed = router.route(request).result
        assert resumed is not None and resumed.reinforced is False
        assert connection.execute("SELECT count(*) FROM objects").fetchone()[0] == 2
        assert NativeRepresentationService(connection).get_representation_metadata(
            resumed.representation_id
        ).readiness == "READY"
        assert original is NativeRepresentationService.publish_representation_ready
    finally:
        qualified.close()


def test_private_native_duplicate_selection_reinforces_exact_current_r1_e1(tmp_path: Path):
    qualified, connection, capability, _private, _shared = _prepared(tmp_path)
    try:
        router = NativeFabricMemoryRouter(capability)
        first = router.route(_request(key="seed", vector=(1.0, 0.0, 0.0))).result
        assert first is not None
        reinforced = router.route(
            _request(key="reinforce", vector=(1.0, 0.0, 0.0), logical_step=20, last_reinforced_ts=200)
        ).result
        assert reinforced is not None
        assert (reinforced.stored, reinforced.reinforced, reinforced.eid) == (True, True, first.eid)
        assert reinforced.memory_object_id == first.memory_object_id
        assert reinforced.memory_revision_id != first.memory_revision_id
        assert reinforced.representation_id != first.representation_id
        assert connection.execute("SELECT count(*) FROM legacy_object_aliases WHERE alias_kind='MOTIF_ID'").fetchone()[0] == 1
        assert connection.execute("SELECT count(*) FROM relationships").fetchone()[0] == 1
    finally:
        qualified.close()


def test_srg_overlay_survives_connection_boundary_and_materializes_in_the_duplicate_r2(tmp_path: Path):
    qualified, connection, capability, private, _shared = _prepared(tmp_path)
    closed = False
    try:
        router = NativeFabricMemoryRouter(capability)
        baseline = {"R": 0.10, "band": 1, "heartbeat": "A", "last_collision_step": -1}
        effective = {"R": 0.48, "band": 1, "heartbeat": "A", "last_collision_step": 20}
        report = {"collision": True, "score": 0.95, "step": 20}
        seed = router.route(_request(
            key="srg-boundary-seed", vector=(1.0, 0.0, 0.0),
            flexible_payload={"qualification_marker": "a3d", "srg": baseline},
        )).result
        assert seed is not None
        _apply_srg_overlay(
            connection, capability, private, eid=seed.eid, state=effective, report=report,
        )
        # The overlay belongs to the prepared capability, not this handle.
        qualified.close()
        closed = True
        reinforcement_request = _request(
            key="srg-boundary-reinforce", vector=(1.0, 0.0, 0.0), logical_step=20,
            last_reinforced_ts=200,
        )
        reinforced = router.route(reinforcement_request).result
        assert reinforced is not None and reinforced.reinforced is True
        with open_existing_native_core_connection(capability.core_database_path) as reopened:
            current = NativeMemoryCompatibilityFacade(reopened.connection).get_memory_by_eid(
                legacy_source_namespace_id=private.runtime_scope.legacy_source_namespace_id,
                eid=seed.eid,
            )
            assert current.revision_id == reinforced.memory_revision_id
            assert current.revision_ordinal == 2
            assert current.payload["srg"] == effective
            assert current.payload["srg_collision"] == report
            assert current.payload["reinforcement_count"] == 1
            assert reopened.connection.execute(
                "SELECT count(*) FROM object_revisions WHERE object_id=?",
                (native_id_to_bytes(seed.memory_object_id),),
            ).fetchone()[0] == 2
            assert NativeRepresentationService(reopened.connection).read_representation_payload(
                reinforced.representation_id
            ) == NativeRepresentationService(reopened.connection).read_representation_payload(
                seed.representation_id
            )
            assert NativeSRGTransientRuntime(
                reopened.connection,
                legacy_source_namespace_id=private.runtime_scope.legacy_source_namespace_id,
                process_state=capability.srg_process_state,
            ).prepare_successor_materialization(
                eid=seed.eid, expected_revision_id=reinforced.memory_revision_id,
            ) is None
            restarted = NativeSRGTransientRuntime(
                reopened.connection,
                legacy_source_namespace_id=private.runtime_scope.legacy_source_namespace_id,
                process_state=NativeSRGProcessState(),
            )
            restarted_view = NativePostWriteMemoryAccess(
                reopened.connection,
                legacy_source_namespace_id=private.runtime_scope.legacy_source_namespace_id,
                expected_dimension=3,
            ).get_current(seed.eid)
            assert restarted.effective_srg_state(restarted_view) == effective
            assert restarted.effective_collision_report(restarted_view) == report
            restarted_capability = prepare_native_fabric_routing_capability(
                binding=capability.binding,
                connection=reopened.connection,
                routing_scopes=(private,),
                expected_core_id=capability.core_id,
            )
            assert NativeFabricMemoryRouter(restarted_capability).route(
                reinforcement_request
            ).result == reinforced
    finally:
        if not closed:
            qualified.close()


@pytest.mark.parametrize("stop", ("source", "pending", "expectation"))
def test_srg_overlay_lost_response_recovery_reuses_r2_then_consumes_the_overlay(
    tmp_path: Path, stop: str,
):
    qualified, connection, capability, private, _shared = _prepared(tmp_path)
    closed = False
    try:
        router = NativeFabricMemoryRouter(capability)
        effective = {"R": 0.48, "band": 1, "heartbeat": "A", "last_collision_step": 20}
        report = {"collision": True, "score": 0.95, "step": 20}
        seed = router.route(_request(
            key="srg-lost-seed", vector=(1.0, 0.0, 0.0),
            flexible_payload={
                "qualification_marker": "a3d",
                "srg": {"R": 0.10, "band": 1, "heartbeat": "A", "last_collision_step": -1},
            },
        )).result
        assert seed is not None
        _apply_srg_overlay(
            connection, capability, private, eid=seed.eid, state=effective, report=report,
        )
        qualified.close()
        closed = True
        retry = _request(
            key="srg-lost-reinforce", vector=(1.0, 0.0, 0.0), logical_step=20,
            last_reinforced_ts=200,
        )
        with pytest.raises(RuntimeError, match="forced interruption"):
            router.route(retry, _test_stop_after=stop)
        completed = router.route(retry).result
        assert completed is not None and completed.reinforced is True
        with open_existing_native_core_connection(capability.core_database_path) as reopened:
            current = NativeMemoryCompatibilityFacade(reopened.connection).get_memory_by_eid(
                legacy_source_namespace_id=private.runtime_scope.legacy_source_namespace_id,
                eid=seed.eid,
            )
            assert current.revision_id == completed.memory_revision_id
            assert current.revision_ordinal == 2
            assert current.payload["srg"] == effective
            assert current.payload["srg_collision"] == report
            assert reopened.connection.execute(
                "SELECT count(*) FROM object_revisions WHERE object_id=?",
                (native_id_to_bytes(seed.memory_object_id),),
            ).fetchone()[0] == 2
            source_intent = json.loads(reopened.connection.execute(
                "SELECT canonical_intent_json FROM operations WHERE idempotency_key=?",
                ("NATIVE_REINFORCEMENT:SOURCE:NATIVE_FABRIC_REINFORCEMENT:srg-lost-reinforce",),
            ).fetchone()[0])
            assert source_intent["retry_contract"]["srg_materialization"]["canonical_digest"]
            assert NativeSRGTransientRuntime(
                reopened.connection,
                legacy_source_namespace_id=private.runtime_scope.legacy_source_namespace_id,
                process_state=capability.srg_process_state,
            ).prepare_successor_materialization(
                eid=seed.eid, expected_revision_id=completed.memory_revision_id,
            ) is None
    finally:
        if not closed:
            qualified.close()


def test_reinforcement_retry_after_committed_r2_recovers_e2_without_reselection(tmp_path: Path):
    qualified, connection, capability, _private, _shared = _prepared(tmp_path)
    try:
        router = NativeFabricMemoryRouter(capability)
        seed = router.route(_request(key="retry-seed", vector=(1.0, 0.0, 0.0))).result
        assert seed is not None
        retry = _request(
            key="retry-reinforcement", vector=(1.0, 0.0, 0.0), logical_step=20,
            last_reinforced_ts=200,
        )
        with pytest.raises(RuntimeError, match="committed reinforcement source"):
            router.route(retry, _test_stop_after="source")
        after_source = _counts(connection)
        with pytest.raises(SubstrateIdempotencyConflict, match="different Fabric inputs"):
            router.route(replace(retry, summary="changed after native R2"))
        assert _counts(connection) == after_source
        completed = router.route(retry).result
        assert completed is not None and completed.reinforced is True
        assert completed.memory_object_id == seed.memory_object_id
        assert _counts(connection)[0] == after_source[0]
        assert _counts(connection)[4] == 2  # original E1 plus recovered E2
    finally:
        qualified.close()


def test_e2_failure_after_native_r2_leaves_source_native_and_retry_resumes(tmp_path: Path, monkeypatch):
    qualified, connection, capability, _private, _shared = _prepared(tmp_path)
    try:
        router = NativeFabricMemoryRouter(capability)
        seed = router.route(_request(key="e2-seed", vector=(1.0, 0.0, 0.0))).result
        assert seed is not None
        request = _request(
            key="e2-failure", vector=(1.0, 0.0, 0.0), logical_step=20,
            last_reinforced_ts=200,
        )

        def fail_ready(*_args, **_kwargs):
            raise RuntimeError("forced E2 publication failure")

        with monkeypatch.context() as patcher:
            patcher.setattr(NativeRepresentationService, "publish_representation_ready", fail_ready)
            with pytest.raises(RuntimeError, match="forced E2 publication failure"):
                router.route(request)
        current = connection.execute(
            "SELECT current_revision_id FROM objects WHERE object_id=?",
            (native_id_to_bytes(seed.memory_object_id),),
        ).fetchone()[0]
        assert native_id_from_bytes(current) != seed.memory_revision_id
        assert connection.execute("SELECT count(*) FROM representation_payloads").fetchone()[0] == 1
        resumed = router.route(request).result
        assert resumed is not None and resumed.reinforced is True
        assert connection.execute("SELECT count(*) FROM representation_payloads").fetchone()[0] == 2
    finally:
        qualified.close()


def test_cross_class_and_contradiction_guards_proceed_to_native_new_memory(tmp_path: Path):
    qualified, connection, capability, _private, _shared = _prepared(tmp_path)
    try:
        router = NativeFabricMemoryRouter(capability)
        seed = router.route(_request(key="guard-seed", vector=(1.0, 0.0, 0.0))).result
        assert seed is not None
        cross_class = router.route(_request(
            key="cross-class", vector=(1.0, 0.0, 0.0), memory_class="baton",
        )).result
        assert cross_class is not None and cross_class.reinforced is False and cross_class.eid != seed.eid
        contradictory = router.route(_request(
            key="contradiction", vector=(1.0, 0.0, 0.0),
            contradiction_guard=lambda _new, _old, _score: True,
        )).result
        assert contradictory is not None and contradictory.reinforced is False
        assert contradictory.eid not in {seed.eid, cross_class.eid}
    finally:
        qualified.close()


def test_tool_result_reinforcement_preserves_no_strength_boost_and_refresh_timestamp(tmp_path: Path):
    qualified, connection, capability, _private, _shared = _prepared(tmp_path)
    try:
        router = NativeFabricMemoryRouter(capability)
        seed = router.route(_request(
            key="tool-seed", vector=(1.0, 0.0, 0.0),
            provenance=ProvenanceV1.for_tool_result("fixture", step=12), strength=0.7,
        )).result
        assert seed is not None
        updated = router.route(_request(
            key="tool-reinforce", vector=(1.0, 0.0, 0.0), logical_step=20,
            last_reinforced_ts=200, last_tool_refresh_ts=201,
        )).result
        assert updated is not None and updated.reinforced is True
        payload = connection.execute(
            "SELECT payload_text FROM object_revisions WHERE object_revision_id=?",
            (native_id_to_bytes(updated.memory_revision_id),),
        ).fetchone()[0]
        assert '"strength":0.7' in payload and '"last_tool_refresh_ts":201' in payload
    finally:
        qualified.close()


def test_process_order_seeds_lexicographically_appends_and_tie_selects_first(tmp_path: Path):
    qualified, connection, capability, private, _shared = _prepared(tmp_path)
    try:
        router = NativeFabricMemoryRouter(capability)
        first = router.route(_request(key="motif-a", vector=(1.0, 0.0, 0.0))).result
        second = router.route(_request(key="motif-b", vector=(0.0, 1.0, 0.0))).result
        assert first is not None and second is not None
        assert capability.process_order.runtime_ids_for_testing(
            routing_scope=private, domain_id="research"
        ) == ("motif_research_0001", "motif_research_0002")
        tied = router.route(_request(key="motif-tie", vector=(1.0, 1.0, 0.0))).result
        assert tied is not None
        # A strict replacement comparator preserves the first process-order
        # motif on an equal score; attach does not alter process order.
        assert tied.motifs == ("motif_research_0001",)
        assert capability.process_order.runtime_ids_for_testing(
            routing_scope=private, domain_id="research"
        ) == ("motif_research_0001", "motif_research_0002")

        restarted = prepare_native_fabric_routing_capability(
            binding=capability.binding,
            connection=connection,
            routing_scopes=(private,),
            expected_core_id=capability.core_id,
        )
        # A fresh capability models process restart: it derives its baseline
        # lexicographically from live runtime IDs without mutating the core.
        with restarted.process_order.locked_catalog(
            reader=NativeMotifRuntimeReader(connection),
            routing_scope=private,
            domain_id="research",
        ) as restart_catalog:
            assert tuple(item.read_model.runtime_motif_id for item in restart_catalog) == (
                "motif_research_0001", "motif_research_0002",
            )
        assert restarted.process_order.runtime_ids_for_testing(
            routing_scope=private, domain_id="research"
        ) == ("motif_research_0001", "motif_research_0002")
    finally:
        qualified.close()


def test_unknown_external_motif_invalidates_first_process_order_owner(tmp_path: Path):
    qualified, connection, capability, private, _shared = _prepared(tmp_path)
    try:
        first_process = NativeFabricMemoryRouter(capability)
        assert first_process.route(_request(key="first", vector=(1.0, 0.0, 0.0))).result is not None
        other_capability = prepare_native_fabric_routing_capability(
            binding=capability.binding,
            connection=connection,
            routing_scopes=(private,),
            expected_core_id=capability.core_id,
        )
        assert NativeFabricMemoryRouter(other_capability).route(
            _request(key="external", vector=(0.0, 1.0, 0.0))
        ).result is not None
        refused = first_process.route(_request(key="first-after-external", vector=(1.0, 1.0, 0.0)))
        assert (refused.qualification.eligible, refused.qualification.reason_code, refused.result) == (
            False, "PROCESS_ORDER_INVALID", None,
        )
    finally:
        qualified.close()


def test_unsupported_split_refuses_claimed_route_before_native_or_legacy_mutation(tmp_path: Path):
    qualified, connection, capability, private, _shared = _prepared(tmp_path)
    try:
        seed = NativeFabricMemoryRouter(capability).route(
            _request(key="split-seed", vector=(1.0, 0.0, 0.0))
        ).result
        assert seed is not None
        motif_object_id = connection.execute(
            "SELECT object_id FROM legacy_object_aliases WHERE legacy_source_namespace_id=? AND alias_kind='MOTIF_ID' AND alias_value='motif_research_0001'",
            (native_id_to_bytes(private.motif_alias_namespace_id),),
        ).fetchone()[0]
        facade = NativeMemoryCompatibilityFacade(connection)
        motifs = NativeMotifService(connection)
        for ordinal in range(2, 96):
            source = facade.create_memory_state(
                legacy_source_namespace_id=private.runtime_scope.legacy_source_namespace_id,
                idempotency_namespace_id=private.idempotency_namespace_id,
                idempotency_key=f"split-source:{ordinal}",
                identity_namespace_id=private.runtime_scope.identity_namespace_id,
                semantic_scope_id=private.runtime_scope.semantic_scope_id,
                summary=f"split source {ordinal}", memory_type="reflection", logical_step=ordinal,
            )
            current = motifs.get_current_motif(native_id_from_bytes(motif_object_id))
            motifs.add_motif_member(
                idempotency_namespace_id=private.idempotency_namespace_id,
                idempotency_key=f"split-membership:{ordinal}",
                motif_alias_namespace_id=private.motif_alias_namespace_id,
                membership_identity_namespace_id=private.membership_identity_namespace_id,
                motif_object_id=current.motif_object_id,
                expected_motif_revision_id=current.motif_revision_id,
                state=replace(current.state, last_active_ts=current.state.last_active_ts + 1),
                member_object_id=source.object_id,
            )
        restarted = prepare_native_fabric_routing_capability(
            binding=capability.binding,
            connection=connection,
            routing_scopes=(private,),
            expected_core_id=capability.core_id,
        )
        before = _counts(connection)
        refused = NativeFabricMemoryRouter(restarted).route(
            _request(key="split-refusal", vector=(0.8, 0.6, 0.0))
        )
        assert (refused.qualification.eligible, refused.qualification.reason_code, refused.result) == (
            False, "UNSUPPORTED_NATIVE_SPLIT", None,
        )
        assert _counts(connection) == before
    finally:
        qualified.close()


def test_shared_scope_creates_new_memory_without_duplicate_reinforcement_and_links_refuse(tmp_path: Path):
    qualified, connection, capability, _private, shared = _prepared(tmp_path, include_shared=True)
    assert shared is not None
    try:
        router = NativeFabricMemoryRouter(capability)
        first = router.route(_request(key="shared-a", scope="shared", vector=(1.0, 0.0, 0.0))).result
        second = router.route(_request(key="shared-b", scope="shared", vector=(1.0, 0.0, 0.0))).result
        assert first is not None and second is not None
        assert (first.reinforced, second.reinforced, first.eid, second.eid) == (False, False, 0, 1)
        before = _counts(connection)
        links = router.route(_request(key="shared-links", scope="shared", raw_links=("legacy:1",)))
        assert (links.qualification.eligible, links.qualification.reason_code, links.result) == (
            False, "LINKS_DEFERRED", None,
        )
        assert _counts(connection) == before
    finally:
        qualified.close()


def test_lane_mismatch_and_structural_payload_refusal_are_pre_source_fail_closed(tmp_path: Path):
    qualified, connection, capability, _private, _shared = _prepared(tmp_path)
    try:
        router = NativeFabricMemoryRouter(capability)
        before = _counts(connection)
        mismatch = router.route(_request(key="wrong-lane", embedder_lane=_lane(model="other")))
        assert mismatch.qualification.reason_code == "EMBEDDER_LANE_MISMATCH"
        structural = router.route(_request(key="structural", flexible_payload={"governance": "forged"}))
        assert structural.qualification.reason_code == "STRUCTURAL_PAYLOAD_REFUSED"
        assert _counts(connection) == before
    finally:
        qualified.close()
