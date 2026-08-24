"""Focused contract tests for optional Hivemind packet-decision telemetry."""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pytest

from torment_service.fabric import TormentFabric


WORKSPACE = "hivemind_telemetry_ws"
DOMAIN = "research"


def _configure_hivemind(
    monkeypatch: pytest.MonkeyPatch,
    *,
    hivemind_enabled: bool,
    telemetry_enabled: bool,
) -> None:
    monkeypatch.setenv("TORMENT_HIVEMIND_ENABLE", "1" if hivemind_enabled else "0")
    monkeypatch.setenv("TORMENT_HIVEMIND_TELEMETRY", "1" if telemetry_enabled else "0")
    monkeypatch.setenv("TORMENT_EMBED_PROVIDER", "hash")
    monkeypatch.setenv("TORMENT_COMPRESS_ENABLE", "0")
    monkeypatch.setenv("TORMENT_SRG_ENABLE", "0")
    monkeypatch.setenv("TORMENT_SQLITE_INDEX_ENABLE", "0")


def _embedding() -> list[float]:
    return np.linspace(0.1, 1.0, 384, dtype=np.float32).tolist()


def _ingest_until_stored(
    fabric: TormentFabric,
    *,
    agent_id: str,
    label: str,
    extra_payload: dict | None = None,
) -> dict:
    for step in range(1, 25):
        result = fabric.ingest(
            workspace_id=WORKSPACE,
            agent_id=agent_id,
            text=f"{label} research observation {step}: repeatable collective signal.",
            step=step,
            domain_id=DOMAIN,
            supplied_embedding=_embedding(),
            extra_payload=extra_payload,
        )
        if result["stored"]:
            return result
    raise AssertionError(f"normal ingest did not store a memory for {agent_id!r}")


def _decision_records(caplog: pytest.LogCaptureFixture) -> list[dict]:
    return [
        record.hivemind_telemetry
        for record in caplog.records
        if record.name == "torment.hivemind"
        and hasattr(record, "hivemind_telemetry")
    ]


def _collective_snapshot(fabric: TormentFabric) -> tuple[list[tuple], list[tuple]]:
    field = fabric._get_collective_field(WORKSPACE)
    packets = sorted(
        (
            packet["workspace_id"],
            packet["agent_id"],
            packet["domain_id"],
            packet["source_eid"],
            packet["summary"],
        )
        for packet in field.all_packets(limit=100)
    )
    events = sorted(
        (
            event["workspace_id"],
            event["domain_id"],
            tuple(event["participating_agents"]),
            tuple(event["source_eids"]),
            event["semantic_overlap"],
        )
        for event in field.recent_events(limit=100)
    )
    return packets, events


