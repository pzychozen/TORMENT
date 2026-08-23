"""Focused regression coverage for conflict-registry corruption honesty."""
from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest
from fastapi import HTTPException

import torment_service.app as appmod
from torment_service.conflicts import ConflictRegistry, ConflictRegistryError
from torment_service.fabric import TormentFabric


WORKSPACE_ID = "conflict-corruption-workspace"


def _legacy_row(conflict_id: str = "legacy-conflict") -> dict:
    return {
        "conflict_id": conflict_id,
        "workspace_id": WORKSPACE_ID,
        "domain_id": "research",
        "eid_a": 1,
        "eid_b": 2,
        "sim": 0.9,
        "conflict_score": 0.7,
        "reason": "legacy",
        "status": "open",
        "created_ts": 1,
    }


@pytest.fixture
def registry(tmp_path: Path) -> ConflictRegistry:
    return ConflictRegistry(str(tmp_path), WORKSPACE_ID, "research")


def _proposal(fabric: TormentFabric, eid: int, deferred: list[str] | None = None) -> dict:
    proposed = fabric.propose_closure(
        workspace_id=WORKSPACE_ID,
        arc_name="conflict-corruption-honesty",
        arc_kind="feature",
        scope=[eid],
        what_it_was="Exercise conflict-registry honesty.",
        what_worked="The boundary reported durable state honestly.",
        what_surprised="No surprise.",
        what_to_carry_forward="Keep the state readable before finality.",
        deferred_or_open_items=list(deferred or []),
    )
    assert proposed["ok"]
    ratified = fabric.ratify_closure(
        WORKSPACE_ID, proposed["closure_id"], ratifier="operator"
    )
    assert ratified["ok"]
    return proposed


def _fabric_with_memory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[TormentFabric, int]:
    monkeypatch.setenv("TORMENT_EMBED_PROVIDER", "hash")
    fabric = TormentFabric(data_dir=str(tmp_path))
    fabric.get_workspace(WORKSPACE_ID)
    fabric.create_agent(WORKSPACE_ID, "atlas")
    result = fabric.ingest(
        workspace_id=WORKSPACE_ID,
        agent_id="atlas",
        text="The release checklist has one pending verification.",
        step=1,
    )
    return fabric, int(result["eid"])


def _corrupt(registry: ConflictRegistry) -> None:
    Path(registry.path).write_text("{ malformed conflict json\n", encoding="utf-8")


def _event_kinds(fabric: TormentFabric, closure_id: str) -> list[str]:
    return [
        event.kind
        for event in fabric._get_closure_ledger(WORKSPACE_ID).list_events(
            closure_id=closure_id
        )
    ]


def test_malformed_base_row_is_typed_and_includes_location(
    registry: ConflictRegistry,
) -> None:
    Path(registry.path).write_text("{ malformed base json\n", encoding="utf-8")

    with pytest.raises(ConflictRegistryError) as caught:
        registry.list(status="any")

    assert caught.value.reason == "malformed_line"
    assert "conflicts.jsonl" in caught.value.detail
    assert "line 1" in caught.value.detail


def test_malformed_event_row_is_typed_and_includes_location(
    registry: ConflictRegistry,
) -> None:
    registry.add(1, 2, 0.9, 0.7, "first")
    Path(registry.events_path).write_text("{ malformed event json\n", encoding="utf-8")

    with pytest.raises(ConflictRegistryError) as caught:
        registry.list(status="any")

    assert caught.value.reason == "malformed_line"
    assert "conflict_events.jsonl" in caught.value.detail
    assert "line 1" in caught.value.detail


def test_invalid_base_row_is_typed(
    registry: ConflictRegistry,
) -> None:
    Path(registry.path).write_text(json.dumps({"conflict_id": "incomplete"}) + "\n", encoding="utf-8")

    with pytest.raises(ConflictRegistryError) as caught:
        registry.list(status="any")

    assert caught.value.reason == "invalid_record"
    assert "conflicts.jsonl" in caught.value.detail


def test_well_formed_row_before_corruption_is_not_partially_returned(
    registry: ConflictRegistry,
) -> None:
    registry.add(1, 2, 0.9, 0.7, "first")
    with Path(registry.path).open("a", encoding="utf-8") as handle:
        handle.write("{ malformed second row\n")

    with pytest.raises(ConflictRegistryError) as caught:
        registry.list(status="any")

    assert caught.value.reason == "malformed_line"


def test_legacy_well_formed_row_still_loads(registry: ConflictRegistry) -> None:
    Path(registry.path).write_text(json.dumps(_legacy_row()) + "\n", encoding="utf-8")

    loaded = registry.list(status="open")

    assert [conflict.conflict_id for conflict in loaded] == ["legacy-conflict"]
    assert loaded[0].origin_scope is None


def test_commit_blocks_and_writes_no_commit_event_when_registry_is_unreadable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    fabric, eid = _fabric_with_memory(tmp_path, monkeypatch)
    try:
        workspace = fabric.get_workspace(WORKSPACE_ID)
        domain_id = workspace.domains[0]
        proposed = _proposal(fabric, eid)
        _corrupt(workspace.conflicts[domain_id])

        result = fabric.commit_closure(WORKSPACE_ID, proposed["closure_id"], "operator")

        assert result["result_code"] == "conflict_state_unreadable"
        assert result["unreadable"]["unreadable_conflict_domains"][0]["domain_id"] == domain_id
        assert _event_kinds(fabric, proposed["closure_id"]) == ["proposed", "ratified"]
    finally:
        fabric.close()


