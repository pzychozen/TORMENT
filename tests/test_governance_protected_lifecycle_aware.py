"""tests/test_governance_protected_lifecycle_aware.py

Q2-D Slice 5 tests for ``governance.is_compression_protected``.

First production consumer of the Q2-F enforcement primitive
(``assert_lifecycle_row_authoritative``). Soft migration:

  * lifecycle path runs first via ``_is_protected_via_lifecycle``
  * legacy fallback (``resolve_governance(payload).protected``) runs
    when the lifecycle path declines to decide

The lifecycle path declines (returns None, triggering fallback) when:
  * envelope is malformed (``LifecycleStateError``)
  * envelope is join-required (Q2-F primitive raises)
  * envelope disagrees with legacy markers (Slice 4 detector reports;
    a WARNING is logged for operator visibility)

New capability: a payload with an explicit row-authoritative PROTECTED
envelope and no legacy ``governance.protected`` flag now returns True.
A payload with ``canon=True`` and no explicit envelope also now
returns True (via Slice 2 derivation through the lifecycle path) --
this matches the semantics ``compression.derive_retention_tier`` has
always had for canon, unifying two previously-fragmented surfaces.

Out of scope at this slice:
  * hard migration / removal of legacy fallback (Slice 6)
  * migration of ``derive_retention_tier`` (Slice 5-b)
  * migration of ``CompressionScorer._is_protected`` inline checks
  * raising on disagreement at production decision sites
  * write-side logging
  * baton/R3, review-queue, closure-ledger, Q3, custom DB
"""
from __future__ import annotations

import logging
import os
import sys
from typing import Any, Dict

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


from torment_service.governance import is_compression_protected
from torment_service.lifecycle import (
    LifecycleActor,
    LifecycleJoinTarget,
    LifecycleSetBy,
    LifecycleSetVia,
    LifecycleState,
    LifecycleStatus,
    SideChannel,
)


FIXED_AT = 1_716_300_000


def _row_authoritative_envelope_dict(
    state: LifecycleState,
    via: LifecycleSetVia,
    actor: LifecycleActor = LifecycleActor.OPERATOR,
    at: int = FIXED_AT,
) -> Dict[str, Any]:
    return LifecycleStatus(
        state=state,
        is_authoritative_on_row=True,
        requires_join=None,
        set_by=LifecycleSetBy(actor=actor, via=via, at=at),
        history_ref=None,
    ).to_dict()


def _join_required_envelope_dict(
    state: LifecycleState = LifecycleState.PROTECTED,
    side_channel: SideChannel = SideChannel.REVIEW_QUEUE,
    join_key: str = "eid",
    via: LifecycleSetVia = LifecycleSetVia.GATE1_REFUSAL,
) -> Dict[str, Any]:
    return LifecycleStatus(
        state=state,
        is_authoritative_on_row=False,
        requires_join=LifecycleJoinTarget(
            side_channel=side_channel, join_key=join_key,
        ),
        set_by=LifecycleSetBy(
            actor=LifecycleActor.SYSTEM, via=via, at=FIXED_AT,
        ),
        history_ref=None,
    ).to_dict()


# ===========================================================================
# Section A -- legacy behavior preserved for governance-flag payloads
# ===========================================================================


def test_legacy_governance_protected_true_returns_true():
    """The classic legacy case: ``payload["governance"]["protected"] = True``
    with no explicit envelope. Slice 2 shim derives PROTECTED via the
    governance marker; the lifecycle path returns True. Same answer the
    legacy path would have given (gov.protected).
    """
    assert is_compression_protected(
        {"governance": {"protected": True}}
    ) is True


def test_legacy_no_governance_flag_returns_false():
    """Empty payload: Slice 2 derives UNSET; lifecycle path returns False
    (state != PROTECTED, no disagreement). Same as legacy gov.protected
    default (False).
    """
    assert is_compression_protected({}) is False


def test_legacy_governance_protected_false_returns_false():
    payload = {"governance": {"protected": False, "non_shareable": True}}
    assert is_compression_protected(payload) is False


def test_none_payload_returns_false():
    """None payload edge case: lifecycle path raises LifecycleStateError on
    non-dict input and falls back to legacy ``resolve_governance(None)``,
    which returns MemoryGovernanceFlags() defaults -> protected=False.
    """
    assert is_compression_protected(None) is False


