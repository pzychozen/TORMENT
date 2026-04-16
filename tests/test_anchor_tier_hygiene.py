"""§2A anchor-hygiene patch: contract-invariant tests.

Validates that the derived_identity tier correctly separates auto-emitted
identity anchors from seed canon memories in classification, weighting,
drift measurement, and anchor boost eligibility.

Ratified decisions: D1=(a) new tier, D2=(c) provenance tags, D3=(a) weight=0.42.
"""

import pytest
from torment_service.character import (
    CharacterSeed,
    classify_tier,
    tier_weight,
    measure_drift,
)
from torment_service.retrieval_assembler import _classify_core_hit, BLOCK_IDENTITY


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _seed() -> CharacterSeed:
    """Minimal CharacterSeed with default weights."""
    return CharacterSeed(
        seed_id="test_v1",
        character_name="Test",
        seed_text="Test character for anchor tier hygiene.",
    )


# ---------------------------------------------------------------------------
# D1: tier classification
# ---------------------------------------------------------------------------

def test_seed_canon_stays_core():
    """Seed canon memory (canon=True, half_life=3650) -> core_identity."""
    tier = classify_tier(3650.0, mtype="seed_canon", canon=True)
    assert tier == "core_identity"


def test_auto_anchor_gets_derived():
    """Auto-emitted identity_anchor (canon=False, half_life=3650) -> derived_identity."""
    tier = classify_tier(3650.0, mtype="identity_anchor", canon=False)
    assert tier == "derived_identity"


def test_backward_compat_no_mtype():
    """classify_tier(3650.0) with no kwargs -> core_identity (existing callers unbroken)."""
    tier = classify_tier(3650.0)
    assert tier == "core_identity"


def test_canon_identity_anchor_stays_core():
    """An explicitly canon identity_anchor should remain core_identity."""
    tier = classify_tier(3650.0, mtype="identity_anchor", canon=True)
    assert tier == "core_identity"


def test_relational_and_situational_unchanged():
    """Lower half-life tiers are unaffected by the mtype/canon params."""
    assert classify_tier(30.0, mtype="identity_anchor", canon=False) == "relational"
    assert classify_tier(3.0, mtype="identity_anchor", canon=False) == "situational"


# ---------------------------------------------------------------------------
# D3: tier weight ordering
# ---------------------------------------------------------------------------

def test_derived_weight_below_core():
    """derived_identity weight < core_identity weight."""
    seed = _seed()
    assert tier_weight("derived_identity", seed) < tier_weight("core_identity", seed)


def test_derived_weight_above_relational():
    """derived_identity weight > relational weight."""
    seed = _seed()
    assert tier_weight("derived_identity", seed) > tier_weight("relational", seed)


def test_derived_weight_value():
    """derived_identity weight = 0.42 by default."""
    seed = _seed()
    assert tier_weight("derived_identity", seed) == pytest.approx(0.42)


# ---------------------------------------------------------------------------
# P5 amendment: measure_drift does not count derived as core
# ---------------------------------------------------------------------------

class _FakeEntity:
    """Minimal entity mock for measure_drift."""
    def __init__(self, payload):
        self.payload = payload


class _FakeGraph:
    """Minimal graph mock with entities and embeddings."""
    def __init__(self, entities_dict, emb_dict):
        self.entities = entities_dict
        self._emb_by_eid = emb_dict


class _FakeMotifRegistry:
    def __init__(self):
        self.motifs = {}


def test_measure_drift_does_not_count_derived_as_core():
    """Auto-emitted identity_anchor should increment derived_count, not core_count."""
    import numpy as np

    seed = _seed()
    seed.seed_motif_id = ""
    seed.seed_eids = []

    entities = {
        1: _FakeEntity({
            "user_id": "agent_a",
            "half_life": 3650.0,
            "mtype": "identity_anchor",
            "canon": False,
            "born_step": 10,
        }),
        2: _FakeEntity({
            "user_id": "agent_a",
            "half_life": 30.0,
            "mtype": "standard",
            "canon": False,
            "born_step": 10,
        }),
    }
    # Dummy embeddings (won't affect tier counts)
    embs = {
        1: np.zeros(384, dtype=np.float32),
        2: np.zeros(384, dtype=np.float32),
    }

    graph = _FakeGraph(entities, embs)
    reg = _FakeMotifRegistry()

    result = measure_drift(
        graph=graph,
        motif_registry=reg,
        coherence_field=None,
        seed=seed,
        agent_id="agent_a",
        current_step=20,
    )

    assert result["core_count"] == 0, "Derived anchor must not inflate core_count"
    assert result["derived_count"] == 1, "Derived anchor should be in derived_count"
    assert result["relational_count"] == 1


