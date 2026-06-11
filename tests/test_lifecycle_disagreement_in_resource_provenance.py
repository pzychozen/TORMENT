"""tests/test_lifecycle_disagreement_in_resource_provenance.py

Q2-D Slice 4-wiring-A tests: the H1b ``resource_provenance`` inspector
now surfaces the Slice 4 disagreement detector's output as a per-row
``lifecycle_disagreement`` field, observability-only.

After this slice, every row in ``resource_provenance``'s response carries:

  "lifecycle_disagreement": None | {
      "kind": "state_mismatch" | "authority_mismatch",
      "explicit_state": <state value>,
      "explicit_is_authoritative_on_row": <bool>,
      "explicit_via": <via value>,
      "derived_via": <via value>
  }

The field is ALWAYS present (None when no disagreement). Malformed
envelopes produce None for this field (the existing ``lifecycle_status``
field already carries the error sentinel; the disagreement field stays
quiet to avoid duplicating noise).

Out of scope for this slice (and these tests):

* write-side disagreement logging (Slice 4-wiring-B)
* raising on disagreement
* stats summary in the inspector's stats block
* reader migration (Q2-D Slice 5+)
* new MCP resource or tier-gate widening
* baton/R3, review-queue, closure-ledger, Q3, custom DB work
"""
from __future__ import annotations

import asyncio
import copy
import json
import os
import sys
import tempfile
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
)


FIXED_AT = 1_716_300_000


# ---------------------------------------------------------------------------
# Local builders
# ---------------------------------------------------------------------------


def _row_authoritative_envelope_dict(
    state: LifecycleState,
    via: LifecycleSetVia,
    actor: LifecycleActor = LifecycleActor.SYSTEM,
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
    actor: LifecycleActor = LifecycleActor.SYSTEM,
    at: int = FIXED_AT,
) -> Dict[str, Any]:
    return LifecycleStatus(
        state=state,
        is_authoritative_on_row=False,
        requires_join=LifecycleJoinTarget(
            side_channel=side_channel, join_key=join_key,
        ),
        set_by=LifecycleSetBy(actor=actor, via=via, at=at),
        history_ref=None,
    ).to_dict()


# ===========================================================================
# Section A -- unit tests on _lifecycle_disagreement_field_for_payload
# ===========================================================================


@pytest.fixture(scope="module")
def disagreement_field():
    """Lazy import: skip the module if MCP deps aren't available."""
    mcp_server = pytest.importorskip("torment_service.mcp_server")
    return mcp_server._lifecycle_disagreement_field_for_payload


def test_helper_returns_none_when_no_envelope_present(disagreement_field):
    """No explicit envelope on the payload -> no disagreement reportable.
    Returns None even when legacy markers are present.
    """
    assert disagreement_field({}) is None
    assert disagreement_field({"canon": True}) is None
    assert disagreement_field({"kind": "seed"}) is None


def test_helper_returns_none_when_no_legacy_marker(disagreement_field):
    """Explicit envelope present but no legacy protected marker ->
    no disagreement possible. Returns None for any explicit state.
    """
    explicit = _row_authoritative_envelope_dict(
        state=LifecycleState.RELEASED,
        via=LifecycleSetVia.RELEASE_PROMOTION,
        actor=LifecycleActor.OPERATOR,
    )
    assert disagreement_field({"lifecycle_status": explicit}) is None
    assert disagreement_field({
        "lifecycle_status": explicit, "text": "no markers",
    }) is None


def test_helper_returns_none_on_full_agreement(disagreement_field):
    """Explicit PROTECTED row-authoritative via=CANON_SET + canon=True ->
    full agreement, no disagreement.
    """
    explicit = _row_authoritative_envelope_dict(
        state=LifecycleState.PROTECTED,
        via=LifecycleSetVia.CANON_SET,
        actor=LifecycleActor.MIGRATION,
    )
    payload = {"lifecycle_status": explicit, "canon": True}
    assert disagreement_field(payload) is None


def test_helper_returns_none_on_provenance_drift(disagreement_field):
    """Explicit PROTECTED row-authoritative via=SCRATCH_PROMOTION +
    canon=True -> both sides agree on load-bearing facts but via differs.
    Slice 4 deliberately does NOT surface provenance drift.
    """
    explicit = _row_authoritative_envelope_dict(
        state=LifecycleState.PROTECTED,
        via=LifecycleSetVia.SCRATCH_PROMOTION,
        actor=LifecycleActor.OPERATOR,
    )
    payload = {"lifecycle_status": explicit, "canon": True}
    assert disagreement_field(payload) is None


