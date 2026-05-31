"""Track J regressions for per-agent kernel runtime history."""

from __future__ import annotations

import inspect
from types import SimpleNamespace
from typing import Any, Dict

import numpy as np
import pytest
from fastapi import HTTPException

from torment_service.embeddings import HashEmbedding
from torment_service.fabric import TormentFabric
from torment_service.memory_kernel import TriOctaMemoryKernel


A_TEXT = "Alpha research note: phase lock synchronization and corridor stability."
B_TEXT = "Candidate 129: signal corridor echo winter glass winter echo marker-129"


def _new_fabric(monkeypatch: pytest.MonkeyPatch) -> TormentFabric:
    monkeypatch.setenv("TORMENT_EMBED_PROVIDER", "hash")
    monkeypatch.setenv("TORMENT_CHARACTER_ENABLE", "0")
    monkeypatch.setenv("TORMENT_CHECKPOINT_ENABLE", "0")
    monkeypatch.setenv("TORMENT_COMPRESS_ENABLE", "0")
    monkeypatch.setenv("TORMENT_SRG_ENABLE", "0")
    monkeypatch.setenv("TORMENT_HIVEMIND_ENABLE", "0")
    monkeypatch.setenv("TORMENT_SQLITE_INDEX_ENABLE", "0")
    fabric = TormentFabric(":memory:")
    fabric.get_workspace("audit", domains=["research"])
    return fabric


def _b_service_snapshot(
    monkeypatch: pytest.MonkeyPatch, *, preload_a: bool,
) -> Dict[str, Any]:
    fabric = _new_fabric(monkeypatch)
    try:
        if preload_a:
            for step in range(1, 13):
                fabric.ingest(
                    workspace_id="audit",
                    agent_id="a",
                    text=A_TEXT,
                    step=step,
                    domain_id="research",
                )
        result = fabric.ingest(
            workspace_id="audit",
            agent_id="b",
            text=B_TEXT,
            step=1,
            domain_id="research",
        )
        graph = fabric.private_graphs[fabric._agent_key("audit", "b")]
        payload = graph.entities[int(result["eid"])].payload
        lifecycle = payload["lifecycle_status"]
        return {
            "coherence": result["debug"]["coherence"],
            "strength": result["signals"]["strength"],
            "half_life": payload["half_life"],
            "canon": payload["canon"],
            "lifecycle": lifecycle["state"],
            "lifecycle_via": lifecycle["set_by"]["via"],
        }
    finally:
        fabric.close()


