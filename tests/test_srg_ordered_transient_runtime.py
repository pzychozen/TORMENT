"""A3D5 qualification for ordered, process-local SRG collision runtime state."""
from __future__ import annotations

from hashlib import sha256
import logging
from pathlib import Path
from types import MappingProxyType, SimpleNamespace

import numpy as np
import pytest

from torment_service.kernel.seed_entities import SeedEntity
from torment_service.memory_graph import MemoryGraph
from torment_service.memory_runtime_access import (
    LegacyPostWriteMemoryAccess,
    RuntimeMemoryEmbedding,
    RuntimeMemoryGovernanceView,
    RuntimeMemoryProvenanceView,
    RuntimeMemoryView,
)
from torment_service.post_write_runtime import (
    FabricPostWriteContext,
    LegacyFabricPostWriteAdapter,
    LegacyFabricPostWriteDependencies,
    PostWriteStorageOutcome,
)
from torment_service.srg_runtime_state import LegacySRGTransientRuntime
from torment_service.substrate.compat import NativeMemoryCompatibilityFacade
from torment_service.substrate import compat as compat_module
from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.errors import SubstrateInvariantViolation
from torment_service.substrate.ids import generate_native_id, native_id_to_bytes
from torment_service.substrate.native_memory_runtime_access import NativePostWriteMemoryAccess
from torment_service.substrate.native_srg_runtime import NativeSRGTransientRuntime
from torment_service.substrate.objects import NativeObjectService, ObjectState
from torment_service.substrate.representations import (
    INTEGRITY_ALGORITHM_SHA256,
    INTEGRITY_VALUE_ENCODING_RAW,
    NativeRepresentationService,
    RepresentationIntegrityExpectationRequest,
    RepresentationReadyRequest,
    RepresentationRequest,
)
from torment_service.substrate.schema import create_schema


def _id():
    return generate_native_id()


def _database(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "a3d5.db")
    create_schema(qualified.connection)
    connection = qualified.connection
    identity, scope, idem, namespace = (_id() for _ in range(4))
    for table, identifier, label in (
        ("identity_namespaces", identity, "a3d5-identities"),
        ("semantic_scopes", scope, "a3d5-scope"),
        ("idempotency_namespaces", idem, "a3d5-idempotency"),
        ("legacy_source_namespaces", namespace, "a3d5-legacy-source"),
    ):
        connection.execute(
            f"INSERT INTO {table} VALUES ({'?,?,0' if table != 'idempotency_namespaces' else '?,?'})",
            (native_id_to_bytes(identifier), label),
        )
    return qualified, connection, identity, scope, idem, namespace


def _srg(*, R: float, band: int, L: float, heartbeat: str) -> dict[str, object]:
    return {
        "R": R, "R_band": band, "R_frequency": 0.244, "L": L,
        "L_amplitude": 0.2, "L_phase": -1.1 if heartbeat == "A" else -1.9,
        "heartbeat_class": heartbeat, "gamma": 0.08699, "is_crystal": False,
        "srg_step": 0, "last_collision_step": -1,
    }


def _provenance(connection):
    value = _id()
    connection.execute(
        "INSERT INTO provenance_records VALUES (?,?,?,?,?,?,?,?,?,?)",
        (
            native_id_to_bytes(value), "RUNTIME_PROVENANCE_V1", "user_input", "user",
            "direct_ingest", "KNOWN", None, None, None, None,
        ),
    )
    return value


def _memory(connection, identity, scope, idem, namespace, key, *, srg_state):
    return NativeMemoryCompatibilityFacade(connection).create_memory_state(
        legacy_source_namespace_id=namespace,
        idempotency_namespace_id=idem,
        idempotency_key=f"memory:{key}",
        identity_namespace_id=identity,
        semantic_scope_id=scope,
        summary=f"memory {key}",
        memory_type="episodic",
        memory_class="core",
        strength=0.8,
        confidence=0.9,
        half_life_days=0.0,
        user_id="aria",
        logical_step=3,
        extra_payload={"srg": srg_state, "ordinary": key},
        governance_state="DERIVED",
        provenance_id=_provenance(connection),
    )


