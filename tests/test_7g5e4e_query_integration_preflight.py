"""7G5E4E legacy-query characterization locks.

These tests do not select native retrieval.  They retain the A0 query-call
baseline and lock A1's prospective composite-identity repair in the legacy
query path.
"""
from __future__ import annotations

import os

import numpy as np

from torment_service.bridges import Bridge
from torment_service.fabric import TormentFabric
from torment_service.motifs import Motif


os.environ.setdefault("TORMENT_EMBED_PROVIDER", "hash")


class _CountingEmbedder:
    """Delegate to the configured hash embedder while recording query calls."""

    def __init__(self, delegate) -> None:
        self._delegate = delegate
        self.provider = delegate.provider
        self.model = delegate.model
        self.dim = delegate.dim
        self.calls: list[str] = []

    def embed(self, text: str):
        self.calls.append(text)
        return self._delegate.embed(text)


class _FixedEmbedder:
    """Deterministic test embedder with the current workspace dimension."""

    def __init__(self, delegate, vector: np.ndarray) -> None:
        self.provider = delegate.provider
        self.model = delegate.model
        self.dim = delegate.dim
        self.vector = np.asarray(vector, dtype=np.float32).reshape(-1)

    def embed(self, text: str):
        return self.vector.copy()


def _install_counting_embedder(fabric: TormentFabric, workspace_id: str, agent_id: str):
    counter = _CountingEmbedder(fabric.kernel.embedder)
    fabric.embedder = counter
    fabric.kernel.embedder = counter
    workspace = fabric.get_workspace(workspace_id)
    agent_key = fabric._agent_key(workspace_id, agent_id)
    for graph in (fabric.private_graphs[agent_key], *workspace.shared_graphs.values()):
        graph.embedder = counter
    return counter, workspace


def _install_fixed_embedder(
    fabric: TormentFabric,
    workspace_id: str,
    agent_id: str,
    vector: np.ndarray,
):
    fixed = _FixedEmbedder(fabric.kernel.embedder, vector)
    fabric.embedder = fixed
    fabric.kernel.embedder = fixed
    workspace = fabric.get_workspace(workspace_id)
    agent_key = fabric._agent_key(workspace_id, agent_id)
    for graph in (fabric.private_graphs[agent_key], *workspace.shared_graphs.values()):
        graph.embedder = fixed
    return fixed, workspace


def _add_lane_memory(
    graph,
    *,
    workspace_id: str,
    agent_id: str,
    scope: str,
    domain_id: str,
    text: str,
    vector: np.ndarray,
    memory_type: str = "fact",
    canon: bool = False,
) -> int:
    return graph.add_memory(
        summary=text,
        embedding=vector,
        mtype=memory_type,
        strength=0.5,
        confidence=0.8,
        half_life_days=30.0,
        canon=canon,
        user_id=agent_id,
        step=1,
        extra_payload={
            "workspace_id": workspace_id,
            "agent_id": agent_id,
            "scope": scope,
            "domain_id": domain_id,
        },
    )


def test_query_repeats_the_same_text_for_router_private_shared_and_bridge_lanes(tmp_path):
    """A non-empty query calls the lane embedder once per searched graph.

    The expected five calls are: Fabric routing, private MemoryGraph, both
    router-selected shared domains, and the one approved bridge-peek domain.
    Deep is explicitly disabled, so it consumes no additional embedding.
    """
    fabric = TormentFabric(data_dir=str(tmp_path))
    try:
        workspace_id, agent_id = "ws", "aria"
        workspace = fabric.get_workspace(workspace_id, domains=["alpha", "beta", "gamma"])
        fabric.create_agent(workspace_id, agent_id)
        counter, workspace = _install_counting_embedder(fabric, workspace_id, agent_id)
        vector = np.zeros(counter.dim, dtype=np.float32)
        vector[0] = 1.0
        agent_key = fabric._agent_key(workspace_id, agent_id)

        _add_lane_memory(
            fabric.private_graphs[agent_key], workspace_id=workspace_id,
            agent_id=agent_id, scope="private", domain_id="alpha",
            text="private evidence", vector=vector,
        )
        for domain_id in ("alpha", "beta", "gamma"):
            _add_lane_memory(
                workspace.shared_graphs[domain_id], workspace_id=workspace_id,
                agent_id=agent_id, scope="shared", domain_id=domain_id,
                text=f"{domain_id} shared evidence", vector=vector,
            )
        workspace.bridges.bridges.append(Bridge(
            from_domain="alpha", from_motif="motif-a",
            to_domain="gamma", to_motif="motif-g", confidence=1.0,
            created_ts=1, status="approved", updated_ts=1,
        ))

        counter.calls.clear()
        result = fabric.query(
            workspace_id, agent_id, "frozen query", domain_id="alpha",
            top_k=4, peek_bridges=True,
            memory_plan={"top_k_by_lane": {"core": 1, "relational": 1, "deep": 0}},
        )

        assert result["domain_used"] == ["alpha", "beta"]
        assert result["bridge_peek_domains"] == ["gamma"]
        assert counter.calls == ["frozen query"] * 5
    finally:
        fabric.close()


