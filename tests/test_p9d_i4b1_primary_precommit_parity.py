"""Focused synthetic qualification for I4B-1/I4B-2 primary/precommit truth.

These tests use only temporary native SQLite cores.  They do not start a
service, open a real root, or contact a provider.
"""
from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
import pytest

from torment_service.collective_models import MemoryGovernanceFlags
from torment_service.fabric import TormentFabric
from torment_service.motif_decision import motif_density
from torment_service.provenance_v1 import ProvenanceV1
from torment_service.substrate.compat import (
    CompatibilityEmbeddingPublicationRequest,
    NativeMemoryCompatibilityFacade,
)
from torment_service.substrate.connection import (
    open_existing_native_core_connection,
    open_temporary_test_connection,
)
from torment_service.substrate.errors import SubstrateIdempotencyConflict, SubstrateObjectNotFound
from torment_service.substrate.fabric_native_routing import (
    NativeFabricMemoryRouter,
    NativeFabricRouteRequest,
    NativeFabricRoutingScope,
    NativePrecommitAttachFailure,
    prepare_native_fabric_routing_capability,
)
from torment_service.substrate.ids import generate_native_id, native_id_from_bytes, native_id_to_bytes
from torment_service.substrate.memory_reinforcement import (
    NativeMemoryReinforcementRequest,
    NativeMemoryReinforcementService,
)
from torment_service.substrate.motif_runtime_reader import NativeMotifRuntimeReader
from torment_service.substrate.native_motif_split import split_strength
from torment_service.substrate.motifs import NativeMotifService
from torment_service.substrate.native_memory_runtime_access import NativePostWriteMemoryAccess
from torment_service.substrate.provenance import NativeProvenanceRecord
from torment_service.substrate.representations import (
    INTEGRITY_ALGORITHM_SHA256,
    INTEGRITY_VALUE_ENCODING_RAW,
    NativeRepresentationService,
    RepresentationIntegrityExpectationRequest,
    RepresentationReadyRequest,
    RepresentationRequest,
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
        provider="synthetic", model="synthetic-v1", dimension=3,
        representation_class="COMPAT_EMBEDDING", generation=1,
        derivation_contract_version="compat-embedding-v1", encoding_id="RAW_VECTOR",
        dtype="float32",
    )


def _routing_scope(connection, *, workspace: str, kind: str, qualifier: str) -> NativeFabricRoutingScope:
    memory_identity, semantic_scope, memory_alias = _id(), _id(), _id()
    motif_identity, membership_identity, motif_alias, idempotency = (_id() for _ in range(4))
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
        (native_id_to_bytes(idempotency), f"{workspace}:{kind}:{qualifier}:idempotency"),
    )
    return NativeFabricRoutingScope(
        runtime_scope=NativeMemoryRuntimeScope(
            workspace_id=workspace,
            scope_kind=kind,
            legacy_source_namespace_id=memory_alias,
            identity_namespace_id=memory_identity,
            semantic_scope_id=semantic_scope,
            agent_id=qualifier if kind == "PRIVATE_AGENT" else None,
            domain_id=qualifier if kind == "SHARED_DOMAIN" else None,
        ),
        motif_alias_namespace_id=motif_alias,
        motif_identity_namespace_id=motif_identity,
        membership_identity_namespace_id=membership_identity,
        idempotency_namespace_id=idempotency,
    )


def _prepared(tmp_path: Path, *, shared: bool = False):
    qualified = open_temporary_test_connection(tmp_path / "i4b1.db")
    metadata = create_schema(qualified.connection)
    connection = qualified.connection
    private = _routing_scope(
        connection, workspace="i4b1-workspace", kind="PRIVATE_AGENT", qualifier="aria",
    )
    shared_scope = (
        _routing_scope(connection, workspace="i4b1-workspace", kind="SHARED_DOMAIN", qualifier="research")
        if shared else None
    )
    scopes = (private,) if shared_scope is None else (private, shared_scope)
    binding = prepare_native_memory_runtime_binding(
        connection=connection,
        core_database_path=qualified.database_path,
        expected_core_id=native_id_from_bytes(metadata.core_id),
        scope_bindings=tuple(item.runtime_scope for item in scopes),
        representation_lane=_lane(),
    )
    capability = prepare_native_fabric_routing_capability(
        binding=binding,
        connection=connection,
        routing_scopes=scopes,
        expected_core_id=native_id_from_bytes(metadata.core_id),
    )
    return qualified, connection, capability, private, shared_scope


def _request(
    *, key: str, vector: tuple[float, float, float] = (1.0, 0.0, 0.0),
    scope: str = "private", **changes,
) -> NativeFabricRouteRequest:
    values = {
        "workspace_id": "i4b1-workspace",
        "scope": scope,
        "agent_id": "aria",
        "domain_id": "research",
        "native_operation_key": key,
        "embedder_lane": _lane(),
        "summary": f"i4b1 {key}",
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
        "flexible_payload": {"qualification_marker": "i4b1"},
        "precommit_parity_required": True,
    }
    values.update(changes)
    return NativeFabricRouteRequest(**values)


def _result(router: NativeFabricMemoryRouter, request: NativeFabricRouteRequest, **kwargs):
    attempt = router.route(request, **kwargs)
    assert attempt.qualification.eligible is True
    assert attempt.result is not None
    return attempt.result


