"""Characterization locks for Fabric's legacy post-write runtime tail.

These exercise ``TormentFabric.ingest`` directly.  They deliberately do not
know about the A3D1 boundary implementation so the same observations guard
the extraction rather than merely testing its new adapter.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

import torment_service.fabric as fabric_module
from torment_service.fabric import TormentFabric
from torment_service.memory_kernel import KernelSignals
from torment_service.post_write_runtime import (
    LegacyFabricPostWriteAdapter,
    PostWriteStorageOutcome,
)


def _configure_legacy_runtime(monkeypatch: pytest.MonkeyPatch, **values: str) -> None:
    defaults = {
        "TORMENT_EMBED_PROVIDER": "hash",
        "TORMENT_AFFECT_ENABLE": "0",
        "TORMENT_CHARACTER_ENABLE": "0",
        "TORMENT_CHECKPOINT_ENABLE": "0",
        "TORMENT_COMPRESS_ENABLE": "0",
        "TORMENT_SRG_ENABLE": "0",
        "TORMENT_HIVEMIND_ENABLE": "0",
        "TORMENT_REINFORCE_SIM_THRESHOLD": "0",
    }
    defaults.update(values)
    for key, value in defaults.items():
        monkeypatch.setenv(key, value)


def _install_kernel_signals(
    monkeypatch: pytest.MonkeyPatch,
    fabric: TormentFabric,
    *,
    write_intent: bool,
    coherence: float = 0.5,
) -> None:
    signals = KernelSignals(
        write_intent=write_intent,
        memory_type="episodic",
        strength=0.9,
        confidence=0.8,
        half_life=20.0,
        promotion_score=0.9,
        links=[],
        stability_delta=0.1,
    )

    def process(state, _text, _runtime_context):
        return state, signals, {"summary": "post-write characterization", "coherence": coherence}

    monkeypatch.setattr(fabric.kernel, "process", process)


def _fabric_with_agent(tmp_path, monkeypatch: pytest.MonkeyPatch, **env: str):
    _configure_legacy_runtime(monkeypatch, **env)
    fabric = TormentFabric(str(tmp_path))
    workspace_id, agent_id = "post-write-workspace", "post-write-agent"
    identity = fabric.create_agent(workspace_id, agent_id)
    identity.overlay["write_threshold"] = 0.0
    fabric.ident_store.save(identity)
    workspace = fabric.get_workspace(workspace_id)
    graph = fabric.private_graphs[fabric._agent_key(workspace_id, agent_id)]
    return fabric, workspace_id, agent_id, workspace, graph


def test_no_write_keeps_world_step_and_periodic_checkpoint_without_new_memory_consumers(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fabric, workspace_id, agent_id, workspace, graph = _fabric_with_agent(
        tmp_path,
        monkeypatch,
        TORMENT_CHECKPOINT_ENABLE="1",
        TORMENT_CHECKPOINT_INTERVAL="3",
    )
    try:
        _install_kernel_signals(monkeypatch, fabric, write_intent=False)
        calls: list[str] = []
        observed: dict[str, object] = {}
        original_step = graph.step_world
        original_run = LegacyFabricPostWriteAdapter.run

        def step_world(*args, **kwargs):
            calls.append("world")
            return original_step(*args, **kwargs)

        def capture_run(adapter, context):
            observed["outcome"] = context.storage_outcome
            return original_run(adapter, context)

        monkeypatch.setattr(graph, "step_world", step_world)
        monkeypatch.setattr(
            LegacyFabricPostWriteAdapter,
            "run",
            capture_run,
        )
        monkeypatch.setattr(
            fabric_module,
            "save_checkpoint",
            lambda **_kwargs: calls.append("checkpoint"),
        )
        monkeypatch.setattr(
            workspace.motif_regs["personal"],
            "attach_or_create",
            lambda *_args, **_kwargs: pytest.fail("no-write path must not touch motif creation"),
        )

        result = fabric.ingest(
            workspace_id,
            agent_id,
            "no write still evolves the world",
            step=3,
            domain_id="personal",
            supplied_embedding=[0.25] * workspace.embed_dim,
        )

        assert result["stored"] is False
        assert result["reinforced"] is False
        assert result["eid"] is None
        assert result["motifs"] == []
        assert result["created_motif"] is None
        assert calls == ["world", "checkpoint"]
        assert observed["outcome"] is PostWriteStorageOutcome.NO_WRITE
    finally:
        fabric.close()


def test_reinforcement_keeps_world_step_but_does_not_enter_new_memory_consumers(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fabric, workspace_id, agent_id, workspace, graph = _fabric_with_agent(
        tmp_path,
        monkeypatch,
        TORMENT_REINFORCE_SIM_THRESHOLD="0.92",
    )
    try:
        _install_kernel_signals(monkeypatch, fabric, write_intent=True)
        embedding = [0.5] * workspace.embed_dim
        existing_eid = graph.spawn_memory(
            summary="reinforce me",
            embedding=embedding,
            mtype="episodic",
            strength=0.6,
            confidence=0.8,
            half_life_days=20.0,
            links=[],
            canon=False,
            user_id=agent_id,
            step=0,
            memory_class="core",
            extra_payload={},
        )
        graph.flush_node(existing_eid)
        calls: list[str] = []
        observed: dict[str, object] = {}
        original_step = graph.step_world
        original_run = LegacyFabricPostWriteAdapter.run

        def step_world(*args, **kwargs):
            calls.append("world")
            return original_step(*args, **kwargs)

        def capture_run(adapter, context):
            observed["outcome"] = context.storage_outcome
            return original_run(adapter, context)

        monkeypatch.setattr(graph, "step_world", step_world)
        monkeypatch.setattr(
            LegacyFabricPostWriteAdapter,
            "run",
            capture_run,
        )
        monkeypatch.setattr(
            workspace.motif_regs["personal"],
            "attach_or_create",
            lambda *_args, **_kwargs: pytest.fail("reinforcement must not create/attach a motif"),
        )
        monkeypatch.setattr(
            fabric,
            "_get_collective_field",
            lambda _workspace_id: pytest.fail("reinforcement must not emit a Hivemind packet"),
        )

        result = fabric.ingest(
            workspace_id,
            agent_id,
            "reinforce me",
            step=4,
            domain_id="personal",
            supplied_embedding=embedding,
        )

        assert result["stored"] is True
        assert result["reinforced"] is True
        assert result["eid"] == existing_eid
        assert result["motifs"] == []
        assert result["created_motif"] is None
        assert calls == ["world"]
        assert observed["outcome"] is PostWriteStorageOutcome.REINFORCED_EXISTING
    finally:
        fabric.close()


def test_new_memory_post_write_consumer_order_and_public_result_are_characterized(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fabric, workspace_id, agent_id, workspace, graph = _fabric_with_agent(
        tmp_path,
        monkeypatch,
        TORMENT_HIVEMIND_ENABLE="1",
    )
    try:
        _install_kernel_signals(monkeypatch, fabric, write_intent=True, coherence=0.5)
        calls: list[str] = []
        registry = workspace.motif_regs["personal"]

        original_search = graph.search_by_embedding
        original_step = graph.step_world
        original_maintenance = registry.update_entropy_and_suggest

        def search_by_embedding(*args, **kwargs):
            calls.append("contradiction")
            return original_search(*args, **kwargs)

        def step_world(*args, **kwargs):
            calls.append("world")
            return original_step(*args, **kwargs)

        def maintenance(*args, **kwargs):
            calls.append("maintenance")
            return original_maintenance(*args, **kwargs)

        class _Field:
            def append_packet(self, _packet, *, embedding):
                assert embedding.shape == (workspace.embed_dim,)
                calls.append("hivemind")
                return None

        monkeypatch.setattr(graph, "search_by_embedding", search_by_embedding)
        monkeypatch.setattr(graph, "step_world", step_world)
        monkeypatch.setattr(registry, "update_entropy_and_suggest", maintenance)
        monkeypatch.setattr(fabric, "_get_collective_field", lambda _workspace_id: _Field())
        monkeypatch.setattr(
            fabric,
            "_maybe_emit_identity_anchor",
            lambda *_args, **_kwargs: calls.append("anchor"),
        )
        monkeypatch.setattr(
            fabric,
            "_refine_identity_anchors",
            lambda *_args, **_kwargs: calls.append("refine"),
        )
        monkeypatch.setattr(
            fabric,
            "_maybe_emit_mood_drift",
            lambda *_args, **_kwargs: calls.append("mood"),
        )
        monkeypatch.setattr(
            workspace.bridges,
            "suggest",
            lambda *_args, **_kwargs: calls.append("bridge"),
        )
        monkeypatch.setattr(fabric_module, "random_chance", lambda _probability: True)

        result = fabric.ingest(
            workspace_id,
            agent_id,
            "new memory records post-write ordering",
            step=5,
            domain_id="personal",
            supplied_embedding=[0.75] * workspace.embed_dim,
        )

        assert result["stored"] is True
        assert result["reinforced"] is False
        assert isinstance(result["eid"], int)
        assert result["motifs"] == ["motif_personal_0001"]
        assert result["created_motif"] == "motif_personal_0001"
        assert calls == [
            "contradiction",
            "hivemind",
            "maintenance",
            "anchor",
            "refine",
            "mood",
            "world",
            "bridge",
        ]
    finally:
        fabric.close()


def test_enabled_periodic_and_return_visible_consumers_keep_order_and_proposal_id(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fabric, workspace_id, agent_id, workspace, graph = _fabric_with_agent(
        tmp_path,
        monkeypatch,
        TORMENT_CHECKPOINT_ENABLE="1",
        TORMENT_CHECKPOINT_INTERVAL="7",
        TORMENT_COMPRESS_ENABLE="1",
        TORMENT_COMPRESS_MIN_STEP="7",
    )
    try:
        _install_kernel_signals(monkeypatch, fabric, write_intent=True)
        identity = fabric.create_agent(workspace_id, agent_id)
        identity.seed["coupling_mode"] = "propose"
        identity.overlay["novelty_bias"] = 0.8
        fabric.ident_store.save(identity)
        policy = workspace.domain_policies["personal"]
        policy.update({
            "auto_propose_min_promotion": 0.0,
            "auto_propose_min_strength": 0.0,
            "auto_propose_min_confidence": 0.0,
            "auto_propose_require_novelty": False,
        })
        calls: list[str] = []
        original_step = graph.step_world

        def step_world(*args, **kwargs):
            calls.append("world")
            return original_step(*args, **kwargs)

        def submit(**kwargs):
            assert kwargs["half_life_days"] == 20.0
            calls.append("proposal")
            return SimpleNamespace(proposal_id="proposal-a3d1")

        monkeypatch.setattr(graph, "step_world", step_world)
        monkeypatch.setattr(fabric_module, "save_checkpoint", lambda **_kwargs: calls.append("checkpoint"))
        import torment_service.compression as compression

        monkeypatch.setattr(
            compression,
            "try_compress",
            lambda *_args, **_kwargs: calls.append("compression") or None,
        )
        monkeypatch.setattr(
            compression,
            "check_hard_cap",
            lambda *_args, **_kwargs: calls.append("hard-cap") or None,
        )
        monkeypatch.setattr(workspace.proposals["personal"], "submit", submit)
        monkeypatch.setattr(
            workspace.bridges,
            "suggest",
            lambda *_args, **_kwargs: calls.append("bridge"),
        )
        monkeypatch.setattr(fabric_module, "random_chance", lambda _probability: True)

        result = fabric.ingest(
            workspace_id,
            agent_id,
            "new memory reaches all enabled post-write consumers",
            step=7,
            domain_id="personal",
            supplied_embedding=[0.33] * workspace.embed_dim,
        )

        assert result["stored"] is True
        assert result["reinforced"] is False
        assert result["proposal_id"] == "proposal-a3d1"
        assert calls == ["world", "checkpoint", "compression", "hard-cap", "proposal", "bridge"]
    finally:
        fabric.close()


def test_adapter_receives_selected_legacy_graph_registry_and_storage_outcome(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fabric, workspace_id, agent_id, workspace, graph = _fabric_with_agent(tmp_path, monkeypatch)
    try:
        _install_kernel_signals(monkeypatch, fabric, write_intent=True)
        observed = {}
        original_run = LegacyFabricPostWriteAdapter.run

        def run(adapter, context):
            observed["graph"] = adapter._deps.graph
            observed["registry"] = adapter._deps.motif_registry
            observed["outcome"] = context.storage_outcome
            return original_run(adapter, context)

        monkeypatch.setattr(LegacyFabricPostWriteAdapter, "run", run)
        result = fabric.ingest(
            workspace_id,
            agent_id,
            "adapter retains the current legacy objects",
            step=8,
            domain_id="personal",
            supplied_embedding=[0.19] * workspace.embed_dim,
        )

        assert result["stored"] is True
        assert observed == {
            "graph": graph,
            "registry": workspace.motif_regs["personal"],
            "outcome": PostWriteStorageOutcome.CREATED_NEW,
        }
    finally:
        fabric.close()