def test_revise_blocks_and_writes_no_revision_event_when_registry_is_unreadable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    fabric, eid = _fabric_with_memory(tmp_path, monkeypatch)
    try:
        workspace = fabric.get_workspace(WORKSPACE_ID)
        proposed = _proposal(fabric, eid)
        assert fabric.commit_closure(WORKSPACE_ID, proposed["closure_id"], "operator")["ok"]
        _corrupt(workspace.conflicts[workspace.domains[0]])
        before = _event_kinds(fabric, proposed["closure_id"])

        result = fabric.revise_closure(
            WORKSPACE_ID,
            proposed["closure_id"],
            {"what_worked": "A revised statement."},
            "operator",
        )

        assert result["result_code"] == "conflict_state_unreadable"
        assert _event_kinds(fabric, proposed["closure_id"]) == before
        assert "revised" not in before
    finally:
        fabric.close()


def test_unreadable_registry_wins_over_discovered_open_conflicts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    fabric, eid = _fabric_with_memory(tmp_path, monkeypatch)
    try:
        workspace = fabric.get_workspace(WORKSPACE_ID)
        workspace.add_domain("unreadable-domain")
        readable_domain, unreadable_domain = workspace.domains[:2]
        readable = workspace.conflicts[readable_domain].add(
            eid, 999, 0.9, 0.7, "open conflict"
        )
        proposed = _proposal(fabric, eid)
        _corrupt(workspace.conflicts[unreadable_domain])

        result = fabric.commit_closure(WORKSPACE_ID, proposed["closure_id"], "operator")

        assert result["result_code"] == "conflict_state_unreadable"
        assert result["unreadable"]["unresolved_conflicts"][0]["conflict_id"] == readable.conflict_id
        assert result["unreadable"]["unreadable_conflict_domains"][0]["domain_id"] == unreadable_domain
    finally:
        fabric.close()


def test_nonempty_declaration_still_blocks_when_registry_is_unreadable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    fabric, eid = _fabric_with_memory(tmp_path, monkeypatch)
    try:
        workspace = fabric.get_workspace(WORKSPACE_ID)
        proposed = _proposal(fabric, eid, deferred=["release verification"])
        _corrupt(workspace.conflicts[workspace.domains[0]])

        result = fabric.commit_closure(WORKSPACE_ID, proposed["closure_id"], "operator")

        assert result["result_code"] == "conflict_state_unreadable"
    finally:
        fabric.close()


def test_non_corruption_read_failure_is_honest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    fabric, eid = _fabric_with_memory(tmp_path, monkeypatch)
    try:
        workspace = fabric.get_workspace(WORKSPACE_ID)
        registry = workspace.conflicts[workspace.domains[0]]
        proposed = _proposal(fabric, eid)

        def deny_read(*_args: object, **_kwargs: object) -> list[object]:
            raise PermissionError("registry access denied")

        monkeypatch.setattr(registry, "list", deny_read)
        result = fabric.commit_closure(WORKSPACE_ID, proposed["closure_id"], "operator")

        assert result["result_code"] == "conflict_state_unreadable"
        assert result["unreadable"]["unreadable_conflict_domains"][0]["reason"] == "read_failed"
    finally:
        fabric.close()


def test_query_and_trace_warn_but_return_when_registry_is_corrupt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture,
) -> None:
    fabric, eid = _fabric_with_memory(tmp_path, monkeypatch)
    try:
        workspace = fabric.get_workspace(WORKSPACE_ID)
        domain_id = workspace.domains[0]
        _corrupt(workspace.conflicts[domain_id])

        with caplog.at_level(logging.WARNING, logger="torment.fabric"):
            query = fabric.query(
                WORKSPACE_ID, "atlas", "release checklist", domain_id=domain_id, top_k=20
            )
            trace = fabric.trace(
                WORKSPACE_ID, "atlas", "release checklist", [eid], domain_id=domain_id
            )

        assert query["results"]
        assert trace["items"]
        assert any("Conflict registry unreadable for query/trace" in record.message for record in caplog.records)
    finally:
        fabric.close()


def test_rest_reports_unreadable_registry_before_value_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    fabric, _ = _fabric_with_memory(tmp_path, monkeypatch)
    try:
        workspace = fabric.get_workspace(WORKSPACE_ID)
        domain_id = workspace.domains[0]
        _corrupt(workspace.conflicts[domain_id])
        monkeypatch.setattr(appmod, "fabric", fabric)

        with pytest.raises(HTTPException) as caught:
            appmod.list_conflicts(WORKSPACE_ID, domain_id)

        assert caught.value.status_code == 500
        assert "unreadable" in str(caught.value.detail).lower()
        assert "not found" not in str(caught.value.detail).lower()
    finally:
        fabric.close()


def test_rest_unknown_domain_remains_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    class UnknownDomainFabric:
        def list_conflicts(self, *_args: object, **_kwargs: object) -> dict:
            raise ValueError("unknown domain")

    monkeypatch.setattr(appmod, "fabric", UnknownDomainFabric())

    with pytest.raises(HTTPException) as caught:
        appmod.list_conflicts(WORKSPACE_ID, "unknown")

    assert caught.value.status_code == 404
