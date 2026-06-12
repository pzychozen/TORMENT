"""tests/test_lifecycle_legacy_protected_at_spawn.py

Q2-D Slice 3 tests: the H1c write-side stamp ``_ensure_lifecycle_envelope``
now composes with the Slice 1 derivation helper (via the ``actor=SYSTEM``
kwarg) to stamp PROTECTED on new rows that carry legacy protected
markers but no explicit lifecycle envelope.

After this slice, ``_ensure_lifecycle_envelope`` has three branches:

  1. payload["lifecycle_status"] absent or None
     a. legacy protected markers present →
        stamp PROTECTED / actor=SYSTEM / via=<marker via>
     b. otherwise →
        stamp canonical H1c UNSET / actor=SYSTEM / via=INGEST_UNMARKED
  2. payload["lifecycle_status"] present and non-null
     → validate-and-keep (explicit wins; malformed raises)

The Slice 1 helper is tested in isolation in
``tests/test_protected_lifecycle_derivation.py``. The H1c original
contract is exercised by ``tests/test_lifecycle_emission_at_spawn.py``
(all 18 existing tests continue to pass unchanged because their fixtures
use payloads without legacy protected markers OR with explicit envelopes
that still win).

Slice 3 closes Hazard B from the Q2-D plan. Combined with Slice 2 (which
closed Hazard A on the read side), the system's protected lifecycle view
is now internally consistent across both legacy on-disk rows and newly
written rows -- with a load-bearing actor distinction (MIGRATION vs
SYSTEM) preserving the audit story of "where did this interpretation
come from?"

Out of scope (these tests do NOT exercise):

* reader migration -- ``governance.is_compression_protected``,
  ``compression.derive_retention_tier``, and ``CompressionScorer``
  still read legacy markers directly (Slice 5+)
* disagreement detection between explicit envelope and legacy markers
  (Slice 4)
* retroactive disk rewrite, baton lifecycle / R3, review-queue /
  closure-ledger work, Q3, custom DB / schema work
"""
from __future__ import annotations

import copy
import os
import sys
import tempfile
from typing import Any, Dict

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


from torment_service.lifecycle import (
    LifecycleActor,
    LifecycleJoinTarget,
    LifecycleSetBy,
    LifecycleSetVia,
    LifecycleState,
    LifecycleStateError,
    LifecycleStatus,
    SideChannel,
    assert_lifecycle_row_authoritative,
    read_lifecycle_envelope,
    validate_lifecycle_envelope,
)


FIXED_AT = 1_716_300_000


def _ensure():
    """Lazy import: the helper is in memory_graph.py which has heavy deps.

    Skip the whole file if those deps aren't available in the env.
    """
    memory_graph = pytest.importorskip("torment_service.memory_graph")
    return memory_graph._ensure_lifecycle_envelope


def _explicit_envelope_dict(
    state: LifecycleState = LifecycleState.RELEASED,
    via: LifecycleSetVia = LifecycleSetVia.RELEASE_PROMOTION,
    actor: LifecycleActor = LifecycleActor.OPERATOR,
) -> Dict[str, Any]:
    return LifecycleStatus(
        state=state,
        is_authoritative_on_row=True,
        requires_join=None,
        set_by=LifecycleSetBy(actor=actor, via=via, at=FIXED_AT),
        history_ref=None,
    ).to_dict()


def _join_required_envelope_dict() -> Dict[str, Any]:
    return LifecycleStatus(
        state=LifecycleState.REVIEW_PENDING,
        is_authoritative_on_row=False,
        requires_join=LifecycleJoinTarget(
            side_channel=SideChannel.REVIEW_QUEUE, join_key="eid",
        ),
        set_by=LifecycleSetBy(
            actor=LifecycleActor.MIGRATION,
            via=LifecycleSetVia.GATE1_REFUSAL,
            at=FIXED_AT,
        ),
        history_ref=None,
    ).to_dict()


# ===========================================================================
# Section A -- marker matrix through _ensure_lifecycle_envelope
# (helper-level unit tests; same call path spawn_memory uses)
# ===========================================================================


MARKER_CASES = [
    ("canon_true", {"canon": True}, "canon_set"),
    ("kind_seed", {"kind": "seed"}, "seed_plant"),
    ("kind_identity", {"kind": "identity"}, "seed_plant"),
    ("kind_core_identity", {"kind": "core_identity"}, "seed_plant"),
    ("tier_core_identity", {"tier": "core_identity"}, "tier_set"),
    ("srg_is_crystal_true",
     {"srg": {"is_crystal": True}}, "srg_crystal"),
    ("governance_protected_true",
     {"governance": {"protected": True}}, "governance_flag"),
]