def test_helper_returns_state_mismatch_dict(disagreement_field):
    """Explicit UNSET + canon=True -> STATE_MISMATCH dict with the five
    expected fields, in JSON-safe shape.
    """
    explicit = _row_authoritative_envelope_dict(
        state=LifecycleState.UNSET,
        via=LifecycleSetVia.UNSET_DEFAULT,
        actor=LifecycleActor.MIGRATION,
    )
    payload = {"lifecycle_status": explicit, "canon": True}
    result = disagreement_field(payload)
    assert result is not None
    assert result == {
        "kind": "state_mismatch",
        "explicit_state": "unset",
        "explicit_is_authoritative_on_row": True,
        "explicit_via": "unset_default",
        "derived_via": "canon_set",
    }


def test_helper_returns_authority_mismatch_dict(disagreement_field):
    """Explicit PROTECTED + join-required + canon=True -> AUTHORITY_MISMATCH
    dict with the five expected fields.
    """
    explicit = _join_required_envelope_dict(
        state=LifecycleState.PROTECTED,
        side_channel=SideChannel.REVIEW_QUEUE,
        via=LifecycleSetVia.GATE1_REFUSAL,
    )
    payload = {"lifecycle_status": explicit, "canon": True}
    result = disagreement_field(payload)
    assert result is not None
    assert result == {
        "kind": "authority_mismatch",
        "explicit_state": "protected",
        "explicit_is_authoritative_on_row": False,
        "explicit_via": "gate1_refusal",
        "derived_via": "canon_set",
    }


def test_helper_returns_none_on_malformed_envelope(disagreement_field):
    """Malformed envelope -> the detector raises LifecycleStateError, the
    helper swallows it and returns None. The lifecycle_status field
    already carries the malformed-envelope error sentinel for the same
    row; duplicating that signal here would be noise without new signal.
    """
    payload = {
        "lifecycle_status": {"state": "totally_made_up"},
        "canon": True,
    }
    assert disagreement_field(payload) is None


def test_helper_returns_none_on_non_dict_lifecycle_status(disagreement_field):
    """A non-dict lifecycle_status (string, int, list) causes the
    validator inside the detector to raise; the helper swallows it.
    """
    for bad in ("released", 42, ["state", "released"]):
        payload = {"lifecycle_status": bad, "canon": True}
        assert disagreement_field(payload) is None


def test_helper_dict_is_json_serializable(disagreement_field):
    """The helper's non-None output must be cleanly JSON-serializable;
    the resource_provenance response is serialized via json.dumps.
    """
    explicit = _row_authoritative_envelope_dict(
        state=LifecycleState.UNSET,
        via=LifecycleSetVia.UNSET_DEFAULT,
    )
    payload = {"lifecycle_status": explicit, "canon": True}
    result = disagreement_field(payload)
    # Round-trip through json.dumps + json.loads.
    encoded = json.dumps(result)
    decoded = json.loads(encoded)
    assert decoded == result


def test_helper_does_not_mutate_payload(disagreement_field):
    """The helper must not mutate the input payload, in either branch
    (disagreement present or absent).
    """
    explicit = _row_authoritative_envelope_dict(
        state=LifecycleState.UNSET,
        via=LifecycleSetVia.UNSET_DEFAULT,
    )
    for payload in (
        {},
        {"canon": True},
        {"lifecycle_status": explicit, "canon": True},
    ):
        snapshot = copy.deepcopy(payload)
        disagreement_field(payload)
        assert payload == snapshot


# ===========================================================================
# Section B -- integration tests through the actual resource_provenance
# MCP handler. Mirrors the harness pattern from
# tests/test_lifecycle_in_resource_provenance.py and
# tests/test_lifecycle_conformance_meta.py.
# ===========================================================================


# Deterministic eids for the mixed-corpus fixture.
EID_CLEAN = 8001         # no envelope, no markers -> lifecycle_status=UNSET,
                          #                            disagreement=None
