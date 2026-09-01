"""A3 qualification-only full Fabric cognition parity over A2 readers."""
from __future__ import annotations

import numpy as np
import pytest

from torment_service.bridges import Bridge
from torment_service.character import CharacterSeed, CharacterState
from torment_service.fabric import TormentFabric
from torment_service.query_read_model import NativeQualifiedQueryReadModel

from tests.test_7g5e4e_native_query_read_model import qualified_models


@pytest.fixture
def fabric_models(qualified_models, tmp_path, monkeypatch):
    legacy_model, native_model, native_embedder, legacy_embedders = qualified_models
    monkeypatch.setenv("TORMENT_CHARACTER_ENABLE", "0")
    monkeypatch.setenv("TORMENT_COMPRESS_ENABLE", "0")
    fabric = TormentFabric(data_dir=str(tmp_path / "fabric"))
    try:
        workspace_id, agent_id = "orchard", "aria"
        ws = fabric.get_workspace(workspace_id, domains=["research", "engineering", "archive"])
        fabric.create_agent(workspace_id, agent_id)
        ak = fabric._agent_key(workspace_id, agent_id)
        private_graph = legacy_model._private[agent_id]._graph
        research_graph = legacy_model._shared["research"]._graph
        engineering_graph = legacy_model._shared["engineering"]._graph
        archive_graph = legacy_model._shared["archive"]._graph
        fabric.private_graphs[ak] = private_graph
        ws.shared_graphs = {
            "research": research_graph,
            "engineering": engineering_graph,
            "archive": archive_graph,
        }
        ws.motif_regs = legacy_model._registries
        ws.embed_dim = 3
        ws.meta["embed_dim"] = 3
        fabric.embedder = native_embedder
        fabric.kernel.embedder = native_embedder
        fabric._character_enable = False
        fabric._compress_enable = False

        # The production-shaped source holds legacy motif memberships in its
        # payload.  A2 reconstructs the same current facts from native motif
        # relationships, so give the direct differential graph that source
        # shape before comparing Fabric's one orchestration law.
        private_graph.entities[1].payload["motifs"] = ["private-anchor"]
        research_graph.entities[1].payload["motifs"] = ["same-id"]
        research_graph.entities[2].payload["motifs"] = ["research-hot"]
        engineering_graph.entities[1].payload["motifs"] = ["same-id"]
        ws.bridges.bridges.append(Bridge(
            from_domain="research", from_motif="same-id",
            to_domain="archive", to_motif="archive-id",
            confidence=.9, created_ts=1, status="approved", updated_ts=1,
        ))
        yield fabric, native_model, native_embedder, legacy_embedders
    finally:
        # The A2 fixture owns the injected graphs/native core.  Fabric owns
        # only its small external stores here, so avoid closing shared readers.
        fabric.private_graphs.clear()
        fabric.workspaces.clear()
        fabric.close()


def _paired_query(fabric, native_model, query_text="qualified query", **kwargs):
    expected = fabric.query("orchard", "aria", query_text, **kwargs)
    actual = fabric._query_with_read_model(
        "orchard", "aria", query_text, read_model=native_model, **kwargs,
    )
    assert actual == expected
    return actual


def _patch_compatibility(fabric, monkeypatch, transform):
    original = fabric._query_read_hits_to_compatibility

    def patched(hits, *, read_model):
        values = original(hits, read_model=read_model)
        for value in values:
            transform(value)
        return values

    monkeypatch.setattr(fabric, "_query_read_hits_to_compatibility", patched)