@pytest.mark.parametrize("label,payload,expected_via", MARKER_CASES)
def test_h1c_stamps_protected_with_system_actor_for_each_marker(
    label, payload, expected_via,
):
    """Section A core: each marker on a payload with no explicit
    envelope causes ``_ensure_lifecycle_envelope`` to stamp PROTECTED
    with ``actor=SYSTEM`` (Slice 3 write-time) and the marker-specific
    via. This is the Slice 3 actor decision lock: SYSTEM, not MIGRATION.
    """
    ensure = _ensure()
    payload_copy = dict(payload)
    ensure(payload_copy)
    env = payload_copy["lifecycle_status"]
    assert env["state"] == "protected", (
        f"{label!r} should stamp PROTECTED via H1c"
    )
    assert env["is_authoritative_on_row"] is True
    assert env["requires_join"] is None
    assert env["history_ref"] is None
    assert env["set_by"]["actor"] == "system", (
        f"{label!r} should use actor=system at the H1c write site"
    )
    assert env["set_by"]["via"] == expected_via
    assert isinstance(env["set_by"]["at"], int)


# ===========================================================================
# Section B -- non-protected and explicit-envelope behavior (helper-level)
# ===========================================================================


def test_h1c_no_marker_no_envelope_still_stamps_canonical_unset():
    """H1c regression preserved: a payload with neither legacy markers
    nor an explicit envelope still gets the canonical
    ``UNSET / SYSTEM / INGEST_UNMARKED`` stamp.
    """
    ensure = _ensure()
    payload: Dict[str, Any] = {}
    ensure(payload)
    env = payload["lifecycle_status"]
    assert env["state"] == "unset"
    assert env["is_authoritative_on_row"] is True
    assert env["set_by"]["actor"] == "system"
    assert env["set_by"]["via"] == "ingest_unmarked"


def test_h1c_explicit_none_lifecycle_status_can_stamp_protected():
    """Missing-key and explicit-``None`` remain equivalent at the write
    site. A payload with ``lifecycle_status=None`` AND ``canon=True``
    routes through the derivation branch and gets stamped PROTECTED
    (not UNSET, not preserved as None).
    """
    ensure = _ensure()
    payload: Dict[str, Any] = {"canon": True, "lifecycle_status": None}
    ensure(payload)
    env = payload["lifecycle_status"]
    assert env is not None
    assert env["state"] == "protected"
    assert env["set_by"]["actor"] == "system"
    assert env["set_by"]["via"] == "canon_set"


def test_h1c_explicit_valid_row_authoritative_envelope_wins_over_canon():
    """Slice 3 boundary lock: a payload with an explicit valid envelope
    AND ``canon=True`` keeps the explicit envelope verbatim. The
    derivation branch is NOT consulted. Silent disagreement is
    acceptable at this slice (Slice 4 will add detection).
    """
    ensure = _ensure()
    explicit = _explicit_envelope_dict(state=LifecycleState.RELEASED)
    payload: Dict[str, Any] = {"canon": True, "lifecycle_status": explicit}
    ensure(payload)
    # Verbatim preserved; canon ignored.
    assert payload["lifecycle_status"] == explicit
    assert payload["lifecycle_status"]["state"] == "released"
    assert payload["lifecycle_status"]["set_by"]["via"] == "release_promotion"
    assert payload["lifecycle_status"]["set_by"]["at"] == FIXED_AT


def test_h1c_explicit_valid_join_required_envelope_wins_over_canon():
    """Explicit-wins applies to non-row-authoritative envelopes too. A
    payload supplying a REVIEW_PENDING join-required envelope and
    ``canon=True`` keeps the join-required envelope, not a derived
    PROTECTED. (No-op for the consumer that cares about review_pending;
    they still must perform the side-channel join.)
    """
    ensure = _ensure()
    explicit = _join_required_envelope_dict()
    payload: Dict[str, Any] = {"canon": True, "lifecycle_status": explicit}
    ensure(payload)
    assert payload["lifecycle_status"] == explicit
    assert payload["lifecycle_status"]["state"] == "review_pending"
    assert payload["lifecycle_status"]["is_authoritative_on_row"] is False


def test_h1c_explicit_malformed_envelope_raises_no_fallback_to_derivation():
    """Keystone Slice 3 safety check: a malformed explicit envelope on a
    payload with legacy protected markers MUST raise. The H1c contract
    does NOT route past a corrupt envelope into the derivation branch.
    Loud failure stays loud.
    """
    ensure = _ensure()
    bad = _explicit_envelope_dict()
    bad["state"] = "totally_made_up"
    payload: Dict[str, Any] = {"canon": True, "lifecycle_status": bad}
    with pytest.raises(LifecycleStateError) as exc_info:
        ensure(payload)
    assert exc_info.value.field == "state"
    assert exc_info.value.reason == "unknown_value"


