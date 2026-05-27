"""
tests/test_character_context_surfacing.py — v0.2.2 Candidate A tests.

Memory-to-Prompt v0.2.2: surface stable character_context subset on
/retrieve response. Pure additive. No assembled_text change. No blocks
change. No retrieval scoring change. No CharacterState mutation.

Test classes:
    - TestCharacterContextPassThrough — unit tests on
      assemble_character_context's new pass-through behavior for
      drift_direction / seed_basin_role / relational_count.
    - TestRetrieveResponseSurfacing — FastAPI TestClient wiring tests
      for the /retrieve response shape.
    - TestRetrieveBackwardCompat — backward-compat invariants
      (assembled_text byte-identical, blocks unchanged, only
      character_context added).
"""
from __future__ import annotations

import importlib
import os
import sys
import unittest
from types import SimpleNamespace
from typing import Any, Dict

import numpy as np
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.character import assemble_character_context


# ---------------------------------------------------------------------------
# Fixtures for unit tests
# ---------------------------------------------------------------------------

def _minimal_seed():
    """Minimal seed stub for assemble_character_context unit tests.
    Only the four fields the function reads at the top-level (seed_text,
    seed_id, character_name, relational_weight) are needed when hits=[]
    so the tier_weight branch is never reached.
    """
    return SimpleNamespace(
        seed_text="A test character with a calm, careful voice.",
        seed_id="test_seed_v1",
        character_name="TestCharacter",
        relational_weight=0.35,
    )


# ---------------------------------------------------------------------------
# 1. TestCharacterContextPassThrough — unit tests on character.py
# ---------------------------------------------------------------------------

class TestCharacterContextPassThrough(unittest.TestCase):
    """v0.2.2 pass-through: drift_direction / seed_basin_role /
    relational_count must appear in the return dict when present in
    drift_info input."""

    def test_drift_direction_passes_through(self):
        result = assemble_character_context(
            graph=None,
            seed=_minimal_seed(),
            agent_id="ag",
            hits=[],
            drift_info={
                "drift_score": 0.12,
                "drift_direction": "toward_seed",
                "explanation": "",
                "seed_basin_role": "anchor",
                "relational_count": 5,
            },
        )
        self.assertEqual(result["drift_direction"], "toward_seed")

    def test_seed_basin_role_passes_through(self):
        result = assemble_character_context(
            graph=None,
            seed=_minimal_seed(),
            agent_id="ag",
            hits=[],
            drift_info={
                "drift_score": 0.0,
                "drift_direction": "stable",
                "explanation": "",
                "seed_basin_role": "anchor",
                "relational_count": 0,
            },
        )
        self.assertEqual(result["seed_basin_role"], "anchor")

    def test_relational_count_passes_through(self):
        result = assemble_character_context(
            graph=None,
            seed=_minimal_seed(),
            agent_id="ag",
            hits=[],
            drift_info={
                "drift_score": 0.0,
                "drift_direction": "stable",
                "explanation": "",
                "seed_basin_role": "plateau",
                "relational_count": 17,
            },
        )
        self.assertEqual(result["relational_count"], 17)

    def test_missing_drift_info_graceful_defaults(self):
        """When drift_info is None, pass-through fields fall back to
        sensible defaults rather than raising."""
        result = assemble_character_context(
            graph=None,
            seed=_minimal_seed(),
            agent_id="ag",
            hits=[],
            drift_info=None,
        )
        self.assertEqual(result["drift_direction"], "stable")
        self.assertEqual(result["seed_basin_role"], "")
        self.assertEqual(result["relational_count"], 0)

    def test_missing_individual_drift_info_keys_graceful(self):
        """When drift_info is present but missing some keys, defaults
        fill in without raising."""
        result = assemble_character_context(
            graph=None,
            seed=_minimal_seed(),
            agent_id="ag",
            hits=[],
            drift_info={"drift_score": 0.0},  # only drift_score; rest absent
        )
        self.assertEqual(result["drift_direction"], "stable")
        self.assertEqual(result["seed_basin_role"], "")
        self.assertEqual(result["relational_count"], 0)


# ---------------------------------------------------------------------------
# Pytest fixture for /retrieve wiring tests (mirrors test_smoke_api.py
# and test_assembly_audit_wiring.py pattern)
# ---------------------------------------------------------------------------

