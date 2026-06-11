"""tests/test_character_q2d_regression.py

Q2-D character/agent regression pack.

Proves the Q2-D soft-migration arc (Slices 1 through 5-c) did not
break the character authoring flow. Specifically, proves that:

  * a character seed planted through ``character.plant_seed`` produces
    payloads that flow correctly through every soft-migrated protected
    reader (``is_compression_protected``, ``derive_retention_tier``,
    ``CompressionScorer._is_protected``)
  * ordinary memory rows continue to be non-protected
  * disagreements are operator-visible without disrupting the
    character flow itself
  * external inference modules (``live_agent.inference``) still import
    cleanly after the Q2-D imports were added

This is a local pytest pack. NO real Anthropic/OpenRouter/Gemini API
calls are made -- those belong in a manual operator script
(see future ``tests/run_external_inference_smoke.py``).

In-process pattern (no TORMENT server start):
  * ``MemoryGraph`` constructed against a tmpdir
  * Optionally ``character.plant_seed`` invoked with a minimal seed
  * Payloads inspected directly off ``graph.entities``
  * Readers invoked directly on payloads

Out of scope for this pack (and these tests):

  * full TORMENT server start
  * Slice 6 hard migration
  * removal of legacy fallback
  * autonomy loops
  * external API round-trips
  * baton/R3, review-queue, closure-ledger, Q3, custom DB
"""
from __future__ import annotations

import copy
import logging
import os
import sys
import tempfile
import time
from typing import Any, Dict, List, Optional

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


from torment_service.compression import (
    CompressionScorer,
    derive_retention_tier,
)
from torment_service.governance import is_compression_protected
from torment_service.lifecycle import (
    LifecycleActor,
    LifecycleJoinTarget,
    LifecycleSetBy,
    LifecycleSetVia,
    LifecycleState,
    LifecycleStatus,
    SideChannel,
    detect_lifecycle_legacy_marker_disagreement,
    read_lifecycle_envelope,
)


FIXED_AT = 1_716_300_000


# ---------------------------------------------------------------------------
# Local test builders
# ---------------------------------------------------------------------------


def _minimal_character_seed():
    """Construct a minimal CharacterSeed for testing. Mirrors the shape
    used in test_character_selfstate.py.
    """
    character = pytest.importorskip("torment_service.character")
    CharacterSeed = character.CharacterSeed
    return CharacterSeed(
        seed_id="q2d_test_v1",
        character_name="Q2D Test Character",
        seed_text=(
            "A controlled test fixture for Q2-D regression. "
            "Identity rooted in clarity. Persistent across sessions."
        ),
        core_half_life=3650.0,  # default ~10 years
    )


def _build_minimal_graph_env():
    """Build the minimum dependencies plant_seed needs:
    MemoryGraph, MotifRegistry, CoherenceField, HashEmbedding.
    Returns dict of components so tests can inject the same env into
    plant_seed and inspect afterward.
    """
    try:
        from torment_service.memory_graph import MemoryGraph
        from torment_service.motifs import MotifRegistry
        from torment_service.coherence_field import CoherenceField
        from torment_service.embeddings import HashEmbedding
    except ImportError as exc:
        pytest.skip(f"graph/motif deps unavailable: {exc}")

    tmpdir = tempfile.mkdtemp(prefix="torment_q2d_char_")
    embedder = HashEmbedding(dim=8)
    graph = MemoryGraph(tmpdir, embedder=embedder)
    motif_registry = MotifRegistry(
        data_dir=tmpdir,
        workspace_id="q2d_test_ws",
        domain_id="q2d_test_domain",
    )
    coherence_field = CoherenceField([])  # empty motif corpus is fine
    return {
        "tmpdir": tmpdir,
        "graph": graph,
        "motif_registry": motif_registry,
        "coherence_field": coherence_field,
        "embedder": embedder,
    }


