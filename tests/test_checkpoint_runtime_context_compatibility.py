"""Track J checkpoint compatibility for per-agent kernel runtime history."""

from __future__ import annotations

from typing import Any, Dict

from torment_service.checkpoint import (
    deserialize_model_state,
    load_latest_checkpoint,
    restore_from_checkpoint,
    save_checkpoint,
)
from torment_service.fabric import TormentFabric
from torment_service.memory_kernel import (
    DEFAULT_DISP_SCALE,
    CorridorMonitor,
    KernelRuntimeContext,
    TriOctaMemoryKernel,
)
from torment_service.cognitive_core import CognitiveCoreState


def _monitor(*, coh_ema: float) -> CorridorMonitor:
    mon = CorridorMonitor()
    mon.coh_ema = coh_ema
    mon.surv_ema = coh_ema + 0.1
    return mon


def _context(*, coh_ema: float) -> KernelRuntimeContext:
    return KernelRuntimeContext(
        mon=_monitor(coh_ema=coh_ema),
        disp_buffer=[0.1, 0.2, 0.3],
        last_effective_scale=1.75,
        cognitive_state=CognitiveCoreState(
            z_mem=0.031,
            z_identity=0.42,
            identity_state=5,
        ),
    )


def _save_payload(
    tmp_path, *, runtime_ctx: KernelRuntimeContext | None,
) -> Dict[str, Any]:
    kernel = TriOctaMemoryKernel()
    path = save_checkpoint(
        data_dir=str(tmp_path),
        workspace_id="audit",
        agent_id="a",
        step=7,
        model_state=kernel.init_state("audit/a"),
        corridor_monitor=_monitor(coh_ema=0.11),
        kernel_runtime_context=runtime_ctx,
    )
    assert path is not None
    payload = load_latest_checkpoint(str(tmp_path), "audit", "a")
    assert payload is not None
    return payload


def test_new_checkpoint_dual_writes_one_runtime_context_monitor(tmp_path) -> None:
    payload = _save_payload(tmp_path, runtime_ctx=_context(coh_ema=0.89))

    assert payload["version"] == 3
    assert payload["corridor_monitor"] == payload["kernel_runtime_context"]["mon"]
    assert payload["corridor_monitor"]["coh_ema"] == 0.89
    assert payload["kernel_runtime_context"]["disp_buffer"] == [0.1, 0.2, 0.3]
    assert payload["kernel_runtime_context"]["last_effective_scale"] == 1.75
    assert payload["kernel_runtime_context"]["cognitive_state"] == {
        "z_mem": 0.031,
        "z_identity": 0.42,
        "identity_state": 5,
    }
    assert payload["model_state"]["z_semantics"] == "kernel_canonical_v4_0"
    assert payload["model_state"]["z_mem"] == 0.031


def test_new_checkpoint_decode_prefers_runtime_context_monitor(tmp_path) -> None:
    payload = _save_payload(tmp_path, runtime_ctx=_context(coh_ema=0.89))
    payload["corridor_monitor"]["coh_ema"] = 0.01

    restored = restore_from_checkpoint(payload)

    runtime_ctx = restored["kernel_runtime_context"]
    assert restored["corridor_monitor"] is runtime_ctx.mon
    assert restored["corridor_monitor"].coh_ema == 0.89
    assert runtime_ctx.disp_buffer == [0.1, 0.2, 0.3]
    assert runtime_ctx.last_effective_scale == 1.75
    assert runtime_ctx.cognitive_state == CognitiveCoreState(
        z_mem=0.031,
        z_identity=0.42,
        identity_state=5,
    )


def test_legacy_checkpoint_decode_synthesizes_safe_runtime_defaults(tmp_path) -> None:
    payload = _save_payload(tmp_path, runtime_ctx=None)

    assert "kernel_runtime_context" not in payload
    restored = restore_from_checkpoint(payload)

    runtime_ctx = restored["kernel_runtime_context"]
    assert restored["corridor_monitor"] is runtime_ctx.mon
    assert runtime_ctx.mon.coh_ema == 0.11
    assert runtime_ctx.disp_buffer == []
    assert runtime_ctx.last_effective_scale == DEFAULT_DISP_SCALE
    assert runtime_ctx.cognitive_state.z_mem == 0.0
    assert runtime_ctx.cognitive_state.z_identity == payload["model_state"]["z"]
    assert runtime_ctx.cognitive_state.identity_state == payload["model_state"]["identity_state"]


def test_legacy_spliced_checkpoint_migrates_cognition_without_polluting_model_state(
    tmp_path,
) -> None:
    payload = _save_payload(tmp_path, runtime_ctx=None)
    payload["version"] = 2
    canonical_model = deserialize_model_state(payload["model_state"])
    legacy_z = float(canonical_model.z) + 1.0
    legacy_identity = (int(canonical_model.identity_state) + 1) % 9
    payload["model_state"]["z"] = legacy_z
    payload["model_state"]["z_mem"] = 0.031
    payload["model_state"]["identity_state"] = legacy_identity

    restored = restore_from_checkpoint(payload)

    model_state = restored["model_state"]
    runtime_ctx = restored["kernel_runtime_context"]
    assert not hasattr(model_state, "z_mem")
    assert model_state.z == canonical_model.z
    assert model_state.identity_state == canonical_model.identity_state
    assert runtime_ctx.cognitive_state == CognitiveCoreState(
        z_mem=0.031,
        z_identity=legacy_z,
        identity_state=legacy_identity,
    )


def test_checkpoint_decode_does_not_install_live_runtime_context(
    tmp_path, monkeypatch,
) -> None:
    monkeypatch.setenv("TORMENT_EMBED_PROVIDER", "hash")
    monkeypatch.setenv("TORMENT_CHARACTER_ENABLE", "0")
    monkeypatch.setenv("TORMENT_CHECKPOINT_ENABLE", "0")
    monkeypatch.setenv("TORMENT_COMPRESS_ENABLE", "0")
    monkeypatch.setenv("TORMENT_SRG_ENABLE", "0")
    monkeypatch.setenv("TORMENT_HIVEMIND_ENABLE", "0")
    monkeypatch.setenv("TORMENT_SQLITE_INDEX_ENABLE", "0")
    fabric = TormentFabric(":memory:")
    try:
        fabric.get_workspace("audit", domains=["research"])
        fabric.create_agent("audit", "a")
        contexts_before = dict(fabric._kernel_contexts)
        payload = _save_payload(tmp_path, runtime_ctx=_context(coh_ema=0.89))

        restored = restore_from_checkpoint(payload)

        assert restored["kernel_runtime_context"].mon.coh_ema == 0.89
        assert fabric._kernel_contexts == contexts_before
    finally:
        fabric.close()