def test_query_does_not_collapse_same_numeric_eid_across_private_and_shared_lanes(tmp_path):
    """The final legacy merge retains two scoped hits whose graph-local EIDs match."""
    fabric = TormentFabric(data_dir=str(tmp_path))
    try:
        workspace_id, agent_id, domain_id = "ws", "aria", "alpha"
        workspace = fabric.get_workspace(workspace_id, domains=[domain_id])
        fabric.create_agent(workspace_id, agent_id)
        vector = np.zeros(fabric.kernel.embedder.dim, dtype=np.float32)
        vector[0] = 1.0
        agent_key = fabric._agent_key(workspace_id, agent_id)
        private_eid = _add_lane_memory(
            fabric.private_graphs[agent_key], workspace_id=workspace_id,
            agent_id=agent_id, scope="private", domain_id=domain_id,
            text="private same-number memory", vector=vector,
        )
        shared_eid = _add_lane_memory(
            workspace.shared_graphs[domain_id], workspace_id=workspace_id,
            agent_id=agent_id, scope="shared", domain_id=domain_id,
            text="shared same-number memory", vector=vector,
        )
        assert private_eid == shared_eid

        result = fabric.query(
            workspace_id, agent_id, "same eid query", domain_id=domain_id,
            top_k=8,
            memory_plan={"top_k_by_lane": {"core": 1, "relational": 1, "deep": 0}},
        )
        identities = {(hit["scope"], int(hit["eid"])) for hit in result["results"]}

        assert ("private", private_eid) in identities
        assert ("shared", shared_eid) in identities
    finally:
        fabric.close()


def test_private_anchor_eid_does_not_full_boost_shared_eid_collision(tmp_path):
    """A private qualifying anchor cannot identify a same-number shared hit."""
    fabric = TormentFabric(data_dir=str(tmp_path))
    try:
        workspace_id, agent_id, domain_id = "ws", "aria", "alpha"
        workspace = fabric.get_workspace(workspace_id, domains=[domain_id])
        fabric.create_agent(workspace_id, agent_id)
        vector = np.zeros(fabric.kernel.embedder.dim, dtype=np.float32)
        vector[0] = 1.0
        agent_key = fabric._agent_key(workspace_id, agent_id)
        private_eid = _add_lane_memory(
            fabric.private_graphs[agent_key], workspace_id=workspace_id,
            agent_id=agent_id, scope="private", domain_id=domain_id,
            text="private seed canon", vector=vector, memory_type="seed_canon", canon=True,
        )
        shared_eid = _add_lane_memory(
            workspace.shared_graphs[domain_id], workspace_id=workspace_id,
            agent_id=agent_id, scope="shared", domain_id=domain_id,
            text="shared identity anchor", vector=vector,
            memory_type="identity_anchor", canon=False,
        )
        assert private_eid == shared_eid

        result = fabric.query(
            workspace_id, agent_id, "identity query", domain_id=domain_id,
            top_k=8, explain=True,
            memory_plan={"top_k_by_lane": {"core": 1, "relational": 1, "deep": 0}},
        )
        shared_hit = next(hit for hit in result["results"] if hit["scope"] == "shared")

        assert shared_hit["explain"]["self_anchor_bonus"] == 0.12 * 0.35
    finally:
        fabric.close()


def test_private_anchor_keeps_full_boost_for_same_qualified_identity(tmp_path):
    """Qualified private identity remains eligible for its own full boost."""
    fabric = TormentFabric(data_dir=str(tmp_path))
    try:
        workspace_id, agent_id, domain_id = "ws", "aria", "alpha"
        workspace = fabric.get_workspace(workspace_id, domains=[domain_id])
        fabric.create_agent(workspace_id, agent_id)
        vector = np.zeros(fabric.kernel.embedder.dim, dtype=np.float32)
        vector[0] = 1.0
        agent_key = fabric._agent_key(workspace_id, agent_id)
        eid = _add_lane_memory(
            fabric.private_graphs[agent_key], workspace_id=workspace_id,
            agent_id=agent_id, scope="private", domain_id=domain_id,
            text="private canon identity anchor", vector=vector,
            memory_type="identity_anchor", canon=True,
        )

        result = fabric.query(
            workspace_id, agent_id, "identity query", domain_id=domain_id,
            top_k=8, explain=True,
            memory_plan={"top_k_by_lane": {"core": 1, "relational": 1, "deep": 0}},
        )
        hit = next(item for item in result["results"] if int(item["eid"]) == eid)

        assert hit["explain"]["self_anchor_bonus"] == 0.12 + 0.04
    finally:
        fabric.close()


