"""Synthetic I4G-R2 public topology qualification; no real-root contact."""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from torment_service import public_runtime as public
from torment_service.public_runtime import NativePublicOperationRefused, NativePublicTormentRuntime
from torment_service.substrate.production_native_owner import (
    NativeProductionResourceOwnerError,
    _require_root_v2_topology,
)


@dataclass(frozen=True)
class _Scope:
    memory_runtime_scope: object

    @property
    def fabric_routing_scope(self) -> object:
        return SimpleNamespace(runtime_scope=self.memory_runtime_scope)


class _Runtime:
    def __init__(self, workspace_id: str, *, private_agents: tuple[str, ...], shared_domains: tuple[str, ...]) -> None:
        self.workspace_id = workspace_id
        self.representation_lane = SimpleNamespace(dimension=384)
        self.scopes = tuple(
            _Scope(SimpleNamespace(workspace_id=workspace_id, scope_kind="PRIVATE_AGENT", agent_id=agent, domain_id=None))
            for agent in private_agents
        ) + tuple(
            _Scope(SimpleNamespace(workspace_id=workspace_id, scope_kind="SHARED_DOMAIN", agent_id=None, domain_id=domain))
            for domain in shared_domains
        )
        self.descriptor = SimpleNamespace(payload={"lanes": [
            {"plan": {"scope_kind": "PRIVATE_AGENT", "agent_id": agent, "motif_domain_id": f"private-{agent}"}}
            for agent in private_agents
        ]})
        self._private = {
            item.memory_runtime_scope.agent_id: item
            for item in self.scopes
            if item.memory_runtime_scope.scope_kind == "PRIVATE_AGENT"
        }
        self._shared = {
            item.memory_runtime_scope.domain_id: item
            for item in self.scopes
            if item.memory_runtime_scope.scope_kind == "SHARED_DOMAIN"
        }

    def lookup_private(self, agent_id: str) -> _Scope:
        return self._private[agent_id]

    def lookup_shared(self, domain_id: str) -> _Scope:
        return self._shared[domain_id]


def _public_runtime(monkeypatch: pytest.MonkeyPatch, runtime: _Runtime) -> NativePublicTormentRuntime:
    monkeypatch.setattr(public, "_read_domain_policies", lambda *_args: {})
    monkeypatch.setattr(public, "_read_workspace_meta", lambda *_args: {})
    monkeypatch.setattr(public, "_ReadOnlyBridges", lambda _path: object())
    monkeypatch.setattr(public, "_ReadOnlyConflictRegistry", lambda _path: object())
    instance = NativePublicTormentRuntime.__new__(NativePublicTormentRuntime)
    instance.native_owner = SimpleNamespace(_recover_active_runtime=lambda workspace_id=None: runtime)
    instance.cognition_fabric = SimpleNamespace(
        data_dir="synthetic-root",
        kernel=SimpleNamespace(embedder=object()),
        prepare_native_cognition_agent=lambda workspace_id, agent_id: (workspace_id, agent_id),
    )
    instance._workspace_views = {}
    return instance


def test_workspace_view_supports_zero_and_many_private_scopes_with_exact_lookup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = _Runtime("ws-many", private_agents=("agent-a", "agent-b"), shared_domains=("alpha", "beta", "gamma"))
    public_runtime = _public_runtime(monkeypatch, runtime)

    view = public_runtime.get_workspace("ws-many")
    assert tuple(view.private_scopes) == ("agent-a", "agent-b")
    assert tuple(view.shared_scopes) == ("alpha", "beta", "gamma")
    assert view.domains == ("alpha", "beta", "gamma")
    assert public_runtime._prepare_native_agent("ws-many", "agent-a") == ("ws-many", "agent-a")
    public_runtime._require_shared_scope("ws-many", "beta")
    with pytest.raises(NativePublicOperationRefused, match="not admitted"):
        public_runtime._prepare_native_agent("ws-many", "unknown")
    with pytest.raises(NativePublicOperationRefused, match="not admitted"):
        public_runtime._require_shared_scope("ws-many", "unknown")


@pytest.mark.parametrize("private_count,shared_count", ((0, 1), (0, 5), (1, 1), (5, 1), (1, 4), (5, 5)))
def test_public_workspace_cardinality_matrix(
    monkeypatch: pytest.MonkeyPatch, private_count: int, shared_count: int,
) -> None:
    private_agents = tuple(f"agent-{index}" for index in range(private_count))
    shared_domains = tuple(f"domain-{index}" for index in range(shared_count))
    public_runtime = _public_runtime(
        monkeypatch,
        _Runtime("ws-matrix", private_agents=private_agents, shared_domains=shared_domains),
    )

    view = public_runtime.get_workspace("ws-matrix")
    assert tuple(view.private_scopes) == private_agents
    assert tuple(view.shared_scopes) == shared_domains


def test_zero_private_workspace_constructs_but_refuses_new_or_unadmitted_agents(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = _Runtime("ws-zero", private_agents=(), shared_domains=("research",))
    public_runtime = _public_runtime(monkeypatch, runtime)

    view = public_runtime.get_workspace("ws-zero")
    assert dict(view.private_scopes) == {}
    assert tuple(view.shared_scopes) == ("research",)
    with pytest.raises(NativePublicOperationRefused, match="not admitted"):
        public_runtime.create_agent("ws-zero", "new-agent")


def test_public_topology_gate_refuses_all_private_only_shapes() -> None:
    _require_root_v2_topology((
        SimpleNamespace(workspace_id="zero-private", scope_kind="SHARED_DOMAIN", agent_id=None, domain_id="research"),
        SimpleNamespace(workspace_id="many-private", scope_kind="PRIVATE_AGENT", agent_id="a", domain_id=None),
        SimpleNamespace(workspace_id="many-private", scope_kind="PRIVATE_AGENT", agent_id="b", domain_id=None),
        SimpleNamespace(workspace_id="many-private", scope_kind="SHARED_DOMAIN", agent_id=None, domain_id="research"),
    ))
    with pytest.raises(NativeProductionResourceOwnerError, match="topology is unsupported"):
        _require_root_v2_topology((
            SimpleNamespace(workspace_id="private-only", scope_kind="PRIVATE_AGENT", agent_id="a", domain_id=None),
        ))
    with pytest.raises(NativeProductionResourceOwnerError, match="no runtime workspaces"):
        _require_root_v2_topology(())


def test_public_topology_gate_refuses_duplicate_scope_identity() -> None:
    with pytest.raises(NativeProductionResourceOwnerError, match="duplicate"):
        _require_root_v2_topology((
            SimpleNamespace(workspace_id="ws", scope_kind="SHARED_DOMAIN", agent_id=None, domain_id="research"),
            SimpleNamespace(workspace_id="ws", scope_kind="SHARED_DOMAIN", agent_id=None, domain_id="research"),
        ))