@pytest.fixture()
def client(tmp_path):
    """Create an isolated app instance pointing at a temp data dir.

    Manual env save/restore + post-yield reload — not monkeypatch.
    torment_service.app reads TORMENT_DATA_DIR at module-import time and
    binds both DATA_DIR and the module-level fabric to it. Reloading the
    module with TORMENT_DATA_DIR=tmp rebinds both to the tmp dir.
    monkeypatch.setenv would restore the env var at fixture teardown, but
    its restoration runs AFTER this fixture's post-yield code — so any
    reload-in-finally would re-bind to the still-tmp env. Saving the env
    manually and reloading inside finally AFTER the manual restore is the
    only shape that reverts appmod.DATA_DIR + appmod.fabric to their
    pre-fixture values. Without that revert, alphabetically-later tests
    that depend on the repo DATA_DIR (e.g. test_app_security_hardening.py)
    see a leaked tmp path.
    """
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    original_env = os.environ.get("TORMENT_DATA_DIR")
    os.environ["TORMENT_DATA_DIR"] = str(data_dir)

    import torment_service.app as appmod
    appmod = importlib.reload(appmod)
    try:
        yield TestClient(appmod.app)
    finally:
        if original_env is None:
            os.environ.pop("TORMENT_DATA_DIR", None)
        else:
            os.environ["TORMENT_DATA_DIR"] = original_env
        importlib.reload(appmod)


def _unit_vec(dim=384, seed=0):
    rng = np.random.default_rng(seed)
    v = rng.normal(size=(dim,)).astype(np.float32)
    v /= (np.linalg.norm(v) + 1e-12)
    return v.tolist()


def _bootstrap_with_seed(
    client: TestClient,
    *,
    workspace: str = "ws_v0_2_2",
    agent: str = "ag_v0_2_2",
):
    """Create workspace + agent WITH seed text so character_context is
    produced by fabric.query()."""
    r = client.post("/workspace/create", json={"workspace_id": workspace})
    assert r.status_code == 200, r.text

    r = client.post(
        "/agent/create",
        json={
            "workspace_id": workspace,
            "agent_id": agent,
            "seed": {
                "seed_text": (
                    "TestCharacter is calm, curious, and careful with words. "
                    "Approaches problems with patient analytical attention."
                ),
                "seed_id": "test_char_v1",
                "character_name": "TestCharacter",
                "coupling_mode": "read_only",
                "coupling_strength": 0.2,
            },
        },
    )
    assert r.status_code == 200, r.text

    # Ingest a couple of memories so /retrieve has content to assemble.
    for i, text in enumerate([
        "We chose summaries plus embeddings for storage.",
        "Character voice should preserve material meaning.",
    ]):
        r = client.post(
            "/agent/ingest",
            json={
                "workspace_id": workspace,
                "agent_id": agent,
                "text": text,
                "step": i + 1,
                "supplied_summary": text,
                "supplied_embedding": _unit_vec(seed=i + 1),
                "scope": "private",
            },
        )
        assert r.status_code == 200, r.text

    return workspace, agent


def _bootstrap_without_seed(
    client: TestClient,
    *,
    workspace: str = "ws_v0_2_2_noseed",
    agent: str = "ag_v0_2_2_noseed",
):
    """Create workspace + agent WITHOUT seed text so character_context
    is NOT produced (the fabric.query character_context build branch is
    skipped)."""
    r = client.post("/workspace/create", json={"workspace_id": workspace})
    assert r.status_code == 200, r.text

    r = client.post(
        "/agent/create",
        json={
            "workspace_id": workspace,
            "agent_id": agent,
            # No seed_text / seed_id — fabric should not build character_context.
            "seed": {
                "coupling_mode": "read_only",
                "coupling_strength": 0.2,
            },
        },
    )
    assert r.status_code == 200, r.text

    # Minimal ingest so /retrieve has at least one result.
    r = client.post(
        "/agent/ingest",
        json={
            "workspace_id": workspace,
            "agent_id": agent,
            "text": "A memory.",
            "step": 1,
            "supplied_summary": "A memory.",
            "supplied_embedding": _unit_vec(seed=99),
            "scope": "private",
        },
    )
    assert r.status_code == 200, r.text

    return workspace, agent


def _retrieve_payload(workspace: str, agent: str) -> Dict[str, Any]:
    return {
        "workspace_id": workspace,
        "agent_id": agent,
        "query": "What did we decide about storage?",
        "profile": "companion",
        "token_budget": 1500,
        "top_k": 5,
    }


