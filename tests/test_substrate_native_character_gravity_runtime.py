"""C1B native Character gravity-correction qualification."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from torment_service.character import CharacterSeed
from torment_service.character_gravity_runtime import (
    CharacterGravityCorrectionRequest,
    CharacterGravityCorrectionStatus,
)
from torment_service.substrate.compat import NativeMemoryCompatibilityFacade
from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.fabric_native_routing import (
    NativeFabricRoutingScope,
    NativeMotifProcessOrder,
)
from torment_service.substrate.ids import generate_native_id, native_id_to_bytes
from torment_service.substrate.motif_runtime_reader import NativeMotifRuntimeReader, NativeRuntimeMotif
from torment_service.substrate.motifs import MotifState, NativeMotifService
from torment_service.substrate.native_character_gravity_runtime import (
    CharacterCorrectionEmbeddingNotByteStable,
    NativeCharacterGravityCorrectionRuntime,
    NativeCharacterGravityCorrectionRuntimeConfiguration,
)
from torment_service.substrate.native_world_runtime import NativeWorldProcessState
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


def _database(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "c1b.db")
    create_schema(qualified.connection)
    connection = qualified.connection
    values = {name: _id() for name in (
        "memory_identity", "motif_identity", "membership_identity", "scope", "idempotency",
        "memory_alias", "motif_alias",
    )}
    for name in ("memory_identity", "motif_identity", "membership_identity"):
        connection.execute("INSERT INTO identity_namespaces VALUES (?,?,0)", (native_id_to_bytes(values[name]), name))
    connection.execute("INSERT INTO semantic_scopes VALUES (?,?,0)", (native_id_to_bytes(values["scope"]), "private"))
    connection.execute("INSERT INTO idempotency_namespaces VALUES (?,?)", (native_id_to_bytes(values["idempotency"]), "c1b"))
    for name in ("memory_alias", "motif_alias"):
        connection.execute("INSERT INTO legacy_source_namespaces VALUES (?,?,0)", (native_id_to_bytes(values[name]), name))
    scope = NativeMemoryRuntimeScope(
        workspace_id="ws", scope_kind="PRIVATE_AGENT", legacy_source_namespace_id=values["memory_alias"],
        identity_namespace_id=values["memory_identity"], semantic_scope_id=values["scope"], agent_id="aria",
    )
    values.update(
        qualified=qualified,
        connection=connection,
        routing_scope=NativeFabricRoutingScope(
            runtime_scope=scope, motif_alias_namespace_id=values["motif_alias"],
            motif_identity_namespace_id=values["motif_identity"],
            membership_identity_namespace_id=values["membership_identity"],
            idempotency_namespace_id=values["idempotency"],
        ),
    )
    return values


class _Embedder:
    provider = "synthetic"
    model = "synthetic-v1"
    dim = 3

    def __init__(self, vector=(1.0, 0.0, 0.0)):
        self.vector = vector
        self.calls: list[str] = []

    def embed(self, text: str):
        self.calls.append(text)
        return np.asarray(self.vector, dtype=np.float32)


def _lane():
    return NativeRepresentationLane(
        provider="synthetic", model="synthetic-v1", dimension=3,
        representation_class="COMPAT_EMBEDDING", generation=1,
        derivation_contract_version="compat-embedding-v1", encoding_id="RAW_VECTOR", dtype="float32",
    )


def _seed(*, motif_id="missing-seed", threshold=0.35):
    return CharacterSeed(
        "seed", "Aria", "A patient and enduring first concept. A second resilient concept.",
        seed_motif_id=motif_id, drift_correction_threshold=threshold,
        drift_gravity_strength=0.12, core_half_life=3650.0,
    )


def _request(seed, *, score=-0.35, direction="away_seed"):
    return CharacterGravityCorrectionRequest(
        "ws", "aria", 10, seed, {"drift_score": score, "drift_direction": direction},
    )


def _runtime(values, embedder, *, choose=None, worlds=None, order=None, parent="native-parent"):
    worlds = worlds or NativeWorldProcessState()
    order = order or NativeMotifProcessOrder()
    config = NativeCharacterGravityCorrectionRuntimeConfiguration(
        workspace_id="ws", agent_id="aria", domain_id="personal", parent_native_operation_key=parent,
        routing_scope=values["routing_scope"], representation_lane=_lane(), embedder=embedder,
        now_ts=lambda: 1000,
        choose_concept=choose or (lambda concepts: concepts[-1]),
    )
    return NativeCharacterGravityCorrectionRuntime(
        values["connection"], configuration=config, world_process_state=worlds, motif_process_order=order,
    ), worlds, order


def _counts(connection):
    return tuple(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in (
        "objects", "object_revisions", "relationships", "relationship_revisions", "representations",
        "representation_payloads", "operations", "semantic_transitions", "integrity_expectations",
        "integrity_measurements",
    ))


def _existing_memory(values, key="existing"):
    provenance = _id()
    values["connection"].execute(
        "INSERT INTO provenance_records VALUES (?,?,?,?,?,?,?,?,?,?)",
        (native_id_to_bytes(provenance), "FIXTURE", "test", "fixture", "known", "KNOWN", None, None, None, None),
    )
    return NativeMemoryCompatibilityFacade(values["connection"]).create_memory_state(
        legacy_source_namespace_id=values["memory_alias"], idempotency_namespace_id=values["idempotency"],
        idempotency_key=f"memory:{key}", identity_namespace_id=values["memory_identity"],
        semantic_scope_id=values["scope"], summary=key, memory_type="reflection", memory_class="core",
        strength=0.7, confidence=0.8, half_life_days=30.0, user_id="aria", logical_step=1,
        extra_payload={}, governance_state="DERIVED", provenance_id=provenance,
    )


def _ready(values, source, key, vector=(1.0, 0.0, 0.0)):
    payload = np.asarray(vector, dtype=np.float32).tobytes()
    service = NativeRepresentationService(values["connection"])
    pending = service.create_representation_pending(
        idempotency_namespace_id=values["idempotency"], idempotency_key=f"pending:{key}",
        request=RepresentationRequest("OBJECT_REVISION", source.object_id, source.revision_id, None, None,
            "COMPAT_EMBEDDING", 1, "compat-embedding-v1", "RAW_VECTOR", "float32", 3, (), None, len(payload)),
    )
    service.establish_representation_integrity_expectation(
        idempotency_namespace_id=values["idempotency"], idempotency_key=f"expect:{key}",
        request=RepresentationIntegrityExpectationRequest(pending.representation_id, INTEGRITY_ALGORITHM_SHA256,
            __import__("hashlib").sha256(payload).digest(), INTEGRITY_VALUE_ENCODING_RAW),
    )
    service.publish_representation_ready(
        idempotency_namespace_id=values["idempotency"], idempotency_key=f"ready:{key}",
        request=RepresentationReadyRequest(pending.representation_id, "COMPAT_EMBEDDING", 1,
            "compat-embedding-v1", "RAW_VECTOR", payload),
    )


def _existing_motif(values, source, runtime_id="existing"):
    return NativeMotifService(values["connection"]).create_motif_with_member(
        idempotency_namespace_id=values["idempotency"], idempotency_key=f"motif:{runtime_id}",
        motif_identity_namespace_id=values["motif_identity"], membership_identity_namespace_id=values["membership_identity"],
        motif_alias_namespace_id=values["motif_alias"],
        state=MotifState(values["scope"], runtime_id, "personal", runtime_id, (1.0, 0.0, 0.0), 0.8, 0.9, ("aria",), 1, 1),
        member_object_id=source.object_id,
    )


def test_threshold_gate_concept_memory_lifecycle_governance_and_representation(tmp_path: Path):
    values = _database(tmp_path)
    try:
        choices: list[tuple[str, ...]] = []
        embedder = _Embedder()
        runtime, _, _ = _runtime(values, embedder, choose=lambda concepts: choices.append(tuple(concepts)) or concepts[-1])
        result = runtime.correct_for_post_write(_request(_seed()))

        assert result.status is CharacterGravityCorrectionStatus.APPLIED
        assert result.correction_applied and result.selected_concept == "A second resilient concept."
        assert result.correction_text == "[identity reinforcement] A second resilient concept."
        assert choices == [("A patient and enduring first concept.", "A second resilient concept.")]
        assert embedder.calls == [result.correction_text]
        native = result.correction_identity
        source = NativeMemoryCompatibilityFacade(values["connection"]).get_memory_by_eid(
            legacy_source_namespace_id=values["memory_alias"], eid=native.source.eid,
        )
        payload = source.payload
        assert {key: payload[key] for key in (
            "summary", "type", "memory_class", "strength", "confidence", "canon", "created_at",
            "last_reinforced", "half_life", "user_id", "seed_id", "tier", "corrects_drift_score", "corrects_at_step",
        )} == {
            "summary": result.correction_text, "type": "drift_correction", "memory_class": "core",
            "strength": 0.12, "confidence": 0.85, "canon": True, "created_at": 10,
            "last_reinforced": 10, "half_life": 3650.0, "user_id": "aria", "seed_id": "seed",
            "tier": "core_identity", "corrects_drift_score": -0.35, "corrects_at_step": 10,
        }
        assert payload["lifecycle_status"]["state"] == "protected"
        assert payload["lifecycle_status"]["set_by"] == {
            "actor": "system", "via": "canon_set", "at": payload["lifecycle_status"]["set_by"]["at"],
        }
        governance = values["connection"].execute(
            "SELECT protected,non_shareable,collective_export_blocked,collective_reingest_blocked,decay_accelerated FROM object_revision_governance"
        ).fetchone()
        assert governance == (0, 0, 0, 0, 0)
        assert result.motif_status == "MOTIF_CREATED"
        world = runtime._world.snapshot_for_testing()
        assert world.eids == (native.source.eid,)
        # A3D8 fresh registration contributes its one legacy genesis sample;
        # no Character-specific world advance occurs.
        assert world.born_steps == (10,) and world.trail_lengths == (1,) and world.history_lengths == (1,)
        assert values["connection"].execute(
            "SELECT readiness,operational_disposition FROM representation_current_state WHERE representation_id=?",
            (native_id_to_bytes(native.representation_id),),
        ).fetchone() == ("READY", "USABLE")
        assert values["connection"].execute("SELECT count(*) FROM integrity_measurements").fetchone()[0] == 1
    finally:
        values["qualified"].close()


@pytest.mark.parametrize("score,direction", [(-0.349, "away_seed"), (-0.35, "stable")])
def test_gate_refusals_do_no_choice_embedding_or_native_write(tmp_path: Path, score, direction):
    values = _database(tmp_path)
    try:
        embedder = _Embedder()
        choices = []
        runtime, _, _ = _runtime(values, embedder, choose=lambda concepts: choices.append(concepts) or concepts[0])
        before = _counts(values["connection"])
        result = runtime.correct_for_post_write(_request(_seed(), score=score, direction=direction))
        assert result.status is CharacterGravityCorrectionStatus.NOT_REQUIRED
        assert not result.correction_applied and not choices and not embedder.calls
        assert _counts(values["connection"]) == before
    finally:
        values["qualified"].close()


def test_empty_seed_motif_skips_motif_and_ready_retry_reuses_everything(tmp_path: Path):
    values = _database(tmp_path)
    try:
        embedder = _Embedder()
        choices = []
        runtime, _, _ = _runtime(values, embedder, choose=lambda concepts: choices.append(tuple(concepts)) or concepts[0])
        request = _request(_seed(motif_id=""))
        first = runtime.correct_for_post_write(request)
        before = _counts(values["connection"])
        retry = runtime.correct_for_post_write(request)
        assert first.correction_identity.source.eid == retry.correction_identity.source.eid
        assert first.motif_status == "MOTIF_SKIPPED"
        assert choices == [("A patient and enduring first concept.", "A second resilient concept.")]
        assert len(embedder.calls) == 1
        assert _counts(values["connection"]) == before
    finally:
        values["qualified"].close()


def test_truthy_missing_seed_motif_uses_catalog_and_attach_keeps_correction_r1(tmp_path: Path):
    values = _database(tmp_path)
    try:
        existing = _existing_memory(values)
        _ready(values, existing, "existing")
        motif = _existing_motif(values, existing)
        runtime, _, _ = _runtime(values, _Embedder())
        result = runtime.correct_for_post_write(_request(_seed(motif_id="stale-seed-motif")))
        native = result.correction_identity
        assert result.motif_status == "MOTIF_ATTACHED"
        assert native.source.memory_revision_ordinal == 1
        current = NativeMotifService(values["connection"]).get_current_motif(motif.motif_object_id)
        assert current.revision_ordinal == 2
        members = NativeMotifRuntimeReader(values["connection"]).list_ordered_current_motif_members(motif.motif_object_id)
        assert [member.member_object_id for member in members][-1] == native.source.memory_object_id
    finally:
        values["qualified"].close()


def test_motif_failure_is_best_effort_but_representation_still_completes(tmp_path: Path, monkeypatch):
    values = _database(tmp_path)
    try:
        existing = _existing_memory(values)
        _existing_motif(values, existing)
        runtime, _, _ = _runtime(values, _Embedder())
        monkeypatch.setattr(runtime._motifs, "add_motif_member", lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("motif boom")))
        result = runtime.correct_for_post_write(_request(_seed(motif_id="truthy")))
        native = result.correction_identity
        assert result.correction_applied and result.motif_status == "MOTIF_FAILED_BEST_EFFORT"
        assert values["connection"].execute(
            "SELECT readiness FROM representation_current_state WHERE representation_id=?", (native_id_to_bytes(native.representation_id),)
        ).fetchone() == ("READY",)
    finally:
        values["qualified"].close()


def test_motif_create_failure_is_best_effort_but_representation_still_completes(tmp_path: Path, monkeypatch):
    values = _database(tmp_path)
    try:
        runtime, _, _ = _runtime(values, _Embedder())
        monkeypatch.setattr(
            runtime._motifs,
            "create_motif_with_member",
            lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("motif create boom")),
        )
        result = runtime.correct_for_post_write(_request(_seed(motif_id="truthy")))
        native = result.correction_identity
        assert result.correction_applied and result.motif_status == "MOTIF_FAILED_BEST_EFFORT"
        assert values["connection"].execute(
            "SELECT readiness FROM representation_current_state WHERE representation_id=?",
            (native_id_to_bytes(native.representation_id),),
        ).fetchone() == ("READY",)
    finally:
        values["qualified"].close()


def test_motif_response_loss_recovers_the_published_result_without_a_duplicate(tmp_path: Path, monkeypatch):
    values = _database(tmp_path)
    try:
        existing = _existing_memory(values)
        _existing_motif(values, existing)
        embedder = _Embedder()
        runtime, _, _ = _runtime(values, embedder)
        original = runtime._motifs.add_motif_member
        invoked = False

        def lose_response(**kwargs):
            nonlocal invoked
            result = original(**kwargs)
            if not invoked:
                invoked = True
                raise RuntimeError("forced motif response loss")
            return result

        monkeypatch.setattr(runtime._motifs, "add_motif_member", lose_response)
        request = _request(_seed(motif_id="truthy"))
        first = runtime.correct_for_post_write(request)
        before = _counts(values["connection"])
        retry = runtime.correct_for_post_write(request)
        assert first.motif_status == retry.motif_status == "MOTIF_ATTACHED"
        assert len(embedder.calls) == 1
        assert _counts(values["connection"]) == before
    finally:
        values["qualified"].close()


def test_representation_response_loss_ready_retry_has_no_new_choice_or_embedder_call(tmp_path: Path, monkeypatch):
    values = _database(tmp_path)
    try:
        embedder = _Embedder()
        choices = []
        runtime, _, _ = _runtime(values, embedder, choose=lambda concepts: choices.append(tuple(concepts)) or concepts[0])
        original = runtime._representations.publish_representation_ready
        first = True

        def lose_response(*args, **kwargs):
            nonlocal first
            result = original(*args, **kwargs)
            if first:
                first = False
                raise RuntimeError("forced Character READY response loss")
            return result

        monkeypatch.setattr(runtime._representations, "publish_representation_ready", lose_response)
        request = _request(_seed(motif_id=""))
        with pytest.raises(RuntimeError, match="READY response loss"):
            runtime.correct_for_post_write(request)
        before = _counts(values["connection"])
        recovered = runtime.correct_for_post_write(request)
        assert recovered.correction_applied and recovered.motif_status == "MOTIF_SKIPPED"
        assert len(embedder.calls) == 1 and len(choices) == 1
        assert _counts(values["connection"]) == before
    finally:
        values["qualified"].close()


def test_source_response_recovery_reembeds_exact_text_and_refuses_byte_drift(tmp_path: Path):
    values = _database(tmp_path)
    try:
        worlds, order = NativeWorldProcessState(), NativeMotifProcessOrder()
        first_embedder = _Embedder((1.0, 0.0, 0.0))
        first, _, _ = _runtime(values, first_embedder, worlds=worlds, order=order)
        request = _request(_seed(motif_id=""))
        first._world.ensure_initialized()
        source, _ = first._source(request, -0.35)  # deliberate source-response loss seam
        first._world.register_fresh_created(
            eid=source.eid, memory_object_id=source.memory_object_id,
            memory_revision_id=source.memory_revision_id, memory_revision_ordinal=1, born_step=10,
        )
        retries_choose = []
        changed, _, _ = _runtime(
            values,
            _Embedder((0.0, 1.0, 0.0)),
            worlds=worlds,
            order=order,
            choose=lambda concepts: retries_choose.append(tuple(concepts)) or concepts[0],
        )
        with pytest.raises(CharacterCorrectionEmbeddingNotByteStable, match="CHARACTER_CORRECTION_EMBEDDING_NOT_BYTE_STABLE"):
            changed.correct_for_post_write(request)
        assert len(first_embedder.calls) == 1
        assert retries_choose == []
        assert values["connection"].execute("SELECT count(*) FROM representations").fetchone()[0] == 0
    finally:
        values["qualified"].close()


def test_split_eligible_attach_is_explicit_retry_stable_and_never_writes_a_fake_membership(tmp_path: Path):
    values = _database(tmp_path)
    try:
        existing = _existing_memory(values)
        motif = _existing_motif(values, existing)
        embedder = _Embedder()
        runtime, _, _ = _runtime(values, embedder)
        original = NativeMotifRuntimeReader(values["connection"]).list_runtime_motifs(
            motif_alias_namespace_id=values["motif_alias"], domain_id="personal", semantic_scope_id=values["scope"],
        )
        model = original[0].read_model
        runtime._motif_reader = type("Reader", (), {
            "list_runtime_motifs": lambda _self, **_kwargs: (
                NativeRuntimeMotif(original[0].motif_object_id, original[0].motif_revision_id,
                    original[0].motif_revision_ordinal, original[0].semantic_scope_id,
                    replace(model, member_count=95)),
            ),
        })()
        before = values["connection"].execute("SELECT count(*) FROM relationships").fetchone()[0]
        result = runtime.correct_for_post_write(_request(_seed(motif_id="truthy")))
        assert result.status is CharacterGravityCorrectionStatus.CHARACTER_MOTIF_SPLIT_PARITY_REQUIRED
        assert result.motif_status == "CHARACTER_MOTIF_SPLIT_PARITY_REQUIRED"
        assert values["connection"].execute("SELECT count(*) FROM relationships").fetchone()[0] == before
        retry = runtime.correct_for_post_write(_request(_seed(motif_id="truthy")))
        assert retry.status is CharacterGravityCorrectionStatus.CHARACTER_MOTIF_SPLIT_PARITY_REQUIRED
        assert retry.motif_status == "CHARACTER_MOTIF_SPLIT_PARITY_REQUIRED"
        assert len(embedder.calls) == 1
        assert values["connection"].execute("SELECT count(*) FROM relationships").fetchone()[0] == before
    finally:
        values["qualified"].close()
