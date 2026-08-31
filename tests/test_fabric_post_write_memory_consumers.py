"""A3D3 qualification for conflict and Hivemind neutral memory reads."""
from __future__ import annotations

from hashlib import sha256
import logging
from types import MappingProxyType, SimpleNamespace
from pathlib import Path

import numpy as np
import pytest

from torment_service.character import CharacterSeed
from torment_service.character_drift_runtime import (
    CharacterDriftMeasurementResult,
    CharacterDriftMeasurementStatus,
)
from torment_service.character_gravity_runtime import (
    CharacterGravityCorrectionResult,
    CharacterGravityCorrectionStatus,
)
from torment_service.fabric import _detect_canon_conflict
from torment_service.kernel.seed_entities import SeedEntity
from torment_service.memory_graph import MemoryGraph
from torment_service.memory_runtime_access import (
    LegacyPostWriteMemoryAccess,
    RuntimeMemoryGovernanceView,
    RuntimeMemoryProvenanceView,
    RuntimeMemorySearchHit,
    RuntimeMemorySearchOutcome,
    RuntimeMemoryView,
)
from torment_service.post_write_runtime import (
    FabricPostWriteContext,
    LegacyFabricPostWriteAdapter,
    LegacyFabricPostWriteDependencies,
    PostWriteStorageOutcome,
)
from torment_service.substrate.compat import NativeMemoryCompatibilityFacade
from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.ids import generate_native_id, native_id_to_bytes
from torment_service.substrate.native_memory_runtime_access import NativePostWriteMemoryAccess
from torment_service.substrate.representations import (
    INTEGRITY_ALGORITHM_SHA256,
    INTEGRITY_VALUE_ENCODING_RAW,
    NativeRepresentationService,
    RepresentationIntegrityExpectationRequest,
    RepresentationReadyRequest,
    RepresentationRequest,
)
from torment_service.substrate.schema import create_schema


def _view(
    eid: int,
    *,
    summary: str = "The auth refactor is merged and deployed to prod yesterday.",
    memory_class: str = "core",
    non_shareable: bool = False,
    export_blocked: bool = False,
    collective_echo: bool = False,
    structurally_explicit: bool = True,
) -> RuntimeMemoryView:
    return RuntimeMemoryView(
        eid=eid,
        summary=summary,
        memory_type="episodic",
        memory_class=memory_class,
        strength=0.8,
        confidence=0.9,
        payload=MappingProxyType({"resonance_score": 0.61, "loop_type": "spiral"}),
        governance=RuntimeMemoryGovernanceView(
            False, non_shareable, export_blocked, False, False, structurally_explicit,
        ),
        provenance=RuntimeMemoryProvenanceView(
            "collective_echo" if collective_echo else "user_input",
            "collective_echo" if collective_echo else "user_input",
            "direct_ingest",
            collective_echo,
            True,
        ),
    )


class _Port:
    def __init__(self, *, outcome: RuntimeMemorySearchOutcome | None = None, views: dict[int, RuntimeMemoryView] | None = None):
        self.outcome = outcome or RuntimeMemorySearchOutcome("SEARCHABLE", ())
        self.views = views or {}
        self.search_calls: list[tuple[object, int, str | None]] = []
        self.current_calls: list[int] = []

    def search_by_embedding(self, embedding, *, top_k: int, user_id: str | None = None):
        self.search_calls.append((embedding, top_k, user_id))
        return self.outcome

    def get_current(self, eid: int):
        self.current_calls.append(eid)
        return self.views.get(eid)

    def list_current(self):
        return tuple(self.views.values())


class _NoGraph:
    @property
    def entities(self):
        raise AssertionError("adapted consumer read graph.entities")

    def search_by_embedding(self, *_args, **_kwargs):
        raise AssertionError("adapted consumer called graph.search_by_embedding")


class _NoSRGRuntime:
    def effective_srg_state(self, _memory):
        raise AssertionError("unexpected SRG state read")

    def effective_collision_report(self, _memory):
        raise AssertionError("unexpected SRG collision report read")

    def apply_collision(self, **_kwargs):
        raise AssertionError("unexpected SRG collision mutation")


