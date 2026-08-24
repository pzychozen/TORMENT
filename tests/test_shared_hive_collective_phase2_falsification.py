"""Real-path Phase 2 characterization for Shared / Hive / Collective.

These tests intentionally use TormentFabric rather than constructing packet,
event, or proposal objects directly.  They operate only in pytest-provided
temporary data roots and record the current scope-transition behavior.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pytest

from torment_service.collective_policy import CollectivePolicy
from torment_service.fabric import TormentFabric


WORKSPACE = "hive_phase2_ws"
CONTROL_WORKSPACE = "hive_phase2_control"
DIRECT_WORKSPACE = "hive_phase2_direct"
E4_WORKSPACE = "hive_phase2_e4"
E5_WORKSPACE = "hive_phase2_e5"
E7_WORKSPACE_A = "hive_phase2_e7_a"
E7_WORKSPACE_B = "hive_phase2_e7_b"
REPRESENTATIVE_WORKSPACE = "hive_phase2_representative"
DOMAIN = "research"


@pytest.fixture
def fabric(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Real Fabric with only deterministic, already-supported test settings."""
    monkeypatch.setenv("TORMENT_HIVEMIND_ENABLE", "1")
    monkeypatch.setenv("TORMENT_EMBED_PROVIDER", "hash")
    monkeypatch.setenv("TORMENT_COMPRESS_ENABLE", "0")
    monkeypatch.setenv("TORMENT_SRG_ENABLE", "0")
    monkeypatch.setenv("TORMENT_SQLITE_INDEX_ENABLE", "0")
    with TormentFabric(data_dir=str(tmp_path)) as instance:
        yield instance