EID_STATE_MISMATCH = 8002 # explicit UNSET + canon=True -> STATE_MISMATCH
EID_AUTH_MISMATCH = 8003  # explicit PROTECTED+join + canon=True ->
                          #                            AUTHORITY_MISMATCH
EID_MALFORMED = 8004      # explicit bogus envelope + canon=True ->
                          #     lifecycle_status=error sentinel,
                          #     disagreement=None (no duplication)


def _try_build_mixed_corpus():
    """Build a fabric with the four-row mixed corpus, return
    (fabric, ws, ag) or skip on missing deps.
    """
    try:
        from torment_service.fabric import TormentFabric
        from torment_service.memory_graph import MemoryGraph
        from torment_service.kernel.seed_entities import SeedEntity
        from torment_service.embeddings import HashEmbedding
        import numpy as np
    except ImportError as exc:
        pytest.skip(f"fabric/graph deps not available: {exc}")

    tmpdir = tempfile.mkdtemp(prefix="torment_q2d_s4wA_")
    os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
    fabric = TormentFabric(data_dir=tmpdir)
    workspace_id = "ws_q2d_s4wA"
    agent_id = "agent_q2d_s4wA"
    ak = fabric._agent_key(workspace_id, agent_id)

    embedder = HashEmbedding(dim=8)
    graph_dir = os.path.join(tmpdir, "workspaces", workspace_id, "agents",
                              agent_id, "private")
    os.makedirs(graph_dir, exist_ok=True)
    graph = MemoryGraph(graph_dir, embedder=embedder)
    fabric.private_graphs[ak] = graph

    zero = np.zeros(3, dtype=float)

    # Row 1: CLEAN -- no envelope, no markers. lifecycle_status -> UNSET via
    # shim, disagreement -> None.
    graph.entities[EID_CLEAN] = SeedEntity(
        eid=EID_CLEAN, born_step=1, channel=0,
        pos=zero.copy(), vel=zero.copy(), vel0=zero.copy(),
        payload={"summary": "clean row, no envelope, no markers", "step": 1,
                  "provenance": {"source_type": "user_input"}},
    )

    # Row 2: STATE_MISMATCH -- explicit UNSET + canon=True.
    explicit_unset = _row_authoritative_envelope_dict(
        state=LifecycleState.UNSET,
        via=LifecycleSetVia.UNSET_DEFAULT,
        actor=LifecycleActor.MIGRATION,
    )
    graph.entities[EID_STATE_MISMATCH] = SeedEntity(
        eid=EID_STATE_MISMATCH, born_step=2, channel=0,
        pos=zero.copy(), vel=zero.copy(), vel0=zero.copy(),
        payload={"summary": "explicit unset + canon", "step": 2,
                  "provenance": {"source_type": "user_input"},
                  "canon": True,
                  "lifecycle_status": explicit_unset},
    )

    # Row 3: AUTHORITY_MISMATCH -- explicit PROTECTED join-required + canon=True.
    explicit_join = _join_required_envelope_dict(
        state=LifecycleState.PROTECTED,
        side_channel=SideChannel.REVIEW_QUEUE,
        via=LifecycleSetVia.GATE1_REFUSAL,
    )
    graph.entities[EID_AUTH_MISMATCH] = SeedEntity(
        eid=EID_AUTH_MISMATCH, born_step=3, channel=0,
        pos=zero.copy(), vel=zero.copy(), vel0=zero.copy(),
        payload={"summary": "explicit protected join + canon", "step": 3,
                  "provenance": {"source_type": "user_input"},
                  "canon": True,
                  "lifecycle_status": explicit_join},
    )

    # Row 4: MALFORMED -- explicit bogus envelope + canon=True.
    # lifecycle_status field surfaces the error sentinel; disagreement
    # stays None (no duplication of the same failure signal).
    bad = _row_authoritative_envelope_dict(
        state=LifecycleState.UNSET, via=LifecycleSetVia.UNSET_DEFAULT,
    )
    bad["state"] = "totally_made_up"
    graph.entities[EID_MALFORMED] = SeedEntity(
        eid=EID_MALFORMED, born_step=4, channel=0,
        pos=zero.copy(), vel=zero.copy(), vel0=zero.copy(),
        payload={"summary": "malformed envelope + canon", "step": 4,
                  "provenance": {"source_type": "user_input"},
                  "canon": True,
                  "lifecycle_status": bad},
    )

    return fabric, workspace_id, agent_id


