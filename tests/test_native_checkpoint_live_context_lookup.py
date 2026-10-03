"""Native checkpoint saves must use the requested agent's LIVE KernelRuntimeContext.

Track-J rule (legacy repair 06647224, now applied to the native private and shared
post-write checkpoint consumers):
  * look up the requested agent's context in the owner's live map at save time;
  * absent at save time -> skip (debug log, no write);
  * replaced since the binding was captured -> use the live object;
  * never recreate a context; never substitute another agent's context;
  * model_state stays binding.model_state; format, arguments and trigger logic unchanged.

The native runtime cannot start everywhere (SQLite admissibility policy), so the binding
is built exactly as public_runtime._post_write_configuration builds it, against a real
TormentFabric (real kernel.process via ingest(_prepare_only=True)), and the REAL adapter
methods are invoked unbound with a minimal self.  save_checkpoint is replaced by a recorder.
"""
from __future__ import annotations

import os
import tempfile
from types import SimpleNamespace
from unittest import mock

import pytest

os.environ.setdefault("TORMENT_EMBED_PROVIDER", "hash")

from torment_service.fabric import TormentFabric
from torment_service.substrate import native_post_write_runtime as npw
from torment_service.substrate.native_post_write_runtime import (
    NativeFabricPostWriteAdapter,
    NativePrivateCheckpointSnapshotBinding,
    NativeSharedCheckpointSnapshotBinding,
)

WS, A, B = "ws_live_ckpt", "agent_a", "agent_b"
CONSUMERS = {
    "private": (NativeFabricPostWriteAdapter._run_private_checkpoint_snapshot,
                NativePrivateCheckpointSnapshotBinding, "private_checkpoint_snapshot_binding"),
    "shared": (NativeFabricPostWriteAdapter._run_shared_checkpoint_snapshot,
               NativeSharedCheckpointSnapshotBinding, "shared_checkpoint_snapshot_binding"),
}


@pytest.fixture()
def fabric():
    f = TormentFabric(data_dir=tempfile.mkdtemp(prefix="live_ckpt_"))
    f.get_workspace(WS)
    f.create_agent(WS, A)
    f.create_agent(WS, B)
    f._checkpoint_enable, f._checkpoint_interval, f._checkpoint_max_keep = True, 1, 3
    try:
        yield f
    finally:
        try:
            f.close()
        except Exception:
            pass


def _process(fabric, agent):
    """Real Fabric cognition incl. kernel.process, as NativePublicIngestExecutor._prepare."""
    return fabric.ingest(WS, agent, "a memory about live checkpoint contexts", step=1, _prepare_only=True)


def _capture(fabric, agent, kind):
    """Exactly public_runtime._post_write_configuration's binding expression."""
    binding_cls = CONSUMERS[kind][1]
    return binding_cls(
        fabric.agent_states.get(fabric._agent_key(WS, agent)),
        fabric.get_kernel_runtime_context(WS, agent),
    )


def _run(fabric, agent, binding, kind, *, step=4):
    method, _cls, attr = CONSUMERS[kind]
    calls, logs = [], []
    self_ = SimpleNamespace(
        _configuration=SimpleNamespace(
            external=SimpleNamespace(owner=fabric, agent_key=fabric._agent_key(WS, agent), character_store=None),
            **{attr: binding},
        ),
        _build_native_checkpoint_motif_summary=lambda connection, context: None,
    )
    context = SimpleNamespace(workspace_id=WS, agent_id=agent, step=step)
    with mock.patch.object(npw, "save_checkpoint", lambda **kw: calls.append(kw)), \
            mock.patch.object(npw, "build_shard_snapshot", lambda *a, **k: None), \
            mock.patch.object(fabric._log, "debug", lambda msg, *args: logs.append(msg % args if args else msg)):
        method(self_, None, context)
    return calls, logs


def _map(fabric):
    return {k: id(v) for k, v in fabric._kernel_contexts.items()}