# ===========================================================================
# Section C -- caller's extra_payload not mutated (helper-level)
# ===========================================================================


def test_caller_dict_with_marker_not_mutated_until_helper_runs():
    """``_ensure_lifecycle_envelope`` does mutate its own (local) payload
    arg by adding ``lifecycle_status``. The semantic guarantee is that
    callers (notably ``spawn_memory``) must not pass a caller-visible
    dict directly -- and they don't: ``spawn_memory`` builds a fresh
    local payload via ``dict.update(extra_payload)`` before invoking
    this helper, so the caller's ``extra_payload`` remains unmutated.

    This test simulates that contract at the helper boundary by
    snapshotting the LOCAL payload before mutation and confirming
    that, after the helper runs, the local payload has gained
    ``lifecycle_status`` but no other field changed.
    """
    ensure = _ensure()
    pre_call = {"canon": True, "text": "x"}
    snapshot_keys = set(pre_call.keys())
    ensure(pre_call)
    # The helper adds exactly one key (lifecycle_status). Everything
    # else stays untouched.
    assert set(pre_call.keys()) == snapshot_keys | {"lifecycle_status"}
    assert pre_call["canon"] is True
    assert pre_call["text"] == "x"


# ===========================================================================
# Section D -- integration tests through MemoryGraph.spawn_memory
# ===========================================================================


def _try_build_graph():
    memory_graph = pytest.importorskip("torment_service.memory_graph")
    embeddings = pytest.importorskip("torment_service.embeddings")
    np = pytest.importorskip("numpy")

    MemoryGraph = memory_graph.MemoryGraph
    HashEmbedding = embeddings.HashEmbedding

    tmpdir = tempfile.mkdtemp(prefix="torment_q2d_slice3_")
    embedder = HashEmbedding(dim=8)
    graph = MemoryGraph(tmpdir, embedder=embedder)
    return graph, tmpdir, embedder, np


def _spawn(graph, embedder, np, extra_payload=None, memory_class="core"):
    emb = np.zeros(embedder.dim, dtype=np.float32)
    return graph.spawn_memory(
        summary="slice 3 test row",
        embedding=emb,
        mtype="episode",
        strength=0.5,
        confidence=0.5,
        half_life_days=30.0,
        canon=False,  # boolean kwarg to spawn_memory, separate from payload["canon"]
        user_id="default",
        step=0,
        extra_payload=extra_payload,
        memory_class=memory_class,
    )


def test_integration_spawn_with_canon_extra_payload_stamps_protected():
    """End-to-end: ``spawn_memory(extra_payload={"canon": True})`` produces
    an entity whose payload carries the H1c-stamped PROTECTED envelope
    with ``actor=SYSTEM`` and ``via=CANON_SET``. Hazard B closed
    end-to-end.
    """
    graph, _tmpdir, embedder, np = _try_build_graph()
    eid = _spawn(graph, embedder, np, extra_payload={"canon": True})
    ent = graph.entities[eid]
    env = ent.payload.get("lifecycle_status")
    assert env is not None
    assert env["state"] == "protected"
    assert env["set_by"]["actor"] == "system"
    assert env["set_by"]["via"] == "canon_set"
    # And canon=True remains on the payload (we didn't strip it).
    assert ent.payload.get("canon") is True


def test_integration_spawn_with_kind_seed_stamps_protected():
    graph, _tmpdir, embedder, np = _try_build_graph()
    eid = _spawn(graph, embedder, np, extra_payload={"kind": "seed"})
    env = graph.entities[eid].payload["lifecycle_status"]
    assert env["state"] == "protected"
    assert env["set_by"]["actor"] == "system"
    assert env["set_by"]["via"] == "seed_plant"


def test_integration_spawn_with_no_markers_still_stamps_unset():
    graph, _tmpdir, embedder, np = _try_build_graph()
    eid = _spawn(graph, embedder, np)
    env = graph.entities[eid].payload["lifecycle_status"]
    assert env["state"] == "unset"
    assert env["set_by"]["actor"] == "system"
    assert env["set_by"]["via"] == "ingest_unmarked"


