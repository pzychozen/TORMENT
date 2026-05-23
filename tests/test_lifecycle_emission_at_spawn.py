"""tests/test_lifecycle_emission_at_spawn.py

Q2-H1c tests for the first explicit write-site lifecycle envelope emission
in ``MemoryGraph.spawn_memory``.

Per the ratified Q2-H1c plan, every new memory row created via
``spawn_memory`` is, on return, guaranteed to carry a ``lifecycle_status``
envelope on its payload:

* Rows with no caller-supplied envelope receive the canonical
  row-authoritative UNSET envelope:
    - ``state = unset``
    - ``is_authoritative_on_row = True``
    - ``set_by.actor = SYSTEM``
    - ``set_by.via  = INGEST_UNMARKED``
    - ``set_by.at   = int(time.time())``
    - ``requires_join = None``
    - ``history_ref  = None``
* ``UNSET_DEFAULT`` (H1a) and ``INGEST_UNMARKED`` (H1c) deliberately
  remain distinct so the two origins can be distinguished at audit time.
* Caller-supplied envelopes are validated and preserved verbatim. A
  malformed envelope raises ``LifecycleStateError``; no silent downgrade.
* Caller-supplied ``extra_payload`` dicts are not mutated.

Out of scope (explicitly NOT exercised here, deferred to later slices):

* lifecycle enforcement primitive (Q2-F)
* protected dual-source collapse (Q2-D)
* review-queue join formalization (Q2-E)
* baton-lifecycle / Q2-envelope overlap resolution (R3)
* retroactive load-path stamping of legacy rows
* any decision-bearing lifecycle behavior

Test layout:

* Section A -- unit tests on the module-level helper
  ``_ensure_lifecycle_envelope``. Direct, deterministic, no MemoryGraph
  setup overhead.
* Section B -- integration tests through ``MemoryGraph.spawn_memory``,
  including a flush+reload round trip to confirm disk persistence.
* Section C -- bonus regression: confirm the H1b
  ``resource_provenance`` MCP resource now surfaces the H1c stamp
  (``via='ingest_unmarked'``), not the H1a shim derive
  (``via='unset_default'``), once the row is written through
  ``spawn_memory``.
"""
from __future__ import annotations

import copy
import os
import sys
import tempfile
import time
from typing import Any, Dict

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


from torment_service.lifecycle import (
    LifecycleActor,
    LifecycleHistoryRef,
    LifecycleJoinTarget,
    LifecycleSetBy,
    LifecycleSetVia,
    LifecycleState,
    LifecycleStateError,
    LifecycleStatus,
    SideChannel,
    read_lifecycle_envelope,
    validate_lifecycle_envelope,
)


# ---------------------------------------------------------------------------
# Local builders
# ---------------------------------------------------------------------------


FIXED_AT = 1_716_300_000


