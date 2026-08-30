"""Focused contract tests for the backend-neutral legacy read adapter."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from torment_service.governance import (
    allows_collective_reingest,
    is_compression_protected,
    is_decay_accelerated,
    should_emit_packet,
)
from torment_service.kernel.seed_entities import SeedEntity
from torment_service.memory_graph import MemoryGraph
from torment_service.memory_runtime_access import (
    LegacyPostWriteMemoryAccess,
    PostWriteMemoryEnumerationPort,
    PostWriteMemoryReadPort,
    runtime_memory_view_from_legacy_payload,
)


class _ThreeDimensionalEmbedder:
    dim = 3

    def embed(self, _text: str) -> np.ndarray:
        return np.zeros(3, dtype=np.float32)


def _graph(tmp_path: Path) -> MemoryGraph:
    return MemoryGraph(str(tmp_path), embedder=_ThreeDimensionalEmbedder())


def _put(graph: MemoryGraph, eid: int, payload: dict, vector: tuple[float, float, float]) -> None:
    graph.entities[eid] = SeedEntity(
        eid=eid, born_step=0, channel=0,
        pos=np.zeros(3), vel=np.zeros(3), vel0=np.zeros(3), payload=payload,
    )
    np.save(graph._emb_path(eid), np.asarray(vector, dtype=np.float32))


def _payload(**overrides: object) -> dict:
    value = {
        "summary": "contract memory",
        "type": "reflection",
        "memory_class": "core",
        "strength": 0.7,
        "confidence": 0.8,
        "half_life": 0.0,
        "user_id": "aria",
        "resonance_score": 0.61,
        "loop_type": "spiral",
        "srg": {"band": 2, "is_crystal": False},
        "ordinary": {"nested": ["safe", {"value": 1}]},
        "governance": {
            "protected": True,
            "non_shareable": True,
            "collective_export_blocked": False,
            "collective_reingest_blocked": True,
            "decay_accelerated": True,
        },
        "provenance": {
            "source_type": "user_input",
            "write_path": "direct_ingest",
        },
    }
    value.update(overrides)
    return value


def test_legacy_current_view_is_immutable_and_exposes_ordered_enumeration(tmp_path: Path):
    graph = _graph(tmp_path)
    payload = _payload()
    payload["embedding_ref"] = {"opaque": "structural"}
    _put(graph, 7, payload, (2.0, 0.6, 0.0))
    access = LegacyPostWriteMemoryAccess(graph, expected_dimension=3)

    assert isinstance(access, PostWriteMemoryReadPort)
    assert isinstance(access, PostWriteMemoryEnumerationPort)
    assert tuple(item.eid for item in access.list_current()) == (7,)
    view = access.get_current(7)
    assert view is not None
    assert (view.eid, view.summary, view.memory_type, view.memory_class) == (7, "contract memory", "reflection", "core")
    assert view.payload["srg"]["band"] == 2
    assert "governance" not in view.payload and "provenance" not in view.payload and "embedding_ref" not in view.payload
    assert view.governance.structurally_explicit is True
    assert view.provenance.source_type == "user_input"
    assert view.provenance.write_path == "direct_ingest"

    with pytest.raises(TypeError):
        view.payload["srg"] = {}  # type: ignore[index]
    with pytest.raises(TypeError):
        view.payload["ordinary"]["nested"] = ()  # type: ignore[index]
    payload["ordinary"]["nested"][1]["value"] = 99
    assert view.payload["ordinary"]["nested"][1]["value"] == 1


def test_legacy_adapter_preserves_search_and_raw_embedding_paths(tmp_path: Path):
    graph = _graph(tmp_path)
    _put(graph, 1, _payload(summary="first", governance={}, provenance="collective"), (1.0, 0.0, 0.0))
    _put(graph, 2, _payload(summary="second", user_id="aria", governance={}, provenance={}), (0.8, 0.6, 0.0))
    _put(graph, 3, _payload(summary="other user", user_id="other", governance={}, provenance={}), (0.8, 0.6, 0.0))
    _put(graph, 4, _payload(summary="zero", governance={}, provenance={}), (0.0, 0.0, 0.0))
    access = LegacyPostWriteMemoryAccess(graph, expected_dimension=3)

    outcome = access.search_by_embedding((1.0, 0.0, 0.0), top_k=3, user_id="aria")
    assert outcome.status == "SEARCHABLE"
    hits = outcome.hits
    assert [hit.eid for hit in hits] == [1, 2]
    assert [hit.view.summary for hit in hits] == ["first", "second"]
    assert hits[0].raw_score == pytest.approx(1.0)
    assert hits[1].raw_score == pytest.approx(0.8, rel=1e-6)
    assert [hit.eid for hit in access.search_by_embedding(
        (1.0, 0.0, 0.0), top_k=4, user_id="aria",
    ).hits] == [1, 2, 4]

    embedding = access.read_current_embedding(4, expected_dimension=3)
    assert embedding is not None and embedding.dimension == 3
    assert embedding.as_float32().tolist() == [0.0, 0.0, 0.0]
    assert embedding.as_float32().flags.writeable is False
    with pytest.raises(ValueError):
        access.read_current_embedding(1, expected_dimension=4)
    assert access.get_current(999) is None and access.read_current_embedding(999, expected_dimension=3) is None


@pytest.mark.parametrize(
    ("governance", "expected_emit", "expected_reingest", "expected_decay", "expected_protected"),
    (
        ({}, True, True, False, False),
        ({"protected": True}, True, True, False, True),
        ({"non_shareable": True}, False, True, False, False),
        ({"collective_export_blocked": True}, False, True, False, False),
        ({"collective_reingest_blocked": True}, True, False, False, False),
        ({"decay_accelerated": True}, True, True, True, False),
        ({"protected": True, "decay_accelerated": True, "non_shareable": True}, False, True, False, True),
    ),
)
def test_governance_projection_has_existing_runtime_meaning(
    governance: dict, expected_emit: bool, expected_reingest: bool, expected_decay: bool, expected_protected: bool,
):
    payload = _payload(governance=governance)
    view = runtime_memory_view_from_legacy_payload(1, payload)
    assert view.governance.structurally_explicit is True
    assert (not view.governance.non_shareable and not view.governance.collective_export_blocked) is expected_emit
    assert (not view.governance.collective_reingest_blocked) is expected_reingest
    assert (view.governance.decay_accelerated and not view.governance.protected) is expected_decay
    assert view.governance.protected is expected_protected
    assert should_emit_packet(payload) is expected_emit
    assert allows_collective_reingest(payload) is expected_reingest
    assert is_decay_accelerated(payload) is expected_decay
    assert is_compression_protected(payload) is expected_protected


def test_hivemind_and_conflict_read_facts_are_sufficient_without_rewiring(tmp_path: Path):
    graph = _graph(tmp_path)
    collective = _payload(
        summary="collective echo", provenance="collective",
        governance={"collective_export_blocked": True},
    )
    _put(graph, 1, collective, (1.0, 0.0, 0.0))
    _put(graph, 2, _payload(summary="candidate", governance={}, provenance={}), (0.8, 0.6, 0.0))
    access = LegacyPostWriteMemoryAccess(graph, expected_dimension=3)

    view = access.get_current(1)
    assert view is not None
    assert view.provenance.collective_echo is True
    assert view.payload["resonance_score"] == 0.61 and view.payload["loop_type"] == "spiral"
    assert not view.governance.non_shareable and view.governance.collective_export_blocked
    outcome = access.search_by_embedding((1.0, 0.0, 0.0), top_k=3, user_id="aria")
    assert outcome.status == "SEARCHABLE"
    hits = outcome.hits
    candidate = next(hit for hit in hits if hit.eid == 2)
    assert candidate.view.memory_class == "core"
    assert candidate.view.summary == "candidate" and candidate.raw_score > 0.0