def _prepare_true_split_fixture(connection, capability, private):
    """Build the already-qualified, deliberately bimodal parent topology."""
    router = NativeFabricMemoryRouter(capability)
    seed = _result(router, _request(key="i4b2-split-seed", vector=(1.0, 0.0, 0.0)))
    motif = NativeMotifService(connection)
    parent = motif.resolve_motif_alias(
        motif_alias_namespace_id=private.motif_alias_namespace_id,
        runtime_motif_id=seed.motifs[0],
    )
    facade = NativeMemoryCompatibilityFacade(connection)
    for ordinal, vector in enumerate(
        [(1.0, 0.0, 0.0)] * 47 + [(-1.0, 0.0, 0.0)] * 47, start=2,
    ):
        raw = np.asarray(vector, dtype=np.float32)
        source = facade.finalize_memory_draft(facade.begin_memory_draft(
            legacy_source_namespace_id=private.runtime_scope.legacy_source_namespace_id,
            idempotency_namespace_id=private.idempotency_namespace_id,
            idempotency_key=f"i4b2-split-source:{ordinal}",
            identity_namespace_id=private.runtime_scope.identity_namespace_id,
            semantic_scope_id=private.runtime_scope.semantic_scope_id,
            summary=f"i4b2 split source {ordinal}", memory_type="reflection", logical_step=ordinal,
            embedding_request=CompatibilityEmbeddingPublicationRequest(
                raw.tobytes(), "COMPAT_EMBEDDING", 1, "compat-embedding-v1", "RAW_VECTOR",
                dtype="float32", dimension=3,
            ),
        )).source
        current = motif.get_current_motif(parent)
        motif.add_motif_member(
            idempotency_namespace_id=private.idempotency_namespace_id,
            idempotency_key=f"i4b2-split-member:{ordinal}",
            motif_alias_namespace_id=private.motif_alias_namespace_id,
            membership_identity_namespace_id=private.membership_identity_namespace_id,
            motif_object_id=parent, expected_motif_revision_id=current.motif_revision_id,
            state=replace(current.state, last_active_ts=current.state.last_active_ts + 1),
            member_object_id=source.object_id,
        )
    return router, motif, parent, _request(
        key="i4b2-qualified-true-split", vector=(0.7, 0.714, 0.0), attach_threshold=0.72,
    )


def _disable_world_observer(monkeypatch) -> None:
    import torment_service.substrate.native_world_runtime as world_module

    monkeypatch.setattr(world_module.NativeWorldRuntime, "ensure_initialized", lambda _self: None)
    monkeypatch.setattr(
        world_module.NativeWorldRuntime,
        "register_fresh_created",
        lambda _self, **_kwargs: None,
    )


def _current_pending_or_aborted_payload(connection) -> dict[str, object]:
    row = connection.execute(
        """SELECT r.payload_text FROM objects o JOIN object_revisions r
             ON r.object_id=o.object_id AND r.object_revision_id=o.current_revision_id
            AND r.revision_ordinal=o.current_revision_ordinal
            WHERE o.object_kind='LEGACY_CORE_NODE' AND r.existence_state IN ('PENDING','ABORTED')
            ORDER BY r.existence_state"""
    ).fetchone()
    assert row is not None
    return json.loads(row[0])


def _split_operation_intent(connection, operation_kind: str) -> dict[str, object]:
    row = connection.execute(
        "SELECT canonical_intent_json FROM operations WHERE operation_kind=?",
        (operation_kind,),
    ).fetchone()
    assert row is not None
    return json.loads(row[0])


def test_i4b1_primary_outcomes_cover_private_shared_and_reinforcement(tmp_path: Path):
    qualified, connection, capability, private, shared = _prepared(tmp_path, shared=True)
    assert shared is not None
    try:
        router = NativeFabricMemoryRouter(capability)
        refused = router.route(_request(key="unclaimed-private", agent_id="other"))
        assert refused.result is None and refused.primary_outcome is not None
        assert (
            refused.qualification.eligible,
            refused.primary_outcome.final_storage_outcome,
            refused.primary_outcome.primary_canonical_state_committed,
        ) == (False, "REFUSED", False)
        observed: list[tuple[int, str, int]] = []

        def observe(eid: int) -> None:
            existence = connection.execute(
                """SELECT r.existence_state FROM legacy_object_aliases a
                   JOIN objects o ON o.object_id=a.object_id
                   JOIN object_revisions r ON r.object_revision_id=o.current_revision_id
                   WHERE a.legacy_source_namespace_id=? AND a.alias_kind='EID' AND a.alias_value=?""",
                (native_id_to_bytes(private.runtime_scope.legacy_source_namespace_id), str(eid)),
            ).fetchone()[0]
            motif_count = connection.execute("SELECT count(*) FROM relationships").fetchone()[0]
            observed.append((eid, existence, motif_count))

        private_create = _result(router, _request(key="private-create", precommit_spawn_observer=observe))
        assert observed == [(0, "PENDING", 0)]
        assert private_create.primary_outcome is not None
        assert (
            private_create.primary_outcome.scope,
            private_create.primary_outcome.attempt_origin,
            private_create.primary_outcome.reinforcement_disposition,
            private_create.primary_outcome.final_storage_outcome,
            private_create.primary_outcome.create_failure_disposition,
            private_create.primary_outcome.primary_canonical_state_committed,
            private_create.primary_outcome.qualified_memory_eid,
        ) == ("private", "DIRECT_CREATE_PATH", "NOT_APPLICABLE", "CREATED_NEW", "NONE", True, 0)
        assert private_create.created_motif == private_create.motifs[0]
        assert connection.execute(
            "SELECT revision_ordinal,existence_state FROM object_revisions WHERE object_id=? ORDER BY revision_ordinal",
            (native_id_to_bytes(private_create.memory_object_id),),
        ).fetchall() == [(1, "PENDING"), (2, "EXISTS")]

        shared_create = _result(router, _request(key="shared-create", scope="shared"))
        assert shared_create.primary_outcome is not None
        assert (shared_create.primary_outcome.scope, shared_create.reinforced, shared_create.eid) == (
            "shared", False, 0,
        )
        reinforced = _result(router, _request(
            key="private-reinforce", logical_step=20, last_reinforced_ts=200,
        ))
        assert reinforced.primary_outcome is not None
        assert (
            reinforced.reinforced,
            reinforced.eid,
            reinforced.primary_outcome.attempt_origin,
            reinforced.primary_outcome.reinforcement_disposition,
            reinforced.primary_outcome.final_storage_outcome,
        ) == (True, private_create.eid, "INGEST_REINFORCEMENT_ATTEMPT", "REINFORCED", "REINFORCED_EXISTING")
        assert reinforced.created_motif is None
    finally:
        qualified.close()


def test_i4b1_primary_recovery_reuses_only_the_exact_precommit_intent(tmp_path: Path):
    qualified, connection, capability, _private, _shared = _prepared(tmp_path)
    try:
        router = NativeFabricMemoryRouter(capability)
        request = _request(key="primary-recovery")
        with pytest.raises(RuntimeError, match="committed native new-memory source"):
            router.route(request, _test_stop_after="source")
        recovered = _result(router, request)
        assert recovered.primary_outcome is not None
        assert (recovered.stored, recovered.eid, recovered.primary_outcome.final_storage_outcome) == (
            True, 0, "CREATED_NEW",
        )
        with pytest.raises(SubstrateIdempotencyConflict, match="idempotency intent differs"):
            router.route(_request(key="primary-recovery", strength=0.8))
    finally:
        qualified.close()


