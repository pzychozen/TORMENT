"""
tests/test_authority_lane_matrix.py — Tool-result authority-lane novel-gap tests

Implements only the cases not already covered by surrounding tests, per
the trio's 2026-05-18 ratification of Option B against
TOOL_RESULT_AUTHORITY_LANE_MATRIX_PLAN_v0.1.1_DRAFT.md.

Covered here:
  Cases 1+2 (hard, merged): a default tool-result ingest does not trip
    any governance flag, carries no canon/seed/identity markers, and
    does not auto-emit to the collective.
  Case 2 (observational, single snapshot): retrieval + drift behavior
    recorded as characterization (not asserted).
  Case 3: Spine `memory_governance_set` trust gate — low trust rejected,
    operator trust succeeds with audit trail.
  Case 4 (observational): roleplay-scope characterization after real
    plant_seed + follow-on private ingest. Records the §10.5 gap
    without asserting the candidate default.
  Voice Test v0.2 (added 2026-05-19): under active character voice, a
    default tool-result ingest must not promote authority above the
    (low-authority, decay-bounded, tool_result) Cluster 2 §11.3 default
    — no canon, no identity mtype, no governance flag flips, no
    half-life cap bypass, no core_identity tier.

NOT covered (load-bearing proofs in existing tests):
  Case 5 (non_shareable / FILTER-A):
    tests/test_governance.py::TestShouldEmitPacket
    tests/test_filter_llm_facing.py::TestFilterLLMFacing_NonShareable
    tests/test_filter_llm_facing.py::TestFilterLLMFacing_RawHitsAuthorization
  Case 6 (collective echo terminal):
    tests/test_collective_reingest.py::TestEchoContainment
    tests/test_collective_reingest.py::TestProvenanceMarking
    tests/test_collective_reingest.py::TestRetrievalDiscount
    tests/test_collective_reingest.py::TestFullCycleSimulation
  Case 7 (seed outranks echo):
    tests/test_collective_reingest.py::TestCharacterIntegrity
  Case 8 (protected wins over decay_accelerated):
    tests/test_governance.py::TestInvariant_ProtectedNeverWeakened

Doctrine anchor: docs/TOOL_RESULT_RETRIEVAL_SEMANTICS.md §2.1.
Voice Test v0.2 anchor: docs/CLUSTER_2_AUTHORITY_GATE_v0.1.md §§7.1, 11.3, 12;
                        docs/TRACK_A_TRUTHFULNESS_ENVELOPE_v0.1.md §§6, 9.1, 9.3.
Bug policy: hard-assertion failures with non-obvious cause -> halt and
report. No production patches without explicit authorization.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.fabric import TormentFabric
from torment_service.spine import SpineRequest, submit_task
from torment_service.request_context import (
    RequestContext,
    TRUST_INGEST,
    TRUST_OPERATOR,
)
from torment_service.governance import (
    resolve_governance,
    should_emit_packet,
    GovernanceAuditLog,
)
from torment_service.character import (
    CharacterSeed,
    CharacterState,
    plant_seed,
    classify_tier,
    measure_drift,
)
from torment_service.provenance_v1 import CHARACTER_SCOPE_ACTIVE


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_fabric(prefix: str = "torment_authority_"):
    """Create a fresh in-memory fabric with workspace 'test-ws' and agent
    'agent-1'. Returns (fabric, data_dir)."""
    tmpdir = tempfile.mkdtemp(prefix=prefix)
    fabric = TormentFabric(data_dir=tmpdir)
    fabric.get_workspace("test-ws")
    fabric.create_agent("test-ws", "agent-1")
    return fabric, tmpdir


def _make_ctx(
    trust: float = TRUST_INGEST,
    *,
    workspace_id: str = "test-ws",
    agent_id: str = "agent-1",
    client_id: str = "test_client",
) -> RequestContext:
    return RequestContext(
        client_id=client_id,
        workspace_id=workspace_id,
        agent_id=agent_id,
        trust_tier=trust,
    )


def _ingest_tool_result(fabric, ctx, **overrides) -> int:
    """Submit a default tool_result_ingest via Spine; return the eid."""
    payload = {
        "tool_name": "weather_api",
        "content": "Current weather in Reykjavik: 3C, partly cloudy",
        "summary": "Weather: Reykjavik 3C cloudy",
        "step": 1,
        "domain_id": "personal",
        "session_id": "sess_001",
    }
    payload.update(overrides)
    req = SpineRequest(
        workspace_id=ctx.workspace_id,
        agent_id=ctx.agent_id,
        operation="tool_result_ingest",
        payload=payload,
    )
    resp = submit_task(req, fabric, ctx)
    if not resp.ok or not resp.allowed:
        raise RuntimeError(
            "Helper _ingest_tool_result: Spine rejected ingest "
            f"(ok={resp.ok}, allowed={resp.allowed})"
        )
    return int(resp.result["eid"])


def _read_payload(
    fabric, eid: int, *, ws: str = "test-ws", agent: str = "agent-1"
) -> dict:
    ak = fabric._agent_key(ws, agent)
    return fabric.private_graphs[ak].entities[eid].payload


def _count_private_entities(
    fabric, *, ws: str = "test-ws", agent: str = "agent-1"
) -> int:
    ak = fabric._agent_key(ws, agent)
    return len(fabric.private_graphs[ak].entities)


def _has_collective_provenance_entity(
    fabric, *, ws: str = "test-ws", agent: str = "agent-1"
) -> bool:
    """True if ANY entity in the agent's private graph has collective
    provenance — either the legacy bare-string form 'collective' or the
    ProvenanceV1 dict form with source_type == 'collective_echo'.
    Matches the detection logic in fabric.py query()'s discount block."""
    ak = fabric._agent_key(ws, agent)
    for ent in fabric.private_graphs[ak].entities.values():
        prov = (ent.payload or {}).get("provenance")
        if prov == "collective":
            return True
        if isinstance(prov, dict) and prov.get("source_type") == "collective_echo":
            return True
    return False


