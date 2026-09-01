"""7G5E4E-A0 characterization locks for the current Fabric query boundary.

These tests do not select native retrieval.  They record the observable
legacy call and identity laws that a later backend-neutral retrieval seam must
preserve (or explicitly repair in a separately authorized compatibility
change).
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


def _install_counting_embedder(fabric: TormentFabric, workspace_id: str, agent_id: str):
    counter = _CountingEmbedder(fabric.kernel.embedder)
    fabric.embedder = counter
    fabric.kernel.embedder = counter
    workspace = fabric.get_workspace(workspace_id)
    agent_key = fabric._agent_key(workspace_id, agent_id)
    for graph in (fabric.private_graphs[agent_key], *workspace.shared_graphs.values()):
        graph.embedder = counter
    return counter, workspace


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


def test_characterization_bare_eid_anchor_boost_crosses_private_shared_scope(tmp_path):
    """Record the outstanding query-scoring collision for the A0 blocker.

    ``anchor_full_boost_eids`` is a bare integer set.  A private seed-canon
    and a shared non-canon identity anchor with the same graph-local EID make
    the shared hit receive the full 0.12 anchor boost.  This is not final-merge
    deduplication, but it is an unsafe cross-scope query identity use.
    """
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

        assert shared_hit["explain"]["self_anchor_bonus"] == 0.12
    finally:
        fabric.close()


def test_characterization_flat_motif_id_lookup_crosses_selected_domain_scope(tmp_path):
    """Record the second A0 namespace blocker in motif-alignment scoring.

    Query builds one centroid map keyed only by ``motif_id``.  With the same
    runtime motif ID in alpha and beta, the later selected beta centroid
    overwrites alpha's centroid, even for an alpha-scoped hit.
    """
    fabric = TormentFabric(data_dir=str(tmp_path))
    try:
        workspace_id, agent_id = "ws", "aria"
        workspace = fabric.get_workspace(workspace_id, domains=["alpha", "beta"])
        fabric.create_agent(workspace_id, agent_id)
        counter, workspace = _install_counting_embedder(fabric, workspace_id, agent_id)
        vector = np.zeros(counter.dim, dtype=np.float32)
        vector[0] = 1.0
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
        eid = _add_lane_memory(
            fabric.private_graphs[agent_key], workspace_id=workspace_id,
            agent_id=agent_id, scope="private", domain_id="alpha",
            text="alpha-scoped motif memory", vector=vector,
        )
        fabric.private_graphs[agent_key].entities[eid].payload["motifs"] = ["same-id"]

        result = fabric.query(
            workspace_id, agent_id, "motif collision query", domain_id="alpha",
            top_k=8,
            memory_plan={"top_k_by_lane": {"core": 1, "relational": 0, "deep": 0}},
        )
        hit = next(item for item in result["results"] if int(item["eid"]) == eid)

        # The alpha centroid is exactly aligned with the query.  The observed
        # zero proves beta's same-string motif ID overwrote it in the flat map.
        assert hit["motif_alignment"] == 0.0
    finally:
        fabric.close()
