"""tests/test_gravity_correction_runtime_conformance.py

gravity_correction runtime-conformance CHARACTERIZATION / HAZARD LOCK.

Candidate-B slice (test-only). This pack characterizes the *current*
emitted shape and gating of ``character.gravity_correction`` and locks
the known governance hazard in place as a regression barrier. It makes
**no production change** and proposes no fix.

What it pins:
  * high away-from-seed drift past threshold emits one additive
    ``drift_correction`` memory (canon=True, tier=core_identity), and
    drift within tolerance / not-away-from-seed emits nothing;
  * the emitted row is additive (the write does not rewrite or delete
    existing rows) and survives flush/reload;
  * THE HAZARD: drift-correction canon is **governance-indistinguishable
    from authored seed canon** — the protection readers treat both as
    protected, and the row carries no ``canon_source`` / source-class
    governance distinction. Only the free-text ``type`` label differs,
    and a type label is a payload flag, not writer authority.

Ratified context this lock guards against silent change of (not fixed here):
  * Seed-Governance SG-O4 (canon must be tellable by source; one boolean
    is not sufficient governance truth) and §8/§9 (drift-correction-canon
    is a distinct automatic source class; named requires-reconciliation
    seam, not patched);
  * Document A A-O1 (class-bound writer authority; payload flags such as
    ``canon`` / ``mtype`` / ``tier`` are not sufficient authority) and
    A-O5 (existing automatic writers are named unreconciled seams);
  * N14 gravity_correction Automatic-Canon Audit-First Reconciliation.

If a later, separately-authorized slice introduces a canon-source
distinction or a writer-authority gate, the HAZARD-LOCK test below is
expected to change deliberately — that is the signal, not a surprise.

In-process pattern (mirrors test_character_q2d_regression.py): MemoryGraph
against a tmpdir + HashEmbedding; no TORMENT server start; no real API
calls; payloads inspected directly off ``graph.entities``.
"""
from __future__ import annotations

import os
import sys
import tempfile
from typing import Any, Dict

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.compression import derive_retention_tier
from torment_service.governance import is_compression_protected


# ---------------------------------------------------------------------------
# Local builders (same shape as test_character_q2d_regression.py)
# ---------------------------------------------------------------------------


def _build_minimal_graph_env() -> Dict[str, Any]:
    memory_graph = pytest.importorskip("torment_service.memory_graph")
    motifs = pytest.importorskip("torment_service.motifs")
    embeddings = pytest.importorskip("torment_service.embeddings")
    MemoryGraph = memory_graph.MemoryGraph
    MotifRegistry = motifs.MotifRegistry
    HashEmbedding = embeddings.HashEmbedding

    tmpdir = tempfile.mkdtemp(prefix="torment_gravity_conformance_")
    embedder = HashEmbedding(dim=8)
    graph = MemoryGraph(tmpdir, embedder=embedder)
    motif_registry = MotifRegistry(
        data_dir=tmpdir,
        workspace_id="gravity_test_ws",
        domain_id="gravity_test_domain",
    )
    return {
        "tmpdir": tmpdir,
        "graph": graph,
        "motif_registry": motif_registry,
        "embedder": embedder,
    }


def _make_seed():
    """Minimal CharacterSeed. seed_motif_id left empty so the optional
    motif-attach branch in gravity_correction is skipped (keeps this
    characterization free of motif-clustering coupling)."""
    character = pytest.importorskip("torment_service.character")
    return character.CharacterSeed(
        seed_id="gravity_test_v1",
        character_name="Gravity Test Character",
        seed_text=(
            "A controlled fixture for gravity-correction characterization. "
            "Identity rooted in clarity. Persistent across sessions."
        ),
        core_half_life=3650.0,
        seed_motif_id="",
    )


def _call_gravity_correction(env, seed, drift_info, step=100):
    character = pytest.importorskip("torment_service.character")
    return character.gravity_correction(
        graph=env["graph"],
        motif_registry=env["motif_registry"],
        embedder=env["embedder"],
        seed=seed,
        agent_id="gravity_test_agent",
        step=step,
        drift_info=drift_info,
    )