def _ready(connection, idem, source, key, vector):
    payload = np.asarray(vector, dtype=np.float32).reshape(-1).tobytes(order="C")
    service = NativeRepresentationService(connection)
    pending = service.create_representation_pending(
        idempotency_namespace_id=idem,
        idempotency_key=f"pending:{key}",
        request=RepresentationRequest(
            "OBJECT_REVISION", source.object_id, source.revision_id, None, None,
            "COMPAT_EMBEDDING", 1, "compat-embedding-v1", "RAW_VECTOR",
            "float32", 3, (), None, len(payload),
        ),
    )
    service.establish_representation_integrity_expectation(
        idempotency_namespace_id=idem,
        idempotency_key=f"expect:{key}",
        request=RepresentationIntegrityExpectationRequest(
            pending.representation_id,
            INTEGRITY_ALGORITHM_SHA256,
            sha256(payload).digest(),
            INTEGRITY_VALUE_ENCODING_RAW,
        ),
    )
    service.publish_representation_ready(
        idempotency_namespace_id=idem,
        idempotency_key=f"ready:{key}",
        request=RepresentationReadyRequest(
            pending.representation_id, "COMPAT_EMBEDDING", 1,
            "compat-embedding-v1", "RAW_VECTOR", payload,
        ),
    )


def _counts(connection) -> tuple[int, ...]:
    return tuple(
        connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
        for table in (
            "objects", "object_revisions", "relationships", "relationship_revisions",
            "representations", "operations", "semantic_transitions",
            "representation_state_effects", "integrity_measurements",
            "object_revision_governance", "provenance_records",
            "relationship_revision_effects", "object_revision_effects",
        )
    )


class _ForbiddenGraph:
    @property
    def entities(self):
        raise AssertionError("SRG consumer directly enumerated graph entities")


class _NoWorldRuntime:
    def advance_for_post_write(self, *, step: int) -> None:
        raise AssertionError(f"SRG consumer unexpectedly stepped world {step}")


def _adapter(memory_access, memory_enumeration, srg_runtime):
    owner = SimpleNamespace(_srg_enable=True, _log=logging.getLogger("a3d5-srg"))
    dependencies = LegacyFabricPostWriteDependencies(
        owner=owner,
        workspace=None,
        graph=_ForbiddenGraph(),
        world_runtime=_NoWorldRuntime(),
        memory_access=memory_access,
        memory_enumeration=memory_enumeration,
        srg_runtime=srg_runtime,
        embedding_dimension=3,
        identity=None,
        motif_registry=None,
        motif_runtime=None,
        model_state=None,
        kernel_context=None,
        agent_key="a3d5",
        detect_canon_conflict=lambda *_args: (False, 0.0, ""),
        proposal_allowed=lambda **_kwargs: False,
        random_chance=lambda _chance: False,
        save_checkpoint=lambda **_kwargs: None,
        build_motif_summary=lambda **_kwargs: None,
        build_shard_snapshot=lambda **_kwargs: None,
        hivemind_log=logging.getLogger("a3d5-hivemind"),
    )
    return LegacyFabricPostWriteAdapter(dependencies)


def _context(eid: int, srg_state: dict[str, object], *, step: int = 11):
    return FabricPostWriteContext.make(
        workspace_id="ws", agent_id="aria", scope="private", chosen_domain="personal",
        step=step, storage_outcome=PostWriteStorageOutcome.CREATED_NEW, stored=True,
        eid=eid, created_motif=None, motif_ids=(), half_life_days=20.0,
        summary="incoming", embedding=np.asarray((1.0, 0.0, 0.0), dtype=np.float32),
        memory_class="core", memory_type="episodic", strength=0.8, confidence=0.9,
        promotion_score=0.9, stability_delta=0.1, tri_mod={}, debug={},
        srg_state=srg_state, phase_durations={}, state_symbol=None, affect_tag=None,
        affect_conf=None, skip_packet_emission=True,
    )


def _legacy_equivalent(tmp_path: Path, connection, namespace, entries):
    graph = MemoryGraph(str(tmp_path), embedder=SimpleNamespace(dim=3, embed=lambda _text: np.zeros(3)))
    reads = NativeMemoryCompatibilityFacade(connection)
    for eid, source, vector in entries:
        payload = dict(
            reads.get_memory_by_eid(
                legacy_source_namespace_id=namespace, eid=eid,
            ).payload
        )
        graph.entities[eid] = SeedEntity(
            eid=eid, born_step=0, channel=0, pos=np.zeros(3), vel=np.zeros(3),
            vel0=np.zeros(3), payload=payload,
        )
        np.save(graph._emb_path(eid), np.asarray(vector, dtype=np.float32))
    return graph, LegacyPostWriteMemoryAccess(graph, expected_dimension=3)