def test_integration_caller_extra_payload_dict_not_mutated_with_marker():
    """Critical contract preserved from H1c: when ``spawn_memory`` is
    called with a marker in ``extra_payload``, the caller's
    ``extra_payload`` dict itself must not be mutated. The H1c stamp
    happens on ``spawn_memory``'s LOCAL payload (which is a fresh dict
    populated via ``dict.update``).
    """
    graph, _tmpdir, embedder, np = _try_build_graph()
    extra: Dict[str, Any] = {"canon": True, "custom_key": "value"}
    snapshot = copy.deepcopy(extra)
    _spawn(graph, embedder, np, extra_payload=extra)
    assert extra == snapshot
    assert "lifecycle_status" not in extra


def test_integration_explicit_envelope_wins_over_extra_payload_canon():
    graph, _tmpdir, embedder, np = _try_build_graph()
    explicit = _explicit_envelope_dict(state=LifecycleState.RELEASED)
    extra = {"canon": True, "lifecycle_status": explicit}
    eid = _spawn(graph, embedder, np, extra_payload=extra)
    env = graph.entities[eid].payload["lifecycle_status"]
    # Explicit wins; canon ignored at the lifecycle layer.
    assert env["state"] == "released"
    assert env["set_by"]["via"] == "release_promotion"
    assert env["set_by"]["at"] == FIXED_AT


def test_integration_malformed_explicit_envelope_raises_no_entity_created():
    """If the explicit envelope is malformed, spawn_memory raises and
    no entity is added to the graph. The legacy marker on the same
    payload does NOT cause the helper to silently swap the malformed
    envelope for a derived one.
    """
    graph, _tmpdir, embedder, np = _try_build_graph()
    bad = _explicit_envelope_dict()
    bad["state"] = "totally_made_up"
    extra = {"canon": True, "lifecycle_status": bad}
    initial_eids = set(graph.entities.keys())
    with pytest.raises(LifecycleStateError):
        _spawn(graph, embedder, np, extra_payload=extra)
    assert set(graph.entities.keys()) == initial_eids


# ===========================================================================
# Section E -- persistence: stamp survives flush + reload
# ===========================================================================


def test_integration_stamped_protected_envelope_persists_through_flush_reload():
    """End-to-end disk round-trip: spawn a canon=True row → flush_node →
    discard graph → reload from disk → the PROTECTED envelope is intact
    on the rehydrated entity.
    """
    memory_graph = pytest.importorskip("torment_service.memory_graph")
    embeddings = pytest.importorskip("torment_service.embeddings")
    np = pytest.importorskip("numpy")

    MemoryGraph = memory_graph.MemoryGraph
    HashEmbedding = embeddings.HashEmbedding

    tmpdir = tempfile.mkdtemp(prefix="torment_q2d_slice3_persist_")
    embedder = HashEmbedding(dim=8)

    graph_a = MemoryGraph(tmpdir, embedder=embedder)
    eid = _spawn(graph_a, embedder, np, extra_payload={"canon": True})
    graph_a.flush_node(eid)
    env_before = dict(graph_a.entities[eid].payload["lifecycle_status"])
    assert env_before["state"] == "protected"
    assert env_before["set_by"]["actor"] == "system"
    assert env_before["set_by"]["via"] == "canon_set"

    # Fresh graph instance against the same data dir -> triggers load.
    graph_b = MemoryGraph(tmpdir, embedder=embedder)
    ent = graph_b.entities.get(eid)
    assert ent is not None, "entity did not rehydrate"
    env_after = ent.payload.get("lifecycle_status")
    assert env_after is not None
    assert env_after == env_before


# ===========================================================================
# Section F -- cross-slice composition: Q2-F + validator + read shim
# ===========================================================================


def test_stamped_envelope_passes_q2f_primitive():
    """A Slice 3 stamped PROTECTED envelope is row-authoritative and so
    passes the Q2-F enforcement primitive. Confirms Slice 3 + Q2-F
    compose: a new protected row can be passed through the eventual
    enforcement guard with no surprises.
    """
    ensure = _ensure()
    payload: Dict[str, Any] = {"canon": True}
    ensure(payload)
    env = read_lifecycle_envelope(payload)
    assert assert_lifecycle_row_authoritative(env) is None


def test_stamped_envelope_revalidates_through_validator():
    """The H1c-stamped envelope (in either branch) is a canonical Q2
    envelope; re-validating its serialized form must succeed.
    """
    ensure = _ensure()
    for payload_seed in ({"canon": True}, {"kind": "identity"}, {}):
        payload = dict(payload_seed)
        ensure(payload)
        env_dict = payload["lifecycle_status"]
        revalidated = validate_lifecycle_envelope(env_dict)
        # Round-trip is byte-identical for the dict form.
        assert revalidated.to_dict() == env_dict


