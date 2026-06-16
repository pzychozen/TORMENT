"""tests/test_identity_anchor_writer_path_characterization.py

_maybe_emit_identity_anchor WRITER-PATH CHARACTERIZATION (test-only).

Seam-2 slice (test-only, RESHAPE per Codex: writer-path characterization
ONLY). This pack drives the *real* ``TormentFabric._maybe_emit_identity_anchor``
once, directly, and pins the *current* automatic emission shape of the
derived identity-anchor writer. It makes **no production change** and
proposes no fix.

This is a characterization of CURRENT automatic emission behavior. It is
NOT a statement of desired/required runtime behavior. If a later,
separately-authorized slice introduces a writer-authority gate, a
seed-governance crossing, or a canon-source distinction for this writer,
these assertions are expected to change deliberately — that is the
signal, not a surprise.

What it pins (writer payload + no-authority-gate fact):
  * one ``identity_anchor`` row is emitted when the count/gap thresholds
    are met by present same-fixture motif members;
  * the emitted row's current writer shape: type=identity_anchor,
    canon=False, half_life=3650.0, anchor_origin="derived",
    anchor_source="motif_cluster", seed_overlap_count / seed_aligned
    present, and source_member_eids matching the fixture's present
    member EIDs;
  * the emission call succeeds WITHOUT any operator-approval,
    seed-governance decision, or authority object being passed — the
    writer exposes no such parameter today.

Deliberately OUT of scope (do not assert here):
  * read-side tier/weight/drift/boost hygiene already covered by
    tests/test_anchor_tier_hygiene.py (touched only incidentally via the
    emitted payload);
  * P4 source-sameness / presence-vs-sameness conformance;
  * reused-EID contamination, cross-agent/source identity, orphan
    filtering, source-family conformance;
  * canon_source presence/absence;
  * Document A / Seed-Gov gates as *required* runtime behavior;
  * prior-anchor retirement (no prior anchor exists in this fixture);
  * any claim that the writer is "purely additive";
  * promotion/admission policy, schema/storage/database, Stage B.

In-process pattern: a fresh temp ``TormentFabric`` + workspace + agent +
its real private ``MemoryGraph`` + one fixture ``Motif`` whose members
are present member EIDs in that graph. No TORMENT server start.
"""
from __future__ import annotations

import inspect
import shutil
import tempfile

import numpy as np
import pytest


# ---------------------------------------------------------------------------
# Fixture: real fabric + workspace + agent + present motif members
# ---------------------------------------------------------------------------


def _build_fabric_env(monkeypatch):
    """Construct a real TormentFabric with a workspace, an agent, four
    present neutral member rows in the agent's private graph, and one
    fixture Motif whose members are exactly those present EIDs.

    Returns a dict of the live objects the writer needs.
    """
    fabric_mod = pytest.importorskip("torment_service.fabric")
    motifs_mod = pytest.importorskip("torment_service.motifs")
    TormentFabric = fabric_mod.TormentFabric
    Motif = motifs_mod.Motif

    # Pin emission thresholds deterministically (read via os.getenv at call).
    monkeypatch.setenv("TORMENT_ID_ANCHOR_MIN_COUNT", "3")
    monkeypatch.setenv("TORMENT_ID_ANCHOR_MIN_GAP_STEPS", "50")
    monkeypatch.setenv("TORMENT_ID_ANCHOR_MAX_EXAMPLES", "2")

    # Neutralize role-tuned variability: multipliers default to 1.0, so the
    # pinned env thresholds are used unchanged. (Affect variability is
    # neutralized separately by emitting members with no affect_tag.)
    monkeypatch.setattr(fabric_mod, "role_multipliers", lambda *_a, **_k: {})

    tmpdir = tempfile.mkdtemp(prefix="torment_id_anchor_writer_char_")
    fabric = TormentFabric(data_dir=tmpdir)
    ws = fabric.get_workspace("ws")
    fabric.create_agent("ws", "agent")

    # First registered domain (default) — robust to the default domain name.
    domain_id = next(iter(ws.motif_regs))

    ak = fabric._agent_key("ws", "agent")
    g = fabric.private_graphs[ak]  # materialized by create_agent

    # Add four present, neutral member rows (no affect_tag -> not
    # affect-sensitive). These are the ONLY EIDs used; all present in g.
    member_eids = []
    for i in range(4):
        text = f"Neutral recurring contribution number {i} for the test motif."
        emb = np.asarray(fabric.kernel.embedder.embed(text), dtype=np.float32)
        eid = g.add_memory(
            summary=text,
            embedding=emb,
            mtype="episode",
            strength=0.5,
            confidence=0.5,
            half_life_days=30.0,
            canon=False,
            user_id="agent",
            step=0,
        )
        member_eids.append(int(eid))

    # One fixture Motif whose members are exactly the present EIDs.
    motif = Motif(
        motif_id="m_test",
        domain_id=domain_id,
        label="recurring test theme",
        centroid=[0.0] * int(ws.embed_dim),
        strength=0.9,
        members=list(member_eids),
        contributing_agents=["agent"],
        stability_score=0.9,
        created_ts=0,
        last_active_ts=0,
    )
    ws.motif_regs[domain_id].motifs["m_test"] = motif

    return {
        "tmpdir": tmpdir,
        "fabric": fabric,
        "ws": ws,
        "domain_id": domain_id,
        "graph": g,
        "member_eids": member_eids,
    }


