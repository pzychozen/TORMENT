"""tests/test_lifecycle_conformance_meta.py

Q2-H1d conformance meta-test (Path 2 -- test-only).

This file is the boundary witness for the Q2 lifecycle transitional
regime. H1a/H1b/H1c are individually well-tested; this slice proves that
the four lifecycle origins compose correctly *together* through one
``resource_provenance`` response, with no cross-row contamination.

The four origins exercised on a single mixed corpus:

  A. Legacy row
       payload has no ``lifecycle_status`` key (truly pre-Q2).
       Inspector must surface: ``state="unset"``,
       ``set_by.actor="migration"``, ``set_by.via="unset_default"``
       (the H1a read-side shim's lazy-derive shape).

  B. New H1c-stamped row
       written through ``MemoryGraph.spawn_memory`` with no caller-
       supplied envelope.
       Inspector must surface: ``state="unset"``,
       ``set_by.actor="system"``, ``set_by.via="ingest_unmarked"``
       (the H1c write-site stamp).

  C. Explicit valid envelope
       payload supplies a complete, valid envelope (state=released,
       via=release_promotion).
       Inspector must surface it verbatim, preserved through the
       inspector, not overwritten by either the shim or the stamp.

  D. Corrupt envelope
       payload carries a non-null but malformed ``lifecycle_status``
       (a fully-shaped envelope with an unknown state value).
       Inspector must surface an explicit per-row error sentinel,
       never silently downgrade to ``state="unset"``.

The conformance assertions:

  * all four eids appear in one response (no row is silently dropped)
  * each row's lifecycle_status carries its expected origin
  * the corrupt row's failure does NOT prevent the other three rows
    from surfacing correctly (one bad row cannot poison the inspector)
  * no row's lifecycle value leaks into another row
  * each row's pre-H1b provenance fields are still present (additive
    H1b behavior holds across the mixed corpus)

Path C / Q2 framing's P0 test category #7 ("conformance meta-test") is
formally retired by this file.

Out of scope (this is a test-only slice):

  * no production code changes
  * no new MCP fields
  * no stats summary
  * no operator-facing feature
  * no Q2-F enforcement primitive
  * no decision-bearing reads
  * no protected collapse, review-queue join, baton-lifecycle refactor,
    compression/cognition changes, load-path stamping, retroactive
    migration/backfill, Q3, or custom DB/schema work
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
from typing import Any, Dict, List

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


from torment_service.lifecycle import (
    LifecycleActor,
    LifecycleSetBy,
    LifecycleSetVia,
    LifecycleState,
    LifecycleStatus,
)


# ---------------------------------------------------------------------------
# Fixture construction
# ---------------------------------------------------------------------------


FIXED_AT = 1_716_300_000

EID_LEGACY = 9001     # Origin A: no envelope on disk -> shim derives UNSET
EID_STAMPED = 9002    # Origin B: written via spawn_memory -> H1c stamp
EID_EXPLICIT = 9003   # Origin C: caller-supplied valid envelope -> preserved
EID_CORRUPT = 9004    # Origin D: malformed envelope -> error sentinel


def _explicit_envelope_dict() -> Dict[str, Any]:
    """A fully-formed valid envelope, distinguishable from both the H1a
    shim and the H1c stamp by its state/via pair.
    """
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


def _corrupt_envelope_dict() -> Dict[str, Any]:
    """A fully-shaped envelope with one invalid value (unknown state).

    Using a fully-shaped envelope (rather than e.g. ``{"state": "bogus"}``
    alone) routes the validator past the required-key checks into the
    state-value branch, so the surfaced error is the more meaningful
    ``state: unknown_value`` rather than ``is_authoritative_on_row:
    missing_required_key``. Both qualify as "malformed and visible" per
    the H1b error-sentinel contract; this variant best exercises the
    "not silently downgraded to unset" guarantee.
    """
    return {
        "state": "TOTALLY_MADE_UP",
        "is_authoritative_on_row": True,
        "requires_join": None,
        "set_by": {
            "actor": "operator",
            "via": "release_promotion",
            "at": FIXED_AT,
        },
        "history_ref": None,
    }


def _build_mixed_corpus():
    """Construct a fabric with a single agent's private graph holding the
    four origins as separate entities. Returns (fabric, workspace_id,
    agent_id) or skips on missing deps.
    """
    try:
        from torment_service.fabric import TormentFabric
        from torment_service.memory_graph import MemoryGraph
        from torment_service.kernel.seed_entities import SeedEntity
        from torment_service.embeddings import HashEmbedding
        import numpy as np
    except ImportError as exc:
        pytest.skip(f"fabric/graph deps not available: {exc}")

    tmpdir = tempfile.mkdtemp(prefix="torment_h1d_meta_")
    os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
    fabric = TormentFabric(data_dir=tmpdir)
    workspace_id = "ws_h1d"
    agent_id = "agent_h1d"
    ak = fabric._agent_key(workspace_id, agent_id)

    # Build a private graph for this agent at the conventional path.
    embedder = HashEmbedding(dim=8)
    graph_dir = os.path.join(tmpdir, "workspaces", workspace_id, "agents",
                              agent_id, "private")
    os.makedirs(graph_dir, exist_ok=True)
    graph = MemoryGraph(graph_dir, embedder=embedder)
    fabric.private_graphs[ak] = graph

    # Origin A: legacy row -- payload has no lifecycle_status key. Inject
    # directly into the graph to bypass any write-time stamping.
    legacy_payload = {
        "summary": "legacy row, predates Q2",
        "step": 1,
        "provenance": {"source_type": "user_input"},
    }
    zero = np.zeros(3, dtype=float)
    legacy_ent = SeedEntity(
        eid=EID_LEGACY, born_step=1, channel=0,
        pos=zero.copy(), vel=zero.copy(), vel0=zero.copy(),
        payload=legacy_payload,
    )
    graph.entities[EID_LEGACY] = legacy_ent

    # Origin B: new H1c-stamped row -- written through the actual
    # spawn_memory write site so the H1c default-stamping happens for
    # real (not simulated).
    stamped_eid = graph.spawn_memory(
        summary="stamped row, new under H1c",
        embedding=np.zeros(embedder.dim, dtype=np.float32),
        mtype="episode",
        strength=0.5,
        confidence=0.5,
        half_life_days=30.0,
        canon=False,
        user_id="default",
        step=2,
        extra_payload={"provenance": {"source_type": "user_input"}},
        memory_class="core",
    )
    # Rebind to a deterministic eid for inspector lookup. The fabric's
    # internal _next_id is opaque, so override the entity dict directly.
    if stamped_eid != EID_STAMPED:
        ent = graph.entities.pop(stamped_eid)
        ent.eid = EID_STAMPED
        graph.entities[EID_STAMPED] = ent

    # Origin C: explicit valid envelope. Inject directly with the envelope
    # already populated on the payload, so we exercise the "supplied
    # envelope survives the read path" leg.
    explicit_payload = {
        "summary": "explicit envelope row",
        "step": 3,
        "provenance": {"source_type": "user_input"},
        "lifecycle_status": _explicit_envelope_dict(),
    }
    explicit_ent = SeedEntity(
        eid=EID_EXPLICIT, born_step=3, channel=0,
        pos=zero.copy(), vel=zero.copy(), vel0=zero.copy(),
        payload=explicit_payload,
    )
    graph.entities[EID_EXPLICIT] = explicit_ent

    # Origin D: corrupt envelope. Inject a payload with a malformed
    # lifecycle_status -- the inspector must surface this as a per-row
    # error sentinel, NOT silently downgrade it to UNSET, and NOT
    # break the rest of the response.
    corrupt_payload = {
        "summary": "corrupt envelope row",
        "step": 4,
        "provenance": {"source_type": "user_input"},
        "lifecycle_status": _corrupt_envelope_dict(),
    }
    corrupt_ent = SeedEntity(
        eid=EID_CORRUPT, born_step=4, channel=0,
        pos=zero.copy(), vel=zero.copy(), vel0=zero.copy(),
        payload=corrupt_payload,
    )
    graph.entities[EID_CORRUPT] = corrupt_ent

    return fabric, workspace_id, agent_id


def _invoke_resource_provenance(fabric, workspace_id, agent_id):
    """Build the MCP server at guarded tier with our fabric as the
    singleton, then call resource_provenance via read_resource. Returns
    the parsed JSON response.
    """
    mcp_mod = pytest.importorskip("torment_service.mcp_server")

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


# ---------------------------------------------------------------------------
# The conformance meta-test
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def inspector_response():
    """Build the mixed corpus once per module and call the inspector once.
    Subsequent tests assert different facets of the same response, so the
    fixture proves the inspector is exercised exactly once across all
    facets of the conformance witness.
    """
    fabric, ws, ag = _build_mixed_corpus()
    return _invoke_resource_provenance(fabric, ws, ag)


def _row_by_eid(response, eid: int) -> Dict[str, Any]:
    """Locate the inspector's row for a given eid; fail explicitly if
    missing (which would itself be a conformance failure: a row was
    silently dropped).
    """
    memories = response.get("memories", [])
    matches = [m for m in memories if int(m["eid"]) == eid]
    assert len(matches) == 1, (
        f"expected exactly one row for eid={eid}, found {len(matches)} "
        f"in response with eids={[m['eid'] for m in memories]}"
    )
    return matches[0]


def test_all_four_origins_appear_in_one_response(inspector_response):
    """Conformance #1: every constructed row reaches the inspector. No
    silent drop. The inspector composes a single response that contains
    all four origins.
    """
    eids_seen = {int(m["eid"]) for m in inspector_response.get("memories", [])}
    expected = {EID_LEGACY, EID_STAMPED, EID_EXPLICIT, EID_CORRUPT}
    assert expected.issubset(eids_seen), (
        f"missing eids in response: {expected - eids_seen}"
    )
    # And no surprise rows in this controlled corpus.
    assert eids_seen == expected, (
        f"unexpected extra eids in response: {eids_seen - expected}"
    )


def test_legacy_row_surfaces_shim_derived_unset(inspector_response):
    """Conformance #2 (Origin A): a row with no lifecycle_status on its
    payload appears with the H1a shim's lazy-derive shape:
    actor=migration, via=unset_default.
    """
    row = _row_by_eid(inspector_response, EID_LEGACY)
    env = row["lifecycle_status"]
    assert "error" not in env, (
        f"legacy row should not produce error sentinel; got {env!r}"
    )
    assert env["state"] == "unset"
    assert env["is_authoritative_on_row"] is True
    assert env["requires_join"] is None
    assert env["set_by"]["actor"] == "migration"
    assert env["set_by"]["via"] == "unset_default"


def test_stamped_row_surfaces_h1c_default(inspector_response):
    """Conformance #3 (Origin B): a row written via spawn_memory under
    H1c surfaces with the H1c write-site stamp: actor=system,
    via=ingest_unmarked. Critically distinct from the legacy
    shim-derive shape.
    """
    row = _row_by_eid(inspector_response, EID_STAMPED)
    env = row["lifecycle_status"]
    assert "error" not in env
    assert env["state"] == "unset"
    assert env["is_authoritative_on_row"] is True
    assert env["set_by"]["actor"] == "system"
    assert env["set_by"]["via"] == "ingest_unmarked"
    # And critically not the shim's via.
    assert env["set_by"]["via"] != "unset_default"


def test_explicit_valid_row_preserved_verbatim(inspector_response):
    """Conformance #4 (Origin C): a row carrying a complete supplied
    envelope surfaces with that envelope intact, neither overwritten by
    the H1c stamp nor downgraded by the H1a shim.
    """
    row = _row_by_eid(inspector_response, EID_EXPLICIT)
    env = row["lifecycle_status"]
    assert "error" not in env
    assert env["state"] == "released"
    assert env["set_by"]["actor"] == "operator"
    assert env["set_by"]["via"] == "release_promotion"
    assert env["set_by"]["at"] == FIXED_AT
    assert env == _explicit_envelope_dict()


def test_corrupt_row_surfaces_error_sentinel(inspector_response):
    """Conformance #5 (Origin D): a row carrying a malformed envelope
    surfaces an explicit per-row error sentinel. The corrupt row is
    NEVER silently downgraded to ``state="unset"`` -- that would let
    corruption masquerade as a legacy row, the exact failure mode the
    Q2 invariant exists to prevent.
    """
    row = _row_by_eid(inspector_response, EID_CORRUPT)
    env = row["lifecycle_status"]
    # The sentinel shape.
    assert "error" in env, f"expected error sentinel, got {env!r}"
    # And the invariant: NOT downgraded to a real lifecycle state.
    assert env.get("state") != "unset"
    assert "state" not in env
    # The sentinel message should still be specific enough that an
    # operator can pivot to logs (this is a soft assertion; the H1b
    # contract is "field: reason", but exact wording is not doctrine).
    assert isinstance(env["error"], str)
    assert env["error"]  # non-empty


def test_corrupt_row_does_not_poison_other_rows(inspector_response):
    """Conformance #6: a single corrupt envelope does not break the
    response. The legacy, stamped, and explicit rows all still surface
    their correct envelopes alongside the corrupt one. This is the
    "no row poisons another row" guarantee.
    """
    legacy = _row_by_eid(inspector_response, EID_LEGACY)
    stamped = _row_by_eid(inspector_response, EID_STAMPED)
    explicit = _row_by_eid(inspector_response, EID_EXPLICIT)
    # Each of the three healthy rows surfaces its expected via:
    assert legacy["lifecycle_status"]["set_by"]["via"] == "unset_default"
    assert stamped["lifecycle_status"]["set_by"]["via"] == "ingest_unmarked"
    assert explicit["lifecycle_status"]["set_by"]["via"] == "release_promotion"


def test_no_lifecycle_value_leaks_across_rows(inspector_response):
    """Conformance #7: every row's lifecycle_status object is structurally
    independent. No two rows share the same dict identity, and no row's
    via accidentally appears under another row's via slot.
    """
    rows = [
        _row_by_eid(inspector_response, eid)
        for eid in (EID_LEGACY, EID_STAMPED, EID_EXPLICIT, EID_CORRUPT)
    ]
    envs = [r["lifecycle_status"] for r in rows]
    # All four are distinct object identities in the response.
    ids = {id(e) for e in envs}
    assert len(ids) == 4, "lifecycle_status dicts share identity across rows"
    # The three healthy rows have three distinct vias.
    healthy_vias = [
        envs[0]["set_by"]["via"],
        envs[1]["set_by"]["via"],
        envs[2]["set_by"]["via"],
    ]
    assert len(set(healthy_vias)) == 3, (
        f"healthy rows should have three distinct vias, got {healthy_vias}"
    )
    # The corrupt row has no via slot at all (it's an error sentinel),
    # so it cannot accidentally collide with another row's via.
    assert "set_by" not in envs[3]


def test_existing_provenance_fields_preserved_across_corpus(inspector_response):
    """Conformance #8: H1b's additive behavior holds across the mixed
    corpus. Every row still carries the pre-H1b fields the inspector
    has always exposed (eid, provenance, has_provenance, summary).
    """
    for eid in (EID_LEGACY, EID_STAMPED, EID_EXPLICIT, EID_CORRUPT):
        row = _row_by_eid(inspector_response, eid)
        for key in ("eid", "provenance", "has_provenance", "summary"):
            assert key in row, (
                f"pre-H1b field {key!r} missing on eid={eid}"
            )
        # Every row in this fixture was given a provenance dict.
        assert row["has_provenance"] is True
        assert isinstance(row["provenance"], dict)
        assert row["provenance"].get("source_type") == "user_input"