class _NoWorldRuntime:
    def advance_for_post_write(self, *, step: int) -> None:
        raise AssertionError(f"unexpected world step {step}")


class _Conflicts:
    def __init__(self) -> None:
        self.rows: list[dict] = []

    def add(self, **values):
        self.rows.append(values)


class _Field:
    def __init__(self) -> None:
        self.packets = []

    def append_packet(self, packet, *, embedding):
        self.packets.append((packet, embedding.copy()))
        return None


def _context(
    *,
    eid: int = 2,
    summary: str = "The auth refactor is not merged and deployed to prod yesterday.",
    embedding=(1.0, 0.0, 0.0),
):
    return FabricPostWriteContext.make(
        workspace_id="ws", agent_id="aria", scope="private", chosen_domain="personal", step=4,
        storage_outcome=PostWriteStorageOutcome.CREATED_NEW, stored=True, eid=eid,
        created_motif=None, motif_ids=(), half_life_days=20.0, summary=summary,
        embedding=np.asarray(embedding, dtype=np.float32), memory_class="core",
        memory_type="episodic", strength=0.8, confidence=0.9, promotion_score=0.9,
        stability_delta=0.1, tri_mod={}, debug={"coherence": 0.5}, srg_state=None,
        phase_durations={}, state_symbol=None, affect_tag=None, affect_conf=None,
        skip_packet_emission=False,
    )


def _adapter(
    port,
    *,
    field: _Field | None = None,
    character_drift_runtime=None,
    character_gravity_runtime=None,
):
    conflicts = _Conflicts()
    field = field or _Field()
    owner = SimpleNamespace(
        _log=logging.getLogger("a3d3-owner"), _hivemind_enable=True,
        _hivemind_telemetry_enable=True, hivemind_events=[],
        character_store=SimpleNamespace(load_state=lambda *_args: None),
        _character_enable=False, _character_drift_every=1,
        _last_drift_was_high={}, drift_reflex_callback=None,
        _get_collective_field=lambda _workspace_id: field,
        _get_proposal_bridge=lambda _workspace_id: SimpleNamespace(maybe_draft_proposal=lambda **_kwargs: None),
    )
    owner._emit_hivemind_packet_telemetry = lambda **values: owner.hivemind_events.append(values)
    derived_runtime = SimpleNamespace(
        maybe_emit_identity_anchor=lambda _context: None,
        refine_identity_anchors=lambda _context: None,
        maybe_emit_mood_drift=lambda _context: None,
    )
    dependencies = LegacyFabricPostWriteDependencies(
        owner=owner,
        workspace=SimpleNamespace(conflicts={"personal": conflicts}, proposals={}),
        graph=_NoGraph(), world_runtime=_NoWorldRuntime(), derived_memory_runtime=derived_runtime,
        memory_access=port, memory_enumeration=port,
        srg_runtime=_NoSRGRuntime(), embedding_dimension=3,
        identity=SimpleNamespace(seed={}), motif_registry=None, motif_runtime=None,
        model_state=None, kernel_context=None, agent_key="ws::aria",
        detect_canon_conflict=_detect_canon_conflict, proposal_allowed=lambda **_kwargs: False,
        random_chance=lambda _probability: False, save_checkpoint=lambda **_kwargs: None,
        build_motif_summary=lambda *_args, **_kwargs: None,
        build_shard_snapshot=lambda *_args, **_kwargs: None,
        hivemind_log=logging.getLogger("torment.hivemind"),
        character_drift_runtime=character_drift_runtime,
        character_gravity_runtime=character_gravity_runtime,
    )
    return LegacyFabricPostWriteAdapter(dependencies), conflicts, field