def _invoke_resource_provenance(fabric, workspace_id, agent_id):
    """Build the MCP server at guarded tier, invoke resource_provenance
    via read_resource, return the parsed JSON response.
    """
    try:
        import torment_service.mcp_server as mcp_mod
    except ImportError as exc:
        pytest.skip(f"mcp_server unavailable: {exc}")

    old_tier = os.environ.get("TORMENT_MCP_EXPOSURE_TIER")
    os.environ["TORMENT_MCP_EXPOSURE_TIER"] = "guarded"
    os.environ.setdefault("TORMENT_MCP_DATA_DIR", fabric.data_dir)
    os.environ.setdefault("TORMENT_MCP_WORKSPACE_ID", workspace_id)
    os.environ.setdefault("TORMENT_MCP_AGENT_ID", agent_id)

    try:
        mcp_mod._fabric = fabric
        mcp_mod._client_ctx = None
        mcp = mcp_mod.create_mcp_server()
        uri = (f"torment://workspace/{workspace_id}/agent/{agent_id}"
               f"/provenance")
        contents = asyncio.run(mcp.read_resource(uri))
        if hasattr(contents, "__iter__"):
            first = next(iter(contents))
        else:
            first = contents
        text = (getattr(first, "content", None)
                or getattr(first, "text", None)
                or str(first))
        return json.loads(text)
    finally:
        if old_tier is None:
            os.environ.pop("TORMENT_MCP_EXPOSURE_TIER", None)
        else:
            os.environ["TORMENT_MCP_EXPOSURE_TIER"] = old_tier


@pytest.fixture(scope="module")
def inspector_response():
    """Build the mixed corpus once per module, call the inspector once,
    return the parsed JSON. Section B's assertions are all read facets
    of this one response.
    """
    fabric, ws, ag = _try_build_mixed_corpus()
    return _invoke_resource_provenance(fabric, ws, ag)


def _row_by_eid(response, eid: int) -> Dict[str, Any]:
    memories = response.get("memories", [])
    matches = [m for m in memories if int(m["eid"]) == eid]
    assert len(matches) == 1, (
        f"expected exactly one row for eid={eid}; found {len(matches)} "
        f"in {[m['eid'] for m in memories]}"
    )
    return matches[0]


def test_integration_state_mismatch_row_surfaces_disagreement(inspector_response):
    """A row with explicit UNSET + canon=True surfaces its
    lifecycle_disagreement field as the STATE_MISMATCH report.
    """
    row = _row_by_eid(inspector_response, EID_STATE_MISMATCH)
    assert "lifecycle_disagreement" in row
    disagreement = row["lifecycle_disagreement"]
    assert disagreement is not None
    assert disagreement["kind"] == "state_mismatch"
    assert disagreement["explicit_state"] == "unset"
    assert disagreement["explicit_is_authoritative_on_row"] is True
    assert disagreement["explicit_via"] == "unset_default"
    assert disagreement["derived_via"] == "canon_set"


def test_integration_authority_mismatch_row_surfaces_disagreement(
    inspector_response,
):
    """A row with explicit PROTECTED + join-required + canon=True
    surfaces lifecycle_disagreement as the AUTHORITY_MISMATCH report.
    """
    row = _row_by_eid(inspector_response, EID_AUTH_MISMATCH)
    disagreement = row["lifecycle_disagreement"]
    assert disagreement is not None
    assert disagreement["kind"] == "authority_mismatch"
    assert disagreement["explicit_state"] == "protected"
    assert disagreement["explicit_is_authoritative_on_row"] is False
    assert disagreement["explicit_via"] == "gate1_refusal"
    assert disagreement["derived_via"] == "canon_set"


def test_integration_no_disagreement_row_has_field_none(inspector_response):
    """A clean row (no envelope, no markers) carries
    lifecycle_disagreement=None. Always-present field with None when
    no disagreement -- predictable schema for operator queries.
    """
    row = _row_by_eid(inspector_response, EID_CLEAN)
    assert "lifecycle_disagreement" in row
    assert row["lifecycle_disagreement"] is None
    # And the lifecycle_status field on the clean row carries the
    # canonical UNSET shape (regression sanity).
    assert row["lifecycle_status"]["state"] == "unset"