def test_sequential_agent_history_isolation_preserves_authority_outcome(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert _b_service_snapshot(monkeypatch, preload_a=False) == _b_service_snapshot(
        monkeypatch, preload_a=True,
    )


def test_kernel_requires_explicit_context_and_keeps_history_off_template() -> None:
    kernel = TriOctaMemoryKernel(embedder=HashEmbedding())
    assert "mon" not in kernel.__dict__
    assert "_disp_buffer" not in kernel.__dict__
    assert "_last_effective_scale" not in kernel.__dict__

    state = kernel.init_state("agent:a")
    ctx = kernel.new_runtime_context()
    params_before = (kernel.params.g, kernel.params.theta_lock)
    omega_before = state.Omega.copy()
    kernel.process(state, A_TEXT, ctx)

    assert ctx.disp_buffer
    assert ctx.mon.coh_ema > 0.0
    assert not np.array_equal(state.Omega, omega_before)
    assert (kernel.params.g, kernel.params.theta_lock) == params_before

    with pytest.raises(RuntimeError, match="KernelRuntimeContext is required"):
        kernel.process(kernel.init_state("agent:b"), B_TEXT, None)  # type: ignore[arg-type]


def test_fabric_context_lifecycle_is_structurally_paired(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fabric = _new_fabric(monkeypatch)
    try:
        assert fabric.get_kernel_runtime_context("audit", "missing") is None
        assert fabric._kernel_contexts == {}

        fabric.create_agent("audit", "a")
        ak = fabric._agent_key("audit", "a")
        assert ak in fabric.agent_states
        assert fabric.get_kernel_runtime_context("audit", "a") is fabric._kernel_contexts[ak]

        removed_ctx = fabric._kernel_contexts.pop(ak)
        with pytest.raises(RuntimeError, match="lifecycle invariant violated"):
            fabric.create_agent("audit", "a")
        fabric._kernel_contexts[ak] = removed_ctx

        contexts_before_clone = dict(fabric._kernel_contexts)
        fabric.clone_workspace(
            "audit",
            "audit_clone",
            include_private=False,
            include_shared=False,
            reembed=False,
        )
        assert fabric._kernel_contexts == contexts_before_clone
        assert fabric.get_kernel_runtime_context("audit_clone", "a") is None
    finally:
        fabric.close()
    assert fabric._kernel_contexts == {}
    assert fabric.agent_states == {}


def test_periodic_checkpoint_routes_requested_agent_monitor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import torment_service.fabric as fabric_module

    fabric = _new_fabric(monkeypatch)
    captured: Dict[str, Any] = {}
    monkeypatch.setattr(
        fabric_module,
        "save_checkpoint",
        lambda **kwargs: captured.update(kwargs),
    )
    try:
        fabric._checkpoint_enable = True
        fabric._checkpoint_interval = 1
        fabric.create_agent("audit", "a")
        fabric.create_agent("audit", "b")
        ctx_a = fabric.get_kernel_runtime_context("audit", "a")
        ctx_b = fabric.get_kernel_runtime_context("audit", "b")
        assert ctx_a is not None and ctx_b is not None
        ctx_a.mon.coh_ema = 0.11
        ctx_b.mon.coh_ema = 0.89

        fabric.ingest("audit", "b", B_TEXT, step=1, domain_id="research")
        assert captured["corridor_monitor"] is ctx_b.mon
        assert captured["corridor_monitor"] is not ctx_a.mon
    finally:
        fabric.close()


def test_manual_checkpoint_routes_requested_agent_monitor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import torment_service.app as app_module
    import torment_service.checkpoint as checkpoint_module

    fabric = _new_fabric(monkeypatch)
    captured: Dict[str, Any] = {}
    monkeypatch.setattr(app_module, "fabric", fabric)
    monkeypatch.setattr(app_module, "DATA_DIR", fabric.data_dir)
    monkeypatch.setattr(
        checkpoint_module,
        "save_checkpoint",
        lambda **kwargs: captured.update(kwargs) or "checkpoint.json",
    )
    try:
        fabric.create_agent("audit", "a")
        fabric.create_agent("audit", "b")
        ctx_a = fabric.get_kernel_runtime_context("audit", "a")
        ctx_b = fabric.get_kernel_runtime_context("audit", "b")
        assert ctx_a is not None and ctx_b is not None

        result = app_module.checkpoint_save(
            app_module.CheckpointSaveReq(workspace_id="audit", agent_id="b")
        )
        assert result["ok"] is True
        assert captured["corridor_monitor"] is ctx_b.mon
        assert captured["corridor_monitor"] is not ctx_a.mon
    finally:
        fabric.close()


def test_manual_checkpoint_fails_closed_when_context_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import torment_service.app as app_module
    import torment_service.checkpoint as checkpoint_module

    fabric = _new_fabric(monkeypatch)
    saved: Dict[str, Any] = {}
    monkeypatch.setattr(app_module, "fabric", fabric)
    monkeypatch.setattr(app_module, "DATA_DIR", fabric.data_dir)
    monkeypatch.setattr(
        checkpoint_module,
        "save_checkpoint",
        lambda **kwargs: saved.update(kwargs),
    )
    try:
        fabric.create_agent("audit", "a")
        ak = fabric._agent_key("audit", "a")
        fabric._kernel_contexts.pop(ak)
        with pytest.raises(HTTPException) as exc:
            app_module.checkpoint_save(
                app_module.CheckpointSaveReq(workspace_id="audit", agent_id="a")
            )
        assert exc.value.status_code == 409
        assert saved == {}
    finally:
        fabric.close()


def test_periodic_checkpoint_skips_when_context_disappears_after_process(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import torment_service.fabric as fabric_module

    fabric = _new_fabric(monkeypatch)
    saved: Dict[str, Any] = {}
    monkeypatch.setattr(
        fabric_module,
        "save_checkpoint",
        lambda **kwargs: saved.update(kwargs),
    )
    try:
        fabric._checkpoint_enable = True
        fabric._checkpoint_interval = 1
        fabric.create_agent("audit", "a")
        ak = fabric._agent_key("audit", "a")
        real_process = fabric.kernel.process

        def drop_context_after_process(state, text, runtime_ctx):
            result = real_process(state, text, runtime_ctx)
            fabric._kernel_contexts.pop(ak)
            return result

        monkeypatch.setattr(fabric.kernel, "process", drop_context_after_process)
        result = fabric.ingest("audit", "a", A_TEXT, step=1, domain_id="research")
        assert result["stored"] is True
        assert saved == {}
    finally:
        fabric.close()


def test_advisory_readers_route_requested_agent_and_skip_absent_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import torment_service.app as app_module
    import torment_service.geometric_harvester as harvester_module
    import torment_service.spine as spine_module
    import torment_service.thinking_controller as thinking_module

    fabric = _new_fabric(monkeypatch)
    captured: list[Dict[str, Any]] = []

    def fake_harvest_geometric_context(**kwargs: Any) -> Dict[str, Any]:
        captured.append(kwargs)
        return kwargs

    class FakeThinkingController:
        def think(self, **kwargs: Any) -> Any:
            return SimpleNamespace(
                memory_plan=SimpleNamespace(top_k_by_lane={}, weight_by_lane={})
            )

    monkeypatch.setattr(harvester_module, "harvest_geometric_context", fake_harvest_geometric_context)
    monkeypatch.setattr(thinking_module, "ThinkingController", FakeThinkingController)
    monkeypatch.setattr(app_module, "fabric", fabric)
    monkeypatch.setenv("TORMENT_THINKING_ADVISORY", "1")
    monkeypatch.setattr(fabric, "query", lambda **kwargs: kwargs)
    try:
        fabric.create_agent("audit", "a")
        fabric.create_agent("audit", "b")
        ctx_a = fabric.get_kernel_runtime_context("audit", "a")
        ctx_b = fabric.get_kernel_runtime_context("audit", "b")
        assert ctx_a is not None and ctx_b is not None
        ctx_a.mon.coh_ema = 0.11
        ctx_b.mon.coh_ema = 0.89

        app_module.query(
            app_module.QueryReq(workspace_id="audit", agent_id="b", query=B_TEXT)
        )
        assert captured[-1]["tri_mod"]["coh_phase"] == 0.89

        spine_module._harvest_geometric_context(fabric, "audit", "b")
        assert captured[-1]["tri_mod"]["coh_phase"] == 0.89

        spine_module._harvest_geometric_context(fabric, "audit", "missing")
        assert captured[-1]["tri_mod"] is None
        assert fabric.get_kernel_runtime_context("audit", "missing") is None

        app_module.query(
            app_module.QueryReq(workspace_id="audit", agent_id="missing", query=B_TEXT)
        )
        assert captured[-1]["tri_mod"] is None
        assert fabric.get_kernel_runtime_context("audit", "missing") is None
    finally:
        fabric.close()


def test_clone_implementation_does_not_copy_live_runtime_contexts() -> None:
    source = inspect.getsource(TormentFabric.clone_workspace)
    assert "_kernel_contexts" not in source
