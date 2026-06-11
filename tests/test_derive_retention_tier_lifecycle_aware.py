"""tests/test_derive_retention_tier_lifecycle_aware.py

Q2-D Slice 5-b tests for ``compression.derive_retention_tier``.

Second production consumer of Q2-F. Soft migration:

  * lifecycle path runs first via ``_protected_via_lifecycle``
  * legacy protected-marker fallback (canon, kind/type, tier,
    srg.is_crystal) runs when the lifecycle path declines to decide
  * non-protected tier logic (identity, echo, tool_result, relational,
    situational) is byte-identical to pre-Slice-5-b

The lifecycle path declines (returns None, triggering fallback) when:

  * envelope is malformed (``LifecycleStateError``)
  * envelope is join-required (Q2-F primitive raises)
  * envelope disagrees with legacy markers (Slice 4 detector reports;
    a WARNING is logged with ``"Q2-D Slice 5-b"`` and
    ``"derive_retention_tier"``)

New capability: a payload with an explicit row-authoritative PROTECTED
envelope and no legacy markers now returns ``"protected"``. Same
behavior unification that Slice 5 established for
``is_compression_protected``.

Out of scope at this slice:

  * ``CompressionScorer._is_protected`` migration (Slice 5-c)
  * hard migration / removal of legacy fallback (Slice 6)
  * any change to identity / echo / tool_result / relational /
    situational logic
  * raising on disagreement at production decision sites
  * baton/R3, review-queue, closure-ledger, Q3, custom DB
"""
from __future__ import annotations

import logging
import os
import sys
from typing import Any, Dict

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


from torment_service.compression import derive_retention_tier
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
# Section A -- legacy protected branch preserved
# ===========================================================================


def test_canon_true_returns_protected():
    """Slice 2 derives PROTECTED from canon=True via the lifecycle
    path; ``derive_retention_tier`` returns "protected".
    """
    assert derive_retention_tier({"canon": True}) == "protected"


@pytest.mark.parametrize("kind_value",
                          ["seed", "identity", "core_identity"])
def test_kind_marker_returns_protected(kind_value):
    assert derive_retention_tier({"kind": kind_value}) == "protected"


def test_type_fallback_returns_protected():
    """``type`` is the fallback marker for ``kind``. Existing behavior."""
    assert derive_retention_tier({"type": "seed"}) == "protected"


def test_tier_core_identity_returns_protected():
    assert derive_retention_tier({"tier": "core_identity"}) == "protected"


def test_srg_is_crystal_returns_protected():
    assert derive_retention_tier(
        {"srg": {"is_crystal": True}}
    ) == "protected"


# ===========================================================================
# Section B -- new lifecycle capability
# ===========================================================================


def test_explicit_protected_envelope_no_markers_returns_protected():
    """NEW capability of Slice 5-b: an explicit row-authoritative
    PROTECTED envelope produces "protected" even when no legacy
    markers are set. Pre-Slice-5-b this would have fallen through
    to identity/relational/situational based on half_life.
    """
    envelope = _row_authoritative_envelope_dict(
        state=LifecycleState.PROTECTED,
        via=LifecycleSetVia.CANON_SET,
    )
    assert derive_retention_tier(
        {"lifecycle_status": envelope}
    ) == "protected"


def test_explicit_released_envelope_high_half_life_returns_identity():
    """Explicit RELEASED + half_life=400: lifecycle decisively says
    non-PROTECTED (state != PROTECTED, row-auth, no disagreement),
    so the function SKIPS the legacy protected branch and falls
    through to existing identity tier logic (half_life >= 365).
    """
    envelope = _row_authoritative_envelope_dict(
        state=LifecycleState.RELEASED,
        via=LifecycleSetVia.RELEASE_PROMOTION,
    )
    payload = {"lifecycle_status": envelope, "half_life": 400}
    assert derive_retention_tier(payload) == "identity"


def test_explicit_unset_envelope_no_half_life_returns_situational():
    envelope = _row_authoritative_envelope_dict(
        state=LifecycleState.UNSET,
        via=LifecycleSetVia.UNSET_DEFAULT,
        actor=LifecycleActor.MIGRATION,
    )
    payload = {"lifecycle_status": envelope}
    assert derive_retention_tier(payload) == "situational"


def test_explicit_released_envelope_short_half_life_returns_situational():
    """Lifecycle says non-protected, half_life too low for identity
    or relational, falls all the way through to situational.
    """
    envelope = _row_authoritative_envelope_dict(
        state=LifecycleState.RELEASED,
        via=LifecycleSetVia.RELEASE_PROMOTION,
    )
    payload = {"lifecycle_status": envelope, "half_life": 1}
    assert derive_retention_tier(payload) == "situational"