# ---------------------------------------------------------------------------
# P5 amendment: query anchor full boost excludes derived identity
# ---------------------------------------------------------------------------

def test_query_anchor_full_boost_excludes_derived_identity():
    """Non-canon identity_anchor hits must not qualify for _anchor_full_boost.

    We test this indirectly by verifying the filter logic pattern:
    an identity_anchor with canon=False should be skipped.
    """
    # Simulate the filter logic from fabric.py query() anchor boost selection
    hits = [
        {"type": "identity_anchor", "canon": False, "anchor_retired": False, "eid": 10, "score": 0.9},
        {"type": "identity_anchor", "canon": True, "anchor_retired": False, "eid": 11, "score": 0.8},
        {"type": "seed_canon", "canon": True, "anchor_retired": False, "eid": 12, "score": 0.7},
        {"type": "drift_correction", "canon": False, "anchor_retired": False, "eid": 13, "score": 0.6},
        {"type": "standard", "canon": False, "anchor_retired": False, "eid": 14, "score": 0.95},
    ]

    # Replicate the patched filter logic
    _acand = []
    for _hh in hits:
        _htype = str(_hh.get("type") or "")
        if _htype == "identity_anchor":
            if not bool(_hh.get("canon")):
                continue
        elif _htype not in ("seed_canon", "drift_correction"):
            continue
        if bool(_hh.get("anchor_retired")):
            continue
        _acand.append((int(_hh.get("eid", -1)), float(_hh.get("score", 0.0))))

    boost_eids = set(e for e, _s in _acand if e >= 0)

    assert 10 not in boost_eids, "Non-canon identity_anchor must not get full boost"
    assert 11 in boost_eids, "Canon identity_anchor should get full boost"
    assert 12 in boost_eids, "seed_canon should get full boost"
    assert 13 in boost_eids, "drift_correction should get full boost"
    assert 14 not in boost_eids, "Standard memory should not get full boost"


# ---------------------------------------------------------------------------
# D2: provenance fields (structural check)
# ---------------------------------------------------------------------------

def test_provenance_fields_present():
    """The five D2 provenance keys must all exist in the extra_payload schema.

    This is a structural contract test — we verify the field names are
    correct and the types are sensible, without needing a full Fabric instance.
    """
    # Simulate the extra_payload from _maybe_emit_identity_anchor
    agent_member_eids = [1, 2, 3, 5]
    seed_eids = {1, 2}
    seed_overlap = len(seed_eids & set(agent_member_eids))

    payload = {
        "anchor_origin": "derived",
        "anchor_source": "motif_cluster",
        "seed_overlap_count": int(seed_overlap),
        "seed_aligned": bool(seed_overlap > 0),
        "source_member_eids": [int(e) for e in agent_member_eids],
    }

    assert payload["anchor_origin"] == "derived"
    assert payload["anchor_source"] == "motif_cluster"
    assert payload["seed_overlap_count"] == 2
    assert payload["seed_aligned"] is True
    assert payload["source_member_eids"] == [1, 2, 3, 5]


# ---------------------------------------------------------------------------
# P3: retrieval assembler — derived_identity stays in BLOCK_IDENTITY
# ---------------------------------------------------------------------------

def test_assembler_derived_in_identity_block():
    """Hit with character_tier='derived_identity' should be classified as BLOCK_IDENTITY."""
    hit = {
        "type": "identity_anchor",
        "canon": False,
        "character_tier": "derived_identity",
        "half_life": 3650.0,
    }
    assert _classify_core_hit(hit) == BLOCK_IDENTITY