def test_stamped_envelope_round_trips_through_read_shim():
    """A payload stamped by H1c (Slice 3) round-trips through
    ``read_lifecycle_envelope`` -- the read shim sees the now-present
    explicit envelope and takes branch 2 (validate-and-return), NOT
    branch 3a (legacy derivation). The stamp IS the explicit envelope,
    so the read shim treats it identically to any other present
    envelope. This proves the two slices compose cleanly: Slice 3
    stamps, Slice 2 reads it back unchanged.
    """
    ensure = _ensure()
    payload: Dict[str, Any] = {"canon": True}
    ensure(payload)
    env_via_read = read_lifecycle_envelope(payload)
    assert env_via_read.state is LifecycleState.PROTECTED
    assert env_via_read.set_by.actor is LifecycleActor.SYSTEM
    assert env_via_read.set_by.via is LifecycleSetVia.CANON_SET


# ===========================================================================
# Section G -- actor distinction: SAME payload, two paths, two actors
# ===========================================================================


def test_actor_distinction_read_path_yields_migration():
    """The read-side Slice 2 path on a legacy-canon payload (no envelope)
    yields ``actor=MIGRATION``. This is the "legacy origin" reading.
    """
    payload: Dict[str, Any] = {"canon": True}
    env = read_lifecycle_envelope(payload)
    assert env.state is LifecycleState.PROTECTED
    assert env.set_by.actor is LifecycleActor.MIGRATION
    assert env.set_by.via is LifecycleSetVia.CANON_SET
    # The read shim does NOT mutate the payload (legacy row stays
    # envelope-less on disk).
    assert "lifecycle_status" not in payload


def test_actor_distinction_write_path_yields_system():
    """The write-side Slice 3 path on the SAME canon=True payload yields
    ``actor=SYSTEM``. This is the "Q2-era runtime assertion" stamping.
    """
    ensure = _ensure()
    payload: Dict[str, Any] = {"canon": True}
    ensure(payload)
    env = payload["lifecycle_status"]
    assert env["state"] == "protected"
    assert env["set_by"]["actor"] == "system"
    assert env["set_by"]["via"] == "canon_set"


def test_actor_distinction_same_marker_two_origins_two_actors():
    """Side-by-side: identical legacy markers, two paths, two actors.
    The audit story is preserved: an inspector can tell whether a
    PROTECTED interpretation came from read-time legacy inference
    (MIGRATION) or write-time runtime assertion (SYSTEM).
    """
    ensure = _ensure()
    legacy_payload: Dict[str, Any] = {"canon": True}
    fresh_payload: Dict[str, Any] = {"canon": True}

    read_env = read_lifecycle_envelope(legacy_payload)
    ensure(fresh_payload)
    write_env_dict = fresh_payload["lifecycle_status"]

    # State and via are identical (same marker, same precedence).
    assert read_env.state.value == write_env_dict["state"] == "protected"
    assert read_env.set_by.via.value == write_env_dict["set_by"]["via"] \
        == "canon_set"
    # Actors are DIFFERENT — this is the load-bearing audit distinction.
    assert read_env.set_by.actor.value == "migration"
    assert write_env_dict["set_by"]["actor"] == "system"


# ===========================================================================
# Section H -- H1b inspector regression: new protected-marker rows now
# surface as PROTECTED/SYSTEM rather than H1c UNSET via resource_provenance.
# ===========================================================================


def test_h1b_inspector_surfaces_new_protected_row_as_protected_system():
    """Cross-slice payoff of Slice 3: when the H1b
    ``_lifecycle_field_for_payload`` helper processes a payload that
    was stamped by the Slice 3 ``_ensure_lifecycle_envelope`` (carrying
    ``canon=True``), the inspector now surfaces
    ``state=protected / actor=system / via=canon_set`` instead of the
    pre-Slice-3 ``state=unset / actor=system / via=ingest_unmarked``.

    This is the operator-visible artifact closing Hazard B and the
    test that catches silent removal of the Slice 3 wiring inside
    ``_ensure_lifecycle_envelope``.
    """
    mcp_server = pytest.importorskip("torment_service.mcp_server")
    _lifecycle_field_for_payload = mcp_server._lifecycle_field_for_payload

    ensure = _ensure()
    payload: Dict[str, Any] = {"canon": True,
                                "summary": "new protected row"}
    ensure(payload)
    surfaced = _lifecycle_field_for_payload(payload)
    assert "error" not in surfaced
    assert surfaced["state"] == "protected"
    assert surfaced["set_by"]["actor"] == "system"
    assert surfaced["set_by"]["via"] == "canon_set"
    # And explicitly: this is NOT the pre-Slice-3 H1c-default shape.
    assert surfaced["set_by"]["via"] != "ingest_unmarked"