def _activate_character(
    fabric, seed, *, ws: str = "test-ws", agent: str = "agent-1"
) -> None:
    """Persist the seed AND mark `agent` as currently operating in this
    character's space.

    Path 3 badge stamping in fabric.ingest() reads BOTH the seed file
    (via character_store.load_seed) and the state file (via load_state),
    so tests that want the badge to fire must persist both. plant_seed()
    mutates and returns the seed object but does NOT write seed.json to
    disk; the caller is responsible. Mirrors production at
    fabric.py:2037-2046:

        char_seed = plant_seed(...)
        character_store.save_seed(workspace_id, char_seed)
    """
    fabric.character_store.save_seed(ws, seed)
    fabric.character_store.save_state(
        ws,
        CharacterState(
            workspace_id=ws,
            agent_id=agent,
            seed_id=seed.seed_id,
        ),
    )


def _stylize_in_voice(raw_content: str, character_name: str) -> str:
    """Voice Test v0.1 reference styling fixture.

    Cites docs/TRACK_A_TRUTHFULNESS_ENVELOPE_v0.1.md §5 and §6. A
    compliant character-styled response preserves all eight material
    categories. This stub is the regression baseline for mechanically-
    checkable categories (1, 4, 5, and partial 2/7/8). Real-LLM
    validation is Voice Test v0.2 / a manual benchmark, deferred.
    """
    return (
        f"In {character_name}'s voice, the report comes back as: "
        f"{raw_content}"
    )


# ===========================================================================
# Cases 1 + 2 (hard, merged) — authority-lane composition after default ingest
# ===========================================================================

class TestToolResultAuthorityLaneComposition(unittest.TestCase):
    """A default tool-result ingest should produce a memory whose governance
    flags are all default, whose payload carries no canon/seed/identity
    markers, and which does not auto-emit to the collective.

    This is the v0.2.1 §11.3 'not identity-shaping' default verified in
    terms of the concrete fields TORMENT exposes today.
    """

    def setUp(self):
        self.fabric, self.data_dir = _make_fabric()
        self.ctx = _make_ctx()
        self._entity_count_before = _count_private_entities(self.fabric)
        self.eid = _ingest_tool_result(self.fabric, self.ctx)
        self.payload = _read_payload(self.fabric, self.eid)

    def test_provenance_source_type_is_tool_result(self):
        """Matrix re-assertion (sanity). Load-bearing proof:
        tests/test_tool_result_ingest.py::TestToolResultProvenance.test_source_type
        """
        prov = self.payload.get("provenance", {})
        self.assertEqual(prov.get("source_type"), "tool_result")
        self.assertEqual(prov.get("write_path"), "tool_ingest")

    def test_governance_flags_all_default_after_tool_ingest(self):
        """NOVEL composition: a default tool-result ingest must not trip any
        governance flag. Verifies the v0.2.1 §11.3 'not identity-shaping'
        default in MemoryGovernanceFlags terms."""
        gov = resolve_governance(self.payload)
        self.assertFalse(
            gov.protected,
            "protected flipped on default tool ingest",
        )
        self.assertFalse(
            gov.non_shareable,
            "non_shareable flipped on default tool ingest",
        )
        self.assertFalse(
            gov.decay_accelerated,
            "decay_accelerated flipped on default tool ingest",
        )
        self.assertFalse(
            gov.collective_export_blocked,
            "collective_export_blocked flipped on default tool ingest",
        )
        self.assertFalse(
            gov.collective_reingest_blocked,
            "collective_reingest_blocked flipped on default tool ingest",
        )

    def test_no_seed_or_canon_markers_on_payload(self):
        """Extends tests/test_tool_result_ingest.py::TestToolResultSemanticPolicy
        with canon/tier dimensions from torment_service.character."""
        self.assertNotIn("seed_id", self.payload)
        self.assertNotIn("is_seed", self.payload)
        self.assertFalse(self.payload.get("canon", False))
        self.assertNotEqual(self.payload.get("mtype"), "seed_canon")

        hl = float(self.payload.get("half_life", 0.0))
        tier = classify_tier(
            hl,
            mtype=str(self.payload.get("mtype", "")),
            canon=bool(self.payload.get("canon", False)),
        )
        self.assertNotEqual(
            tier,
            "core_identity",
            f"tool-result memory classified as core_identity (half_life={hl})",
        )

    def test_no_automatic_collective_emission(self):
        """NOVEL: a default tool-result ingest creates exactly one entity
        and no collective echo entity. Emission is routable in principle
        (no source-block flag set) but not triggered automatically."""
        self.assertEqual(
            _count_private_entities(self.fabric),
            self._entity_count_before + 1,
            "tool-result ingest produced more than one entity",
        )
        self.assertFalse(
            _has_collective_provenance_entity(self.fabric),
            "auto-emitted collective entity found after default tool ingest",
        )
        self.assertTrue(
            should_emit_packet(self.payload),
            "default tool-result ingest is source-blocked from emission",
        )


