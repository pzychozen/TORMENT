"""Focused Phase 7G5A2 decision/persistence separation coverage."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from torment_service.motif_decision import (
    CURRENT_MOTIF_DECISION_POLICY,
    MotifReadModel,
    decide_attach_or_create,
    motif_label_from_summary,
    realize_attach_next_state,
)
from torment_service.motifs import Motif, MotifRegistry
from torment_service.substrate.compat import NativeMemoryCompatibilityFacade
from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.errors import SubstrateRevisionConflict
from torment_service.substrate.ids import generate_native_id, native_id_to_bytes
from torment_service.substrate.motif_decision_adapter import NativeMotifDecisionAdapter
from torment_service.substrate.motifs import MotifState, NativeMotifService
from torment_service.substrate.objects import NativeObjectService
from torment_service.substrate.schema import create_schema


def _read(
    motif_id: str,
    *,
    centroid=(1.0, 0.0),
    strength=0.0,
    members=0,
    stability=0.0,
    agents=("aria",),
) -> MotifReadModel:
    return MotifReadModel(motif_id, "reflection", f"{motif_id} label", centroid, strength, members, agents, stability, 100, 101)


def test_decision_preserves_create_threshold_dimension_and_iteration_contracts():
    no_motifs = decide_attach_or_create((), np.asarray([], dtype=np.float32), 0.72)
    assert no_motifs.kind == "CREATE_NEW"  # Current _unit empty-vector behavior is preserved.

    below = decide_attach_or_create((_read("below"),), np.asarray([0.5, np.sqrt(0.75)], dtype=np.float32), 0.72)
    assert below.kind == "CREATE_NEW"

    boundary = decide_attach_or_create((_read("boundary"),), np.asarray([0.62, np.sqrt(1.0 - 0.62 ** 2)], dtype=np.float32), 0.62)
    assert boundary.kind == "ATTACH_EXISTING"

    first = _read("first", centroid=(1.0, 0.0))
    second = _read("second", centroid=(1.0, 0.0))
    mismatch = _read("mismatch", centroid=(1.0, 0.0, 0.0))
    tied = decide_attach_or_create((mismatch, first, second), np.asarray([1.0, 0.0], dtype=np.float32), 0.72)
    assert tied.kind == "ATTACH_EXISTING"
    assert tied.selected.runtime_motif_id == "first"  # strict > keeps first-in-order tie winner


def test_decision_and_successor_match_current_density_gravity_and_attach_math():
    source = _read("motif_reflection_0001", strength=0.70, members=8, stability=0.80, agents=("aria",))
    candidate = np.asarray([0.8, 0.6], dtype=np.float32)
    decision = decide_attach_or_create((source,), candidate, 0.72, CURRENT_MOTIF_DECISION_POLICY)
    density = float(min(1.0, np.log1p(8) / np.log(129.0)))
    gravity = 0.10 * 0.70 + 0.07 * density + 0.05 * 0.80
    expected_raw = float(np.dot(candidate, np.asarray(source.centroid, dtype=np.float32)) / ((np.linalg.norm(candidate) + 1e-12) * (np.linalg.norm(source.centroid) + 1e-12)))
    assert decision.kind == "ATTACH_EXISTING"
    assert decision.pre_mutation_density == pytest.approx(density, abs=1e-12)
    assert decision.raw_similarity == pytest.approx(expected_raw, abs=1e-7)
    assert decision.attach_score == pytest.approx(expected_raw + gravity, abs=1e-7)
    assert decision.effective_threshold == pytest.approx(max(0.62, 0.72 - (0.04 * density + 0.03 * 0.70)), abs=1e-12)

    successor = realize_attach_next_state(decision, agent_id="nox", last_active_ts=102)
    learning_rate = float(np.clip(0.12 / np.sqrt(1.0 + 8 / 8.0), 0.025, 0.08))
    expected_centroid = np.asarray(source.centroid, dtype=np.float32)
    expected_centroid = expected_centroid / (np.linalg.norm(expected_centroid) + 1e-12)
    expected_centroid = (1.0 - learning_rate) * expected_centroid + learning_rate * candidate
    expected_centroid = expected_centroid / (np.linalg.norm(expected_centroid) + 1e-12)
    expected_strength = max(0.70, min(1.0, 0.12 + 0.88 * (1.0 - np.exp(-9 / 24.0))))
    expected_stability = np.clip(0.90 * 0.80 + 0.10 * max(0.0, expected_raw), 0.0, 1.0)
    assert np.asarray(successor.centroid) == pytest.approx(expected_centroid, abs=1e-7)
    assert successor.strength == pytest.approx(expected_strength, abs=1e-12)
    assert successor.stability_score == pytest.approx(expected_stability, abs=1e-12)
    assert successor.contributing_agents == ("aria", "nox")
    assert realize_attach_next_state(decision, agent_id="aria", last_active_ts=102).contributing_agents == ("aria",)
    assert motif_label_from_summary("reflection", "!!!") == "reflection motif"
    assert motif_label_from_summary("reflection", "A clear persistent reflective thread") == "clear persistent reflective thread"


def _legacy_registry(tmp_path: Path) -> MotifRegistry:
    return MotifRegistry(str(tmp_path), "decision_ws", "reflection")


def _legacy_motif(motif_id="motif_reflection_0001", members=None) -> Motif:
    return Motif(motif_id, "reflection", "Legacy basin", [1.0, 0.0], 0.70, [1] if members is None else members, ["aria"], 0.80, 100, 101)


def test_legacy_wrapper_preserves_return_shape_duplicate_append_and_save_event_order(tmp_path: Path, monkeypatch):
    registry = _legacy_registry(tmp_path)
    registry.motifs["motif_reflection_0001"] = _legacy_motif()
    calls: list[object] = []
    monkeypatch.setattr(registry, "save", lambda: calls.append("save"))
    monkeypatch.setattr(registry, "_log_event", lambda event: calls.append(event))
    monkeypatch.setattr(registry, "_maybe_split_motif", lambda _motif_id: None)
    result = registry.attach_or_create(np.asarray([1.0, 0.0], dtype=np.float32), 1, "aria", "unused", 0.72)
    assert result == (["motif_reflection_0001"], None)
    assert registry.motifs["motif_reflection_0001"].members == [1, 1]
    assert calls[0] == "save" and calls[1]["type"] == "MOTIF_ATTACH"
    assert calls[1]["density"] == pytest.approx(float(np.log1p(1) / np.log(129.0)))

    monkeypatch.setattr(registry, "_maybe_split_motif", lambda motif_id: {"parent": motif_id, "child": "child"})
    split = registry.attach_or_create(np.asarray([1.0, 0.0], dtype=np.float32), 2, "nox", "unused", 0.72)
    assert split == (["motif_reflection_0001", "child"], None)

    fresh = _legacy_registry(tmp_path / "fresh")
    fresh_calls: list[object] = []
    monkeypatch.setattr(fresh, "save", lambda: fresh_calls.append("save"))
    monkeypatch.setattr(fresh, "_log_event", lambda event: fresh_calls.append(event))
    created = fresh.attach_or_create(np.asarray([1.0, 0.0], dtype=np.float32), 7, "aria", "!!!", 0.72)
    assert created == (["motif_reflection_0001"], "motif_reflection_0001")
    assert fresh.motifs[created[1]].label == "reflection motif"
    assert fresh_calls[0] == "save" and fresh_calls[1]["type"] == "MOTIF_CREATE"

    empty = _legacy_registry(tmp_path / "empty")
    empty_created, empty_id = empty.attach_or_create(np.asarray([], dtype=np.float32), 8, "aria", "empty", 0.72)
    assert empty_created == [empty_id]
    assert empty.motifs[empty_id].centroid == []


def test_legacy_wrapper_persists_current_json_and_event_shape(tmp_path: Path):
    registry = _legacy_registry(tmp_path)
    created, created_id = registry.attach_or_create(np.asarray([1.0, 0.0], dtype=np.float32), 7, "aria", "A durable reflection", 0.72)
    assert created == [created_id]
    payload = json.loads(Path(registry.path).read_text(encoding="utf-8"))
    assert payload["motifs"][created_id]["members"] == [7]
    event = json.loads(Path(registry.events_path).read_text(encoding="utf-8").splitlines()[0])
    assert event == {
        "type": "MOTIF_CREATE", "motif_id": created_id, "memory_eid": 7,
        "agent_id": "aria", "label": "durable reflection", "workspace_id": "decision_ws",
        "domain_id": "reflection", "ts": event["ts"],
    }


def _id():
    return generate_native_id()


def _native_fixture(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "adapter.db")
    create_schema(qualified.connection)
    connection = qualified.connection
    motif_identity, membership_identity, memory_identity = _id(), _id(), _id()
    scope, memory_scope = _id(), _id()
    idempotency, memory_alias, motif_alias = _id(), _id(), _id()
    for value, key in ((motif_identity, "motif"), (membership_identity, "membership"), (memory_identity, "memory")):
        connection.execute("INSERT INTO identity_namespaces VALUES (?,?,0)", (native_id_to_bytes(value), key))
    for value, key in ((scope, "motif-scope"), (memory_scope, "memory-scope")):
        connection.execute("INSERT INTO semantic_scopes VALUES (?,?,0)", (native_id_to_bytes(value), key))
    connection.execute("INSERT INTO idempotency_namespaces VALUES (?,?)", (native_id_to_bytes(idempotency), "idem"))
    for value, key in ((memory_alias, "memory-alias"), (motif_alias, "motif-alias")):
        connection.execute("INSERT INTO legacy_source_namespaces VALUES (?,?,0)", (native_id_to_bytes(value), key))
    return qualified, {
        "connection": connection, "motif_identity": motif_identity, "membership_identity": membership_identity,
        "memory_identity": memory_identity, "scope": scope, "memory_scope": memory_scope,
        "idempotency": idempotency, "memory_alias": memory_alias, "motif_alias": motif_alias,
    }


def _native_memory(values, key: str):
    return NativeMemoryCompatibilityFacade(values["connection"]).create_memory_state(
        legacy_source_namespace_id=values["memory_alias"], idempotency_namespace_id=values["idempotency"],
        idempotency_key=key, identity_namespace_id=values["memory_identity"], semantic_scope_id=values["memory_scope"],
        summary=key, memory_type="reflection", logical_step=1,
    )


def test_native_adapter_applies_same_decisions_without_membership_payload_authority(tmp_path: Path):
    qualified, values = _native_fixture(tmp_path)
    try:
        service = NativeMotifService(values["connection"])
        adapter = NativeMotifDecisionAdapter(service)
        first_memory, second_memory, third_memory = _native_memory(values, "first"), _native_memory(values, "second"), _native_memory(values, "third")
        first_plan = adapter.decide(ordered_motif_object_ids=(), embedding=np.asarray([1.0, 0.0], dtype=np.float32), attach_threshold=0.72)
        created = adapter.apply(
            first_plan, member_object_id=first_memory.object_id, agent_id="aria", idempotency_namespace_id=values["idempotency"],
            idempotency_key="native-create", motif_alias_namespace_id=values["motif_alias"], membership_identity_namespace_id=values["membership_identity"],
            motif_identity_namespace_id=values["motif_identity"], runtime_motif_id="motif_reflection_0001", domain_id="reflection",
            semantic_scope_id=values["scope"], summary="A durable reflection", created_ts=100, last_active_ts=100,
        )
        assert created.motif_object_id != created.membership_relationship_id
        assert service.resolve_motif_alias(motif_alias_namespace_id=values["motif_alias"], runtime_motif_id="motif_reflection_0001") == created.motif_object_id
        assert len(service.list_current_motif_members(created.motif_object_id)) == 1
        assert values["connection"].execute("SELECT count(*) FROM representations").fetchone()[0] == 0
        source_before = NativeObjectService(values["connection"]).get_current_object(second_memory.object_id)
        attach_plan = adapter.decide(ordered_motif_object_ids=(created.motif_object_id,), embedding=np.asarray([1.0, 0.0], dtype=np.float32), attach_threshold=0.72)
        added = adapter.apply(
            attach_plan, member_object_id=second_memory.object_id, agent_id="nox", idempotency_namespace_id=values["idempotency"],
            idempotency_key="native-attach", motif_alias_namespace_id=values["motif_alias"], membership_identity_namespace_id=values["membership_identity"],
            last_active_ts=101,
        )
        current = service.get_current_motif(created.motif_object_id)
        assert current.motif_revision_id == added.motif_revision_id
        assert {item.member_object_id for item in service.list_current_motif_members(created.motif_object_id)} == {first_memory.object_id, second_memory.object_id}
        assert NativeObjectService(values["connection"]).get_current_object(second_memory.object_id) == source_before
        assert "members" not in current.state.payload() and "member_count" not in current.state.payload()
        assert values["connection"].execute("SELECT count(*) FROM representation_current_state WHERE readiness='READY'").fetchone()[0] == 0
        assert values["connection"].execute("SELECT count(*) FROM object_revisions WHERE authority_category='ACTIVE_AUTHORIZATION'").fetchone()[0] == 0

        duplicate_plan = adapter.decide(ordered_motif_object_ids=(created.motif_object_id,), embedding=np.asarray([1.0, 0.0], dtype=np.float32), attach_threshold=0.72)
        before = values["connection"].execute("SELECT count(*) FROM object_revisions").fetchone()[0]
        with pytest.raises(SubstrateRevisionConflict):
            adapter.apply(
                duplicate_plan, member_object_id=second_memory.object_id, agent_id="nox", idempotency_namespace_id=values["idempotency"],
                idempotency_key="native-duplicate", motif_alias_namespace_id=values["motif_alias"], membership_identity_namespace_id=values["membership_identity"],
                last_active_ts=102,
            )
        assert values["connection"].execute("SELECT count(*) FROM object_revisions").fetchone()[0] == before

        stale_plan = adapter.decide(ordered_motif_object_ids=(created.motif_object_id,), embedding=np.asarray([1.0, 0.0], dtype=np.float32), attach_threshold=0.72)
        state = current.state
        advanced = service.advance_motif_state(
            idempotency_namespace_id=values["idempotency"], idempotency_key="advance-before-stale", motif_alias_namespace_id=values["motif_alias"],
            motif_object_id=created.motif_object_id, expected_motif_revision_id=current.motif_revision_id,
            state=MotifState(state.semantic_scope_id, state.runtime_motif_id, state.domain_id, state.label, state.centroid, state.strength, state.stability_score, state.contributing_agents, state.created_ts, 102, state.derivation_metadata, state.extra_payload),
        )
        with pytest.raises(SubstrateRevisionConflict):
            adapter.apply(
                stale_plan, member_object_id=third_memory.object_id, agent_id="nox", idempotency_namespace_id=values["idempotency"],
                idempotency_key="native-stale", motif_alias_namespace_id=values["motif_alias"], membership_identity_namespace_id=values["membership_identity"],
                last_active_ts=103,
            )
        assert service.get_current_motif(created.motif_object_id).motif_revision_id == advanced.motif_revision_id
        assert {item.member_object_id for item in service.list_current_motif_members(created.motif_object_id)} == {first_memory.object_id, second_memory.object_id}
    finally:
        qualified.close()