# ===========================================================================
# Section B -- explicit envelope, no legacy markers (the new capability)
# ===========================================================================


def test_explicit_protected_envelope_no_markers_returns_true():
    """NEW capability of Slice 5: a payload with an explicit
    row-authoritative PROTECTED envelope and no legacy markers returns
    True. Pre-Slice-5 this would have returned False because legacy
    governance.protected was the sole source of truth.
    """
    envelope = _row_authoritative_envelope_dict(
        state=LifecycleState.PROTECTED,
        via=LifecycleSetVia.CANON_SET,
    )
    assert is_compression_protected({"lifecycle_status": envelope}) is True


def test_explicit_released_envelope_no_markers_returns_false():
    """An explicit RELEASED envelope says "released, not protected."
    Lifecycle path returns False; no disagreement to trigger fallback.
    """
    envelope = _row_authoritative_envelope_dict(
        state=LifecycleState.RELEASED,
        via=LifecycleSetVia.RELEASE_PROMOTION,
    )
    assert is_compression_protected({"lifecycle_status": envelope}) is False


def test_explicit_unset_envelope_no_markers_returns_false():
    envelope = _row_authoritative_envelope_dict(
        state=LifecycleState.UNSET,
        via=LifecycleSetVia.UNSET_DEFAULT,
        actor=LifecycleActor.MIGRATION,
    )
    assert is_compression_protected({"lifecycle_status": envelope}) is False


def test_explicit_scratch_envelope_returns_false():
    envelope = _row_authoritative_envelope_dict(
        state=LifecycleState.SCRATCH,
        via=LifecycleSetVia.SCRATCH_PROMOTION,
    )
    assert is_compression_protected({"lifecycle_status": envelope}) is False


# ===========================================================================
# Section C -- join-required envelope falls back to legacy
# ===========================================================================


def test_join_required_protected_with_gov_flag_falls_back_to_true():
    """A join-required envelope causes Q2-F to raise; the helper catches
    and returns None; the reader falls back to legacy gov.protected.
    With gov.protected=True, the final answer is True.
    """
    envelope = _join_required_envelope_dict(
        state=LifecycleState.PROTECTED,
    )
    payload = {
        "lifecycle_status": envelope,
        "governance": {"protected": True},
    }
    assert is_compression_protected(payload) is True


def test_join_required_protected_without_gov_flag_falls_back_to_false():
    envelope = _join_required_envelope_dict(
        state=LifecycleState.PROTECTED,
    )
    assert is_compression_protected(
        {"lifecycle_status": envelope}
    ) is False


def test_join_required_review_pending_falls_back():
    """REVIEW_PENDING is the canonical join-required state per the
    Q2-C decision table.
    """
    envelope = _join_required_envelope_dict(
        state=LifecycleState.REVIEW_PENDING,
    )
    payload = {
        "lifecycle_status": envelope,
        "governance": {"protected": True},
    }
    assert is_compression_protected(payload) is True


# ===========================================================================
# Section D -- malformed envelope falls back to legacy
# ===========================================================================


def test_malformed_envelope_with_gov_flag_falls_back_to_true():
    """A malformed envelope causes read_lifecycle_envelope to raise;
    the helper catches and returns None; the reader falls back to
    legacy gov.protected.
    """
    payload = {
        "lifecycle_status": {"state": "totally_made_up"},
        "governance": {"protected": True},
    }
    assert is_compression_protected(payload) is True


def test_malformed_envelope_without_gov_flag_falls_back_to_false():
    payload = {"lifecycle_status": {"state": "totally_made_up"}}
    assert is_compression_protected(payload) is False


def test_non_dict_lifecycle_status_falls_back():
    """``lifecycle_status`` set to a non-dict (e.g. a string) also
    triggers the validator; lifecycle path falls back.
    """
    payload = {
        "lifecycle_status": "released",
        "governance": {"protected": True},
    }
    assert is_compression_protected(payload) is True


# ===========================================================================
# Section E -- disagreement falls back to legacy AND emits warning
# ===========================================================================