def test_private_anchor_eid_does_not_full_boost_bridge_shared_collision(tmp_path):
    """Bridge routing cannot replace a shared hit's destination-domain identity."""
    fabric = TormentFabric(data_dir=str(tmp_path))
    try:
        workspace_id, agent_id = "ws", "aria"
        workspace = fabric.get_workspace(workspace_id, domains=["alpha", "beta", "gamma"])
        fabric.create_agent(workspace_id, agent_id)
        vector = np.zeros(fabric.kernel.embedder.dim, dtype=np.float32)
        vector[0] = 1.0
        agent_key = fabric._agent_key(workspace_id, agent_id)
        private_eid = _add_lane_memory(
            fabric.private_graphs[agent_key], workspace_id=workspace_id,
            agent_id=agent_id, scope="private", domain_id="alpha",
            text="private seed canon", vector=vector, memory_type="seed_canon", canon=True,
        )
        bridge_eid = _add_lane_memory(
            workspace.shared_graphs["gamma"], workspace_id=workspace_id,
            agent_id=agent_id, scope="shared", domain_id="gamma",
            text="bridge shared identity anchor", vector=vector,
            memory_type="identity_anchor", canon=False,
        )
        assert private_eid == bridge_eid
        workspace.bridges.bridges.append(Bridge(
            from_domain="alpha", from_motif="motif-a",
            to_domain="gamma", to_motif="motif-g", confidence=1.0,
            created_ts=1, status="approved", updated_ts=1,
        ))

        result = fabric.query(
            workspace_id, agent_id, "identity bridge query", domain_id="alpha",
            top_k=8, explain=True, peek_bridges=True,
            memory_plan={"top_k_by_lane": {"core": 1, "relational": 1, "deep": 0}},
        )
        bridge_hit = next(item for item in result["results"] if item.get("via_bridge"))

        assert bridge_hit["domain_id"] == "gamma"
        assert bridge_hit["bridge_domain"] == "gamma"
        assert bridge_hit["explain"]["self_anchor_bonus"] == 0.12 * 0.35
    finally:
        fabric.close()


def test_same_string_motifs_resolve_in_each_hit_domain(tmp_path):
    """Alpha and beta same-string motifs retain their separate geometry."""
    fabric = TormentFabric(data_dir=str(tmp_path))
    try:
        workspace_id, agent_id = "ws", "aria"
        workspace = fabric.get_workspace(workspace_id, domains=["alpha", "beta"])
        fabric.create_agent(workspace_id, agent_id)
        vector = np.zeros(fabric.kernel.embedder.dim, dtype=np.float32)
        vector[0] = 1.0
        fixed, workspace = _install_fixed_embedder(fabric, workspace_id, agent_id, vector)
        now = 1
        workspace.motif_regs["alpha"].motifs["same-id"] = Motif(
            "same-id", "alpha", "alpha motif", vector.tolist(),
            1.0, [], [], 0.5, now, now,
        )
        workspace.motif_regs["beta"].motifs["same-id"] = Motif(
            "same-id", "beta", "beta motif", (-vector).tolist(),
            1.0, [], [], 0.5, now, now,
        )
        agent_key = fabric._agent_key(workspace_id, agent_id)
        alpha_eid = _add_lane_memory(
            fabric.private_graphs[agent_key], workspace_id=workspace_id,
            agent_id=agent_id, scope="private", domain_id="alpha",
            text="alpha-scoped motif memory", vector=vector,
        )
        beta_eid = _add_lane_memory(
            workspace.shared_graphs["beta"], workspace_id=workspace_id,
            agent_id=agent_id, scope="shared", domain_id="beta",
            text="beta-scoped motif memory", vector=vector,
        )
        fabric.private_graphs[agent_key].entities[alpha_eid].payload["motifs"] = ["same-id"]
        workspace.shared_graphs["beta"].entities[beta_eid].payload["motifs"] = ["same-id"]

        result = fabric.query(
            workspace_id, agent_id, "motif collision query", domain_id="alpha",
            top_k=8,
            memory_plan={"top_k_by_lane": {"core": 1, "relational": 1, "deep": 0}},
        )
        alpha_hit = next(item for item in result["results"] if item["scope"] == "private")
        beta_hit = next(item for item in result["results"] if item["scope"] == "shared")

        assert alpha_hit["motif_alignment"] == 1.0
        assert beta_hit["motif_alignment"] == 0.0

        fixed.vector = -vector
        reversed_result = fabric.query(
            workspace_id, agent_id, "motif collision reverse query", domain_id="alpha",
            top_k=8,
            memory_plan={"top_k_by_lane": {"core": 1, "relational": 1, "deep": 0}},
        )
        reversed_alpha = next(item for item in reversed_result["results"] if item["scope"] == "private")
        reversed_beta = next(item for item in reversed_result["results"] if item["scope"] == "shared")

        assert reversed_alpha["motif_alignment"] == 0.0
        assert reversed_beta["motif_alignment"] == 1.0
    finally:
        fabric.close()