def test_i4b1_semantic_and_exception_reinforcement_fallthroughs_create(tmp_path: Path, monkeypatch):
    qualified, connection, capability, _private, _shared = _prepared(tmp_path)
    try:
        router = NativeFabricMemoryRouter(capability)
        seed = _result(router, _request(key="semantic-seed"))
        semantic = _result(router, _request(key="semantic-fallthrough", memory_class="baton"))
        assert semantic.primary_outcome is not None
        assert (semantic.reinforced, semantic.eid != seed.eid, semantic.primary_outcome.reinforcement_disposition) == (
            False, True, "SEMANTIC_FALLTHROUGH_TO_CREATE",
        )

        exception_seed = _result(router, _request(key="exception-seed", vector=(0.0, 1.0, 0.0)))
        original = NativeMemoryReinforcementService.reinforce
        with monkeypatch.context() as patcher:
            patcher.setattr(
                NativeMemoryReinforcementService,
                "reinforce",
                lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("forced reinforcement failure")),
            )
            exception = _result(router, _request(
                key="exception-fallthrough", vector=(0.0, 1.0, 0.0), logical_step=20,
            ))
        assert original is NativeMemoryReinforcementService.reinforce
        assert exception.primary_outcome is not None
        assert (
            exception.reinforced,
            exception.eid != exception_seed.eid,
            exception.primary_outcome.reinforcement_disposition,
            exception.primary_outcome.final_storage_outcome,
        ) == (False, True, "EXCEPTION_FALLTHROUGH_TO_CREATE", "CREATED_NEW")
    finally:
        qualified.close()


def test_i4b1_tool_result_formula_and_direct_ingest_provenance_backfill(tmp_path: Path):
    qualified, connection, capability, private, _shared = _prepared(tmp_path)
    try:
        router = NativeFabricMemoryRouter(capability)
        tool = _result(router, _request(
            key="tool-seed",
            provenance=ProvenanceV1.for_tool_result("synthetic-tool", step=12),
            strength=0.7,
        ))
        tool_update = _result(router, _request(
            key="tool-reinforce", logical_step=20, last_reinforced_ts=200,
            last_tool_refresh_ts=201,
        ))
        payload = connection.execute(
            "SELECT payload_text FROM object_revisions WHERE object_revision_id=?",
            (native_id_to_bytes(tool_update.memory_revision_id),),
        ).fetchone()[0]
        assert tool_update.primary_outcome is not None
        assert tool_update.primary_outcome.final_storage_outcome == "REINFORCED_EXISTING"
        assert '"strength":0.7' in payload and '"last_tool_refresh_ts":201' in payload

        # This pre-activation fixture is created lawfully as a source with an
        # explicit governance child and E1, but no provenance child.
        facade = NativeMemoryCompatibilityFacade(connection)
        source = facade.create_memory_state(
            legacy_source_namespace_id=private.runtime_scope.legacy_source_namespace_id,
            idempotency_namespace_id=private.idempotency_namespace_id,
            idempotency_key="provenance-absent-source",
            identity_namespace_id=private.runtime_scope.identity_namespace_id,
            semantic_scope_id=private.runtime_scope.semantic_scope_id,
            summary="preactivation provenance-absent source", memory_type="reflection",
            user_id="aria", logical_step=30,
        )
        connection.execute(
            "INSERT INTO object_revision_governance VALUES (?,?,?,?,?,?,?,?)",
            (native_id_to_bytes(source.object_id), native_id_to_bytes(source.revision_id), 1, 0, 0, 0, 0, 0),
        )
        vector = np.asarray((0.0, 1.0, 0.0), dtype=np.float32).tobytes(order="C")
        representations = NativeRepresentationService(connection)
        pending = representations.create_representation_pending(
            idempotency_namespace_id=private.idempotency_namespace_id,
            idempotency_key="provenance-absent-e1-pending",
            request=RepresentationRequest(
                "OBJECT_REVISION", source.object_id, source.revision_id, None, None,
                "COMPAT_EMBEDDING", 1, "compat-embedding-v1", "RAW_VECTOR", "float32", 3,
                (), None, len(vector),
            ),
        )
        representations.establish_representation_integrity_expectation(
            idempotency_namespace_id=private.idempotency_namespace_id,
            idempotency_key="provenance-absent-e1-expectation",
            request=RepresentationIntegrityExpectationRequest(
                pending.representation_id, INTEGRITY_ALGORITHM_SHA256,
                sha256(vector).digest(), INTEGRITY_VALUE_ENCODING_RAW,
            ),
        )
        e1 = representations.publish_representation_ready(
            idempotency_namespace_id=private.idempotency_namespace_id,
            idempotency_key="provenance-absent-e1-ready",
            request=RepresentationReadyRequest(
                pending.representation_id, "COMPAT_EMBEDDING", 1,
                "compat-embedding-v1", "RAW_VECTOR", vector,
            ),
        )
        backfilled = NativeMemoryReinforcementService(connection).reinforce(
            NativeMemoryReinforcementRequest(
                legacy_source_namespace_id=private.runtime_scope.legacy_source_namespace_id,
                eid=source.eid, expected_revision_id=source.revision_id,
                expected_representation_id=e1.representation_id,
                idempotency_namespace_id=private.idempotency_namespace_id,
                idempotency_key="provenance-absent-reinforce", reinforcement_step=31,
                last_reinforced_ts=310, expected_dimension=3,
                direct_ingest_provenance_backfill=NativeProvenanceRecord(
                    "RUNTIME_PROVENANCE_V1", "direct_ingest", "user",
                    "DIRECT", "UNKNOWN", memory_role="INPUT", descriptive_notes="i4b1 fixture",
                ),
            )
        )
        row = connection.execute(
            """SELECT p.source_channel FROM object_revisions r
               JOIN provenance_records p ON p.provenance_id=r.provenance_id
               WHERE r.object_revision_id=?""",
            (native_id_to_bytes(backfilled.source.revision_id),),
        ).fetchone()
        assert row == ("direct_ingest",)
        assert NativeMemoryCompatibilityFacade(connection).get_memory_by_eid(
            legacy_source_namespace_id=private.runtime_scope.legacy_source_namespace_id,
            eid=source.eid,
        ).revision_id == backfilled.source.revision_id
    finally:
        qualified.close()