def _spawn_minimal_seed_row(graph, embedder) -> int:
    """Direct ``spawn_memory`` call replicating the EXACT payload shape
    ``character.plant_seed`` produces for one seed concept. Used by
    tests that want to validate the lifecycle-stamp contract without
    the full motif-clustering / coherence-field overhead of plant_seed
    itself.
    """
    import numpy as np
    concept = "Identity rooted in clarity."
    emb = embedder.embed(concept)
    return graph.spawn_memory(
        summary=concept,
        embedding=emb,
        mtype="seed_canon",
        strength=0.95,
        confidence=0.95,
        half_life_days=3650.0,
        canon=True,                    # ← THE legacy protected marker
        user_id="q2d_test_agent",
        step=0,
        extra_payload={
            "seed_id": "q2d_test_v1",
            "character_name": "Q2D Test Character",
            "tier": "core_identity",   # ← also a legacy protected marker
            "seed_concept_index": 0,
        },
    )


# ===========================================================================
# PHASE 1 -- Static character seed lifecycle (keystone)
#
# The most important phase: a character seed planted through the canonical
# path produces rows whose lifecycle envelope flows correctly through every
# Q2-D-migrated reader.
# ===========================================================================


def test_seed_row_carries_protected_lifecycle_envelope_via_direct_spawn():
    """KEYSTONE: a single seed concept written via spawn_memory with the
    EXACT payload shape plant_seed uses produces a row whose
    lifecycle_status envelope is PROTECTED / SYSTEM / CANON_SET.

    This is the regression test that proves Q2-D Slice 3 (H1c
    write-side stamping) correctly handles character-seed-shape
    payloads. If this fails, every character seed write is broken.
    """
    env = _build_minimal_graph_env()
    eid = _spawn_minimal_seed_row(env["graph"], env["embedder"])
    payload = env["graph"].entities[eid].payload

    assert "lifecycle_status" in payload, "H1c did not stamp envelope"
    envelope = payload["lifecycle_status"]
    assert envelope["state"] == "protected", (
        f"seed row should be PROTECTED; got {envelope['state']!r}"
    )
    assert envelope["is_authoritative_on_row"] is True
    assert envelope["requires_join"] is None
    assert envelope["history_ref"] is None
    assert envelope["set_by"]["actor"] == "system", (
        "Slice 3 write-time actor must be SYSTEM (not MIGRATION)"
    )
    # CANON_SET wins by precedence over TIER_SET (Slice 1 derivation order).
    assert envelope["set_by"]["via"] == "canon_set"
    assert isinstance(envelope["set_by"]["at"], int)


def test_seed_row_has_no_disagreement():
    """The H1c stamp on a freshly-planted seed should be in full
    agreement with what Slice 1's derivation helper would produce for
    the same payload's legacy markers. No disagreement = no warning
    log clutter, no operator alarm, no soft-fallback path triggered.
    """
    env = _build_minimal_graph_env()
    eid = _spawn_minimal_seed_row(env["graph"], env["embedder"])
    payload = env["graph"].entities[eid].payload

    disagreement = detect_lifecycle_legacy_marker_disagreement(payload)
    assert disagreement is None, (
        f"seed row should not produce a disagreement; got {disagreement!r}"
    )


def test_is_compression_protected_returns_true_for_seed_row():
    """Slice 5 reader: a freshly-planted seed row reads as protected
    via the lifecycle path's direct True branch.
    """
    env = _build_minimal_graph_env()
    eid = _spawn_minimal_seed_row(env["graph"], env["embedder"])
    payload = env["graph"].entities[eid].payload

    assert is_compression_protected(payload) is True


def test_derive_retention_tier_returns_protected_for_seed_row():
    """Slice 5-b reader: derive_retention_tier returns 'protected'."""
    env = _build_minimal_graph_env()
    eid = _spawn_minimal_seed_row(env["graph"], env["embedder"])
    payload = env["graph"].entities[eid].payload

    assert derive_retention_tier(payload) == "protected"


