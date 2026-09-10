"""Disposable tests for the ratified two-field Character rebaseline."""
from __future__ import annotations

import hashlib
from pathlib import Path
from uuid import uuid4

import pytest

from torment_service.character import CharacterSeed, CharacterState, CharacterStore
from torment_service.substrate.character_baseline_disposition import (
    CharacterBaselineBinding,
    CharacterBaselineDispositionOwner,
    CharacterBaselineRefused,
    CharacterBaselineRequest,
    QualifiedTargetGeometry,
    character_state_semantic_digest,
)


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _request() -> CharacterBaselineRequest:
    return CharacterBaselineRequest(
        workspace_id="ws",
        agent_id="agent",
        seed_id="seed",
        operation_key="character-baseline:one",
        binding=CharacterBaselineBinding(
            corrected_core_id=uuid4(), p6_receipt_id=str(uuid4()),
            root_admission_envelope_digest=_digest("envelope"), plan_digest=_digest("plan"),
        ),
        target_geometry=QualifiedTargetGeometry(
            target_representation_identity="native:qualified:384",
            ordered_native_memory_digest=_digest("ordered-memory"),
            native_seed_geometry_digest=_digest("seed-geometry"),
            expected_dimension=384, distance_to_seed=0.8125,
        ),
    )


def _prepared(root: Path) -> tuple[CharacterStore, CharacterBaselineDispositionOwner, CharacterBaselineRequest, CharacterState]:
    store = CharacterStore(str(root))
    seed = CharacterSeed(seed_id="seed", character_name="A", seed_text="a sufficiently long character seed.", seed_motif_id="motif", seed_eids=[1])
    store.save_seed("ws", seed)
    state = CharacterState(
        workspace_id="ws", agent_id="agent", seed_id="seed", drift_score=-0.44,
        drift_direction="away_seed", distance_to_seed=0.21, seed_basin_phi=0.9,
        seed_basin_kappa=0.8, seed_basin_tension=0.7, seed_basin_role="basin",
        core_count=3, relational_count=4, situational_count=5, drift_history=[(1, -0.1), (2, -0.44)],
    )
    store.save_state("ws", state)
    return store, CharacterBaselineDispositionOwner(data_root=root, store=store), _request(), state


def test_target_geometry_rebaseline_changes_only_the_ratified_two_fields(tmp_path: Path):
    store, owner, request, predecessor = _prepared(tmp_path)
    receipt = owner.execute(request)
    successor = store.load_state("ws", "agent")
    assert successor is not None
    assert successor.distance_to_seed == pytest.approx(0.8125)
    assert successor.drift_direction == "stable"
    before = predecessor.to_dict(); after = successor.to_dict()
    for field in before:
        if field not in {"distance_to_seed", "drift_direction", "updated_ts"}:
            assert after[field] == before[field]
    assert owner.verify_completed_receipt_digest(receipt.digest) == receipt
    assert owner.execute(request) == receipt


def test_completed_receipt_refuses_if_a_later_state_overwrites_the_exact_successor(tmp_path: Path):
    store, owner, request, _predecessor = _prepared(tmp_path)
    receipt = owner.execute(request)
    changed = store.load_state("ws", "agent")
    assert changed is not None
    changed.core_count += 1
    store.save_state("ws", changed)
    with pytest.raises(CharacterBaselineRefused, match="completion no longer matches"):
        owner.execute(request)
    with pytest.raises(CharacterBaselineRefused, match="no longer proves"):
        owner.verify_completed_receipt_digest(receipt.digest)


def test_prepared_record_recovers_only_when_the_exact_predecessor_is_stable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    store, owner, request, _predecessor = _prepared(tmp_path)
    real_save = store.save_state
    calls = 0

    def crash_after_save(workspace_id: str, state: CharacterState) -> None:
        nonlocal calls
        calls += 1
        real_save(workspace_id, state)
        if calls == 1:
            raise RuntimeError("simulated crash after CharacterStore persistence")

    monkeypatch.setattr(store, "save_state", crash_after_save)
    with pytest.raises(RuntimeError, match="simulated crash"):
        owner.execute(request)
    monkeypatch.setattr(store, "save_state", real_save)
    recovered = CharacterBaselineDispositionOwner(data_root=tmp_path, store=store).execute(request)
    assert owner.verify_completed_receipt_digest(recovered.digest) == recovered
    assert character_state_semantic_digest(store.load_state("ws", "agent")) == recovered.successor_semantic_digest