def test_i4b1_flush_failure_preserves_orphan_motif_but_not_canonical_memory(tmp_path: Path):
    qualified, connection, capability, private, _shared = _prepared(tmp_path)
    try:
        router = NativeFabricMemoryRouter(capability)
        audit_path = tmp_path / "synthetic_embed_audit.json"

        def write_synthetic_embed_audit(_eid: int) -> None:
            audit_path.write_text(json.dumps({"dirty": True}), encoding="utf-8")

        request = _request(
            key="flush-failure", precommit_spawn_observer=write_synthetic_embed_audit,
        )
        failed = _result(router, request, _test_stop_after="precommit_canonical_failure")
        assert failed.primary_outcome is not None
        witness = failed.primary_outcome
        assert (
            failed.stored, failed.eid, witness.final_storage_outcome,
            witness.create_failure_disposition, witness.primary_canonical_state_committed,
            witness.qualified_memory_eid,
        ) == (False, None, "NO_WRITE", "CANONICAL_FLUSH_FAILURE_STRUCTURED", False, 0)
        assert json.loads(audit_path.read_text(encoding="utf-8")) == {"dirty": True}
        with pytest.raises(SubstrateObjectNotFound, match="not canonical"):
            NativeMemoryCompatibilityFacade(connection).get_memory_by_eid(
                legacy_source_namespace_id=private.runtime_scope.legacy_source_namespace_id, eid=0,
            )
        assert NativeMemoryCompatibilityFacade(connection).search_by_embedding(
            legacy_source_namespace_id=private.runtime_scope.legacy_source_namespace_id,
            embedding=np.asarray((1.0, 0.0, 0.0), dtype=np.float32), dimension=3,
            representation_class="COMPAT_EMBEDDING", generation=1,
            derivation_contract_version="compat-embedding-v1", encoding_id="RAW_VECTOR",
            dtype="float32", top_k=3, user_id="aria",
        ) == ()
        assert NativePostWriteMemoryAccess(
            connection,
            legacy_source_namespace_id=private.runtime_scope.legacy_source_namespace_id,
            expected_dimension=3,
        ).list_current() == ()

        reader = NativeMotifRuntimeReader(connection)
        motifs = reader.list_runtime_motifs(
            motif_alias_namespace_id=private.motif_alias_namespace_id,
            domain_id="research", semantic_scope_id=private.runtime_scope.semantic_scope_id,
        )
        assert len(motifs) == 1 and motifs[0].read_model.member_count == 1
        assert reader.project_coherence_field_rows(
            motif_alias_namespace_id=private.motif_alias_namespace_id,
            domain_id="research", expected_dimension=3,
            semantic_scope_id=private.runtime_scope.semantic_scope_id,
        )[0]["members"] == 1
        assert reader.domain_centroid(
            motif_alias_namespace_id=private.motif_alias_namespace_id,
            domain_id="research", dimension=3,
            semantic_scope_id=private.runtime_scope.semantic_scope_id,
        ) == pytest.approx(np.asarray((1.0, 0.0, 0.0), dtype=np.float32))
        assert connection.execute(
            "SELECT revision_ordinal,existence_state FROM object_revisions "
            "WHERE object_id=? ORDER BY revision_ordinal",
            (native_id_to_bytes(witness.qualified_memory_object_id),),
        ).fetchall() == [(1, "PENDING"), (2, "ABORTED")]
        assert _result(router, request) == failed

        later = _result(router, _request(key="after-failure", vector=(0.0, 1.0, 0.0)))
        assert later.eid == 1
    finally:
        qualified.close()


def test_i4b1_attach_failure_aborts_reservation_without_motif_residue(tmp_path: Path, monkeypatch):
    qualified, connection, capability, private, _shared = _prepared(tmp_path)
    try:
        router = NativeFabricMemoryRouter(capability)
        request = _request(key="attach-failure")
        with monkeypatch.context() as patcher:
            patcher.setattr(
                NativeMotifService,
                "create_motif_with_member",
                lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("forced attach failure")),
            )
            with pytest.raises(NativePrecommitAttachFailure) as raised:
                router.route(request)
        witness = raised.value.witness
        assert (
            witness.final_storage_outcome,
            witness.create_failure_disposition,
            witness.primary_canonical_state_committed,
            witness.qualified_memory_eid,
        ) == ("NO_WRITE", "PRECOMMIT_MOTIF_ATTACH_FAILURE_RAISED", False, 0)
        with pytest.raises(NativePrecommitAttachFailure) as recovered:
            router.route(request)
        assert recovered.value.witness == witness
        assert connection.execute("SELECT count(*) FROM relationships").fetchone()[0] == 0
        assert connection.execute(
            "SELECT revision_ordinal,existence_state FROM object_revisions "
            "WHERE object_id=? ORDER BY revision_ordinal",
            (native_id_to_bytes(witness.qualified_memory_object_id),),
        ).fetchall() == [(1, "PENDING"), (2, "ABORTED")]
        assert NativeMotifRuntimeReader(connection).list_runtime_motifs(
            motif_alias_namespace_id=private.motif_alias_namespace_id,
            domain_id="research", semantic_scope_id=private.runtime_scope.semantic_scope_id,
        ) == ()
        later = _result(router, _request(key="after-attach-failure"))
        assert later.eid == 1
    finally:
        qualified.close()


