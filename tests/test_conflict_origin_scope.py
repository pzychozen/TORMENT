"""Focused regression coverage for qualified ConflictRegistry origins."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from torment_service.conflicts import ConflictRegistry
from torment_service.fabric import (
    TormentFabric,
    _build_conflict_map,
    _conflict_hit_key,
)


WORKSPACE_ID = "conflict-origin-workspace"
DOMAIN_A = "research"
DOMAIN_B = "operations"


@pytest.fixture
def registry(tmp_path: Path) -> ConflictRegistry:
    return ConflictRegistry(str(tmp_path), WORKSPACE_ID, DOMAIN_A)


def _workspace(*registries: ConflictRegistry) -> SimpleNamespace:
    return SimpleNamespace(conflicts={registry.domain_id: registry for registry in registries})


def _private_hit(agent_id: str, eid: int) -> dict:
    return {"scope": "private", "agent_id": agent_id, "eid": eid}


def _shared_hit(domain_id: str, eid: int) -> dict:
    return {"scope": "shared", "domain_id": domain_id, "eid": eid}


def test_private_ingest_producer_stamps_private_origin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TORMENT_EMBED_PROVIDER", "hash")
    fabric = TormentFabric(data_dir=":memory:")
    try:
        fabric.get_workspace(WORKSPACE_ID)
        fabric.create_agent(WORKSPACE_ID, "atlas")
        fabric.ingest(
            workspace_id=WORKSPACE_ID,
            agent_id="atlas",
            text="The release is deployed to production today.",
            step=1,
            scope="private",
        )
        fabric.ingest(
            workspace_id=WORKSPACE_ID,
            agent_id="atlas",
            text="The release is not deployed to production today.",
            step=2,
            scope="private",
        )

        conflicts = [
            conflict
            for conflict in fabric.get_workspace(WORKSPACE_ID).conflicts.values()
            for conflict in conflict.list(status="open", limit=500)
        ]
        assert conflicts
        assert all(conflict.origin_scope == "private" for conflict in conflicts)
        assert all(conflict.origin_agent_id == "atlas" for conflict in conflicts)
        assert all(conflict.origin_domain_id is None for conflict in conflicts)
    finally:
        fabric.close()


def test_shared_producer_stamps_shared_origin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TORMENT_EMBED_PROVIDER", "hash")
    fabric = TormentFabric(data_dir=":memory:")
    try:
        workspace = fabric.get_workspace(WORKSPACE_ID)
        domain_id = workspace.domains[0]
        embedding = fabric.kernel.embedder.embed("release deployment status")
        fabric.propose_share(
            WORKSPACE_ID,
            "atlas",
            "The release is deployed to production today.",
            embedding=embedding,
            domain_id=domain_id,
        )
        fabric.process_proposals(
            WORKSPACE_ID, domain_id, min_distinct_agents=1, sim_threshold=0.0
        )
        fabric.propose_share(
            WORKSPACE_ID,
            "beacon",
            "The release is not deployed to production today.",
            embedding=embedding,
            domain_id=domain_id,
        )
        fabric.process_proposals(
            WORKSPACE_ID, domain_id, min_distinct_agents=1, sim_threshold=0.0
        )

        conflicts = workspace.conflicts[domain_id].list(status="open", limit=500)
        assert conflicts
        assert all(conflict.origin_scope == "shared" for conflict in conflicts)
        assert all(conflict.origin_agent_id is None for conflict in conflicts)
        assert all(conflict.origin_domain_id == domain_id for conflict in conflicts)
    finally:
        fabric.close()


def test_private_conflict_does_not_tag_colliding_shared_query_or_trace(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TORMENT_EMBED_PROVIDER", "hash")
    fabric = TormentFabric(data_dir=":memory:")
    try:
        workspace = fabric.get_workspace(WORKSPACE_ID)
        domain_id = workspace.domains[0]
        fabric.create_agent(WORKSPACE_ID, "agent-a")
        fabric.ingest(
            workspace_id=WORKSPACE_ID,
            agent_id="agent-a",
            text="The release is deployed to production today.",
            step=1,
            domain_id=domain_id,
        )
        fabric.ingest(
            workspace_id=WORKSPACE_ID,
            agent_id="agent-a",
            text="The release is not deployed to production today.",
            step=2,
            domain_id=domain_id,
        )
        private_conflict = workspace.conflicts[domain_id].list(status="open", limit=1)[0]

        embedding = fabric.kernel.embedder.embed("release deployment status")
        fabric.propose_share(
            WORKSPACE_ID,
            "publisher",
            "The release is deployed to production today.",
            embedding=embedding,
            domain_id=domain_id,
        )
        fabric.process_proposals(
            WORKSPACE_ID, domain_id, min_distinct_agents=1, sim_threshold=0.0
        )
        shared_eid = next(iter(workspace.shared_graphs[domain_id].entities))
        assert shared_eid in {private_conflict.eid_a, private_conflict.eid_b}

        query = fabric.query(
            WORKSPACE_ID, "observer", "release deployment status",
            domain_id=domain_id, top_k=20, explain=True,
        )
        query_hit = next(
            hit for hit in query["results"]
            if hit.get("scope") == "shared" and int(hit["eid"]) == shared_eid
        )
        assert query_hit["explain"]["conflict_status"] is None
        assert query_hit["explain"]["conflict_penalty"] == 0.0

        trace = fabric.trace(
            WORKSPACE_ID, "observer", "release deployment status", [shared_eid],
            domain_id=domain_id,
        )
        trace_hit = next(hit for hit in trace["items"] if hit.get("scope") == "shared")
        assert trace_hit["explain"]["conflict_status"] is None
        assert trace_hit["explain"]["conflict_penalty"] == 0.0
    finally:
        fabric.close()


def test_shared_conflict_tags_matching_shared_query_and_trace(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TORMENT_EMBED_PROVIDER", "hash")
    fabric = TormentFabric(data_dir=":memory:")
    try:
        workspace = fabric.get_workspace(WORKSPACE_ID)
        domain_id = workspace.domains[0]
        embedding = fabric.kernel.embedder.embed("release deployment status")
        for agent_id, text in (
            ("atlas", "The release is deployed to production today."),
            ("beacon", "The release is not deployed to production today."),
        ):
            fabric.propose_share(
                WORKSPACE_ID, agent_id, text, embedding=embedding, domain_id=domain_id
            )
            fabric.process_proposals(
                WORKSPACE_ID, domain_id, min_distinct_agents=1, sim_threshold=0.0
            )

        conflict = workspace.conflicts[domain_id].list(status="open", limit=1)[0]
        target_eid = int(conflict.eid_a)
        query = fabric.query(
            WORKSPACE_ID, "observer", "release deployment status",
            domain_id=domain_id, top_k=20, explain=True,
        )
        query_hit = next(
            hit for hit in query["results"]
            if hit.get("scope") == "shared" and int(hit["eid"]) == target_eid
        )
        assert query_hit["explain"]["conflict_status"] == "open"
        assert query_hit["explain"]["conflict_penalty"] == pytest.approx(
            conflict.conflict_score
        )

        trace = fabric.trace(
            WORKSPACE_ID, "observer", "release deployment status", [target_eid],
            domain_id=domain_id,
        )
        trace_hit = next(hit for hit in trace["items"] if hit.get("scope") == "shared")
        assert trace_hit["explain"]["conflict_status"] == "open"
        assert trace_hit["explain"]["conflict_penalty"] == pytest.approx(
            conflict.conflict_score
        )
    finally:
        fabric.close()


@pytest.mark.parametrize(
    "origin_scope,origin_agent_id,origin_domain_id",
    [
        ("private", None, None),
        ("private", "agent-a", "research"),
        ("shared", None, None),
        ("shared", "agent-a", "research"),
        ("unknown", None, None),
        (None, "agent-a", None),
    ],
)
def test_invalid_origin_combinations_fail_before_append(
    registry: ConflictRegistry,
    origin_scope: str | None,
    origin_agent_id: str | None,
    origin_domain_id: str | None,
) -> None:
    before = Path(registry.path).read_text(encoding="utf-8") if Path(registry.path).exists() else ""

    with pytest.raises(ValueError):
        registry.add(
            10,
            11,
            0.9,
            0.7,
            "invalid origin",
            origin_scope=origin_scope,
            origin_agent_id=origin_agent_id,
            origin_domain_id=origin_domain_id,
        )

    after = Path(registry.path).read_text(encoding="utf-8") if Path(registry.path).exists() else ""
    assert after == before


def test_private_conflicts_do_not_match_other_agent_or_shared_eid(
    registry: ConflictRegistry,
) -> None:
    conflict = registry.add(
        17,
        18,
        0.91,
        0.72,
        "private conflict",
        origin_scope="private",
        origin_agent_id="agent-a",
    )
    conflict_map = _build_conflict_map(_workspace(registry), WORKSPACE_ID, [DOMAIN_A])

    assert _conflict_hit_key(_private_hit("agent-a", 17)) in conflict_map
    assert _conflict_hit_key(_private_hit("agent-b", 17)) not in conflict_map
    assert _conflict_hit_key(_shared_hit(DOMAIN_A, 17)) not in conflict_map
    assert conflict.conflict_id in conflict_map[("private", "agent-a", 17)]["conflict_ids"]


def test_shared_conflicts_match_only_their_origin_domain(tmp_path: Path) -> None:
    first = ConflictRegistry(str(tmp_path), WORKSPACE_ID, DOMAIN_A)
    second = ConflictRegistry(str(tmp_path), WORKSPACE_ID, DOMAIN_B)
    first.add(
        23,
        24,
        0.93,
        0.81,
        "shared conflict",
        origin_scope="shared",
        origin_domain_id=DOMAIN_A,
    )
    conflict_map = _build_conflict_map(
        _workspace(first, second), WORKSPACE_ID, [DOMAIN_A, DOMAIN_B]
    )

    matching = _conflict_hit_key(_shared_hit(DOMAIN_A, 23))
    other_domain = _conflict_hit_key(_shared_hit(DOMAIN_B, 23))
    assert matching in conflict_map
    assert conflict_map[matching]["max_score"] == pytest.approx(0.81)
    assert other_domain not in conflict_map


def test_legacy_rows_are_listable_but_ignored_for_qualified_lookup(
    registry: ConflictRegistry,
) -> None:
    legacy_row = {
        "conflict_id": "legacy-row",
        "workspace_id": WORKSPACE_ID,
        "domain_id": DOMAIN_A,
        "eid_a": 31,
        "eid_b": 32,
        "sim": 0.9,
        "conflict_score": 0.7,
        "reason": "legacy",
        "status": "open",
        "created_ts": 1,
    }
    Path(registry.path).write_text(json.dumps(legacy_row) + "\n", encoding="utf-8")

    listed = registry.list(status="open")
    assert listed[0].origin_scope is None
    conflict_map = _build_conflict_map(_workspace(registry), WORKSPACE_ID, [DOMAIN_A])
    assert _conflict_hit_key(_shared_hit(DOMAIN_A, 31)) not in conflict_map
    assert _conflict_hit_key(_private_hit("agent-a", 31)) not in conflict_map