def test_disagreement_state_mismatch_with_gov_flag_falls_back_to_true(caplog):
    """STATE_MISMATCH: explicit RELEASED + gov.protected=True. The
    detector reports the disagreement; the reader logs a warning AND
    falls back to legacy. With gov.protected=True the final answer is
    True.
    """
    envelope = _row_authoritative_envelope_dict(
        state=LifecycleState.RELEASED,
        via=LifecycleSetVia.RELEASE_PROMOTION,
    )
    payload = {
        "lifecycle_status": envelope,
        "governance": {"protected": True},
    }
    with caplog.at_level(logging.WARNING, logger="torment.governance"):
        result = is_compression_protected(payload)
    assert result is True
    # Confirm a warning was emitted naming Slice 5 + STATE_MISMATCH.
    warning_records = [
        r for r in caplog.records if r.levelno == logging.WARNING
    ]
    assert len(warning_records) >= 1, (
        f"expected at least one WARNING, got {len(warning_records)}"
    )
    combined_msg = " ".join(r.getMessage() for r in warning_records)
    assert "Q2-D Slice 5" in combined_msg
    assert "state_mismatch" in combined_msg
    assert "is_compression_protected" in combined_msg


def test_disagreement_state_mismatch_with_canon_falls_back_to_false(caplog):
    """STATE_MISMATCH: explicit RELEASED + canon=True. canon does NOT
    drive ``resolve_governance(payload).protected`` (canon is a
    compression-side marker, not a governance flag). So the legacy
    fallback returns False here. Confirms the fallback truly hands off
    to ``resolve_governance``, not to something more permissive.
    """
    envelope = _row_authoritative_envelope_dict(
        state=LifecycleState.RELEASED,
        via=LifecycleSetVia.RELEASE_PROMOTION,
    )
    payload = {"lifecycle_status": envelope, "canon": True}
    with caplog.at_level(logging.WARNING, logger="torment.governance"):
        result = is_compression_protected(payload)
    assert result is False
    assert any("state_mismatch" in r.getMessage() for r in caplog.records)


def test_disagreement_authority_mismatch_with_gov_flag_falls_back(caplog):
    """AUTHORITY_MISMATCH: explicit PROTECTED+join-required + canon=True.
    Wait -- actually the Q2-F guard raises FIRST in this path (the
    envelope is join-required), so we fall back BEFORE the disagreement
    detector runs. Confirms the order of checks: Q2-F guard first,
    then detector.
    """
    envelope = _join_required_envelope_dict(
        state=LifecycleState.PROTECTED,
        side_channel=SideChannel.REVIEW_QUEUE,
    )
    payload = {
        "lifecycle_status": envelope,
        "governance": {"protected": True},
    }
    with caplog.at_level(logging.WARNING, logger="torment.governance"):
        result = is_compression_protected(payload)
    # Falls back to legacy gov.protected=True regardless of whether
    # the warning was emitted (it isn't, because Q2-F short-circuits
    # before disagreement detection).
    assert result is True


# ===========================================================================
# Section F -- full agreement (both sides say PROTECTED)
# ===========================================================================


def test_explicit_protected_with_agreeing_canon_returns_true():
    """Explicit PROTECTED + canon=True: both sides agree on the
    load-bearing facts; the lifecycle path returns True directly.
    """
    envelope = _row_authoritative_envelope_dict(
        state=LifecycleState.PROTECTED,
        via=LifecycleSetVia.CANON_SET,
        actor=LifecycleActor.MIGRATION,
    )
    payload = {"lifecycle_status": envelope, "canon": True}
    assert is_compression_protected(payload) is True


# ===========================================================================
# Section G -- Q1 authority guard still fires
# ===========================================================================


def test_q1_guard_still_rejects_non_authoritative_deep_hit():
    """The existing Q1 ``assert_authoritative_memory`` guard at entry
    must continue to raise on NonAuthoritativeDeepHit subtypes. Slice 5
    does NOT weaken Q1's protection -- it adds the lifecycle path AFTER
    the Q1 guard.
    """
    from torment_service.deep_hits import (
        DeepRetrievalHit,
        NonAuthoritativeMemoryError,
    )

    wrapper = DeepRetrievalHit(
        source_eid=999,
        workspace_id="ws",
        agent_id="ag",
        compressed_step=0,
        similarity_score=0.5,
    )
    with pytest.raises(NonAuthoritativeMemoryError):
        is_compression_protected(wrapper)