# ===========================================================================
# Section C -- fallback cases (lifecycle declines, legacy resolves)
# ===========================================================================


def test_join_required_envelope_with_canon_falls_back_to_protected():
    """Q2-F raises NonAuthoritativeLifecycleError; helper returns None;
    legacy protected branch sees canon=True and returns "protected".
    """
    envelope = _join_required_envelope_dict(
        state=LifecycleState.PROTECTED,
    )
    payload = {"lifecycle_status": envelope, "canon": True}
    assert derive_retention_tier(payload) == "protected"


def test_malformed_envelope_with_canon_falls_back_to_protected():
    payload = {
        "lifecycle_status": {"state": "totally_made_up"},
        "canon": True,
    }
    assert derive_retention_tier(payload) == "protected"


def test_disagreement_state_mismatch_falls_back_to_protected_with_warning(
    caplog,
):
    """STATE_MISMATCH (explicit RELEASED + canon=True): the lifecycle
    helper logs a warning AND returns None; the legacy protected
    branch sees canon=True and returns "protected". Slice 5-b's
    contract: soft migration preserves legacy outcome on disagreement.
    """
    envelope = _row_authoritative_envelope_dict(
        state=LifecycleState.RELEASED,
        via=LifecycleSetVia.RELEASE_PROMOTION,
    )
    payload = {"lifecycle_status": envelope, "canon": True}
    with caplog.at_level(logging.WARNING, logger="torment_service.compression"):
        result = derive_retention_tier(payload)
    assert result == "protected"
    warning_records = [
        r for r in caplog.records if r.levelno == logging.WARNING
    ]
    assert len(warning_records) >= 1
    combined = " ".join(r.getMessage() for r in warning_records)
    # Slice 5-c generalized the log marker to slice-agnostic "Q2-D"
    # so the same helper can serve multiple callers; site name still
    # accurately names the function.
    assert "Q2-D" in combined
    assert "derive_retention_tier" in combined
    assert "state_mismatch" in combined


def test_join_required_envelope_no_markers_falls_through_to_tier_logic():
    """A join-required envelope with NO legacy markers: Q2-F raises,
    helper returns None, legacy protected branch finds nothing, the
    function falls through to non-protected tier logic.
    """
    envelope = _join_required_envelope_dict(
        state=LifecycleState.PROTECTED,
    )
    # With half_life=400, falls through to identity (not protected).
    payload = {"lifecycle_status": envelope, "half_life": 400}
    assert derive_retention_tier(payload) == "identity"


def test_malformed_envelope_no_markers_falls_through_to_situational():
    payload = {"lifecycle_status": {"state": "bogus"}}
    assert derive_retention_tier(payload) == "situational"


# ===========================================================================
# Section D -- non-protected tier logic unchanged (regression guards)
# ===========================================================================


def test_identity_tier_via_high_half_life():
    """half_life >= 365 -> identity (unchanged)."""
    assert derive_retention_tier({"half_life": 400}) == "identity"


def test_echo_tier_via_collective_provenance_dict():
    payload = {"provenance": {"source_type": "collective_echo"}}
    assert derive_retention_tier(payload) == "echo"


def test_echo_tier_via_legacy_bare_string_provenance():
    payload = {"provenance": "collective"}
    assert derive_retention_tier(payload) == "echo"


def test_tool_result_tier_via_tool_result_provenance():
    payload = {"provenance": {"source_type": "tool_result"}}
    assert derive_retention_tier(payload) == "tool_result"


def test_relational_tier_via_medium_half_life():
    assert derive_retention_tier({"half_life": 30}) == "relational"


def test_situational_tier_default():
    assert derive_retention_tier({"half_life": 1}) == "situational"


def test_situational_tier_empty_payload():
    assert derive_retention_tier({}) == "situational"


# ===========================================================================
# Section E -- Q2-F is load-bearing
# ===========================================================================


def test_q2f_blocks_join_required_lifecycle_from_returning_protected():
    """An explicit PROTECTED envelope that is JOIN-REQUIRED should
    NOT yield "protected" from the lifecycle path. Q2-F's guard raises;
    helper returns None; legacy fallback finds no marker; the
    function falls through to non-protected tier logic.

    This is the Slice 5-b "Q2-F is load-bearing" test: without the
    Q2-F check, the lifecycle path might naively return True for
    state=PROTECTED regardless of authoritativity, and the function
    would return "protected" when it shouldn't.
    """
    envelope = _join_required_envelope_dict(
        state=LifecycleState.PROTECTED,
    )
    payload = {"lifecycle_status": envelope, "half_life": 400}
    # No legacy markers, half_life=400 -> identity (not protected).
    assert derive_retention_tier(payload) == "identity"