def test_full_query_cognition_is_identical_over_legacy_and_native_read_models(fabric_models):
    fabric, native_model, native_embedder, legacy_embedders = fabric_models
    kwargs = {
        "top_k": 6,
        "domain_id": "research",
        "peek_bridges": True,
        "explain": True,
        "continuity_debug": True,
        "memory_plan": {
            "top_k_by_lane": {"core": 2, "relational": 2, "deep": 0},
            "weight_by_lane": {"core": 1.1, "relational": .9},
        },
    }
    native_embedder.calls.clear()
    for embedder in legacy_embedders:
        embedder.calls.clear()
    expected = fabric.query("orchard", "aria", "  qualified query  ", **kwargs)
    assert native_embedder.calls == ["  qualified query  "]
    assert sum(embedder.calls.count("qualified query") for embedder in legacy_embedders) == 4
    native_embedder.calls.clear()
    actual = fabric._query_with_read_model(
        "orchard", "aria", "  qualified query  ", read_model=native_model,
        **kwargs,
    )
    assert actual == expected
    assert native_embedder.calls == ["  qualified query  "] + ["qualified query"] * 4
    assert [item["scope"] for item in actual["results"]] == [item["scope"] for item in expected["results"]]
    assert all("_a3_qualified_query_hit" not in item for item in actual["results"])
    assert actual["bridge_peek_domains"] == ["archive"]
    assert actual["motifs"]["active"] == expected["motifs"]["active"]
    assert actual["continuity_debug"] == expected["continuity_debug"]


def test_native_qualification_refuses_an_enabled_deep_profile(fabric_models):
    fabric, native_model, _native_embedder, _legacy_embedders = fabric_models
    fabric._compress_enable = True
    with pytest.raises(ValueError, match="does not support enabled deep retrieval"):
        fabric._query_with_read_model(
            "orchard", "aria", "qualified query", read_model=native_model,
        )


def test_native_query_uses_current_native_geometry_not_the_legacy_router(fabric_models):
    fabric, native_model, _native_embedder, _legacy_embedders = fabric_models
    result = fabric._query_with_read_model(
        "orchard", "aria", "qualified query", read_model=native_model,
        top_k=4,
    )
    assert result["domain_used"] == ["research", "engineering"]
    assert np.isfinite([item["final_score"] for item in result["results"]]).all()


@pytest.mark.parametrize(
    "query_text,kwargs",
    (
        ("qualified query", {}),
        ("qualified query", {"memory_plan": {"top_k_by_lane": {"core": 0, "relational": 0, "deep": 0}}}),
        ("   ", {"peek_bridges": True, "explain": True}),
    ),
)
def test_default_zero_budget_and_blank_query_parity(fabric_models, query_text, kwargs):
    fabric, native_model, native_embedder, _legacy_embedders = fabric_models
    native_embedder.calls.clear()
    result = _paired_query(fabric, native_model, query_text, **kwargs)
    if not query_text.strip():
        assert result["results"] == []
        assert native_embedder.calls == [query_text, query_text]
    if kwargs.get("memory_plan"):
        assert result["results"] == []


def test_stable_automatic_routing_requested_domain_and_unknown_domain_failure(fabric_models):
    fabric, native_model, native_embedder, _legacy_embedders = fabric_models
    original_vector = native_embedder.vector.copy()
    try:
        native_embedder.vector = np.zeros(3, dtype=np.float32)
        tied = _paired_query(
            fabric, native_model,
            memory_plan={"top_k_by_lane": {"core": 0, "relational": 0, "deep": 0}},
        )
        assert tied["domain_used"] == ["research", "engineering"]
    finally:
        native_embedder.vector = original_vector

    requested = _paired_query(fabric, native_model, domain_id="engineering")
    assert requested["domain_used"][0] == "engineering"
    with pytest.raises(KeyError):
        fabric.query("orchard", "aria", "qualified query", domain_id="missing")
    with pytest.raises(KeyError):
        fabric._query_with_read_model(
            "orchard", "aria", "qualified query", read_model=native_model,
            domain_id="missing",
        )