def test_conflict_consumer_reads_only_the_neutral_port_and_preserves_first_match():
    candidate = _view(1)
    port = _Port(outcome=RuntimeMemorySearchOutcome(
        "SEARCHABLE", (
            RuntimeMemorySearchHit(_view(2), 1.0, 1.0, 1.0),
            RuntimeMemorySearchHit(candidate, 0.95, 0.95, 1.0),
        ),
    ))
    adapter, conflicts, _field = _adapter(port)

    adapter._run_contradiction_surface(_context())

    assert len(port.search_calls) == 1
    assert port.search_calls[0][1:] == (3, "aria")
    assert conflicts.rows == [{
        "eid_a": 1, "eid_b": 2, "sim": 0.95,
        "conflict_score": pytest.approx(8 / 9), "reason": "negation_mismatch",
        "origin_scope": "private", "origin_agent_id": "aria", "origin_domain_id": None,
    }]


@pytest.mark.parametrize(
    ("case", "summary", "memory_class", "raw_score", "status", "include_hit", "expected_rows"),
    (
        ("ordinary non-conflicting memory", "a wholly unrelated observation", "core", 0.70, "SEARCHABLE", True, 0),
        ("similar non-contradictory memory", "The auth refactor is not merged and deployed to prod yesterday.", "core", 0.95, "SEARCHABLE", True, 0),
        ("similar contradictory memory", "The auth refactor is merged and deployed to prod yesterday.", "core", 0.95, "SEARCHABLE", True, 1),
        ("different memory class", "The auth refactor is merged and deployed to prod yesterday.", "archive", 0.95, "SEARCHABLE", True, 0),
        ("different agent filters candidate", "The auth refactor is merged and deployed to prod yesterday.", "core", 0.95, "SEARCHABLE", False, 0),
        ("zero query", "The auth refactor is merged and deployed to prod yesterday.", "core", 0.95, "ZERO_NORM", False, 0),
        ("missing candidate", "The auth refactor is merged and deployed to prod yesterday.", "core", 0.95, "SEARCHABLE", False, 0),
    ),
)
def test_conflict_read_parity_cases(
    case: str,
    summary: str,
    memory_class: str,
    raw_score: float,
    status: str,
    include_hit: bool,
    expected_rows: int,
):
    candidate = _view(1, summary=summary, memory_class=memory_class)
    hits = (RuntimeMemorySearchHit(candidate, raw_score, raw_score, 1.0),) if include_hit else ()
    port = _Port(outcome=RuntimeMemorySearchOutcome(status, hits))
    adapter, conflicts, _field = _adapter(port)

    adapter._run_contradiction_surface(_context())

    assert len(conflicts.rows) == expected_rows, case
    if expected_rows:
        assert conflicts.rows[0] == {
            "eid_a": 1, "eid_b": 2, "sim": raw_score,
            "conflict_score": pytest.approx(8 / 9), "reason": "negation_mismatch",
            "origin_scope": "private", "origin_agent_id": "aria", "origin_domain_id": None,
        }


@pytest.mark.parametrize(
    ("view", "emitted", "provenance_class"),
    (
        (_view(2), True, None),
        (_view(2, non_shareable=True), False, None),
        (_view(2, export_blocked=True), False, None),
        (_view(2, collective_echo=True), False, "collective_echo"),
    ),
)
def test_hivemind_uses_structural_port_views_without_graph_reads(view, emitted: bool, provenance_class: str | None):
    port = _Port(views={2: view})
    adapter, _conflicts, field = _adapter(port)

    adapter._run_hivemind(_context())

    assert port.current_calls == [2, 2] if emitted else [2]
    assert bool(field.packets) is emitted
    if emitted:
        packet, embedding = field.packets[0]
        assert (packet.resonance_score, packet.loop_type) == (0.61, "spiral")
        assert embedding.tolist() == [1.0, 0.0, 0.0]
    telemetry = adapter._deps.owner.hivemind_events[-1]
    assert telemetry["provenance_class"] == provenance_class


def test_hivemind_preserves_missing_memory_and_separate_read_points():
    port = _Port(views={})
    adapter, _conflicts, field = _adapter(port)

    adapter._run_hivemind(_context())

    assert port.current_calls == [2, 2]
    assert len(field.packets) == 1
    packet, _embedding = field.packets[0]
    assert (packet.resonance_score, packet.loop_type) == (None, None)


class _FailingHivemindPort(_Port):
    def get_current(self, eid: int):
        self.current_calls.append(eid)
        raise RuntimeError("controlled read failure")