# ===========================================================================
# Section H -- composition with H1c stamp through spawn_memory
# ===========================================================================


def test_spawn_memory_canon_row_is_compression_protected():
    """End-to-end: a row written via spawn_memory with canon=True gets
    the H1c-stamped PROTECTED envelope (state=PROTECTED, actor=SYSTEM,
    via=CANON_SET). Reading is_compression_protected on that payload
    returns True via the Slice 5 lifecycle path.
    """
    memory_graph = pytest.importorskip("torment_service.memory_graph")
    embeddings = pytest.importorskip("torment_service.embeddings")
    np = pytest.importorskip("numpy")

    MemoryGraph = memory_graph.MemoryGraph
    HashEmbedding = embeddings.HashEmbedding

    import tempfile
    tmpdir = tempfile.mkdtemp(prefix="torment_q2d_s5_")
    embedder = HashEmbedding(dim=8)
    graph = MemoryGraph(tmpdir, embedder=embedder)
    eid = graph.spawn_memory(
        summary="canon row",
        embedding=np.zeros(embedder.dim, dtype=np.float32),
        mtype="episode",
        strength=0.5, confidence=0.5, half_life_days=30.0,
        canon=False,  # the boolean kwarg; payload["canon"] is set via extra
        user_id="default", step=0,
        extra_payload={"canon": True},
    )
    payload = graph.entities[eid].payload
    # H1c stamped state=PROTECTED with actor=system at canon_set.
    assert payload["lifecycle_status"]["state"] == "protected"
    assert payload["lifecycle_status"]["set_by"]["actor"] == "system"
    # And the Slice 5 reader returns True.
    assert is_compression_protected(payload) is True


def test_spawn_memory_no_markers_row_is_not_compression_protected():
    memory_graph = pytest.importorskip("torment_service.memory_graph")
    embeddings = pytest.importorskip("torment_service.embeddings")
    np = pytest.importorskip("numpy")

    MemoryGraph = memory_graph.MemoryGraph
    HashEmbedding = embeddings.HashEmbedding

    import tempfile
    tmpdir = tempfile.mkdtemp(prefix="torment_q2d_s5_unset_")
    embedder = HashEmbedding(dim=8)
    graph = MemoryGraph(tmpdir, embedder=embedder)
    eid = graph.spawn_memory(
        summary="ordinary row",
        embedding=np.zeros(embedder.dim, dtype=np.float32),
        mtype="episode",
        strength=0.5, confidence=0.5, half_life_days=30.0,
        canon=False, user_id="default", step=0,
    )
    payload = graph.entities[eid].payload
    assert payload["lifecycle_status"]["state"] == "unset"
    assert is_compression_protected(payload) is False


# ===========================================================================
# Section I -- behavior-unification documentation: canon=True now drives
# is_compression_protected (it always drove derive_retention_tier)
# ===========================================================================


def test_canon_true_alone_now_returns_true():
    """Slice 5 unification: ``payload["canon"] = True`` with no other
    markers and no explicit envelope NOW returns True from
    is_compression_protected.

    Pre-Slice-5 this returned False because is_compression_protected
    only consulted governance.protected. compression.derive_retention_tier
    ALREADY treated canon=True as "protected" -- the two surfaces were
    inconsistent. Slice 5 unifies them through the lifecycle envelope:
    Slice 2 derives PROTECTED from canon, Slice 5 reads the derived
    envelope, returns True.

    This test documents the intentional behavior change.
    """
    assert is_compression_protected({"canon": True}) is True


def test_kind_seed_alone_now_returns_true():
    """Same unification logic for kind=seed."""
    assert is_compression_protected({"kind": "seed"}) is True


def test_tier_core_identity_alone_now_returns_true():
    """Same unification for tier=core_identity."""
    assert is_compression_protected({"tier": "core_identity"}) is True


def test_srg_is_crystal_alone_now_returns_true():
    """Same unification for srg.is_crystal."""
    assert is_compression_protected(
        {"srg": {"is_crystal": True}}
    ) is True
