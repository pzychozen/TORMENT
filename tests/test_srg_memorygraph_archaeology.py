"""A3D4 archaeology locks legacy SRG order and collision durability facts."""
from __future__ import annotations

from copy import deepcopy
import logging
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from torment_service.memory_graph import MemoryGraph
from torment_service.memory_runtime_access import LegacyPostWriteMemoryAccess
from torment_service.post_write_runtime import (
    FabricPostWriteContext,
    LegacyFabricPostWriteAdapter,
    PostWriteStorageOutcome,
)
from torment_service.srg_engine import SRGMemoryState
from torment_service.srg_runtime_state import LegacySRGTransientRuntime


class _ThreeDimensionalEmbedder:
    dim = 3

    def embed(self, _text: str) -> np.ndarray:
        return np.zeros(3, dtype=np.float32)


def _add_memory(graph: MemoryGraph, label: str, *, embedding=(1.0, 0.0, 0.0), extra=None) -> int:
    return graph.add_memory(
        summary=label,
        embedding=np.asarray(embedding, dtype=np.float32),
        mtype="episodic",
        strength=0.8,
        confidence=0.9,
        half_life_days=20.0,
        user_id="aria",
        step=1,
        extra_payload=extra or {},
    )


def _node_record(eid: int, marker: str) -> dict:
    return {
        "eid": eid,
        "born_step": 1,
        "channel": 0,
        "payload": {
            "summary": marker,
            "type": "episodic",
            "memory_class": "core",
            "strength": 0.8,
            "confidence": 0.9,
            "pos": [0.0, 0.0, 0.0],
            "vel": [0.0, 0.0, 0.0],
            "vel0": [0.0, 0.0, 0.0],
        },
    }


def test_legacy_entities_order_is_creation_order_and_updates_do_not_move_entries(tmp_path: Path):
    graph = MemoryGraph(str(tmp_path), embedder=_ThreeDimensionalEmbedder())
    try:
        assert list(graph.entities) == []
        eids = [_add_memory(graph, label) for label in ("first", "second", "third")]
        assert list(graph.entities) == eids

        # Fabric reinforcement reaches this durable update primitive.  An
        # appended current record changes facts, not the existing dict slot.
        graph.update_payload(eids[0], {"reinforcement_count": 1})
        assert list(graph.entities) == eids
    finally:
        graph.close()

    reloaded = MemoryGraph(str(tmp_path), embedder=_ThreeDimensionalEmbedder())
    try:
        assert list(reloaded.entities) == eids
        assert reloaded.entities[eids[0]].payload["reinforcement_count"] == 1
    finally:
        reloaded.close()


def test_jsonl_reconstruction_preserves_first_record_order_while_last_record_wins(tmp_path: Path):
    writer = MemoryGraph(str(tmp_path), embedder=_ThreeDimensionalEmbedder())
    try:
        writer._append_jsonl(writer.meta_path, _node_record(42, "first-42"))
        writer._append_jsonl(writer.meta_path, _node_record(7, "first-7"))
        writer._append_jsonl(writer.meta_path, _node_record(42, "last-42"))
    finally:
        writer.close()

    reloaded = MemoryGraph(str(tmp_path), embedder=_ThreeDimensionalEmbedder())
    try:
        assert list(reloaded.entities) == [42, 7]
        assert reloaded.entities[42].payload["summary"] == "last-42"
    finally:
        reloaded.close()


def test_aborted_unflushed_memory_is_removed_without_reordering_later_current_memory(tmp_path: Path):
    graph = MemoryGraph(str(tmp_path), embedder=_ThreeDimensionalEmbedder())
    try:
        first = _add_memory(graph, "first")
        pending = graph.spawn_memory(
            summary="pending",
            embedding=np.asarray((0.0, 1.0, 0.0), dtype=np.float32),
            mtype="episodic",
            strength=0.8,
            confidence=0.9,
            half_life_days=20.0,
            user_id="aria",
            step=2,
        )
        assert list(graph.entities) == [first, pending]
        graph.abort_unflushed_node(pending)
        later = _add_memory(graph, "later", embedding=(0.0, 0.0, 1.0))
        assert later > pending
        assert list(graph.entities) == [first, later]
    finally:
        graph.close()

    reloaded = MemoryGraph(str(tmp_path), embedder=_ThreeDimensionalEmbedder())
    try:
        assert list(reloaded.entities) == [first, later]
        assert pending not in reloaded.entities
    finally:
        reloaded.close()


def _collision_context(eid: int, srg_state: dict) -> FabricPostWriteContext:
    return FabricPostWriteContext.make(
        workspace_id="ws",
        agent_id="aria",
        scope="private",
        chosen_domain="personal",
        step=11,
        storage_outcome=PostWriteStorageOutcome.CREATED_NEW,
        stored=True,
        eid=eid,
        created_motif=None,
        motif_ids=(),
        half_life_days=20.0,
        summary="incoming",
        embedding=np.asarray((1.0, 0.0, 0.0), dtype=np.float32),
        memory_class="core",
        memory_type="episodic",
        strength=0.8,
        confidence=0.9,
        promotion_score=0.9,
        stability_delta=0.1,
        tri_mod={},
        debug={},
        srg_state=srg_state,
        phase_durations={},
        state_symbol=None,
        affect_tag=None,
        affect_conf=None,
        skip_packet_emission=False,
    )


def test_actual_srg_collision_mutates_live_payloads_but_is_not_durable_without_another_write(tmp_path: Path):
    existing_srg = SRGMemoryState(R=0.10, R_band=0, L=8.0, L_phase=0.2, heartbeat_class="A")
    incoming_srg = SRGMemoryState(R=0.15, R_band=0, L=10.0, L_phase=-0.3, heartbeat_class="B")
    graph = MemoryGraph(str(tmp_path), embedder=_ThreeDimensionalEmbedder())
    try:
        existing = _add_memory(graph, "existing", extra={"srg": existing_srg.to_dict()})
        incoming = _add_memory(graph, "incoming", extra={"srg": incoming_srg.to_dict()})
        before_existing = deepcopy(graph.entities[existing].payload["srg"])
        before_incoming = deepcopy(graph.entities[incoming].payload["srg"])
        access = LegacyPostWriteMemoryAccess(graph, expected_dimension=3)
        adapter = LegacyFabricPostWriteAdapter(SimpleNamespace(
            owner=SimpleNamespace(_srg_enable=True, _log=logging.getLogger("a3d4-archaeology")),
            memory_access=access,
            memory_enumeration=access,
            srg_runtime=LegacySRGTransientRuntime(graph),
            embedding_dimension=3,
        ))

        adapter._run_srg_collision(_collision_context(incoming, incoming_srg.to_dict()))

        assert graph.entities[existing].payload["srg"] != before_existing
        assert graph.entities[incoming].payload["srg"] != before_incoming
        assert graph.entities[incoming].payload["srg_collision"]["collision"] is True
    finally:
        graph.close()

    reloaded = MemoryGraph(str(tmp_path), embedder=_ThreeDimensionalEmbedder())
    try:
        assert reloaded.entities[existing].payload["srg"] == before_existing
        assert reloaded.entities[incoming].payload["srg"] == before_incoming
        assert "srg_collision" not in reloaded.entities[incoming].payload
    finally:
        reloaded.close()
