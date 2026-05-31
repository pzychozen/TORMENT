"""Focused G1 regressions for fail-closed ordinary-ingest canon authority."""

from __future__ import annotations

import tempfile
from contextlib import contextmanager
from typing import Iterator
from unittest.mock import patch

import pytest

from torment_service.fabric import TormentFabric


@pytest.fixture
def fabric() -> Iterator[TormentFabric]:
    data_dir = tempfile.mkdtemp(prefix="torment_g1_fail_closed_")
    instance = TormentFabric(data_dir=data_dir)
    instance.get_workspace("test-ws")
    instance.create_agent("test-ws", "agent-1")
    try:
        yield instance
    finally:
        instance.close()


def _payload_for(fabric: TormentFabric, eid: int) -> dict:
    agent_key = fabric._agent_key("test-ws", "agent-1")
    return fabric.private_graphs[agent_key].entities[int(eid)].payload


@contextmanager
def _forced_high_promotion(fabric: TormentFabric):
    real_process = fabric.kernel.process

    def patched_process(state, text, runtime_ctx):
        state_out, signals, debug = real_process(state, text, runtime_ctx)
        signals.write_intent = True
        signals.strength = 1.0
        signals.confidence = 1.0
        signals.promotion_score = 1.0
        return state_out, signals, debug

    with patch.object(fabric.kernel, "process", side_effect=patched_process):
        yield


@pytest.mark.parametrize(
    "text",
    [
        "The weather is mild today, with a little wind near the river.",
        "A copper paperclip sits beside the blue notebook.",
        "Eland's mother survived the bridge collapse and recovered at the hill clinic.",
    ],
)
def test_high_coh_ordinary_ingest_stays_retrievable_without_canon_authority(
    fabric: TormentFabric,
    text: str,
) -> None:
    with _forced_high_promotion(fabric):
        result = fabric.ingest(
            workspace_id="test-ws",
            agent_id="agent-1",
            text=text,
            step=10,
        )

    assert result["stored"] is True
    assert result["signals"]["promotion_score"] == 1.0
    payload = _payload_for(fabric, result["eid"])
    assert payload["canon"] is False
    assert payload["lifecycle_status"]["state"] == "unset"
    assert payload["lifecycle_status"]["set_by"]["via"] == "ingest_unmarked"

    retrieval = fabric.query(
        workspace_id="test-ws",
        agent_id="agent-1",
        query_text=text,
        top_k=8,
    )
    assert any(int(hit["eid"]) == int(result["eid"]) for hit in retrieval["results"])


def test_operator_approved_proposal_still_materializes_shared_canon(
    fabric: TormentFabric,
) -> None:
    proposed = fabric.propose_share(
        workspace_id="test-ws",
        agent_id="agent-1",
        summary="Operator-reviewed harbor protocol.",
        domain_id="personal",
        strength=0.9,
        confidence=0.9,
    )
    proposal_id = proposed["proposal"]["proposal_id"]

    approved = fabric.decide_proposal(
        workspace_id="test-ws",
        domain_id="personal",
        proposal_id=proposal_id,
        decision="approve",
        note="G1 governed-path regression",
    )
    payload = fabric.get_workspace("test-ws").shared_graphs["personal"].entities[
        approved["created_shared_eid"]
    ].payload

    assert payload["canon"] is True
    assert payload["lifecycle_status"]["state"] == "protected"
    assert payload["lifecycle_status"]["set_by"]["via"] == "canon_set"


def test_corroborated_proposals_still_materialize_shared_canon(
    fabric: TormentFabric,
) -> None:
    fabric.create_agent("test-ws", "agent-2")
    summary = "Two agents corroborated the harbor evacuation protocol."
    for agent_id in ("agent-1", "agent-2"):
        fabric.propose_share(
            workspace_id="test-ws",
            agent_id=agent_id,
            summary=summary,
            domain_id="personal",
            strength=0.9,
            confidence=0.9,
        )

    processed = fabric.process_proposals(
        workspace_id="test-ws",
        domain_id="personal",
        sim_threshold=0.95,
        min_distinct_agents=2,
        step=20,
    )

    assert processed["approved_groups"] == 1
    eid = processed["created_shared_eids"][0]
    payload = fabric.get_workspace("test-ws").shared_graphs["personal"].entities[eid].payload
    assert payload["canon"] is True
    assert payload["lifecycle_status"]["state"] == "protected"
    assert payload["lifecycle_status"]["set_by"]["via"] == "canon_set"