@pytest.fixture
def telemetry_fabric(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Real Fabric with optional Hivemind decision telemetry enabled."""
    monkeypatch.setenv("TORMENT_HIVEMIND_ENABLE", "1")
    monkeypatch.setenv("TORMENT_HIVEMIND_TELEMETRY", "1")
    monkeypatch.setenv("TORMENT_EMBED_PROVIDER", "hash")
    monkeypatch.setenv("TORMENT_COMPRESS_ENABLE", "0")
    monkeypatch.setenv("TORMENT_SRG_ENABLE", "0")
    monkeypatch.setenv("TORMENT_SQLITE_INDEX_ENABLE", "0")
    with TormentFabric(data_dir=str(tmp_path)) as instance:
        yield instance


def _embedding() -> list[float]:
    """A valid deterministic 384-dimension input for the ordinary ingest API."""
    return np.linspace(0.1, 1.0, 384, dtype=np.float32).tolist()


def _proposal_embedding(second_component: float) -> list[float]:
    """Near-identical vectors with a deliberate, inspectable distinction."""
    embedding = np.zeros(384, dtype=np.float32)
    embedding[0] = 1.0
    embedding[1] = second_component
    return (embedding / np.linalg.norm(embedding)).tolist()


def _prepare_workspace(fabric: TormentFabric, workspace_id: str) -> None:
    fabric.get_workspace(workspace_id, domains=[DOMAIN])


def _ingest_until_stored(
    fabric: TormentFabric,
    *,
    workspace_id: str,
    agent_id: str,
    label: str,
    extra_payload: dict | None = None,
) -> dict:
    """Drive only normal Fabric ingests until its existing write gate stores one."""
    for step in range(1, 25):
        result = fabric.ingest(
            workspace_id=workspace_id,
            agent_id=agent_id,
            text=(
                f"{label} research observation {step}: "
                "the shared oscillator study found a repeatable signal."
            ),
            step=step,
            domain_id=DOMAIN,
            supplied_embedding=_embedding(),
            extra_payload=extra_payload,
        )
        if result["stored"]:
            return result
    raise AssertionError(f"normal ingest did not store a memory for {agent_id!r}")


def _jsonl_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _real_convergence_event(
    fabric: TormentFabric,
    *,
    workspace_id: str,
    agents: tuple[str, str] = ("agent_a", "agent_b"),
) -> dict:
    """Create one event only through normal Fabric ingest and Hive emission."""
    _prepare_workspace(fabric, workspace_id)
    for agent_id in agents:
        _ingest_until_stored(
            fabric,
            workspace_id=workspace_id,
            agent_id=agent_id,
            label=f"{workspace_id}_{agent_id}",
        )
    events = fabric._get_collective_field(workspace_id).recent_events(limit=100)
    assert events
    event = events[-1]
    assert event["workspace_id"] == workspace_id
    assert event["domain_id"] == DOMAIN
    assert set(event["participating_agents"]) == set(agents)
    return event


class TestE1PositiveControl:
    def test_real_hive_path_emits_persists_and_converges(self, fabric: TormentFabric) -> None:
        _prepare_workspace(fabric, WORKSPACE)

        result_a = _ingest_until_stored(
            fabric, workspace_id=WORKSPACE, agent_id="agent_a", label="agent a",
        )
        result_b = _ingest_until_stored(
            fabric, workspace_id=WORKSPACE, agent_id="agent_b", label="agent b",
        )

        field = fabric._get_collective_field(WORKSPACE)
        packets = field.all_packets(limit=100)
        events = field.recent_events(limit=100)

        packets_a = [packet for packet in packets if packet["agent_id"] == "agent_a"]
        packets_b = [packet for packet in packets if packet["agent_id"] == "agent_b"]
        assert packets_a and packets_b
        assert all(packet["workspace_id"] == WORKSPACE for packet in packets)
        assert all(packet["domain_id"] == DOMAIN for packet in packets)
        assert any(packet["source_eid"] == result_a["eid"] for packet in packets_a)
        assert any(packet["source_eid"] == result_b["eid"] for packet in packets_b)

        assert events
        event = events[-1]
        assert event["workspace_id"] == WORKSPACE
        assert event["domain_id"] == DOMAIN
        assert set(event["participating_agents"]) == {"agent_a", "agent_b"}
        assert len(event["source_packets"]) == 2
        assert set(event["source_eids"]) == {result_a["eid"], result_b["eid"]}

        collective_root = Path(fabric.data_dir) / "workspaces" / WORKSPACE / "collective"
        persisted_packets = _jsonl_rows(collective_root / "packets.jsonl")
        persisted_events = _jsonl_rows(collective_root / "events.jsonl")
        assert {packet["packet_id"] for packet in packets}.issubset(
            {packet["packet_id"] for packet in persisted_packets}
        )
        assert event["event_id"] in {row["event_id"] for row in persisted_events}

        _prepare_workspace(fabric, CONTROL_WORKSPACE)
        control = fabric._get_collective_field(CONTROL_WORKSPACE)
        assert control.all_packets() == []
        assert control.recent_events() == []


class TestE3GovernanceEmission:
    def test_valid_block_and_malformed_non_dict_characterization(
        self, telemetry_fabric: TormentFabric, caplog: pytest.LogCaptureFixture,
    ) -> None:
        fabric = telemetry_fabric
        caplog.set_level(logging.INFO, logger="torment.hivemind")
        _prepare_workspace(fabric, WORKSPACE)
        field = fabric._get_collective_field(WORKSPACE)

        blocked = _ingest_until_stored(
            fabric,
            workspace_id=WORKSPACE,
            agent_id="blocked_agent",
            label="blocked",
            extra_payload={"governance": {"non_shareable": True}},
        )
        blocked_graph = fabric.private_graphs[fabric._agent_key(WORKSPACE, "blocked_agent")]
        blocked_payload = blocked_graph.entities[blocked["eid"]].payload
        assert blocked_payload["governance"]["non_shareable"] is True
        assert field.all_packets() == []

        caplog.clear()
        malformed = _ingest_until_stored(
            fabric,
            workspace_id=WORKSPACE,
            agent_id="malformed_agent",
            label="malformed",
            extra_payload={"governance": [1]},
        )
        malformed_graph = fabric.private_graphs[fabric._agent_key(WORKSPACE, "malformed_agent")]
        malformed_payload = malformed_graph.entities[malformed["eid"]].payload
        emitted = [
            packet for packet in field.all_packets(limit=100)
            if packet["source_eid"] == malformed["eid"] and packet["agent_id"] == "malformed_agent"
        ]

        # Characterization witness: malformed non-dict governance is accepted,
        # normalized by resolve_governance() to permissive defaults, and does
        # not throw inside the normal packet-emission path.
        assert malformed_payload["governance"] == [1]
        telemetry = [
            record.hivemind_telemetry
            for record in caplog.records
            if record.name == "torment.hivemind"
            and hasattr(record, "hivemind_telemetry")
        ]
        assert len(telemetry) == 1
        decision = telemetry[0]
        assert decision["workspace_id"] == WORKSPACE
        assert decision["agent_id"] == "malformed_agent"
        assert decision["source_eid"] == malformed["eid"]
        assert decision["packet_emitted"] is True
        assert decision["gate_outcome"] == "emitted"
        assert decision["skip_reason"] is None
        assert not [record for record in caplog.records if record.levelno >= logging.ERROR]
        assert len(emitted) == 1
        assert malformed_graph.entities[malformed["eid"]] is not None


class TestE6BridgeQuorum:
    def test_collective_candidate_remains_group_evidence_but_cannot_represent(
        self, fabric: TormentFabric,
    ) -> None:
        """Collective provenance remains grouped without owning canon content."""
        _prepare_workspace(fabric, REPRESENTATIVE_WORKSPACE)
        authority_embedding = _proposal_embedding(0.0)
        supporting_embedding = _proposal_embedding(0.1)
        collective_embedding = _proposal_embedding(0.2)

        authority = fabric.propose_share(
            workspace_id=REPRESENTATIVE_WORKSPACE,
            agent_id="authority_agent_a",
            summary="Independent proposition selected by agent A",
            embedding=authority_embedding,
            domain_id=DOMAIN,
            mtype="fact",
            strength=0.8,
            confidence=0.7,
        )["proposal"]
        support = fabric.propose_share(
            workspace_id=REPRESENTATIVE_WORKSPACE,
            agent_id="authority_agent_b",
            summary="Independent proposition selected by agent B",
            embedding=supporting_embedding,
            domain_id=DOMAIN,
            mtype="fact",
            strength=0.7,
            confidence=0.7,
        )["proposal"]
        collective = fabric.propose_share(
            workspace_id=REPRESENTATIVE_WORKSPACE,
            agent_id="collective_evidence",
            summary="[collective proposal] convergence metadata only",
            embedding=collective_embedding,
            domain_id=DOMAIN,
            mtype="collective_echo",
            strength=0.99,
            confidence=0.99,
        )["proposal"]

        processed = fabric.process_proposals(
            workspace_id=REPRESENTATIVE_WORKSPACE,
            domain_id=DOMAIN,
        )

        assert processed["approved"] == 3
        shared = fabric.get_workspace(REPRESENTATIVE_WORKSPACE).shared_graphs[DOMAIN].entities[
            processed["created_shared_eids"][0]
        ]
        stored_embedding = fabric.get_workspace(REPRESENTATIVE_WORKSPACE).shared_graphs[
            DOMAIN
        ]._shard_reader.load_one(shared.payload["embedding_ref"])
        assert shared.payload["summary"] == "Independent proposition selected by agent A"
        assert shared.payload["type"] == "fact"
        assert stored_embedding is not None
        assert np.allclose(stored_embedding, authority_embedding)
        assert shared.payload["support_agents"] == ["authority_agent_a", "authority_agent_b"]
        assert set(shared.payload["source_proposal_ids"]) == {
            authority["proposal_id"],
            support["proposal_id"],
            collective["proposal_id"],
        }

    def test_collective_only_proposals_cannot_establish_quorum_or_create_canon(
        self, fabric: TormentFabric,
    ) -> None:
        workspace_id = f"{REPRESENTATIVE_WORKSPACE}_collective_only"
        _prepare_workspace(fabric, workspace_id)
        first = fabric.propose_share(
            workspace_id=workspace_id,
            agent_id="collective_evidence_a",
            summary="[collective proposal] first metadata artifact",
            embedding=_proposal_embedding(0.0),
            domain_id=DOMAIN,
            mtype="collective_echo",
            strength=0.99,
            confidence=0.99,
        )["proposal"]
        second = fabric.propose_share(
            workspace_id=workspace_id,
            agent_id="collective_evidence_b",
            summary="[collective proposal] second metadata artifact",
            embedding=_proposal_embedding(0.1),
            domain_id=DOMAIN,
            mtype="collective_echo",
            strength=0.98,
            confidence=0.98,
        )["proposal"]

        processed = fabric.process_proposals(workspace_id=workspace_id, domain_id=DOMAIN)

        registry = fabric.get_workspace(workspace_id).proposals[DOMAIN]
        assert processed["approved"] == 0
        assert processed["created_shared_eids"] == []
        assert {proposal.proposal_id for proposal in registry.list_pending(limit=100)} == {
            first["proposal_id"],
            second["proposal_id"],
        }

    def test_collective_proposal_does_not_supply_independent_quorum(
        self, fabric: TormentFabric,
    ) -> None:
        _prepare_workspace(fabric, WORKSPACE)

        # Three real agent ingests create at least two distinct-pair convergence
        # events without changing the production cooldown or bridge thresholds.
        for agent_id in ("agent_a", "agent_b", "agent_c"):
            _ingest_until_stored(
                fabric,
                workspace_id=WORKSPACE,
                agent_id=agent_id,
                label=agent_id,
            )

        field = fabric._get_collective_field(WORKSPACE)
        events = field.recent_events(limit=100)
        assert len(events) >= 2
        assert all(event["policy_flags"]["proposal_eligible"] is False for event in events)

        workspace = fabric.get_workspace(WORKSPACE)
        registry = workspace.proposals[DOMAIN]
        collective_proposals = [
            proposal for proposal in registry.list_pending(limit=100)
            if "[collective proposal]" in proposal.summary
        ]
        assert len(collective_proposals) == 1
        collective = collective_proposals[0]
        source_event_id = collective.summary.split("[collective_source:", 1)[1].split("]", 1)[0]
        source_event = next(event for event in events if event["event_id"] == source_event_id)
        assert collective.status == "pending"
        assert collective.note is None
        assert collective.agent_id == source_event["participating_agents"][0]
        assert collective.mtype == "collective_echo"

        # Counterfactual: a single ordinary proposal cannot meet the default
        # two-distinct-agent quorum by itself.
        _prepare_workspace(fabric, CONTROL_WORKSPACE)
        _ingest_until_stored(
            fabric,
            workspace_id=CONTROL_WORKSPACE,
            agent_id="agent_b",
            label="control_agent_b",
        )
        fabric.propose_share(
            workspace_id=CONTROL_WORKSPACE,
            agent_id="agent_b",
            summary="Shared oscillator study result",
            embedding=_embedding(),
            domain_id=DOMAIN,
        )
        control_result = fabric.process_proposals(
            workspace_id=CONTROL_WORKSPACE,
            domain_id=DOMAIN,
        )
        assert control_result["approved"] == 0
        assert control_result["created_shared_eids"] == []

        direct = fabric.propose_share(
            workspace_id=WORKSPACE,
            agent_id="agent_b",
            summary="Shared oscillator study result",
            embedding=_embedding(),
            domain_id=DOMAIN,
        )["proposal"]
        processed = fabric.process_proposals(workspace_id=WORKSPACE, domain_id=DOMAIN)

        # The collective proposal remains a real, persisted, reviewable group
        # member, but does not provide an independent agent vote.
        assert processed["approved"] == 0
        assert processed["created_shared_eids"] == []
        pending_by_id = {
            proposal.proposal_id: proposal
            for proposal in registry.list_pending(limit=100)
        }
        assert set(pending_by_id) == {collective.proposal_id, direct["proposal_id"]}
        assert all(proposal.status == "pending" for proposal in pending_by_id.values())

        # A collective artifact also does not prevent a later, genuine
        # two-agent quorum from working through the unchanged grouping path.
        direct_c = fabric.propose_share(
            workspace_id=WORKSPACE,
            agent_id="agent_c",
            summary="Shared oscillator study result",
            embedding=_embedding(),
            domain_id=DOMAIN,
        )["proposal"]
        mixed = fabric.process_proposals(workspace_id=WORKSPACE, domain_id=DOMAIN)

        assert mixed["approved"] == 3
        assert len(mixed["created_shared_eids"]) == 1
        shared_eid = mixed["created_shared_eids"][0]
        shared_entity = workspace.shared_graphs[DOMAIN].entities[shared_eid]
        assert shared_entity.payload["canon"] is True
        assert shared_entity.payload["source"] == "proposal_group"
        assert shared_entity.payload["agent_id"] == "collective"
        assert shared_entity.payload["support_agents"] == ["agent_b", "agent_c"]
        assert set(shared_entity.payload["source_proposal_ids"]) == {
            collective.proposal_id,
            direct["proposal_id"],
            direct_c["proposal_id"],
        }
        assert shared_entity.payload["summary"] == "Shared oscillator study result"
        assert source_event_id not in shared_entity.payload["summary"]
        assert shared_entity.payload["type"] == "fact"

    def test_two_direct_agents_still_reach_default_quorum(
        self, fabric: TormentFabric,
    ) -> None:
        _prepare_workspace(fabric, DIRECT_WORKSPACE)

        # These are ordinary public Fabric proposals; the method creates each
        # agent graph through its existing production path.
        direct_a = fabric.propose_share(
            workspace_id=DIRECT_WORKSPACE,
            agent_id="direct_agent_a",
            summary="Independent shared oscillator result",
            embedding=_embedding(),
            domain_id=DOMAIN,
        )["proposal"]
        direct_b = fabric.propose_share(
            workspace_id=DIRECT_WORKSPACE,
            agent_id="direct_agent_b",
            summary="Independent shared oscillator result",
            embedding=_embedding(),
            domain_id=DOMAIN,
        )["proposal"]

        workspace = fabric.get_workspace(DIRECT_WORKSPACE)
        registry = workspace.proposals[DOMAIN]
        pending = registry.list_pending(limit=100)
        assert {proposal.proposal_id for proposal in pending} == {
            direct_a["proposal_id"],
            direct_b["proposal_id"],
        }
        assert all(proposal.mtype != "collective_echo" for proposal in pending)

        processed = fabric.process_proposals(
            workspace_id=DIRECT_WORKSPACE,
            domain_id=DOMAIN,
        )

        assert processed["approved"] == 2
        assert len(processed["created_shared_eids"]) == 1
        shared_entity = workspace.shared_graphs[DOMAIN].entities[
            processed["created_shared_eids"][0]
        ]
        assert shared_entity.payload["canon"] is True
        assert shared_entity.payload["support_agents"] == [
            "direct_agent_a",
            "direct_agent_b",
        ]
        assert set(shared_entity.payload["source_proposal_ids"]) == {
            direct_a["proposal_id"],
            direct_b["proposal_id"],
        }


class TestE4PolicySemantics:
    def test_opt_out_is_fresh_policy_only_and_reingest_uses_event_domain(
        self, fabric: TormentFabric,
    ) -> None:
        event = _real_convergence_event(fabric, workspace_id=E4_WORKSPACE)

        # This is a lower-level characterization control, not a public
        # production opt-out path.
        opted_out = CollectivePolicy(fabric.data_dir, E4_WORKSPACE)
        opted_out.set_agent_opt_out("agent_x", True)
        blocked = opted_out.evaluate(event, "agent_x", DOMAIN)
        assert blocked.eligible is False
        assert blocked.gate_failed == "agent_opt_in"

        fresh_policy = CollectivePolicy(fabric.data_dir, E4_WORKSPACE)
        assert fresh_policy.is_agent_opted_in("agent_x") is True
        fresh_result = fresh_policy.evaluate(event, "agent_x", DOMAIN)
        assert fresh_result.eligible is True

        # agent_x has no prior workspace/domain activity.  The public Fabric
        # method has no target-domain argument and derives it from the event.
        target_result = fabric.reingest_convergence(
            workspace_id=E4_WORKSPACE,
            target_agent_id="agent_x",
            event_id=event["event_id"],
        )
        assert target_result["eligible"] is True
        target_graph = fabric.private_graphs[
            fabric._agent_key(E4_WORKSPACE, "agent_x")
        ]
        target_echo = target_graph.entities[target_result["echo_eid"]]
        assert target_echo.payload["domain_id"] == event["domain_id"]

        # The public path also permits a participating agent to receive an
        # echo from the event it participated in.
        self_target = event["participating_agents"][0]
        self_result = fabric.reingest_convergence(
            workspace_id=E4_WORKSPACE,
            target_agent_id=self_target,
            event_id=event["event_id"],
        )
        assert self_result["eligible"] is True
        assert self_result["echo_eid"] is not None
        assert self_target in event["participating_agents"]


class TestE5EchoTerminalityRestart:
    def test_real_echo_is_terminal_and_restart_dedup_persists(
        self, fabric: TormentFabric,
    ) -> None:
        event = _real_convergence_event(fabric, workspace_id=E5_WORKSPACE)
        field = fabric._get_collective_field(E5_WORKSPACE)
        packets_before = field.all_packets(limit=100)
        events_before = field.recent_events(limit=100)

        target_agent = "echo_target"
        first = fabric.reingest_convergence(
            workspace_id=E5_WORKSPACE,
            target_agent_id=target_agent,
            event_id=event["event_id"],
        )
        assert first["eligible"] is True
        echo_eid = first["echo_eid"]
        assert echo_eid is not None

        target_graph = fabric.private_graphs[
            fabric._agent_key(E5_WORKSPACE, target_agent)
        ]
        echo = target_graph.entities[echo_eid]
        payload = echo.payload
        assert payload["provenance"]["source_type"] == "collective_echo"
        assert payload["source_event_id"] == event["event_id"]
        assert payload["governance"]["collective_export_blocked"] is True
        assert payload["governance"]["collective_reingest_blocked"] is True
        assert len(field.all_packets(limit=100)) == len(packets_before)
        assert len(field.recent_events(limit=100)) == len(events_before)
        assert not [
            packet for packet in field.all_packets(limit=100)
            if packet["source_eid"] == echo_eid and packet["agent_id"] == target_agent
        ]

        data_root = Path(fabric.data_dir)
        log_path = data_root / "workspaces" / E5_WORKSPACE / "collective" / "reingest_log.jsonl"
        assert _jsonl_rows(log_path) == [{
            "agent_id": target_agent,
            "event_id": event["event_id"],
            "ts": _jsonl_rows(log_path)[0]["ts"],
        }]
        assert len(target_graph.entities) == 1

        # A fresh Fabric reloads the persisted reingest tracker before the
        # duplicate attempt; the original fixture's close is idempotent.
        fabric.close()
        restarted = TormentFabric(data_dir=str(data_root))
        try:
            duplicate = restarted.reingest_convergence(
                workspace_id=E5_WORKSPACE,
                target_agent_id=target_agent,
                event_id=event["event_id"],
            )
            assert duplicate["eligible"] is False
            assert duplicate["gate_failed"] == "dedup"
            restarted_graph = restarted.private_graphs[
                restarted._agent_key(E5_WORKSPACE, target_agent)
            ]
            echoes = [
                entity for entity in restarted_graph.entities.values()
                if entity.payload.get("source_event_id") == event["event_id"]
            ]
            assert len(echoes) == 1
            assert echoes[0].eid == echo_eid
            assert len(_jsonl_rows(log_path)) == 1
        finally:
            restarted.close()


class TestE7WorkspaceIsolation:
    def test_packets_events_echoes_and_shared_state_do_not_cross_workspaces(
        self, fabric: TormentFabric,
    ) -> None:
        _prepare_workspace(fabric, E7_WORKSPACE_A)
        _prepare_workspace(fabric, E7_WORKSPACE_B)
        field_a = fabric._get_collective_field(E7_WORKSPACE_A)
        field_b = fabric._get_collective_field(E7_WORKSPACE_B)
        shared_a_before = len(fabric.get_workspace(E7_WORKSPACE_A).shared_graphs[DOMAIN].entities)
        shared_b_before = len(fabric.get_workspace(E7_WORKSPACE_B).shared_graphs[DOMAIN].entities)

        _ingest_until_stored(
            fabric, workspace_id=E7_WORKSPACE_A, agent_id="agent_a", label="a_first",
        )
        assert field_a.all_packets(limit=100)
        assert field_b.all_packets(limit=100) == []

        packets_a_before_b = field_a.all_packets(limit=100)
        _ingest_until_stored(
            fabric, workspace_id=E7_WORKSPACE_B, agent_id="agent_a", label="b_first",
        )
        assert field_a.all_packets(limit=100) == packets_a_before_b
        assert field_b.all_packets(limit=100)

        _ingest_until_stored(
            fabric, workspace_id=E7_WORKSPACE_A, agent_id="agent_b", label="a_second",
        )
        _ingest_until_stored(
            fabric, workspace_id=E7_WORKSPACE_B, agent_id="agent_b", label="b_second",
        )

        packets_a = field_a.all_packets(limit=100)
        packets_b = field_b.all_packets(limit=100)
        events_a = field_a.recent_events(limit=100)
        events_b = field_b.recent_events(limit=100)
        assert events_a and events_b
        assert all(packet["workspace_id"] == E7_WORKSPACE_A for packet in packets_a)
        assert all(packet["workspace_id"] == E7_WORKSPACE_B for packet in packets_b)
        packet_ids_a = {packet["packet_id"] for packet in packets_a}
        packet_ids_b = {packet["packet_id"] for packet in packets_b}
        assert packet_ids_a.isdisjoint(packet_ids_b)
        assert all(event["workspace_id"] == E7_WORKSPACE_A for event in events_a)
        assert all(event["workspace_id"] == E7_WORKSPACE_B for event in events_b)
        assert all(set(event["source_packets"]).issubset(packet_ids_a) for event in events_a)
        assert all(set(event["source_packets"]).issubset(packet_ids_b) for event in events_b)
        collective_a = Path(fabric.data_dir) / "workspaces" / E7_WORKSPACE_A / "collective"
        collective_b = Path(fabric.data_dir) / "workspaces" / E7_WORKSPACE_B / "collective"
        persisted_packets_a = _jsonl_rows(collective_a / "packets.jsonl")
        persisted_packets_b = _jsonl_rows(collective_b / "packets.jsonl")
        persisted_events_a = _jsonl_rows(collective_a / "events.jsonl")
        persisted_events_b = _jsonl_rows(collective_b / "events.jsonl")
        assert all(packet["workspace_id"] == E7_WORKSPACE_A for packet in persisted_packets_a)
        assert all(packet["workspace_id"] == E7_WORKSPACE_B for packet in persisted_packets_b)
        assert all(event["workspace_id"] == E7_WORKSPACE_A for event in persisted_events_a)
        assert all(event["workspace_id"] == E7_WORKSPACE_B for event in persisted_events_b)
        assert packet_ids_a.issubset({packet["packet_id"] for packet in persisted_packets_a})
        assert packet_ids_b.issubset({packet["packet_id"] for packet in persisted_packets_b})

        private_b_before = {
            agent_id: len(fabric.private_graphs[
                fabric._agent_key(E7_WORKSPACE_B, agent_id)
            ].entities)
            for agent_id in ("agent_a", "agent_b")
        }
        shared_b_before_echo = len(fabric.get_workspace(E7_WORKSPACE_B).shared_graphs[DOMAIN].entities)
        echo = fabric.reingest_convergence(
            workspace_id=E7_WORKSPACE_A,
            target_agent_id="echo_target",
            event_id=events_a[-1]["event_id"],
        )
        assert echo["eligible"] is True
        assert echo["echo_eid"] is not None
        assert {
            agent_id: len(fabric.private_graphs[
                fabric._agent_key(E7_WORKSPACE_B, agent_id)
            ].entities)
            for agent_id in ("agent_a", "agent_b")
        } == private_b_before
        assert fabric._agent_key(E7_WORKSPACE_B, "echo_target") not in fabric.private_graphs
        assert len(fabric.get_workspace(E7_WORKSPACE_A).shared_graphs[DOMAIN].entities) == shared_a_before
        assert len(fabric.get_workspace(E7_WORKSPACE_B).shared_graphs[DOMAIN].entities) == shared_b_before
        assert len(fabric.get_workspace(E7_WORKSPACE_B).shared_graphs[DOMAIN].entities) == shared_b_before_echo