def test_i4b1_external_symbol_owner_persists_before_canonical_commit(tmp_path: Path):
    qualified, connection, capability, private, _shared = _prepared(tmp_path)
    owner = TormentFabric(data_dir=str(tmp_path / "external-owner"))
    try:
        def persist_symbol(effect):
            return owner._apply_native_precommit_symbol_state(
                effect.workspace_id, effect.agent_id,
                primary_motif_id=effect.runtime_motif_id,
                current_tension=effect.current_tension,
                enrichment=dict(effect.enrichment),
            )

        router = NativeFabricMemoryRouter(capability)
        created = _result(router, _request(
            key="external-symbol-created", precommit_symbol_state_owner=persist_symbol,
        ))
        symbol_path = tmp_path / "external-owner" / "workspaces" / "i4b1-workspace" / "agents" / "aria" / "symbol_state.json"
        persisted = json.loads(symbol_path.read_text(encoding="utf-8"))
        canonical = NativeMemoryCompatibilityFacade(connection).get_memory_by_eid(
            legacy_source_namespace_id=private.runtime_scope.legacy_source_namespace_id,
            eid=created.eid,
        )
        assert canonical.payload["symbol_trace"] == persisted["symbol_trace"]

        failed = _result(router, _request(
            key="external-symbol-failed", vector=(0.0, 1.0, 0.0),
            precommit_symbol_state_owner=persist_symbol,
        ), _test_stop_after="precommit_canonical_failure")
        assert failed.primary_outcome is not None
        assert json.loads(symbol_path.read_text(encoding="utf-8"))["last_motif_id"] == "motif_research_0002"
        with pytest.raises(SubstrateObjectNotFound, match="not canonical"):
            NativeMemoryCompatibilityFacade(connection).get_memory_by_eid(
                legacy_source_namespace_id=private.runtime_scope.legacy_source_namespace_id,
                eid=failed.primary_outcome.qualified_memory_eid,
            )
    finally:
        owner.close()
        qualified.close()


def test_i4b1_restart_retains_failed_eid_and_orphan_motif_without_canonical_visibility(tmp_path: Path):
    qualified, connection, capability, private, _shared = _prepared(tmp_path)
    reopened = None
    try:
        request = _request(key="restart-flush-failure")
        failed = _result(
            NativeFabricMemoryRouter(capability), request,
            _test_stop_after="precommit_canonical_failure",
        )
        assert failed.primary_outcome is not None
        failed_eid = failed.primary_outcome.qualified_memory_eid
        assert failed_eid == 0
        database_path = qualified.database_path
        qualified.close()
        qualified = None

        reopened = open_existing_native_core_connection(database_path)
        reopened_connection = reopened.connection
        restarted = prepare_native_fabric_routing_capability(
            binding=capability.binding,
            connection=reopened_connection,
            routing_scopes=(private,),
            expected_core_id=capability.core_id,
        )
        facade = NativeMemoryCompatibilityFacade(reopened_connection)
        alias_state = reopened_connection.execute(
            """SELECT r.existence_state FROM legacy_object_aliases a
               JOIN objects o ON o.object_id=a.object_id
               JOIN object_revisions r ON r.object_revision_id=o.current_revision_id
               WHERE a.legacy_source_namespace_id=? AND a.alias_kind='EID' AND a.alias_value=?""",
            (native_id_to_bytes(private.runtime_scope.legacy_source_namespace_id), str(failed_eid)),
        ).fetchone()
        assert alias_state == ("ABORTED",)
        with pytest.raises(SubstrateObjectNotFound, match="not canonical"):
            facade.get_memory_by_eid(
                legacy_source_namespace_id=private.runtime_scope.legacy_source_namespace_id,
                eid=failed_eid,
            )
        assert facade.search_by_embedding(
            legacy_source_namespace_id=private.runtime_scope.legacy_source_namespace_id,
            embedding=np.asarray((1.0, 0.0, 0.0), dtype=np.float32), dimension=3,
            representation_class="COMPAT_EMBEDDING", generation=1,
            derivation_contract_version="compat-embedding-v1", encoding_id="RAW_VECTOR",
            dtype="float32", top_k=3, user_id="aria",
        ) == ()
        assert NativePostWriteMemoryAccess(
            reopened_connection,
            legacy_source_namespace_id=private.runtime_scope.legacy_source_namespace_id,
            expected_dimension=3,
        ).list_current() == ()
        motifs = NativeMotifRuntimeReader(reopened_connection).list_runtime_motifs(
            motif_alias_namespace_id=private.motif_alias_namespace_id,
            domain_id="research", semantic_scope_id=private.runtime_scope.semantic_scope_id,
        )
        assert len(motifs) == 1 and motifs[0].read_model.member_count == 1

        recovered = NativeFabricMemoryRouter(restarted).route(request)
        assert recovered.result is not None
        assert recovered.result.primary_outcome == failed.primary_outcome
        later = _result(
            NativeFabricMemoryRouter(restarted),
            _request(key="restart-after-failed-eid", vector=(0.0, 1.0, 0.0)),
        )
        assert later.eid == failed_eid + 1
    finally:
        if reopened is not None:
            reopened.close()
        if qualified is not None:
            qualified.close()


def test_i4b2_t0_pre_stage_a_failure_leaves_no_true_split_motif_residue(tmp_path: Path, monkeypatch):
    _disable_world_observer(monkeypatch)
    qualified, connection, capability, private, _shared = _prepared(tmp_path)
    try:
        router, motif, parent, request = _prepare_true_split_fixture(connection, capability, private)
        before_members = motif.list_current_motif_members(parent)
        monkeypatch.setattr(
            NativeMotifService,
            "attach_member_for_precommit_split",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("forced Stage A failure")),
        )

        with pytest.raises(NativePrecommitAttachFailure) as failed:
            router.route(request)

        assert failed.value.witness.create_failure_disposition == "PRECOMMIT_MOTIF_ATTACH_FAILURE_RAISED"
        assert len(motif.list_current_motif_members(parent)) == len(before_members)
        assert connection.execute(
            "SELECT count(*) FROM operations WHERE operation_kind LIKE 'NATIVE_I4B2_PRECOMMIT_SPLIT_%'"
        ).fetchone()[0] == 0
        assert _current_pending_or_aborted_payload(connection)["failure_stage"] == "I4B2_STAGE_0"
        assert capability.process_order.runtime_ids_for_testing(
            routing_scope=private, domain_id="research",
        ) == ("motif_research_0001",)
    finally:
        qualified.close()


