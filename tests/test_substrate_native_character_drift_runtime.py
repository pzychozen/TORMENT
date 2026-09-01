"""C1A native Character drift measurement qualification."""
from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from torment_service.character import (
    CharacterDriftMemoryObservation,
    CharacterSeed,
    CharacterState,
    measure_drift_from_observations,
)
from torment_service.character_drift_runtime import (
    CharacterDriftMeasurementStatus,
    CharacterDriftPostWriteRequest,
    LegacyCharacterDriftRuntime,
)
from torment_service.motifs import Motif
from torment_service.substrate.compat import NativeMemoryCompatibilityFacade
from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.errors import SubstrateConfigurationError
from torment_service.substrate.ids import generate_native_id, native_id_to_bytes
from torment_service.substrate.motif_runtime_reader import NativeMotifRuntimeReader
from torment_service.substrate.motifs import MotifState, NativeMotifService
from torment_service.substrate.native_character_drift_runtime import (
    NativeCharacterDriftRuntime,
    NativeCharacterDriftRuntimeConfiguration,
    _legacy_cache_normalize,
)
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


def _id():
    return generate_native_id()


def _database(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "c1a.db")
    create_schema(qualified.connection)
    connection = qualified.connection
    values = {name: _id() for name in (
        "memory_identity", "motif_identity", "membership_identity", "memory_scope",
        "motif_scope", "idempotency", "memory_alias", "other_memory_alias", "motif_alias",
    )}
    for name in ("memory_identity", "motif_identity", "membership_identity"):
        connection.execute(
            "INSERT INTO identity_namespaces VALUES (?,?,0)",
            (native_id_to_bytes(values[name]), f"c1a-{name}"),
        )
    for name in ("memory_scope", "motif_scope"):
        connection.execute(
            "INSERT INTO semantic_scopes VALUES (?,?,0)",
            (native_id_to_bytes(values[name]), f"c1a-{name}"),
        )
    connection.execute(
        "INSERT INTO idempotency_namespaces VALUES (?,?)",
        (native_id_to_bytes(values["idempotency"]), "c1a-idempotency"),
    )
    for name in ("memory_alias", "other_memory_alias", "motif_alias"):
        connection.execute(
            "INSERT INTO legacy_source_namespaces VALUES (?,?,0)",
            (native_id_to_bytes(values[name]), f"c1a-{name}"),
        )
    values.update(qualified=qualified, connection=connection)
    return values


def _provenance(values, key: str):
    value = _id()
    values["connection"].execute(
        "INSERT INTO provenance_records VALUES (?,?,?,?,?,?,?,?,?,?)",
        (native_id_to_bytes(value), "RUNTIME_PROVENANCE_V1", "user_input", "user", key,
         "KNOWN", None, None, None, None),
    )
    return value


def _memory(
    values, key: str, *, user_id: str = "aria", half_life: float = 30.0,
    born_step: int | None = None, memory_type: str = "reflection", source_namespace=None,
):
    extra = {} if born_step is None else {"born_step": born_step}
    return NativeMemoryCompatibilityFacade(values["connection"]).create_memory_state(
        legacy_source_namespace_id=source_namespace or values["memory_alias"],
        idempotency_namespace_id=values["idempotency"], idempotency_key=f"memory:{key}",
        identity_namespace_id=values["memory_identity"], semantic_scope_id=values["memory_scope"],
        summary=f"memory {key}", memory_type=memory_type, memory_class="core",
        strength=0.7, confidence=0.8, half_life_days=half_life, user_id=user_id,
        logical_step=1, extra_payload=extra, governance_state="DERIVED",
        provenance_id=_provenance(values, key),
    )