def test_hivemind_governance_read_failure_remains_fail_soft(caplog):
    port = _FailingHivemindPort()
    adapter, _conflicts, field = _adapter(port)

    with caplog.at_level(logging.ERROR, logger="torment.hivemind"):
        adapter._run_hivemind(_context())

    assert port.current_calls == [2, 2]
    assert len(field.packets) == 1
    assert "Hivemind packet governance evaluation failed" in caplog.text


class _ThreeDimensionalEmbedder:
    dim = 3

    def embed(self, _text):
        return np.zeros(3, dtype=np.float32)


def test_legacy_zero_query_elides_raw_graph_search_before_conflict(tmp_path: Path, monkeypatch):
    graph = MemoryGraph(str(tmp_path), embedder=_ThreeDimensionalEmbedder())
    graph.entities[2] = SeedEntity(2, 0, 0, np.zeros(3), np.zeros(3), np.zeros(3), {
        "summary": "incoming", "type": "episodic", "memory_class": "core", "strength": 0.8, "confidence": 0.9,
    })
    port = LegacyPostWriteMemoryAccess(graph, expected_dimension=3)
    adapter, conflicts, _field = _adapter(port)
    zero_context = _context(eid=2, embedding=(0.0, 0.0, 0.0))
    monkeypatch.setattr(graph, "search_by_embedding", lambda *_args, **_kwargs: pytest.fail("raw legacy search must be elided"))

    adapter._run_contradiction_surface(zero_context)

    assert conflicts.rows == []


def _id():
    return generate_native_id()


def _native_database(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "a3d3-native.db")
    create_schema(qualified.connection)
    connection = qualified.connection
    identity, scope, idem, namespace = (_id() for _ in range(4))
    for table, identifier, label in (
        ("identity_namespaces", identity, "a3d3-identities"),
        ("semantic_scopes", scope, "a3d3-scope"),
        ("idempotency_namespaces", idem, "a3d3-idempotency"),
        ("legacy_source_namespaces", namespace, "a3d3-source"),
    ):
        connection.execute(
            f"INSERT INTO {table} VALUES ({'?,?,0' if table != 'idempotency_namespaces' else '?,?'})",
            (native_id_to_bytes(identifier), label),
        )
    return qualified, connection, identity, scope, idem, namespace


def _native_memory(connection, identity, scope, idem, namespace, key, *, governance, source_type="user_input"):
    provenance_id = _id()
    connection.execute(
        "INSERT INTO provenance_records VALUES (?,?,?,?,?,?,?,?,?,?)",
        (native_id_to_bytes(provenance_id), "RUNTIME_PROVENANCE_V1", source_type, "user", "direct_ingest",
         "KNOWN", None, None, None, None),
    )
    source = NativeMemoryCompatibilityFacade(connection).create_memory_state(
        legacy_source_namespace_id=namespace, idempotency_namespace_id=idem, idempotency_key=f"memory:{key}",
        identity_namespace_id=identity, semantic_scope_id=scope, summary=f"memory {key}",
        memory_type="episodic", memory_class="core", strength=0.8, confidence=0.9,
        half_life_days=0.0, user_id="aria", logical_step=2,
        extra_payload={"resonance_score": 0.61, "loop_type": "spiral"},
        governance_state="DERIVED", provenance_id=provenance_id,
    )
    connection.execute(
        """INSERT INTO object_revision_governance(
            object_id,object_revision_id,object_revision_ordinal,protected,non_shareable,
            collective_export_blocked,collective_reingest_blocked,decay_accelerated
        ) VALUES (?,?,?,?,?,?,?,?)""",
        (native_id_to_bytes(source.object_id), native_id_to_bytes(source.revision_id), 1,
         0, int(governance.get("non_shareable", False)), int(governance.get("collective_export_blocked", False)),
         0, 0),
    )
    return source