def test_integration_malformed_row_has_status_error_and_disagreement_none(
    inspector_response,
):
    """A row with a malformed explicit envelope: lifecycle_status carries
    the error sentinel (existing H1b behavior); lifecycle_disagreement
    is None (Slice 4-wiring-A intentional non-duplication).
    """
    row = _row_by_eid(inspector_response, EID_MALFORMED)
    # The lifecycle_status field carries the malformed-envelope error.
    assert "lifecycle_status" in row
    assert "error" in row["lifecycle_status"]
    assert "state" in row["lifecycle_status"]["error"]
    # And the disagreement field is None -- we don't duplicate the error.
    assert "lifecycle_disagreement" in row
    assert row["lifecycle_disagreement"] is None


def test_integration_mixed_corpus_all_distinguishable(inspector_response):
    """All four rows appear in one response with their distinct
    disagreement shapes. No row poisons another row's disagreement
    field; the corrupt row's None coexists with the other rows'
    correctly-populated reports.
    """
    eids_seen = {int(m["eid"]) for m in inspector_response.get("memories", [])}
    expected = {EID_CLEAN, EID_STATE_MISMATCH, EID_AUTH_MISMATCH,
                EID_MALFORMED}
    assert expected.issubset(eids_seen)

    # Pull each row's disagreement value.
    clean = _row_by_eid(inspector_response, EID_CLEAN)
    state_mm = _row_by_eid(inspector_response, EID_STATE_MISMATCH)
    auth_mm = _row_by_eid(inspector_response, EID_AUTH_MISMATCH)
    malformed = _row_by_eid(inspector_response, EID_MALFORMED)

    assert clean["lifecycle_disagreement"] is None
    assert state_mm["lifecycle_disagreement"]["kind"] == "state_mismatch"
    assert auth_mm["lifecycle_disagreement"]["kind"] == "authority_mismatch"
    assert malformed["lifecycle_disagreement"] is None


def test_integration_existing_fields_preserved(inspector_response):
    """Slice 4-wiring-A is additive: every pre-existing per-row key
    (eid, provenance, has_provenance, summary, lifecycle_status) still
    appears on each row of the mixed corpus. The new
    lifecycle_disagreement key is purely additive.
    """
    for eid in (EID_CLEAN, EID_STATE_MISMATCH, EID_AUTH_MISMATCH,
                 EID_MALFORMED):
        row = _row_by_eid(inspector_response, eid)
        for key in ("eid", "provenance", "has_provenance", "summary",
                    "lifecycle_status"):
            assert key in row, (
                f"pre-existing field {key!r} missing on eid={eid}"
            )
        # Spot-check: the fixture gave each row a provenance dict.
        assert row["has_provenance"] is True
        assert row["provenance"].get("source_type") == "user_input"


def test_integration_field_is_always_present_on_every_row(inspector_response):
    """The lifecycle_disagreement field is ALWAYS present on every row,
    regardless of whether a disagreement was detected. Locks the
    predictable-schema ratification.
    """
    for memory in inspector_response.get("memories", []):
        assert "lifecycle_disagreement" in memory, (
            f"lifecycle_disagreement missing on eid={memory.get('eid')}"
        )


# ===========================================================================
# Section C -- guarded-tier regression
# ===========================================================================


def test_resource_provenance_still_hidden_at_open_tier():
    """The new lifecycle_disagreement field must not accidentally widen
    the tier gate. The whole resource_provenance MCP resource remains
    hidden at the open tier; the new field stays inside guarded.
    """
    try:
        from tests.test_mcp_resource_gating import _get_resource_uris
    except ImportError as exc:
        pytest.skip(f"tier gate harness unavailable: {exc}")

    uris = _get_resource_uris("open")
    provenance_uris = [u for u in uris if "provenance" in u]
    assert provenance_uris == [], (
        f"resource_provenance leaked to open tier: {provenance_uris}"
    )


def test_resource_provenance_visible_at_guarded_tier():
    """Sanity: the resource_provenance URI is still registered at the
    guarded tier after Slice 4-wiring-A. Regression guard.
    """
    try:
        from tests.test_mcp_resource_gating import _get_resource_uris
    except ImportError as exc:
        pytest.skip(f"tier gate harness unavailable: {exc}")

    uris = _get_resource_uris("guarded")
    provenance_uris = [u for u in uris if "provenance" in u]
    assert len(provenance_uris) >= 1