kinds = pytest.mark.parametrize("kind", sorted(CONSUMERS))


@kinds
def test_stable_context_is_the_exact_live_requested_context(fabric, kind):
    _process(fabric, A)
    ak = fabric._agent_key(WS, A)
    live = fabric._kernel_contexts[ak]
    binding = _capture(fabric, A, kind)
    calls, _ = _run(fabric, A, binding, kind)
    assert len(calls) == 1
    kw = calls[0]
    assert kw["kernel_runtime_context"] is live and kw["corridor_monitor"] is live.mon
    assert kw["model_state"] is binding.model_state is fabric.agent_states[ak]
    assert (kw["workspace_id"], kw["agent_id"], kw["step"], kw["max_checkpoints"]) == (WS, A, 4, 3)


@kinds
def test_context_removed_after_capture_is_skipped_at_save_time(fabric, kind):
    _process(fabric, A)
    ak = fabric._agent_key(WS, A)
    binding = _capture(fabric, A, kind)
    assert binding.kernel_runtime_context is not None
    del fabric._kernel_contexts[ak]
    before = _map(fabric)
    calls, logs = _run(fabric, A, binding, kind)
    assert calls == []                                   # HEAD: stale captured context was written
    assert f"checkpoint skipped: KernelRuntimeContext missing for {ak}" in logs
    assert _map(fabric) == before and ak not in fabric._kernel_contexts   # never recreated


@kinds
def test_context_absent_before_capture_is_still_skipped(fabric, kind):
    _process(fabric, A)
    ak = fabric._agent_key(WS, A)
    del fabric._kernel_contexts[ak]
    binding = _capture(fabric, A, kind)
    calls, logs = _run(fabric, A, binding, kind)
    assert calls == [] and f"checkpoint skipped: KernelRuntimeContext missing for {ak}" in logs
    assert ak not in fabric._kernel_contexts


@kinds
def test_context_replaced_after_capture_uses_the_live_object(fabric, kind):
    _process(fabric, A)
    ak = fabric._agent_key(WS, A)
    old = fabric._kernel_contexts[ak]
    binding = _capture(fabric, A, kind)
    replacement = fabric.kernel.new_runtime_context()
    fabric._kernel_contexts[ak] = replacement
    calls, _ = _run(fabric, A, binding, kind)
    assert len(calls) == 1
    assert calls[0]["kernel_runtime_context"] is replacement     # HEAD: old captured object
    assert calls[0]["corridor_monitor"] is replacement.mon
    assert calls[0]["kernel_runtime_context"] is not old
    assert calls[0]["model_state"] is binding.model_state


@kinds
def test_another_agent_context_is_never_substituted(fabric, kind):
    _process(fabric, A)
    _process(fabric, B)
    ka, kb = fabric._agent_key(WS, A), fabric._agent_key(WS, B)
    ctx_b = fabric._kernel_contexts[kb]
    binding = _capture(fabric, A, kind)
    del fabric._kernel_contexts[ka]
    calls, _ = _run(fabric, A, binding, kind)
    assert all(c["kernel_runtime_context"] is not ctx_b for c in calls)   # holds on HEAD and after
    assert calls == []                                                    # live rule: A absent -> skip
    assert fabric._kernel_contexts[kb] is ctx_b and ka not in fabric._kernel_contexts


@kinds
@pytest.mark.parametrize("enable,interval,step", [(False, 1, 4), (True, 5, 4), (True, 1, 0)],
                         ids=["checkpoint_disabled", "step_not_on_interval", "step_zero"])
def test_non_triggering_paths_remain_no_ops(fabric, kind, enable, interval, step):
    _process(fabric, A)
    fabric._checkpoint_enable, fabric._checkpoint_interval = enable, interval
    before = _map(fabric)
    calls, logs = _run(fabric, A, _capture(fabric, A, kind), kind, step=step)
    assert calls == [] and logs == [] and _map(fabric) == before