def test_i4b2_reachable_true_split_uses_two_stage_precommit_topology(tmp_path: Path, monkeypatch):
    # The synthetic historical members below deliberately omit structural
    # provenance, which is immaterial to the motif topology under test.  Keep
    # the world observer outside this focused, motif-only qualification.
    import torment_service.substrate.native_world_runtime as world_module

    monkeypatch.setattr(world_module.NativeWorldRuntime, "ensure_initialized", lambda _self: None)
    monkeypatch.setattr(world_module.NativeWorldRuntime, "register_fresh_created", lambda _self, **_kwargs: None)
    qualified, connection, capability, private, _shared = _prepared(tmp_path)
    try:
        router = NativeFabricMemoryRouter(capability)
        seed = _result(router, _request(key="i4b1-split-seed", vector=(1.0, 0.0, 0.0)))
        motif = NativeMotifService(connection)
        parent = motif.resolve_motif_alias(
            motif_alias_namespace_id=private.motif_alias_namespace_id,
            runtime_motif_id=seed.motifs[0],
        )
        facade = NativeMemoryCompatibilityFacade(connection)
        for ordinal, vector in enumerate(
            [(1.0, 0.0, 0.0)] * 47 + [(-1.0, 0.0, 0.0)] * 47, start=2,
        ):
            raw = np.asarray(vector, dtype=np.float32)
            source = facade.finalize_memory_draft(facade.begin_memory_draft(
                legacy_source_namespace_id=private.runtime_scope.legacy_source_namespace_id,
                idempotency_namespace_id=private.idempotency_namespace_id,
                idempotency_key=f"i4b1-split-source:{ordinal}",
                identity_namespace_id=private.runtime_scope.identity_namespace_id,
                semantic_scope_id=private.runtime_scope.semantic_scope_id,
                summary=f"i4b1 split source {ordinal}", memory_type="reflection", logical_step=ordinal,
                embedding_request=CompatibilityEmbeddingPublicationRequest(
                    raw.tobytes(), "COMPAT_EMBEDDING", 1, "compat-embedding-v1", "RAW_VECTOR",
                    dtype="float32", dimension=3,
                ),
            )).source
            current = motif.get_current_motif(parent)
            motif.add_motif_member(
                idempotency_namespace_id=private.idempotency_namespace_id,
                idempotency_key=f"i4b1-split-member:{ordinal}",
                motif_alias_namespace_id=private.motif_alias_namespace_id,
                membership_identity_namespace_id=private.membership_identity_namespace_id,
                motif_object_id=parent, expected_motif_revision_id=current.motif_revision_id,
                state=replace(current.state, last_active_ts=current.state.last_active_ts + 1),
                member_object_id=source.object_id,
            )
        result = _result(router, _request(
            key="i4b1-qualified-true-split", vector=(0.7, 0.714, 0.0), attach_threshold=0.72,
        ))
        assert result.primary_outcome is not None
        assert (
            result.stored, result.reinforced, result.created_motif,
            result.precommit_true_split, result.primary_outcome.final_storage_outcome,
        ) == (True, False, None, True, "CREATED_NEW")
        assert result.motifs[0] == "motif_research_0001"
        assert result.motifs[1].startswith("motif_research_0001_split_")
        rows = connection.execute(
            "SELECT operation_kind FROM operations WHERE idempotency_key LIKE 'I4B2:%' ORDER BY operation_kind"
        ).fetchall()
        assert rows == [
            ("NATIVE_I4B2_PRECOMMIT_SPLIT_ATTACH",),
            ("NATIVE_I4B2_PRECOMMIT_SPLIT_FINALIZE",),
        ]
        child = motif.resolve_motif_alias(
            motif_alias_namespace_id=private.motif_alias_namespace_id,
            runtime_motif_id=result.motifs[1],
        )
        candidate = NativeMemoryCompatibilityFacade(connection).get_memory_by_eid(
            legacy_source_namespace_id=private.runtime_scope.legacy_source_namespace_id,
            eid=result.eid,
        )
        assert candidate is not None
        parent_members = {member.member_object_id for member in motif.list_current_motif_members(parent)}
        child_members = {member.member_object_id for member in motif.list_current_motif_members(child)}
        assert candidate.object_id in parent_members | child_members
        assert candidate.object_id not in parent_members & child_members
        parent_state = motif.get_current_motif(parent).state
        child_state = motif.get_current_motif(child).state
        # The partition controls member count, centroid, strength, stability,
        # density and therefore gravity inputs; no I4B-2 formula exists.
        assert len(parent_members) + len(child_members) == 96
        assert parent_state.strength == pytest.approx(split_strength(len(parent_members), floor=.18))
        assert child_state.strength == pytest.approx(split_strength(len(child_members), floor=.15))
        assert parent_state.stability_score == child_state.stability_score
        assert motif_density(len(parent_members)) > 0.0
        assert motif_density(len(child_members)) > 0.0
        reader = NativeMotifRuntimeReader(connection)
        domain_centroid = reader.domain_centroid(
            motif_alias_namespace_id=private.motif_alias_namespace_id,
            domain_id="research",
            dimension=3,
            semantic_scope_id=private.runtime_scope.semantic_scope_id,
        )
        assert domain_centroid is not None and np.isfinite(domain_centroid).all()
    finally:
        qualified.close()


def test_i4b2_stage_a_crash_replays_the_stored_partition_without_replanning(tmp_path: Path, monkeypatch):
    _disable_world_observer(monkeypatch)
    qualified, connection, capability, private, _shared = _prepared(tmp_path)
    reopened = None
    try:
        router, motif, parent, request = _prepare_true_split_fixture(connection, capability, private)
        with pytest.raises(RuntimeError, match="after precommit split stage A"):
            router.route(request, _test_stop_after="precommit_split_after_stage_a")
        stage_a = connection.execute(
            "SELECT count(*) FROM operations WHERE operation_kind='NATIVE_I4B2_PRECOMMIT_SPLIT_ATTACH'"
        ).fetchone()[0]
        stage_b = connection.execute(
            "SELECT count(*) FROM operations WHERE operation_kind='NATIVE_I4B2_PRECOMMIT_SPLIT_FINALIZE'"
        ).fetchone()[0]
        pending = connection.execute(
            "SELECT count(*) FROM objects o JOIN object_revisions r ON r.object_id=o.object_id "
            "AND r.object_revision_id=o.current_revision_id AND r.revision_ordinal=o.current_revision_ordinal "
            "WHERE o.object_kind='LEGACY_CORE_NODE' AND r.existence_state='PENDING'"
        ).fetchone()
        assert (stage_a, stage_b, pending) == (1, 0, (1,))
        assert len(motif.list_current_motif_members(parent)) == 96

        # A restart recreates both the connection and process-order owner.  The
        # persisted Stage-A operation is the sole authority for the Stage-B
        # partition; recovery does not plan against the changed parent.
        database_path = qualified.database_path
        qualified.close()
        qualified = None
        reopened = open_existing_native_core_connection(database_path)
        capability = prepare_native_fabric_routing_capability(
            binding=capability.binding,
            connection=reopened.connection,
            routing_scopes=(private,),
            expected_core_id=capability.core_id,
        )
        recovered = _result(NativeFabricMemoryRouter(capability), request)
        assert recovered.precommit_true_split is True
        assert recovered.motifs[0] == "motif_research_0001"
        assert len(recovered.motifs) == 2
        assert reopened.connection.execute(
            "SELECT count(*) FROM operations WHERE operation_kind='NATIVE_I4B2_PRECOMMIT_SPLIT_ATTACH'"
        ).fetchone()[0] == 1
        assert reopened.connection.execute(
            "SELECT count(*) FROM operations WHERE operation_kind='NATIVE_I4B2_PRECOMMIT_SPLIT_FINALIZE'"
        ).fetchone()[0] == 1
        assert capability.process_order.runtime_ids_for_testing(
            routing_scope=private, domain_id="research",
        ) == recovered.motifs
    finally:
        if reopened is not None:
            reopened.close()
        if qualified is not None:
            qualified.close()