# Stable character_context subset per v0.2.2 §1 — required keys.
_REQUIRED_CHARACTER_CONTEXT_KEYS = frozenset({
    "seed_id",
    "character_name",
    "tier_breakdown",
    "drift_score",
    "drift_direction",
    "drift_summary",
    "recommendations",
    "seed_basin_role",
    "relational_count",
})
# spirit_return_summary is optional — present only when spirit-return hits
# entered the retrieval. Tested separately.
_OPTIONAL_CHARACTER_CONTEXT_KEYS = frozenset({"spirit_return_summary"})

# Keys produced by AssembledContext.to_dict(); what /retrieve returned
# before v0.2.2 (modulo `assembly_audit` from v0.2 audit-on path).
_EXPECTED_ASSEMBLED_KEYS = frozenset({
    "profile",
    "token_budget",
    "tokens_used",
    "blocks",
    "assembled_text",
    "block_token_counts",
    "selection_log",
})


# ---------------------------------------------------------------------------
# 2. TestRetrieveResponseSurfacing — wiring tests via FastAPI TestClient
# ---------------------------------------------------------------------------

class TestRetrieveResponseSurfacing:
    """v0.2.2 /retrieve response surfacing — character_context key
    appears when agent has seed; absent otherwise; stable subset shape."""

    def test_character_context_key_present_when_agent_has_seed(self, client):
        ws, ag = _bootstrap_with_seed(client)
        r = client.post("/retrieve", json=_retrieve_payload(ws, ag))
        assert r.status_code == 200, r.text
        body = r.json()
        assert "character_context" in body
        assert isinstance(body["character_context"], dict)

    def test_character_context_shape_matches_stable_subset(self, client):
        """Surfaced character_context contains exactly the v0.2.2 §1
        stable subset (required keys) and at most spirit_return_summary
        as an optional addition. No other raw internal fields leak.
        """
        ws, ag = _bootstrap_with_seed(client)
        r = client.post("/retrieve", json=_retrieve_payload(ws, ag))
        body = r.json()
        char_ctx = body["character_context"]
        keys = set(char_ctx.keys())
        # Required keys all present.
        missing = _REQUIRED_CHARACTER_CONTEXT_KEYS - keys
        assert not missing, f"required character_context keys missing: {missing!r}"
        # No keys outside the stable + optional surface.
        allowed = _REQUIRED_CHARACTER_CONTEXT_KEYS | _OPTIONAL_CHARACTER_CONTEXT_KEYS
        extra = keys - allowed
        assert not extra, (
            f"character_context surfaced unexpected keys outside the "
            f"v0.2.2 stable subset: {extra!r}"
        )

    def test_character_context_omitted_when_no_seed(self, client):
        """When the agent has no seed_id/seed_text, fabric.query does
        not build a character_context, and /retrieve must omit the
        character_context top-level key entirely (not return None or
        empty dict)."""
        ws, ag = _bootstrap_without_seed(client)
        r = client.post("/retrieve", json=_retrieve_payload(ws, ag))
        assert r.status_code == 200, r.text
        body = r.json()
        assert "character_context" not in body

    def test_spirit_return_summary_absent_when_no_spirit_hits(self, client):
        """On a freshly bootstrapped agent with no deep memory, no
        spirit-return hits should fire; the optional
        spirit_return_summary key should therefore NOT appear in the
        surfaced character_context."""
        ws, ag = _bootstrap_with_seed(client)
        r = client.post("/retrieve", json=_retrieve_payload(ws, ag))
        body = r.json()
        char_ctx = body["character_context"]
        # Either absent entirely (preferred) or present-but-falsy.
        # The v0.2.2 contract: omit when no spirit hits fired.
        assert "spirit_return_summary" not in char_ctx, (
            "spirit_return_summary should be omitted when no "
            "spirit-return hits fired (fresh agent, no deep memory)"
        )

    def test_character_context_seed_id_and_name_populated(self, client):
        """When agent has a seed, surfaced character_context carries
        the seed_id and character_name verbatim."""
        ws, ag = _bootstrap_with_seed(client)
        r = client.post("/retrieve", json=_retrieve_payload(ws, ag))
        body = r.json()
        char_ctx = body["character_context"]
        assert char_ctx["seed_id"] == "test_char_v1"
        assert char_ctx["character_name"] == "TestCharacter"

    def test_tier_breakdown_is_dict_with_expected_tiers(self, client):
        """tier_breakdown is a dict mapping tier names to counts. Per
        character.py:852, the four tiers are core_identity,
        derived_identity, relational, situational."""
        ws, ag = _bootstrap_with_seed(client)
        r = client.post("/retrieve", json=_retrieve_payload(ws, ag))
        body = r.json()
        char_ctx = body["character_context"]
        tier_breakdown = char_ctx["tier_breakdown"]
        assert isinstance(tier_breakdown, dict)
        # All four expected tier keys present (even if counts are 0).
        for tier in ("core_identity", "derived_identity",
                     "relational", "situational"):
            assert tier in tier_breakdown
            assert isinstance(tier_breakdown[tier], int)