def _ready(values, source, key: str, vector: tuple[float, float, float]):
    payload = np.asarray(vector, dtype=np.float32).tobytes(order="C")
    representations = NativeRepresentationService(values["connection"])
    pending = representations.create_representation_pending(
        idempotency_namespace_id=values["idempotency"], idempotency_key=f"pending:{key}",
        request=RepresentationRequest(
            "OBJECT_REVISION", source.object_id, source.revision_id, None, None,
            "COMPAT_EMBEDDING", 1, "compat-embedding-v1", "RAW_VECTOR", "float32", 3,
            (), None, len(payload),
        ),
    )
    representations.establish_representation_integrity_expectation(
        idempotency_namespace_id=values["idempotency"], idempotency_key=f"expect:{key}",
        request=RepresentationIntegrityExpectationRequest(
            pending.representation_id, INTEGRITY_ALGORITHM_SHA256,
            sha256(payload).digest(), INTEGRITY_VALUE_ENCODING_RAW,
        ),
    )
    representations.publish_representation_ready(
        idempotency_namespace_id=values["idempotency"], idempotency_key=f"ready:{key}",
        request=RepresentationReadyRequest(
            pending.representation_id, "COMPAT_EMBEDDING", 1,
            "compat-embedding-v1", "RAW_VECTOR", payload,
        ),
    )


def _seed_motif(values, source, *, runtime_id: str = "seed-motif", centroid=(1.0, 0.0, 0.0)):
    return NativeMotifService(values["connection"]).create_motif_with_member(
        idempotency_namespace_id=values["idempotency"], idempotency_key=f"motif:{runtime_id}",
        motif_identity_namespace_id=values["motif_identity"],
        membership_identity_namespace_id=values["membership_identity"],
        motif_alias_namespace_id=values["motif_alias"],
        state=MotifState(
            values["motif_scope"], runtime_id, "personal", runtime_id,
            centroid, 0.8, 0.9, ("aria",), 1, 1,
        ),
        member_object_id=source.object_id,
    )


class _Store:
    """In-memory CharacterStore shape with explicit persisted snapshots."""

    def __init__(self, seed: CharacterSeed, state: CharacterState | None = None):
        self.seed = seed
        self.state = state
        self.saved: list[CharacterState] = []

    def load_seed(self, _workspace_id: str, seed_id: str):
        return self.seed if seed_id == self.seed.seed_id else None

    def load_state(self, _workspace_id: str, _agent_id: str):
        return None if self.state is None else CharacterState.from_dict(self.state.to_dict())

    def save_state(self, _workspace_id: str, state: CharacterState):
        state.updated_ts = 700
        self.state = CharacterState.from_dict(state.to_dict())
        self.saved.append(self.state)


def _config(values, *, seed_id="seed", cache=True):
    return NativeCharacterDriftRuntimeConfiguration(
        workspace_id="ws", agent_id="aria", seed_id=seed_id, domain_id="personal",
        motif_alias_namespace_id=values["motif_alias"], semantic_scope_id=values["motif_scope"],
        expected_dimension=3, character_enabled=True, drift_every=5,
        embedding_cache_enabled=cache,
    )


def _native(values, store, *, config=None):
    access = NativePostWriteMemoryAccess(
        values["connection"], legacy_source_namespace_id=values["memory_alias"], expected_dimension=3,
    )
    return NativeCharacterDriftRuntime(
        configuration=config or _config(values), store=store, memory_read=access,
        memory_enumeration=access, motif_reader=NativeMotifRuntimeReader(values["connection"]),
    )


def _semantic_counts(connection):
    tables = (
        "objects", "object_revisions", "relationships", "relationship_revisions", "representations",
        "representation_payloads", "operations", "semantic_transitions", "object_revision_effects",
        "relationship_revision_effects", "memory_runtime_enumeration_orders",
    )
    return tuple(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in tables)


def _legacy_runtime(values, seed, state, sources_and_vectors, *, motif_present=True):
    facade = NativeMemoryCompatibilityFacade(values["connection"])
    entities, cache = {}, {}
    for source, vector in sources_and_vectors:
        payload = facade.get_memory_by_eid(
            legacy_source_namespace_id=values["memory_alias"], eid=source.eid,
        ).payload
        entities[source.eid] = SimpleNamespace(payload=payload)
        if vector is not None:
            cache[source.eid] = _legacy_cache_normalize(vector, expected_dimension=3)
    motifs = {}
    if motif_present:
        motifs[seed.seed_motif_id] = Motif(
            seed.seed_motif_id, "personal", "seed", [1.0, 0.0, 0.0], 0.8,
            list(seed.seed_eids), ["aria"], 0.9, 1, 1,
        )
    graph = SimpleNamespace(entities=entities, _emb_by_eid=cache)
    return LegacyCharacterDriftRuntime(
        character_enabled=True, drift_every=5, seed_id=seed.seed_id,
        store=_Store(seed, state), graph=graph, motif_registry=SimpleNamespace(motifs=motifs),
    )