# ===========================================================================
# Section F -- warning log specifics
# ===========================================================================


def test_disagreement_log_includes_slice_marker_and_function_name(caplog):
    envelope = _row_authoritative_envelope_dict(
        state=LifecycleState.RELEASED,
        via=LifecycleSetVia.RELEASE_PROMOTION,
    )
    payload = {"lifecycle_status": envelope, "kind": "seed"}
    with caplog.at_level(logging.WARNING, logger="torment_service.compression"):
        derive_retention_tier(payload)
    assert any(
        # Slice 5-c generalized "Q2-D Slice 5-b" to "Q2-D".
        "Q2-D" in r.getMessage()
        and "derive_retention_tier" in r.getMessage()
        for r in caplog.records
    )


def test_no_warning_on_join_required_fallback(caplog):
    """Per the ratified scope, warning is only emitted on disagreement
    -- NOT on ordinary join-required / malformed fallback. Slice 5-b
    log policy.
    """
    envelope = _join_required_envelope_dict(
        state=LifecycleState.PROTECTED,
    )
    payload = {"lifecycle_status": envelope, "canon": True}
    with caplog.at_level(logging.WARNING, logger="torment_service.compression"):
        derive_retention_tier(payload)
    # No warning records emitted -- Q2-F short-circuits before the
    # disagreement detector runs.
    assert all(
        # Slice 5-c generalized the marker to "Q2-D"; check for that
        # to confirm no disagreement warning was emitted at all.
        "Q2-D" not in r.getMessage() for r in caplog.records
    )


# ===========================================================================
# Section G -- CompressionScorer._is_protected untouched sanity check
# ===========================================================================


def test_compression_scorer_is_protected_canon_still_true():
    """Slice 5-b does NOT touch ``CompressionScorer._is_protected``.
    Its own inline canon/kind/tier checks remain. Regression guard
    to catch accidental migration.
    """
    from torment_service.compression import CompressionScorer
    scorer = CompressionScorer()
    assert scorer._is_protected({"canon": True}) is True


def test_compression_scorer_is_protected_empty_still_false():
    from torment_service.compression import CompressionScorer
    scorer = CompressionScorer()
    assert scorer._is_protected({}) is False


def test_compression_scorer_is_protected_seed_kind_still_true():
    """Inline kind check still works in the scorer (unchanged path)."""
    from torment_service.compression import CompressionScorer
    scorer = CompressionScorer()
    assert scorer._is_protected({"kind": "seed"}) is True


# ===========================================================================
# Section H -- composition with H1c (spawn_memory writes the envelope)
# ===========================================================================


def test_h1c_canon_row_yields_protected_tier():
    """End-to-end: row from ``spawn_memory(extra_payload={"canon": True})``
    carries the H1c-stamped PROTECTED envelope; ``derive_retention_tier``
    on that payload returns "protected" via the lifecycle path.
    """
    memory_graph = pytest.importorskip("torment_service.memory_graph")
    embeddings = pytest.importorskip("torment_service.embeddings")
    np = pytest.importorskip("numpy")

    MemoryGraph = memory_graph.MemoryGraph
    HashEmbedding = embeddings.HashEmbedding

    import tempfile
    tmpdir = tempfile.mkdtemp(prefix="torment_q2d_s5b_canon_")
    embedder = HashEmbedding(dim=8)
    graph = MemoryGraph(tmpdir, embedder=embedder)
    eid = graph.spawn_memory(
        summary="canon row",
        embedding=np.zeros(embedder.dim, dtype=np.float32),
        mtype="episode",
        strength=0.5, confidence=0.5, half_life_days=30.0,
        canon=False, user_id="default", step=0,
        extra_payload={"canon": True},
    )
    payload = graph.entities[eid].payload
    assert derive_retention_tier(payload) == "protected"


def test_h1c_no_markers_row_follows_normal_tier_logic():
    """An H1c-stamped row with no legacy markers carries the canonical
    UNSET envelope. ``derive_retention_tier`` falls through to the
    half_life-based tier classification, NOT the protected branch.
    Half_life=30 from spawn_memory's default -> "relational".
    """
    memory_graph = pytest.importorskip("torment_service.memory_graph")
    embeddings = pytest.importorskip("torment_service.embeddings")
    np = pytest.importorskip("numpy")

    MemoryGraph = memory_graph.MemoryGraph
    HashEmbedding = embeddings.HashEmbedding

    import tempfile
    tmpdir = tempfile.mkdtemp(prefix="torment_q2d_s5b_unset_")
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
    # half_life_days=30 -> relational tier (>= 7, < 365).
    assert derive_retention_tier(payload) == "relational"