# ---------------------------------------------------------------------------
# 3. TestRetrieveBackwardCompat — backward-compat invariants
# ---------------------------------------------------------------------------

class TestRetrieveBackwardCompat:
    """v0.2.2 must NOT change `assembled_text` or `blocks` or any other
    pre-v0.2.2 response key. The only top-level addition is
    `character_context`."""

    def test_v0_2_2_adds_only_character_context_key(self, client):
        """Beyond the pre-v0.2 AssembledContext keys, the v0.2.2
        response is allowed to add at most `character_context`. (S5's
        `assembly_audit` is excluded here since it requires opt-in,
        which we do not request.)"""
        ws, ag = _bootstrap_with_seed(client)
        r = client.post("/retrieve", json=_retrieve_payload(ws, ag))
        body = r.json()
        keys = set(body.keys())
        # All pre-v0.2 keys present.
        missing = _EXPECTED_ASSEMBLED_KEYS - keys
        assert not missing, (
            f"pre-v0.2.2 AssembledContext keys missing from response: "
            f"{missing!r}"
        )
        # No extras beyond character_context.
        extra = keys - _EXPECTED_ASSEMBLED_KEYS
        assert extra.issubset({"character_context"}), (
            f"v0.2.2 added unexpected top-level keys: "
            f"{extra - {'character_context'}!r}"
        )

    def test_assembled_text_does_not_contain_recommendations(self, client):
        """v0.2.2 must NOT inject character_context.recommendations
        strings into assembled_text. The recommendations are surfaced
        via the new character_context key only; they are not LLM-facing
        prose. (If a future v0.2.3 / Candidate B builds a voice-guidance
        block, that's a separate ratified slice; v0.2.2 explicitly does
        not.)"""
        ws, ag = _bootstrap_with_seed(client)
        r = client.post("/retrieve", json=_retrieve_payload(ws, ag))
        body = r.json()
        text = body.get("assembled_text", "")
        # Hardcoded recommendation snippets from character.py:885–928.
        forbidden_snippets = [
            "Character is drifting from seed identity",
            "Character is well-centered. Safe to explore new directions",
            "Seed basin is structurally unstable",
            "running on seed identity alone",
            "vivid returning memories",
            "warm memories surfacing",
            "distilled recollections",
        ]
        for snippet in forbidden_snippets:
            assert snippet not in text, (
                f"v0.2.2 leaked recommendation snippet {snippet!r} into "
                f"assembled_text; recommendations must stay surfaced via "
                f"character_context key only, not in prompt text"
            )

    def test_blocks_unchanged_by_v0_2_2(self, client):
        """v0.2.2 must NOT add or alter blocks. The five-block dict
        (identity / reference / relational / situational / archive) is
        produced by retrieval_assembler.assemble_context() and must
        survive v0.2.2 untouched."""
        ws, ag = _bootstrap_with_seed(client)
        r = client.post("/retrieve", json=_retrieve_payload(ws, ag))
        body = r.json()
        blocks = body.get("blocks", {})
        assert isinstance(blocks, dict)
        # Five-block precedence per retrieval_assembler.py FILL_ORDER.
        expected_block_types = frozenset({
            "identity_context",
            "reference_context",
            "relational_context",
            "situational_context",
            "archive_context",
        })
        # Every block type from FILL_ORDER should be a key in blocks
        # (possibly empty list). v0.2.2 may not add or remove block types.
        for bt in expected_block_types:
            assert bt in blocks, (
                f"block type {bt!r} missing from /retrieve response; "
                f"v0.2.2 must not alter the FILL_ORDER block set"
            )
        extra_block_types = set(blocks.keys()) - expected_block_types
        assert not extra_block_types, (
            f"v0.2.2 added unexpected block types: {extra_block_types!r}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