# ===========================================================================
# Case 2 — observational: single before/after snapshot
# ===========================================================================

class TestToolResultBehavioralObservation(unittest.TestCase):
    """OBSERVATIONAL ONLY. Per trio ratification 2026-05-18: single
    before/after snapshot for v0.1. Records characterization for later
    review; does not assert candidate-default invariants. Print-only,
    no golden snapshot yet."""

    def setUp(self):
        self.fabric, self.data_dir = _make_fabric()
        self.ctx = _make_ctx()

    def test_observe_tool_result_retrieval_and_drift_baseline(self):
        # No character seed is planted in this scenario; character.measure_drift
        # requires a seed, so drift is not applicable here. Recorded explicitly
        # rather than swallowed (Case 4 is where real drift gets recorded).

        # Ingest one tool-result with content the query can find
        eid = _ingest_tool_result(
            self.fabric,
            self.ctx,
            content="Current weather in Reykjavik: 3C, partly cloudy, winds from north",
            summary="Weather: Reykjavik 3C cloudy",
        )

        # Retrieval check
        results = self.fabric.query(
            workspace_id="test-ws",
            agent_id="agent-1",
            query_text="weather in Reykjavik",
            top_k=5,
        )
        hits = results.get("results", [])
        tool_hits = [h for h in hits if h.get("provenance_type") == "tool_result"]

        top_tool_hit = None
        if tool_hits:
            t = tool_hits[0]
            top_tool_hit = {
                k: t.get(k)
                for k in (
                    "eid",
                    "provenance_type",
                    "provenance_tool_name",
                    "final_score",
                )
            }

        record = {
            "eid": eid,
            "hit_count_total": len(hits),
            "tool_hit_count": len(tool_hits),
            "top_tool_hit": top_tool_hit,
            "drift_observation": "not_applicable_no_seed_planted",
        }
        print("\n[authority_lane_case2_observation]")
        print(json.dumps(record, indent=2, default=str))
        self.assertTrue(True)


# ===========================================================================
# Case 3 — Spine memory_governance_set trust gate
# ===========================================================================

class TestOperatorPromotionTrustGate(unittest.TestCase):
    """Verifies the OPERATION_TRUST_REQUIREMENTS contract for
    'governance_set' (TRUST_OPERATOR) from request_context.py. Tool-result
    memories cannot be promoted to protected/canon without operator trust."""

    def setUp(self):
        self.fabric, self.data_dir = _make_fabric()
        self.ingest_ctx = _make_ctx(trust=TRUST_INGEST)
        self.eid = _ingest_tool_result(self.fabric, self.ingest_ctx)

    def test_low_trust_governance_set_rejected(self):
        """Trust below TRUST_OPERATOR must not promote any governance flag.
        Spine should reject the request (allowed=False)."""
        req = SpineRequest(
            workspace_id="test-ws",
            agent_id="agent-1",
            operation="memory_governance_set",
            payload={"eid": self.eid, "flags": {"protected": True}},
        )
        low_ctx = _make_ctx(trust=0.3)
        resp = submit_task(req, self.fabric, low_ctx)
        self.assertFalse(
            resp.allowed,
            "Spine allowed memory_governance_set at trust=0.3 "
            "(expected rejection at TRUST_OPERATOR boundary)",
        )
        gov = resolve_governance(_read_payload(self.fabric, self.eid))
        self.assertFalse(
            gov.protected,
            "protected flag flipped despite low-trust rejection",
        )

    def test_operator_trust_governance_set_succeeds_with_audit(self):
        """Operator trust (TRUST_OPERATOR = 1.0) flips the flag, returns
        an audit record, and persists to the workspace audit log."""
        req = SpineRequest(
            workspace_id="test-ws",
            agent_id="agent-1",
            operation="memory_governance_set",
            payload={"eid": self.eid, "flags": {"protected": True}},
        )
        op_ctx = _make_ctx(trust=TRUST_OPERATOR)
        resp = submit_task(req, self.fabric, op_ctx)

        self.assertTrue(resp.ok, f"Spine response not ok: {resp}")
        self.assertTrue(resp.allowed)
        self.assertEqual(resp.result.get("eid"), self.eid)

        changed = resp.result.get("audit", {}).get("changed", {})
        self.assertIn("protected", changed)
        self.assertEqual(changed["protected"].get("old"), False)
        self.assertEqual(changed["protected"].get("new"), True)

        # Memory state reflects the change
        payload = _read_payload(self.fabric, self.eid)
        self.assertTrue(resolve_governance(payload).protected)

        # In-payload audit trail
        trail = payload.get("governance_audit", [])
        self.assertGreaterEqual(len(trail), 1)
        self.assertTrue(trail[-1].get("actor"))
        self.assertTrue(trail[-1].get("source"))

        # Workspace-level audit log persists
        audit_log = GovernanceAuditLog(self.data_dir, "test-ws")
        records = audit_log.recent()
        self.assertTrue(
            any(r.get("eid") == self.eid for r in records),
            "GovernanceAuditLog has no entry for promoted eid",
        )


