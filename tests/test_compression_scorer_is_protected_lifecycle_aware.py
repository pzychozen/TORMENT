"""tests/test_compression_scorer_is_protected_lifecycle_aware.py

Q2-D Slice 5-c tests for ``CompressionScorer._is_protected``.

Third and final protected-reader migration. Soft migration shape
identical to Slice 5 and Slice 5-b:

  * lifecycle path runs first via ``_protected_via_lifecycle``
    (the same shared helper Slice 5-b uses for
    ``derive_retention_tier``, now generalized to accept a ``site=``
    keyword for accurate per-site disagreement logging)
  * legacy fallback (canon, kind/type, tier, plus delegation to
    ``governance.is_compression_protected``) runs when the lifecycle
    path declines to decide
  * non-protected paths short-circuit on ``lifecycle_protected is False``

The lifecycle path declines (returns None, triggering fallback) when:

  * envelope is malformed (``LifecycleStateError``)
  * envelope is join-required (Q2-F primitive raises)
  * envelope disagrees with legacy markers (Slice 4 detector reports;
    a WARNING is logged with ``"Q2-D"`` and
    ``"CompressionScorer._is_protected"``)

Behavior unification with the other two protected readers: after
Slice 5-c, ``_is_protected({"srg": {"is_crystal": True}})`` returns
True. This unifies the scorer with ``derive_retention_tier`` and
``is_compression_protected``, which already treat ``srg.is_crystal``
as protected.

Out of scope at this slice:

  * hard migration / removal of legacy fallback (Slice 6)
  * scoring formula or compression threshold changes
  * ``PROTECTED_KINDS`` / ``PROTECTED_TIERS`` changes
  * governance helper consolidation
  * raising on disagreement
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


from torment_service.compression import (
    CompressionScorer,
    _protected_via_lifecycle,
)
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


@pytest.fixture()
def scorer():
    """Fresh CompressionScorer per test."""
    return CompressionScorer()


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
# Section A -- lifecycle-first protected (the new direct path)
# ===========================================================================


def test_explicit_protected_envelope_no_markers_returns_true(scorer):
    """Explicit row-authoritative PROTECTED envelope with no legacy
    markers returns True via the lifecycle path's direct True branch.
    """
    envelope = _row_authoritative_envelope_dict(
        state=LifecycleState.PROTECTED,
        via=LifecycleSetVia.CANON_SET,
    )
    assert scorer._is_protected({"lifecycle_status": envelope}) is True


def test_explicit_released_envelope_no_markers_returns_false(scorer):
    """Explicit row-authoritative RELEASED with no markers: lifecycle
    decisively says non-PROTECTED; scorer short-circuits to False
    without consulting legacy fallback.
    """
    envelope = _row_authoritative_envelope_dict(
        state=LifecycleState.RELEASED,
        via=LifecycleSetVia.RELEASE_PROMOTION,
    )
    assert scorer._is_protected({"lifecycle_status": envelope}) is False


def test_explicit_unset_envelope_no_markers_returns_false(scorer):
    envelope = _row_authoritative_envelope_dict(
        state=LifecycleState.UNSET,
        via=LifecycleSetVia.UNSET_DEFAULT,
        actor=LifecycleActor.MIGRATION,
    )
    assert scorer._is_protected({"lifecycle_status": envelope}) is False


# ===========================================================================
# Section B -- legacy fallback (inline markers)
# ===========================================================================


def test_canon_true_returns_true(scorer):
    """Slice 2 derives PROTECTED from canon=True via the lifecycle
    path; scorer returns True via the lifecycle True branch.
    """
    assert scorer._is_protected({"canon": True}) is True


@pytest.mark.parametrize("kind_value",
                          ["seed", "identity", "core_identity"])
def test_kind_marker_returns_true(scorer, kind_value):
    assert scorer._is_protected({"kind": kind_value}) is True


def test_tier_core_identity_returns_true(scorer):
    assert scorer._is_protected({"tier": "core_identity"}) is True


def test_empty_payload_returns_false(scorer):
    """No envelope, no markers: lifecycle path returns False
    (UNSET ≠ PROTECTED, no disagreement); scorer returns False.
    Regression guard for the pre-Slice-5-c default behavior.
    """
    assert scorer._is_protected({}) is False


# ===========================================================================
# Section C -- legacy fallback via governance delegation
# ===========================================================================


def test_governance_protected_true_returns_true(scorer):
    """governance.protected=True: Slice 1 derivation picks it up
    through the lifecycle path; lifecycle returns True; scorer returns
    True via the lifecycle True branch (the governance-delegation
    fallback is not exercised in this case because lifecycle decided).
    """
    assert scorer._is_protected(
        {"governance": {"protected": True}}
    ) is True


# ===========================================================================
# Section D -- lifecycle-can't-decide cases (fallback exercised)
# ===========================================================================


def test_malformed_envelope_with_canon_falls_back_to_true(scorer):
    """Malformed envelope: lifecycle helper returns None; fallback
    inline canon check returns True.
    """
    payload = {
        "lifecycle_status": {"state": "totally_made_up"},
        "canon": True,
    }
    assert scorer._is_protected(payload) is True


def test_join_required_envelope_with_canon_falls_back_to_true(scorer):
    """Q2-F raises NonAuthoritativeLifecycleError; lifecycle helper
    returns None; inline canon check in the fallback returns True.
    """
    envelope = _join_required_envelope_dict(
        state=LifecycleState.PROTECTED,
    )
    payload = {"lifecycle_status": envelope, "canon": True}
    assert scorer._is_protected(payload) is True


def test_disagreement_state_mismatch_falls_back_with_warning(
    scorer, caplog,
):
    """STATE_MISMATCH (explicit RELEASED + canon=True): lifecycle
    helper logs a warning AND returns None; fallback inline canon
    check returns True. Soft-migration contract preserved.
    """
    envelope = _row_authoritative_envelope_dict(
        state=LifecycleState.RELEASED,
        via=LifecycleSetVia.RELEASE_PROMOTION,
    )
    payload = {"lifecycle_status": envelope, "canon": True}
    with caplog.at_level(logging.WARNING, logger="torment_service.compression"):
        result = scorer._is_protected(payload)
    assert result is True
    warning_records = [
        r for r in caplog.records if r.levelno == logging.WARNING
    ]
    assert len(warning_records) >= 1
    combined = " ".join(r.getMessage() for r in warning_records)
    assert "Q2-D" in combined
    assert "CompressionScorer._is_protected" in combined
    assert "state_mismatch" in combined


def test_malformed_envelope_no_markers_returns_false(scorer):
    """Malformed envelope with no fallback markers: lifecycle returns
    None; fallback finds nothing; scorer returns False.
    """
    payload = {"lifecycle_status": {"state": "totally_made_up"}}
    assert scorer._is_protected(payload) is False


# ===========================================================================
# Section E -- Q2-F is load-bearing
# ===========================================================================


def test_q2f_blocks_join_required_protected_with_no_markers(scorer):
    """Explicit PROTECTED join-required envelope, no legacy markers.
    Q2-F's guard raises NonAuthoritativeLifecycleError inside the
    lifecycle helper; helper returns None; legacy fallback finds no
    markers; scorer returns False. Without Q2-F, the lifecycle path
    might naively return True for state=PROTECTED regardless of
    authoritativity, and the scorer would return True when it
    shouldn't.
    """
    envelope = _join_required_envelope_dict(
        state=LifecycleState.PROTECTED,
    )
    assert scorer._is_protected({"lifecycle_status": envelope}) is False


# ===========================================================================
# Section F -- warning log specifics
# ===========================================================================


def test_disagreement_log_includes_site_name(scorer, caplog):
    envelope = _row_authoritative_envelope_dict(
        state=LifecycleState.RELEASED,
        via=LifecycleSetVia.RELEASE_PROMOTION,
    )
    payload = {"lifecycle_status": envelope, "kind": "seed"}
    with caplog.at_level(logging.WARNING, logger="torment_service.compression"):
        scorer._is_protected(payload)
    assert any(
        "Q2-D" in r.getMessage()
        and "CompressionScorer._is_protected" in r.getMessage()
        for r in caplog.records
    )


def test_no_warning_on_join_required_fallback(scorer, caplog):
    """Per the ratified scope, warning fires ONLY on disagreement --
    not on ordinary join-required / malformed fallback. Slice 5-c
    inherits Slice 5-b's log policy unchanged.
    """
    envelope = _join_required_envelope_dict(
        state=LifecycleState.PROTECTED,
    )
    payload = {"lifecycle_status": envelope, "canon": True}
    with caplog.at_level(logging.WARNING, logger="torment_service.compression"):
        scorer._is_protected(payload)
    assert all(
        # No Q2-D disagreement warning should have been emitted; Q2-F
        # short-circuits the helper before the disagreement detector
        # runs.
        "Q2-D" not in r.getMessage() for r in caplog.records
    )


# ===========================================================================
# Section G -- srg.is_crystal behavior unification (THE design call)
# ===========================================================================


def test_srg_is_crystal_alone_now_returns_true(scorer):
    """**INTENTIONAL BEHAVIOR CHANGE** from Slice 5-c.

    Pre-Slice-5-c, ``CompressionScorer._is_protected({"srg": {"is_crystal":
    True}})`` returned False -- the scorer's inline checks did NOT
    consult ``srg.is_crystal``, and the governance-delegation
    fallback didn't carry it either.

    The other two protected readers (``derive_retention_tier`` and
    ``governance.is_compression_protected``) ALREADY treat
    ``srg.is_crystal`` as protected via the Slice 1 lifecycle
    derivation. Pre-Slice-5-c, the scorer was the lone holdout --
    inconsistent with the other two readers.

    Slice 5-c brings the scorer into alignment: ``srg.is_crystal=True``
    now triggers the lifecycle-first PROTECTED return. This is the
    intentional unification ratified as part of the slice's scope.

    This test exists explicitly to document the behavior change so it
    cannot be silently reverted in a future refactor.
    """
    assert scorer._is_protected({"srg": {"is_crystal": True}}) is True


def test_srg_is_crystal_false_does_not_trigger(scorer):
    """Regression guard for the strict-marker semantics inherited
    from Slice 1: srg.is_crystal=False does NOT trigger protected.
    """
    assert scorer._is_protected({"srg": {"is_crystal": False}}) is False


# ===========================================================================
# Section H -- composition with H1c (spawn_memory writes the envelope)
# ===========================================================================


def test_h1c_canon_row_is_protected(scorer):
    """End-to-end: row from spawn_memory(extra_payload={"canon": True})
    carries the H1c-stamped PROTECTED envelope; _is_protected returns
    True via the lifecycle path's direct True branch.
    """
    memory_graph = pytest.importorskip("torment_service.memory_graph")
    embeddings = pytest.importorskip("torment_service.embeddings")
    np = pytest.importorskip("numpy")

    MemoryGraph = memory_graph.MemoryGraph
    HashEmbedding = embeddings.HashEmbedding

    import tempfile
    tmpdir = tempfile.mkdtemp(prefix="torment_q2d_s5c_canon_")
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
    assert scorer._is_protected(payload) is True


def test_h1c_no_markers_row_is_not_protected(scorer):
    """An H1c-stamped row with no legacy markers carries the canonical
    UNSET envelope; _is_protected returns False.
    """
    memory_graph = pytest.importorskip("torment_service.memory_graph")
    embeddings = pytest.importorskip("torment_service.embeddings")
    np = pytest.importorskip("numpy")

    MemoryGraph = memory_graph.MemoryGraph
    HashEmbedding = embeddings.HashEmbedding

    import tempfile
    tmpdir = tempfile.mkdtemp(prefix="torment_q2d_s5c_unset_")
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
    assert scorer._is_protected(payload) is False


# ===========================================================================
# Section I -- helper generalization regression guards
# ===========================================================================


def test_helper_returns_expected_bool_with_site_kwarg():
    """The Slice 5-c generalization added a required ``site=`` kwarg.
    Direct helper calls must pass it; the helper returns the same
    True/False/None contract regardless of site name.
    """
    assert _protected_via_lifecycle({"canon": True}, site="test") is True
    assert _protected_via_lifecycle({}, site="test") is False


def test_helper_log_message_includes_supplied_site(caplog):
    """Direct helper call with a custom site name produces a warning
    whose text contains that name. Confirms the site parameter
    actually plumbs through to the log message.
    """
    envelope = _row_authoritative_envelope_dict(
        state=LifecycleState.RELEASED,
        via=LifecycleSetVia.RELEASE_PROMOTION,
    )
    payload = {"lifecycle_status": envelope, "canon": True}
    with caplog.at_level(logging.WARNING, logger="torment_service.compression"):
        _protected_via_lifecycle(payload, site="some_custom_site")
    assert any(
        "some_custom_site" in r.getMessage()
        for r in caplog.records
    )


def test_helper_site_is_required_keyword():
    """Calling the helper without site= must raise TypeError. Locks
    the contract that callers must always identify themselves.
    """
    with pytest.raises(TypeError):
        _protected_via_lifecycle({"canon": True})  # missing site=