def _request(step=10, outcome="CREATED_NEW"):
    return CharacterDriftPostWriteRequest("ws", "aria", step, True, outcome, "private")


def _state_without_timestamp(state: CharacterState):
    value = asdict(state)
    value.pop("updated_ts")
    return value


def test_native_character_measurement_matches_legacy_order_filter_cache_and_external_state(tmp_path: Path):
    values = _database(tmp_path)
    try:
        seed_source = _memory(values, "seed", half_life=3650, born_step=1, memory_type="seed_canon")
        recent = _memory(values, "recent", born_step=9)
        old_core = _memory(values, "old", half_life=3650, born_step=1)
        default_born = _memory(values, "default-born")
        other_agent = _memory(values, "other", user_id="other", born_step=9)
        missing = _memory(values, "missing", born_step=9)
        # Deliberately unlike the native motif centroid: parity proves the
        # motif branch wins before either seed-EID fallback is considered.
        _ready(values, seed_source, "seed", (0.0, 4.0, 0.0))
        _ready(values, recent, "recent", (4.0, 3.0, 0.0))
        _ready(values, old_core, "old", (0.0, 1.0, 0.0))
        _ready(values, default_born, "default-born", (0.0, 0.0, 2.0))
        _ready(values, other_agent, "other", (0.0, 1.0, 0.0))
        _seed_motif(values, seed_source)
        seed = CharacterSeed(
            "seed", "Character", "Stable Character seed.", seed_motif_id="seed-motif",
            seed_eids=[seed_source.eid], drift_window_steps=5,
        )
        prior = CharacterState("ws", "aria", "seed", distance_to_seed=0.6)
        native_store, legacy_store = _Store(seed, prior), _Store(seed, prior)
        before = _semantic_counts(values["connection"])
        native = _native(values, native_store)
        access = NativePostWriteMemoryAccess(
            values["connection"], legacy_source_namespace_id=values["memory_alias"], expected_dimension=3,
        )
        assert [item.eid for item in access.list_current()] == [
            seed_source.eid, recent.eid, old_core.eid, default_born.eid, other_agent.eid, missing.eid,
        ]
        native_result = native.measure_for_post_write(_request())
        legacy = _legacy_runtime(
            values, seed, prior,
            ((seed_source, (0.0, 4.0, 0.0)), (recent, (4.0, 3.0, 0.0)),
             (old_core, (0.0, 1.0, 0.0)), (default_born, (0.0, 0.0, 2.0)),
             (other_agent, (0.0, 1.0, 0.0)), (missing, None)),
        )
        legacy._store = legacy_store
        legacy_result = legacy.measure_for_post_write(_request())

        assert native_result.status is legacy_result.status is CharacterDriftMeasurementStatus.MEASURED
        assert native_result.drift is not None and legacy_result.drift is not None
        assert dict(native_result.drift) == pytest.approx(dict(legacy_result.drift))
        assert native_result.drift["core_count"] == 1  # old tier count happens before recency exclusion
        assert native_result.drift["relational_count"] == 3  # recent/default/missing; exact-agent only
        assert native_result.drift["total_recent"] == 1  # missing representation and default born_step=0 are excluded
        assert native_result.drift["drift_direction"] == "toward_seed"
        assert _state_without_timestamp(native_store.state) == _state_without_timestamp(legacy_store.state)
        assert native_store.state is not None and native_store.state.drift_history == [(10, native_result.drift["drift_score"])]
        assert _semantic_counts(values["connection"]) == before
    finally:
        values["qualified"].close()


