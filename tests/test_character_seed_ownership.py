"""Regression coverage for workspace-local CharacterSeed ownership."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import threading

import pytest
from fastapi import HTTPException

from torment_service.character import CharacterSeed
from torment_service.fabric import TormentFabric


WORKSPACE_ID = "seed-owner-workspace"


@pytest.fixture
def fabric():
    instance = TormentFabric(data_dir=":memory:")
    instance.get_workspace(WORKSPACE_ID)
    try:
        yield instance
    finally:
        instance.close()


def _seed(seed_id: str, text: str) -> dict:
    return {
        "seed_id": seed_id,
        "character_name": f"Character {seed_id}",
        "seed_text": text,
    }


def _assert_rejected_agent_has_no_residue(fabric: TormentFabric, agent_id: str) -> None:
    agent_key = fabric._agent_key(WORKSPACE_ID, agent_id)
    agent_dir = Path(fabric.data_dir) / "workspaces" / WORKSPACE_ID / "agents" / agent_id

    assert fabric.ident_store.load(WORKSPACE_ID, agent_id) is None
    assert agent_key not in fabric.private_graphs
    assert agent_key not in fabric.agent_states
    assert agent_key not in fabric._kernel_contexts
    assert fabric.character_store.load_state(WORKSPACE_ID, agent_id) is None
    assert not agent_dir.exists()


@pytest.mark.parametrize(
    "second_text",
    [
        "A different authored character with incompatible modulation.",
        "A first character with a stable and precise voice.",
    ],
)
def test_new_agent_cannot_reuse_existing_character_seed(
    fabric: TormentFabric, second_text: str
) -> None:
    seed_id = "shared-seed"
    first_text = "A first character with a stable and precise voice."
    fabric.create_agent(WORKSPACE_ID, "agent-a", seed=_seed(seed_id, first_text))

    with pytest.raises(HTTPException) as exc_info:
        fabric.create_agent(WORKSPACE_ID, "agent-b", seed=_seed(seed_id, second_text))

    assert exc_info.value.status_code == 409
    detail = str(exc_info.value.detail)
    assert WORKSPACE_ID in detail
    assert seed_id in detail
    assert "agent-b" in detail
    assert "agent-a" in detail
    persisted = fabric.character_store.load_seed(WORKSPACE_ID, seed_id)
    assert persisted is not None
    assert persisted.seed_text == first_text
    assert persisted.owner_agent_id == "agent-a"
    _assert_rejected_agent_has_no_residue(fabric, "agent-b")


def test_new_character_seed_is_stamped_with_its_owner(fabric: TormentFabric) -> None:
    fabric.create_agent(
        WORKSPACE_ID,
        "owner-agent",
        seed=_seed("owned-seed", "A character whose seed has a single owner."),
    )

    persisted = fabric.character_store.load_seed(WORKSPACE_ID, "owned-seed")
    assert persisted is not None
    assert persisted.owner_agent_id == "owner-agent"


def test_owned_seed_allows_its_same_agent_when_identity_is_missing(
    fabric: TormentFabric,
) -> None:
    fabric.character_store.save_seed(
        WORKSPACE_ID,
        CharacterSeed(
            seed_id="orphaned-owned-seed",
            character_name="Owned Character",
            seed_text="A persisted seed whose identity needs to be recreated.",
            owner_agent_id="owner-agent",
        ),
    )

    identity = fabric.create_agent(
        WORKSPACE_ID,
        "owner-agent",
        seed=_seed("orphaned-owned-seed", "The persisted seed text remains in place."),
    )

    assert identity.agent_id == "owner-agent"
    persisted = fabric.character_store.load_seed(WORKSPACE_ID, "orphaned-owned-seed")
    assert persisted is not None
    assert persisted.owner_agent_id == "owner-agent"


def test_legacy_seed_without_owner_rejects_new_agent_without_adopting_it(
    fabric: TormentFabric,
) -> None:
    legacy = CharacterSeed(
        seed_id="legacy-shared-seed",
        character_name="Legacy Character",
        seed_text="A legacy character record without an ownership field.",
    ).to_dict()
    legacy.pop("owner_agent_id")
    seed_path = Path(fabric.character_store._seed_path(WORKSPACE_ID, "legacy-shared-seed"))
    seed_path.parent.mkdir(parents=True, exist_ok=True)
    seed_path.write_text(json.dumps(legacy), encoding="utf-8")

    loaded = fabric.character_store.load_seed(WORKSPACE_ID, "legacy-shared-seed")
    assert loaded is not None
    assert loaded.owner_agent_id == ""

    with pytest.raises(HTTPException) as exc_info:
        fabric.create_agent(
            WORKSPACE_ID,
            "new-agent",
            seed=_seed("legacy-shared-seed", "A new text must not adopt a legacy seed."),
        )

    assert exc_info.value.status_code == 409
    reloaded = fabric.character_store.load_seed(WORKSPACE_ID, "legacy-shared-seed")
    assert reloaded is not None
    assert reloaded.owner_agent_id == ""
    _assert_rejected_agent_has_no_residue(fabric, "new-agent")


def test_existing_agent_create_is_idempotent_even_with_changed_seed_payload(
    fabric: TormentFabric,
) -> None:
    original = _seed("original-seed", "The original authored text remains authoritative.")
    fabric.create_agent(WORKSPACE_ID, "agent-a", seed=original)

    fabric.create_agent(
        WORKSPACE_ID,
        "agent-a",
        seed=_seed("original-seed", "This changed text must be ignored."),
    )
    fabric.create_agent(
        WORKSPACE_ID,
        "agent-a",
        seed=_seed("changed-seed", "This changed identifier must also be ignored."),
    )

    identity = fabric.ident_store.load(WORKSPACE_ID, "agent-a")
    assert identity is not None
    assert identity.seed == original
    persisted = fabric.character_store.load_seed(WORKSPACE_ID, "original-seed")
    assert persisted is not None
    assert persisted.seed_text == original["seed_text"]
    assert persisted.owner_agent_id == "agent-a"
    assert fabric.character_store.load_seed(WORKSPACE_ID, "changed-seed") is None


def test_different_seed_ids_create_independent_owned_character_seeds(
    fabric: TormentFabric,
) -> None:
    fabric.create_agent(WORKSPACE_ID, "agent-a", seed=_seed("seed-a", "First seed."))
    fabric.create_agent(WORKSPACE_ID, "agent-b", seed=_seed("seed-b", "Second seed."))

    first = fabric.character_store.load_seed(WORKSPACE_ID, "seed-a")
    second = fabric.character_store.load_seed(WORKSPACE_ID, "seed-b")
    assert first is not None and first.owner_agent_id == "agent-a"
    assert second is not None and second.owner_agent_id == "agent-b"


def test_unseeded_creation_does_not_look_up_a_character_seed(
    fabric: TormentFabric, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = []
    original_load_seed = fabric.character_store.load_seed

    def record_load_seed(workspace_id: str, seed_id: str):
        calls.append((workspace_id, seed_id))
        return original_load_seed(workspace_id, seed_id)

    monkeypatch.setattr(fabric.character_store, "load_seed", record_load_seed)
    fabric.create_agent(WORKSPACE_ID, "unseeded-agent")

    assert calls == []


def test_concurrent_new_agents_share_one_seed_owner_and_reject_the_loser(
    fabric: TormentFabric,
) -> None:
    seed_id = "concurrent-seed"
    barrier = threading.Barrier(2)

    def create(agent_id: str) -> tuple[str, int | None]:
        barrier.wait()
        try:
            fabric.create_agent(
                WORKSPACE_ID,
                agent_id,
                seed=_seed(seed_id, f"Concurrent seed for {agent_id}."),
            )
            return agent_id, None
        except HTTPException as exc:
            return agent_id, exc.status_code

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(create, ("agent-a", "agent-b")))

    winners = [agent_id for agent_id, status_code in outcomes if status_code is None]
    rejected = [agent_id for agent_id, status_code in outcomes if status_code == 409]
    assert len(winners) == 1
    assert len(rejected) == 1
    persisted = fabric.character_store.load_seed(WORKSPACE_ID, seed_id)
    assert persisted is not None
    assert persisted.owner_agent_id == winners[0]
    _assert_rejected_agent_has_no_residue(fabric, rejected[0])