def _live_envelope_dict(
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


# ===========================================================================
# Section A -- unit tests on the helper _ensure_lifecycle_envelope
# ===========================================================================


def _ensure():
    """Lazy import: the helper is in memory_graph.py which has heavy deps.

    Skip if those deps aren't installed in this environment.
    """
    try:
        from torment_service.memory_graph import _ensure_lifecycle_envelope
    except ImportError as exc:
        pytest.skip(f"memory_graph import failed (deps?): {exc}")
    return _ensure_lifecycle_envelope


# --- Category 1 -- absent envelope -> stamped UNSET ---------------------


def test_absent_envelope_gets_h1c_default_unset():
    """Contract: new payload with no lifecycle_status gets the canonical
    H1c UNSET envelope (actor=SYSTEM, via=INGEST_UNMARKED).
    """
    ensure = _ensure()
    payload: Dict[str, Any] = {"text": "fresh row"}
    ensure(payload)
    env = payload["lifecycle_status"]
    assert env["state"] == "unset"
    assert env["is_authoritative_on_row"] is True
    assert env["requires_join"] is None
    assert env["history_ref"] is None
    assert env["set_by"]["actor"] == "system"
    assert env["set_by"]["via"] == "ingest_unmarked"
    assert isinstance(env["set_by"]["at"], int)


def test_explicit_none_lifecycle_status_treated_as_absent():
    """Contract: payload['lifecycle_status'] = None is treated identically
    to absent; both result in the stamped default UNSET envelope.
    Matches the H1a shim's read-side ergonomics.
    """
    ensure = _ensure()
    payload: Dict[str, Any] = {"lifecycle_status": None, "other": 7}
    ensure(payload)
    env = payload["lifecycle_status"]
    assert env is not None
    assert env["state"] == "unset"
    assert env["set_by"]["via"] == "ingest_unmarked"


def test_h1c_via_distinct_from_h1a_unset_default():
    """Audit-distinguishability guard: the H1c stamp uses INGEST_UNMARKED,
    not UNSET_DEFAULT. UNSET_DEFAULT remains structurally reserved for the
    H1a read-side lazy-derive path, so the two origins can always be told
    apart on inspection.
    """
    ensure = _ensure()
    payload: Dict[str, Any] = {}
    ensure(payload)
    assert payload["lifecycle_status"]["set_by"]["via"] == "ingest_unmarked"
    assert payload["lifecycle_status"]["set_by"]["via"] != "unset_default"


# --- Category 2 -- supplied valid envelope is preserved -----------------


def test_supplied_valid_envelope_is_preserved_verbatim():
    """Contract: a caller-supplied valid envelope is validated and left
    intact. The H1c default stamp does NOT overwrite it, and the
    embedded set_by.at is preserved (no clock rewrite).
    """
    ensure = _ensure()
    supplied = _live_envelope_dict(state=LifecycleState.PROTECTED,
                                    via=LifecycleSetVia.CANON_SET,
                                    actor=LifecycleActor.SYSTEM)
    payload: Dict[str, Any] = {"lifecycle_status": supplied, "other": "data"}
    ensure(payload)
    # Verbatim preserved, including set_by.at
    assert payload["lifecycle_status"] == supplied
    assert payload["lifecycle_status"]["set_by"]["at"] == FIXED_AT
    assert payload["lifecycle_status"]["set_by"]["via"] == "canon_set"


def test_supplied_join_required_envelope_preserved():
    """A more complex envelope (join-required) is also preserved verbatim."""
    ensure = _ensure()
    supplied = LifecycleStatus(
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
    payload: Dict[str, Any] = {"lifecycle_status": supplied}
    ensure(payload)
    assert payload["lifecycle_status"] == supplied
    assert payload["lifecycle_status"]["requires_join"]["side_channel"] \
        == "review_queue"


# --- Category 3 -- supplied malformed envelope raises (loud) ------------


def test_supplied_malformed_unknown_state_raises():
    """Contract: malformed supplied envelopes MUST raise LifecycleStateError.
    No silent downgrade to UNSET. The keystone safety check for H1c.
    """
    ensure = _ensure()
    # Fully-formed envelope shape, but unknown state value -- forces the
    # validator past the missing-key checks into the state-value branch.
    bad = _live_envelope_dict()
    bad["state"] = "totally_made_up"
    with pytest.raises(LifecycleStateError) as exc_info:
        ensure({"lifecycle_status": bad})
    assert exc_info.value.field == "state"
    assert exc_info.value.reason == "unknown_value"


def test_supplied_malformed_missing_key_raises():
    ensure = _ensure()
    bad = _live_envelope_dict()
    del bad["set_by"]
    with pytest.raises(LifecycleStateError) as exc_info:
        ensure({"lifecycle_status": bad})
    assert exc_info.value.field == "set_by"
    assert exc_info.value.reason == "missing_required_key"


def test_supplied_non_dict_envelope_raises():
    """payload['lifecycle_status'] set to a string/number/list must raise,
    not coerce. Same loud-failure contract as the H1a shim.
    """
    ensure = _ensure()
    for bad in ("released", 42, ["state", "released"], 1.5):
        with pytest.raises(LifecycleStateError) as exc_info:
            ensure({"lifecycle_status": bad})
        assert exc_info.value.field == "lifecycle_status"
        assert exc_info.value.reason == "not_a_dict"


# --- Category 4 -- timestamp source -------------------------------------


def test_stamped_at_is_within_recent_wall_clock_window():
    """Contract: set_by.at = int(time.time()) for the H1c default stamp.
    Sandwich the call between two wall-clock reads.
    """
    ensure = _ensure()
    before = int(time.time())
    payload: Dict[str, Any] = {}
    ensure(payload)
    after = int(time.time())
    at = payload["lifecycle_status"]["set_by"]["at"]
    assert isinstance(at, int)
    assert at >= before
    assert at <= after


# --- Category 5 -- stamped envelope round-trips through H1a reader ------


def test_stamped_envelope_round_trips_through_read_lifecycle_envelope():
    """Cross-slice consistency: a row stamped by H1c reads back as the same
    typed LifecycleStatus when fetched via the H1a read shim.
    """
    ensure = _ensure()
    payload: Dict[str, Any] = {"text": "x"}
    ensure(payload)
    env_dict = payload["lifecycle_status"]
    typed = read_lifecycle_envelope(payload)
    # The shim should NOT lazily derive when an envelope is present; it
    # should validate-and-return what's on the row.
    assert typed.state is LifecycleState.UNSET
    assert typed.set_by.via is LifecycleSetVia.INGEST_UNMARKED
    assert typed.set_by.actor is LifecycleActor.SYSTEM
    assert typed.to_dict() == env_dict


def test_stamped_envelope_revalidates_cleanly():
    """The stamped envelope must itself pass validate_lifecycle_envelope.
    No special-case shapes should leak out of the helper.
    """
    ensure = _ensure()
    payload: Dict[str, Any] = {}
    ensure(payload)
    revalidated = validate_lifecycle_envelope(payload["lifecycle_status"])
    assert revalidated.state is LifecycleState.UNSET


# ===========================================================================
# Section B -- integration tests through MemoryGraph.spawn_memory
# ===========================================================================


def _try_build_graph():
    """Construct a fresh MemoryGraph in a temp dir. Skip on missing deps."""
    try:
        from torment_service.memory_graph import MemoryGraph
        from torment_service.embeddings import HashEmbedding
        import numpy as np
    except ImportError as exc:
        pytest.skip(f"memory_graph deps not available: {exc}")
    tmpdir = tempfile.mkdtemp(prefix="torment_h1c_test_")
    embedder = HashEmbedding(dim=8)
    graph = MemoryGraph(tmpdir, embedder=embedder)
    return graph, tmpdir, embedder, np


def _spawn(graph, embedder, np, extra_payload=None, memory_class="core"):
    """Spawn a default-ish memory row, return its eid."""
    emb = np.zeros(embedder.dim, dtype=np.float32)
    return graph.spawn_memory(
        summary="test row",
        embedding=emb,
        mtype="episode",
        strength=0.5,
        confidence=0.5,
        half_life_days=30.0,
        canon=False,
        user_id="default",
        step=0,
        extra_payload=extra_payload,
        memory_class=memory_class,
    )


def test_integration_spawn_memory_default_row_has_h1c_envelope():
    graph, _tmpdir, embedder, np = _try_build_graph()
    eid = _spawn(graph, embedder, np)
    ent = graph.entities[eid]
    env = ent.payload.get("lifecycle_status")
    assert env is not None
    assert env["state"] == "unset"
    assert env["set_by"]["actor"] == "system"
    assert env["set_by"]["via"] == "ingest_unmarked"
    assert env["is_authoritative_on_row"] is True
    assert env["requires_join"] is None


def test_integration_spawn_memory_with_supplied_envelope_preserves_it():
    graph, _tmpdir, embedder, np = _try_build_graph()
    supplied = _live_envelope_dict(state=LifecycleState.RELEASED,
                                    via=LifecycleSetVia.RELEASE_PROMOTION,
                                    actor=LifecycleActor.OPERATOR)
    eid = _spawn(graph, embedder, np,
                  extra_payload={"lifecycle_status": supplied})
    ent = graph.entities[eid]
    assert ent.payload["lifecycle_status"] == supplied


def test_integration_spawn_memory_malformed_supplied_envelope_raises():
    graph, _tmpdir, embedder, np = _try_build_graph()
    bad = _live_envelope_dict()
    bad["state"] = "bogus_state_name"
    initial_eids = set(graph.entities.keys())
    with pytest.raises(LifecycleStateError):
        _spawn(graph, embedder, np,
                extra_payload={"lifecycle_status": bad})
    # No entity should have been added when validation fails.
    assert set(graph.entities.keys()) == initial_eids


def test_integration_caller_extra_payload_dict_not_mutated():
    """Critical: spawn_memory must not mutate the caller's extra_payload."""
    graph, _tmpdir, embedder, np = _try_build_graph()
    extra: Dict[str, Any] = {"custom_key": "custom_value"}
    snapshot = copy.deepcopy(extra)
    _spawn(graph, embedder, np, extra_payload=extra)
    assert extra == snapshot
    assert "lifecycle_status" not in extra


def test_integration_envelope_persists_through_flush_and_reload():
    """End-to-end: stamp → flush → discard graph → reload from disk →
    envelope still on the rehydrated entity's payload.
    """
    try:
        from torment_service.memory_graph import MemoryGraph
        from torment_service.embeddings import HashEmbedding
        import numpy as np
    except ImportError as exc:
        pytest.skip(f"memory_graph deps not available: {exc}")

    tmpdir = tempfile.mkdtemp(prefix="torment_h1c_persist_")
    embedder = HashEmbedding(dim=8)

    graph_a = MemoryGraph(tmpdir, embedder=embedder)
    eid = _spawn(graph_a, embedder, np)
    graph_a.flush_node(eid)
    env_before = dict(graph_a.entities[eid].payload["lifecycle_status"])

    # Fresh graph instance against the same data dir -> triggers load
    graph_b = MemoryGraph(tmpdir, embedder=embedder)
    ent = graph_b.entities.get(eid)
    assert ent is not None, "entity did not rehydrate from disk"
    env_after = ent.payload.get("lifecycle_status")
    assert env_after is not None, "lifecycle_status missing after reload"
    assert env_after == env_before


def test_integration_baton_row_gets_both_baton_lifecycle_and_h1c_envelope():
    """R3 coexistence guard: baton rows keep their baton_lifecycle dict AND
    also receive the H1c default UNSET envelope. The baton row's actual
    baton lifecycle stays untouched -- only the Q2 envelope is added.

    The baton_lifecycle requirement of fabric.ingest is enforced at the
    fabric layer, not the graph layer, so direct spawn_memory calls can
    supply any (or no) baton_lifecycle dict. This test exercises the
    graph layer's H1c behavior: it stamps the envelope regardless of
    memory_class, and does not touch baton_lifecycle.
    """
    graph, _tmpdir, embedder, np = _try_build_graph()
    baton_payload = {
        "owner": "user",
        "status": "active",
        "expires_when": "step_after_50",
        "resolution_condition": "user_responds",
    }
    extra = {"baton_lifecycle": dict(baton_payload)}
    eid = _spawn(graph, embedder, np, extra_payload=extra,
                  memory_class="baton")
    ent = graph.entities[eid]
    # H1c envelope present and default-stamped
    env = ent.payload.get("lifecycle_status")
    assert env is not None
    assert env["state"] == "unset"
    assert env["set_by"]["via"] == "ingest_unmarked"
    # baton_lifecycle preserved verbatim
    assert ent.payload.get("baton_lifecycle") == baton_payload


# ===========================================================================
# Section C -- bonus regression: H1b resource_provenance surfaces the H1c
# stamp rather than the H1a shim derive once rows go through spawn_memory.
# ===========================================================================


def test_h1b_resource_provenance_surfaces_h1c_stamp_not_h1a_shim():
    """Cross-slice regression guard: rows written through the H1c stamping
    path should appear in the H1b provenance inspector with
    ``via='ingest_unmarked'`` (the H1c origin), not
    ``via='unset_default'`` (the H1a shim-derived origin). If the H1c
    wiring is silently removed, this test catches it.

    Uses the same helper-level proxy as the H1b test file: invoke the
    H1b row-building helper on a payload that was stamped by H1c.
    """
    try:
        from torment_service.mcp_server import _lifecycle_field_for_payload
    except ImportError as exc:
        pytest.skip(f"mcp_server import unavailable: {exc}")

    ensure = _ensure()
    payload: Dict[str, Any] = {"text": "row stamped by H1c"}
    ensure(payload)
    surfaced = _lifecycle_field_for_payload(payload)
    assert "error" not in surfaced
    assert surfaced["state"] == "unset"
    assert surfaced["set_by"]["actor"] == "system"
    assert surfaced["set_by"]["via"] == "ingest_unmarked"
    # And critically: it is NOT the H1a shim's derive
    assert surfaced["set_by"]["via"] != "unset_default"