def test_seed_eid_and_recent_average_fallbacks_are_namespaced_and_parity_preserved(tmp_path: Path):
    values = _database(tmp_path)
    try:
        seed_source = _memory(values, "seed", memory_type="seed_canon", born_step=1)
        recent = _memory(values, "recent", born_step=9)
        _ready(values, seed_source, "seed", (3.0, 0.0, 0.0))
        _ready(values, recent, "recent", (0.0, 2.0, 0.0))
        seed = CharacterSeed("seed", "Character", "Seed text.", seed_motif_id="lost-motif", seed_eids=[seed_source.eid], drift_window_steps=5)
        native_store, legacy_store = _Store(seed), _Store(seed)
        native_result = _native(values, native_store).measure_for_post_write(_request())
        legacy = _legacy_runtime(values, seed, None, ((seed_source, (3.0, 0.0, 0.0)), (recent, (0.0, 2.0, 0.0))), motif_present=False)
        legacy._store = legacy_store
        legacy_result = legacy.measure_for_post_write(_request())
        assert native_result.drift is not None and legacy_result.drift is not None
        assert dict(native_result.drift) == pytest.approx(dict(legacy_result.drift))
        assert native_result.drift["distance_to_seed"] == pytest.approx(1.0)
        assert native_store.state is not None and native_store.state.seed_id == "seed"

        # A seed EID is never global: another namespace's EID 0 cannot supply it.
        _memory(values, "other-seed", source_namespace=values["other_memory_alias"])
        other_seed = NativeMemoryCompatibilityFacade(values["connection"]).get_memory_by_eid(
            legacy_source_namespace_id=values["other_memory_alias"], eid=0,
        )
        _ready(values, other_seed, "other-seed", (3.0, 0.0, 0.0))
        missing_seed = CharacterSeed("seed", "Character", "Seed text.", seed_motif_id="lost-motif", seed_eids=[999], drift_window_steps=5)
        average_result = _native(values, _Store(missing_seed), config=_config(values)).measure_for_post_write(_request())
        assert average_result.drift is not None
        assert average_result.drift["distance_to_seed"] == pytest.approx(0.0)
    finally:
        values["qualified"].close()


def test_no_recent_state_cap_gates_and_reinforcement_oddity(tmp_path: Path):
    values = _database(tmp_path)
    try:
        seed_source = _memory(values, "seed", memory_type="seed_canon", born_step=1)
        old = _memory(values, "old", born_step=1)
        _ready(values, seed_source, "seed", (1.0, 0.0, 0.0))
        _ready(values, old, "old", (0.0, 1.0, 0.0))
        _seed_motif(values, seed_source)
        seed = CharacterSeed("seed", "Character", "Seed text.", seed_motif_id="seed-motif", seed_eids=[seed_source.eid], drift_window_steps=5)
        store = _Store(seed, CharacterState("ws", "aria", "seed", drift_history=[(n, 0.0) for n in range(50)]))
        runtime = _native(values, store)
        no_recent = runtime.measure_for_post_write(_request())
        assert no_recent.status is CharacterDriftMeasurementStatus.MEASURED
        assert no_recent.drift is not None and no_recent.drift["total_recent"] == 0
        assert no_recent.drift["core_count"] == 0 and no_recent.drift["relational_count"] == 1
        assert store.state is not None and len(store.state.drift_history) == 50
        assert store.state.drift_history[0][0] == 1 and store.state.drift_history[-1][0] == 10
        before_state = _state_without_timestamp(store.state)
        reinforcement = runtime.measure_for_post_write(_request(outcome="REINFORCED_EXISTING"))
        assert reinforcement.status is CharacterDriftMeasurementStatus.REINFORCED_EFFECTIVE_NOOP
        assert _state_without_timestamp(store.state) == before_state
        assert runtime.measure_for_post_write(CharacterDriftPostWriteRequest("ws", "aria", 0, True, "CREATED_NEW", "private")).status is CharacterDriftMeasurementStatus.NOT_DUE
        assert runtime.measure_for_post_write(CharacterDriftPostWriteRequest("ws", "aria", 9, True, "CREATED_NEW", "private")).status is CharacterDriftMeasurementStatus.NOT_DUE
        assert runtime.measure_for_post_write(CharacterDriftPostWriteRequest("ws", "aria", 10, False, "CREATED_NEW", "private")).status is CharacterDriftMeasurementStatus.NOT_DUE
    finally:
        values["qualified"].close()