def _ready(connection, idem, source, key):
    payload = np.asarray((1.0, 0.0, 0.0), dtype=np.float32).tobytes()
    representations = NativeRepresentationService(connection)
    pending = representations.create_representation_pending(
        idempotency_namespace_id=idem, idempotency_key=f"pending:{key}",
        request=RepresentationRequest("OBJECT_REVISION", source.object_id, source.revision_id, None, None,
                                      "COMPAT_EMBEDDING", 1, "compat-embedding-v1", "RAW_VECTOR", "float32", 3, (), None, len(payload)),
    )
    representations.establish_representation_integrity_expectation(
        idempotency_namespace_id=idem, idempotency_key=f"expect:{key}",
        request=RepresentationIntegrityExpectationRequest(pending.representation_id, INTEGRITY_ALGORITHM_SHA256, sha256(payload).digest(), INTEGRITY_VALUE_ENCODING_RAW),
    )
    representations.publish_representation_ready(
        idempotency_namespace_id=idem, idempotency_key=f"ready:{key}",
        request=RepresentationReadyRequest(pending.representation_id, "COMPAT_EMBEDDING", 1, "compat-embedding-v1", "RAW_VECTOR", payload),
    )


def _native_counts(connection):
    return tuple(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in (
        "objects", "object_revisions", "representations", "operations", "semantic_transitions",
        "object_revision_governance", "provenance_records",
    ))


def test_native_port_qualifies_same_conflict_and_hivemind_consumer_facts_read_only(tmp_path: Path):
    qualified, connection, identity, scope, idem, namespace = _native_database(tmp_path)
    try:
        _native_memory(connection, identity, scope, idem, namespace, "ignored", governance={})
        candidate = _native_memory(connection, identity, scope, idem, namespace, "candidate", governance={})
        current = _native_memory(connection, identity, scope, idem, namespace, "current", governance={})
        _ready(connection, idem, candidate, "candidate")
        _ready(connection, idem, current, "current")
        port = NativePostWriteMemoryAccess(connection, legacy_source_namespace_id=namespace, expected_dimension=3)
        adapter, conflicts, field = _adapter(port)
        before = _native_counts(connection)

        outcome = port.search_by_embedding((1.0, 0.0, 0.0), top_k=3, user_id="aria")
        candidate_hit = next(hit for hit in outcome.hits if hit.eid == candidate.eid)
        assert (candidate_hit.view.summary, candidate_hit.view.memory_class, candidate_hit.raw_score) == (
            "memory candidate", "core", pytest.approx(1.0),
        )

        adapter._run_contradiction_surface(_context(eid=current.eid, summary="memory candidate not true"))
        adapter._run_hivemind(_context(eid=current.eid, summary="memory current"))

        assert len(conflicts.rows) == 1
        assert conflicts.rows[0]["eid_a"] == candidate.eid
        assert conflicts.rows[0]["eid_b"] == current.eid
        assert len(field.packets) == 1
        packet, _embedding = field.packets[0]
        assert (packet.source_eid, packet.resonance_score, packet.loop_type) == (current.eid, 0.61, "spiral")
        assert _native_counts(connection) == before
    finally:
        qualified.close()


@pytest.mark.parametrize(
    ("governance", "source_type", "emitted", "provenance_class"),
    (
        ({}, "user_input", True, None),
        ({"non_shareable": True}, "user_input", False, None),
        ({"collective_export_blocked": True}, "user_input", False, None),
        ({}, "collective_echo", False, "collective_echo"),
    ),
)
def test_native_port_qualifies_hivemind_structural_admission_read_only(
    tmp_path: Path,
    governance: dict[str, bool],
    source_type: str,
    emitted: bool,
    provenance_class: str | None,
):
    qualified, connection, identity, scope, idem, namespace = _native_database(tmp_path)
    try:
        source = _native_memory(
            connection, identity, scope, idem, namespace, "hivemind",
            governance=governance, source_type=source_type,
        )
        _ready(connection, idem, source, "hivemind")
        port = NativePostWriteMemoryAccess(connection, legacy_source_namespace_id=namespace, expected_dimension=3)
        adapter, _conflicts, field = _adapter(port)
        before = _native_counts(connection)

        view = port.get_current(source.eid)
        assert view is not None
        assert view.governance.structurally_explicit is True
        assert view.provenance.collective_echo is (source_type == "collective_echo")
        adapter._run_hivemind(_context(eid=source.eid, summary="memory hivemind"))

        assert bool(field.packets) is emitted
        if emitted:
            packet, _embedding = field.packets[0]
            assert (packet.resonance_score, packet.loop_type) == (0.61, "spiral")
        telemetry = adapter._deps.owner.hivemind_events[-1]
        assert telemetry["provenance_class"] == provenance_class
        assert _native_counts(connection) == before
    finally:
        qualified.close()