def _renumber_aliases(connection, namespace, values):
    for source, eid in values:
        connection.execute(
            """
            UPDATE legacy_object_aliases SET alias_value=?
             WHERE legacy_source_namespace_id=? AND alias_kind='EID' AND object_id=?
            """,
            (str(eid), native_id_to_bytes(namespace), native_id_to_bytes(source.object_id)),
        )


def test_native_and_legacy_srg_collision_have_ordered_selection_and_transient_parity(tmp_path: Path):
    qualified, connection, identity, scope, idem, namespace = _database(tmp_path)
    try:
        first = _memory(connection, identity, scope, idem, namespace, "first", srg_state=_srg(R=0.10, band=1, L=10.0, heartbeat="A"))
        second = _memory(connection, identity, scope, idem, namespace, "second", srg_state=_srg(R=0.20, band=1, L=12.0, heartbeat="B"))
        incoming = _memory(connection, identity, scope, idem, namespace, "incoming", srg_state=_srg(R=0.30, band=1, L=6.0, heartbeat="B"))
        for source, key in ((first, "first"), (second, "second"), (incoming, "incoming")):
            _ready(connection, idem, source, key, (1.0, 0.0, 0.0))
        # The structural ordinal was published at creation.  Test a source
        # compatibility namespace where numeric EID order is different.
        _renumber_aliases(connection, namespace, ((first, 42), (second, 7), (incoming, 100)))
        native_reads = NativePostWriteMemoryAccess(
            connection, legacy_source_namespace_id=namespace, expected_dimension=3,
        )
        assert [view.eid for view in native_reads.list_current()] == [42, 7, 100]
        graph, legacy_reads = _legacy_equivalent(
            tmp_path / "legacy", connection, namespace,
            ((42, first, (1.0, 0.0, 0.0)), (7, second, (1.0, 0.0, 0.0)), (100, incoming, (1.0, 0.0, 0.0))),
        )
        assert [view.eid for view in legacy_reads.list_current()] == [42, 7, 100]

        native_runtime = NativeSRGTransientRuntime(
            connection, legacy_source_namespace_id=namespace,
        )
        native_adapter = _adapter(native_reads, native_reads, native_runtime)
        legacy_runtime = LegacySRGTransientRuntime(graph)
        legacy_adapter = _adapter(legacy_reads, legacy_reads, legacy_runtime)
        durable_before = _counts(connection)
        context = _context(100, _srg(R=0.30, band=1, L=6.0, heartbeat="B"))

        native_adapter._run_srg_collision(context)
        legacy_adapter._run_srg_collision(context)
        assert _counts(connection) == durable_before
        native_first = native_runtime.effective_srg_state(native_reads.get_current(42))
        native_second = native_runtime.effective_srg_state(native_reads.get_current(7))
        native_incoming = native_runtime.effective_srg_state(native_reads.get_current(100))
        assert native_first is not None and native_second is not None and native_incoming is not None
        # Equal vectors select first qualified enumeration entry, not EID 7.
        assert native_first["last_collision_step"] == 11
        assert native_second["last_collision_step"] == -1
        assert native_incoming["last_collision_step"] == 11
        assert native_runtime.effective_collision_report(native_reads.get_current(100))["collision"] is True
        assert graph.entities[42].payload["srg"] == dict(native_first)
        assert graph.entities[7].payload["srg"] == dict(native_second)
        assert graph.entities[100].payload["srg"] == dict(native_incoming)
        first_R_after_one = float(native_first["R"])

        # The second collision sees the existing process's effective overlay.
        native_adapter._run_srg_collision(_context(100, _srg(R=0.30, band=1, L=6.0, heartbeat="B"), step=12))
        legacy_adapter._run_srg_collision(_context(100, _srg(R=0.30, band=1, L=6.0, heartbeat="B"), step=12))
        assert float(native_runtime.effective_srg_state(native_reads.get_current(42))["R"]) != first_R_after_one
        assert graph.entities[42].payload["srg"] == dict(native_runtime.effective_srg_state(native_reads.get_current(42)))
        assert _counts(connection) == durable_before

        # A new provider represents restart and exposes the unchanged durable baseline.
        restarted = NativeSRGTransientRuntime(connection, legacy_source_namespace_id=namespace)
        assert restarted.effective_srg_state(native_reads.get_current(42))["last_collision_step"] == -1
        assert restarted.effective_srg_state(native_reads.get_current(100))["last_collision_step"] == -1
        assert restarted.effective_collision_report(native_reads.get_current(100)) is None
    finally:
        qualified.close()