def test_conflict_governance_and_provenance_parity(fabric_models, monkeypatch):
    fabric, native_model, _native_embedder, _legacy_embedders = fabric_models
    ws = fabric.get_workspace("orchard")
    conflict = ws.conflicts["research"].add(
        1, 2, .91, .62, "A3 qualified conflict",
        origin_scope="shared", origin_domain_id="research",
    )

    def transform(value):
        if value.get("scope") == "shared" and value.get("domain_id") == "research":
            value["canon"] = True
            if value.get("eid") == 1:
                value["provenance"] = {"source_type": "collective_echo"}

    _patch_compatibility(fabric, monkeypatch, transform)
    result = _paired_query(fabric, native_model, explain=True, top_k=6)
    research = next(item for item in result["results"] if item["scope"] == "shared" and item["domain_id"] == "research" and item["eid"] == 1)
    engineering = next(item for item in result["results"] if item["scope"] == "shared" and item["domain_id"] == "engineering" and item["eid"] == 1)
    assert research["conflict_ids"] == [conflict.conflict_id]
    assert research["explain"]["conflict_penalty"] == pytest.approx(.62)
    assert engineering["explain"]["conflict_status"] is None
    assert research["provenance_type"] == "collective_echo"
    assert research["explain"]["collective_discount"] == pytest.approx(.5)

    def non_shareable(value):
        value["governance"] = {"non_shareable": True}

    _patch_compatibility(fabric, monkeypatch, non_shareable)
    filtered = _paired_query(fabric, native_model, top_k=1)
    assert filtered["results"] == []
    assert len(filtered["filter_excluded"]) == 1
    assert filtered["filter_excluded"][0]["excluded_reason"] == "non_shareable"
    assert filtered["_core_hits_in_count"] == 1


def test_character_context_and_cold_native_recovery_parity(fabric_models):
    fabric, native_model, native_embedder, _legacy_embedders = fabric_models
    identity = fabric.ident_store.load("orchard", "aria")
    assert identity is not None
    identity.seed = {"seed_id": "aria-a3", "seed_text": "Aria keeps a precise, gentle research voice."}
    fabric.ident_store.save(identity)
    fabric.character_store.save_seed("orchard", CharacterSeed(
        "aria-a3", "Aria", "Aria keeps a precise, gentle research voice.",
        owner_agent_id="aria", seed_motif_id="private-anchor", seed_eids=[1],
    ))
    fabric.character_store.save_state("orchard", CharacterState(
        "orchard", "aria", "aria-a3", drift_score=.2,
        drift_direction="toward_seed", relational_count=2,
    ))
    fabric._character_enable = True
    result = _paired_query(fabric, native_model, explain=True)
    assert result["character_context"]["seed_id"] == "aria-a3"
    assert all("character_tier" in item and "character_weighted_score" in item for item in result["results"])
    assert any(item["character_weighted_score"] != item["final_score"] for item in result["results"])

    native_model.close()
    cold = NativeQualifiedQueryReadModel(
        native_model._a3_fixture_runtime, embedder=native_embedder,
    )
    try:
        cold_result = fabric._query_with_read_model(
            "orchard", "aria", "qualified query", read_model=cold, explain=True,
        )
        assert cold_result == result
    finally:
        cold.close()


def test_native_srg_is_transient_qualified_and_matches_legacy_breathing(fabric_models, monkeypatch):
    fabric, native_model, _native_embedder, _legacy_embedders = fabric_models
    fabric._srg_enable = True
    fabric._srg_last_ingest_band_by_agent[("orchard", "aria")] = 4
    before = native_model.private_lane("orchard", "aria").search("qualified query", top_k=1)[0]
    original_effective = native_model.effective_srg_state

    def effective_with_fixture_modifiers(hit):
        state = dict(original_effective(hit) or {})
        state.update({"R_band": 4, "heartbeat_class": "A", "is_crystal": False, "L_amplitude": .25, "L_phase": .1})
        return state

    monkeypatch.setattr(native_model, "effective_srg_state", effective_with_fixture_modifiers)

    def nested_srg(value):
        source = dict(value.get("srg") or {})
        source.update({"R_band": 4, "heartbeat_class": "A", "is_crystal": False, "L_amplitude": .25, "L_phase": .1})
        value.pop("srg", None)
        value["payload"] = {"srg": source}

    _patch_compatibility(fabric, monkeypatch, nested_srg)
    first = _paired_query(fabric, native_model, explain=True)
    second = _paired_query(fabric, native_model, explain=True)
    assert first["results"][0]["explain"]["srg_same_band_bonus"] == pytest.approx(1.08)
    assert second["results"][0]["explain"]["srg_same_band_bonus"] == pytest.approx(1.08)
    assert first["results"][0]["explain"]["srg_heartbeat_bonus"] == pytest.approx(1.03)
    after = native_model.private_lane("orchard", "aria").search("qualified query", top_k=1)[0]
    assert after.native_revision_id == before.native_revision_id
    state = original_effective(after)
    assert state is not None and state["srg_step"] >= 2