@pytest.fixture
def telemetry_fabric(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    _configure_hivemind(monkeypatch, hivemind_enabled=True, telemetry_enabled=True)
    with TormentFabric(data_dir=str(tmp_path)) as fabric:
        fabric.get_workspace(WORKSPACE, domains=[DOMAIN])
        yield fabric


def test_eligible_packet_emits_structured_decision_record(
    telemetry_fabric: TormentFabric,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="torment.hivemind")
    result = _ingest_until_stored(
        telemetry_fabric,
        agent_id="eligible_agent",
        label="eligible",
    )

    decisions = [
        record
        for record in _decision_records(caplog)
        if record["agent_id"] == "eligible_agent"
        and record["source_eid"] == result["eid"]
    ]

    assert len(decisions) == 1
    decision = decisions[0]
    assert decision["event_kind"] == "hivemind_packet_decision"
    assert decision["workspace_id"] == WORKSPACE
    assert decision["domain_id"] == DOMAIN
    assert decision["packet_emitted"] is True
    assert decision["gate_outcome"] == "emitted"
    assert decision["skip_reason"] is None
    assert decision["coherence"] >= 0.15
    assert decision["convergence_occurred"] is False
    assert decision["convergence_event_id"] is None
    assert decision["convergence_partner_agent_id"] is None
    assert decision["semantic_similarity"] is None
    assert decision["sequence"] >= 1
    assert isinstance(decision["timestamp"], float)


def test_ineligible_packet_emits_governance_skip_reason(
    telemetry_fabric: TormentFabric,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="torment.hivemind")
    result = _ingest_until_stored(
        telemetry_fabric,
        agent_id="blocked_agent",
        label="blocked",
        extra_payload={"governance": {"non_shareable": True}},
    )

    decisions = [
        record
        for record in _decision_records(caplog)
        if record["agent_id"] == "blocked_agent"
        and record["source_eid"] == result["eid"]
    ]

    assert len(decisions) == 1
    decision = decisions[0]
    assert decision["packet_emitted"] is False
    assert decision["gate_outcome"] == "skipped"
    assert decision["skip_reason"] == "governance: non_shareable or export_blocked"
    assert decision["coherence"] is not None
    assert decision["convergence_occurred"] is False


def test_hivemind_disabled_is_explicitly_observable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    _configure_hivemind(monkeypatch, hivemind_enabled=False, telemetry_enabled=True)
    caplog.set_level(logging.INFO, logger="torment.hivemind")
    with TormentFabric(data_dir=str(tmp_path)) as fabric:
        fabric.get_workspace(WORKSPACE, domains=[DOMAIN])
        result = _ingest_until_stored(fabric, agent_id="disabled_agent", label="disabled")

    decisions = [
        record
        for record in _decision_records(caplog)
        if record["agent_id"] == "disabled_agent"
        and record["source_eid"] == result["eid"]
    ]
    assert len(decisions) == 1
    assert decisions[0]["packet_emitted"] is False
    assert decisions[0]["gate_outcome"] == "blocked"
    assert decisions[0]["skip_reason"] == "hivemind_disabled"


def test_convergence_record_links_partner_event_and_similarity(
    telemetry_fabric: TormentFabric,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="torment.hivemind")
    _ingest_until_stored(telemetry_fabric, agent_id="agent_a", label="first")
    result_b = _ingest_until_stored(telemetry_fabric, agent_id="agent_b", label="second")
    event = telemetry_fabric._get_collective_field(WORKSPACE).recent_events(limit=10)[-1]

    decisions = [
        record
        for record in _decision_records(caplog)
        if record["agent_id"] == "agent_b" and record["source_eid"] == result_b["eid"]
    ]
    assert len(decisions) == 1
    decision = decisions[0]
    assert decision["packet_emitted"] is True
    assert decision["convergence_occurred"] is True
    assert decision["convergence_event_id"] == event["event_id"]
    assert decision["convergence_partner_agent_id"] == "agent_a"
    assert decision["semantic_similarity"] == event["semantic_overlap"]


def test_telemetry_enablement_preserves_collective_outputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    _configure_hivemind(monkeypatch, hivemind_enabled=True, telemetry_enabled=False)
    caplog.set_level(logging.INFO, logger="torment.hivemind")
    with TormentFabric(data_dir=str(tmp_path / "disabled")) as disabled:
        disabled.get_workspace(WORKSPACE, domains=[DOMAIN])
        disabled_a = _ingest_until_stored(disabled, agent_id="agent_a", label="first")
        disabled_b = _ingest_until_stored(disabled, agent_id="agent_b", label="second")
        disabled_snapshot = _collective_snapshot(disabled)
    assert not _decision_records(caplog)

    _configure_hivemind(monkeypatch, hivemind_enabled=True, telemetry_enabled=True)
    caplog.clear()
    caplog.set_level(logging.INFO, logger="torment.hivemind")
    with TormentFabric(data_dir=str(tmp_path / "enabled")) as enabled:
        enabled.get_workspace(WORKSPACE, domains=[DOMAIN])
        enabled_a = _ingest_until_stored(enabled, agent_id="agent_a", label="first")
        enabled_b = _ingest_until_stored(enabled, agent_id="agent_b", label="second")
        enabled_snapshot = _collective_snapshot(enabled)

    assert [(disabled_a["stored"], disabled_a["eid"]), (disabled_b["stored"], disabled_b["eid"])] == [
        (enabled_a["stored"], enabled_a["eid"]),
        (enabled_b["stored"], enabled_b["eid"]),
    ]
    assert enabled_snapshot == disabled_snapshot
    assert _decision_records(caplog)


def test_temporary_packet_gate_stderr_output_is_removed(
    telemetry_fabric: TormentFabric,
    capsys: pytest.CaptureFixture,
) -> None:
    _ingest_until_stored(telemetry_fabric, agent_id="stderr_agent", label="stderr")

    assert "PACKET-GATE" not in capsys.readouterr().err


def test_packet_emission_errors_still_use_the_established_error_channel(
    telemetry_fabric: TormentFabric,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    def fail_collective_field(_: str):
        raise RuntimeError("telemetry error-channel witness")

    monkeypatch.setattr(telemetry_fabric, "_get_collective_field", fail_collective_field)
    caplog.set_level(logging.INFO, logger="torment.hivemind")
    result = _ingest_until_stored(telemetry_fabric, agent_id="error_agent", label="error")

    errors = [
        record
        for record in caplog.records
        if record.name == "torment.hivemind"
        and record.levelno == logging.ERROR
        and "Hivemind packet emission failed" in record.getMessage()
    ]
    assert result["stored"] is True
    assert len(errors) == 1
    assert errors[0].exc_info is not None
    decisions = _decision_records(caplog)
    assert decisions[-1]["gate_outcome"] == "error"
    assert decisions[-1]["skip_reason"] == "packet_emission_error"