# ===========================================================================
# Writer-path characterization
# ===========================================================================


def test_identity_anchor_writer_emits_current_shape(monkeypatch):
    """Calling the real _maybe_emit_identity_anchor with present members past
    threshold emits one identity_anchor row in its CURRENT writer shape."""
    env = _build_fabric_env(monkeypatch)
    fabric = env["fabric"]
    g = env["graph"]
    member_eids = env["member_eids"]

    # Direct call to the real writer. Note the argument list: there is NO
    # operator-approval, seed-governance, or authority object — characterizing
    # that the writer exposes no such gate today.
    eid = fabric._maybe_emit_identity_anchor(
        env["ws"],
        agent_id="agent",
        domain_id=env["domain_id"],
        step=1000,
        motif_ids=["m_test"],
    )

    try:
        assert eid is not None, "writer should emit one anchor past threshold"
        payload = g.entities[int(eid)].payload

        # Current emitted writer shape (stored field names per memory_graph).
        assert payload["type"] == "identity_anchor"
        assert payload["canon"] is False
        assert float(payload["half_life"]) == 3650.0
        assert payload["anchor_origin"] == "derived"
        assert payload["anchor_source"] == "motif_cluster"

        # No seed planted in this fixture -> overlap is zero, not aligned.
        assert "seed_overlap_count" in payload
        assert payload["seed_overlap_count"] == 0
        assert payload["seed_aligned"] is False

        # source_member_eids reflects exactly the present same-fixture members.
        assert "source_member_eids" in payload
        assert set(payload["source_member_eids"]) == set(member_eids)
        assert len(payload["source_member_eids"]) == len(member_eids)
    finally:
        shutil.rmtree(env["tmpdir"], ignore_errors=True)


def test_identity_anchor_writer_takes_no_authority_object(monkeypatch):
    """The emission succeeds with no operator-approval / seed-governance /
    authority parameter — characterizing the absence of a writer-authority
    gate on this automatic writer today (named, not asserted as desired)."""
    env = _build_fabric_env(monkeypatch)
    fabric = env["fabric"]

    try:
        # Signature characterization: the writer exposes no authority-style
        # parameter to pass even if a caller wanted to.
        params = set(
            inspect.signature(fabric._maybe_emit_identity_anchor).parameters
        )
        for forbidden in (
            "approval", "authority", "operator", "governance",
            "seed_revision", "admission", "authorized",
        ):
            assert forbidden not in params, (
                f"writer unexpectedly exposes a {forbidden!r} parameter"
            )

        # And the call itself succeeds passing none of those.
        eid = fabric._maybe_emit_identity_anchor(
            env["ws"],
            agent_id="agent",
            domain_id=env["domain_id"],
            step=1000,
            motif_ids=["m_test"],
        )
        assert eid is not None
    finally:
        shutil.rmtree(env["tmpdir"], ignore_errors=True)