def _high_away_drift() -> Dict[str, Any]:
    # drift_score < -drift_correction_threshold (default 0.35) AND away_seed
    return {"drift_score": -0.9, "drift_direction": "away_seed"}


def _within_tolerance_drift() -> Dict[str, Any]:
    # drift_score > -threshold -> gated out as "drift within tolerance"
    return {"drift_score": -0.1, "drift_direction": "away_seed"}


def _not_away_drift() -> Dict[str, Any]:
    # past threshold but not away_seed -> gated out as "not drifting away"
    return {"drift_score": -0.9, "drift_direction": "toward_seed"}


# ===========================================================================
# PHASE 1 — emitted shape on high away-from-seed drift
# ===========================================================================


def test_high_away_seed_drift_emits_correction():
    env = _build_minimal_graph_env()
    seed = _make_seed()
    result = _call_gravity_correction(env, seed, _high_away_drift())

    assert result["correction_applied"] is True
    assert "correction_eid" in result
    assert isinstance(result["correction_eid"], int)


def test_emitted_memory_mtype_is_drift_correction():
    env = _build_minimal_graph_env()
    seed = _make_seed()
    result = _call_gravity_correction(env, seed, _high_away_drift())
    payload = env["graph"].entities[result["correction_eid"]].payload

    assert payload["type"] == "drift_correction"


def test_emitted_memory_is_canon_true():
    env = _build_minimal_graph_env()
    seed = _make_seed()
    result = _call_gravity_correction(env, seed, _high_away_drift())
    payload = env["graph"].entities[result["correction_eid"]].payload

    assert payload["canon"] is True


def test_emitted_payload_reflects_core_identity_and_seed_correction_facts():
    env = _build_minimal_graph_env()
    seed = _make_seed()
    result = _call_gravity_correction(env, seed, _high_away_drift(), step=100)
    payload = env["graph"].entities[result["correction_eid"]].payload

    # tier + seed correction provenance facts already present today.
    assert payload.get("tier") == "core_identity"
    assert payload.get("seed_id") == "gravity_test_v1"
    assert payload.get("corrects_drift_score") == pytest.approx(-0.9)
    assert payload.get("corrects_at_step") == 100


# ===========================================================================
# PHASE 2 — gating (no emission when not high-away-from-seed)
# ===========================================================================


def test_drift_within_tolerance_does_not_emit():
    env = _build_minimal_graph_env()
    seed = _make_seed()
    result = _call_gravity_correction(env, seed, _within_tolerance_drift())

    assert result["correction_applied"] is False
    assert result.get("reason") == "drift within tolerance"


def test_drift_not_away_from_seed_does_not_emit():
    env = _build_minimal_graph_env()
    seed = _make_seed()
    result = _call_gravity_correction(env, seed, _not_away_drift())

    assert result["correction_applied"] is False
    assert result.get("reason") == "not drifting away"


# ===========================================================================
# PHASE 3 — additive (no rewrite/delete) + flush/reload persistence
# ===========================================================================


def _spawn_baseline_row(graph, embedder) -> int:
    text = "An ordinary baseline memory present before any correction."
    emb = embedder.embed(text)
    return graph.spawn_memory(
        summary=text,
        embedding=emb,
        mtype="episode",
        strength=0.5,
        confidence=0.5,
        half_life_days=30.0,
        canon=False,
        user_id="gravity_test_agent",
        step=0,
    )


def test_correction_is_additive_not_rewrite():
    env = _build_minimal_graph_env()
    seed = _make_seed()
    graph = env["graph"]

    baseline_eid = _spawn_baseline_row(graph, env["embedder"])
    baseline_before = dict(graph.entities[baseline_eid].payload)
    count_before = len(graph.entities)

    result = _call_gravity_correction(env, seed, _high_away_drift())

    # New row added; baseline row neither deleted nor mutated.
    assert result["correction_applied"] is True
    assert result["correction_eid"] != baseline_eid
    assert len(graph.entities) == count_before + 1
    assert baseline_eid in graph.entities
    assert graph.entities[baseline_eid].payload == baseline_before