def test_compression_scorer_is_protected_returns_true_for_seed_row():
    """Slice 5-c reader: scorer._is_protected returns True."""
    env = _build_minimal_graph_env()
    eid = _spawn_minimal_seed_row(env["graph"], env["embedder"])
    payload = env["graph"].entities[eid].payload

    scorer = CompressionScorer()
    assert scorer._is_protected(payload) is True


def test_seed_row_through_full_plant_seed_path():
    """End-to-end with the REAL plant_seed function (not just a
    spawn_memory shape replica). Exercises motif clustering +
    coherence + the full character authoring path.

    plant_seed writes one row per concept (split from seed_text).
    Every resulting row must carry the PROTECTED envelope.
    """
    try:
        from torment_service.character import plant_seed
    except ImportError as exc:
        pytest.skip(f"character.plant_seed unavailable: {exc}")

    env = _build_minimal_graph_env()
    seed = _minimal_character_seed()
    planted = plant_seed(
        graph=env["graph"],
        motif_registry=env["motif_registry"],
        coherence_field=env["coherence_field"],
        embedder=env["embedder"],
        seed=seed,
        agent_id="q2d_test_agent",
        step=0,
    )

    # plant_seed mutates the seed object with the populated eids.
    assert planted.seed_eids, "plant_seed did not populate seed_eids"

    # Every planted row carries the PROTECTED envelope at SYSTEM/CANON_SET.
    for eid in planted.seed_eids:
        payload = env["graph"].entities[eid].payload
        assert "lifecycle_status" in payload
        envelope = payload["lifecycle_status"]
        assert envelope["state"] == "protected"
        assert envelope["set_by"]["actor"] == "system"
        assert envelope["set_by"]["via"] == "canon_set"
        # And each row reads as protected through all three readers.
        assert is_compression_protected(payload) is True
        assert derive_retention_tier(payload) == "protected"
        assert CompressionScorer()._is_protected(payload) is True


def test_seed_row_persists_protected_through_flush_and_reload():
    """Disk round-trip: spawn seed row → flush_node → reload from a
    fresh MemoryGraph instance → the PROTECTED envelope is intact.
    """
    try:
        from torment_service.memory_graph import MemoryGraph
        from torment_service.embeddings import HashEmbedding
    except ImportError as exc:
        pytest.skip(f"memory_graph deps unavailable: {exc}")

    tmpdir = tempfile.mkdtemp(prefix="torment_q2d_char_persist_")
    embedder = HashEmbedding(dim=8)

    graph_a = MemoryGraph(tmpdir, embedder=embedder)
    eid = _spawn_minimal_seed_row(graph_a, embedder)
    graph_a.flush_node(eid)
    env_before = dict(graph_a.entities[eid].payload["lifecycle_status"])
    assert env_before["state"] == "protected"

    # Reload from disk.
    graph_b = MemoryGraph(tmpdir, embedder=embedder)
    ent = graph_b.entities.get(eid)
    assert ent is not None, "seed row did not rehydrate"
    env_after = ent.payload.get("lifecycle_status")
    assert env_after == env_before, "envelope corrupted across reload"

    # Readers still return True on the reloaded payload.
    assert is_compression_protected(ent.payload) is True
    assert derive_retention_tier(ent.payload) == "protected"


# ===========================================================================
# PHASE 2 -- Ordinary memory stays ordinary
#
# Catches the failure mode "Q2-D accidentally made ordinary character
# memories look protected." Non-seed, non-canon rows must remain
# non-protected across all three readers.
# ===========================================================================


