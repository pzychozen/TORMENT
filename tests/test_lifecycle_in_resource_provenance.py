"""tests/test_lifecycle_in_resource_provenance.py

Q2-H1b tests for the first production read-site wiring of
``read_lifecycle_envelope`` -- the per-row ``lifecycle_status`` field
surfaced by the guarded ``resource_provenance`` MCP resource.

Per the ratified Q2-H1b plan, the wiring must:

* surface the canonical row-authoritative UNSET envelope for legacy rows
  (no ``lifecycle_status`` on the payload)
* round-trip valid envelopes through ``.to_dict()``
* surface an inline error sentinel for malformed envelopes (no silent
  downgrade to UNSET, no broken inspector response)
* not mutate the payload
* not change any pre-existing per-row field, the sort order, the limit,
  or the exposure tier gate

Out of scope (deferred to later Q2 slices):

* lifecycle enforcement primitive (Q2-F)
* protected dual-source collapse (Q2-D)
* review-queue join formalization (Q2-E)
* baton-lifecycle coexistence (R3)
* write-side envelope emission (write-side H1)
* any Q3 affect-provenance work

Test structure:

* Section A -- unit tests on the helper ``_lifecycle_field_for_payload``
  that exercise the full contract directly. This is the same code path
  the resource invokes per row.
* Section B -- integration tests that build a TormentFabric, inject
  entities with controlled payloads, and invoke the registered MCP
  ``resource_provenance`` handler to assert the per-row dict shape.
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
    LifecycleJoinTarget,
    LifecycleSetBy,
    LifecycleSetVia,
    LifecycleState,
    LifecycleStatus,
    SideChannel,
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
    """A row-authoritative envelope serialized to its canonical dict shape."""
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
# Section A -- unit tests on _lifecycle_field_for_payload
#
# The helper is the per-row computation the resource invokes. Tests of the
# helper exercise the exact same code path the resource uses; the resource
# wiring just calls it once per row.
# ===========================================================================


@pytest.fixture(scope="module")
def lifecycle_field():
    """Import the helper. Skip the whole module if MCP deps aren't installed
    in this environment (the helper lives in mcp_server.py which imports
    fastmcp). The Windows source-of-truth environment will have these.
    """
    mcp_server = pytest.importorskip("torment_service.mcp_server")
    return mcp_server._lifecycle_field_for_payload


# --- Category 1 -- absent envelope -> canonical UNSET --------------------


def test_legacy_payload_missing_key_yields_unset(lifecycle_field):
    """Contract point 1: legacy row with no lifecycle_status surfaces UNSET."""
    payload = {"text": "hello", "step": 1}
    result = lifecycle_field(payload)
    assert result["state"] == "unset"
    assert result["is_authoritative_on_row"] is True
    assert result["requires_join"] is None
    assert result["history_ref"] is None
    assert result["set_by"]["actor"] == "migration"
    assert result["set_by"]["via"] == "unset_default"


def test_legacy_payload_explicit_none_yields_unset(lifecycle_field):
    """Explicit lifecycle_status=None is treated identically to missing-key,
    per the H1a shim's ratified contract.
    """
    payload = {"text": "hello", "lifecycle_status": None}
    result = lifecycle_field(payload)
    assert result["state"] == "unset"
    assert result["set_by"]["actor"] == "migration"
    assert result["set_by"]["via"] == "unset_default"


# --- Category 2 -- valid envelope round-trips ----------------------------


def test_valid_envelope_round_trips_via_helper(lifecycle_field):
    """Contract point 2: explicit valid envelope round-trips through the
    resource (via the helper) unchanged. The embedded set_by.at MUST be
    preserved -- the helper does not overwrite it.
    """
    envelope = _live_envelope_dict(state=LifecycleState.RELEASED)
    payload = {"text": "released doc", "lifecycle_status": envelope}
    result = lifecycle_field(payload)
    assert result == envelope
    assert result["set_by"]["at"] == FIXED_AT


def test_valid_join_required_envelope_round_trips(lifecycle_field):
    envelope = _join_required_envelope_dict()
    payload = {"text": "pending review", "lifecycle_status": envelope}
    result = lifecycle_field(payload)
    assert result == envelope
    assert result["requires_join"]["side_channel"] == "review_queue"


# --- Category 3 -- mixed rows (helper-level proxy for point 3) ----------


def test_mixed_payloads_helper_emits_correct_per_row_shape(lifecycle_field):
    """Contract point 3: mixed legacy + Q2-aware rows surface correctly.
    Helper-level proof: calling the helper on each payload independently
    produces the right per-row shape.
    """
    envelope = _live_envelope_dict(state=LifecycleState.PROTECTED,
                                    via=LifecycleSetVia.CANON_SET,
                                    actor=LifecycleActor.SYSTEM)
    payloads = [
        {"text": "legacy"},                              # no envelope
        {"text": "explicit none", "lifecycle_status": None},
        {"text": "q2-aware", "lifecycle_status": envelope},
    ]
    results = [lifecycle_field(p) for p in payloads]
    assert results[0]["state"] == "unset"
    assert results[0]["set_by"]["via"] == "unset_default"
    assert results[1]["state"] == "unset"
    assert results[2]["state"] == "protected"
    assert results[2]["set_by"]["via"] == "canon_set"


# --- Category 4 -- malformed envelope surfaces error sentinel -----------


def test_malformed_unknown_state_yields_error_sentinel(lifecycle_field):
    """Contract point 4: malformed present envelope surfaces an explicit
    per-row error sentinel. The shim does NOT silently downgrade.
    """
    bad = {"state": "totally_made_up", "is_authoritative_on_row": True,
           "requires_join": None, "set_by": {"actor": "operator",
                                              "via": "api", "at": 1},
           "history_ref": None}
    payload = {"lifecycle_status": bad}
    result = lifecycle_field(payload)
    assert "error" in result
    assert "state" in result["error"]
    assert "unknown_value" in result["error"]
    # And critically: state is NOT silently 'unset'
    assert result.get("state") != "unset"


def test_malformed_missing_required_key_yields_error_sentinel(lifecycle_field):
    bad = {"state": "released", "is_authoritative_on_row": True,
           "requires_join": None, "history_ref": None}
    # set_by deliberately missing
    payload = {"lifecycle_status": bad}
    result = lifecycle_field(payload)
    assert "error" in result
    assert "set_by" in result["error"]
    assert "missing_required_key" in result["error"]


def test_malformed_non_dict_envelope_yields_error_sentinel(lifecycle_field):
    payload = {"lifecycle_status": "not a dict"}
    result = lifecycle_field(payload)
    assert "error" in result
    assert "lifecycle_status" in result["error"]
    assert "not_a_dict" in result["error"]


# --- Category 5 -- no-mutation guarantee --------------------------------


def test_helper_does_not_mutate_legacy_payload(lifecycle_field):
    payload: Dict[str, Any] = {"text": "hi", "step": 2}
    snapshot = copy.deepcopy(payload)
    lifecycle_field(payload)
    assert payload == snapshot
    assert "lifecycle_status" not in payload


def test_helper_does_not_mutate_present_payload(lifecycle_field):
    envelope = _live_envelope_dict()
    inner_id = id(envelope)
    payload: Dict[str, Any] = {"text": "hi", "lifecycle_status": envelope}
    snapshot = copy.deepcopy(payload)
    lifecycle_field(payload)
    assert payload == snapshot
    assert id(payload["lifecycle_status"]) == inner_id


# --- Category 6 -- result is JSON-serializable --------------------------


def test_helper_result_is_json_serializable(lifecycle_field):
    """The MCP resource serializes the response via json.dumps. The helper
    output must be cleanly serializable in all three branches.
    """
    for payload in (
        {},
        {"lifecycle_status": _live_envelope_dict()},
        {"lifecycle_status": {"state": "bogus"}},  # malformed
    ):
        result = lifecycle_field(payload)
        json.dumps(result)  # must not raise


# ===========================================================================
# Section B -- integration tests on the actual resource_provenance handler
#
# These build a TormentFabric, inject entities directly into the agent's
# private graph (bypassing the ingest write path -- we want controlled
# payload shapes), then invoke the registered MCP resource and assert on
# the JSON response. These tests catch any future regression where the
# helper is correct but the wiring is silently removed.
# ===========================================================================


def _try_import_mcp_module():
    """Best-effort import of the MCP server module. Returns None when the
    environment lacks the FastMCP dependency, in which case the integration
    tests are skipped.
    """
    try:
        import torment_service.mcp_server as mcp_mod
        return mcp_mod
    except ImportError:
        return None


def _try_build_fabric_with_entity(payload: Dict[str, Any]):
    """Build a fabric, inject a single entity with the supplied payload,
    return (fabric, ak, eid) or raise pytest.skip on missing deps.
    """
    np = pytest.importorskip("numpy")
    pytest.importorskip("fastapi")
    from torment_service.fabric import TormentFabric
    from torment_service.memory_graph import MemoryGraph
    from torment_service.kernel.seed_entities import SeedEntity

    tmpdir = tempfile.mkdtemp(prefix="torment_h1b_test_")
    os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
    fabric = TormentFabric(data_dir=tmpdir)
    workspace_id = "ws_h1b"
    agent_id = "agent_h1b"
    ak = fabric._agent_key(workspace_id, agent_id)
    # Ensure a graph exists for this agent. Use the same data layout the
    # fabric expects; bypassing ingest is intentional to control payload.
    graph_dir = os.path.join(tmpdir, "workspaces", workspace_id, "agents",
                             agent_id, "private")
    os.makedirs(graph_dir, exist_ok=True)
    graph = MemoryGraph(graph_dir)
    fabric.private_graphs[ak] = graph
    eid = 1001
    zero = np.zeros(3, dtype=float)
    ent = SeedEntity(
        eid=eid,
        born_step=0,
        channel=0,
        pos=zero.copy(),
        vel=zero.copy(),
        vel0=zero.copy(),
        payload=payload,
    )
    graph.entities[eid] = ent
    return fabric, workspace_id, agent_id, eid


def _invoke_resource_provenance(mcp_mod, fabric, workspace_id, agent_id):
    """Set the singleton fabric on the MCP module, build the server at
    guarded tier, and call resource_provenance via read_resource. Returns
    the parsed JSON response dict.
    """
    old_tier = os.environ.get("TORMENT_MCP_EXPOSURE_TIER")
    os.environ["TORMENT_MCP_EXPOSURE_TIER"] = "guarded"
    os.environ.setdefault("TORMENT_MCP_DATA_DIR", fabric.data_dir)
    os.environ.setdefault("TORMENT_MCP_WORKSPACE_ID", workspace_id)
    os.environ.setdefault("TORMENT_MCP_AGENT_ID", agent_id)

    try:
        mcp_mod._fabric = fabric
        mcp_mod._client_ctx = None
        mcp = mcp_mod.create_mcp_server()
        uri = f"torment://workspace/{workspace_id}/agent/{agent_id}/provenance"
        contents = asyncio.run(mcp.read_resource(uri))
        # FastMCP returns an iterable of ResourceContents; take the first
        # text payload.
        if hasattr(contents, "__iter__"):
            first = next(iter(contents))
        else:
            first = contents
        text = getattr(first, "content", None) or getattr(first, "text", None)
        if text is None:
            text = str(first)
        return json.loads(text)
    finally:
        if old_tier is None:
            os.environ.pop("TORMENT_MCP_EXPOSURE_TIER", None)
        else:
            os.environ["TORMENT_MCP_EXPOSURE_TIER"] = old_tier


def test_integration_legacy_row_surfaces_unset_envelope():
    """End-to-end: a legacy payload reaches the inspector response carrying
    the canonical UNSET envelope. Proves the wiring is in place.
    """
    mcp_mod = _try_import_mcp_module()
    if mcp_mod is None:
        pytest.skip("MCP module unavailable in this environment")

    payload = {"text": "legacy memory body", "step": 7,
               "provenance": {"source_type": "user_input"}}
    fabric, ws, ag, eid = _try_build_fabric_with_entity(payload)
    response = _invoke_resource_provenance(mcp_mod, fabric, ws, ag)

    assert "memories" in response
    memory = next(m for m in response["memories"] if int(m["eid"]) == eid)
    assert "lifecycle_status" in memory
    ls = memory["lifecycle_status"]
    assert ls["state"] == "unset"
    assert ls["is_authoritative_on_row"] is True
    assert ls["set_by"]["actor"] == "migration"
    assert ls["set_by"]["via"] == "unset_default"


def test_integration_existing_provenance_fields_unchanged_by_h1b():
    """Contract point 6: every pre-H1b field is still present and correct.
    The lifecycle_status field is purely additive.
    """
    mcp_mod = _try_import_mcp_module()
    if mcp_mod is None:
        pytest.skip("MCP module unavailable in this environment")

    payload = {"text": "body", "summary": "short summary", "step": 11,
               "provenance": {"source_type": "tool_result",
                              "tool_name": "search",
                              "write_path": "tool_result_ingest"}}
    fabric, ws, ag, eid = _try_build_fabric_with_entity(payload)
    response = _invoke_resource_provenance(mcp_mod, fabric, ws, ag)

    memory = next(m for m in response["memories"] if int(m["eid"]) == eid)
    # Pre-H1b fields, all still present and shaped as before.
    for key in ("eid", "agent_id", "scope", "provenance_type", "summary",
                "provenance", "has_provenance", "created_step"):
        assert key in memory, f"pre-H1b field {key!r} missing"
    assert memory["scope"] == "private"
    assert memory["summary"] == "short summary"
    assert memory["provenance_type"] == "tool_result"
    assert memory["has_provenance"] is True
    assert memory["created_step"] == 11
    # And the additive H1b field is also there.
    assert "lifecycle_status" in memory