def test_correction_persists_through_flush_and_reload():
    memory_graph = pytest.importorskip("torment_service.memory_graph")
    embeddings = pytest.importorskip("torment_service.embeddings")
    MemoryGraph = memory_graph.MemoryGraph
    HashEmbedding = embeddings.HashEmbedding
    motifs = pytest.importorskip("torment_service.motifs")
    MotifRegistry = motifs.MotifRegistry

    tmpdir = tempfile.mkdtemp(prefix="torment_gravity_persist_")
    embedder = HashEmbedding(dim=8)
    graph_a = MemoryGraph(tmpdir, embedder=embedder)
    motif_registry = MotifRegistry(
        data_dir=tmpdir, workspace_id="gw", domain_id="gd"
    )
    seed = _make_seed()

    character = pytest.importorskip("torment_service.character")
    result = character.gravity_correction(
        graph=graph_a,
        motif_registry=motif_registry,
        embedder=embedder,
        seed=seed,
        agent_id="gravity_test_agent",
        step=100,
        drift_info=_high_away_drift(),
    )
    eid = result["correction_eid"]

    # gravity_correction calls graph.flush_node(eid); reload sees it.
    graph_b = MemoryGraph(tmpdir, embedder=embedder)
    ent = graph_b.entities.get(eid)
    assert ent is not None, "drift_correction row did not rehydrate"
    assert ent.payload["type"] == "drift_correction"
    assert ent.payload["canon"] is True


# ===========================================================================
# PHASE 4 — HAZARD LOCK
#
# drift-correction canon is governance-INDISTINGUISHABLE from authored
# seed canon. This pins the current state named by Seed-Gov SG-O4 /
# Document A A-O1 / N14. A deliberate future fix should change this test
# on purpose.
# ===========================================================================


def _spawn_seed_canon_row(graph, embedder) -> int:
    """Authored seed-canon row, same canon-governance shape plant_seed
    produces (mirrors test_character_q2d_regression._spawn_minimal_seed_row).
    """
    concept = "Identity rooted in clarity."
    emb = embedder.embed(concept)
    return graph.spawn_memory(
        summary=concept,
        embedding=emb,
        mtype="seed_canon",
        strength=0.95,
        confidence=0.95,
        half_life_days=3650.0,
        canon=True,
        user_id="gravity_test_agent",
        step=0,
        extra_payload={
            "seed_id": "gravity_test_v1",
            "tier": "core_identity",
        },
    )


def test_drift_correction_canon_not_governance_distinguishable_from_seed_canon():
    env = _build_minimal_graph_env()
    seed = _make_seed()
    graph = env["graph"]

    seed_eid = _spawn_seed_canon_row(graph, env["embedder"])
    result = _call_gravity_correction(env, seed, _high_away_drift())
    drift_eid = result["correction_eid"]

    seed_payload = graph.entities[seed_eid].payload
    drift_payload = graph.entities[drift_eid].payload

    # Both are canon.
    assert seed_payload["canon"] is True
    assert drift_payload["canon"] is True

    # The protection readers treat the automatic drift-correction canon
    # IDENTICALLY to authored seed canon — they cannot tell the source apart.
    assert is_compression_protected(seed_payload) is True
    assert is_compression_protected(drift_payload) is True
    assert derive_retention_tier(seed_payload) == derive_retention_tier(drift_payload)

    # No governance source-class field distinguishes the automatic canon.
    # (Seed-Gov SG-O4: "v0.1 selects no storage representation/field/schema"
    # for canon-by-source — so there is nothing to distinguish them by.)
    assert "canon_source" not in drift_payload
    assert "canon_source" not in seed_payload

    # The ONLY difference is the free-text ``type`` label, which Document A
    # A-O1 classifies as a payload flag, not writer authority.
    assert drift_payload["type"] == "drift_correction"
    assert seed_payload["type"] == "seed_canon"