def _spawn_ordinary_row(graph, embedder, half_life_days: float = 30.0) -> int:
    """Spawn a non-protected ordinary memory row. Mirrors a typical
    user-text ingest at the spawn_memory layer.
    """
    import numpy as np
    text = "An ordinary conversational memory with no protected markers."
    emb = embedder.embed(text)
    return graph.spawn_memory(
        summary=text,
        embedding=emb,
        mtype="episode",
        strength=0.5,
        confidence=0.5,
        half_life_days=half_life_days,
        canon=False,
        user_id="q2d_test_agent",
        step=0,
    )


def test_ordinary_memory_has_unset_envelope():
    """Ordinary memory row has the canonical H1c UNSET envelope."""
    env = _build_minimal_graph_env()
    eid = _spawn_ordinary_row(env["graph"], env["embedder"])
    payload = env["graph"].entities[eid].payload

    assert "lifecycle_status" in payload
    envelope = payload["lifecycle_status"]
    assert envelope["state"] == "unset"
    assert envelope["is_authoritative_on_row"] is True
    assert envelope["set_by"]["actor"] == "system"
    assert envelope["set_by"]["via"] == "ingest_unmarked"


def test_ordinary_memory_is_not_compression_protected():
    """Slice 5 reader: ordinary memory is NOT compression-protected."""
    env = _build_minimal_graph_env()
    eid = _spawn_ordinary_row(env["graph"], env["embedder"])
    payload = env["graph"].entities[eid].payload

    assert is_compression_protected(payload) is False


def test_ordinary_memory_tier_is_not_protected():
    """Slice 5-b reader: ordinary memory's tier is half_life-based,
    not 'protected'. With half_life=30 -> "relational".
    """
    env = _build_minimal_graph_env()
    eid = _spawn_ordinary_row(env["graph"], env["embedder"], half_life_days=30.0)
    payload = env["graph"].entities[eid].payload

    tier = derive_retention_tier(payload)
    assert tier != "protected", (
        f"ordinary memory tier should not be 'protected'; got {tier!r}"
    )
    assert tier == "relational"


def test_ordinary_memory_scorer_is_not_protected():
    """Slice 5-c reader: scorer says ordinary memory is not protected."""
    env = _build_minimal_graph_env()
    eid = _spawn_ordinary_row(env["graph"], env["embedder"])
    payload = env["graph"].entities[eid].payload

    scorer = CompressionScorer()
    assert scorer._is_protected(payload) is False


def test_ordinary_memory_has_no_disagreement():
    """Sanity: a freshly-stamped ordinary row should not produce a
    Slice 4 disagreement (the H1c stamp matches what derivation says
    for a no-marker row: nothing).
    """
    env = _build_minimal_graph_env()
    eid = _spawn_ordinary_row(env["graph"], env["embedder"])
    payload = env["graph"].entities[eid].payload

    disagreement = detect_lifecycle_legacy_marker_disagreement(payload)
    assert disagreement is None


# ===========================================================================
# PHASE 3 -- Deliberate disagreement fixture
#
# Synthesizes a payload that combines explicit envelope + legacy markers
# in conflict. Verifies operator visibility through the disagreement
# detector and the soft-fallback warning behavior. Kept isolated;
# disagreements are NOT a normal part of the character flow.
# ===========================================================================


def _explicit_released_envelope() -> Dict[str, Any]:
    return LifecycleStatus(
        state=LifecycleState.RELEASED,
        is_authoritative_on_row=True,
        requires_join=None,
        set_by=LifecycleSetBy(
            actor=LifecycleActor.OPERATOR,
            via=LifecycleSetVia.RELEASE_PROMOTION,
            at=FIXED_AT,
        ),
        history_ref=None,
    ).to_dict()


def test_deliberate_disagreement_payload_detected():
    """A synthesized payload combining explicit RELEASED envelope with
    canon=True legacy marker. Slice 4 detector should report
    STATE_MISMATCH.
    """
    payload = {
        "lifecycle_status": _explicit_released_envelope(),
        "canon": True,
        "summary": "synthesized disagreement fixture",
    }
    result = detect_lifecycle_legacy_marker_disagreement(payload)
    assert result is not None
    assert result.kind.value == "state_mismatch"
    assert result.explicit_state.value == "released"
    assert result.derived_via.value == "canon_set"