def test_native_order_is_immutable_across_successors_appends_for_new_memory_and_fails_closed(tmp_path: Path):
    qualified, connection, identity, scope, idem, namespace = _database(tmp_path)
    try:
        first = _memory(connection, identity, scope, idem, namespace, "first", srg_state=_srg(R=0.1, band=1, L=9.0, heartbeat="A"))
        second = _memory(connection, identity, scope, idem, namespace, "second", srg_state=_srg(R=0.2, band=1, L=9.0, heartbeat="B"))
        _renumber_aliases(connection, namespace, ((first, 42), (second, 7)))
        reads = NativePostWriteMemoryAccess(connection, legacy_source_namespace_id=namespace, expected_dimension=3)
        assert [view.eid for view in reads.list_current()] == [42, 7]
        NativeMemoryCompatibilityFacade(connection).patch_memory_state(
            legacy_source_namespace_id=namespace, eid=7, patch={"ordinary": "successor"},
            idempotency_namespace_id=idem, idempotency_key="advance-second",
        )
        assert [view.eid for view in reads.list_current()] == [42, 7]
        appended = _memory(connection, identity, scope, idem, namespace, "appended", srg_state=_srg(R=0.3, band=1, L=9.0, heartbeat="A"))
        assert [view.eid for view in reads.list_current()] == [42, 7, appended.eid]
        assert connection.execute(
            "SELECT runtime_ordinal FROM memory_runtime_enumeration_orders "
            "WHERE legacy_source_namespace_id=? ORDER BY runtime_ordinal",
            (native_id_to_bytes(namespace),),
        ).fetchall() == [(0,), (1,), (2,)]

        unqualified = NativeObjectService(connection).create_object(
            idempotency_namespace_id=idem,
            idempotency_key="unqualified-order",
            state=ObjectState(identity, scope, "LEGACY_CORE_NODE", "EXISTS", "UNSET", True, "UNKNOWN", "NOT_APPLICABLE", {"summary": "unqualified"}, "JSON"),
        )
        connection.execute(
            "INSERT INTO legacy_object_aliases VALUES (?,'EID','999',?)",
            (native_id_to_bytes(namespace), native_id_to_bytes(unqualified.object_id)),
        )
        with pytest.raises(SubstrateInvariantViolation, match="runtime enumeration order"):
            reads.list_current()
    finally:
        qualified.close()


def test_native_memory_creation_rolls_back_if_its_required_runtime_order_cannot_publish(tmp_path: Path, monkeypatch):
    qualified, connection, identity, scope, idem, namespace = _database(tmp_path)
    try:
        before = tuple(
            connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            for table in ("objects", "object_revisions", "legacy_object_aliases", "memory_runtime_enumeration_orders", "operations")
        )

        def fail(*_args, **_kwargs):
            raise RuntimeError("forced runtime-order publication failure")

        monkeypatch.setattr(compat_module, "publish_runtime_order", fail)
        with pytest.raises(RuntimeError, match="forced runtime-order publication failure"):
            _memory(connection, identity, scope, idem, namespace, "rollback", srg_state=_srg(R=0.1, band=1, L=9.0, heartbeat="A"))
        after = tuple(
            connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            for table in ("objects", "object_revisions", "legacy_object_aliases", "memory_runtime_enumeration_orders", "operations")
        )
        assert after == before
    finally:
        qualified.close()