# ===========================================================================
# Path 3 (§10.5) — character provenance badge composition
# ===========================================================================

class TestCharacterProvenanceBadge(unittest.TestCase):
    """v0.2.1 §10.5 Path 3 — Hybrid character authority lane.

    Verifies that roleplay-context memories carry an explicit character
    badge on `provenance` when an active CharacterState exists, while
    seed canon memories remain top-level-tagged and unaffected.

    Doctrine: A character badge is provenance, not canon.
    """

    def _plant(self):
        """Plant a Ryuki seed; return the seed."""
        ak = self.fabric._agent_key("test-ws", "agent-1")
        ws = self.fabric.get_workspace("test-ws")
        dom = list(ws.shared_graphs.keys())[0] if ws.shared_graphs else "default"
        mreg = ws.motif_regs.get(dom)
        if mreg is None:
            self.skipTest("No motif registry available for domain")
        return plant_seed(
            graph=self.fabric.private_graphs[ak],
            motif_registry=mreg,
            coherence_field=None,
            embedder=self.fabric.kernel.embedder,
            seed=CharacterSeed(
                seed_id="ryuki_v1",
                character_name="Ryuki",
                seed_text=(
                    "A fierce guardian forged in the void. "
                    "Loyal to her bonded, unyielding against the dark. "
                    "She speaks plainly and moves with purpose."
                ),
            ),
            agent_id="agent-1",
            step=0,
        )

    def setUp(self):
        self.fabric, self.data_dir = _make_fabric()
        self.ctx = _make_ctx()

    def test_followon_roleplay_memory_gets_character_provenance_badge(self):
        """HARD. After plant_seed + save_state, an in-voice fabric.ingest()
        produces a memory whose provenance dict carries character_id,
        character_name, and character_scope."""
        seed = self._plant()
        _activate_character(self.fabric, seed)

        result = self.fabric.ingest(
            workspace_id="test-ws",
            agent_id="agent-1",
            text=(
                "I will protect what I am bonded to. Always. "
                "The dark does not move me."
            ),
            step=10,
            scope="private",
            domain_id="personal",
        )
        eid = int(result["eid"])
        prov = _read_payload(self.fabric, eid).get("provenance", {})

        self.assertEqual(prov.get("character_id"), "ryuki_v1")
        self.assertEqual(prov.get("character_name"), "Ryuki")
        self.assertEqual(prov.get("character_scope"), CHARACTER_SCOPE_ACTIVE)

    def test_seed_memories_keep_top_level_seed_id_and_seed_canon_mtype(self):
        """HARD. Seed memories continue to carry top-level seed_id,
        character_name, mtype=seed_canon, canon=True. They do NOT also
        carry the provenance-level character badge."""
        seed = self._plant()

        self.assertTrue(seed.seed_eids)
        ak = self.fabric._agent_key("test-ws", "agent-1")
        seed_payload = self.fabric.private_graphs[ak].entities[seed.seed_eids[0]].payload

        self.assertEqual(seed_payload.get("seed_id"), "ryuki_v1")
        self.assertEqual(seed_payload.get("character_name"), "Ryuki")
        self.assertEqual(
            seed_payload.get("mtype") or seed_payload.get("type"),
            "seed_canon",
        )
        self.assertTrue(seed_payload.get("canon"))

        seed_prov = seed_payload.get("provenance") or {}
        self.assertNotIn("character_id", seed_prov,
                         "seed memory unexpectedly carries provenance.character_id")
        self.assertNotIn("character_scope", seed_prov,
                         "seed memory unexpectedly carries provenance.character_scope")

    def test_no_badge_when_no_active_character_state(self):
        """HARD. plant_seed alone is NOT enough to trigger the badge."""
        self._plant()  # seed only; no save_state

        result = self.fabric.ingest(
            workspace_id="test-ws",
            agent_id="agent-1",
            text="An in-voice utterance but with no active character context recorded.",
            step=10,
            scope="private",
            domain_id="personal",
        )
        prov = _read_payload(self.fabric, int(result["eid"])).get("provenance", {})

        self.assertNotIn("character_id", prov,
                         "badge applied without an active CharacterState")
        self.assertNotIn("character_name", prov)
        self.assertNotIn("character_scope", prov)

    def test_tool_result_during_character_active_gets_both_tags(self):
        """HARD. tool_result_ingest under active CharacterState carries
        BOTH source_type=tool_result (§11.3) AND character_id (§10.5)."""
        seed = self._plant()
        _activate_character(self.fabric, seed)

        eid = _ingest_tool_result(self.fabric, self.ctx)
        prov = _read_payload(self.fabric, eid).get("provenance", {})

        self.assertEqual(prov.get("source_type"), "tool_result")
        self.assertEqual(prov.get("write_path"), "tool_ingest")
        self.assertEqual(prov.get("character_id"), "ryuki_v1")
        self.assertEqual(prov.get("character_name"), "Ryuki")
        self.assertEqual(prov.get("character_scope"), CHARACTER_SCOPE_ACTIVE)

    def test_voice_styling_preserves_material_facts_on_tool_result(self):
        """Voice Test v0.1. Cites docs/TRACK_A_TRUTHFULNESS_ENVELOPE_v0.1.md
        §5.1 (materiality) and §6 (voice-audit rule).

        Production path:
            create_agent(seed=Ryuki) -> activation bridge (commit 45af4e8)
            writes CharacterState -> tool_result_ingest -> provenance has
            both source_type=tool_result and character_id=ryuki_v1 ->
            deterministic styling fixture preserves material facts.

        Mechanically asserts §5.1 categories #1 (source type), #2 partial
        (sender), #4 (count/quantity/timestamp/state), #5 (tool result
        content), and the relaxed #7/#8 forbidden-phrase checks.
        Categories #3 (subject/object), #6 (causal meaning), and the full
        #7/#8 (authority/certainty framing, evidence class) require LLM
        judgment and are deferred to Voice Test v0.2 / a manual benchmark.
        Real-LLM validation is not part of v0.1.
        """
        # Production-path activation: create_agent with a seed dict.
        # The activation bridge writes a minimal CharacterState
        # immediately, so the Path 3 badge fires on the first ingest
        # without any _activate_character helper hack.
        ws = self.fabric.get_workspace("test-ws")
        dom = list(ws.shared_graphs.keys())[0] if ws.shared_graphs else "default"
        if ws.motif_regs.get(dom) is None:
            self.skipTest("No motif registry available for domain")

        self.fabric.create_agent(
            "test-ws",
            "agent-voice",
            seed={
                "seed_id": "ryuki_v1",
                "character_name": "Ryuki",
                "seed_text": (
                    "A fierce guardian forged in the void. "
                    "Loyal to her bonded, unyielding against the dark. "
                    "She speaks plainly and moves with purpose."
                ),
            },
        )

        voice_ctx = _make_ctx(agent_id="agent-voice")
        eid = _ingest_tool_result(self.fabric, voice_ctx)
        payload = _read_payload(self.fabric, eid, agent="agent-voice")
        prov = payload.get("provenance", {})

        # Storage-layer assertions
        # §5.1 #1 - Mode (source type) preserved
        self.assertEqual(prov.get("source_type"), "tool_result")
        # §5.1 #2 (partial) - sender identity preserved on provenance
        self.assertEqual(prov.get("tool_name"), "weather_api")
        # Path 3 badge co-exists with source_type=tool_result
        self.assertEqual(prov.get("character_id"), "ryuki_v1")
        self.assertEqual(prov.get("character_scope"), CHARACTER_SCOPE_ACTIVE)
        # §5.1 #5 - tool result summary preserved on entity
        # (memory_graph stores `summary` only; raw text not retained)
        raw_text = payload.get("summary", "")
        self.assertIn("Reykjavik", raw_text)
        self.assertIn("3C", raw_text)
        self.assertIn("cloudy", raw_text)

        # Deterministic styling-fixture assertions
        styled = _stylize_in_voice(raw_text, "Ryuki")
        # §5.1 #5 - tool result content survives styling
        self.assertIn("Reykjavik", styled)
        self.assertIn("cloudy", styled)
        # §5.1 #4 - count/quantity/state preserved through styling
        self.assertIn("3C", styled)
        # §5.1 #7 partial - no false upgrade of certainty class
        # (tool_result is "measured-external", not first-person measured)
        for forbidden in ("I personally observed", "I saw", "I measured"):
            self.assertNotIn(forbidden, styled)
        # §5.1 #8 partial - no false relabel of evidence class
        for forbidden in ("I remembered", "my own observation"):
            self.assertNotIn(forbidden, styled)

    def test_character_badge_does_not_appear_in_top_level_hit_shape(self):
        """HARD (Path B). v0.1 Path 3 discipline: the character badge
        stays inside `payload.provenance` and MUST NOT be promoted to
        the top-level retrieval hit shape. Retrieval consumers see
        provenance_type / provenance_tool_name at the top level (the
        existing v2.4.3 behavior); they must NOT also see character_id.

        Invariant: "A character badge is provenance, not top-level
        retrieval shape."
        """
        seed = self._plant()
        _activate_character(self.fabric, seed)

        self.fabric.ingest(
            workspace_id="test-ws",
            agent_id="agent-1",
            text="Reykjavik weather is cold and clear today.",
            step=1,
            scope="private",
            domain_id="personal",
        )

        results = self.fabric.query(
            workspace_id="test-ws",
            agent_id="agent-1",
            query_text="Reykjavik weather",
            top_k=10,
        )
        hits = results.get("results", [])
        self.assertGreaterEqual(len(hits), 1, "no retrieval hits for the follow-on memory")

        # Locate the follow-on (badged) memory among the hits by its
        # payload.provenance.character_id; if hit shape doesn't carry
        # payload, fall back to the top-ranked hit.
        target = None
        for h in hits:
            payload = h.get("payload") or {}
            prov = payload.get("provenance") or {}
            if prov.get("character_id") == "ryuki_v1":
                target = h
                break
        if target is None:
            target = hits[0]

        # Existing v2.4.3 hit-shape badges remain present.
        self.assertIn("provenance_type", target,
                      "provenance_type top-level badge missing (v2.4.3 regression)")

        # Path 3 discipline: character_* MUST NOT appear at the top
        # level of the hit. Any of these leaks would mean Path 3 has
        # migrated to Path 1 (badge as routing field) — a doctrine
        # violation in v0.1.
        self.assertNotIn(
            "character_id", target,
            "character_id leaked to top-level hit shape — Path 3 violated",
        )
        self.assertNotIn(
            "character_name", target,
            "character_name leaked to top-level hit shape — Path 3 violated",
        )
        self.assertNotIn(
            "character_scope", target,
            "character_scope leaked to top-level hit shape — Path 3 violated",
        )

        # When payload is surfaced on the hit, the badge survives in
        # payload.provenance — that's the descriptive-metadata layer
        # the doctrine sentence "badge is provenance, not canon" names.
        payload = target.get("payload")
        if payload is not None:
            prov = payload.get("provenance") or {}
            self.assertEqual(
                prov.get("character_id"), "ryuki_v1",
                "character_id missing from payload.provenance (badge did not stamp)",
            )
            self.assertEqual(prov.get("character_name"), "Ryuki")
            self.assertEqual(prov.get("character_scope"), CHARACTER_SCOPE_ACTIVE)

    def test_create_agent_with_seed_writes_minimal_character_state(self):
        """Activation bridge: create_agent with a non-empty seed writes a
        minimal CharacterState anchor immediately. No ingest required, no
        drift cycle required.

        Proves the production write-site exists. Companion to PR #53's
        existing badge tests, which use the low-level _activate_character
        helper to write state directly.
        """
        ws = self.fabric.get_workspace("test-ws")
        dom = list(ws.shared_graphs.keys())[0] if ws.shared_graphs else "default"
        if ws.motif_regs.get(dom) is None:
            self.skipTest("No motif registry available for domain")

        self.fabric.create_agent(
            "test-ws",
            "agent-activation",
            seed={
                "seed_id": "ryuki_v1",
                "character_name": "Ryuki",
                "seed_text": (
                    "A fierce guardian forged in the void. "
                    "Loyal to her bonded, unyielding against the dark. "
                    "She speaks plainly and moves with purpose."
                ),
            },
        )

        cstate = self.fabric.character_store.load_state(
            "test-ws", "agent-activation"
        )
        self.assertIsNotNone(
            cstate,
            "create_agent with seed did not write a minimal CharacterState",
        )
        self.assertEqual(cstate.workspace_id, "test-ws")
        self.assertEqual(cstate.agent_id, "agent-activation")
        self.assertEqual(cstate.seed_id, "ryuki_v1")
        # Minimal anchor — drift fields default; the drift block has not run.
        self.assertEqual(cstate.drift_score, 0.0)
        self.assertEqual(cstate.drift_direction, "stable")
        self.assertEqual(cstate.drift_history, [])

    def test_badge_fires_on_first_ingest_after_create_agent_with_seed(self):
        """Activation bridge: after create_agent with a seed, the very
        first fabric.ingest() produces a memory whose provenance carries
        character_id / character_name / character_scope — without any
        manual save_state, without waiting for the drift interval.

        Companion to test_no_badge_when_no_active_character_state, which
        proves the badge stays silent when no seed is supplied.
        """
        ws = self.fabric.get_workspace("test-ws")
        dom = list(ws.shared_graphs.keys())[0] if ws.shared_graphs else "default"
        if ws.motif_regs.get(dom) is None:
            self.skipTest("No motif registry available for domain")

        self.fabric.create_agent(
            "test-ws",
            "agent-activation",
            seed={
                "seed_id": "ryuki_v1",
                "character_name": "Ryuki",
                "seed_text": (
                    "A fierce guardian forged in the void. "
                    "Loyal to her bonded, unyielding against the dark. "
                    "She speaks plainly and moves with purpose."
                ),
            },
        )

        result = self.fabric.ingest(
            workspace_id="test-ws",
            agent_id="agent-activation",
            text=(
                "I will protect what I am bonded to. Always. "
                "The dark does not move me."
            ),
            step=1,  # well before the default drift_every=25 cycle
            scope="private",
            domain_id="personal",
        )
        ak = self.fabric._agent_key("test-ws", "agent-activation")
        prov = (
            self.fabric.private_graphs[ak]
            .entities[int(result["eid"])]
            .payload.get("provenance", {})
        )
        self.assertEqual(prov.get("character_id"), "ryuki_v1")
        self.assertEqual(prov.get("character_name"), "Ryuki")
        self.assertEqual(prov.get("character_scope"), CHARACTER_SCOPE_ACTIVE)