def test_deliberate_disagreement_surfaces_in_h1b_inspector_helper():
    """The H1b/Slice 4-wiring-A inspector helper for resource_provenance
    surfaces the disagreement as a structured dict on the row.
    """
    mcp_server = pytest.importorskip("torment_service.mcp_server")
    _lifecycle_disagreement_field_for_payload = (
        mcp_server._lifecycle_disagreement_field_for_payload
    )

    payload = {
        "lifecycle_status": _explicit_released_envelope(),
        "canon": True,
    }
    field = _lifecycle_disagreement_field_for_payload(payload)
    assert field is not None
    assert field["kind"] == "state_mismatch"
    assert field["explicit_state"] == "released"


def test_disagreement_payload_falls_back_to_legacy_with_warning(caplog):
    """Slice 5 reader on the same disagreement payload: lifecycle path
    declines (disagreement detected → warning logged → None), legacy
    fallback runs (gov.protected not set → False). Final answer is
    False (legacy default), and a WARNING log was emitted.
    """
    payload = {
        "lifecycle_status": _explicit_released_envelope(),
        "canon": True,
    }
    with caplog.at_level(logging.WARNING, logger="torment.governance"):
        result = is_compression_protected(payload)
    # Final answer: legacy fallback returns False (canon isn't a
    # governance flag; resolve_governance().protected is False).
    assert result is False
    # A Slice 5 warning was emitted.
    assert any(
        "Q2-D Slice 5" in r.getMessage()
        and "state_mismatch" in r.getMessage()
        for r in caplog.records
    )


def test_disagreement_payload_falls_back_in_derive_retention_tier(caplog):
    """Slice 5-b reader on the same disagreement payload: falls back
    to legacy protected branch, which sees canon=True and returns
    'protected'. Warning is emitted.
    """
    payload = {
        "lifecycle_status": _explicit_released_envelope(),
        "canon": True,
    }
    with caplog.at_level(logging.WARNING, logger="torment_service.compression"):
        result = derive_retention_tier(payload)
    assert result == "protected"
    assert any(
        "Q2-D" in r.getMessage()
        and "derive_retention_tier" in r.getMessage()
        for r in caplog.records
    )


# ===========================================================================
# PHASE 4 -- External inference import smoke
#
# No real API calls. Purely regression — proves Q2-D's lifecycle imports
# didn't break the live_agent.inference module's transitive import graph.
# ===========================================================================


def test_live_agent_inference_module_imports():
    """``live_agent.inference`` imports cleanly. If Q2-D introduced a
    transitive import problem, this fails loud at module load.
    """
    try:
        from live_agent import inference  # noqa: F401
    except ImportError as exc:
        pytest.fail(
            f"live_agent.inference failed to import after Q2-D: {exc}"
        )


def test_claude_inference_class_resolves_without_instantiation():
    """The ClaudeInference symbol resolves without crashing. We
    explicitly do NOT instantiate it (instantiation may want a real
    API key + may probe the network). Just confirms the class
    definition survived Q2-D's import changes.
    """
    try:
        from live_agent.inference import ClaudeInference
    except ImportError as exc:
        pytest.fail(
            f"live_agent.inference.ClaudeInference unavailable: {exc}"
        )
    # Sanity: the class is a class.
    assert isinstance(ClaudeInference, type)


def test_memory_bridge_module_imports():
    """The memory_bridge module (which any external-inference flow
    eventually consults to write/read TORMENT memory) imports cleanly
    after the Q2-D changes.
    """
    try:
        from live_agent import memory_bridge  # noqa: F401
    except ImportError as exc:
        pytest.fail(
            f"live_agent.memory_bridge failed to import after Q2-D: {exc}"
        )
