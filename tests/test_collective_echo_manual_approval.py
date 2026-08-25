"""Focused regression coverage for collective-derived proposal authority."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from torment_service.fabric import TormentFabric


WORKSPACE = "collective_echo_manual_approval"
DOMAIN = "research"


@pytest.fixture
def fabric(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("TORMENT_EMBED_PROVIDER", "hash")
    monkeypatch.setenv("TORMENT_COMPRESS_ENABLE", "0")
    monkeypatch.setenv("TORMENT_SRG_ENABLE", "0")
    monkeypatch.setenv("TORMENT_SQLITE_INDEX_ENABLE", "0")
    with TormentFabric(data_dir=str(tmp_path)) as instance:
        instance.get_workspace(WORKSPACE, domains=[DOMAIN])
        yield instance


def _embedding(second_component: float = 0.0) -> list[float]:
    vector = np.zeros(384, dtype=np.float32)
    vector[0] = 1.0
    vector[1] = second_component
    return (vector / np.linalg.norm(vector)).tolist()


def _proposal(
    fabric: TormentFabric,
    *,
    agent_id: str,
    summary: str,
    mtype: str,
    strength: float = 0.8,
    confidence: float = 0.9,
    embedding: list[float] | None = None,
) -> dict:
    return fabric.propose_share(
        workspace_id=WORKSPACE,
        agent_id=agent_id,
        summary=summary,
        embedding=embedding or _embedding(),
        domain_id=DOMAIN,
        mtype=mtype,
        strength=strength,
        confidence=confidence,
    )["proposal"]


def _registry(fabric: TormentFabric):
    return fabric.get_workspace(WORKSPACE).proposals[DOMAIN]


def test_collective_direct_approval_is_refused_without_mutation(
    fabric: TormentFabric,
) -> None:
    proposal = _proposal(
        fabric,
        agent_id="collective_evidence",
        summary="[collective proposal] convergence metadata",
        mtype="collective_echo",
    )
    workspace = fabric.get_workspace(WORKSPACE)
    shared = workspace.shared_graphs[DOMAIN]
    shared_before = len(shared.entities)
    registry = _registry(fabric)

    with pytest.raises(
        ValueError,
        match="collective-derived proposals require the grouped independent-authority path",
    ):
        fabric.decide_proposal(
            workspace_id=WORKSPACE,
            domain_id=DOMAIN,
            proposal_id=proposal["proposal_id"],
            decision="approve",
        )

    assert len(shared.entities) == shared_before
    assert registry.apply_events()[proposal["proposal_id"]].status == "pending"
    assert not Path(registry.events_path).exists(), "refusal must not append a decision event"


def test_collective_direct_rejection_remains_available(fabric: TormentFabric) -> None:
    proposal = _proposal(
        fabric,
        agent_id="collective_evidence",
        summary="[collective proposal] convergence metadata",
        mtype="collective_echo",
    )

    result = fabric.decide_proposal(
        workspace_id=WORKSPACE,
        domain_id=DOMAIN,
        proposal_id=proposal["proposal_id"],
        decision="reject",
    )

    assert result == {"ok": True, "decision": "rejected", "proposal_id": proposal["proposal_id"]}
    assert _registry(fabric).apply_events()[proposal["proposal_id"]].status == "rejected"


def test_non_collective_direct_approval_preserves_canonical_fields(
    fabric: TormentFabric,
) -> None:
    summary = "Operator-reviewed ordinary proposition."
    proposal = _proposal(
        fabric,
        agent_id="ordinary_agent",
        summary=summary,
        mtype="fact",
        strength=0.84,
        confidence=0.91,
    )

    result = fabric.decide_proposal(
        workspace_id=WORKSPACE,
        domain_id=DOMAIN,
        proposal_id=proposal["proposal_id"],
        decision="approve",
    )

    payload = fabric.get_workspace(WORKSPACE).shared_graphs[DOMAIN].entities[
        result["created_shared_eid"]
    ].payload
    assert payload["summary"] == summary
    assert payload["type"] == "fact"
    assert payload["strength"] == 0.84
    assert payload["confidence"] == 0.91
    assert payload["canon"] is True
    assert payload["half_life"] == 30.0
    assert payload["source"] == "proposal_manual"
    assert payload["support_agents"] == ["ordinary_agent"]


def test_refused_collective_proposal_remains_group_evidence_after_quorum(
    fabric: TormentFabric,
) -> None:
    first_summary = "Independent authority proposition from agent A."
    collective = _proposal(
        fabric,
        agent_id="collective_evidence",
        summary="[collective proposal] convergence metadata",
        mtype="collective_echo",
        strength=0.99,
        confidence=0.99,
        embedding=_embedding(0.2),
    )
    with pytest.raises(ValueError):
        fabric.decide_proposal(
            workspace_id=WORKSPACE,
            domain_id=DOMAIN,
            proposal_id=collective["proposal_id"],
            decision="approve",
        )

    first = _proposal(
        fabric,
        agent_id="genuine_a",
        summary=first_summary,
        mtype="fact",
        strength=0.8,
        embedding=_embedding(0.0),
    )
    second = _proposal(
        fabric,
        agent_id="genuine_b",
        summary="Independent authority proposition from agent B.",
        mtype="fact",
        strength=0.7,
        embedding=_embedding(0.1),
    )

    processed = fabric.process_proposals(workspace_id=WORKSPACE, domain_id=DOMAIN)

    assert processed["approved"] == 3
    shared = fabric.get_workspace(WORKSPACE).shared_graphs[DOMAIN].entities[
        processed["created_shared_eids"][0]
    ].payload
    assert shared["summary"] == first_summary
    assert shared["support_agents"] == ["genuine_a", "genuine_b"]
    assert set(shared["source_proposal_ids"]) == {
        collective["proposal_id"],
        first["proposal_id"],
        second["proposal_id"],
    }


def test_one_genuine_proposal_and_echo_do_not_form_quorum(fabric: TormentFabric) -> None:
    collective = _proposal(
        fabric,
        agent_id="collective_evidence",
        summary="[collective proposal] convergence metadata",
        mtype="collective_echo",
        embedding=_embedding(0.1),
    )
    genuine = _proposal(
        fabric,
        agent_id="genuine_a",
        summary="Independent authority proposition from agent A.",
        mtype="fact",
        embedding=_embedding(0.0),
    )

    processed = fabric.process_proposals(workspace_id=WORKSPACE, domain_id=DOMAIN)

    assert processed["approved"] == 0
    assert processed["created_shared_eids"] == []
    pending = _registry(fabric).list_pending(limit=10)
    assert {proposal.proposal_id for proposal in pending} == {
        collective["proposal_id"], genuine["proposal_id"]
    }