def _character_correction_seed() -> CharacterSeed:
    return CharacterSeed(
        "seed", "Aria", "A durable concept.", seed_motif_id="seed-motif",
        drift_correction_threshold=0.2, drift_gravity_strength=0.12, core_half_life=3650.0,
    )


class _HighCharacterMeasurement:
    def __init__(self, calls: list[str]) -> None:
        self._calls = calls
        self._seed = _character_correction_seed()
        self._drift = {"drift_score": -0.2, "drift_direction": "away_seed"}

    def measure_for_post_write(self, _request):
        self._calls.append("measurement")
        return CharacterDriftMeasurementResult(
            CharacterDriftMeasurementStatus.CHARACTER_GRAVITY_CORRECTION_REQUIRED,
            seed=self._seed, drift=self._drift, high_drift=True,
        )


class _RecordingCharacterCorrection:
    def __init__(self, calls: list[str], *, fail: bool = False) -> None:
        self._calls = calls
        self._fail = fail
        self.requests = []

    def correct_for_post_write(self, request):
        self._calls.append("correction")
        self.requests.append(request)
        if self._fail:
            raise RuntimeError("correction did not complete")
        return CharacterGravityCorrectionResult(CharacterGravityCorrectionStatus.APPLIED, True)


def test_neutral_character_ports_preserve_correction_then_rising_edge_reflex():
    calls: list[str] = []
    measurement = _HighCharacterMeasurement(calls)
    correction = _RecordingCharacterCorrection(calls)
    adapter, _conflicts, _field = _adapter(
        _Port(), character_drift_runtime=measurement, character_gravity_runtime=correction,
    )
    adapter._deps.owner.drift_reflex_callback = lambda workspace_id, agent_id, drift: calls.append(
        f"reflex:{workspace_id}:{agent_id}:{drift['drift_score']}"
    )

    adapter._run_character_drift(_context())
    adapter._run_character_drift(_context())

    assert calls == [
        "measurement", "correction", "reflex:ws:aria:-0.2",
        "measurement", "correction",
    ]
    assert [(request.workspace_id, request.agent_id, request.step) for request in correction.requests] == [
        ("ws", "aria", 4), ("ws", "aria", 4),
    ]
    assert adapter._deps.owner._last_drift_was_high == {("ws", "aria"): True}


def test_character_correction_failure_preserves_reflex_edge_and_callback_is_swallowed():
    failed_calls: list[str] = []
    failed = _RecordingCharacterCorrection(failed_calls, fail=True)
    failed_adapter, _conflicts, _field = _adapter(
        _Port(), character_drift_runtime=_HighCharacterMeasurement(failed_calls),
        character_gravity_runtime=failed,
    )
    failed_adapter._deps.owner.drift_reflex_callback = lambda *_args: failed_calls.append("reflex")

    failed_adapter._run_character_drift(_context())

    assert failed_calls == ["measurement", "correction"]
    assert failed_adapter._deps.owner._last_drift_was_high == {}

    callback_calls: list[str] = []
    callback_adapter, _conflicts, _field = _adapter(
        _Port(), character_drift_runtime=_HighCharacterMeasurement(callback_calls),
        character_gravity_runtime=_RecordingCharacterCorrection(callback_calls),
    )

    def failing_callback(*_args):
        callback_calls.append("reflex")
        raise RuntimeError("application callback failure")

    callback_adapter._deps.owner.drift_reflex_callback = failing_callback
    callback_adapter._run_character_drift(_context())

    assert callback_calls == ["measurement", "correction", "reflex"]
    assert callback_adapter._deps.owner._last_drift_was_high == {("ws", "aria"): True}