def test_i4b2_stage_b_and_canonical_failure_recover_exact_output_topology(tmp_path: Path, monkeypatch):
    _disable_world_observer(monkeypatch)
    qualified, connection, capability, private, _shared = _prepared(tmp_path)
    try:
        router, _motif, _parent, request = _prepare_true_split_fixture(connection, capability, private)
        with pytest.raises(RuntimeError, match="after precommit split stage B"):
            router.route(request, _test_stop_after="precommit_split_after_stage_b")
        staged = connection.execute(
            "SELECT count(*) FROM objects o JOIN object_revisions r ON r.object_id=o.object_id "
            "AND r.object_revision_id=o.current_revision_id AND r.revision_ordinal=o.current_revision_ordinal "
            "WHERE o.object_kind='LEGACY_CORE_NODE' AND r.existence_state='PENDING'"
        ).fetchone()
        assert staged == (1,)
        failed = _result(
            router, request, _test_stop_after="precommit_canonical_failure",
        )
        assert failed.primary_outcome is not None
        assert (
            failed.stored, failed.created_motif, failed.precommit_true_split,
            failed.primary_outcome.create_failure_disposition, len(failed.motifs),
        ) == (False, None, True, "CANONICAL_FLUSH_FAILURE_STRUCTURED", 2)
        import torment_service.substrate.fabric_native_routing as routing_module
        monkeypatch.setattr(
            routing_module,
            "_runtime_motif_ids_for_member",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("split recovery scanned memberships")),
        )
        assert _result(router, request) == failed
    finally:
        qualified.close()


def test_i4b2_canonical_recovery_uses_stage_b_outputs_not_member_scan(tmp_path: Path, monkeypatch):
    _disable_world_observer(monkeypatch)
    qualified, connection, capability, private, _shared = _prepared(tmp_path)
    try:
        router, _motif, _parent, request = _prepare_true_split_fixture(connection, capability, private)
        with pytest.raises(RuntimeError, match="committed native new-memory source"):
            router.route(request, _test_stop_after="source")

        import torment_service.substrate.fabric_native_routing as routing_module

        monkeypatch.setattr(
            routing_module,
            "_runtime_motif_ids_for_member",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(
                AssertionError("true-split canonical recovery scanned memberships")
            ),
        )
        recovered = _result(router, request)
        assert (recovered.stored, recovered.precommit_true_split, recovered.created_motif) == (True, True, None)
        assert len(recovered.motifs) == 2
        assert connection.execute(
            "SELECT count(*) FROM operations WHERE operation_kind='NATIVE_I4B2_PRECOMMIT_SPLIT_FINALIZE'"
        ).fetchone()[0] == 1
    finally:
        qualified.close()


def test_i4b2_canonical_replay_preserves_the_original_create_disposition(tmp_path: Path, monkeypatch):
    _disable_world_observer(monkeypatch)
    qualified, connection, capability, private, _shared = _prepared(tmp_path)
    try:
        router, _motif, _parent, request = _prepare_true_split_fixture(connection, capability, private)
        first = _result(router, request)
        replay = _result(router, request)
        assert (first.stored, first.reinforced, first.created_motif, first.precommit_true_split) == (
            True, False, None, True,
        )
        assert (replay.stored, replay.reinforced, replay.created_motif, replay.precommit_true_split) == (
            True, False, None, True,
        )
        assert first.motifs == replay.motifs
        assert first.primary_outcome is not None and replay.primary_outcome is not None
        assert (
            replay.primary_outcome.attempt_origin,
            replay.primary_outcome.reinforcement_disposition,
            replay.primary_outcome.final_storage_outcome,
        ) == (
            first.primary_outcome.attempt_origin,
            first.primary_outcome.reinforcement_disposition,
            "CREATED_NEW",
        )
    finally:
        qualified.close()


def test_i4b2_stage_b_moves_the_stored_candidate_to_child_without_duplication(
    tmp_path: Path,
    monkeypatch,
):
    _disable_world_observer(monkeypatch)
    monkeypatch.setenv("TORMENT_REINFORCE_SIM_THRESHOLD", "1.1")
    qualified, connection, capability, private, _shared = _prepared(tmp_path)
    try:
        router, motif, parent, request = _prepare_true_split_fixture(connection, capability, private)
        request = replace(
            request,
            native_operation_key=f"{request.native_operation_key}:child",
            incoming_embedding=(0.7, 0.714, 0.0),
            attach_threshold=0.0,
        )
        with pytest.raises(RuntimeError, match="after precommit split stage A"):
            router.route(request, _test_stop_after="precommit_split_after_stage_a")

        intent = _split_operation_intent(connection, "NATIVE_I4B2_PRECOMMIT_SPLIT_ATTACH")
        assert intent["final_split"]["candidate_in_child"] is True
        candidate_row = connection.execute(
            """SELECT o.object_id FROM objects o JOIN object_revisions r
                 ON r.object_id=o.object_id AND r.object_revision_id=o.current_revision_id
                AND r.revision_ordinal=o.current_revision_ordinal
                WHERE o.object_kind='LEGACY_CORE_NODE' AND r.existence_state='PENDING'"""
        ).fetchone()
        assert candidate_row is not None
        candidate_object_id = native_id_from_bytes(candidate_row[0])
        stage_a_member = next(
            member for member in motif.list_current_motif_members(parent)
            if member.member_object_id == candidate_object_id
        )

        result = _result(router, request)
        child = motif.resolve_motif_alias(
            motif_alias_namespace_id=private.motif_alias_namespace_id,
            runtime_motif_id=result.motifs[1],
        )
        parent_members = {
            member.member_object_id: member.relationship_id
            for member in motif.list_current_motif_members(parent)
        }
        child_members = {
            member.member_object_id: member.relationship_id
            for member in motif.list_current_motif_members(child)
        }
        assert candidate_object_id not in parent_members
        assert child_members[candidate_object_id] != stage_a_member.relationship_id
    finally:
        qualified.close()