def test_bridge_hit_cannot_borrow_same_string_primary_motif_centroid(tmp_path):
    """A bridge-peek hit keeps absence when its source geometry was not selected."""
    fabric = TormentFabric(data_dir=str(tmp_path))
    try:
        workspace_id, agent_id = "ws", "aria"
        workspace = fabric.get_workspace(workspace_id, domains=["alpha", "beta", "gamma"])
        fabric.create_agent(workspace_id, agent_id)
        vector = np.zeros(fabric.kernel.embedder.dim, dtype=np.float32)
        vector[0] = 1.0
        _install_fixed_embedder(fabric, workspace_id, agent_id, vector)
        now = 1
        workspace.motif_regs["alpha"].motifs["same-id"] = Motif(
            "same-id", "alpha", "alpha motif", vector.tolist(),
            1.0, [], [], 0.5, now, now,
        )
        workspace.motif_regs["gamma"].motifs["same-id"] = Motif(
            "same-id", "gamma", "gamma motif", (-vector).tolist(),
            1.0, [], [], 0.5, now, now,
        )
        bridge_eid = _add_lane_memory(
            workspace.shared_graphs["gamma"], workspace_id=workspace_id,
            agent_id=agent_id, scope="shared", domain_id="gamma",
            text="bridge motif memory", vector=vector,
        )
        workspace.shared_graphs["gamma"].entities[bridge_eid].payload["motifs"] = ["same-id"]
        workspace.bridges.bridges.append(Bridge(
            from_domain="alpha", from_motif="same-id",
            to_domain="gamma", to_motif="same-id", confidence=1.0,
            created_ts=1, status="approved", updated_ts=1,
        ))

        result = fabric.query(
            workspace_id, agent_id, "bridge motif query", domain_id="alpha",
            top_k=8, peek_bridges=True,
            memory_plan={"top_k_by_lane": {"core": 0, "relational": 1, "deep": 0}},
        )
        bridge_hit = next(item for item in result["results"] if item.get("via_bridge"))

        assert bridge_hit["domain_id"] == "gamma"
        assert bridge_hit["motif_alignment"] == 0.0
    finally:
        fabric.close()


def test_hit_without_motif_keeps_qualified_fallback_threshold_behavior(tmp_path):
    """Fallback still returns the best selected motif only at the 0.55 threshold."""
    fabric = TormentFabric(data_dir=str(tmp_path))
    try:
        workspace_id, agent_id, domain_id = "ws", "aria", "alpha"
        workspace = fabric.get_workspace(workspace_id, domains=[domain_id])
        fabric.create_agent(workspace_id, agent_id)
        vector = np.zeros(fabric.kernel.embedder.dim, dtype=np.float32)
        vector[0] = 1.0
        fixed, workspace = _install_fixed_embedder(fabric, workspace_id, agent_id, vector)
        now = 1
        workspace.motif_regs[domain_id].motifs["fallback-id"] = Motif(
            "fallback-id", domain_id, "fallback motif", vector.tolist(),
            1.0, [], [], 0.5, now, now,
        )
        agent_key = fabric._agent_key(workspace_id, agent_id)
        eid = _add_lane_memory(
            fabric.private_graphs[agent_key], workspace_id=workspace_id,
            agent_id=agent_id, scope="private", domain_id=domain_id,
            text="motif-free memory", vector=vector,
        )

        aligned = fabric.query(
            workspace_id, agent_id, "fallback aligned query", domain_id=domain_id,
            top_k=8,
            memory_plan={"top_k_by_lane": {"core": 1, "relational": 0, "deep": 0}},
        )
        aligned_hit = next(item for item in aligned["results"] if int(item["eid"]) == eid)
        assert aligned_hit["motifs"] == ["fallback-id"]
        assert aligned_hit["motif_alignment"] == 1.0

        orthogonal = np.zeros_like(vector)
        orthogonal[1] = 1.0
        fixed.vector = orthogonal
        unaligned = fabric.query(
            workspace_id, agent_id, "fallback unaligned query", domain_id=domain_id,
            top_k=8,
            memory_plan={"top_k_by_lane": {"core": 1, "relational": 0, "deep": 0}},
        )
        unaligned_hit = next(item for item in unaligned["results"] if int(item["eid"]) == eid)
        assert unaligned_hit["motifs"] == []
        assert unaligned_hit["motif_alignment"] == 0.0
    finally:
        fabric.close()