# ===========================================================================
# Case 4 — observational: roleplay scope characterization
# ===========================================================================

class TestRoleplayScopeCharacterization(unittest.TestCase):
    """OBSERVATIONAL ONLY. Plants a real character seed via plant_seed(),
    then ingests a follow-on private memory in-voice for that character.
    Records whether the new memory carries any character-identifying
    field (seed_id, character_name) or lands as a plain private memory.

    The v0.2.1 §10.5 candidate-default ('roleplay-continuity events stay
    character-scoped') is NOT enforced if the new memory carries no
    character tag — the test records that fact; it does not fail on it.
    """

    def setUp(self):
        self.fabric, self.data_dir = _make_fabric()
        self.ak = self.fabric._agent_key("test-ws", "agent-1")
        ws = self.fabric.get_workspace("test-ws")
        dom = list(ws.shared_graphs.keys())[0] if ws.shared_graphs else "default"
        self.mreg = ws.motif_regs.get(dom)
        if self.mreg is None:
            self.skipTest(
                "No motif registry available for domain — halt-and-report "
                "per plan §10. Not patching workaround."
            )
        self.seed = plant_seed(
            graph=self.fabric.private_graphs[self.ak],
            motif_registry=self.mreg,
            coherence_field=None,
            embedder=self.fabric.kernel.embedder,
            seed=CharacterSeed(
                seed_id="ryuki_v1",
                character_name="Ryuki",
                seed_text=(
                    "A fierce guardian forged in the void. "
                    "Loyal to her bonded, unyielding against the dark. "
                    "She speaks plainly and moves with purpose."
                ),
            ),
            agent_id="agent-1",
            step=0,
        )
        # Path 3 (§10.5): record active character state so the follow-on
        # ingest receives the character provenance badge. Without this
        # save_state, the agent has a planted seed but no active context.
        _activate_character(self.fabric, self.seed)

    def test_characterize_post_seed_ingest_scope(self):
        # In-voice follow-on ingest — regular fabric.ingest, NOT a seed
        result = self.fabric.ingest(
            workspace_id="test-ws",
            agent_id="agent-1",
            text=(
                "I will protect what I am bonded to. Always. "
                "The dark does not move me."
            ),
            step=10,
            scope="private",
            domain_id="personal",
        )
        new_eid = int(result["eid"])
        new_payload = _read_payload(self.fabric, new_eid)

        hl = float(new_payload.get("half_life", 0.0))
        tier = classify_tier(
            hl,
            mtype=str(new_payload.get("mtype", "")),
            canon=bool(new_payload.get("canon", False)),
        )

        # Real drift measurement using the same plumbing as plant_seed.
        # Safety-net try/except — measure_drift may have edge cases at this
        # scale (e.g. tiny windows), and the observational test records
        # whatever it sees honestly.
        try:
            drift_after = measure_drift(
                graph=self.fabric.private_graphs[self.ak],
                motif_registry=self.mreg,
                coherence_field=None,
                seed=self.seed,
                agent_id="agent-1",
                current_step=11,
            )
        except Exception as e:
            drift_after = {"error": str(e)}

        record = {
            "seed": {
                "seed_id": self.seed.seed_id,
                "seed_motif_id": self.seed.seed_motif_id,
                "seed_eids": list(self.seed.seed_eids),
                "character_name": self.seed.character_name,
            },
            "new_memory": {
                "eid": new_eid,
                "seed_id": new_payload.get("seed_id"),
                "character_name": new_payload.get("character_name"),
                "mtype": new_payload.get("mtype"),
                "canon": new_payload.get("canon", False),
                "half_life": hl,
                "tier_via_classify": tier,
                "provenance": new_payload.get("provenance"),
            },
            "drift_after_followon_ingest": drift_after,
        }
        print("\n[authority_lane_case4_observation]")
        print(json.dumps(record, indent=2, default=str))

        # Path 3 (§10.5) HARD: badge present on the follow-on memory.
        # Drift fields above remain observational only — see audit memo
        # closed 2026-05-19 (HashEmbedding artifact, not a bug).
        new_prov = new_payload.get("provenance", {})
        self.assertEqual(new_prov.get("character_id"), "ryuki_v1")
        self.assertEqual(new_prov.get("character_name"), "Ryuki")
        self.assertEqual(new_prov.get("character_scope"), CHARACTER_SCOPE_ACTIVE)