def test_native_srg_overlay_fails_closed_when_current_revision_advances(tmp_path: Path):
    qualified, connection, identity, scope, idem, namespace = _database(tmp_path)
    try:
        source = _memory(connection, identity, scope, idem, namespace, "current", srg_state=_srg(R=0.1, band=1, L=9.0, heartbeat="A"))
        reads = NativePostWriteMemoryAccess(connection, legacy_source_namespace_id=namespace, expected_dimension=3)
        view = reads.get_current(source.eid)
        runtime = NativeSRGTransientRuntime(connection, legacy_source_namespace_id=namespace)
        state = runtime.effective_srg_state(view)
        runtime.apply_collision(
            existing=view, incoming=view, existing_state=state, incoming_state=state,
            incoming_report={"collision": True},
        )
        NativeMemoryCompatibilityFacade(connection).patch_memory_state(
            legacy_source_namespace_id=namespace, eid=source.eid, patch={"ordinary": "advanced"},
            idempotency_namespace_id=idem, idempotency_key="advance-under-overlay",
        )
        with pytest.raises(SubstrateInvariantViolation, match="current revision changed"):
            runtime.effective_srg_state(reads.get_current(source.eid))
    finally:
        qualified.close()


@pytest.mark.parametrize(
    ("case", "candidate_eid", "candidate_state", "candidate_vector", "expected"),
    (
        ("self", 10, _srg(R=0.1, band=1, L=9.0, heartbeat="A"), (1.0, 0.0, 0.0), None),
        ("no-srg", 1, None, (1.0, 0.0, 0.0), None),
        ("missing-embedding", 1, _srg(R=0.1, band=1, L=9.0, heartbeat="A"), None, None),
        ("zero", 1, _srg(R=0.1, band=1, L=9.0, heartbeat="A"), (0.0, 0.0, 0.0), None),
        ("near-zero", 1, _srg(R=0.1, band=1, L=9.0, heartbeat="A"), (1e-13, 0.0, 0.0), None),
        ("below-threshold", 1, _srg(R=0.1, band=1, L=9.0, heartbeat="A"), (0.7, 0.71414284, 0.0), None),
        ("band-refusal", 1, _srg(R=0.1, band=3, L=9.0, heartbeat="A"), (1.0, 0.0, 0.0), None),
        ("success", 1, _srg(R=0.1, band=1, L=9.0, heartbeat="A"), (1.0, 0.0, 0.0), 1),
    ),
)
def test_srg_consumer_preserves_qualified_filters_and_collision_gate(
    case, candidate_eid, candidate_state, candidate_vector, expected,
):
    incoming_state = _srg(R=0.3, band=1, L=6.0, heartbeat="B")
    incoming = _view(10)
    candidate = _view(candidate_eid)
    port = _Port({10: incoming, candidate_eid: candidate}, {candidate_eid: candidate_vector})
    runtime = _RecordingRuntime({10: incoming_state, candidate_eid: candidate_state})
    _adapter(port, port, runtime)._run_srg_collision(_context(10, incoming_state))
    assert runtime.applied == ([] if expected is None else [expected]), case


def _view(eid: int) -> RuntimeMemoryView:
    return RuntimeMemoryView(
        eid=eid, summary=f"memory {eid}", memory_type="episodic", memory_class="core",
        strength=0.8, confidence=0.9, payload=MappingProxyType({}),
        governance=RuntimeMemoryGovernanceView(False, False, False, False, False, True),
        provenance=RuntimeMemoryProvenanceView("user_input", "user_input", "direct", False, True),
    )


class _Port:
    def __init__(self, views, vectors):
        self._views = views
        self._vectors = vectors

    def get_current(self, eid):
        return self._views.get(eid)

    def list_current(self):
        return tuple(self._views.values())

    def read_current_embedding(self, eid, *, expected_dimension):
        vector = self._vectors.get(eid)
        return None if vector is None else RuntimeMemoryEmbedding.from_float32_vector(vector, expected_dimension=expected_dimension)

    def search_by_embedding(self, *_args, **_kwargs):
        raise AssertionError("SRG collision does not search")


class _RecordingRuntime:
    def __init__(self, states):
        self.states = states
        self.applied = []

    def effective_srg_state(self, memory):
        return self.states.get(memory.eid)

    def effective_collision_report(self, _memory):
        return None

    def apply_collision(self, *, existing, incoming, existing_state, incoming_state, incoming_report):
        self.applied.append(existing.eid)
        self.states[existing.eid] = dict(existing_state)
        self.states[incoming.eid] = dict(incoming_state)