def test_i4b2_stage_b_keeps_a_parent_candidate_current_without_duplication(tmp_path: Path, monkeypatch):
    """Exercise Stage B's explicit candidate-in-parent storage contract.

    The policy fixture reaches the child branch above.  This focused service
    test supplies the complementary already-attached plan, proving that Stage
    B retains the Stage-A relationship instead of manufacturing a second one.
    """
    _disable_world_observer(monkeypatch)
    qualified, connection, capability, private, _shared = _prepared(tmp_path)
    try:
        router, motif, parent, request = _prepare_true_split_fixture(connection, capability, private)
        with pytest.raises(RuntimeError, match="after precommit split stage A"):
            router.route(request, _test_stop_after="precommit_split_after_stage_a")

        from torment_service.substrate.motifs import _split_plan_from_intent

        intent = _split_operation_intent(connection, "NATIVE_I4B2_PRECOMMIT_SPLIT_ATTACH")
        plan = replace(_split_plan_from_intent(intent["final_split"]), candidate_in_child=False)
        candidate_row = connection.execute(
            """SELECT o.object_id FROM objects o JOIN object_revisions r
                 ON r.object_id=o.object_id AND r.object_revision_id=o.current_revision_id
                AND r.revision_ordinal=o.current_revision_ordinal
                WHERE o.object_kind='LEGACY_CORE_NODE' AND r.existence_state='PENDING'"""
        ).fetchone()
        assert candidate_row is not None
        candidate_object_id = native_id_from_bytes(candidate_row[0])
        stage_a_member = next(
            member for member in motif.list_current_motif_members(parent)
            if member.member_object_id == candidate_object_id
        )
        result = motif.finalize_precommit_attached_split(
            idempotency_namespace_id=private.idempotency_namespace_id,
            idempotency_key="i4b2-direct-parent-candidate",
            motif_identity_namespace_id=private.motif_identity_namespace_id,
            membership_identity_namespace_id=private.membership_identity_namespace_id,
            motif_alias_namespace_id=private.motif_alias_namespace_id,
            plan=plan,
            attached_parent_revision_id=motif.get_current_motif(parent).motif_revision_id,
            attached_candidate_membership_id=stage_a_member.relationship_id,
            request_identity={"fixture": "i4b2-direct-parent-candidate"},
        )
        child_members = motif.list_current_motif_members(result.child_motif_object_id)
        parent_members = motif.list_current_motif_members(parent)
        assert any(
            member.member_object_id == candidate_object_id
            and member.relationship_id == stage_a_member.relationship_id
            for member in parent_members
        )
        assert all(member.member_object_id != candidate_object_id for member in child_members)
    finally:
        qualified.close()


def test_i4b2_stage_b_failure_records_instrumented_stage_count(tmp_path: Path, monkeypatch):
    _disable_world_observer(monkeypatch)
    qualified, connection, capability, private, _shared = _prepared(tmp_path)
    try:
        router, motif, parent, request = _prepare_true_split_fixture(connection, capability, private)
        original = NativeMotifService.finalize_precommit_attached_split

        def fail_after_child_creation(self, *args, **kwargs):
            kwargs["_test_fail_after"] = "child_object"
            return original(self, *args, **kwargs)

        monkeypatch.setattr(NativeMotifService, "finalize_precommit_attached_split", fail_after_child_creation)
        with pytest.raises(NativePrecommitAttachFailure):
            router.route(request)
        # The Stage-B semantic transaction rolled back, so Stage A is the only
        # surviving topology: the parent still holds the candidate and no
        # child alias/current relationship was published.
        assert len(motif.list_current_motif_members(parent)) == 96
        assert connection.execute(
            "SELECT count(*) FROM operations WHERE operation_kind='NATIVE_I4B2_PRECOMMIT_SPLIT_FINALIZE'"
        ).fetchone()[0] == 0
        assert _current_pending_or_aborted_payload(connection)["failure_stage"] == "I4B2_STAGE_1"
        assert capability.process_order.runtime_ids_for_testing(
            routing_scope=private, domain_id="research",
        ) == ("motif_research_0001",)
    finally:
        qualified.close()


def test_i4b1_live_motif_order_appends_then_recovers_lexically(tmp_path: Path):
    qualified, connection, capability, private, _shared = _prepared(tmp_path)
    try:
        router = NativeFabricMemoryRouter(capability)
        assert _result(router, _request(key="first-motif", vector=(1.0, 0.0, 0.0))).motifs == (
            "motif_research_0001",
        )
        assert _result(router, _request(key="second-motif", vector=(0.0, 1.0, 0.0))).motifs == (
            "motif_research_0002",
        )
        assert capability.process_order.runtime_ids_for_testing(
            routing_scope=private, domain_id="research"
        ) == ("motif_research_0001", "motif_research_0002")
        restarted = prepare_native_fabric_routing_capability(
            binding=capability.binding,
            connection=connection,
            routing_scopes=(private,),
            expected_core_id=capability.core_id,
        )
        with restarted.process_order.locked_catalog(
            reader=NativeMotifRuntimeReader(connection), routing_scope=private, domain_id="research",
        ) as catalog:
            assert tuple(item.read_model.runtime_motif_id for item in catalog) == (
                "motif_research_0001", "motif_research_0002",
            )
    finally:
        qualified.close()
