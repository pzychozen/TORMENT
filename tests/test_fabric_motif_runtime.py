"""Focused Phase 7G5A3A legacy Fabric motif runtime-boundary tests."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from torment_service.fabric import TormentFabric
from torment_service.motif_runtime import LegacyMotifRuntimeAdapter
from torment_service.motifs import Motif, MotifRegistry


def _motif(
    motif_id: str,
    *,
    centroid: list[float] | None = None,
    members: list[int] | None = None,
) -> Motif:
    return Motif(
        motif_id=motif_id,
        domain_id="personal",
        label=f"label {motif_id}",
        centroid=centroid or [1.0, 0.0],
        strength=0.4,
        members=members or [1],
        contributing_agents=["agent"],
        stability_score=0.6,
        created_ts=10,
        last_active_ts=20,
    )


def _registry(tmp_path: Path) -> MotifRegistry:
    return MotifRegistry(str(tmp_path), "workspace", "personal")


def test_legacy_runtime_delegates_create_attach_threshold_tie_duplicate_and_split(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry = _registry(tmp_path / "primary")
    runtime = LegacyMotifRuntimeAdapter(registry)

    created = runtime.attach_or_create(
        np.asarray([1.0, 0.0], dtype=np.float32),
        memory_eid=1,
        agent_id="agent",
        summary="first motif",
        attach_threshold=0.72,
    )
    assert created.affected_runtime_ids == ("motif_personal_0001",)
    assert created.created_runtime_id == "motif_personal_0001"

    attached = runtime.attach_or_create(
        np.asarray([1.0, 0.0], dtype=np.float32),
        memory_eid=1,
        agent_id="agent",
        summary="duplicate member remains legacy append behavior",
        attach_threshold=0.72,
    )
    assert attached.affected_runtime_ids == ("motif_personal_0001",)
    assert attached.created_runtime_id is None
    assert registry.motifs["motif_personal_0001"].members == [1, 1]

    threshold = runtime.attach_or_create(
        np.asarray([0.5, np.sqrt(0.75)], dtype=np.float32),
        memory_eid=2,
        agent_id="agent",
        summary="below attach threshold",
        attach_threshold=0.72,
    )
    assert threshold.created_runtime_id == "motif_personal_0002"

    tied_registry = _registry(tmp_path / "tie")
    tied_registry.motifs["first"] = _motif("first")
    tied_registry.motifs["second"] = _motif("second")
    tied = LegacyMotifRuntimeAdapter(tied_registry).attach_or_create(
        np.asarray([1.0, 0.0], dtype=np.float32),
        memory_eid=3,
        agent_id="agent",
        summary="strict first registry order wins ties",
        attach_threshold=0.72,
    )
    assert tied.affected_runtime_ids == ("first",)
    assert tied_registry.motifs["first"].members == [1, 3]
    assert tied_registry.motifs["second"].members == [1]

    monkeypatch.setattr(
        registry,
        "_maybe_split_motif",
        lambda motif_id: {"parent": motif_id, "child": "split-child"},
    )
    split = runtime.attach_or_create(
        np.asarray([1.0, 0.0], dtype=np.float32),
        memory_eid=4,
        agent_id="agent",
        summary="split result is relayed unchanged",
        attach_threshold=0.72,
    )
    assert split.affected_runtime_ids == ("motif_personal_0001", "split-child")
    assert split.created_runtime_id is None


def test_legacy_runtime_field_projection_is_exact_and_keeps_registry_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry = _registry(tmp_path)
    registry.motifs["second"] = _motif("second", members=[9, 8])
    registry.motifs["first"] = _motif("first", centroid=[0.0, 1.0], members=[7])
    radius_calls: list[str] = []

    def radius(motif: Motif) -> float:
        radius_calls.append(motif.motif_id)
        return {"second": 0.25, "first": 0.5}[motif.motif_id]

    monkeypatch.setattr(registry, "_motif_radius", radius)
    rows = LegacyMotifRuntimeAdapter(registry).project_coherence_field_rows()

    assert radius_calls == ["second", "first"]
    assert rows == [
        {
            "motif_id": "second",
            "label": "label second",
            "centroid": [1.0, 0.0],
            "strength": 0.4,
            "stability_score": 0.6,
            "members": [9, 8],
            "radius": 0.25,
        },
        {
            "motif_id": "first",
            "label": "label first",
            "centroid": [0.0, 1.0],
            "strength": 0.4,
            "stability_score": 0.6,
            "members": [7],
            "radius": 0.5,
        },
    ]


def test_ordinary_ingest_keeps_motif_then_field_then_flush_then_maintenance_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TORMENT_EMBED_PROVIDER", "hash")
    monkeypatch.setenv("TORMENT_CHARACTER_ENABLE", "0")
    monkeypatch.setenv("TORMENT_CHECKPOINT_ENABLE", "0")
    monkeypatch.setenv("TORMENT_COMPRESS_ENABLE", "0")
    monkeypatch.setenv("TORMENT_SRG_ENABLE", "0")
    monkeypatch.setenv("TORMENT_HIVEMIND_ENABLE", "0")
    monkeypatch.setenv("TORMENT_REINFORCE_SIM_THRESHOLD", "0")

    fabric = TormentFabric(str(tmp_path))
    workspace_id, agent_id = "runtime-workspace", "runtime-agent"
    try:
        identity = fabric.create_agent(workspace_id, agent_id)
        identity.overlay["write_threshold"] = 0.0
        fabric.ident_store.save(identity)
        workspace = fabric.get_workspace(workspace_id)
        registry = workspace.motif_regs["personal"]
        graph = fabric.private_graphs[fabric._agent_key(workspace_id, agent_id)]
        calls: list[str] = []

        original_attach = registry.attach_or_create
        original_radius = registry._motif_radius
        original_entropy = registry.update_entropy_and_suggest
        original_flush = graph.flush_node

        def tracked_attach(*args, **kwargs):
            calls.append("attach")
            return original_attach(*args, **kwargs)

        def tracked_radius(motif: Motif) -> float:
            calls.append("radius")
            return original_radius(motif)

        def tracked_flush(eid: int) -> None:
            calls.append("flush")
            return original_flush(eid)

        def tracked_entropy(*args, **kwargs):
            calls.append("maintenance")
            return original_entropy(*args, **kwargs)

        monkeypatch.setattr(registry, "attach_or_create", tracked_attach)
        monkeypatch.setattr(registry, "_motif_radius", tracked_radius)
        monkeypatch.setattr(registry, "update_entropy_and_suggest", tracked_entropy)
        monkeypatch.setattr(graph, "flush_node", tracked_flush)

        result = fabric.ingest(
            workspace_id,
            agent_id,
            "ordinary Fabric motif runtime boundary",
            step=1,
            domain_id="personal",
            supplied_embedding=[1.0] * workspace.embed_dim,
        )

        assert result["stored"] is True
        assert isinstance(result["eid"], int)
        assert result["motifs"] == ["motif_personal_0001"]
        assert result["created_motif"] == "motif_personal_0001"
        assert calls.index("attach") < calls.index("radius") < calls.index("flush") < calls.index("maintenance")

        entity = graph.entities[result["eid"]]
        assert "state_symbol" in entity.payload
        assert "resonance_score" in entity.payload
        persisted = [json.loads(line) for line in Path(graph.meta_path).read_text(encoding="utf-8").splitlines()]
        assert persisted[-1]["eid"] == result["eid"]
    finally:
        fabric.close()