def test_shared_trigger_stops_before_native_seed_or_scope_reads(tmp_path: Path):
    values = _database(tmp_path)
    try:
        seed = CharacterSeed(
            "seed", "Aria", "Private seed text.",
            seed_motif_id="motif_x", seed_eids=[1, 2],
        )
        runtime = _native(values, _Store(seed))
        runtime._store = SimpleNamespace(
            load_seed=lambda *_args: pytest.fail("shared trigger must not load a private seed"),
        )
        runtime._memory_enumeration = SimpleNamespace(
            list_current=lambda: pytest.fail("shared trigger must not enumerate shared memories"),
        )
        runtime._memory_read = SimpleNamespace(
            read_current_embedding=lambda *_args, **_kwargs: pytest.fail("shared trigger must not read seed EIDs"),
        )
        runtime._motif_reader = SimpleNamespace(
            list_runtime_motifs=lambda **_kwargs: pytest.fail("shared trigger must not read private motif IDs"),
        )

        result = runtime.measure_for_post_write(
            CharacterDriftPostWriteRequest("ws", "aria", 10, True, "CREATED_NEW", "shared")
        )

        assert result.status is CharacterDriftMeasurementStatus.NOT_APPLICABLE_SCOPE
        assert not result.measured and result.seed is None and result.drift is None
    finally:
        values["qualified"].close()


def test_prior_direction_threshold_high_drift_refusal_and_no_native_mutation(tmp_path: Path):
    values = _database(tmp_path)
    try:
        seed_source = _memory(values, "seed", memory_type="seed_canon", born_step=1)
        away = _memory(values, "away", born_step=9)
        _ready(values, seed_source, "seed", (1.0, 0.0, 0.0))
        _ready(values, away, "away", (0.0, 1.0, 0.0))
        _seed_motif(values, seed_source)
        seed = CharacterSeed("seed", "Character", "Seed text.", seed_motif_id="seed-motif", seed_eids=[seed_source.eid], drift_window_steps=5)
        store = _Store(seed, CharacterState("ws", "aria", "seed", distance_to_seed=0.0))
        before = _semantic_counts(values["connection"])
        result = _native(values, store).measure_for_post_write(_request())
        assert result.status is CharacterDriftMeasurementStatus.CHARACTER_GRAVITY_CORRECTION_REQUIRED
        assert result.high_drift and result.drift is not None
        assert result.drift["drift_direction"] == "away_seed" and result.drift["drift_score"] < -seed.drift_correction_threshold
        assert _semantic_counts(values["connection"]) == before
        assert store.state is not None and store.state.drift_history == [(10, result.drift["drift_score"])]
    finally:
        values["qualified"].close()


def test_cache_disabled_is_refused_and_cache_normalization_is_legacy_exact(tmp_path: Path):
    values = _database(tmp_path)
    try:
        raw = np.asarray((2.0, 0.6, 0.0), dtype=np.float32)
        expected = raw / (np.linalg.norm(raw) + 1e-12)
        assert np.array_equal(_legacy_cache_normalize(raw, expected_dimension=3), expected.astype(np.float32))
        seed = CharacterSeed("seed", "Character", "Seed text.", seed_motif_id="seed-motif")
        access = NativePostWriteMemoryAccess(values["connection"], legacy_source_namespace_id=values["memory_alias"], expected_dimension=3)
        with pytest.raises(SubstrateConfigurationError, match="TORMENT_GRAPH_EMB_CACHE"):
            NativeCharacterDriftRuntime(
                configuration=_config(values, cache=False), store=_Store(seed), memory_read=access,
                memory_enumeration=access, motif_reader=NativeMotifRuntimeReader(values["connection"]),
            )
    finally:
        values["qualified"].close()


def test_direction_threshold_is_strict_and_preserves_all_three_legacy_labels():
    seed = CharacterSeed("seed", "Character", "Seed text.", drift_window_steps=5)
    observations = [CharacterDriftMemoryObservation(7, {"user_id": "aria", "born_step": 9})]

    def measure(previous_distance: float):
        return measure_drift_from_observations(
            observations=observations,
            cached_embedding=lambda _eid: np.asarray((1.0, 0.0, 0.0), dtype=np.float32),
            seed_centroid=lambda _average: np.asarray((1.0, 0.0, 0.0), dtype=np.float32),
            coherence_field=None, seed=seed, agent_id="aria", current_step=10,
            previous_state=CharacterState("ws", "aria", "seed", distance_to_seed=previous_distance),
        )

    assert measure(-0.03)["drift_direction"] == "stable"  # strictly greater, never >=
    assert measure(-0.031)["drift_direction"] == "away_seed"
    assert measure(0.031)["drift_direction"] == "toward_seed"