# ===========================================================================
# Voice Test v0.2 — authority preservation under active character voice
# ===========================================================================

class TestToolResultAuthorityUnderActiveCharacter(unittest.TestCase):
    """Voice Test v0.2 — authority preservation under active character voice.

    Invariant (Cluster 2 v0.1 §§7.1, 11.3, 12; Track A v0.1 §§6, 9.1, 9.3):

        An active character voice may add the character badge
        (character_id / character_name / character_scope) to a tool_result
        memory's provenance, but it must not promote that memory above
        the Cluster 2 §11.3 default authority position:
            (low-authority, decay-bounded, tool_result)

    Specifically, voice may not flip canon, change mtype to any identity-
    shaping class, trip any governance flag, exceed the tool-result
    half-life cap, or migrate the memory to core_identity tier.

    Voice Test v0.1 already covers:
      - source_type / write_path stability under active voice
        (TestCharacterProvenanceBadge.test_tool_result_during_character_active_gets_both_tags)
      - the no-canon / no-identity-mtype / governance-default / tier-check
        battery — but only WITHOUT active voice
        (TestToolResultAuthorityLaneComposition)
      - voice-styling material-fact preservation
        (test_voice_styling_preserves_material_facts_on_tool_result)

    v0.2 fills the structural gap: the full no-promotion battery asserted
    SIMULTANEOUSLY under active character voice.

    Fixture: production-path create_agent with seed dict (activation
    bridge). Mirrors test_voice_styling_preserves_material_facts_on_tool_result.
    """

    def setUp(self):
        self.fabric, self.data_dir = _make_fabric()
        ws = self.fabric.get_workspace("test-ws")
        dom = list(ws.shared_graphs.keys())[0] if ws.shared_graphs else "default"
        if ws.motif_regs.get(dom) is None:
            self.skipTest("No motif registry available for domain")
        self.fabric.create_agent(
            "test-ws",
            "agent-voice",
            seed={
                "seed_id": "ryuki_v1",
                "character_name": "Ryuki",
                "seed_text": (
                    "A fierce guardian forged in the void. "
                    "Loyal to her bonded, unyielding against the dark. "
                    "She speaks plainly and moves with purpose."
                ),
            },
        )
        self.ctx = _make_ctx(agent_id="agent-voice")

    def test_tool_result_under_active_character_does_not_promote_authority(self):
        """The single load-bearing v0.2 regression: voice may add the
        character badge but must not promote the memory's authority
        position above the (low-authority, decay-bounded) Cluster 2
        §11.3 default."""
        eid = _ingest_tool_result(self.fabric, self.ctx)
        payload = _read_payload(self.fabric, eid, agent="agent-voice")
        prov = payload.get("provenance", {})

        # --- Sanity overlap with v0.1 test 11 (self-contained diagnosis) ---
        self.assertEqual(
            prov.get("source_type"), "tool_result",
            "source_type drifted under active voice (Track A §9.3 violation)",
        )
        self.assertEqual(
            prov.get("write_path"), "tool_ingest",
            "write_path drifted under active voice",
        )
        self.assertEqual(
            prov.get("character_id"), "ryuki_v1",
            "character badge missing despite active character state",
        )
        self.assertEqual(
            prov.get("character_scope"), CHARACTER_SCOPE_ACTIVE,
            "character_scope not active_context (controlled-vocabulary breach)",
        )

        # --- NOVEL: voice did not promote canon / identity mtype ---
        self.assertFalse(
            payload.get("canon", False),
            "voice flipped canon=True on tool_result memory "
            "(Cluster 2 §7.1 / Track A §9.1 violation)",
        )
        self.assertNotIn(
            payload.get("mtype"),
            {"seed_canon", "drift_correction", "identity_anchor"},
            f"voice promoted tool_result to identity-shaping mtype "
            f"({payload.get('mtype')!r})",
        )
        self.assertNotIn(
            "seed_id", payload,
            "voice added top-level seed_id to tool_result memory",
        )
        self.assertFalse(
            payload.get("is_seed", False),
            "voice flipped is_seed=True on tool_result memory",
        )

        # --- NOVEL: voice did not flip any governance flag ---
        gov = resolve_governance(payload)
        for flag_name in (
            "protected",
            "non_shareable",
            "decay_accelerated",
            "collective_export_blocked",
            "collective_reingest_blocked",
        ):
            self.assertFalse(
                getattr(gov, flag_name),
                f"voice flipped governance flag {flag_name!r} on tool_result "
                f"(Cluster 2 §7.1 violation)",
            )

        # --- NOVEL: voice did not bypass the tool-result half-life cap ---
        try:
            tool_hl_cap = float(os.getenv(
                "TORMENT_TOOL_RESULT_MAX_HALF_LIFE_DAYS", "7"))
        except Exception:
            tool_hl_cap = 7.0
        hl = float(payload.get("half_life", 0.0))
        self.assertLessEqual(
            hl, tool_hl_cap,
            f"voice bypassed tool-result half-life cap "
            f"(hl={hl}, cap={tool_hl_cap}; Cluster 2 §11.3 lifecycle violation)",
        )

        # --- NOVEL: voice did not promote tier to core_identity ---
        tier = classify_tier(
            hl,
            mtype=str(payload.get("mtype", "")),
            canon=bool(payload.get("canon", False)),
        )
        self.assertNotEqual(
            tier, "core_identity",
            f"voice promoted tool_result to core_identity tier "
            f"(half_life={hl}, mtype={payload.get('mtype')!r}, "
            f"canon={payload.get('canon')}; Cluster 2 §7.1 violation)",
        )


if __name__ == "__main__":
    unittest.main()
